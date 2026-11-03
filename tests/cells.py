"""§5's cells, one at a time: a probe document per cell and the witnesses it names.

``docs/plan/rebuild-plan.md`` §8, *"THE TWO CHECKS ARE APPLIED COMPOSITIONALLY, AND
CERTAINTY COMES FROM THE TABLE"*, is this module's whole specification, and it is quoted
rather than paraphrased:

    **AND CERTAINTY ITSELF COMES FROM §5's TABLE, NOT FROM THE DRAW.**  §5 is a keyword x
    position decision table: each cell says what one keyword at one position compiles to.
    **Prove each cell once** -- the annotation it emits admits exactly the values that
    keyword admits at that position, against the boundary values the keyword itself names
    -- and **prove each composition rule once** -- ``allOf`` intersects, ``anyOf`` unions,
    a restatement merges -- and faithfulness over any document follows **by structural
    induction on the document**.  The obligation becomes the table's cells plus the
    composition rules, which is finite and terminates, and it covers documents no draw
    will ever reach.

**THIS IS NOT A THIRD CHECK, AND THE REASON IS THE ONE §8 GIVES FOR DELETING ONE.**  The
deleted instrument compared a class's ``model_json_schema()`` against the document, which
"diffed schema TEXT" and "produced 1,086 'facts' over 155 pairs that no payload had ever
demonstrated".  Every cell proof here is a **drawn payload**: a value is placed at the
position's instance location, the DOCUMENT is asked about it through
``harness.conforms`` -- the same reading the run uses, with ``format`` asserted -- and
the emitted class is asked about the same value.  One value, two verdicts.  Nothing in
this module reads generated text against document text, and nothing asserts an
annotation, a field list or a rule tuple.

**WHY A CELL AND NOT A DOCUMENT.**  §8 measured why the draw cannot finish: the
canonicaliser enumerates **every SUBSET** of a union's branches, so an eighteen-branch
site is 262,143 subsets of which 0.19% complete inside 60 s, and 86 of 2,793 pairs return
no verdict at any budget -- "it is ``2^n``: a constant factor is not available".  A cell
is one keyword at one position inside a two-keyword probe, so the cost of a cell proof is
a function of the KEYWORD and not of any document that states it.  That is the whole
point: the set this module ranges over reaches the 86 documents no draw will ever finish,
because it never looks at a whole document.

**WHERE THE WITNESSES COME FROM, and it is not a sample.**  §8: "The draw COVERS the
node's admissible space by constraint class; it does not sample it. ... For each keyword
the node states, the draw takes the classes that keyword distinguishes: every member of an
``enum``, both sides of each bound and the bound itself".  So ``maxLength: 3`` names
``""``, ``"abc"`` and ``"abcd"``; ``minimum: 0`` names ``-1``, ``0`` and ``1``; an ``enum``
names its members and a non-member.  The keyword names its own witnesses and this module
invents no sample, which is why :data:`NODES` carries the witnesses BESIDE the node that
states the keyword rather than deriving them from a generator.

**WHAT A PROOF ASSERTS, in the two directions §2 gives them.**  A value the document
ADMITS and the class refuses is a NARROWING, which §2 forbids outright and which this
module fails on unconditionally.  A value the document REFUSES and the class admits is a
WIDENING, which §2 permits only as a DECLARED approximation -- so it passes exactly where
the run declares one at that document, and fails where it does not.  §8: "An approximation
that still refuses a value the document admits is a NARROWING wearing a declaration, and
it fails here, by value and by pointer.  That is what keeps the declared set from being an
allowlist."

**THE POSITION WRAPPERS ARE THE DESCENT COLUMN'S, not a second reading of it.**  §3 gives
nine positions and ``keywords.descends_at(Position.ROOT)`` says which keyword reaches each
one: ``properties`` reaches PROP, ``items`` and ``contains`` reach ELEM,
``additionalProperties`` and ``patternProperties`` reach MAPV, ``propertyNames`` reaches
KEY, ``oneOf``/``anyOf`` reach BRANCH, ``allOf`` reaches CONJ, the four conditionals reach
RULE, and ``definitions``/``$defs`` reach DEF.  :func:`wrap` is that column read as a
constructor, and :func:`test_every_wrapper_descends_by_the_column` is the equality.

**AND EVERY POSITION'S INSTANCE LOCATION IS §8's, which it settled on 2026-10-27**: "The
draw places a value at the instance location the node's pointer names, and a position with
no location makes a widening UNPROVABLE".  A mapping value's location is "``x`` then any
key the mapping admits; a key is a free choice and the draw makes one" --
:data:`MAPPING_KEY`.  A ``definitions`` entry "has no location of its own and never will:
an entry is reachable only through a ``$ref`` that names it", and the settlement
"re-points it to the referring pointer, which is a ``properties`` segment the draw already
places" -- which is exactly what the DEF wrapper builds.
"""

