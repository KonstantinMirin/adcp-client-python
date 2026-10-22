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

It runs three checks over that pair:

  the accepts check (``check_accepts``)
      schema -> payload -> model: every instance the schema admits, the model
      admits.

  the refuses check (``check_refuses``)
      model -> mutated keyword -> schema: for each constraint keyword in the
      document, an instance that violates exactly that keyword is refused.

  the schema comparison (``compare_schema``)
      every fact the document states about a value, the model's own
      ``model_json_schema()`` states too.

**The third is not redundant and here is the measurement that forces it.**  Where
``accept`` validates against the document before constructing -- which is the
production entry point and so the only honest thing to run the first two
through -- its schema half refuses everything the document refuses, so the
ANNOTATIONS are never exercised.  On ``core/pagination-request.json`` a model
with ``Any`` on every field passes both checks over the SAME 75 instances a
faithful model is graded over, so no count of instances separates them.  Three
lanes found that independently, by widening their own lowering and staying green.
The accepts and refuses checks grade the entry point; ``compare_schema`` grades
the generated code.

Nothing is enumerated by hand.  The keyword comes from the document, the instance
from ``hypothesis_jsonschema``, and the expected refusal is the keyword that was
stepped.  ``conforms`` runs as a control before any refusal is asserted: an
instance the step failed to push out of the schema grades nothing, and is counted
rather than silently passed.

A site under an optional key is reachable only if the generator populates that
key, which it mostly does not; ``force_path`` makes the way down mandatory in the
generated-from document so the mutation lands where it was aimed.  What is left
ungraded after that is a hop with no instance location to make mandatory -- a
union branch, a pattern-matched key -- and the control still counts it.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import re
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, TypeGuard

import jsonschema
from hypothesis import HealthCheck, Phase, given, settings
from hypothesis import strategies as st
from hypothesis.errors import HypothesisException, Unsatisfiable
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
def resolve(schema: dict, *, store: Mapping[str, Any], base_uri: str = "") -> dict:
    """Inline every ``$ref`` using hypothesis_jsonschema's own resolver.

    ``store`` maps an absolute URI to the document at it.  A ``$ref`` that is not
    in the store raises, by the library's design: it never fetches remotely.
    """
    doc = copy.deepcopy(schema)
    resolver = LocalResolver(base_uri=base_uri, referrer=copy.deepcopy(doc), store=dict(store))
    return resolve_all_refs(doc, resolver=resolver)


def strategy(schema: dict, custom_formats: Mapping[str, Any]) -> st.SearchStrategy:
    return from_schema(schema, custom_formats=dict(custom_formats))


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


# --------------------------------------------------------------------------- #
# the step: one constraint keyword, rewritten so every instance violates it
# --------------------------------------------------------------------------- #
# A looser step ("minItems: 1 -> 0") leaves it to chance whether the generator
# walks into the violation.  Each step below is EXCLUSIVE: the stepped subschema
# admits only instances the original refuses, so the control fires only when the
# site itself is unreachable (an optional subtree, an untaken union branch).
@dataclass(frozen=True)
class Step:
    """A constraint FACT about one instance location, and how to rewrite it away.

    ``steps()`` finds every site by walking the document once and copies nothing:
    a resolved document can be megabytes with thousands of sites, and
    deep-copying it per site cost 93 s on a 214-site document before this was
    made lazy. ``materialize`` produces the stepped document for the sites a
    caller actually grades.

    **A fact can be stated at more than one schema position, and the step is the
    fact rather than the position.**  ``allOf`` conjoins, so a document whose root
    and whose conjunct both state ``minLength: 3`` states one fact about one
    instance location through two positions.  Rewriting ONE of them left the other
    stating the original bound, the conjunction of the two admitted no instance,
    and ``hypothesis_jsonschema`` raised -- so the site cost a step and graded
    nothing.  MEASURED on a root ``allOf`` restating ``required``, ``minLength``
    and ``minItems``: 6 of 6 sites reported ``harness_error``, in three different
    exception shapes.  D7 makes that restatement the normal case rather than an
    edge: where a composition tightens an inherited field's requiredness the
    subclass redeclares the field with the base's keywords, and a composed class's
    ``required`` is the union of its own and every base's.

    So ``positions`` holds every position stating the fact and ``materialize``
    rewrites all of them, which pushes the instance out of the document once.
    ``pointer`` is the outermost of them, because a report names one site.
    """

    keyword: str  # the constraint that was stepped, as the document spells it
    describe: str  # human-readable "before -> after"
    _rewrite: Callable[[dict], None]
    positions: tuple[str, ...]  # every position stating this fact, outermost first
    #: Whether the rewrite puts the document's OWN statement at this site back,
    #: NEGATED -- so what it admits is exactly the set of instances the document
    #: refuses there -- or merely one witness the harness chose.
    #:
    #: This is the only thing that separates the two reasons a stepped document
    #: can admit nothing, and both have a test.  A COMPLEMENT that admits nothing
    #: says the DOCUMENT admits no instance violating this keyword here: nothing
    #: of the harness's choosing is in it, so the emptiness is the document's and
    #: the honest verdict is the zero-denominator one (``no_evidence``) -- an
    #: ``if`` whose condition implies its branch, a combinator exhaustive over its
    #: own type.  A WITNESS that admits nothing says only that THIS witness does
    #: not exist: ``maxLength 4`` is stepped to "exactly 5 characters", and a
    #: ``const`` of four characters at the same instance location rules that out
    #: while the document still refuses every five-character value.  The harness
    #: cannot build the instance; the document has one.  That is a harness
    #: limitation and is REPORTED (``harness_error``), with the contradicting
    #: keyword named, because §6 forbids a green mark over an ungraded site.
    #:
    #: Set by the emitting branch, which is the one place that knows which of the
    #: two it built.  A list consulted at the catch site would be a second answer
    #: to the same question, and would go stale the first time a family is added.
    complement: bool = False

    @property
    def pointer(self) -> str:
        """The one position a report names.  Derived, so the two cannot disagree."""
        return self.positions[0]

    def materialize(self, schema: dict, *, force: bool = True) -> dict:
        """The stepped document to GENERATE from. The original still decides.

        ``force`` makes the path down to the site mandatory (see ``force_path``).
        It is on because a site the generator never populates grades nothing;
        ``force=False`` exists so a measurement can draw the unforced case from
        the same inputs in the same process, and nothing else passes it.

        EVERY position is forced, not only the one a report names, and what that
        buys is a DENOMINATOR rather than a verdict.  Measured on a fact stated in
        two union branches that neither branch requires: forcing the first
        position alone makes the key mandatory in that branch only, the generator
        satisfies the OTHER branch and omits the key, and 8 of 25 examples grade
        nothing.  Forcing every position makes it 25 of 25.  Both report ``pass``,
        so no outcome separates them -- which is why the test for it asserts the
        control count and not the verdict.
        """
        doc = copy.deepcopy(schema)
        if force:
            for pointer in self.positions:
                _force_into(doc, pointer)
        for pointer in self.positions:
            self._rewrite(at(doc, "" if pointer == "/" else pointer))
        return doc


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


