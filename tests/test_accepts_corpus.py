"""The held accepts corpus, and the four ways it could be wrong.

``docs/plan/rebuild-plan.md`` §8 makes the accepts draw the thing that PROVES a widening
rather than believing it, and ``pyproject.toml``'s own invariant says what that costs a
cache: *"A faster suite that grades something else would not be faster, so the identity
of the failure set is the thing to check if this ever changes."*  So a corpus of drawn
instances is admissible only under conditions, and every one of them is graded here:

1. **A hit replays the instance a draw produced**, not a similar one.  The class sees the
   same bytes, through the same ``body``, and every counter the report carries is the one
   a drawing run produced.
2. **A changed DOCUMENT does not reuse a held instance, and a changed RENDERING of an
   unchanged document does.**  The key is the content address of the caller's static
   identity for the draw -- for a bundle pair, the document's own raw bytes and its raw
   reference closure's (``bundle.source_identities``) beside the pointer -- so an upstream
   edit anywhere in the closure misses, and a change to how ``bundle.record`` inlines
   misses nothing.  Both halves are graded, the second one by perturbing the inliner.
   There is no dependency graph anywhere in it: the closure is read off the ``$ref``
   strings the documents themselves write.
3. **A held entry that cannot stand in reddens**, and the two shapes of that are checked
   separately: an instance the document refuses, and an entry that cannot cover the
   obligation -- *including an empty one*, which is the one failure mode that would read
   as "the obligation passed".
4. **The corpus moves no verdict.**  A pair graded from a hit and the same pair graded
   from a draw report the same outcome, the same instance count and the same comparison.
5. **THE CORPUS IS IN THE TREE, AND ITS CURRENCY IS GRADED.**  ``docs/plan/architecture.md``
   ("The drawn corpus is COMMITTED", 2026-10-30).  Every graded PAIR has a committed entry
   under the current key, less the pairs no draw can reach; the floor answers before the
   shared cache and no run writes the floor; and a committed entry the document refuses
   reddens rather than being repaired by the cache behind it.  The gate is shown red by
   the event it exists to catch -- a generator bump -- and not only green.

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
``tests/corpus.py`` only stores bytes.  The harness never DERIVES the identity either --
the caller hands it one, because the only party who can see upstream of our own inliner is
the caller.  So the tests below hand the harness a dict and a perturbed dict; nothing here
needs the real store to make its claim.

A literal schema written in this file IS its own static identity -- nothing inlined it --
so the unit tests pass ``DOC`` as both, which is the degenerate case of the same rule and
not an exception to it.
"""

from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from importlib import resources
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from pydantic import BaseModel, ConfigDict

import corpus as corpus_module
from adcp.types._base import PACKAGE, SchemaRef, schema_at
from codegen import bundle, harness
from codegen.harness import Pair, check_accepts, check_pair, corpus_defect, corpus_key
from nodeset import claimed

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"

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
    first = check_accepts(
        DOC, accept_of(Faithful), examples=1, seen=drew, corpus=store, identity=DOC
    )
    assert first.outcome == "pass" and first.examples == 1
    assert first.replayed == 0, "a cold key cannot be a hit"
    assert store.puts == [first.corpus_key], store.puts

    replayed: list[Any] = []
    second = check_accepts(
        DOC, accept_of(Faithful), examples=1, seen=replayed, corpus=store, identity=DOC
    )
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
# 2. the key is the content address of the draw's own STATIC input
# --------------------------------------------------------------------------- #
def test_every_input_to_the_draw_is_in_the_key_and_nothing_else_is() -> None:
    """Four inputs, each moved on its own, and the key moves with each.

    The seed is deliberately absent, and NOT because the draw is a pure function of the
    four: ``_SETTINGS`` fixes ``derandomize``, so there is no seed for a caller to vary,
    and the residual nondeterminism the next test records is process state no key can
    name.  What the key has to do is say when the QUESTION moved, and the document says
    the rest.
    """
    base = corpus_key(DOC, examples=1, custom_formats={})
    moved = {
        "the identity": corpus_key({**DOC, "maxProperties": 2}, examples=1, custom_formats={}),
        "the example count": corpus_key(DOC, examples=2, custom_formats={}),
        "a format strategy": corpus_key(DOC, examples=1, custom_formats={"uuid": object()}),
    }
    for what, key in moved.items():
        assert key != base, f"{what} moved and the key did not"
    assert len(set(moved.values())) == len(moved), "two different inputs share one key"
    # Stable within the process, which is what makes a hit possible at all: the key is
    # computed from the identity's canonical spelling, so key order cannot move it.
    reordered = {k: DOC[k] for k in reversed(list(DOC))}
    assert corpus_key(reordered, examples=1, custom_formats={}) == base


