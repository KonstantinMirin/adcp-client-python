"""One hook: a base with branches validates as the branch a document satisfies.

A schema root whose branches partition the document space generates a base and
one class per branch. The base carries THIS hook, so the root's name resolves to
the matching branch wherever it appears -- called directly, nested in another
model, or validated through a ``TypeAdapter``.

Two mechanisms, because no single one reaches all four. The core-schema hook
covers every path pydantic validates THROUGH; ``__new__`` covers ``Base(**data)``,
which allocates the object before validation runs and so cannot be reached by a
schema at all. For a long stretch only the hook was here, and the sentence above
was false of its last clause: direct construction returned a loose base whose
serializer could not serialize it.

Overriding ``model_validate`` reaches only one of the four. Pydantic validates a
nested field and a ``TypeAdapter`` through the CORE SCHEMA, so an override is
invisible on both paths -- and most roots with branches are nested object
schemas, which is where the response side's override left a document satisfying
no branch to parse as the loose base.

WHICH CLASS GETS THE BRANCHES' SCHEMA is decided by a fact about the class, not
by a registration: the base is the class that DECLARES ``_branch_models``. A
branch inherits that method and must get its own shape back; so must a
refinement declared elsewhere, and the canonical layer declares exactly one.

Membership is not enough for that test. ``cls in branches`` -- the guard the
response side's ``model_validate`` override used, correctly, for years -- admits
both "is a branch" and "is an unrelated subclass", and only the second matters
once the schema itself is being replaced. A guard sufficient for one mechanism
is silently wrong for another.

The branches subclass the base, so they do not exist while the base is being
built. The hook returns the base's own schema then, and the declaring module's
``model_rebuild(force=True)`` after the branches are defined is what installs
the union. That rebuild resolves a forward reference the class cannot name at
declaration time, in the module that declares it -- which is what
``model_rebuild`` is for, and is not the same thing as a foreign module patching
a field onto a class and forcing a rebuild to make the patch take.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, cast

from pydantic import GetCoreSchemaHandler, TypeAdapter, WrapValidator
from pydantic_core import CoreSchema

from adcp.types._conditions import name_the_combinator

if TYPE_CHECKING:
    from pydantic import BaseModel

__all__ = ["BranchDispatchMixin"]


class BranchDispatchMixin:
    """Give the declaring class its branches' core schema."""

    @classmethod
    def _branch_models(cls) -> tuple[type, ...]:
        """The branch classes this root resolves to.

        A base overrides this. The default is empty so a class that mixes this
        in without declaring branches keeps its own shape.
        """
        return ()

    @classmethod
    def _branch_combinator(cls) -> str:
        """The JSON Schema keyword a refusal names: ``anyOf`` or ``oneOf``.

        ``core/error.json`` requires every ``issues[]`` entry to carry a keyword
        drawn from the JSON Schema vocabulary. A document satisfying no branch
        fails each branch at FIELD validation, so pydantic reports ``missing``
        and nothing names the root's combinator -- and ``missing`` is outside
        that vocabulary.

        The union this hook builds carries the wrapper that supplies it. An
        earlier version of this mixin built a BARE union and the keyword was
        silently lost on every path through the base, while the per-branch
        residual checks still named it -- so the refusals that named a keyword
        were the ones that needed it least.
        """
        return "anyOf"

    def __new__(cls, **data: Any) -> Any:
        """Construct the branch the document satisfies, not the base.

        The core-schema hook below covers every path pydantic validates THROUGH:
        a nested field, a ``TypeAdapter``, ``model_validate``. It cannot cover
        ``Base(**data)``, because by the time validation runs the object has
        already been allocated -- ``BaseModel.__init__`` validates with
        ``self_instance=self``, so a successful direct construction left a BASE
        instance whose serializer is the union of its branches. That object is
        not merely loosely typed: the union serializer matches no branch, falls
        back to inferring a model, re-enters the same union, and recurses.
        Measured on the canonical create request --
        ``model_dump(mode="python")`` survives the fallback, ``mode="json"``
        raises ``ValueError: Circular reference detected (id repeated)`` and
        ``model_dump_json()`` raises ``PydanticSerializationError``
        (salesagent-setka). Choosing the class is the only place that can be
        fixed, so it is fixed here.

        Gated on the same question the hook asks -- does this class DECLARE
        ``_branch_models`` -- so a branch, and a refinement declared elsewhere,
        construct themselves. One identity question, one place.

        CEILING: direct construction validates TWICE. ``__new__`` has to choose
        the branch before ``type.__call__`` can run that branch's ``__init__``,
        and that ``__init__`` validates the same payload again into the object
        returned here. It is idempotent, and ``model_validate`` remains
        single-pass, so the cost falls on the rarer path. Removing it needs
        pydantic to expose branch selection without building an instance.
        """
        if not data or "_branch_models" not in cls.__dict__:
            # No data: ``model_construct``, ``copy.deepcopy`` and unpickling all
            # call ``cls.__new__(cls)`` and must get a blank instance rather than
            # a validation of ``{}``. Not the declaring class: a branch keeps its
            # own construction, for the same reason it keeps its own schema.
            return super().__new__(cls)
        try:
            branches = cls._branch_models()
        except NameError:
            # The branches subclass this class, so a construction attempted while
            # the module is still executing has none to choose from yet.
            return super().__new__(cls)
        if not branches:
            return super().__new__(cls)
        # The base's own validator IS the union the hook installed, so this asks
        # the same question the other three paths ask, with the same refusal --
        # including the root's combinator keyword on a document satisfying no
        # branch. Cast because the mixin is a plain class: it has no pydantic
        # attributes of its own and is only ever mixed into a model, which is
        # the one assumption this file makes about its host.
        host = cast("type[BaseModel]", cls)
        return host.__pydantic_validator__.validate_python(data)

    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        if "_branch_models" not in cls.__dict__:
            # A branch, or a refinement elsewhere. Its own shape, not the union.
            # This is also why building the union cannot re-enter here: a branch
            # does not declare the method, so asking it for its schema returns
            # immediately. A re-entry guard was written for that case and then
            # removed, because removing it does not recurse -- the structural
            # test already prevents what the guard was watching for.
            return handler(source)
        try:
            branches = cls._branch_models()
        except NameError:
            # The branches subclass this class, so they are not defined yet. The
            # declaring module's model_rebuild(force=True) runs this again.
            return handler(source)
        if not branches:
            return handler(source)
        union: Any = branches[0]
        for branch in branches[1:]:
            union |= branch
        wrapped = Annotated[
            union,
            WrapValidator(name_the_combinator(cls._branch_combinator(), branches)),
        ]
        return TypeAdapter(wrapped).core_schema
