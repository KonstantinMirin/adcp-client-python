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
    on_our_base = sorted(n for n, o in mine.items() if issubclass(o, base.AdCPBaseModel))
    assert not on_our_base, (
        f"adcp.types.{module} declares {on_our_base} on AdCPBaseModel; upstream's machinery "
        "has no schema subject and putting it on our base invents one"
    )
    for name, obj in mine.items():
        assert getattr(obj, "__adcp_schema__", None) is None, (
            f"adcp.types.{module}.{name} carries __adcp_schema__ and no document states it"
        )


def test_the_client_types_live_in_the_sdk_namespace_and_not_in_the_type_layer() -> None:
    """`AgentConfig`, `Protocol`, `TaskResult`, `TaskStatus`, `DebugInfo` describe the LIBRARY.

    They are absent from the schema for the honest reason that the schema describes the
    PROTOCOL: `AgentConfig` is `id, agent_uri, protocol, auth_token`, `Protocol` is which
    transport the client speaks, `TaskResult` is the SDK's return wrapper and `DebugInfo` is
    its diagnostics.  Upstream filed all five under `types/`, which is what makes
    `adcp.types.core` look like a naming collision when it is a LAYERING one.  They are
    restored to the SDK's own namespace so that `adcp.types` stays schema-derived.
    """
    client = importlib.import_module("adcp._client_types")
    for word in ("AgentConfig", "Protocol", "TaskResult", "TaskStatus", "DebugInfo"):
        assert isinstance(getattr(client, word, None), type), f"{word} is not here"
    types = importlib.import_module("adcp.types")
    assert not any(
        getattr(types, "__dict__", {}).get(w) is getattr(client, w)
        for w in ("TaskResult", "AgentConfig")
    ), "a client type is bound in adcp.types' own namespace, which is the layer it is not in"
