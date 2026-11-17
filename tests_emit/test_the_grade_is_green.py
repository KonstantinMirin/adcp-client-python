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


def _pair_ids() -> list[tuple[int, str]]:
    """``(index into found, "document#pointer")`` for every pair, for ``parametrize``.

    **PER PAIR AND NOT PER DOCUMENT, because a group cannot split the document that is
    the long pole.**  Per-document groups took the grade from 430 s to 134 s and then
    stopped: only 10 of 16 workers did any work, because the tail is a single document
    whose own pairs are the expensive ones.  Measured, the heaviest hold
    ``protocol/get-adcp-capabilities-response.json`` 86 pairs, ``brand.json`` 68,
    ``core/format.json`` 56, ``core/async-response-data.json`` 47 -- so the work that
    could not be spread is concentrated in a handful of documents and splitting THEM is
    the remaining win.

    The index is the selector and the ``document#pointer`` is the id a reader sees.
    ``harness.pairs`` returns a stable order, so an index means the same pair on every
    worker; nothing is keyed on it beyond this call.

    THE COST OF SPLITTING is memo locality: ``Construction._memo`` is per WORKER, so
    pairs of one document landing on different workers rebuild that document's shared
    subtrees once per worker.  Whether that costs more than the balance buys is a
    measurement and not a guess -- if the wall clock rises, per-document was right and
    this goes back.
    """
    from codegen import harness
    from codegen.emit import PACKAGE

    found, _ = harness.pairs(importlib.import_module(PACKAGE))
    #: The CLASS is in the id because a pointer is not unique: §4 emits one class per
    #: SUBJECT and a union's base and branches all stamp the same node, so
    #: ``core/creative-representation.json#/allOf/0`` names both
    #: ``CreativeRepresentationFormatId`` and ``...FormatKind``.  Without it pytest
    #: disambiguates by appending ``_0``, which made the failing set differ from the
    #: artifact's by one row and said nothing about why.
    return [
        (i, f"{p.ref.document}{p.ref.pointer} {getattr(p.model, '__name__', '?')}")
        for i, p in enumerate(found)
    ]


def pytest_generate_tests(metafunc: Any) -> None:
    """Parametrise at COLLECTION and not at import.

    Called once per worker, after ``conftest`` has bound the fresh tree -- which is the
    whole reason it is a hook: a module-scope ``_documents()`` runs during IMPORT, binds
    ``adcp.types._schemas`` before ``fresh._bound()`` has had its say, and the suite
    refuses to collect at all with "the generated half of adcp.types is already bound
    outside the fresh tree".  Measured: the module would not collect, and the gate beside
    it collected fine, which is what said the fault was here and not environmental.
    """
    if "pair_index" in metafunc.fixturenames:
        #: No ``xdist_group``: every pair is independent, so ``--dist load`` may place
        #: each one anywhere.  A group per document was the previous shape and is what
        #: pinned a document's pairs to one worker.
        metafunc.parametrize(
            "pair_index",
            [pytest.param(i, id=name) for i, name in _pair_ids()],
        )


#: **THE THREE CHECKS THAT ARE THE CONTRACT**, in the owner's words (2026-11-17):
#: *"All we need to make sure is that schema valid and schema invalid payload are being
#: validated by the emitted Python classes and that valid Python class instantiated and
#: filled produces the valid JSON serialization when it is being dumped. That's it."*
#:
#: So the gate is three assertions per pair and not six:
#:
#:     accepts   a payload the DOCUMENT admits, the class admits
#:     refuses   a payload the DOCUMENT refuses, the class refuses
#:     dump      an instance's dump is valid against the document
#:
#: **AND ROUND-TRIP BYTE-IDENTITY IS EXPLICITLY NOT THE TEST**, also his words -- *"we do
#: not test round trip without changing bytes because that would be impossible to meet"*.
#: `dump` asserts the dump is document-VALID, which is a different and achievable claim.
#:
#: `widening`, `undeclared` and `admits` are the approximation bookkeeping -- they grade
#: whether a DECLARATION matches the direction a class differs from its document. They
#: are measured and reported by :func:`test_this_pair_has_no_undeclared_approximation`
#: below, which is deliberately NOT this gate: a pair can satisfy the contract above
#: while its declaration is mislabelled, and conflating the two is how 19 bookkeeping
#: rows came to be quoted as emission defects.
CONTRACT = ("accepts", "refuses", "dump")

