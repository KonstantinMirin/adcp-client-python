"""The constraint reader's grammar, and its closure over the pinned bundle.

Two obligations live here and nothing else does.

The first is per-production: for every keyword the grammar claims a production
for, a constructed node carrying that keyword compiles to the node the grammar
names. ``_PRODUCTION_FIXTURES`` is the whole map, and
:func:`test_the_fixture_map_covers_exactly_the_claimed_grammar` makes a
production added without a fixture and a claim made without a production both
fail, so neither half can drift.

The second is closure: every root constraint node in the pinned bundle parses
with zero unaccounted keys. That is §2's keyword census turned into a guard --
it re-derives the accounting on every run instead of citing a measurement, so a
bundle sync that introduces a keyword kind the grammar does not know turns this
red rather than quietly widening the models.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from scripts.schema_constraints import (
    COMPILED_KEYWORDS,
    DECLARED_BEHAVIORAL_KEY,
    NON_ASSERTING_KEYS,
    AllOf,
    AnyOf,
    Cond,
    DeclaredShape,
    DependentRequired,
    EveryItem,
    IfThen,
    KeysSatisfy,
    MatchingKeysSatisfy,
    NoOtherProps,
    Not,
    OneOf,
    OtherPropsSatisfy,
    PropCount,
    PropSatisfies,
    SomeItem,
    Supplied,
    Undeclarable,
    UnexpressibleKeywordError,
    UnplaceableConstraintError,
    ValueBounds,
    ValueConst,
    ValueEnum,
    ValueItems,
    ValueLen,
    ValuePattern,
    ValueType,
    ValueUnique,
    bundle_document_resolver,
    read_root_constraints,
    root_carries_constraints,
)


def _bundle_dir() -> Path:
    from scripts.post_generate_fixes import SCHEMA_DIR

    return SCHEMA_DIR


# --------------------------------------------------------------------------- #
# Per-production: one constructed node each
# --------------------------------------------------------------------------- #


def _read(root: dict[str, Any], **kwargs: Any) -> Any:
    return read_root_constraints(root, DeclaredShape.from_schema(root), **kwargs)


def _only_arm_condition(root: dict[str, Any], **kwargs: Any) -> Cond:
    """The condition of a root whose single ``anyOf`` arm carries the keyword."""
    constraints = _read(root, **kwargs)
    assert len(constraints.arms) == 1, root
    return constraints.arms[0].condition


def _arm_root(arm: dict[str, Any], properties: dict[str, Any] | None = None) -> dict[str, Any]:
    """A root declaring ``properties`` whose one overlay arm is ``arm``.

    The arm declares no new names, so it is an overlay: its keywords are
    constraint content rather than a declaration the generator renders.
    """
    return {
        "title": "Thing",
        "type": "object",
        "properties": properties if properties is not None else {"a": {}, "b": {}},
        "anyOf": [arm],
    }


#: One constructed node per claimed production, and the Cond it must compile to.
#: The keys are exactly ``COMPILED_KEYWORDS``, enforced below.
_PRODUCTION_FIXTURES: dict[str, tuple[dict[str, Any], Cond]] = {
    "required": (_arm_root({"required": ["a"]}), Supplied("a")),
    "properties": (
        _arm_root({"properties": {"a": {"const": 1}}}),
        PropSatisfies("a", ValueConst(1)),
    ),
    "not": (_arm_root({"not": {"required": ["a"]}}), Not(Supplied("a"))),
    "allOf": (
        _arm_root({"allOf": [{"required": ["a"]}, {"required": ["b"]}]}),
        AllOf((Supplied("a"), Supplied("b"))),
    ),
    "anyOf": (
        _arm_root({"anyOf": [{"required": ["a"]}, {"required": ["b"]}]}),
        AnyOf((Supplied("a"), Supplied("b"))),
    ),
    "oneOf": (
        _arm_root({"oneOf": [{"required": ["a"]}, {"required": ["b"]}]}),
        OneOf((Supplied("a"), Supplied("b"))),
    ),
    "if": (
        _arm_root({"if": {"required": ["a"]}, "then": {"required": ["b"]}}),
        IfThen(Supplied("a"), Supplied("b"), None),
    ),
    "then": (
        # A ``then`` with no sibling ``if`` asserts nothing, which is JSON
        # Schema's own reading; the production is what accounts for the key.
        _arm_root({"then": {"required": ["a"]}, "required": ["b"]}),
        Supplied("b"),
    ),
    "else": (
        _arm_root(
            {
                "if": {"required": ["a"]},
                "then": {"required": ["b"]},
                "else": {"not": {"required": ["b"]}},
            }
        ),
        IfThen(Supplied("a"), Supplied("b"), Not(Supplied("b"))),
    ),
    "dependencies": (
        _arm_root({"dependencies": {"a": ["b"]}}),
        DependentRequired("a", ("b",)),
    ),
    "dependentRequired": (
        _arm_root({"dependentRequired": {"a": ["b"]}}),
        DependentRequired("a", ("b",)),
    ),
    "dependentSchemas": (
        _arm_root({"dependentSchemas": {"a": {"required": ["b"]}}}),
        IfThen(Supplied("a"), Supplied("b"), None),
    ),
    "const": (
        _arm_root({"properties": {"a": {"const": "x"}}}),
        PropSatisfies("a", ValueConst("x")),
    ),
    "enum": (
        _arm_root({"properties": {"a": {"enum": ["x", "y"]}}}),
        PropSatisfies("a", ValueEnum(("x", "y"))),
    ),
    "type": (
        _arm_root({"properties": {"a": {"type": "string"}}}),
        PropSatisfies("a", ValueType(("string",))),
    ),
    "pattern": (
        _arm_root({"properties": {"a": {"pattern": "^x"}}}),
        PropSatisfies("a", ValuePattern("^x")),
    ),
    "minLength": (
        _arm_root({"properties": {"a": {"minLength": 1}}}),
        PropSatisfies("a", ValueLen(minimum=1)),
    ),
    "maxLength": (
        _arm_root({"properties": {"a": {"maxLength": 9}}}),
        PropSatisfies("a", ValueLen(maximum=9)),
    ),
    "minimum": (
        _arm_root({"properties": {"a": {"minimum": 0}}}),
        PropSatisfies("a", ValueBounds(ge=0)),
    ),
    "maximum": (
        _arm_root({"properties": {"a": {"maximum": 100}}}),
        PropSatisfies("a", ValueBounds(le=100)),
    ),
    "exclusiveMinimum": (
        _arm_root({"properties": {"a": {"exclusiveMinimum": 0}}}),
        PropSatisfies("a", ValueBounds(gt=0)),
    ),
    "exclusiveMaximum": (
        _arm_root({"properties": {"a": {"exclusiveMaximum": 1}}}),
        PropSatisfies("a", ValueBounds(lt=1)),
    ),
    "minItems": (
        _arm_root({"properties": {"a": {"minItems": 1}}}),
        PropSatisfies("a", ValueItems(minimum=1)),
    ),
    "maxItems": (
        _arm_root({"properties": {"a": {"maxItems": 2}}}),
        PropSatisfies("a", ValueItems(maximum=2)),
    ),
    "uniqueItems": (
        _arm_root({"properties": {"a": {"uniqueItems": True}}}),
        PropSatisfies("a", ValueUnique()),
    ),
    "items": (
        _arm_root({"properties": {"a": {"items": {"required": ["b"]}}}}),
        PropSatisfies("a", EveryItem(Supplied("b"))),
    ),
    "contains": (
        _arm_root({"properties": {"a": {"contains": {"required": ["b"]}}}}),
        PropSatisfies("a", SomeItem(Supplied("b"))),
    ),
    "propertyNames": (
        _arm_root({"properties": {"a": {"propertyNames": {"pattern": "^x"}}}}),
        PropSatisfies("a", KeysSatisfy(ValuePattern("^x"))),
    ),
    "patternProperties": (
        _arm_root({"properties": {"a": {"patternProperties": {"^x": {"minimum": 1}}}}}),
        PropSatisfies("a", MatchingKeysSatisfy("^x", ValueBounds(ge=1))),
    ),
    "minProperties": (
        _arm_root({"properties": {"a": {"minProperties": 1}}}),
        PropSatisfies("a", PropCount(minimum=1)),
    ),
    "maxProperties": (
        _arm_root({"properties": {"a": {"maxProperties": 3}}}),
        PropSatisfies("a", PropCount(maximum=3)),
    ),
    "additionalProperties": (
        _arm_root({"properties": {"a": {"properties": {"b": {}}, "additionalProperties": False}}}),
        PropSatisfies("a", NoOtherProps(("b",))),
    ),
    "$ref": (
        {
            "title": "Thing",
            "type": "object",
            "properties": {"a": {"type": "object"}},
            "$defs": {"narrowed": {"required": ["b"]}},
            "anyOf": [{"properties": {"a": {"$ref": "#/$defs/narrowed"}}}],
        },
        PropSatisfies("a", Supplied("b")),
    ),
}


def test_the_fixture_map_covers_exactly_the_claimed_grammar() -> None:
    """A production without a fixture, or a claim without a production, fails.

    The map below is the per-production obligation set. Deriving the
    parametrization from it and the claim from ``COMPILED_KEYWORDS``
    independently is what makes the two halves unable to drift apart.
    """
    assert set(_PRODUCTION_FIXTURES) == set(COMPILED_KEYWORDS)


@pytest.mark.parametrize("keyword", sorted(_PRODUCTION_FIXTURES), ids=str)
def test_each_grammar_production_compiles_its_keyword(keyword: str) -> None:
    """One constructed node per production, compiled to the node it names."""
    root, expected = _PRODUCTION_FIXTURES[keyword]
    assert _only_arm_condition(root) == expected


def test_additional_properties_as_a_subschema_grades_the_unnamed_members() -> None:
    """The map form, which is how the bundle spells ``dict[str, <enum>]``.

    The ``false`` form is in the fixture map above; this is the production's
    other branch, and a map type has no sibling ``properties`` to exempt.
    """
    root = _arm_root({"properties": {"a": {"additionalProperties": {"enum": ["pass", "fail"]}}}})

    assert _only_arm_condition(root) == PropSatisfies(
        "a", OtherPropsSatisfy((), ValueEnum(("pass", "fail")))
    )


def test_presence_is_membership_not_a_null_check() -> None:
    """``required`` compiles to supplied-ness, which is what the schema asks.

    Measured: an ``is None`` guard is only correct when the field's default
    happens to be ``None``. A non-None default makes it false for an absent
    field and the check over-refuses, and an unguarded attribute read raises on
    absence and on an explicit null alike. ``Supplied`` is the grammar's only
    presence node, so no compiled predicate can spell presence the other ways.
    """
    assert _only_arm_condition(_arm_root({"required": ["a"]})) == Supplied("a")


# --------------------------------------------------------------------------- #
# The closure rule
# --------------------------------------------------------------------------- #


def test_a_keyword_outside_every_named_rule_aborts_naming_file_pointer_keyword() -> None:
    """The refusal carries what a maintainer needs to grow the grammar."""
    root = _arm_root({"unevaluatedProperties": False})

    with pytest.raises(UnexpressibleKeywordError) as raised:
        _read(root, schema_file="made-up/thing.json")

    assert raised.value.schema_file == "made-up/thing.json"
    assert raised.value.pointer == "anyOf/0"
    assert raised.value.keyword == "unevaluatedProperties"


def test_a_constraint_naming_a_field_the_schema_declares_but_the_class_does_not_refuses() -> None:
    """A dropped field surfaces loudly instead of placing the constraint nowhere."""
    root = _arm_root({"required": ["b"]})
    declared_without_b = DeclaredShape(fields={"a": "a"}, nested={})

    with pytest.raises(UnplaceableConstraintError) as raised:
        read_root_constraints(root, declared_without_b, schema_file="media-buy/thing.json")

    assert raised.value.name == "b"


def test_a_required_name_the_schema_never_declares_is_statically_false() -> None:
    """An AdCP root that forbids a key no arm declares is not a dropped field.

    ``control-media-buy-request`` forbids ``creatives``: the document may not
    carry the key at all, so a model has no field for it and can be given none.
    That is decidable, and deciding it is what keeps the field-drop refusal
    above meaningful rather than firing on every such root.
    """
    root = {
        "title": "Thing",
        "type": "object",
        "properties": {"a": {}},
        "not": {"anyOf": [{"required": ["creatives"]}]},
    }

    assert _read(root).conjuncts == (Not(AnyOf((Undeclarable("creatives"),))),)


def test_a_keyword_equal_to_the_declaration_is_a_proven_restatement() -> None:
    """Equality is checked, and a narrowing is not equality.

    ``packages.items.allOf[0].$ref`` to ``package-request.json`` restates the
    declared item type; the sibling member's ``required`` narrows it. The first
    drops out of the compiled tree and the second does not.
    """
    root = {
        "title": "Thing",
        "type": "object",
        "properties": {"packages": {"items": {"$ref": "core/package-request.json"}}},
        "anyOf": [
            {
                "properties": {
                    "packages": {
                        "items": {
                            "allOf": [
                                {"$ref": "core/package-request.json"},
                                {"required": ["budget"]},
                            ]
                        }
                    }
                }
            }
        ],
    }

    assert _only_arm_condition(root) == PropSatisfies("packages", EveryItem(Supplied("budget")))


def test_a_narrowing_of_the_declared_type_compiles_rather_than_restating() -> None:
    root = {
        "title": "Thing",
        "type": "object",
        "properties": {"a": {"type": "string"}},
        "anyOf": [{"properties": {"a": {"type": "string", "const": "x"}}}],
    }

    assert _only_arm_condition(root) == PropSatisfies("a", ValueConst("x"))


def test_the_declared_behavioral_key_is_classified_not_compiled() -> None:
    """``x-adcp-validation`` is a contract citation, not a tolerance entry.

    ``docs/validation-contract.md`` puts these rules outside the structural
    models' promise. The parser records that an arm carries them -- which is
    what lets ``oneOf`` cardinality refuse rather than approximate -- and there
    is no per-schema list anywhere.
    """
    root = _arm_root({"required": ["a"], DECLARED_BEHAVIORAL_KEY: {"verifier_constraints": {}}})

    constraints = _read(root)

    assert constraints.declares_behavioral_rules
    assert constraints.arms[0].declares_behavioral_rules
    assert constraints.arms[0].condition == Supplied("a")


def test_the_three_classification_sets_are_disjoint() -> None:
    """A key classified two ways would make the accounting ambiguous."""
    assert not (COMPILED_KEYWORDS & NON_ASSERTING_KEYS)
    assert DECLARED_BEHAVIORAL_KEY not in COMPILED_KEYWORDS
    assert DECLARED_BEHAVIORAL_KEY not in NON_ASSERTING_KEYS


# --------------------------------------------------------------------------- #
# Bundle closure: §2's census, re-derived every run
# --------------------------------------------------------------------------- #

#: Positions whose subschema grades the same object as its parent, plus the
#: containers a constraint descends through. Walked here independently of the
#: parser, so the census is a second reading rather than the parser's own.
_SUBSCHEMA = (
    "not",
    "if",
    "then",
    "else",
    "items",
    "contains",
    "propertyNames",
    "additionalProperties",
    "unevaluatedProperties",
)
_SUBSCHEMA_LISTS = ("anyOf", "oneOf", "allOf", "prefixItems")
_SUBSCHEMA_MAPS = (
    "properties",
    "patternProperties",
    "dependencies",
    "dependentSchemas",
    "$defs",
    "definitions",
)


def _constrained_roots() -> list[tuple[str, dict[str, Any]]]:
    """Every pinned schema whose root states more than its merged properties."""
    bundle = _bundle_dir()
    roots: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(bundle.rglob("*.json")):
        if "bundled" in path.parts:
            continue
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(schema, dict) and root_carries_constraints(schema):
            roots.append((path.relative_to(bundle).as_posix(), schema))
    return roots


def _keys_in_constraint_content(schema: dict[str, Any]) -> Iterator[str]:
    """Every key the root's constraint content carries, at any depth."""

    def walk(node: Any) -> Iterator[str]:
        if not isinstance(node, dict):
            return
        yield from node
        for key in _SUBSCHEMA:
            if isinstance(node.get(key), dict):
                yield from walk(node[key])
        for key in _SUBSCHEMA_LISTS:
            if isinstance(node.get(key), list):
                for member in node[key]:
                    yield from walk(member)
        for key in _SUBSCHEMA_MAPS:
            if isinstance(node.get(key), dict):
                for member in node[key].values():
                    yield from walk(member)

    for combinator in ("anyOf", "oneOf"):
        arms = schema.get(combinator)
        if isinstance(arms, list) and arms:
            for arm in arms:
                yield from walk(arm)
            break
    for keyword in ("if", "then", "else", "not"):
        if keyword in schema:
            yield keyword
            yield from walk(schema[keyword])
    for keyword in ("dependencies", "dependentRequired"):
        members = schema.get(keyword)
        if isinstance(members, dict):
            yield keyword
            for member in members.values():
                yield from walk(member)


