"""The decisions this compiler takes on purpose, pinned so an edit to one reddens.

An agent degraded 86 emitted modules from a pydantic URL type to ``str``.  It read
``docs/plan/rebuild-plan.md`` §2 -- "a model may be looser than its document, never
tighter" -- found ``codegen/constraints.py``'s :func:`~codegen.constraints.url_type`
deliberately narrowing, and changed the code.  **The contradiction was real and
findable by anyone**, and the narrowing is a decision predating this work: the bundle
spells "a URL" nine ways across 300 ``format: uri`` positions, a bare ``format: uri``
is RFC 3986 and admits ``urn:``, ``file:///`` and ``http://`` alike, and ``AdCPUrl``
everywhere was measured WORSE -- 228 of 300 positions narrowed against ``HttpUrl``'s
227.  The change was merged and reverted.  **Every test stayed green through both.**

That is the hole this file closes.  §2 already names the rule it violates:

    "A narrowing taken on purpose is admitted by an ENUMERATED registry and by nothing
    else.  The registry is the authority ... **A reading that finds code contradicting
    this section reports it and does not change either side.**  A registry entry is a
    decision even though it is not in this document."

A decision whose whole expression is a function body and a docstring has no reader but
a human, and a human who reads the two documents first will read the decision as the
defect they name.  So each decision here is READ BY A TEST, and the test's failure
message is the product: it names the decision, says where the rationale lives, gives
the measurement, and tells the reader to REPORT rather than repair.

**Four shapes, and which one a decision gets is decided by what can be derived.**

1. **Derived on both sides** -- the strongest, and ``codegen/dump_exemptions.py``'s
   ``test_the_origin_only_part_is_the_packaged_positions`` is the model.
   :data:`~codegen.harness.URL_IMPLIED`'s two values are what pydantic's own URL types
   render, so the pin asks pydantic rather than restating ``2083``
   (:func:`test_url_implied_holds_the_value_the_selected_arms_actually_render`).
2. **A derived mapping, pinned by value** -- :func:`~codegen.constraints.url_type` is a
   FUNCTION, so no registry guards it at all, and restating its branch here would be a
   second copy of a keyword decision.  What is pinned instead is the mapping it
   produces over the bundle: each spelling of a URL the bundle states, against the type
   the function chooses for it.  A function of the bundle, so it shrinks on its own when
   upstream repairs a pattern
   (:func:`test_url_type_chooses_the_same_type_for_every_spelling_of_a_url_the_bundle_states`).
3. **A value pin** -- :data:`DECISIONS`, for a registry whose value is neither derivable
   nor graded anywhere else.  The recorded copy is COMPARED and never USED, which is
   what keeps it from being the drifting duplicate §8 warns about: nothing in this suite
   reads the copy to decide anything, so a copy that went stale can only redden.
4. **The reach, derived by perturbation** -- a value pin is complete with respect to
   itself and blind beyond itself, which is §8's "a hand-written list beside the
   comparison".  So the facts the comparison ADMITS over the whole graded population are
   derived by switching each admission mechanism off and reading what reappears, and
   that set is pinned by keyword.  A new hand-written row is a new keyword in it
   (:func:`test_the_comparison_admits_no_fact_this_file_does_not_name`).

**What this file does NOT claim, said rather than implied** (§8: "A check is exhaustive
over the set of nodes it claims, or it does not exist.  A check that enumerates a subset
reports on that subset only, and says so").  Shape 4 reaches the five mechanisms
``compare_schema`` admits a fact through today: :data:`~codegen.harness.URL_IMPLIED`,
``_schema_half_enforces``, ``_narrows_nothing``, ``_constrains_nothing`` and
``_states_no_graded_fact``.  A SIXTH mechanism -- a new ``continue`` in that function
that neither appends to a reported counter nor routes through one of those predicates --
is outside it.  It is also a
shape the comparison does not currently have, and the thing that would make it visible
is a structural reading of the source, which is a different instrument from this one.
"""

from __future__ import annotations

import importlib
import pathlib
from collections.abc import Callable, Mapping
from typing import Any, NamedTuple

import pytest
from pydantic import TypeAdapter

from codegen import bundle, constraints, harness

from tests.nodeset import claimed

#: The bundle SOURCE, which is where every measurement in this build is taken (§6) and
#: the only space a decision about "the bundle" can be stated over.  Deliberately not the
#: packaged tree: which documents are PACKAGED is a function of how much the emitter
#: emits, so a pin over that space has to rise every time a row lands -- the failure
#: ``codegen/dump_exemptions.py``'s ``PIN`` records and the one its derived half replaced.
SOURCE = pathlib.Path("schemas/cache/3.2")

#: What a reader who reddened one of these tests is being told, in the words §2 uses.
#: One string, so no test can give a softer version of it.
INSTRUCTION = """
This is a RECORDED DECISION, not a derivation and not a defect.

DO NOT edit the expectation in tests/test_decision_set.py to go green, and DO NOT
change the decision to agree with a document that seems to contradict it.  Both sides
were measured, and the measurement is quoted above.

docs/plan/rebuild-plan.md section 2: "A reading that finds code contradicting this
section reports it and does not change either side.  A registry entry is a decision
even though it is not in this document."

So: if you have found a contradiction, REPORT IT -- file it against this epic, quote
both sides, and leave both standing.  If the decision has genuinely been superseded,
the diff that supersedes it says so in the row that decided, and moves this pin in the
same diff a reviewer reads.
""".strip()