from __future__ import annotations

import functools
import json
import sys
import tempfile
import types
from pathlib import Path
from typing import Any, NamedTuple

from pydantic import TypeAdapter

from codegen import bundle, emit, harness, keywords
from codegen.keywords import Position

DRAFT = "http://json-schema.org/draft-07/schema#"
REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "schemas" / "cache" / "3.2"

#: The one key a MAPV probe places its witness under, and the one key a KEY probe places
#: where the witness cannot be a key.  §8's "a key is a free choice and the draw makes
#: one", made once here rather than per cell so no cell's verdict turns on the choice.
MAPPING_KEY = "k"

#: The property a RULE probe's CONSEQUENT requires.  A rule position states a condition,
#: so the witness that distinguishes the condition is the instance that matches it
#: WITHOUT the consequent satisfied beside the instance that matches it WITH -- which is
#: what :func:`witnesses_at` builds, and this is the name the consequent names.
GUARD = "g"

#: The document a cross-document ``$ref`` names, which is what §5's ``$ref`` row compiles
#: FIRST ("Another document's root -> an IMPORT of that module's symbol").  A LOCAL root
#: ``$ref`` is a verdict ("a pointer into this document, which is not a binding at all"),
#: so the row's probe is the cross-document form and the local form is the DEF wrapper's.
TARGET_URI = "https://adcontextprotocol.org/schemas/3.2.4/core/target.json"
TARGET = {"$schema": DRAFT, "title": "T", "type": "string", "maxLength": 3}
#: A CLASS target, for the ``$ref`` row at CONJ: §5 makes a ``$ref`` conjunct a BASE, and
#: "where it is not [a class] -- a scalar, an enum, a container, or a union root -- it is
#: not a class a model can extend".  The bundle's own ``$ref`` conjuncts are envelopes.
ENVELOPE_URI = "https://adcontextprotocol.org/schemas/3.2.4/core/envelope.json"
ENVELOPE = {
    "$schema": DRAFT,
    "title": "Envelope",
    "type": "object",
    "properties": {"ver": {"type": "string"}},
    "required": ["ver"],
}
#: An ENUM target, for the ``enum`` row at CONJ: §5's cell is "CONJ beside a ``$ref``
#: whose target is an enumeration -> §2's intersection of the two vocabularies".
VOCAB_URI = "https://adcontextprotocol.org/schemas/3.2.4/core/vocab.json"
VOCAB = {"$schema": DRAFT, "title": "Vocab", "type": "string", "enum": ["a", "b", "c"]}

_S = {"type": "string"}


def _obj(**props: Any) -> dict:
    return {"type": "object", "properties": dict(props)}


class Probe(NamedTuple):
    """The smallest node stating one keyword, and the witnesses that keyword names."""

    node: dict
    witnesses: tuple[Any, ...]
    #: **Which conditional holds the node at a RULE position**, where it is not ``if``.
    #: §3's RULE position is reached by four keywords, not one
    #: (``keywords.descends_at(Position.ROOT)[...]`` is ``else``, ``if``, ``not``,
    #: ``then``), and §5 gives several rows a cell *per conditional*: the ``anyOf`` row
    #: reads "RULE: under ``not`` -> the union of the branches' groups; else nothing",
    #: and the ``allOf`` row "under ``not`` -> single-group conjuncts merge into one
    #: group; else nothing".  So a RULE probe that always used ``if`` would grade the
    #: *else nothing* half of those cells and report the other half's absence as a
    #: widening.  The conditional is the cell's and is named with it.
    under: str = "if"


