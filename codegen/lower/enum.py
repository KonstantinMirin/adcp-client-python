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
Upper-casing is also the whole of the keyword question *for the canonical name*:
every Python keyword is lower-case, so a ``keyword.iskeyword`` branch beside the
rule would be unreachable code, and the same holds for ``enum.Enum``'s own
reserved names (``name``, ``value``, ``_name_``, ``_value_``) and for ``mro``.

**EACH MEMBER ALSO CARRIES A SECOND SPELLING -- THE VALUE PUSHED THROUGH
UPSTREAM'S IDENTIFIER SANITISER -- AND THAT ONE IS WHERE THE KEYWORD QUESTION
COMES BACK** (:func:`their_spelling`, :func:`member_aliases`,
:attr:`ir.Member.alias`, ``adcp.types._base.MemberAlias``).
``docs/plan/final-state.md`` reading 10: ours are ``UPPER_SNAKE`` because that is
PYTHON's -- ``HTTPStatus.CONTINUE``, ``Signals.SIGHUP`` -- and
``datamodel-code-generator``'s is its sanitiser's output, and ``core/error.json``
states the value list ``transient|correctable|terminal`` while saying nothing
about the attribute a caller types -- so neither spelling is the document's, both
reach the same member, and a class carrying both admits exactly the same set.
``Recovery.transient is Recovery.TRANSIENT``, with ``__members__`` unmoved,
because the second spelling is a DESCRIPTOR and a descriptor is not a member.

**"THE DERIVED SPELLING" IS NOT "THE VALUE VERBATIM", AND THAT WORD COST 159
FILES.**  Where the value is already an identifier the two coincide; where it is
kebab -- ``media-buy``, ``dark-bg``, ``top-left``, ``full-lockup`` -- upstream
does not refuse it, it SANITISES it and ships ``media_buy``.  A rule phrased as
*verbatim* reads the unsanitisable case as a REFUSAL, so the attribute never
appeared -- and ``src/adcp/webhooks.py:92`` reads ``AdcpProtocol.media_buy`` at
MODULE SCOPE, which held all 159 of upstream's ``tests/conformance/`` and
``tests/reporting/`` files at pytest startup.  The spelling is refused rather
than repaired only where the SANITISER cannot rescue it, under one of FOUR
counted reasons (:data:`ALIAS_REFUSALS`) -- reading 10 names three and the
measurement added the fourth.  ``pass`` and ``global`` are the two values that
make ``keyword.iskeyword`` a live branch there, and the sanitiser's answer to
them is the trailing underscore their wheel carries, not a refusal.

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

import re
from collections.abc import Sequence
from dataclasses import replace
from keyword import iskeyword
from typing import Any

import jsonschema

from adcp.types._base import MEMBER_NAMES_TAKEN
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


#: Every character ``datamodel-code-generator``'s identifier sanitiser replaces, as the
#: complement of the ASCII identifier alphabet.  ASCII and not ``str.isalnum``, which is
#: what makes this DIFFERENT from :func:`member_name`'s own character test: ``'é'.isalnum()``
#: is true and ``é`` survives :func:`member_name`, where the sanitiser writes ``_`` for it.
#: The two namings are therefore not one function read twice, and :data:`RE_CASES` is where
#: that difference is counted.
_OUTSIDE_AN_IDENTIFIER = re.compile(r"[^0-9a-zA-Z_]")

#: What upstream's sanitiser prefixes when the derived text cannot BEGIN an identifier --
#: a leading digit, a leading underscore, or nothing at all.  Their constant, not ours:
#: :data:`PREFIX` is what OUR canonical naming uses for the same situation, and the two
#: differ because the two names are two packages' (``field_3d_render = '3d_render'`` on
#: their wheel, ``V_3D_RENDER`` here).
THEIR_PREFIX = "field_"


