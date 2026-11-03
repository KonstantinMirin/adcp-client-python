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
values that spell one member name get NO ENUM CLASS at all: §5's row gives them a
``Literal`` of the members, because the collision exists only where a Python
IDENTIFIER has to be minted per member and a ``Literal`` mints none
(:func:`two_members_spell_one_name`).  The injectivity that makes the SUFFIXLESS
rule safe is computed over :func:`member_name`, which is the function that
ACTUALLY RUNS: the compiler's ``Enum`` model renders ``{{ field.name }}``
verbatim and names nothing itself, so binding the test to any other function
would leave it vacuous while the compiler aliased two values onto one member.
That is also why the ROUTE is asked of ``member_name`` and not of a second
spelling function written beside it -- one derivation, read twice.
``tests/test_enum.py`` asserts the verbatim rendering rather than assuming it.

**Three refusals, and all three are statements about REPRESENTABILITY** rather
than keywords this row has not got to yet.  Each is a property of the VALUE SET
and therefore holds whichever of the two renderings the set takes, which is why
:func:`decide` is the one reading of it:

* members of mixed type -- there is no one base, and ``StrEnum`` over an integer
  silently stringifies it;
* an empty ``enum`` -- it admits no instance, so there is nothing to enumerate;
* a value appearing twice -- Python ALIASES the second member onto the first
  silently, so the class would carry fewer members than the document lists, and
  ``Literal`` deduplicates it the same way.

A fourth refusal stood here until 2026-10-29 and §5's row withdrew it: two values
spelling one member name is a property of the NAMING and not of the value set, so
the row drops the name rather than the document.

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
  no guard at all -- its cell is ANNOTATION at ROOT, so it states no fact about an
  instance and there is nothing a draw could put to it; measured 0 of 214.
