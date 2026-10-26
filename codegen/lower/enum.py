"""D2's enumeration row: an ``enum`` node becomes a ``StrEnum`` or an ``IntEnum``.

Root and inline, by the same function: a root enum is the whole document and an
inline one is a property's own schema, and nothing about the decision differs.
What differs is what the caller does with the rendered class, and that is the
module writer's half (``codegen.emit``): a root's module binds
``__adcp_schema__`` and ``strict_validate`` beside it, an inline one is just a
class the parent's field names.

Measured over ``schemas/cache/3.2`` (1,054 portable documents), and every number
here is an input to the decisions below rather than a result of them: **214** root
enums, all declaring ``type: "string"``; **1,069** enum nodes over **535**
documents; **137** nodes carrying ``enumDescriptions`` (1,151 entries, 10 of them
multi-line); **66** carrying a ``default``, none of them a root; and **0**
carrying a constraint keyword beside the ``enum``, so there is no
enum-plus-``minLength`` intersection for this row to resolve.

**Member names are UPPER-CASED, and that is a correctness requirement rather than
a convention.**  ``pass`` and ``global`` are both live enum VALUES in this bundle,
and a lower-cased member emits ``pass = "pass"`` -- a module that does not parse,
so the failure is an import error at the gate rather than a wrong type.
Upper-casing is also the whole of the keyword question: every Python keyword is
lower-case, so a ``keyword.iskeyword`` branch beside the rule would be
unreachable code, and the same holds for ``enum.Enum``'s own reserved names
(``name``, ``value``, ``_name_``, ``_value_``) and for ``mro``.

**No member name is ever suffixed.**  A suffix would make two different values
reachable under two names that differ only by punctuation nobody chose, so two
values that spell one member name REFUSE the document instead -- see
:func:`decide`.  The injectivity that makes that safe is computed over
:func:`member_name`, which is the function that ACTUALLY RUNS: the compiler's
``Enum`` model renders ``{{ field.name }}`` verbatim and names nothing itself, so
binding the check to any other function would leave it vacuous while the compiler
aliased two values onto one member.  ``tests/test_enum.py`` asserts the verbatim
rendering rather than assuming it.

**Four refusals, and all four are statements about REPRESENTABILITY** rather than
keywords this row has not got to yet:

* two values spelling one member name -- the class would have fewer members than
  the document has values, and which value won would depend on document order;
* members of mixed type -- there is no one base, and ``StrEnum`` over an integer
  silently stringifies it;
* an empty ``enum`` -- it admits no instance, so there is nothing to enumerate;
* a value appearing twice -- Python ALIASES the second member onto the first
  silently, so the class would again carry fewer members than the document lists.

**``bool`` is excluded on purpose** and is not an oversight of :data:`BASES`:
``bool`` is a subclass of ``int``, so a boolean enum would otherwise render an
``IntEnum`` of 0 and 1 and a consumer would read ``1`` where the document says
``true``.  ``float`` is absent for a plainer reason -- the compiler has no
enumeration base for it.

**KNOWN CEILINGS**, both named rather than coded against because this bundle does
not reach either:

* two nodes with IDENTICAL content under one document are two classes here, where
  D3 says they are one node.  Measured: 36 such repeats over 21 documents, and
  every one of them sits under ``oneOf``/``allOf``/``definitions``/``items`` --
  positions this step does not descend into -- so the reachable count is 0.  The
  fix is a content-keyed memo on the module, and it belongs to the step whose
  population reaches one, because the name it would then keep depends on which
  position is visited first.
* a multi-line member description reaches the compiler's template through
  ``field.docstring``, which is inserted without escaping, so a description
  containing ``\"\"\"`` would emit a module that does not parse.  Measured: 0 of
  the bundle's 1,151 entries contain one.  A root enum's own ``default`` is
  likewise dropped (an enumeration has no field to carry one), and that one needs
  no guard at all -- ``harness.FACTS`` compares ``default``, so the schema
  comparison reddens it; measured 0 of 214.
"""

from __future__ import annotations

from typing import Any

from codegen import compiler, ir
from codegen.refusal import Kind, Refusal