def _resolve(subject: str) -> Any:
    """The live object a dotted ``module.NAME`` names, or an :class:`AssertionError`.

    Resolved by name at grading time rather than imported at module scope, so a decision
    that was DELETED reddens here with its own message instead of as an ``ImportError``
    during collection -- which is a failure the reader cannot tell from a broken test.
    """
    module, _, name = subject.rpartition(".")
    try:
        holder = importlib.import_module(module)
    except ImportError as e:  # pragma: no cover -- a module that stopped existing
        raise AssertionError(f"{subject}: {module} no longer imports ({e})\n\n{INSTRUCTION}") from e
    if not hasattr(holder, name):
        raise AssertionError(
            f"{subject}: {module} no longer declares {name}.\n\n"
            f"A decision was DELETED, which is the one edit a value pin cannot show as a "
            f"changed value.\n\n{INSTRUCTION}"
        )
    return getattr(holder, name)


class Decision(NamedTuple):
    """One decision pinned by VALUE, with the reason a reader needs before changing it.

    ``subject`` is the dotted name, resolved at grading time by :func:`_resolve`.

    ``rationale`` is WHERE the reasoning lives.  Required, and it is the half the
    incident was missing: the degradation was a correct reading of a document beside a
    decision whose reasoning the reader never reached.  A pin that says only "this
    changed" sends the next reader back to the same two documents.

    ``because`` is the MEASUREMENT, in one sentence, so the message carries the figure
    and not just a pointer to it.

    ``recorded`` is the value as this guard recorded it.  It is COMPARED and never USED
    -- no other assertion in this suite reads it -- so a recorded value that drifts from
    the live one can only redden, never decide anything.

    ``read`` turns the live object into the comparable value, for a registry whose own
    value is not comparable: ``lower.scalars.FORMAT_TYPES`` holds CHOOSERS, and two
    lambdas are never equal, so what is pinned is the path each chooser answers.
    """

    subject: str
    rationale: str
    because: str
    recorded: Any
    read: Callable[[Any], Any] = lambda live: live


#: **The decisions pinned by value, and the set is small on purpose.**  A guard over a
#: mechanical lookup is noise that the first person it annoys deletes, and a guard over a
#: decision another check already grades by a DERIVED equality is the duplicate §8 warns
#: about.  Each candidate from the incident's own inventory was re-measured; the ones not
#: here are named in :data:`NOT_PINNED_HERE` with the reason, because "we looked and
#: decided not to" is the half of an inventory a reader cannot reconstruct.
DECISIONS: tuple[Decision, ...] = (
    Decision(
        subject="codegen.harness.FORMAT_SHAPES",
        rationale=(
            "codegen/harness.py, the comment above FORMAT_SHAPES, and "
            "docs/plan/rebuild-plan.md section 8's accepts obligation"
        ),
        because=(
            "section 8 asks the draw to COVER a format's admissible space rather than "
            "sample it -- 'for a format every shape the format's own checker admits "
            "rather than the shape a generator finds most likely'.  A generator draws "
            "the LIKELY shape (a short https URL, a UTC 'Z'), so a draw alone runs green "
            "forever against a type that refuses every other admissible shape.  Each "
            "shape here is one such class and REMOVING one silently narrows the proof: "
            "tests/test_approximation.py asserts that every shape present is admissible "
            "and that the KEYS are lower.scalars.FORMAT_TYPES, and neither of those "
            "notices a shape that is gone"
        ),
        recorded={
            "uri": (
                ("an https URL", "https://example.com/a"),
                ("a plain http URL", "http://example.com/a"),
                ("a URN", "urn:ietf:rfc:3986"),
                ("a file URL", "file:///tmp/a"),
                ("a mailto URI", "mailto:a@example.com"),
                ("a URL longer than 2,083 characters", "https://example.com/" + "a" * 2200),
                ("a URL with a port and a query", "https://example.com:8443/a?b=c#d"),
            ),
            "date-time": (
                ("a UTC timestamp", "2026-10-26T12:00:00Z"),
                ("an offset timestamp", "2026-10-26T12:00:00+02:00"),
                ("a negative-offset timestamp", "2026-10-26T12:00:00-05:00"),
                ("a fractional-second timestamp", "2026-10-26T12:00:00.123456Z"),
            ),
            "date": (
                ("a date", "2026-10-26"),
                ("a leap day", "2024-02-29"),
                ("the first day of an era", "0001-01-01"),
            ),
        },
        read=dict,
    ),
    Decision(
        subject="codegen.lower.scalars.FORMAT_TYPES",
        rationale=(
            "codegen/lower/scalars.py, the comment above FORMAT_TYPES, and "
            "docs/plan/rebuild-plan.md D5's format row"
        ),
        because=(
            "this is the table the degradation went through, and the SHORTEST way to "
            "repeat it: dropping the 'uri' row stops url_type being asked at all, so "
            "every format: uri position falls back to the constrained str with the "
            "format riding as json_schema_extra, and the pin on url_type's own mapping "
            "stays green while 86 modules lose their URL type.  'AdCPUrl everywhere' was "
            "measured at 228 of the bundle's 300 uri positions narrowed against their "
            "document, and 'no URL type at all' is wider still -- it is the position "
            "section 2's first principle permits and D5 declines, because the schema "
            "half runs the document before anything is constructed and the annotation is "
            "then the only STATIC claim there is"
        ),
        recorded={
            "date-time": "pydantic.AwareDatetime",
            "date": "datetime.date",
            "uri": "adcp.types.constraints.HttpUrl",
        },
        # Each value is a CHOOSER, so what is pinned is the path it answers for a node
        # stating nothing.  ``uri``'s answer for an empty node is the bare-uri arm, which
        # is 227 of the bundle's 300 positions and the arm the degradation replaced; the
        # other arm is pinned over the bundle by the mapping test below.
        read=lambda table: {fmt: choose({}) for fmt, choose in table.items()},
    ),
    Decision(
        subject="codegen.lower.union.ROOT_CONJUNCTS",
        rationale=(
            "codegen/lower/union.py's module docstring and the comment above "
            "ROOT_CONJUNCTS, against docs/plan/rebuild-plan.md D7"
        ),
        because=(
            "a REFUSAL taken on purpose, and the one entry in the incident's inventory "
            "whose edit changes no accepted set at all -- so nothing in the emitted tree "
            "can report it.  Its own comment records the probe: removing 'allOf' while "
            "the keyword screen still admits it emits 0 further documents and only moves "
            "the REASON 37 of them are refused.  D7 reads the other way about those 37, "
            "and the conflict is recorded AT this tuple with the probe that decided it "
            "rather than resolved by preference, which is exactly a decision a reader of "
            "D7 alone would 'fix'.  What the entry forecloses becomes reachable at the "
            "first branch repair: _base.applied_schema conjoins an enclosing type, which "
            "by itself unblocks a branch in 17 of the 41, and without the entry such a "
            "document emits a base that drops its composed bases"
        ),
        recorded=("allOf", "properties", "required", "additionalProperties"),
    ),
)