# The hops along a pointer whose presence in an instance is OPTIONAL and can be
# made mandatory: a named property (and the trigger key of a dependent schema) by
# adding the name to its own parent's ``required``, a collection by forbidding it
# to be empty.  Every other hop falls through to a plain descent, which is the
# right answer for each of them for a different reason: an ``allOf`` branch and a
# ``contains`` subschema already apply to every instance; a union branch is a
# partial barrier the generator clears on its own (the control pair takes its
# branch on 18 of 40 examples, and one is enough to grade); and a pattern-matched key, a
# ``not`` / ``propertyNames`` subschema or a ``$defs`` entry has no instance
# location to make mandatory at all, so a site beneath one stays unreachable and
# the control still counts it as ungraded.  A ``then`` / ``else`` DOES have one --
# its sibling ``if`` -- and ``force_path`` adds it as a conjunct; see the hop.
_FORCE_NAMED = ("properties", "dependentSchemas")

#: Candidate instances for a ``pattern`` step, tried in order.  Short, so a
#: ``maxLength`` beside the pattern does not rule them all out, and spread across
#: character classes, so a pattern restricting to one of them still has a miss.
#:
#: The last member is the one axis the first seven do not cover and ``format``
#: being asserted introduced: a sibling ``format`` has to ADMIT the candidate
#: too, and none of the first seven is a well-formed value of any format.
#: Measured at ``core/platform-extension-ref.json#/properties/uri``, which
#: states ``format: uri`` beside ``pattern: ^https://``: once the checker was
#: passed, all seven failed the ``conforms`` screen, the site got no step at all,
#: and the refuses-check denominator fell by that step's 25 instances -- the
#: pattern went from graded to ungraded without any pair reporting a failure.
#: An absolute URI with a scheme the pattern refuses clears both screens and
#: grades it again.  It is LAST so a shorter candidate still wins wherever one
#: clears, which is every other pattern site in this population.
#:
#: ``uri`` is the only format in this bundle that co-occurs with a string
#: constraint at any scale -- 73 of its 300 uses, against 4 for ``email``, 2 for
#: ``hostname`` and 0 for ``date-time`` and ``date`` -- so one member is the
#: whole of what this axis needs today.
_PATTERN_MISSES = ("!", "A", "0", " ", "", "\x00", "__adcp_harness__", "http://a.example/")


def force_path(schema: dict, pointer: str) -> dict:
    """Copy of ``schema`` in which the path down to ``pointer`` is mandatory.

    MEASURED mechanism for a site that grades nothing: the parent object IS
    generated, but the optional key holding the stepped site is never populated.
    At every probed site the parent was present in 11-24 of 50 instances and the
    key inside it in 0 of 50 -- ``hypothesis_jsonschema`` biases hard toward the
    minimal object, and ``derandomize=True`` makes that bias reproducible, which
    is why it is 50 consecutive omissions rather than a coin flip.  Three
    competing explanations were ruled out by the same probe: an identical inlined
    copy elsewhere in the resolved document (0 at every site), the keyword being
    normalised away by ``canonicalish``, and an unsatisfiable parent.

    So each property traversed on the way to the site is added to its OWN
    parent's ``required``, and each collection traversed is forbidden to be
    empty.  This is applied to the STEPPED document only -- the one the generator
    draws from.  The ORIGINAL decides whether an instance violates anything
    (see ``check_refuses``), so the control stays independent: rewrite the
    original here and a site could be reported as graded on the strength of a
    constraint this function added.

    A hop is left alone when forcing it would contradict a bound already at that
    node (``maxItems: 0``, ``maxProperties: 0``).  Such a site is genuinely
    unreachable, and an unsatisfiable stepped document would report it as a
    harness error instead of as the ungraded site it is.
    """
    doc = copy.deepcopy(schema)
    _force_into(doc, pointer)
    return doc


def _force_into(doc: dict, pointer: str) -> None:
    """``force_path``'s body, applied IN PLACE.

    One step can hold several positions (see ``Step``), and each is forced into
    the same document: copying per position would discard the previous one's
    forcing.
    """
    parts = [p for p in pointer.split("/") if p]
    node: Any = doc
    i = 0
    while i < len(parts):
        k = parts[i]
        nxt = parts[i + 1] if i + 1 < len(parts) else None
        if k in _DESCEND_MAP and nxt is not None:
            name = nxt.replace("~1", "/").replace("~0", "~")
            if k in _FORCE_NAMED and isinstance(node, dict):
                req = node.setdefault("required", [])
                if name not in req:
                    req.append(name)
            node = node[k][name]
            i += 2
        elif k == "items" and isinstance(node.get("items"), list) and _is_index(nxt):
            _at_least(node, "minItems", "maxItems", int(nxt) + 1)
            node = node["items"][int(nxt)]
            i += 2
        elif k in _DESCEND_LIST and _is_index(nxt):
            if k == "prefixItems":
                _at_least(node, "minItems", "maxItems", int(nxt) + 1)
            node = node[k][int(nxt)]
            i += 2
        elif k in ("items", "additionalItems", "unevaluatedItems"):
            _at_least(node, "minItems", "maxItems", 1)
            node = node[k]
            i += 1
        elif k in ("additionalProperties", "unevaluatedProperties"):
            _at_least(node, "minProperties", "maxProperties", 1)
            node = node[k]
            i += 1
        elif k in ("then", "else") and isinstance(node.get("if"), dict):
            # A ``then`` applies only to an instance its sibling ``if`` MATCHES, and
            # nothing made the ``if`` match: ``hypothesis_jsonschema`` draws the
            # minimal object, the condition is usually a ``const`` on an optional
            # key, and a site under ``then`` was then graded by the control instead
            # of by the model.  ``core/canvas-constraint.json``'s
            # ``if unit == "percent" then x.maximum = 100`` is the inventory's one
            # ``maximum`` triple, and this is the hop it needed.
            #
            # So the condition is added as a CONJUNCT of the node holding it --
            # negated for an ``else``, which is what reaches that branch.  Same rule
            # as every other hop here: make the way down mandatory in the
            # generated-from document only, and leave the ORIGINAL to decide what an
            # instance violates.
            condition = copy.deepcopy(node["if"])
            node.setdefault("allOf", []).append(
                condition if k == "then" else {"not": condition}
            )
            node = node[k]
            i += 1
        else:
            node = node[int(k)] if isinstance(node, list) else node[k]
            i += 1


def _is_index(part: str | None) -> TypeGuard[str]:
    return part is not None and part.isdigit()


def _whole(value: Any) -> int | None:
    """``value`` if it is a JSON integer, which ``True`` is not."""
    return value if isinstance(value, int) and not isinstance(value, bool) else None


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