def their_spelling(value: Any) -> str | None:
    """Upstream's member attribute for one enum value, by their generator's own rule.

    ``docs/plan/final-state.md`` reading 10: **"'the derived spelling' is not 'the value
    verbatim', which is the word that cost 159 files."**  Where the value is already an
    identifier the two coincide and the distinction is invisible; where it is not -- a
    kebab value like ``media-buy`` -- ``datamodel-code-generator`` does not refuse it, it
    SANITISES it to ``media_buy`` and ships that.  A rule phrased as *verbatim* reads the
    unsanitisable case as a REFUSAL and emits no spelling at all, and
    ``src/adcp/webhooks.py:92`` reads ``AdcpProtocol.media_buy`` at MODULE SCOPE: all 159
    files under upstream's ``tests/conformance/`` and ``tests/reporting/`` aborted at
    pytest startup on that one attribute.

    **FOUR CLAUSES, READ OFF THEIR INSTALLED WHEEL AND NOT GUESSED FROM THEIR OUTPUT**:

    1. every character outside ``[0-9A-Za-z_]`` becomes ``_`` (``media-buy`` ->
       ``media_buy``, ``4:2:0`` -> ``4_2_0``);
    2. a python KEYWORD takes a trailing ``_`` (``pass`` -> ``pass_``,
       ``global`` -> ``global_``);
    3. text that cannot BEGIN an identifier -- a leading digit, a leading underscore, or
       the empty string -- is prefixed :data:`THEIR_PREFIX` with its leading underscores
       dropped (``3d_render`` -> ``field_3d_render``, ``1.0`` -> ``field_1_0``);
    4. and anything the first three leave unusable derives NOTHING, which is the ``None``
       this returns -- a value skipped with a counted reason rather than bound under a
       name no caller of either package could have written.

    MEASURED against the genuine 9.6.1 wheel over the 1,125 enum classes of
    ``adcp.types.domains.**`` -- the GENERATED half, which is the only half this is a
    statement about: **6,159 canonical string members, 6,159 identifiers reproduced, 0
    mismatches.**  ``adcp.types.core`` is excluded because it is HAND-WRITTEN and spells
    ``TaskStatus.COMPLETED`` the way the standard library does, so it states nothing about
    a sanitiser; and 36 ``__members__`` entries are python's own ALIASES of a value the
    document repeats (``zip_1 = 'zip'`` beside ``zip``), which is a suffix their generator
    mints for a DUPLICATE and :func:`decide` refuses the whole node for before any name is
    read.

    **Clause 4 is unreachable over a string, and that is stated rather than pruned.**  The
    first clause leaves only ``[0-9A-Za-z_]``, the third guarantees a leading letter or an
    ASCII identifier start, so the result is always an identifier -- and the ASCII result
    is also always NFKC-normal, which is why the NFKC test the verbatim rule needed has no
    successor here.  The branch is kept because ``None`` is the signature a NON-string
    value takes (6 integer members of this bundle have no spelling at all), and collapsing
    the two would make an integer member's refusal a special case at every call site.
    """
    if not isinstance(value, str):
        return None
    derived = _OUTSIDE_AN_IDENTIFIER.sub("_", value)
    if iskeyword(derived):
        derived += "_"
    elif not derived or derived[0].isdigit() or derived.startswith("_"):
        derived = f"{THEIR_PREFIX}{derived.lstrip('_')}"
    return derived if derived.isidentifier() else None


