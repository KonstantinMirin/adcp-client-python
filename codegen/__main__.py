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
from codegen import bundle as bundle_module
from codegen import harness, held, keywords, patch, refusal
from codegen.emit import PACKAGE, TREE, emit, write

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
    identities = bundle_module.source_identities(bundle_dir)
    formats = harness.FORMAT_STRATEGIES
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
            pair = harness.Pair(
                name=name,
                schema=schema_at(p.ref),
                model=p.model,
                accept=p.accept,
                document=schema_at(SchemaRef(p.ref.document, "#")),
                ref=p.ref,
                declared=harness.declarations_of(holder),
                identity={
                    "document": p.ref.document,
                    "pointer": p.ref.pointer,
                    "source": identities[p.ref.document],
                },
            )
        except Exception as e:  # a row with a cause, never a lost pair
            rows.append(
                harness.verdict_row(
                    p.ref, None, model=model, error=f"pairing raised {type(e).__name__} {e}"
                )
            )
            continue
        #: **THE RUN REPLAYS AND DOES NOT DRAW, and a pair with no held instance is a ROW
        #: and not a draw.**  The accepts key is computable without grading anything
        #: (``harness.corpus_key`` over the pair's static identity), so the run can see
        #: the miss before it costs anything -- and a miss costs, by design: "an absent
        #: corpus is one full cold run."
        #:
        #: Measured, which is why this line exists rather than a comment about it: the
        #: committed floor is short 98 of the 2,793 pairs
        #: (``adcp-client-python-3be.26``), 15 of them at or above 8 MB of resolved node,
        #: and the two largest -- ``core/async-response-data.json#`` and
        #: ``core/mcp-webhook-payload.json#`` at 44 MB -- ran 2 h 57 m at 32 GB of RSS
        #: without finishing.  A run that drew them would never write the table at all,
        #: and a table nobody can obtain is the terminal figure this artifact replaces.
        #:
        #: **So the division is: the SUITE draws and the RUN reports.**  The drawn corpus
        #: is committed precisely so that "a cold checkout pays zero draws", and the
        #: shortfall has its own instrument
        #: (``test_every_graded_pair_has_a_committed_entry_under_the_current_key``).  What
        #: this adds is the shortfall PER PAIR, in the artifact, as ``absent`` -- which is
        #: strictly more than a hang and strictly more than a count.
        key = harness.corpus_key(pair.identity, custom_formats=formats)
        if held.STORE.get(key) is None:
            rows.append(
                harness.verdict_row(
                    p.ref, None, model=model, error="no held instance for this pair"
                )
            )
            continue
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