def _admits_nothing(schema: Any) -> bool:
    """Whether ``schema`` admits no instance at all, by the GENERATOR'S own reading.

    ``hypothesis_jsonschema`` is what will be asked to generate from the stepped
    document, so its canonical form is the authority on what is satisfiable; a list
    of spellings maintained here would be a second answer that drifts.  That matters
    for every step below that negates part of a document: a negation whose
    conjunction with the rest is unsatisfiable produces a HARNESS ERROR, which
    reports as a red pair rather than as the ungraded site it is.  The name is
    private, so degrade to the literal rather than break on an upgrade.
    """
    try:
        from hypothesis_jsonschema._canonicalise import FALSEY, canonicalish
    except ImportError:  # pragma: no cover
        return schema is False
    try:
        return bool(canonicalish(schema) == FALSEY)
    except Exception:  # a schema the canonicaliser cannot reduce is not known-empty
        return False


def _admits_more_than(node: dict, n: int) -> bool:
    """Whether the node admits an object of MORE than ``n`` properties.

    A closed object admits only the keys it declares, so a ``maxProperties`` at or
    above that count cannot be pushed past: the site is genuinely unreachable, and a
    step that asked for ``n + 1`` keys anyway would report an unsatisfiable strategy
    in place of the ungraded site it is.  Measured on
    ``core/operator-identity.json``'s ``operator_unit``, which is also the reason
    the test is "closed" and not "``additionalProperties`` is ``False``": that node
    spells closed as ``{"additionalProperties": {"not": {}}}``, a subschema no
    instance satisfies, and a check against the literal read it as open.
    """
    extra = node.get("additionalProperties")
    if extra is None or not _admits_nothing(extra):
        return True
    declared = node.get("properties")
    return isinstance(declared, dict) and len(declared) > n


def _at_least(node: Any, floor_kw: str, ceiling_kw: str, n: int) -> None:
    """Raise ``floor_kw`` to ``n``, unless a ceiling at the same node forbids it."""
    if not isinstance(node, dict):
        return
    ceiling = node.get(ceiling_kw)
    if isinstance(ceiling, int) and not isinstance(ceiling, bool) and ceiling < n:
        return  # genuinely unreachable; do not manufacture an unsatisfiable step
    cur = node.get(floor_kw)
    if not (isinstance(cur, int) and not isinstance(cur, bool) and cur >= n):
        node[floor_kw] = n


#: The pointer hops that do NOT move the instance cursor, so two positions either
#: side of one address the same instance location.  ``allOf``, ``anyOf`` and
#: ``oneOf`` take an index; ``then`` and ``else`` do not.
_APPLICATOR_INDEXED = ("allOf", "anyOf", "oneOf")
_APPLICATOR_PLAIN = ("then", "else")

#: A position beneath one of these states no fact ABOUT the instance that a
#: sibling could restate, so it joins no group and is always a step of its own.
#: A step beneath an ``if`` makes the condition FAIL, which releases ``then``
#: instead of pushing the instance out of the document; a step beneath a ``not``
#: is satisfied by the negation.  Such a site stays exactly as reachable as it is
#: today, and the control counts it when it grades nothing.
#:
#: MEASURED, and this is why the rule is "groups with nothing" rather than "keeps
#: the hop in its location": ``core/creative-approval-scope.json`` states
#: ``required: ['approval_status']`` inside ``/allOf/0/if`` AND inside
#: ``/allOf/1/if`` -- two different conditions, which keeping the ``if`` hop while
#: dropping the ``allOf`` index collapses to one location called ``/if``.  They
#: are not one fact and grouping them says they are.
_NEVER_GROUPED = ("if", "not")


def instance_location(pointer: str) -> str:
    """The instance location a schema position addresses.

    Two positions with the same location constrain the same place in an instance,
    which is what makes them restatements of one fact rather than two facts.  A
    position under an ``if`` or a ``not`` gets its own pointer back, so it is
    equal to no other position and groups with nothing (see ``_NEVER_GROUPED``).
    """
    parts = [p for p in pointer.split("/") if p]
    out: list[str] = []
    i = 0
    while i < len(parts):
        p = parts[i]
        if p in _NEVER_GROUPED:
            return pointer or "/"
        if p in _APPLICATOR_INDEXED and _is_index(parts[i + 1] if i + 1 < len(parts) else None):
            i += 2
        elif p in _APPLICATOR_PLAIN:
            i += 1
        else:
            out.append(p)
            i += 1
    return "/" + "/".join(out)


#: What a node can say that constrains NO value: a name, a note, a presence
#: default.  Everything else at a node narrows what the node admits, so the
#: complement of this set is "the keywords that could contradict a step" -- which
#: is the honest way round, because a list of CONSTRAINTS would have to be
#: complete and would go silently short of the vocabulary (``const`` is the
#: fixture's own collider and is not a keyword ``steps`` can step).
_ANNOTATION_ONLY = frozenset(
    {
        "$schema",
        "$id",
        "$comment",
        "title",
        "description",
        "examples",
        "default",
        "deprecated",
        "readOnly",
        "writeOnly",
        "enumDescriptions",
    }
)


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


def contradicting(schema: dict, step: Step) -> tuple[str, ...]:
    """Every keyword stated at this step's instance location that it did not rewrite.

    What a reader is owed when a witness step admits nothing: the step mutated one
    keyword at one position, and something ELSE about the same place in an
    instance ruled the mutation out.  ``pointer:keyword``, so the report names the
    position as well as the keyword.

    An EMPTY result is a finding of its own rather than a blank: it says the
    contradiction is NOT at this instance location, so the step is not what the
    reader should look at.  It does not say which of the other causes it is, and
    the measured population holds at least two.  ``core/reference-renderer.json``
    does not generate in its ORIGINAL resolved form -- it exhausts
    ``hypothesis_jsonschema``'s filter before any step is applied -- so all 14 of
    its unsteppable sites are that one fact and none is a collision.
    ``core/media-buy-frequency-cap.json`` generates, and five of its sites report
    an empty collider anyway: a ``maxProperties`` and the ``required`` names
    ``force_path`` adds on the way down are at different nodes, so neither is at
    the stepped site's location.  Do not read an empty result as either one.

    Called only from the failure path, so the second walk costs one traversal per
    site the check could not step rather than one per site.
    """
    location = instance_location(step.pointer)
    stepped = set(step.positions)
    return tuple(
        f"{pointer}:{keyword}"
        for pointer, node in _nodes(schema)
        if pointer not in stepped and instance_location(pointer) == location
        for keyword in sorted(node)
        if keyword not in _ANNOTATION_ONLY
    )


