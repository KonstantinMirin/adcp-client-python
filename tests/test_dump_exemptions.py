"""The exempt set, graded over the populations that justify it.

``codegen/dump_exemptions.py`` carries the positions where a document refuses the
SDK's own correct output, because D5 and D8 both stay as written and the defect is
upstream (``adcontextprotocol/adcp#8398``).  An exemption inside the only check that
reads generated code is the most dangerous thing in this build, so every claim the
module makes is asserted here over a whole population rather than on an example:

* the set only SHRINKS, pinned by count;
* every entry names its upstream issue;
* every entry's pointer resolves in its packaged document AND the keyword still holds
  the value the entry states -- which is how the set shrinks on its own when upstream
  repairs a position, with no one watching;
* the ``uri`` patterns refused by their own type's output are exactly the ones the module
  DECLARES, re-measured over all eight rather than read off the module;
* every position those patterns reach is exempt, and every exempt position is one of
  theirs -- including the ones the record HOISTED, which is the direction that could not
  fail before ``dump_exemptions._occurrences`` existed;
* the strike explains every dump the document refuses today, and touches nothing else.

D14: a check is exhaustive over a population or it does not exist.  Every denominator
below is asserted non-empty.
"""

from __future__ import annotations

import functools
import json
import pathlib
import re
from typing import Any, NamedTuple

import fresh
import pytest
from hypothesis import HealthCheck, Phase, given, settings
from hypothesis import strategies as st
from pydantic import TypeAdapter

import adcp.types.constraints as public_constraints
from adcp.types._base import SchemaRef, schema_at
from codegen import bundle, constraints, dump_exemptions, harness
from codegen.dump_exemptions import (
    EXEMPT,
    ORIGIN_ONLY,
    PERCENT_FREE,
    PIN,
    UPSTREAM,
    VIOLATING,
    Exemption,
)
from tests.nodeset import claimed

#: The packaged tree, which is the pointer space an entry names: section 6 measures
#: these documents at 0 ``$ref`` occurrences, so what the harness grades is the
#: resolved form and a node reached through a ``$ref`` in the bundle source is an
#: inlined copy here.
#:
#: **The tree a FRESH run emits** (``docs/plan/architecture.md``, 2026-10-29), which is
#: the same tree ``_class_for`` imports its classes out of: an entry's position space and
#: the pair it is checked against have to be one tree, or the ORIGIN_ONLY equality is a
#: comparison between two compilers.  ``tests/fresh.py`` owns it.
PACKAGED = fresh.TREE

#: The bundle source, for the pattern census (section 6).
#:
#: **The bundle a run reads, taken from the ONE declaration of it**
#: (``adcp-client-python-lzzj.11.1``).  This module held its own PUBLISHED literal while
#: every class it grades was emitted from the PATCHED bundle, so its two halves ranged over
#: two different document sets.  Measured against ``fresh.PUBLISHED``: the published
#: directory is portable over 1,054 documents and the run's over 1,059, the five only the
#: patched one holds are documents ``patches/8525`` ADDS, and of the 1,054 they share 211
#: differ -- 200 of those beyond ``$schema``/``title``/``description``.  So the published
#: path is ``adcp-client-python-fr4r``'s lookup error waiting at whichever clause names a
#: document first, and a quietly different answer at each of the others.
SOURCE = fresh.BUNDLE

#: The pairs the dump half refuses on the committed tree, named rather than discovered, so
#: this file does not grade a population another lane is moving.  Each is ``(document,
#: pointer, the exempt keyword the document refuses the dump on)``.
#:
#: **IT WAS THREE AND IS TWO, because the third was REPAIRED rather than exempted.**
#: ``core/provenance.json#/properties/disclosure/properties/jurisdictions/items/properties/render_guidance``
#: on ``minProperties`` was here, and the dump it named was refused for a reason that was
#: OURS: the class resolved ``extra="ignore"`` and dropped the undeclared key the document
#: counts, so an instance whose only key was undeclared dumped to ``{}``.
#: ``docs/plan/rebuild-plan.md`` §8 sentence 4's second consequence (2026-11-03) decides
#: that such a count "is answered by the class KEEPING the keys the document counts",
#: ``lower.objects.declare_object`` takes that reversal, and the pair now passes with no entry
#: at all -- so the entry, its reason, its ancestors below and the exposure bound that
#: graded it are all gone together.  The registry's shrink-only pin fell from 1 to 0.
REFUSED_TODAY = (
    ("core/attestation-issuer.json", "#/oneOf/2", "pattern"),
    ("core/attestation-capabilities.json", "#", "pattern"),
)


def _walk(node: Any, ptr: str = "") -> Any:
    """Every VALUE of a document, by JSON pointer, ``$defs`` and all (section 6).

    **It yielded the MAPPINGS only, and that is what made
    :func:`test_the_strike_removes_only_the_named_keywords` vacuous.**  A ``pattern`` holds
    a string, so the pointer that names it was yielded by nothing: the ``before - after``
    difference over a strike that removes one was the EMPTY SET, the loop that checked
    every removed pointer against the exempt keywords ran zero times, and the value
    comparison at the end of that test -- keyed on ``not isinstance(node, (dict, list))``
    -- compared ``{}`` against ``{}``.  Three assertions, all three true of a strike that
    removed nothing and of a strike that removed the wrong thing.

    Every reader of this function that wanted mappings alone already guards with
    ``isinstance(node, dict)``, so widening it costs them nothing and gives that test the
    difference it was written to enumerate.  A gate that passes when nothing happens is not
    a gate, and this one had the defect in its own walk.
    """
    yield ptr, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk(value, f"{ptr}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{ptr}/{index}")


