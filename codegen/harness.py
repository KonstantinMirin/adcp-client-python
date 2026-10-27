"""Property-based conformance harness for a (JSON Schema document, model) pair.

Knows nothing about any particular schema vocabulary, directory layout, code
generator or model package.  Its whole input is:

  * ``schema``  - a JSON Schema document, as a dict, with every ``$ref`` already
                  resolved (use ``resolve`` below, or resolve it yourself).
                  ``resolve`` inlines a fresh copy of a subtree at every site
                  that references it, so it costs O(paths through the ref
                  graph) -- affordable for one document, and not for a bundle:
                  it left 63 of 1,033 unresolvable at any practical budget.
                  For a whole population use ``codegen.resolved_cache``, which
                  memoizes per URI and composes by reference. This module does
                  not import it, and must not: ``selfcheck`` asserts that
                  ``harness`` imports nothing beyond its four libraries and
                  stdlib, so the choice belongs to the caller.
  * ``model``   - anything ``pydantic.TypeAdapter`` accepts: a BaseModel subclass,
                  a RootModel, an Enum, a bare annotation, a union alias.
  * ``accept``  - the entry point an instance is offered through, SUPPLIED by the
                  caller.  It used to be sniffed off the model with ``getattr``,
                  and sniffing cannot tell a model that has no entry point from
                  one whose entry point is missing: the fallback was the model's
                  CONSTRUCTOR, which is not an accepted set, so a model that
                  should have had one was graded wide and green.  The caller
                  knows which it is; this module does not and now does not guess.

**ONE CLASS AGAINST ONE SCHEMA, AND NO ITERATION OVER KEYWORDS** (section 6).  Per
pair, four things happen and each is O(1) in the document's keyword count:

  the accepts check (``check_accepts``)
      schema -> payload -> model: an instance the schema admits, the model admits.
      It then DUMPS what it constructed and validates the dump against the same
      document (``AcceptsResult.round_tripped``), which is the one thing in this
      module that reads what the class does with a value rather than whether it
      took it.

  the liveness check (``check_liveness``)
      one payload the DOCUMENT refuses, routed through the entry point the caller
      supplies -- ``strict_validate``, whose schema half answers.  It proves that
      class's schema half is CONNECTED and that the ref it names resolves to the
      document it names.  It is not a measurement of the class: pydantic is
      deliberately less strict than the schema, so a refusal says the document
      answered (D4).

  the schema comparison (``compare_schema``)
      every fact the document states about a value, the model's own
      ``model_json_schema()`` states too.  **This is what grades the generated
      code**, and it is the only check that sees a ``default`` or a
      ``description``, because neither changes the accepted set.

**WHAT THIS MODULE USED TO DO AND NO LONGER DOES, and the reason is stronger than
its cost.**  The refuses check mutated ONE KEYWORD at a time, drew an instance the
mutated schema accepts, and passed it to the caller's ``accept`` -- which validates
against THE DOCUMENT before constructing.  So a step site asserted that
``jsonschema`` rejects a payload violating the schema it was handed, and the
generated class took no part in the outcome: on ``core/pagination-request.json`` a
model with ``Any`` on every field accepted, refused 75 of 75 instances and recorded
no wrong acceptance, exactly as a faithful one did.  27,791 of those sites over the
graded population were the suite's entire wall clock, spent on a property of a
third-party validator.  A payload the schema refuses is informative
about the WIRING and nothing else, so ``check_liveness`` sends exactly one.

**There is no process-global canonicalisation memo here**, and the documents this
grades arrive as the DOCUMENT OF RECORD (``bundle.record``, which inlines every
cross-document ``$ref`` and rewrites nothing), so the one recursion reference
resolution needs has happened before the harness sees anything.  What remains is the
library's own: ``merged`` re-enters ``canonicalish``
for every subschema it sorts, so one ``from_schema`` call re-canonicalises the same
subtrees of one document.  ``canonicalisation_shared_within_one_call`` shares those
for the duration of ONE check and drops them on the way out -- its docstring carries
the measurement that forces it, and why that is not the unbounded process-global
dict section 6 deleted.
"""

from __future__ import annotations

import copy
import json
from contextlib import contextmanager
from collections import Counter
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import jsonschema
from hypothesis import HealthCheck, Phase, given, settings
from hypothesis import strategies as st
from hypothesis.errors import HypothesisException
from hypothesis_jsonschema import _canonicalise as _hjs_canon
from hypothesis_jsonschema import from_schema
from hypothesis_jsonschema._canonicalise import HypothesisRefResolutionError
from hypothesis_jsonschema._resolve import LocalResolver, resolve_all_refs
from pydantic import TypeAdapter, ValidationError

from adcp.types._base import (
    APPROXIMATIONS,
    KINDS,
    UNDERDETERMINED,
    Approximation,
    SchemaRef,
)
from codegen import attribution, bundle, dump_exemptions, keywords
from codegen.keywords import Position, Rung

# --------------------------------------------------------------------------- #
# formats
# --------------------------------------------------------------------------- #
# hypothesis_jsonschema ignores a `format` it does not know, silently and without
# a warning, which turns an unsupported format into arbitrary text and so into a
# false direction-1 failure.  A caller supplies a strategy per format its
# documents use; `missing_formats` says which ones still need one.
BUILTIN_FORMATS: frozenset[str]
try:  # the name is private, so degrade rather than break on an upgrade
    from hypothesis_jsonschema._from_schema import STRING_FORMATS as _BF

    BUILTIN_FORMATS = frozenset(_BF)
except ImportError:  # pragma: no cover
    BUILTIN_FORMATS = frozenset()


def format_occurrences(schema: Any) -> Counter[str]:
    """Every ``format`` annotation at a schema position, COUNTED.

    ``formats_used`` is this, deduped. The count is the separate question: a format
    used once and a format used 46 times are the same membership and very different
    populations, and a verdict read off a population nobody counted is a verdict
    over however many sites there turned out to be -- including none.
    """
    out: Counter[str] = Counter()

    def rec(node: Any) -> None:
        if isinstance(node, list):
            for v in node:
                rec(v)
            return
        if not isinstance(node, dict):
            return
        f = node.get("format")
        if isinstance(f, str):
            out[f] += 1
        for k, v in node.items():
            if k in _DESCEND_MAP and isinstance(v, dict):
                for vv in v.values():
                    rec(vv)
            elif k in _DESCEND_ONE and isinstance(v, (dict, list)):
                rec(v)
            elif k in _DESCEND_LIST and isinstance(v, list):
                rec(v)

    rec(schema)
    return out


def formats_used(schema: Any) -> set[str]:
    """Every ``format`` value appearing at a SCHEMA POSITION in a document.

    Position is the whole of it, and a walk that ignores position reports formats
    that do not exist. ``examples``, ``example``, ``default``, ``const`` and
    ``enum`` hold INSTANCE data, so a dict beneath one of them is a value: its
    ``format`` key is a data field with a name that collides, not a format
    annotation, and no generator ever consults it. A bundle met here illustrated a
    field-mapping object whose own ``format`` property named a date layout, inside
    an ``examples`` array, at 46 places. The blanket walk reported that layout as an
    uncovered format and a strategy was written for it; the strategy covered nothing
    and its only effect would have been to stop ``missing_formats`` saying so. That
    is strictly worse than the silence it was meant to fix, because the silence is
    reported and the quiet is not.

    Skipping those five keyword NAMES wherever they appear is not the same fix and
    is wrong: a property may legitimately be named ``default``, and in that bundle 95
    were. So this descends only where a subschema can legally appear, by the same
    tables ``steps`` descends (declared with it below, so the two walks cannot come
    to disagree about what a schema position is).
    """
    return set(format_occurrences(schema))


def missing_formats(schema: Any, custom_formats: Mapping[str, Any]) -> set[str]:
    """Formats the document uses that neither the library nor the caller covers."""
    return formats_used(schema) - BUILTIN_FORMATS - set(custom_formats)


# --------------------------------------------------------------------------- #
# resolution
# --------------------------------------------------------------------------- #
def resolve(
    schema: dict, *, store: Mapping[str, Any], base_uri: str = "", referrer: Any = None
) -> dict:
    """Inline every ``$ref`` using hypothesis_jsonschema's own resolver.

    **CONFINED TO DRAWING, and that is the whole of what it is for now.**
    ``docs/plan/architecture.md`` §4 keeps the payload generator's resolver inside the
    accepts check, where it may canonicalise its own copy because that copy is an
    instrument of ONE check and is not the document.  :func:`check_accepts` is the one
    caller, it hands the copy to ``from_schema`` and to nothing else, and nothing
    downstream reads what it writes.  The DOCUMENT is ``bundle.record``'s, which inlines
    and rewrites nothing -- so the six folds that undid this resolver's rewritings are
    deleted (§9) and none of them can come back by this door.

    ``store`` maps an absolute URI to the document at it.  A ``$ref`` that is not
    in the store raises, by the library's design: it never fetches remotely.

    ``referrer`` is what a LOCAL pointer (``#/definitions/x``) resolves against, and
    it defaults to ``schema`` -- which is right for a whole document and wrong for a
    NODE of one.  ``bundle.record`` inlines a cross-document reference and leaves a
    local one, so a nested node's own ``$ref`` is a pointer into the DOCUMENT ROOT:
    given the node as its own referrer, the library raises
    ``_RefResolutionError: Unresolvable JSON pointer``.  Pass the document and the
    same call inlines it (``salesagent-j3k2l.28``).
    """
    doc = copy.deepcopy(schema)
    scope = copy.deepcopy(doc if referrer is None else referrer)
    resolver = LocalResolver(base_uri=base_uri, referrer=scope, store=dict(store))
    return resolve_all_refs(doc, resolver=resolver)


def strategy(schema: dict, custom_formats: Mapping[str, Any]) -> st.SearchStrategy:
    return from_schema(schema, custom_formats=dict(custom_formats))


@contextmanager
def canonicalisation_shared_within_one_call() -> Iterator[dict[str, Any]]:
    """Share ``canonicalish`` results for the duration of ONE check, then drop them.

    **THIS IS A DIVERGENCE FROM SECTION 6's LETTER AND IT IS MEASURED.**  Section 6
    says ``_CANON_MEMO`` is "DELETED, not bounded", because "a repetition that
    resolution removes needs no cache at all".  The first half is right and is done:
    there is no process-global dict here, nothing is retained between pairs, and
    nothing is patched at import time.  **The second half is refuted by the
    measurement.**  The repetition the memo covered is not only across step sites --
    ``merged`` re-enters ``canonicalish`` for every subschema it sorts
    (``_canonicalise.py:631``), so ONE ``from_schema`` call on ONE already-resolved
    document re-canonicalises the same subtrees. Resolution cannot remove that: the
    document arrives with zero ``$ref`` and the repetition is inside the library's
    own recursion.

    Measured on ``core/macro-declaration.json#``, 18,301 bytes, one pair, single
    process, no profiler:

    ======================================  ==========  =============
    ``from_schema`` on that one document    seconds     memo entries
    ======================================  ==========  =============
    sharing within the call                     43.58            504
    no sharing at all                         >600.0  (stopped)     -
    ======================================  ==========  =============

    So deleting the sharing outright does not make the suite cheaper, it makes one
    pair cost more than the whole population does with it.

    **What section 6's complaint actually names, and what this keeps out.**  The
    defect was "an unbounded process-global dict ... grows by roughly 340 entries per
    pair", retained across every pair of the population and multiplied by ten
    workers, with a measured hit rate and no measured size.  A memo whose lifetime is
    one call has none of those properties: its contents are one document's
    subschemas, 504 at the measured worst, it is discarded on exit including on an
    exception, and that size is the figure above rather than an unknown.  The name
    says the lifetime, so a later reader cannot widen it without renaming it.
    """
    memo: dict[str, Any] = {}
    uncached = _hjs_canon.canonicalish

    def shared(schema: Any) -> Any:
        try:
            key = json.dumps(schema, sort_keys=True, default=repr)
        except (TypeError, ValueError):
            return uncached(schema)
        hit = memo.get(key)
        if hit is None:
            hit = memo[key] = uncached(schema)
        # A DEEP COPY on the way out: the library mutates the nodes it is handed, so
        # returning the held object would let one call corrupt every later one.
        return copy.deepcopy(hit)

    _hjs_canon.canonicalish = shared
    try:
        yield memo
    finally:
        _hjs_canon.canonicalish = uncached


def format_pattern_positions(schema: Any) -> list[tuple[str, dict]]:
    """Every position where a ``format`` and a ``pattern`` meet, node and pointer.

    **The shape ``hypothesis_jsonschema`` has no generator for**, and the reason is in
    its own source: ``string_schema`` takes the FORMAT's strategy and then applies the
    pattern as a ``.filter()``, with the comment *"This isn't really supported, but
    we'll do our best with a filter"*.  Where the pattern restricts the value beyond
    what the format strategy happens to emit, every draw is filtered out and
    ``hypothesis`` raises ``Unsatisfiable`` over the WHOLE schema, naming no node.

    It is not gated on the format being ASSERTED, and that is deliberate: the filter
    runs whether or not a checker is installed, so the drawing problem is the same.

    **This is the CO-OCCURRENCE census and not the undrawable population**, which is
    the distinction :func:`undrawable_formats` exists to draw: over the 3.2 bundle 73
    positions in 47 of 1,054 documents state the two keywords together, in 8 distinct
    ``(format, pattern)`` pairs, and 72 of the 73 DRAW.
    """
    return [
        (pointer or "/", node)
        for pointer, node in _nodes(schema)
        if isinstance(node.get("format"), str) and isinstance(node.get("pattern"), str)
    ]


def _drawing_this_node(instance: Any) -> None:
    """The body :func:`undrawable_formats` draws into: the draw IS the measurement.

    Named rather than a lambda because ``hypothesis`` puts this function's name in
    ``Unsatisfiable``'s own sentence, which :func:`_why` carries into the report.
    """


def undrawable_formats(
    schema: Any, *, custom_formats: Mapping[str, Any] = (), examples: int = 25
) -> tuple[str, ...]:
    """Of the positions :func:`format_pattern_positions` names, the ones a draw cannot reach.

    **Co-occurrence is not the undrawable shape, and the measurement is the whole
    difference.** 72 of the bundle's 73 format-beside-pattern positions draw, because
    ``hypothesis_jsonschema``'s ``uri`` strategy emits ``https://A.COM`` and that
    matches every one of the bundle's patterns that pins the scheme or the general host
    shape -- 7 of its 8 distinct pairs.  The eighth pins a LITERAL host,
    ``^https://github\\.com/`` at
    ``core/reference-renderer.json#/properties/provenance/properties/source_repository``,
    and no generic generator reaches a literal host: 459 of 459 draws are filtered, at
    10, 25 and 50 examples alike.

    So a cause naming every co-occurrence would admit a ``strategy_error`` from ANY
    cause, as long as the document states the two keywords somewhere.  This draws each
    node ALONE and keeps the ones that failed, with hypothesis's own reason per
    position -- which is what makes :attr:`PairReport.no_instrument` conditional on a
    measurement of the shape rather than on two keywords meeting.

    **Derandomized, so the answer is a function of (node, library version)** and P7's
    determinism holds over it.

    KNOWN CEILING: a node undrawable only IN CONTEXT -- a conjunct narrowing the
    pattern beside it -- draws here and is not named, so its pair reddens rather than
    being admitted.  That is the safe direction and it is visible: an exit this check
    cannot explain is a failure and not a tolerance.  The upgrade path is to draw the
    node as the generator sees it, which needs the merged node the library builds
    internally.
    """
    out: list[str] = []
    for pointer, node in format_pattern_positions(schema):
        try:
            run = given(instance=strategy(node, dict(custom_formats)))(_drawing_this_node)
            settings(max_examples=examples, phases=[Phase.generate], **_SETTINGS)(run)()
        except Exception as e:  # noqa: BLE001 -- any failure to draw names the position
            out.append(
                f"{pointer}: format {node['format']!r} beside pattern"
                f" {node['pattern']!r} [{_why(e)}]"
            )
    return tuple(out)


def validator_for(schema: dict) -> Any:
    """The validator the document's own ``$schema`` names.

    One function so the three places below cannot come to validate with
    different vocabularies, and so ``format`` is asserted in all of them: see
    ``_validating``.
    """
    return jsonschema.validators.validator_for(schema, jsonschema.Draft7Validator)


def _validating(cls: Any, schema: dict) -> Any:
    """A validator instance that ASSERTS ``format``, with the draft's own checker.

    ``jsonschema`` treats ``format`` as a pure annotation unless it is handed a
    ``FormatChecker``, and the consequence is not a missing nicety: the whole
    accepted set of a formatted node went ungraded, so a model carrying a
    format-derived Python type was narrower than its own document and no check
    reported it.  The accepts check could not, because
    ``hypothesis_jsonschema`` HONOURS a format it knows when generating -- it
    produced an offset in 200 of 200 ``date-time`` instances -- and the schema
    comparison could not, because the type states exactly the fact the document
    states.

    The checker is ``cls.FORMAT_CHECKER``, the one the declared draft defines,
    rather than ``jsonschema.FormatChecker()``.  That is the faithful reading:
    the global registry carries every checker any draft defines, so it would
    assert ``uuid`` against a draft-07 document, which draft-07 does not define
    as a format -- the SDK inventing a constraint.  Which formats the draft's own
    checker can actually decide depends on what is installed, and ``pyproject``
    names the two packages that make this bundle's own formats decidable
    (``rfc3339-validator``, ``rfc3987``).  The emitter gates its type selection
    on the same set, so the two halves cannot disagree about which formats are
    asserted.
    """
    return cls(schema, format_checker=cls.FORMAT_CHECKER)


def conforms(schema: dict, instance: Any, *, validator_cls=None) -> bool | None:
    """True / False, or None when the document is not usable as a validator."""
    cls = validator_cls or validator_for(schema)
    try:
        _validating(cls, schema).validate(instance)
        return True
    except jsonschema.ValidationError:
        return False
    except Exception:
        return None


def violated_keywords(schema: dict, instance: Any, *, validator_cls=None) -> list[str]:
    """Which keywords the ORIGINAL document rejects this instance on.

    The step's own keyword is NOT a safe label for a refuses-check failure.  Two
    reasons, both measured here: ``canonicalish`` DERIVES constraints while
    resolving (``uniqueItems: true`` over a 2-member enum became ``maxItems: 2``,
    so a "maxItems" step produced an instance the document refuses on
    ``uniqueItems``), and a step drops sibling keywords it would otherwise
    contradict.  Asking the validator which keyword bit makes the attribution
    exact instead of assumed.
    """
    cls = validator_cls or validator_for(schema)
    out: list[str] = []
    for err in _validating(cls, schema).iter_errors(instance):
        for e in [err, *err.context] if err.context else [err]:
            if isinstance(e.validator, str):
                out.append(e.validator)
    return sorted(set(out))


_DESCEND_ONE = (
    "items",
    "additionalProperties",
    "contains",
    "not",
    "if",
    "then",
    "else",
    "propertyNames",
    "additionalItems",
    "unevaluatedProperties",
    "unevaluatedItems",
)
_DESCEND_MAP = ("properties", "$defs", "definitions", "patternProperties", "dependentSchemas")
_DESCEND_LIST = ("oneOf", "anyOf", "allOf", "prefixItems")


#: ``bundle.escape_key``, not a second copy: a pointer segment is spelled by four
#: readers and the two halves have to agree about a key carrying a ``/``.
#:
#: **It was ``compiler.escape_key``, and that import is what kept ``codegen.compiler``
#: in §9's permitted set.**  §11 puts a pointer speller in the SOURCE layer, so §14
#: step 5 moved the pair to ``codegen/bundle.py`` -- a module §9 permits by name, "for
#: the record and the document set" -- and the verifier now imports no module of the
#: walk at all.
_esc = bundle.escape_key


def at(doc: Any, pointer: str) -> Any:
    """Dereference a JSON Pointer against a document.

    ``bundle.node_at`` is the one reading, beside ``escape_key``'s inverse; this is
    the verifier's name for it.
    """
    return bundle.node_at(doc, pointer)


def _nodes(schema: Any, pointer: str = "") -> list[tuple[str, dict]]:
    """Every dict node of the document, with its pointer, by the same descent."""
    out: list[tuple[str, dict]] = []
    if isinstance(schema, list):
        for i, v in enumerate(schema):
            out += _nodes(v, f"{pointer}/{i}")
        return out
    if not isinstance(schema, dict):
        return out
    out.append((pointer or "/", schema))
    for k, v in schema.items():
        if k in _DESCEND_MAP and isinstance(v, dict):
            for kk, vv in v.items():
                out += _nodes(vv, f"{pointer}/{k}/{_esc(kk)}")
        elif k in _DESCEND_ONE and isinstance(v, (dict, list)):
            out += _nodes(v, f"{pointer}/{k}")
        elif k in _DESCEND_LIST and isinstance(v, list):
            out += _nodes(v, f"{pointer}/{k}")
    return out


# --------------------------------------------------------------------------- #
# results
# --------------------------------------------------------------------------- #
@dataclass
class FormatStrategyVerdict:
    """Whether a supplied format strategy produces values the format itself admits.

    ``unchecked`` is a distinct outcome from ``pass`` and that distinction is the
    reason this type exists: a validator with no checker for a format answers True
    for every input, garbage included, so grading a strategy against one says
    nothing at all. Reporting that as a pass is the vacuous pass.
    """

    fmt: str = ""
    checked: bool = False  # the validator has a checker for this format
    examples: int = 0
    accepted: int = 0  # produced values the checker admits
    rejected: str = ""  # first produced value the checker REFUSES, if any
    counterexample_refused: bool | None = None  # the second answer
    detail: str = ""

    @property
    def outcome(self) -> str:
        if self.detail:
            return "error"
        if not self.checked:
            return "unchecked"  # nothing graded the strategy; NOT a pass
        if not self.examples:
            return "no_examples"
        if self.rejected:
            return "generates_invalid"  # every site using it would pass vacuously
        if self.counterexample_refused is not True:
            return "checker_accepts_anything"
        return "pass"