def steps(schema: dict) -> list[Step]:
    """Every constraint FACT in the document, each as one exclusive step.

    A fact restated at a second position is ONE step that rewrites both, because
    rewriting one of them leaves the other constraining the value and the
    conjunction of the two can admit no instance at all (see ``Step``).

    **Two positions are the same fact when they state the same keyword at the same
    instance location AND their rewrites are identical**, and the admission rule
    says that directly: the key carries the VALUE the rewrite is derived from, so
    equal keys mean interchangeable rewrites and the group can apply any one of
    them at every position.  That is why a group can never manufacture a
    contradiction of its own: two positions stating DIFFERENT bounds for one
    keyword are an intersection rather than a restatement, so they key differently
    and stay separate steps behaving exactly as they do today.

    The stated value is in the key rather than read off ``describe`` because
    MEASURED, ``describe`` does not determine the rewrite for the five families
    whose rewrite READS the node it rewrites.  ``if/then -> the condition, the
    branch negated`` holds no value at all, so
    ``core/account-timezone-capability.json``'s four conjuncts -- four different
    ``if`` conditions about one instance location -- grouped into ONE step whose
    materialization demands ``mode`` be ``seller_fixed`` and ``account_fixed`` at
    once.  That is unsatisfiable, so D6's ``then`` family went from 4 sites x 20
    biting examples to one site grading nothing, and step 7's exit condition --
    the harness steps every one of the six -- stopped holding.
    ``core/macro-encoding.json`` is the same shape with three conjuncts, and
    ``not`` lost a site the same way: ``not {"required": ["fixed_timezone"]}`` and
    ``not {"required": ["supported_timezones"]}`` describe identically through
    their key lists and are two facts.
    """
    Key = tuple[str, str, str, str]
    found: dict[Key, list[str]] = {}
    rewrites: dict[Key, Callable[[dict], None]] = {}
    complements: dict[Key, bool] = {}

    def emit(
        pointer: str,
        keyword: str,
        describe: str,
        rewrite: Callable[[dict], None],
        *,
        states: Any = None,
        complement: bool = False,
    ) -> None:
        """Record one position of one fact.

        ``states`` is the value the rewrite is derived from, and is passed by the
        branches whose rewrite reads the node rather than closing over a bound.
        ``None`` means the rewrite is a function of the keyword alone, so
        ``describe`` already determines it.
        """
        pointer = pointer or "/"
        key = (instance_location(pointer), keyword, describe, _stated(states))
        if key in found:
            found[key].append(pointer)
            return
        found[key] = [pointer]
        rewrites[key] = rewrite
        complements[key] = complement

    def rec(node: Any, pointer: str) -> None:
        if isinstance(node, list):
            for i, v in enumerate(node):
                rec(v, f"{pointer}/{i}")
            return
        if not isinstance(node, dict):
            return

        n = node.get("minItems")
        if isinstance(n, int) and not isinstance(n, bool) and n >= 1:

            def r(t: dict, _n: int = n) -> None:
                t.pop("minItems", None)
                t["maxItems"] = 0

            emit(pointer, "minItems", f"minItems {n} -> maxItems 0", r)

        n = node.get("maxItems")
        if isinstance(n, int) and not isinstance(n, bool):

            def r(t: dict, _n: int = n) -> None:
                t["minItems"] = _n + 1
                t["maxItems"] = _n + 1
                t.pop("uniqueItems", None)

            emit(pointer, "maxItems", f"maxItems {n} -> exactly {n + 1}", r)

        n = node.get("maxLength")
        if isinstance(n, int) and not isinstance(n, bool):

            def r(t: dict, _n: int = n) -> None:
                t["minLength"] = _n + 1
                t["maxLength"] = _n + 1
                # a pattern/format/enum/const at the same site would contradict
                # the lengthened string and make the step unsatisfiable
                for k in ("pattern", "format", "enum", "const"):
                    t.pop(k, None)

            emit(pointer, "maxLength", f"maxLength {n} -> exactly {n + 1}", r)

        n = node.get("minLength")
        if isinstance(n, int) and not isinstance(n, bool) and n >= 1:

            def r(t: dict, _n: int = n) -> None:
                t["minLength"] = 0
                t["maxLength"] = _n - 1
                for k in ("pattern", "format", "enum", "const"):
                    t.pop(k, None)

            emit(pointer, "minLength", f"minLength {n} -> at most {n - 1}", r)

        n = node.get("minimum")
        if isinstance(n, (int, float)) and not isinstance(n, bool):

            def r(t: dict, _n: Any = n) -> None:
                t.pop("minimum", None)
                t.pop("exclusiveMinimum", None)
                t["maximum"] = _n - 1

            emit(pointer, "minimum", f"minimum {n} -> maximum {n - 1}", r)

        n = node.get("maximum")
        if isinstance(n, (int, float)) and not isinstance(n, bool):

            def r(t: dict, _n: Any = n) -> None:
                t.pop("maximum", None)
                t.pop("exclusiveMaximum", None)
                t["minimum"] = _n + 1

            emit(pointer, "maximum", f"maximum {n} -> minimum {n + 1}", r)

        req = node.get("required")
        if isinstance(req, list) and req:
            for key in req:
                if not isinstance(key, str):
                    continue

                def r(t: dict, _k: str = key) -> None:
                    t["required"] = [x for x in t.get("required", []) if x != _k]
                    t["not"] = {"required": [_k]}  # every instance omits it

                emit(pointer, "required", f"required drops {key!r}", r)

        if node.get("additionalProperties") is False and isinstance(node.get("properties"), dict):

            def r(t: dict) -> None:
                t["additionalProperties"] = True
                t.setdefault("properties", {})["__harness_extra__"] = {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 3,
                }
                t["required"] = sorted(set(t.get("required", [])) | {"__harness_extra__"})

            emit(
                pointer,
                "additionalProperties",
                "additionalProperties false -> an extra property",
                r,
            )

        p = node.get("pattern")
        if isinstance(p, str):
            # A `pattern` step has to be a value the pattern refuses, and no
            # rewrite of the pattern itself produces one reliably.  So the step
            # pins a `const` -- exclusive by construction -- chosen from a fixed
            # list by two tests: the ORIGINAL pattern must not match it
            # (`jsonschema` uses `re.search`, so the candidate is graded the way
            # the document will grade it), and the node WITHOUT its pattern must
            # admit it, so the instance violates the pattern and nothing else.
            # A node no candidate clears gets no step and the pair reports its own
            # zero denominator; inventing one that also violates a `minLength`
            # would make the step's keyword a label for someone else's refusal.
            without = {k: v for k, v in node.items() if k != "pattern"}
            pick = next(
                (
                    c
                    for c in _PATTERN_MISSES
                    if re.search(p, c) is None and conforms(without, c) is True
                ),
                None,
            )
            if pick is not None:

                def r(t: dict, _c: str = pick) -> None:
                    t.pop("pattern", None)
                    t["type"] = "string"
                    t["const"] = _c

                emit(pointer, "pattern", f"pattern {p!r} -> the non-matching {pick!r}", r)

        e = node.get("enum")
        if isinstance(e, list) and e and all(isinstance(x, str) for x in e):

            def r(t: dict, _e: list = e) -> None:
                t.pop("enum", None)
                t["type"] = "string"
                t["const"] = "__harness_not_a_member__"
                for k in ("pattern", "format", "minLength", "maxLength"):
                    t.pop(k, None)

            emit(pointer, "enum", f"enum of {len(e)} -> a non-member", r)

        # ----------------------------------------------------------------- #
        # D6's six families: what a document says about an instance AS A WHOLE
        # ----------------------------------------------------------------- #
        # NONE OF THESE HAD A STEP BEFORE THIS.  The nine keywords above were the
        # whole of ``steps()``, and step 7's six families are WHOLLY DISJOINT from
        # them -- so every rule the step lowers would have been graded by nothing,
        # in either direction, and the bundle's 485 ``uniqueItems`` occurrences
        # were 0 of 5,545 site rows.  Two of the nine steps ``pop``
        # ``uniqueItems`` to stay satisfiable, which is how its absence went
        # unnoticed.
        if node.get("uniqueItems") is True:
            # Forcing a duplicate is the one thing draft-07 cannot say directly, so
            # the step says it two ways.  PIGEONHOLE where the item schema admits a
            # countable set of values (``const``, ``enum``, ``boolean``, ``null``):
            # ask for one more element than there are values and a repeat is
            # unavoidable, so the step is exclusive.  Otherwise EXACTLY ``slots``
            # elements drawn from one schema, which is NOT exclusive and does not
            # pretend to be -- the first example of ``{"type": "string"}`` is
            # ``["", ""]`` and later ones differ, so the site is graded by that
            # example and the control counts the rest.  One refusal is a pass;
            # ``no_evidence`` is what a site with none reports.
            bound = _distinct_values(node.get("items"))
            ceiling = _whole(node.get("maxItems"))
            slots = max(2, _whole(node.get("minItems")) or 0)
            if bound is not None and (ceiling is None or ceiling > bound):

                def r(t: dict, _n: int = bound + 1) -> None:
                    t.pop("uniqueItems", None)
                    t["minItems"] = _n
                    t.pop("maxItems", None)

                emit(pointer, "uniqueItems", f"uniqueItems over {bound} values -> {bound + 1}", r)
            elif ceiling is None or ceiling >= slots:

                def r(t: dict, _n: int = slots) -> None:
                    t.pop("uniqueItems", None)
                    t["minItems"] = _n
                    t["maxItems"] = _n

                emit(pointer, "uniqueItems", f"uniqueItems true -> {slots} draws, one schema", r)

        dependencies = node.get("dependencies")
        if isinstance(dependencies, dict):
            own = [k for k in node.get("required", []) if isinstance(k, str)]
            for trigger in sorted(dependencies):
                names = dependencies[trigger]
                if not isinstance(names, list):
                    continue  # the schema-valued form; its own keywords step themselves
                for dependent in names:
                    if not isinstance(dependent, str) or dependent == trigger:
                        continue
                    if dependent in own or trigger in own:
                        continue  # the node already settles presence; nothing to push out

                    def r(t: dict, _k: str = trigger, _d: str = dependent) -> None:
                        rest = {k: v for k, v in t.get("dependencies", {}).items() if k != _k}
                        t["dependencies"] = rest
                        if not rest:
                            t.pop("dependencies")
                        t["required"] = sorted({*t.get("required", []), _k})
                        t["not"] = {"required": [_d]}  # every instance omits the dependent

                    emit(pointer, "dependencies", f"{trigger!r} present, {dependent!r} not", r)

        n = node.get("minProperties")
        req = len([k for k in node.get("required", []) if isinstance(k, str)])
        if isinstance(n, int) and not isinstance(n, bool) and n > max(req, 0):
            # ``n > len(required)`` is the step's own satisfiability: an object with
            # at most n-1 keys still has to carry every required one, and a
            # ``minProperties`` no larger than the required count is already implied
            # by ``required`` -- stepping it would grade ``required`` under another
            # name.
            def r(t: dict, _n: int = n) -> None:
                t.pop("minProperties", None)
                t["maxProperties"] = _n - 1

            emit(pointer, "minProperties", f"minProperties {n} -> maxProperties {n - 1}", r)

        n = node.get("maxProperties")
        if isinstance(n, int) and not isinstance(n, bool) and _admits_more_than(node, n):

            def r(t: dict, _n: int = n) -> None:
                t.pop("maxProperties", None)
                t["minProperties"] = _n + 1

            emit(pointer, "maxProperties", f"maxProperties {n} -> minProperties {n + 1}", r)

        negated = node.get("not")
        if isinstance(negated, dict) and negated:
            # The general step, and the only one that needs no reading of the
            # subschema at all: the thing the document FORBIDS becomes a CONJUNCT,
            # so every instance satisfies it and the original refuses on ``not``.
            # An empty ``not`` is skipped because the document then admits nothing
            # and there is no instance to draw.
            def r(t: dict) -> None:
                t.setdefault("allOf", []).append(t.pop("not"))

            emit(
                pointer,
                "not",
                f"not {sorted(negated)} -> the same as a conjunct",
                r,
                states=negated,
                complement=True,
            )

        if isinstance(node.get("if"), dict):
            # A conditional is "if C then T", so an instance violating exactly it
            # satisfies C and violates T.  Both legs are stated as conjuncts and the
            # conditional itself is dropped, which makes the step exclusive: every
            # instance drawn matches the condition and fails the branch.  The
            # ``else`` leg is the same with C negated.
            for keyword in ("then", "else"):
                branch = node.get(keyword)
                if not isinstance(branch, dict) or not branch:
                    continue

                def r(t: dict, _k: str = keyword) -> None:
                    condition = t.pop("if")
                    taken = t.pop(_k)
                    t.pop("then", None)
                    t.pop("else", None)
                    t.setdefault("allOf", []).extend(
                        [condition if _k == "then" else {"not": condition}, {"not": taken}]
                    )

                emit(
                    pointer,
                    keyword,
                    f"if/{keyword} -> the condition, the branch negated",
                    r,
                    states=[node["if"], branch],
                    complement=True,
                )

        for keyword in ("oneOf", "anyOf"):
            branches = node.get(keyword)
            if not isinstance(branches, list) or not branches:
                continue
            # Violating a combinator means matching NO branch, which is a violation
            # of ``anyOf`` (at least one) and of ``oneOf`` (exactly one) alike.  So
            # every branch is negated as a conjunct.  A combinator exhaustive over
            # its own type has an UNSATISFIABLE negation and no violating instance
            # exists; the step is still emitted and ``check_refuses`` reports it as
            # ``no_evidence``, which is what a site with no instance is.  Screening
            # it here was tried and REMOVED: ``canonicalish`` on the rewritten node
            # cost 63.7 s against 0.0 s for 120 documents and rejected 0 of 2,205
            # sites, so it was 500x for no decision.
            def r(t: dict, _k: str = keyword) -> None:
                t.setdefault("allOf", []).extend({"not": b} for b in t.pop(_k))

            emit(
                pointer,
                keyword,
                f"{keyword} of {len(branches)} -> every branch negated",
                r,
                states=branches,
                complement=True,
            )

        for k, v in node.items():
            if k in _DESCEND_MAP and isinstance(v, dict):
                for kk, vv in v.items():
                    rec(vv, f"{pointer}/{k}/{_esc(kk)}")
            elif k in _DESCEND_ONE and isinstance(v, (dict, list)):
                rec(v, f"{pointer}/{k}")
            elif k in _DESCEND_LIST and isinstance(v, list):
                rec(v, f"{pointer}/{k}")

    rec(schema, "")
    out: list[Step] = []
    for key, positions in found.items():
        _, keyword, describe, _stated_value = key
        # Shallowest first, so the position a report NAMES is the outermost one
        # stating the fact rather than whichever the document happens to spell
        # first -- `rec` follows the document's own key order, which would make
        # the reported pointer a function of how the file was written.
        ordered = sorted(positions, key=lambda p: (p.count("/"), p))
        out.append(
            Step(keyword, describe, rewrites[key], tuple(ordered), complement=complements[key])
        )
    return out


