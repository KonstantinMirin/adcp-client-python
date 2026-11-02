"""§3a's PASS B: one vocabulary spelled two ways, and the pin names a MEMBER of it.

``docs/plan/architecture.md`` §3a: *"Pass A is DETERMINISTIC: structural identity. Pass B
is NORMALISING -- the same concept spelled two ways, which Pass A cannot see because the
two spellings are genuinely different JSON."*  The first of the cases it names:

    **``const`` against ``enum``.**  ``core/registry-event.json`` states ``enum: [...]`` at
    its root's ``event_type`` and ``const: "property.created"`` at its branch's.  One
    vocabulary, two keywords.

and what it dissolves: *"where a root's ``enum`` and a branch's ``const`` are one
vocabulary, both reference the one entry, so the pin is ``Literal[Entry.MEMBER]`` because
no other member exists to name."*

**Pass B RUNS FIRST, on measurement** (§3a as of 2026-11-02).  Of the 264 base-class
``[assignment]`` errors a type checker reports over the emitted tree, **145 are a
``Literal`` pin declared against a base's enumeration** -- 44 are a base declaring
``dict[str, Any]``, 31 are an object, 23 a container and 21 an enum against a different
enum.  Of the 145, **97 have the base's enumeration declared in the SAME module and 48
import it**, so in both cases the class already exists and is already ONE object: the pin
only has to name its member.  The cross-document COLLECTION reaches about 10 of the 145,
because 108 of the enum-base errors are stated at a single position that L0 never
collects, 41 are untitled cross-document which §3a expressly refuses to collapse, 5 are
same-document restatements §4 already owns and 2 are the title conflicts.

So this row needs no catalogue entry, no namespace decision and no new reference edge
between documents.  It is the normalisation alone.

**WHY IT IS AN INCOMPATIBLE OVERRIDE AND NOT A NARROWING TODAY.**  A branch class
inherits ``event_type: EventType`` from its base and redeclares it
``Literal['property.created']`` -- a raw ``str`` literal against a ``StrEnum``, and
``Literal['property.created']`` is not a subtype of ``EventType`` because the value is not
the member.  ``Literal[EventType.PROPERTY_CREATED]`` IS, so the same narrowing a reader
sees in the document becomes one the checker sees too.

**THE RENDERING IS BYTE-IDENTICAL IN THE SCHEMA, which is the safety argument and is
asserted rather than assumed.**  Measured on the pinned ``pydantic``:
``Literal[E.A]`` where ``E.A`` is a ``StrEnum`` member of value ``"property.created"``
renders ``{"const": "property.created", "type": "string"}`` -- exactly what
``Literal['property.created']`` renders -- and ``model_validate`` takes the raw string.
``tests/test_pass_b.py`` holds the equality on ``model_json_schema()`` at a converted site
and on the accepts and dump verdicts for its pair, so neither is taken on trust.

**AND IT BELONGS IN THE LOWERING, NOT IN THE RENDERER, because only the lowering has the
KIND.**  The sibling lane measured that ``render`` cannot tell an imported enumeration from
an imported ``Annotated`` alias: ``brand.json``'s ``default_language`` and
``markdown-asset.json``'s ``markdown_flavor`` produce byte-identical
:class:`codegen.ir.TypeRef`\\ s, and ``LanguageTag`` is not callable -- so a renderer asked
to write ``Literal[Symbol.MEMBER]`` could not know whether ``Symbol`` has members at all.
:func:`pins_a_member` never asks that question of a symbol.  It asks it of the base's own
DECLARATION, which states the ``enum`` or does not, and it requires the base's decided type
to be a bare named symbol before it will touch it.  Two independent conditions, both read
where the declaration is in hand, and neither one a guess about what a name denotes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from codegen import ir
from codegen.lower.enum import member_name

#: The member types an enumeration HAS a base for, which is ``lower.enum.BASES``' own
#: reading.  Exact types and not an ``isinstance`` test, because ``bool`` is a subclass of
#: ``int``: a boolean vocabulary renders no enum class, so there is no member to name.
MEMBERS = (str, int)


def vocabulary(declaration: Mapping[str, Any]) -> tuple[object, ...] | None:
    """The members ``declaration`` enumerates, or ``None`` where it enumerates none.

    ``None`` for a declaration with no ``enum``, an ``enum`` that is not a list, one with
    fewer than TWO members, members of mixed type, and a member type with no enumeration
    base.  The two-member floor is this row's own: a one-member ``enum`` is a pin and not a
    vocabulary to narrow, and ``docs/plan/rebuild-plan.md`` §5's ``const`` row is the
    general case for a pin whose field has no collected vocabulary -- it stays, and this
    row never reaches a node it decides.
    """
    members = declaration.get("enum")
    if not isinstance(members, list) or len(members) < 2:
        return None
    kinds = {type(m) for m in members}
    if len(kinds) != 1 or next(iter(kinds)) not in MEMBERS:
        return None
    return tuple(members)


def pin(declaration: Mapping[str, Any]) -> object | None:
    """The one value ``declaration`` pins, or ``None`` where it pins none.

    Both spellings, because §3a names both and they are one fact: a ``const``, and a
    single-member ``enum`` -- *"a single-member ``enum`` against a ``const`` -- the same
    fact from the other side."*
    """
    if "const" in declaration:
        value = declaration["const"]
        return value if isinstance(value, MEMBERS) and not isinstance(value, bool) else None
    members = declaration.get("enum")
    if isinstance(members, list) and len(members) == 1:
        value = members[0]
        return value if isinstance(value, MEMBERS) and not isinstance(value, bool) else None
    return None


def names_a_type(decided: ir.TypeRef) -> bool:
    """Is ``decided`` a BARE NAMED SYMBOL -- one type, nothing wrapped around it?

    The second of the two conditions, and the one that keeps this row off every type that
    is not a class a member can be named on: a container, a union, a generic alias
    applied to arguments, a pin already, and a type the renderer resolves to a dotted path
    rather than to a symbol of the emitted tree.  ``members`` is empty because a type that
    already names members has been narrowed once and narrowing it again would read one
    row's output as another's input.
    """
    return bool(
        decided.local
        and decided.path
        and not decided.container
        and not decided.of
        and decided.key is None
        and not decided.literals
        and not decided.members
        and not decided.facts
        and decided.format is None
    )


def pins_a_member(
    restated: Mapping[str, Any],
    inherited: Mapping[str, Any],
    base_field: ir.Field | None,
) -> ir.TypeRef | None:
    """§3a's Pass B at one property: the base's enumeration, narrowed to the pinned member.

    ``restated`` is the merged declaration this class states for the property (§2's
    intersection, as ``lower_composition`` computed it), ``inherited`` is the base's own
    declaration with a ``$ref`` already dereferenced, and ``base_field`` is the base's
    DECIDED field -- the three things a normalisation of two spellings of one vocabulary
    needs, and none of them a reading of a symbol.

    ``None`` where the row does not fire, which is every case §5's ``const`` row already
    decides: the base enumerates nothing, the base's type is not a bare named symbol, the
    restatement pins nothing, or the pin is not one of the base's members.

    **A pin OUTSIDE the base's vocabulary is NOT this row's to report.**  The two
    declarations apply to one instance, so their intersection is empty and the node admits
    nothing -- which is §5's empty-intersection row, computed by ``_intersection`` before
    this function is reached, on the declarations and not on a decided type.  Returning
    ``None`` leaves that answer where it already is rather than giving the same fact a
    second reporter.

    **Two members spelling ONE Python name means the base rendered a ``Literal`` and not a
    class** (§5's ``enum`` row), so there is no member to name and the row declines.  Asked
    of ``lower.enum.member_name`` and of no second spelling function, which is the
    injectivity argument that module's own docstring makes: the question "do these two
    values collide" is only answerable by the function that does the spelling.
    """
    if base_field is None or not names_a_type(base_field.type):
        return None
    members = vocabulary(inherited)
    if members is None:
        return None
    value = pin(restated)
    if value is None or value not in members:
        return None
    spelled = [member_name(m) for m in members]
    if len(set(spelled)) != len(spelled):
        return None
    return replace(base_field.type, members=(member_name(value),))