#: **The four reasons a member's SECOND spelling cannot be emitted**, as the words a
#: count is reported under.  ``docs/plan/final-state.md`` reading 10: "REFUSED where the
#: spelling cannot be one *after sanitising*: where no identifier can be derived at all (a
#: leading digit, the empty string, pure punctuation), where two values sanitise onto one
#: attribute, and where the derived spelling collides with a canonical member."
#:
#: **THE CLASSES ARE OVER WHAT THE SANITISER CANNOT RESCUE, NEVER OVER WHAT IT WAS BUILT
#: TO HANDLE**, and that correction is the whole of this row.  The predecessor class was
#: "not a python identifier", asked of the value VERBATIM, and most of what it held was
#: kebab -- ``dark-bg``, ``top-left``, ``full-lockup``, ``media-buy`` -- which upstream
#: does not refuse but TRANSFORMS (:func:`their_spelling`).  A refusal was named where the
#: truth is a transformation, and the cost was 159 of upstream's behavioural files at
#: zero.  So the first class is now asked of the DERIVED spelling and holds only what no
#: derivation reaches.
#:
#: Each is a property of the member SET and not of one value, which is why
#: :func:`member_aliases` ranges over the whole set and why :attr:`ir.Member.alias`
#: defaults to ``None``: whether ``'foo'`` can be a second name depends on what the other
#: members are called.
#:
#: **``NO_SPELLING_DERIVES`` IS THE NON-STRING MEMBERS AND NOTHING ELSE**, which is a
#: consequence of :func:`their_spelling`'s clause 4 being unreachable over a string rather
#: than a figure about this bundle: 6 integer members have no spelling, and a leading
#: digit or a punctuation-only value is handled by :data:`THEIR_PREFIX` instead of
#: refused.  Reading 10 names a leading digit and the empty string as members of this
#: class; the derivation read off upstream's wheel says they are not, and this is the
#: place that disagreement is recorded as a measurement.
#:
#: **``RE_CASES`` IS NO LONGER A THEOREM, AND THE SANITISER IS WHAT TOOK THAT AWAY.**
#: While the alias was the value verbatim, a collision between one member's alias and
#: another's canonical name forced the two to spell ONE canonical name -- which §5's row
#: has already sent to a ``Literal`` with no class and no member names at all
#: (:func:`two_members_spell_one_name`) -- so the class was empty by construction.  That
#: argument used the two namings agreeing on the character test, and they no longer do:
#: :func:`member_name` keeps any ``str.isalnum`` character and :data:`_OUTSIDE_AN_IDENTIFIER`
#: keeps only ASCII, and :data:`THEIR_PREFIX` can mint ``field_x`` from both ``_x`` and the
#: literal value ``field_x`` while ``member_name`` spells those ``X`` and ``FIELD_X``.  So
#: the class is now a GUARD whose emptiness is MEASURED over this bundle rather than
#: argued, and if it is ever non-empty it is a migration-guide entry and not a §5 defect.
#: The bundle's one same-canonical-name collision is still reported where it lives -- at
#: the NODE, ``formats/canonical/html5.json#/properties/clicktag_macro``
#: (``clickTag``/``clickTAG``), whose two member spellings upstream has and this tree has
#: NEITHER of.
#:
#: **A FOURTH REASON THE MEASUREMENT ADDED, which reading 10's three do not name**
#: (``adcp.types._base.MEMBER_NAMES_TAKEN``): the derived spelling is a name the
#: ENUMERATION ITSELF already resolves.  ``"name"`` is a live enum value of this bundle, so
#: the first tree emitted with aliases carried ``name = MemberAlias('NAME')`` and
#: ``Kind.NAME.name`` returned the MEMBER instead of ``'NAME'`` -- the ``enum.Enum.name``
#: descriptor shadowed by a class-body line, which breaks the enum protocol on a class
#: whose document says nothing about python attributes.  Upstream's own wheel carries
#: ``name = 'name'`` at eight classes and takes that breakage; this is the one place the
#: derivation is deliberately not followed, and it is counted rather than hidden.  The
#: three named reasons are collisions with something a DOCUMENT put in the class; this one
#: is a collision with the LANGUAGE.
NO_SPELLING_DERIVES = "no python identifier derives from the value"
RE_CASES = "two values sanitise onto one attribute"
IS_THE_CANONICAL_NAME = "already the canonical member name"
TAKEN_BY_THE_BASE = "a name the enumeration already resolves"

ALIAS_REFUSALS = (NO_SPELLING_DERIVES, RE_CASES, IS_THE_CANONICAL_NAME, TAKEN_BY_THE_BASE)


