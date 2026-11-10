"""Emit Python types for bundle documents named on the command line.

    python -m codegen --bundle schemas/cache/3.2 core/pagination-request.json

The committed tree is the same command over ``bundle.portable(BUNDLE)``: every
document of the bundle that can be emitted at all, derived from the bundle and never
listed by hand.  ``tests/test_emit.py``'s ``tree_population()`` is that reading and is
what regenerates the tree; it is NOT the union of the seven STEP selectors
(``population()``, whose predicates live in ``tests/populations.py``), because a step is
a phase of the rebuild and the tree is an ARTIFACT -- a population drawn from the phases
made the tree's contents depend on which documents an earlier run happened to reach
through a ``$ref`` (``adcp-client-python-10l.73``).
``docs/plan/architecture.md`` §5 puts the STEP predicates under ``tests/`` ("the
document-set predicates a step's result was stated over are the tests' business and live
under ``tests/``") and they are still there; the tree's population is the bundle's own
and is read by the one predicate this package already has.  So this package still names
no population, and the one the tree is graded against is the one the suite counts.

A document this command does not name is still emitted when a named one
REFERENCES it: a module cannot import a symbol from a module no run wrote, so
``emit`` walks ``$ref`` transitively and the run emits the closure.

**This module exists so that no module of the compiler is ever bound as
``__main__``.**  ``runpy`` binds the file it executes under the name
``__main__``, so ``python -m codegen.emit`` left ``codegen.emit`` importable
under its own name as a SECOND module object: one dispatch table, one decider
and one ``Refusal`` class per binding, and a class compared by identity across
that boundary is two classes.  The compiler's answer used to be a prohibition --
no module of the walk could name ``codegen.emit`` at all, so the per-node
decision and the constraint namer were carried on :class:`codegen.compiler.Module`
as callables, and the only way back to them was through a dataclass field.

The entry point is the structural fix: ``python -m codegen`` executes THIS file
as ``__main__``, this file holds no state the compiler reads, and every module of
the compiler is reached by import alone.  ``codegen.emit`` is therefore imported
once, by name, on every path -- so the decision can be reached by NAME, the
context carries data rather than functions, and the import rule shrinks to the
two boundaries that are about design (``tests/test_import_rule.py``).

The bundle directory is an argument (D9) and there is no default, so no version
literal can enter this package.  The output path is a function of the document
path (D1): ``core/pagination-request.json`` ->
``src/adcp/types/_schemas/core/pagination_request.py``.
"""

from __future__ import annotations

import argparse
import collections
import importlib
import sys
import time
from pathlib import Path

from adcp.types._base import KINDS, SchemaRef, schema_at
from codegen import bundle, catalogue, harness, held, keywords, patch, refusal
from codegen.emit import PACKAGE, TREE, emit, write
from codegen.verify import witness

#: Where the run writes §10's per-pair verdict table, relative to the tree it wrote.
#:
#: **Beside the tree and not inside it**, because ``emit.write`` PRUNES the tree: it
#: deletes every ``.py`` and ``.json`` under it that this run did not intend, so a table
#: written inside would survive only until the next run and would be deleted by a run over
#: part of the population.  Beside it, the path is a function of ``--tree`` exactly as the
#: modules are, so a run over a scratch tree leaves its table there and a run over the
#: committed tree leaves it where a reviewer and ``git diff`` can both reach it.
VERDICTS = "verdicts.tsv"

#: Seconds one pair of the verdict table may cost before the run gives up on it and writes
#: ``absent`` instead.  ``harness.within`` says what forces a bound at all; what forces THIS
#: number is the shape of the cost: a pair whose instances are held replays in 0.0 to 0.4 s,
#: and the pairs that exceed a budget of any size are the ones that DRAW -- 133 s to over
#: 2 h 57 m each.  There is nothing between the two, so the budget is small enough that the
#: whole table stays obtainable and large enough that no replayed pair can reach it.
BUDGET = 30