#: The cells an enum node CONSUMES -- this row's own coverage, which is what a
#: screen's second argument is once the table decides admission.  ``type`` agrees with
#: the member types at all 1,069 nodes and is therefore read off the members
#: instead (:data:`BASES`), which is also what lets the 164 typeless enum nodes
#: through.  ``default`` is carried by the PARENT -- all 66 of the bundle's enum
#: defaults are inline, so the field the enum annotates is what holds one.
#:
#: ``enumDescriptions`` is carried (into the member docstrings) and is admitted by
#: the TABLE as the annotation it is, so it is not named here: §6 lists it, with
#: ``x-enum-descriptions`` beside it, as "member docstrings on the enumeration".
#: ``enumMetadata`` is NOT carried, and that is a decision with a measured cost: it
#: states nothing about an instance -- ``enum`` has already closed the value set --
#: and an enumeration has no slot for a per-value metadata block, so the four
#: documents carrying one emit without it.  It is a ceiling because the block carries
#: normative consumer guidance ("SDKs MUST consume this block") that this SDK does not
#: surface.  §6's own row is where that decision now lives, once for every position --
#: which is what reaches the fourth document carrying one
#: (``core/media-buy-available-action-id.json``, a UNION root, which this set does not).
CLAIMS = frozenset({"type", "enum", "default"})


#: What a member name takes when the value's own text cannot begin an identifier.
#: 17 string values (``1.0``, ``4:2:0``, ``3d_render``, ...) and 6 integer values
#: need it.  A prefix rather than a leading underscore, because a single leading
#: underscore reads as private and ``enum`` gives such a name no special meaning
#: to lean on; and ``V`` for the value it names, because the alternative is to
#: derive something from the property or the document, which D5's "an alias names
#: a constraint, never a concept" rules out for the same reason here.
PREFIX = "V_"

#: The JSON Schema type name for each Python member type that HAS an enumeration
#: base, keyed by ``type(value).__name__`` so the lookup is by exact type.
#:
#: Exact, because ``bool`` is a subclass of ``int``: an ``isinstance`` test would
#: admit a boolean enum and render an ``IntEnum`` of 0 and 1, handing a consumer
#: ``1`` where the document says ``true``.  Measured over all 1,069 nodes: 1,066
#: all-``str``, 3 all-``int``, and 0 of every other shape -- so the two rows are
#: the whole of what this bundle needs and the refusals below are guards.
BASES = {"str": "string", "int": "integer"}


def member_name(value: Any) -> str:
    """The Python member name for one enum value.

    THE function the compiler's output is named by; see the module docstring on
    why the injectivity check binds to this one and nowhere else.

    Non-alphanumerics become underscores, the result is stripped of them and
    upper-cased, and a result that cannot begin an identifier takes
    :data:`PREFIX`.  Nothing is suffixed and nothing is truncated, so the name is
    a function of the value alone -- not of the other members, not of the
    document, and not of the order they are visited in.
    """
    name = "".join(c if c.isalnum() or c == "_" else "_" for c in str(value)).strip("_").upper()
    return name if name and not name[0].isdigit() else f"{PREFIX}{name}"


#: The two combinator keywords, as a POSITION test.  A node under one of them shares
#: its parent's instance and is a BRANCH, which is the one position where D3 resolves
#: no name for an enum node -- see :func:`resolves_no_name`.
_BRANCH_OF = ("oneOf", "anyOf")


def resolves_no_name(node: dict, pointer: str) -> bool:
    """Does the POSITION supply no name for this enum node?  Then D2 renders a
    ``Literal``.

    **D2: "an ``enum`` node -> ``StrEnum``/``IntEnum`` where a name reaches it, and a
    ``Literal`` of its members where none does", and an untitled ``enum`` branch whose
    POSITION supplies no name is the second.**  A ``const`` is a one-member value set
    and D2 already renders it without naming it; an ``enum`` is the same construct with
    more members.  A lowering that can proceed without a name does, rather than
    inventing one -- which is D3's own rule that a name is an input to a lowering.

    **A position supplies a name or it does not, and that is a property of the POSITION
    rather than an accident of collision.**  A branch under a ``properties`` segment
    takes that property's own derived name (D3's nested rule, parent +
    ``pascal_case(property)``), which nothing else wants -- so a name reaches it and it
    keeps its ``StrEnum``.  A branch of a ROOT union takes none, because the root's own
    class holds the only name that position derives.

    So the test is whether the combinator is AT THE DOCUMENT ROOT: a root union's branch
    is addressed ``/<kw>/<i>`` and nothing else is.  Written as the pointer's own shape
    rather than as a search for a ``properties`` segment, because the two readings agree
    on every position in this bundle and only this one says what it means -- a deeper
    pointer has a parent, and the parent is what supplies the name.

    **Why no parent node has to be consulted**, which is what lets the union row pass
    nothing down: D3 resolves a branch name in order -- the branch's own title, the
    discriminator ``const``, the sorted required set, the branch's own root type word.
    For an ENUM node only the first can apply, because ``_const_pin`` reads the branch's
    ``properties`` and an enum node declares none, a ``required`` list likewise, and the
    type-word step names a branch only where the root types differ, which two string
    value sets never do.

    Measured over the 1,054 portable documents of ``schemas/cache/3.2``: **4 untitled
    enum branches in 4 documents, 2 at a ROOT and 2 nested**, and the split is exactly
    what this function returns.  The two at a root are
    ``core/geo-place-system.json#/anyOf/0`` and ``core/geo-place-type.json#/anyOf/0``,
    each an untitled string value set beside a constrained string.  The two nested keep
    their ``StrEnum``: ``error-details/accessibility-violation.json`` at
    ``/properties/violations/items/properties/failure_kind/oneOf/0``, whose eight
    canonical values are a concept a consumer dispatches on and so needs an importable
    symbol for, and ``media-buy/get-products-request.json``, which is refused elsewhere.
    Of the 353 combinator-branch positions with no D3 identity of any shape, these 4 are
    the only enum nodes.
    """
    if node.get("title"):
        return False
    hops = pointer.split("/")
    # ``/<kw>/<i>`` and nothing deeper: ``["", kw, i]``.
    return len(hops) == 3 and hops[-2] in _BRANCH_OF and hops[-1].isdigit()  # noqa: PLR2004