def _silent_about_extras(node: Any) -> bool:
    """Does this node, and every conjunct draft-07 applies to the same instance, say
    nothing about ``additionalProperties``?

    **Asked of the node as the document APPLIES it, which is §8's pairing rules and not
    a second reading of them.**  Entry four's exposure is about a CLASS's ``extra``
    setting, and D8 derives that from the node the class is paired with: a class cut out
    at ``.../allOf/N`` is paired with the COMPOSITION (§8's third pairing rule), so a
    sibling conjunct's ``additionalProperties: false`` is that class's own and the class
    drops no key.

    Read as the BARE node instead, ``core/package-delivery-metric-value.json`` at
    ``/allOf/1/properties/qualifier`` counts as an exposure it does not have: the
    conjunct's whole text there is ``{"minProperties": 1}``, its sibling conjunct closes
    the object, and the emitted ``Qualifier`` carries
    ``extra='forbid'`` beside its ``PropertyCount`` -- so no instance of it dumps to
    ``{}`` and no document refuses its dump.  That position joined the packaged tree at
    ``adcp-client-python-10l.21``'s fifth instalment, which is the first row to declare a
    class at a conjunct pointer at all.
    """
    if "additionalProperties" in node:
        return False
    return all(_silent_about_extras(c) for c in node.get("allOf", ()) if isinstance(c, dict))


def _packaged(document: str) -> dict:
    return json.loads((PACKAGED / document).read_text())


def _pair(document: str, pointer: str) -> harness.Pair:
    """The graded pair at one position, built the way ``test_emit.pair_of`` builds it.

    Built here rather than imported, so this file names its three pairs literally and
    does not read a helper in the module whose pins another lane is moving.
    """
    ref = SchemaRef(document, pointer)
    model = _model_at(ref)
    return harness.Pair(
        name=f"{document}{pointer}",
        schema=schema_at(ref),
        model=model,
        accept=model.strict_validate,
        document=schema_at(SchemaRef(document, "#")),
        ref=ref,
    )


def _model_at(ref: SchemaRef) -> Any:
    """The emitted class whose ``__adcp_schema__`` IS ``ref``.

    Read off the class rather than named by hand, because the pairing is what makes a
    pair a pair: a class found by name could be pointed at another node and this file
    would grade the wrong thing.
    """
    import importlib

    path = ref.document.removesuffix(".json").replace("-", "_").replace("/", ".")
    module = importlib.import_module(f"adcp.types._schemas.{path}")
    found = [
        value
        for value in vars(module).values()
        if isinstance(value, type) and getattr(value, "__dict__", {}).get("__adcp_schema__") == ref
    ]
    assert len(found) == 1, (ref, [getattr(v, "__name__", v) for v in found])
    return found[0]


def _drawn_dump(pair: harness.Pair) -> Any:
    """The harness's OWN draw for this pair, dumped the way the dump half dumps it.

    ``check_accepts`` is called for the draw rather than re-implemented, so this file
    measures the production instrument: same strategy, same settings, same example
    stream.  It hands back what it drew in ``seen``, and the dump is the harness's
    own default.
    """
    seen: list[Any] = []
    harness.check_accepts(pair.schema, pair.accept, examples=1, seen=seen)
    assert seen, pair.name
    return harness._wire_dump(pair.accept(seen[-1]))  # the production dump


# --------------------------------------------------------------------------- #
# the set itself
# --------------------------------------------------------------------------- #
def test_the_exempt_set_only_shrinks() -> None:
    """An exemption may be removed and never added -- over the part that is PINNED.

    The pin is a literal in the module and not a ``len()`` read back off the tuple,
    because a pin computed from the thing it grades cannot fail.  Removing an entry
    leaves this green; adding one reddens it, and the only way to raise the pin is to
    raise it deliberately in a diff a reviewer sees.

    **It covers the entries that are NOT ``ORIGIN_ONLY``**, and the split is the fix for
    a failure this pin could not express.  The number of positions one upstream pattern
    reaches is a property of how much of the bundle is PACKAGED: every row that emits a
    document carrying that authored node adds a position, so an absolute count over that
    part obliges each of them to raise a shrink-only pin.  That part is derived by
    :func:`test_the_origin_only_part_is_the_packaged_positions` instead, and what is
    pinned here is the part that genuinely is not a function of emission.

    **AND THE PINNED PART IS NOW EMPTY, which is a STATE and not a vacuous assertion.**
    This read ``assert pinned, "the pinned part is empty: this assertion would hold
    vacuously"`` -- the right guard while the part had members, because a ``<=`` over an
    empty list says nothing.  The last member was the ``minProperties`` entry, and
    ``docs/plan/rebuild-plan.md`` §8 sentence 4 removed it by repairing the pair rather
    than exempting it (see :data:`REFUSED_TODAY`).  ``PIN`` is 0, and
    ``tests/test_every_check_names_its_set.py`` says in as many words that ``== 0`` is
    "this part is empty, which the design asks for" and is not a census.  So the claim is
    stated as the EQUALITY it always was -- the pinned part is exactly ``PIN`` entries --
    which is false the moment an entry is added at either end and carries its own
    content at zero: *this SDK exempts no dump for a reason of its own.*  The
    non-emptiness guard moves onto ``EXEMPT`` itself, so an empty registry still cannot
    **THE PARTITION IS "IS THE VALUE A VIOLATING PATTERN", NOT "IS IT ``ORIGIN_ONLY``".**
    It was the second, and that reading would have obliged this pin to rise from 0 to 4 on
    the day ``PERCENT_FREE`` reached an emitted document -- for four positions that are a
    function of EMISSION in exactly the way the split exists to take out of the pin.
    ``ORIGIN_ONLY``'s own declaration had already decided the case ("a second violating
    pattern in a later bundle is a second entry here"), so the predicate names the KIND the
    derived half covers and the pin keeps counting the part that is this SDK's own
    decision.  It is still an EQUALITY at zero and still false the moment an entry is added
    for a reason of this SDK's own."""
    assert EXEMPT, "the registry is empty: every assertion over it would hold vacuously"
    pinned = [e for e in EXEMPT if e.value not in VIOLATING]
    assert len(pinned) == PIN, {
        "the pinned part of the exempt set": [f"{e.document}{e.pointer}" for e in pinned],
        "PIN": PIN,
        "note": "PIN may FALL and may not rise; raising it is a decision in a diff",
    }


