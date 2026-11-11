"""Upstream's restored MACHINERY is not, and cannot become, a type of ours.

`survey/upstream_machinery.py` decides WHICH of upstream's hand-written files come back
(upstream's own two readings: a generation header, and source importers against test
importers).  This file is the other half of that decision -- what must stay TRUE of them
once they are here -- and there are two things.

**THEY ARE ABSENT FROM THE POPULATION THE THREE CHECKS RANGE OVER.**  `./check`'s three
numbers, the emit record and the domain-surface gate are all stated over what the COMPILER
wrote, keyed on `emit.surface`; a restored file is written by nobody and read off no
document, so a fresh tree must not carry it.  If one ever appeared there it would be a
document's module by the only test the suite has, and a figure that says "1,059 emitted"
would be counting a file upstream hand-wrote.

**AND NO CLASS THEY DECLARE IS A CLASS OF OURS.**  Upstream's conventions are not ours and
must not be made so: measured over `4ed0bce87`, their `core.py` declares 15 plain
`BaseModel`s, `registry.py` 107 `RegistryBaseModel`s and 47 `Enum`s, `canonical_creative.py`
33 `CanonicalBoundaryModel`s, and `base.py` a `RootModel[_RootT]` -- which this project
deliberately never emits, because a `RootModel` cannot be subclassed to change `extra`.
Folding any of them onto `AdCPBaseModel` would invent a schema subject for something that
has none, so the gate is that they are NOT on our base and NOT the object any domain
surface exports.  The defect this prevents is a hand-written `BaseModel` reachable from
`adcp.types` that a consumer cannot tell from an emitted class.

The population is the TSV's own rows and not a list here, so a module restored or dropped
later is graded or stops being graded in the same breath.
"""

from __future__ import annotations

import csv
import importlib
import types as types_module
from pathlib import Path

import pytest

import fresh

REPO = Path(__file__).resolve().parent.parent
TABLE = REPO / "survey" / "upstream-machinery-9.6.1.tsv"


def _rows() -> list[dict[str, str]]:
    text = [ln for ln in TABLE.read_text().splitlines() if not ln.startswith("#")]
    return list(csv.DictReader(text, delimiter="\t"))


def _restored() -> list[str]:
    """Every module the TSV records as upstream's OWN FILE, byte for byte.

    `restored` is byte identity against upstream's commit and not "a file is at the path",
    which is the distinction the gate below needs and the one this test caught the survey
    getting wrong: our EMITTED domain surfaces occupy `core`, `creative`, `media_buy`,
    `protocol` and `signals`, so a column that said "present" reported five modules of ours
    as upstream's machinery and this gate then demanded a fresh emit not write them.  An
    adapter module of ours at such a path is `adapter-module` by its own marker, which is the
    predicate every other survey reads.
    """
    return [r["module"] for r in _rows() if r["here_now"] == "restored"]


def test_the_classification_table_is_the_population_and_is_not_empty() -> None:
    rows = _rows()
    assert rows, f"{TABLE} carries no rows; the gate below would range over nothing"
    assert _restored(), (
        "no module of upstream's is present as upstream's, so either the restoration was "
        "reverted or the table no longer describes this tree"
    )


@pytest.mark.parametrize("module", _restored())
def test_a_restored_module_is_absent_from_the_tree_the_compiler_writes(module: str) -> None:
    """A fresh emit must not carry it, or `./check`'s population would include it."""
    rel = Path(*module.split(".")).with_suffix(".py")
    written = Path(fresh._materialised()) / rel  # noqa: SLF001 -- the run's own tree
    assert not written.exists(), (
        f"a fresh tree carries {rel}, so the compiler wrote a file upstream hand-wrote and "
        "every figure stated over the emitted population now counts it"
    )