@dataclass
class AcceptsResult:
    examples: int = 0
    #: pass | model_refused_valid | model_dropped_a_fact | strategy_error | model_error
    outcome: str = "unrun"
    detail: str = ""
    counterexample: str = ""
    #: How many of :attr:`examples` were dumped back out and still admitted by the
    #: DOCUMENT.  The denominator ``check_pair`` reads to tell a pair whose class
    #: round-tripped every instance from one the generator never reached.
    round_tripped: int = 0

    #: The exempt positions this pair's dump actually NEEDED,
    #: ``"<document>#<pointer>/<keyword>"`` each, from ``codegen.dump_exemptions``.
    #:
    #: **REPORTED and not silent, which is the precedent every other excused fact in
    #: this module follows** -- ``_schema_half_enforces``, ``_narrows_nothing`` and
    #: ``url_typed`` all put the excuse on the result where a reader of the pair meets
    #: it.  An exemption the harness does not report is one nobody reading a green
    #: pair can see, and this is the only check that reads what a class DID with a
    #: value.  So a non-empty list beside ``outcome == "pass"`` is a CONDITIONAL pass.
    #:
    #: **"Needed" and not "in force", and the difference was measured.**  An entry
    #: applies to every pair whose node CONTAINS the position, which it must -- an
    #: ancestor pair's dump carries the nested node, which is exactly why
    #: ``core/attestation-capabilities.json#`` is refused for a position inside
    #: ``core/attestation-issuer.json``.  But 8 pairs contain one of the four
    #: positions and only 3 are refused without it: the other 5 are ancestors whose
    #: drawn instance never reached the node.  Reporting all 8 would make this field
    #: mean "an exemption lies somewhere inside me", which is not a fact about the
    #: pair's verdict, and would make a conditional pass unreadable among pairs that
    #: pass on their own merits.  So the dump is re-validated against the UNSTRUCK
    #: node and the label is recorded only where that refuses it.
    dump_exempt: list[str] = field(default_factory=list)


@dataclass
class LivenessResult:
    """One payload the DOCUMENT refuses, offered to the entry point under test."""

    #: Which perturbation produced the payload, naming the fact it broke
    #: (``"drops the required key 'x'"``), or ``""`` when none was found.
    how: str = ""
    #: Which keywords the document refused the payload on -- asked of the document
    #: rather than assumed from the perturbation, because a perturbation can break
    #: more than it aimed at.
    violated: tuple[str, ...] = ()
    payload: str = ""
    detail: str = ""
    #: pass | schema_half_not_connected | model_error | no_payload
    outcome: str = "unrun"


# --------------------------------------------------------------------------- #
# the two directions
# --------------------------------------------------------------------------- #
_SETTINGS = dict(
    deadline=None,
    database=None,
    derandomize=True,  # byte-identical example stream across runs
    suppress_health_check=list(HealthCheck),
)


def check_format_strategy(
    fmt: str,
    strategy: st.SearchStrategy,
    *,
    counterexample: Any,
    examples: int = 50,
    format_checker: Any = None,
) -> FormatStrategyVerdict:
    """Grade a ``custom_formats`` entry before it is trusted to generate.

    ``missing_formats`` says which formats have no strategy. It cannot say whether
    a strategy that EXISTS is right, and a wrong one is the more dangerous of the
    two: a strategy emitting values the format refuses makes every site using that
    format pass vacuously, and a vacuous pass is reported by nothing. So both
    answers are required of every entry --

      * the values it produces are admitted by the format;
      * a deliberately malformed value of the same shape is REFUSED.

    The second answer is not redundant. Without it, a validator that has no checker
    for the format (``conforms`` then answers True for every input) is
    indistinguishable from one that genuinely admits what was generated. That case
    is reported as ``unchecked``, which is not a pass: a format nothing checks
    cannot be graded by checking it, and the caller is owed that fact rather than a
    green mark.
    """
    fc = format_checker if format_checker is not None else jsonschema.FormatChecker()
    v = FormatStrategyVerdict(fmt=fmt, checked=fmt in fc.checkers)
    if not v.checked:
        return v

    def body(value: Any) -> None:
        v.examples += 1
        if fc.conforms(value, fmt):
            v.accepted += 1
        elif not v.rejected:
            v.rejected = repr(value)[:200]

    try:
        run = given(value=strategy)(body)
        run = settings(max_examples=examples, phases=[Phase.explicit, Phase.generate], **_SETTINGS)(
            run
        )
        run()
        v.counterexample_refused = not fc.conforms(counterexample, fmt)
    except Exception as e:
        v.detail = f"{type(e).__name__}: {e}"[:300]
    return v


class _DumpRefused(Exception):
    """The class constructed a value whose DUMP its own document refuses.

    Raised from inside the accepts check's body and caught BY NAME, so the verdict
    is ``model_dropped_a_fact`` and not the ``model_error`` any other exception from
    the body reads as.  The instance that showed it is reported verbatim: there is
    no shrink phase to simplify it, and at the default ``examples=1`` there is one
    generated instance for a shrink to have worked on anyway.
    """


def _wire_dump(value: Any) -> Any:
    """What ``value`` looks like on the wire, by pydantic's own reading.

    ``mode="json"`` so a ``datetime`` and a URL come back as the strings their
    documents declare; ``by_alias`` because a document's key is the alias wherever
    the two differ; and ``exclude_unset`` because a key the payload never carried
    is not a fact the document stated about it -- dumping the model's rendering of
    absence instead would charge the class for a ``null`` the instance never had.

    A scalar root is an ``Annotated`` ALIAS and not a class (D2), so there is no
    ``model_dump`` to call and the adapter for the value's own type is the dump:
    it is the same conversion pydantic would apply to that field inside a class.
    """
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True, exclude_unset=True)
    return TypeAdapter(type(value)).dump_python(value, mode="json")


#: A key no document in any bundle declares, used to probe a closed object.
_ALIEN_KEY = "__adcp_harness_not_a_property__"

#: Values spanning the JSON types, tried in order as a whole-instance replacement.
#: One of them has a different JSON type from any instance, so a document that
#: states a root ``type`` at all refuses at least one.
_ALIEN_VALUES: tuple[Any, ...] = (None, "__adcp_harness__", -1, [], {}, True)


def refusing_payload(
    schema: dict, instance: Any, *, validator_cls: Any = None
) -> tuple[Any, str] | None:
    """One payload the DOCUMENT refuses, derived from one it ACCEPTS.

    Section 6 asks for one payload the schema refuses per class, routed through the
    entry point once.  It is DERIVED from the accepted instance
    rather than drawn, which is the whole saving: a draw from a mutated document
    costs ``from_schema`` another canonicalisation of the whole document, and the
    27,791 of those is what this rebuild removes.

    Three perturbations, tried in this order, and the order is the point:

    1. **drop a key the root ``required`` names.**  A missing required key is the
       plainest thing a document refuses, so it is the cheapest proof that the
       schema half ran at all.
    2. **replace the whole instance with a value of another JSON type.**  Reaches a
       root that demands no key, and a scalar root, which the first cannot.
    3. **add a property no document declares.**  Last, so it is reached only by a
       root that admits every scalar -- an open object.

    **Every candidate is screened by the DOCUMENT**, which is what keeps this from
    asserting a refusal the document does not make: ``conforms`` has to answer
    ``False`` before a payload is offered to anything.  Where no candidate is
    refused the document admits all three shapes, there is no invalid payload to
    find, and ``None`` says so rather than a perturbation being forced through.
    """
    cls = validator_cls or validator_for(schema)

    def refused(candidate: Any) -> bool:
        return conforms(schema, candidate, validator_cls=cls) is False

    if isinstance(instance, dict):
        for key in schema.get("required", []) if isinstance(schema.get("required"), list) else []:
            if key in instance:
                candidate = {k: v for k, v in instance.items() if k != key}
                if refused(candidate):
                    return candidate, f"drops the required key {key!r}"
    for alien in _ALIEN_VALUES:
        if type(alien) is not type(instance) and refused(alien):
            return alien, f"replaces the instance with {alien!r}"
    if isinstance(instance, dict):
        candidate = {**instance, _ALIEN_KEY: 1}
        if refused(candidate):
            return candidate, f"adds the property {_ALIEN_KEY!r}"
    return None


def check_liveness(
    schema: dict,
    accept: Callable[[Any], Any],
    instance: Any,
    *,
    validator_cls: Any = None,
) -> LivenessResult:
    """Offer one payload the document refuses to the entry point, ONCE per class.

    **This is a LIVENESS check on the wiring and it is not a measurement of the
    class.**  Section 6 is explicit about why, and about why it used to be read the
    other way: pydantic is DELIBERATELY less strict than the schema.  D4 gives the
    schema the acceptance decision and pydantic the construction, so a model holds
    the document's types and emits the document's schema rather than reimplementing
    every JSON Schema keyword -- which is the whole reason ``strict_validate``
    exists.  So a payload the schema refuses says nothing about the generated code
    on EITHER route: ``model_validate`` may accept it by design, and ``accept``
    refuses it because the document answered.

    What one refusal through ``accept`` does prove is that this class's schema half
    is CONNECTED and that the ref it names resolves to the document it names.  That
    is worth asserting once per class, and it is what the 27,791-site sweep was
    already asserting -- 27,791 times, at the cost of the suite's entire wall clock.

    An ACCEPTANCE is therefore ``schema_half_not_connected``: the document refuses
    this payload and the entry point did not, so either the schema half is not
    running or ``__adcp_schema__`` does not resolve to this document.

    **That verdict is a statement about the WIRING and never about pydantic's
    strictness, and the distinction is load-bearing enough to say twice.**  Pass this
    a bare ``model_validate`` and it will report ``schema_half_not_connected`` on a
    perfectly correct class, because a correct class MAY accept a schema-invalid
    payload -- that is D4, and section 6 says so in as many words.  So ``accept`` is
    the entry point the caller ships, the one whose schema half answers first; the
    only thing an acceptance can mean through THAT is that the half is missing.
    ``check_pair`` passes ``pair.accept`` and there is no other production call site.

    **A refusal means pydantic's ``ValidationError`` and nothing else**, and that is
    measured rather than chosen: over 838 graded pairs, 0 refused this payload with
    any other exception, so admitting a foreign exception as a refusal would cost
    nothing today and would hide the one thing it could ever hide -- an entry point
    raising something the caller cannot catch, which is how the specification's own
    probe came to read a pair nothing graded as green.  So a foreign exception is
    ``model_error`` with its type in ``detail``, which is a verdict and not a pass.
    """
    res = LivenessResult()
    cls = validator_cls or validator_for(schema)
    found = refusing_payload(schema, instance, validator_cls=cls)
    if found is None:
        res.outcome = "no_payload"
        return res
    payload, how = found
    res.how = how
    res.payload = _dump(payload)
    res.violated = tuple(violated_keywords(schema, payload, validator_cls=cls))
    try:
        accept(payload)
    except ValidationError:
        res.outcome = "pass"
    except Exception as e:  # not a refusal this caller could catch
        res.outcome = "model_error"
        res.detail = f"{type(e).__name__}: {e}"[:300]
    else:
        res.outcome = "schema_half_not_connected"
    return res


def check_accepts(
    schema: dict,
    accept: Callable[[Any], Any],
    *,
    examples: int = 25,
    custom_formats: Mapping[str, Any] = (),
    dump: Callable[[Any], Any] | None = None,
    seen: list[Any] | None = None,
    ref: SchemaRef | None = None,
) -> AcceptsResult:
    """The accepts check: every instance the schema admits, ``accept`` admits --
    and what it constructed, DUMPED back out, is an instance the schema admits too.

    This is where a model NARROWER than its document fails, and the annotations
    are load-bearing here even behind a schema check: the schema half passes an
    instance it admits, and then the constructor runs on it.  A ``maxLength``
    the annotation invented, or a required field the model does not declare, is
    refused at construction and reported.

    **The dump is the half that reads what the class DID with the value**, and the
    accepts check alone cannot: a class that takes an instance and loses a key, or
    renames one, or coerces it to a shape the document refuses, accepts every
    instance there is.  So the constructed value goes back out through ``dump`` and
    the DOCUMENT decides again, which costs one validation and no draw.  ``dump``
    defaults to the pydantic reading of "what this value looks like on the wire" --
    ``mode="json"``, by alias, and only the fields the payload actually set, because
    a field the instance never carried is not a fact the document stated about it.

    A pair whose ``dump`` raises is a ``model_error`` like any other construction
    failure; a dump the document refuses is ``model_dropped_a_fact``, named for what
    it is rather than for the check that caught it.

    **``ref`` names the node, and it buys exactly one thing: the dump is validated
    against the document with ``codegen.dump_exemptions``' struck keywords removed.**
    Four positions state a keyword no correct class can satisfy -- a ``pattern`` that
    forbids what RFC 3986 normalization produces, and a ``minProperties`` over keys
    D8 drops -- and D5 and D8 both stay as written, so the positions are exempt and
    the defect is upstream (``adcontextprotocol/adcp#8398``).

    **THE STRIKE TOUCHES THIS VALIDATION AND NOTHING ELSE, and that is what keeps it
    from being a relaxation of the accepts half.** The instance is DRAWN from
    ``schema`` and the constructor still runs on it, so a model narrower than its
    document still fails here exactly as before; a keyword struck for the dump is
    still in force for every instance going IN. Without a ``ref`` nothing is struck,
    which loses an exemption and cannot invent one.

    **``Phase.shrink`` is NOT in the phase list, and that is a measured decision
    rather than an omission.**  Hypothesis caps a shrink at its own
    ``MAX_SHRINKING_SECONDS``, 300 s, so each FAILING pair could cost five minutes
    of a worker's wall clock -- measured here: one failing pair held a core at 99%
    for over ten minutes across two of its checks, against 0.1-0.4 s for a passing
    one.  What a shrink buys is a smaller counterexample, and at the default
    ``examples=1`` there is exactly ONE generated instance, so shrinking it cannot
    reach a different failure -- it can only simplify the one already reported in
    ``counterexample``.  ``Phase.target`` is out with it because no call site
    supplies a ``target()``, so it had nothing to steer.
    """
    res = AcceptsResult()
    cf = dict(custom_formats)
    #: The instances this check drew, in order, HANDED BACK to the caller when it
    #: supplies a list.  ``check_pair`` reads the first one and derives the refused
    #: payload from it, which is what keeps the liveness check from costing a second
    #: draw -- the one saving in this module that is a reuse rather than a deletion.
    seen = [] if seen is None else seen
    validator_cls = validator_for(schema)
    #: The schema the DUMP answers to: the node with the exempt keywords struck, or
    #: the node itself.  Computed once per call rather than per instance, and by
    #: IDENTITY when nothing is exempt, so the pairs with no entry are untouched.
    dump_schema = (
        schema if ref is None else dump_exemptions.struck(schema, ref.document, ref.pointer)
    )
    dump_validator_cls = validator_cls if dump_schema is schema else validator_for(dump_schema)

    def body(instance: Any) -> None:
        res.examples += 1
        seen.append(instance)
        built = accept(instance)
        back = dump(built) if dump is not None else _wire_dump(built)
        if dump_schema is not schema and conforms(schema, back, validator_cls=validator_cls) is (
            False
        ):
            # The strike MATTERED for this instance: the unstruck node refuses this
            # dump and the struck one is about to be asked.  Recorded here rather than
            # once per call, so the field says what this pair needed and not what lies
            # inside it -- see ``AcceptsResult.dump_exempt``.
            assert ref is not None  # dump_schema differs only when a ref was supplied
            res.dump_exempt = dump_exemptions.labels(ref.document, ref.pointer)
        if conforms(dump_schema, back, validator_cls=dump_validator_cls) is False:
            # The CAUSE goes first, because ``detail`` is truncated and a reason at
            # the end of a megabyte of dumped instance is a reason nothing can read.
            broke = violated_keywords(dump_schema, back, validator_cls=dump_validator_cls)
            raise _DumpRefused(
                f"the document refuses the dump on {', '.join(broke)}"
                f"; dumped {_dump(back)} from {_dump(instance)}"
            )
        res.round_tripped += 1

    try:
        with canonicalisation_shared_within_one_call():
            run = given(instance=strategy(schema, cf))(body)
            run = settings(
                max_examples=examples,
                phases=[Phase.explicit, Phase.generate],
                **_SETTINGS,
            )(run)
            run()
        res.outcome = "pass"
    except _DumpRefused as e:
        res.outcome = "model_dropped_a_fact"
        res.detail = str(e)[:400]
        res.counterexample = _dump(seen[-1]) if seen else ""
    except ValidationError as e:
        err = e.errors()[0]
        res.outcome = "model_refused_valid"
        res.detail = f"{err['type']} at {err['loc']}: {err['msg']}"
        res.counterexample = _dump(seen[-1]) if seen else ""
    except (HypothesisRefResolutionError, HypothesisException, RecursionError) as e:
        res.outcome = "strategy_error"
        #: ``_why`` and not the raw message: hypothesis's advice to whoever wrote the
        #: test was pushing the filtered-draw count past the truncation, and the cut
        #: belongs HERE rather than in the reader -- :attr:`PairReport.no_instrument`
        #: re-split the same sentence for want of this line, which is one rule in two
        #: places and the one that goes stale.
        res.detail = _why(e)
    except Exception as e:  # a model that raises something other than ValidationError
        res.outcome = "model_error"
        res.detail = f"{type(e).__name__}: {e}"[:400]
        res.counterexample = _dump(seen[-1]) if seen else ""
    return res


