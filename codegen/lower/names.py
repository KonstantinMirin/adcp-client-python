"""Naming and content dedup, as ONE pass over the finished module.

``docs/plan/architecture.md`` §7: **"Naming is a pass over the module, not a thread
through the walk."**  This module takes a :class:`codegen.compiler.Module` whose
declarations are keyed by POINTER and whose ``TypeRef``\\ s name local declarations by
pointer, and returns the module with a symbol table -- by §4 of
``docs/plan/rebuild-plan.md``'s rules: the root by ``pascal_case(title)``; a nested
declaration by its OWN position (``<Property>`` at PROP, ``<Property>Item`` at ELEM,
``<Property>Value`` at MAPV, ``<Root><Key>`` at DEF); a branch by its own ``title``, else
the ``const`` it pins on the discriminating property, else its sorted ``required`` set,
else its index among the branches (``<Base>Branch<i>``).

**A nested name is its own position and not the path to it, and §4's collision rule is
what pays for that** (:data:`COLLISION`, :func:`spell`).  "The module path already
carries the document, so a nested name does not repeat it" -- so two positions of one
module can derive one name, and where N do, ALL N lengthen by their own nearest ancestor
segment until every name in the module is unique.  Before the rule was written this pass
folded every hop to the root and concatenated, which cannot collide and therefore needed
no rule: 808 of 2,118 emitted classes were longer than 30 characters, 141 longer than 50,
and one was ``GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext``.
With the rule it is 235 of 2,144 over 30, the median falls from 26 characters to 17, and
2,116 of 2,226 named positions keep the one segment §4 derives.
:func:`segments` is the same readings kept as a CHAIN so that :func:`spell` can spend as
few of them as the module requires, and the chain's whole spelling is the name the fold
gave -- which is why the refusal two indistinguishable positions earn is the same
refusal, over the same documents, as before.

**The walk computes no name, and §7 reads §4's own rule strictly.**  §4 says a name is
an input to a lowering and is never computed inside one; §7 adds "read strictly, it is
not an input either: it is assigned after".  So a handler declares at a pointer and
records the HOP its child's name is derived through (:data:`Hop` below), and nothing
before this pass holds a symbol of this module's own.  Every symbol slot in the IR --
``ClassDecl.name``, ``EnumDecl.name``, ``AliasDecl.name``, ``RootBinding.symbol``,
``ClassDecl.bases``, ``ClassDecl.branches``, ``UnionInstall``, and every ``TypeRef``
marked ``local`` -- holds a POINTER until :func:`assign` runs, and a NAME after.  A
pointer is ``""`` or begins with ``/`` and a name is an identifier, so the two cannot be
mistaken for one another, and the one slot that mixes them is ``bases``: a base is
either a pointer into this module or a symbol another module declares, and :func:`assign`
resolves the pointers and leaves the symbols.

**The SCOPE of the dedup is ONE MODULE, which is one document (D1).**  §9 of the
semantics document decides it: "do not decide one document's output by a census over
the run -- a name, a shape or an import that depends on which other documents the run
includes makes a one-document emission and a whole-bundle emission disagree about the
same document."  Two documents that inline identical content therefore keep a class
each; collapsing them would need a rule for which module owns the survivor, D1 gives a
node exactly one home, and 0 of the bundle's 1,271 identical-content groups have a ROOT
carrying that content for a ``$ref`` to reach.  :data:`SCOPE` is the sentence, and the
only inputs this pass has are the module and the reserved attribute set, so the scope is
held by the signature as well as by the sentence.

**The dedup KEY is NODE EQUALITY.**  ``codegen/schema/nodes.py`` excludes ``pointer``
and ``position`` from a node's equality, so two nodes are equal exactly when they state
the same thing about an instance -- which is §4's content dedup read off the type system
rather than off a JSON serialisation with a position bit appended (``emit.content_key``,
deleted).  Measured over the memo's own population: 7,250 nodes in 677 documents, 283
groups by the deleted key and 283 by this equality, and 0 documents whose partition
differs.  **Do not reintroduce a serialisation-based key.**

**What the dedup does with a group**: §4's own sentence.  "The class is declared under
the name of the position the walk reaches first, and every later position of the same
content binds its own derived name to that class by identity, ``X = Y``."  So one class
per group, declared at the first pointer in document order, and every later pointer
binds the name ITS OWN position derives -- never a sibling position's name, which would
read as one branch carrying another's type and would make a public symbol a function of
which key the walk reached first.

**ONE refusal is this pass's, and it is a VERDICT of the document: two pointers deriving
one name.**  A branch with no identity was the second, and §4 has the fourth naming rule
that retires it (``docs/plan/architecture.md`` §13 item 7, closed 2026-10-26): a branch
with no ``title``, no pinned ``const`` and no ``required`` set takes its **index among the
branches**, ``<Base>Branch<i>``.  A name is not an acceptance fact, so the fallback
neither widens nor narrows and costs no approximation; the index is a function of the
branch's own position in its own document, so no census over the run enters and the
refusal was minting a verdict where §4 states a fallback.

**Not EVERYTHING here runs in the pass, and the reading is which calls the WALK makes.**
Four functions are the walk's: :func:`same_node` and :func:`adopt`, because a second
occurrence's children are never lowered and the pruning is a decision about the walk;
and :func:`alias_for` and :func:`name_the_node`, because the alias a ``$ref``-named node
takes carries that node's own facts and the parent's field must reference it rather than
restate it.  All four are NAMING acts -- a name bound to a declaration, at a pointer --
which is why §7 puts them beside the rules, and none of them computes a name: each
declares at a POINTER and :func:`assign` is still the one function that binds a symbol.
:func:`name_the_node` and :func:`alias_for` arrived from ``compiler.py`` at
``adcp-client-python-3be.5``, with the walk's per-node entry (``compiler.lower_node``),
which is what stopped reaching them through ``codegen.emit``.

**The index is the LAST rung and is accepted only there.**  A positional name carries
nothing about which position it names -- the upstream v9 SDK numbers 1,092 of its 4,360
classes and renames a sibling when a branch is inserted ahead of it -- so §4 reaches for
it only after the three IDENTITY rungs have each been tried and found nothing.  A document
that gives a branch no identity at all leaves nothing else, and an index at least says
WHICH branch.  :func:`branch_identity` is the one place the order is written.
"""

from __future__ import annotations

import keyword as _keyword
import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from codegen import ir
from codegen.refusal import Kind, Refusal
from codegen.schema import nodes

if TYPE_CHECKING:  # pragma: no cover -- the annotation only; see :func:`assign`
    from codegen.compiler import Decided, Module

#: **The stated scope of the content dedup** (§14 step 7's own words for this row, and
#: §9's rule behind it).  Read by ``tests/test_emit.py``, so the sentence the code states
#: and the sentence a check grades are one string.
SCOPE = (
    "one module, which is one document (D1): a name, a shape or an import that depended "
    "on which other documents the run includes would make a one-document emission and a "
    "whole-bundle emission disagree about the same document (section 9)"
)