#: **The candidates from the incident's inventory that are deliberately NOT pinned by
#: value here, each with the reason.**  Prose, not an allowlist: nothing reads this and no
#: assertion is satisfied by an entry.  It is here because an inventory without its
#: negative half asks the next reader to re-measure everything to find out whether a
#: subject was considered.  Two kinds of reason, and only two are admissible:
#: a MECHANICAL LOOKUP, whose error is visible in the ordinary grade; and a decision
#: another check already grades by a DERIVED equality, where a second value pin is the
#: duplicate that drifts.
NOT_PINNED_HERE: Mapping[str, str] = {
    "codegen.harness._TIGHTER_BOUND": (
        "A MECHANICAL LOOKUP: max for a floor, min for a ceiling, re-derivable from each "
        "keyword's own name.  A wrong entry computes a LOOSER composed bound, so the "
        "document reads as looser, the model reads as narrower, and the pair reports "
        "added or differs -- _tighter's own docstring states that direction ('a looser "
        "expectation is a FALSE FAILURE that is visible').  An error here cannot pass "
        "green, so a pin over it grades nothing the suite does not already grade."
    ),
    "codegen.harness._ALIEN_VALUES": (
        "ALREADY A DERIVED EQUALITY.  It is the liveness probe's population, and "
        "test_emit.test_a_refused_payload_is_derived_for_every_pair_an_instance_was_"
        "drawn_for asserts the pairs reporting 'no_payload' ARE the four named ones.  "
        "Remove a member and a document that stated a root type stops being refused a "
        "payload, the set grows, and that equality reddens -- over the whole population "
        "rather than against a copy of the tuple."
    ),
    "codegen.dump_exemptions.EXEMPT and PIN": (
        "ALREADY RATCHETED AND ALREADY DERIVED, both halves, in "
        "tests/test_dump_exemptions.py: PIN is shrink-only over the non-ORIGIN_ONLY "
        "entries, the ORIGIN_ONLY part is a derived equality against the packaged "
        "positions, and every entry's pointer and VALUE are re-resolved against its "
        "document.  A value pin here would be the second copy that drifts -- and it "
        "would have to rise every time a row emits another document carrying the node, "
        "which is the failure that file's own docstring records."
    ),
    "codegen.ir._SECTION_7_APPROXIMATION": (
        "NOT A DEVIATION: a BINDING.  Section 7 puts Approximation in the IR layer and "
        "its VALUE in the emitted module, and both hold by declaring it in "
        "adcp.types._base and binding the name here.  The tuple exists so the names are "
        "bound; the strings it carries are the emitted artifact's own and every emitted "
        "module that spells one grades them."
    ),
    "codegen.keywords._REFUSED and _REGISTRY_KEYS": (
        "ALREADY GRADED BY A GENERATED ARTIFACT.  The table generates sections 5, 6 and "
        "7's grids and test_keywords.test_the_committed_grids_are_what_the_table_"
        "generates asserts the committed document equals what the table generates, so a "
        "changed cell either moves the document in the same diff or reddens.  The two "
        "cells that carry the decision are asserted by name besides "
        "(errorMessage -> REFUSE -> VERDICT, version -> NOTHING and admitted)."
    ),
    "codegen.constraints.HTTPS_ONLY, URL and HTTP_URL": (
        "COVERED BY THE DERIVED MAPPING below, and pinning them beside it would be the "
        "same fact twice.  HTTPS_ONLY is url_type's own input: widen it to a prefix and "
        "the bundle's '^https://' spelling stops matching, its entry flips to HttpUrl, "
        "and the mapping reddens.  URL and HTTP_URL are the two paths the mapping's "
        "values ARE."
    ),
    "codegen.compiler.INLINE and _AXES, codegen.lower.enum.CLAIMS, "
    "codegen.constraints.NAMED_CONTAINERS": (
        "VISIBLE IN THE ORDINARY GRADE.  Each is a hand-written coverage or naming set "
        "whose edit moves the emitted tree or the comparison: a conjunct admitted into "
        "INLINE emits a class, a bound added to _AXES changes the composed intersection "
        "the comparison reads, a keyword added to CLAIMS changes an enumeration's "
        "rendering, and NAMED_CONTAINERS decides a symbol the emitted constraints module "
        "declares.  None is a decision no check reads, which is the condition for being "
        "here."
    ),
}


