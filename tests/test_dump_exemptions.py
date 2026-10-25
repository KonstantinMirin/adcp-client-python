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
* **exactly one** of the eight ``uri`` patterns the bundle states is refused by its own
  type's output, re-measured over all eight rather than read off the module;
* the strike explains every dump the document refuses today, and touches nothing else.

D14: a check is exhaustive over a population or it does not exist.  Every denominator
below is asserted non-empty.
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import Any, NamedTuple

import pytest
from hypothesis import HealthCheck, Phase, given, settings
from hypothesis import strategies as st
from pydantic import TypeAdapter

import adcp.types.constraints as public_constraints
from adcp.types._base import SchemaRef, schema_at
from codegen import bundle, constraints, dump_exemptions, harness
from codegen.dump_exemptions import EXEMPT, ORIGIN_ONLY, PIN, UPSTREAM, Exemption

#: The packaged tree, which is the pointer space an entry names: section 6 measures
#: these documents at 0 ``$ref`` occurrences, so what the harness grades is the
#: resolved form and a node reached through a ``$ref`` in the bundle source is an
#: inlined copy here.
PACKAGED = pathlib.Path("src/adcp/types/_schemas")

#: The bundle source, for the pattern census.  Every measurement in this build is
#: taken over ``schemas/cache/<version>/`` (section 6).
SOURCE = pathlib.Path("schemas/cache/3.2")

#: The three pairs the dump half refuses on the committed tree, named rather than
#: discovered, so this file does not grade a population another lane is moving.  Each
#: is ``(document, pointer, the exempt keyword the document refuses the dump on)``.
REFUSED_TODAY = (
    ("core/attestation-issuer.json", "#/oneOf/2", "pattern"),
    ("core/attestation-capabilities.json", "#", "pattern"),
    (
        "core/provenance.json",
        "#/properties/disclosure/properties/jurisdictions/items/properties/render_guidance",
        "minProperties",
    ),
)


def _walk(node: Any, ptr: str = "") -> Any:
    """Every node of a document, by JSON pointer, ``$defs`` and all (section 6)."""
    if isinstance(node, dict):
        yield ptr, node
        for key, value in node.items():
            yield from _walk(value, f"{ptr}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{ptr}/{index}")


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
    return harness._wire_dump(pair.accept(seen[-1]))  # noqa: SLF001 -- the production dump