# --------------------------------------------------------------------------- #
# §4's name rules
# --------------------------------------------------------------------------- #
def class_name(title: str) -> str:
    """``pascal_case`` that keeps an acronym: only the first letter of a word is
    touched, so ``TMPX Chunk`` stays ``TMPXChunk`` and does not become
    ``TmpxChunk``.

    **A keyword is NOT suffixed here, and that is measured rather than tidy**
    (``adcp-client-python-10l.37``).  A title is one SEGMENT of a chain and a keyword is
    a property of the whole SPELLING, so the guard belongs where the spelling is made
    (:func:`spelling`).  Put here it moved two symbols the grammar never objected to:
    ``core/geo-region-support.json``'s ``CountriesValueTrue`` and
    ``governance/sync-plans-request.json``'s ``BudgetTrue`` are both ``_suffixed`` onto
    their parent -- §4 names a pinned branch ``<Base><Const>`` -- so the segment is
    ``True`` and the name is not.
    """
    words: list[str] = []
    cur = ""
    for ch in title:
        if ch.isalnum():
            cur += ch
        elif cur:
            words.append(cur)
            cur = ""
    if cur:
        words.append(cur)
    return "".join(w[:1].upper() + w[1:] for w in words)


def _suffixed(chain: tuple[str, ...], suffix: str) -> tuple[str, ...]:
    """``chain`` with ``suffix`` spelled onto its LAST segment rather than appended as a
    segment of its own.

    §4 names three positions off their container -- ``<Property>Item`` for an element,
    ``<Property>Value`` for a mapping value, ``<Base><Const>`` for a pinned branch -- and
    each of the three is ONE segment, because ``Item``, ``Value`` and ``True`` name no
    position on their own: a collision between two elements has to lengthen past the
    container to say anything at all.

    An empty chain is the position under a mapping's KEY, which derives no name
    (:class:`Unnamed`), and the suffix is then the whole chain -- which is what the fold
    produced there before this pass had segments.
    """
    return (chain[:-1] + (chain[-1] + suffix,)) if chain else (suffix,)


#: One WORD of a derived symbol: an acronym run, a capitalised word, or a lowercase run.
#: The acronym arm is first and refuses to eat the next word's capital, so
#: ``HTMLAssetRequirements`` is three words and not ``HTMLA`` plus ``ssetRequirements``.
#: It is the inverse of :func:`class_name`'s "only the first letter of a word is touched",
#: which is why an acronym survives the round trip.
_WORD = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")


def _words(symbol: str) -> tuple[str, ...]:
    """A derived symbol back into the words :func:`class_name` spelled it from."""
    return tuple(_WORD.findall(symbol))


def _distinguishing(target: str, root: str) -> str:
    """**What the TARGET's name says that the ROOT's does not** -- §4's fourth branch rung.

    §4: "Where the root's name and the target's share a leading run, the branch takes the
    root's name plus the target's distinguishing remainder -- so ``AssetRequirementsImage``,
    not the target's name repeated."  The run is read at either END, because the bundle
    writes it both ways and one rule has to cover both: ``AssetRequirements`` beside
    ``ImageAssetRequirements`` shares its run as the target's SUFFIX, and
    ``GetCreativeFeaturesResponse`` beside ``GetCreativeFeaturesSuccess`` shares it as
    both names' PREFIX.  Measured over the 13 bare-``$ref`` branches of bundle 3.2 that
    reach this rung: 12 share a suffix and 1 a prefix, and 0 share both.

    **Why the remainder and not the target's name itself.**  §4's rung says "the TARGET's
    own derived name", and spelled literally that name is already TAKEN: the branch's
    second base IS the target, so the module imports the symbol, and :func:`spell`'s
    ``occupied`` is the rule that an imported name is a name taken.  A branch is a chain
    of one at this rung and has no ancestor to lengthen by, so ``occupied`` would keep the
    shadowing name rather than refuse it -- ``class ImageAssetRequirements(AssetRequirements,
    ImageAssetRequirements)`` -- and every field annotated with the import would be
    retyped.  The remainder spells the same fact onto the base's own segment, which is
    what §4's own example asks for and what the three existing suffix rungs already do
    (:func:`_suffixed`).

    Returns ``""`` where the target's name says nothing the root's does not; the rung then
    answers nothing and the branch falls to its index, exactly as §4's root-collision
    clause has a rung do.
    """
    them, mine = _words(target), _words(root)
    prefix = 0
    while prefix < min(len(them), len(mine)) and them[prefix] == mine[prefix]:
        prefix += 1
    suffix = 0
    while (
        suffix < min(len(them), len(mine)) - prefix
        and them[len(them) - 1 - suffix] == mine[len(mine) - 1 - suffix]
    ):
        suffix += 1
    # The longer shared run wins, and only one of the two is spent: a name sharing a run
    # at BOTH ends would otherwise lose the middle twice.
    if suffix > prefix:
        return "".join(them[: len(them) - suffix])
    return "".join(them[prefix:])


def spelling(chain: tuple[str, ...], depth: int) -> str:
    """One position's name carrying its last ``depth`` segments.

    ``depth`` 1 is the name §4 derives, each further step is the next nearest ancestor
    prepended (§4's collision rule, :func:`spell`), and ``len(chain)`` is the whole path
    -- which is the name this emitter gave every position before the rule was written.

    **A SPELLING PYTHON RESERVES IS SUFFIXED, which is :func:`field_name`'s own loop at
    the other half of the seam** (``adcp-client-python-10l.37``).  ``str.isidentifier``
    -- the check ``emit`` makes of a root's derived symbol -- answers ``True`` for every
    keyword, so ``class None(Base):`` passed every guard this compiler had and the
    module it was written into did not PARSE.  A keyword is a name the grammar has
    taken, which is the fact :func:`spell`'s ``occupied`` already carries for a name an
    IMPORT has taken; the two answers differ only because a position can lengthen past
    an import and none can lengthen past the grammar -- a ROOT and a titled BRANCH are
    chains of one.  So the spelling moves by the one character ``field_name`` moves it
    by, and it moves HERE rather than in :func:`class_name` because the question is
    about the whole name: two of this tree's symbols end in a ``True`` segment and
    neither is a keyword.  Two positions that collide after the suffix collide for
    :func:`spell` to see, because this is the function it compares.

    Nothing is lost, because a class's identity is its ``__adcp_schema__`` pointer and
    not its symbol -- the difference from a FIELD, where the wire name is kept as an
    alias because the document's accepted set depends on it.

    Measured over the committed tree: **2 positions**, the branches
    ``formats/canonical/display_tag.json#/allOf/1/oneOf/3`` and
    ``formats/canonical/image.json#/allOf/1/oneOf/3``, each titled "none".  No other
    symbol in the tree moves by one character.
    """
    name = "".join(chain[max(len(chain) - depth, 0) :])
    while _keyword.iskeyword(name):
        name += "_"
    return name


def entry_key(pointer: str) -> str:
    """The ``definitions``/``$defs`` KEY a local reference's pointer names.

    RFC 6901's two escapes, inverted.  The one reading of a pointer's last segment in
    this compiler, and it is a KEY and not a POSITION: §6 forbids recovering a position
    from a pointer string, and a DEF entry's position is the parser's (``Position.DEF``)
    -- what is read here is the name the document gave the entry, which the pointer
    carries because the pointer IS that key.
    """
    return pointer.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~")


# --------------------------------------------------------------------------- #
# the HOPS: what the walk records instead of a name
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Root:
    """The document ROOT: ``pascal_case(title)``, and the OUTERMOST segment of every
    name derived below it (:func:`segments`)."""

    title: str


@dataclass(frozen=True)
class Property:
    """A value of ``properties``: ``<Property>``, a segment of its own."""

    parent: str
    key: str


@dataclass(frozen=True)
class Item:
    """An array's ``items``: ``<Property>Item``, spelled onto the segment the array is
    spelled with, because ``Item`` names no position on its own."""

    parent: str


@dataclass(frozen=True)
class Value:
    """A mapping's value schema: ``<Property>Value``, spelled onto the segment the
    mapping is spelled with, because ``Value`` names no position on its own."""

    parent: str