def _stated(value: Any) -> str:
    """A stable identity for the value a rewrite is derived from.

    Digested rather than carried whole because the value is a SUBSCHEMA for every
    branch that passes one -- a resolved document's ``anyOf`` branch list is
    megabytes at the largest site -- and the key only ever needs equality.
    """
    if value is None:
        return ""
    text = json.dumps(value, sort_keys=True, default=str)
    return hashlib.blake2b(text.encode(), digest_size=16).hexdigest()


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
    outcome: str = "unrun"  # pass | model_refused_valid | strategy_error | model_error
    detail: str = ""
    counterexample: str = ""


@dataclass
class RefusesResult:
    keyword: str = ""
    pointer: str = ""
    describe: str = ""
    # every position the fact was stepped at; more than one means the document
    # restates it (a root and an `allOf` conjunct, say) and all of them were
    # rewritten together -- see `Step`
    positions: tuple[str, ...] = ()
    examples: int = 0
    control_fired: int = 0  # step did not push the instance out of the schema
    refused: int = 0
    accepted_invalid: int = 0
    error_types: dict[str, int] = field(default_factory=dict)
    # which keyword the ORIGINAL document actually rejected the instances on;
    # the step's own keyword is not a safe label (see violated_keywords)
    violated: dict[str, int] = field(default_factory=dict)
    counterexample: str = ""
    counterexample_violated: list[str] = field(default_factory=list)
    harness: str = ""
    #: The stepped document admits no instance at all, so there is nothing that
    #: violates exactly this keyword here.  Recorded rather than silently dropped,
    #: and NOT a harness error: see ``check_refuses``.  Written only for a
    #: COMPLEMENT step, where the emptiness is the document's own property.
    unsatisfiable: str = ""
    #: For a WITNESS step the harness could not build: the keywords stated at this
    #: step's instance location that it did not rewrite, each with its position.
    #: ``harness`` carries the same names, so a report that prints only the one
    #: line still names them; see ``contradicting``.
    collides: tuple[str, ...] = ()
    #: Set only where the whole GROUP admitted nothing and one position alone did
    #: bite: the position the instance was pushed out of.  ``positions`` still
    #: holds every position stating the fact, so the pair of them says the
    #: denominator came from one statement of it rather than all -- which is why
    #: it is recorded instead of left to be inferred from a smaller count.
    stepped_at: str = ""
    #: Set where the WITNESS strategy admitted nothing: the check could not DRAW an
    #: instance, so the obstruction is the GENERATOR and not the model.  ``harness``
    #: carries the same text and still makes this a ``harness_error``; this field is
    #: what :attr:`PairReport.no_instrument` reads to tell the two things
    #: ``harness_error`` means apart -- "hypothesis has no instance for this shape"
    #: and "the harness broke" -- which are not the same finding and do not have the
    #: same owner.  Written only for a WITNESS step, exactly as
    #: :attr:`unsatisfiable` is written only for a COMPLEMENT one.
    undrawable: str = ""

    @property
    def outcome(self) -> str:
        if self.harness:
            return "harness_error"
        if self.accepted_invalid:
            return "model_accepted_invalid"
        if self.refused:
            return "pass"
        return "no_evidence"  # control fired on every example: nothing was graded


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