# --------------------------------------------------------------------------- #
# the default probe per keyword
# --------------------------------------------------------------------------- #
#: One entry per keyword with a live cell.  The node is the SMALLEST node stating the
#: keyword, and the witnesses are the boundary values §8 says the keyword distinguishes:
#: every member of an ``enum`` and a non-member, both sides of each bound and the bound
#: itself, one value per ``type`` word, the pinned value and another.
NODES: dict[str, Probe] = {
    "type": Probe({"type": "string"}, ("s", 1, True, None, [], {})),
    "properties": Probe(_obj(a=_S), ({"a": "s"}, {"a": 1}, {})),
    "required": Probe({**_obj(a=_S), "required": ["a"]}, ({"a": "s"}, {})),
    "$ref": Probe({"$ref": TARGET_URI}, ("", "abc", "abcd")),
    "const": Probe({"const": "x"}, ("x", "y")),
    "enum": Probe({"enum": ["a", "b"]}, ("a", "b", "z")),
    "default": Probe({"type": "string", "default": "d"}, ("s",)),
    "pattern": Probe({"type": "string", "pattern": "^a+$"}, ("", "a", "aa", "b")),
    "format": Probe(
        {"type": "string", "format": "date-time"},
        ("2026-01-01T00:00:00Z", "not-a-date"),
    ),
    "minLength": Probe({"type": "string", "minLength": 2}, ("a", "ab", "abc")),
    "maxLength": Probe({"type": "string", "maxLength": 3}, ("", "abc", "abcd")),
    "minimum": Probe({"type": "integer", "minimum": 0}, (-1, 0, 1)),
    "maximum": Probe({"type": "integer", "maximum": 5}, (4, 5, 6)),
    "exclusiveMinimum": Probe({"type": "integer", "exclusiveMinimum": 0}, (-1, 0, 1)),
    "exclusiveMaximum": Probe({"type": "integer", "exclusiveMaximum": 5}, (4, 5, 6)),
    "multipleOf": Probe({"type": "integer", "multipleOf": 3}, (3, 4)),
    "items": Probe({"type": "array", "items": _S}, ([], ["s"], [1])),
    "minItems": Probe(
        {"type": "array", "items": _S, "minItems": 2},
        (["a"], ["a", "b"], ["a", "b", "c"]),
    ),
    "maxItems": Probe(
        {"type": "array", "items": _S, "maxItems": 2}, (["a", "b"], ["a", "b", "c"])
    ),
    "uniqueItems": Probe(
        {"type": "array", "items": _S, "uniqueItems": True}, (["a", "b"], ["a", "a"])
    ),
    "contains": Probe(
        {"type": "array", "items": _S, "contains": {"const": "a"}},
        ([], ["a"], ["b"], ["b", "a"]),
    ),
    "additionalProperties": Probe(
        {**_obj(a=_S), "additionalProperties": False}, ({"a": "s"}, {"a": "s", "z": 1})
    ),
    "patternProperties": Probe(
        {"type": "object", "patternProperties": {"^a": _S}},
        ({"ab": "s"}, {"ab": 1}, {}),
    ),
    "propertyNames": Probe(
        {"type": "object", "propertyNames": {"type": "string", "maxLength": 3}},
        ({"abc": 1}, {"abcd": 1}, {}),
    ),
    "minProperties": Probe(
        {"type": "object", "additionalProperties": True, "minProperties": 2},
        ({"a": 1}, {"a": 1, "b": 2}),
    ),
    "maxProperties": Probe(
        {"type": "object", "additionalProperties": True, "maxProperties": 2},
        ({"a": 1, "b": 2}, {"a": 1, "b": 2, "c": 3}),
    ),
    "dependencies": Probe(
        {**_obj(a=_S, b=_S), "dependencies": {"a": ["b"]}},
        ({"a": "x"}, {"a": "x", "b": "y"}, {"b": "y"}, {}),
    ),
    "allOf": Probe(
        {
            "allOf": [
                _obj(a={"type": "string", "minLength": 2}),
                _obj(a={"type": "string", "maxLength": 3}),
            ]
        },
        ({"a": "a"}, {"a": "ab"}, {"a": "abc"}, {"a": "abcd"}),
    ),
    "anyOf": Probe(
        {"anyOf": [{**_obj(a=_S), "required": ["a"]}, {**_obj(b=_S), "required": ["b"]}]},
        ({"a": "x"}, {"b": "y"}, {"a": "x", "b": "y"}, {}),
    ),
    "oneOf": Probe(
        {"oneOf": [{**_obj(a=_S), "required": ["a"]}, {**_obj(b=_S), "required": ["b"]}]},
        ({"a": "x"}, {"b": "y"}, {"a": "x", "b": "y"}, {}),
    ),
    "if": Probe(
        {
            **_obj(a=_S, b=_S),
            "if": {"required": ["a"], "properties": {"a": {"const": "x"}}},
            "then": {"required": ["b"]},
        },
        ({"a": "x"}, {"a": "x", "b": "y"}, {"a": "z"}, {}),
    ),
    "then": Probe(
        {
            **_obj(a=_S, b=_S),
            "if": {"required": ["a"], "properties": {"a": {"const": "x"}}},
            "then": {"required": ["b"]},
        },
        ({"a": "x"}, {"a": "x", "b": "y"}, {"a": "z"}, {}),
    ),
    "else": Probe(
        {
            **_obj(a=_S, b=_S),
            "if": {"required": ["a"], "properties": {"a": {"const": "x"}}},
            "else": {"required": ["b"]},
        },
        ({"a": "x"}, {"a": "z"}, {"a": "z", "b": "y"}, {}),
    ),
    "not": Probe(
        {**_obj(a=_S), "additionalProperties": True, "not": {"required": ["a"]}},
        ({"a": "x"}, {}, {"z": 1}),
    ),
}