def literal(node: dict, pointer: str) -> compiler.Decided:
    """D2's rendering for a value set no name reaches: a ``Literal`` of its members.

    **The value set is read by :func:`decide`, not by a second reading of it here.**
    An empty ``enum``, a member type with no base, and a value appearing twice are
    statements about the VALUE SET and hold whatever it is rendered as, so sharing
    ``decide`` is what keeps one answer to "what does this node enumerate". The name
    handed to it is unused -- this rendering claims no symbol -- and is passed as the
    empty string so that nothing here invents one.

    KNOWN CEILING: ``decide`` also refuses two values that spell ONE MEMBER NAME, and a
    ``Literal`` has no member names, so that refusal does not belong to this rendering.
    It is shared anyway rather than split, because splitting it is two readings of the
    value set to keep in step for a case the bundle does not have: measured over the 4
    nodes this reaches, 0 carry such a pair. The upgrade, at the first one, is to take
    the values before ``member_name`` runs rather than to copy the other three refusals.
    """
    return compiler.Decided(
        ir.TypeRef(literals=tuple(m.value for m in decide(node, "", pointer).members))
    )


def decide(node: dict, name: str, pointer: str) -> ir.EnumDecl:
    """What one ``enum`` node IS: a named enumeration over its own members.

    ``name`` is an input (D3).  The base comes from the members' own type and not
    from ``type``, which is what admits the 164 typeless enum nodes and which the
    schema comparison grades either way -- it compares ``type`` as a fact the
    document states, so a base disagreeing with a declared ``type`` reddens
    rather than passing quietly.  (Measured: they agree at 1,069 of 1,069, so this
    is the faithful reading and not a workaround.)
    """
    values = node.get("enum")
    if not isinstance(values, list) or not values:
        raise Refusal(
            "enum",
            pointer,
            "an empty enum admits no instance, so it enumerates nothing",
            kind=Kind.VERDICT,
        )

    kinds = sorted({type(v).__name__ for v in values})
    if len(kinds) > 1:
        raise Refusal(
            "enum",
            pointer,
            f"members of mixed type {kinds} have no one base",
            kind=Kind.VERDICT,
        )
    kind = BASES.get(kinds[0])
    if kind is None:
        raise Refusal(
            "enum",
            pointer,
            f"a {kinds[0]} member has no enumeration base"
            + (" (bool is an int subclass and would enumerate 0 and 1)" if kinds[0] == "bool" else ""),
            kind=Kind.VERDICT,
        )

    descriptions = node.get("enumDescriptions")
    seen: set[Any] = set()
    spelled: dict[str, Any] = {}
    members: list[ir.Member] = []
    for value in values:
        if value in seen:
            raise Refusal(
                "enum",
                pointer,
                f"{value!r} appears twice; Python aliases the second member onto the first "
                "silently, so the class would carry fewer members than the document lists",
                kind=Kind.VERDICT,
            )
        seen.add(value)
        member = member_name(value)
        if member in spelled:
            raise Refusal(
                "enum",
                pointer,
                f"{value!r} and {spelled[member]!r} both spell the member {member!r}",
                kind=Kind.VERDICT,
            )
        spelled[member] = value
        text = descriptions.get(str(value)) if isinstance(descriptions, dict) else None
        members.append(
            ir.Member(
                name=member,
                value=value,
                description=text if isinstance(text, str) and text else None,
            )
        )

    description = node.get("description")
    return ir.EnumDecl(
        name=name,
        kind=kind,
        members=tuple(members),
        description=description if isinstance(description, str) and description else None,
    )