@dataclass(frozen=True)
class Entry:
    """A ``definitions``/``$defs`` entry: ``<Root><Key>``, the root being the parent."""

    key: str


@dataclass(frozen=True)
class Branch:
    """A branch of ``oneOf``/``anyOf``: the FACTS §4's four rules read, as values.

    §4 "Names"'s branch rules are "its own ``title``, else the ``const`` it pins on the
    discriminating property, else its sorted ``required`` set, else its index among the
    branches", and each of the first three is a
    fact of the branch's own DECLARATION.  The declaration is ``lower/union.py``'s to read
    -- §6 keeps that reading at the declaration level and
    ``tests/test_import_rule.py``'s ``MAY_READ_A_DECLARATION`` names the module -- so what
    crosses into this pass is the three facts and not the mapping.  Extracting a fact is
    not deriving a name: which fact wins, how it is spelled, and what a parent prefix is
    are all below, and a module that reads no mapping cannot come to read one.

    :attr:`pin` is the ``const`` the branch pins on the discriminating property, read over
    the property map §4 gives the rule: the branch's own, or -- for a bare ``$ref`` branch
    -- the TARGET's, because §4 says a ``$ref`` branch's fields are the target's and the
    walk is what resolved them.

    :attr:`index` is the fourth rule's own fact, and its PRESENCE is the difference
    between the two positions a branch is named at.  A ROOT union declares one class per
    branch, so a root branch needs a name of its own whatever it states and the walk
    records its index; a NESTED union is a TYPE, and a branch that lowers to an annotation
    needs no name at all, so the walk records none and §4's fourth rung has nothing to
    apply -- the branch falls back to the union's own derived name, which is what a member
    type has always been spelled with.  One field carries that difference because it IS
    that difference: a second boolean beside it would be a second copy of the decision.

    It is a FIELD and never recovered from the pointer string.  The branch's pointer ends
    in the index and §6 forbids reading a position out of a pointer -- the union is what
    knows its branch order, so the union hands the hop its index, exactly as it hands the
    branch the fact that it is a root union's branch.
    """

    parent: str
    #: The branch's own ``title``, where it states one that is a non-empty string.
    title: str | None = None
    #: **Every ``const`` the branch pins, in the order the document writes the keys**
    #: (§4, "Rung 2 reads EVERY pin the branch states", decided 2026-10-29).  It held ONE
    #: pin and declined to choose where a branch pinned several, which sent the five most
    #: heavily identified branches of the bundle to their index.  A tuple and not a scalar
    #: because the rung reads them all: one field, meaning "the pins this branch states",
    #: where a scalar beside a count would be two readings of one keyword.
    pins: tuple[Any, ...] = ()
    #: Its ``required`` set, as the document lists it.
    required: tuple[str, ...] = ()
    #: **The SYMBOL a bare ``$ref`` branch's target declares** -- §4's fourth rung, which
    #: reads "where the branch is a bare ``$ref``, the TARGET's own derived name".  It is
    #: the one naming fact of a branch that no reading of the branch's own node can reach:
    #: such a branch states nothing but ``$ref``, so rungs 1 to 3 all answer ``None`` and
    #: every one of them falls to the index.  ``lower/union.py`` resolves the target
    #: already (:class:`union.Inherited`, "the SYMBOL, which is the branch's second base")
    #: and hands the resolution over rather than this pass reading a reference.
    #:
    #: ``None`` where the branch is not a bare ``$ref``, and ``None`` where the target is
    #: a node of THIS module: a local ``$ref``'s ``TypeRef.path`` is a POINTER until
    #: :func:`assign` runs, so there is no name to read and the branch keeps its index.
    #: A pointer is ``""`` or begins with ``/`` and a name is an identifier, which is this
    #: module's own convention for telling the two apart.
    target: str | None = None
    #: Its index among its union's branches, in the document's own order, where the branch
    #: is a CLASS and so needs a name of its own; ``None`` where it is a member type.
    index: int | None = None


@dataclass(frozen=True)
class Unnamed:
    """A position with NO name to derive: a mapping's KEY type.

    Not an omission and not a failure: ``propertyNames`` states a constraint on a key
    and §4's nested rule derives a name from a PROPERTY, an element or a value, so there
    is no rule to apply here.  The empty name is what the walk passed at those two call
    sites before this pass existed, and a declaration that needed one would collide with
    the other unnamed position and refuse by name.
    """


#: What the walk records for a child it lowers, instead of the child's name.  Keyed by
#: the child's POINTER on :attr:`codegen.compiler.Module.hops`.
#:
#: **A child at its PARENT's pointer needs no hop**, and two shapes are in that
#: position: a ``type``-list member and an extras store, both of which the parser builds
#: at the node's own pointer because each is the same instance re-read (§4).  They
#: inherit the entry the grandparent recorded, so there is one name per pointer and the
#: recursion below cannot meet itself.
Hop = Root | Property | Item | Value | Entry | Branch | Unnamed


# --------------------------------------------------------------------------- #
# §4's branch rules
# --------------------------------------------------------------------------- #
def branch_identity(hop: Branch, parent: tuple[str, ...]) -> tuple[str, ...] | None:
    """§4 "Names"'s four branch rules, in order, as the branch's own SEGMENTS, or
    ``None`` where none of them applies.

    A title names ITSELF, so it is a chain of one and the branch's ancestors are no part
    of it.  A ``const``, a required set or an index is spelled ON the parent's own last
    segment, so a branch named by any of them shares its base's spelling -- which is what
    §4 writes for the fourth rule as well, ``<Base>Branch<i>``.  The required-set key is
    deliberate: it is stable when the spec adds an OPTIONAL field and renames exactly
    when requiredness changes, which is a semantic change a caller should meet as an
    ``ImportError`` rather than as a silent repoint.

    **Which fact wins decides the SPELLING and the PLACEMENT together, which is why both
    are here.**  A caller handed the spelling alone would have to read ``hop.title``
    again to find out whether the ancestors belong in the chain, and that reading would
    be a second copy of the first rule.

    **A name is never derived from the neighbourhood.**  The rule a previous generator
    reached for -- name the sole classed branch after its PARENT -- makes a class name a
    function of what its siblings happen to be, so adding a branch renames an unrelated
    class.  §4 has no such rule, and its fourth rung is not that rule either: an index is
    a fact of the branch's OWN position, so what it reads is where this branch is and
    never what its siblings happen to state.  Inserting a branch AFTER this one moves no
    name, which is the property :data:`INDEX_IS_THE_LAST_RUNG` states and
    ``tests/test_names_collision.py`` grades.

    **The index is the LAST rung and only the last.**  It is tried after all FOUR identity
    rungs have answered nothing, because a positional name says nothing about
    what it names; where an identity exists the identity wins, and a branch whose index
    the walk did not record (a nested union's, which needs no name of its own) answers
    ``None`` and takes the union's own derived name.

    **The fourth identity rung is the bare ``$ref``'s target** (:data:`REF_TARGET_RUNG`),
    added because the index was reaching 18 branches of this bundle and 13 of them are a
    bare ``$ref`` whose target names itself -- ``image-asset-requirements.json``,
    ``video-asset-requirements.json``.  ``isinstance(req, AssetRequirementsBranch7)``
    requires counting the document's branches to learn that it means JavaScript, which is
    the usability failure a positional name IS.
    """
    rungs = branch_rungs(hop, parent)
    return rungs[0] if rungs else None


