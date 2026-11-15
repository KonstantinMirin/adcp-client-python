"""The grade itself, as a pytest run -- one test per DOCUMENT, so xdist spreads it.

**WHY THIS EXISTS AND WHAT IT REPLACES.**  ``./verify`` grades all 2,609 pairs in one
process in ~430 s and writes ``verdicts.tsv`` beside ``verify.json``;
``test_the_verdicts_are_green.py`` then READS that artifact and fails per not-pass row.
Three steps with a human between them -- and the scaffolding that keeps them honest
(``.gitattributes merge=ours``, the recorded provenance head, the freshness clause, the
"re-take the measurement" commits) exists ONLY because the grade is a file rather than a
test run.

The cost is what forced that shape, and the cost is addressable.  Measured on this tree:

    harness.pairs                4.3 s     (2,609 pairs over 1,020 documents)
    catalogue.admitted_identities 5.7 s
    bundle.portable              0.1 s
    ---------------------------------
    setup                       10.1 s     of ~430 s

So 98% of the grade is the per-pair loop and 2% is setup a worker can pay once.  That is
exactly the shape ``pytest -n auto --dist loadgroup`` wants.

**THE PRE-CACHED PAYLOAD IS WHY THE FIXTURE IS SESSION-SCOPED.**
:class:`codegen.verify.witness.Construction` memoises every built value in ``_memo``,
keyed ``(document, pointer, stack)`` -- and its own docstring says why that is not an
optimisation: *"One answer per node per document, keyed on the pointer, is what makes the
cost linear, the budget unnecessary and the cycle closed."*  A per-test Construction would
rebuild every shared subtree once per document and the cost would stop being linear.  One
per worker, warmed across every document that worker grades, is the whole point.

``records`` likewise holds EVERY document and not the worker's share: a pair in one
document reaches another through a ``$ref``, so a partial record set would answer
``no_witness`` for a reason that is the harness's and not the document's.

**ONE DERIVATION, TWO CALLERS.**  ``codegen.__main__.graded_rows`` is the per-pair step;
``grade`` calls it with no filter and writes the artifact, this module calls it once per
document.  Neither is a copy of the other, so they cannot drift -- and the claim is
asserted by diffing ``verdicts.tsv`` across the extraction rather than by this sentence.

**ABSENT IS NOT A PASS**, which is the one thing a reader of this file must not forget.
A row whose check never ran is reported here as a failure of coverage, not skipped: the
verdict table's own header says *"absent is NOT a pass -- it is the check that was never
put to this pair"*, and five separate repairs in this project's history lowered the
not-pass count by moving pairs into ``absent``.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import fresh  # noqa: F401  -- binds the generated half before anything imports it
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _setup() -> tuple[Any, Any, Any, Any]:
    """``(found, identity_of, construction, formats)`` -- the grade's own 10.1 s of setup.

    Built exactly as ``codegen.__main__.grade`` builds it, through the same calls, so a
    document graded here is graded against the same records, identities and construction
    the artifact-writing path uses.
    """
    from codegen import bundle, catalogue, harness, patch
    from codegen.emit import PACKAGE
    from codegen.verify import witness

    #: EVERY call below is ``grade``'s own, with its own arguments.  Two of them were
    #: wrong in the first draft and the per-document rows disagreed with the artifact at
    #: once: ``bundle.read`` where ``grade`` uses ``bundle.record(bundle_dir, document,
    #: known)``, and ``harness.pairs(schemas)`` without the ``path=`` that binds THIS
    #: tree.  A setup that is merely similar grades a different thing.
    bundle_dir = patch.for_build(ROOT / "schemas" / "cache" / "3.2")
    tree = ROOT / "src" / "adcp" / "types" / "_schemas"
    schemas = importlib.import_module(PACKAGE)
    found, _unimportable = harness.pairs(schemas, path=[str(tree.resolve())])
    identities = catalogue.admitted_identities(bundle_dir, stated=harness.stated_instances)

    def identity_of(document: str, pointer: str) -> dict:
        return {"document": document, "pointer": pointer, "admits": identities[document]}

    known = set(bundle.portable(bundle_dir))
    records = {}
    for document in sorted({p.ref.document for p in found}):
        record = bundle.record(bundle_dir, document, known)
        if isinstance(record, dict):
            records[document] = record
    return found, identity_of, witness.Construction(records), harness.FORMAT_STRATEGIES


@pytest.fixture(scope="session")
def setup() -> tuple[Any, Any, Any, Any]:
    """The setup, once per WORKER -- see this module's docstring on ``_memo``."""
    return _setup()


def _documents() -> list[str]:
    """Every document the tree states a pair for, for ``parametrize`` at collection.

    Costs ``harness.pairs`` once per worker at import.  That is 4.3 s against a per-pair
    loop of ~420 s, and it is what buys one test per document rather than one test for
    the whole tree.
    """
    from codegen import harness
    from codegen.emit import PACKAGE

    found, _ = harness.pairs(importlib.import_module(PACKAGE))
    return sorted({p.ref.document for p in found})


def pytest_generate_tests(metafunc: Any) -> None:
    """Parametrise at COLLECTION and not at import.

    Called once per worker, after ``conftest`` has bound the fresh tree -- which is the
    whole reason it is a hook: a module-scope ``_documents()`` runs during IMPORT, binds
    ``adcp.types._schemas`` before ``fresh._bound()`` has had its say, and the suite
    refuses to collect at all with "the generated half of adcp.types is already bound
    outside the fresh tree".  Measured: the module would not collect, and the gate beside
    it collected fine, which is what said the fault was here and not environmental.
    """
    if "document" in metafunc.fixturenames:
        metafunc.parametrize(
            "document",
            [pytest.param(d, marks=pytest.mark.xdist_group(name=d)) for d in _documents()],
        )


def test_every_pair_of_this_document_passes(document: str, setup: Any) -> None:
    """Every pair of ``document`` passes all six checks, and none of them is absent.

    One test per document and a GROUP per document, so ``--dist loadgroup`` may place
    them on any worker: the single global ``GRADED_REPORTS_GROUP`` is what pinned the
    whole grade to one worker before this.
    """
    from codegen.__main__ import graded_rows

    found, identity_of, construction, formats = setup
    rows = graded_rows(
        found,
        identity_of=identity_of,
        construction=construction,
        formats=formats,
        only=document,
    )
    bad = [r for r in rows if "\tverdict=pass" not in r]
    assert not bad, f"{len(bad)} of {len(rows)} pairs:\n" + "\n".join(
        "  " + r.split("\t", 3)[-1][:220] for r in bad[:10]
    )
