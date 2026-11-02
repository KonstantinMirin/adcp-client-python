"""§3a's PASS B: the pin names a MEMBER, the schema does not move, and the count does.

``codegen/lower/normalise.py`` is the row.  Three obligations here, and they are three
because they fail differently:

* **THE COUNT.**  A branch redeclaring an inherited enum field with a raw ``str``
  ``Literal`` is an incompatible override and not a narrowing, and a type checker says so.
  The population is derived from the bundle and the count is a RATCHET with its direction
  stated, because every emitting row moves it.
* **THE SCHEMA DOES NOT MOVE.**  ``Literal[E.MEMBER]`` and ``Literal['value']`` render the
  same JSON Schema and validate the same payloads.  That is the whole safety argument for
  the conversion, and it is ASSERTED here on the pinned pydantic rather than assumed from
  a docstring -- at a converted site of the emitted tree, and on the member form in
  isolation.
* **THE ROW DECLINES WHERE IT CANNOT NAME A MEMBER.**  The sibling lane measured that
  ``render`` cannot tell an imported enumeration from an imported ``Annotated`` alias --
  ``brand.json``'s ``default_language`` and ``markdown-asset.json``'s ``markdown_flavor``
  produce byte-identical ``TypeRef``\\ s and ``LanguageTag`` is not callable.  Pass B never
  asks that of a symbol: it asks it of the base's DECLARATION.  The two conditions are
  graded directly, over hand-built declarations, so the guard is exercised rather than
  argued.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from nodeset import claimed, ratchet

from codegen import ir
from codegen.lower import normalise

REPO = Path(__file__).resolve().parents[1]
TREE = REPO / "src" / "adcp" / "types" / "_schemas"

#: A member form in an emitted annotation: ``Literal[Symbol.MEMBER]``.  Read off the AST
#: and not off the text -- the pattern is the ATTRIBUTE access inside a ``Literal``
#: subscript, which is what the rendering IS, where a regex over the text would also match
#: a dotted value inside a string literal (``Literal['account.status_changed']`` is a live
#: annotation of this bundle and is exactly that).
def _member_pins(path: Path) -> list[tuple[str, str, str]]:
    """``(class, field, "Symbol.MEMBER")`` for every member-form pin in one module."""
    out: list[tuple[str, str, str]] = []
    for node in ast.walk(ast.parse(path.read_text())):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Name):
                continue
            for inner in ast.walk(stmt.annotation):
                if not (
                    isinstance(inner, ast.Subscript)
                    and isinstance(inner.value, ast.Name)
                    and inner.value.id == "Literal"
                ):
                    continue
                for arm in (
                    inner.slice.elts if isinstance(inner.slice, ast.Tuple) else [inner.slice]
                ):
                    if isinstance(arm, ast.Attribute) and isinstance(arm.value, ast.Name):
                        out.append(
                            (node.name, stmt.target.id, f"{arm.value.id}.{arm.attr}")
                        )
    return out


def _tree_member_pins() -> dict[str, list[tuple[str, str, str]]]:
    """Every member-form pin of the committed tree, keyed by module.

    ``claimed`` is asked of the KEYS at every call site, which is what names the set a
    check ranges over and refuses an empty one; the mapping is what the site then reads.
    """
    return {
        str(path.relative_to(TREE)): found
        for path in sorted(TREE.rglob("*.py"))
        if (found := _member_pins(path))
    }


def test_a_pin_inside_a_named_vocabulary_names_its_member() -> None:
    """The population, and its direction: a pin over an inherited enumeration is a member.

    A RATCHET and not an equality (``tests/nodeset.py``): the number of branch sites that
    restate a root-declared enum property is a function of the bundle, and every row that
    changes which documents emit moves it.  The direction is what the row promises -- a
    site that converted does not go back to a raw value pin, because the raw form is the
    incompatible override this row removes.

    The floor is read off the tree the committed artifact is, which
    ``test_emit.py::test_the_committed_tree_is_what_a_fresh_run_emits`` holds equal to a
    fresh run's.
    """
    found = _tree_member_pins()
    claimed("modules carrying a member-form pin", found)
    sites = sum(len(v) for v in found.values())
    ratchet(
        "member-form pins in the emitted tree",
        sites,
        at_least=100,
        because=(
            "section 3a's Pass B converts a branch's raw value pin over an inherited "
            "enumeration into a member of it; a site that converted may not return to the "
            "raw form, which is the incompatible override the row removes.  A bundle that "
            "states fewer such branches lowers this and is why it is a floor and not an "
            "equality"
        ),
    )


def test_the_member_form_and_the_value_form_state_one_schema() -> None:
    """THE SAFETY ARGUMENT, asserted on the pinned pydantic and not assumed.

    The conversion is sound only if ``Literal[E.MEMBER]`` and ``Literal['value']`` state
    the same thing to pydantic: the same JSON Schema, the same accepted payload, and the
    same dumped value.  All three are checked, because they are three different ways the
    conversion could have moved the artifact's behaviour.
    """
    from enum import StrEnum
    from typing import Literal

    from pydantic import BaseModel

    class Vocabulary(StrEnum):
        CREATED = "property.created"
        UPDATED = "property.updated"

    class Member(BaseModel):
        event_type: Literal[Vocabulary.CREATED]

    class Value(BaseModel):
        event_type: Literal["property.created"]

    def without_title(model: type[BaseModel]) -> dict:
        # The model's own ``title`` is its class name and is the one key that differs by
        # construction, so it is dropped rather than the two models being given one name.
        schema = model.model_json_schema()
        schema.pop("title", None)
        for entry in schema.get("properties", {}).values():
            entry.pop("title", None)
        return schema

    assert without_title(Member) == without_title(Value), (
        json.dumps(without_title(Member), sort_keys=True),
        json.dumps(without_title(Value), sort_keys=True),
    )
    assert Member(event_type="property.created").event_type == "property.created"
    assert Member.model_validate(
        {"event_type": "property.created"}
    ).model_dump() == Value.model_validate({"event_type": "property.created"}).model_dump()
    assert Member.model_validate({"event_type": "property.created"}).model_dump(
        mode="json"
    ) == {"event_type": "property.created"}


def test_a_converted_site_of_the_tree_states_the_documents_own_const() -> None:
    """The same equality at a REAL converted site, read through the emitted class.

    ``core/registry-event.json`` is §3a's own example: ``enum`` at the root's
    ``event_type`` and ``const`` at its branch's.  The branch class's rendered schema for
    that property must be the document's ``const`` exactly -- not a one-member ``enum``,
    not the base's whole vocabulary -- or the conversion changed what the class says it
    accepts.

    Read off the COMMITTED tree, which the byte-compare holds equal to a fresh run's, and
    through ``model_json_schema()`` rather than off the text: the question is what pydantic
    states, and only pydantic answers it.
    """
    from adcp.types._schemas.core.registry_event import (
        RegistryEventPropertyCreatedProperty,
    )

    schema = RegistryEventPropertyCreatedProperty.model_json_schema()
    pinned = schema["properties"]["event_type"]
    assert pinned.get("const") == "property.created", pinned
    assert pinned.get("type") == "string", pinned
    assert "enum" not in pinned, pinned
    assert RegistryEventPropertyCreatedProperty.model_fields["event_type"].is_required()


def test_the_row_declines_where_no_member_can_be_named() -> None:
    """Pass B's two conditions, graded over declarations rather than argued.

    This is the guard the sibling lane's measurement makes load-bearing: a symbol alone
    does not say whether it has members, so the row reads the base's DECLARATION for the
    vocabulary and requires the base's decided type to be a bare named symbol.  Each arm
    below removes one of the two and asserts the row declines.
    """
    enumeration = ir.TypeRef("EventType", local=True)
    base = ir.Field(name="event_type", wire="event_type", type=enumeration, required=True)
    declared = {"type": "string", "enum": ["property.created", "property.updated"]}
    pin = {"type": "string", "const": "property.created"}

    fires = normalise.pins_a_member(pin, declared, base)
    assert fires is not None and fires.members == ("PROPERTY_CREATED",), fires
    assert fires.path == "EventType" and fires.local

    # The base declares no vocabulary -- a constrained string, which is the case the
    # sibling lane's `LanguageTag` is: one symbol, no members.
    assert normalise.pins_a_member(pin, {"type": "string", "pattern": "^x"}, base) is None
    # A one-member `enum` is a pin and not a vocabulary to narrow.
    assert normalise.pins_a_member(pin, {"enum": ["property.created"]}, base) is None
    # The base's decided type is not a bare named symbol.
    for wrapped in (
        ir.TypeRef("list", container="list", of=(enumeration,)),
        ir.TypeRef(literals=("property.created",)),
        ir.TypeRef("EventType", local=True, members=("PROPERTY_CREATED",)),
        ir.TypeRef("str"),
    ):
        assert (
            normalise.pins_a_member(pin, declared, ir.Field("x", "x", wrapped, True)) is None
        ), wrapped
    # The restatement pins nothing, and a pin outside the vocabulary is the empty
    # intersection -- reported where it already is and not a second time here.
    assert normalise.pins_a_member({"type": "string"}, declared, base) is None
    assert normalise.pins_a_member({"const": "nope"}, declared, base) is None
    # A boolean pin names nothing: `true` is the same value for every property of the
    # bundle, and a boolean vocabulary renders no enum class at all.
    assert normalise.pins_a_member({"const": True}, {"enum": [True, False]}, base) is None
    # Two members spelling ONE Python name means the base rendered a `Literal`, so there
    # is no member for this row to name.
    assert (
        normalise.pins_a_member(
            {"const": "clickTag"}, {"enum": ["clickTag", "clickTAG"]}, base
        )
        is None
    )


def test_no_member_form_pin_names_a_symbol_its_module_cannot_resolve() -> None:
    """Every ``Literal[Symbol.MEMBER]`` of the tree names a symbol that module resolves.

    The failure this prevents is an undefined name at import, which is the shape
    ``compiler._placeable`` declines 39 sites to avoid.  Graded by reading each module's
    own bindings -- its imports and its class declarations -- so a module that pins a
    member of something it never names reddens here and not three test files away.

    Over the whole tree and not a sample, which is what ``claimed`` asserts: the set is
    every member-form pin ``_member_pins`` finds.
    """
    offenders: dict[str, list[str]] = {}
    held = _tree_member_pins()
    claimed("modules carrying a member-form pin", held)
    for module, pins in held.items():
        tree = ast.parse((TREE / module).read_text())
        bound = {
            alias.asname or alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        } | {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        missing = sorted({p.split(".")[0] for _, _, p in pins} - bound)
        if missing:
            offenders[module] = missing
    assert not offenders, json.dumps(offenders, indent=2)


def test_every_member_form_pin_names_a_member_its_enumeration_declares() -> None:
    """``Literal[E.M]`` where ``E`` declares no ``M`` is an ``AttributeError`` at import.

    The complement of the check above: the symbol resolves, and the member it names
    exists.  Read through the IMPORTED tree so the question is asked of the class object,
    which is the thing a consumer's annotation resolves to.
    """
    import importlib

    bad: dict[str, list[str]] = {}
    held = _tree_member_pins()
    claimed("modules carrying a member-form pin", held)
    for module, pins in held.items():
        name = "adcp.types._schemas." + module.removesuffix(".py").replace("/", ".").removesuffix(
            ".__init__"
        )
        loaded = importlib.import_module(name)
        for klass, field_name, spelled in pins:
            symbol, member = spelled.split(".", 1)
            held = getattr(loaded, symbol, None)
            if held is None or not hasattr(held, member):
                bad.setdefault(module, []).append(f"{klass}.{field_name}: {spelled}")
    assert not bad, json.dumps(bad, indent=2)


def test_the_pins_the_row_converted_are_the_restatements_and_not_a_sample() -> None:
    """Every member-form pin sits on a class with a BASE, which is what the row is about.

    Pass B fires only where an enclosing class already decided the property's type, so a
    member form on a class with no base would mean the row reached a node it has no
    business at -- a pin the document states on its own, which §5's ``const`` row owns and
    which this row's docstring says it never reaches.
    """
    baseless: dict[str, list[str]] = {}
    held = _tree_member_pins()
    claimed("modules carrying a member-form pin", held)
    for module, pins in held.items():
        tree = ast.parse((TREE / module).read_text())
        bases = {
            node.name: [ast.unparse(b) for b in node.bases]
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        }
        for klass, field_name, spelled in pins:
            held = [b for b in bases.get(klass, []) if b not in ("StrEnum", "IntEnum")]
            if not held:
                baseless.setdefault(module, []).append(f"{klass}.{field_name}: {spelled}")
    assert not baseless, json.dumps(baseless, indent=2)


def test_the_member_spelling_is_lower_enums_own(
) -> None:
    """A member name here is ``lower.enum.member_name``'s and never a second spelling.

    One derivation read twice, which is ``codegen/lower/enum.py``'s own injectivity
    argument: the declaring side mints the identifier and this row names it, so a second
    spelling function would be a copy that can disagree with the one that runs.
    """
    from codegen.lower.enum import member_name

    assert re.fullmatch(r"[A-Z_][A-Z0-9_]*", member_name("property.created"))
    enumeration = ir.TypeRef("EventType", local=True)
    base = ir.Field("event_type", "event_type", enumeration, True)
    for value in ("property.created", "4:2:0", "pass", "1.0"):
        got = normalise.pins_a_member(
            {"const": value}, {"enum": [value, "other"]}, base
        )
        assert got is not None and got.members == (member_name(value),), (value, got)
