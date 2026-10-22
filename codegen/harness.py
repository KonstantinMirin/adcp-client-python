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
import json
import re
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, TypeGuard

import jsonschema
from hypothesis import HealthCheck, Phase, given, settings
from hypothesis import strategies as st
from hypothesis.errors import HypothesisException
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
    """A constraint site, and how to rewrite it. The rewrite is NOT applied yet.

    ``steps()`` finds every site by walking the document once and copies nothing:
    a resolved document can be megabytes with thousands of sites, and
    deep-copying it per site cost 93 s on a 214-site document before this was
    made lazy. ``materialize`` produces the stepped document for the sites a
    caller actually grades.
    """

    keyword: str  # the constraint that was stepped, as the document spells it
    pointer: str  # JSON Pointer to the subschema it was stepped at
    describe: str  # human-readable "before -> after"
    _rewrite: Callable[[dict], None]

    def materialize(self, schema: dict, *, force: bool = True) -> dict:
        """The stepped document to GENERATE from. The original still decides.

        ``force`` makes the path down to the site mandatory (see ``force_path``).
        It is on because a site the generator never populates grades nothing;
        ``force=False`` exists so a measurement can draw the unforced case from
        the same inputs in the same process, and nothing else passes it.
        """
        doc = force_path(schema, self.pointer) if force else copy.deepcopy(schema)
        self._rewrite(at(doc, "" if self.pointer == "/" else self.pointer))
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
# ``not`` / ``if`` / ``then`` / ``else`` / ``propertyNames`` subschema or a
# ``$defs`` entry has no instance location to make mandatory at all, so a site
# beneath one stays unreachable and the control still counts it as ungraded.
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
        else:
            node = node[int(k)] if isinstance(node, list) else node[k]
            i += 1
    return doc


def _is_index(part: str | None) -> TypeGuard[str]:
    return part is not None and part.isdigit()


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


def steps(schema: dict) -> list[Step]:
    """Every constraint keyword in the document, each as one exclusive step."""
    out: list[Step] = []

    def emit(pointer: str, keyword: str, describe: str, rewrite: Callable[[dict], None]) -> None:
        out.append(Step(keyword, pointer or "/", describe, rewrite))

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

        for k, v in node.items():
            if k in _DESCEND_MAP and isinstance(v, dict):
                for kk, vv in v.items():
                    rec(vv, f"{pointer}/{k}/{_esc(kk)}")
            elif k in _DESCEND_ONE and isinstance(v, (dict, list)):
                rec(v, f"{pointer}/{k}")
            elif k in _DESCEND_LIST and isinstance(v, list):
                rec(v, f"{pointer}/{k}")

    rec(schema, "")
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
    outcome: str = "unrun"  # pass | model_refused_valid | strategy_error | model_error
    detail: str = ""
    counterexample: str = ""


@dataclass
class RefusesResult:
    keyword: str = ""
    pointer: str = ""
    describe: str = ""
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
    res = RefusesResult(keyword=step.keyword, pointer=step.pointer, describe=step.describe)
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
    except Exception as e:
        res.harness = f"{type(e).__name__}: {e}"[:300]
    return res


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


def _narrows_nothing(keyword: str, value: Any, doc: dict) -> bool:
    """Does a model-only fact narrow the document's accepted set, or not?

    A fact the model states and the document does not is reported, because that
    is how a model NARROWER than its document shows up.  Two kinds narrow
    nothing, and they are 57 of the 57 model-only facts this population has:

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
    """
    if keyword == "default":
        return value is None and "null" not in str(doc.get("type", ""))
    return keyword == "additionalProperties" and value is True


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
        got = _normalize(got, defs)
        for kw in FACTS:
            if kw not in doc:
                continue
            res.compared += 1
            where = f"{pointer}/{kw}"
            if kw not in got:
                res.missing.append(f"{where}: the document says {doc[kw]!r}")
                continue
            a, b = doc[kw], got[kw]
            if kw == "additionalProperties":
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
            if _narrows_nothing(kw, got[kw], doc):
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

    @property
    def graded_instances(self) -> int:
        """The refuses check's denominator: instances that reached the model.

        An instance the step failed to push out of the document grades nothing
        and is counted by the control instead.
        """
        return sum(r.refused + r.accepted_invalid for r in self.refuses)

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
        if self.accepts is None or self.accepts.outcome != "pass":
            return "accepts:" + (self.accepts.outcome if self.accepts else "unrun")
        bad = [r.outcome for r in self.refuses if r.outcome not in ("pass", "no_evidence")]
        if bad:
            return "refuses:" + bad[0]
        if self.comparison is None or self.comparison.outcome not in ("pass", "no_evidence"):
            return "comparison:" + (self.comparison.outcome if self.comparison else "unrun")
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