def test_a_store_with_no_identity_beside_it_raises_rather_than_keying_on_the_schema() -> None:
    """**No fallback, because the fallback WAS the defect.**

    Keying on the schema is keying on ``bundle.record``'s rendering of a document, which is
    what redrew the corpus whenever this package's inliner moved.  A default that quietly
    went back to it would restore that for any caller who omitted the argument, and the
    only symptom would be a cold run nobody ordered -- a cost, with nothing red.  So the
    pair that cannot say what question it is asking does not get a cache: it raises here,
    and a caller with nothing static to offer passes ``corpus=None`` and draws.

    Both doors, because ``check_pair`` is the one the population comes through and it does
    not pass ``identity`` itself -- it reads :attr:`Pair.identity`, which defaults to
    ``None``.
    """
    store = Held()
    with pytest.raises(ValueError, match="STATIC identity"):
        check_accepts(DOC, accept_of(Faithful), examples=1, corpus=store)
    with pytest.raises(ValueError, match="STATIC identity"):
        check_pair(Pair(name="anonymous", schema=DOC, model=Faithful, accept=accept_of(Faithful)),
                   corpus=store)
    assert (store.gets, store.puts) == ([], []), "the store was read under no identity"
    # And the same pair with no store grades, so what the raise refuses is the CACHE and
    # not the pair.
    assert check_accepts(DOC, accept_of(Faithful), examples=1, corpus=None).outcome == "pass"


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
    the KEY -- a function of the identity's canonical bytes and nothing else -- and that is
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
    assert len(keys) == 1, "the key is not a function of the identity alone"
    assert keys == {corpus_key(DOC, examples=1, custom_formats={})}, "and not this one's"
    assert {run[2] for run in runs} == {"pass"}


# --------------------------------------------------------------------------- #
# 2b. the key covers the dependency closure, and NOT our rendering of it
# --------------------------------------------------------------------------- #
def test_every_packaged_record_is_self_contained() -> None:
    """**The property the DRAW needs**, measured on the packaged tree.

    ``bundle.record`` inlines every cross-document ``$ref`` and rewrites nothing, so a
    record carries its whole dependency closure as literal text and ``check_pair``'s
    instance checks can draw from a node without reaching for another document.  If one
    did NOT -- if a single ``$ref`` still named another document -- ``hypothesis_jsonschema``
    would meet an unresolvable reference and report a generator failure wearing the model's
    name, and ``strict_validate`` would try to FETCH it.

    **It is no longer what the KEY rests on, and that is the point of this row.**  The key
    used to hash this record, which made a dependency's edit reach the dependent BY
    CONSTRUCTION -- and made our own inlining reach it the same way, so the whole corpus was
    redrawn whenever the inliner moved and no document had.  The closure now comes from
    ``bundle.source_identities``, over the RAW bundle, which is where the two can be told
    apart.

    A LOCAL ``$ref`` (``#/definitions/x``) is not a hole: it points inside the same record,
    which ``harness.resolve`` inlines against that same record.
    """
    records = claimed("packaged records", RECORDS.rglob("*.json"))
    cross = sorted(
        f"{path.relative_to(RECORDS)}: {m.group(1)}"
        for path in records
        for m in re.finditer(r'"\$ref"\s*:\s*"([^"]*)"', path.read_text())
        if not m.group(1).startswith("#")
    )
    assert cross == [], cross


def _bundle_of(root: Path, documents: dict[str, Any]) -> Path:
    """A bundle of exactly these documents, written under ``root``.

    A SYNTHETIC bundle and not a copy of the real one, because what the test below claims
    is a property of the closure rather than of bundle 3.2: three documents say it, and the
    population the claim ranges over is then visible in the test rather than in a sample of
    1,054.  ``bundle.portable`` reads a directory, and ``bundle.document_for`` resolves a
    ``$ref``'s document half as the longest trailing run of segments that IS a document
    here, so a bare ``dep.json`` names one.
    """
    for name, doc in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc))
    return root