def test_the_origin_only_part_is_the_packaged_positions() -> None:
    """The ``ORIGIN_ONLY`` entries ARE the packaged positions stating that pattern.

    Both sides derived, neither a literal count.  The entries were pinned by size, and
    a size has no denominator here: when ``salesagent-j3k2l.43`` made
    ``core/audience-evidence-requirements.json`` emit, its packaged form inlined an
    already-exempted authored node a third time, so the set was one short of the
    positions it exists to cover and the only way to say so was to raise a shrink-only
    pin.

    What this buys, and each one is a thing the count could not do:

    * it **reddens when a position is MISSED**, which is the real obligation, rather than
      when a number moves;
    * it **shrinks on its own** when upstream repairs the pattern -- the value stops
      matching and both sides fall together, which is the mechanism this module already
      relies on for every other entry;
    * it **grows only with emission**, and the growth is explained by one upstream issue
      rather than by a judgement call.

    It compares one exact string against the packaged tree, so it is still the literal
    set of positions this module's first rule requires and not a predicate over regexes.

    **THE LEFT SIDE IS THE PACKAGED DOCUMENT'S OWN TEXT, WHICH IS THE SPACE AN ENTRY
    NAMES, AND IT USED TO BE THE APPLIED ONE.**  That mismatch is what made this equality
    unsatisfiable rather than merely red: it walked ``schema_at``'s expansion, where the
    record's storage is put back, so a node the record hoisted was counted once per
    OCCURRENCE -- 146 positions against 74 of the text, three of them for one authored node
    at three places in one document.  An entry per occurrence is not a position of any
    shipped file, and 97 of those entries could never have been the one that acted: the
    expansion shares one object per stored subtree, so the first strike removes the keyword
    at all of them.  So the derivation reads the document the way the entry does, and
    ``dump_exemptions._occurrences`` is where the two spaces meet -- asserted separately,
    through the production entry point, by
    :func:`test_an_entry_at_a_hoisted_position_lands_where_the_pair_reads_it`.

    **AND BOTH SIDES RANGE OVER WHAT REACHES A PAIR**, which is the population the strike
    can act in: a document the tree grades no pair for produces no dump, so a position in
    it refuses nothing and an entry at it could never act.  One position is outside the set
    for exactly that reason and it is named in :data:`EXEMPT`'s own comment.  Derived off
    the graded tree rather than off ``dump_exemptions``' own crossing, so this equality and
    the mechanism it grades do not agree with each other by construction.
    """
    positions = claimed(
        "packaged positions whose pattern is ORIGIN_ONLY and that reach a pair",
        _packaged_text_positions(lambda node: node.get("pattern") == ORIGIN_ONLY),
    )
    exempted = claimed(
        "ORIGIN_ONLY entries of EXEMPT",
        {f"{e.document}#{e.pointer}" for e in EXEMPT if e.value == ORIGIN_ONLY},
    )
    assert exempted == positions, {
        "reaches a pair and is not exempt": sorted(positions - exempted),
        "exempt and reaches no pair": sorted(exempted - positions),
    }


@functools.cache
def _graded_documents() -> frozenset[str]:
    """The documents the tree grades a pair for, which is what "reaches a pair" ranges over.

    Read off ``test_emit.graded()`` -- the suite's one reading of the emitted tree -- and
    not off the packaged directory: ``fresh.TREE`` carries the resolved JSON for 1,059
    documents and the tree grades a pair for 1,020 of them, so "is in the package" and
    "reaches a pair" are different populations and the difference is where an inert entry
    would hide.

    **The two figures were 1,054 and 1,015 and were read off the PUBLISHED bundle**, which
    is the defect ``adcp-client-python-lzzj.11.1`` moved this module off: ``fresh.TREE`` has
    always come from the patched bundle, so the smaller number never described the directory
    the sentence names.  Re-measured here -- ``len(list(fresh.TREE.rglob("*.json")))`` and
    ``len({ref.document for ref, *_ in test_emit.graded()})`` over 2,589 graded pairs.
    """
    import test_emit  # the tree reader, one reading for the whole suite

    return frozenset(g.ref.document for g in test_emit.graded())


def _packaged_text_positions(wanted: Any) -> set[str]:
    """``"<document>#<pointer>"`` for every node of a GRADED document that ``wanted`` picks.

    The document's own TEXT, which is the space :class:`Exemption` names: read with
    :func:`json.loads` off the packaged file and walked by :func:`_walk`, so a subtree the
    record STORED is at its ``definitions/Shared<N>`` pointer here and not at the positions
    the document applies it.  ``bundle.nodes(schema_at(...))`` is the other space and is
    what this replaced; see :func:`test_the_origin_only_part_is_the_packaged_positions`.
    """
    return {
        f"{document}#{pointer}"
        for document in sorted(_graded_documents())
        for pointer, node in _walk(_packaged(document))
        if isinstance(node, dict) and wanted(node)
    }


