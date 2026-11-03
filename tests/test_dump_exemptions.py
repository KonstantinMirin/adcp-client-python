"""The exempt set, graded over the populations that justify it.

``codegen/dump_exemptions.py`` carries the positions where a document refuses the
SDK's own correct output.  There is **one** such position, D8's ``minProperties`` node,
and the defect is upstream (``adcontextprotocol/adcp#8398``).  An exemption inside the
only check that reads generated code is the most dangerous thing in this build, so every
claim the module makes is asserted here over a whole population rather than on an
example:

* the set only SHRINKS, pinned by count, over the WHOLE set;
* every entry names its upstream issue;
* every entry's pointer resolves in its packaged document AND the keyword still holds
  the value the entry states -- which is how the set shrinks on its own when upstream
  repairs a position, with no one watching;
* **no ``format: uri`` position needs an exemption**, re-measured over every ``uri``
  pattern the bundle states rather than taken on trust;
* the strike explains every dump the document refuses today, and touches nothing else.

**EIGHT ENTRIES LEFT THIS SET, and the measurement that justified them is inverted
rather than deleted.**  They were ``format: uri`` positions on one pattern,
``^https://[^/?#@]+$``, and the reading was that the pattern was unsatisfiable by a
NORMALIZING URL library -- true -- and therefore upstream's.  Section 2 re-read it on
2026-11-02: the SDK's own type decision was the defect, because a pydantic URL type
rewrites the value, so what the class dumped was never the string it was handed.  With
the type withdrawn every one of those dumps satisfies its own pattern with nothing
struck.  :func:`test_no_uri_pattern_refuses_the_value_a_uri_field_now_carries` is the
former census, over the same population, asserting the opposite -- so the eight cannot
come back unnoticed and the instrument that was once their justification is now their
refutation.

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
from pydantic import ConfigDict, TypeAdapter

from adcp.types._base import REGEX_ENGINE, SchemaRef, schema_at
from codegen import bundle, constraints, dump_exemptions, harness, ir, render
from codegen.dump_exemptions import EXEMPT, PIN, UPSTREAM, Exemption

import fresh
from tests.nodeset import claimed

#: The packaged tree, which is the pointer space an entry names: section 6 measures
#: these documents at 0 ``$ref`` occurrences, so what the harness grades is the
#: resolved form and a node reached through a ``$ref`` in the bundle source is an
#: inlined copy here.
#:
#: **The tree a FRESH run emits** (``docs/plan/architecture.md``, 2026-10-29), which is
#: the same tree ``_class_for`` imports its classes out of: an entry's position space and
#: the pair it is checked against have to be one tree, or a position's exemption is
#: decided against one compiler and graded against another.  ``tests/fresh.py`` owns it.
PACKAGED = fresh.TREE

#: The bundle source, for the pattern census.  Every measurement in this build is
#: taken over ``schemas/cache/<version>/`` (section 6).
SOURCE = pathlib.Path("schemas/cache/3.2")

#: The pairs the dump half refuses on the committed tree, named rather than discovered,
#: so this file does not grade a population another lane is moving.  Each is
#: ``(document, pointer, the exempt keyword the document refuses the dump on)``.
#:
#: **It was three and is one.**  The two that left were ``format: uri`` positions whose
#: dump the document refused on its own ``pattern``, and they are not refused any more:
#: the class carries the string it was given, so the dump satisfies the pattern and there
#: is nothing to strike.  A tuple and not a count, so their absence is readable.
REFUSED_TODAY = (
    (
        "core/provenance.json",
        "#/properties/disclosure/properties/jurisdictions/items/properties/render_guidance",
        "minProperties",
    ),
)

#: The pattern the eight withdrawn entries stood on, named HERE now that
#: ``codegen/dump_exemptions.py`` does not name it: it is the anchor of this file's
#: ``uri`` census and no longer a value any entry holds.  ``$`` immediately after the
#: authority, which RFC 3986 section 6.2.3 makes unsatisfiable by a normalizing URL
#: library, and satisfiable with nothing struck by a field carrying the author's string.
ORIGIN_ONLY = "^https://[^/?#@]+$"


def _walk(node: Any, ptr: str = "") -> Any:
    """Every node of a document, by JSON pointer, ``$defs`` and all (section 6)."""
    if isinstance(node, dict):
        yield ptr, node
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
    return harness._wire_dump(pair.accept(seen[-1]))  # noqa: SLF001 -- the production dump


# --------------------------------------------------------------------------- #
# the set itself
# --------------------------------------------------------------------------- #
def test_the_exempt_set_only_shrinks() -> None:
    """An exemption may be removed and never added -- over the part that is PINNED.

    The pin is a literal in the module and not a ``len()`` read back off the tuple,
    because a pin computed from the thing it grades cannot fail.  Removing an entry
    leaves this green; adding one reddens it, and the only way to raise the pin is to
    raise it deliberately in a diff a reviewer sees.

    **It covers the WHOLE set again**, and that is the withdrawal's doing rather than a
    loosening.  The pin was split because the number of positions one upstream pattern
    reaches is a property of how much of the bundle is PACKAGED -- every row that emitted
    a document carrying that authored node added a position, so an absolute count over
    that part obliged each of them to raise a shrink-only pin, which is the one thing
    such a pin may not do.  Those positions are gone with the type that needed them, so
    nothing left here is a function of emission and the strongest form of the pin is
    available again.
    """
    assert EXEMPT, "the set is empty: this assertion would hold vacuously"
    assert len(EXEMPT) <= PIN, [f"{e.document}{e.pointer}" for e in EXEMPT]


def test_no_position_stating_the_withdrawn_pattern_is_exempt() -> None:
    """The ``ORIGIN_ONLY`` positions still exist and NONE of them is exempt.

    Both sides derived, neither a literal count, and the direction is the one that
    changed.  This test asserted that the exempt entries ARE the packaged positions
    stating that pattern; section 2's withdrawal of 2026-11-02 made the equality false in
    the good direction -- the positions are all still there, upstream has repaired
    nothing, and not one of them needs an exemption, because the class now dumps the
    string it was handed.

    The first assertion is what keeps the second from being vacuous: the pattern is still
    in the packaged tree at pairs this suite grades, so "no entry" is a statement about
    live positions rather than about an empty set.  If an entry for one of them ever
    comes back, it reddens here and a reader is sent to
    :func:`test_no_uri_pattern_refuses_the_value_a_uri_field_now_carries`, which says
    whether the type stopped carrying the document's own string.
    """
    import test_emit  # the tree reader, one reading for the whole suite

    positions = claimed(
        "packaged positions whose pattern is ORIGIN_ONLY",
        {
            f"{document}#{pointer}"
            for document in sorted({g.ref.document for g in test_emit.graded()})
            for pointer, node in bundle.nodes(schema_at(SchemaRef(document, "#")))
            if isinstance(node, dict) and node.get("pattern") == ORIGIN_ONLY
        },
    )
    exempted = {f"{e.document}#{e.pointer}" for e in EXEMPT}
    assert not (positions & exempted), sorted(positions & exempted)
    assert not [e for e in EXEMPT if e.value == ORIGIN_ONLY], [
        f"{e.document}{e.pointer}" for e in EXEMPT if e.value == ORIGIN_ONLY
    ]


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

    The entry's authored node is inlined all over the packaged tree.  Only where a
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
    # Each copy that IS a pair's own node, re-read as the document applies it
    # (:func:`_silent_about_extras`): the exposure is a class's ``extra`` setting and D8
    # derives that from the node the class is paired with, so a conjunct whose sibling
    # closes the object has no exposure to bound.  The intersection is asserted
    # non-empty first, so the applied reading cannot empty the denominator silently.
    own = copies & graded
    assert own, "the denominator is empty: no copy is a pair's own node"
    exposed = {
        c for c in own if _silent_about_extras(schema_at(SchemaRef(*c.split("#", 1))))
    }
    assert exposed == {f"{entry.document}#{entry.pointer}"}, (sorted(own), sorted(exposed))


# --------------------------------------------------------------------------- #
# the measurement eight entries rested on, asserting the opposite
# --------------------------------------------------------------------------- #
def _uri_patterns() -> dict[str, int]:
    """Every ``pattern`` the bundle states at a ``format: uri`` node, with its count.

    **The instrument is "any node carrying ``format: uri``"**, which is section 5's own
    and gives its figures.  Additionally requiring ``type: string`` misses
    ``core/macro-bearing-url.json#/anyOf/1`` -- the ``^https?://`` position whose author
    admitted ``http`` deliberately -- because that node states no ``type`` of its own.
    Narrowing the instrument here would drop the pattern most worth grading.
    """
    out: dict[str, int] = {}
    for document in sorted(bundle.portable(SOURCE)):
        for _, node in _walk(bundle.read(SOURCE, document)):
            if isinstance(node, dict) and node.get("format") == "uri" and "pattern" in node:
                out[node["pattern"]] = out.get(node["pattern"], 0) + 1
    return out


def test_the_bundles_uri_pattern_population_is_the_one_the_census_draws_over() -> None:
    """The distinct ``format: uri`` patterns, as the SET the census below ranges over.

    Named and asserted non-empty rather than sized: :data:`ORIGIN_ONLY` is asserted BY
    NAME, because it is the pattern the eight withdrawn entries stood on and the one the
    census has to still meet for its verdict to mean anything.  A bundle version's
    reading of how many sites each pattern occupies says nothing about that.
    """
    patterns = claimed("distinct format:uri patterns in the bundle", _uri_patterns())
    assert ORIGIN_ONLY in patterns, sorted(patterns)


#: Draws per pattern.  **40 is not enough and the number was measured, not guessed.**
#: At 40 draws two independent streams disagreed about how many of the patterns their own
#: type's output refused -- one said one, the other said two -- which is the same "passes
#: by luck of the draw" failure this file has met before, arriving in the instrument
#: instead of in the dump half.  At 500 both streams agreed.  The number is kept at 500
#: now that the expected answer is ZERO violations, because that is the direction a weak
#: instrument passes by accident: a census that draws too little reports no violation
#: whatever the type does.
DRAWS = 500


class Roundtrip(NamedTuple):
    """How a ``format: uri`` field's own type treats the strings its pattern admits.

    ``refused_in`` is the count the TYPE rejected on the way in -- the input direction,
    which D4 gives to the schema half -- and it is carried so ``round_tripped`` can be
    asserted non-empty.  A pattern whose every draw was refused on the way in would
    report zero violations while measuring nothing.

    ``rewritten`` is the count where the value came back DIFFERENT, and it is the
    stronger half: section 2's defect was value identity, and a type could rewrite a
    value into a form the pattern happens to admit while still having lost the author's
    string.  ``violated`` is the count the pattern then refuses, which is the half that
    made a dump fail.
    """

    round_tripped: int
    rewritten: int
    violated: int
    refused_in: int
    examples: tuple[tuple[str, str], ...]


def _uri_type(pattern: str) -> Any:
    """The type the EMITTER gives a ``{type: string, format: uri, pattern: …}`` node.

    Resolved and RENDERED by production -- ``constraints.resolve`` names the shape and
    ``render.constraints_module`` writes the declaration -- then executed, which is the
    same arrangement ``tests/test_emit.py`` uses to grade an alias module's text.  Two
    things that matters for: the type is not restated here, so a lane that changes what a
    ``uri`` node resolves to moves this census with it; and every pattern in the bundle
    is graded, including the ones whose documents no run emits, where a lookup in the
    emitted module would have found nothing and silently graded less.
    """
    path = constraints.resolve("string", {"pattern": pattern}, format="uri")
    assert path is not None, pattern
    name = path.rsplit(".", 1)[1]
    namespace: dict[str, Any] = {}
    exec(render.constraints_module({name: ("string", {"pattern": pattern}, "uri")}), namespace)  # noqa: S102
    return namespace[name]


def _roundtrip(pattern: str, examples: int = DRAWS) -> Roundtrip:
    """Strings the pattern admits, round-tripped through the type the EMITTER chooses.

    Drawn rather than written: written candidates for every pattern would be a guess
    about what each one means, and a wrong guess shows up as a pattern graded only on
    values that happen to round-trip.  ``re.search`` and not ``fullmatch``, because
    search is what JSON Schema's ``pattern`` means.
    """
    # The ENGINE is production's too, and it has to be: ``regex_engine`` is a model
    # config, so an ``Annotated`` alias has nowhere to carry one and
    # ``_base.strict_alias`` passes it at the adapter -- the channel that exists for
    # exactly this.  A bare adapter takes pydantic's Rust engine, which refuses a
    # look-around ``pattern`` outright and disagrees with Python's about ``$``, so a
    # census built on one would grade a type no class in the tree uses.
    adapter = TypeAdapter(_uri_type(pattern), config=ConfigDict(regex_engine=REGEX_ENGINE))
    counts = {"round_tripped": 0, "rewritten": 0, "violated": 0, "refused_in": 0}
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
        if out != value:
            counts["rewritten"] += 1
            if len(bad) < 2:
                bad.append((value, out))
        if re.search(pattern, out) is None:
            counts["violated"] += 1
            if len(bad) < 2:
                bad.append((value, out))

    body()
    return Roundtrip(
        counts["round_tripped"],
        counts["rewritten"],
        counts["violated"],
        counts["refused_in"],
        tuple(bad),
    )


def _packaged_positions(pattern: str) -> list[str]:
    """Every packaged position stating ``pattern`` at a ``format: uri`` node.

    The packaged tree is the only space that reaches a pair, which is what made a
    violating pattern with no position here upstream's problem and not an exemption.
    """
    return sorted(
        f"{f.relative_to(PACKAGED)}#{ptr}"
        for f in PACKAGED.rglob("*.json")
        for ptr, node in _walk(json.loads(f.read_text()))
        if isinstance(node, dict) and node.get("format") == "uri" and node.get("pattern") == pattern
    )


def test_no_uri_pattern_refuses_the_value_a_uri_field_now_carries() -> None:
    """**The census eight entries rested on, over every pattern, asserting the OPPOSITE.**

    It used to read "every violating pattern that reaches a pair is exempt", and it found
    two violators: ``ORIGIN_ONLY``, refused on 100% of round-tripped draws, and
    ``^https://[!$&-;=@-~]+$``, refused on a few.  Both were properties of the TYPE and
    not of the pattern: every pydantic URL type is backed by the Rust ``url`` crate,
    which normalizes -- it gives an authority-only URL a path of ``/``, lowercases the
    host, and percent-encodes a byte the authority may not carry raw -- so a pattern that
    forbids what normalization PRODUCES cannot be satisfied by that type's output,
    whatever it was handed.

    Section 2 withdrew the type (2026-11-02).  A ``format: uri`` field carries the
    document's own string, so the output IS the input and no pattern can refuse it.  Two
    assertions, and the first is the stronger one:

    * **nothing is REWRITTEN.** Injectivity is the property section 2 named, and it is
      what every fact depending on value identity rests on -- a ``uniqueItems`` over URI
      items, a ``const``, an origin comparison a consumer makes.  A type that rewrote a
      value into a form the pattern happens to admit would pass the second assertion and
      fail reading 1 anyway.
    * **nothing is VIOLATED**, which is the half that made a dump fail and the half the
      eight entries excused.

    Over EVERY pattern the bundle states at a ``uri`` node, including the ones whose
    documents no run emits: the type is rendered from the shape rather than looked up in
    the emitted module (:func:`_uri_type`), so the census does not shrink to whatever
    happens to be packaged.  And the two patterns that used to violate are asserted
    present by name, so this cannot pass because the bundle stopped stating them.
    """
    patterns = _uri_patterns()
    assert patterns, "the denominator is empty: no uri pattern would be graded"
    assert ORIGIN_ONLY in patterns, sorted(patterns)
    assert "^https://[!$&-;=@-~]+$" in patterns, sorted(patterns)
    measured = {p: _roundtrip(p) for p in sorted(patterns)}
    for pattern, got in measured.items():
        assert got.round_tripped, (pattern, got, "no value survived the type: nothing graded")
    assert {p: g for p, g in measured.items() if g.rewritten} == {}, {
        p: (g.rewritten, g.round_tripped, g.examples) for p, g in measured.items() if g.rewritten
    }
    assert {p: g for p, g in measured.items() if g.violated} == {}, {
        p: (g.violated, g.round_tripped, g.examples) for p, g in measured.items() if g.violated
    }
    # And the consequence, read off the set rather than inferred: no entry is a
    # ``pattern`` entry any more.  Both halves together are what makes the withdrawal
    # checkable -- a census with no exempt set to compare against would pass while an
    # entry sat there doing nothing.
    assert [e for e in EXEMPT if e.keyword == "pattern"] == []
    # The positions are still THERE, so neither assertion above is about an empty tree.
    claimed("packaged positions stating ORIGIN_ONLY", _packaged_positions(ORIGIN_ONLY))


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
#: made a conditional pass unreadable -- five of the eight passed on their own merits.
#:
#: It was five and is three: the two that left were ancestors of a ``format: uri``
#: position, and with those entries withdrawn ``applying_to`` matches nothing at either,
#: so there is no longer an entry for them to decline to use.
ANCESTORS = (
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

    An ancestor pair's dump carries the nested node, so ``applying_to`` matching by
    prefix is right: a position inlined into a larger pair is still in that pair's dump.

    What would be wrong is REPORTING it everywhere it applies.  These three pairs
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
    """Every pair that has no entry pays no copy and cannot be altered at all.

    Identity and not equality, because that is the property the harness will rely on
    to tell an exempted pair from an ordinary one without asking twice -- and because
    an equal-but-copied schema would make a future strike at the wrong depth invisible
    here.
    """
    document = "core/pagination-request.json"
    pair = _pair(document, "#")
    assert dump_exemptions.struck(pair.schema, document, "#") is pair.schema, document
    assert dump_exemptions.applying_to(document, "#") == ()
