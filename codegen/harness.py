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
grades arrive already resolved (``codegen.emit`` writes them out with zero ``$ref``),
so the one recursion reference resolution needs has happened before the harness sees
anything.  What remains is the library's own: ``merged`` re-enters ``canonicalish``
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
from collections.abc import Callable, Iterator, Mapping
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

    ``store`` maps an absolute URI to the document at it.  A ``$ref`` that is not
    in the store raises, by the library's design: it never fetches remotely.

    ``referrer`` is what a LOCAL pointer (``#/definitions/x``) resolves against, and
    it defaults to ``schema`` -- which is right for a whole document and wrong for a
    NODE of one.  ``bundle.resolved`` inlines a remote reference and leaves a local
    one, so a nested node's own ``$ref`` is a pointer into the DOCUMENT ROOT: given
    the node as its own referrer, the library raises
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


def filtered_formats(schema: Any) -> tuple[str, ...]:
    """Every position where a ``format`` and a ``pattern`` meet, with both values.

    **The shape ``hypothesis_jsonschema`` cannot draw**, and the reason is in its own
    source: ``string_schema`` takes the FORMAT's strategy and then applies the pattern
    as a ``.filter()``, with the comment *"This isn't really supported, but we'll do
    our best with a filter"*.  Where the pattern restricts the value beyond what the
    format strategy happens to emit, every draw is filtered out and ``hypothesis``
    raises ``Unsatisfiable`` over the WHOLE schema, naming no node.

    So this names the nodes, derived from the document rather than guessed, and
    :attr:`PairReport.no_instrument` reports them beside hypothesis's own message --
    which carries the filtered-draw count.  Measured on the emitted population:
    ``core/reference-renderer.json`` states ``format: uri`` beside
    ``pattern: ^https://github\\.com/`` and 459 of 459 draws are filtered, at 10, 25
    and 50 examples alike.

    It is not gated on the format being ASSERTED, and that is deliberate: the filter
    runs whether or not a checker is installed, so the drawing problem is the same.
    """
    return tuple(
        f"{pointer or '/'}: format {node['format']!r} beside pattern {node['pattern']!r}"
        for pointer, node in _nodes(schema)
        if isinstance(node.get("format"), str) and isinstance(node.get("pattern"), str)
    )


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


def _esc(s: str) -> str:
    return s.replace("~", "~0").replace("/", "~1")


def at(doc: Any, pointer: str) -> Any:
    """Dereference a JSON Pointer against a document."""
    cur = doc
    for part in pointer.lstrip("/").split("/"):
        if part == "":
            continue
        part = part.replace("~1", "/").replace("~0", "~")
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur


def _distinct_values(items: Any) -> int | None:
    """How many values ``items`` admits, when that is a countable number.

    The one thing a ``uniqueItems`` step needs and draft-07 cannot state: with a
    known bound, asking for bound + 1 elements forces a repeat, so the step is
    EXCLUSIVE.  ``None`` means the schema admits more values than can be exhausted
    and the step falls back to repeated draws from one schema, which is not
    exclusive and does not pretend to be.
    """
    if not isinstance(items, dict):
        return None  # a tuple-validation list: each slot has its own schema
    if "const" in items:
        return 1
    if isinstance(items.get("enum"), list):
        return len(items["enum"]) or None
    return {"boolean": 2, "null": 1}.get(items.get("type"))


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

    def body(instance: Any) -> None:
        res.examples += 1
        seen.append(instance)
        built = accept(instance)
        back = dump(built) if dump is not None else _wire_dump(built)
        if conforms(schema, back, validator_cls=validator_cls) is False:
            # The CAUSE goes first, because ``detail`` is truncated and a reason at
            # the end of a megabyte of dumped instance is a reason nothing can read.
            raise _DumpRefused(
                "the document refuses the dump on "
                f"{', '.join(violated_keywords(schema, back, validator_cls=validator_cls))}"
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
        res.detail = f"{type(e).__name__}: {e}"[:400]
    except Exception as e:  # a model that raises something other than ValidationError
        res.outcome = "model_error"
        res.detail = f"{type(e).__name__}: {e}"[:400]
        res.counterexample = _dump(seen[-1]) if seen else ""
    return res


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
#: What a document can STATE about a value, and therefore what the model has to
#: state too.  Three groups, and the grouping is the reason this is one list:
#: the constraints (an accepted set), ``required`` / ``additionalProperties`` /
#: ``type`` / ``enum`` / ``const`` (also an accepted set, at the object level),
#: and ``default`` / ``description`` / ``format``, which do NOT change the
#: accepted set and are exactly what a hand-rolled renderer drops without any
#: acceptance test noticing.  ``title`` is absent on purpose: pydantic derives
#: one for every class and every property and the documents carry one only at a
#: root, so it is a name the compiler makes up rather than a fact to compare.
FACTS = (
    "type",
    "enum",
    "const",
    "format",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minLength",
    "maxLength",
    "pattern",
    "minItems",
    "maxItems",
    "uniqueItems",
    "required",
    "additionalProperties",
    "default",
    "description",
)


@dataclass
class ComparisonResult:
    """The schema comparison's verdict for one pair."""

    compared: int = 0  # facts the document states that were looked for
    model_facts: int = 0  # facts the model states that the document does not
    missing: list[str] = field(default_factory=list)  # the model states nothing
    differs: list[str] = field(default_factory=list)  # the model states something else
    added: list[str] = field(default_factory=list)  # the document states nothing
    #: D5's URL-type row, which is a CATEGORY OF ITS OWN and weaker than every
    #: other admission here -- see :func:`_url_typed`.  Counted separately and
    #: never folded into ``missing`` or into the implied-fact rows, so a reader can
    #: see how many facts this row excuses and at which positions.
    url_typed: list[str] = field(default_factory=list)
    #: The fifth resolver canonicalization: a DOCUMENT fact that constrains
    #: nothing, so the model omitting it is not a drop -- see
    #: :func:`_constrains_nothing`.  Counted separately for the same reason
    #: ``url_typed`` is: a fold that disappears into a green ``missing`` is
    #: invisible and permanent, and this one must stay auditable at its positions.
    constrains_nothing: list[str] = field(default_factory=list)
    detail: str = ""

    @property
    def outcome(self) -> str:
        if self.detail:
            return "harness_error"
        if self.missing or self.differs:
            return "model_drops_a_fact"
        if self.added:
            return "model_adds_a_fact"
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
    for a node that says nothing -- so a model that invents a type is still reported.  Two
    derivations, because two shapes in this bundle constrain an instance's type without
    naming it:

    * a ``const``.  ``{"const": "platform"}`` admits exactly the string ``"platform"``, so
      ``type: string`` beside it forbids nothing the node already admits.  pydantic renders
      a ``Literal`` as ``{"const": ..., "type": ...}`` and there is no spelling of a
      literal that omits the type.  It is also where a ONE-MEMBER ``enum`` arrives, on
      either side: :func:`_one_member_enum` writes that spelling as this one, so this
      derivation and the ``description`` row beside it in :func:`_narrows_nothing` answer
      a one-member set however the side that holds it spelled it
      (``salesagent-j3k2l.28``).
    * a ``oneOf``/``anyOf`` whose EVERY branch declares the same ``type``.  Draft-07
      requires an instance to satisfy a branch, so a root that states no ``type`` of its
      own and whose branches all state ``object`` admits only objects.  §4's union base is
      a pydantic model and so renders ``type: object``; 7 of this bundle's union roots
      state the branches' type and not their own.

    **This is not a tolerance for "the model states more".**  It is the question
    :func:`_narrows_nothing` already exists to ask -- whether the accepted set moved -- and
    it is decided from the document.  ``tests/test_emit.py`` asserts, at every site the
    rule excuses, that the document really does refuse an instance of every other type,
    and that a typeless node with no such derivation is still reported.
    """
    if "const" in doc:
        return _JSON_TYPE.get(type(doc["const"])) == value
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


def _constrains_nothing(keyword: str, doc: Mapping[str, Any]) -> bool:
    """Does a DOCUMENT fact constrain its accepted set, or not?

    The fifth resolver canonicalization, and the mirror of :func:`_narrows_nothing`:
    that one asks whether a MODEL-only fact narrows the document, this one asks
    whether a DOCUMENT-only fact constrains anything at all.  A fact that admits
    exactly what its absence admits is not dropped by a model that omits it, so
    reporting it as ``missing`` says the model is wider than its schema when it is
    not.  Measured on the 1,054-document bundle: 5 facts in 1 of its 2 shapes, and
    nothing else reaches this.

    * **``required: []``** -- an empty list demands no key, which is what silence
      demands.  5 sites, and all 5 of the facts this fold accounts for today.
    * **``enum: [false, true]`` at a node the document declares ``boolean``** --
      the two members are the whole of the boolean domain, so the enum admits
      exactly what ``boolean`` admits.  **0 sites in the bundle, and the arm is
      kept.**  It had 5 -- ``/properties/replayed`` in five response documents --
      and every one of them was a CONJUNCT's ``enum``: the resolver's finite-type
      rewrite of the base's boolean, gap-filled beside the node's own
      ``type: boolean``.  ``_composed`` now undoes that rewrite per conjunct
      (``salesagent-j3k2l.28``), so the fact arrives as the ``type`` the node
      already states and never reaches this function.  The shape this arm is for
      is a document stating the PAIR in its own node, which the bundle does not do
      today and which draft-07 plainly permits; its 3 positive and 12 negative
      cases in ``tests/test_comparison_folds.py`` are what grade it, and they are
      hand-written for exactly that reason.

    **Each clause is gated to ITS OWN SHAPE and the gates are the whole of this
    function's correctness.**  A fold that matches one real constraint is invisible
    and permanent, which is why section 6 gates the other four by shape rather than
    by keyword name:

    * ``enum: [false]`` on a boolean PINS the value and must still compare.  So
      must ``enum: [true]``.  The membership test is on the SET, so
      ``[true, false]`` folds and ``[false]`` does not.
    * ``enum: [false, true]`` where the document does NOT declare ``boolean``
      restricts a wider domain -- a bare node, or ``["boolean", "null"]``, admits
      ``null`` that the enum forbids -- so the type is required to be exactly
      ``"boolean"`` and a list spelling does not qualify.
    * ``required: ["x"]`` demands a key and must still compare, so the value is
      required to be empty rather than merely a list.

    This is NOT the place to excuse a fact that is merely hard to render.  A
    document fact the model cannot express is ``missing``, and that is the report
    the specification wants.
    """
    if keyword == "required":
        return doc.get("required") == []
    if keyword == "enum":
        members = doc.get("enum")
        return (
            doc.get("type") == "boolean"
            and isinstance(members, list)
            and {type(m) for m in members} == {bool}
            and set(members) == {True, False}
        )
    return False


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

    A fact the model states and the document does not is reported, because that
    is how a model NARROWER than its document shows up.  Three kinds narrow
    nothing; two of them are 57 of the 57 model-only facts step 1's and step 2's
    population has, and the third arrived with step 5's union roots:

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
    * **``additionalProperties: true``**, 1 of them.  Silence permits an
      additional property, so ``true`` permits exactly as much and forbids
      nothing.  It arises from the resolver: ``resolve_all_refs`` drops a
      redundant ``additionalProperties: true`` while inlining, so
      ``core/installment-ref.json``'s resolved ``collection_ref`` states nothing
      where ``core/collection-ref.json`` states ``true`` and the imported class
      carries ``allow``.  The same resolver rewrites ``false`` into
      ``{"not": {}}`` (see ``_closed``), so this is the second half of one
      canonicalization rather than a second phenomenon.

      ``additionalProperties: false`` model-only is NOT excused: it forbids what
      silence permits, which is a narrowing, and it is also how a class that
      forbids where its own document is silent would show up -- D8 maps silence
      to ``ignore``, which states nothing.
    * **``type``, ``description`` and ``default`` AT A NODE THE DOCUMENT GIVES AN
      ``enum``.**  The third resolver canonicalization, and the same resolver as
      the second: ``canonicalish`` reduces an enum node to its ``enum`` ALONE,
      dropping ``type``, ``title``, ``description`` and ``default`` -- measured
      directly, ``{"type": "string", "enum": ["a", "b"], "description": "d",
      "default": "a"}`` canonicalizes to ``{"enum": ["a", "b"]}``, while the same
      node with ``minLength`` in place of the ``enum`` keeps all four.  So a
      faithful enumeration states three facts its own resolved document no longer
      does, and none of the three can narrow the ``enum``, which pins the accepted
      set exactly.  Measured over this population: 42 such facts at 12 pairs
      (``type`` 20, ``description`` 20, ``default`` 2), and **every one of them at
      a node the document gives an enum** -- 0 elsewhere.

      Each is still gated on the value, so the row cannot excuse a real
      narrowing: the ``type`` has to be the one the document's own members imply
      (a model claiming ``integer`` over a string enum reddens), and the
      ``default`` has to BE one of the members (a default outside the document's
      set is the generator inventing a value, and reddens).  A ``description``
      changes no accepted set in any direction, so there is nothing further to
      ask of it -- and the ``missing``/``differs`` half still catches a dropped or
      wrong one, which is the defect that matters.
    * **a ``type`` the node's own content already forces**, which
      :func:`_entails_type` decides from the document.  A typeless node with nothing
      forcing it is still reported.
    * **a ``description`` AT A NODE THE DOCUMENT GIVES A ``const``.**  The same
      resolver canonicalization as the bullet above, at a ONE-MEMBER enum written
      as a ``const``: ``canonicalish`` reduces a node whose value set is finite to
      that set alone and drops every annotation at it.  Measured directly --
      ``{"type": "string", "const": "OKP", "description": "d"}`` inlined through a
      ``$ref`` comes back ``{"const": "OKP"}``, and so does the same node written
      ``{"enum": ["OKP"]}`` -- and measured on the live pair both ways round:
      ``core/agent-encryption-key.json``'s ``kty`` keeps its ``type`` and its
      ``description`` in its OWN resolved document, and keeps neither inside
      ``core/authorized-agent-base.json``, which references it.

      So a faithful class whose field carries the document's ``description``
      states a fact its referrer's resolved document no longer does.  The
      ``type`` half of the same drop is already decided, by
      :func:`_entails_type`'s ``const`` branch; this row is the ``description``
      half and nothing else.  **It is gated on the document stating a ``const``
      at that node**, so it excuses nothing anywhere else, and a ``description``
      changes no accepted set in any direction -- while the
      ``missing``/``differs`` half still catches a dropped or wrong one, which
      is the defect that matters.

      Measured over the emitted population: **3 such facts at 1 pair**
      (``core/authorized-agent-base.json``'s ``crv``, ``kty`` and ``use``), all
      three a ``description``, and **0 elsewhere**.  A ``default`` or any other
      annotation at a const node has no row and is still reported: 0 of the
      bundle's 1,486 const nodes carries one.
    """
    if "enum" in doc:
        return _implied_by_an_enum(keyword, value, doc["enum"])
    if keyword == "description":
        return "const" in doc
    if keyword == "default":
        return value is None and not required
    if keyword == "type":
        return _entails_type(doc, value)
    return keyword == "additionalProperties" and value is True


#: The JSON Schema type name for each Python member type an ``enum`` can hold.
#: ``bool`` before ``int``, because ``bool`` is a subclass of it.
_MEMBER_TYPES: tuple[tuple[type, str], ...] = (
    (bool, "boolean"),
    (int, "integer"),
    (float, "number"),
    (str, "string"),
)


def _implied_by_an_enum(keyword: str, value: Any, members: Any) -> bool:
    """Is a model-only fact implied by the ``enum`` the document states?

    See ``_narrows_nothing``'s third bullet.  ``None`` is excused for ``default``
    on the same ground as everywhere else -- it is how Python spells an omitted
    key -- and anything the three rows do not name is reported.
    """
    if not isinstance(members, list) or not members:
        return False
    if keyword == "description":
        return True
    if keyword == "default":
        return value is None or any(type(value) is type(m) and value == m for m in members)
    if keyword == "type":
        implied = {next((n for t, n in _MEMBER_TYPES if type(m) is t), None) for m in members}
        return len(implied) == 1 and value in implied
    return False


def _admitted(value: Any, doc: Mapping[str, Any]) -> bool:
    """Does the node's own restored ``type`` admit this value?

    The gate on the ``default`` a rewritten node lost.  Decided by the DOCUMENT's
    restored type rather than by the model, so a default outside the document's set
    -- the generator inventing a value -- is still reported.
    """
    kind = doc.get("type")
    admits = {
        "boolean": lambda v: isinstance(v, bool),
        "null": lambda v: v is None,
    }.get(kind if isinstance(kind, str) else "")
    return admits is not None and admits(value)


#: The two value sets draft-07 can write as a ``type`` and ``canonicalish`` rewrites
#: into an enumeration of their members.
_FINITE = ({"enum": [False, True]}, "boolean"), ({"const": None}, "null")


def _one_member_enum(node: dict) -> dict:
    """``{"enum": [v]}`` written as the ``const`` it is.

    **One accepted set in two spellings, so the two sides are written the same one.**
    ``enum: [v]`` and ``const: v`` admit exactly the same instance and draft-07 offers
    both, and the two sides reach a node by their own routes: a document states either,
    ``canonicalish`` rewrites a one-member ``enum`` into a ``const`` while INLINING a
    remote reference, and the model states whichever its own lowering chose -- D2's
    ``const`` row renders a ``Literal`` and so a ``const``, while a one-member enum node
    becomes a one-member ``StrEnum`` and so an ``enum``.  So a faithful class read as
    both dropping a ``const`` and adding an ``enum`` at a node where nothing disagreed.

    Measured at 3 facts in each direction over 1 pair:
    ``creative/get-creative-features-terminal-success.json``'s ``audit_observations``
    ``items`` inlines ``creative/audit-observation.json``, whose ``code``, ``severity``
    and ``recovery`` are each a one-member ``enum``.  **The same document's own pair is
    green and that is the tell**: ``bundle.resolved`` of ``audit-observation.json``
    keeps ``{"type": "string", "enum": ["OVERSIGHT_DISCLOSURE_CARVEOUT_CLAIMED"], ...}``
    whole, and the referrer's resolved copy of that very node is
    ``{"const": "OVERSIGHT_DISCLOSURE_CARVEOUT_CLAIMED"}`` -- the rewrite happens on the
    inlining path and nowhere else, which is the same mechanism
    :func:`_uncanonicalized` folds out at a boolean (``salesagent-j3k2l.28``).

    **Toward ``const`` and not toward ``enum``, because ``const`` is where the rows that
    answer a one-member set already are.**  The resolver drops the node's ``type`` and
    its ``description`` when it rewrites, and both halves are already decided for a
    ``const`` node -- the ``type`` by :func:`_entails_type`'s ``const`` derivation, over
    a population of **832 typeless const nodes** that
    ``test_the_document_type_word_is_not_restated_beside_the_literal`` asserts it fires
    at every one of, and the ``description`` by :func:`_narrows_nothing`'s ``const``
    row.  Folding the other way would have left both of those answering nothing the
    comparison asks while a second derivation over the ``enum`` answered instead, which
    is two rows for one fact.

    ``{"enum": [false, true]}`` is NOT one member and is untouched: it is a boolean and
    :func:`_uncanonicalized` restores it as the ``type`` the document wrote.
    ``{"enum": [null]}`` folds to ``{"const": null}``, which is that same restoration's
    other entry, so the one spelling reaches it from both -- 0 sites today.

    A node stating BOTH keywords is left alone.  Draft-07 CONJOINS them, so the two are
    separate statements there and each is compared as its side writes it; 0 nodes of the
    bundle state the pair.
    """
    members = node.get("enum")
    if "const" in node or not isinstance(members, list) or len(members) != 1:
        return node
    return {**{k: v for k, v in node.items() if k != "enum"}, "const": members[0]}


def _uncanonicalized(doc: dict) -> tuple[dict, bool]:
    """The document's node with the resolver's FINITE-TYPE rewrite undone.

    ``resolve`` is ``hypothesis_jsonschema``'s own resolver, used here deliberately
    so the schema the runtime decides with is the schema the harness grades, and it
    canonicalizes while inlining.  For a type whose value set is finite it writes
    the set out and **drops every annotation at that node**: measured,
    ``{"type": "boolean", "description": "..."}`` resolves to
    ``{"enum": [false, true]}`` and ``{"type": "null", "description": "..."}`` to
    ``{"const": null}``.  Every other type keeps its keys --
    ``{"type": "string", "description": "d"}`` and
    ``{"type": "integer", "minimum": 1, "description": "d"}`` both come back whole
    -- so this is one mechanism at two shapes and not a general licence.

    The ``type`` is RESTORED, because ``enum: [false, true]`` IS ``type: boolean``:
    the same accepted set, written two ways, and the second is the resolver's
    spelling rather than the document's.  The dropped ``description`` cannot be
    restored and is NOT copied off the model -- a fixture derived from the thing it
    grades cannot falsify anything.  The flag says the node was rewritten, and
    :func:`compare_schema` admits a model-only ``description`` at exactly such a
    node and nowhere else, so the hole is one shape wide and named.

    This is the third canonicalization the comparison folds out, beside ``_closed``
    and the ``additionalProperties: true`` arm of ``_narrows_nothing``.  Reached for
    the first time by ``core/demographic-predicate.json``, whose referenced
    ``include_unknown`` is a plain boolean.  :func:`_derived_max_items` is the
    fourth, and the only one that folds out a fact the resolver ADDS.
    """
    for canonical, kind in _FINITE:
        if doc == canonical:
            return {"type": kind}, True
    if _derived_max_items(doc):
        return {k: v for k, v in doc.items() if k != "maxItems"}, False
    return doc, False


def _derived_max_items(doc: Mapping[str, Any]) -> bool:
    """Is this node's ``maxItems`` one the RESOLVER DERIVED from its ``uniqueItems``?

    The FOURTH canonicalization, and the only one that folds out a fact the resolver
    ADDS rather than one it drops or rewrites.  ``uniqueItems: true`` over a
    countable item set bounds an instance's length at the number of distinct values
    the items admit, and ``canonicalish`` writes that bound out as a ``maxItems``
    the document's own text does not state.  The mechanism was already measured in
    this module -- :func:`violated_keywords`'s docstring records
    ``uniqueItems: true`` over a 2-member enum becoming ``maxItems: 2`` -- and it
    became reachable by the COMPARISON only once a document carrying ``uniqueItems``
    emitted a class (``salesagent-j3k2l.19``).  Measured at 3 pairs:
    ``core/principal-declarations-state.json`` (twice, ``maxItems: 2`` over a
    2-member enum), ``core/requirements/vast-asset-requirements.json`` (the same),
    and ``property/property-error.json`` (``maxItems: 20`` over the 20-member
    channel enum).

    **A HAND-WRITTEN ROW, gated on the exact derivation and not on "a bound beside a
    uniqueItems".**  The value must equal :func:`_distinct_values` of the items, so a
    document's own ``maxItems`` is still compared: measured over the bundle, 28 raw
    nodes state both keywords and 21 of them state a bound BELOW their item count,
    which this does not touch.  At the 7 where the two coincide -- all in
    ``protocol/get-adcp-capabilities-response.json``, refused today for another
    keyword -- the model's own ``uniqueItems`` over the same item set already forbids
    a longer instance, so no accepted set goes ungraded either way.  A rule reading
    "a maxItems beside a uniqueItems is admitted" would be shorter and would excuse a
    genuine dropped bound, invisibly and for good.
    """
    if doc.get("uniqueItems") is not True:
        return False
    bound = _distinct_values(doc.get("items"))
    return bound is not None and doc.get("maxItems") == bound


def _closed(x: Any) -> Any:
    """``additionalProperties``, with the one canonicalization folded out.

    ``{"not": {}}`` is the never-satisfiable schema and so is ``false``, and
    ``resolve`` -- which is ``hypothesis_jsonschema``'s own resolver, used here
    deliberately so the schema the runtime decides with is the schema the harness
    grades -- rewrites the second into the first while inlining.  Measured at one
    site in this step's population (``core/operator-identity.json``'s
    ``operator_unit``, closed in the raw document and ``{"not": {}}`` in the
    resolved one), and it is a fact about the resolver rather than about the
    model: the two forms refuse the same instances.
    """
    return False if x == {"not": {}} else x


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

    Four normalizations, and each one is forced by a decision this pipeline made
    rather than by anything arbitrary in pydantic:

    * **A one-member value set, which draft-07 spells two ways.**
      :func:`_one_member_enum` writes a one-member ``enum`` as the ``const`` it is, on
      both sides, because the document and the model each reach that node by their own
      route and pick their own spelling of one accepted set.
    * **A local ``$ref``.**  A nested object is a nested CLASS and a
      cross-document reference is an IMPORT (P2), so pydantic hoists both into
      ``$defs`` and references them.  ``codegen.bundle.resolved`` inlines a REMOTE
      reference and leaves a LOCAL one, so the document says ``$ref`` too -- at a
      ``definitions`` entry, which is the one section resolution does not reach
      (measured on ``core/placement-presentation.json``: the local reference at
      ``/properties/decorations/items/oneOf/0`` IS inlined and the one at
      ``/definitions/text_decoration/properties/layer`` is not).
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
      states no fact in :data:`FACTS`, and the pair reddens rather than passing
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
      beside a local ``$ref``, is to keep only the keys outside :data:`FACTS`.
    """
    if depth > 16 or not isinstance(node, dict):  # a self-referential $defs chain
        return node if isinstance(node, dict) else {}
    node = _one_member_enum(node)
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
        # Each branch read through the FINITE-TYPE rewrite, which is the third
        # canonicalization (:func:`_uncanonicalized`) applied one level down rather
        # than a fourth rule.  The resolver writes a finite type out as its members
        # WHILE INLINING, so the same union is two shapes depending on whether the
        # document states it or references one that does: measured, the three
        # documents that reference
        # ``creative/creative-feature-result.json#/properties/value`` carry
        # ``oneOf: [{"enum": [false, true]}, {"type": "number"}, {"type": "string"}]``
        # where the two that state it carry ``{"type": "boolean"}`` as the first
        # branch.  Without this the fold fired on the 2 and not on the 3, and the 3
        # reported the model's type list as ``added`` -- the reading half-done is
        # the same defect it was built to close.  ``{"const": null}`` is the same
        # rewrite of a ``null`` branch and is restored by the same call.
        branches = [_uncanonicalized(b)[0] for b in stated]
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
            # ``FACTS``, and the pair reddens visibly instead of passing blind.
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
    return node


#: How deep an ``allOf`` chain ``_composed`` folds before it stops folding.  Same
#: constant and same shape as ``_normalize``'s, deliberately: two instruments that
#: cut a traversal at different places disagree about node identity for no reason
#: anyone can read off either of them (``docs/plan/rebuild-plan.md`` §9).
_COMPOSE_DEPTH = 16


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
    * **Every other fact fills a gap and never overrides.**  The node's own
      declaration wins.  KNOWN CEILING: where a node and a conjunct state the
      same ordering keyword with different bounds the effective constraint is
      the TIGHTER one, and this reports the looser one as expected -- a false
      failure, which is the safe direction and is visible.  Measured over 61 of
      the 342 ``allOf``-root documents in the 3.2 bundle (smallest first, an
      80-second budget): no ordering keyword is stated in two views at a root,
      and of the 6 properties declared in both a root and a conjunct the only
      keyword that ever DISAGREES is ``description`` (3 of 6), where the node
      winning is also the right answer -- the class's field description comes
      from the root's own declaration.  Intersecting by direction would be code
      for a population of zero; the upgrade path is to replace the gap-fill with
      a per-keyword intersection if a document ever collides on a bound.

    **``if`` / ``then`` / ``else`` / ``not`` need no code and that is not an
    oversight.**  A conjunct holding only those states nothing unconditional
    about the value, and none of them is in ``FACTS``, so such a conjunct
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
    caller hands this a RESOLVED document (``codegen.bundle.resolved`` writes it
    into the package and ``adcp.types._base.schema_at`` reads it back), and 0 of
    the conjuncts in that 61-document sample still carried a ``$ref``.  A
    conjunct that somehow did would state no fact in ``FACTS`` and so fold to
    nothing, which is the pre-existing behaviour rather than a new hole.
    """
    conjuncts = doc.get("allOf") if isinstance(doc, dict) else None
    if not isinstance(conjuncts, list) or depth > _COMPOSE_DEPTH:
        return doc
    out = {k: v for k, v in doc.items() if k != "allOf"}
    for conjunct in conjuncts:
        if not isinstance(conjunct, dict):
            continue
        # The conjunct is read through the SAME canonicalization the node is read
        # through (:func:`_uncanonicalized`), and BEFORE its facts are folded in.
        # The resolver's finite-type rewrite drops the ``type`` when it writes a
        # boolean out as ``{"enum": [false, true]}``, so an inlined base's boolean
        # arrives here typeless; gap-filling that node's ``enum`` leaves the merged
        # node with an enum and no type, which is neither spelling of the fact and
        # is a shape no document states.  Measured at 9 facts over 5
        # ``formats/canonical`` documents, each restating an inherited boolean with
        # nothing but a ``default`` and a ``description``: the enum read as
        # ``missing`` while the base plainly states the same accepted set the model
        # does.  Undoing the rewrite first hands the fold ``{"type": "boolean"}``,
        # the document's own spelling, and the pair grades the accepted set as a
        # ``type``.
        #
        # NOT a widening of ``_constrains_nothing``, whose ``type == "boolean"``
        # gate is correct and unchanged: an untyped ``enum: [false, true]`` the
        # DOCUMENT itself states is still compared, because this rewrites a
        # CONJUNCT the resolver wrote and nothing else.
        c = _uncanonicalized(_one_member_enum(_composed(conjunct, depth + 1)))[0]
        for kw in FACTS:
            if kw != "required" and kw in c and kw not in out:
                out[kw] = c[kw]
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
        if isinstance(c.get("items"), dict) and "items" not in out:
            out["items"] = c["items"]
    return out


def compare_schema(schema: dict, model: Any, *, document: dict | None = None) -> ComparisonResult:
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
    """
    res = ComparisonResult()
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

    def compare(doc: Any, got: Any, pointer: str, *, required: bool = False) -> None:
        """``required`` is whether the PARENT document demands this key.

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
        doc, rewritten = _uncanonicalized(doc)
        for kw in FACTS:
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
                # The fifth canonicalization: a document fact that constrains
                # nothing is not dropped by a model that omits it.  Counted apart
                # from ``missing`` so the fold stays auditable at its positions.
                if _constrains_nothing(kw, doc):
                    res.constrains_nothing.append(
                        f"{where}: the document says {doc[kw]!r}, which admits exactly "
                        "what its absence admits"
                    )
                    continue
                res.missing.append(f"{where}: the document says {doc[kw]!r}")
                continue
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
                    compare(a, b, f"{where}")
                    continue
                a, b = _closed(a), _closed(b)
            elif kw == "description":
                a, b = _text(a), _text(b)
            elif kw in ("required", "enum"):
                a, b = sorted(map(repr, a or [])), sorted(map(repr, b or []))
            elif kw == "type" and (isinstance(a, list) or isinstance(b, list)):
                a = sorted(a) if isinstance(a, list) else [a]
                b = sorted(b) if isinstance(b, list) else [b]
            if a != b:
                res.differs.append(f"{where}: the document says {doc[kw]!r}, the model {got[kw]!r}")
        for kw in FACTS:
            if kw in doc or kw not in got:
                continue
            res.model_facts += 1
            # ``rewritten``: the resolver dropped the node's ANNOTATIONS when it
            # wrote the finite type out as its members, so the model states a
            # ``description`` and a ``default`` its RESOLVED document no longer does.
            # Admitted at that node only; see ``_uncanonicalized``.  The ``default``
            # is still gated on the VALUE -- it has to be one the restored type
            # admits -- so this cannot excuse a generator inventing one; measured on
            # ``core/canonical-projection-slot-override.json``'s two booleans, whose
            # documents state ``default: true`` and ``default: false`` and whose
            # resolved nodes state neither.  ``description`` needs no gate: it
            # changes no accepted set in any direction.
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
            if (
                _narrows_nothing(kw, got[kw], doc, required=required)
                or (rewritten and kw == "description")
                or (rewritten and kw == "default" and _admitted(got[kw], doc))
            ):
                continue
            res.added.append(f"{pointer}/{kw}: the model says {got[kw]!r}, the document nothing")

        props = doc.get("properties") or {}
        mine = got.get("properties") if isinstance(got.get("properties"), dict) else {}
        demanded = doc.get("required") if isinstance(doc.get("required"), list) else []
        if isinstance(props, dict):
            for key in sorted(props):
                at = f"{pointer}/properties/{_esc(key)}"
                if key not in mine:
                    res.compared += 1
                    res.missing.append(f"{at}: the model declares no such property")
                    continue
                compare(props[key], mine[key], at, required=key in demanded)
        for key in sorted(set(mine) - set(props)):
            res.model_facts += 1
            res.added.append(
                f"{pointer}/properties/{_esc(key)}: the document declares no such property"
            )
        if isinstance(doc.get("items"), dict):
            compare(doc["items"], got.get("items"), f"{pointer}/items")

    compare(schema, emitted, "")
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

@dataclass
class PairReport:
    name: str
    model_repr: str = ""
    accepts: AcceptsResult | None = None
    liveness: LivenessResult | None = None
    comparison: ComparisonResult | None = None
    missing_formats: list[str] = field(default_factory=list)
    #: The DOCUMENT's own positions where a ``format`` and a ``pattern`` meet,
    #: filled by :func:`check_pair` because a report does not hold the document it
    #: graded.  Read by :attr:`no_instrument` to name the shape behind an accepts
    #: check that could not draw.
    accepts_filtered_formats: tuple[str, ...] = ()

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
        filtered-draw count -- beside the document's own positions where a ``format``
        and a ``pattern`` meet (:func:`filtered_formats`), because that is the shape
        ``hypothesis_jsonschema``'s ``string_schema`` filters and cannot satisfy.
        The positions are DERIVED from the document, not guessed: hypothesis raises
        over the whole schema and names no node.
        """
        if self.accepts is None or self.accepts.outcome != "strategy_error":
            return ()
        where = "; ".join(self.accepts_filtered_formats) or (
            "no format-beside-pattern position in this document"
        )
        why = self.accepts.detail.split(" Try making")[0].strip()[:200]
        return (f"accepts: {where}; {why}",)

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
        if self.comparison is None or self.comparison.outcome not in ("pass", "no_evidence"):
            return "comparison:" + (self.comparison.outcome if self.comparison else "unrun")
        if self.no_instrument:
            return "no_instrument"
        if not self.graded_instances:
            return "no_accepts_check_evidence"
        return "pass"


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
    rep.accepts_filtered_formats = filtered_formats(pair.schema)
    accepted: list[Any] = []
    #: **The two INSTANCE checks need a self-contained schema and the comparison does
    #: not, which is the whole of why this line exists.**  ``bundle.resolved`` inlines
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
    )
    rep.liveness = (
        check_liveness(drawn_from, pair.accept, accepted[0])
        if accepted
        else LivenessResult(outcome="no_payload", detail="the accepts check drew no instance")
    )
    rep.comparison = compare_schema(pair.schema, pair.model, document=pair.document)
    return rep