def test_every_entry_names_its_upstream_issue() -> None:
    """Nothing here may read as this SDK's own decision about a document.

    D5 and D8 both stay as written, so every entry is a position waiting on upstream,
    and the issue number is what says so to the next reader.
    """
    assert EXEMPT, "the denominator is empty: no entry would be graded"
    for entry in EXEMPT:
        assert UPSTREAM in entry.reason, (entry.document, entry.pointer, entry.reason)


@pytest.mark.parametrize("entry", EXEMPT, ids=lambda e: f"{e.document}{e.pointer}")
def test_every_entry_resolves_and_still_states_its_value(entry: Exemption) -> None:
    """A stale entry is reported by name, and THIS is how the set shrinks by itself.

    The entry states which keyword it strikes and what that keyword holds.  When
    upstream repairs the position -- ``^https://[^/?#@]+$`` to
    ``^https://[^/?#@]+/?$``, or a ``minProperties`` the node drops -- the value stops
    matching and this reddens until the entry is removed.  So the set does not depend
    on anybody remembering to revisit it: the repair itself reddens the build.
    """
    node = dump_exemptions._at(  # the resolution under test
        _packaged(entry.document), dump_exemptions._path(entry.pointer)
    )
    assert isinstance(node, dict), (entry.document, entry.pointer, "pointer does not resolve")
    assert entry.keyword in node, (entry.document, entry.pointer, entry.keyword, sorted(node))
    assert node[entry.keyword] == entry.value, (entry.keyword, node[entry.keyword], entry.value)


def _graded_positions() -> set[str]:
    """``"<document>#<pointer>"`` for every class and alias the emitted tree carries.

    The pairing read off the classes themselves, the way ``check_pair``'s caller reads
    it: a class from the module that DEFINES it, and D2's root-scalar row from the
    module that carries the ``__adcp_schema__`` for its alias.
    """
    import importlib
    import pkgutil

    import adcp.types._schemas as pkg

    out: set[str] = set()
    for info in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        module = importlib.import_module(info.name)
        for value in vars(module).values():
            if not isinstance(value, type):
                continue
            ref = value.__dict__.get("__adcp_schema__")
            if isinstance(ref, SchemaRef) and value.__module__ == info.name:
                out.add(f"{ref.document}#{ref.pointer.lstrip('#')}")
        ref = vars(module).get("__adcp_schema__")
        if isinstance(ref, SchemaRef):
            out.add(f"{ref.document}#{ref.pointer.lstrip('#')}")
    return out


# **THE ``minProperties`` EXPOSURE BOUND IS GONE, AND SO IS THE EXPOSURE.**
# ``test_the_minproperties_entry_is_the_only_copy_that_is_a_pairs_own_node`` stood here.
# It bounded a LATENT defect: the exempt node is inlined all over the packaged tree, and
# at every copy nested inside a larger pair the dump would refuse as soon as a draw gave
# ``render_guidance`` exactly one key and that key undeclared.  The invariant it asserted
# -- exactly one copy is a graded pair's own node -- was the honest statement of a risk
# nobody had retired.
#
# It is retired now rather than re-pinned.  The refusal was never the node's: our own
# ``extra="ignore"`` dropped the key the document counts, and ``docs/plan/rebuild-plan.md``
# §8 sentence 4 answers such a count by the class KEEPING those keys.  With
# ``extra="allow"`` resolved at every node a property count rides over, no copy of that
# node -- own-node or nested, drawn or undrawn -- can dump to ``{}`` by losing a key it
# counts.  So there is no exposure left to bound, and a bound over an empty exposure is
# the vacuous check §8's last paragraph forbids.
#
# What replaces it is the pair passing on its own merits, which
# ``test_check_pair_passes_the_exempt_pair_and_reports_why`` grades for the entries that
# remain and ``test_an_unexempt_pair_reports_no_exemption_and_still_passes`` grades for a
# pair with no entry -- the shape ``core/provenance.json`` now has.


# --------------------------------------------------------------------------- #
# the measurement the pattern entries rest on
# --------------------------------------------------------------------------- #
def _uri_patterns() -> dict[str, int]:
    """Every ``pattern`` the bundle states at a ``format: uri`` node, with its count.

    **The instrument is "any node carrying ``format: uri``"**, which is D5's own and
    gives its figures: 8 distinct patterns over 73 sites.  Additionally requiring
    ``type: string`` gives 7 over 71 and misses
    ``core/macro-bearing-url.json#/anyOf/1`` -- the ``^https?://`` position D5 singles
    out as the one whose author admitted ``http`` deliberately -- because that node
    states no ``type`` of its own.  Narrowing the instrument here would drop the one
    pattern most worth grading.
    """
    out: dict[str, int] = {}
    for document in sorted(bundle.portable(SOURCE)):
        for _, node in _walk(bundle.read(SOURCE, document)):
            if isinstance(node, dict) and node.get("format") == "uri" and "pattern" in node:
                out[node["pattern"]] = out.get(node["pattern"], 0) + 1
    return out