# --------------------------------------------------------------------------- #
# the cells whose SMALLEST stating node is a different node at the position
# --------------------------------------------------------------------------- #
#: A cell is ``(keyword, position)`` and the smallest node STATING that keyword at that
#: position is not always the keyword's default node -- a RULE position states a
#: CONDITION, and a CONJ position states a conjunct §5 gives the keyword a cell for.
#: Each entry below is the shape the BUNDLE states at that cell, reduced to the two
#: keywords the cell is about; the document and pointer it was read off is named, so the
#: shape is the bundle's and not a guess about what the compiler will accept.
AT: dict[tuple[str, Position], Probe] = {
    # ``{"contains": {...}}`` alone in the conjunct, with no type word beside it:
    # creative/list-creatives-response.json
    # #/properties/creatives/items/properties/assignments/properties/assigned_packages
    # /items/allOf/3/then/properties/approval_scopes/allOf/0
    ("contains", Position.CONJ): Probe(
        {"contains": {"properties": {"s": {"const": "approved"}}}},
        ([], [{"s": "approved"}], [{"s": "other"}]),
    ),
    # ``{"maxProperties": 1}`` alone in the conjunct: core/media-buy-support.json
    # #/not/allOf/1
    ("maxProperties", Position.CONJ): Probe(
        {"maxProperties": 1}, ({}, {"a": 1}, {"a": 1, "b": 2})
    ),
    # ``type: object`` with ``properties``, which is every ``type`` conjunct the bundle
    # states: brand.json #/oneOf/4/allOf/0
    ("type", Position.CONJ): Probe(_obj(a=_S), ({"a": "s"}, {"a": 1})),
    # ``additionalProperties`` at a conjunct is ``true`` -- §5: "``true`` is the identity
    # and contributes nothing" -- beside the properties it admits extras of:
    # core/demographic-targeting-intent.json #/properties/age/allOf/1
    ("additionalProperties", Position.CONJ): Probe(
        {**_obj(a=_S), "additionalProperties": True}, ({"a": "s"}, {"a": "s", "z": 1})
    ),
    # §5's ``enum`` cell at CONJ: "beside a ``$ref`` whose target is an enumeration ->
    # §2's intersection of the two vocabularies": core/creative-approval-scope.json
    # #/properties/approval_status/allOf/1
    ("enum", Position.CONJ): Probe({"enum": ["a", "b"]}, ("a", "b", "c", "z")),
    # §5's ``$ref`` cell at CONJ: "a BASE where the target is a class declaring fields":
    # account/get-account-financials-request.json #/allOf/0
    ("$ref", Position.CONJ): Probe(
        {"$ref": ENVELOPE_URI}, ({"ver": "1"}, {}, {"ver": 1})
    ),
    # A RULE position states a CONDITION, and §5's ``if`` cell reads one only where it
    # "states ``required`` plus ``properties`` with ``const`` or ``enum`` values".  So the
    # probe at a RULE position is that form: aao/agent-publishers.json
    # #/definitions/PublisherEntry/allOf/0/if and /then.
    ("properties", Position.RULE): Probe(
        {"required": ["a"], "properties": {"a": {"const": "x"}}},
        ({"a": "x"}, {"a": "z"}, {}),
    ),
    ("required", Position.RULE): Probe(
        {"required": ["a"], "properties": {"a": {"const": "x"}}},
        ({"a": "x"}, {"a": "z"}, {}),
    ),
    # §5's ``anyOf`` cell at RULE: "under ``not`` -> the union of the branches' groups":
    # account/get-account-financials-response.json #/oneOf/1/not
    ("anyOf", Position.RULE): Probe(
        {"anyOf": [{"required": ["a"]}, {"required": ["b"]}]},
        ({}, {"a": "x"}, {"b": "y"}, {"a": "x", "b": "y"}),
        under="not",
    ),
    # §5's ``allOf`` cell at RULE: "under ``not`` -> single-group conjuncts merge into one
    # group": core/creative-operation-format-declaration.json #/allOf/3/not
    ("allOf", Position.RULE): Probe(
        {"allOf": [{"required": ["a"]}, {"required": ["b"]}]},
        ({}, {"a": "x"}, {"b": "y"}, {"a": "x", "b": "y"}),
        under="not",
    ),
    # §5's ``not`` cell: ``not: {required: ...}`` -> a ``ForbiddenGroups`` rule, at a RULE
    # position inside a ``then``: account/sync-accounts-response.json
    # #/oneOf/0/properties/accounts/items/allOf/0/then
    ("not", Position.RULE): Probe(
        {"not": {"required": ["a"]}}, ({}, {"a": "x"}, {"b": "y"}), under="then"
    ),
    # §5's ``if`` and ``then`` cells at a RULE position: a conditional nested inside
    # another conditional's ``else``, which is the one shape the bundle states them at --
    # core/reporting-schedule-offering.json #/allOf/0/else.
    ("if", Position.RULE): Probe(
        {
            "if": {"required": ["b"], "properties": {"b": {"const": "y"}}},
            "then": {"required": [GUARD]},
        },
        ({"b": "y"}, {"b": "z"}, {}),
        under="else",
    ),
    ("then", Position.RULE): Probe(
        {
            "if": {"required": ["b"], "properties": {"b": {"const": "y"}}},
            "then": {"required": [GUARD]},
        },
        ({"b": "y"}, {"b": "z"}, {}),
        under="else",
    ),
    # §5's ``else`` cell at a RULE position, by the same shape with the inner arm negated.
    ("else", Position.RULE): Probe(
        {
            "if": {"required": ["b"], "properties": {"b": {"const": "y"}}},
            "else": {"required": [GUARD]},
        },
        ({"b": "y"}, {"b": "z"}, {}),
        under="else",
    ),
}