def test_a_dependencys_own_raw_bytes_are_in_its_dependents_identity(tmp_path: Path) -> None:
    """Perturb the TARGET's own bytes, and the referrer's identity moves -- no edge read.

    This is the claim ``bundle.source_identities``' docstring makes, checked rather than
    argued, and it is the half that the record's self-containment used to buy: the
    dependency is in the referrer's identity because the closure is taken over the ``$ref``
    strings the documents write, so an upstream edit to a target reaches every document that
    reaches it.  Nothing here consults a map of what depends on what.

    Two controls, and the second is the one this row adds.  A document OUTSIDE the closure
    keeps its identity, so the perturbation is not moving every identity by being a
    perturbation.  And the referrer's own raw bytes did not move at all -- the key would
    have hit, under a key that read the raw document alone and no closure.
    """
    docs: dict[str, Any] = {
        "referrer.json": {"type": "object", "properties": {"a": {"$ref": "dep.json"}}},
        "dep.json": {"type": "string", "maxLength": 4},
        "unrelated.json": {"type": "integer"},
    }
    root = _bundle_of(tmp_path / "before", docs)
    before = bundle.source_identities(root)
    assert sorted(before) == ["dep.json", "referrer.json", "unrelated.json"], sorted(before)

    moved = {**docs, "dep.json": {"type": "string", "maxLength": 5}}
    after = bundle.source_identities(_bundle_of(tmp_path / "after", moved))

    assert after["referrer.json"] != before["referrer.json"], (
        "the target moved and the referrer's identity did not"
    )
    assert after["dep.json"] != before["dep.json"]
    assert after["unrelated.json"] == before["unrelated.json"], "a document outside the closure"
    # And the referrer's own file is byte-identical in both bundles, which is why the
    # closure has to be in the digest rather than the raw document alone.
    assert (
        (tmp_path / "before" / "referrer.json").read_bytes()
        == (tmp_path / "after" / "referrer.json").read_bytes()
    )


#: The documents the inliner perturbation below is measured over.  A SAMPLE and it says so:
#: what it has to cover is the two SHAPES the perturbation can meet -- a document whose
#: record differs from its raw document, which is what an inlining change moves, and one
#: whose record IS its raw document, which nothing can move -- rather than a count.  The
#: share of the graded population in the first shape is read by comparing
#: ``bundle.record`` against ``bundle.read`` over the documents ``test_emit.graded()``
#: names, and it is most of them.
INLINED = (
    "error-details/authorization-required.json",
    "formats/canonical/image.json",
    "media-buy/create-media-buy-async-response-submitted.json",
    "media-buy/decline-proposals-request.json",
)
NOT_INLINED = ("core/pagination-request.json", "core/context.json")


def test_our_own_inlining_moves_the_record_and_moves_no_key() -> None:
    """**THE ROW'S OWN GATE: perturb the INLINER, and no held instance is redrawn.**

    A gate that passes when nothing happens is not a gate, so the inlining is actually
    changed here -- ``bundle._beside`` is where an inlined copy and its referring node's
    keys are combined, and the perturbation makes it spell the result differently at every
    site a cross-document reference was inlined at.  That is a change to our RENDERING of
    the bundle and to nothing else: no document moved, and the accepted set at every node
    is what it was.

    Three claims, in the order that makes the gate one:

    1. the record MOVED for every document that inlines anything, and did not for a
       document that inlines nothing -- so the perturbation reaches the thing it claims to;
    2. ``corpus_key`` handed the RECORD, which is the argument it used to be handed, moves
       for every one of those -- so under the old key every held instance of the inlining
       share of the bundle was redrawn by a change to no document;
    3. ``corpus_key`` handed the IDENTITY moves for none of them, and the identities
       themselves are byte-identical under the perturbation.

    The third is asserted over the identity ``test_emit.pair_of`` actually hands the
    harness, not over a restatement of it here, so a later identity that read the record
    would redden this.
    """
    import test_emit

    sample = (*INLINED, *NOT_INLINED)
    unperturbed = bundle._beside  # noqa: SLF001 -- the seam the perturbation replaces

    def differently(placed: dict, referring: Any, position: Any) -> dict:
        return {**unperturbed(placed, referring, position), "$comment": "spelled otherwise"}

    def keys(records: dict[str, Any]) -> dict[str, str]:
        return {d: corpus_key(r, examples=1, custom_formats={}) for d, r in records.items()}

    before = {d: bundle.record(BUNDLE, d) for d in sample}
    live = {d: test_emit.identity_of(SchemaRef(d, "#")) for d in sample}
    key_before = keys(live)
    try:
        with mock.patch.object(bundle, "_beside", differently):
            after = {d: bundle.record(BUNDLE, d) for d in sample}
            #: Cleared, so a cached answer cannot stand in for the one this perturbation
            #: would produce: an identity read through ``bundle.record`` would move here,
            #: and a held value would hide that it had.
            test_emit.source_identities.cache_clear()
            perturbed = {d: test_emit.identity_of(SchemaRef(d, "#")) for d in sample}
            key_after = keys(perturbed)
    finally:
        test_emit.source_identities.cache_clear()

    # 1. the perturbation reaches the record, where there is an inlined copy to reach.
    assert [d for d in sample if after[d] != before[d]] == list(INLINED)
    assert [d for d in sample if after[d] == before[d]] == list(NOT_INLINED)

    # 2. the OLD key -- this function, handed the record it used to be handed.
    old_before, old_after = keys(before), keys(after)
    assert [d for d in sample if old_after[d] != old_before[d]] == list(INLINED), (
        "the reconstruction of the old key no longer moves; the gate has stopped gating"
    )

    # 3. the key as it stands, over the identity the population hands the harness, read
    #    AGAIN under the live perturbation: the identity is identical and so is every key.
    assert perturbed == live, [d for d in sample if perturbed[d] != live[d]]
    assert key_after == key_before, [d for d in sample if key_after[d] != key_before[d]]

    # And the identity's own reading is pinned to the RAW bundle, which is what an
    # identity read off the packaged record -- yesterday's inlining -- would fail.
    source = bundle.source_identities(BUNDLE)
    assert {d: live[d]["source"] for d in sample} == {d: source[d] for d in sample}


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
    res = check_accepts(
        DOC, accept_of(Faithful), examples=1, corpus=Held({key: []}), identity=DOC
    )
    assert res.outcome == "corpus_rejected", res.outcome
    assert res.examples == 0 and res.round_tripped == 0
    assert "0 instances" in res.detail and "the obligation is 1" in res.detail, res.detail