def _brief(value: Any) -> str:
    """One value's ``repr``, with a long one elided in the middle.

    ``FORMAT_SHAPES`` carries a 2,220-character URL on purpose -- it is the class row
    ``.10``'s live narrowing was measured on -- and printing it twice buries the one line
    a reader needs.  Elided in the MIDDLE and never truncated at the end, so the shape
    stays readable from both ends and no reader mistakes an elision for the value.
    """
    text = repr(value)
    if len(text) <= 160:
        return text
    return f"{text[:90]} ... <{len(text) - 150} chars> ... {text[-60:]}"


def _members(was: Any, now: Any) -> str | None:
    """Which MEMBERS of a sequence left and arrived, where both sides are sequences.

    A whole-tuple diff of a registry whose entries are long is unreadable, and a registry
    whose entries are long is the common case here.  ``None`` where either side is not a
    sequence, and the caller falls back to the two values.
    """
    if not isinstance(was, (tuple, list)) or not isinstance(now, (tuple, list)):
        return None
    gone = [m for m in was if m not in now]
    came = [m for m in now if m not in was]
    lines = [f"        LEFT:    {_brief(m)}" for m in gone]
    lines += [f"        ARRIVED: {_brief(m)}" for m in came]
    return "\n".join(lines) if lines else None


def _moved(recorded: Mapping[Any, Any], live: Mapping[Any, Any]) -> str:
    """The entries that moved, keyed, with the member-level difference where there is one."""
    out = []
    for key in sorted(set(recorded) | set(live), key=repr):
        was, now = recorded.get(key, "<absent>"), live.get(key, "<absent>")
        if was == now:
            continue
        detail = _members(was, now)
        out.append(
            f"    {key!r}:\n{detail}"
            if detail
            else f"    {key!r}: {_brief(was)} -> {_brief(now)}"
        )
    return "\n".join(out)


def _say(subject: str, rationale: str, because: str, body: str) -> str:
    """The failure message, in the one order a reader needs it.

    **This is the product of this file and not its decoration.**  A guard that fails with
    ``assert {...} == {...}`` teaches nothing, and the next agent re-points the expected
    value -- which is a smaller version of the same incident.  So the message leads with
    WHAT changed, then WHERE the reasoning is, then the MEASUREMENT, then the
    instruction, and the instruction is :data:`INSTRUCTION` for every failure in this
    file so no one of them can give a softer version of it.
    """
    return (
        f"\n\nA RECORDED DECISION CHANGED: {subject}\n\n"
        f"{body}\n\n"
        f"WHY IT IS WHAT IT IS -- the rationale lives at:\n  {rationale}\n\n"
        f"THE MEASUREMENT:\n  {because}\n\n"
        f"{INSTRUCTION}\n"
    )


@pytest.mark.parametrize("decision", DECISIONS, ids=lambda d: d.subject)
def test_a_recorded_decision_still_holds_the_value_it_recorded(decision: Decision) -> None:
    """One registry, pinned by value, reddening with a message that names the decision.

    The recorded value is a COPY and that is the one objection worth answering: a
    hand-written duplicate beside the real thing drifts, and then the guard grades the
    copy.  What keeps this from being that: the copy is only ever COMPARED.  Nothing in
    this suite reads :attr:`Decision.recorded` to decide anything, so the worst a stale
    copy can do is redden -- which is the outcome a reader can act on -- and the live
    object is resolved by NAME at grading time, so a decision that was deleted reddens
    here too rather than disappearing with the test that read it.
    """
    live = decision.read(_resolve(decision.subject))
    if live == decision.recorded:
        return
    if isinstance(live, dict) and isinstance(decision.recorded, dict):
        body = "  these entries moved:\n" + _moved(decision.recorded, live)
    elif (detail := _members(decision.recorded, live)) is not None:
        body = "  these members moved:\n" + detail
    else:
        body = f"  recorded here: {_brief(decision.recorded)}\n  live now:      {_brief(live)}"
    raise AssertionError(_say(decision.subject, decision.rationale, decision.because, body))


