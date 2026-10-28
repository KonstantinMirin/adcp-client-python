"""The held accepts corpus, and the four ways it could be wrong.

``docs/plan/rebuild-plan.md`` §8 makes the accepts draw the thing that PROVES a widening
rather than believing it, and ``pyproject.toml``'s own invariant says what that costs a
cache: *"A faster suite that grades something else would not be faster, so the identity
of the failure set is the thing to check if this ever changes."*  So a corpus of drawn
instances is admissible only under conditions, and every one of them is graded here:

1. **A hit replays the instance a draw produced**, not a similar one.  The class sees the
   same bytes, through the same ``body``, and every counter the report carries is the one
   a drawing run produced.
2. **A changed document does not reuse a held instance.**  The key is the content address
   of the schema handed to ``from_schema``, so a record that moved by one byte misses --
   and because ``bundle.record`` inlines every cross-document ``$ref``, a dependency that
   moved has already moved the dependent's bytes.  That is the whole of the delta, and
   there is no dependency graph anywhere in it.
3. **A held entry that cannot stand in reddens**, and the two shapes of that are checked
   separately: an instance the document refuses, and an entry that cannot cover the
   obligation -- *including an empty one*, which is the one failure mode that would read
   as "the obligation passed".
4. **The corpus moves no verdict.**  A pair graded from a hit and the same pair graded
   from a draw report the same outcome, the same instance count and the same comparison.

**AND THE DRAW IT REPLACES IS NOT REPRODUCIBLE, which is the measurement that decided the
shape rather than a caveat on it.**  Two full passes over the same 1,664 pairs at the same
pinned inputs drew a different instance for 23 of them, and one identical 208-pair shard
re-run differed from itself on 3 -- not on the seed (``_SETTINGS`` fixes ``derandomize``),
not on ``PYTHONHASHSEED``, not on the recursion limit, but on process-global state inside
``hypothesis`` whose lifetime garbage collection governs.  So the witness those pairs are
graded against is decided today by which worker ``xdist`` sent them to.  A held corpus is
therefore the more stable instrument, not the less: it pins what scheduling currently
decides, and it re-offers the pinned value to the DOCUMENT on every read, so a pinned
witness cannot outlive the schema it was drawn from.

The division of labour is the point of the shape: ``harness.corpus_key`` and
``harness.corpus_defect`` decide, inside the module §9 forbids to read a path, and
``tests/corpus.py`` only stores bytes.  So the tests below hand the harness a dict and a
perturbed dict; nothing here needs the real store to make its claim.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from importlib import resources
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict

import corpus as corpus_module
from adcp.types._base import PACKAGE, SchemaRef, schema_at
from codegen import harness
from codegen.harness import Pair, check_accepts, check_pair, corpus_defect, corpus_key
from nodeset import claimed

REPO = Path(__file__).resolve().parents[1]

#: The packaged records, reached the way ``adcp.types._base._document`` reaches them --
#: through the package rather than through a path spelled here, so this cannot grade a
#: directory the runtime does not read.
RECORDS = Path(str(resources.files(PACKAGE)))

#: One object document that demands both keys, so a held instance can be perturbed in
#: exactly one axis.  ``tests/test_harness_halves.py``'s ``DOC`` for the same reason.
DOC: dict[str, Any] = {
    "type": "object",
    "required": ["a", "b"],
    "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
    "additionalProperties": False,
}


class Faithful(BaseModel):
    model_config = ConfigDict(extra="forbid")
    a: str
    b: int


def accept_of(cls: type[BaseModel]):
    """The production shape of an entry point: the document decides, then the class builds."""
    import jsonschema

    def accept(payload: Any) -> Any:
        jsonschema.Draft7Validator(DOC).validate(payload)
        return cls.model_validate(payload)

    return accept


class Held:
    """``tests/corpus.Store``'s interface over a dict, so a test can perturb one entry.

    A dict and not the real store, because what these tests judge is what the HARNESS
    does with what it is handed: the real store's own obligations -- an atomic write, a
    value it declines to hold -- are graded further down against the real thing.
    """

    def __init__(self, entries: dict[str, Any] | None = None) -> None:
        self.entries: dict[str, Any] = dict(entries or {})
        self.gets: list[str] = []
        self.puts: list[str] = []

    def get(self, key: str) -> Any:
        self.gets.append(key)
        return self.entries.get(key)

    def put(self, key: str, instances: list[Any]) -> None:
        self.puts.append(key)
        self.entries[key] = instances


# --------------------------------------------------------------------------- #
# 1. a hit replays the instance the draw produced
# --------------------------------------------------------------------------- #
def test_a_hit_replays_the_instance_the_draw_produced_and_says_that_it_did() -> None:
    """The same bytes reach the class, and the report says where they came from.

    A cache that produced an EQUIVALENT instance would be a different instrument: the
    obligation is about the values the document admits, and two of them can disagree
    about what a class does.  So the claim is identity of the instance, not of the
    verdict -- the verdict follows.
    """
    store = Held()
    drew: list[Any] = []
    first = check_accepts(DOC, accept_of(Faithful), examples=1, seen=drew, corpus=store)
    assert first.outcome == "pass" and first.examples == 1
    assert first.replayed == 0, "a cold key cannot be a hit"
    assert store.puts == [first.corpus_key], store.puts

    replayed: list[Any] = []
    second = check_accepts(DOC, accept_of(Faithful), examples=1, seen=replayed, corpus=store)
    assert second.replayed == second.examples == 1
    assert second.corpus_key == first.corpus_key
    assert replayed == drew, (replayed, drew)
    # Every counter the report carries, not just the verdict: ``graded_instances`` is the
    # suite's one denominator and a replay that moved it would be grading less.
    assert (second.outcome, second.round_tripped, second.dump_exempt) == (
        first.outcome,
        first.round_tripped,
        first.dump_exempt,
    )


def test_a_pair_with_no_store_draws_exactly_as_it_always_did() -> None:
    """``corpus=None`` is the old path, and the report says so by its own fields."""
    seen: list[Any] = []
    res = check_accepts(DOC, accept_of(Faithful), examples=1, seen=seen, corpus=None)
    assert res.outcome == "pass" and res.examples == 1
    assert (res.replayed, res.corpus_key) == (0, "")
    assert len(seen) == 1


# --------------------------------------------------------------------------- #
# 2. the key is the content address of the draw's own input
# --------------------------------------------------------------------------- #
def test_every_input_to_the_draw_is_in_the_key_and_nothing_else_is() -> None:
    """Four inputs, each moved on its own, and the key moves with each.

    The seed is deliberately absent, and NOT because the draw is a pure function of the
    four: ``_SETTINGS`` fixes ``derandomize``, so there is no seed for a caller to vary,
    and the residual nondeterminism the next test records is process state no key can
    name.  What the key has to do is say when the SCHEMA moved, and the document says the
    rest.
    """
    base = corpus_key(DOC, examples=1, custom_formats={})
    moved = {
        "the schema": corpus_key({**DOC, "maxProperties": 2}, examples=1, custom_formats={}),
        "the example count": corpus_key(DOC, examples=2, custom_formats={}),
        "a format strategy": corpus_key(DOC, examples=1, custom_formats={"uuid": object()}),
    }
    for what, key in moved.items():
        assert key != base, f"{what} moved and the key did not"
    assert len(set(moved.values())) == len(moved), "two different inputs share one key"
    # Stable within the process, which is what makes a hit possible at all: the key is
    # computed from the schema's canonical spelling, so key order cannot move it.
    reordered = {k: DOC[k] for k in reversed(list(DOC))}
    assert corpus_key(reordered, examples=1, custom_formats={}) == base


def test_the_key_is_the_same_in_another_process() -> None:
    """A key computed in one worker names the same entry in another, or there is no cache.

    **This is the half of determinism the design actually needs, and the other half does
    not hold.**  Measured over the graded population: two full passes at the same pinned
    inputs drew a DIFFERENT instance for 23 of 1,664 pairs, and one identical 208-pair
    shard re-run differed from itself on 3 -- not on the seed, not on ``PYTHONHASHSEED``,
    not on the recursion limit, but on process-global state inside ``hypothesis`` whose
    lifetime garbage collection governs.  So the suite's witness for those pairs is
    decided today by which worker ``xdist`` sent them to and when the collector ran.

    Holding the witness is therefore a REDUCTION in drift and not a source of one: the
    corpus pins what the draw leaves to the scheduler, and ``corpus_defect`` re-offers the
    pinned value to the document on every read, so what is pinned is still a value the
    document admits and not a payload that outlived its schema.  What must be stable is
    the KEY -- a function of the schema's canonical bytes and nothing else -- and that is
    what this checks across separate interpreters at three hash seeds.
    """
    source = (
        "import json,sys;"
        "sys.path[:0]=['.','src','tests'];"
        "from codegen.harness import check_accepts, corpus_key;"
        "import test_accepts_corpus as t;"
        "seen=[];"
        "r=check_accepts(t.DOC, t.accept_of(t.Faithful), examples=1, seen=seen);"
        "print(json.dumps([corpus_key(t.DOC, examples=1, custom_formats={}), seen, r.outcome]))"
    )
    runs = []
    for seed in ("0", "1", "12345"):
        env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": ".:src:tests"}
        done = subprocess.run(
            [sys.executable, "-c", source], cwd=REPO, env=env, capture_output=True, text=True
        )
        assert done.returncode == 0, done.stderr[-2000:]
        runs.append(json.loads(done.stdout.strip().splitlines()[-1]))
    keys = claimed("keys computed in another interpreter", {run[0] for run in runs})
    assert len(keys) == 1, "the key is not a function of the schema alone"
    assert keys == {corpus_key(DOC, examples=1, custom_formats={})}, "and not this one's"
    assert {run[2] for run in runs} == {"pass"}


# --------------------------------------------------------------------------- #
# 2b. why that key covers the dependency closure, with no dependency graph
# --------------------------------------------------------------------------- #
def test_every_packaged_record_is_self_contained() -> None:
    """**The property that makes the delta trivial**, measured on the packaged tree.

    ``bundle.record`` inlines every cross-document ``$ref`` and rewrites nothing, so a
    record carries its whole dependency closure as literal text.  If one did NOT -- if a
    single ``$ref`` still named another document -- then a change to that document would
    leave the dependent's bytes untouched, its key would hit, and the suite would grade a
    class against a schema that had moved.  The key would need a dependency graph beside
    it, and ``docs/plan/architecture.md`` §3 forbids the second copy that would be.

    A LOCAL ``$ref`` (``#/definitions/x``) is not a hole: it points inside the same
    record, which ``harness.resolve`` inlines against that same record, so its target's
    bytes are already in the hash.
    """
    records = claimed("packaged records", RECORDS.rglob("*.json"))
    cross = sorted(
        f"{path.relative_to(RECORDS)}: {m.group(1)}"
        for path in records
        for m in re.finditer(r'"\$ref"\s*:\s*"([^"]*)"', path.read_text())
        if not m.group(1).startswith("#")
    )
    assert cross == [], cross


#: The dependency whose inlined copies the test below perturbs, and one dependent of it.
#: A title and not a path, because what is in the dependent's record is the inlined TEXT:
#: ``Provenance`` is the most-inlined node of the bundle, and the record naming it here is
#: the one ``codegen/harness.py``'s own docstring measures at 5.19 MB.
INLINED_TITLE = "Provenance"
DEPENDENT = "media-buy/get-media-buy-delivery-response.json"


def test_a_dependencys_own_bytes_are_in_its_dependents_key() -> None:
    """Perturb the INLINED copy, and the dependent's key moves -- with no edge read.

    This is the claim ``corpus_key``'s docstring makes, checked rather than argued: the
    dependency's text is part of the dependent's record, so re-emitting after a change to
    the dependency produces different record bytes, a different node, and a different key.
    Nothing here consults ``bundle.edges`` or any map of what depends on what; the bytes
    are the map.

    The control is in the same assertion: a document that does NOT carry the perturbed
    text keeps its key, so the perturbation is not moving every key by being a
    perturbation.
    """
    record = json.loads((RECORDS / DEPENDENT).read_text())
    before = corpus_key(record, examples=1, custom_formats={})
    text = json.dumps(record)
    assert f'"title": "{INLINED_TITLE}"' in text, (
        f"{DEPENDENT} no longer inlines {INLINED_TITLE}; pick a dependent that does"
    )
    # The perturbation a dependency's own edit would produce once re-emitted: one keyword,
    # at one inlined position.  Applied to a COPY -- nothing on disk moves.
    perturbed = json.loads(text.replace(f'"title": "{INLINED_TITLE}"', '"title": "Provenanc"', 1))
    after = corpus_key(perturbed, examples=1, custom_formats={})
    assert after != before, "a dependency moved inside the record and the key did not"

    control = json.loads((RECORDS / "core" / "pagination-request.json").read_text())
    assert f'"title": "{INLINED_TITLE}"' not in json.dumps(control)
    assert corpus_key(control, examples=1, custom_formats={}) == corpus_key(
        json.loads(json.dumps(control)), examples=1, custom_formats={}
    )


# --------------------------------------------------------------------------- #
# 3. a held entry that cannot stand in REDDENS
# --------------------------------------------------------------------------- #
def test_an_empty_entry_is_not_the_obligation_passing() -> None:
    """**The one failure mode a corpus of this shape can have.**

    §8's accepts draw is what proves a widening rather than believing it, so a pair that
    graded NO instance has not passed -- and a store answering ``[]`` is exactly a pair
    that graded no instance while looking like a hit.  It is a verdict, with the count at
    zero, so ``PairReport.outcome`` reddens it twice: once on the accepts outcome and
    once on the denominator.
    """
    key = corpus_key(DOC, examples=1, custom_formats={})
    res = check_accepts(DOC, accept_of(Faithful), examples=1, corpus=Held({key: []}))
    assert res.outcome == "corpus_rejected", res.outcome
    assert res.examples == 0 and res.round_tripped == 0
    assert "0 instances" in res.detail and "the obligation is 1" in res.detail, res.detail


def test_an_entry_that_cannot_cover_the_obligation_reddens() -> None:
    """Short of the example count, which is the same defect as empty one step along."""
    key = corpus_key(DOC, examples=3, custom_formats={})
    held = Held({key: [{"a": "x", "b": 1}, {"a": "y", "b": 2}]})
    res = check_accepts(DOC, accept_of(Faithful), examples=3, corpus=held)
    assert res.outcome == "corpus_rejected", res.outcome
    assert res.examples == 0
    # And an entry at the obligation's own count is accepted, so the clause above is
    # judging the COUNT and not the hit.
    whole = Held({key: [{"a": "x", "b": 1}, {"a": "y", "b": 2}, {"a": "z", "b": 3}]})
    assert check_accepts(DOC, accept_of(Faithful), examples=3, corpus=whole).outcome == "pass"


def test_a_held_instance_the_document_refuses_reddens_rather_than_being_redrawn() -> None:
    """A stale entry under a live key, which the key alone makes unreachable.

    So this is the defence BEHIND the key: reaching it means the store answered for a key
    it was not asked about, and that is the one way a held corpus could grade a class
    against the wrong document.  Not a silent re-draw -- a store that can do this is
    broken, and a fallback would hide it for as long as it kept happening.
    """
    key = corpus_key(DOC, examples=1, custom_formats={})
    res = check_accepts(DOC, accept_of(Faithful), examples=1, corpus=Held({key: [{"a": "x"}]}))
    assert res.outcome == "corpus_rejected", res.outcome
    assert res.examples == 0
    assert "refuses held instance 0 on required" in res.detail, res.detail


def test_the_defect_reading_is_the_documents_and_not_a_predicate_of_ours() -> None:
    """``corpus_defect`` asks the DOCUMENT, and reads ``is False`` the way the dump does.

    Three answers a validator can give and what each means here: refused (a defect),
    admitted (no defect), and *no answer at all* -- a document ``jsonschema`` cannot build
    a validator from states nothing about any instance, so it cannot refuse one either.
    The accepts check's own dump half already reads that third answer this way
    (``conforms(...) is False``), and two readings of one answer is how a held entry comes
    to redden a pair that was green.
    """
    assert corpus_defect(DOC, [{"a": "x", "b": 1}], 1) == ""
    assert "refuses held instance 0" in corpus_defect(DOC, [{"a": "x"}], 1)
    unusable = {"type": "object", "properties": {"a": {"pattern": "("}}}
    assert corpus_defect(unusable, [{"a": "x"}], 1) == "", "a document that cannot decide refused"


def test_a_rejected_entry_is_a_verdict_on_the_pair() -> None:
    """``PairReport.outcome`` turns it into one, which is what makes the suite redden.

    Through ``check_pair`` and not by reading ``AcceptsResult``, because the suite asserts
    on the pair's verdict: a new accepts outcome that fell through to ``pass`` would be a
    cache that silently stopped grading.
    """
    pair = Pair(name="held", schema=DOC, model=Faithful, accept=accept_of(Faithful))
    key = corpus_key(DOC, examples=1, custom_formats={})
    rep = check_pair(pair, corpus=Held({key: []}))
    assert rep.accepts.outcome == "corpus_rejected"
    assert rep.graded_instances == 0
    assert rep.outcome == "accepts:corpus_rejected", rep.outcome


def test_a_miss_costs_a_draw_and_never_passes_on_nothing() -> None:
    """A key this store has never been asked for draws, and the entry is then held.

    Which is what makes the delta a delta: a new document adds one key and a changed one
    changes its own key and every dependent's, so the work is proportional to the change
    and an absent corpus is one full cold run.
    """
    store = Held()
    moved = {**DOC, "properties": {**DOC["properties"], "a": {"type": "string", "maxLength": 9}}}
    first = check_accepts(DOC, accept_of(Faithful), examples=1, corpus=store)
    second = check_accepts(moved, accept_of(Faithful), examples=1, corpus=store)
    assert first.corpus_key != second.corpus_key
    assert (first.replayed, second.replayed) == (0, 0)
    assert sorted(store.entries) == sorted({first.corpus_key, second.corpus_key})
    # The moved schema's own key now hits, and the ORIGINAL's still does: a delta holds
    # both, where a whole-corpus rebuild would have replaced one with the other.
    assert check_accepts(moved, accept_of(Faithful), examples=1, corpus=store).replayed == 1
    assert check_accepts(DOC, accept_of(Faithful), examples=1, corpus=store).replayed == 1


def test_a_draw_that_produced_nothing_is_not_held() -> None:
    """A ``strategy_error`` holds no entry, so the next run draws rather than reading one.

    An entry for it would claim a draw happened, and the pair's verdict is precisely that
    one did not: ``PairReport.no_instrument`` is what reads that, and a held empty list
    would reach ``corpus_rejected`` instead and change the pair's reported cause.
    """
    store = Held()
    # A ``format`` beside a ``pattern`` the format's own strategy cannot satisfy -- the
    # shape ``harness.format_pattern_positions`` names, and the only one in this bundle
    # that fails to draw.
    undrawable = {"type": "string", "format": "date-time", "pattern": "^zzz$"}
    res = check_accepts(undrawable, lambda x: x, examples=1, corpus=store)
    assert res.outcome == "strategy_error", res.outcome
    assert store.entries == {}, store.entries


# --------------------------------------------------------------------------- #
# 4. the corpus moves no verdict
# --------------------------------------------------------------------------- #
#: The pairs graded both ways below.  A SAMPLE and it says so: grading the whole
#: population twice is the cold run this row exists to remove, and what the sample has to
#: cover is the SHAPES a record can have -- a root object, a nested node, an enumeration,
#: a union branch, a mapping root -- rather than a count of documents.
BOTH_WAYS = (
    "core/pagination-request.json#",
    "core/context.json#",
    "core/ext.json#",
    "core/format-id.json#",
    "enums/reporting-destination-setup-state.json#",
    "core/reference-renderer.json#",
)


@pytest.mark.parametrize("name", BOTH_WAYS)
def test_a_replayed_pair_and_a_drawn_pair_report_the_same_thing(name: str) -> None:
    """Same verdict, same denominator, same comparison, same liveness -- on real records.

    The identity of the failure set is what ``pyproject.toml`` says to check when the
    suite gets faster, and this is that check at the level of one pair: every field the
    suite asserts on is compared between a pair that drew and the same pair that replayed.
    ``replayed`` and ``corpus_key`` are the two that are MEANT to differ, and they are
    asserted to differ rather than excluded.
    """
    import test_emit

    document, pointer = name.split("#")
    ref = SchemaRef(document, "#" + pointer)
    g = next(x for x in test_emit.graded() if x.ref == ref)
    pair = test_emit.pair_of(g)

    store = Held()
    cold = check_pair(pair, custom_formats=test_emit.FORMAT_STRATEGIES, corpus=store)
    warm = check_pair(pair, custom_formats=test_emit.FORMAT_STRATEGIES, corpus=store)

    assert cold.outcome == warm.outcome
    assert cold.graded_instances == warm.graded_instances
    assert (cold.accepts.outcome, cold.accepts.examples, cold.accepts.dump_exempt) == (
        warm.accepts.outcome,
        warm.accepts.examples,
        warm.accepts.dump_exempt,
    )
    assert (cold.liveness.outcome, cold.liveness.how, cold.liveness.violated) == (
        warm.liveness.outcome,
        warm.liveness.how,
        warm.liveness.violated,
    )
    assert (cold.comparison.outcome, cold.comparison.compared) == (
        warm.comparison.outcome,
        warm.comparison.compared,
    )
    assert cold.accepts.replayed == 0
    assert warm.accepts.replayed == warm.accepts.examples
    assert warm.accepts.corpus_key == cold.accepts.corpus_key


# --------------------------------------------------------------------------- #
# the store's own two obligations
# --------------------------------------------------------------------------- #
def test_the_store_declines_a_value_it_cannot_hold_faithfully(tmp_path: Path) -> None:
    """A value that does not survive JSON is not held, and that is the safe direction.

    ``hypothesis`` draws values JSON cannot carry back -- a ``nan`` is not equal to
    itself -- and an entry that read back as something else would redden a pair that had
    been green.  The cost of declining is one re-draw per run for that pair.
    """
    store = corpus_module.Store(tmp_path)
    store.put("a" * 64, [{"ok": 1}])
    assert store.get("a" * 64) == [{"ok": 1}]
    store.put("b" * 64, [float("nan")])
    assert store.get("b" * 64) is None
    assert store.declined == 1 and store.held == 1


def test_an_unreadable_entry_is_a_miss_and_a_parsed_one_is_the_harnesss_business(
    tmp_path: Path,
) -> None:
    """The store's own division: unparseable is ``None``; parsed is handed over as-is.

    A truncated file is not an entry, so there is nothing to grade and nothing to hide --
    the pair draws.  An entry that PARSES and says the wrong thing is the dangerous case,
    and the store does not get to decide that one: ``harness.corpus_defect`` does, out
    loud, which is what the tests above grade.
    """
    store = corpus_module.Store(tmp_path)
    key = "c" * 64
    store.put(key, [{"ok": 1}])
    path = store._path(key)  # noqa: SLF001 -- the test is about this file's bytes
    path.write_text("{not json")
    assert store.get(key) is None
    path.write_text(json.dumps([{"wrong": True}]))
    assert store.get(key) == [{"wrong": True}], "the store filtered what the harness grades"


def test_the_store_is_a_build_artifact_and_not_a_committed_one() -> None:
    """Regenerable on a miss, so it is ignored by git -- and the SIZE is not the reason.

    ``corpus.DIRECTORY``'s comment carries both halves: 0.16 MB over 1,661 entries is small
    enough to commit, and what keeps it out is that a committed corpus is a second derived
    artifact whose currency nothing grades.  Stated here as a property of the tree rather
    than as a sentence, so a corpus cannot be committed by accident: a run that regenerates
    cannot leave the working tree dirty.
    """
    rel = corpus_module.DIRECTORY.relative_to(REPO)
    ignored = {line.strip().rstrip("/") for line in (REPO / ".gitignore").read_text().splitlines()}
    assert rel.name in ignored, rel
    done = subprocess.run(
        ["git", "check-ignore", "-q", str(rel) + "/x"], cwd=REPO, capture_output=True
    )
    assert done.returncode == 0, "git does not ignore the corpus directory"