def test_an_entry_that_cannot_cover_the_obligation_reddens() -> None:
    """Short of the example count, which is the same defect as empty one step along."""
    key = corpus_key(DOC, examples=3, custom_formats={})
    held = Held({key: [{"a": "x", "b": 1}, {"a": "y", "b": 2}]})
    res = check_accepts(DOC, accept_of(Faithful), examples=3, corpus=held, identity=DOC)
    assert res.outcome == "corpus_rejected", res.outcome
    assert res.examples == 0
    # And an entry at the obligation's own count is accepted, so the clause above is
    # judging the COUNT and not the hit.
    whole = Held({key: [{"a": "x", "b": 1}, {"a": "y", "b": 2}, {"a": "z", "b": 3}]})
    assert (
        check_accepts(
            DOC, accept_of(Faithful), examples=3, corpus=whole, identity=DOC
        ).outcome
        == "pass"
    )


def test_a_held_instance_the_document_refuses_reddens_rather_than_being_redrawn() -> None:
    """A stale entry under a live key, which the key alone makes unreachable.

    So this is the defence BEHIND the key: reaching it means the store answered for a key
    it was not asked about, and that is the one way a held corpus could grade a class
    against the wrong document.  Not a silent re-draw -- a store that can do this is
    broken, and a fallback would hide it for as long as it kept happening.
    """
    key = corpus_key(DOC, examples=1, custom_formats={})
    res = check_accepts(
        DOC, accept_of(Faithful), examples=1, corpus=Held({key: [{"a": "x"}]}), identity=DOC
    )
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
    pair = Pair(
        name="held", schema=DOC, model=Faithful, accept=accept_of(Faithful), identity=DOC
    )
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
    first = check_accepts(DOC, accept_of(Faithful), examples=1, corpus=store, identity=DOC)
    second = check_accepts(
        moved, accept_of(Faithful), examples=1, corpus=store, identity=moved
    )
    assert first.corpus_key != second.corpus_key
    assert (first.replayed, second.replayed) == (0, 0)
    assert sorted(store.entries) == sorted({first.corpus_key, second.corpus_key})
    # The moved schema's own key now hits, and the ORIGINAL's still does: a delta holds
    # both, where a whole-corpus rebuild would have replaced one with the other.
    assert (
        check_accepts(moved, accept_of(Faithful), examples=1, corpus=store, identity=moved).replayed
        == 1
    )
    assert (
        check_accepts(DOC, accept_of(Faithful), examples=1, corpus=store, identity=DOC).replayed
        == 1
    )


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
    res = check_accepts(
        undrawable, lambda x: x, examples=1, corpus=store, identity=undrawable
    )
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