def check_accepts(
    schema: dict,
    accept: Callable[[Any], Any],
    *,
    examples: int = 25,
    custom_formats: Mapping[str, Any] = (),
) -> AcceptsResult:
    """The accepts check: every instance the schema admits, ``accept`` admits.

    This is where a model NARROWER than its document fails, and the annotations
    are load-bearing here even behind a schema check: the schema half passes an
    instance it admits, and then the constructor runs on it.  A ``maxLength``
    the annotation invented, or a required field the model does not declare, is
    refused at construction and reported.
    """
    res = AcceptsResult()
    cf = dict(custom_formats)
    seen: list[Any] = []

    def body(instance: Any) -> None:
        res.examples += 1
        seen.append(instance)
        accept(instance)

    try:
        run = given(instance=strategy(schema, cf))(body)
        run = settings(
            max_examples=examples,
            phases=[Phase.explicit, Phase.generate, Phase.target, Phase.shrink],
            **_SETTINGS,
        )(run)
        run()
        res.outcome = "pass"
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


def check_refuses(
    schema: dict,
    accept: Callable[[Any], Any],
    step: Step,
    *,
    examples: int = 25,
    custom_formats: Mapping[str, Any] = (),
    force_path_to_site: bool = True,
) -> RefusesResult:
    """The refuses check: an instance violating exactly ``step.keyword`` is refused.

    **A WITNESS group that admits nothing is retried one position at a time**,
    because the obligation is to grade the KEYWORD at that location and a group
    is a claim about how many positions state it, not part of the obligation.
    Measured on ``core/inventory-list-application.json``, the only pair in the
    emitted 448 that reaches this: a ``required`` group over ``/oneOf/0`` and
    ``/oneOf/1`` dropping ``list_type``, which is the root ``discriminator``'s own
    propertyName.  Forbidding it in BOTH branches leaves the root ``oneOf``
    nothing to pick and the stepped document admits nothing; forbidding it in ONE
    leaves the other branch requiring it, so exactly one branch can match -- 6 of
    25 examples bite and the ORIGINAL refuses every one of them on ``required``.

    That is not a weaker step. The mutation stays exclusive at the position it is
    applied to; what shrinks is the DENOMINATOR, because the instance is pushed
    out of one statement of the fact and not all of them, and the control counts
    the rest. The lane that introduced grouping across a branch hop said so of
    that case already: the ORIGINAL document decides, so a group that pushes out
    only some branches reports a fired control and never a false pass.

    A COMPLEMENT step is NOT retried. Its emptiness is the document's own
    property rather than a witness the harness chose badly, so narrowing it would
    turn an honest ``no_evidence`` into a different question.

    ``force_path_to_site`` is passed to ``Step.materialize``; see ``force_path``
    for why the default is on and why it touches only the generated-from document.

    WHAT A GREEN RESULT CANNOT DISTINGUISH: where ``accept`` validates against
    the document before constructing, the refusal is implied by the control.
    ``violated_keywords`` asks the original document which keyword bit, and an
    entry point validating against that same document with the same library must
    then refuse -- so a pass says the entry point's accepted set is the
    document's, which is the obligation, and says nothing about whether the
    annotations underneath would have refused too.  ``compare_schema`` is what
    grades those.
    """
    whole = _refuses_once(
        schema,
        accept,
        step,
        examples=examples,
        custom_formats=custom_formats,
        force_path_to_site=force_path_to_site,
    )
    if whole.outcome != "harness_error" or len(step.positions) == 1:
        return whole
    for one in step.positions:
        narrowed = _refuses_once(
            schema,
            accept,
            dataclasses.replace(step, positions=(one,)),
            examples=examples,
            custom_formats=custom_formats,
            force_path_to_site=force_path_to_site,
        )
        if narrowed.refused or narrowed.accepted_invalid:
            # The fact is still stated at every position; only one was pushed out,
            # so the report keeps the group and names the position that bit.
            narrowed.positions = step.positions
            narrowed.stepped_at = one
            return narrowed
    return whole  # every position alone admits nothing too; report the group