#: The outer condition a ``then``-held or ``else``-held RULE probe is reached through,
#: and the key it tests.  One condition, declared once: a probe whose outer condition
#: differed per cell would make a cell's verdict a function of the wrapper.
TRIGGER = "t"
OUTER = {"required": [TRIGGER], "properties": {TRIGGER: {"const": "on"}}}


def is_a_class_node(node: dict) -> bool:
    """Does this node become a CLASS rather than a scalar, an alias or a container?

    §5's ``oneOf``/``anyOf`` cell: "A root union with a scalar branch beside a class
    branch -> refused by name: the root symbol is a class or an alias, no shape in §4
    carries both".  So a BRANCH probe's companion branch has to be the same kind as the
    node under test, and this is the bit that decides which -- read off the keywords that
    make a node an object, which is the ARM table's own object column plus the three
    object-only structural keywords.
    """
    return node.get("type") == "object" or any(
        k in node
        for k in (
            "properties",
            "required",
            "additionalProperties",
            "patternProperties",
            "propertyNames",
            "dependencies",
            "minProperties",
            "maxProperties",
            "if",
            "then",
            "else",
            "not",
            "allOf",
            "anyOf",
            "oneOf",
        )
    )


#: The companion a BRANCH probe puts beside the node under test, one per kind.
CLASS_BRANCH = {"type": "object", "properties": {"zz": _S}, "required": ["zz"]}
SCALAR_BRANCH = {"type": "string", "minLength": 9}
#: The companion a CONJ probe puts beside the conjunct under test: an object conjunct,
#: which is what §5's ``allOf`` cell composes ("inline conjuncts are fields and rules of
#: this class").
CONJ_COMPANION = {"type": "object", "properties": {"zz": _S}}


