"""What the dispatch hook does with an already-CONSTRUCTED instance.

The deleted ``ResponseArmDispatchMixin.model_validate`` opened with
``if isinstance(obj, cls): return obj`` -- a pass-through for an instance. The
hook that replaced it installs the branches' union as the class's CORE SCHEMA,
so pydantic decides that, from ``revalidate_instances``. Measured, the two agree
on a branch instance, a sibling branch's instance, a refinement subclass, and a
nested field, and they differ on exactly one input: an instance of the LOOSE
BASE, which the override returned by identity and the hook refuses.

That difference shipped unnamed. The removal commit's message states it in
text -- "identity for an instance of the LOOSE BASE" -- and text is not a test,
so nothing failed when the override went away. This file is the missing half.

It grades two things, and the SECOND is the durable one:

* an instance of the loose base is refused by its own name, over every root the
  hook dispatches;
* ``revalidate_instances`` is pydantic's default on every generated class.

The agreement on the other four inputs is not a property of this codebase. It
follows from pydantic's default ``'never'``, under which a model schema accepts
an existing instance of its own class without revalidating -- and NOTHING here
states that default. Set ``revalidate_instances='always'`` on a root's BRANCHES
and the agreement is gone, silently; set it on the root itself and nothing
changes, because the root's core schema is the union and the branches are its
members. So the default is pinned here rather than relied upon, over every
generated class rather than over the bases, because the whole reason this file
exists is that a behavioural difference reached main with no test naming it.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

# Importing the consolidated module is what loads every generated domain module,
# and the canonical layer is a separate import. The derivation walks what is
# loaded, so a population derived before these imports is empty.
import adcp.types._generated  # noqa: F401
import adcp.types.canonical_creative  # noqa: F401
from adcp.types.base import AdCPBaseModel
from tests.test_branch_dispatch_on_every_path import _roots_with_branches

#: Pydantic's default, and the fact the four agreeing cases rest on. Named here
#: so the assertion reads as a claim about this codebase rather than a repeat of
#: the library's documentation: nothing in ``adcp`` sets this, so nothing in
#: ``adcp`` currently prevents it from changing.
PYDANTIC_DEFAULT_REVALIDATION = "never"


def _generated_models() -> list[type[BaseModel]]:
    """Every generated model class, by (module, qualname) identity.

    Neither half of that identity is sufficient alone. An exported name hides
    aliases -- ``adcp.types.CreativeAsset`` is the canonical refinement while
    ``adcp.types._generated.CreativeAsset`` is the base over branches -- and
    ``__qualname__`` alone collapses two distinct classes that share a name:
    ``CreateMediaBuyRequest`` names one base in the domain tree and another in
    the canonical layer, and counting by qualname loses one of them.
    """
    import sys

    found: dict[tuple[str, str], type[BaseModel]] = {}
    for module in list(sys.modules.values()):
        if module is None or not getattr(module, "__name__", "").startswith("adcp.types"):
            continue
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, BaseModel):
                found[(value.__module__, value.__qualname__)] = value
    return list(found.values())


def test_an_instance_of_the_loose_base_is_refused_by_its_own_name() -> None:
    """The one input on which the hook and the deleted pass-through disagree.

    The override returned this object: a branch and a refinement both subclass
    the base, so ``isinstance(obj, cls)`` was true for them AND for an instance
    of the base itself. The hook refuses it, because the base is not a member of
    its own branches' union -- the union is what its core schema now is.

    The refusal is ``model_type`` and nothing else. It does NOT name the root's
    combinator, which the document path does name and which
    ``core/error.json`` requires of an ``issues[]`` keyword; that gap is
    salesagent-jrec5 and is deliberately not asserted here, so this test pins
    what is true today rather than failing for a second reason.
    """
    roots = _roots_with_branches()
    assert roots, "the derivation selected no root to grade"

    for name, root in sorted(roots.items()):
        instance = root.model_construct()
        with pytest.raises(ValidationError) as caught:
            root.model_validate(instance)
        assert {entry["type"] for entry in caught.value.errors()} == {"model_type"}, (
            f"{name} refused an instance of itself with "
            f"{sorted({e['type'] for e in caught.value.errors()})}, not {{'model_type'}}"
        )


def test_a_branch_instance_passes_through_the_base_by_identity() -> None:
    """The four inputs on which the hook and the pass-through AGREE.

    Stated as a test because the agreement is what made the override's deletion
    safe, and because it is the half that moves if ``revalidate_instances``
    does. Each object is built with ``model_construct``: an unvalidated instance
    is what separates "passed through" from "revalidated", and a valid one
    cannot -- it comes back either way.
    """
    roots = _roots_with_branches()
    assert roots, "the derivation selected no root to grade"

    for name, root in sorted(roots.items()):
        branches = root._branch_models()  # type: ignore[attr-defined]
        assert branches, f"{name} declares _branch_models but names no branch"

        for label, instance in (
            ("its own branch", branches[0].model_construct()),
            ("a sibling branch", branches[-1].model_construct()),
            (
                "a refinement subclass",
                type(f"{branches[0].__name__}Refinement", (branches[0],), {}).model_construct(),
            ),
        ):
            returned = root.model_validate(instance)
            assert returned is instance, (
                f"{name} did not return {label} by identity; it returned {type(returned).__name__}"
            )

        class Holder(AdCPBaseModel):
            payload: root  # type: ignore[valid-type]

        nested = branches[0].model_construct()
        assert Holder.model_validate({"payload": nested}).payload is nested, (
            f"{name} nested in another model's field did not keep the instance"
        )


def test_the_identity_pass_through_rests_on_a_pydantic_default_nothing_here_states() -> None:
    """Pin ``revalidate_instances``, because the agreement above is its consequence.

    Not one generated class sets it, and ``AdCPBaseModel`` does not either, so
    there is nothing to inherit: the value is pydantic's ``'never'``. Were a
    config change to make it ``'always'`` or ``'subclass-instances'``, every
    identity assertion in this file would become false and the hook would
    revalidate objects the deleted override passed through -- which is a
    behaviour change inside a config edit, the same shape as the one this file
    was written for.

    Which classes govern that is not the obvious half, and it is measured:
    setting ``revalidate_instances='always'`` on a BASE breaks this assertion
    and leaves the identity one passing, because the base's core schema IS the
    branches' union and it is the union MEMBERS that accept an instance. Setting
    it on the branches breaks both. So the population here is every generated
    model rather than the nineteen bases -- scoping it to the bases would pin
    the classes that do not decide the behaviour.
    """
    models = _generated_models()
    assert len(models) > 1000, f"the derivation found only {len(models)} generated models"

    setters = [
        f"{model.__module__}.{model.__qualname__}"
        for model in models
        if "revalidate_instances" in model.model_config
    ]
    assert not setters, (
        f"{len(setters)} generated class(es) set revalidate_instances, so the identity "
        f"pass-through this file asserts is no longer uniform: {sorted(setters)[:5]}"
    )
    assert "revalidate_instances" not in AdCPBaseModel.model_config, (
        "AdCPBaseModel now sets revalidate_instances, so the generated tree inherits a "
        "revalidation policy and the identity assertions above need re-measuring"
    )
    assert (
        BaseModel.model_config.get("revalidate_instances", PYDANTIC_DEFAULT_REVALIDATION)
        == PYDANTIC_DEFAULT_REVALIDATION
    ), "pydantic's own default for revalidate_instances moved"