"""

from __future__ import annotations

from typing import Any

import jsonschema

from codegen import compiler, ir
from codegen.compiler import Module
from codegen.keywords import Position
from codegen.refusal import Kind, Refusal
from codegen.schema import nodes

#: The cells an enum node CONSUMES -- this row's own coverage, which is what a
#: screen's second argument is once the table decides admission.  ``type`` agrees with
#: the member types at all 1,069 nodes and is therefore read off the members
#: instead (:data:`BASES`), which is also what lets the 164 typeless enum nodes
#: through.
#:
#: **``default`` was a third entry and the table already admitted it**
#: (``adcp-client-python-3be.8``).  Its cell is ANNOTATION everywhere and FIELD at PROP,
#: so :func:`keywords.lowers` is false at every one of the nine positions and
#: ``compiler._screen`` passes it over whether or not this set names it -- the entry was
#: the stale ADMISSION kind §14 step 5 removed from every one of these sets, kept here by
#: a comment ("``default`` is carried by the PARENT -- all 66 of the bundle's enum
#: defaults are inline, so the field the enum annotates is what holds one") which states
#: exactly why it should NOT be claimed.  Removing it changes no outcome, by construction
#: and then by the three numbers.  What forbids its return is
#: ``test_no_claim_set_names_a_keyword_the_table_admits_for_free``, which is the gate that
#: found it.
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
CLAIMS = frozenset({"type", "enum"})


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


def lower(
    node: nodes.Enumeration, mod: Module, *, of_a_root_union: bool = False
) -> ir.Decided | Refusal:
    """§4's enumeration row: a ``StrEnum``/``IntEnum`` where a name reaches the node and
    its members spell one name each, and a ``Literal`` of its members otherwise.

    **``of_a_root_union`` is a fact this row is HANDED, and §6 settled that it must be.**
    §6 said the pointer read ``hops[-2]`` "becomes ``node.position is BRANCH``" and then
    said why that is the wrong fact: ``position is BRANCH`` says "a branch of SOME union",
    while the predicate it replaces answers "a branch of a ROOT union", and the two
    differ -- taking the shorter sentence literally turns
    ``error-details/accessibility-violation.json``'s ``StrEnum`` into a ``Literal``, which
    changes a module where a document emitted before.  "The fact belongs to the UNION, not
    to the enum... §4 already gives the ``Union`` node the root's siblings when it is at
    ROOT, so the union knows its own position; the branch lowering is told by its parent
    rather than inferring it from itself."  So the enum handler reads a fact it is handed,
    the union handler reads ``node.position``, and **no node parses a pointer**.

    A branch under a ``properties`` segment takes that property's own derived name (§4's
    nested rule), which nothing else wants, so a name reaches it and it keeps its
    ``StrEnum``.  A branch of a ROOT union takes none, because the root's own class holds
    the only name that position derives.

    **The ``Literal`` has a SECOND route in, and §5's row says it is the same answer**:
    a node whose members spell fewer Python names than it has values
    (:func:`two_members_spell_one_name`).  The two routes are ``or``-ed rather than folded
    into one predicate because they answer different questions --
    :func:`resolves_no_name` is about the POSITION, which is a sentence its own docstring
    insists on, and this one is about the MEMBERS -- and they agree on what to do about it.
    """
    # **The row's own screen, at the node's own position, over the cells this row
    # consumes.**  It was in ``emit``'s then-private per-node dispatch, in the enum arm,
    # and the conversion to the parser dropped it;
    # nothing in the bundle paid for that -- the emitted set, the refused set and the tree
    # were all identical -- which is exactly why it is a hole rather than a harmless
    # omission.  ``test_enum.py``'s ``enumMetadata`` cost claim found it by REMOVING the
    # keyword's row and measuring which documents then refuse: three enum roots kept
    # emitting a keyword no section names, which is §9's "a keyword handled in code but
    # named in none of §5, §6 or §7 is an invented rule" arriving through a screen that
    # was not there.
    #
    # **The node's own facts are claimed BESIDE :data:`CLAIMS`, because the MEMBERS
    # decide them**, and that is the same reading ``lower.const`` makes of a one-member
    # set read over more members.  A ``pattern`` beside an ``enum`` lowers at every
    # position, so "a later D2 row does" promises a row that cannot exist; what the row
    # owes is the intersection, and a closed value set makes it a validation:
    # ``{m1..mn}`` intersected with a non-descending constraint is the members every one
    # of them satisfies.  Where ALL do, the enumeration is exactly the document's set and
    # nothing is dropped; where one does not, the document admits a strict subset of the
    # members and :func:`excluded` refuses, because an enumeration listing a value the
    # document excludes is wider than its schema.
    #
    # The docstring's "0 carrying a constraint keyword beside the ``enum``" is a
    # measurement of the RAW bundle; §2's intersection rule merges a root's constrained
    # property with a branch's value set and hands the merged declaration back to the
    # parser, so the nodes the walk decides do reach one --
    # ``core/postal-country-system.json#/anyOf/3/properties/country``, where the root's
    # ``^[A-Z]{2}$`` lands beside ``["DE", "CH", "AT"]``.
    refused = compiler.check_keywords(node, CLAIMS | set(node.facts), mod=mod)
    if refused is not None:
        return refused
    outside = excluded(node)
    if outside is not None:
        return outside
    if resolves_no_name(node, of_a_root_union=of_a_root_union) or two_members_spell_one_name(
        node
    ):
        return literal(node)
    # **§3a's CATALOGUE, asked at the node's own position.**  "A node's type is a
    # REFERENCE to a catalogue entry, or a fresh type where the node is genuinely
    # unique" -- and ``mod.vocabularies`` is the first of those, so a position that
    # RESTATES a vocabulary the bundle names imports the symbol the naming position
    # declares instead of minting a second class over the same members.
    #
    # **Asked here and not above the ``Literal`` arm**, which is a scope and not an
    # oversight: a ``Literal`` position declares no class, so it is not part of the
    # defect §3a states -- "the defect is the positions that restate the vocabulary
    # inline instead" of referencing the existing symbol, and what makes a restatement
    # one is the second CLASS.  Over this bundle that leaves 2 of the 24 restating
    # positions spelling their members a second time inside a ``Literal``
    # (``core/webhook-challenge.json`` and ``core/agent-webhook-challenge.json``, both
    # at an ``if`` branch of *Authentication Scheme*), and widening the arm would change
    # what §4 derives at a position it deliberately gives no name.
    entry = mod.vocabularies.get(node.pointer)
    if entry is None and not node.facts:
        # **The VALUE LIST arm, for a restating position no pointer of this document's own
        # text reaches** (:attr:`compiler.Module.restatements`): a node a COMPOSITION
        # re-lowers at a pointer belonging to no edge of either document, and a position
        # whose home is in this same module.  Asked only where the node carries no
        # constraint beside its ``enum``, because a value list beside a ``pattern`` admits
        # a subset of the members and is not the entry's vocabulary.
        # **A document ROOT is never answered here**, and that is §1's rule: "every
        # portable document contributes a symbol", so a root that referenced another
        # module's class would leave its own document with no exported name.  The pointer
        # is empty exactly at the root (``bundle.nodes_at`` starts at ``""``).
        restated = None if node.pointer == "" else mod.restatements.get(node.members)
        if isinstance(restated, str):
            # A home in THIS module, so the reference is local and no import is written.
            # ``emit`` leaves the home's own pointer out of the map, and the comparison is
            # the guard that says so: the home declares, so it must reach ``decide`` below.
            if restated != node.pointer:
                return ir.Decided(ir.TypeRef(restated, local=True))
        elif restated is not None:
            entry = restated
    if entry is not None:
        # The same two records a ``$ref`` writes, through the same one writer: §1 gives a
        # class one import path, so the symbol is taken from the module that DECLARES it
        # and never re-exported from a third.
        mod.importing(entry.symbol, compiler.Importable(entry.module, entry.document))
        return ir.Decided(ir.TypeRef(entry.symbol))
    # **Declared at the node's POINTER, with no name of its own** (§7): the enumeration
    # the walk builds carries the pointer in its name slot and ``lower/names.py`` binds
    # §4's derived name onto it in one pass over the finished module.
    declared = decide(node, node.pointer)
    if isinstance(declared, Refusal):
        return declared
    collision = mod.declare(node.pointer, declared)
    if collision is not None:
        return collision
    return ir.Decided(ir.TypeRef(node.pointer, local=True))


def excluded(node: nodes.Enumeration) -> Refusal | None:
    """The refusal for a member the node's OWN constraints exclude, or ``None``.

    §2's intersection rule can put a constraint of the value beside a closed value set,
    and the two then disagree about what the node admits: the document's set is
    ``{members} ∩ {the constraint}``, so a member outside the constraint is a value the
    enumeration offers and the document refuses.  Dropping it would be this compiler
    rewriting the document's own ``enum`` -- a member the document enumerates would become
    unnameable, with nothing in the emitted class recording that it was ever there -- and
    keeping it is a model wider than its schema, which is the defect P3 exists to remove.  So the node is refused, on the KEYWORD that
    excludes the member, and the upstream fix is the document stating the set it means.

    Asked of the document's own validator rather than of a table of this module's, for
    :func:`codegen.lower.const.decides`'s reason: one reading of draft-07, and it is the
    schema half's.

    Population 0 over the 1,054 portable documents: the one node the intersection rule
    reaches states ``^[A-Z]{2}$`` beside ``["DE", "CH", "AT"]`` and all three members
    match.  Reached only by a document whose own two statements disagree.
    """
    for keyword, fact in sorted(node.facts.items()):
        check = jsonschema.Draft7Validator({keyword: fact})
        outside = [m for m in node.members if not check.is_valid(m)]
        if outside:
            return Refusal(
                keyword,
                node.pointer,
                f"the {keyword} {fact!r} excludes {outside!r} of the node's own members: "
                "the document admits fewer values than the enumeration would offer, and "
                "neither dropping a member nor keeping one states the document's set",
                kind=Kind.VERDICT,
            )
    return None


def resolves_no_name(node: nodes.Enumeration, *, of_a_root_union: bool = False) -> bool:
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
    #
    # **KEY is the OTHER position that supplies none, added at
    # ``adcp-client-python-10l.20``, and reading it off ``node.position`` is not the
    # mistake §6 corrected.**  §6's objection was to the FACT and not to the field:
    # ``position is BRANCH`` says "a branch of SOME union" where the predicate means "a
    # branch of a ROOT union", and the two differ.  KEY has no such ambiguity -- §4's
    # nested rule names a property, an element, a mapping VALUE and a ``definitions``
    # entry, and names no key at all, which ``containers._key_type`` already states as
    # ``names.Unnamed()``.  So "KEY supplies no name" is unconditional, it is a fact the
    # PARSER assigned about this very node (§6: "Who carries the position.  The node
    # does"), and no pointer is parsed for it.
    #
    # §5's group (a) is the sentence: "A `Literal` of the members is the key type, and
    # Pydantic renders `dict[Literal[…], V]` back as `propertyNames: {enum: […]}` -- the
    # document's own keyword, rendered and gradable.  Faithful, not wide.  Where the key
    # node is named, the `StrEnum` is the key type and renders the same way" -- which is
    # the ``node.title`` half, unchanged and now reached at a second position.
    return not node.title and (of_a_root_union or node.position is Position.KEY)


def two_members_spell_one_name(node: nodes.Enumeration) -> bool:
    """Do two of the node's members spell ONE Python member name?  Then §5's row renders
    a ``Literal`` and no enum class.

    **§5's ``enum`` row, decided 2026-10-29**: "Two members whose spellings yield one
    Python name → a ``Literal`` of the members and NOT an enum class.  The collision
    exists only because an enum mints a Python IDENTIFIER per member; a ``Literal`` needs
    none, so both values are carried exactly as the document spells them and nothing is
    dropped.  This is the same answer the row already gives an untitled branch of a root
    union, reached by a second route."  So this is not a widening: the accepted set is the
    same list of values either way, no rung of §2's ladder is spent and nothing is
    attributed.  What is given up is an importable symbol per member, which is DX.

    **Asked of :func:`member_name` and of nothing else.**  The question "do these two
    values collide" is only answerable by the function that does the spelling, and a
    second spelling function written here to answer it would be a copy that can disagree
    with the one that runs -- the defect the module docstring's injectivity paragraph
    exists to prevent, arriving from the other side.  One derivation, read twice: once
    here to choose the rendering, once in :func:`decide` to name the members of the
    rendering that has names.

    A DUPLICATE VALUE also spells one name twice, and that is a refusal
    (:func:`decide`) rather than a route -- a ``Literal`` deduplicates a repeated value
    exactly as ``Enum`` aliases a repeated member, so the document's list is longer than
    either rendering whatever is chosen.  The order is what keeps the sentence right:
    this predicate sends the node to :func:`literal`, which reads the value set through
    :func:`decide`, which reports the repeat on its own terms before any name is read.

    THE READING, not the figure: the group is every ``enum`` node of the bundle two of
    whose members spell one member name.  ``tests/test_enum.py`` names that set and
    asserts the rendering each of its nodes takes, so a second node joining it is a
    reading that changes and not a count that moves.
    """
    spelled = [member_name(value) for value in node.members]
    return len(set(spelled)) < len(spelled)


def literal(node: nodes.Enumeration) -> ir.Decided | Refusal:
    """D2's rendering for a value set no name reaches: a ``Literal`` of its members.

    **The value set is read by :func:`decide`, not by a second reading of it here.**
    An empty ``enum``, a member type with no base, and a value appearing twice are
    statements about the VALUE SET and hold whatever it is rendered as, so sharing
    ``decide`` is what keeps one answer to "what does this node enumerate". The name
    handed to it is unused -- this rendering claims no symbol -- and is passed as the
    empty string so that nothing here invents one.

    **The ceiling that stood here is GONE, and it is gone by the sharing rather than by a
    split.**  It read: ``decide`` also refuses two values that spell one member name, a
    ``Literal`` has no member names, so that refusal does not belong to this rendering --
    and the upgrade named for the first colliding node was "take the values before
    ``member_name`` runs".  §5's row took that upgrade one step further on 2026-10-29 by
    sending the colliding node HERE, so the refusal is not in ``decide`` for this
    rendering to be excused from: what is left there are the three statements about the
    value set, every one of which this rendering owes as much as an enum class does.  The
    member names ``decide`` derives on this path are read by nobody -- the rendering has
    no slot for one -- which is the whole of why the collision stops mattering.
    """
    enumerated = decide(node, "")
    if isinstance(enumerated, Refusal):
        return enumerated
    return ir.Decided(ir.TypeRef(literals=tuple(m.value for m in enumerated.members)))


def decide(node: nodes.Enumeration, name: str) -> ir.EnumDecl | Refusal:
    """What one ``enum`` node IS: a named enumeration over its own members.

    ``name`` is an input (D3).  The base comes from the members' own type and not
    from ``type``, which is what admits the 164 typeless enum nodes and which the
    accepts draw grades either way: ``harness.check_accepts`` draws against the
    document's ``enum`` and ``type`` together and offers each instance to the class,
    so a base that cannot take a member the document admits refuses it by value
    rather than passing quietly.  (Measured: they agree at 1,069 of 1,069, so this
    is the faithful reading and not a workaround.)
    """
    pointer = node.pointer
    values = list(node.members)
    # :attr:`nodes.Enumeration.members` is empty for BOTH shapes the refusal names -- an
    # ``enum`` that is not a list at all, and one that is the empty list -- because
    # neither enumerates a value.
    if not values:
        return Refusal(
            "enum",
            pointer,
            "an empty enum admits no instance, so it enumerates nothing",
            kind=Kind.VERDICT,
        )

    kinds = sorted({type(v).__name__ for v in values})
    if len(kinds) > 1:
        return Refusal(
            "enum",
            pointer,
            f"members of mixed type {kinds} have no one base",
            kind=Kind.VERDICT,
        )
    kind = BASES.get(kinds[0])
    if kind is None:
        return Refusal(
            "enum",
            pointer,
            f"a {kinds[0]} member has no enumeration base"
            + (" (bool is an int subclass and would enumerate 0 and 1)" if kinds[0] == "bool" else ""),
            kind=Kind.VERDICT,
        )

    # **BOTH spellings are read, which is §6's own sentence and a defect fix.**  §6 lists
    # ``enumDescriptions`` and ``x-enum-descriptions`` in one row -- "Two spellings of one
    # keyword; both are read" -- and this read the first alone, so
    # ``enums/signal-value-type.json``, which states the second and only the second,
    # emitted with no member docstrings.  ``nodes.Enumeration.descriptions`` is the merge
    # the parser makes of the two, and §14's preamble settles the byte delta: a *bytes*
    # mark forbids an UNDECLARED change and not conforming to a sentence the semantics
    # document already decided.
    # **A MEMBER NAME IS DERIVED HERE AND NEVER JUDGED HERE, since 2026-10-29.**  A
    # hand-written ``Kind.VERDICT`` stood in this loop for two values spelling one member
    # name -- one of the three left in this compiler, and the one that cost 21 of the 95
    # refusals for ``formats/canonical/html5.json``'s ``clicktag_macro`` alone.  §5's row
    # withdrew the clause: the collision is a property of the NAMING, which is this
    # compiler's, and ``architecture.md`` §2 forbids reporting a compiler's property as a
    # document's verdict -- so the row drops the NAME (the node renders as a ``Literal``,
    # :func:`two_members_spell_one_name`) and keeps every member the document states.
    # Deleting the raise site is part of that row and not a consequence of it: a refusal
    # left standing beside a route that no longer reaches it is a second answer waiting
    # for a caller.
    #
    # What remains is the repeated VALUE, which is a property of the value set: both
    # renderings carry fewer values than the document lists, so neither can state it.
    descriptions = node.descriptions
    seen: set[Any] = set()
    members: list[ir.Member] = []
    for value in values:
        if value in seen:
            return Refusal(
                "enum",
                pointer,
                f"{value!r} appears twice; Python aliases the second member onto the first "
                "silently, so the class would carry fewer members than the document lists",
                kind=Kind.VERDICT,
            )
        seen.add(value)
        member = member_name(value)
        text = descriptions.get(str(value))
        members.append(
            ir.Member(
                name=member,
                value=value,
                description=text if isinstance(text, str) and text else None,
            )
        )

    return ir.EnumDecl(
        name=name, kind=kind, members=tuple(members), description=node.description
    )