def member_aliases(members: Sequence[ir.Member]) -> tuple[dict[str, str], dict[str, str]]:
    """The second spelling of each member, and the reason for each one refused.

    ``({alias: canonical name}, {canonical name: reason})``, over the members of ONE
    decided enumeration, and the two halves partition the member set: every member is in
    exactly one of them, so a spelling this compiler does not emit is reported under one
    of :data:`ALIAS_REFUSALS` and never dropped by silence.

    THE one derivation, read by :func:`decide` to fill :attr:`ir.Member.alias` and by the
    gate to count the refusals -- the discipline :func:`member_name` already carries for
    the canonical spelling, for the same reason: a second spelling function written beside
    the one that runs is a copy that can disagree with it, and a refusal count derived
    from a copy would describe a tree nobody emitted.

    **THE ALIAS IS THE SANITISED SPELLING AND NOT THE VALUE VERBATIM**
    (:func:`their_spelling`), which is the correction this function carries and the one
    word that cost 159 of upstream's behavioural files.  The two coincide wherever the
    value is already an identifier, which is most of this bundle, so for those the change
    is invisible; where the value is kebab -- ``dark-bg``, ``media-buy`` -- the verbatim rule
    read a REFUSAL where upstream performs a TRANSFORMATION, and the attribute a consumer
    of their package writes never appeared.  A SANITISED spelling is still not a third
    convention: it is read off their generator's own rule and reproduced 6,159 of 6,159
    against their installed wheel, so what is emitted is a name a caller of their package
    actually writes.

    **``str.isidentifier`` asked of the VALUE was the whole of the defect, and it is gone
    from here.**  It admitted ``pass`` and ``global`` -- live enum VALUES of this bundle --
    whose verbatim spelling is a module that does not PARSE, and it rejected every kebab
    value.  Both halves are now the sanitiser's: clause 2 makes ``pass`` into ``pass_``,
    which is what their wheel carries, and clause 1 makes ``media-buy`` into ``media_buy``.
    A SOFT keyword (``match``, ``case``, ``type``, ``_``) is contextual and binds a name
    fine, so only the hard list is read -- ``keyword.iskeyword``'s own.  The NFKC test the
    verbatim rule needed has no successor: a sanitised spelling is ASCII by construction
    and therefore already normal.

    **The LAST test is the one reading 10 does not name** (:data:`TAKEN_BY_THE_BASE`), and
    it is asked last on purpose: a spelling that is already its own canonical name or
    another member's is refused for the reason a reader of the class would give, and only
    a spelling that would otherwise be EMITTED is weighed against the language's own names.
    """
    aliases: dict[str, str] = {}
    refused: dict[str, str] = {}
    taken = {member.name for member in members}
    for member in members:
        spelling = their_spelling(member.value)
        if spelling is None:
            refused[member.name] = NO_SPELLING_DERIVES
        elif spelling == member.name:
            refused[member.name] = IS_THE_CANONICAL_NAME
        elif spelling in taken or spelling in aliases:
            refused[member.name] = RE_CASES
        elif spelling in MEMBER_NAMES_TAKEN:
            refused[member.name] = TAKEN_BY_THE_BASE
        else:
            aliases[spelling] = member.name
    return aliases, refused


#: What §3a's module-level value list is named under, before its members.  PRIVATE by its
#: leading underscore, which is the whole of why §4 does not govern it: §4 refuses to mint
#: a PUBLIC name no document states, and a consumer never writes this one -- the types
#: built over it keep the names the bundle gives them.
VALUES = "_VALUES"