# --------------------------------------------------------------------------- #
# the set itself
# --------------------------------------------------------------------------- #
def test_the_exempt_set_only_shrinks() -> None:
    """An exemption may be removed and never added.

    The pin is a literal in the module and not a ``len()`` read back off the tuple,
    because a pin computed from the thing it grades cannot fail.  Removing an entry
    leaves this green; adding one reddens it, and the only way to raise the pin is to
    raise it deliberately in a diff a reviewer sees.
    """
    assert len(EXEMPT) <= PIN, [f"{e.document}{e.pointer}" for e in EXEMPT]


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
    node = dump_exemptions._at(  # noqa: SLF001 -- the resolution under test
        _packaged(entry.document), dump_exemptions._path(entry.pointer)  # noqa: SLF001
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


def test_the_minproperties_entry_is_the_only_copy_that_is_a_pairs_own_node() -> None:
    """The accepted exposure, asserted as the INVARIANT and not as a count.

    Entry four's authored node is inlined all over the packaged tree.  Only where a
    copy is a graded pair's OWN node does the dump refuse with certainty -- the dump is
    then ``{}`` at the root.  Where the copy is nested inside a larger pair, a refusal
    needs a drawn instance that gives ``render_guidance`` exactly one key and that key
    undeclared, which is the latent exposure the module names.

    **The count of copies is deliberately NOT pinned, and the first version of this
    test pinned it and was wrong.**  It asserted 90, and merging ``.28`` forward moved
    it to 92 because that row emits more documents -- so the pin reddened on
    population growth, which the metric pins to HAPPEN.  A number that moves whenever
    the build succeeds is noise.  The invariant does not move: exactly one copy is a
    pair's own node, and it is the one in the set.  A second copy becoming a pair's own
    node reddens here, which is the condition that would actually produce a new
    certain refusal.
    """
    entry = next(e for e in EXEMPT if e.keyword == "minProperties")
    copies = {
        f"{f.relative_to(PACKAGED)}#{ptr}"
        for f in PACKAGED.rglob("*.json")
        for ptr, node in _walk(json.loads(f.read_text()))
        if isinstance(node, dict) and "minProperties" in node and "additionalProperties" not in node
    }
    assert len(copies) > 1, copies  # the denominator: there IS an exposure to bound
    graded = _graded_positions()
    assert graded, "the denominator is empty: no pair would be checked"
    assert copies & graded == {f"{entry.document}#{entry.pointer}"}, copies & graded


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
    """D5's 8 distinct patterns over 73 sites, re-measured, so the census below has a
    denominator this build agrees with rather than one carried forward."""
    patterns = _uri_patterns()
    assert len(patterns) == 8, sorted(patterns)
    assert sum(patterns.values()) == 73, sum(patterns.values())
    assert patterns[constraints.HTTPS_ONLY] == 47, patterns[constraints.HTTPS_ONLY]
    assert ORIGIN_ONLY in patterns, sorted(patterns)


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
        except Exception:  # noqa: BLE001 -- refused on the way IN, which is D4's half
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
    """Every packaged position stating ``pattern`` at a ``format: uri`` node.

    The packaged tree is the only space that reaches a pair, which is what makes a
    violating pattern with no position here upstream's problem and not an exemption.
    """
    return sorted(
        f"{f.relative_to(PACKAGED)}#{ptr}"
        for f in PACKAGED.rglob("*.json")
        for ptr, node in _walk(json.loads(f.read_text()))
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

    ``^https://[!$&-;=@-~]+$`` is the second violator and it is deliberately NOT
    exempt.  The class forbids ``%``, so percent-encoding a ``{`` or an ``@`` breaks
    it -- measured at 4 of 380 round-tripped draws of this function's own stream, a
    RATE where the first is a certainty.  **The reason it is not exempt is reach, not
    rate**: its one site is ``core/agent-reporting-destination-state.json#/properties/
    setup/properties/setup_url``, that document is not emitted, so it reaches no pair
    and no class emits a value against it.  That is what the last assertion states,
    and it is read off the packaged tree rather than off a draw.  If the emitter
    starts emitting the document, the first assertion reddens and a human decides
    whether the set grows.

    **No drawn RATE is asserted here, deliberately.**  A derandomized stream is a
    function of this function's identity and of the pinned ``hypothesis`` version, so
    a rate assertion would redden on a rename -- a defect in the instrument wearing
    the clothes of a defect in the SDK.  What is asserted is a certainty (every
    round-tripped value refused) and two facts read off documents.
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
    # ORIGIN_ONLY is not violated at a RATE: it is unsatisfiable, and that is the
    # ground D5 keeps the URL type on.  Every value the type accepts and re-emits is
    # refused by it, so no conforming URL library could satisfy it.
    origin = measured[ORIGIN_ONLY]
    assert origin.violated == origin.round_tripped, origin
    # The second violator reaches no packaged document, which is why it is upstream's
    # and not exempted here.  Read off the tree, so no draw decides it.
    assert _packaged_positions("^https://[!$&-;=@-~]+$") == []


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
    """
    pair = _pair(document, pointer)
    relaxed = dump_exemptions.struck(pair.schema, document, pointer)
    before = {ptr for ptr, _ in _walk(pair.schema)}
    after = {ptr for ptr, _ in _walk(relaxed)}
    assert not after - before, after - before
    expected = {
        f"{dump_exemptions._path(e.pointer)[len(dump_exemptions._path(pointer)) :]}"  # noqa: SLF001
        for e in dump_exemptions.applying_to(document, pointer)
    }
    assert expected, (document, pointer, "no entry applies, so nothing is being graded")
    removed = before - after
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
ANCESTORS = (
    ("core/attestation-issuer.json", "#"),
    ("core/attestation-capabilities.json", "#/properties/accepted_issuers/items"),
    ("core/provenance.json", "#"),
    ("core/provenance.json", "#/properties/disclosure"),
    (
        "core/provenance.json",
        "#/properties/disclosure/properties/jurisdictions/items",
    ),
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