def test_the_bundles_uri_pattern_population_is_the_one_d5_states() -> None:
    """D5's distinct ``format: uri`` patterns, as the SET the census below draws over.

    Named and asserted non-empty rather than sized: the two patterns the exemption
    turns on are asserted BY NAME, which is what the three counts were standing in for
    -- a bundle version's reading of how many sites each one occupies says nothing
    about whether the two patterns the decision names are still there.
    """
    patterns = claimed("distinct format:uri patterns in the bundle", _uri_patterns())
    assert constraints.HTTPS_ONLY in patterns, sorted(patterns)
    for declared in VIOLATING:
        # Each pattern the exemption is keyed on, by name: a bundle that stops stating one
        # leaves its entries covering positions no document holds, and the census below
        # would then be measuring a pattern nothing uses.
        assert declared in patterns, (declared, sorted(patterns))


#: Draws per pattern.  **40 is not enough and the number was measured, not guessed.**
#: At 40 draws two independent streams disagreed about how many of the eight patterns
#: their own type's output refuses -- one said one, the other said two -- which is the
#: same "passes by luck of the draw" failure the latent entry exists for, arriving in
#: the instrument instead of in the dump half.  At 500 the two violating patterns are
#: found by both, and the rates separate them: one violates 96 of 96 round-tripped
#: values and the other 15 of 348.
DRAWS = 500


class Roundtrip(NamedTuple):
    """How a pattern's own type's output fares against it: a rate, not a verdict.

    ``refused_in`` is the count the TYPE rejected on the way in -- the input direction,
    which D4 gives to the schema half -- and it is carried so ``round_tripped`` can be
    asserted non-empty.  A pattern whose every draw was refused on the way in would
    report zero violations while measuring nothing.
    """

    round_tripped: int
    violated: int
    refused_in: int
    examples: tuple[tuple[str, str], ...]


def _roundtrip(pattern: str, examples: int = DRAWS) -> Roundtrip:
    """Strings the pattern admits, round-tripped through the type the EMITTER chooses.

    Drawn rather than written: written candidates for eight patterns would be eight
    guesses about what each one means, and a wrong guess shows up as a pattern graded
    only on values that happen to round-trip.  The type comes from
    ``constraints.url_type``'s own rule, so this grades the emitter's choice and not a
    type chosen here.  ``re.search`` and not ``fullmatch``, because search is what
    JSON Schema's ``pattern`` means.
    """
    adapter = TypeAdapter(
        public_constraints.AdCPUrl
        if pattern == constraints.HTTPS_ONLY
        else public_constraints.HttpUrl
    )
    counts = {"round_tripped": 0, "violated": 0, "refused_in": 0}
    bad: list[tuple[str, str]] = []

    @settings(
        max_examples=examples,
        deadline=None,
        database=None,
        derandomize=True,
        phases=[Phase.generate],
        suppress_health_check=list(HealthCheck),
    )
    @given(st.from_regex(pattern))
    def body(value: str) -> None:
        try:
            out = adapter.dump_python(adapter.validate_python(value), mode="json")
        except Exception:  # refused on the way IN, which is D4's half
            counts["refused_in"] += 1
            return
        counts["round_tripped"] += 1
        if re.search(pattern, out) is None:
            counts["violated"] += 1
            if len(bad) < 2:
                bad.append((value, out))

    body()
    return Roundtrip(
        counts["round_tripped"], counts["violated"], counts["refused_in"], tuple(bad)
    )


def _packaged_positions(pattern: str) -> list[str]:
    """Every position of a GRADED document stating ``pattern`` at a ``format: uri`` node.

    A position that reaches a pair is the only one the strike can act in, which is what
    makes a violating pattern with no position here upstream's problem and not an
    exemption.

    **IT RANGED OVER EVERY FILE IN THE PACKAGE AND NOW RANGES OVER THE GRADED DOCUMENTS**,
    which is this function's own name followed: the test it feeds is
    ``..._that_reaches_a_pair_is_exempt``, and ``PACKAGED.rglob`` answers "is in the
    package" -- 1,054 documents against the 1,015 the tree emits a class for.  The
    difference is not hypothetical: ``core/async-response-refs/media-buy/
    get-products-async-response-input-required.json`` states :data:`ORIGIN_ONLY` and the
    tree grades no pair for it, so an entry there could never act and the equality would
    have demanded one.
    """
    return sorted(
        f"{document}#{ptr}"
        for document in sorted(_graded_documents())
        for ptr, node in _walk(_packaged(document))
        if isinstance(node, dict) and node.get("format") == "uri" and node.get("pattern") == pattern
    )