def grade(tree: Path, package: Path | None, bundle_dir: Path) -> tuple[str, int]:
    """Grade every pair of the tree this run WROTE, and return the table and the row count.

    **The run grades what it wrote, which is the whole of why this is here.**
    ``docs/plan/architecture.md`` §10: "one row per graded pair, written to a FILE by the
    run -- document, pointer, and each check's verdict -- because a figure that exists only
    in a terminal cannot be reviewed, and because a check that computed nothing shows up
    there as a blank column instead of as a pass."  The checks are
    ``codegen.harness``'s, the pairing is ``harness.pairs``, and the format is
    ``harness.verdict_table``; this function is only WHICH TREE and WHICH STORE, which is
    the run's half of the division ``tests/compared.py`` holds for the suite.

    **The tree is bound in FRONT of the committed one and nothing is copied.**  An emitted
    module says ``from adcp.types.constraints import StrMatchingA828669D`` -- an ABSOLUTE
    name -- so the modules have to be imported as ``adcp.types._schemas.*`` and cannot be
    loaded from a path.  Prepending ``tree`` to that package's ``__path__`` is what makes
    the import reach THIS run's output; prepending ``package`` to ``adcp.types.__path__``
    is what makes its aliases resolve through THIS run's ``constraints`` module.

    **A run that wrote no ``--package`` is graded anyway and the table says so.**  Without
    it the aliases resolve through the COMMITTED ``constraints`` module, so a module naming
    a constraint this run minted and the committed module lacks does not import -- and that
    is reported as a row per module with every verdict ``absent:unimportable``, which is
    exactly the blank column this artifact exists to make visible.  Suppressing the grade
    in that case would be a flag by another name.

    **The draws are REPLAYED from the committed floor** (``codegen.held``).  A cold grade of
    the population is 2,015.6 s against a 39.6 s warm pass, and the floor is in the
    repository precisely so that a fresh checkout pays no draw; a run that drew would make
    the artifact cost hours and nobody would run it.  ``harness.corpus_defect`` re-offers
    every held instance to the DOCUMENT before it counts, so a replayed verdict is not a
    remembered one, and the row's ``evidence`` column says which run paid.
    """
    import adcp.types

    schemas = importlib.import_module(PACKAGE)
    if package is not None:
        adcp.types.__path__.insert(0, str(package.resolve()))
    schemas.__path__.insert(0, str(tree.resolve()))
    found, unimportable = harness.pairs(schemas, path=[str(tree.resolve())])
    #: **WHAT A HELD VALUE IS KEYED ON: what the document ADMITS, never its bytes**
    #: (``adcp-client-python-lzzj.8``; ``catalogue.admitted_identities`` carries the
    #: measurement).  ``bundle.source_identities`` digested a document's raw bytes and its
    #: raw closure's, so an acceptance-preserving rewrite of the bundle moved every key and
    #: an improvement to the schema cost exactly as much as a regression -- measured at
    #: 1,054 of 1,054 identities moved by a patch whose every difference is a gained
    #: annotation, 854 of them by a trailing newline alone.  Over the same pair of bundles
    #: this reading moves 0 of 1,054.  ``harness.stated_instances`` is handed in because
    #: ``examples`` is a SOURCE OF INSTANCES and an admitted key alone would drop it; §9
    #: forbids the catalogue to the verifier, so the screen travels as an argument.
    identities = catalogue.admitted_identities(
        bundle_dir, stated=harness.stated_instances
    )
    formats = harness.FORMAT_STRATEGIES

    def identity_of(document: str, pointer: str) -> dict:
        """The pair's static identity -- the one thing the accepts store is keyed on."""
        return {"document": document, "pointer": pointer, "admits": identities[document]}

    #: **WHICH TREE a fixture's node is read from, per document.**  ``schema_at`` resolves a
    #: record through the module the class was emitted into, and a fixture is a node of some
    #: OTHER document than the pair's -- so the mapping has to exist, and it is
    #: ``harness.pairs``' own answer rather than an inference from a path.  A document with
    #: no pair of its own (nothing emitted for it) falls back to the imported package, which
    #: is the only tree such a caller has named.
    module_of = {p.ref.document: p.module for p in found}
    #: §8's FIXTURES FOR THE RUN, the same object and the same three readers the suite's
    #: grading pass builds (``tests/test_emit.fixtures``).  Without it the run's draw pays
    #: the unsubstituted node at every referring position -- ``adcp-client-python-gbw``:
    #: "the fixture derivation is in codegen/harness.py and the suite passes fixtures
    #: through it, but codegen/__main__.py was not wired to harness.Fixtures".
    fixtures = harness.Fixtures(
        read=lambda document: bundle.read(bundle_dir, document),
        node=lambda document, pointer: schema_at(
            SchemaRef(document, pointer), module=module_of.get(document)
        ),
        identity=identity_of,
        documents=frozenset(bundle.portable(bundle_dir)),
        corpus=held.STORE,
        custom_formats=formats,
    )
    #: **THE CONSTRUCTION, BUILT ONCE FOR THE WHOLE RUN** -- the row
    #: ``adcp-client-python-8bw4`` names, and the clause of the fifth target that was not
    #: met: *"the three checks ARE the grading path"*.  Before this, ``Construction``
    #: appeared nowhere in ``codegen/`` -- ``harness`` borrowed two validator readings from
    #: ``verify.witness`` and nothing else -- so every row this function writes was the
    #: SAMPLER's verdict, and the construction's coverage was a property of
    #: ``tests/test_witness_applied.py``: a test asserting construction COULD grade the
    #: tree, beside an artifact it did not grade.
    #:
    #: **ONE object for the run, which is §9's memoisation rule and not an optimisation.**
    #: "One answer per node per document, keyed on the pointer, is what makes the cost
    #: linear, the budget unnecessary and the cycle closed."  The memo lives on the
    #: instance, so a second ``Construction`` would pay the walk twice and -- worse --
    #: would report two readings of one number; ``tests/constructed.py`` holds exactly one
    #: per process for the suite and this is the run's half of that decision.
    #:
    #: **THE RECORDS ARE ``bundle.record``'s, and a document the record REFUSES is simply
    #: absent** -- which is graded rather than silent: such a pair gets no witness, says so
    #: in ``PairReport.witness_absent``, and falls through to the store exactly as a pair
    #: whose pointer the record does not hold does.
    #: **THE RECORDS THE PAIRING NAMES, AND NOT THE WHOLE BUNDLE'S.**  ``known`` stays the
    #: full portable set because that is what resolves a cross-document reference, but a
    #: record is BUILT only for a document some pair of this run names -- which is the
    #: whole bundle on a whole-bundle run and one document on a one-document run.  Measured
    #: before this line said ``sorted(known)``: a single-document run cost 1 m 20 s of
    #: which the emit was 10.9 s, because it built 1,059 records and walked them for a
    #: pairing of one.  ``Construction.__init__`` copies the mapping eagerly, so the
    #: shrinking has to happen here rather than behind a lazy mapping.
    known = set(bundle.portable(bundle_dir))
    records = {}
    for document in sorted({p.ref.document for p in found}):
        record = bundle.record(bundle_dir, document, known)
        if isinstance(record, dict):
            records[document] = record
    construction = witness.Construction(records)
    rows = [
        #: A row for a module that did not import, so the table has no HOLE where its
        #: pairs would have been.  ``harness.pairs`` records them rather than raising,
        #: and a reader of the table cannot otherwise tell a module whose classes all
        #: passed from a module whose classes were never built.
        harness.verdict_row(None, None, name=name, model="-", error=f"unimportable module {why}")
        for name, why in sorted(unimportable.items())
    ]
    for p in found:
        name = f"{p.ref.document}{p.ref.pointer}"
        model = getattr(p.model, "__name__", repr(p.model))[:120]
        #: EVERY failure of the per-pair setup becomes a row, and never an exception out
        #: of this loop.  Measured on this base: four pairs of
        #: ``media-buy/buy-products-request.json`` and
        #: ``media-buy/request-proposals-request.json`` declare a pointer the document of
        #: record does not carry, and ``schema_at`` raises ``KeyError`` on it -- which is
        #: enough to take a whole grading pass down and leave every other pair ungraded.
        #: ``adcp-client-python-82m.4``'s own reason: "one raised in its own setup so it
        #: never computed anything.  In a per-pair table, a check that computed nothing is
        #: a BLANK COLUMN."
        try:
            holder = (
                p.model if isinstance(p.model, type) else importlib.import_module(p.module)
            )
            #: **``module=`` IS WHICH TREE, and without it this run graded the tree it
            #: wrote against the records that were INSTALLED** (``adcp-client-python-ir3l``).
            #: ``schemas.__path__`` is bound to ``tree`` above so the MODULES come from
            #: this run's output, but ``schema_at`` resolved its records through the
            #: imported package, which answers from wherever ``_schemas/__init__.py`` was
            #: loaded.  Measured over bundle 3.3: 1,806 pairs, 0 pass, 1,806 absent -- 107
            #: ``FileNotFoundError`` for a 3.3-only document the committed tree has no
            #: record for, 28 ``KeyError``/``IndexError`` at a pointer that is not 3.3's,
            #: and every shared document served the 3.2 text with no error at all.
            #: ``harness.pairs`` already records which module each pair was taken from, so
            #: the tree is not inferred here -- it is the one the class came out of.
            pair = harness.Pair(
                name=name,
                schema=schema_at(p.ref, module=p.module),
                model=p.model,
                accept=p.accept,
                document=schema_at(SchemaRef(p.ref.document, "#"), module=p.module),
                ref=p.ref,
                declared=harness.declarations_of(holder),
                #: ONE derivation of the identity, shared with the fixture reader above:
                #: the store's key and a fixture's key are the same key, and two spellings
                #: of it is a divergence waiting to happen.
                identity=identity_of(p.ref.document, p.ref.pointer),
            )
        except Exception as e:  # a row with a cause, never a lost pair
            rows.append(
                harness.verdict_row(
                    p.ref, None, model=model, error=f"pairing raised {type(e).__name__} {e}"
                )
            )
            continue
        #: **THE RUN DRAWS WHERE THE STORE IS SHORT, AND THE STORE IS A SAVING RATHER THAN
        #: THE INSTRUMENT.**  What stood here skipped a pair the store held nothing for and
        #: wrote ``absent:no held instance for this pair``, on the division "the SUITE draws
        #: and the RUN reports".  That division made the table a function of the STORE, and
        #: ``docs/plan/final-state.md`` reading 1 forbids exactly it: "BOTH CHECKS ARE A
        #: FUNCTION OF (class, document) AND OF NOTHING ELSE", and "A PAIR THAT CAN ONLY BE
        #: GRADED FROM A STORE IS NOT VERIFIED, IT IS REMEMBERED."  A pair whose only
        #: obstruction is a missing cache entry read the same ``absent`` as a pair whose
        #: node admits nothing, so the artifact could not tell a saving apart from a defect.
        #:
        #: MEASURED over the 28 pairs the floor was short at ``00092b521``
        #: (``adcp-client-python-gbw``): 23 draw and PASS in 0.0-0.2 s each, under one
        #: second for all 23 together; 2 report ``no_instrument`` by a named cause
        #: (``core/reference-renderer.json#`` and its ``#/properties/provenance``); 2 report
        #: ``accepts:strategy_error`` in 0.0 s because the node admits nothing
        #: (``adcp-client-python-qzx.5``'s dead union branch); and 1 is cut
        #: (``core/signal-coverage-forecast.json#``, ``adcp-client-python-qzx.8``).  So the
        #: skip was hiding 23 passes behind the same word as 5 real findings.
        #:
        #: **The cost the skip was defending against is bounded by :data:`BUDGET` already,
        #: and is now bounded for the draw too** -- a pair that cannot be drawn inside it
        #: reads ``absent`` with the budget in the cause, which NAMES the draw instead of
        #: naming the cache.  ``adcp-client-python-3be.26``'s 2 h 57 m pairs are reached by
        #: that clause and not by this one.
        #:
        #: **And the draw is FIXTURED**, which is the other half the run was missing: §8's
        #: rule ("a referenced document is graded by its own pair, so at a referring
        #: position it is a fixture and not a draw") was wired into the suite's grading pass
        #: and not into the run's, so a drawing run would have paid the unsubstituted node.
        #: ``_fixtures`` is the same object the suite builds, from the same three readers.
        #: **A BACKSTOP ON THE WALL CLOCK, because §8's obligation draws from a key space
        #: nothing can precompute.**  ``check_widening`` derives its draws from the
        #: declared pointer -- a value class, an intermediate node, the node conjoined
        #: with a demand -- so which positions a pair asks for is known only by running
        #: it, and the committed widening floor holds ZERO entries (``tests/corpus.py``
        #: records that it has no currency gate yet).  Measured: 246.7 s on one pair of
        #: ``core/async-response-data.json`` and over 600 s on another, with every accepts
        #: draw already replayed.
        #:
        #: A pair that does not finish inside the budget becomes ``absent`` with the
        #: budget in the cause, which is this artifact's own rule applied to itself: a
        #: check that computed nothing is a blank column, and a blank column is still a
        #: row.  ``SIGALRM`` and not a thread, because the harness is pure Python on this
        #: thread and a timer that cannot interrupt it is not a bound.
        try:
            with harness.within(BUDGET):
                report = harness.check_pair(
                    pair,
                    custom_formats=formats,
                    corpus=held.STORE,
                    widening_corpus=held.WIDENING_STORE,
                    fixtures=fixtures,
                    construction=construction,
                )
        except harness.OverBudget:
            rows.append(
                harness.verdict_row(
                    p.ref, None, model=model, error=f"did not finish inside {BUDGET} s"
                )
            )
            continue
        except Exception as e:  # as above: the run reports, it does not die
            rows.append(
                harness.verdict_row(
                    p.ref, None, model=model, error=f"check raised {type(e).__name__} {e}"
                )
            )
            continue
        rows.append(harness.verdict_row(p.ref, report, model=model))
    return harness.verdict_table(rows), len(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="codegen", description=__doc__)
    ap.add_argument("--bundle", type=Path, required=True, help="the schema bundle directory")
    ap.add_argument("--tree", type=Path, default=TREE, help="where the modules are written")
    ap.add_argument(
        "--package",
        type=Path,
        default=None,
        help="where D5's alias module is written; a WHOLE-RUN artifact, so a run over "
        "part of the population must leave it out (see `write`)",
    )
    ap.add_argument("document", nargs="+", help="bundle-relative document paths")
    ns = ap.parse_args(argv)

    # **THE PATCH SET IS PART OF THE BUILD** (``patch.BUILD``, ``patch.for_build``).  The
    # bundle stays an ARGUMENT, which is D9 -- no version lives in ``codegen/`` -- and what
    # this line adds is that whatever bundle is named is read through the override table
    # rather than raw.  Measured before it existed: ``grep 'patch.apply\|patch.additions'
    # codegen/*.py`` matched nothing, so the table was written and reviewed and the emitter
    # never saw it.  The GRADE reads the same directory: a harness validating an instance
    # against the published document while the model was compiled from the patched one would
    # be §8's comparison asked of two different schemas.
    # **A REFERENCE THAT DISOWNS ITS OWN BUNDLE'S BASE URI IS REPORTED AND NOT FATAL**
    # (``patch.bases``, ``patch.BASE_URI_AGREEMENT``), and this line is the report.  It is
    # section 5's ``default`` arrangement one layer out -- "dropped and REPORTED" -- because
    # a reader who sees only the refusals would never learn that one of bundle 3.3's 4,164
    # resolving references spells another protocol version, and a silent majority vote is
    # how a second bundle's references would come to drift unnoticed.
    #
    # **Read off the bundle NAMED and before the patch is applied**, which is two decisions
    # and both are the same reason: a dissenting reference is UPSTREAM's defect in the
    # PUBLISHED documents, not a property of the patched copy, and a report printed after
    # ``for_build`` would be lost on exactly the bundle that has one -- ``for_build`` raises
    # on bundle 3.3 today for an entry whose defect upstream has already fixed
    # (``adcp-client-python-82m.60``).  The report is a fact about the input, so it arrives
    # whether or not the run that reads it gets any further.
    #
    # **AND A BUNDLE THAT IS ALREADY PATCHED SAYS SO, BEFORE ANYTHING ELSE IS REPORTED**
    # (``docs/plan/architecture.md``, "AND A BUNDLE DIRECTORY MUST SAY WHETHER IT IS
    # PATCHED, BECAUSE A CALLER CANNOT TELL").  ``for_build`` makes the second application a
    # no-op rather than a raise, and the rule is that the no-op SAYS SO: a run whose
    # ``--bundle`` already holds the table is reading the same input as one handed the
    # published directory, and a reader comparing two runs' reports needs that in the report
    # rather than inferred from the absence of a refusal.  It is printed off the VALUE -- the
    # record beside the directory -- which is the whole of the repair; before it, this line
    # could only have been a guess about what the caller meant.
    already = patch.sets_applied(ns.bundle)
    if already is not None:
        print(
            f"already patched: {ns.bundle} holds {', '.join(already) or '(nothing)'} by the "
            "record beside it, so the build applies nothing further"
        )
    for dissent in patch.bases(ns.bundle).dissenting:
        print(f"dissenting base URI in {dissent}")
    bundle_dir = patch.for_build(ns.bundle)
    out = emit(bundle_dir, ns.document)
    write(out, ns.tree, ns.package)
    if ns.package is None:
        print(
            f"not written: {', '.join(sorted(out.beside))} "
            f"(D5's alias module is a whole-run artifact; pass --package to write it)"
        )
    # Section 5's ``default`` row says "dropped and REPORTED", and this line is the
    # report.  Printed BEFORE the refusals, because a drop is a fact about a document
    # this run EMITTED: a reader scanning the refusals for a document's name would not
    # find it, and the drop would then be invisible to everyone but the suite.
    for document in sorted(out.drops):
        for pointer, value in sorted(out.drops[document].items()):
            print(
                f"dropped {document} at {pointer} on default: the document says "
                f"{value!r} and the property is REQUIRED, so the default can never be "
                "applied and no rendering carries it"
            )
    for document in sorted(out.refusals):
        r = out.refusals[document]
        print(
            f"refused {document} ({r['resolved']}) at {r['pointer']} "
            f"on {r['keyword']}: {r['detail']}"
        )
    # A NAME THE CLASS CARRIES NOTHING FOR is not a refusal and is printed as its own
    # line: the document emitted, and what the reader needs to know is that one name at
    # one pointer reached no class.
    for document in sorted(out.carries_nothing):
        for line in out.carries_nothing[document]:
            print(f"carries nothing for {document} at {line}")
    # **Section 2's approximations, as TWO figures over TWO denominators that are never
    # added** (``docs/plan/architecture.md`` section 10): "``approximated K facts in D
    # documents``, split by kind (WIDENED / UNDERDETERMINED) and by attribution (ours /
    # upstream), with the upstream half listing its issues.  ``K`` and ``D`` are different
    # counts over different denominators and the report never adds them.  Neither is
    # pinned: both rise when a document starts emitting, and the semantics document's
    # section 9 forbids pinning a figure that moves with emission."
    #
    # Printed BEFORE the refusals and AFTER the drops, in the same place and for the same
    # reason the drops are printed there: an approximation is a fact about a document this
    # run EMITTED, so a reader scanning the refusals for the document's name would not
    # find it.
    #
    # Printed WHATEVER the figures are, including zero, which is section 10's rule for the
    # defect counts read across: a reader sees the figure being met rather than inferring
    # it from silence.  At section 14 step 8 it is zero in every column, and that IS the
    # step's exit condition.
    declared = [a for one in out.approximations.values() for a in one]
    for a in declared:
        print(
            f"approximated {a.document}{a.pointer} on {a.keyword}: the document says "
            f"{a.fact!r} and the annotation does not carry it; rung {a.rung} ({a.kind}), "
            f"{a.attribution}"
        )
    by_kind = collections.Counter(a.kind for a in declared)
    ours = [a for a in declared if a.attribution.startswith(keywords.DOCUMENT)]
    upstream = sorted({a.attribution for a in declared if a not in ours})
    print(
        f"approximated {len(declared)} facts in {len(out.approximations)} documents "
        f"({', '.join(f'{k} {by_kind[k]}' for k in KINDS)}; "
        f"ours {len(ours)}, upstream {len(declared) - len(ours)})"
        + (f": {', '.join(upstream)}" if upstream else "")
    )
    # **The report names the KINDS and not "refused" alone.**  "refused" admits "not
    # built yet", which is how `emitted + refused == 1054` stayed green over 385
    # documents waiting on rows nobody had written, so the one figure the exit
    # condition counts -- emitted plus VERDICTS -- is printed beside the partition
    # rather than left to a reader to assemble.
    #
    # **Section 10 would replace this pair with ``emitted N / population N``, and the
    # reason it could not be replaced is gone -- so this is now an open decision and not a
    # blocked one.**  The section's reason is that "``M`` goes to zero over this bundle and
    # the pair stops partitioning anything".  At section 14 step 8 ``M`` was 285, because
    # that step widens no cell and so moves no document out of the refused set, and a
    # report printing ``emitted 769 / population 1054`` beside 285 refusals would have
    # stated a partition the run did not hold.  Step 10 took ``M`` to zero: the READING is
    # the ``refused`` figure this very line prints, and it is what ``./check`` reports.
    #
    # The pair nevertheless STAYS, and that is a decision rather than a leftover. The
    # delivery report is required to read the three numbers off ``Refusal.kind`` with the
    # ``deferred``/``verdict`` split and never summed, and ``emitted N / population N``
    # drops the split; changing the lines a delivery quotes is a report change nobody has
    # taken. So the pair is here on purpose, with the approximation figures beside it, and
    # no step is behind on it.
    counted = collections.Counter(r["resolved"] for r in out.refusals.values())
    verdicts = sum(counted[k] for k in refusal.FINAL_KINDS)
    print(
        f"emitted {len(out.emitted)} / refused {len(out.refusals)} "
        f"({', '.join(f'{k} {n}' for k, n in sorted(counted.items()))}); "
        f"accounted {len(out.emitted) + verdicts}; "
        f"{len(set(ns.document))} named, the rest reached through a $ref"
    )
    # **§10's per-pair verdict table, written by the RUN and named on stdout.**  Not behind
    # a flag, not only on failure, and not by a test: every figure this command used to
    # produce lived in a terminal, and the two checks that were counted as passing while
    # having never run at all were invisible for exactly that reason
    # (``adcp-client-python-82m.4``).  The path is printed and the counts are not: the
    # counts are IN the file, where a reviewer can grep them and a diff can date them.
    #
    # LAST, after every line above, because grading imports the tree this run wrote and a
    # tree that does not import must not cost the report its numbers.
    started = time.time()
    table, written = grade(ns.tree, ns.package, bundle_dir)
    path = ns.tree.parent / VERDICTS
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(table)
    print(
        f"verdicts {written} rows -> {path} "
        f"(grep 'dump=fail' for one check, diff against the last run for what moved)"
    )
    # **THE DURATION IS ON STDERR, because stdout is an OUTPUT and a wall clock is not a
    # function of the inputs.**  P7 is "the output is a function of its inputs and of
    # nothing else", and ``tests/test_emit.py``'s property compares the whole report
    # between two runs at different hash seeds precisely because a refused document says
    # everything it has to say here and nowhere in ``files``.  A ``.1f`` of elapsed
    # seconds made that comparison fail on the one character of the report that no input
    # decides -- 50.3 s against 48.8 s -- so the property could not grade the sentences
    # it exists for.
    #
    # Not deleted, because the figure is what tells an operator that grading is the
    # expensive half of the run.  ``./check`` already settled where it goes: its own
    # ``({...:.2f} s)`` line is printed to ``sys.stderr`` beside three stdout lines that
    # are the delivery's numbers.  This is that same split, in the other entry point.
    print(f"({time.time() - started:.1f} s)", file=sys.stderr)
    return 1 if out.refusals else 0


if __name__ == "__main__":
    sys.exit(main())