def _refuses_once(
    schema: dict,
    accept: Callable[[Any], Any],
    step: Step,
    *,
    examples: int,
    custom_formats: Mapping[str, Any],
    force_path_to_site: bool,
) -> RefusesResult:
    """One attempt at ``step``, over exactly the positions it holds.

    Private, because which positions an attempt pushes out is ``check_refuses``'s
    decision and nothing outside it should be able to ask for a subset.
    """
    res = RefusesResult(
        keyword=step.keyword,
        pointer=step.pointer,
        describe=step.describe,
        positions=step.positions,
    )
    cf = dict(custom_formats)
    validator_cls = validator_for(schema)

    def body(instance: Any) -> None:
        res.examples += 1
        bit = violated_keywords(schema, instance, validator_cls=validator_cls)
        if not bit:
            res.control_fired += 1  # the step did not bite here; grades nothing
            return
        for k in bit:
            res.violated[k] = res.violated.get(k, 0) + 1
        try:
            accept(instance)
        except ValidationError as e:
            res.refused += 1
            t = e.errors()[0]["type"]
            res.error_types[t] = res.error_types.get(t, 0) + 1
        else:
            res.accepted_invalid += 1
            if not res.counterexample:
                res.counterexample = _dump(instance)
                res.counterexample_violated = bit

    try:
        run = given(instance=strategy(step.materialize(schema, force=force_path_to_site), cf))(body)
        run = settings(max_examples=examples, phases=[Phase.explicit, Phase.generate], **_SETTINGS)(
            run
        )
        run()
    except Unsatisfiable as e:
        # TWO DIFFERENT THINGS RAISE THIS and the verdict is not the same for
        # them, so the step says which it is (``Step.complement``) rather than
        # the catch site guessing from the exception, which is identical for
        # both -- an empty strategy and a filter nothing clears, measured.
        #
        # A COMPLEMENT step put the document's own statement back negated, so
        # what it admits IS the set of instances the document refuses here.
        # Empty means NO INSTANCE EXISTS that violates exactly this keyword at
        # this site, so nothing was graded -- ``no_evidence``, the
        # zero-denominator verdict, and NOT a harness error.  The distinction is
        # not cosmetic: a harness error reddens the whole pair, so this would
        # fail a class that is perfectly faithful.  The shapes are an
        # ``if``/``then`` whose condition implies its branch and a combinator
        # exhaustive over its own type (``anyOf`` of ``string`` and
        # ``not string``).
        #
        # A WITNESS step substituted a bound the HARNESS chose, so empty means
        # only that this witness does not exist -- the document still refuses
        # what the keyword forbids, and the check simply could not build an
        # instance.  That is reported, with the contradicting keyword named,
        # because §6 forbids a green mark over a site nothing graded and
        # ``no_evidence`` is in ``PairReport``'s admitted set.
        detail = f"{type(e).__name__}: {e}"[:160]
        if step.complement:
            res.unsatisfiable = detail
        else:
            res.collides = contradicting(schema, step)
            named = ", ".join(res.collides) or "nothing at this instance location"
            res.harness = f"{detail} | contradicted by: {named}"[:300]
            res.undrawable = f"contradicted by {named}; {_why(e)}"[:300]
    except Exception as e:
        res.harness = f"{type(e).__name__}: {e}"[:300]
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
      literal that omits the type.
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


def _narrows_nothing(keyword: str, value: Any, doc: dict) -> bool:
    """Does a model-only fact narrow the document's accepted set, or not?

    A fact the model states and the document does not is reported, because that
    is how a model NARROWER than its document shows up.  Three kinds narrow
    nothing; two of them are 57 of the 57 model-only facts step 1's and step 2's
    population has, and the third arrived with step 5's union roots:

    * **``default: null``**, 56 of them.  D4 renders an optional property
      ``T | None = None``, because a Python attribute holds ``None`` for an
      omitted key, and pydantic reports that as a default.  It is how absence is
      spelled in Python, not a claim about the document: presence is the schema's
      ``required`` axis and that is compared in both directions.  A model-only
      ``default`` with any OTHER value IS an added claim and is reported -- the
      difference between "absent renders as None" and "the generator invented a
      default".
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
        return value is None and "null" not in str(doc.get("type", ""))
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
    ``include_unknown`` is a plain boolean.
    """
    for canonical, kind in _FINITE:
        if doc == canonical:
            return {"type": kind}, True
    return doc, False


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


def _normalize(node: Any, defs: Mapping[str, Any], depth: int = 0) -> dict:
    """The model's node for one position, written the way the document writes it.

    Three normalizations, and each one is forced by a decision this pipeline made
    rather than by anything arbitrary in pydantic:

    * **``$ref`` into ``$defs``.**  A nested object is a nested CLASS and a
      cross-document reference is an IMPORT (P2), so pydantic hoists both into
      ``$defs`` and references them.  The document the class names is resolved,
      so the same facts are inline there.
    * **An ``anyOf`` with a ``null`` branch.**  D4 renders an optional property
      ``T | None``, because the attribute holds ``None`` for an omitted key.
      pydantic states that as a union; the document states the type and leaves
      presence to ``required``.  Unwrapping the null branch compares like with
      like.
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
    * **The outer keys win.**  ``default`` and ``description`` sit outside the
      ``anyOf`` and the type facts inside the branch.
    """
    if depth > 16 or not isinstance(node, dict):  # a self-referential $defs chain
        return node if isinstance(node, dict) else {}
    if "$ref" in node:
        name = str(node["$ref"]).rsplit("/", 1)[-1]
        target = defs.get(name)
        outer = {k: v for k, v in node.items() if k != "$ref"}
        return {**_normalize(target, defs, depth + 1), **outer} if target is not None else outer
    branches = node.get("anyOf")
    if isinstance(branches, list) and branches and all(isinstance(b, dict) for b in branches):
        live = [b for b in branches if b.get("type") != "null"]
        nulls = [b for b in branches if b.get("type") == "null"]
        outer = {k: v for k, v in node.items() if k != "anyOf"}
        if len(nulls) == 1 and len(live) == 1:
            return {**_normalize(live[0], defs, depth + 1), **outer}
        if len(nulls) <= 1 and len(live) > 1 and all(set(b) == {"type"} for b in live):
            return {"type": [b["type"] for b in live], **outer}
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
        c = _composed(conjunct, depth + 1)
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