def test_every_violating_uri_pattern_that_reaches_a_pair_is_exempt() -> None:
    """**The measurement the pattern entries rest on, over all eight patterns.**

    Every pydantic URL type is backed by the Rust ``url`` crate, which normalizes:
    it gives an authority-only URL a path of ``/`` -- RFC 3986 S6.2.3's normalized
    form -- lowercases the host, and percent-encodes a byte the authority may not
    carry raw.  So a pattern that forbids what normalization PRODUCES cannot be
    satisfied by the type's output, whatever it was handed.

    **Two of the eight are violated, not one**, and the earlier reading of "exactly
    one" was a 40-draw artifact.  The property asserted is therefore not a count of
    violating patterns but the one that decides the SDK's output: every violating
    pattern that reaches a packaged document is exempt, and every exempt position
    belongs to a violating pattern.  Both directions redden.

    * A second violating pattern in a later bundle, at a position the emitter emits,
      reddens here rather than waiting for a draw to find it in the dump half.
    * When upstream repairs a pattern, it leaves this set and
      ``test_every_entry_resolves_and_still_states_its_value`` reddens on the entry
      until it is removed.

    **:data:`PERCENT_FREE` IS THE SECOND VIOLATOR AND IT IS EXEMPT NOW, WHICH IS THIS
    TEST'S OWN SENTENCE BEING KEPT.**  What stood here read: "it is deliberately NOT
    exempt.  The class forbids ``%``, so percent-encoding a ``{`` or an ``@`` breaks it --
    measured at 4 of 380 round-tripped draws ... **the reason it is not exempt is reach,
    not rate**: its one site is ``core/agent-reporting-destination-state.json#/properties/
    setup/properties/setup_url``, that document is not emitted, so it reaches no pair ...
    If the emitter starts emitting the document, the first assertion reddens and a human
    decides whether the set grows."  The emitter emits it, and ``core/principal-state.json``
    and the two principal responses besides -- four positions, all four in documents the
    tree grades -- so the condition that paragraph named has arrived and the last assertion
    it describes is FALSE as a fact about the tree.

    The decision is that the set grows, and the ground is that the defect is the SAME ONE:
    the pattern forbids a character URL normalisation PRODUCES, so the document refuses the
    canonical spelling of a value it accepts.  ``dump_exemptions._PCT`` names the character
    and the RFC, and the entry names the same upstream issue every other entry names --
    which is the only ground this set may grow on.  It does not raise the shrink-only pin,
    because the pin is keyed on the KIND and ``ORIGIN_ONLY``'s own declaration had already
    decided this case: "a second violating pattern in a later bundle is a second entry
    here, taken the same way over the whole pattern population."

    **What replaces the last assertion is the stronger thing it was standing in for**: the
    patterns MEASURED to violate are exactly the ones :data:`VIOLATING` declares.  Both
    directions redden -- a third violator in a later bundle is unexempted and named here
    rather than waiting for a draw to find it in the dump half, and a pattern upstream
    repairs leaves a declared key with nothing violating under it and its entries stale.

    **No drawn RATE is asserted here, deliberately.**  A derandomized stream is a
    function of this function's identity and of the pinned ``hypothesis`` version, so
    a rate assertion would redden on a rename -- a defect in the instrument wearing
    the clothes of a defect in the SDK.  What is asserted is a certainty (every
    round-tripped value refused, for ``ORIGIN_ONLY``), one set equality against the
    module's declaration, and one fact read off documents.
    """
    patterns = _uri_patterns()
    assert patterns, "the denominator is empty: no uri pattern would be graded"
    measured = {p: _roundtrip(p) for p in sorted(patterns)}
    for pattern, got in measured.items():
        assert got.round_tripped, (pattern, got, "no value survived the type: nothing graded")
    violating = {p: got for p, got in measured.items() if got.violated}
    reaching = sorted(pos for p in violating for pos in _packaged_positions(p))
    exempt = sorted(f"{e.document}#{e.pointer}" for e in EXEMPT if e.keyword == "pattern")
    assert reaching == exempt, {
        "violating patterns": {p: (g.violated, g.round_tripped) for p, g in violating.items()},
        "positions they reach": reaching,
        "exempt": exempt,
    }
    # The measured violating set IS the declared one, in both directions: the module's
    # literal patterns are what the entries are keyed on, and a draw deciding membership
    # without the declaration agreeing is an exemption resting on a stream.
    assert set(violating) == set(VIOLATING), {
        "measured to violate": {p: (g.violated, g.round_tripped) for p, g in violating.items()},
        "declared in VIOLATING": sorted(VIOLATING),
    }
    # ORIGIN_ONLY is not violated at a RATE: it is unsatisfiable, and that is the
    # ground D5 keeps the URL type on.  Every value the type accepts and re-emits is
    # refused by it, so no conforming URL library could satisfy it.
    origin = measured[ORIGIN_ONLY]
    assert origin.violated == origin.round_tripped, origin
    # PERCENT_FREE is violated at a rate and REACHES pairs, which is the pair of facts
    # that moved it into the set.  The reach is read off the tree, so no draw decides it.
    assert _packaged_positions(PERCENT_FREE), PERCENT_FREE


# --------------------------------------------------------------------------- #
# what the strike does, and what it does not
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("document", "pointer", "keyword"), REFUSED_TODAY, ids=lambda x: str(x)[:60]
)
def test_the_strike_explains_the_refused_dump_and_the_document_still_refuses_it(
    document: str, pointer: str, keyword: str
) -> None:
    """**Both halves, on the harness's own draw, through the harness's own validator.**

    The first assertion is what keeps this from being a test of nothing: the DOCUMENT
    as it stands still refuses this dump, so the pair really is red and the strike is
    really what explains it.  Without that, a pair whose defect was fixed elsewhere
    would leave the second assertion green and this file would report an exemption
    doing work nobody needs.

    The second is the exemption: the dump conforms to the document with exactly the
    named keyword struck at exactly the named position.

    **The instance is drawn from, and the first check validates against, the document
    AS IT STANDS.**  Only the DUMP is validated against the struck copy.  That split
    is the whole exemption -- nothing about what the class accepts moves, so the
    accepts half is not relaxed by any of this.
    """
    pair = _pair(document, pointer)
    back = _drawn_dump(pair)
    assert harness.conforms(pair.schema, back) is False, (pair.name, back)
    relaxed = dump_exemptions.struck(pair.schema, document, pointer)
    assert relaxed is not pair.schema, pair.name
    assert harness.conforms(relaxed, back) is True, (
        pair.name,
        keyword,
        harness.violated_keywords(relaxed, back),
    )