def wrap(position: Position, node: dict, under: str = "if") -> tuple[dict, Any]:
    """The probe document putting ``node`` at ``position``, and where a witness goes.

    One wrapper per position, and the structural keyword each one uses is the one
    ``keywords.descends_at(Position.ROOT)`` names for that position --
    ``tests/test_cells.py::test_every_wrapper_descends_by_the_columns_own_keyword`` is
    the equality, so this is the descent column read as a constructor rather than a
    second list of which keyword holds what.
    """
    base: dict[str, Any] = {"title": "Probe"}
    if position is Position.ROOT:
        return {**base, **node}, lambda w: w
    if position is Position.PROP:
        return (
            {**base, "type": "object", "properties": {"p": node}, "required": ["p"]},
            lambda w: {"p": w},
        )
    if position is Position.ELEM:
        return {**base, "type": "array", "items": node}, lambda w: [w]
    if position is Position.MAPV:
        return (
            {**base, "type": "object", "additionalProperties": node},
            lambda w: {MAPPING_KEY: w},
        )
    if position is Position.KEY:
        return (
            {**base, "type": "object", "propertyNames": node},
            lambda w: {w: 1} if isinstance(w, str) else {MAPPING_KEY: 1},
        )
    if position is Position.BRANCH:
        companion = CLASS_BRANCH if is_a_class_node(node) else SCALAR_BRANCH
        return {**base, "anyOf": [node, companion]}, lambda w: w
    if position is Position.CONJ:
        return {**base, "allOf": [node, CONJ_COMPANION]}, lambda w: w
    if position is Position.RULE:
        shell = {
            **base,
            "type": "object",
            "properties": {GUARD: _S, TRIGGER: _S},
            "additionalProperties": True,
        }
        if under == "if":
            held = {"if": node, "then": {"required": [GUARD]}}
            place = lambda w: w  # noqa: E731
        elif under == "not":
            held = {"not": node}
            place = lambda w: w  # noqa: E731
        elif under == "then":
            held = {"if": OUTER, "then": node}
            place = lambda w: {**w, TRIGGER: "on"}  # noqa: E731
        elif under == "else":
            held = {"if": OUTER, "else": node}
            place = lambda w: {**w, TRIGGER: "off"}  # noqa: E731
        else:
            raise AssertionError(under)
        return {**shell, **held}, place
    if position is Position.DEF:
        return (
            {
                **base,
                "definitions": {"D": node},
                "type": "object",
                "properties": {"p": {"$ref": "#/definitions/D"}},
                "required": ["p"],
            },
            lambda w: {"p": w},
        )
    raise AssertionError(position)


def probe_for(keyword: str, position: Position) -> Probe:
    """The cell's own probe: the position's override where it has one."""
    return AT.get((keyword, position)) or NODES[keyword]