# --------------------------------------------------------------------------- #
# url_type: a decision expressed as a FUNCTION, pinned as the mapping it produces
# --------------------------------------------------------------------------- #
#: **Every spelling of a URL the bundle states at a ``format: uri`` node, against the
#: type :func:`codegen.constraints.url_type` chooses for it.**  ``None`` is the bare
#: ``format: uri`` -- 227 of the bundle's 300 positions, and the arm the degradation
#: replaced with ``str``.
#:
#: **Keyed by the document's own PATTERN and not by position, and the key set is derived
#: off the bundle.**  Position would be a pin of 300 entries that a bundle version bump
#: rewrites wholesale; pattern is the same mapping at the granularity the decision is
#: actually taken at, and it is 9 entries a reader can audit.  Both sides are a function
#: of the pinned bundle and of nothing else -- not of how much the emitter EMITS, which
#: is what obliged ``dump_exemptions.PIN`` to rise and what its derived half replaced.
#:
#: **The value is a SET of paths, deliberately, and that is not padding.**  ``url_type``
#: reads only the node's ``pattern`` today, so one spelling answers one type; recording a
#: set is what makes a function that grew a SECOND input visible -- the same spelling
#: would then answer two types at two positions and the entry would hold two paths.
#:
#: It shrinks on its own.  When upstream repairs ``^https://[^/?#@]+$`` -- the one pattern
#: no conforming URL library can satisfy, filed at ``adcontextprotocol/adcp#8398`` and
#: exempted at six positions in ``codegen/dump_exemptions.py`` -- the key leaves the
#: bundle, the repaired spelling arrives, and this reddens naming both.
URL_TYPE_OVER_THE_BUNDLE: Mapping[str | None, frozenset[str]] = {
    None: frozenset({"adcp.types.constraints.HttpUrl"}),
    "^https://": frozenset({"adcp.types.constraints.AdCPUrl"}),
    "^https://(?![^/]*@)(?!localhost(?:[:/]|$))(?!\\[)(?!\\d+(?:\\.\\d+){3}(?::|/|$))"
    "(?:[A-Za-z0-9-]+\\.)+[A-Za-z]{2,}(?::\\d+)?(?:/|$)": frozenset(
        {"adcp.types.constraints.HttpUrl"}
    ),
    "^https://[!$&-;=@-~]+$": frozenset({"adcp.types.constraints.HttpUrl"}),
    "^https://[^/?#@]+$": frozenset({"adcp.types.constraints.HttpUrl"}),
    "^https://[^/?#@]+(?:/[^?#]*)?$": frozenset({"adcp.types.constraints.HttpUrl"}),
    "^https://[^/?#@]+(?:/[^?#]*)?(?:\\?[^#]*)?$": frozenset(
        {"adcp.types.constraints.HttpUrl"}
    ),
    "^https://github\\.com/": frozenset({"adcp.types.constraints.HttpUrl"}),
    "^https?://(?:[A-Za-z0-9._~!$&'()*+,;=:%-]+@)?"
    "(?:[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?|\\[[0-9A-Fa-f:.]+\\])"
    "(?::[0-9]{1,5})?(?:[/?#]|$)": frozenset({"adcp.types.constraints.HttpUrl"}),
}

#: ``url_type``'s own rationale, quoted once so the mapping test and the value test give
#: one reader one reason.
URL_TYPE_RATIONALE = (
    "codegen/constraints.py's url_type docstring, the comment above "
    "codegen.lower.scalars.FORMAT_TYPES, and docs/plan/rebuild-plan.md D5's format row"
)
URL_TYPE_BECAUSE = (
    "format: uri references RFC 3986, so a bare {'type': 'string', 'format': 'uri'} "
    "admits https://, http://, urn: and file:/// alike.  'AdCPUrl everywhere' refuses "
    "three of the four and was measured at 228 of the bundle's 300 uri positions in 128 "
    "of 160 documents narrowed against their own document; HttpUrl's own ceiling is 227, "
    "which is why the SPLIT is the decision and neither arm alone is.  End to end on a "
    "shipped class: core/placement-evidence.json#/properties/url states only the bare "
    "pair, the document admits {'url': 'http://x.example/p'}, and AdCPUrl there made "
    "PlacementEvidence.strict_validate raise \"URL scheme should be 'https'\".  The other "
    "direction is no less measured: the eight patterns the bundle states cannot be "
    "carried by any URL type, so the document's own pattern stays with the schema half "
    "and HttpUrl's two added facts are admitted by harness.URL_IMPLIED, one row each."
)


def _uri_nodes() -> list[tuple[str, dict]]:
    """Every ``format: uri`` node of the bundle, by position.

    The instrument is "any node carrying ``format: uri``", which is D5's own and gives
    its figures.  Additionally requiring ``type: string`` drops
    ``core/macro-bearing-url.json#/anyOf/1`` -- the ``^https?://`` position whose author
    admitted ``http`` deliberately, and the one spelling most worth grading -- because
    that node states no ``type`` of its own.
    """
    out: list[tuple[str, dict]] = []
    for document in sorted(bundle.portable(SOURCE)):
        for pointer, node in _walk(bundle.read(SOURCE, document)):
            if isinstance(node, dict) and node.get("format") == "uri":
                out.append((f"{document}#{pointer}", node))
    return out