@pytest.fixture(scope="module")
def constrained_roots() -> list[tuple[str, dict[str, Any]]]:
    return _constrained_roots()


def test_the_closure_population_is_the_whole_pinned_bundle(
    constrained_roots: list[tuple[str, dict[str, Any]]],
) -> None:
    """A derivation that selects nothing passes for free.

    §2 measured 250 roots with a combinator and 51 with a root ``not``, 23 with
    ``if``, 19 with ``dependencies``, 8 with ``dependentRequired`` -- hundreds,
    overlapping. The floor below is what distinguishes "everything parsed" from
    "the walk found nothing to parse"; the exact count is re-derived rather
    than asserted, because a bundle sync moves it legitimately.
    """
    assert len(constrained_roots) > 250, (
        "the bundle walk found almost no root constraint content; the closure "
        "rule below would then grade nothing"
    )


def test_every_root_constraint_node_in_the_bundle_parses_with_no_unaccounted_key(
    constrained_roots: list[tuple[str, dict[str, Any]]],
) -> None:
    """Closure: a keyword this SDK cannot express cannot reach a shipped model.

    Every refusal is collected rather than failing on the first, so a bundle
    sync that introduces several kinds names all of them in one run.
    """
    resolve = bundle_document_resolver(_bundle_dir())
    refusals: list[str] = []
    for name, schema in constrained_roots:
        try:
            read_root_constraints(
                schema,
                DeclaredShape.from_schema(schema),
                schema_file=name,
                resolve_document=resolve,
            )
        except (UnexpressibleKeywordError, UnplaceableConstraintError) as refusal:
            refusals.append(str(refusal))

    assert not refusals, "\n".join(refusals)


def test_every_key_the_bundle_carries_falls_under_a_named_rule(
    constrained_roots: list[tuple[str, dict[str, Any]]],
) -> None:
    """The census as a guard: the key set is accounted for, not sampled.

    This reads the bundle independently of the parser, so it grades the three
    named sets against the real key population rather than against the walk
    the parser happens to take.
    """
    accounted = COMPILED_KEYWORDS | NON_ASSERTING_KEYS | {DECLARED_BEHAVIORAL_KEY}
    found: set[str] = set()
    for _name, schema in constrained_roots:
        found.update(_keys_in_constraint_content(schema))

    assert len(found) > 30, f"the census walk found only {sorted(found)}"
    assert found <= accounted, sorted(found - accounted)