# --------------------------------------------------------------------------- #
# section 8's accepts OBLIGATION: a widening is PROVED, not believed
# --------------------------------------------------------------------------- #
#: **Every shape the format's own checker admits**, for the three formats section 5's
#: ``format`` row lets SELECT A PYTHON TYPE -- and those are the three a narrowing can
#: come from, because a selected type brings its own constraints with it where a format
#: riding as ``json_schema_extra`` brings none.  ``codegen.lower.scalars.FORMAT_TYPES`` is
#: the declaration of which three; this is the shapes, and the two are asserted against
#: each other in ``tests/test_approximation.py`` so a fourth selected format arrives here
#: with its shapes or reddens.
#:
#: Section 8: "for a ``format`` every shape the format's own checker admits rather than the
#: shape a generator finds most likely".  A generator finds the LIKELY shape, which for
#: ``uri`` is a short ``http://`` and for ``date-time`` is a UTC ``Z`` -- so a draw alone
#: is green against a type that refuses every other admissible shape, which is exactly the
#: defect ``URL_IMPLIED``'s two rows record on the other side.
#:
#: Each value is admitted by RFC 3986 / RFC 3339 as the draft's own checker reads it, and
#: ``tests/test_approximation.py`` asserts that of every one of them against the checker
#: rather than taking this comment's word for it.
FORMAT_SHAPES: Mapping[str, tuple[tuple[str, Any], ...]] = {
    "uri": (
        ("an https URL", "https://example.com/a"),
        ("a plain http URL", "http://example.com/a"),
        ("a URN", "urn:ietf:rfc:3986"),
        ("a file URL", "file:///tmp/a"),
        ("a mailto URI", "mailto:a@example.com"),
        # 2,220 characters, which is what row .10's live narrowing is measured on: the
        # document states no length and ``HttpUrl`` renders ``maxLength: 2083``.
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
}

#: The keywords whose classes are enumerated from the node, each with how.  A keyword NOT
#: here has no derivation and :func:`value_classes` says so rather than passing -- the
#: vacuous-pass rule this module applies to ``FormatStrategyVerdict.unchecked`` and to
#: ``PairReport.no_instrument`` alike: a check that cannot reach its subject reports that,
#: it does not report a pass.
#:
#: Section 8 names three families and all three are here: "every member of an ``enum``,
#: both sides of each bound and the bound itself, and for a ``format`` every shape the
#: format's own checker admits".  A ``const`` is a one-member ``enum``; a ``pattern``, a
#: ``type`` and the structural keywords have one class, which is the node as it stands.
_BOUNDS: Mapping[str, tuple[str, str]] = {
    # keyword -> (the keyword that pins the LOW end, the keyword that pins the HIGH end)
    "minLength": ("minLength", "maxLength"),
    "maxLength": ("minLength", "maxLength"),
    "minItems": ("minItems", "maxItems"),
    "maxItems": ("minItems", "maxItems"),
    "minProperties": ("minProperties", "maxProperties"),
    "maxProperties": ("minProperties", "maxProperties"),
    "minimum": ("minimum", "maximum"),
    "maximum": ("minimum", "maximum"),
}


def _restricted(node: Mapping[str, Any], **pins: Any) -> dict:
    """``node`` with the keywords in ``pins`` replaced -- a RESTRICTION of it.

    Every value class is a sub-schema of the node and the class's value is a draw from
    that sub-schema, which is what makes "a value the document admits" true by
    construction rather than by assertion: a restriction admits a subset of what the node
    admits.  :func:`check_widening` validates each drawn value against the node anyway,
    because "by construction" is a claim about this function and the claim is cheap to
    check.
    """
    return {**node, **pins}


def value_classes(keyword: str, node: Mapping[str, Any]) -> tuple[tuple[str, dict], ...]:
    """**The classes ``keyword`` distinguishes at ``node``**, as labelled sub-schemas.

    Section 8: "The draw COVERS the node's admissible space by constraint class; it does
    not sample it.  'Never tighter' is a claim about every value the document admits, and a
    sampling draw reports only the values it drew -- so it can run green forever against a
    type that refuses a whole class of admissible value."

    Empty means NO DERIVATION, which :func:`check_widening` reports as
    ``no_value_classes`` and never as a pass.  A keyword whose classes cannot be
    enumerated is a widening nothing proves, and section 9's rule about a check that
    cannot reach its subject applies: "A check is exhaustive over the set of nodes it
    claims, or it does not exist."
    """
    if keyword == "enum" and isinstance(node.get("enum"), list):
        return tuple(
            (f"enum member {member!r}", _restricted(node, enum=[member]))
            for member in node["enum"]
        )
    if keyword == "const":
        return (("the pinned const", dict(node)),)
    if keyword == "type":
        words = node["type"] if isinstance(node.get("type"), list) else [node.get("type")]
        return tuple((f"type {w!r}", _restricted(node, type=w)) for w in words if w)
    if keyword == "format" and node.get("format") in FORMAT_SHAPES:
        return tuple(
            (f"{label} ({node['format']})", _restricted(node, const=value))
            for label, value in FORMAT_SHAPES[node["format"]]
        )
    if keyword in _BOUNDS and isinstance(node.get(keyword), (int, float)):
        low, high = _BOUNDS[keyword]
        bound = node[keyword]
        inside = bound + 1 if keyword.startswith("min") else bound - 1
        floor, ceiling = node.get(low), node.get(high)
        out = [(f"{keyword} exactly ({bound})", _restricted(node, **{low: bound, high: bound}))]
        # **Both sides and the bound itself**, less the side the node's OTHER bound
        # forbids: a ``minLength: 1, maxLength: 1`` node admits exactly one length, and a
        # class for length 2 would be a value the DOCUMENT refuses -- which section 8 says
        # nothing about, because the schema half refuses it first.
        if (floor is None or inside >= floor) and (ceiling is None or inside <= ceiling):
            out.append(
                (f"{keyword} one step inside ({inside})", _restricted(node, **{low: inside, high: inside}))
            )
        return tuple(out)
    if keyword == "uniqueItems" and node.get("uniqueItems") is True:
        # What the keyword DISTINGUISHES is a list of two or more members, since a list of
        # one cannot repeat: so the class is the shortest list the document admits that has
        # a duplicate to forbid, and the length is PINNED rather than floored -- an
        # unpinned draw may take any length above it, and a class whose value varies run to
        # run is a class that reports a narrowing it did not reach.
        least = max(2, node.get("minItems") or 0)
        ceiling = node.get("maxItems")
        if ceiling is not None and ceiling < least:
            return ()  # the document admits no list long enough to repeat
        return (
            (
                f"{least} distinct members",
                _restricted(node, minItems=least, maxItems=least),
            ),
        )
    if keyword in ("pattern", "multipleOf", "exclusiveMinimum", "exclusiveMaximum"):
        # One class: the node as it stands, drawn with the keyword in force.  A second
        # class would need a value one step from the bound, and for a ``pattern`` or a
        # float bound there is no step this module can name.
        return ((f"a value the {keyword} admits", dict(node)),)
    if keyword == "properties" and isinstance(node.get("properties"), dict):
        return tuple(
            (f"the property {key!r} present", _restricted(node, required=[key]))
            for key in sorted(node["properties"])
        )
    if keyword == "required" and isinstance(node.get("required"), list):
        return (("every required name present", dict(node)),)
    if keyword in ("additionalProperties", "patternProperties", "propertyNames"):
        return ((f"a key the {keyword} admits", _restricted(node, minProperties=1)),)
    if keyword in ("items", "contains"):
        return ((f"a list the {keyword} admits", _restricted(node, minItems=1)),)
    if keyword in ("allOf", "oneOf", "anyOf", "not", "if", "then", "else", "dependencies", "$ref"):
        return ((f"a value the {keyword} admits", dict(node)),)
    return ()


def instance_path(pointer: str) -> tuple[Any, ...] | None:
    """The INSTANCE location a schema pointer describes, or ``None`` where it has none.

    ``#/properties/x`` describes the value under the key ``x``; ``#/items`` describes
    every element, so index 0 stands for it; a same-instance hop -- ``#/allOf/0``,
    ``#/oneOf/1``, ``#/then`` -- describes the SAME instance and contributes no segment,
    which is ``adcp.types._base.SAME_INSTANCE_LIST``'s own rule read the other way.

    ``None`` for a pointer whose segments describe no instance location at all -- a
    ``#/definitions/x`` reached only through a ``$ref``, an ``#/if``, a
    ``#/propertyNames`` -- and :func:`check_widening` reports that as
    ``no_instance_path`` rather than placing a value somewhere the document does not mean.
    """
    segments = [s for s in pointer.lstrip("#").split("/") if s]
    out: list[Any] = []
    i = 0
    while i < len(segments):
        word = segments[i]
        if word == "properties" and i + 1 < len(segments):
            out.append(bundle.unescape_key(segments[i + 1]))
            i += 2
        elif word == "items":
            out.append(0)
            i += 1
        elif word in ("allOf", "anyOf", "oneOf") and i + 1 < len(segments):
            i += 2  # a same-instance hop through a list: no segment
        elif word in ("then", "else"):
            i += 1  # a same-instance hop
        else:
            return None
    return tuple(out)


def _placed(instance: Any, path: Sequence[Any], value: Any) -> Any:
    """``instance`` with ``value`` at ``path``, as a copy.

    A path segment the instance does not carry is CREATED, because a widened fact can sit
    at an optional property the drawn instance happened to omit: the point of the draw is
    the value at the pointer, so an instance without it says nothing.
    """
    if not path:
        return value
    out = copy.deepcopy(instance)
    cursor = out
    for segment in path[:-1]:
        if isinstance(segment, int):
            if not isinstance(cursor, list) or len(cursor) <= segment:
                return None
            cursor = cursor[segment]
        else:
            if not isinstance(cursor, dict):
                return None
            cursor = cursor.setdefault(segment, {})
    last = path[-1]
    if isinstance(last, int):
        if not isinstance(cursor, list):
            return None
        while len(cursor) <= last:
            cursor.append(value)
        cursor[last] = value
    else:
        if not isinstance(cursor, dict):
            return None
        cursor[last] = value
    return out


@dataclass
class WideningResult:
    """Whether each declared approximation really WIDENS, by value and by pointer.

    Section 8: "An approximation is a claim about this check, and this check is what
    proves it ... An approximation that still refuses a value the document admits is a
    NARROWING wearing a declaration, and it fails here, by value and by pointer.  This is
    what keeps 'approximated' from being an allowlist."

    ``unproved`` is as much a failure as ``narrowings``, and that is the decision rather
    than an omission: a declaration whose classes this module cannot enumerate, or whose
    pointer describes no instance location, is a widening nobody has proved -- and section
    9's "a check is exhaustive over the set of nodes it claims, or it does not exist" says
    what to do with it.
    """

    #: How many declarations were put to the check.
    declarations: int = 0
    #: How many drawn values reached the entry point and were accepted.
    accepted: int = 0
    #: A value the DOCUMENT admits and the class REFUSES, by pointer and by value.
    narrowings: list[str] = field(default_factory=list)
    #: A declaration this check could not reach, with the reason.
    unproved: list[str] = field(default_factory=list)
    detail: str = ""

    @property
    def outcome(self) -> str:
        if self.detail:
            return "error"
        if self.narrowings:
            return "narrowing_wearing_a_declaration"
        if self.unproved:
            return "unproved_widening"
        if not self.declarations:
            return "no_declarations"  # nothing was claimed, so nothing is owed
        return "pass"


def check_widening(
    schema: dict,
    accept: Callable[[Any], Any],
    declared: Sequence[Approximation],
    *,
    at: str = "#",
    instance: Any = None,
    custom_formats: Mapping[str, Any] = (),
) -> WideningResult:
    """Section 8's accepts OBLIGATION, one declaration at a time.

    ``instance`` is a payload the accepts check already drew for this pair, which is what
    keeps this from costing a second whole-document draw: the obligation is about the value
    at ONE pointer, so the rest of the payload is any payload the document admits.  With
    none supplied the obligation can still run for a declaration at the pair's own root,
    where the drawn class value IS the whole instance.

    Each class is a RESTRICTION of the document's own node (:func:`value_classes`), so a
    value drawn from it is a value the document admits -- asserted against the node anyway,
    because a restriction is a claim about :func:`_restricted` and checking it is cheap.
    The value is then placed at the pointer's instance location and offered to the entry
    point.  A ``ValidationError`` there is the one thing section 2 says must never happen:
    "An annotation tighter than its document refuses a payload the protocol permits, and
    ``strict_validate`` cannot repair it."
    """
    res = WideningResult()
    cf = dict(custom_formats)
    validator_cls = validator_for(schema)
    for one in declared:
        res.declarations += 1
        if one.kind == UNDERDETERMINED:
            # Section 2: "No comparison, draw or dump can see one, which is precisely why
            # it is declared and why its instrument is different (section 8)."  Its check
            # is the disjointness equality (:func:`underdetermined_census`) and claiming
            # it here would report a pass this check cannot earn.
            res.declarations -= 1
            continue
        relative = "" if one.pointer == at else one.pointer[len(at.rstrip("/")) :]
        node = at_or_none(schema, relative)
        if not isinstance(node, dict) or one.keyword not in node:
            res.unproved.append(
                f"{one.pointer}/{one.keyword}: the document states no such keyword at "
                "that pointer, so there is no fact to prove dropped (section 9: never "
                "approximate on a keyword the walk itself inserted)"
            )
            continue
        path = instance_path(relative)
        if path is None:
            res.unproved.append(
                f"{one.pointer}/{one.keyword}: the pointer describes no instance "
                "location, so no drawn value can be placed at it"
            )
            continue
        classes = value_classes(one.keyword, node)
        if not classes:
            res.unproved.append(
                f"{one.pointer}/{one.keyword}: no value class is derivable for this "
                "keyword, so the widening is declared and unproved"
            )
            continue
        for label, restriction in classes:
            try:
                value = one_instance(restriction, cf)
            except Exception as e:  # noqa: BLE001 -- any draw failure is unproved, not a pass
                res.unproved.append(
                    f"{one.pointer}/{one.keyword}: {label} could not be drawn: {_why(e)}"
                )
                continue
            if conforms(node, value, validator_cls=validator_for(node)) is False:
                res.unproved.append(
                    f"{one.pointer}/{one.keyword}: {label} drew {_dump(value)}, which the "
                    "document's own node refuses -- the restriction is not one"
                )
                continue
            payload = _placed(instance, path, value)
            if payload is None:
                res.unproved.append(
                    f"{one.pointer}/{one.keyword}: {label} has nowhere to go in the drawn "
                    f"instance at {list(path)}"
                )
                continue
            if conforms(schema, payload, validator_cls=validator_cls) is False:
                res.unproved.append(
                    f"{one.pointer}/{one.keyword}: {label} placed at {list(path)} makes a "
                    "payload the document refuses, so it says nothing about the class"
                )
                continue
            try:
                accept(payload)
            except ValidationError as e:
                err = e.errors()[0]
                res.narrowings.append(
                    f"{one.pointer}/{one.keyword}: {label} -- the document admits "
                    f"{_dump(value)} and the class refuses it "
                    f"({err['type']} at {err['loc']}: {err['msg']}); declared "
                    f"approximated at rung {one.rung}, {one.attribution}"
                )
                continue
            except Exception as e:  # noqa: BLE001
                res.unproved.append(
                    f"{one.pointer}/{one.keyword}: {label} raised "
                    f"{type(e).__name__}: {e}"[:300]
                )
                continue
            res.accepted += 1
    return res


def at_or_none(doc: Any, pointer: str) -> Any:
    """:func:`at`, answering ``None`` for a pointer the document does not hold."""
    try:
        return at(doc, pointer)
    except Exception:  # noqa: BLE001 -- a pointer the document does not hold
        return None


def one_instance(schema: Mapping[str, Any], custom_formats: Mapping[str, Any]) -> Any:
    """ONE value the schema admits.

    ``hypothesis``'s ``example()`` is not available outside a test, so this runs the same
    ``given`` machinery :func:`check_accepts` runs, with one example, and keeps the first
    value.  ``derandomize`` is on in :data:`_SETTINGS`, so the value is the same on every
    run -- which is what makes a narrowing this check reports reproducible from the report.
    """
    drawn: list[Any] = []

    def body(instance: Any) -> None:
        drawn.append(instance)

    with canonicalisation_shared_within_one_call():
        run = given(instance=strategy(dict(schema), dict(custom_formats)))(body)
        settings(max_examples=1, phases=[Phase.explicit, Phase.generate], **_SETTINGS)(run)()
    if not drawn:
        raise HypothesisException("the strategy produced no instance")
    return drawn[0]


def _why(e: BaseException) -> str:
    """``hypothesis``'s own reason, up to the point where it starts advising.

    ``Unsatisfiable``'s message is the reason followed by advice -- *"Try making your
    filters or assumes less strict, or rewrite using strategy parameters..."* -- and
    the advice is for whoever wrote the test, not a fact about the document.  The
    reason half carries the number this report needs (*"459 of 459 test cases failed
    a .filter() or assume() condition"*), so the cut keeps the measurement and drops
    the boilerplate that was pushing it past the truncation.
    """
    return f"{type(e).__name__}: {str(e).split(' Try making')[0].strip()}"[:200]


def _dump(x: Any) -> str:
    try:
        return json.dumps(x, default=str)[:600]
    except Exception:
        return repr(x)[:600]


# --------------------------------------------------------------------------- #
# the schema comparison: the model's own schema against the document
# --------------------------------------------------------------------------- #
#: What a document can STATE about a value, and therefore what the model has to state
#: too -- **DERIVED from ``codegen.keywords``, never written here.**
#:
#: Section 8 of the semantics document: "the comparison derives its compared set from
#: the same declaration: every keyword it renders as a fact.  A hand-written list beside
#: the comparison is the one way this check can be complete with respect to itself and
#: blind to everything beyond it: a keyword missing from it is unexamined in BOTH
#: directions, so the grader cannot tell whether we rendered it, dropped it, or invented
#: it -- and it reports a pass either way."  So one check stands above the three: the
#: comparison's keyword set EQUALS the set the declaration renders, and this function is
#: that equality rather than an assertion about it.
#:
#: The POSITION is a parameter because ``rendered`` is per cell: ``deprecated`` is a
#: field fact at PROP and at a class root and nothing at an element, and a list written
#: here could not say so.  Each caller passes the position it is reading at, which is a
#: structural fact of the caller -- a property's value is at PROP, an array's element at
#: ELEM, a mapping's value at MAPV, a key schema at KEY -- and never recovered from the
#: pointer string.
#:
#: ``title`` is absent, and it is the table that says so: §6's row ends "Never
#: rendered."  pydantic derives one for every class and every property and the documents
#: carry one only at a root, so it is a name the compiler makes up rather than a fact to
#: compare.
def compared_facts(position: Position) -> tuple[str, ...]:
    """The keywords a faithful model RENDERS at ``position``, read off the table.

    A TUPLE in the table's own declaration order, and that is not decoration: the
    comparison reports one line per fact and a reader of two reports compares them, so
    the order facts are reported in has to be a function of the DECLARATION rather than
    of a set's hash.  The set is ``keywords.rendered_at``; this is that set, ordered by
    the document the grids are generated into.
    """
    rendered = keywords.rendered_at(position)
    return tuple(k for k in keywords.TABLE if k in rendered)


#: The facts the document-side FOLDS range over: a composed conjunct's and a union
#: branch agreement's.  The same derivation at the position those readings are taken at
#: -- a conjunct applies to the same instance as the node it composes, and a branch of a
#: root union is read under the root's own siblings, so both are the node's own position
#: and ROOT is the one every pair is entered at.
FOLDED_FACTS = compared_facts(Position.ROOT)


# --------------------------------------------------------------------------- #
# section 7's declaration, read off the artifact as a CONSUMER reads it
# --------------------------------------------------------------------------- #
#: A site: the document, the pointer, and the keyword whose fact is dropped.  The key both
#: section 8 set equalities range over, and the key ``codegen.attribution``'s registry is
#: already keyed by -- one spelling of an approximation's ADDRESS, so neither equality has
#: to reconcile two.
Site = tuple[str, str, str]


def site_of(declared: Approximation) -> Site:
    return (declared.document, declared.pointer, declared.keyword)


def declarations_of(subject: Any) -> tuple[Approximation, ...]:
    """Section 7's ``__adcp_approximations__``, off a class or off a module.

    Section 9 forbids the verifier the walk, so this is the whole of how a declaration
    reaches the grader: "``render.py`` writes ``__adcp_approximations__`` onto the class,
    the root model or the enumeration, and beside the module for an alias ... and
    ``verify/`` reads it as a consumer reads any other class attribute."  ONE function for
    both, because ``vars()`` answers for a class and for a module alike.

    **``vars`` and not ``getattr``, so an INHERITED declaration is not read as this
    class's own.**  A union branch subclasses its base, and the base is at ``#`` and so
    declares everything in the document (``render.declared_at``'s containment rule); read
    through ``getattr`` a branch would claim its base's declarations and the equality would
    pass over a widening nothing at that branch widened.  ``graded()`` already draws the
    same line for ``__adcp_schema__`` and for the same reason.
    """
    found = vars(subject).get(APPROXIMATIONS, ())
    return tuple(found)


def declared_facts(declared: Sequence[Approximation], base: str) -> dict[tuple[str, str], Approximation]:
    """``declared`` keyed by the PAIR-RELATIVE pointer and the keyword.

    ``base`` is the pair's own pointer, as ``__adcp_schema__`` spells it, and the
    comparison reports a pointer relative to the node it entered at -- ``""`` at the pair's
    own node, ``/properties/x`` one level in.  So the two meet by subtracting ``base``,
    which is one string operation on one spelling and not a reconciliation of two
    (``compiler.schema_ref`` is the sole producer of the spelling).

    A declaration at a pointer OUTSIDE this pair's node is dropped here: it belongs to
    another pair, and the run-level equality (:func:`census`) is where every declaration
    has to be accounted for.
    """
    out: dict[tuple[str, str], Approximation] = {}
    for one in declared:
        if one.pointer == base:
            out[("", one.keyword)] = one
        elif one.pointer.startswith(base.rstrip("/") + "/"):
            out[(one.pointer[len(base.rstrip("/")) :], one.keyword)] = one
    return out


@dataclass
class ComparisonResult:
    """The schema comparison's verdict for one pair."""

    compared: int = 0  # facts the document states that were looked for
    model_facts: int = 0  # facts the model states that the document does not
    missing: list[str] = field(default_factory=list)  # the model states nothing
    differs: list[str] = field(default_factory=list)  # the model states something else
    added: list[str] = field(default_factory=list)  # the document states nothing
    #: **Section 8's fifth outcome**: "the document states the fact, the model does not,
    #: and an approximation at that pointer and keyword declares it, names its rung and
    #: carries an attribution.  Not a defect.  Counted, listed, and proved wide by the
    #: accepts draw."  So a pair with entries here still PASSES, the way a pair with a
    #: ``dump_exempt`` entry does, and the report prints the figure.
    approximated: list[str] = field(default_factory=list)
    #: The same facts as :attr:`approximated`, as SITES rather than as sentences -- the
    #: set the run-level equality ranges over (:func:`census`).  Two fields for one fact,
    #: deliberately: every other bucket here is a list of sentences because the report
    #: prints one line per entry, and a set equality cannot be computed over a sentence
    #: without parsing it back out, which is the reading section 3 of the architecture
    #: document refuses for the same reason.
    approximated_at: list[Site] = field(default_factory=list)
    #: **Section 8's sixth outcome**: "an approximation is declared at a pointer and
    #: keyword where the model DOES state the fact.  A defect, and the mirror of
    #: *missing*.  Without it the declarations rot: a cell gets written, the widening stops
    #: happening, the declaration stays, and it then hides the next real gap at the same
    #: pointer behind a stale excuse."  Pinned at zero.
    over_declared: list[str] = field(default_factory=list)
    #: D5's URL-type row, which is a CATEGORY OF ITS OWN and weaker than every
    #: other admission here -- see :func:`_url_typed`.  Counted separately and
    #: never folded into ``missing`` or into the implied-fact rows, so a reader can
    #: see how many facts this row excuses and at which positions.
    url_typed: list[str] = field(default_factory=list)
    #: A DOCUMENT fact that constrains nothing, so the model omitting it is not a
    #: drop -- see :func:`_constrains_nothing`.  Counted separately for the same reason
    #: ``url_typed`` is: a fold that disappears into a green ``missing`` is
    #: invisible and permanent, and this one must stay auditable at its positions.
    constrains_nothing: list[str] = field(default_factory=list)
    #: A ``propertyNames`` the model TYPES and pydantic does not render, at a
    #: ``__pydantic_extra__`` store -- see :func:`_extra_key_typed`.  Counted apart
    #: from ``missing`` for the reason the two lists above are: an admission that
    #: disappears into a green ``missing`` is invisible and permanent, and this one
    #: must stay auditable at its positions.
    extra_key_typed: list[str] = field(default_factory=list)
    detail: str = ""

    @property
    def outcome(self) -> str:
        if self.detail:
            return "harness_error"
        if self.missing or self.differs:
            return "model_drops_a_fact"
        if self.added:
            return "model_adds_a_fact"
        # Section 8's sixth outcome is a DEFECT and ranks with the other three: a
        # declaration that outlives its widening hides the next real gap at the same
        # pointer.  Below ``added`` because it is a fact about the DECLARATION where the
        # three above are facts about the model, so a reader of a red pair meets the
        # model's own disagreement first.  ``approximated`` is NOT here: section 8 says
        # "Not a defect", so a pair carrying one passes and the figure is reported.
        if self.over_declared:
            return "declaration_outlived_its_widening"
        if not self.compared:
            return "no_evidence"  # the document states nothing; nothing was graded
        return "pass"


def _text(x: Any) -> Any:
    """A description compared by its words, not by its line breaks."""
    return " ".join(x.split()) if isinstance(x, str) else x


#: The JSON type name of a Python value, by its EXACT type, so ``True`` is ``"boolean"``
#: and not ``"integer"``.
_JSON_TYPE = {
    str: "string",
    bool: "boolean",
    int: "integer",
    float: "number",
    type(None): "null",
    dict: "object",
    list: "array",
}


def _entails_type(doc: dict, value: Any) -> bool:
    """Does the document's own node already admit ONLY instances of ``value``?

    Asked of the node, not answered from a list of excused sites, and it answers ``False``
    for a node that says nothing -- so a model that invents a type is still reported.
    Three derivations, because three shapes in this bundle constrain an instance's type
    without naming it, and every one of them is a fact of the DOCUMENT read against a
    rendering THIS PIPELINE chose:

    * a ``const``.  ``{"const": "platform"}`` admits exactly the string ``"platform"``, so
      ``type: string`` beside it forbids nothing the node already admits.  pydantic renders
      a ``Literal`` as ``{"const": ..., "type": ...}`` and there is no spelling of a
      literal that omits the type.  **832 nodes of the raw bundle, in 186 documents,
      state a ``const`` with no ``type``**, so the shape is the document's own and not a
      view of it.
    * an ``enum`` whose members are all of ONE JSON type.  The vocabulary pins the
      accepted set, so the type word beside it forbids nothing -- the same statement the
      ``const`` arm makes about a one-member set, which is why the two are one function
      and not two.  §4's enumeration row renders a ``StrEnum``, and pydantic writes
      ``{"enum": [...], "type": "string"}`` for one; **164 nodes of the raw bundle, in 79
      documents, state the ``enum`` and no ``type``**.  Gated on ONE implied type, so a
      model claiming ``integer`` over a string enum, or any type at all over a mixed
      vocabulary, is still reported.
    * a ``oneOf``/``anyOf`` whose EVERY branch declares the same ``type``.  Draft-07
      requires an instance to satisfy a branch, so a root that states no ``type`` of its
      own and whose branches all state ``object`` admits only objects.  §4's union base is
      a pydantic model and so renders ``type: object``; **34 of this bundle's union roots
      state the branches' type and not their own**, 33 of them with the branches read as
      written and the 34th only once a branch's local reference is.

      **The branch is asked for its own ``type`` word and a branch that is a bare local
      ``$ref`` has none**, which is why :func:`_normalize` resolves one before this arm
      reads it (:func:`_branch_target`).  Nothing here resolves anything: this arm reads
      the branches it is handed, and :func:`_normalize` is where the two sides' spellings
      are read, so the reading is applied once and to both.  Measured over the graded
      population, the arm decides a model-only ``type`` at **221 pairs** with the branch
      read through its reference and at **220** without -- the one pair is
      ``core/requirements/catalog-field-binding.json#``, whose root states no ``type``
      and whose three branches each state ``object``, two of them through
      ``#/definitions/ScalarBinding`` and ``#/definitions/AssetPoolBinding``.

    **The ``enum`` arm MOVED HERE from ``_narrows_nothing``'s enum row and is not a fold
    added.**  That row admitted a model-only ``type``, ``description`` and ``default`` at
    an enum node on the ground that ``canonicalish`` had dropped all four while inlining
    -- the delegated resolver's rewriting, which §9 deletes.  The ``description`` and the
    ``default`` go with it, because ``bundle.record`` keeps the document's own.  The
    ``type`` half has a second and independent source that the record does not touch, and
    the measurement above is it: a document that states no type beside its enum.  So the
    arm stays and belongs with the question it is actually asking.

    **This is not a tolerance for "the model states more".**  It is the question
    :func:`_narrows_nothing` already exists to ask -- whether the accepted set moved -- and
    it is decided from the document.  ``tests/test_emit.py`` asserts, at every site the
    rule excuses, that the document really does refuse an instance of every other type,
    and that a typeless node with no such derivation is still reported.
    """
    if "const" in doc:
        return _JSON_TYPE.get(type(doc["const"])) == value
    members = doc.get("enum")
    if isinstance(members, list) and members:
        # ``_JSON_TYPE`` is keyed on the EXACT type, so ``True`` implies ``boolean`` and
        # not ``integer``; a member of any other Python type implies ``None``, which no
        # ``type`` word equals, so a mixed vocabulary never reaches one answer.
        implied = {_JSON_TYPE.get(type(m)) for m in members}
        return len(implied) == 1 and value in implied
    for combinator in ("oneOf", "anyOf"):
        branches = doc.get(combinator)
        if isinstance(branches, list) and branches:
            return all(isinstance(b, dict) and b.get("type") == value for b in branches)
    return False


#: The two facts a pydantic URL type renders OF ITS OWN, each with the exact value
#: it renders, and each admitted by its own hand-written row below.  Written as
#: ``keyword -> value`` and compared for equality, so the rows admit THESE TWO
#: FACTS and not "a bound on a URL type": a rule that admitted any added bound
#: would be invisible and permanent, which is what D5 forbids of a hand-written
#: row.  Measured on pydantic 2.13.5 -- ``AnyUrl`` renders the first, ``HttpUrl``
#: renders both, and no document in the bundle states either at a ``uri`` node.
URL_IMPLIED = {"minLength": 1, "maxLength": 2083}


def _url_typed(got: Mapping[str, Any]) -> bool:
    """Is the MODEL's node at this position a pydantic URL type?

    Read off the model's own rendered schema and not off what the emitter
    intended, because the comparison grades the model.  Every one of pydantic's
    22 URL types renders ``{"type": "string", "format": "uri", "minLength": 1}``
    -- ``HttpUrl`` adds ``maxLength: 2083`` and the rest add nothing -- and an
    ``Annotated[str, ...]`` carrying a ``format`` annotation renders the first two
    and never the ``minLength``, so those three keys are the signature and a plain
    ``str`` cannot wear it by accident.  Measured on pydantic 2.13.5.

    ``minLength`` and not ``maxLength`` is what the signature turns on, because
    D5 selects BOTH arms: ``AdCPUrl`` at the 47 positions whose document restricts
    the scheme to https, ``HttpUrl`` everywhere else, and only one of the two
    renders the ``maxLength``.
    """
    return (
        got.get("type") == "string" and got.get("format") == "uri" and got.get("minLength") == 1
    )


def _constrains_nothing(keyword: str, doc: Mapping[str, Any], *, required: bool = False) -> bool:
    """Does a DOCUMENT fact constrain its accepted set, or not?

    The mirror of :func:`_narrows_nothing`: that one asks whether a MODEL-only fact
    narrows the document, this one asks whether a DOCUMENT-only fact constrains
    anything at all.  A fact that admits exactly what its absence admits is not
    dropped by a model that omits it, so reporting it as ``missing`` says the model is
    wider than its schema when it is not.

    **Two arms, and NEITHER is the delegated resolver's.**  ``docs/plan/architecture.md``
    §9 deletes every fold that undoes a rewriting of that resolver and keeps the
    readings this pipeline's own output forces; these two are the second kind -- one
    reads a keyword the DOCUMENT itself writes, the other grades a decision §5 of the
    semantics document made:

    * **``required: []``** -- an empty list demands no key, which is what silence
      demands.  The document's own keyword, and §5 decides it compiles to nothing, so
      a model that omits it drops nothing.  5 sites.
    * **``default`` on a property the enclosing node REQUIRES** -- a default is
      applied to an instance that OMITS the key, and a required key is in every
      instance the document admits, so the default can never be applied and its
      absence from the model admits and refuses exactly what its presence would.
      Section 5's ``default`` row drops it for that reason (``compiler.fields``,
      which also REPORTS the drop), and this arm is the grading half of the same
      decision, gated on the same shape.  5 of the bundle's 339 property defaults
      sit on a required property.

    **DELETED with the delegated resolver: ``enum: [false, true]`` at a node the
    document declares ``boolean``.**  That arm restored a finite type the resolver had
    written out as its members while inlining, and it had 0 sites in the bundle
    already, because the bundle states no such pair in its own text -- all 5 it ever
    had were a CONJUNCT's ``enum`` the resolver wrote.  ``bundle.record`` writes the
    ``type`` the document writes, so there is no rewriting left to undo and the arm
    would fire only on a document stating the pair itself, where §9's own rule is that
    the fold must not fire: ``enum: [false, true]`` the DOCUMENT states is a fact to
    compare.

    **Each clause is gated to ITS OWN SHAPE and the gates are the whole of this
    function's correctness.**  A fold that matches one real constraint is invisible
    and permanent:

    * ``required: ["x"]`` demands a key and must still compare, so the value is
      required to be empty rather than merely a list.
    * A ``default`` on an OPTIONAL property is the one case where a default does
      something -- the key may be omitted and the value then applies -- so it must
      still compare, and the gate is ``required`` and not the keyword's name.  That
      is also why ``required`` is a parameter here rather than something read off
      ``doc``: requiredness is stated by the ENCLOSING node, which this function is
      not handed, and reading it off the node itself would make every default fold.

    This is NOT the place to excuse a fact that is merely hard to render.  A
    document fact the model cannot express is ``missing``, and that is the report
    the specification wants.
    """
    if keyword == "required":
        return doc.get("required") == []
    return keyword == "default" and required


def _schema_half_enforces(keyword: str, doc: Mapping[str, Any], got: Mapping[str, Any]) -> bool:
    """D5's URL-type row: the schema half enforces this keyword and the annotation
    does not restate it.

    **This is a category of its own and it is WEAKER than every other admission in
    this module, which is why it is not one of them.**  The enum rows admit a fact
    the document's own members IMPLY -- the fact is still true of the model. This
    row admits a fact the model does not state AT ALL, on the ground that
    ``strict_validate`` validates the document before the constructor ever runs,
    so the accepted set of the ENTRY POINT still carries it.  Folding it into
    :func:`_narrows_nothing` would make a genuine omission look like a derivation,
    so it has its own counter (``ComparisonResult.url_typed``) and its own gate.

    D5 makes a ``format: uri`` field's type FOLLOW THE DOCUMENT'S OWN PATTERN --
    ``AdCPUrl`` (``Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]``)
    at the 47 positions whose pattern is ``^https://``, and ``HttpUrl`` everywhere
    else, because ``AdCPUrl`` everywhere refused ``http://``, ``urn:`` and ``file:``
    values the document ADMITS at 228 of the bundle's 300 ``uri`` positions. Either
    way no URL type can carry a ``pattern`` at all, so the document's own pattern
    stays with the schema half. Three facts follow, and this category admits exactly
    those three, each gated and each in its own row:

    * the document's ``pattern`` is not on the annotation. Gated on the keyword
      being ``pattern``, the document stating ``format: uri``, and the model's node
      being a URL type (:func:`_url_typed`). Any other dropped keyword -- a
      ``maxLength``, a ``minLength`` the document states, an ``enum`` -- still lands
      in ``missing``. Measured over the emitted population: 1 of 30 ``format: uri``
      positions states a ``pattern`` (``core/platform-extension-ref.json``'s
      ``/properties/uri``, ``^https://``) and 0 state any other string constraint,
      so a ``maxLength`` falling through this gate costs no document today and
      would redden rather than pass if one appeared.
    * the ``minLength: 1`` every pydantic URL type renders, which no document
      states. Gated on the value being exactly ``1`` at such a node.
    * the ``maxLength: 2083`` ``HttpUrl`` renders, which no document states either.
      Gated on the value being exactly ``2083``.

    **The last two are TWO rows and not one widened one.** :data:`URL_IMPLIED` holds
    the two keyword/value pairs and they are compared for equality, so a model
    stating any OTHER bound on a URL type is still reported. A rule reading "a bound
    on a URL type is admitted" would be shorter and would admit a third bound nobody
    decided, invisibly and for good -- which is the thing D5 says a hand-written row
    must never do. Each of these names itself and can be audited.

    **A note on what these rows do NOT excuse.** ``format: uri`` is RFC 3986, which
    admits every scheme, so ``HttpUrl`` still refuses ``urn:`` and ``file:`` values
    the document admits -- 227 of the bundle's 300 ``uri`` positions stay narrower
    than their document, which is the ceiling D5 accepts after ``AdCPUrl``
    everywhere was measured at 228 and withdrawn. Nothing in this harness grades
    it: ``allowed_schemes`` has no rendering in pydantic's schema output, so there
    is no keyword on either side; ``format`` is not a step keyword, so ``steps()``
    returns ``[]``; and ``hypothesis_jsonschema``'s ``uri`` strategy drew ``https``
    in 200 of 200 derandomized examples. That instrument gap is
    ``salesagent-j3k2l.10``'s. These rows are about the keywords, not about that.
    """
    if not _url_typed(got) or doc.get("format") != "uri":
        return False
    return keyword == "pattern"


def _narrows_nothing(keyword: str, value: Any, doc: dict, *, required: bool = False) -> bool:
    """Does a model-only fact narrow the document's accepted set, or not?

    A fact the model states and the document does not is reported, because that is how
    a model NARROWER than its document shows up.  **Two kinds narrow nothing, and both
    are a reading THIS PIPELINE'S OWN OUTPUT forces** -- which is the half
    ``docs/plan/architecture.md`` §9 keeps when the record is this package's own
    inliner:

    * **``default: null`` AT A KEY THE DOCUMENT DOES NOT DEMAND**, 56 of them.  D4
      renders an optional property ``T | None = None``, because a Python attribute
      holds ``None`` for an omitted key, and pydantic reports that as a default.
      It is how absence is spelled in Python, not a claim about the document:
      presence is the schema's ``required`` axis and that is compared in both
      directions.  A model-only ``default`` with any OTHER value IS an added claim
      and is reported -- the difference between "absent renders as None" and "the
      generator invented a default".

      **``required`` is the axis, and this clause used to read the node's declared
      ``null`` as a proxy for it.**  The proxy was
      ``"null" not in str(doc.get("type", ""))``, introduced in ``296175436`` with
      no measurement naming it and with **0 sites** -- every nullable node in the
      bundle was refused at the time, so it was never graded.  It is wrong in both
      directions, and each cell was measured:

      * at an OPTIONAL property the document declares ``["string", "null"]`` for,
        the default is still D4's spelling of absence and nothing else, and the
        proxy reported it.  That is what blocked
        ``core/webhook-activity-record.json`` and ``core/delivery-metrics.json``
        from emitting, at ``added`` rather than at the ``type`` the row is about.
      * at a REQUIRED property the proxy ADMITTED one, and a default on a key the
        document demands makes that key omissible -- which is the model inventing
        a default, the very thing the ``value is None`` gate exists for.
        ``compiler.fields`` refuses a document default on a required property for
        exactly this reason, so a model-only one is the same defect arriving from
        the other side.

      So the clause reads ``required``, which the comparison knows and this
      function was not being told.  One rule with the parameter it was missing,
      not a second rule beside it.
    * **a ``type`` the node's own content already forces**, which
      :func:`_entails_type` decides from the document.  A typeless node with nothing
      forcing it is still reported.

    **DELETED with the delegated resolver (§9), and each one undid a rewriting of it
    rather than reading anything of ours:**

    * ``additionalProperties: true``, **and this one MOVED rather than went** -- see
      :func:`_silent_about_extras`.  The arm read
      ``keyword == "additionalProperties" and value is True`` on the MODEL side only,
      and its stated reason was the resolver: ``resolve_all_refs`` dropped a redundant
      ``additionalProperties: true`` while inlining, so a referrer's copy of a target
      stated nothing where the target states ``true``.  That half is gone --
      ``bundle.record`` copies the key, so both sides state it where the document does.
      What the one-site measurement beside it never split off is the OTHER source: §4's
      mapping row renders a property-less object as ``dict[K, V]``, and pydantic has no
      spelling of ``dict[str, Any]`` that omits the keyword, so a faithful mapping states
      it where its document is silent -- 23 pairs of the committed tree, measured.  That
      is a reading this pipeline's own output forces, which §9 keeps and applies to BOTH
      sides, so it is a normalisation of the NODE and no longer a model-only admission.
      ``additionalProperties: false`` and a TYPED value are untouched on either side.
    * ``type``, ``description`` and ``default`` at a node the document gives an
      ``enum``.  ``canonicalish`` reduced an enum node to its ``enum`` ALONE while
      inlining, dropping ``type``, ``title``, ``description`` and ``default``, so a
      faithful enumeration stated three facts its own resolved document no longer did.
      The record keeps all four, so the ``description`` and the ``default`` are
      compared against the document's own.  **The ``type`` half is NOT deleted, it
      MOVED**: 164 nodes of the raw bundle, in 79 documents, state an ``enum`` with no
      ``type`` of their own, and a pydantic ``StrEnum`` renders one -- that is this
      pipeline's output and not the resolver's, so :func:`_entails_type` answers it
      beside the ``const`` it already answered, one derivation of "the type the
      node's own content forces" rather than two.
    * a ``description`` at a node the document gives a ``const``.  The same
      ``canonicalish`` reduction at a one-member set: the referrer's copy of
      ``core/agent-encryption-key.json``'s ``kty`` kept neither its ``type`` nor its
      ``description``, while the target's own record kept both.  The record now keeps
      both at both, so a dropped or wrong ``description`` is graded in both directions
      and nothing is excused.
    """
    if keyword == "default":
        return value is None and not required
    return keyword == "type" and _entails_type(doc, value)


def _silent_about_extras(node: Any) -> Any:
    """A MAPPING's ``additionalProperties: true``, read as the silence it is.

    **A reading THIS PIPELINE'S OWN OUTPUT forces, so §9 keeps it, and it is applied to
    BOTH sides by the one function.**  ``docs/plan/architecture.md`` §9 keeps "the
    readings this pipeline's own output forces ... and each is applied to both sides" and
    names three of them -- a nested class hoisted to ``$defs``, D4's ``| None``, a type
    list rendered as a union.  Those three are EXAMPLES of the criterion and not the
    whole of it: §4's mapping row renders a property-less object as ``dict[K, V]``, and
    pydantic 2.13.5 has no spelling of ``dict[str, Any]`` that omits
    ``additionalProperties: true`` -- so a faithful mapping states a keyword its document
    is silent about, in exactly the way a faithful multi-type node states an ``anyOf``.

    **The two spellings are ONE acceptance fact.**  draft-07's ``additionalProperties``
    constrains the keys a schema does not already declare, and ``true`` admits every one
    of them, which is what silence admits; the two schemas accept and refuse identical
    instances.  §2's "silence -> ``ignore``, ``true`` -> ``allow``" is a statement about
    PYDANTIC's retention of an extra key on a CLASS, not about a document's accepted set,
    and what this comparison grades is the accepted set.

    **SCOPED TO A MAPPING -- a node that declares no ``properties`` -- and the scope is
    the whole of its correctness.**  On a node WITH ``properties`` the distinction is
    load-bearing exactly as §2 says, a store's extras are retained or ignored by it, and
    nothing here touches such a node.  The arm this replaces was
    ``keyword == "additionalProperties" and value is True`` on the MODEL side only,
    justified by a one-site measurement of the delegated resolver's redundant-key drop,
    and it was silently absorbing 23 pairs of this mechanism -- a blanket predicate whose
    population nobody had split.  One blanket predicate is not replaced by another: the
    gate reads the node's own shape.

    ``additionalProperties: false`` is NOT touched, on either side.  It forbids what
    silence permits, so the two are different accepted sets: a model closing a mapping
    its document leaves open is a NARROWING and is reported, and a document closing one
    the model leaves open is ``missing``.  A TYPED value is not touched either -- it
    restricts the value schema, which silence does not -- so a model typing a mapping
    whose document says ``true`` still reports.

    No ``type`` gate, because none is needed: for an object with no declared property the
    two spellings admit the same keys, and for a non-object the keyword constrains
    nothing either way.
    """
    # **"Declares no ``properties``" means an EMPTY map as well as an absent one**, and
    # the two sides spell that difference without meaning it: a document that declares
    # no property writes no ``properties`` key, and pydantic renders ``properties: {}``
    # for a model with no field -- so the membership test read one side as a mapping and
    # the other as a class.  Measured at §14 step 9, where a union base over a root that
    # declares no property of its own is the first such node to emit:
    # ``core/format-option-ref.json#`` and the two pairs that reach it through a ``$ref``
    # reported ``/additionalProperties: the model says True, the document nothing`` for a
    # model whose accepted set is its document's.  The gate is the docstring's own words
    # and the direction is unchanged -- ``false`` and a typed value are still untouched
    # on both sides.
    if not isinstance(node, Mapping) or node.get("properties"):
        return node
    if node.get("additionalProperties") is not True:
        return node
    return {k: v for k, v in node.items() if k != "additionalProperties"}


def _declares_null(doc: Any) -> bool:
    """Does the DOCUMENT declare ``null`` among this node's types?

    The one question :func:`_normalize` cannot answer from the model, and the one
    it has to ask: ``{"type": ["string", "null"]}`` and an OPTIONAL
    ``{"type": "string"}`` are different documents that D4 renders as the same
    ``str | None``, so the model's own schema does not say which it came from.
    Read off the document, which does.

    A list, because that is the only spelling a multi-type node has; the lone
    ``{"type": "null"}`` is included for completeness and has no site in the
    bundle.
    """
    kind = doc.get("type") if isinstance(doc, Mapping) else None
    return "null" in kind if isinstance(kind, list) else kind == "null"


def _constrains_a_key(key_schema: Mapping[str, Any]) -> bool:
    """Does a ``propertyNames`` node say anything about a key that is GRADABLE?

    A key schema one side states and the other does not is reported only where it
    carries a fact: ``{"x-entity": "product"}`` beside a ``minLength`` is an
    ``x-`` annotation §6 admits and no model renders, so a side stating the node
    and no fact is not a side that dropped one.  A local ``$ref`` counts, because
    the comparison resolves one and the facts behind it are the key type's.
    """
    return "$ref" in key_schema or any(
        kw in key_schema for kw in compared_facts(Position.KEY)
    )


def _extra_key_typed(doc: Mapping[str, Any], got: Mapping[str, Any]) -> bool:
    """Is this node a STORE whose extra key the model types, which pydantic does not
    render?

    Section 5's ``additionalProperties`` row makes a typed one on a CLASS -- a node
    declaring ``properties`` as well -- ``allow`` with a typed ``__pydantic_extra__``,
    and section 5's ``propertyNames`` row makes the key a TYPE.  The emitter writes
    both: ``__pydantic_extra__: dict[StrMaxLen128, V]``.  **pydantic 2.13.5 renders the
    VALUE of that dict as ``additionalProperties`` and drops its KEY**, so the document's
    ``propertyNames`` has nowhere to be read back from -- measured on
    ``governance/reported-outcome-error.json``, the bundle's only graded store with a
    constrained key, and the first document to reach it (``salesagent-j3k2l.41``).

    **This is an admission of the STRONG kind: the fact is true of the model.**  The
    model refuses a 129-character extra key and accepts a short one, which
    ``tests/test_inner_facts.py`` asserts against the emitted class rather than leaving
    to this sentence -- so the premise this row rests on is graded and not merely
    written down.  It is counted in :attr:`ComparisonResult.extra_key_typed` and never
    folded into ``missing``, for ``url_typed``'s reason: a fold that disappears into a
    green ``missing`` is invisible and permanent.

    Three gates, and the first is what makes it a store rather than a mapping:

    * the DOCUMENT declares ``properties`` here.  A mapping has none, and a mapping's
      key IS rendered -- as ``propertyNames`` or as ``patternProperties``, which
      :func:`_patterned_key` reads on both sides -- so a mapping dropping its key
      schema is still reported;
    * the model renders a typed ``additionalProperties``, so a model that widened the
      store's value to ``Any`` (``additionalProperties: true``) or closed it is not
      admitted here;
    * the model renders no ``propertyNames`` of its own, which is the caller's own
      ``elif``: a model that DOES render one is compared against the document's.

    KNOWN CEILING, named because it is a real narrowing and the bundle does not reach
    it: the model types the key of an EXTRA, so a declared property whose name the
    document's ``propertyNames`` would refuse is admitted by the model.  A declared key
    is a fixed string the document itself writes, so such a document contradicts
    itself; 0 of this bundle's store nodes do.
    """
    return (
        isinstance(doc.get("properties"), dict)
        and isinstance(got.get("additionalProperties"), dict)
        and bool(got["additionalProperties"])
    )


def _patterned_key(node: Any, *, closed: bool) -> dict | None:
    """A mapping whose KEY carries a pattern, written as a key schema and a value.

    **One shape, three spellings, and the comparison has to read all three.**  §2
    says a mapping's key is a TYPE, and a patterned key is
    ``dict[Annotated[str, StringConstraints(pattern=P)], V]``.  The document spells
    that two ways and pydantic renders it a third:

    * ``propertyNames: {"pattern": P}`` beside ``additionalProperties: V`` -- every
      key matches ``P``, every value matches ``V``;
    * ``patternProperties: {P: V}`` beside ``additionalProperties: false`` -- a key
      matching ``P`` has value ``V``, and no other key is admitted, which is the
      same statement;
    * pydantic 2.13.5 renders the annotation as ``{"type": "object",
      "patternProperties": {P: V}}`` and states no ``additionalProperties`` at all,
      although the validator does refuse a non-matching key (``{"AB": 1}`` accepted,
      ``{"abc": 1}`` refused for ``^[A-Z]{2}$``).

    So this writes all three as the FIRST spelling, which is the one whose two
    keywords the rest of the comparison already reads: ``additionalProperties`` is
    in :func:`compared_facts` and recursed into, and ``propertyNames`` is descended into
    beside it.  Without it the ``propertyNames`` document reported a faithful model
    as dropping its ``additionalProperties`` (measured: ``model_drops_a_fact`` at
    ``core/geo-region-support.json#/properties/countries/additionalProperties`` and
    at ``trusted-match/identity-match-response.json#/properties/tmpx_providers``),
    while the ``patternProperties`` document passed with the value schema and the
    key expression both ungraded -- the two halves of the same hole.

    ``closed`` is whether a bare ``patternProperties`` -- one with no
    ``additionalProperties`` beside it -- closes this node's keys, and it is the one
    thing the node cannot say for itself.  **It is a property of the SIDE and not a
    guess**: pydantic only ever renders a patterned key for a dict whose key type
    refuses a non-matching key, so on the model side a bare ``patternProperties``
    IS closed; in a document, draft-07 admits every key the pattern does not match,
    so it is not.  A document in that shape therefore gets no reading here and is
    compared as it stands, which is the fail-safe direction -- and the emitter
    refuses it outright (``lower.containers.mapping``), so no emitted pair reaches
    it.

    ``None`` where the node is not this shape, and the caller then leaves it alone.
    A node with ``properties`` is a CLASS and not a mapping, and more than one
    pattern is a value schema per key shape, which §5 refuses.
    """
    if not isinstance(node, dict):
        return None
    patterned = node.get("patternProperties")
    if not isinstance(patterned, dict) or len(patterned) != 1 or "properties" in node:
        return None
    # A key schema BESIDE the pattern is pydantic's rendering of a key type carrying
    # a length bound as well, and the two halves are one key: measured on 2.13.5,
    # ``dict[Annotated[str, StringConstraints(min_length=1, max_length=64,
    # pattern=P)], V]`` renders ``{"patternProperties": {P: V}, "propertyNames":
    # {"minLength": 1, "maxLength": 64}}``, which is the shape 5 of the bundle's 13
    # patterned key sites state.  So the model's two halves MERGE.  In a DOCUMENT the
    # same pair is two statements about one key type, which §5 refuses, so it gets no
    # reading here -- ``closed`` is again the side.
    beside = node.get("propertyNames")
    if beside is not None and not (closed and isinstance(beside, dict) and "pattern" not in beside):
        return None
    if "additionalProperties" in node:
        if node["additionalProperties"] is not False:
            return None  # two value schemas for one mapping value
    elif not closed:
        return None
    ((expr, value),) = patterned.items()
    out = {k: v for k, v in node.items() if k not in ("patternProperties", "additionalProperties")}
    out["propertyNames"] = {**(beside or {}), "pattern": expr}
    out["additionalProperties"] = value
    return out


def _key_schema(node: Mapping[str, Any]) -> dict:
    """A ``propertyNames`` node with its implied ``type`` restored, on either side.

    A JSON object's key is a string, so ``type: "string"`` on a key schema states
    what the POSITION already says.  That is why the bundle writes it at 5 of its 13
    patterned key sites and leaves it out at the other 8, and why pydantic renders
    ``propertyNames: {"minLength": 1}`` for a key type that IS a ``str``.  Restored
    on BOTH sides so neither spelling reads as a fact the other dropped;
    ``lower.containers._key`` supplies the same word on the document side before
    lowering, for the same reason.

    Not supplied over a declared ``type``, nor over a ``$ref`` -- a reference NAMES
    the key type and brings its own facts, which :func:`_normalize` resolves.
    """
    if "type" in node or "$ref" in node:
        return dict(node)
    return {"type": "string", **node}


#: The two combinators a union of types is spelled with, and BOTH are read,
#: because the two sides spell it differently.  ``anyOf`` is pydantic's only
#: spelling of a union; ``oneOf`` is the DOCUMENT's at 2 of this bundle's 3
#: fold positions (``creative/creative-feature-result.json#/properties/value``
#: and ``property/property-feature-value.json#/properties/value``, each
#: ``oneOf: [{"type": "boolean"}, {"type": "number"}, {"type": "string"}]``).
#: Reading only ``anyOf`` folded the model and left the document unfolded, which
#: is the asymmetry ``salesagent-j3k2l.33`` is about.
#:
#: **A ``oneOf`` of bare types is a type list because a value has exactly one
#: JSON type -- with one exception, gated below**: ``integer`` and ``number``
#: both admit ``5``, so a ``oneOf`` naming both REFUSES every integer while the
#: type list admits it.  That pair is the only overlap in draft-07's type
#: vocabulary, and ``true`` is ``boolean`` and not ``number`` in it.
_UNION_KEYWORDS = ("anyOf", "oneOf")


def _target(ref: Any, root: Any) -> Any:
    """The node a LOCAL ``$ref`` names, found by walking its POINTER from ``root``.

    **A pointer walk and not the last segment of the reference**, which is what
    this used to be: measured over all 1,054 portable documents of the bundle there
    are 405 local-``$ref`` sites, and 3 of them name a ``definitions`` section
    NESTED inside a property
    (``brand/get-brand-identity-response.json`` ->
    ``#/oneOf/0/properties/fonts/definitions/font_role``).  A last-segment lookup
    answers those 3 from whatever section happens to hold that key, silently, and
    the walk answers all 405 for the same amount of code.

    ``None`` for anything that does not resolve, which is the FAIL-SAFE direction:
    the caller leaves the node's own annotations in place and states no fact, so
    every fact the model carries reads as ``added`` and the pair reddens.  A
    reading that invented facts for an unresolvable reference would do the
    opposite.
    """
    if not isinstance(ref, str) or not ref.startswith("#"):
        return None
    try:
        target = at(root, ref[1:])
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    return target if isinstance(target, dict) else None


def _branch_target(branch: Any, root: Any) -> Any:
    """A union BRANCH that is a bare local ``$ref``, read as the node it names.

    **The same reading :func:`_normalize` already takes at a NODE, taken one level in
    at a BRANCH, and taken by the one function on BOTH sides.**  §9's "a nested class
    hoisted to ``$defs``" is the reading: ``bundle.record`` inlines a REMOTE reference
    and leaves a LOCAL one as written, pydantic names a nested class the same way, so
    both sides spell a branch that is another node as a ``$ref`` -- and a reading
    applied at the node and not at the branch makes a branch state nothing where its
    document states a type, a ``required`` and a shape.  Measured: a root union whose
    first two branches are ``{"$ref": "#/definitions/ScalarBinding"}`` and
    ``{"$ref": "#/definitions/AssetPoolBinding"}``, each a ``type: object``, answered
    :func:`_entails_type` with two silent branches, so the base's own ``type: object``
    -- which §4 renders for every union base -- reported as ``added`` against a
    document that states it at every branch.

    **ONE HOP, and the gate is that the branch is BARE.**  Measured over the records of
    all 1,054 portable documents there are 33 union branches that are a local ``$ref``,
    in 28 union nodes, and **all 33 carry no key beside the ``$ref``** -- so the gate
    costs no site and keeps the rule off a shape nobody showed it.  A branch with a
    sibling, and a target that is itself a reference, are both left as they are: no hop
    happens, the branch states no ``type`` word, :func:`_entails_type` answers ``False``
    and the pair REDDENS rather than passing blind.  The targets bear this out -- 3 of
    the 33 resolve to a node whose own content is a ``oneOf``, which states no ``type``,
    and that is exactly the answer the one hop gives.

    ``None`` from :func:`_target` is the same fail-safe: the branch stays as written.
    """
    if not isinstance(branch, dict) or set(branch) != {"$ref"}:
        return branch
    target = _target(branch["$ref"], root)
    return branch if target is None else target


def _conjoined_type(node: dict, kw: str, branches: list[dict]) -> tuple[dict, list[dict]]:
    """A ``type`` word BESIDE a union is conjoined into every branch, which is what
    draft-07 says it is.

    **A reading THIS PIPELINE'S OWN OUTPUT forces, so §9 keeps it** -- the emitter is
    what conjoins the word, through ``_base.applied_schema``, and nothing of the
    delegated resolver is involved.  Every branch of a draft-07 combinator is applied to
    the SAME instance, so a sibling ``type`` asserts about that instance too and a
    branch stating none of its own has it: ``{"type": "string", "anyOf": [{"format":
    "uri-template"}, ...]}`` and ``{"anyOf": [{"type": "string", "format":
    "uri-template"}, ...]}`` are one document said two ways.  **They are the two ways
    the two SIDES say it**: the document states the word once at the root, and the
    emitter conjoins it into each branch -- ``_base.applied_schema``, which is the
    schema half's own reading of what a branch says, and ``lower.union.applied_type``
    is where the walk asks it -- so pydantic renders it per branch and the node itself
    states no type at all.

    Without this the word is in :func:`compared_facts` on the document's side and absent from
    the model's, and a faithful alias reports as dropping its own ``type``.  Measured on
    ``core/macro-bearing-url.json``, the bundle's only graded node stating a ``type``
    beside a union, and the first document to reach it (``salesagent-j3k2l.41``).

    **Conjoining DOWN and not hoisting up, and the measurement is what decided it.**
    Hoisting a word every branch states up to the node equalizes the same pair and
    keeps the fact compared, which is better in principle -- and it is wrong, because
    the two sides' branches are shaped differently and the hoist then fires on one side
    only.  Measured by doing it: **11 pairs reported a drop and 4 an addition**, every
    one of them faithful.  A document stating ``type: object`` inline in each branch
    hoists while the model renders those branches as ``$ref`` -- that is
    ``core/placement-presentation.json`` and six more -- and a model whose branches
    state ``type: string`` hoists while the document's branches state no type at all,
    which is ``core/geo-place-area.json`` and three more.  Conjoining down fires on the
    SHAPE the keyword's own semantics name and so fires wherever that shape is, on
    either side.

    **KNOWN CEILING: the word stops being COMPARED at that node.**  Neither side
    recurses into a branch, so a fact moved into the branches is a fact no comparison
    reads -- green by disappearing, which is the thing this module's folds are meant
    not to be.  What bounds it: the fold fires only where the node states a ``type``
    BESIDE a union, 1 graded node in this bundle, and that node's accepted set is still
    graded by the accepts and refuses checks against the document's own schema.
    Closing it needs ``compare`` to recurse into a union's branches pairwise, which is
    a reading of which branch answers which and is not this function's.
    """
    word = node.get("type")
    if not isinstance(word, str):
        return node, branches
    conjoined = [b if "type" in b else {**b, "type": word} for b in branches]
    return {k: v for k, v in node.items() if k != "type"} | {kw: conjoined}, conjoined


def _normalize(
    node: Any,
    root: Any,
    depth: int = 0,
    *,
    declared_null: bool = False,
    null_is_absence: bool = True,
) -> dict:
    """One node for one position, written the way the two sides can be compared.

    **Called on BOTH sides, which is the whole of ``salesagent-j3k2l.32`` and
    ``.33``.**  It began as "the MODEL's node written the way the document writes
    it" and that was the defect: every normalization below is a statement about
    one SPELLING of a fact, and a spelling the document also uses has to be read
    the same way or a faithful class reads as narrower than its own document.
    Measured, with the two shapes reachable: a document-side local ``$ref``
    produced **43 ``added`` facts over 4 pairs in 2 documents**, and the folds
    below produced **9 more over 7 pairs**, for a faithful class in every case.
    ``added`` is the half that can make a faithful SDK refuse valid traffic, and
    it is 0 over the whole graded tree.

    ``root`` is the schema a ``$ref`` resolves against and so is per-side: the
    model's own ``model_json_schema()`` for the model, and the whole resolved
    DOCUMENT for the document -- a nested pair's node is a sub-node and
    ``#/definitions/x`` is relative to the document root, which is why
    :class:`Pair` carries the document and not only the node.

    **Every normalization left here is a reading THIS PIPELINE'S OWN OUTPUT forces,
    which is the half ``docs/plan/architecture.md`` §9 keeps, and each is applied to
    BOTH sides.**  The one-member-``enum`` respelling that stood first in this list is
    deleted with the delegated resolver: ``canonicalish`` rewrote ``enum: [v]`` into
    ``const: v`` while inlining a remote reference, so one accepted set arrived in two
    spellings depending on which side held it.  ``bundle.record`` copies the
    document's own spelling, and §4's enumeration row renders an ``enum`` for an
    ``enum`` node and a ``Literal`` -- so a ``const`` -- for a ``const`` one, so the
    two sides now reach the node with the same keyword and there is nothing to fold.

    * **A local ``$ref``.**  A nested object is a nested CLASS and a
      cross-document reference is an IMPORT (P2), so pydantic hoists both into
      ``$defs`` and references them.  ``codegen.bundle.record`` inlines a REMOTE
      reference and leaves a LOCAL one as written, so the document says ``$ref`` too,
      and this is the "nested class hoisted to ``$defs``" reading §9 names.

      **AT A UNION BRANCH TOO, and that is one reading in one place rather than a
      second rule.**  The reading was taken at the node and not at the branches inside
      a combinator, so a branch that is a bare local ``$ref`` stated nothing and
      :func:`_entails_type` read a root union's branches as typeless where the document
      types every one of them -- ``core/requirements/catalog-field-binding.json#``, whose
      base's ``type: object`` reported as ``added`` against a document stating it three
      times.  :func:`_branch_target` carries the hop and the measurement that scopes it.
    * **An ``anyOf`` with a ``null`` branch, AND WHICH OF THE TWO THINGS IT IS.**
      D4 renders an optional property ``T | None``, because the attribute holds
      ``None`` for an omitted key.  pydantic states that as a union; the document
      states the type and leaves presence to ``required``.  Unwrapping the null
      branch compares like with like.

      **A document that DECLARES ``null`` renders the same union, and unwrapping
      that one erased the document's own fact.**  ``["string", "null"]`` is
      ``str | None``, which is what D4 renders for an optional ``{"type":
      "string"}`` as well -- so one model schema stood for two different
      documents, and the comparison reported a faithful model as dropping its
      ``type`` while a model that DROPPED the declared null compared the same way.
      Neither could be graded, which is why ``lower.containers.multi_type``
      refused a ``null`` arm by name rather than emit a node no check reads.

      The distinction is not available on the model's side at all, so it comes
      from ``declared_null``, which the caller reads off the DOCUMENT
      (:func:`_declares_null`).  Where the document declares null the branch is a
      type fact and is folded INTO the type list; where it does not, the branch is
      presence and is unwrapped exactly as before.  Measured on
      ``core/webhook-activity-record.json``'s ``completed_at``
      (``["string", "null"]``, ``format: date-time``),
      ``core/delivery-metrics.json``'s ``completion_rate`` and
      ``core/error.json``'s discriminator ``value``
      (``["string", "number", "boolean", "null"]``).

      A model that drops the declared null folds into nothing -- with no null
      branch neither arm of this fold applies -- so it is still reported, which is
      the half ``tests/test_emit.py`` reddens on.

      **``null_is_absence`` is the OTHER half of that same question, and the
      measurement that forced it.**  D4 renders ``None`` for an OPTIONAL property;
      a REQUIRED one has no default, so a ``null`` branch there is a type the model
      admits and the document does not.  Unwrapping it regardless made those two
      cases one cell again from the other direction: measured, a model declaring
      ``v: bool | float | str | None`` at a property its document REQUIRES and
      types ``[boolean, number, string]`` compared byte-identical to the faithful
      ``v: bool | float | str`` -- both ``pass``.  So the null is folded into the
      ``type`` unless the caller says the position really can be absent, and the
      caller reads that off the parent document's ``required``.
      KNOWN CEILING: the axis ``compare`` carries is "the parent demands this
      key", which cannot tell an OPTIONAL property from a position with no
      presence question at all (an ``items``, a root, a mapping's value), so a
      null branch at one of those is still read as absence.  Closing that needs a
      third state on the axis rather than a wider rule here.
    * **A union of BARE types is a ``type`` LIST.**  draft-07 lets a node name
      several types at once and pydantic has no spelling for that but a union, so
      ``{"type": ["number", "string"]}`` comes back
      ``{"anyOf": [{"type": "number"}, {"type": "string"}]}`` -- one fact in two
      spellings, and without this fold the model was reported as stating no
      ``type`` at all.  Measured on ``error-details/conflict.json``, whose two
      multi-type properties were the first in the emitted population: the
      comparison said ``model_drops_a_fact`` twice for a model that states exactly
      what its document states.

      The fold applies only where EVERY branch is a bare ``{"type": X}``.  A
      branch carrying anything else is a union of constrained types rather than a
      type list, and folding it would throw that branch's constraint away -- so
      such a union is left alone and compares as it is.  It also cannot excuse an
      omission in either direction: a model listing more types than the document
      still differs after the fold, and a model listing fewer never folds into a
      match.

      **KNOWN CEILING: a bare type beside a DESCRIPTION does not fold either.**
      ``{"type": "string", "description": "..."}`` is a bare type as far as the
      accepted set goes, but this keeps the exact-key test -- folding would throw the
      branch's own description away, and the direction of the miss is safe: the node
      stays a combinator,
      states no fact in :func:`compared_facts`, and the pair reddens rather than passing
      blind.  0 of the 3 fold positions in this bundle carry one.
    * **The outer keys win.**  ``default`` and ``description`` sit outside the
      ``anyOf`` and the type facts inside the branch.

      **KNOWN CEILING, and the measurement that bounds it.**  Draft-07 IGNORES
      every sibling of a ``$ref``, so a document stating
      ``{"$ref": X, "minimum": 5}`` means X alone, and letting the sibling win
      there would let the document EXCUSE a model that really is narrower.  What
      bounds it is the bundle: of the 405 local-``$ref`` sites the only keys ever
      beside one are ``description`` (58) and ``deprecated`` (4), so **0 sites
      carry a constraint keyword beside a local ``$ref``** and the rule's unsafe
      half has no population.  ``description`` winning is not optional in the
      other direction -- the compiler transcribes the sibling onto the field, so
      a reading that preferred the target's description would report an ``added``
      fact at 58 sites.  The upgrade path, if a document ever states a constraint
      beside a local ``$ref``, is to keep only the keys outside :func:`compared_facts`.
    """
    if depth > 16 or not isinstance(node, dict):  # a self-referential $defs chain
        return node if isinstance(node, dict) else {}
    if "$ref" in node:
        target = _target(node["$ref"], root)
        # ``declared_null`` deliberately does NOT travel through here.  It would be an
        # arm with no site: measured over the graded population, 5 positions have a
        # document declaring ``null`` and **all 5 render as an ``anyOf``, 0 as a
        # ``$ref``** -- pydantic names a nested CLASS that way, and a class is not a
        # null arm.  A derivation matching nothing is green for free, and this one
        # also fails SAFE if such a position ever appears: the fold does not fire, so
        # the document's ``type`` reads as missing and the pair reddens.
        outer = {k: v for k, v in node.items() if k != "$ref"}
        return {**_normalize(target, root, depth + 1), **outer} if target is not None else outer
    for kw in _UNION_KEYWORDS:
        stated = node.get(kw)
        if not (isinstance(stated, list) and stated and all(isinstance(b, dict) for b in stated)):
            continue
        # The branches as the DOCUMENT writes them.  They were read through the
        # delegated resolver's finite-type rewrite here, because that resolver wrote a
        # finite type out as its members WHILE INLINING and so gave one union two
        # shapes depending on whether the document stated it or referenced one that
        # did: the three documents referencing
        # ``creative/creative-feature-result.json#/properties/value`` carried
        # ``oneOf: [{"enum": [false, true]}, ...]`` where the two that state it carry
        # ``{"type": "boolean"}``.  ``bundle.record`` copies the branch, so all five
        # now carry the one shape and the rewrite has nothing to undo (§9).
        #
        # A branch that is a bare local ``$ref`` is read as the node it NAMES
        # (:func:`_branch_target`) -- the same reading this function already takes at a
        # node, taken one level in, and taken here so BOTH sides get it from the one
        # call.  The node is rebuilt with the resolved branches below, so every reader
        # downstream -- the two fold arms, and :func:`_entails_type`, which asks each
        # branch for its ``type`` word -- sees what the branch states rather than the
        # pointer it states it through.
        branches = [_branch_target(b, root) for b in stated]
        node, branches = _conjoined_type(node, kw, branches)
        # ``_conjoined_type`` rebuilds the node when a sibling ``type`` conjoins and
        # leaves it alone otherwise, so the resolved branches are put back here: a
        # fall-through returns ``node``, and returning it with the branches AS WRITTEN
        # would make this reading reach the fold arms and nothing else.
        node = {**node, kw: branches}
        live = [b for b in branches if b.get("type") != "null"]
        nulls = [b for b in branches if b.get("type") == "null"]
        outer = {k: v for k, v in node.items() if k != kw}
        # The null branch is a TYPE FACT unless the position can really be absent:
        # the document declares it, or the model renders it at a key nothing can
        # omit.  Either way it is folded INTO the type rather than unwrapped.
        keep_null = declared_null or not null_is_absence
        if len(nulls) == 1 and len(live) == 1:
            one = {**_normalize(live[0], root, depth + 1), **outer}
            if not keep_null:
                return one
            kind = one.get("type")
            # The null is a TYPE FACT here, so the fold has to carry it forward or
            # not fire.  Returning ``one`` without it would drop the document's own
            # ``null`` -- and then a model that DROPPED the null compares identical
            # to one that kept it, which is the conflation
            # ``test_a_declared_null_is_never_read_as_absence`` exists to redden on.
            # A live branch with no ``type`` word of its own has nowhere to put it, so
            # that case does not fold: the node stays a combinator, states no fact in
            # ``compared_facts``, and the pair reddens visibly instead of passing blind.
            if isinstance(kind, str):
                return {**one, "type": [kind, "null"]}
            if isinstance(kind, list) and "null" in kind:
                return one
            return node
        if len(nulls) <= 1 and len(live) > 1 and all(set(b) == {"type"} for b in live):
            kinds = [b["type"] for b in live]
            if kw == "oneOf" and {"integer", "number"} <= set(kinds):
                # The one overlap in draft-07's type vocabulary: both branches admit
                # ``5``, so this ``oneOf`` refuses every integer and the type list
                # admits it.  Folding would state a fact the document does not.
                return node
            return {"type": [*kinds, "null"] if keep_null and nulls else kinds, **outer}
        # **DELETED WITH THE DELEGATED RESOLVER (§9): the same-title lift.**  It fired
        # where every branch of a combinator carried the SAME ``title``, which was the
        # signature of ``canonicalish`` rewriting a root ``if``/``then`` into an
        # ``anyOf`` of the two cases and copying the node's own ``title`` into both.
        # The pair it existed for -- ``media-buy/sync-catalogs-request.json`` at
        # ``/properties/item_availability_updates/items``, which references
        # ``core/catalog-item-availability-update.json``, whose root carries
        # ``if``/``then`` -- now reads the target's own node, with its ``properties``,
        # its ``required``, its ``type`` and its ``description`` where the document
        # writes them, so there are no agreed facts to lift back up.  ``_agreed`` and
        # ``_widest`` were its only readers and go with it.
    return node


#: How deep an ``allOf`` chain ``_composed`` folds before it stops folding.  Same
#: constant and same shape as ``_normalize``'s, deliberately: two instruments that
#: cut a traversal at different places disagree about node identity for no reason
#: anyone can read off either of them (``docs/plan/rebuild-plan.md`` §9).
_COMPOSE_DEPTH = 16

#: The answer :func:`_tighter` gives for a keyword whose two values it cannot order.
#: A sentinel rather than ``None``, because ``None`` is a legal JSON value and a
#: keyword can hold it -- ``default: null`` is in the bundle.
_UNDECIDED = object()

#: The ordering keywords of :func:`compared_facts`, and which direction is TIGHTER: ``max`` for a
#: floor (the higher of two minima binds) and ``min`` for a ceiling.
_TIGHTER_BOUND = {
    "minimum": max,
    "exclusiveMinimum": max,
    "minLength": max,
    "minItems": max,
    "maximum": min,
    "exclusiveMaximum": min,
    "maxLength": min,
    "maxItems": min,
}


def _in_vocabulary(value: Any, members: Any) -> bool:
    """Is ``value`` one of ``members``, where ``members`` is a stated ``enum``?

    ``False`` for anything that is not a list, which is what makes the vocabulary-axis
    collapse in :func:`_composed` conditional on the two actually agreeing: a ``const``
    OUTSIDE a composed ``enum`` is an EMPTY intersection, and dropping the vocabulary
    there would hide a document that admits nothing behind a model that admits one
    value.  The empty intersection is the emitter's refusal to make, so this leaves
    both facts standing and the pair reports.
    """
    return isinstance(members, list) and any(value == member for member in members)


def _one_vocabulary(node: dict, conjunct: dict) -> tuple[dict, dict]:
    """``node`` and ``conjunct`` with ONE statement left on the vocabulary axis.

    ``const: v`` and ``enum: [...v...]`` state the same kind of fact about an instance,
    so the intersection of the two is the PIN and the vocabulary is not a second fact
    beside it.  Whichever view supplies the pin, the other's vocabulary goes -- so the
    gap-fill below cannot leave a merged node carrying both, which is a shape no
    document states.

    Measured on ``core/canonical-media-buy-action.json``, whose branch states
    ``{"const": "control_media_buy"}`` for ``task`` over a composed base's three-member
    ``enum``: keeping both made the document read as stating an ``enum`` the faithful
    model (a ``Literal``) does not, 3 ``missing`` facts over the 3 branches.

    Gated on the pin being IN the vocabulary.  A ``const`` outside it is an EMPTY
    intersection -- the emitter's refusal to make -- and dropping the vocabulary there
    would hide a document that admits nothing behind a model that admits one value, so
    both facts are left standing and the pair reports.
    """
    if "const" in conjunct and _in_vocabulary(conjunct["const"], node.get("enum")):
        return {k: v for k, v in node.items() if k != "enum"}, conjunct
    if "const" in node and _in_vocabulary(node["const"], conjunct.get("enum")):
        return node, {k: v for k, v in conjunct.items() if k != "enum"}
    return node, conjunct


def _vocabulary(view: Any) -> list | None:
    """The value set ``view`` states, or ``None`` where it states none.

    A ``const`` is read as the one-member set it is, which is the same rewrite
    ``codegen.compiler._as_enum`` makes on the model side and for the same reason: a pin
    and a vocabulary are one axis, so one reader answers ``const`` against ``const``,
    ``const`` against ``enum`` and ``enum`` against ``enum``.  Read BEFORE
    :func:`_one_vocabulary` collapses the axis, because that collapse drops one of the
    two statements and the question here is which VIEW made the surviving one.
    """
    if not isinstance(view, dict):
        return None
    if "const" in view:
        return [view["const"]]
    members = view.get("enum")
    return members if isinstance(members, list) else None


def _inside(inner: list | None, outer: list | None) -> bool:
    """Is ``inner`` a STRICT subset of ``outer``, both read as stated value sets?

    Strictness is "every member of ``inner`` is in ``outer`` and some member of
    ``outer`` is not in ``inner``" and not a length comparison, so a duplicate member --
    which the ``enum`` row refuses at emission but which this reader meets before any
    such check -- cannot make a set read as smaller than the one it equals.
    """
    if inner is None or outer is None:
        return False
    return all(_in_vocabulary(m, outer) for m in inner) and any(
        not _in_vocabulary(m, inner) for m in outer
    )


def _described_by_the_conjunct(node: dict, conjunct: dict) -> dict:
    """``node`` with its ``description`` stood down where the CONJUNCT states the one.

    **The view that states the composed node's VALUE SET states its description**, which
    is ``docs/plan/rebuild-plan.md`` §6's description row read where §2's intersection
    puts it: "a composed base's loses to the document's own".  Under ``allOf`` the
    composed node admits the intersection, and where one view's vocabulary is strictly
    inside the other's the intersection IS that view's declaration -- so that view is
    the one the document states at this pointer, and its description comes with it.
    The model reads it the same way one step earlier: ``compiler._intersection`` decides
    the field from the narrowing declaration and carries that declaration's annotations
    (``compiler.RENDERED``), so the element type is the narrowing ``$ref``'s class and
    its docstring is that target's description.  §9 keeps the two spellings apart and
    requires them to agree; this is the document half of the one in the compiler.

    Measured on ``core/media-buy-frequency-cap-requirement.json`` at
    ``/properties/supported_control_modes/items``, whose base declares the element as
    ``enums/frequency-cap-control-mode.json`` (three members, "A supported package
    frequency-cap control shape.") and whose own overlay narrows it to
    ``enums/media-buy-frequency-cap-control-mode.json`` (one member, "The aggregate
    MediaBuy frequency-cap control shape supported in 3.2."): the merged node took the
    conjunct's ``enum`` by :func:`_tighter` and kept the BASE's description, so a class
    faithful to the narrowing declaration read as dropping a fact -- 1 ``differs`` here
    and 1 at ``core/media-buy-support-requirements.json``, which reaches the same node
    through a ``$ref``.

    **Three gates, and each one has to be here.**

    * **The conjunct must state a description.**  Silence inherits (§6 clause 3), so a
      narrowing conjunct that says nothing to a reader leaves the base's description
      standing rather than deleting it.  Measured: ``core/canonical-media-buy-action.json``
      narrows ``task`` to a ``const`` and states no description of its own, and dropping
      the base's there would make the document state none where the model states one.
    * **The conjunct's set must be INSIDE the node's.**  Where the node is the narrower
      view the node already states the composed declaration and its own description is
      the answer -- 3 sites on this tree, each a response's own ``status`` pinned to one
      member of the task-status vocabulary ``core/protocol-envelope.json`` states.
    * **STRICTLY inside.**  Two views stating the same value set state the same
      declaration, and then §6's default stands: the node's own wins.  That is also
      where the other 277 sites land -- two descriptions differing on no narrowing at
      all, over 145 pairs -- and the gap-fill's own measurement is the reason: at a
      pointer the document declares itself, the node IS the document's own.

    The axis is the VOCABULARY and not every keyword :func:`_tighter` can order.  A
    conjunct narrowing a BOUND beside a description of its own has **0 sites** on this
    tree, and so does one widening a vocabulary; an arm for either would be a derivation
    matching nothing (``_restatement``'s own precedent).  ``default`` is left out for the
    same measurement: the 7 sites where two views default a property differently are
    all at ``neither``, where this rule does not fire.
    """
    if "description" not in conjunct:
        return node
    if not _inside(_vocabulary(conjunct), _vocabulary(node)):
        return node
    return {k: v for k, v in node.items() if k != "description"}


def _tighter(keyword: str, node: Any, conjunct: Any) -> Any:
    """The INTERSECTION of two views of one keyword, or :data:`_UNDECIDED`.

    Section 2's rule, in the two spellings it names for a keyword both views state: "an enum is
    the intersection of the members, a bound is the tighter one".  Anything else is
    ``_UNDECIDED`` and the caller keeps the node's own, which is the behaviour this
    replaced and the safe direction: a looser expectation is a FALSE FAILURE that is
    visible, where a silently widened one is a pair that passes for nothing.
    """
    if node == conjunct:
        return node
    if keyword == "enum" and isinstance(node, list) and isinstance(conjunct, list):
        both = [member for member in node if _in_vocabulary(member, conjunct)]
        # An EMPTY intersection is a document that admits nothing at this node, which
        # is the emitter's refusal to make and not a fact to hand the comparison: the
        # node's own is kept so the pair reports rather than grading against a
        # vocabulary no instance satisfies.
        return both or _UNDECIDED
    if keyword in _TIGHTER_BOUND:
        if isinstance(node, bool) or isinstance(conjunct, bool):
            return _UNDECIDED  # draft-04's boolean exclusiveMinimum, a different keyword
        if not isinstance(node, int | float) or not isinstance(conjunct, int | float):
            return _UNDECIDED
        return _TIGHTER_BOUND[keyword](node, conjunct)
    return _UNDECIDED


def _composed(doc: Any, depth: int = 0) -> Any:
    """The document's node with every ``allOf`` conjunct's facts folded in.

    **``allOf`` conjoins, so a conjunct's unconditional facts ARE the
    document's.**  Draft-07 applies every conjunct to the whole instance, and a
    composing class flattens every inherited field into its own ``properties``
    and its own ``required`` -- so without this the two halves read the document
    differently and a FAITHFUL composing class reports as both dropping and
    adding facts.  Measured on a root stating ``required: ['label']`` beside a
    conjunct requiring ``kind``: ``/required`` differed, ``/properties/kind``
    read as added, and the conjunct's own ``maximum`` was compared against
    nothing -- 0 of the four cases in this module's own test set were graded
    right, including the one whose VERDICT looked right.

    Three rules, and each is the one the vocabulary forces:

    * **``required`` composes by union.**  It is a set of names and every
      conjunct contributes its own.
    * **``properties`` composes by key.**  A key two views declare is not merged
      here: the conjunct's declaration is stashed as an ``allOf`` on the merged
      node, and ``compare`` folds it by calling this function again when it
      descends.  One mechanism for composition at every depth rather than a
      second rule for properties.
    * **A CONSTRAINING fact two views state composes to the intersection**
      (:func:`_tighter`), and one only the conjunct states fills a gap.  That is
      §2 in its own words -- "an enum is the intersection of the members, a bound
      is the tighter one" -- and the keyword this function cannot order keeps the
      node's, which is a looser expectation and so a visible false failure rather
      than a pair that passes for nothing.
    * **A ``description`` two views state goes with the view that states the
      composed VALUE SET** (:func:`_described_by_the_conjunct`), which is §6's
      "a composed base's loses to the document's own" read where §2's
      intersection puts it.  **This bullet WAS the KNOWN CEILING and the ceiling
      is gone.**  It read "every other fact fills a gap and never overrides, the
      node's own declaration wins", measured over 61 of the 342 ``allOf``-root
      documents of the 3.2 bundle at a ROOT, where "the node winning is also the
      right answer" because at a root the node IS the document's own.  It is not
      the node at an OVERLAY: once the conjunct's ``properties`` and ``items``
      are stashed and folded on descent, the node at the descended pointer is
      the BASE's declaration and the stash is the document's own, so the polarity
      flips and the gap-fill graded the WIDER of two descriptions.  Re-measured
      over the whole graded tree rather than at roots alone: 2 sites where a
      conjunct both narrows the vocabulary and states a description of its own,
      3 where the NODE is the narrower view, 277 where neither narrows, and 0
      where the narrowing is a BOUND.

    **``if`` / ``then`` / ``else`` / ``not`` need no code and that is not an
    oversight.**  A conjunct holding only those states nothing unconditional
    about the value, and none of them is in ``compared_facts``, so such a conjunct
    contributes nothing by construction.  That is the dominant conjunct shape in
    the bundle: 352 ``if``/``then`` conjuncts against 21 that state
    ``properties``.

    **``anyOf`` / ``oneOf`` at a root are left alone, and must be.**  A branch's
    properties are satisfied by SOME branch, not by every instance, so folding
    one in the way a conjunct is folded would state a fact the document does not
    state.  What that costs is nothing here: a union root emits a base and one
    subclass per branch (§4), each naming its own node on ``__adcp_schema__``, so
    a branch is compared as a document in its own right by the pairing rather
    than through its parent.

    A ``$ref`` conjunct is not resolved here, and does not need to be: the
    caller hands this a RESOLVED document (``codegen.bundle.record`` writes it
    into the package and ``adcp.types._base.schema_at`` reads it back), and 0 of
    the conjuncts in that 61-document sample still carried a ``$ref``.  A
    conjunct that somehow did would state no fact in ``compared_facts`` and so fold to
    nothing, which is the pre-existing behaviour rather than a new hole.
    """
    conjuncts = doc.get("allOf") if isinstance(doc, dict) else None
    if not isinstance(conjuncts, list) or depth > _COMPOSE_DEPTH:
        return doc
    out = {k: v for k, v in doc.items() if k != "allOf"}
    for conjunct in conjuncts:
        if not isinstance(conjunct, dict):
            continue
        # The conjunct as the DOCUMENT writes it.  It was read through the delegated
        # resolver's finite-type rewrite and its one-member respelling first, because
        # that resolver dropped the ``type`` when it wrote a boolean out as
        # ``{"enum": [false, true]}`` and an inlined base's boolean then arrived here
        # typeless -- 9 facts over 5 ``formats/canonical`` documents, each restating an
        # inherited boolean, whose ``enum`` read as ``missing``.  ``bundle.record``
        # copies the base's ``{"type": "boolean"}``, so the conjunct arrives in the
        # document's own spelling and both undoings are deleted (§9).
        c = _composed(conjunct, depth + 1)
        # **The view that states the composed node's VALUE SET states its description**
        # (:func:`_described_by_the_conjunct`), read BEFORE the vocabulary axis
        # collapses: the collapse drops one of the two statements and this asks which
        # VIEW made the surviving one.  Written as a stand-down of the node's own rather
        # than as a second write, so the gap-fill below stays the one place a fact
        # crosses from a conjunct to the merged node.
        out = _described_by_the_conjunct(out, c)
        # One statement on the vocabulary axis before anything is gap-filled, so the
        # merged node cannot carry a ``const`` beside the ``enum`` it pins.
        out, c = _one_vocabulary(out, c)
        for kw in FOLDED_FACTS:
            if kw == "required" or kw not in c:
                continue
            if kw not in out:
                out[kw] = c[kw]
                continue
            # **Section 2's intersection rule, where the KNOWN CEILING below used to gap-fill
            # and keep the node's.**  "Where composed schemas constrain the same
            # property, the field carries the INTERSECTION, never the union: an enum is
            # the intersection of the members, a bound is the tighter one."  The ceiling
            # was measured as a population of zero at a root and is no longer zero:
            # ``core/audience-evidence-requirements.json`` at
            # ``/properties/maximum_age`` composes ``core/duration.json`` (whose ``unit``
            # is a five-member ``enum``) with a conjunct narrowing ``unit`` to four, and
            # the node that KEPT the five read as the document stating a vocabulary the
            # faithful model does not -- 1 ``differs`` at the node and 1 at its parent.
            #
            # Derived HERE and not imported from ``codegen.compiler``, which carries the
            # same rule for the model side.  The shared alternative is tempting and is
            # the hazard this comparison exists to avoid: one body of code deciding what
            # the model states AND what the document states agrees with itself by
            # construction, so a defect in it is green on both sides.  ``_normalize``'s
            # both-sided sharing is not the same thing -- that is one reading of one
            # DOCUMENT serving two inputs, where this would be one reading serving the
            # product and its own grader.
            narrower = _tighter(kw, out[kw], c[kw])
            if narrower is not _UNDECIDED:
                out[kw] = narrower
        req = c.get("required")
        if isinstance(req, list):
            have = out["required"] if isinstance(out.get("required"), list) else []
            out["required"] = [*have, *(k for k in req if k not in have)]
        props = c.get("properties")
        if isinstance(props, dict):
            mine = dict(out["properties"]) if isinstance(out.get("properties"), dict) else {}
            for name, sub in props.items():
                node = mine.get(name)
                if isinstance(node, dict):
                    pending = node["allOf"] if isinstance(node.get("allOf"), list) else []
                    mine[name] = {**node, "allOf": [*pending, sub]}
                else:
                    mine[name] = sub
            out["properties"] = mine
        # ``items`` composes the way ``properties`` does, by the SAME mechanism: the
        # conjunct's declaration is stashed as an ``allOf`` on the merged node and this
        # function folds it when the comparison descends.  It gap-filled instead, so an
        # overlay narrowing an array's element kept the WIDER element -- measured on
        # ``core/media-buy-frequency-cap-requirement.json`` at
        # ``/properties/supported_control_modes``, whose conjunct narrows the element
        # from a three-member enumeration to one, reported as the model adding a
        # ``const`` and dropping an ``enum``.  Section 2: the intersection holds at any depth,
        # INCLUDING an overlay under ``items``.
        if isinstance(c.get("items"), dict):
            mine_items = out.get("items")
            if isinstance(mine_items, dict):
                pending = mine_items["allOf"] if isinstance(mine_items.get("allOf"), list) else []
                out["items"] = {**mine_items, "allOf": [*pending, c["items"]]}
            else:
                out["items"] = c["items"]
    return out


def compare_schema(
    schema: dict,
    model: Any,
    *,
    document: dict | None = None,
    position: Position = Position.ROOT,
    declared: Sequence[Approximation] = (),
    at: str = "#",
) -> ComparisonResult:
    """The document's facts and the model's, compared in BOTH directions.

    ``document`` is the WHOLE resolved document ``schema`` is a node of, and it is
    what a local ``$ref`` on the document side resolves against.  It defaults to
    ``schema``, which is exactly right for a root pair and FAIL-SAFE for a nested
    one: with no root supplied a ``#/definitions/x`` does not resolve, the node
    states only its own annotations, and every fact the model carries reads as
    ``added`` -- the pair reddens instead of passing blind.

    * ``missing`` / ``differs`` -- the document states a fact and the model
      states nothing, or something else.  That is a model WIDER than its
      document, which neither the accepts nor the refuses check can see once the
      entry point validates the schema first.
    * ``added`` -- the model states a fact and the document does not.  That is a
      model NARROWER than its document.

    **This was one-directional, and that was a hole of the same shape as the one
    it was built to close.**  Measured: a model declaring ``min_length=1`` and
    ``pattern="^x"`` on a property whose document says only
    ``{"type": "string"}`` produced a report byte-identical to a faithful
    model's -- 4 facts compared, nothing missing, nothing differing, ``pass``.

    The accepts check is supposed to catch that, and for a CONSTRAINT it does:
    it draws an instance the document admits and the narrower annotation refuses
    it (measured on the same probe: ``model_refused_valid`` at
    ``greater_than_equal``).  It does not catch a narrowing that comes from a
    ``format``, because ``hypothesis_jsonschema`` honours the format when
    generating -- 200 of 200 instances carried a UTC offset for
    ``format: date-time``.  So for ``format`` there was no check at all in
    either direction, and ``AnyUrl`` passed for the wrong reason: it renders a
    ``minLength: 1`` its document does not state.

    ``title`` is in neither direction: pydantic derives one for every class and
    every property, so it is a name the compiler makes up rather than a fact
    about a value.  The one other systematic model-only fact is D4's rendering
    of absence, and ``_narrows_nothing`` says exactly which and why.

    **``declared`` and ``at`` are section 8's fifth and sixth outcomes.**  ``declared`` is
    section 7's declaration read off the artifact (:func:`declarations_of`) and ``at`` is
    the pair's own pointer, which is what the declaration's absolute pointer is relative
    to.  Under section 2 every unexpressed keyword widens instead of refusing, so "the
    *missing* bucket would fill with facts the design decided to drop, and a grader that
    cannot tell a decided widening from a defect grades nothing".  The split is made HERE,
    at the one place a fact is found absent, so there is no second traversal and no second
    reading of what the document states.

    **Nothing is loosened by it, and the direction is the whole of why**: *missing* keeps
    its old meaning exactly -- the document states a compared fact and NOTHING declares its
    absence -- so a pair with no declaration grades byte-identically to before.  What is
    added is the other direction: a declaration at a pointer and keyword the model DOES
    state is *over-declared*, which is a defect the comparison could not previously see at
    all.
    """
    res = ComparisonResult()
    facts = declared_facts(declared, at)

    def declaration(pointer: str, kw: str) -> Approximation | None:
        """The declaration for this fact, pair-relative, or ``None``."""
        return facts.get((pointer, kw))

    def approximated(one: Approximation, where: str, what: Any) -> None:
        res.approximated.append(
            f"{where}: the document says {what!r} and the model nothing; approximated at "
            f"rung {one.rung} ({one.kind}), {one.attribution}"
        )
        res.approximated_at.append(site_of(one))

    def over_declared(one: Approximation, where: str, what: Any) -> None:
        res.over_declared.append(
            f"{where}: declared approximated at rung {one.rung} ({one.attribution}) and "
            f"the model states {what!r}; a declaration that outlives its widening hides "
            "the next real gap at the same pointer"
        )
    try:
        emitted = (
            model.model_json_schema()
            if isinstance(model, type) and hasattr(model, "model_json_schema")
            else TypeAdapter(model).json_schema()
        )
    except Exception as e:  # a model whose schema cannot be built states nothing
        res.detail = f"{type(e).__name__}: {e}"[:300]
        return res
    #: The two roots a ``$ref`` resolves against, one per side.  Captured here and
    #: not threaded through ``compare``, because they are properties of the PAIR and
    #: do not change as the recursion descends -- a ``#/definitions/x`` three levels
    #: into a node is still relative to the document root.
    root = document if isinstance(document, dict) else schema

    def compare(
        doc: Any,
        got: Any,
        pointer: str,
        at_position: Position,
        *,
        required: bool = False,
    ) -> None:
        """``at_position`` is this node's POSITION, and ``required`` is whether the
        PARENT document demands this key.

        The position decides the compared set (:func:`compared_facts`), and it is a
        PARAMETER at every recursion because each descent knows it structurally: a
        value of ``properties`` is at PROP, an ``items`` at ELEM, a typed
        ``additionalProperties`` at MAPV, a ``propertyNames`` at KEY.  Deriving it from
        ``pointer`` instead would be the reading §11 names as a repetition, and a
        pointer cannot tell a RULE node from a PROP one.

        Two of this function's decisions need it and neither can derive it from the
        node: ``_narrows_nothing`` asks it of a model-only ``default``, and a
        non-property position (a root, an ``items``, a mapping's value) has no
        presence question at all, which is what the ``False`` default states.
        """
        if not isinstance(doc, dict):
            return
        # The document side is read the way the schema half reads it: a conjunct's
        # facts are the document's (see `_composed`).  At every node, not only at
        # the root -- a property's own node composes too, and the pydantic side is
        # flattened at every depth, so one call in the recursion is the whole of it.
        # ONE instrument, both sides.  The document's node is normalized FIRST and
        # by the same function: a local ``$ref`` is resolved against the document
        # root and a union of types is folded to the type list it spells, because
        # the document uses those two spellings too and reading them on one side
        # only reported a faithful class as NARROWER than its own document -- 43
        # ``added`` facts for the reference and 9 for the folds, measured
        # (salesagent-j3k2l.32, .33).  ``_normalize`` before ``_composed`` so a
        # reference whose TARGET composes still has its conjuncts folded.
        #
        # ``declared_null=True`` on this side is not a guess read off anything: a
        # DOCUMENT has no other way to spell a nullable value at a node, because
        # presence is ``required`` at the parent.  A null BRANCH here is therefore
        # always a type fact, which is what makes the fold lossless and what keeps a
        # model that drops the null reportable.
        doc = _composed(_normalize(doc, root, declared_null=True))
        # The DOCUMENT decides whether a null branch on the model's side is a type
        # fact or D4's spelling of absence, so the document is read first and the
        # model's node is normalized against it.
        got = _normalize(
            got, emitted, declared_null=_declares_null(doc), null_is_absence=not required
        )
        # §2's key rule: a mapping's key is a TYPE, and the one type has three
        # spellings across the two sides.  Written as one shape here, on BOTH sides
        # and by the same function, so the key expression and the value schema are
        # each graded rather than excused (:func:`_patterned_key`).  ``closed`` is
        # the one fact that differs by side and it is a property of the renderer,
        # not of the node.
        doc = _patterned_key(doc, closed=False) or doc
        got = _patterned_key(got, closed=True) or got
        # A MAPPING's ``additionalProperties: true`` is the silence it is, on BOTH sides
        # and by the one function -- §9's "the readings this pipeline's own output
        # forces", of which §4's ``dict[K, V]`` rendering is one
        # (:func:`_silent_about_extras`).  AFTER ``_composed`` and ``_patterned_key``, so
        # a conjunct's gap-filled value and a patterned key's synthesised one are read
        # the same way the node's own is.
        doc, got = _silent_about_extras(doc), _silent_about_extras(got)
        for kw in compared_facts(at_position):
            if kw not in doc:
                continue
            res.compared += 1
            where = f"{pointer}/{kw}"
            if kw not in got:
                # D5's URL-type row, and its own counter: the schema half enforces
                # this keyword and the annotation does not restate it.  Counted as
                # ``compared`` above, because the fact WAS looked for.
                if _schema_half_enforces(kw, doc, got):
                    res.url_typed.append(
                        f"{where}: the document says {doc[kw]!r}; the model is a URL type "
                        "and the schema half enforces it"
                    )
                    continue
                # A document fact that constrains nothing is not dropped by a model
                # that omits it.  Counted apart from ``missing`` so the fold stays
                # auditable at its positions.
                if _constrains_nothing(kw, doc, required=required):
                    res.constrains_nothing.append(
                        f"{where}: the document says {doc[kw]!r}, which admits exactly "
                        "what its absence admits"
                    )
                    continue
                # **Section 8's fifth outcome, and the ONE place *missing* splits.**  The
                # fold rows above come first on purpose: each says the model omitting the
                # keyword is not a drop AT ALL, so a declaration there would be
                # over-declared rather than approximated, and reading the declaration
                # first would excuse a fact nothing dropped.
                one = declaration(pointer, kw)
                if one is not None:
                    approximated(one, where, doc[kw])
                    continue
                res.missing.append(f"{where}: the document says {doc[kw]!r}")
                continue
            # The model DOES state it, so a declaration here has outlived its widening.
            stale = declaration(pointer, kw)
            if stale is not None:
                over_declared(stale, where, got[kw])
            a, b = doc[kw], got[kw]
            if kw == "additionalProperties":
                if isinstance(a, dict) and a and isinstance(b, dict):
                    # A TYPED ``additionalProperties`` is a subschema, so it is
                    # compared the way ``items`` is -- recursively, with the model's
                    # side normalized -- and not as an opaque value.  Step 6's
                    # mapping row makes the model's side a local class, which
                    # pydantic renders ``{"$ref": "#/$defs/..."}``: comparing the
                    # two as values reports a difference that is a SPELLING, while
                    # the facts inside the value schema go ungraded.  Measured on
                    # ``error-details/vendor-error-codes.json``, whose two nested
                    # mappings reported ``model_drops_a_fact`` for a model stating
                    # exactly what its document states; recursing instead grades the
                    # value's own ``type``, ``required`` and ``enum``.
                    compare(a, b, f"{where}", Position.MAPV)
                    continue
                # ``_closed`` stood here and is DELETED WITH THE DELEGATED RESOLVER
                # (§9): it read ``{"not": {}}`` as the ``false`` it is, which the
                # resolver wrote while inlining a closed object.  0 raw nodes of the
                # bundle spell a closed object that way, so with ``bundle.record``
                # copying the document's own ``false`` there is nothing to fold, and a
                # ``{"not": {}}`` a document itself ever states is a fact to compare.
            elif kw == "description":
                a, b = _text(a), _text(b)
            elif kw in ("required", "enum"):
                a, b = sorted(map(repr, a or [])), sorted(map(repr, b or []))
            elif kw == "type" and (isinstance(a, list) or isinstance(b, list)):
                a = sorted(a) if isinstance(a, list) else [a]
                b = sorted(b) if isinstance(b, list) else [b]
            if a != b:
                res.differs.append(f"{where}: the document says {doc[kw]!r}, the model {got[kw]!r}")
        for kw in compared_facts(at_position):
            if kw in doc or kw not in got:
                continue
            res.model_facts += 1
            # The two ``rewritten`` arms stood here and are DELETED WITH THE DELEGATED
            # RESOLVER (§9): that resolver dropped the node's annotations when it wrote
            # a finite type out as its members, so a faithful model stated a
            # ``description`` and a ``default`` its own resolved document no longer did
            # -- ``core/canonical-projection-slot-override.json``'s two booleans state
            # ``default: true`` and ``default: false`` and their resolved nodes stated
            # neither.  ``bundle.record`` copies both, so both are COMPARED, which is
            # the stronger grade in each direction.
            #
            # D5's URL-type rows for the facts a URL type ADDS, one row per fact,
            # each naming itself and each gated on its own exact value
            # (:data:`URL_IMPLIED`).  ``minLength: 1`` is rendered by every pydantic
            # URL type and ``maxLength: 2083`` by ``HttpUrl``, which D5 selects at
            # every ``uri`` position whose document does not restrict the scheme to
            # https; no document in the bundle states either at such a node.
            #
            # TWO ROWS AND NOT ONE WIDENED ROW, deliberately: a rule reading "a bound
            # on a URL type is admitted" would admit a third bound nobody decided,
            # invisibly and for good. These admit these two values and nothing else,
            # so a model stating any other bound is still reported.
            if (
                kw in URL_IMPLIED
                and got[kw] == URL_IMPLIED[kw]
                and _url_typed(got)
                and doc.get("format") == "uri"
            ):
                res.url_typed.append(
                    f"{pointer}/{kw}: the model says {URL_IMPLIED[kw]}, which "
                    + ("any URL type renders" if kw == "minLength" else "HttpUrl renders")
                )
                continue
            if _narrows_nothing(kw, got[kw], doc, required=required):
                continue
            # A declaration where the DOCUMENT states nothing is over-declared too, and
            # for a second reason: section 9's "never approximate on a keyword the walk
            # itself inserted" -- "an approximation must name something the document
            # states, or the document is blamed for the compiler's own rewriting".  Here
            # the document states nothing at all, so the declaration names no fact.
            invented = declaration(pointer, kw)
            if invented is not None:
                over_declared(invented, f"{pointer}/{kw}", got[kw])
            res.added.append(f"{pointer}/{kw}: the model says {got[kw]!r}, the document nothing")

        props = doc.get("properties") or {}
        mine = got.get("properties") if isinstance(got.get("properties"), dict) else {}
        demanded = doc.get("required") if isinstance(doc.get("required"), list) else []
        if isinstance(props, dict):
            for key in sorted(props):
                into = f"{pointer}/properties/{_esc(key)}"
                if key not in mine:
                    res.compared += 1
                    # A property the model does not declare is the ``properties``
                    # keyword's own fact and the comparison reports it per KEY, so the
                    # declaration that covers it is the one at this node for
                    # ``properties`` -- section 5's CONTAINER rung, where an object
                    # whose declared fields cannot be rendered is its bare container.
                    # The declaration is keyed by (pointer, keyword) and this is the
                    # pointer and the keyword the document states it at.
                    one = declaration(pointer, "properties")
                    if one is not None:
                        approximated(one, into, props[key])
                        continue
                    res.missing.append(f"{into}: the model declares no such property")
                    continue
                compare(props[key], mine[key], into, Position.PROP, required=key in demanded)
        for key in sorted(set(mine) - set(props)):
            res.model_facts += 1
            res.added.append(
                f"{pointer}/properties/{_esc(key)}: the document declares no such property"
            )
        if isinstance(doc.get("items"), dict):
            compare(doc["items"], got.get("items"), f"{pointer}/items", Position.ELEM)
        # A mapping's KEY SCHEMA, descended into the way ``items`` is -- it is a
        # schema at a pointer the document names, and §2 makes it a type, so the
        # facts it states are the key type's and are graded as such.  Ungraded
        # before this row: ``propertyNames`` is in neither ``compared_facts`` nor any
        # descent, so a model that widened a bounded key to ``str`` compared
        # identically to one that carried the bound.
        key_doc, key_got = doc.get("propertyNames"), got.get("propertyNames")
        if isinstance(key_doc, dict) and isinstance(key_got, dict):
            compare(
                _key_schema(key_doc),
                _key_schema(key_got),
                f"{pointer}/propertyNames",
                Position.KEY,
            )
        elif isinstance(key_doc, dict) and _constrains_a_key(key_doc):
            res.compared += 1
            if _extra_key_typed(doc, got):
                res.extra_key_typed.append(
                    f"{pointer}/propertyNames: the document says {key_doc!r}; the model "
                    "types the key of a __pydantic_extra__ store, which pydantic enforces "
                    "and does not render"
                )
            elif (one := declaration(pointer, "propertyNames")) is not None:
                approximated(one, f"{pointer}/propertyNames", key_doc)
            else:
                res.missing.append(
                    f"{pointer}/propertyNames: the document says {key_doc!r}, "
                    "the model states no key schema"
                )
        elif isinstance(key_got, dict) and _constrains_a_key(key_got):
            res.model_facts += 1
            res.added.append(
                f"{pointer}/propertyNames: the model says {key_got!r}, the document nothing"
            )

    compare(schema, emitted, "", position)
    return res


# --------------------------------------------------------------------------- #
# the pair, and one entry point over a sequence of them
# --------------------------------------------------------------------------- #
@dataclass
class Pair:
    """One graded unit: a name for reporting, a resolved document, a model, and
    the entry point the caller says an instance is offered through."""

    name: str
    schema: dict
    model: Any
    accept: Callable[[Any], Any]
    #: The WHOLE resolved document ``schema`` is a node of, which only the schema
    #: comparison reads and only to resolve a local ``$ref`` on the DOCUMENT side.
    #:
    #: **A second field and not a wider ``schema``, because they answer different
    #: questions.**  ``schema`` is what the pair is GRADED against -- the node the
    #: class names, which is what the accepts and refuses checks must draw
    #: instances from.  The root is only the scope a ``#/definitions/x`` is
    #: relative to, and a nested pair's node does not contain it: measured on
    #: ``core/bidding-policy-capability.json``, whose
    #: ``#/definitions/scope_capability`` pair references
    #: ``#/definitions/policy_profile``, a SIBLING in the root's own
    #: ``definitions`` section.
    #:
    #: ``None`` means "the node is the root", which is true of a root pair and
    #: FAIL-SAFE for a nested one -- see :func:`compare_schema`.
    document: dict | None = None

    #: WHICH document and pointer this node is, for ``codegen.dump_exemptions``.
    #:
    #: **A stated field and not a read off ``model``, because the two are not the
    #: same fact for every pair.**  D2's root-scalar row is graded as an ALIAS: the
    #: model is an ``Annotated`` and the ``__adcp_schema__`` is on its MODULE, so
    #: ``pair.model.__adcp_schema__`` answers for a class and raises for an alias.
    #: ``pair.accept.__self__`` reaches it for a class too and is worse -- it makes
    #: the dependency invisible in the signature, which is the thing a signature is
    #: for.
    #:
    #: ``None`` is FAIL-SAFE in the direction that matters: a caller grading a bare
    #: node supplies none, ``dump_exemptions.applying_to`` then matches nothing, and
    #: the dump is validated against the node as it stands.  An absent ref loses an
    #: exemption; it can never invent one.
    ref: SchemaRef | None = None

    #: **Section 7's approximation declaration for this pair's own artifact.**
    #:
    #: A stated field for :attr:`ref`'s exact reason, and it is the same reason: section 7
    #: puts the declaration "onto the class, the root model or the enumeration, and beside
    #: the MODULE for an alias", so ``pair.model.__adcp_approximations__`` answers for a
    #: class and does not exist for an alias.  :func:`declarations_of` is the reader for
    #: both -- the caller says which object holds it and this module does the reading, so
    #: section 9's "the verifier reads the declaration off the class, as a consumer" stays
    #: true of the code that grades it.
    #:
    #: ``()`` is FAIL-SAFE in the direction that matters: a caller grading a bare node
    #: supplies none, every unexpressed fact reads as *missing*, and the pair reddens
    #: rather than passing on a declaration nobody handed it.
    declared: tuple[Approximation, ...] = ()


@dataclass
class PairReport:
    name: str
    model_repr: str = ""
    accepts: AcceptsResult | None = None
    liveness: LivenessResult | None = None
    comparison: ComparisonResult | None = None
    #: Section 8's accepts obligation for this pair's declarations, and ``None`` where the
    #: pair declares nothing -- which is every pair of the tree at section 14 step 8.
    #: ``None`` and not an empty result, so ``outcome`` can tell "nothing was claimed" from
    #: "a claim was checked", the way it already tells ``accepts:unrun`` from a pass.
    widening: WideningResult | None = None
    missing_formats: list[str] = field(default_factory=list)
    #: The DOCUMENT's own format-beside-pattern positions a draw CANNOT REACH, each
    #: measured by drawing that node alone (:func:`undrawable_formats`).  Filled by
    #: :func:`check_pair` because a report does not hold the document it graded, and
    #: filled only where the accepts check errored, because that is the only pair it
    #: says anything about.  Read by :attr:`no_instrument` to name the shape behind an
    #: accepts check that could not draw.
    accepts_undrawable: tuple[str, ...] = ()

    @property
    def graded_instances(self) -> int:
        """How many instances reached the class and came back out through its dump.

        The one denominator this harness has, and it is the accepts check's: an
        instance is drawn, constructed, dumped, and the document decides on the
        dump.  A pair reporting zero here was never exercised by an instance at
        all, which :attr:`outcome` turns into a refusal rather than a pass.
        """
        return self.accepts.round_tripped if self.accepts is not None else 0

    @property
    def no_instrument(self) -> tuple[str, ...]:
        """Every check of this pair that could not DRAW, with its CAUSE.

        **Tracking, with no ratchet on it, and that is the decision rather than an
        omission.**  A shrink-only count assumes a fixed or shrinking population and
        the emitted tree GROWS every merge, so each new batch of documents can
        legitimately contribute new undrawable pairs and a shrink-only gate would
        redden on correct work.  It can only shrink once ``hypothesis`` draws these
        shapes, which is unscheduled, so shrink-only is unachievable in principle and
        not merely premature.

        **The CAUSE matters more than the count**, because this is the population the
        eventual generator work starts from, so the entry names a shape to act on
        rather than "cannot draw": hypothesis's own message -- which carries the
        filtered-draw count -- beside the document's own positions a draw cannot
        reach, because that is the shape ``hypothesis_jsonschema``'s ``string_schema``
        filters and cannot satisfy.  The positions are DERIVED from the document, not
        guessed: hypothesis raises over the whole schema and names no node.

        **They are the MEASURED positions and not the co-occurrences**
        (:func:`undrawable_formats`), and the difference is this exit's whole
        admissibility: 72 of the bundle's 73 format-beside-pattern positions draw, so
        an entry naming every co-occurrence would speak for a ``strategy_error`` from
        any cause at all in a document that happens to state the two keywords
        somewhere.

        **So this is EMPTY where no position of the document is undrawable, and that
        is the refusal rather than a gap.**  A generator failure nothing explains has
        no admitted exit: :attr:`outcome` reads this and reports
        ``accepts:strategy_error``, which is a verdict on the pair.
        """
        if self.accepts is None or self.accepts.outcome != "strategy_error":
            return ()
        if not self.accepts_undrawable:
            return ()
        return (f"accepts: {'; '.join(self.accepts_undrawable)}; {self.accepts.detail}",)

    @property
    def outcome(self) -> str:
        """One verdict for the pair, and **a zero denominator is a refusal**.

        Structural here rather than a convention a caller is trusted to apply,
        because a report can enforce it and a reader cannot.  What it guards is a
        pair no instance reached: an entry point raising an exception this module
        does not catch leaves the accepts check with nothing round-tripped.

        The order is the same one it always had, and for the same reason: a MODEL
        defect outranks an INSTRUMENT one, so the comparison is read before
        ``no_instrument``, and the zero-denominator exits come last so a pair whose
        generator produced nothing names that instead of "nothing was graded".

        **``no_instrument`` is ADMITTED only where a measured position explains the
        generator's failure**, which is ``salesagent-j3k2l.10``'s decision made
        structural: the shape is the designed exit, so a ``strategy_error`` nothing
        identifies as that shape falls through to ``accepts:strategy_error`` and is a
        verdict on the pair like any other accepts outcome.
        """
        if self.missing_formats:
            return "missing_formats"
        if self.accepts is None:
            return "accepts:unrun"
        # ``strategy_error`` is held back here and answered by ``no_instrument``
        # below: it says the GENERATOR produced nothing, which is not a verdict on
        # the model.  Every other accepts outcome is a verdict and still wins.
        if self.accepts.outcome not in ("pass", "strategy_error"):
            return "accepts:" + self.accepts.outcome
        if self.liveness is None:
            return "liveness:unrun"
        if self.liveness.outcome not in ("pass", "no_payload"):
            return "liveness:" + self.liveness.outcome
        # Section 8's accepts obligation, ranked with the accepts check it is part of and
        # BELOW it: a model that refuses a drawn instance outright is a verdict about the
        # whole pair, where this is a verdict about one declaration's claim.  Above the
        # comparison, because "an approximation that still refuses a value the document
        # admits is a NARROWING wearing a declaration" and a narrowing outranks a
        # bookkeeping disagreement about what was declared.
        if self.widening is not None and self.widening.outcome not in ("pass", "no_declarations"):
            return "widening:" + self.widening.outcome
        if self.comparison is None or self.comparison.outcome not in ("pass", "no_evidence"):
            return "comparison:" + (self.comparison.outcome if self.comparison else "unrun")
        if self.accepts.outcome == "strategy_error":
            return "no_instrument" if self.no_instrument else "accepts:strategy_error"
        if not self.graded_instances:
            return "no_accepts_check_evidence"
        return "pass"


# --------------------------------------------------------------------------- #
# section 8's TWO EQUALITIES, over the run
# --------------------------------------------------------------------------- #
@dataclass
class Census:
    """**Section 8's second equality**: the approximated set equals the declared set.

    "Every *approximated* fact has a declaration (or it is *missing*), and every
    declaration has an *approximated* fact (or it is *over-declared*).  Both directions,
    for the reason the first equality has them: a set checked in one direction is complete
    with respect to itself, and what it omits passes."

    **Two sets a machine derives, and neither is hand-written.**  ``declared`` is read off
    the emitted artifacts -- what the emitter recorded it could not render -- and
    ``approximated`` is what the comparison found absent from a model and present in its
    document.  Section 8: "Nobody can add an entry to make a failure go away without the
    model actually widening at that pointer, because the accepts draw then has to accept
    the values the keyword distinguishes.  A declaration is a claim with two instruments
    pointed at it."

    **Over the RUN and not over one pair**, and that is forced.  ``render.declared_at``
    carries a declaration on every artifact whose node contains it, so a declaration under
    a root union's ``#/oneOf/0`` sits on the base as well as on the branch -- and the
    base's own comparison never descends a combinator, so at that pair the declaration is
    neither *approximated* nor *over-declared*.  Per pair the equality would therefore
    fail on a correct tree; over the union of the pairs the branch reports it and the
    equality is exact.
    """

    #: Every site any artifact declares, with the declaration -- the emitter's own record
    #: of what it could not render, read off the tree.
    declared: dict[Site, Approximation] = field(default_factory=dict)
    #: Every site the comparison reported *approximated* at, over every pair.
    approximated: set[Site] = field(default_factory=set)
    #: Sites declared and never reported approximated: the equality's failing direction.
    #: A defect, and section 8's *over-declared* -- either the model states the fact (and
    #: the pair that visited it says so) or no pair's comparison reached the pointer at
    #: all, which is a declaration nothing grades.
    undeclared_widenings: list[str] = field(default_factory=list)
    #: Every *over-declared* line the pairs reported, carried through so one object
    #: answers for the whole equality.
    over_declared: list[str] = field(default_factory=list)
    #: An attribution whose issue reference ``codegen.attribution`` does not hold, which
    #: section 9's grader row names: "an upstream attribution's issue | ``attribution.py``'s
    #: own test | an entry with no issue is a ``BuildFailure``".
    unattributed: list[str] = field(default_factory=list)

    @property
    def stale(self) -> list[Site]:
        """The declared sites with no approximated fact, as sites."""
        return sorted(set(self.declared) - self.approximated)

    @property
    def outcome(self) -> str:
        if self.over_declared or self.undeclared_widenings or self.unattributed:
            return "the declared set and the approximated set disagree"
        return "pass"

    @property
    def documents(self) -> int:
        """How many DOCUMENTS carry at least one approximation.

        A different figure over a different denominator from ``len(approximated)``, and
        section 2 says the two are never added: "The number of documents carrying at least
        one is a different figure over a different denominator, and the two are never
        added."
        """
        return len({document for document, _, _ in self.declared})


def census(graded: Sequence[tuple[Pair, PairReport]]) -> Census:
    """The second equality, computed over every pair of a run.

    ``graded`` is the pairs and their reports, which is the whole of what the equality
    needs: the DECLARED half is ``pair.declared`` -- read off the artifact by
    :func:`declarations_of` -- and the APPROXIMATED half is
    ``report.comparison.approximated_at``.  Neither is a set this function writes.

    The first equality of section 8 -- "the comparison's keyword set equals the set the
    declaration renders" -- is not here: it is a property of ``compared_facts`` and
    ``keywords.rendered_at``, so ``tests/test_every_check_names_its_set.py`` holds it over
    the declaration directly, which is where a set equality between two derivations
    belongs.
    """
    out = Census()
    for pair, report in graded:
        for one in pair.declared:
            out.declared[site_of(one)] = one
        if report.comparison is None:
            continue
        out.approximated |= set(report.comparison.approximated_at)
        out.over_declared += [f"{pair.name}: {line}" for line in report.comparison.over_declared]
    for site in out.stale:
        one = out.declared[site]
        out.undeclared_widenings.append(
            f"{one.document}{one.pointer}/{one.keyword}: declared approximated at rung "
            f"{one.rung} ({one.attribution}) and no pair's comparison reported the fact "
            "absent from a model -- either the model states it, or no pair graded that "
            "pointer, and both are a declaration nothing earns"
        )
    out.unattributed = unattributed(out.declared.values())
    return out


def unattributed(declared: Sequence[Approximation] | Any) -> list[str]:
    """Every declaration whose attribution names neither a cell nor a live issue.

    Section 2's attribution "is a choice of two and not a free-text note", and this is
    where that bites on the artifact: an ``Ours`` attribution is the cell's own address, so
    it is ``keywords.address`` of the keyword and nothing else; an ``Upstream`` one is an
    entry of ``codegen.attribution``'s registry, so the site has to be in it.  A string
    that is neither is a free-text note wearing an attribution.

    This is the verifier's half of section 9's grader row.  ``attribution.py``'s own test
    holds the other half -- that an entry with no issue cannot exist -- and the two are
    different claims: that one is about the REGISTRY, this is about what an artifact says
    it read out of it.
    """
    out: list[str] = []
    for one in declared:
        issue = attribution.issue_for(one.document, one.pointer, one.keyword)
        expected = issue.attribution if issue is not None else keywords.address(one.keyword)
        if one.attribution != expected:
            out.append(
                f"{one.document}{one.pointer}/{one.keyword}: the artifact says "
                f"{one.attribution!r} and the declaration says {expected!r}; section 2 "
                "makes the attribution a choice of two -- the cell's own address, or an "
                "entry of codegen.attribution -- and never a free-text note"
            )
        if one.rung not in set(Rung):
            out.append(
                f"{one.document}{one.pointer}/{one.keyword}: rung {one.rung!r} is not one "
                f"of section 2's ladder, {[r.value for r in Rung]}"
            )
        if one.kind not in KINDS:
            out.append(
                f"{one.document}{one.pointer}/{one.keyword}: kind {one.kind!r} is not one "
                f"of section 2's two, {list(KINDS)}"
            )
    return out


# --------------------------------------------------------------------------- #
# the UNDERDETERMINED equality: the one approximation no check above can see
# --------------------------------------------------------------------------- #
#: The combinators whose branches a union's dispatch has to separate, DERIVED from the
#: declaration: ``keywords.combinators`` is "the keywords whose subschemas occupy a BRANCH,
#: which is what a combinator IS -- so the pair is a reading of the declaration and not a
#: literal".  Section 9's rule that nothing under ``codegen/`` names a keyword in a set
#: literal holds of the verifier too, and section 9's own permitted import is what makes it
#: possible: the keyword table is "the declared semantics, and both halves must read the
#: same declaration or the grade means nothing".
#:
#: At ROOT, because a union's branches are read under the enclosing node's own position and
#: ROOT is where the derivation enters; the pair is the same at every position the table
#: gives one.
_COMBINATORS = tuple(sorted(keywords.combinators(Position.ROOT)))


#: The keywords whose subschema sits at RULE, DERIVED from the descent column rather than
#: named: ``keywords.descends_at`` is "the ONE descent table, where today there are three",
#: and a keyword holding a RULE subschema is exactly what a conditional is.  Section 11
#: names the three descent tables as a repetition with one owner, and the verifier's own
#: walk of the record is one of the three readers section 3 gives that column.
_RULE_KEYWORDS = tuple(
    sorted(k for k, p in keywords.descends_at(Position.ROOT).items() if p is Position.RULE)
)


def _rule_free_nodes(schema: Any, pointer: str = "") -> list[tuple[str, dict]]:
    """Every dict node of the document that is NOT under a conditional, with its pointer.

    :func:`_nodes` with one difference, and the difference is a POSITION carried by the
    descent: a subschema reached through ``if``, ``then``, ``else`` or ``not`` is at RULE,
    and section 3 of the semantics document says no type is lowered from a RULE node -- so
    the subtree has no declaration for a derivation over declarations to range over.

    Not a filter over :func:`_nodes`' pointers, deliberately: section 6 of the
    architecture document makes deriving position from a pointer string the repetition
    section 11 names, and "a pointer cannot tell a RULE node from a PROP one" in general --
    a document may hold a property literally named ``then``.  The descent knows it
    structurally, so the descent is what carries it.
    """
    out: list[tuple[str, dict]] = []
    if isinstance(schema, list):
        for i, v in enumerate(schema):
            out += _rule_free_nodes(v, f"{pointer}/{i}")
        return out
    if not isinstance(schema, dict):
        return out
    out.append((pointer or "/", schema))
    for k, v in schema.items():
        if k in _RULE_KEYWORDS:
            continue  # at RULE: no type is lowered from here (semantics §3)
        if k in _DESCEND_MAP and isinstance(v, dict):
            for kk, vv in v.items():
                out += _rule_free_nodes(vv, f"{pointer}/{k}/{_esc(kk)}")
        elif k in _DESCEND_ONE and isinstance(v, (dict, list)):
            out += _rule_free_nodes(v, f"{pointer}/{k}")
        elif k in _DESCEND_LIST and isinstance(v, list):
            out += _rule_free_nodes(v, f"{pointer}/{k}")
    return out


def _pins(node: Mapping[str, Any]) -> dict[str, Any]:
    """Each property this branch pins to a single value, by key.

    A one-member ``enum`` is a ``const`` -- section 5's ``enum`` row says so of the model
    side and draft-07 says so of the document -- so both spellings are read, which is the
    whole of what the first separator needs.
    """
    out: dict[str, Any] = {}
    for key, declaration in (node.get("properties") or {}).items():
        if not isinstance(declaration, dict):
            continue
        if "const" in declaration:
            out[key] = declaration["const"]
        elif isinstance(declaration.get("enum"), list) and len(declaration["enum"]) == 1:
            out[key] = declaration["enum"][0]
    return out


def _forbids(node: Mapping[str, Any]) -> frozenset[str]:
    """The names ``node`` forbids ONE AT A TIME, read off its ``not`` over ``required``.

    **A second spelling of ``codegen.lower.rules``' reduction, over the DOCUMENT**, for
    the reason :func:`separates` is one of the walk's: a verifier that asked the walk
    which names a branch forbids would compare the walk's answer with itself.

    ``not: {"required": [n]}`` says ``n`` is not present.  ``not`` over an ``anyOf`` of
    those says none of them is -- "not (a or b)" is "not a and not b" -- and over an
    ``allOf`` of them says the same, because every member asserts the presence of its own
    name.  A group of MORE than one name forbids no single name: "not (a and b)" leaves
    either one present, so a longer group is read and contributes nothing, which is the
    same distinction ``adcp.types._runtime.ForbiddenGroups`` draws between its shapes.
    """
    found: set[str] = set()

    def groups(sub: Any) -> None:
        if not isinstance(sub, Mapping):
            return
        names = sub.get("required")
        if isinstance(names, list) and len(names) == 1 and isinstance(names[0], str):
            found.add(names[0])
        for keyword in ("anyOf", "allOf"):
            if isinstance(sub.get(keyword), list):
                for member in sub[keyword]:
                    groups(member)

    groups(node.get("not"))
    return frozenset(found)


def separates(a: Mapping[str, Any], b: Mapping[str, Any], a_type: Any, b_type: Any) -> str | None:
    """What tells two branch NODES apart, or ``None`` where nothing does.

    **A second spelling of ``codegen.lower.union.separates``, over the DOCUMENT, and
    deliberately so.**  Section 9: "the intersection rule it carries stays a second
    spelling of the one in ``lower/composition.py`` on purpose ... One body of code
    deciding what the model states and what the document states agrees with itself by
    construction, so a defect in it is green on both sides."  The same reasoning holds
    exactly here: if the verifier asked the walk which unions it could not separate, the
    equality below would compare the walk's answer with itself.

    Section 4's three separators, each read off the branch nodes of the record:

    * one property pinned to different single values;
    * a ``required`` name one branch declares and the other forbids -- BY NAME, through a
      ``not`` over ``required`` (:func:`_forbids`), which is the idiom §4 itself names
      ("each branch forbidding a name the other requires"), or by admitting no name
      outside its own map;
    * scalar branches of different ``type``.
    """
    first, second = _pins(a), _pins(b)
    for key in sorted(set(first) & set(second)):
        if first[key] != second[key]:
            return f"{key!r} is pinned two ways"
    for one, other in ((a, b), (b, a)):
        required = {n for n in (one.get("required") or []) if isinstance(n, str)}
        named = sorted(required & _forbids(other))
        if named:
            return f"one branch requires {named} and the other forbids each by name"
    for one, other in ((a, b), (b, a)):
        closed = other.get("additionalProperties") is False and "patternProperties" not in other
        if not closed:
            continue
        declared = set(other.get("properties") or {})
        required = {n for n in (one.get("required") or []) if isinstance(n, str)}
        if required - declared:
            return f"one branch requires {sorted(required - declared)} and the other forbids it"
    scalars = a_type not in (None, "object") and b_type not in (None, "object")
    if scalars and a_type != b_type:
        return f"the branches are scalars of type {a_type!r} and {b_type!r}"
    return None


def inseparable_unions(record: Mapping[str, Any]) -> tuple[str, ...]:
    """Every union POINTER of this document whose branches the derivation cannot separate.

    Section 8: an UNDERDETERMINED approximation "is invisible to all three checks, and that
    is why it needs an instrument of its own ... Its check is section 4's disjointness
    derivation: **the set of unions declaring one equals the set the derivation cannot
    separate**, in both directions, so a union that becomes separable loses its declaration
    and a union that stops being separable gains one."

    Pairwise, for ``lower.union.overlapping``'s reason: "Where the branches are pairwise
    disjoint, the payload selects its own branch and the order they are tried in cannot
    change which one it reaches."  One unseparated pair makes the answer a property of
    declaration order, which is what UNDERDETERMINED names.

    A union whose branches are NOT all shapes is not in this set: section 4 lowers one to
    an alias over the union of their types, where "which branch an overlapping payload
    becomes" is not a question a declaration order answers -- there are no branch classes
    to order.  A branch is a shape here where its node, under the root's applied ``type``,
    is an object.

    **A union at a RULE position is not in it either, and the POSITION is carried by the
    descent rather than read off the pointer string.**  Section 3 of the semantics
    document: under a conditional "a keyword describes what a rule tests, so no type is
    lowered from it", so there is no branch class at all.  Section 6 of the architecture
    document is explicit that a pointer STRING cannot answer this -- "a handler never
    derives position from a pointer string", and "a pointer cannot tell a RULE node from a
    PROP one" -- so :func:`_rule_free_nodes` sets the flag where it descends through
    ``if``/``then``/``else``/``not`` and the question is never asked of a pointer.
    Measured over the emitted tree: 3 of this derivation's pointers are at a RULE position
    and all 3 leave with this clause.
    """
    out: list[str] = []
    for pointer, node in _rule_free_nodes(record):
        for kw in _COMBINATORS:
            branches = node.get(kw)
            if not isinstance(branches, list) or len(branches) < 2:  # noqa: PLR2004
                continue
            if not all(isinstance(b, Mapping) for b in branches):
                continue
            # **A PRESENCE-ONLY combinator is not a union at all**, and §4 of the
            # architecture document decides it where the parser reads it: "a combinator
            # whose every branch is ``required``-only is not a ``Union`` but a rule source
            # of the enclosing object (the ``presence_only`` reading, read once here)".
            # It lowers to a ``RequiredGroups`` rule on the enclosing class, so there are
            # no branch classes for a declaration order to choose between -- which is the
            # whole of what UNDERDETERMINED names.  Measured: without this clause the
            # derivation reports 185 pointers, 16 of them roots whose documents emit as a
            # single class with a presence rule.
            if all(set(b) <= {"required"} for b in branches):
                continue
            applied = [b.get("type") or node.get("type") for b in branches]
            if not all(t == "object" or (t is None and b.get("properties")) for t, b in zip(applied, branches)):
                continue
            base = "" if pointer == "/" else pointer
            if any(
                separates(branches[i], branches[j], applied[i], applied[j]) is None
                for i in range(len(branches))
                for j in range(i + 1, len(branches))
            ):
                out.append(f"#{base}/{kw}")
    return tuple(sorted(out))


def underdetermined_census(
    declared: Sequence[Approximation], records: Mapping[str, Mapping[str, Any]]
) -> tuple[list[str], list[str]]:
    """Section 8's UNDERDETERMINED equality, in BOTH directions.

    Returns ``(declared and separable, inseparable and undeclared)``.  Both empty is the
    equality; either non-empty is a defect, and the two say different things -- a union that
    became separable keeps a declaration it has not earned, and one that stopped being
    separable carries no declaration at all and the value it constructs is then a property
    of declaration order with nothing saying so.

    ``records`` is document -> document of record, which is the verifier's own reading of
    what the document states (section 9).
    """
    declared_at = {
        (one.document, one.pointer)
        for one in declared
        if one.kind == UNDERDETERMINED
    }
    inseparable = {
        (document, pointer)
        for document, record in records.items()
        for pointer in inseparable_unions(record)
    }
    return (
        sorted(f"{d}{p}: declared UNDERDETERMINED and the derivation separates it" for d, p in declared_at - inseparable),
        sorted(f"{d}{p}: the derivation cannot separate these branches and nothing declares it" for d, p in inseparable - declared_at),
    )


def check_pair(
    pair: Pair,
    *,
    accepts_examples: int = 1,
    custom_formats: Mapping[str, Any] = (),
) -> PairReport:
    """ONE CLASS AGAINST ONE SCHEMA: the whole harness, per section 6.

    Resolve the document once (the caller's documents arrive resolved), draw a
    payload the schema accepts, construct the class from it, dump the instance and
    compare the dump against the schema; send one payload the schema refuses
    through the entry point, which proves that class's schema half is connected; and
    compare the class's own ``model_json_schema()`` against the document.  That is
    1,055 units of work over
    the graded population rather than 27,791, and the only recursion anywhere in it
    belongs to reference resolution.

    **``max_steps`` and ``refuses_examples`` are gone with the check they
    parametrised.**  A step site mutated one keyword, drew an instance the mutated
    schema accepts, and handed it to ``accept`` -- which validates against THE
    DOCUMENT first, so the assertion was that ``jsonschema`` rejects a payload
    violating the schema it was handed and the generated class took no part in the
    outcome.  Nothing read the result of those 27,791 draws that a faithful class
    and a class carrying ``Any`` on every field did not produce identically.

    The payload the liveness check offers is DERIVED from the accepted instance
    (:func:`refusing_payload`) and screened by the document, so it costs no draw.
    That is the one place a pair's instance is reused, and the reuse is why there are
    two document validations per pair instead of thousands.
    """
    rep = PairReport(
        name=pair.name, model_repr=getattr(pair.model, "__name__", repr(pair.model))[:120]
    )
    rep.missing_formats = sorted(missing_formats(pair.schema, custom_formats))
    accepted: list[Any] = []
    #: **The two INSTANCE checks need a self-contained schema and the comparison does
    #: not, which is the whole of why this line exists.**  ``bundle.record`` inlines
    #: a remote reference and leaves a LOCAL one, so a nested node can say
    #: ``{"$ref": "#/definitions/rectangle"}`` -- a pointer into its DOCUMENT.  Handed
    #: that node alone, ``hypothesis_jsonschema``'s generator raises
    #: ``_RefResolutionError`` and the pair reports ``model_error``, which is a
    #: statement about the GENERATOR wearing the model's name: measured at 5 pairs
    #: over ``core/placement-presentation.json`` and
    #: ``core/bidding-policy-capability.json`` (``salesagent-j3k2l.28``).  Resolving
    #: against the document is what ``adcp.types._base._refuse`` does for the same
    #: reason, by evolving a document-rooted validator onto the node, so the schema
    #: the runtime decides with and the schema the harness draws from agree.
    #:
    #: The COMPARISON keeps the UNRESOLVED node on purpose: what it grades is what the
    #: document STATES at that pointer, and ``_normalize`` reads a ``$ref`` on both
    #: sides against a per-side root -- which is ``salesagent-j3k2l.32``/``.33``'s
    #: landed reading and whose bundle population is exactly these pairs.  Grading the
    #: inlined node instead would take that reading's population back to 0.
    #:
    #: FAIL-SAFE, and the direction matters: with no document supplied -- which is
    #: ``Pair``'s own default and what a caller grading a bare node passes -- a local
    #: ``$ref`` does not resolve and the library RAISES, so the unresolved node is
    #: used and the checks report what they report.  Resolution is a convenience for
    #: the generator, never a licence: a reference the resolution cannot inline leaves
    #: the node stating no fact, every fact the model carries reads as ``added``, and
    #: the pair reddens rather than passing blind.
    try:
        drawn_from = resolve(pair.schema, store={}, referrer=pair.document)
    except Exception:  # noqa: BLE001 -- any resolution failure falls back to the node
        drawn_from = pair.schema
    rep.accepts = check_accepts(
        drawn_from,
        pair.accept,
        examples=accepts_examples,
        custom_formats=custom_formats,
        seen=accepted,
        ref=pair.ref,
    )
    #: Measured only where the generator errored, because that is the only pair the
    #: measurement says anything about -- 2 of 1,079 on the emitted tree, so the
    #: isolated draws cost nothing over the population.  The node is drawn from the
    #: SAME schema the accepts check drew from, so a position the resolution inlined
    #: is screened too.
    if rep.accepts.outcome == "strategy_error":
        rep.accepts_undrawable = undrawable_formats(drawn_from, custom_formats=custom_formats)
    rep.liveness = (
        check_liveness(drawn_from, pair.accept, accepted[0])
        if accepted
        else LivenessResult(outcome="no_payload", detail="the accepts check drew no instance")
    )
    rep.comparison = compare_schema(
        pair.schema,
        pair.model,
        document=pair.document,
        declared=pair.declared,
        at=pair.ref.pointer if pair.ref is not None else "#",
    )
    #: **Section 8's accepts obligation, and it runs only where a declaration claims
    #: something.**  "An approximation is a claim about this check, and this check is what
    #: proves it."  A pair declaring nothing owes nothing, so this costs no draw over the
    #: 769-module tree as it stands -- which is section 14 step 8's exit condition read
    #: from the verifier's side.
    #:
    #: The instance is the accepts check's OWN first draw, so the obligation costs one draw
    #: per value class and no whole-document draw.  With none -- the accepts check drew
    #: nothing -- only a declaration at the pair's own root can be proved, and every other
    #: one is reported ``unproved`` rather than passed.
    if pair.declared:
        rep.widening = check_widening(
            drawn_from,
            pair.accept,
            pair.declared,
            at=pair.ref.pointer if pair.ref is not None else "#",
            instance=accepted[0] if accepted else None,
            custom_formats=custom_formats,
        )
    return rep