def _walk(node: Any, ptr: str = "") -> Any:
    """Every node of a document, by JSON pointer, ``$defs`` and all (§6)."""
    if isinstance(node, dict):
        yield ptr, node
        for key, value in node.items():
            yield from _walk(value, f"{ptr}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, f"{ptr}/{index}")


def test_url_type_chooses_the_same_type_for_every_spelling_of_a_url_the_bundle_states() -> None:
    """**The gap the incident went through, pinned as a mapping and not as a branch.**

    ``url_type`` is a decision whose whole expression is a function body with the
    measurement in its docstring, so no registry guards it and no test read it.  The
    obvious guard -- assert ``AdCPUrl`` where the pattern is ``HTTPS_ONLY`` and
    ``HttpUrl`` elsewhere -- is a SECOND COPY of a keyword decision, which the
    architecture gates forbid and which would pass unchanged for a function rewritten to
    read a different keyword with the same effect on nothing.

    What is pinned instead is the mapping the function PRODUCES over the bundle: the
    function is asked about every ``format: uri`` node the bundle states, and the answers
    are collected under the node's own ``pattern``.  So the pin is a function of the
    bundle, the branch is nowhere restated, and every way of breaking the decision lands
    here:

    * ``AdCPUrl`` everywhere, or ``str`` everywhere, moves eight or nine entries;
    * widening ``HTTPS_ONLY`` moves the ``^https://`` entry to ``HttpUrl``;
    * a second input to the function makes one spelling answer two paths;
    * an upstream repair to a pattern removes a key and adds another, which is the
      shrink-on-its-own :data:`URL_TYPE_OVER_THE_BUNDLE` is written for.
    """
    nodes = _uri_nodes()
    claimed("format: uri positions the bundle states", {position for position, _ in nodes})
    live: dict[str | None, set[str]] = {}
    for _, node in nodes:
        live.setdefault(node.get("pattern"), set()).add(constraints.url_type(node))
    derived = {pattern: frozenset(paths) for pattern, paths in live.items()}
    if derived == dict(URL_TYPE_OVER_THE_BUNDLE):
        return
    moved = {
        pattern: (
            sorted(URL_TYPE_OVER_THE_BUNDLE.get(pattern, frozenset())) or "<not in the bundle>",
            sorted(derived.get(pattern, frozenset())) or "<no longer in the bundle>",
        )
        for pattern in sorted(set(URL_TYPE_OVER_THE_BUNDLE) | set(derived), key=repr)
        if URL_TYPE_OVER_THE_BUNDLE.get(pattern) != derived.get(pattern)
    }
    raise AssertionError(
        _say(
            "codegen.constraints.url_type, as the mapping it produces over the bundle",
            URL_TYPE_RATIONALE,
            URL_TYPE_BECAUSE,
            "  these spellings of a URL now resolve differently (recorded -> live):\n"
            + "\n".join(f"    {p!r}: {was} -> {now}" for p, (was, now) in moved.items()),
        )
    )


def test_url_implied_holds_the_value_the_selected_arms_actually_render() -> None:
    """``URL_IMPLIED``'s two values, DERIVED from pydantic instead of restated.

    Its own comment states the claim: "the two facts a pydantic URL type renders OF ITS
    OWN, each with the exact value it renders ... compared for equality, so the rows admit
    THESE TWO FACTS and not 'a bound on a URL type': a rule that admitted any added bound
    would be invisible and permanent."

    **So the pin asks pydantic rather than writing ``2083`` down again**, and both sides
    are derived: the arms are the ones ``url_type`` actually selects over the bundle, each
    resolved to its type and rendered through ``TypeAdapter``, and the keys are
    ``URL_IMPLIED``'s own.  That is stronger than a literal in three ways -- ``2083`` is a
    fact about pydantic's rendering and not about this SDK, so a pydantic upgrade that
    moved it would redden a literal pin as a defect in the SDK while reddening this one as
    what it is; a value edited in the registry reddens; and an arm swapped for a type that
    renders something else reddens even when the registry is untouched.

    The reach of the registry -- that it admits exactly these keywords and no third one --
    is the next test's, derived over the graded population.
    """
    nodes = _uri_nodes()
    claimed("format: uri positions the bundle states", {position for position, _ in nodes})
    arms = sorted({constraints.url_type(node) for _, node in nodes})
    rendered: dict[str, Any] = {}
    for path in arms:
        module, _, name = path.rpartition(".")
        rendered[path] = TypeAdapter(getattr(importlib.import_module(module), name)).json_schema()
    #: What the arms render AT THE KEYWORDS THE REGISTRY NAMES.  Keyed off the registry so
    #: this does not become a second statement about which facts a URL type adds -- that
    #: half is the reach test's, and a disagreement there is what says the key set moved.
    live = {
        keyword: sorted(
            {repr(schema[keyword]) for schema in rendered.values() if keyword in schema}
        )
        for keyword in sorted(harness.URL_IMPLIED)
    }
    recorded = {keyword: [repr(value)] for keyword, value in sorted(harness.URL_IMPLIED.items())}
    if live == recorded:
        return
    raise AssertionError(
        _say(
            "codegen.harness.URL_IMPLIED, against what the arms url_type selects render",
            "codegen/harness.py, the comment above URL_IMPLIED and compare_schema's "
            "URL-type rows, and docs/plan/rebuild-plan.md section 2's narrowing clause",
            "section 2: 'A narrowing taken on purpose is admitted by an ENUMERATED "
            "registry and by nothing else ... Each entry is compared by equality so it "
            "admits that fact and not its kind -- a rule admitting \"the sort of bound a "
            "URL type adds\" would be invisible and permanent.'  These are the two facts "
            "pydantic's URL types render that no bare format: uri document states, and "
            "they are two rows and not one widened row for exactly that reason.",
            f"  the arms url_type selects over the bundle: {arms}\n"
            f"  what they render:  {live}\n"
            f"  what URL_IMPLIED says they render: {recorded}",
        )
    )


# --------------------------------------------------------------------------- #
# the reach: what the comparison ADMITS, derived by switching each row off
# --------------------------------------------------------------------------- #
#: **Every fact the schema comparison admits over the whole graded population, by the
#: mechanism that admits it, keyed by KEYWORD.**  Derived on the live side by
#: perturbation: each mechanism is switched off, the comparison is re-run, and what
#: reappears in the reported buckets is that mechanism's reach.  Pinned by keyword and
#: never by count -- how MANY positions a row covers is a property of how much the
#: emitter emits, and a number that moves whenever the build succeeds is noise
#: (``test_every_check_names_its_set.py``'s first rule).
#:
#: This is what keeps the value pins above from being "a hand-written list beside the
#: comparison ... complete with respect to itself and blind to everything beyond it"
#: (§8).  A new hand-written row, wherever in these mechanisms it is written, admits
#: some keyword; that keyword appears in this derivation and is not in this mapping, and
#: the guard reddens naming it.  A row that STOPS firing reddens too, which is the
#: shrink-on-its-own ``dump_exemptions`` relies on: the compiler got better, and the
#: decision goes.
ADMITTED: Mapping[str, frozenset[str]] = {
    "harness.URL_IMPLIED": frozenset({"minLength", "maxLength"}),
    "harness._schema_half_enforces": frozenset({"pattern"}),
    "harness._narrows_nothing": frozenset({"type", "default"}),
    "harness._constrains_nothing": frozenset({"required", "default"}),
    "harness._states_no_graded_fact": frozenset({"properties"}),
}

#: Why each mechanism admits what it admits, for the message.  One sentence each, and
#: each one is the measurement its own docstring carries.
WHY_ADMITTED: Mapping[str, str] = {
    "harness.URL_IMPLIED": (
        "the two facts a pydantic URL type renders of its own, which no bare format: uri "
        "document states -- minLength: 1 by every URL type and maxLength: 2083 by "
        "HttpUrl.  TWO ROWS AND NOT ONE WIDENED ROW: a rule reading 'a bound on a URL "
        "type is admitted' would admit a third bound nobody decided, invisibly and for "
        "good"
    ),
    "harness._schema_half_enforces": (
        "the document's own pattern at a URL-typed node, which no URL type can carry.  "
        "D5 keeps the pattern with the SCHEMA half -- strict_validate runs the document "
        "before anything is constructed -- so the model omitting it drops no enforcement. "
        " Gated on the keyword being pattern, so a maxLength or an enum the document "
        "states still lands in missing"
    ),
    "harness._narrows_nothing": (
        "the two model-only facts this pipeline's own output forces: D4 renders an "
        "optional property T | None = None and pydantic reports that as default: null, "
        "which is how absence is spelled in Python and not a claim about the document; "
        "and a type word a conjunct entails, where the model is a union root's base class "
        "and the document states the word inside the branches"
    ),
    "harness._constrains_nothing": (
        "a DOCUMENT fact that admits exactly what its absence admits, so a model omitting "
        "it is not wider: an empty required, and a default at a key the document does not "
        "demand.  The mirror of _narrows_nothing, and reported apart from missing so the "
        "fold stays auditable at its positions"
    ),
    "harness._states_no_graded_fact": (
        "a model-only properties ENTRY that is the empty schema, which section 8 reads the "
        "way section 5's additionalProperties row already reads {} -- as true, so the "
        "entry constrains nothing and a document with no entry for the key admits exactly "
        "the same instances.  It is the FIRST mechanism on the added side, and added is "
        "the half that can make a faithful SDK refuse valid traffic, so the scope is the "
        "empty schema and nothing wider: any GRADED key in the entry is a real fact and "
        "still reports added"
    ),
}


#: The ``ComparisonResult`` lists a perturbation can move a keyword between: the two
#: buckets that REPORT an admission (``url_typed``, ``constrains_nothing``) and the two
#: that report a defect (``added``, ``missing``).  Named by their own attribute names and
#: read with ``getattr``, so a bucket renamed in the harness reddens here rather than
#: being silently measured as empty.
BUCKETS = ("url_typed", "constrains_nothing", "vacuous_entry", "added", "missing")


def _reach() -> dict[str, frozenset[str]]:
    """Each mechanism's reach over the graded population, by perturbation.

    One live pass and one pass per mechanism, each comparing every graded pair the way
    ``check_pair`` does -- same node, same document scope, same declarations, same
    pointer.  The DELTA is the reach: a keyword the live pass reports as admitted and the
    perturbed pass does not (the mechanism stopped excusing it), or a keyword the
    perturbed pass reports as a defect and the live pass does not (the mechanism was
    hiding it).

    Probing by patching the row is this tree's own idiom for a measurement a reading
    cannot take -- ``union.ROOT_CONJUNCTS``'s comment records two such probes -- and it is
    what makes the reach DERIVED rather than a second list of keywords.  The patches are
    undone by :func:`unittest.mock.patch`'s context, so nothing leaks into the pairs
    another test in this worker grades.
    """
    from unittest import mock

    import test_emit  # the tree reader, one reading for the whole suite

    pairs = [test_emit.pair_of(g) for g in test_emit.graded()]
    #: The DENOMINATOR, named here rather than in the caller because this is where the
    #: derivation happens.  A perturbation over zero pairs reports an empty reach for
    #: every mechanism, which is a broken instrument that reads as "no decision is
    #: admitted" -- the vacuous pass section 8's last paragraph is about.
    claimed("graded pairs the comparison runs over", {pair.name for pair in pairs})

    def pass_over() -> dict[str, set[str]]:
        found: dict[str, set[str]] = {b: set() for b in BUCKETS}
        for pair in pairs:
            res = harness.compare_schema(
                pair.schema,
                pair.model,
                document=pair.document,
                declared=pair.declared,
                at=pair.ref.pointer if pair.ref is not None else "#",
            )
            for bucket in BUCKETS:
                found[bucket] |= _keywords(getattr(res, bucket))
        return found

    live = pass_over()
    out: dict[str, frozenset[str]] = {}
    with mock.patch.object(harness, "URL_IMPLIED", {}):
        out["harness.URL_IMPLIED"] = frozenset(live["url_typed"] - pass_over()["url_typed"])
    with mock.patch.object(harness, "_schema_half_enforces", lambda *a, **k: False):
        gone = live["url_typed"] - pass_over()["url_typed"]
        out["harness._schema_half_enforces"] = frozenset(gone)
    with mock.patch.object(harness, "_narrows_nothing", lambda *a, **k: False):
        out["harness._narrows_nothing"] = frozenset(pass_over()["added"] - live["added"])
    with mock.patch.object(harness, "_constrains_nothing", lambda *a, **k: False):
        out["harness._constrains_nothing"] = frozenset(pass_over()["missing"] - live["missing"])
    # The ADDED direction, and the delta is read there for the reason the two above read
    # it in ``missing``: with the fold off, the entry it excuses reappears as ``added``.
    with mock.patch.object(harness, "_states_no_graded_fact", lambda *a, **k: False):
        out["harness._states_no_graded_fact"] = frozenset(pass_over()["added"] - live["added"])
    return out


def _keywords(lines: list[str]) -> set[str]:
    """The keyword each reported line is about.

    Every bucket spells a line ``"<pointer>/<keyword>: <sentence>"``, so the keyword is
    the last pointer segment before the colon.  Read off the production message rather
    than re-derived, because the message is what a reader of a red pair sees and a
    keyword this cannot read is a line that names no fact.
    """
    return {line.split(":", 1)[0].rsplit("/", 1)[-1] for line in lines}


def test_the_comparison_admits_no_fact_this_file_does_not_name() -> None:
    """**The half that keeps the pins above from being blind beyond themselves.**

    A value pin reddens when an entry it names changes and says nothing at all about a
    decision added beside it -- which is §8's "a hand-written list beside the comparison
    is the one way this check can be complete with respect to itself and blind to
    everything beyond it".  So the facts the comparison ADMITS are derived, over every
    graded pair, by switching each admission mechanism off and reading what reappears.

    Both sides are then sets of keywords and both redden:

    * **a new row** -- a keyword that was reported as a defect and is now excused appears
      in the derivation, is absent from :data:`ADMITTED`, and this names it.  That is the
      shape the incident would have taken had it gone the other way: a row added to make a
      red pair green is exactly a decision taken without a reader;
    * **a row that stops firing** -- its keyword leaves the derivation and this reddens
      until the entry goes, so a decision the compiler outgrew cannot sit here excusing
      nothing.

    No COUNT is pinned, deliberately: how many positions a row covers is a property of
    how much of the bundle the emitter emits, so a count here would redden on the build
    succeeding.  What is pinned is which FACTS are excused and by what, which is the thing
    a reader of a green pair needs to know and cannot otherwise find out.
    """
    live = _reach()
    claimed("admission mechanisms the comparison carries", set(live))
    if live == dict(ADMITTED):
        return
    moved = {
        mechanism: (
            sorted(ADMITTED.get(mechanism, frozenset())),
            sorted(live.get(mechanism, frozenset())),
        )
        for mechanism in sorted(set(ADMITTED) | set(live))
        if ADMITTED.get(mechanism) != live.get(mechanism)
    }
    raise AssertionError(
        _say(
            "the facts codegen.harness.compare_schema admits, by mechanism",
            "codegen/harness.py: the comment above URL_IMPLIED, and the docstrings of "
            "_schema_half_enforces, _narrows_nothing and _constrains_nothing.  The rule "
            "they all answer to is docs/plan/rebuild-plan.md section 2's narrowing "
            "clause, and section 8's two equalities above the three checks",
            "\n  ".join(
                f"{mechanism}: {WHY_ADMITTED.get(mechanism, '<no reason recorded>')}"
                for mechanism in sorted(moved)
            ),
            "  the admitted set moved (recorded -> live):\n"
            + "\n".join(
                f"    {mechanism}: {was} -> {now}" for mechanism, (was, now) in moved.items()
            )
            + "\n\n  A keyword that APPEARED is a fact the comparison used to report and "
            "now excuses.\n  A keyword that LEFT is a decision excusing nothing, and the "
            "entry goes.",
        )
    )