@pytest.mark.parametrize("module", _restored())
def test_no_class_a_restored_module_declares_is_a_class_of_ours(module: str) -> None:
    """Not on our base, and not the object a domain surface exports."""
    import adcp.types._base as base

    held = importlib.import_module(f"adcp.types.{module}")
    mine = {
        name: obj
        for name, obj in vars(held).items()
        if isinstance(obj, type) and getattr(obj, "__module__", "") == held.__name__
    }
    #: **INVENTING A SUBJECT IS LANDING ON OUR BASE FROM NOWHERE, AND EXTENDING ONE IS
    #: NOT.**  This read ``not issubclass(o, AdCPBaseModel)``, which is the property for a
    #: restored HELPER -- every one here today -- and the wrong one for a restored SUBCLASS
    #: LAYER.  ``canonical_creative`` WAS one: upstream's canonical boundary was written as
    #: ``class Product(_LegacyProduct, CanonicalBoundaryModel)`` where ``_LegacyProduct`` IS
    #: ``adcp.types.domains.core.product.Product``, so its classes were on our base BY
    #: CONSTRUCTION and the document behind each was ours.  Measured over that file at the
    #: time: 36 classes, 32 on our base, and **0** of those 32 reaching it without an
    #: emitted ``_schemas`` class in the MRO -- which is why the predicate is what it is.
    #: That file is deleted (``adcp-client-python-2f52``), and the clause it forced stays:
    #: a class on our base must have one of our document classes behind it, and a class
    #: that lands there from nowhere still fails.
    invented = sorted(
        n
        for n, o in mine.items()
        if issubclass(o, base.AdCPBaseModel)
        and not any(getattr(b, "__module__", "").startswith(base.PACKAGE) for b in o.__mro__[1:])
    )
    assert not invented, (
        f"adcp.types.{module} declares {invented} on AdCPBaseModel with no emitted class "
        "behind them; upstream's machinery has no schema subject of its own and landing on "
        "our base without one of ours in the MRO invents one"
    )
    for name, obj in mine.items():
        own = obj.__dict__.get("__adcp_schema__")
        assert own is None, (
            f"adcp.types.{module}.{name} DECLARES __adcp_schema__ and no document states it"
        )


def test_the_client_types_live_in_the_sdk_namespace_and_not_in_the_type_layer() -> None:
    """`AgentConfig`, `Protocol`, `TaskResult`, `TaskStatus`, `DebugInfo` describe the LIBRARY.

    They are absent from the schema for the honest reason that the schema describes the
    PROTOCOL: `AgentConfig` is `id, agent_uri, protocol, auth_token`, `Protocol` is which
    transport the client speaks, `TaskResult` is the SDK's return wrapper and `DebugInfo` is
    its diagnostics.  Upstream filed all five under `types/`, which is what makes
    `adcp.types.core` look like a naming collision when it is a LAYERING one.  They are
    restored to `adcp.core` -- the SDK's own PUBLIC namespace, which is the path upstream's
    own `tests/test_public_api.py::test_client_types_are_exported` already requires them at
    (`adcp.AgentConfig`, `adcp.Protocol`) -- so that `adcp.types` stays schema-derived.

    **THE ASSERTION IS ON OBJECT IDENTITY AND NEVER ON THE WORD, because eight of these
    words are ALSO emitted and the rule is about which class answers.**  `TaskStatus` is
    the case that separates them: `adcp.types.TaskStatus` is the nine-member enum from
    `enums/task-status.json` and `adcp.core.TaskStatus` is upstream's five-member one, and
    `Policy`, `PolicyExemplars`, `PolicyHistory`, `PolicyRevision`, `PolicySummary`,
    `ResolvedBrand` and `ResolvedProperty` each name a `registry` class of ours as well.  A
    gate written on the WORD would have to either forbid seven emitted names or pass
    vacuously; written on identity it says the one true thing -- no object `adcp.core`
    defines is what the flat type surface hands back.

    `adcp.types.core` is EXEMPT by construction and deliberately so: 231 module-scope asks
    in upstream's own source and tests name that path for these classes, and the twenty-one
    `X as X` lines there are the compatibility seam that keeps them resolving.  The seam
    re-exports; it does not declare, which is what
    `test_the_public_domain_path.py::test_the_composition_names_no_type_of_its_own` reads.
    """
    client = importlib.import_module("adcp.core")
    for word in ("AgentConfig", "Protocol", "TaskResult", "TaskStatus", "DebugInfo"):
        assert isinstance(getattr(client, word, None), type), f"{word} is not here"

    #: Every class and function `adcp.core` DEFINES, off the loaded module rather than its
    #: text, so a name upstream adds in a later release joins the population with nothing
    #: here edited.  Constants are dropped because identity does not discriminate an int.
    defined = {
        name: obj
        for name, obj in vars(client).items()
        if not name.startswith("_")
        and getattr(obj, "__module__", None) == "adcp.core"
        and isinstance(obj, type | types_module.FunctionType)
    }
    assert len(defined) >= 19, (
        f"adcp.core defines only {len(defined)} classes and functions, so this gate has "
        "lost its subject; upstream's restored machinery is twenty-one public names"
    )

    surface = importlib.import_module("adcp.types")
    leaked = sorted(
        name for name, obj in defined.items() if getattr(surface, name, None) is obj
    )
    assert not leaked, (
        f"the flat type surface hands back adcp.core's own object for {leaked}; "
        "adcp.types is the compiler's namespace and these describe the LIBRARY, so a "
        "consumer writing `from adcp.types import " + (leaked[0] if leaked else "X") + "` "
        "would get a hand-written class where a schema-derived one is the contract"
    )