def branch_rungs(hop: Branch, parent: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """§4's four branch rules as a LADDER: every rung that answers, in the section's order.

    :func:`branch_identity` is the FIRST rung of this and is what a chain starts at.  The
    rest exist because §4 now says a rung can fail to identify: "Where a rung derives one
    name for two branches it has not identified either, so BOTH fall to the next rung",
    and "a branch colliding with its own document ROOT ... falls to the next rung"
    (both decided 2026-10-29).  Falling is not lengthening -- these chains are one segment
    with nothing to lengthen by -- so it is a second axis and :func:`spell_the_rungs`
    walks it.

    **Rung 2 is EVERY pin, in the document's own key order** (:attr:`Branch.pins`).  A
    branch pinning ``country: FR`` and ``system: code_postal`` is ``FRCodePostal``; one
    pinning ``country: US`` alone is ``US``, because one pin in key order is that one pin.
    The order is the DOCUMENT's and never sorted: sorting would make a public symbol a
    function of spelling, which is the reading ``_const_pin`` declined for and the reason
    it answered nothing at all for such a branch.

    **Which rungs a ROOT has: exactly one.**  A root is not a branch and never reaches
    here -- :func:`segments` answers it from :class:`Root` -- so its ladder is the single
    chain §4's D5 fixes, and "the root keeps the name" needs no clause of its own here.
    That is why the collision rule below says only "a position with a rung left advances":
    the root has none, so it cannot move, and the branch beside it is the side that does.
    """
    out: list[tuple[str, ...]] = []
    if hop.title:
        out.append((class_name(hop.title),))
    if hop.pins:
        out.append(_suffixed(parent, "".join(class_name(str(p)) for p in hop.pins)))
    if hop.required:
        out.append(
            _suffixed(parent, "".join(class_name(str(k)) for k in sorted(hop.required)))
        )
    if hop.target and parent:
        # **Rung 4, and the last IDENTITY rung** (§4 "Names", the branch ladder): "else,
        # where the branch is a bare ``$ref``, the TARGET's own derived name".  Both
        # inputs -- the target's symbol and the root's own name -- are facts about the ONE
        # branch, so the rule is insertion-stable, which is §4's own criterion and what
        # the branch rule reverted at ``64d0f897`` failed: inserting a thirteenth asset
        # kind ahead of the others renames none of them.
        remainder = _distinguishing(hop.target, parent[-1])
        if remainder:
            out.append(_suffixed(parent, remainder))
    if hop.index is not None:
        out.append(_suffixed(parent, f"Branch{hop.index}"))
    # A rung spelling the same chain as the rung above it is not a rung to fall to: it
    # identifies the branch no better and the fall would not terminate.  Measured: a
    # branch whose title spells its own pin, and a one-branch union whose index repeats
    # its required set.
    return tuple(dict.fromkeys(out))


#: §4's fourth IDENTITY branch rung, in the section's own terms.  QUOTED by the check that
#: grades it (``tests/test_names_collision.py``), so the sentence the code states and the
#: sentence a check reports against are one string.
REF_TARGET_RUNG = (
    "where the branch is a bare $ref, the TARGET's own derived name; and where the root's "
    "name and the target's share a run, the branch takes the root's name plus the target's "
    "distinguishing remainder -- AssetRequirementsImage, not the target's name repeated. "
    "Both inputs are facts about the one branch, so the rule is insertion-stable "
    "(section 4)"
)

#: §4's fifth branch rule and the one ground it stands on, in the section's own terms.
#: QUOTED by the check that grades it (``tests/test_names_collision.py``), so the sentence
#: the code states and the sentence a check reports against are one string.
INDEX_IS_THE_LAST_RUNG = (
    "a branch with no title, no pinned const and no required set takes its index among "
    "the branches, <Base>Branch<i>; a name is not an acceptance fact, so the fallback "
    "neither widens nor narrows, and the index is a fact of the branch's own position, "
    "so inserting a branch after it moves no name (section 4)"
)


# --------------------------------------------------------------------------- #
# the field spelling, which is pydantic's own surface read once
# --------------------------------------------------------------------------- #
def field_name(key: str, reserved: frozenset[str] = frozenset()) -> str:
    """The Python field name for a property key, which is the key itself unless the
    model layer cannot carry a field under that name.

    A key is carried as-is or it is carried under an ALIAS, never dropped.  The bundle
    has keys a Python attribute cannot spell (``$schema``) and keys pydantic reads as
    something other than a field: a leading underscore makes a private attribute and no
    field at all, so ``core/truncation-sentinel.json``'s required ``_truncation`` was
    silently absent from the model -- the model refused the document's own instance AND
    accepted an instance omitting the required key, in the same class.

    The alias is the ONLY accepted spelling (no ``populate_by_name``), so the model's
    accepted set stays the document's: the wire name is accepted and the Python name is
    not a second way in.

    **``reserved`` is what the MODEL LAYER carries, and it is an ARGUMENT because §8
    draws the boundary where it does.**  This function read
    ``hasattr(pydantic.BaseModel, name)``, and that import was the one model-layer read
    left outside ``codegen/render.py`` -- named as a shrink-only exception in
    ``tests/test_import_rule.py``'s set.  §8 bans ``pydantic`` under ``lower/``
    outright, so moving the reading here would have GROWN that set; the set shrinks
    instead, because the reserved names are DERIVED in ``render.py`` (``render.RESERVED``)
    and handed to :func:`assign` by the run.  The fact is still read off the model layer
    and never listed by hand, and no module under ``lower/`` names pydantic.
    """
    name = "".join(c if c.isalnum() or c == "_" else "_" for c in key).lstrip("_")
    if not name or name[0].isdigit():
        name = f"f_{name}"
    while _keyword.iskeyword(name) or name.startswith("model_") or name in reserved:
        name += "_"
    return name


# --------------------------------------------------------------------------- #
# §4's content dedup: the equality, and the binding at a later position
# --------------------------------------------------------------------------- #
def same_node(mod: Module, node: nodes.Base) -> str | None:
    """The POINTER an EQUAL node already declared in this module, or ``None``.

    **§4's content dedup, keyed on NODE EQUALITY.**  §14 step 5 deleted
    ``emit.content_key`` -- ``json.dumps([the node's own mapping, node.applied])`` -- and
    ``schema/nodes.py`` says what replaces it: ``pointer`` and ``position`` are excluded
    from the kinds' equality, so two nodes are equal exactly when they state the same
    thing about an instance.  Everything else a node STATES is compared, including
    ``annotations`` (a node differing only in a ``$comment`` states a different thing to
    a reader) and ``applied`` (a node whose enclosing type word decides differently --
    which is the bit the old key appended by hand, and 1,390 of the bundle's nodes
    declare ``properties`` with no ``type``, 556 of them with that word applied and 834
    without, so both sides are populated).

    ``compiler.Module.collapsed`` is where the equality's CUT at a ``$ref`` and the
    reason the memo is a SEQUENCE are both written down: a node carries mappings and is
    not hashable, and a hash would be a second spelling of what identical means.

    **Measured over the memo's own population**, which is the nodes
    ``compiler.lower_node`` is called on: 7,250 nodes in 677 documents over the whole
    portable set, 283 groups of more than one node by the deleted key and 283 by this
    equality, and 0 documents whose partition differs.  So the replacement is a
    relocation and not a decision.

    **Asked in the WALK and not in the pass, and the reason is the pruning.**  A second
    occurrence's CHILDREN are never lowered -- they would declare a second class each,
    and their drops and their reports would be recorded twice -- so the equality has to
    be consulted before the node is decided.  What the PASS owns is everything §4
    actually decides about a group: which pointer declares, what each pointer is called,
    and that a later pointer binds the class by identity (:func:`adopt`, :func:`assign`).
    :data:`SCOPE` is the scope of all of it.

    **What SEEDS the memo is a symbol declared AT THE NODE'S OWN POINTER**, which is
    exactly D2's class and enumeration rows and :func:`name_the_node`'s alias
    (``compiler.lower_node`` is the one writer of ``mod.collapsed``).  An annotation
    declares nothing, so an identical annotation is simply decided again -- to the same
    annotation, since the inputs are the same -- and a ``$ref`` whose symbol the module
    IMPORTED is not seeded either, because the import is already in ``mod.imports`` and
    §2's rule is an import of a symbol the TARGET declares.  A node that declares a
    symbol at its pointer and then decides to a CONTAINER over it is therefore not
    seeded; a nested union is the shape that would be, and it is covered anyway because
    its BRANCHES collapse through the same entry and two identical branch lists then
    decide to one annotation.  No such pair survives the run, and clause 1 of the check
    reddens by name if one appears.
    """
    return next((at for other, at in mod.collapsed if other == node), None)


def adopt(mod: Module, pointer: str, declared: str) -> ir.TypeRef | Refusal:
    """§4's content dedup at the SECOND and later positions of one node: the class the
    first position declared, under the name THIS position's own rule derives.

    **One class, as many names as the node has positions.**  §4's dedup is a statement
    about CLASSES -- one node yields one class -- and §4's nested rule derives a name per
    POSITION, so a node at three positions has one class and three derived names.  An
    alias is a NAME BOUND TO THAT CLASS and not a second class, which is why the two
    rules do not collide and why nothing here is hand-assigned: the name is whatever
    :func:`segments` folds the adopting position's own hops to and :func:`spell`
    spells.

    What this refuses to do is type a field by a SIBLING POSITION's name.  Binding
    ``PreviewRenderHtml.dimensions`` to ``PreviewRenderUrlDimensions`` would read as the
    html branch carrying the url branch's type, and it would make the public symbol a
    function of which key the walk happened to reach first.  The upstream v9 SDK is the
    worked case of the opposite failure -- 1,092 of its 4,360 classes are numbered
    variants of content it declares over and over, ``WholesaleFeedEvent1`` through
    ``WholesaleFeedEvent9`` among them -- and the answer to that is one class aliased,
    not one class renamed.

    **The DECLARATION is an ``ir.AliasDecl``, the same statement §4's root-scalar row
    emits**, so there is one alias spelling in the emitter and not a second one here.  It
    carries no constraints, no description and no format on purpose: the node is EQUAL to
    the one the class already lowered, so every fact about it is already stated on the
    class, and a ``Field(description=...)`` wrapper here would both restate it and make
    the alias an ``Annotated`` object rather than the class itself -- which is the one
    thing a consumer must be able to rely on.  ``X = TheClass`` is the class by IDENTITY:
    ``X is TheClass``, ``isinstance`` works, and a type checker follows it.

    **Two positions take the class symbol directly rather than an alias, and
    :func:`assign` is what decides that** -- it has to be, because neither test can be
    made before the names are derived.  A position whose hops derive NO name (a mapping's
    key type) has no name to bind, and a position whose derived name IS the declared
    one would be ``X = X``.  The walk declares the alias at the adopting pointer either
    way and the pass drops the degenerate ones, mapping the adopting pointer straight
    onto the declaring class's symbol.

    **The adopting pointer IS declared**, under its own name, so a cross-document
    ``$ref`` naming the second position resolves to it -- ``emit.exported`` lists the
    symbol at every bundle-named pointer, so the import side and the export side still
    read one fact.  Before the alias this arm refused DEFERRED instead; 0 of the
    collapsed pointers are among the bundle's 216 named nodes, so the change closes a
    ceiling nothing reaches rather than moving a refusal.
    """
    collision = mod.declare(
        pointer, ir.AliasDecl(pointer, ir.TypeRef(declared, local=True))
    )
    if collision is not None:
        return collision
    return ir.TypeRef(pointer, local=True)


# --------------------------------------------------------------------------- #
# §2's rule at a node some OTHER document names: the alias that holds the symbol
# --------------------------------------------------------------------------- #
def alias_for(pointer: str, node: nodes.Base, decided: Decided) -> ir.AliasDecl:
    """One node's own decision, as the alias that names it.

    Shared by the THREE rows that declare an alias -- a root
    (``compiler.declare_alias``), a node another document names
    (:func:`name_the_node`) and a container's described contents
    (``lower.containers._contents``) -- because "the annotation for this node, under this
    name" is the same question in all three and a second copy of it is how two of them
    come to carry a node's ``format`` or its ``description`` differently.  They differ
    only in what wraps the statement, which is each row's own and stays there.

    The bound and the ``format`` ride on the alias's own TYPE, exactly as a field's do
    (§2, and :attr:`codegen.ir.TypeRef.facts`): one carrier, so an alias and a property
    cannot come to spell one ``minLength`` two ways.

    **Here and not in ``compiler.py`` because an alias is a NAME BOUND TO A STATEMENT**,
    which §7 makes this module's: ":func:`adopt` and this build the same declaration, and
    the reading that tells them apart is what each binds -- ``adopt`` binds a class an
    EQUAL node already declared and carries no facts of its own, because every fact is
    already on that class; this binds the node's OWN decision, so every fact it states
    has to ride along or be dropped."
    """
    return ir.AliasDecl(
        # The POINTER in the name slot until :func:`assign` binds it (§7).
        pointer,
        replace(decided.type, facts=decided.constraints, format=decided.format),
        description=node.description,
    )


def name_the_node(
    mod: Module, pointer: str, node: nodes.Base, decided: Decided
) -> ir.TypeRef | Refusal:
    """Give a node a SYMBOL in its own module, because a ``$ref`` elsewhere names it.

    A fragment reference resolves to an import of a symbol the target module declares,
    never to a copy (§2's rule).  A node D2 makes a CLASS already has one -- the walk
    declared it and ``decided.type.local`` says so -- and this is the other case: an
    array, a scalar or a mapping is an annotation with no name, so the target module has
    nothing to export and the reference has nothing to import.

    **The node's type BECOMES the symbol**, which is why the TYPE comes back rather than
    only the declaration being made: the alias carries the constraints and the referring
    property then references it, so the node's facts have ONE spelling in the module.
    Declaring the alias and leaving the parent's field to restate the same ``minLength``
    inline would be the copy P2 removes, two spellings deep in one file.

    Not ``compiler.declare_alias``, which is a ROOT's whole module -- the reference, the
    alias and the bound ``strict_validate``, all at module scope, where there is room for
    exactly one of each.  A named node is INSIDE a document that already has a root, so
    it takes the alias statement alone.  It therefore carries no ``__adcp_schema__`` of
    its own, and that is the existing arrangement rather than a gap: every nested node
    that is not a class is ungraded on its own today, and this one is graded twice over
    anyway -- inside its own document's pair, which names the whole document, and inside
    its referrer's, whose resolved schema inlines this very node at the pointer the
    reference carries.

    **No name is computed here and none is passed in** (§7, and §14 step 7): the
    declaration is made at the node's own POINTER, and :func:`assign` binds it to the
    name §4's nested rule derives for that position -- which is the hop the node's parent
    recorded when it lowered this child.

    **It returns the TYPE and not a ``Decided``, which is :func:`adopt`'s signature**, and
    the two callers are the reason as much as the symmetry is: ``lower.containers``
    answers ``ir.TypeRef | Refusal`` itself and now returns this call's result straight,
    and the walk's own entry (``compiler.lower_node``) is the one place that wraps.  It
    is also what keeps this module's arrow to ``compiler.py`` inside ``if
    TYPE_CHECKING`` -- ``compiler`` imports this module at module level, so a runtime
    name from it here would close the cycle the audit reports.
    """
    collision = mod.declare(pointer, alias_for(pointer, node, decided))
    if collision is not None:
        return collision
    return ir.TypeRef(pointer, local=True)


# --------------------------------------------------------------------------- #
# the pass
# --------------------------------------------------------------------------- #
def segments(
    pointer: str, hops: Mapping[str, Hop], seen: frozenset[str] = frozenset()
) -> tuple[str, ...] | Refusal:
    """§4's name rules for the node at ``pointer``, as the SEGMENTS of its path with the
    root first -- so the LAST segment is the name §4 derives for it and each earlier one
    is an ancestor a collision can lengthen by (:func:`spell`).

    A name is a function of the node's PATH through the document and of nothing else --
    not of its content, not of which other nodes exist, not of the order the walk
    happened to reach it in.  That is what makes it recomputable after the walk, and it
    is also §9's rule: no census over the run enters here.

    **A chain and not a name, and that is the whole of §4's "the module path already
    carries the document".**  This fold used to CONCATENATE every hop to the root, which
    needs no collision rule because it cannot collide -- and that is why 808 of 2,118
    emitted classes were longer than 30 characters and one was
    ``GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext``.  The
    segments are the same readings, kept apart, so :func:`spell` can spend exactly as
    many of them as the module's own names require.

    Three positions are a segment rather than a name of their own, and :func:`_suffixed`
    is where: an element, a mapping value and a pinned branch are each spelled onto the
    segment their container is spelled with.  A ``definitions`` entry is one segment too,
    because §4 names it ``<Root><Key>`` -- the root is part of the name the section
    states, exactly as the property is part of ``<Property>Item``.  A branch TITLE names
    itself, so it starts a chain and its ancestors are no part of it.

    **An INDEX is a fact of the node's own position and so it is a fact of its path**, and
    that is why §4's fourth branch rung does not cost this function its first paragraph: a
    branch's index is where it sits under its own combinator, not a reading of what its
    siblings state, so inserting a branch after it renames nothing.  The index arrives as
    a field on the hop (:class:`Branch`) because §6 forbids recovering a position from the
    pointer string that happens to end in it.

    ``seen`` is the pointers already on this fold, so a hop table that named a pointer
    through itself answers once rather than recurring.  The parser gives a child a
    pointer strictly below its parent's, so the population is 0; it is written because
    a fold with no base case is a crash and §9 says a crash is not an outcome.
    """
    hop = hops.get(pointer)
    if hop is None or pointer in seen:
        return ()
    if isinstance(hop, Unnamed):
        return ()
    if isinstance(hop, Root):
        return (class_name(hop.title),)
    if isinstance(hop, Entry):
        root = segments("", hops, seen | {pointer})
        if isinstance(root, Refusal):
            return root
        return ("".join(root) + class_name(hop.key),)
    parent = segments(hop.parent, hops, seen | {pointer})
    if isinstance(parent, Refusal):
        return parent
    if isinstance(hop, Property):
        return (*parent, class_name(hop.key))
    if isinstance(hop, Item):
        return _suffixed(parent, "Item")
    if isinstance(hop, Value):
        return _suffixed(parent, "Value")
    derived = branch_identity(hop, parent)
    # A branch whose four rungs all answer nothing is a NESTED union's branch and nothing
    # else -- §4's fourth rung always answers for a branch that is a class, because the
    # union records its index -- and a member type takes the union's own derived name.
    # **This arm used to mint a VERDICT here**, and it was minting one where §4 states a
    # fallback; the raise site is gone with it, which is one of the hand-written
    # ``Kind`` arguments ``docs/plan/architecture.md`` §3 counts.
    return parent if derived is None else derived


def ladder(
    pointer: str, hops: Mapping[str, Any], seen: frozenset[str] = frozenset()
) -> tuple[tuple[str, ...], ...] | Refusal:
    """Every chain this position could be named by, best first: §4's rungs.

    One rung for every position but a BRANCH, which is the whole of §4's asymmetry here --
    a property, an element, a mapping value, a definitions entry and a ROOT each derive
    their name from one fact, and only a branch has a section-ordered ladder of facts to
    fall down (:func:`branch_rungs`).  So this is :func:`segments` with the branch arm
    widened, and :func:`segments` is its first rung.

    The PARENT chain a rung is suffixed onto is the parent's own FIRST rung, which is
    :func:`segments`' answer and the chain every other reading of the parent uses.  A
    parent that itself falls to a later rung therefore keeps its children's SHORT names
    where they were -- and a short name is what a child is declared under unless it
    collides, so the parent's fall reaches a child only through the lengthening axis.
    Measured over the portable set: of the branch positions that fall to a later rung, 0
    have a named descendant that collides, so the two axes do not interact in this bundle
    and the simpler reading is the measured one.
    """
    hop = hops.get(pointer)
    if not isinstance(hop, Branch) or pointer in seen:
        chain = segments(pointer, hops, seen)
        return chain if isinstance(chain, Refusal) else (chain,)
    parent = segments(hop.parent, hops, seen | {pointer})
    if isinstance(parent, Refusal):
        return parent
    return branch_rungs(hop, parent) or (parent,)


#: §4's collision rule, in the section's own words.  QUOTED by the checks that grade it
#: (``tests/test_names_collision.py``), so the sentence the code states and the sentence
#: a check reports against are one string.
COLLISION = (
    "every position derives its short name; where N positions of one module derive the "
    "same name, ALL N lengthen -- each prepends its own nearest ancestor segment -- and "
    "the step repeats until every name in the module is unique; a position whose short "
    "name collides with nothing keeps it (section 4)"
)


def spell(
    chains: Mapping[str, tuple[str, ...]], occupied: frozenset[str] = frozenset()
) -> dict[str, str] | Refusal:
    """§4's collision rule over the names of ONE module: pointer -> the name it is
    declared under, or the refusal of a module two of whose positions cannot be told
    apart.

    :data:`COLLISION` is the rule.  Every position starts at the name §4 derives (its
    last segment); the positions sharing a name ALL lengthen by their own nearest
    ancestor segment; the step repeats until no name is shared.

    **ALL N lengthen, and that is the whole of why this is order-independent.**
    Lengthening only the later collider would make a public symbol a function of which
    position the walk reached first, which §9 forbids and which :func:`adopt` already
    refuses for the same reason.  Lengthening all of them makes each name a function of
    the SET of colliding positions, and that set is a function of the one document --
    which is why this takes a mapping and not a module, and why nothing here can consult
    the run.

    ``occupied`` is the names the module's own IMPORTS hold: what the walk reported
    (``Module.imports``) and what the renderer brings in (``render.CARRIERS``, via
    :func:`assign`).  A module's namespace is its declarations AND what it imports -- a
    class shadowing an imported symbol retypes every field annotated with it, and
    ``class Field(StrEnum)`` beside ``from pydantic import Field`` makes
    ``Annotated[X, Field(description=…)]`` call the class -- so an imported name is a
    name taken, and a position deriving it lengthens.  Measured over the portable set
    with §4's nested rule in force: 25 positions of 2,226 derive an occupied name -- 3
    a symbol their own document's ``$ref`` imports, 5 one the renderer brings
    (``Field`` four times and ``Presence`` once), and 17 a name in the vocabulary the
    renderer could bring and this module does not.

    It is not a census over the run.  A module imports a symbol because ITS OWN ``$ref``
    names the target, so the set is a function of the one document and its closure, which
    a one-document emission writes as well; §9's rule is about the documents BEYOND that
    closure.  An import cannot lengthen, so only the positions move.

    **An occupied name a position cannot lengthen past is kept and does not refuse**, and
    the reason is that it is exactly the name this emitter has always given that position.
    A ROOT and a titled branch are chains of ONE -- §4 names them after the document and
    after the branch's own title -- so neither has an ancestor to prepend, and refusing
    them would refuse 99 documents of this bundle on a name no document says anything
    about -- measured by making it refuse: ``core/error.json``'s root is ``Error`` and
    the runtime exports an ``Error``, and 98 more follow it or chain behind one.
    Lengthening is an improvement where it is available and the status quo where it is
    not.

    The REFUSAL is the one this pass always had, and it needs two positions: both spelled
    with their whole paths, neither with an ancestor left to prepend, and spelled alike.
    That is exactly the population the fold refused before the rule was written -- the
    full path was the name then -- so the rule moves no document into the refused set.
    """
    spelled, shared = _lengthened(chains, occupied)
    if not shared:
        return spelled
    # Nothing colliding can lengthen and §4's rung axis is not this function's -- see
    # :func:`spell_the_rungs`, which is what the run calls.  The pointer named is the one
    # that COLLIDED, the later of the two in declaration order, which is the pointer
    # ``Module.declare``'s symmetric check names as well.
    #
    # **MEASURED UNREACHABLE over the 1,054 portable documents: 0 modules reach it**
    # (``adcp-client-python-10l.78``), which is §4's own sentence -- "no document of
    # bundle 3.2 refuses for a derivable name again: rung 4 always answers, because a
    # branch always has an index".  It is kept because the positions that are NOT branches
    # have one rung each and two of them could in principle spell alike with nothing to
    # lengthen by, and §9 says a crash is not an outcome.
    #
    # **The kind is HAND-WRITTEN and this row did not derive it, deliberately.**  §9's
    # test makes it a VERDICT and not a deferral -- two positions of one document spelling
    # alike at every rung and every length is a fact about that document's own titles and
    # keys, and no unwritten row would clear it -- but ``compiler.kind_for("title", …)``
    # answers DEFERRED at every position, because ``title``'s cell is a lowering effect.
    # So the kind cannot be read off a cell here, and minting a different one to make the
    # count fall would be the ninth hand-minted verdict wearing a derivation's clothes.
    # Filed as a numbered request instead; the arm is unreachable, so no report moves
    # either way.
    at = next(p for p in chains if p in {q for ps in shared.values() for q in ps[1:]})
    return Refusal(
        "title",
        at,
        f"two nodes in this document derive the class name {spelled[at]!r}",
        kind=Kind.VERDICT,
    )


def _lengthened(
    chains: Mapping[str, tuple[str, ...]], occupied: frozenset[str]
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """§4's collision rule run to a fixed point: the names, and the groups still sharing one.

    ONE reading with two readers, which is why it is split out: :func:`spell` turns a
    surviving group into the refusal, and :func:`spell_the_rungs` turns it into the set of
    positions that fall to their next rung.  Asked twice, the second ask would be a second
    reading of "which positions cannot be told apart", and the refusal and the fall would
    be free to disagree about the set.
    """
    depth = dict.fromkeys(chains, 1)
    while True:
        spelled = {p: spelling(chains[p], depth[p]) for p in chains}
        groups: dict[str, list[str]] = {}
        for pointer, name in spelled.items():
            groups.setdefault(name, []).append(pointer)
        colliding = {
            name: ps for name, ps in groups.items() if len(ps) > 1 or name in occupied
        }
        lengthened = False
        for group in colliding.values():
            for pointer in group:
                if depth[pointer] < len(chains[pointer]):
                    depth[pointer] += 1
                    lengthened = True
        if lengthened:
            continue
        # A position alone on a name an import holds KEEPS it (see the docstring above);
        # only a name two positions share is unresolved.
        return spelled, {name: ps for name, ps in colliding.items() if len(ps) > 1}


#: §4's rung rule, in the section's own words.  QUOTED by the checks that grade it, so the
#: sentence the code states and the sentence a check reports against are one string.
RUNG_FALL = (
    "where a rung derives one name for two branches it has not identified either, so "
    "both fall to the next rung; and a branch colliding with its own document ROOT loses "
    "the name -- the root keeps it, because D5 fixes a document's one exported symbol, "
    "and the branch falls the same way any colliding rung does (section 4)"
)


def spell_the_rungs(
    ladders: Mapping[str, tuple[tuple[str, ...], ...]],
    occupied: frozenset[str] = frozenset(),
) -> dict[str, str] | Refusal:
    """§4's two naming axes together: LENGTHEN first, and FALL where lengthening is spent.

    :data:`COLLISION` is the first axis and :data:`RUNG_FALL` the second.  A position
    starts at its first rung; :func:`_lengthened` spends ancestor segments until no name
    is shared; and a group that still shares a name falls -- every member of it that has a
    rung left takes the next one and starts lengthening again.

    **The ROOT is not special-cased and must not be.**  "The root keeps the name" is not a
    clause here: a root's ladder has exactly ONE rung, because D5 fixes a document's
    exported symbol, so it has nothing to advance and the branch beside it is the only
    side that can move.  §4's sentence is the CONSEQUENCE of the ladder's shape, and
    writing it as a test on the pointer ``""`` would be a second statement of D5 for the
    two to disagree through.

    **Lengthening is tried before falling**, which is §4's order and not a preference: the
    collision rule is stated for every position and the fall is stated for the case where
    "these chains are one segment with nothing to lengthen by".  A branch that can
    lengthen keeps the name its best rung derives, so no identity is given up while a
    cheaper fix is available -- measured, that keeps every one of this bundle's existing
    branch names except the three §4 names.

    It TERMINATES because each fall strictly advances at least one position's rung index
    and :func:`branch_rungs` is finite and duplicate-free; when no member of a sharing
    group has a rung left, the refusal is :func:`spell`'s and says what it always said.
    """
    rung = dict.fromkeys(ladders, 0)
    while True:
        chains = {p: ladders[p][rung[p]] for p in ladders}
        spelled, shared = _lengthened(chains, occupied)
        if not shared:
            return spelled
        fell = False
        for group in shared.values():
            for pointer in group:
                if rung[pointer] + 1 < len(ladders[pointer]):
                    rung[pointer] += 1
                    fell = True
        if not fell:
            return spell(chains, occupied)


def resolved(decided: ir.TypeRef, symbols: Mapping[str, str]) -> ir.TypeRef:
    """One decided type with every LOCAL pointer replaced by the symbol it names.

    Recursive over the type TREE and not over a rendered string: a container carries its
    members in ``of`` with a mapping's key beside them, so ``list[X] | None`` reaches
    ``X`` through two levels and neither can be read off ``path``.

    A local path that is NOT in the table is a symbol another module declares -- a
    cross-document import, which §5's ``$ref`` row makes an import of the TARGET's own
    symbol -- and it is left exactly as the walk decided it.  That is the one slot where
    a pointer and a name share a field, and the table is what tells them apart.
    """
    out = decided
    if decided.local and decided.path in symbols:
        out = replace(out, path=symbols[decided.path])
    if decided.of:
        out = replace(out, of=tuple(resolved(inner, symbols) for inner in decided.of))
    if decided.key is not None:
        out = replace(out, key=resolved(decided.key, symbols))
    return out


def _bound(declaration: ir.Declaration, symbols: Mapping[str, str]) -> ir.Declaration:
    """One declaration with every symbol slot bound: its own name, its bases, its
    branches, and every type it holds."""
    if isinstance(declaration, ir.ClassDecl):
        return replace(
            declaration,
            name=symbols[declaration.name],
            fields=tuple(
                replace(f, type=resolved(f.type, symbols)) for f in declaration.fields
            ),
            extras=(
                None
                if declaration.extras is None
                else resolved(declaration.extras, symbols)
            ),
            bases=tuple(resolved(b, symbols) for b in declaration.bases),
            branches=(
                None
                if declaration.branches is None
                else tuple(resolved(b, symbols) for b in declaration.branches)
            ),
        )
    if isinstance(declaration, ir.EnumDecl):
        return replace(declaration, name=symbols[declaration.name])
    if isinstance(declaration, ir.AliasDecl):
        return replace(
            declaration,
            name=symbols[declaration.name],
            type=resolved(declaration.type, symbols),
        )
    if isinstance(declaration, ir.RootBinding):
        held = declaration.declaration
        return replace(
            declaration,
            symbol=symbols[declaration.symbol],
            # The two kinds a root binding can wrap, narrowed by construction rather than
            # by an ``isinstance`` standing in for a branch: ``RootBinding.declaration``
            # is ``AliasDecl | EnumDecl`` and each has its own rewrite above.
            declaration=(
                replace(
                    held,
                    name=symbols[held.name],
                    type=resolved(held.type, symbols),
                )
                if isinstance(held, ir.AliasDecl)
                else replace(held, name=symbols[held.name])
            ),
        )
    if isinstance(declaration, ir.RootModelDecl):
        # §7's third root shape, whose name and whose wrapped type are bound exactly as a
        # class's are.  An ARM of its own and not the fallthrough, because the fallthrough
        # is what the type checker reads as "everything left", and adding a declaration to
        # ``ir.Declaration`` without one here is how a new kind silently takes another
        # kind's rewrite -- which is what mypy reported the moment ``RootModelDecl`` joined
        # the union.
        return replace(
            declaration,
            name=symbols[declaration.name],
            type=resolved(declaration.type, symbols),
            branches=(
                None
                if declaration.branches is None
                else tuple(resolved(b, symbols) for b in declaration.branches)
            ),
        )
    return replace(
        declaration,
        base=resolved(declaration.base, symbols),
        branches=tuple(resolved(b, symbols) for b in declaration.branches),
    )


def _at(declaration: ir.Declaration) -> str | None:
    """The POINTER a declaration was declared at, which is what its name slot holds
    until this pass runs.  ``None`` for the one declaration that binds no name --
    :class:`codegen.ir.UnionInstall`, whose two statements are about symbols the module
    already declares."""
    if isinstance(
        declaration, ir.ClassDecl | ir.EnumDecl | ir.AliasDecl | ir.RootModelDecl
    ):
        return declaration.name
    if isinstance(declaration, ir.RootBinding):
        return declaration.symbol
    return None


def assign(mod: Module, carriers: frozenset[str] = frozenset()) -> ir.Module | Refusal:
    """The pass: every declaration of one module given the name §4 derives for it.

    ``mod`` is the walk's own module value, ``compiler.Module``, and the import of it is
    under ``TYPE_CHECKING``: the arrow at RUN time runs one way (``compiler`` imports this
    module for §4's rules and nothing here imports it back), so the annotation is the only
    thing that needs the name and the type checker gets it.  What this reads is four
    fields -- the declarations in declaration order, the hops, the adoptions and the
    imports -- and nothing else of the walk.

    ``carriers`` is the other half of the module's NAMESPACE: the names the renderer
    brings in, which the walk does not report (``render.CARRIERS``, handed in by the run
    for :func:`field_name`'s reason -- §8 bans ``pydantic`` under ``lower/`` and the one
    module allowed to read the model layer derives the set).  It is empty by default,
    which spells every position by §4 alone; the run passes it, so a class cannot take
    the name of an import the module's own fields are annotated with.

    THE WHOLE OF THE DEDUP IS HERE, and it is §4's own sentence: declarations whose
    NODES are equal are one class, declared under the first pointer in document order,
    and every later pointer binds its own derived name to it by identity.  The walk
    records the equality -- it must, because a second occurrence's CHILDREN are not
    lowered at all and a declaration it never made has no name to derive -- and this
    pass is what turns the record into names: it decides nothing from the order the
    walk iterated in, because the adopting pointer takes the name ITS OWN position
    derives and the declaring pointer takes its own.

    **The names are decided over the WHOLE module and not one declaration at a time**,
    because §4's collision rule is about a SET: the positions sharing a derived name all
    lengthen, so no position's name can be settled before every position's chain is
    known.  So this fold collects the chains (:func:`segments`) and :func:`spell` decides
    the names from them -- and the refusal two indistinguishable positions earn is
    :func:`spell`'s, where the whole set is in hand, rather than a first-come check that
    would name whichever the walk reached second.

    :data:`SCOPE` is the scope, and the signature holds it: the only inputs are this
    module and §4's rules, so there is no census over the run to decide a name by.
    """
    #: The declarations §4's dedup leaves unwritten: an adopting position that derives NO
    #: name of its own, and one whose derived name IS the declaring class's.  The first
    #: has nothing to bind and the second would be ``X = X``; both take the class symbol
    #: DIRECTLY, which is what mapping the adopting pointer onto the declaring symbol
    #: does for every type that names it.
    degenerate: set[int] = set()
    #: Pointer -> §4's RUNGS for it, best first (:func:`ladder`).  One rung for every
    #: position but a branch; :func:`spell_the_rungs` walks both axes.
    ladders: dict[str, tuple[tuple[str, ...], ...]] = {}
    #: An adopting pointer that binds no name of its own -> the pointer whose class it
    #: takes.  Resolved after :func:`spell`, because the symbol it takes is not decided
    #: until the declaring position's own name is.
    takes: dict[str, str] = {}
    for i, declaration in enumerate(mod.declarations):
        pointer = _at(declaration)
        if pointer is None:
            continue
        rungs = ladder(pointer, mod.hops)
        if isinstance(rungs, Refusal):
            return rungs
        #: The dedup comparison reads the FIRST rung, which is the name this position
        #: derives before any collision is known -- §4's dedup is about two positions
        #: stating the same NODE, and a rung is about telling two names apart, so the
        #: question this asks is settled before the rung axis is walked.
        chain = rungs[0]
        declares = mod.adopted.get(pointer)
        #: Compared over the WHOLE chain, which is this position's own longest spelling:
        #: two positions whose paths spell alike derive one name at every length, so the
        #: degenerate arm is the same arm it was when the fold returned that spelling.
        if declares is not None and "".join(chain) in (
            "",
            "".join(ladders[declares][0] if declares in ladders else ()),
        ):
            takes[pointer] = declares
            degenerate.add(i)
            continue
        ladders[pointer] = rungs
    spelled = spell_the_rungs(ladders, carriers | {symbol for _, symbol in mod.imports})
    if isinstance(spelled, Refusal):
        return spelled
    symbols: dict[str, str] = dict(spelled)
    for pointer, declares in takes.items():
        symbols[pointer] = symbols[declares]
    return ir.Module(
        document=mod.document,
        root=symbols.get("", ""),
        declarations=tuple(
            _bound(d, symbols)
            for i, d in enumerate(mod.declarations)
            if i not in degenerate
        ),
        imports=frozenset(mod.imports),
        symbols=symbols,
        adopted=dict(mod.adopted),
        # §7's ``approximations`` slot, carried through unchanged: this pass assigns
        # SYMBOLS, and a declaration names a POINTER, which naming does not move.  It is a
        # tuple here because the IR is immutable and the walk's accumulator is a list.
        approximations=tuple(mod.approximations),
    )