#: The approximation bookkeeping, graded apart from the contract.
BOOKKEEPING = ("widening", "undeclared", "admits")


def _cells(row: str) -> dict[str, str]:
    """A row's cells, read as the artifact spells them.

    `csv.DictReader` over the real header is the only reader for `verdicts.tsv`, and
    this is its per-row equivalent: a `split("=")` by hand answered 0 graded pairs for a
    file holding 2,550 of them, minutes before a correct read answered 101. A hand-rolled
    reader that is wrong is worse than no reader, because it reports.
    """
    return dict(field.split("=", 1) for field in row.split("\t") if "=" in field)


def test_this_pair_meets_the_contract(pair_index: int, setup: Any) -> None:
    """A document-valid payload is accepted, a document-invalid one refused, the dump valid.

    :data:`CONTRACT`'s three checks, and **absent is not a pass** -- a check never put to
    this pair is a fact about the draw and not evidence about the class, which is what
    `verdicts.tsv`'s own header says.

    One test per PAIR, so ``pytest -n auto`` may place any pair on any worker.
    """
    from codegen.__main__ import graded_rows

    found, identity_of, construction, formats = setup
    rows = graded_rows(
        [found[pair_index]],
        identity_of=identity_of,
        construction=construction,
        formats=formats,
    )
    bad = []
    for row in rows:
        cells = _cells(row)
        for check in CONTRACT:
            #: The cell's VALUE, which is `pass`, `fail:<cause>` or `absent:<cause>`.
            #: Comparing it to the check's NAME is the mistake that made every one of
            #: 2,609 pairs fail on this gate's first run -- a hand-rolled reader being
            #: wrong in the commit that exists to stop hand-rolling readers.
            if cells.get(check, "") != "pass":
                where = f"{cells.get('document', '?')}{cells.get('pointer', '')}"
                bad.append(f"{where}: {cells.get(check)}")
    assert not bad, f"{len(bad)} contract failures:\n" + "\n".join("  " + b[:220] for b in bad[:10])


def test_this_pair_has_no_undeclared_approximation(pair_index: int, setup: Any) -> None:
    """:data:`BOOKKEEPING`, graded APART from the contract and for a different reason.

    These three ask whether a class that differs from its document carries a DECLARATION
    saying so, and in which direction. A failure here is a mislabelled or missing
    declaration, not a payload the class gets wrong -- so it must not be able to redden
    the contract gate, and the contract gate must not be able to hide it.
    """
    from codegen.__main__ import graded_rows

    found, identity_of, construction, formats = setup
    rows = graded_rows(
        [found[pair_index]],
        identity_of=identity_of,
        construction=construction,
        formats=formats,
    )
    bad = []
    for row in rows:
        cells = _cells(row)
        for check in BOOKKEEPING:
            #: **ONLY AN EXPLICIT `fail`**, because `absent` is the CORRECT state here
            #: and not a gap: `widening=absent:no_declarations` is what a pair with no
            #: declarations must say, so counting absent would redden 2,468 of 2,609
            #: pairs for being ordinary. That is the opposite of :data:`CONTRACT`, where
            #: a check never put to the pair is no evidence about the class and so is
            #: not a pass. Verified against the artifact: 22 pairs fail here, 14 fail
            #: the contract.
            if (cells.get(check) or "").startswith("fail"):
                where = f"{cells.get('document', '?')}{cells.get('pointer', '')}"
                bad.append(f"{where}: {check}={cells.get(check)}")
    assert not bad, f"{len(bad)} bookkeeping failures:\n" + "\n".join(
        "  " + b[:220] for b in bad[:10]
    )