@pytest.mark.parametrize(
    ("document", "pointer", "keyword"), REFUSED_TODAY, ids=lambda x: str(x)[:60]
)
def test_the_strike_removes_only_the_named_keywords(
    document: str, pointer: str, keyword: str
) -> None:
    """The struck copy differs from the document in the exempt keywords and nowhere else.

    A strike that removed a sibling keyword, or struck at the wrong depth, would widen
    the check in a way the pass/fail of the pair cannot show -- the pair would go green
    either way.  So the difference is enumerated: every pointer present in one and not
    the other has to be an entry's own keyword.

    **IT IS AN EQUALITY AGAINST THE POSITIONS THE STRIKE SAID IT WOULD TOUCH**, where it
    used to be "the last segment of each removed pointer is a keyword some entry names".
    That form was true of a strike at the wrong DEPTH -- any ``pattern`` anywhere scored --
    and the set it computed was used for nothing but a non-emptiness guard.  The positions
    come from ``dump_exemptions._strikes``, which answers in the APPLIED space, so the
    comparison is between where the module says it struck and where the document changed.
    """
    pair = _pair(document, pointer)
    relaxed = dump_exemptions.struck(pair.schema, document, pointer)
    before = {ptr for ptr, _ in _walk(pair.schema)}
    after = {ptr for ptr, _ in _walk(relaxed)}
    assert not after - before, after - before
    expected = {
        "/".join(("", *where, entry.keyword))
        for entry, where in dump_exemptions._strikes(document, pointer)
    }
    assert expected, (document, pointer, "no entry applies, so nothing is being graded")
    removed = before - after
    assert removed == expected, {"removed": sorted(removed), "the strike named": sorted(expected)}
    for gone in removed:
        assert gone.rsplit("/", 1)[-1] in {e.keyword for e in EXEMPT}, (gone, removed)
    # Values, not only shapes: every node that survives in both holds what it held.
    kept = {
        ptr: json.dumps(node, sort_keys=True, default=repr)
        for ptr, node in _walk(pair.schema)
        if not isinstance(node, (dict, list))
    }
    now = {
        ptr: json.dumps(node, sort_keys=True, default=repr)
        for ptr, node in _walk(relaxed)
        if not isinstance(node, (dict, list))
    }
    assert {k: v for k, v in kept.items() if k in now} == {
        k: v for k, v in now.items() if k in kept
    }


@pytest.mark.parametrize(
    ("document", "pointer", "keyword"), REFUSED_TODAY, ids=lambda x: str(x)[:60]
)
def test_check_pair_passes_the_exempt_pair_and_reports_why(
    document: str, pointer: str, keyword: str
) -> None:
    """**The WIRING, through the production entry point, which nothing else grades.**

    Everything above grades the set and the strike.  This grades the one thing they
    cannot: that ``check_pair`` actually reaches them.  Before the ``ref`` was threaded
    from ``check_pair`` into ``check_accepts``, every test in this file passed while the
    suite's own verdict for these three pairs was unchanged -- the strike was correct
    and connected to nothing.

    Both halves again, and the second is the precedent the lead held me to: the pair
    PASSES, and it says why.  An exemption the harness does not report is one no reader
    of a green pair can see, so ``dump_exempt`` carries the positions in force and a
    non-empty list beside a pass is a CONDITIONAL pass.
    """
    pair = _pair(document, pointer)
    report = harness.check_pair(pair)
    assert report.outcome == "pass", (report.outcome, report.accepts.detail)
    assert report.accepts.round_tripped == 1, report.accepts
    assert report.accepts.dump_exempt, report.accepts
    assert all(label.endswith(f"/{keyword}") for label in report.accepts.dump_exempt), (
        report.accepts.dump_exempt,
        keyword,
    )


def test_an_unexempt_pair_reports_no_exemption_and_still_passes() -> None:
    """``dump_exempt`` is empty for a pair with no entry, which is what makes a
    non-empty one readable as a conditional pass rather than as noise every pair
    carries."""
    report = harness.check_pair(_pair("core/pagination-request.json", "#"))
    assert report.outcome == "pass", (report.outcome, report.accepts.detail)
    assert report.accepts.dump_exempt == [], report.accepts.dump_exempt


#: The pairs an exempt position lies INSIDE but whose own dump does not need it: an
#: ancestor whose drawn instance never reached the node.  Named, because the first
#: version of the reported field recorded all eight pairs an entry applies to and that
#: made a conditional pass unreadable -- five of the eight pass on their own merits.
#:
#: **The three ``core/provenance.json`` ancestors are gone with their entry**, which is
#: the ``minProperties`` repair recorded at :data:`REFUSED_TODAY`: an ancestor of a
#: position that is no longer exempt is not an ancestor of anything this file grades.
ANCESTORS = (
    ("core/attestation-issuer.json", "#"),
    ("core/attestation-capabilities.json", "#/properties/accepted_issuers/items"),
)


@pytest.mark.parametrize(("document", "pointer"), ANCESTORS, ids=lambda x: str(x)[:60])
def test_an_ancestor_of_an_exempt_position_reports_nothing_it_did_not_need(
    document: str, pointer: str
) -> None:
    """An entry applies to every pair whose node CONTAINS it, and must.

    An ancestor pair's dump carries the nested node, which is exactly why
    ``core/attestation-capabilities.json#`` is refused for a position authored in
    ``core/attestation-issuer.json``.  So ``applying_to`` matching by prefix is right.

    What would be wrong is REPORTING it everywhere it applies.  These five pairs
    contain an exempt position and pass without it, because their drawn instance never
    reached the node -- so the strike is available to them and they do not use it.
    ``dump_exempt`` records what the dump NEEDED, which keeps a non-empty list meaning
    "this pair passes conditionally" rather than "an exemption exists somewhere below
    me".  Both halves are asserted: the entry does apply, and nothing is reported.
    """
    assert dump_exemptions.applying_to(document, pointer), (document, pointer)
    report = harness.check_pair(_pair(document, pointer))
    assert report.outcome == "pass", (report.outcome, report.accepts.detail)
    assert report.accepts.dump_exempt == [], report.accepts.dump_exempt