def test_no_run_writes_a_corpus_entry_inside_the_checkout() -> None:
    """**The CACHE is still a build artifact, and no run may write the committed floor.**

    What stood here was ``test_the_store_is_a_build_artifact_and_not_a_committed_one``, and
    its claim is withdrawn rather than weakened: ``docs/plan/architecture.md`` ("The drawn
    corpus is COMMITTED", 2026-10-30) puts the drawn instances in the tree, because the
    clause the old argument rested on -- "the gate for it would have to redden on any
    in-flight record change" -- stopped being true when ``harness.corpus_key``'s argument
    became ``bundle.source_identities`` instead of ``bundle.record``.
    ``corpus.CACHE_ROOT``'s comment carries that reasoning and
    :func:`test_every_graded_pair_has_a_committed_entry_under_the_current_key` is the gate
    the old argument said could not exist.

    What survives is the half that is still true and is the reason the floor can be
    trusted: **a RUN writes only the cache.**  ``corpus.Layered.put`` goes to the cache, the
    cache is outside the checkout, and promotion into the floor is ``--write-corpus`` and
    nothing else -- so no suite run leaves the working tree dirty and no lane promotes an
    entry by accident.  Three readings, in the order a reader needs them:

    1. the cache the suite WRITES is not inside this repository at all;
    2. ``.gitignore`` still carries the cache's directory NAME, because ``ADCP_CACHE`` can
       point a cache back inside a checkout and the name is what would then keep it out of
       a commit;
    3. every file the FLOOR holds is TRACKED, which is the committed-ness claim stated as
       a property of the tree: an untracked entry there is a run that wrote the floor, or
       a ``--write-corpus`` nobody committed.
    """
    assert not corpus_module.DIRECTORY.is_relative_to(REPO), (
        f"the shared cache writes inside the checkout: {corpus_module.DIRECTORY}"
    )
    assert corpus_module.STORE.cache.directory == corpus_module.DIRECTORY, (
        "the shared store's writes no longer go to the cache"
    )
    #: What ``ADCP_CACHE`` names, which is the directory a cache pointed back inside a
    #: checkout would be rooted at -- so that is the name ``.gitignore`` has to carry.
    name = corpus_module.CACHE_ROOT.name
    ignored = {line.strip().rstrip("/") for line in (REPO / ".gitignore").read_text().splitlines()}
    assert name in ignored, name
    done = subprocess.run(
        ["git", "check-ignore", "-q", f"{name}/x"], cwd=REPO, capture_output=True
    )
    assert done.returncode == 0, "git does not ignore a cache directory inside the checkout"

    #: And the floor: every entry in it is a file git knows about.  ``git ls-files`` and
    #: not ``git status``, so the claim is about THESE files and is not disturbed by an
    #: unrelated edit elsewhere in the tree.
    floor = corpus_module.FLOOR.directory.relative_to(REPO)
    listed = subprocess.run(
        ["git", "ls-files", "--", str(floor)], cwd=REPO, capture_output=True, text=True
    )
    assert listed.returncode == 0, listed.stderr
    tracked = claimed("tracked committed corpus entries", listed.stdout.split())
    present = {str(p.relative_to(REPO)) for p in corpus_module.FLOOR.files()}
    assert present - tracked == set(), (
        f"untracked entries in the committed corpus -- a run wrote the floor, or a "
        f"--write-corpus was not committed: {sorted(present - tracked)[:5]}"
    )


# --------------------------------------------------------------------------- #
# 5. the committed floor, and the gate the old argument said could not exist
# --------------------------------------------------------------------------- #
#: The example count the POPULATION is graded at, read off the signature that decides it
#: rather than written here.  It is in the key (:func:`corpus_key`), so a default that
#: moved would move every key in the population -- and the gate below would then report
#: the floor short of it, which is the correct reading of a redraw that is owed.  A literal
#: ``1`` here would instead make the gate assert the floor is current under a count nothing
#: grades at.
ACCEPTS_EXAMPLES = inspect.signature(check_pair).parameters["accepts_examples"].default


def live_keys() -> dict[str, str]:
    """Every graded pair's CURRENT corpus key, by the pair's own name.

    The key ``check_pair`` would compute for that pair: ``test_emit.identity_of``'s
    identity, the population's example count and ``test_emit.FORMAT_STRATEGIES``.  Spelled
    from those three rather than by grading the pair, because the gate below has to read
    the floor's currency **without drawing anything** -- a gate that cost a cold run to
    report that a cold run is owed would be unrunnable exactly when it matters.
    """
    import test_emit

    return {
        f"{g.ref.document}{g.ref.pointer}": corpus_key(
            test_emit.identity_of(g.ref),
            examples=ACCEPTS_EXAMPLES,
            custom_formats=test_emit.FORMAT_STRATEGIES,
        )
        for g in test_emit.graded()
    }


