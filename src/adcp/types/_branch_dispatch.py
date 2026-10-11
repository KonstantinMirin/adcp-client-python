"""One hook: a base with branches validates as the branch a document satisfies.

A schema root whose branches partition the document space generates a base and
one class per branch. The base carries THIS hook, so the root's name resolves to
the matching branch wherever it appears -- called directly, nested in another
model, or validated through a ``TypeAdapter``.

Overriding ``model_validate`` reaches only the first of those. Pydantic
validates a nested field and a ``TypeAdapter`` through the CORE SCHEMA, so an
override is invisible on both paths -- and most roots with branches are nested
object schemas, which is where the response side's override left a document
satisfying no branch to parse as the loose base.

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

from typing import Any

from pydantic import GetCoreSchemaHandler, TypeAdapter
from pydantic_core import CoreSchema

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
        return TypeAdapter(union).core_schema