def compare_schema(schema: dict, model: Any) -> ComparisonResult:
    """The document's facts and the model's, compared in BOTH directions.

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
    defs = emitted.get("$defs", {})

    def compare(doc: Any, got: Any, pointer: str) -> None:
        if not isinstance(doc, dict):
            return
        # The document side is read the way the schema half reads it: a conjunct's
        # facts are the document's (see `_composed`).  At every node, not only at
        # the root -- a property's own node composes too, and the pydantic side is
        # flattened at every depth, so one call in the recursion is the whole of it.
        doc = _composed(doc)
        got = _normalize(got, defs)
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
                _narrows_nothing(kw, got[kw], doc)
                or (rewritten and kw == "description")
                or (rewritten and kw == "default" and _admitted(got[kw], doc))
            ):
                continue
            res.added.append(f"{pointer}/{kw}: the model says {got[kw]!r}, the document nothing")

        props = doc.get("properties") or {}
        mine = got.get("properties") if isinstance(got.get("properties"), dict) else {}
        if isinstance(props, dict):
            for key in sorted(props):
                at = f"{pointer}/properties/{_esc(key)}"
                if key not in mine:
                    res.compared += 1
                    res.missing.append(f"{at}: the model declares no such property")
                    continue
                compare(props[key], mine[key], at)
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


@dataclass
class PairReport:
    name: str
    model_repr: str = ""
    accepts: AcceptsResult | None = None
    refuses: list[RefusesResult] = field(default_factory=list)
    comparison: ComparisonResult | None = None
    step_sites: int = 0
    missing_formats: list[str] = field(default_factory=list)
    #: The DOCUMENT's own positions where a ``format`` and a ``pattern`` meet,
    #: filled by :func:`check_pair` because a report does not hold the document it
    #: graded.  Read by :attr:`no_instrument` to name the shape behind an accepts
    #: check that could not draw.
    accepts_filtered_formats: tuple[str, ...] = ()

    @property
    def graded_instances(self) -> int:
        """The refuses check's denominator: instances that reached the model.

        An instance the step failed to push out of the document grades nothing
        and is counted by the control instead.
        """
        return sum(r.refused + r.accepted_invalid for r in self.refuses)

    @property
    def no_instrument(self) -> tuple[str, ...]:
        """Every check of this pair that could not DRAW, each with its CAUSE.

        **Tracking, with no ratchet on it, and that is the decision rather than an
        omission.**  A shrink-only count assumes a fixed or shrinking population and
        the emitted tree GROWS every merge, so each new batch of documents can
        legitimately contribute new undrawable pairs and a shrink-only gate would
        redden on correct work.  It can only shrink once ``hypothesis`` draws these
        shapes, which is unscheduled, so shrink-only is unachievable in principle and
        not merely premature.

        **The CAUSE matters more than the count**, because this is the population the
        eventual generator work starts from, so each entry names a shape to act on
        rather than "cannot draw":

        * the ACCEPTS check reports hypothesis's own message -- which carries the
          filtered-draw count -- beside the document's own positions where a
          ``format`` and a ``pattern`` meet (:func:`filtered_formats`), because that
          is the shape ``hypothesis_jsonschema``'s ``string_schema`` filters and
          cannot satisfy.  The positions are DERIVED from the document, not guessed:
          hypothesis raises over the whole schema and names no node.
        * a REFUSES step reports its keyword, its position and what contradicts it,
          all of which the step already knows.
        """
        out: list[str] = []
        if self.accepts is not None and self.accepts.outcome == "strategy_error":
            where = "; ".join(self.accepts_filtered_formats) or (
                "no format-beside-pattern position in this document"
            )
            why = self.accepts.detail.split(" Try making")[0].strip()[:200]
            out.append(f"accepts: {where}; {why}")
        out += [
            f"refuses {r.keyword!r} at {r.pointer or '/'}: {r.undrawable}" for r in self.refuses if r.undrawable
        ]
        return tuple(out)

    @property
    def outcome(self) -> str:
        """One verdict for the pair, and **a zero denominator is a refusal**.

        Structural here rather than a convention a caller is trusted to apply,
        because a report can enforce it and a reader cannot.  What it guards is a
        pair no instance reached: an entry point raising an exception this module
        does not catch leaves every step at ``harness_error`` with nothing
        graded.  It is NOT what catches a model wider than its document --
        measured, a model with ``Any`` on every field passes the refuses check
        over the same 75 instances a faithful one does, so the denominator is
        identical and the schema comparison is the only check that separates
        them.
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
        bad = [
            r.outcome
            for r in self.refuses
            if r.outcome not in ("pass", "no_evidence") and not r.undrawable
        ]
        if bad:
            return "refuses:" + bad[0]
        if self.comparison is None or self.comparison.outcome not in ("pass", "no_evidence"):
            return "comparison:" + (self.comparison.outcome if self.comparison else "unrun")
        # AFTER the comparison, so a model defect is never reported as an instrument
        # one, and BEFORE the two zero-denominator verdicts, so a pair whose steps
        # were all undrawable names that instead of "nothing was graded".
        if self.no_instrument:
            return "no_instrument"
        if not self.step_sites:
            return "no_constraint_to_step"  # the document states nothing to step
        if not self.graded_instances:
            return "no_refuses_check_evidence"
        return "pass"


def check_pair(
    pair: Pair,
    *,
    accepts_examples: int = 25,
    refuses_examples: int = 25,
    max_steps: int | None = 4,
    custom_formats: Mapping[str, Any] = (),
) -> PairReport:
    rep = PairReport(
        name=pair.name, model_repr=getattr(pair.model, "__name__", repr(pair.model))[:120]
    )
    rep.missing_formats = sorted(missing_formats(pair.schema, custom_formats))
    rep.accepts_filtered_formats = filtered_formats(pair.schema)
    rep.accepts = check_accepts(
        pair.schema, pair.accept, examples=accepts_examples, custom_formats=custom_formats
    )
    all_steps = steps(pair.schema)
    rep.step_sites = len(all_steps)
    chosen = _spread(all_steps, max_steps)
    for s in chosen:
        rep.refuses.append(
            check_refuses(
                pair.schema,
                pair.accept,
                s,
                examples=refuses_examples,
                custom_formats=custom_formats,
            )
        )
    rep.comparison = compare_schema(pair.schema, pair.model)
    return rep


def _spread(all_steps: list[Step], limit: int | None) -> list[Step]:
    """Pick up to ``limit`` steps, one per keyword before repeating any."""
    if limit is None or len(all_steps) <= limit:
        return all_steps
    by_kw: dict[str, list[Step]] = {}
    for s in all_steps:
        by_kw.setdefault(s.keyword, []).append(s)
    out: list[Step] = []
    while len(out) < limit:
        progressed = False
        for kw in sorted(by_kw):
            if by_kw[kw]:
                out.append(by_kw[kw].pop(0))
                progressed = True
                if len(out) >= limit:
                    break
        if not progressed:
            break
    return out