def grades_to_an_entry(name: str, into: Path) -> tuple[bool, str]:
    """Does grading this pair against an EMPTY store leave an entry in it.

    **THE ONE EXEMPTION, and it is derived from the code that writes the floor rather than
    restated beside it.**  Not every graded pair CAN hold an entry: ``check_accepts`` holds
    one only where the draw covered the whole obligation and did not error
    (:func:`test_a_draw_that_produced_nothing_is_not_held`), and ``corpus.Store.put``
    declines a value JSON cannot carry back
    (:func:`test_the_store_declines_a_value_it_cannot_hold_faithfully`).  So "every graded
    pair has a committed entry" is false as stated, and the true claim is the one below:
    every pair the suite's own write path WOULD hold an entry for, holds one.

    Two restatements were tried and both are wrong, which is why this one grades instead of
    reading:

    * ``harness.undrawable_formats``, the instrument that admits a ``no_instrument`` pair.
      It does not cover the pairs whose draw fails for its own stated KNOWN CEILING -- a
      node undrawable only IN CONTEXT.  Measured:
      ``core/package-format-snapshot.json#/allOf/0/oneOf/13`` states three
      ``uri``-beside-``^https://`` positions that each draw alone, and the pair's draw
      still reports ``Unsatisfiable`` with 453 of 459 cases filtered.  A gate resting on
      that function would call such a pair unexplained.
    * a declared list of the pairs that hold nothing, which is the second copy the design
      forbids and the thing that goes stale.

    ``into`` is a store of its own, so this neither reads nor warms the shared cache: what
    is being measured is what a draw produces, and a cache hit would answer a different
    question.
    """
    import test_emit

    g = next(x for x in test_emit.graded() if f"{x.ref.document}{x.ref.pointer}" == name)
    probe = corpus_module.Store(into)
    rep = check_pair(
        test_emit.pair_of(g), custom_formats=test_emit.FORMAT_STRATEGIES, corpus=probe
    )
    return bool(probe.keys()), (
        f"{rep.outcome} / accepts {rep.accepts.outcome} at {rep.accepts.examples} of "
        f"{ACCEPTS_EXAMPLES} instances, store held {probe.held} declined {probe.declined}"
    )


def document_bytes(name: str) -> int:
    """The pair's own document's raw size, which is the order the gate explains misses in.

    A cost proxy and nothing else: the draw's cost tracks the size of the node a strategy
    is built over, and this is the cheapest reading correlated with it -- a ``stat`` on the
    bundle, with no record built and no resolution.  Why the ORDER matters is in the gate.
    """
    return (BUNDLE / name.split("#")[0]).stat().st_size


def committed_misses(
    names: Iterable[str], keys: dict[str, str]
) -> tuple[dict[str, str], dict[str, str]]:
    """Of ``names``, the pairs the FLOOR does not answer, and those with no excuse.

    The gate's whole reading, as a function, so the test below asserts on it and
    :func:`test_a_generator_bump_reddens_the_committed_gate` can run the same reading over
    the keys a bumped generator computes and watch it come back red.  A gate whose red
    state is reachable only by a reviewer's imagination is not shown to gate anything.

    ``keys`` is handed in rather than read here for exactly that reason: the two callers
    differ in nothing but which key space they are asking about.

    The FLOOR alone and never ``corpus.STORE``: the obligation is that the entry is
    COMMITTED, and a reading that accepted a cache hit would be green on the machine whose
    cache happened to be warm and red everywhere else.

    **THE SECOND HALF IS LAZY AND CHEAPEST-FIRST, which is what keeps the gate runnable in
    the state it exists to report.**  Explaining a miss costs that pair's own draw
    (:func:`grades_to_an_entry`), and after a bundle bump EVERY pair is a miss -- so an
    eager explanation would cost a full cold run to say that a full cold run is owed.  The
    assertion is "no missing pair would have produced an entry", and ONE counterexample
    settles that, so the misses are explained in ascending document size and the walk stops
    at the first pair that produces one.  Red in seconds; exhaustive only when green, where
    the set left to explain is the pairs that genuinely hold nothing.
    """
    held = corpus_module.FLOOR.keys()
    missing = {name: keys[name] for name in names if keys[name] not in held}
    unexplained: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for n, name in enumerate(sorted(missing, key=lambda name: (document_bytes(name), name))):
            produced, why = grades_to_an_entry(name, Path(tmp) / str(n))
            if produced:
                unexplained[name] = why
                break
    return missing, unexplained