def witnesses_at(position: Position, probe: Probe) -> tuple[Any, ...]:
    """The witnesses placed at this position.

    At a RULE position the node is a CONDITION and not a value schema, so the pair that
    distinguishes it is the instance matching the condition WITHOUT the consequent
    satisfied beside the same instance WITH it -- one refused and one admitted by the
    document wherever the condition bites, and both admitted wherever it does not.  A
    single witness per condition would pass against a model that carried no rule at all.
    """
    if position is Position.RULE:
        if probe.under == "not":
            # A ``not`` refuses the instance it matches outright, so the condition's two
            # sides ARE the witnesses and the consequent is not in the shape.
            return probe.witnesses
        out: list[Any] = []
        for w in probe.witnesses:
            if isinstance(w, dict):
                out.append(dict(w))
                out.append({**w, GUARD: "gg"})
        return tuple(out)
    return probe.witnesses


# --------------------------------------------------------------------------- #
# compiling one probe
# --------------------------------------------------------------------------- #
#: The documents every probe bundle carries beside the probe, so the ``$ref`` row's three
#: targets resolve.  Written on every probe rather than per cell: a probe that names none
#: of them emits them unreferenced and nothing about the cell under test changes.
BESIDE = {
    "core/target.json": TARGET,
    "core/envelope.json": ENVELOPE,
    "core/vocab.json": VOCAB,
}

_BOUND = [0]


def compile_probe(doc: dict) -> tuple[emit.Emitted, dict]:
    """``emit.emit`` over a one-document bundle holding this probe, and the probe read back.

    The document is written and read back rather than passed, because that is the path a
    bundle document takes and ``harness.conforms`` must be asked about the same bytes the
    compiler saw.
    """
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "bundle"
        (root / "core").mkdir(parents=True, exist_ok=True)
        for name, text in BESIDE.items():
            (root / name).write_text(json.dumps(text, indent=1))
        path = root / "core/probe.json"
        path.write_text(json.dumps({"$schema": DRAFT, **doc}, indent=1))
        population = ["core/probe.json", *BESIDE]
        return emit.emit(root, population), json.loads(path.read_text())


def bind(out: emit.Emitted) -> Any:
    """The probe module's root symbol, EXECUTED rather than inspected.

    ``tests/test_required_with_no_declaration.py``'s reading and for its reason: "a test
    that inspects the rendered text passes on a rendering that does not run, and this
    row's claim is about an accepted set".  The fresh ``constraints`` module is bound
    under its own import name for the duration, because an alias this probe mints is one
    the committed module does not carry -- ``tests/fresh.py`` states the same rule for
    the tree.
    """
    _BOUND[0] += 1
    constraints = types.ModuleType("adcp.types.constraints")
    exec(  # executing the compiler's own output is the point
        compile(out.beside.get("constraints.py", ""), "<constraints>", "exec"),
        constraints.__dict__,
    )
    saved = sys.modules.get("adcp.types.constraints")
    sys.modules["adcp.types.constraints"] = constraints
    held: dict[str, Any] = {}
    try:
        for name in BESIDE:
            module = types.ModuleType("_cell_beside")
            exec(
                compile(_standalone(out.files[name.replace(".json", ".py")]), "<b>", "exec"),
                module.__dict__,
            )
            held.update(
                {k: v for k, v in module.__dict__.items() if not k.startswith("__")}
            )
        module = types.ModuleType(f"_cell_probe_{_BOUND[0]}")
        sys.modules[module.__name__] = module
        try:
            module.__dict__.update(held)
            exec(
                compile(_standalone(out.files["core/probe.py"]), "<probe>", "exec"),
                module.__dict__,
            )
        finally:
            del sys.modules[module.__name__]
    finally:
        if saved is None:
            del sys.modules["adcp.types.constraints"]
        else:
            sys.modules["adcp.types.constraints"] = saved
    return module.__dict__[module.__all__[0]]


def _standalone(text: str) -> str:
    """The module text with its sibling imports dropped, the symbols being in hand."""
    return "\n".join(
        line
        for line in text.splitlines()
        if not (line.startswith("from .") or line.startswith("from adcp.types._schemas"))
    )