def values_name(members: tuple[Any, ...]) -> str:
    """The module-level name §3a's VALUE LIST is written under.

    **A function of the VALUE LIST and of nothing else**, which is the property §3a's
    naming correction asks of every catalogue name: "the name is a function of which
    position a walk happened to visit" is the defect, and a name spelled from the members
    cannot be one.  It is not a MINT either -- the name is the value list, spelled as an
    identifier, and it names no concept the bundle does not: "a ``description`` states
    what a thing IS; it does not state what it is CALLED" is about a public type name, and
    this is a private constant a consumer never writes.

    ``member_name`` and no second spelling function, for the reason that function's own
    module docstring gives: it is the one place a value becomes an identifier, so the
    constant's name and the members it carries cannot come to disagree about a value.

    **NOT INJECTIVE on its own, and the guard is where the constants are collected**: the
    separator is also a character ``member_name`` produces, so ``('a', 'b')`` and
    ``('a_b',)`` spell one name.  Two value lists of one module spelling one name is a
    :class:`codegen.refusal.BuildFailure` -- a defect of this compiler and not of any
    document -- raised where a module's constants are gathered
    (``lower/names.py``'s ``the_value_lists``, ``emit.vocabularies_modules``).  Measured
    over this bundle: 0 collisions.
    """
    return "_".join((VALUES, *(member_name(value) for value in members)))


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
    if entry is None:
        # **The VALUE LIST arm, for a restating position no pointer of this document's own
        # text reaches** (:attr:`compiler.Module.restatements`): a node a COMPOSITION
        # re-lowers at a pointer belonging to no edge of either document, and a position
        # whose home is in this same module.
        #
        # **IT WAS ASKED ONLY OF A NODE WITH NO CONSTRAINT BESIDE ITS ``enum``, and that
        # guard is :func:`excluded` restated** -- "a value list beside a ``pattern``
        # admits a subset of the members and is not the entry's vocabulary".  The premise
        # is false by the time this line runs: :func:`excluded` above REFUSES a node whose
        # own constraints exclude any member, so past it every member satisfies every
        # fact, the node admits exactly the members, and the value list IS the admitted
        # set whatever is spelled beside it.  Two positions over one value list therefore
        # admit the same instances, which is the whole of what the key has to mean.
        #
        # Measured, the guard cost exactly one class: ``core/postal-area.json`` re-lowers
        # ``core/postal-country-system.json#/anyOf/3/properties/country``, where §2's
        # intersection rule puts the root's ``^[A-Z]{2}$`` beside ``["DE", "CH", "AT"]`` --
        # the one node of this bundle that reaches the case -- and all three members match
        # it, so BOTH sides dropped the pattern and declared the same three-member class.
        # Relaxing it moves that one position onto the home's symbol and moves nothing
        # else: the emitted tree differs in that module and in no other.
        #
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
    # **§3a's OTHER half, for a value list the bundle states under two names it judges
    # DISTINCT** (:attr:`compiler.Module.value_lists`): "the VALUE LIST is a module-level
    # constant in the catalogue layer, written once per distinct member set; the NAMED TYPE
    # is constructed from it at each position that needs one, keeping the name §4 derives
    # and keeping the types distinct."
    #
    # So this position still DECLARES -- the arms above are the ones that import a type --
    # and what it takes from the catalogue is the values.  Asked after them for the same
    # reason they are ordered among themselves: a position that is the same type as another
    # imports it and has no second type to build.
    shared = mod.value_lists.get(node.members)
    spelled = (
        shared
        if isinstance(shared, str)
        else None
        if shared is None
        else mod.needs_values(shared)
    )
    # **Declared at the node's POINTER, with no name of its own** (§7): the enumeration
    # the walk builds carries the pointer in its name slot and ``lower/names.py`` binds
    # §4's derived name onto it in one pass over the finished module.
    declared = decide(node, node.pointer, value_list=spelled)
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


def decide(
    node: nodes.Enumeration, name: str, *, value_list: str | None = None
) -> ir.EnumDecl | Refusal:
    """What one ``enum`` node IS: a named enumeration over its own members.

    ``value_list`` is §3a's module-level value list this enumeration is CONSTRUCTED from,
    where the bundle states that value list under two names it judges distinct, and
    ``None`` -- which is every other position -- where the members are written in the
    class body.  An input like ``name`` and for the same reason: which of the two forms a
    position takes is §3a's decision and not this function's, and the MEMBERS are derived
    here either way, so nothing about what the node admits depends on it.

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

    # **Reading 10's SECOND spelling, filled here because this is where the member set is
    # finished.**  Every refusal above has already run, so the set handed to
    # :func:`member_aliases` is exactly the one a class would carry -- one member per
    # value, each with its canonical name -- which is what the collision cases are asked
    # over.  The refusal half of the return is not read here and is not dropped either:
    # it is a function of the members, so the gate derives it from the same call rather
    # than from a record this function would have to carry.
    aliases, _ = member_aliases(members)
    spelled = {canonical: alias for alias, canonical in aliases.items()}
    return ir.EnumDecl(
        name=name,
        kind=kind,
        members=tuple(replace(m, alias=spelled.get(m.name)) for m in members),
        description=node.description,
        values=value_list,
    )