def test_every_graded_pair_has_a_committed_entry_under_the_current_key(pytestconfig) -> None:
    """**THE GATE THE OLD ARGUMENT SAID COULD NOT EXIST.**

    ``tests/corpus.py`` recorded that "the committed corpus is up to date" would be an
    obligation nothing grades, and that any gate for it "would have to redden on any
    in-flight record change, which is correct work".  That was true of the key it was
    written about -- ``bundle.record``, this package's own inlining, so every compiler edit
    invalidated every entry.  ``harness.corpus_key``'s argument is now
    ``bundle.source_identities``: the document's own raw bytes, its reference closure's raw
    bytes, the example count, the format strategies and the generator version.  **A
    compiler edit moves nothing here.  A bundle bump or a generator bump moves everything**,
    and both are deliberate events with a redraw attached.  So this is now gradeable, and
    this is the grade.

    **ONE EQUALITY, BOTH SIDES DERIVED**, which is ``codegen.dump_exemptions``' shape: the
    keys the committed corpus holds are exactly the keys the graded population asks for,
    less the pairs the suite's own write path produces no entry for
    (:func:`grades_to_an_entry`).  Three ways it reddens, and each is a thing that genuinely
    happened:

    * a bundle or generator bump landed and the corpus was not redrawn -- every pair of
      every moved document is missing;
    * a document that did not emit before now emits, so the population grew and nothing
      drew the new pairs;
    * the floor holds an entry nothing asks for any more, which is the residue a bump
      leaves behind and is why the equality is asserted in both directions rather than
      just "every pair is covered".

    **PER PAIR AND NEVER PER DOCUMENT.**  ``graded()`` is pairs, not documents -- the
    reading is in the message this test prints, and at the time it was written it was 2,793
    pairs over 1,054 documents.  A gate keyed on documents would read green with a third of
    the pairs missing, which is the state the floor was in before this row.

    **THE KEY READING COSTS NO DRAW**, for :func:`live_keys`' reason, and the explanation of
    a miss is lazy and cheapest-first (:func:`committed_misses`) -- so the gate reddens in
    seconds on the bump it exists to catch, and pays a draw only for the pairs that are
    genuinely left holding nothing when it is green.  ``--write-corpus`` is the redraw's
    second step and this is where it acts, for the reason ``tests/test_keywords.py``'s grids
    flag acts inside the test that grades them: the thing that knows what the tree should
    contain is the thing that writes it.
    """
    keys = live_keys()
    names = claimed("graded pairs", keys)
    if pytestconfig.getoption("--write-corpus"):
        wrote, absent = corpus_module.STORE.promote(set(keys.values()))
        stale = corpus_module.FLOOR.keys() - set(keys.values())
        for key in sorted(stale):
            corpus_module.FLOOR._path(key).unlink(missing_ok=True)  # noqa: SLF001
        print(
            f"--write-corpus: promoted {wrote}, pruned {len(stale)}, "
            f"{len(absent)} of {len(names)} pair keys answered by neither store"
        )
        return

    missing, unexplained = committed_misses(names, keys)
    extra = corpus_module.FLOOR.keys() - set(keys.values())
    assert unexplained == {}, (
        f"{len(missing)} of {len(names)} graded pairs have no committed entry under their "
        f"current key, and this one WOULD have produced an entry -- so the committed corpus "
        f"is short of the population rather than bounded by it.  Run the suite to fill the "
        f"shared cache, then pytest -n 0 --write-corpus.  {unexplained}"
    )
    assert extra == set(), (
        f"the committed corpus holds {len(extra)} entries the graded population does not "
        f"ask for -- the residue of a bundle or generator bump; pytest --write-corpus "
        f"prunes them"
    )
    print(
        f"committed corpus: {corpus_module.FLOOR.entries()} entries, "
        f"{corpus_module.FLOOR.bytes_held()} bytes of content, over {len(names)} graded "
        f"pairs; {len(missing)} pairs hold nothing, and grading each of those against an "
        f"empty store leaves it empty"
    )