#: The one hoisted position this file grades by name, and the pair that reads it.  Chosen
#: because it is the position ``adcp-client-python-lzzj.2`` was diagnosed on: the record
#: stores ``core/attestation-issuer.json``'s origin branch under ``definitions/Shared11``
#: and the pair at ``#/properties/attestation_evaluations/items`` applies it under
#: ``/properties/reference``, so the two pointers below are one node with two spellings and
#: nothing but ``_occurrences`` relates them.
HOISTED = (
    "core/audience-evidence-selection.json",
    "#/properties/attestation_evaluations/items",
    "/definitions/Shared11/properties/issuer/oneOf/2/properties/origin",
    "/properties/reference/properties/issuer/oneOf/2/properties/origin",
)


def test_an_entry_at_a_hoisted_position_lands_where_the_pair_reads_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**An entry at a position the record HOISTED reaches the pair, and strikes it.**

    This is the direction that was structurally unfailable, so it is asserted in both:
    the premise that the two spellings really are different, and the effect that the
    strike lands anyway.

    The premise first, because without it this passes over a position that was never
    hoisted and says nothing: the entry's pointer is in the packaged document's own TEXT,
    the pair's is in the applied space, and a PREFIX comparison between them -- which is
    what :func:`dump_exemptions.applying_to` did -- answers that the entry is not inside
    the pair.  That assertion is the old mechanism, written out, and it holds: the strike
    reaching the pair anyway is the whole repair.

    Then the effect, twice.  Once on the entry the registry carries, through
    :func:`dump_exemptions.applying_to`, :func:`dump_exemptions.labels` and
    :func:`dump_exemptions.struck` -- the three production entry points -- which measures
    that an exemption at a hoisted position is in force today.  And once by INJECTING an
    entry for a keyword no entry names, which is the half that cannot be satisfied by the
    population happening to be right: the probe strikes ``format`` at the same hoisted
    node, the keyword disappears at the position the pair reads, and the pair's own schema
    is left holding it.  Before ``_occurrences``, both calls answered ``()`` and ``struck``
    returned the schema by identity with the keyword exactly where it was.
    """
    document, pointer, stored, applied = HOISTED
    at = dump_exemptions._path(pointer)

    # THE PREMISE.  The text's pointer is not under the pair's -- this is the old
    # mechanism's own comparison -- and the document nevertheless applies the node inside
    # the pair, which is what makes the two spellings one node.
    assert dump_exemptions._path(stored)[: len(at)] != at, (stored, pointer)
    schema = _pair(document, pointer).schema
    node = dump_exemptions._at(schema, dump_exemptions._path(applied))
    assert isinstance(node, dict), (applied, "the pair does not apply the node here")
    assert node["pattern"] == ORIGIN_ONLY, node
    assert node["format"] == "uri", node

    # THE EFFECT, on the registry's own entry and through the production entry points.
    entries = [e for e in EXEMPT if e.document == document and e.pointer == stored]
    assert len(entries) == 1, entries
    assert dump_exemptions.applying_to(document, pointer) == (entries[0],)
    assert dump_exemptions.labels(document, pointer) == [f"{document}#{stored}/pattern"]
    relaxed = dump_exemptions.struck(schema, document, pointer)
    assert relaxed is not schema, document
    struck_node = dump_exemptions._at(relaxed, dump_exemptions._path(applied))
    assert "pattern" not in struck_node, struck_node
    assert struck_node["format"] == "uri", struck_node  # and nothing beside it moved

    # THE EFFECT, on an entry this test puts there.  A keyword no entry names, so the
    # assertion cannot be carried by the population: it is the MECHANISM being graded.
    probe = Exemption(
        document=document,
        pointer=stored,
        keyword="format",
        value="uri",
        reason=f"this test's own probe, struck to grade the mechanism; {UPSTREAM}",
        latent=True,
    )
    monkeypatch.setattr(dump_exemptions, "EXEMPT", (*EXEMPT, probe))
    dump_exemptions._occurrences.cache_clear()  # the map is keyed on the document alone
    try:
        assert probe in dump_exemptions.applying_to(document, pointer)
        probed = dump_exemptions.struck(schema, document, pointer)
        at_node = dump_exemptions._at(probed, dump_exemptions._path(applied))
        assert "format" not in at_node, at_node
        assert "pattern" not in at_node, at_node  # the registry's entry still landed
    finally:
        monkeypatch.undo()
        dump_exemptions._occurrences.cache_clear()
    # The strike copies: the pair's own schema never lost the keyword.
    assert dump_exemptions._at(schema, dump_exemptions._path(applied))["format"] == "uri"


def test_a_pair_with_no_entry_is_returned_by_identity() -> None:
    """The 1,051 pairs that have no entry pay no copy and cannot be altered at all.

    Identity and not equality, because that is the property the harness will rely on
    to tell an exempted pair from an ordinary one without asking twice -- and because
    an equal-but-copied schema would make a future strike at the wrong depth invisible
    here.
    """
    document = "core/pagination-request.json"
    pair = _pair(document, "#")
    assert dump_exemptions.struck(pair.schema, document, "#") is pair.schema, document
    assert dump_exemptions.applying_to(document, "#") == ()