class Verdicts(NamedTuple):
    """One cell's grade: the witnesses, and the two directions §2 reads them in."""

    #: ``emitted``, or the refusal's resolution -- ``verdict`` or ``deferred`` -- where
    #: the probe produced no class at all.
    outcome: str
    #: The keyword the refusal names, where there is one.
    refused_on: str | None
    #: ``(the instance as JSON, the document's verdict, the class's verdict)``.
    rows: tuple[tuple[str, Any, bool], ...]
    #: Witnesses the DOCUMENT admits and the class refuses -- §2's forbidden direction.
    narrowed: tuple[tuple[str, Any, bool], ...]
    #: Witnesses the document refuses and the class admits -- a widening, legal only
    #: where the run declares one.
    widened: tuple[tuple[str, Any, bool], ...]
    #: The keywords the run declared an approximation for on this probe.
    declared: tuple[str, ...]

    @property
    def proved(self) -> bool:
        """Did a payload prove this cell: no narrowing, and no undeclared widening."""
        return (
            self.outcome == "emitted"
            and not self.narrowed
            and not (self.widened and not self.declared)
        )


def grade(keyword: str, position: Position) -> Verdicts:
    """One cell, proved or not, by payload.

    The DOCUMENT's verdict is ``harness.conforms``, which is the run's own reading and
    asserts ``format`` with the declared draft's checker -- so neither half here is a
    second opinion about what the document says.
    """
    probe = probe_for(keyword, position)
    document, place = wrap(position, probe.node, probe.under)
    out, resolved = compile_probe(document)
    if out.refusals:
        refusal = out.refusals.get("core/probe.json") or next(iter(out.refusals.values()))
        return Verdicts(
            str(refusal["resolved"]).split(".")[-1], refusal["keyword"], (), (), (), ()
        )
    try:
        symbol = bind(out)
    except SyntaxError as error:
        # The module the run wrote is not parseable Python.  Not a verdict and not a
        # deferral: the compiler reported neither and emitted a file no consumer can
        # import, so the cell has no annotation AND no refusal naming it.
        return Verdicts(f"unparseable: {error.msg}", None, (), (), (), ())
    adapter = TypeAdapter(symbol)
    rows = []
    for witness in witnesses_at(position, probe):
        instance = place(witness)
        try:
            adapter.validate_python(instance)
            by_class = True
        except Exception:  # any refusal is a refusal
            by_class = False
        rows.append((json.dumps(instance, default=str), harness.conforms(resolved, instance), by_class))
    return Verdicts(
        "emitted",
        None,
        tuple(rows),
        tuple(r for r in rows if r[1] is True and not r[2]),
        tuple(r for r in rows if r[1] is False and r[2]),
        tuple(a.keyword for a in out.approximations.get("core/probe.json", [])),
    )


# --------------------------------------------------------------------------- #
# the two sets the gate compares
# --------------------------------------------------------------------------- #
def live() -> frozenset[tuple[str, Position]]:
    """**The LIVE cells**: a cell that selects a type, renders a constraint or states a
    rule.

    ``keywords.COMPILES`` is that reading and it is the declaration's own: "The effects
    that COMPILE TO SOMETHING -- a type, a field or a rule.  Section 6's preamble is the
    complement of this".  So the set is derived from the table and is not a list.
    """
    return frozenset(
        (keyword, position)
        for keyword in keywords.TABLE
        for position in Position
        if keywords.cell(keyword, position).effect in keywords.COMPILES
    )


@functools.cache
def stated_by_the_bundle() -> frozenset[tuple[str, Position]]:
    """Every ``(keyword, position)`` any portable document STATES.

    Read through ``bundle.nodes_at``, which carries the POSITION the descent column
    assigned rather than recovering it from a pointer -- ``docs/plan/architecture.md`` §6:
    "the position is assigned from the structural keyword descended through, so no reader
    derives it from a pointer -- and the readings that did were a measured defect in both
    directions".

    **This is the set the induction has to range over to reach a document**, which is why
    it is measured rather than assumed: a cell no document states is a cell no document's
    faithfulness depends on.
    """
    found: set[tuple[str, Position]] = set()
    for document in bundle.portable(SOURCE):
        for _, node, position in bundle.nodes_at(bundle.read(SOURCE, document)):
            for keyword in node:
                if keyword in keywords.TABLE:
                    found.add((keyword, position))
    return frozenset(found)