def test_a_generator_bump_reddens_the_committed_gate() -> None:
    """**THE GATE SHOWN RED, by the event it exists to catch.**

    A gate that passes when nothing happens is not a gate, so the bump is actually made
    here: ``harness._DRAW_VERSION`` is the hypothesis and hypothesis-jsonschema versions
    and it is one of ``corpus_key``'s four inputs, so moving it moves every key in the
    population -- which is exactly what a dependency bump does to this corpus, and why the
    pin in ``pyproject.toml`` is exact.

    Two readings, and the second is the one that makes it a demonstration rather than an
    argument:

    1. over the WHOLE population, a bumped generator's keys intersect the committed floor
       in nothing -- so there is no partial-hit story in which the gate stays green;
    2. over :data:`BOTH_WAYS`, the gate's own reading (:func:`committed_misses`) returns
       EMPTY at the live version and returns a MISS FOR EVERY ONE of those pairs under the
       bump, with an unexplained one among them.  That second return value is the thing the
       gate asserts is empty, so this is the gate's assertion failing and not a proxy for
       it.

    The unexplained half is ONE pair rather than all of them, and that is the reading
    :func:`committed_misses` is built to give: it stops at the first counterexample,
    because one pair that would have produced an entry already settles the claim and
    explaining the rest after a bump is the cold run the gate exists to report rather than
    to perform.

    A sample for the second, and it says so: :data:`BOTH_WAYS`' own comment states what it
    covers and why a count is not what is wanted.  The first reading is over the whole
    population, because keys are cheap.
    """
    live = live_keys()
    floor = corpus_module.FLOOR.keys()
    held = claimed(
        "graded pairs the committed floor answers", {n for n, k in live.items() if k in floor}
    )
    #: :data:`BOTH_WAYS` INTERSECTED with what the floor answers, and the member that
    #: drops out says why the intersection is taken rather than asserted away:
    #: ``core/reference-renderer.json#`` is the bundle's one genuinely undrawable position
    #: (``harness.undrawable_formats``' literal-host reading), so the floor holds nothing
    #: for it and nothing CAN be shown red about it.  Named here, so the sample this test
    #: ranges over is a set with members rather than whatever is left.
    sample = claimed("sampled pairs the committed floor answers", set(BOTH_WAYS) & held)
    assert committed_misses(sample, live) == ({}, {}), "the sample is not green to begin with"

    with mock.patch.object(harness, "_DRAW_VERSION", harness._DRAW_VERSION + " +bumped"):
        bumped = live_keys()
    assert set(bumped) == set(live), "the bump moved the population, not the keys"
    assert set(bumped.values()) & floor == set(), (
        "a bumped generator still hits the committed floor: the version is not in the key"
    )
    missing, unexplained = committed_misses(sample, bumped)

    assert set(missing) == sample, sorted(sample - set(missing))
    assert unexplained, "the gate's assertion would still pass under a generator bump"
    assert set(unexplained) <= sample, sorted(set(unexplained) - sample)


def test_the_floor_answers_before_the_cache_and_only_the_cache_is_written(
    tmp_path: Path,
) -> None:
    """``corpus.Layered``'s two rules, each one shown to be the rule it claims to be.

    **Read order is not a performance detail here.**  The two stores are addressed by one
    key, so a key they both hold is a question they both answer -- but the draw is not
    reproducible (``corpus_key``'s docstring measures it), so the two answers can be
    different instances of the same question.  Which store answers therefore decides which
    witness the suite grades, and committing the corpus is only worth anything if that is
    the committed one.  So the floor is given the entry a reader of the tree would see and
    the cache a different one, and the floor's is what comes back.

    **And the write goes to the cache**, which is what keeps a suite run from dirtying the
    tree: the floor is byte-identical afterwards and the new key is in the cache alone.
    """
    floor, cache = corpus_module.Store(tmp_path / "floor"), corpus_module.Store(tmp_path / "cache")
    store = corpus_module.Layered(floor, cache)
    key = "f" * 64
    floor.put(key, [{"committed": True}])
    cache.put(key, [{"committed": False}])
    assert store.get(key) == [{"committed": True}], "the cache answered over the floor"

    store.put("e" * 64, [{"drawn": True}])
    assert floor.keys() == {key}, "a run wrote the committed floor"
    assert cache.keys() == {key, "e" * 64}
    # And a key only the cache holds is still answered: that is what the cache is for.
    assert store.get("e" * 64) == [{"drawn": True}]


def test_a_committed_entry_the_document_refuses_is_not_repaired_by_the_cache() -> None:
    """**Why a committed entry cannot pass quietly when it is wrong.**

    The key says "this is the same question"; ``harness.corpus_defect`` says "the document
    still accepts this", and neither replaces the other -- which is the clause that makes a
    corpus in the tree safe rather than merely cheap.  The composition is new with the
    floor and so is graded here: the floor answers, the DOCUMENT refuses the answer, and
    the pair is ``corpus_rejected`` -- with a correct entry sitting in the cache the whole
    time.

    A fall-through to the cache on a refused floor entry is the one repair that would make
    a stale commit invisible, so it is asserted absent rather than assumed: the verdict is
    the rejection, not the cache's instance.
    """
    key = corpus_key(DOC, examples=1, custom_formats={})
    floor, cache = Held({key: [{"a": "x"}]}), Held({key: [{"a": "x", "b": 1}]})
    res = check_accepts(
        DOC,
        accept_of(Faithful),
        examples=1,
        corpus=corpus_module.Layered(floor, cache),  # type: ignore[arg-type]
        identity=DOC,
    )
    assert res.outcome == "corpus_rejected", res.outcome
    assert res.examples == 0
    assert "refuses held instance 0 on required" in res.detail, res.detail
