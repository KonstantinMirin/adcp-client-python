"""§3a's CATALOGUE, layer L0: every enum vocabulary the bundle states, collected once.

``docs/plan/architecture.md`` §3a declares this layer.  The defect it exists to remove is
that the bundle states one value set at many positions in many spellings, and compiling
each position independently turns one protocol concept into several Python types that are
not interchangeable: measured on the committed tree, **897 enum classes for 715 distinct
member-sets, 128 member-sets emitted more than once across 310 classes**.

**It reads the BUNDLE and never the run's document set**, which is the distinction §3a
draws and the whole of why the clause that forbade this layer no longer applies: §9 forbids
a census over the RUN -- the argument list, which differs between a one-document command
and a whole-population emission -- and the bundle is pinned and is an input to every run
alike, so a reading of it yields the same answer in both.  :func:`collect` takes a bundle
directory and nothing else, which is that rule held by the signature.

WHAT IS COLLECTED, re-measured over the 1,054 portable documents of
``schemas/cache/3.2``
---------------------------------------------------------------------------

A POSITION here is a node that STATES an ``enum``.  A ``$ref`` reaching one is not a
position: §5's ``$ref`` row already compiles it to an import of the target's symbol, so it
declares no second class and is not part of the defect.

===================================================  =====
distinct structural identities                         822
stated at more than one position                       165
  ... positions those cover                            412
stated in more than one DOCUMENT                       142
  ... positions those cover                            358
repeated INSIDE one document                            23
  ... positions those cover                             54
===================================================  =====

**§3a's table reads 807 / 663 / 16,135 for this layer and those are a different
reading.**  They count a ``$ref`` position as a statement of the vocabulary it reaches:
over the DOCUMENT OF RECORD, where §3 inlines every reference, the same walk reads 171,331
positions and 627 repeated identities, and over the raw bundle plus one position per
reference edge it reads 1,999 and 371.  Neither is the population that mints a class, and
the three-way naming split §3a states -- 203 / 457 / 3 -- is a reading of the first of
them.  Over the positions that STATE a vocabulary the split is **15 / 124 / 3**, and the 3
agree exactly, which is the tell: a title is stated at ONE position and every ``$ref``
reaching it carries that one title along, so expanding the references multiplies the
titled and untitled groups and leaves the conflicting ones alone.

IDENTITY IS STRUCTURAL
----------------------

§3a: "Identity here is STRUCTURAL and ignores annotations -- ``description``, ``title``,
``examples``, ``default``, ``$comment``, ``deprecated`` -- because an annotation does not
change what a node admits."  :data:`ANNOTATIONS` is that set, by name and not by pattern,
for the reason §2 of ``docs/plan/rebuild-plan.md`` gives for every admission in this
compiler: silence cannot distinguish "this keyword carries no acceptance meaning" from
"this keyword constrains instances and we have not read it".

**The member list keeps the document's ORDER, and that is a decision with a measured
cost.**  Order does not change what a node admits either, so an order-insensitive identity
is the reading the sentence above would extend to -- and it merges two vocabularies the
bundle means to keep apart.  Measured: ``enums/gop-type.json`` states
``["closed", "open"]`` under the title *GOP Type* -- a Group of Pictures structure -- and
``governance/report-plan-outcome-response.json``'s ``delivery_period_state`` states
``["open", "closed"]`` for a reporting period.  One title between them, so §3a's naming
rule would give the second the first's name and type a governance field ``GOPType``.
That is exactly the coincidental overlap §3a's untitled rule exists to refuse, arriving
through the identity instead of through the name.  Keeping the order refuses it, and the
cost is that a vocabulary restated in a different order is two entries.

THE NAME COMES FROM THE BUNDLE
------------------------------

§4's standing rule, and §3a's three-way split for this layer.  Of the 142 identities
stated in more than one document:

* **15 carry exactly one ``title``** the bundle gives, and that title is the name;
* **124 carry none anywhere**, and are NOT collapsed across documents -- nothing names the
  concept, and without a title there is nothing to tell a coincidental member-set overlap
  from an identity;
* **3 carry conflicting titles**, and are a decision brought to the owner
  (:attr:`Catalogue.conflicting`).  They are not collapsed and no name is picked: §3a says
  so, and picking the commonest would mint a public name no document states for the other
  side of the conflict.

Within ONE document a name is not needed from a title, because §4's content dedup already
decides it -- "two nodes with identical content emit one class ... declared under the name
of the position the walk reaches first, and every later position of the same content binds
its own derived name to that class by identity, ``X = Y``".  All 23 same-document repeats
are untitled, so that rule is the whole answer for them and this module records them
(:attr:`Catalogue.restated`) rather than naming them.

WHERE AN ENTRY LIVES
--------------------

§3a: "An entry lives in the NARROWEST namespace that contains every position referencing
it ... referenced from one document → that document's module; from one domain → that
domain; from more than one domain → the shared namespace", which is ``adcp.types.common``.

:func:`home` computes that, and it reports the case §3a does not settle rather than
choosing in it.  **13 of the 15 nameable entries are stated at a document ROOT**, and for
those two decided rules give two homes: §3a's three-way rule says the shared namespace
(their positions cross domains), and §4's own clause of 2026-10-30 says the opposite --
"a root keeps the name because D5 fixes its symbol, and an imported symbol is fixed more
firmly still: it is ANOTHER document's name, which this module has no standing to move".
Moving such an entry to the shared namespace moves a name ``adcp.types.<domain>`` exports
today.  :attr:`Entry.rooted` carries the fact and :func:`home` answers by §3a's rule, so a
caller can read both and the decision is the owner's.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Collection, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from adcp.types._base import SAME_INSTANCE_FACTS, SAME_INSTANCE_LIST, SAME_INSTANCE_ONE, applied_schema
from codegen import bundle, keywords, vocabularies
from codegen.lower import names

#: :data:`keywords.CARRIED` and :data:`keywords.ANNOTATIONS`, under the names this module
#: has always exported them by.
#:
#: **THEY LIVE IN ``codegen/keywords.py`` NOW, AND THEY WERE ALWAYS A READING OF THE
#: TABLE AND OF NOTHING ELSE.**  ``_carried``'s own argument -- "DERIVED from
#: ``codegen/keywords.py`` and not listed" -- is the argument for its HOME: the derivation
#: reads ``TABLE``, ``cell``, ``descends_at`` and ``admitted_by_prefix``, and this module
#: contributed the question rather than any of the facts.
#:
#: What moved it is a SECOND reader.  ``harness._content_key`` keys §8's fixture memo, and
#: ``adcp-client-python-lzzj.8`` is the measurement for why it has to key on admission:
#: keyed on raw text, an annotation-only edit re-buckets the memo and a different value
#: gets pinned, which is how two pairs flipped verdict on a node BYTE-IDENTICAL between
#: two bundles.  The verifier may not import this module (§9 names its import set and
#: ``codegen.catalogue`` is not in it) and it does import ``codegen.keywords``, so the one
#: declaration had to sit where both readers can reach it.  Restated in the verifier it
#: would have been the hand-written list ``_carried`` exists to have deleted.
CARRIED = keywords.CARRIED
ANNOTATIONS = keywords.ANNOTATIONS

#: The shared namespace, which is ONE place and not one per layer (§3a).  A consumer who
#: does not know which domain a type belongs to has exactly one module to look in.
SHARED = "common"

#: The member types an enumeration HAS a base for, which is ``lower.enum.BASES``' own
#: reading and is why a float or a boolean vocabulary is not collected: ``bool`` is an
#: ``int`` subclass, so a boolean enumeration would render an ``IntEnum`` of 0 and 1 and
#: hand a consumer ``1`` where the document says ``true``.  Measured over the bundle's
#: enum nodes: 1,066 all-``str``, 3 all-``int``, 0 of every other kind.
MEMBER_TYPES = (str, int)


def domain(document: str) -> str:
    """§1's DOMAIN for a document: the first segment of its module path.

    Restated here rather than imported because §11's arrows run ``catalogue <- emit``: the
    run may know this layer and this layer may not know the run.  The DERIVATION is one
    sentence and the two cannot come apart without ``tests/test_catalogue.py``'s own
    equality against ``emit.domain`` reddening, which is the half that does not go stale.

    The hyphen becomes an underscore because the domain is a MODULE name -- ``media-buy``
    is reached at ``adcp.types.media_buy`` -- and a document at the tree's root is a domain
    of its own, which is ``emit.domain``'s own reading of the same path.
    """
    head, _, rest = document.partition("/")
    return (head if rest else document.removesuffix(".json")).replace("-", "_")


@dataclass(frozen=True)
class Stated:
    """One position that STATES a vocabulary: where it is, and what it says there."""

    document: str
    pointer: str
    position: keywords.Position
    #: The members, in the document's own order.
    members: tuple[object, ...]
    #: The node's own ``title``, or ``None``.  §3a's naming rule reads this and nothing
    #: else: a name is the bundle's or there is none.
    title: str | None
    #: The identity :func:`identity` computed, carried so a caller does not recompute it.
    identity: tuple[tuple[str, str], ...]
    #: Does the walk LOWER a type from this position at all?  ``False`` for a position
    #: inside a ``definitions`` entry no ``$ref`` names, which §5 lowers nothing from --
    #: ``bundle.named_nodes`` is what asks and ``bundle.section_entries`` is what a
    #: section entry is.  Such a position states the vocabulary and declares no class, so
    #: it cannot be an entry's HOME: measured over this bundle, one entry's first position
    #: in bundle order is of that kind -- ``a2ui/si-catalog.json``'s
    #: ``definitions/IntegrationAction``, which nothing references -- and homing the entry
    #: there left its three restating positions importing a symbol no module declares and
    #: two of them minting a class instead.
    reached: bool = True

    @property
    def is_a_root(self) -> bool:
        """Is this position the document's own ROOT?

        The pointer is empty exactly there, which is a fact about the walk that produced
        it (:func:`bundle.nodes_at` starts at ``""``) and not a reading of a pointer's
        segments -- §6 forbids recovering a POSITION from a pointer string, and this is
        not one: :attr:`position` carries the position, and a root is the one position no
        keyword descends into, so its pointer is the empty one by construction.
        """
        return self.pointer == ""


@dataclass(frozen=True)
class Entry:
    """One catalogue entry: a vocabulary, the name the bundle gives it, and where it lives.

    An entry is DERIVED and never minted (§3a, §4): :attr:`name` is a title the bundle
    states, and :attr:`home` is computed from the positions that state the vocabulary.
    """

    #: The VALUE LIST this entry is the one type over (:func:`value_list`).
    vocabulary: Vocabulary
    #: The members in document order, read off the NAMING position so that the rendered
    #: order is a function of the document that names the concept.
    members: tuple[object, ...]
    #: ``"string"`` or ``"integer"``, in JSON Schema's words, which is ``ir.EnumDecl``'s
    #: own spelling of the base.
    kind: str
    #: The ``title`` the bundle states, exactly as it states it, or ``None`` where the
    #: bundle titles this vocabulary at no position and
    #: ``codegen/vocabularies.py``'s judgement is what makes it one type.
    title: str | None
    #: Every position that states this vocabulary, in bundle order.
    positions: tuple[Stated, ...]
    #: The name ``codegen/vocabularies.py`` states for this entry, or ``None`` where §4's
    #: own derivation at :attr:`naming` is the name -- which is every titled entry (the
    #: title IS the name §4 derives at a root) and every entry of
    #: ``vocabularies.AGREED`` (every position derived the one name already).
    name: str | None = None
    #: The position this entry is DECLARED at (:attr:`naming`), chosen by :func:`collect`
    #: because the choice needs the bundle's reference graph and an :class:`Entry` carries
    #: only its own positions.
    at: Stated | None = None

    @property
    def documents(self) -> frozenset[str]:
        return frozenset(p.document for p in self.positions)

    @property
    def domains(self) -> frozenset[str]:
        return frozenset(domain(p.document) for p in self.positions)

    @property
    def rooted(self) -> tuple[Stated, ...]:
        """The positions that state this vocabulary at a document ROOT.

        Non-empty for 13 of the 15 entries, and the fact §3a's namespace rule and §4's
        root rule disagree over -- see the module docstring's last paragraph.
        """
        return tuple(p for p in self.positions if p.is_a_root)

    @property
    def naming(self) -> Stated:
        """The position whose ``title`` NAMES this entry, which is where it lives.

        §3a: "A DOCUMENT ROOT IS ALREADY A HOME ... §1's 'every portable document
        contributes a symbol' means ``enums/gop-type.json`` already exports ``GOPType``
        from ``adcp.types.enums``.  There is nothing to relocate.  **So L0's job for
        those 13 is not to move them -- it is to stop every other position minting a
        copy.**"

        The same sentence reaches the two entries stated at no root, because what it
        turns on is §1's export set and not the root rule: a titled position has a
        symbol on the surface whatever position it sits at, so the entry is already at
        home there and the narrowest-namespace rule has nothing to relocate either.
        Measured over this bundle: at all 15 entries the symbol §4 derives at this
        position is ``pascal_case(title)``, so the name the other positions reference is
        the title's and is not minted here.

        **A DOCUMENT ROOT COMES FIRST, which is §3a's correction of 2026-11-02** -- "a
        document root beats a restating title, so a conflict with a rooted vocabulary is
        not one ... where one of the titles belongs to a document of its own, §1 has
        already given that vocabulary an exported symbol and §3a's own rule says a
        document root is already a home.  There is nothing to mint, because the bundle
        named it."  So where this entry's title is stated at a root, that root is the
        home; otherwise the first titled position in bundle order is, and the order is
        the bundle's so the answer is not the collection's iteration order.

        **AN UNTITLED ENTRY'S HOME IS A ROOT TOO WHERE IT HAS ONE, and otherwise its
        first position in bundle order.**  §1 settles both: "every portable document
        contributes a symbol", so a root cannot become a reference to another document's
        class and is the one position of its group that MUST declare -- which makes it the
        home rather than a candidate for one.  Where no position is a root, every position
        derives a symbol on its own module's surface, so the entry is already at home at
        any of them and the choice is the bundle's ORDER: §4's content dedup makes the
        same choice inside a module -- "declared under the name of the position the walk
        reaches first" -- and :func:`states` iterates the bundle in sorted document order,
        so the answer is a function of the bundle and not of this run.
        """
        if self.at is not None:
            return self.at
        return min(self.positions, key=lambda p: ranked(p, self.title))

    @property
    def restating(self) -> tuple[Stated, ...]:
        """Every position that states this vocabulary and is not the one that NAMES it.

        §3a's whole job for layer L0: "to stop every other position minting a copy".
        These are the positions that reference :attr:`naming`'s symbol instead of
        declaring a second class over the same members.

        **A position at a document ROOT is never among them**, and that is §1's rule and
        not a precaution: "every portable document contributes a symbol", so a root that
        declared nothing would leave its own document with no exported name.  It is also
        what keeps §3a's correction honest in one direction only: a root beats a restating
        title, and a root never becomes a restatement of anything.

        **A position in the HOME's OWN document is not among them either**, and that is
        §4's scope rather than a second rule: within one module "two nodes of identical
        content are one class", the dedup key is node equality, and a position this clause
        drops is one §4 either already merged or deliberately kept apart.  Reaching into
        a module to merge two of its own declarations is a change to that rule and not to
        this one.

        **AND A POSITION THE WALK LOWERS NOTHING FROM IS NOT AMONG THEM**
        (:attr:`Stated.reached`), which is :attr:`ShapeEntry.restating`'s sixth exclusion
        read one layer down and in that one's own words: "a position that declares nothing
        is not one minting a second definition".  :func:`declared_at` already refuses such
        a position as a HOME -- a home that declares no class leaves the entry with nothing
        to reference -- and the two halves must agree, because this list is what
        ``emit.needs`` turns into an ORDERING EDGE.

        **The asymmetry was measurable and it was not theoretical.**  One position of this
        bundle is unreached -- ``a2ui/si-catalog.json#/definitions/IntegrationAction``,
        which nothing references -- and it carried a catalogue edge from
        ``a2ui/si-catalog.json`` (standing index 2) to
        ``protocol/get-adcp-capabilities-response.json`` (index 1,012) for
        *Protocol Transport Type*.  No import is emitted at a pointer the walk never
        reaches, so the edge constrained the run's order and corresponded to nothing in any
        module -- an over-approximation that can close a reference cycle no module could
        have, which is ``adcp-client-python-6qi7``'s hazard with no symbol behind it.
        ``tests/test_catalogue_homes.py`` is what found it, by the potential and not by a
        refusal.
        """
        home = (self.naming.document, self.naming.pointer)
        return tuple(
            p
            for p in self.positions
            if (p.document, p.pointer) != home
            and not p.is_a_root
            and p.reached
            and p.document != self.naming.document
        )


@dataclass(frozen=True)
class Shared:
    """One VALUE LIST more than one TYPE is emitted over: §3a's other local state.

    §3a gives a value list three local answers and this is the second and the third of
    them together, because what they share is exactly what this carries:

        * **separate types, one value list** -- the positions are genuinely different
          subjects;
        * **separate types pending a name** -- the positions are plausibly one subject
          and nothing in the bundle names it.

    and §3a's title-conflict rule reaches the same outcome from the other side: "where
    the bundle states two concepts, both names are right and merging types one subject
    with the other's name ... In neither case is there a third name to collapse to."

    So the TYPES are per position and the VALUE LIST is one: "the VALUE LIST is a
    module-level constant in the catalogue layer, written once per distinct member set;
    the NAMED TYPE is constructed from it at each position that needs one."  This names
    the constant's content and where it lives; :class:`Entry` beside it is the one-type
    answer and names a class.

    **It is a VIEW over the collection's partition and not a fifth part of it.**  Every
    entry here is also in :attr:`Catalogue.untitled` or :attr:`Catalogue.conflicting`,
    which is where §3a's own naming split puts it; what this adds is the one fact the
    walk needs about it and neither of those carries -- that one value list serves more
    than one type, so it is written once somewhere both can reach.
    """

    vocabulary: Vocabulary
    #: The members in the bundle's own order, which every position states alike: the
    #: value list IS the key (:func:`value_list`), so there is one order to carry.
    members: tuple[object, ...]
    #: ``"string"`` or ``"integer"``, in JSON Schema's words.
    kind: str
    #: Every position that states this value list, in bundle order.
    positions: tuple[Stated, ...]
    #: The titles the bundle gives it: empty for ``codegen/vocabularies.py``'s judged
    #: rows, and two for a conflict §3a leaves alone.
    titles: tuple[str, ...] = ()

    @property
    def documents(self) -> frozenset[str]:
        return frozenset(p.document for p in self.positions)

    @property
    def domains(self) -> frozenset[str]:
        return frozenset(domain(p.document) for p in self.positions)


@dataclass(frozen=True)
class Conflict:
    """A vocabulary the bundle gives MORE THAN ONE title: §3a's third naming case.

    Not collapsed, not named, and brought to the owner.  The titles and the positions are
    carried because that is what the decision needs: whether the two titles name one
    concept the bundle spells twice or two concepts whose value sets coincide.
    """

    vocabulary: Vocabulary
    titles: tuple[str, ...]
    positions: tuple[Stated, ...]


@dataclass(frozen=True)
class Reference:
    """Where ONE catalogue entry lives, for the position that is about to reference it.

    The NODE and not the module: §11's arrows run ``catalogue <- emit``, and the import
    spelling is a function of the two document PATHS, which D1 derives and
    ``emit.relative_module`` is the one derivation of.  So this layer names the home's
    document and the pointer inside it, the run turns that into a spelling, and the
    spelling is not derived twice.

    :attr:`title` rides along because it is the entry's own evidence: a reader of a
    refusal or of a report wants the name the bundle states, and re-deriving it from the
    pointer would be a second reading of the thing §3a says is read once.
    """

    document: str
    pointer: str
    #: The entry's own name: the ``title`` the bundle states, or the name
    #: ``codegen/vocabularies.py`` judges for a vocabulary the bundle titles nowhere.
    title: str | None


@dataclass(frozen=True)
class Catalogue:
    """Layer L0 over one bundle: the entries, and the two groups that are NOT entries."""

    #: value list -> the entry, for a vocabulary the bundle states in more than one
    #: document and names.
    entries: Mapping[Vocabulary, Entry]
    #: The vocabularies stated in more than one document with NO title anywhere.  Not
    #: entries, by §3a's rule, and carried so a check can range over the population rather
    #: than over a list (``tests/nodeset.py``'s ``claimed``).
    untitled: tuple[tuple[Stated, ...], ...]
    #: §3a's third case, for the owner.
    conflicting: tuple[Conflict, ...]
    #: The vocabularies a SINGLE document states at more than one position.  §4's content
    #: dedup is the whole rule for them; this is the population it has to reach.
    restated: tuple[tuple[Stated, ...], ...]
    #: Every stating position, which is the set every count above partitions.
    positions: tuple[Stated, ...] = field(default=())
    #: value list -> §3a's SHARED value list (:class:`Shared`), for the value lists more
    #: than one type is emitted over.  A VIEW over the partition and not a part of it.
    shared: Mapping[Vocabulary, Shared] = field(default_factory=dict)
    #: value list -> the one position that states it, for a value list the bundle states
    #: at EXACTLY ONE position.
    #:
    #: Not a group and not a naming question -- one position states it, so §3a's
    #: three-way split has nothing to decide and :func:`collect`'s partition passes it
    #: over.  **It is carried because a position that STATES a value list is not the only
    #: position that DECLARES a class over one**: §2's intersection rule hands a base's
    #: node back to a composing document, which lowers it again, and a second class over
    #: one value list is exactly what reading 4 forbids.  Measured over this bundle: of
    #: the 643 value lists stated at one position, **1** carries two classes in the
    #: emitted tree -- ``core/postal-country-system.json``'s ``["DE", "CH", "AT"]``,
    #: re-lowered by ``core/postal-area.json`` -- and ``codegen/vocabularies.py``'s own
    #: docstring records the row that was written for it and refused: "the bundle states
    #: it at ONE position ... which is a restatement §4 and §5 own and this layer never
    #: sees."  It sees it here, as a HOME and not as a judgement: one position, so there
    #: is nothing to judge and nothing to name.
    alone: Mapping[Vocabulary, Stated] = field(default_factory=dict)

    def entry_at(self, document: str, pointer: str) -> Entry | None:
        """The entry the position at ``(document, pointer)`` states, or ``None``.

        The lookup the walk makes: §3a's "the catalogue is an INPUT to the walk, never a
        pass over its output -- a node's type is a REFERENCE to an entry, or a fresh type
        where the node is genuinely unique".  ``None`` is the second of those.
        """
        for entry in self.entries.values():
            for position in entry.positions:
                if position.document == document and position.pointer == pointer:
                    return entry
        return None

    def restating(self) -> dict[str, dict[str, Reference]]:
        """document -> pointer -> the entry's home, for every position that RESTATES one.

        **This is the whole of what the walk consults** (§3a: "the catalogue is an INPUT
        to the walk, never a pass over its output -- a node's type is a REFERENCE to a
        catalogue entry, or a fresh type where the node is genuinely unique").  A
        position in this table is the first of those and every other enum position is
        the second, so the walk asks one question of a mapping and derives nothing.

        Keyed by DOCUMENT first, because the run hands one document at a time to the
        walk and §11's arrows forbid the walk knowing the run: what crosses the seam is
        this document's own rows and not a reading of the bundle.

        A pure function of the BUNDLE, which is §9's rule held by the signature of
        :func:`collect`: the same answer for a one-document command and for the whole
        population, so a module's text does not depend on who else was named.
        """
        out: dict[str, dict[str, Reference]] = {}
        for entry in self.entries.values():
            home = Reference(
                document=entry.naming.document,
                pointer=entry.naming.pointer,
                title=entry.title,
            )
            for position in entry.restating:
                out.setdefault(position.document, {})[position.pointer] = home
        return out

    def pinned(self, entry: Entry, value: object) -> bool:
        """Is ``value`` one of ``entry``'s members?

        §3a's Pass B, ``const`` against ``enum``: "where a root's ``enum`` and a branch's
        ``const`` are one vocabulary, both reference the one entry, so the pin is
        ``Literal[Entry.MEMBER]`` because no other member exists to name".  The question a
        pin asks of an entry is this one, and ``docs/plan/rebuild-plan.md`` §5's ``const``
        row stays the general case for a pin whose field has no collected entry.
        """
        return value in entry.members


def identity(node: Mapping[str, object]) -> tuple[tuple[str, str], ...]:
    """The STRUCTURAL identity of one node: every key that changes what it admits.

    Sorted by key, so the identity is a function of the node's content and not of the
    order a mapping was built in (P7); the VALUE is serialised with sorted keys for the
    same reason, and the ``enum`` list keeps the document's order for the reason the module
    docstring measures.
    """
    return tuple(
        sorted(
            (key, json.dumps(value, sort_keys=True))
            for key, value in node.items()
            if key not in ANNOTATIONS and not key.startswith("x-")
        )
    )


def vocabulary(node: Mapping[str, object]) -> tuple[object, ...] | None:
    """The members ``node`` enumerates, or ``None`` where it enumerates none this layer
    collects.

    ``None`` for a node with no ``enum``, for an ``enum`` that is not a list, for an empty
    one -- which admits no instance, so it enumerates nothing -- for members of mixed
    type, and for a member type with no enumeration base.  Those are
    ``lower.enum.decide``'s own three refusals, asked here as a reading rather than as a
    verdict: a node this layer does not collect is a node the walk compiles on its own,
    which is §3a's "a fresh type where the node is genuinely unique" and not a refusal of
    anything.
    """
    members = node.get("enum")
    if not isinstance(members, list) or not members:
        return None
    kinds = {type(m) for m in members}
    if len(kinds) != 1:
        return None
    if next(iter(kinds)) not in MEMBER_TYPES:
        return None
    return tuple(members)


#: The JSON Schema type word for each collected member type, which is
#: ``lower.enum.BASES``' own mapping read from the other side.  Keyed by the exact type,
#: because ``bool`` is a subclass of ``int`` and an ``isinstance`` test would admit it.
KIND = {str: "string", int: "integer"}

#: **A VALUE LIST: the key reading 4 is worded on.**  "A set of values stated at more than
#: one position is written once and referenced, never restated ... no value list appears
#: twice in the emitted tree."  The kind rides along because ``['1', '2']`` and ``[1, 2]``
#: render two different bases and are two value lists.
Vocabulary = tuple[str, tuple[object, ...]]


def value_list(stated: Stated) -> Vocabulary:
    """The VALUE LIST ``stated`` states, which is what an entry is keyed on.

    **COARSER than :func:`identity`, and the difference is measured rather than argued.**
    Reading 4 is worded on the value list -- "no value list appears twice in the emitted
    tree" -- and §3a's structural identity splits one value list wherever two positions
    state it with any other admitting keyword spelled differently.  Over this bundle's 169
    value lists stated at more than one position, **159 carry one structural identity and
    10 carry two; in all 10 the whole of the difference is a redundant ``type: "string"``
    beside an all-``str`` ``enum``**, which admits not one value more.  So the coarser key
    merges no two positions that admit different sets, and
    ``tests/test_catalogue.py``'s own check of that is what keeps the sentence true: a
    group whose positions differ in a keyword that NARROWS would redden there rather than
    collapse here.

    It is what §3a's "stronger rule" needs to reach at all.  *Reporting Status View* is
    titled at ``protocol/get-reporting-status-request.json``'s ``view`` and restated
    untitled beside a ``type`` at two error branches of the response; under the structural
    key the titled identity and the untitled one are two entries, the second carries no
    title, and §3a's "one type, named for the title, referenced by every position" cannot
    be applied to it.
    """
    return (KIND[type(stated.members[0])], stated.members)


def stating(bundle_dir: Path, documents: Collection[str] | None = None) -> list[str]:
    """The documents every layer of this file collects positions FROM, in sorted order.

    Two readings in one place, because all three state generators need both and a third
    spelling of either is a third thing to keep in agreement:

    * ``documents`` defaults to :func:`bundle.portable`, which is the whole bundle.  **A
      caller that passes the RUN's document set would be the census §9 forbids**, which is
      why the default is the bundle and the parameter is documented as a test's.
    * **A NON-HOME MEMBER OF A REPEATED DOCUMENT IS NOT A STATING POSITION OF ANY LAYER**
      (:func:`bundle.repeated`, whose docstring carries the measurement and the home rule).
      The document declares nothing -- its module binds the home's root symbol -- so a
      position inside it is one no class is emitted at, and §3a's own sentence about a CONJ
      home is the precedent: "a layer that collects a position no class is emitted at has
      collected a home that cannot declare."  Measured on bundle 3.2: without this screen 6
      L0 vocabularies and 1 L2 structure home inside such a document and their restating
      positions import a symbol no module wrote.
    """
    repeated = bundle.repeated(bundle_dir)
    return sorted(
        d
        for d in (documents if documents is not None else bundle.portable(bundle_dir))
        if d not in repeated
    )


def states(bundle_dir: Path, documents: Collection[str] | None = None) -> Iterator[Stated]:
    """Every position of the bundle that STATES a vocabulary this layer collects.

    ``documents`` is for a test that wants a named subset and defaults to
    :func:`bundle.portable`, which is the whole bundle.  **A caller that passes the RUN's
    document set here would be the census §9 forbids**, which is why the default is the
    bundle and the parameter is documented as a test's: the two readings differ and only
    one of them is a function of the pinned input.
    """
    names = bundle.named_nodes(bundle_dir)
    for document in stating(bundle_dir, documents):
        doc = bundle.read(bundle_dir, document)
        # The ``definitions`` entries of this document that NO ``$ref`` names, which §5
        # lowers no type from: a position inside one declares nothing, so it cannot be an
        # entry's home (:attr:`Stated.reached`).
        unreferenced = tuple(
            sorted(bundle.section_entries(doc) - names.get(document, frozenset()))
        )
        for pointer, node, position in bundle.nodes_at(doc):
            members = vocabulary(node)
            if members is None:
                continue
            title = node.get("title")
            yield Stated(
                document=document,
                pointer=pointer,
                position=position,
                members=members,
                title=title if isinstance(title, str) and title.strip() else None,
                identity=identity(node),
                reached=not any(pointer.startswith(entry) for entry in unreferenced),
            )


def titles(positions: Collection[Stated]) -> frozenset[str]:
    """The distinct titles the bundle gives this vocabulary, which decides §3a's case."""
    return frozenset(p.title for p in positions if p.title is not None)


def ranked(position: Stated, title: str | None) -> tuple[object, ...]:
    """:attr:`Entry.naming`'s order over the positions of one entry, best first.

    A root carrying the entry's own title, then any position carrying it, then any root,
    then the bundle's own order.  §1 is what puts the roots first: "every portable document
    contributes a symbol", so a root cannot become a reference to another document's class
    and is the one position of its group that MUST declare.
    """
    return (
        not position.reached,
        not (position.is_a_root and position.title == title),
        position.title != title,
        not position.is_a_root,
        position.document,
        position.pointer,
    )


def declared_at(positions: Collection[Stated], standing: Mapping[str, int]) -> Stated:
    """The position a vocabulary's ONE class is declared at (:attr:`Entry.naming`).

    **A ROOT, then the STANDING ORDER, and the bundle's own order to break a tie** --
    which is :func:`shape_ranked`'s order at L2, read here one layer down, and the two
    layers now state ONE home rule rather than two.  §1 is what puts the roots first
    ("every portable document contributes a symbol", so a root cannot become a reference
    to another module's class); §3a is what puts the standing order next --
    ``emit.standing_order`` is a topological index of the bundle's REFERENCE graph, the
    home is the group's earliest document in it, so the edge this layer adds runs
    backwards along an order of all the reference edges.

    **A ``title`` DOES NOT ENTER THIS ORDER, and the measurement that forced the
    separation at L2 forces it here.**  :func:`shape_ranked`: "a rule that let the first
    decide the second put the home wherever the bundle -- or an override -- happened to
    write the word", measured as *emitted 896 / refused 163*.  The hazard is not L2's: at
    either layer a titled position can sit in a document that references the restating
    one, and then the catalogue edge closes a cycle.  So the title answers *what is this
    entry CALLED* (:attr:`Entry.title`, ``emit.judged``) and this answers *which document
    may declare it*, and nothing here branches on the first.

    **WHAT THIS REPLACED, and why it was a census rather than a rule.**  The home was
    "the stating document the other stating documents ALREADY REACH" -- ranked by how many
    of the group's own documents reach the position, over a transitive ``$ref`` closure
    this module computed itself.  Its own docstring said plainly that the order was
    *"measured cycle-free and not cycle-free by construction"*, and
    ``adcp-client-python-6qi7`` is what a census costs: ``emit.needs`` unions the reference
    graph with the catalogue's homes, so a home inside a document that references the
    restating one closes a cycle ``emit.order`` must read as a VERDICT.  A reach COUNT is
    not a linear extension of anything -- two entries over one pair of documents answer in
    opposite directions, because their groups differ and so do their counts -- so the
    property could only ever be checked after the fact.

    **AND IT IS NOW ACYCLIC BY CONSTRUCTION, over BOTH catalogue layers at once.**  With
    ``idx`` the standing order's index, take ``φ(D) = idx(D)``.  A ``$ref`` edge
    ``D -> D'`` decreases ``φ`` because ``idx`` is a topological index of exactly those
    edges.  A catalogue edge ``D -> home`` decreases it because the home is the group's
    EARLIEST stating document: ``idx(home) <= idx(D)`` for every stating ``D``, and
    strictly for the ``D`` that are not the home itself -- which are the only ones that
    carry an edge (:attr:`Entry.restating` drops the home's own document).  Every edge of
    the unioned graph strictly decreases ``φ``, so a cycle is **unrepresentable** rather
    than absent.  That is §3a's ask held by a derivation, and
    ``tests/test_catalogue_homes.py`` is the gate on it.

    **THE ONE EDGE THE DERIVATION DOES NOT COVER IS A ROOT'S, and §1 is why it stands.**
    A root sorts ahead of the standing order, so a rooted home need not be the group's
    earliest document and ``idx(home) > idx(D)`` is possible there.  §1 forbids the
    alternative -- a root that declared nothing would leave its own document with no
    exported name -- so the clause is not a weakening this function chose.  What makes it
    safe is strictly weaker than a construction and is MEASURED per entry rather than
    counted: a rooted home must not REACH a restating document through the reference
    graph.  The gate states that half separately and names the pair when it fires.

    ``standing`` is ``emit.standing_order``'s and is handed IN, which is §3a's own rule --
    "a derived reading of the bundle is an argument, not something a callee recomputes" --
    and is what :func:`collect` takes it positionally for.

    **AND THERE IS NO ``title`` PARAMETER, which is the separation held by the signature
    rather than by a sentence.**  :func:`shape_ranked` keeps one and says it is unused;
    here the argument is simply gone, so a future reader cannot reintroduce the branch
    without changing every caller -- and the title is read where the NAME is decided
    (``emit.judged``, :attr:`Entry.title`) and nowhere else.
    """
    return min(positions, key=lambda p: _home_order(p, standing))


def _home_order(position: Stated, standing: Mapping[str, int]) -> tuple[object, ...]:
    """:func:`declared_at`'s order over the positions of one entry, best first.

    ``reached`` first, for :attr:`Stated.reached`'s own reason: a home the walk lowers
    nothing from declares no class for anything to reference.  Then §1's roots, then §3a's
    standing order, then the bundle's own order so the answer is a function of the bundle
    and not of an iteration.
    """
    return (
        not position.reached,
        not position.is_a_root,
        standing.get(position.document, len(standing)),
        position.document,
        position.pointer,
    )


def the_name(positions: Collection[Stated], stated: Collection[str]) -> str | None:
    """The one title that NAMES this value list, or ``None`` where §3a's conflict rule
    holds.

    One title and it is the name.  Two or more, and **§3a's correction of 2026-11-02
    decides between them by whether either belongs to a document of its own**:

        "§3a said of two titles over one member set that *'in neither case is there a
        third name to collapse to, and minting one is what §4 refuses'*.  That is right
        about minting and wrong about the population it ranges over: where one of the
        titles belongs to a **document of its own**, §1 has already given that vocabulary
        an exported symbol and §3a's own rule says a document root is already a home.
        There is nothing to mint, because the bundle named it.  The other title is then a
        restating position that happens to carry a title of its own -- a case §3a did not
        cover -- and a local title does not create a second type over an identical member
        set, because no value distinguishes them.  **So the conflict rule applies only
        where NEITHER title is a document root.**"

    So exactly one rooted title is the name, and that is this bundle's
    *Delivery Recipient Cloud* against *Reporting Cloud*: ``aws, azure, gcp`` stated at
    ``enums/delivery-recipient-cloud.json``'s own root and restated under a title at
    ``core/reporting-dataset-share.json``.  **Minting a third name for it -- the ``Cloud``
    that reads best and that no document states -- is what §4 refuses**, and the root
    makes the mint unnecessary rather than merely wrong.

    ``None`` where two or more titles are each a root, because then §1 obliges both
    documents to export a symbol and neither can become a reference to the other: that is
    *Catalog Action* / *Creative Action* and *Canonical Media Buy Action Mode* /
    *Media Buy Action Mode*, two titled ``enums/`` documents apiece.  §3a's answer for
    them is unchanged -- "a conflict is reported and left alone, and the only judgement is
    whether to file it upstream".
    """
    if len(stated) == 1:
        return next(iter(stated))
    rooted = {p.title for p in positions if p.is_a_root and p.title is not None}
    return next(iter(rooted)) if len(rooted) == 1 else None


def namespace(documents: Collection[str]) -> str:
    """The NARROWEST namespace containing every one of ``documents`` (§3a).

    One document → that document, as a bundle-relative path, which is the module the walk
    writes today.  One domain → that domain's name.  More than one → :data:`SHARED`.

    One derivation, read by both of §3a's local answers: :func:`home` asks it of an
    :class:`Entry`'s positions and ``emit.vocabularies_modules`` asks it of a
    :class:`Shared`'s, and §3a states the rule once -- "an entry lives in the NARROWEST
    namespace that contains every position referencing it".
    """
    held = frozenset(documents)
    if len(held) == 1:
        return next(iter(held))
    domains = frozenset(domain(d) for d in held)
    return next(iter(domains)) if len(domains) == 1 else SHARED


def home(entry: Entry) -> str:
    """The NARROWEST namespace containing every position that states ``entry`` (§3a).

    **It answers by §3a's rule even where :attr:`Entry.rooted` is non-empty**, and the
    module docstring states why that is reported rather than resolved here: for 13 of the
    15 entries §3a's rule and §4's root rule give different homes, and choosing between
    them moves -- or declines to move -- a name the domain surface exports today.
    """
    return namespace(entry.documents)


#: The keywords whose subschemas sit at a DEF position: a SECTION, not an admission.
#:
#: **OUT of the key** (:class:`Admitted`), which is the one consequence of §3a's
#: admission test that §3a does not spell.  An entry no ``$ref`` names admits nothing, and
#: an entry one DOES name is already in the key at the referring site because references
#: resolve -- so keeping the section would make two nodes that admit exactly the same set
#: differ on a side-car, which is the error the sentence exists to prevent.  Derived from
#: the descent column's own child position, never listed: ``definitions`` and ``$defs``
#: are the keywords whose subschemas occupy a DEF position, which is what a definitions
#: section IS.
SECTIONS = frozenset(k for k, p in bundle.DESCENDS.items() if p is keywords.Position.DEF)

#: Subschema lists an instance reads as a SET: ``allOf``, ``anyOf``, ``oneOf``.  No payload
#: can see which branch the document wrote first, so the key sorts them -- the same
#: sentence that puts property ORDER out of the key (§3a: "order is the axis a census must
#: be explicitly blind to or it reports a difference no payload can see").
UNORDERED = bundle.HELD_IN_A_LIST
#: The keywords holding a bag of named subschemas that IS an admission: ``properties`` and
#: ``patternProperties``.  :data:`SECTIONS` is what the difference is.
BY_NAME = bundle.HELD_BY_NAME - SECTIONS

#: What a key records where a reference closes a cycle: the HOP COUNT back to the node the
#: cycle returns to, which is a function of the structure and not of where the walk
#: started.  A bundle whose references form a cycle has no finite inlining, and the key has
#: to say "the same node, N hops up" rather than recurse.
CYCLE = "<cycle>"


class Admitted:
    """**A LAYER'S KEY: exactly what changes the set of admitted instances** (§3a, 2026-11-03).

    ``docs/plan/architecture.md`` §3a settles the recursion and the order -- an object's
    identity is the identity of its property types, collected L0 upward -- and the section
    of 2026-11-03 settles what the key CONTAINS:

        "The test is admission-equivalence, and it is the one L0 already used.  Two nodes
        are one entry exactly when no instance distinguishes them.  So the key holds the
        property NAMES (a different name admits different instances), ``required``,
        ``additionalProperties``, and every narrowing keyword -- each changes what is
        admitted.  It does not hold a ``title``, a ``description``, an ``examples``, or the
        ORDER of the properties."

    Four readings of that sentence are applied here and each is the admission test asked
    of one more keyword:

    * **what is IN** is every key :data:`ANNOTATIONS` does not hold and the ``x-`` prefix
      does not admit, which is L0's own screen (:func:`identity`) -- derived from
      ``codegen/keywords.py``'s TABLE and never listed, so a keyword joining the table
      joins the key by its own cell rather than by a second declaration here;
    * **a reference RESOLVES to what it names before keying.**  §3a: "an unresolved key
      UNDERCOUNTS, measurably so at the array layer."  Measured over this bundle's array
      positions the unresolved key reads 918 identities and the resolved one 891, and the
      difference is positions where one document spells a type inline that another reaches
      through a ``$ref``;
    * **ORDER is out** wherever no payload can see it: a property bag is sorted by name, a
      ``required`` list is sorted, a combinator's branch list is sorted.  ``enum``'s order
      stays IN, and that is not an inconsistency -- :func:`value_list`'s own docstring
      measures the cost of dropping it (``["closed", "open"]`` and ``["open", "closed"]``
      are two vocabularies the bundle means to keep apart) and the rendered member ORDER
      is a fact a consumer meets;
    * **a definitions SECTION is out** (:data:`SECTIONS`).

    **A key read off the RENDERED ANNOTATION is not this key** and this class is why the
    distinction has a name: a rendered annotation carries a ``description``, so a census
    over it moves when the renderer does, and a figure that moves when the renderer changes
    cannot be a layer's identity.  Every figure in §3a's L2/L3 row and in the 42 row's own
    tables was taken over the tree; this is taken over the bundle.

    **It reads the BUNDLE and never the run's document set**, which is :func:`collect`'s
    own rule and §9's: the answer is the same for a one-document command and for a
    whole-population emission.
    """

    def __init__(self, bundle_dir: Path) -> None:
        self.dir = bundle_dir
        self.documents = frozenset(bundle.portable(bundle_dir))
        self._read: dict[str, dict] = {}
        self._keys: dict[tuple[str, str], str] = {}
        #: ``(the reference's target, the resolution stack) -> the target's key.``  A MEMO
        #: over a pure function of the bundle and not a second reading of it: the target is
        #: ``(document, pointer)``, the stack is what the cycle arm reads, and
        #: :meth:`reached` derives the node from the first alone -- so the pair fixes every
        #: argument :meth:`of` would be called with and the cached answer is the computed
        #: one.
        #:
        #: It exists because the same few targets are resolved thousands of times: every
        #: composed position of this bundle conjoins one of a handful of referenced
        #: documents, and ``core/macro-declaration.json`` alone is re-keyed once per
        #: position that names it.  Measured on ``schemas/cache/3.2``: the L2A collection
        #: falls from 13.7 s to 4.1 s, L2 from 6.7 s to 2.5 s and L2C from 1.7 s to 1.0 s,
        #: and every key of every entry of all four layers is byte-identical either way
        #: (``tests/test_catalogue.py::test_resolving_a_reference_is_memoised_and_the_keys_
        #: are_the_same``).
        self._targets: dict[tuple[tuple[str, str], tuple[tuple[str, str], ...]], object] = {}
        #: The document set a collection ranged over -> L2A's collected positions over it,
        #: which is L2's own screen (:func:`shape_states`' ``applied``).  **PUBLIC, unlike
        #: the three memos above**, because :func:`collect_shapes` is what fills it: it is
        #: part of what this object carries FOR the layers that share it rather than state
        #: of its own keying.
        #:
        #: **IT IS HELD HERE SO THE SCREEN IS NOT A PARAMETER ANY CALLER CAN PASS WRONGLY.**
        #: §3a asks that a derived reading be an argument rather than something a callee
        #: recomputes, and the point of that rule is that one run reads one collection; a
        #: screen a caller could supply differently is the same defect the rule forbids,
        #: arriving through the argument instead of around it.  So :func:`collect_shapes`
        #: derives it and this object -- which is already what a run shares between its
        #: layers -- holds it, and the emitter's two passes collect L2A once between them.
        self.screens: dict[object, frozenset[tuple[str, str]]] = {}

    def document(self, name: str) -> dict:
        if name not in self._read:
            self._read[name] = bundle.read(self.dir, name)
        return self._read[name]

    def target(self, document: str, uri: object) -> tuple[str, str] | None:
        """``(document, pointer)`` a ``$ref`` names, or ``None`` where nothing does.

        A LOCAL reference (``#/definitions/x``) names a node of the REFERRER, which is
        ``bundle.split_ref``'s empty document half; an absolute one is matched against the
        bundle's own file set by ``bundle.document_for``.  ``None`` for a reference this
        bundle does not hold, and the key then carries the URI unresolved -- which is
        honest about what is known and keeps two unresolvable references to one URI equal.
        """
        if not isinstance(uri, str):
            return None
        head, pointer = bundle.split_ref(uri)
        if head == "":
            return (document, pointer)
        named = bundle.document_for(head, self.documents)
        return None if named is None else (named, pointer)

    def reached(
        self, document: str, node: object, stack: tuple[tuple[str, str], ...] = ()
    ) -> tuple[str, object, tuple[tuple[str, str], ...]] | None:
        """Where a ``$ref`` node RESOLVES to, or ``None`` where it resolves nowhere.

        ``(document, node, stack)`` of the node the reference names, for the two readers
        that must treat a reference as the thing it names: :meth:`of` and
        :meth:`stating`.  ``None`` for a reference this bundle does not hold, for a
        pointer naming no node, and for a CYCLE -- each of which is a node whose own
        text is all there is to read.
        """
        if not isinstance(node, dict) or "$ref" not in node:
            return None
        at = self.target(document, node["$ref"])
        if at is None or at in stack:
            return None
        try:
            found = bundle.node_at(self.document(at[0]), at[1])
        except (KeyError, IndexError, TypeError, ValueError):
            # A pointer naming no node: the reference is unresolvable in fact whatever
            # its spelling, and ``bundle.record`` is what refuses the document for it.
            # A census is not a verdict (§3a), so the key carries the URI and the run
            # reports the refusal.
            return None
        return (at[0], found, (*stack, at))

    def of(self, document: str, node: object, stack: tuple[tuple[str, str], ...] = ()) -> object:
        """The decided key of one node, as a hashable structure.

        **A ``$ref`` RESOLVES INTO THIS KEY AND STAYS A MEMBER OF IT**, which is a
        DECLARATION's identity and is not admission-equivalence: a reference is a position
        that reaches another declaration, and this key keeps that apart from a position
        that spells the type itself.  The key an ADMISSION digest needs is
        :class:`Resolved`'s, and ``adcp-client-python-82m.56`` carries the measurement of
        what the difference cost -- the catalogue's own layering question is open there and
        is not settled here, because settling it moves the emitted tree.
        """
        if isinstance(node, list):
            return ("[]", tuple(self.of(document, v, stack) for v in node))
        if not isinstance(node, dict):
            return json.dumps(node, sort_keys=True)
        out: list[tuple[str, object]] = []
        for word in sorted(node):
            if word in ANNOTATIONS or word.startswith("x-") or word in SECTIONS:
                continue
            held = node[word]
            if word == "$ref":
                at = self.target(document, held)
                resolved = self.reached(document, node, stack)
                if at is not None and at in stack:
                    out.append((word, (CYCLE, len(stack) - stack.index(at))))
                elif resolved is None:
                    out.append((word, ("unresolved", json.dumps(held))))
                elif at is None:
                    # Unreachable beside ``resolved is None`` -- :meth:`reached` answers
                    # ``None`` for every reference :meth:`target` answers ``None`` for --
                    # and spelled so the memo's key is a pair of two known halves.
                    out.append((word, ("unresolved", json.dumps(held))))
                elif (memo := (at, stack)) in self._targets:
                    out.append((word, self._targets[memo]))
                else:
                    self._targets[memo] = reached_key = self.of(*resolved)
                    out.append((word, reached_key))
            elif word in BY_NAME and isinstance(held, dict):
                out.append(
                    (word, tuple(sorted((k, self.of(document, v, stack)) for k, v in held.items())))
                )
            elif word in UNORDERED and isinstance(held, list):
                out.append((word, tuple(sorted(repr(self.of(document, e, stack)) for e in held))))
            elif word in bundle.DESCENDS:
                out.append((word, self.of(document, held, stack)))
            elif word == "required" and isinstance(held, list):
                out.append((word, tuple(sorted(map(str, held)))))
            else:
                out.append((word, json.dumps(held, sort_keys=True)))
        return tuple(out)

    def key(self, document: str, node: object) -> str:
        """:meth:`of` as one string, which is what an entry is keyed on."""
        return repr(self.of(document, node))

    def stating(
        self,
        document: str,
        node: object,
        pointer: str = "",
        stack: tuple[tuple[str, str], ...] = (),
    ) -> Iterator[tuple[str, dict]]:
        """``bundle.nodes`` over this document's RESOLVED tree: a ``$ref`` is its target.

        **Why the stated instances are read HERE and not off a closure of document NAMES**
        (``adcp-client-python-82m.56``).  :func:`admitted_identities` used to digest, per
        member of a document's reference closure, that member's NAME beside the instances
        it states -- so extracting a shared scalar into its own document moved the
        referring document's key twice over: the instance left the referrer's own text and
        a new name joined its closure.  Measured over the published bundle against the
        patched one, that was 434 of 1,054 documents on a difference no validator can see.
        Read over the resolution the pointer is the same pointer in both, the instance is
        the same instance, and 0 of 1,054 move.

        A reference is MOUNTED AT THE REFERRING POINTER, which is what makes the two
        spellings one reading: the published bundle states the node inline at ``P`` and the
        patched one states a ``$ref`` at ``P``, and both yield the same node at ``P``.
        ``stack`` stops a cycle, and a node whose reference resolves nowhere is yielded as
        it stands -- :meth:`reached`'s three ``None`` cases.
        """
        if isinstance(node, list):
            for i, held in enumerate(node):
                yield from self.stating(document, held, f"{pointer}/{i}", stack)
            return
        if not isinstance(node, dict):
            return
        resolved = self.reached(document, node, stack)
        if resolved is not None:
            yield from self.stating(resolved[0], resolved[1], pointer, resolved[2])
            return
        yield pointer, node
        for _, suffix, sub, _ in bundle.subschemas(node):
            yield from self.stating(document, sub, f"{pointer}{suffix}", stack)


class Resolved(Admitted):
    """:class:`Admitted` with a resolved ``$ref`` SPLICED IN PLACE OF the node that states it.

    **ADMISSION-EQUIVALENCE, which is what a DRAW's key needs and what a DECLARATION's key
    is not** (``adcp-client-python-82m.56``).  §3a's test -- "two nodes are one entry
    exactly when no instance distinguishes them" -- is satisfied by this class and not by
    :class:`Admitted`, which keeps the ``$ref`` keyword as a member of the key around the
    target's key.  So ``{"$ref": "core/currency-code.json"}`` and the inline
    ``{"type": "string", "pattern": "^[A-Z]{3}$"}`` it names are TWO keys there and ONE
    here, although no instance tells them apart.

    **MEASURED, AND IT IS WHY THIS CLASS EXISTS.**  ``patch.for_build`` hands a run the
    published 3.2 bundle with ``patches/8525`` applied, which extracts five shared scalars
    into their own documents and rewrites the sites that stated them inline to ``$ref``
    them -- ``patch.seen_by_a_validator`` is zero over the whole difference.  Keyed by
    :class:`Admitted`, **429 of 1,054 document identities moved** for it and
    **1,727 of 2,589 graded pairs lost their committed accepts entry**, which is the row
    this class closes.  Keyed here, 0 of 1,054 move;
    ``tests/test_accepts_corpus.py::test_an_acceptance_preserving_patch_moves_no_admitted_identity``
    is that reading as a gate.

    **The ``$ref``'s SIBLINGS go with it, because draft-07 ignores them** -- and the bundle
    states none anyway: 0 of the 4,507 nodes that state a ``$ref`` also state a keyword this
    key would carry, which ``test_a_reference_states_no_sibling_this_key_would_carry``
    reads off the bundle rather than asserting here.  Draft-07 is the bundle's one dialect
    (``test_every_portable_document_states_one_dialect``).

    **:class:`Admitted` IS NOT CHANGED, and that is a scope decision rather than an
    oversight.**  Its key decides which positions share an emitted DECLARATION, so
    splicing there moves the generated tree and the public surface -- measured: it
    re-forms ``tests/duplicates.py``'s cross-document duplicate groups, which
    ``test_every_cross_document_duplicate_group_is_decided`` reddens on.  Whether a
    reference and the inline spelling of what it names should be one declaration is §3a's
    open question and the owner's; it is filed, not answered here.
    """

    def of(self, document: str, node: object, stack: tuple[tuple[str, str], ...] = ()) -> object:
        """:meth:`Admitted.of` with the resolution SPLICED IN, and memoised on the hop.

        **THE MEMO IS :attr:`Admitted._targets` AND IT IS READ HERE BECAUSE IT CANNOT BE
        READ WHERE IT IS WRITTEN FROM** (``adcp-client-python-lqun``, defect 1).
        :meth:`Admitted.of`'s ``$ref`` arm holds the same memo under the same key, and on
        this class it is DEAD CODE: this method resolves before delegating, so the resolved
        reading reaching ``super().of`` no longer states a ``$ref`` and that arm is never
        entered.  Instrumented over a whole :func:`admitted_identities` pass, ``_targets``
        recorded ZERO hits and ZERO misses while its own docstring claimed a measured
        saving -- the saving was real for :class:`Admitted` and nothing on the digest path
        was collecting it.

        **The key is the HOP and never the node**, which is §9's identity rule: ``at`` is
        the ``(document, pointer)`` the reference names, ``stack`` is what the cycle arm
        reads, and :meth:`reached` derives the node from the first alone -- so the pair
        fixes every argument this call would be made with.  Keyed on ``id(node)`` instead
        it reproduces every key byte-identically ONLY while the node is pinned: measured,
        an unpinned temporary's address is reused and keys move silently.

        Measured over the patched bundle's 1,059 documents: the identities pass 7.67 s ->
        5.46 s, 11,521 hits over 42,028 distinct hops where there were none, and the
        sha256 over every document identity UNCHANGED.
        """
        resolved = self.reached(document, node, stack)
        if resolved is None:
            return super().of(document, node, stack)
        if (memo := (resolved[2][-1], stack)) not in self._targets:
            self._targets[memo] = self.of(*resolved)
        return self._targets[memo]


def unreferenced(node: Any) -> Any:
    """``node`` with every ``$ref`` struck, recursively: what it asserts BY ITSELF.

    **The screen in :func:`admitted_identities` runs OFFLINE, and that is not a
    preference.**  ``harness.conforms`` builds a validator on the node it is handed, and
    ``jsonschema`` 4.26 answers an unresolvable remote reference by **fetching it over the
    network** (``validators._warn_for_remote_retrieve`` -> ``urllib.request.urlopen``).
    Measured on one raw bundle document, ``account/get-account-financials-response.json``:
    three ``examples`` members screened against the raw root took **21.7 seconds, 21.67 of
    it in six ``urlopen`` calls**, and over the bundle that is minutes of a key nobody can
    afford to compute.  The records the draw screens against carry no remote reference --
    the inliner has already copied them in -- so the cost appears only where a reader
    screens the RAW bundle, which is here.

    **Struck and not resolved, because the direction is what matters.**  ``$ref`` ignores
    its siblings in draft-07, so a struck reference leaves a node that asserts a SUBSET of
    what the real one asserts: the screened list can therefore only be too LONG, never too
    short, and a key that carries one witness too many costs a redraw where a key that
    missed one would hold a witness the draw no longer produces.  The one position that
    inverts is a reference under ``not`` -- ``{"not": {"$ref": X}}`` becomes
    ``{"not": {}}``, which admits nothing -- and ``not`` is a keyword both halves of
    ``strict_validate`` already refuse, so no graded pair states one.

    The keys a node's own assertions are made of are untouched, which is what keeps the
    measured case exact: 64 of the 115 pairs whose node states ``examples`` admit no member
    of it, because the bundle's ``{"description", "data"}`` wrapper is refused by a root
    that ``required``s its own keys -- and ``required`` is the root's own word, not
    something a reference carried in.
    """
    if isinstance(node, list):
        return [unreferenced(member) for member in node]
    if not isinstance(node, Mapping):
        return node
    return {word: unreferenced(value) for word, value in node.items() if word != "$ref"}


def admitted_identities(
    bundle_dir: Path, *, stated: Callable[[Any], list[Any]]
) -> dict[str, str]:
    """Per portable document, the digest of what it ADMITS and of the instances it STATES.

    **``harness.corpus_key``'s argument, and the answer to the criticism that an
    improvement to the schema costs exactly as much as a regression**
    (``adcp-client-python-lzzj.8``).  ``docs/plan/final-state.md`` reading 1 states the
    rule this function exists to satisfy:

        "**BOTH CHECKS ARE A FUNCTION OF (class, document) AND OF NOTHING ELSE.** Point
        them at another bundle and they answer for that bundle, because there is nothing
        to carry over and nothing to expire. **A stored value, a key over a document's
        bytes, or any artifact that must be re-derived when the bundle moves makes an
        improvement to the schema cost exactly as much as a regression** -- and it makes
        the instrument answer for the bundle it was built against instead of for the
        compiler."

    **WHAT IT REPLACES AND WHAT WAS MEASURED.**  ``bundle.source_identities`` digested a
    document's RAW BYTES and the raw bytes of its reference closure.  So an
    ACCEPTANCE-PRESERVING rewrite of the bundle moved every key: measured over the
    published bundle against a patched one, 22,338 differences, ``patch.seen_by_a_validator``
    **zero** -- nothing lost, nothing changed, every difference a gained
    ``$schema``/``title``/``description`` -- and all 1,054 document identities moved
    anyway, of which 854 differed by a TRAILING NEWLINE alone.  Keyed on what a document
    admits, every one of those is invisible and the held corpus is still the corpus.

    **AND AN ACCEPTANCE-PRESERVING REWRITE MOVED 434 OF THE 1,054 ANYWAY, WHICH IS WHAT
    ``adcp-client-python-82m.56`` MEASURED AND WHAT THIS FUNCTION NOW FIXES.**  The claim
    above was asserted of the published bundle against ``patches/8735`` -- four added
    titles -- and held there.  It is false of the bundle a RUN reads: ``patch.for_build``
    also applies ``patches/8525``, which extracts five shared scalars into their own
    documents and rewrites the sites that stated them inline to ``$ref`` them, with
    ``patch.seen_by_a_validator`` zero over the whole difference.  **Both halves of the
    digest moved for it and neither should have**: :class:`Admitted` kept ``$ref`` as a
    member of the key (429 documents), and the stated half digested a closure of document
    NAMES, so a new member joined and an instance left the referrer's own text (434).  The
    floor was addressed by the old spelling, so **1,727 of 2,589 graded pairs lost their
    committed accepts entry** and fell back to a redraw or to nothing.  The two repairs are
    :class:`Resolved` and :meth:`Admitted.stating`, and after them 21 of 1,054 move -- every
    one of those because ``patches/8525`` genuinely DROPS the ``examples`` its inline sites
    stated, which is a changed witness and a key that is owed its move.

    **The half that must survive, and it does** (``codegen/held.py``): *a compiler edit
    moves no key.*  That is why the key was taken off ``bundle.record`` in the first place
    -- the record is OUR inlining of a document, so keying on it redrew the population
    whenever the inliner moved and no document had.  Nothing here reads the record:
    :class:`Admitted` reads the raw bundle, resolves a ``$ref`` to what it names, and the
    ``stated`` screen is applied to the document's own text.  A compiler edit moves
    nothing; an acceptance-preserving bundle rewrite moves nothing; a changed CONSTRAINT
    moves the documents it changes.

    **:class:`Admitted` IS NOT SUFFICIENT ALONE, AND BOTH GAPS ARE DROPPED ANNOTATIONS
    THAT DECIDE WHICH VALUE IS DRAWN.**  The class drops :data:`ANNOTATIONS`, which is
    right for a layer's identity and wrong for a draw's:

    * **``examples`` IS IN ``ANNOTATIONS`` AND IS A SOURCE OF INSTANCES.**
      ``harness.check_accepts`` answers in the order "THE STORE, THEN THE DOCUMENT'S OWN
      ``examples``, THEN THE DRAW" (the owner's decision, 2026-11-04), and
      ``harness.Fixtures._stated`` reads a REFERENCED document's ``examples`` to pin a
      fixture position.  So a node whose ``examples`` changed would keep an
      admission-only key and change its witness.  The ``stated`` half closes it -- **and
      it carries the SCREENED list and never the raw keyword**, because a member the node
      REFUSES is not a witness: 64 of the 115 pairs whose node states ``examples`` have
      none the node admits (the bundle's ``{"description", "data"}`` wrapper), and
      counting those would move the key for a member that can never be drawn.  The screen
      is ``harness.stated_instances`` itself, handed in, so the key's reading of "which
      instances does this node state" is the DRAW's reading and not a second one -- applied
      to :func:`unreferenced`, which says why the screen runs offline and in which
      direction it errs.
    * **``$schema`` IS IN ``ANNOTATIONS`` AND DECIDES THE DIALECT**, and it is absent from
      this key on purpose.  Carrying the string would be wrong in the direction this
      function exists to fix: the measured patch ADDS ``$schema: draft-07`` to documents
      that stated none, which changes no keyword's meaning and would move every one of
      those keys.  What must not happen is a document in ANOTHER dialect keying the same
      as a draft-07 one while every keyword in it means something else -- and that is a
      question about the whole bundle rather than about one key, so it is asserted over
      the bundle instead of digested per document:
      ``tests/test_accepts_corpus.py::test_every_portable_document_states_one_dialect``
      reads ``harness.validator_for``'s own answer for every portable document and is red
      on the first one that selects a different validator.  A dialect change is then a
      NAMED RED with a decision attached, not a silently re-keyed population.

    **THE CLOSURE IS IN THE DIGEST BY RESOLUTION AND BY NOTHING ELSE**, which is this
    function's current change (``adcp-client-python-82m.56``).  :class:`Admitted` resolves
    every ``$ref`` into the document it names, so a referenced document's CONSTRAINTS are
    inside this document's admitted key already.  The ``stated`` half needs the closure too,
    because ``Fixtures._stated`` draws a fixture from the REFERENCED document's
    ``examples``; it used to get it from ``bundle.edges``, digesting each closure member's
    bundle-relative NAME beside the instances that member states, **and that spelling moved
    a key for a refactor.**  Extracting a shared scalar into its own document moved the
    referring document twice over: the instance left the referrer's own text, and a new name
    joined its closure.  Measured over the published 3.2 bundle against the one
    ``patch.for_build`` hands the run -- which differs from it by exactly that extraction and
    by nothing ``patch.seen_by_a_validator`` can see -- **434 of 1,054 documents moved**, and
    1,727 of 2,589 graded pairs lost their committed accepts entry for it.  Read over
    :meth:`Admitted.stating` -- the document's RESOLVED tree, a reference mounted at the
    referring pointer -- the pointer and the instance are the same in both bundles and
    **0 of 1,054 move**.  So there is no edge list here and no member name in the digest.

    ``stated`` is the caller's, which is the seam §9 draws for every reader the verifier
    needs: ``harness.stated_instances`` is the verifier's function and this module may not
    import the verifier, so the reading is handed in exactly as ``harness.Fixtures`` takes
    its three readers.  Both callers -- ``codegen/__main__.py`` and
    ``tests/test_emit.identity_of`` -- hand in that one function, so there is one screen.
    """
    admitted = Resolved(bundle_dir)
    documents = sorted(admitted.documents)

    def states(document: str) -> str:
        """Every instance ``document`` STATES and ADMITS, by the pointer that states it."""
        held: list[tuple[str, str]] = []
        for pointer, node in admitted.stating(document, admitted.document(document)):
            if "examples" not in node:
                continue
            found = stated(unreferenced(node))
            if found:
                held.append((pointer, json.dumps(found, sort_keys=True, default=repr)))
        return json.dumps(sorted(held))

    out: dict[str, str] = {}
    for document in documents:
        digest = hashlib.sha256()
        digest.update(b"admits\0")
        digest.update(admitted.key(document, admitted.document(document)).encode())
        digest.update(b"\0states\0")
        digest.update(states(document).encode())
        out[document] = digest.hexdigest()
    return out


@dataclass(frozen=True)
class Shaped:
    """One position that STATES an object type (L2) or an array type (L3).

    :class:`Stated` is L0's, and this is the same fact at the layers whose identity is a
    STRUCTURE rather than a value list: where it is, what it admits (:class:`Admitted`),
    and the ``title`` §3a's naming split reads.
    """

    document: str
    pointer: str
    position: keywords.Position
    #: The decided key (:class:`Admitted`).
    key: str
    #: The node's own ``title``, or ``None``.  §3a's naming rule reads this and nothing
    #: else -- "a description states what a thing IS, not what it is CALLED, so it mints no
    #: name".
    title: str | None
    #: **Is this position the walk's path to a node ANOTHER document names?**  A ``$ref``
    #: naming a ``definitions`` entry of this document is what makes that entry lowered at
    #: all -- §5's own sentence is that "17 of the bundle's 76 named nodes are
    #: ``definitions`` entries, which no row descends", and those are REFUSED for exactly
    #: this reason.  So where a restating position's subtree carries the local ``$ref``
    #: that reaches a named entry, collapsing the position would take the walk's only path
    #: to that entry with it: the entry declares no symbol, and the document that names it
    #: by ``$ref`` is refused for a defect in neither of them.
    #:
    #: **Measured, this screens exactly one position** --
    #: ``core/reporting-dataset-share-destination.json#/oneOf/1/properties/recipient``,
    #: whose ``cloud`` property spells ``#/definitions/ReportingCloud`` and whose class
    #: body is the one thing that binds the alias ``ReportingCloud =
    #: DeliveryRecipientCloud``.  ``core/reporting-delivery-offering.json`` names that
    #: pointer directly, and collapsing the position refused it and 25 documents behind it.
    #: The collapse is not WRONG there -- the two nodes admit the same instances, which is
    #: what the key says -- so this is a fact about where a named node gets lowered and not
    #: about the entry, and the position declares its own class exactly as it does today.
    keeps_a_named_node: bool = False
    #: **Is this position a BRANCH of the document's own ROOT union?**  §5 gives a root
    #: union "a base plus one class per branch", so such a branch's class carries the
    #: union's dispatch base and its INSTANCE is one of the union's branches -- which a
    #: plain reference to another module's class cannot be.  §4's union row is the shape
    #: the bundle gets when it writes a ``$ref`` there instead: "a class with two bases:
    #: the target, which supplies the fields, and the union's base, which supplies the
    #: dispatch".
    #:
    #: **So the collapse is WITHHELD here and the position is reported, not fixed**
    #: (:attr:`Shapes.of_a_root_union`).  Inheritance is the available answer and it is a
    #: second type: ``Declarer -> Branch`` does not type-check where ``Branch -> Declarer``
    #: does, so reading 4's "written once" and §3's "every union root dispatches" give
    #: different answers and the one that settles it is the union-dispatch design's, not
    #: this layer's.  That is the same question the 127 raw stating sites carrying more than
    #: one emitted class ask, and this is its L2 face.
    #:
    #: Read off the pointer's DEPTH beside the position this layer already carries, and
    #: that is not §6's forbidden recovery of a position from a pointer string: the
    #: POSITION is :attr:`position`, assigned by the descent column, and what the depth
    #: adds is only whether the node the combinator belongs to is the document's own root.
    #: Measured, it selects exactly two positions of this bundle.
    of_a_root_union: bool = False
    #: The names of this node's own ``properties``, **in the document's own order**, which
    #: is the field set :func:`structure_in_words` spells a name from.  Empty for an L3
    #: position, which states an element type and no field set.
    #:
    #: The ORDER is out of the key (:class:`Admitted`) because no payload can see it, and
    #: it is in here because a NAME is not an admission fact: two positions whose property
    #: bags differ only in order are one entry, and the name is spelled from the HOME's
    #: order, which is derived and reads the way the document reads.
    fields: tuple[str, ...] = ()
    #: **Does this position sit INSIDE an ``if``, ``then``, ``else`` or ``not``?**  §3a's
    #: "a RULE position mints no type, so a node inside an ``if``, ``then``, ``else`` or
    #: ``not`` is not a stating position of any layer" -- read TRANSITIVELY, which is what
    #: the sentence says and what :func:`shape_states`' own screen reads one step deep.
    #:
    #: **This layer neither collapses such a position nor counts it out**, and the split is
    #: ``adcp-client-python-q5g``'s: whether it is a stating position at all is that row's
    #: question, so the census is left exactly where it was and the COLLAPSE declines to
    #: reach a subschema that states what an instance must not be and names no subject.
    #: It is one of :attr:`declares_no_class`' three reasons.
    beneath_a_rule: bool = False
    #: **Is this position's subschema CONSUMED by the node that holds it, so that no class
    #: is declared at its pointer?**  Three reasons, each a standing rule of another
    #: section, and all three have the same consequence here: such a position is **neither
    #: a HOME nor a restating position** -- a home that declares nothing leaves the entry
    #: with no class for anything to reference, and a position that declares nothing is not
    #: one minting a second definition.  It is :attr:`ShapeEntry.undeclared`, reported.
    #:
    #: * **a RULE position**, which is §3a's own "a RULE position mints no type", read
    #:   transitively (:attr:`beneath_a_rule`, ``adcp-client-python-q5g``);
    #: * **a CONJ position**, which is §5's ``allOf`` row -- "inline conjuncts are fields
    #:   and rules of THIS class" -- so a conjunct's properties are declared on the node
    #:   holding the ``allOf`` and the conjunct's own pointer carries no class.  Measured
    #:   over this bundle: 0 of the 21 CONJ stating positions of a collected structure
    #:   carry one, and 8 structures took one as a home and were left homeless by it;
    #: * **a position beneath a ``contains``**, which is that keyword's own cell -- "the
    #:   model states the **predicate**, not a transcription of the subschema" -- so the
    #:   subschema there is a predicate source.  Its descent POSITION is ELEM, the same
    #:   one ``items`` descends to, so the position cannot tell the two apart and the PATH
    #:   is what does; 1 position of this bundle.
    declares_no_class: bool = False
    #: **Is this position a node the bundle's own ``$ref``\\ s NAME?**
    #: ``bundle.named_nodes`` is the reading, and §5's answer is that such a node declares
    #: a symbol on demand because a reference names it -- so a referring document imports
    #: that symbol and a position that stopped declaring takes the referrer with it.
    #:
    #: **So the collapse is WITHHELD here and the position is reported**, which is
    #: :attr:`keeps_a_named_node`'s rule read from the other side: that one is a position
    #: whose SUBTREE carries the local reference reaching a named entry, this one is the
    #: named node itself.  Measured, it selects one position of this bundle --
    #: ``core/committed-metric.json#/oneOf/1/properties/qualifier``, which
    #: ``compliance/comply-test-controller-request.json`` names by absolute ``$ref``, and
    #: collapsing it refused that document on "its target declares no symbol at that
    #: pointer".
    #:
    #: **An ALIAS at the position is the available answer and it is not taken here**: §3a's
    #: "a restated title that a consumer needs is an alias at its position, never a second
    #: class" would have the module bind the imported symbol under the name §4 derives, and
    #: a referrer would import THAT.  What makes it the wrong call for this layer is §1 --
    #: the name a cross-module reference resolves is read off ``ir.Module.symbols`` and the
    #: binding is the thing §1's one-path rule then has to decide about, which is that
    #: section's and not this one's.
    is_a_named_node: bool = False

    @property
    def is_a_root(self) -> bool:
        """Is this position the document's own ROOT?  :attr:`Stated.is_a_root`'s reason."""
        return self.pointer == ""


@dataclass(frozen=True)
class ShapeEntry:
    """One L2 entry: a structure, the name §4 derives for it, and where it is declared.

    **A STRUCTURE THE BUNDLE NEVER TITLES IS NAMED FROM ITSELF** (``rebuild-plan.md``,
    2026-11-04), which retires the reading of §3a's third answer this class was written
    under -- "pending a name" was being read as "pending upstream", and it waits for
    nothing.  So an entry's name is §4's three ordered steps and :attr:`step` says which
    answered; the upstream ask stays filed (``adcontextprotocol/adcp#8735``) and an answer
    there REPLACES a derived name with a stated one.
    """

    key: str
    #: The ``title`` the bundle states, or ``None`` where it titles this structure at no
    #: position -- which is §4's steps 2 and 3 instead, and :attr:`name` is what they
    #: derive.
    title: str | None
    #: Every position that states this structure, in bundle order.
    positions: tuple[Shaped, ...]
    #: The position this entry is DECLARED at.
    at: Shaped
    #: **The name §4's step 2 derives, or ``None`` where step 3 answers.**
    #:
    #: Step 3 is "the declaring position", and at this layer that needs no name minted
    #: here: the home declares in its own document's module, where §4's "the module path
    #: already carries the document" holds, so §4's own spelling AT the home IS the
    #: declaring position.  ``None`` therefore means "§4 names it where it is declared",
    #: which is exactly what the 17 entries the bundle TITLES already carry -- there the
    #: title is the name §4 derives at the naming position, so a row would be a second
    #: statement of one answer (``emit.judged``).
    #:
    #: L1's :attr:`ScalarEntry.name` is never ``None`` for the opposite reason, and the
    #: difference is derived rather than a convention: a constrained scalar is declared in
    #: ``adcp.types.constraints``, a module with no document, so there is no position for
    #: §4 to spell it at and :func:`_home_name` has to write the document into the name.
    name: str | None = None
    #: **WHICH of §4's three steps answered**: 1 the bundle's own title, 2 the structure in
    #: words, 3 the declaring position.  **There is no fourth** --
    #: :attr:`ScalarEntry.step` is the same field one layer down and
    #: ``docs/plan/rebuild-plan.md`` §4 is the one statement of the list.
    step: int = 1

    @property
    def documents(self) -> frozenset[str]:
        return frozenset(p.document for p in self.positions)

    @property
    def spelled(self) -> str:
        """What a REPORT calls this entry: §4's three steps read as one string.

        The bundle's title, else the name derived from the structure, else the declaring
        position -- which is step 3's own answer and is a name a reader follows to the
        position rather than a digest.
        """
        return self.title or self.name or f"{self.at.document}{self.at.pointer or ' /'}"

    @property
    def restating(self) -> tuple[Shaped, ...]:
        """Every position that states this structure and is not the one that DECLARES it.

        §3a's whole job for a catalogue layer: "to stop every other position minting a
        copy".  The first three exclusions are :attr:`Entry.restating`'s, verbatim and for
        the same three reasons -- a document ROOT must declare because §1 says every
        portable document contributes a symbol; a position in the home's own document is
        §4's content dedup's and not this layer's; and the home itself declares.  The
        fourth and the fifth are :attr:`Shaped.keeps_a_named_node` and
        :attr:`Shaped.is_a_named_node`, which are §5's two sides of a named node, and the
        sixth is :attr:`Shaped.declares_no_class`.
        """
        return tuple(
            p
            for p in self._elsewhere
            if not p.keeps_a_named_node
            and not p.of_a_root_union
            and not p.is_a_named_node
            and not p.declares_no_class
        )

    @property
    def withheld(self) -> tuple[Shaped, ...]:
        """The positions this entry does NOT answer at, with the reason each carries.

        **Enumerated and never counted**, which is reading 4's own requirement of a
        separate-type decision.  Three reasons, and each is a standing rule of another
        section rather than a judgement of this one: :attr:`Shaped.of_a_root_union` is §3's
        and §4's union rows, and :attr:`Shaped.keeps_a_named_node` and
        :attr:`Shaped.is_a_named_node` are §5's two sides of a node a ``$ref`` names.

        **A position INSIDE a rule is not one of these**, and the difference is what a
        reader of either list may conclude: a withheld position MUST declare -- the reason
        it carries is why a reference cannot stand there -- so a check asserts that it
        still does, and one that stopped means the reason went stale.  A position inside a
        rule, a conjunct or a predicate declares nothing at all (:attr:`undeclared`).
        """
        return tuple(
            p
            for p in self._elsewhere
            if not p.declares_no_class
            and (p.keeps_a_named_node or p.of_a_root_union or p.is_a_named_node)
        )

    @property
    def undeclared(self) -> tuple[Shaped, ...]:
        """The positions of this entry at which no class is declared at all.

        :attr:`Shaped.declares_no_class` carries the three reasons and the owner of each.
        Reported, so the population is read rather than assumed, and left alone: there is
        no second definition at such a position to remove.
        """
        return tuple(p for p in self._elsewhere if p.declares_no_class)

    @property
    def _elsewhere(self) -> tuple[Shaped, ...]:
        """Every position of this entry that is not one §1 or §4 obliges to declare.

        :attr:`Entry.restating`'s first three exclusions, verbatim and for the same three
        reasons, as the one reading the three lists above each screen further: the home
        declares, a document ROOT declares because §1 says every portable document
        contributes a symbol, and a position in the home's own document is §4's content
        dedup's.

        **AND ``not p.is_a_root`` IS WHY THE 39 BYTE-IDENTICAL DOCUMENT PAIRS SURVIVED
        READING 4 AT ALL FOUR LAYERS** (``adcp-client-python-82m.40``): a root is screened
        out here, so no entry of any layer ever held two of them as restating positions,
        and the duplication was invisible to a gate stated over :attr:`restating`.  The
        clause STANDS -- every portable document does contribute a symbol, and the 39
        contribute theirs by RE-EXPORTING the home's class rather than declaring a second
        one (``emit.lower_document``) -- so what was missing was never a weakening of this
        line but a layer above it whose subject is the DOCUMENT (:func:`bundle.repeated`).
        """
        home = (self.at.document, self.at.pointer)
        return tuple(
            p
            for p in self.positions
            if (p.document, p.pointer) != home
            and not p.is_a_root
            and p.document != self.at.document
        )


@dataclass(frozen=True)
class ShapeConflict:
    """A structure the bundle gives MORE THAN ONE title: §3a's third naming case at L2.

    Not collapsed, not named, and brought to the owner -- :class:`Conflict` is L0's and the
    rule is the same one.  Where exactly one of the titles belongs to a document ROOT that
    root is the home and this is not a conflict, which is §3a's correction of 2026-11-02
    and is :func:`the_name`'s own reading.
    """

    key: str
    titles: tuple[str, ...]
    positions: tuple[Shaped, ...]


@dataclass(frozen=True)
class Shapes:
    """One STRUCTURAL layer over a bundle: L2's object types, or L3's array types.

    The parts are a PARTITION of the structures stated at more than one position, and the
    partition is what a check ranges over: a structure is stated in one document
    (:attr:`restated`) or in several, and in the second case it is COLLECTED
    (:attr:`entries`) -- named by the bundle's own title or, where the bundle titles it
    nowhere, from the structure itself -- or it is one of the three the key does not
    settle: two names neither of which is a document's own (:attr:`conflicting`), nothing
    but document roots (:attr:`duplicated`), or nothing but positions inside a rule
    (:attr:`declaring_nothing`).  :attr:`untitled` is the layer that collects NOTHING, which is
    L3's by derivation.

    **THE UNTITLED STRUCTURES ARE COLLECTED AT L2 AND NOT AT L3, and the reason is §3a's
    own and not a scope.**  "The array layer collects nothing, by derivation rather than by
    measurement: ``list[X]`` is written once in Python by construction, so the only thing
    an array position can write twice is its ELEMENT -- and an element is owned by a layer
    beneath."  So an untitled ARRAY structure has nothing to declare and nothing to name,
    and the check that ranges over it asks whether the layer beneath owns its element.

    **The last of those is EMPTY, and what emptied it is a layer above this one rather
    than a judgement inside it** (``adcp-client-python-82m.40``).  It held ten object
    structures stated at exactly two positions, both of them a document ROOT, both carrying
    the same title -- the bundle ships one document at two paths, under
    ``core/async-response-refs/`` and under the domain's own directory -- and this layer
    reported them because the decided key does not settle which root may become a reference
    to the other.

    **It still does not settle it, and the measurement says why the question was never this
    layer's.**  Asked of the 78 roots of the 39 byte-identical document pairs, the
    admission key answers those ten, **ten more inside groups that mix DIFFERENT protocol
    states** -- five operations' *Submitted* envelopes admit identically and their titles
    conflict, which is :class:`ShapeConflict` doing the right thing -- one inside a
    three-position entry, and **eighteen it does not collect at all**, their root being an
    ``allOf`` with no ``properties`` of its own.  So this layer's key both over-groups and
    under-reaches the population, because the subject is not a structure stated twice: it
    is a **repeated DOCUMENT**, whose identity is the document's own bytes and is strictly
    finer than admission-equivalence.  :func:`bundle.repeated` is that layer, it answers all
    39, and :func:`stating` is what keeps a non-home member out of this one -- so the
    positions never reach a group here and the part is empty by derivation.
    """

    #: key -> the entry, for every structure this layer COLLECTS: stated in more than one
    #: document, and named either by the one title the bundle gives it or -- where the
    #: bundle titles it at no position -- by §4's steps 2 and 3 from the structure itself.
    entries: Mapping[str, ShapeEntry]
    #: The structures stated in more than one document that this layer declines to collect
    #: FOR WANT OF A TITLE.  Empty at L2, where the same structures are :attr:`entries`
    #: named from themselves; at L3 it is every untitled group, by the derivation in the
    #: class docstring; at L2C it is every group the bundle does not title at EVERY stating
    #: position, which is that layer's evidence rule (:func:`shape_states`) and is why the
    #: part is not "no title anywhere" any more.
    untitled: tuple[tuple[Shaped, ...], ...]
    #: §3a's conflict case, for the owner.
    conflicting: tuple[ShapeConflict, ...]
    #: The structures a SINGLE document states at more than one position.  §4's content
    #: dedup is the whole rule for them.
    restated: tuple[tuple[Shaped, ...], ...]
    #: The structures whose every stating position is a document ROOT.  See the class
    #: docstring: §1 and reading 4 give different answers and the key settles neither.
    duplicated: tuple[tuple[Shaped, ...], ...]
    #: The structures NO stating position of which declares a class
    #: (:attr:`Shaped.declares_no_class`).  Reported and left alone: a structure with no
    #: position that declares has nothing to write once and nothing to stop minting.  The
    #: reason per position is the position's own, and for the rule positions among them
    #: whether they are stating positions at all is ``adcp-client-python-q5g``'s question.
    declaring_nothing: tuple[tuple[Shaped, ...], ...]
    #: The positions of an ENTRY this layer withholds the collapse at, as
    #: ``(entry spelled, position)`` -- :attr:`ShapeEntry.withheld`, flattened so a report
    #: and a check range over one list.  **Enumerated, never counted**, which is reading
    #: 4's requirement of every separate-type decision.
    withheld: tuple[tuple[str, Shaped], ...]
    #: The positions of an ENTRY at which no class is declared, flattened the same way
    #: (:attr:`ShapeEntry.undeclared`).  Separate from :attr:`withheld` because a withheld
    #: position must DECLARE -- that is what its reason is about -- and one of these
    #: declares nothing, so there is nothing at it to collapse or to assert.
    undeclared: tuple[tuple[str, Shaped], ...]
    #: Every stating position, which is the set every count above partitions.
    positions: tuple[Shaped, ...]

    def restating(self) -> dict[str, dict[str, Reference]]:
        """document -> pointer -> the entry's home, for every position that RESTATES one.

        **The whole of what the walk consults**, and the same table shape
        :meth:`Catalogue.restating` hands it for L0: a position in it is "a REFERENCE to a
        catalogue entry" and every other object position is "a fresh type where the node is
        genuinely unique".  Keyed by DOCUMENT first, because the run hands one document at
        a time to the walk and §11's arrows forbid the walk knowing the run.
        """
        out: dict[str, dict[str, Reference]] = {}
        for entry in self.entries.values():
            home = Reference(
                document=entry.at.document, pointer=entry.at.pointer, title=entry.spelled
            )
            for position in entry.restating:
                out.setdefault(position.document, {})[position.pointer] = home
        return out


#: The pointer segments at which draft-07 keeps the SAME instance, so a node below one
#: carries what the nodes above it assert about that instance.  ``adcp.types._base``'s own
#: two lists and not a third: :func:`applied_schema` conjoins at exactly these hops and at
#: no other, so a pointer holding none of them applies nothing and this is an exact screen
#: rather than a cheaper approximation of one.
_SAME_INSTANCE_HOPS = frozenset((*SAME_INSTANCE_LIST, *SAME_INSTANCE_ONE))


def applied_conjunction(doc: dict, pointer: str, node: Mapping[str, object]) -> dict | None:
    """The object type the DOCUMENT APPLIES at ``pointer``, written as ONE conjunction.

    ``None`` wherever the question does not arise, and the three reasons are below.

    **THE DEFECT.** ``core/assets/daast-asset.json`` states
    ``macro_declarations.items: {"$ref": "core/macro-declaration.json"}`` at its root and,
    in its ``url`` delivery branch, narrows the SAME property to
    ``{"properties": {"location": {"properties": {"field": {"const": "url"}}}}}``.
    draft-07 holds a root's assertions and its branch's against one instance, so the type
    the document applies at ``#/oneOf/0/properties/macro_declarations/items`` is the
    narrowing CONJOINED with the reference -- which is, statement for statement, what
    ``core/assets/url-asset.json`` spells inline at
    ``#/properties/macro_declarations/items`` and the bundle titles *URL Macro
    Declaration* there.  Read as its own text alone, the branch's node is a different node
    from url-asset's and :class:`Admitted` correctly reports two keys, so the layer whose
    whole job is to stop a second declaration could not see the two were one type and the
    tree declared it twice.  **The node's own text cannot be titled into agreement
    either**: it says nothing about a macro declaration, the subject exists only once the
    root's reference is applied, and a title there would be a claim the node does not
    support.  So the repair is at what a STATING POSITION IS and not in a name.

    **THE RULE IS ``_base.applied_schema``'S AND IS NOT RESTATED HERE**, which is
    ``bundle.constrained_to_object``'s own reason at the same seam: that function is what
    the RUNTIME resolves a class's ``__adcp_schema__`` through, so a second derivation of
    "what does the document apply here" is exactly how the emitter comes to declare a class
    the runtime would grade against a different schema.  Nothing of draft-07 is decided
    here; what is decided is that this layer asks it.

    **THE CONJUNCTION IS THE DOCUMENT'S OWN ``allOf`` AND NOT A MERGE.**  A node's own
    ``properties``/``required``/``additionalProperties`` and its ``allOf`` conjuncts hold
    against the same instance, so folding the first into the second changes no statement --
    and it is what makes the two spellings of one type key alike, which an intersection
    could not do without discarding the ``$ref`` the key is built around (the admission key
    keeps a reference AS a member, ``adcp-client-python-32yh``).  **So this needs no splice
    of that key**: both sides reach ``(('allOf', (<the reference's key>, <the narrowing's
    key>)),)`` and the equality is the key's own.

    The five ``None``\\ s, the first two of which are also what keeps this an exact screen
    rather than a walk of the whole bundle from every pointer -- :func:`applied_schema`
    rebuilds a node from its document's root, so the two cheap readings are asked first and
    neither can change the answer:

    * the pointer crosses no hop at which draft-07 keeps the SAME instance, so nothing
      enclosing this node asserts anything about the instance it describes;
    * the node's own text states none of the facts a conjunction is made of -- and
      :func:`applied_schema` adds no such key, it only adds the ``allOf``, so a node silent
      in all three is silent in the applied reading too;
    * the document applies nothing -- :func:`applied_schema` returns the node UNCHANGED,
      as the same object, so identity is the answer and not a comparison;
    * nothing is COMPOSED at the position, so this is not the composed layer's question and
      the node's own ``properties`` are the whole of what it states (L2's reading, intact);
    * the applied node states NO facts of its own beside the conjunction, so it is already
      spelled as a conjunction and L2C reads it as it stands.
    """
    if not any(part in _SAME_INSTANCE_HOPS for part in pointer.split("/")):
        return None
    if not any(node.get(word) for word in SAME_INSTANCE_FACTS):
        return None
    applied = applied_schema(doc, "#" + pointer)
    if applied is node or not isinstance(applied, dict):
        return None
    conjuncts = applied.get("allOf")
    if not isinstance(conjuncts, list) or not conjuncts:
        return None
    own = {word: applied[word] for word in SAME_INSTANCE_FACTS if applied.get(word)}
    if not own:
        return None
    beside = {
        word: value
        for word, value in applied.items()
        if word != "allOf" and word not in SAME_INSTANCE_FACTS
    }
    return {**beside, "allOf": [*conjuncts, own]}


def shape_states(
    admitted: Admitted,
    layer: str,
    documents: Collection[str] | None = None,
    applied: Collection[tuple[str, str]] = (),
) -> Iterator[Shaped]:
    """Every position of the bundle that STATES an object type (``"L2"``) or an array
    type (``"L3"``).

    **L2 is a node holding a non-empty ``properties``**, which is what an object type IS
    and is the population the 42 row's split was asked of.  **L3 is a node whose ``items``
    is a schema**, which is what an array type is.

    **AND L2C IS THE OBJECT TYPE A NODE STATES THROUGH ITS CONJUNCTS AND NOT THROUGH ITS
    OWN ``properties``** -- a node holding a non-empty ``allOf`` and no ``properties`` of
    its own, which over this bundle is 256 positions, 114 of them in 32 groups that state
    one structure in more than one document.  ``{"allOf": [{"$ref": X}, {<a narrowing>}]}``
    is an object type exactly as much as an inline ``properties`` bag is -- the compiler
    declares a class at it, and reading 4 ranges over every class the tree declares -- but
    L2's predicate reads the node's OWN ``properties`` and a composed object states none,
    so the whole population was invisible to the one layer whose job is to stop a second
    declaration.  **Measured over the tree: 22 of its 40 duplicate declarations sit at such
    a position, in 10 of its 15 duplicate groups** -- which is the larger half of reading
    4's remaining object-layer question, and the half no layer was reading.

    **IT IS A LAYER OF ITS OWN AND NOT A WIDENING OF L2, because the evidence for a shared
    subject is not the same at the two.**  §3a's own argument for the array layer transfers
    verbatim: *"what tells a shared subject from a coincidental overlap is that an object's
    key holds the property NAMES, while an array's key over a scalar element holds no name
    at all -- which is why the object layer can collapse on identity and the array layer
    must not."*  A composed node's key holds the key of its ``$ref``'s TARGET, which every
    member of a group shares by construction, plus a narrowing conjunct that is typically a
    bare ``required`` or a ``not`` and carries no name of anything.  So identity here is
    evidence of a shared BASE, never of a shared subject -- measured, and the measurement
    is the reason this layer collects nothing untitled: collapsing the 32 groups on identity
    alone would make one type of ``core/rights-attestation-evaluation.json``'s ``reference``
    and ``core/rights-constraint.json``'s ``attestation_refs`` items, of
    ``core/format.json``'s ``canonical_parameters`` and ``core/transformer.json``'s
    ``input_formats`` items, and of ``media-buy/request-proposals-response.json``'s
    ``losses`` and ``legacy-purchase-continuation-input.json``'s ``accepted_losses`` --
    pairs whose two positions name two subjects and which the owner's reading of
    ``adcp-client-python-s44.1`` records as correct splits.  **What tells them apart is a
    ``title``, and the bundle states one at no position of any of the 32** -- which is the
    whole of ``adcontextprotocol/adcp#8735``'s ask read at this layer, and
    :func:`collect_shapes` is where the rule is.

    **A RULE POSITION MINTS NO TYPE and is not a stating position.**  §3's RULE position is
    where ``if``, ``then``, ``else`` and ``not`` hold their subschemas, and a conditional's
    subschema compiles to a RULE rather than to a type -- so a node holding ``properties``
    there constrains an instance of the ENCLOSING type and declares none of its own.
    Measured: 806 of the 3,261 nodes of this bundle holding a non-empty ``properties`` sit
    at a RULE, and excluding them reproduces the 42 row's 2,455 L2 positions exactly.

    **A ``definitions`` entry no ``$ref`` names is not one either**, which is §5 ("a
    position inside one declares nothing") and is :attr:`Stated.reached`'s own reading at
    L0.  Sixteen L2 positions and three L3 positions of this bundle are of that kind, and
    they are the whole of the difference between this population and the 42 row's.

    **THE SCREEN IS READ ONE STEP DEEP AND THAT IS ``adcp-client-python-q5g``'s ROW, so
    the census is unmoved and a position BENEATH a rule is MARKED** instead
    (:attr:`Shaped.beneath_a_rule`).  §3a's sentence says "inside", which is transitive,
    and the ``continue`` above reads it as "at": a node at ``#/oneOf/1/not/anyOf/1`` is a
    BRANCH position with the ``not`` one hop above it and is collected.  Changing the
    population is that row's decision; what this layer does with the mark is this one's,
    and the answer is that the COLLAPSE declines to reach such a position.

    **``applied`` IS WHERE THE NODE'S OWN TEXT IS NOT THE TYPE, AND SUCH A POSITION IS NOT
    AN L2 STATING POSITION.**  L2 keys on a node's OWN ``properties``, and at a position
    L2A collects the document applies a type that bag is only part of
    (:func:`applied_conjunction`) -- so what L2 would read there is the narrowing ALONE,
    which is the type declared at that position by nothing.  Left in, the two layers state
    two answers about one pointer and the later one wins silently: measured, the
    ``{"properties": {"location": {...}}}`` narrowing of ``core/macro-declaration.json`` is
    restated at 7 positions in 7 asset documents, L2 collected them as an entry homed at
    ``core/assets/daast-asset.json#/oneOf/0/properties/macro_declarations/items``, L2A then
    bound that very position to *URL Macro Declaration*, and the entry was left with a home
    declaring no class -- which is
    ``tests/test_catalogue.py::test_no_object_structure_emits_more_than_one_definition``'s
    own red.  Screened, the five positions left are every one of them a CONJ and the entry
    falls to :attr:`Shapes.declaring_nothing`, where a structure no position of which
    declares a class belongs.

    It is handed IN for :func:`shape_declared_at`'s reason -- a derived reading of the
    bundle is an argument and not something a callee recomputes -- and the empty default is
    the honest one: a caller censusing L2 alone is reading the layer's own predicate, which
    is what every figure above is taken over.
    """
    screened = frozenset(applied)
    names = bundle.named_nodes(admitted.dir)
    for document in stating(admitted.dir, documents):
        doc = admitted.document(document)
        unreferenced = tuple(
            sorted(bundle.section_entries(doc) - names.get(document, frozenset()))
        )
        #: Every pointer of this document at which a RULE holds its subschema, as the
        #: prefixes a descendant of one is recognised by.  The POSITION is the descent
        #: column's (``bundle.nodes_at``) and not a reading of the pointer string, which
        #: is §6's rule; what the prefix adds is only whether an ancestor is one of them.
        of_a_rule = tuple(
            sorted(p for p, _, at in bundle.nodes_at(doc) if at is keywords.Position.RULE)
        )
        for pointer, node, position in bundle.nodes_at(doc):
            if position is keywords.Position.RULE:
                continue
            if any(pointer.startswith(entry) for entry in unreferenced):
                continue
            #: The node every field below is read off.  It is the position's OWN text at
            #: every layer but L2A, where it is the node the DOCUMENT APPLIES there -- which
            #: is the whole of that layer: one position, two readings, and the one that
            #: decides whether another position declares this type already is the
            #: document's.  Bound here rather than assigned in the arm so the two readings
            #: are visibly two things and the walk's own node is never overwritten.
            stated = node
            if layer == "L2":
                held = node.get("properties")
                if not isinstance(held, dict) or not held:
                    continue
                if (document, pointer) in screened:
                    continue
            elif layer == "L2C":
                held = node.get("properties")
                if isinstance(held, dict) and held:
                    continue
                conjuncts = node.get("allOf")
                if not isinstance(conjuncts, list) or not conjuncts:
                    continue
            elif layer == "L2A":
                composed = applied_conjunction(doc, pointer, node)
                if composed is None:
                    continue
                stated = composed
            elif not isinstance(node.get("items"), dict):
                continue
            title = stated.get("title")
            yield Shaped(
                document=document,
                pointer=pointer,
                position=position,
                key=admitted.key(document, stated),
                title=title if isinstance(title, str) and title.strip() else None,
                keeps_a_named_node=any(
                    bundle.split_ref(spelled) == ("", named)
                    for _, sub in bundle.nodes(stated)
                    if isinstance(spelled := sub.get("$ref"), str)
                    for named in names.get(document, frozenset())
                ),
                of_a_root_union=(
                    position is keywords.Position.BRANCH and pointer.count("/") == 2
                ),
                fields=tuple(stated.get("properties", {}) or ()),
                beneath_a_rule=(beneath := any(
                    pointer.startswith(f"{at}/") for at in of_a_rule
                )),
                declares_no_class=(
                    beneath
                    or position is keywords.Position.CONJ
                    or bool(PREDICATED.intersection(pointer.split("/")))
                ),
                is_a_named_node=pointer in names.get(document, frozenset()),
            )


def shape_ranked(
    position: Shaped, title: str | None, standing: Mapping[str, int] | None = None
) -> tuple[object, ...]:
    """:attr:`ShapeEntry.at`'s order over the positions of one entry, best first.

    **A ROOT, then the STANDING ORDER, and a position inside a rule last.**  §1 is what puts
    the roots first -- "every portable document contributes a symbol", so a root cannot
    become a reference to another module's class and is the one position of its group that
    MUST declare.  §3a is what puts the standing order next: "THE HOME IS THE GROUP'S
    EARLIEST DOCUMENT IN THE DEPENDENCY ORDER THAT ALREADY EXISTS", so the arrow a
    restatement adds runs backwards along a topological order of all the other arrows and
    "a cycle is not avoided by care -- it is unrepresentable".  A position inside a rule
    sorts last because the home is where the structure is DECLARED and a subschema inside a
    rule declares nothing -- a home chosen there would leave the entry homeless.

    **A ``title`` DOES NOT ENTER THIS ORDER, and separating the two questions is what the
    first run of the override table paid for.**  :attr:`ShapeEntry.title` answers *what is
    this entry CALLED* and :attr:`ShapeEntry.at` answers *which document may declare it*,
    and a rule that let the first decide the second put the home wherever the bundle -- or
    an override -- happened to write the word.  Measured the first time
    ``patch.apply`` reached a compile path at all: the override table's one row titles
    ``brand.json#/definitions/data_subject_contestation``, the titled position therefore
    outranked every other, ``core/brand-ref.json`` came to import from ``brand.json``,
    ``brand.json`` already referenced ``core/brand-ref.json``, and the run read **emitted
    891 / refused 163** -- 2 primary on one reference cycle and 161 chained behind them.

    That is exactly the failure §3a forbids a home rule to be capable of: "a rule whose
    soundness has to be MEASURED for cycles is the wrong rule; the right one cannot produce
    them."  The title-first order could, this one cannot, and the entry is named by its title
    either way because the NAME is read off :attr:`ShapeEntry.title` and never off the home.

    ``standing`` is ``emit.standing_order``'s and is handed IN (§3a: "a derived reading of
    the bundle is an argument, not something a callee recomputes").  ``None`` is for a caller
    comparing positions of ONE document, where the term separates nothing; the pointer below
    it is then what decides.  ``title`` is unused and kept in the signature because every
    caller holds one and a caller that stopped passing it would read as though the name had
    stopped mattering.
    """
    return (
        position.declares_no_class,
        not position.is_a_root,
        0 if standing is None else standing.get(position.document, len(standing)),
        position.document,
        position.pointer,
    )


#: The keywords whose subschema the model states a **PREDICATE** over rather than a type,
#: so no class is declared beneath one (:attr:`Shaped.declares_no_class`).
#:
#: ``keywords.py``'s own cell is the reason and the whole of it: "an existential
#: quantifier -- ``items`` constrains every element, ``contains`` says at least one matches
#: -- and the model states the **predicate**, not a transcription of the subschema".
#:
#: **LISTED and not derived from the table, which is the one place in this module that is
#: true, and the reason is in the cell rather than in a column**: ``contains`` descends to
#: ``ELEM``, exactly as ``items`` does, and carries ``Effect.TYPE``, exactly as ``items``
#: does -- so no field of the row tells the two apart and only the cell's sentence does.
#: A second such keyword joins by the same reading of its own cell.
PREDICATED = frozenset({"contains"})

#: **The word an OBJECT structure's own kind contributes to a name in words.**
#: :data:`BASE_WORD` is L1's -- ``Str``, ``Int``, ``Float`` -- and this is the same
#: alphabet one layer up: ``StrMaxLen100`` reads as the constrained string it is, and
#: ``ObjStartEnd`` reads as the object with those two fields.
#:
#: **It is what stops a ONE-FIELD structure claiming a subject.**  ``{status}`` spelled
#: ``Status`` reads as a status, which is the thing the field is a property OF, and the
#: name would then claim exactly what §3a refuses; ``ObjStatus`` claims only what the key
#: proves -- this is the type with this field.  ``_home_name``'s own measurement is why it
#: cannot collide back: "no class of the tree is named for a type word".
OBJECT_WORD = "Obj"

#: **The longest name a derivation IN WORDS may spell, which is §4's own measurement of
#: what a name is and not a budget.**  §4 on the fold this one replaced: it "needs no
#: collision rule because it cannot collide -- and that is why 808 of 2,118 emitted
#: classes were longer than 30 characters and one was
#: ``GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext``".
#:
#: A field set whose words do not fit in a name has **no spelling in words**, exactly as a
#: ``pattern`` is a constraint L1 can spell none of (``collect_scalars``' step 2), and
#: §4's next step answers instead.  It bounds a DERIVATION and is never a check's figure:
#: nothing asserts how many entries fall either side of it.
IN_WORDS = 30


def structure_in_words(fields: Collection[str]) -> str | None:
    """§4's step 2 at L2: the STRUCTURE in words, or ``None`` where it has no spelling.

    ``docs/plan/rebuild-plan.md``: "where the bundle does not name a structure, the name is
    derived FROM THE STRUCTURE, by §4's steps in order", and "an object structure's
    identity is its field set, so the same derivation applies one layer up".  So this is
    ``constraints.symbol`` at the layer above -- the layer's own identity, spelled -- and
    an object type's identity is the names of its fields.

    **It claims only what it can prove.**  "A name derived from the fields claims only what
    it can prove: *this is the type with these fields.*  A name taken from one position's
    property key claims a subject, and that is what §3a refuses."  Every word here is in
    the layer's identity, so it is stated at EVERY position of the entry; a property key is
    stated at one, which is ``^[A-Z]{3}$`` at ``currency`` AND ``airport_code`` one layer
    down.

    **In the HOME's own document order and never sorted.**  Order is out of the KEY
    (:class:`Admitted`) because no payload can see it; a name is not an admission fact, and
    the home is derived, so the home's own order is a function of the bundle and reads the
    way the document reads.  Sorting spells ``ObjEndStart`` for a period the bundle writes
    ``start`` then ``end``.

    ``None`` for an L3 position, which states an element type and carries no field set --
    the array layer collects nothing and has nothing to name (:class:`Shapes`).
    """
    if not fields:
        return None
    spelled = OBJECT_WORD + "".join(names.class_name(field) for field in fields)
    return spelled if len(spelled) <= IN_WORDS else None


def shape_declared_at(
    positions: Collection[Shaped], title: str | None, standing: Mapping[str, int]
) -> Shaped:
    """The position one STRUCTURE's single class is declared at (:attr:`ShapeEntry.at`).

    :func:`declared_at` is L0's and the first half is the same: a TITLE or a ROOT answers
    outright (:func:`shape_ranked`).  **What is left is a structure the bundle names at no
    position and states at no root**, and there §3a asks that the home be "the stating
    position the other stating positions reach through a reference", so that the arrow a
    restatement adds runs the way the dependency arrows already run.

    **AND THE ORDER IT RANKS BY IS THE STANDING ONE OVER THE WHOLE BUNDLE, NOT A COUNT
    INSIDE THE GROUP -- which is the one place this layer's rule is stronger than L0's,
    and the reason is measured.**  :func:`declared_at` ranks a position by how many of its
    OWN group's documents reach it, and that is a reading inside one entry: two entries
    over one pair of documents answer in opposite directions, because their groups differ
    and so do their counts.  Measured, that is exactly the residue --
    ``ObjUrlMessageExpiresAt`` homed in ``account/sync-accounts-response.json`` while the
    step-3 entry at ``core/account.json#/properties/credit_limit`` is homed in
    ``core/account.json``, neither document ``$ref``\\ s the other, and the two edges close
    a cycle no single entry can see.

    ``standing`` is ``emit.standing_order``'s: document -> its index in the dependency
    order of the graph that ALREADY EXISTS -- every reference the walk lowers, and every
    edge L0's own collection adds.  **The home is the group's earliest document in it**,
    so every edge this layer adds runs BACKWARDS along a topological order of all the
    other edges, and the graph with this layer's edges in it is acyclic by construction
    rather than by measurement.  That is §3a's "the dependency arrows point one way" held
    by a derivation, which is what the section asks for: "a cycle is not avoided by care --
    it is unrepresentable".

    **It is handed IN and not recomputed**, which is §3a's own rule -- "a derived reading
    of the bundle is an argument, not something a callee recomputes" -- and is why
    ``collect_shapes`` takes it positionally: a caller cannot forget it and read a
    different collection than the run does.

    Measured over this bundle at L2, against the three orders that are equally functions
    of it.  **Both columns come from ONE instrument, the emitter's own run**, which is what
    makes them comparable: a cycle is a VERDICT for every document ON it (``emit.order``)
    and every document that REFERENCES one refuses through the chain, so the two are
    different denominators over one reading and neither is the other.

    ========================================================  ========  ========  =======
    the home is                                               emitted   on a      refused
                                                                        cycle     in all
    ========================================================  ========  ========  =======
    the first stating position in bundle order                     838        10       216
    the document the most other stating documents reach (L0's)    1041         2        13
    the stating document of the smallest transitive reach          1028         6        26
    **the group's earliest document in the standing order**     **1054**     **0**    **0**
    ========================================================  ========  ========  =======

    So none of the rejected orders emits a wrong answer -- the first refuses 216 of the
    bundle's 1,054 documents, 10 of them on a cycle and 206 chained behind those.  **A
    reach-SIZE order is a linear extension of the reference graph and is still not
    enough**, and the reason is the whole argument for ranking by the standing order: L0's
    edges are not reference edges and do not run the reference graph's way, so an
    extension of the references alone has L0's arrows pointing against it.
    """
    # **ONE ORDER AND NOT TWO ARMS**, which is :func:`shape_ranked`'s own correction: this
    # function held a TITLED arm that fell through to the document's name and an untitled arm
    # that ranked by the standing order, and a title therefore decided WHERE the entry was
    # declared as well as what it was called.  §3a states one home rule and
    # :func:`shape_ranked` is now it, so there is nothing left here to branch on.
    return min(positions, key=lambda p: shape_ranked(p, title, standing))


def collect_shapes(
    admitted: Admitted,
    layer: str,
    standing: Mapping[str, int],
    documents: Collection[str] | None = None,
) -> Shapes:
    """One STRUCTURAL layer over the bundle: §3a's L2 or L3, under the decided key.

    §3a's three-way split, asked of each group of positions that state one structure, with
    its third case decided rather than deferred (``docs/plan/rebuild-plan.md``, 2026-11-04,
    "A STRUCTURE THE BUNDLE NEVER TITLES IS NAMED FROM ITSELF"):

    * **one named type** where the bundle names the subject -- one title, or several of
      which exactly one belongs to a document ROOT (:func:`the_name`'s rule);
    * **one named type NAMED FROM ITSELF** where the bundle titles the structure nowhere.
      That is §4's steps 2 and 3 in §4's own order: the structure in words
      (:func:`structure_in_words`), else the declaring position, which at this layer is
      §4's own spelling at the home.  The upstream ask is not withdrawn and is not a
      blocker -- an answer there replaces a derived name with a stated one;
    * **separate types over one definition** where the key does not settle it: the names
      conflict (:attr:`Shapes.conflicting`), every position is a root the bundle obliges to
      declare (:attr:`Shapes.duplicated`), or no position of it declares a class and so
      declares no class at all (:attr:`Shapes.declaring_nothing`).

    **WHY NAMING FROM THE STRUCTURE IS SAFE, and it is the whole argument**: two positions
    sharing :class:`Admitted`'s key ADMIT IDENTICALLY, so collapsing them cannot change
    what any class accepts or refuses.  A name is not an acceptance fact, so neither half
    of this moves a verdict.

    **A step-2 candidate TWO entries derive has identified neither, so both fall to step
    3**, which is ``collect_scalars``' own rule at the layer below and §4's first-fit
    semantics for its name candidates.  Two structures derive one step-2 name exactly when
    they share a field set and differ in a keyword the key holds and the name does not --
    ``required`` or ``additionalProperties`` -- and a name that cannot tell them apart is
    not a name for either.

    ``standing`` is §3a's home rule's own input and :func:`shape_declared_at` is the rule.
    **AT L2 THE SCREEN IS DERIVED HERE AND IS NOT A PARAMETER**, which is §3a's "a caller
    cannot forget it and read a different collection than the run does" read at a screen
    rather than at an order: L2 must not read a node's own ``properties`` as the type where
    the DOCUMENT applies a named type that bag is only part of (:func:`shape_states`'
    ``applied``, which carries the measurement), and a screen a caller supplies is a screen
    a caller can supply differently.  Measured before it moved here: this module's own L2
    fixture and ``tests/test_catalogue_homes.py``'s both read L2 unscreened while the run
    read it screened, so the gate on a homeless entry ranged over a layer no run collects.
    :attr:`Admitted.screens` is where the answer is held, so the emitter's two passes
    collect L2A once between them.
    """
    if layer == "L2":
        held = None if documents is None else frozenset(documents)
        if held not in admitted.screens:
            admitted.screens[held] = collect_applied(
                admitted,
                collect_shapes(admitted, "L2C", standing, documents),
                standing,
                documents,
            ).collected
        applied: Collection[tuple[str, str]] = admitted.screens[held]
    else:
        applied = ()
    grouped: dict[str, list[Shaped]] = {}
    every: list[Shaped] = []
    for position in shape_states(admitted, layer, documents, applied):
        every.append(position)
        grouped.setdefault(position.key, []).append(position)

    entries: dict[str, ShapeEntry] = {}
    untitled: list[tuple[Shaped, ...]] = []
    conflicting: list[ShapeConflict] = []
    restated: list[tuple[Shaped, ...]] = []
    duplicated: list[tuple[Shaped, ...]] = []
    declaring_nothing: list[tuple[Shaped, ...]] = []
    #: key -> (the title the bundle states or ``None``, the home), for every group this
    #: layer collects.  Read in one pass BEFORE the names are derived, because §4's
    #: first-fit is a statement about the whole set: a step-2 candidate two entries derive
    #: identifies neither, and that cannot be known one entry at a time.
    collecting: dict[str, tuple[str | None, Shaped]] = {}

    for key, group in grouped.items():
        if len(group) < 2:
            continue
        if len({p.document for p in group}) == 1:
            restated.append(tuple(group))
            continue
        stated = frozenset(p.title for p in group if p.title is not None)
        title: str | None = None
        if layer == "L2C" and any(p.title is None for p in group):
            # **AT L2C THE TITLE MUST BE AT EVERY STATING POSITION, which is stricter than
            # the clause below and is the layer's own evidence rule** (:func:`shape_states`:
            # identity at a composed position is evidence of a shared BASE and never of a
            # shared subject).  One title among several untitled positions is enough at L2,
            # where the key carries the property names and the positions are known to be
            # one subject before any title is read; here it would let a word written once
            # decide for positions that say nothing, and the measurement in
            # :func:`shape_states` is what two of those positions turn out to be.  The
            # judgment table states the same test as its own evidence: "the bundle names
            # EVERY one of the N positions".
            untitled.append(tuple(group))
            continue
        if len(stated) == 1:
            title = next(iter(stated))
        elif len(stated) > 1:
            rooted = {p.title for p in group if p.is_a_root and p.title is not None}
            if len(rooted) != 1:
                conflicting.append(ShapeConflict(key, tuple(sorted(stated)), tuple(group)))
                continue
            title = next(iter(rooted))
        elif layer != "L2":
            # The array layer COLLECTS NOTHING, by derivation (:class:`Shapes`): an array
            # type renders as ``list[X]``, which Python writes once by construction, so
            # there is nothing here to declare and nothing to name.
            untitled.append(tuple(group))
            continue
        elif all(p.declares_no_class for p in group):
            declaring_nothing.append(tuple(group))
            continue
        collecting[key] = (title, shape_declared_at(group, title, standing))

    #: §4's step 2 per group, and then its first-fit rule over the whole layer: a name two
    #: groups derive is taken by neither.
    candidate = {
        key: structure_in_words(at.fields) if title is None else None
        for key, (title, at) in collecting.items()
    }
    taken: dict[str, int] = {}
    for spelled in candidate.values():
        if spelled is not None:
            taken[spelled] = taken.get(spelled, 0) + 1

    for key, (title, at) in collecting.items():
        name = candidate[key]
        if name is not None and taken[name] > 1:
            name = None
        entry = ShapeEntry(
            key=key,
            title=title,
            positions=tuple(grouped[key]),
            at=at,
            name=name,
            step=1 if title is not None else (2 if name is not None else 3),
        )
        # **An entry with no position to stop minting is not an entry**, and which part
        # it belongs to is read off the positions rather than asserted: every position a
        # ROOT is §1's case, where each is obliged to declare; every other position inside
        # a RULE is q5g's, where none of them declares at all.  Both are questions the key
        # cannot settle, so both are reported.
        if not entry.restating and not entry.withheld:
            (declaring_nothing if entry.undeclared else duplicated).append(entry.positions)
            continue
        entries[key] = entry

    return Shapes(
        entries=entries,
        untitled=tuple(untitled),
        conflicting=tuple(conflicting),
        restated=tuple(restated),
        duplicated=tuple(duplicated),
        declaring_nothing=tuple(declaring_nothing),
        withheld=tuple(
            (entry.spelled, position)
            for entry in entries.values()
            for position in entry.withheld
        ),
        undeclared=tuple(
            (entry.spelled, position)
            for entry in entries.values()
            for position in entry.undeclared
        ),
        positions=tuple(every),
    )


@dataclass(frozen=True)
class Applied:
    """Layer L2A: the positions a DOCUMENT applies an already-collected entry's type at.

    A PARTITION of the L2A census, so every position is in exactly one part and nothing is
    dropped quietly: it reaches a collected entry (:attr:`entries`), or it declares no
    class (:attr:`undeclared`), or the type it applies is one no other position of the
    bundle states under a name (:attr:`unmatched`).
    """

    #: key -> the collected entry EXTENDED with the applied positions: ``positions`` is the
    #: union and ``at`` is the home re-decided over it.  A :class:`ShapeEntry` and not a
    #: kind of its own, so :attr:`ShapeEntry.restating`'s five screens and
    #: :func:`shape_declared_at`'s one home rule are the same code here as at L2C.
    entries: dict[str, ShapeEntry]
    #: The censused positions at which no class is declared at all
    #: (:attr:`Shaped.declares_no_class`) -- at this layer every one of them is a CONJ,
    #: which is §5's ``allOf`` row: a conjunct's properties are declared on the node
    #: holding the ``allOf``, so the conjunct's own pointer carries no class and there is
    #: nothing at it either to collapse or to home.  Reported, never counted out.
    undeclared: tuple[Shaped, ...]
    #: The censused positions whose applied type matches no collected entry.  Reported
    #: rather than screened, because a position here is the honest statement of the layer's
    #: boundary: the document applies a composed type the bundle names nowhere, and §3a's
    #: third local state is where that belongs and not this one.
    unmatched: tuple[Shaped, ...]
    #: Every L2A position censused, which is the set the three parts above partition.
    positions: tuple[Shaped, ...]
    #: The ``(document, pointer)`` of every position this layer COLLECTED -- the ones whose
    #: own text does not state the entry's type, so the entry gained them here.  It is
    #: ``collect_shapes``' ``applied`` screen (:func:`shape_states` carries why): L2 reads a
    #: node's own ``properties``, and at one of these that bag is part of the type and not
    #: the type, so L2 must not collect the position as a statement of anything.
    collected: frozenset[tuple[str, str]]

    def restating(self) -> dict[str, dict[str, Reference]]:
        """document -> pointer -> the entry's home, for every position that RESTATES one.

        :meth:`Shapes.restating`'s own table, read off the EXTENDED entries -- so a
        position of the entry gets the same row it already had and the applied positions
        get theirs, under one home.  Merged into ``compiler.Module.objects`` after L2C's,
        which is what makes the collapse the BUILD's: the walk's question at a position is
        the one it already asks of every pointer, "is this position a REFERENCE to a
        catalogue entry", and this layer is a fourth answer to it and not a new question.
        """
        out: dict[str, dict[str, Reference]] = {}
        for entry in self.entries.values():
            home = Reference(
                document=entry.at.document, pointer=entry.at.pointer, title=entry.spelled
            )
            for position in entry.restating:
                out.setdefault(position.document, {})[position.pointer] = home
        return out


def collect_applied(
    admitted: Admitted,
    composed: Shapes,
    standing: Mapping[str, int],
    documents: Collection[str] | None = None,
) -> Applied:
    """§3a's layer L2A: **a position is read as the type the DOCUMENT APPLIES there.**

    :func:`applied_conjunction` is the reading and carries the defect. What is decided here
    is the two things a reading cannot decide on its own -- WHICH entry such a position may
    join, and WHERE the one class is declared.

    **IT JOINS ONLY AN ENTRY ``composed`` ALREADY COLLECTED, WHICH IS WHY NO TITLE IS OWED
    AT THE POSITION ITSELF.**  L2C collects a group only where the bundle TITLES every
    position whose own text states the type, and that rule stands untouched -- it is the
    layer's evidence rule and the measurement behind it is
    :func:`shape_states`'s: at a composed position, identity is evidence of a shared BASE
    and never of a shared subject, so a word written once must not decide for positions
    that say nothing.  **A position here says nothing BECAUSE ITS OWN TEXT CANNOT**: the
    subject exists only once the document applies the reference from above, so demanding
    the title at it demands a sentence the bundle is structurally unable to state, and
    writing one would be the very claim-a-node-does-not-support that the override table is
    not allowed to be.  What licenses the collapse is that the SUBJECT is named -- reading
    4, verbatim: *"a name is minted per ENTRY and never per position"* -- and the entry is
    named because every position that CAN carry the title does.

    **AND THE HOME IS ``shape_declared_at``'S, RE-DECIDED OVER THE UNION, so there is one
    home rule and not two and the acyclicity is still by construction.**  §3a: *"the home
    is the group's earliest document in the dependency order that already exists"*, so
    every edge this layer adds runs BACKWARDS along a topological order of all the other
    edges -- and that argument covers an applied position exactly as it covers a stating
    one, because it is an argument about the standing order and not about the group.  A
    screen that only ADMITTED positions later in the order would be the measured-for-cycles
    rule §3a forbids; re-ranking cannot produce a cycle at all, and where an applied
    position is the earliest document the home MOVES TO IT and the entry's former home
    takes a row like any other restating position.

    Measured on ``schemas/cache/3.2``: **942 positions censused, 931 unmatched, 9
    declaring no class, 2 COLLECTED.**  The 931 apply a composed type the bundle titles at
    no position at all, which is :attr:`Shapes.untitled` -- L2C's own third state and
    ``adcontextprotocol/adcp#8735``'s ask -- and not this layer's to answer; they are
    listed and nothing is done to them.  The 2 are
    ``core/assets/daast-asset.json#/oneOf/0/properties/macro_declarations/items`` and
    ``core/assets/vast-asset.json#/oneOf/0/properties/macro_declarations/items``, both
    joining *URL Macro Declaration*, whose home STAYS
    ``core/assets/url-asset.json#/properties/macro_declarations/items`` because url-asset
    stands at 389 in the standing order against daast-asset's 490 and vast-asset's 496.

    **IT IS A LAYER AND NOT A TABLE, which is the architecture clause this closes.**  The
    group it decides was a COLLAPSE row of ``tests/duplicates.py`` -- a judgment a reader
    had to go and look up -- and *"an override the build does not apply is a lie"*.  A
    lookup into that table at emit time was the other candidate and is refused by §3a
    twice over: rewriting emitted output to deduplicate it afterwards is the
    post-processing this project exists to refuse, and a home not derived from the bundle
    makes which module declares a class a function of the dependency order.  Both terms
    here are derived from the bundle alone -- the type by draft-07's own semantics, the
    home by the standing order -- so the row this deletes is deleted by the tree no longer
    forming the group.
    """
    collected = dict(composed.entries)
    every: list[Shaped] = []
    undeclared: list[Shaped] = []
    unmatched: list[Shaped] = []
    joining: dict[str, list[Shaped]] = {}
    for position in shape_states(admitted, "L2A", documents):
        every.append(position)
        entry = collected.get(position.key)
        if entry is None:
            unmatched.append(position)
            continue
        if (position.document, position.pointer) in {
            (p.document, p.pointer) for p in entry.positions
        }:
            # The position states the type in its own text too and is already a position of
            # the entry -- one node read twice is one position, not two.
            continue
        if position.declares_no_class:
            undeclared.append(position)
            continue
        joining.setdefault(position.key, []).append(position)

    entries: dict[str, ShapeEntry] = {}
    for key, found in joining.items():
        entry = collected[key]
        union = (*entry.positions, *found)
        entries[key] = ShapeEntry(
            key=entry.key,
            title=entry.title,
            positions=union,
            at=shape_declared_at(union, entry.title, standing),
            name=entry.name,
            step=entry.step,
        )
    return Applied(
        entries=entries,
        undeclared=tuple(undeclared),
        unmatched=tuple(unmatched),
        positions=tuple(every),
        collected=frozenset(
            (position.document, position.pointer)
            for found in joining.values()
            for position in found
        ),
    )


# --------------------------------------------------------------------------- #
# §3a's layer L1: the CONSTRAINED SCALARS, and the name each one takes
# --------------------------------------------------------------------------- #
#: The pointer segment that contributes a SUFFIX to the subject a named ancestor gives,
#: which is §4's nested rule read one step at a time: ``<Property>Item`` for an array
#: element, ``<Property>Value`` for a mapping value.
#:
#: **DERIVED from the descent column and never listed** (§3, §11: the table is the one
#: place a keyword decision lives).  The two WORDS are §4's and are the two
#: ``lower/names.py`` spells for the same two positions; which keywords reach them is the
#: table's answer, so a keyword joining ``ELEM`` or ``MAPV`` joins this by its own cell.
#: ``patternProperties`` lands here rather than in :data:`NAMING` because its key is a
#: REGEX and not a name the bundle gives a subject.
SUFFIXED = {
    **{keyword: "Item" for keyword, at in bundle.DESCENDS.items() if at is keywords.Position.ELEM},
    **{keyword: "Value" for keyword, at in bundle.DESCENDS.items() if at is keywords.Position.MAPV},
}

#: The keywords that hold a bag of named subschemas whose KEY is the name the bundle
#: gives the subject beneath it -- §4's "the property the constraint belongs to", and the
#: ``definitions`` key beside it.  Derived for :data:`SUFFIXED`'s reason: a ``PROP`` or a
#: ``DEF`` position is reached through a keyword whose key IS a name.
NAMING = frozenset(
    keyword
    for keyword, at in bundle.DESCENDS.items()
    if at in (keywords.Position.PROP, keywords.Position.DEF)
)


@dataclass(frozen=True)
class Constrained:
    """One position that STATES a constrained scalar: §3a's layer L1.

    :class:`Stated` is L0's and :class:`Shaped` is L2's and L3's; this is the same fact at
    the layer whose identity is a CONSTRAINT SET.  **The identity is the constraint and
    the constraint carries no name**, which is the whole of why this layer needs a naming
    rule of its own and why §3a's argument for the array layer transfers to it verbatim
    (see :func:`collect_scalars`).
    """

    document: str
    pointer: str
    position: keywords.Position
    #: The document's own type word: ``string``, ``integer`` or ``number``.  Taken from
    #: the nearest enclosing node that states one where this node states none, because a
    #: ``pattern`` under an ``anyOf`` of a ``type: string`` root is a constrained STRING
    #: and the type word is the ancestor's -- ``core/macro-bearing-url.json`` is the case,
    #: and reading the node alone misses it and every alias the intersection derives.
    kind: str
    #: The constraint keywords this position states, in :data:`constraints_spelling`'s
    #: order, which is the KEY this layer is collected on.
    constraints: tuple[tuple[str, object], ...]
    #: The ``format`` where one is part of the shape, which ``constraints.Shape`` carries
    #: as a third member for ``ir.TypeRef``'s own reason.
    format: str | None
    #: The node's own ``title``, or ``None``.
    title: str | None
    #: **The name the BUNDLE gives this position's subject**, or ``None`` where it gives
    #: none -- §4's step 1, in §4's own order: a ``title``, a ``definitions`` key, the
    #: property the constraint belongs to, and §4's nested rule beneath any of them.
    subject: str | None
    #: Does the walk LOWER a type from this position at all?  :attr:`Stated.reached`'s
    #: reading: ``False`` inside a ``definitions`` entry no ``$ref`` names.
    reached: bool = True
    #: **Does §1 ALREADY EXPORT A SYMBOL for the type at this position?**  True at a
    #: document ROOT -- D5 fixes a document's own symbol -- and at a ``definitions`` entry
    #: a ``$ref`` names, which §4's nested rule declares in its own module under the
    #: entry's key.
    #:
    #: It is what stops §4's step 1 taking a name that is already taken.  §3a's own
    #: correction says a document root "is already a home.  There is nothing to mint,
    #: because the bundle named it", and §4 says which side moves when two positions want
    #: one name: "a root keeps the name because D5 fixes its symbol ... So the colliding
    #: branch falls, and the import keeps the name."  An alias carries no
    #: ``__adcp_schema__``, so it is the side that moves, and the move is to §4's step 3.
    #:
    #: Measured, without this 9 alias symbols took a name the module importing them
    #: declares -- ``core/experimental-feature-id.json``'s root against
    #: ``ExperimentalFeatureID``, and ``definitions/code`` against the ``Code`` its own
    #: module declares for the same node.
    declares_a_symbol: bool = False

    @property
    def key(self) -> tuple[str, tuple[tuple[str, object], ...], str | None]:
        """This position's SHAPE, which is ``constraints.Shape`` read as a hashable key."""
        return (self.kind, self.constraints, self.format)

    @property
    def is_a_root(self) -> bool:
        """Is this position the document's own ROOT?  :attr:`Stated.is_a_root`'s reason."""
        return self.pointer == ""


@dataclass(frozen=True)
class ScalarEntry:
    """One L1 entry: a constraint, the name §4's derivation gives it, and where it lives."""

    key: tuple[str, tuple[tuple[str, object], ...], str | None]
    #: The symbol ``adcp.types.constraints`` declares for this constraint.
    name: str
    #: WHICH of §4's three steps answered -- 1 the bundle's own name for the subject, 2 the
    #: constraint in words, 3 the declaring position.  **There is no fourth**, and a step
    #: of 3 is simultaneously the name and the UPSTREAM ASK: the bundle states this
    #: constraint for subjects it names differently or not at all, so the symbol names
    #: where the type is declared and claims no subject.
    step: int
    #: Every position that states this constraint, in bundle order.
    positions: tuple[Constrained, ...]
    #: The position this entry is DECLARED at, which is the name's home at step 3.
    at: Constrained

    @property
    def documents(self) -> frozenset[str]:
        return frozenset(p.document for p in self.positions)

    @property
    def subjects(self) -> tuple[str, ...]:
        """The distinct names the bundle gives the subjects of this one constraint."""
        return tuple(sorted({p.subject for p in self.positions if p.subject is not None}))


@dataclass(frozen=True)
class Scalars:
    """§3a's layer L1 over a bundle: every constrained scalar, collected once and named.

    **The three parts are §4's three derivation steps and nothing else**, which is what
    "there is no fourth step" means held by a type: :attr:`named_by_the_bundle`,
    :attr:`named_by_the_constraint` and :attr:`pending_a_name` partition
    :attr:`entries`, and a reader asking which step answered reads
    :attr:`ScalarEntry.step`.
    """

    #: shape -> its entry, for every constrained scalar the bundle states.
    entries: Mapping[tuple[str, tuple[tuple[str, object], ...], str | None], ScalarEntry]
    #: Every stating position, which is the set the entries partition.
    positions: tuple[Constrained, ...]

    def _relaxed(self) -> dict[object, ScalarEntry]:
        """The lookup keys an entry also answers at, for a shape the WALK composes.

        A shape reaching ``constraints.resolve`` is not always a shape some node of the
        bundle states verbatim: a ``format: uri`` that SELECTS a URL type leaves the bound
        behind without the format (§5's ``format`` row), and an ``allOf`` intersection
        composes a constraint set no single node writes.  Both are the same constraint, so
        both reach the same entry: the format is dropped and then the type word, in that
        order, and a relaxed key is only ever added where it is UNAMBIGUOUS -- two entries
        wanting one relaxed key cancel it, so the fallback can never hand a caller the
        wrong constraint's name.
        """
        counted: dict[object, list[ScalarEntry]] = {}
        for entry in self.entries.values():
            kind, cons, _ = entry.key
            for relaxed in ((kind, cons, None), cons):
                if relaxed != entry.key:
                    counted.setdefault(relaxed, []).append(entry)
        return {key: group[0] for key, group in counted.items() if len(group) == 1}

    def table(self) -> dict[object, str]:
        """shape -> the symbol, which is the WHOLE of what the walk consults.

        The same arrangement :meth:`Catalogue.restating` is for L0: a plain mapping, so
        the walk reads a table and never this layer's collection, and §11's arrows hold.
        Keyed on the exact shape and on :meth:`_relaxed`'s unambiguous fallbacks together,
        the exact key winning where both answer.
        """
        return {
            **{key: entry.name for key, entry in self._relaxed().items()},
            **{key: entry.name for key, entry in self.entries.items()},
        }

    @property
    def named_by_the_bundle(self) -> tuple[ScalarEntry, ...]:
        """§4's step 1: the entries the bundle itself names."""
        return tuple(e for e in self.entries.values() if e.step == 1)

    @property
    def named_by_the_constraint(self) -> tuple[ScalarEntry, ...]:
        """§4's step 2: the entries whose constraint has a spelling in words."""
        return tuple(e for e in self.entries.values() if e.step == 2)

    @property
    def pending_a_name(self) -> tuple[ScalarEntry, ...]:
        """§4's step 3, which is also the UPSTREAM ASK, stated over a set of the bundle.

        The bundle states one constraint at positions whose subjects it names differently
        or not at all, so there is no name for the CONSTRAINT to take and the symbol names
        its declaring position instead.  **That is a name and not a digest** -- a reader
        follows it to the position and finds the constraint -- and it is an ask filed
        rather than answered: upstream naming the subject moves the entry to step 1.
        """
        return tuple(e for e in self.entries.values() if e.step == 3)


def _words(name: str) -> list[str]:
    """One pascal-case name split at its capital boundaries, acronyms kept whole.

    The unit a shared leading RUN is measured in: §4's rule is about segments and
    cutting one mid-word would mint a name no reader can map back to the bundle.
    """
    out: list[str] = []
    for ch in name:
        if ch.isupper() and out and not (out[-1].isupper() and len(out[-1]) == 1):
            out.append(ch)
        elif out:
            out[-1] += ch
        else:
            out.append(ch)
    merged: list[str] = []
    for word in out:
        if len(word) == 1 and word.isupper() and merged and merged[-1].isupper():
            merged[-1] += word
        else:
            merged.append(word)
    return merged


def _run(out: str, word: str) -> str:
    """``word`` appended to ``out`` past the leading RUN the two share (§4).

    §4: "Where the root's name and the target's share a leading run, the branch takes the
    root's name plus the target's distinguishing remainder, so
    ``core/requirements/asset-requirements.json``'s branch on ``image-asset-requirements``
    is ``AssetRequirementsImage`` and not the target's name repeated."  Both inputs are
    facts about the one position, so the rule is insertion-stable, which is §4's own
    criterion.

    Measured on this bundle's longest step-3 name: ``Get Account Financials Response``
    stating ``Get Account Financials Success`` at a branch reads
    ``GetAccountFinancialsResponseSuccessCurrency`` rather than
    ``GetAccountFinancialsResponseGetAccountFinancialsSuccessCurrency``.
    """
    if not out:
        return word
    if out in word:
        return word
    # **A ``word`` the accumulated name already CONTAINS is still appended**, and that is
    # not redundancy for its own sake: dropping it makes the symbol equal the DOCUMENT's
    # own name, which §1 exports for the document's root class, and §4's rule is that the
    # root keeps the name ("D5 fixes its symbol") and the colliding side moves.  Measured,
    # dropping it collided 8 alias symbols with the root class of their own home --
    # ``core/agent-webhook-challenge.json``'s ``challenge`` against
    # ``AgentWebhookChallenge`` and seven more.  Only a shared LEADING run is collapsed,
    # which is the rule §4 states.
    head, tail = _words(out), _words(word)
    shared = 0
    while shared < min(len(head), len(tail)) and head[shared] == tail[shared]:
        shared += 1
    return out + "".join(tail[shared:])


def _subject(doc: Mapping[str, object], pointer: str, node: Mapping[str, object]) -> str | None:
    """§4's step 1 at ONE position: the name the bundle gives this position's subject.

    §4's own list in §4's own order -- "a ``title``, a ``definitions`` key, the property
    the constraint belongs to" -- with §4's nested rule applied beneath any of the three,
    so an array element of ``allowed_tasks`` is still an allowed task and not nameless.
    **A ``description`` is not read**: §3a's sentence is that "a description states what a
    thing IS, not what it is CALLED, so it mints no name".

    A combinator's BRANCH contributes its own ``title`` where it carries one and nothing
    at all otherwise, which is §4's branch candidates minus the index: a minted name may
    not contain a positional index, so a branch the bundle does not name is walked past
    rather than numbered.
    """
    title = node.get("title")
    if isinstance(title, str) and title.strip():
        return names.class_name(title)
    parts = [p for p in pointer.split("/") if p]
    out, walked, at = "", "", 0
    while at < len(parts):
        part = parts[at]
        walked += f"/{part}"
        if part in NAMING and at + 1 < len(parts):
            out += names.class_name(parts[at + 1])
            walked += f"/{parts[at + 1]}"
            at += 2
            continue
        if part in SUFFIXED:
            # **The suffix lands on the name SO FAR and never on the next segment.**
            # §4 names an array element ``<Property>Item``, so ``any_of/items/.../role``
            # is a ``role`` of an ``AnyOfItem`` and not an ``AnyOfRoleItem`` -- and a
            # trailing ``items`` with nothing named after it keeps its suffix instead of
            # losing it, which is the same bug read from the other end.
            out += SUFFIXED[part]
            at += 1
            continue
        if part.isdigit():
            try:
                branch = bundle.node_at(doc, walked)
            except (KeyError, IndexError, TypeError, ValueError):
                branch = {}
            spelled = branch.get("title") if isinstance(branch, dict) else None
            if isinstance(spelled, str) and spelled.strip():
                out = _run(out, names.class_name(spelled))
            at += 1
            continue
        at += 1
    if out:
        return out
    root = doc.get("title")
    if isinstance(root, str) and root.strip():
        return names.class_name(root)
    return None


def _home_name(bundle_dir: Path, at: Constrained) -> str:
    """§4's step 3: the DECLARING POSITION, spelled as a name.

    §1's rule is that "for a symbol carrying no ``__adcp_schema__`` the declaring position
    is its catalogue entry's home", and this is that rule written out: the home's own
    document, then the subject that position carries (:func:`_subject`).  The document is
    IN the name here and is not in a nested class's, and §4 says why -- "the module path
    already carries the document" is true of ``adcp.types._schemas`` and false of
    ``adcp.types.constraints``, which carries no document at all, so the name must.

    Where the position's own subject already contains the document's name the document is
    not repeated, which is §4's rule for a branch sharing a leading run with its root.

    **No positional index and no digest**, which is §4's one rule for both: a branch
    contributes its own title or nothing (:func:`_subject`), and nothing here is a
    function of the constraint's bytes.
    """
    doc = bundle.read(bundle_dir, at.document)
    title = doc.get("title")
    head = names.class_name(
        title if isinstance(title, str) and title.strip() else Path(at.document).stem
    )
    name = head if at.subject is None else _run(head, at.subject)
    if name != head:
        return name
    # **A NAME THAT CAME OUT AS THE DOCUMENT'S OWN takes the type word in front**, because
    # §1 exports the document's name for its root and D5 fixes it.  Two positions reduce
    # to it -- the root itself, whose subject IS the document's title, and a combinator
    # branch with no naming ancestor, which falls back to the root's title
    # (``core/macro-bearing-url.json``'s ``anyOf`` arms).  The word is the document's own
    # type word, which is the alphabet ``constraints.symbol`` already spells in, so
    # ``StrExperimentalFeatureID`` reads as what it is: the constrained string that root
    # states.  No class of the tree is named for a type word, so this cannot collide back.
    return BASE_WORD.get(at.kind, "") + name


def scalar_states(
    bundle_dir: Path,
    spelled: Collection[str],
    documents: Collection[str] | None = None,
) -> Iterator[Constrained]:
    """Every position of the bundle that STATES a constrained scalar.

    ``spelled`` is ``constraints.SPELLING``'s keyword set, handed IN rather than imported:
    §11's arrows run ``catalogue <- constraints``, so the layer that owns the spelling
    says which keywords it spells and this one collects over them.

    **A RULE POSITION MINTS NO TYPE** (§3a), so a node inside an ``if``, ``then``, ``else``
    or ``not`` is not a stating position -- it constrains an instance of the enclosing type
    and declares none of its own.  **A ``definitions`` entry no ``$ref`` names is not one
    either**, which is :attr:`Stated.reached`'s reading at L0.

    **The type word is INHERITED where a node states none**, which is the one reading a
    node-local census gets wrong: ``core/macro-bearing-url.json`` states ``type: string``
    at its root and the ``pattern`` on an ``anyOf`` branch beneath it, and a census reading
    each node alone collects neither the branch nor the alias the walk derives for it.
    """
    named = bundle.named_nodes(bundle_dir)
    for document in stating(bundle_dir, documents):
        doc = bundle.read(bundle_dir, document)
        unreferenced = tuple(
            sorted(bundle.section_entries(doc) - named.get(document, frozenset()))
        )
        words: dict[str, str] = {}
        for pointer, node, position in bundle.nodes_at(doc):
            word = node.get("type")
            if isinstance(word, str):
                words[pointer] = word
            elif position is keywords.Position.KEY:
                # A ``propertyNames`` node constrains a KEY, and a JSON object's key is a
                # string by the keyword rather than by a ``type`` the document states.
                words[pointer] = "string"
            elif position in INHERITS:
                # **The type word is inherited ONLY through a step that keeps the
                # INSTANCE**, which a combinator's branch and an ``allOf`` conjunct do and
                # a property, an element and a mapping value do not: the string under
                # ``type: string`` plus ``anyOf`` is the same string, and a property of an
                # object is a different instance entirely.  Found by pointer PREFIX over
                # the walk's own order, which yields an ancestor before its descendants.
                for upto in range(len(pointer), -1, -1):
                    if pointer[:upto] in words:
                        words[pointer] = words[pointer[:upto]]
                        break
            if position is keywords.Position.RULE:
                continue
            kind = words.get(pointer)
            if kind not in SCALAR_WORDS:
                continue
            stated = tuple(sorted((k, node[k]) for k in node if k in spelled))
            fmt = node.get("format")
            fmt = fmt if isinstance(fmt, str) else None
            if not stated and fmt is None:
                continue
            title = node.get("title")
            yield Constrained(
                document=document,
                pointer=pointer,
                position=position,
                kind=kind,
                constraints=stated,
                format=fmt,
                title=title if isinstance(title, str) and title.strip() else None,
                subject=_subject(doc, pointer, node),
                reached=not any(pointer.startswith(entry) for entry in unreferenced),
                declares_a_symbol=(
                    pointer == "" or pointer in named.get(document, frozenset())
                ),
            )


#: The type words a constrained SCALAR can carry, which is ``constraints.BASE``'s own key
#: set read from this side.  Restated rather than imported for :func:`domain`'s reason --
#: §11's arrows run ``catalogue <- constraints`` -- and ``tests/test_catalogue.py``'s
#: equality against ``constraints.BASE`` is what keeps the two from coming apart.
SCALAR_WORDS = frozenset({"string", "integer", "number"})

#: **§4's STEP 2, as a type**: ``constraints.symbol``, which spells a constraint set in
#: words or answers ``None`` where one of its keywords has no words.  Taken as a parameter
#: rather than imported because §11's arrows run ``catalogue <- constraints``: the layer
#: that OWNS the spelling says what it spells, and this one collects over the answer.
InWords = Callable[..., str | None]

#: The positions a node INHERITS its enclosing node's type word at, because the instance
#: is the same one: a combinator's branch and an ``allOf`` conjunct.  Every other position
#: is a different instance and states its own type or none.
INHERITS = frozenset({keywords.Position.BRANCH, keywords.Position.CONJ})


def collect_scalars(
    bundle_dir: Path,
    spelled: Collection[str],
    in_words: InWords,
    documents: Collection[str] | None = None,
) -> Scalars:
    """Layer L1 over the bundle: every constrained scalar, named by §4's three steps.

    ``in_words`` is ``constraints.symbol`` -- §4's step 2, which is the owning layer's
    own spelling of a constraint set and is handed in for :func:`scalar_states`' reason.

    **§3a'S ARGUMENT FOR THE ARRAY LAYER IS THIS LAYER'S ARGUMENT TOO, and it is what
    decides step 1.**  §3a: "What tells a shared subject from a coincidental overlap is
    that an object's key holds the property NAMES, while an array's key over a scalar
    element holds no name at all -- which is why the object layer can collapse on identity
    and the array layer must not."  **A constrained scalar's key holds no name either**:
    it is the constraint, and nothing in it says what the constraint is ABOUT.  So one
    position's ``title`` names THAT POSITION's subject and says nothing about the
    constraint's, and step 1 answers only where every stating position names the SAME
    subject -- which is the only condition under which the bundle has named the
    constraint's own subject rather than one site's.

    Measured over this bundle, that is the difference between a name and a lie:
    ``^[A-Za-z0-9_.:-]{1,128}$`` is titled "Reporting Delivery Offering ID" at one of its
    ten positions and reached at ``name``, ``external_ref`` and ``reporting_profile`` at
    the others, and ``^[A-Z]{3}$`` is stated at 86 positions in 62 documents for
    ``currency`` AND ``airport_code``.  L0's rule -- one title anywhere decides -- would
    name both, and both names would be false at most of their sites.

    **The three steps, and there is no fourth** (``docs/plan/rebuild-plan.md`` §4):

    1. the bundle's own name for the subject, where every position agrees on one;
    2. else the constraint in words, which answers for every shape whose keywords all have
       a spelling -- so never for one carrying a ``pattern``, because a regular expression
       has no words and a name spelling the OTHER keywords alone would drop a fact;
    3. else the declaring position (:func:`_home_name`), which is also where two
       candidates colliding at step 1 separate -- "never by a hash of either".

    A step-1 candidate that two entries derive has identified neither, so BOTH fall to the
    next step, which is §4's own first-fit semantics for its name candidates.
    """
    grouped: dict[tuple[str, tuple[tuple[str, object], ...], str | None], list[Constrained]] = {}
    every: list[Constrained] = []
    for position in scalar_states(bundle_dir, spelled, documents):
        every.append(position)
        grouped.setdefault(position.key, []).append(position)

    # Step 1's candidate per shape, and then the collision rule over the whole layer.
    candidate: dict[object, str | None] = {}
    for key, group in grouped.items():
        subjects = {p.subject for p in group}
        answered = len(subjects) == 1 and None not in subjects
        # ... **and no stating position already carries §1's symbol for the type**
        # (:attr:`Constrained.declares_a_symbol`): there the subject's name is taken and
        # the alias is the side that moves, which is §4's own rule for a root and for an
        # imported symbol alike.
        candidate[key] = (
            subjects.pop()
            if answered and not any(p.declares_a_symbol for p in group)
            else None
        )
    taken: dict[str, int] = {}
    for word in candidate.values():
        if word is not None:
            taken[word] = taken.get(word, 0) + 1

    entries: dict[tuple[str, tuple[tuple[str, object], ...], str | None], ScalarEntry] = {}
    for key, group in grouped.items():
        kind, cons, fmt = key
        at = min(group, key=lambda p: (not p.reached, p.document, p.pointer))
        first = candidate[key]
        if first is not None and taken[first] == 1:
            step, name = 1, first
        elif (second := in_words(kind, dict(cons), format=fmt)) is not None:
            step, name = 2, second
        else:
            step, name = 3, _home_name(bundle_dir, at)
        entries[key] = ScalarEntry(
            key=key, name=name, step=step, positions=tuple(group), at=at
        )
    return Scalars(entries=_separated(entries, in_words), positions=tuple(every))


def _separated(
    entries: Mapping[tuple[str, tuple[tuple[str, object], ...], str | None], ScalarEntry],
    in_words: InWords,
) -> dict[tuple[str, tuple[tuple[str, object], ...], str | None], ScalarEntry]:
    """Two entries that derived one name at step 3, separated by their own CONSTRAINT.

    §4: "two constraints that collide at step 2 separate [at step 3], **never by a hash of
    either**", and this is the converse case -- two constraints colliding at step 3, where
    the positions that declare them are siblings the bundle names identically.  Measured,
    this bundle has exactly one such pair: ``core/macro-bearing-url.json``'s ``/anyOf/1``
    and ``/anyOf/2``, two patterns under one untitled ``anyOf`` whose only naming ancestor
    is the document root.

    **The index is not available and that is §4's own rule** -- "no name the compiler mints
    contains a content digest or a positional index" -- so what separates them is the part
    of each constraint that HAS a spelling in words, which is the ``format``: one branch
    states ``format: uri`` beside its pattern and the other states none.

    Where that still leaves two entries on one name nothing here invents a third, and
    ``constraints.record`` fails the build with both constraints in the message, which is
    the designed outcome for the emitter disagreeing with itself about what a name means.
    """
    held: dict[str, list[ScalarEntry]] = {}
    for entry in entries.values():
        held.setdefault(entry.name, []).append(entry)
    renamed = dict(entries)
    for name, group in held.items():
        if len(group) < 2:
            continue
        for entry in group:
            kind, _, fmt = entry.key
            word = in_words(kind, {}, format=fmt) if fmt is not None else None
            if word is None:
                continue
            renamed[entry.key] = ScalarEntry(
                key=entry.key,
                name=name + word.removeprefix(BASE_WORD.get(kind, "")),
                step=entry.step,
                positions=entry.positions,
                at=entry.at,
            )
    return renamed


#: The word a scalar's own ``type`` contributes to a name in words, which is
#: ``constraints.BASE`` read from this side -- stripped off a separating segment because
#: the segment is appended to a name that already says what it is about.
BASE_WORD = {"string": "Str", "integer": "Int", "number": "Float"}


def collect(
    bundle_dir: Path,
    standing: Mapping[str, int],
    documents: Collection[str] | None = None,
) -> Catalogue:
    """Layer L0 over the bundle: one pass, before naming (§3a).

    The four groups are a PARTITION of the VALUE LISTS stated at more than one position,
    and the partition is the thing a check ranges over: a value list is stated in one
    document (:attr:`Catalogue.restated`) or in several, and in the second case the bundle
    names it (:attr:`Catalogue.entries`), names it nowhere (:attr:`Catalogue.untitled`) or
    gives it two names neither of which is a document's own
    (:attr:`Catalogue.conflicting`).  Nothing falls outside and nothing is counted twice.

    **Keyed on the VALUE LIST and not on §3a's structural identity** --
    :func:`value_list` carries the measurement that makes the two interchangeable here and
    the one case the coarser key reaches that the finer one cannot.

    ``standing`` is §3a's home rule's input (``emit.standing_order``) and
    :func:`declared_at` is the rule.  It is POSITIONAL for ``collect_shapes``' own reason:
    a caller cannot forget it and read a different collection than the run does.
    """
    grouped: dict[Vocabulary, list[Stated]] = {}
    every: list[Stated] = []
    for position in states(bundle_dir, documents):
        every.append(position)
        grouped.setdefault(value_list(position), []).append(position)

    entries: dict[Vocabulary, Entry] = {}
    untitled: list[tuple[Stated, ...]] = []
    conflicting: list[Conflict] = []
    restated: list[tuple[Stated, ...]] = []
    shared: dict[Vocabulary, Shared] = {}
    alone: dict[Vocabulary, Stated] = {}

    def more_than_one_type(key: Vocabulary, group: list[Stated], titles: tuple[str, ...]) -> None:
        """Record §3a's second and third local states, which agree on the value list."""
        shared[key] = Shared(
            vocabulary=key,
            members=group[0].members,
            kind=KIND[type(group[0].members[0])],
            positions=tuple(group),
            titles=titles,
        )

    for key, group in grouped.items():
        if len(group) < 2:
            (alone[key],) = group
            continue
        if len({p.document for p in group}) == 1:
            restated.append(tuple(group))
            continue
        stated_titles = titles(group)
        if not stated_titles:
            # **§3a's JUDGEMENT, for the value lists the bundle names nowhere**, which is
            # the one question this collection cannot derive and ``codegen/vocabularies.py``
            # is where it is declared.  §3a's default for an untitled vocabulary is that it
            # is NOT collapsed, so an un-rowed value list falls through to ``untitled``
            # exactly as every untitled one did before the rows existed.
            if not vocabularies.one_subject(key):
                untitled.append(tuple(group))
                # §3a's "separate types, one value list" and "separate types pending a
                # name": where the judgement declares one of those, the VALUE LIST is one
                # and the types are per position.  An UN-ROWED untitled group is neither
                # -- §3a's default leaves it exactly as it was before this layer existed,
                # which is what measurement says it should be: of this bundle's 24
                # un-rowed groups, 17 emit no class at all and 7 emit one, so there is no
                # value list to write twice and a constant for one would have no user.
                if vocabularies.separate(key):
                    more_than_one_type(key, group, ())
                continue
            at = declared_at(group, standing)
            entries[key] = Entry(
                vocabulary=key,
                members=at.members,
                kind=KIND[type(at.members[0])],
                title=None,
                positions=tuple(group),
                name=vocabularies.judged(key),
                at=at,
            )
            continue
        title = the_name(group, stated_titles)
        if title is None:
            titled = tuple(sorted(stated_titles))
            conflicting.append(Conflict(key, titled, tuple(group)))
            # §3a's conflict rule reaches the same place from the other side: "a
            # conflicting title is not a question about which name wins ... In neither
            # case is there a third name to collapse to, and minting one is what §4
            # refuses."  Both names stand, so two types stand, and the value list under
            # them is one.
            more_than_one_type(key, group, titled)
            continue
        # The entry's member order is the NAMING position's: §3a derives the name from the
        # bundle, so the document that names the concept is the one whose spelling of it
        # the entry carries.
        naming = declared_at(group, standing)
        entries[key] = Entry(
            vocabulary=key,
            members=naming.members,
            kind=KIND[type(naming.members[0])],
            title=title,
            positions=tuple(group),
            at=naming,
        )
    return Catalogue(
        entries=entries,
        untitled=tuple(untitled),
        conflicting=tuple(conflicting),
        restated=tuple(restated),
        positions=tuple(every),
        shared=shared,
        alone=alone,
    )
