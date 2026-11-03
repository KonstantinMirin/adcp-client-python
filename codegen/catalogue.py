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

import json
from collections.abc import Collection, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from codegen import bundle, keywords, vocabularies

#: The EFFECTS a keyword can have without changing what a node ADMITS: a symbol
#: (``NAME``), a fact a lowering carries (``ANNOTATION``), a fact the enclosing FIELD
#: carries, or nothing at all.  The complement is :data:`keywords.LOWERED` -- "the
#: effects the NODE'S OWN handler has to write code for" -- which is exactly the set that
#: compiles to a TYPE or a RULE and therefore narrows an instance.
#:
#: ``FIELD`` is here on §2's own sentence about the one keyword that reaches it: a
#: ``default`` "neither widens nor narrows what the class accepts".
CARRIED = frozenset(
    {
        keywords.Effect.NAME,
        keywords.Effect.ANNOTATION,
        keywords.Effect.FIELD,
        keywords.Effect.NOTHING,
    }
)


def _carried() -> frozenset[str]:
    """Every keyword the TABLE gives no admitting effect at any position (§3a).

    §3a: "Identity here is STRUCTURAL and ignores annotations ... because an annotation
    does not change what a node admits."  **DERIVED from ``codegen/keywords.py`` and not
    listed**, which is the one declaration §9 gives this question: "a keyword handled in
    code but named in none of §5, §6 or §7 is an invented rule", and a hand-written list
    beside the table is how the two come to disagree -- the list said ``default`` was an
    annotation while the table says its cell is FIELD at PROP, and said
    ``discriminator`` while the table says NOTHING.  It also hid the collection from
    ``tests/test_keywords.py``'s census, which reads literal keyword collections and
    cannot read a derivation it has no reason to doubt.

    Two screens beside the effect, and both are about what a key IS rather than what it
    asserts:

    * a keyword the descent column DESCENDS into is a SECTION or a subschema holder, so
      two nodes differing in one differ in a node below -- it is not an annotation of
      this node whatever its own cell says;
    * a keyword admitted by the ``x-`` PREFIX is admitted by prefix at the point of use
      (:func:`identity`), for the reason §6 admits it that way: "The ``x-`` namespace is
      admitted by prefix AND listed by name", and a prefix test cannot be a set member.

    Measured over this bundle: the derived set and the list it replaces produce the same
    15 entries, the same 124 untitled groups, the same 3 conflicts, the same 23
    same-document restatements and the same 22 restating positions.  What it adds is the
    21 document-level metadata keys (``version``, ``lastUpdated``, ``baseUrl``, ...) and
    ``errorMessage``, every one of which the table already says asserts nothing -- so
    the derivation is wider than the list in exactly the direction §3a's sentence is.
    """
    descends = frozenset(
        word for position in keywords.Position for word in keywords.descends_at(position)
    )
    return frozenset(
        word
        for word, _ in keywords.TABLE.items()
        if (
            effects := {
                answer.effect
                for position in keywords.Position
                if (answer := keywords.cell(word, position)) is not None
            }
        )
        and effects <= CARRIED
        and word not in descends
        and not keywords.admitted_by_prefix(word)
    )


#: The keys whose value does not change what a node ADMITS, so two nodes differing only in
#: one of them are one vocabulary (§3a): :func:`_carried`'s derivation, and beside it the
#: two keys the TABLE does not list at all.
#:
#: ``$id`` and ``example`` are a document's own declaration of where it lives and the
#: bundle's singular spelling of ``examples``.  Neither has a row, so neither has a cell
#: to derive an effect from, and both are stated here -- which is the residue a
#: derivation cannot reach and is why it is two names and not fourteen.
ANNOTATIONS = _carried() | frozenset({"$id", "example"})

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
        """
        home = (self.naming.document, self.naming.pointer)
        return tuple(
            p
            for p in self.positions
            if (p.document, p.pointer) != home
            and not p.is_a_root
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


def states(bundle_dir: Path, documents: Collection[str] | None = None) -> Iterator[Stated]:
    """Every position of the bundle that STATES a vocabulary this layer collects.

    ``documents`` is for a test that wants a named subset and defaults to
    :func:`bundle.portable`, which is the whole bundle.  **A caller that passes the RUN's
    document set here would be the census §9 forbids**, which is why the default is the
    bundle and the parameter is documented as a test's: the two readings differ and only
    one of them is a function of the pinned input.
    """
    names = bundle.named_nodes(bundle_dir)
    for document in sorted(documents if documents is not None else bundle.portable(bundle_dir)):
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


def beneath(bundle_dir: Path) -> dict[str, frozenset[str]]:
    """document -> every document it reaches through a ``$ref``, transitively.

    A reading of the BUNDLE and not of the run, which is §9's rule and the same one
    :func:`collect` is permitted by: the answer is the same for a one-document command and
    for a whole-population emission.
    """
    direct: dict[str, set[str]] = {}
    for edge in bundle.edges(bundle_dir):
        if edge.target is not None and edge.target != edge.document:
            direct.setdefault(edge.document, set()).add(edge.target)
    out: dict[str, frozenset[str]] = {}
    for document in direct:
        seen: set[str] = set()
        unread = [document]
        while unread:
            for target in direct.get(unread.pop(), ()):
                if target not in seen:
                    seen.add(target)
                    unread.append(target)
        out[document] = frozenset(seen)
    return out


def declared_at(
    positions: Collection[Stated], title: str | None, reaches: Mapping[str, frozenset[str]]
) -> Stated:
    """The position a vocabulary's ONE class is declared at (:attr:`Entry.naming`).

    A TITLE or a ROOT answers it outright and :func:`ranked` is that order.  **What is left
    is a vocabulary the bundle names at no position and states at no root**, and there §3a
    says both where the entry belongs and why the obvious answer is wrong:

        "An entry lives in the NARROWEST namespace that contains every position
        referencing it ... **But a cycle is only possible if the shared type lives INSIDE a
        document module.**  Put the catalogue in its own layer beneath every document
        module and the dependency arrows point one way, so a cycle is not avoided by care
        -- it is unrepresentable."

    **That layer is not built here and the reason is a question §3a does not settle: the
    NAME.**  An entry in a module with no document has no position for §4 to derive a name
    at, and §4's collision rule lengthens a colliding name "by its own nearest ancestor
    segment" -- which an entry stated at six positions has six of.  Measured over this
    bundle under §3a's own namespace rule, 8 of the 95 untitled entries collide inside the
    namespace it sends them to: six distinct value lists derive ``Reason`` in the shared
    one, ``Mode`` and ``Unit`` collide in ``core`` and ``Status`` in ``media_buy``.  Until
    that sentence exists an entry is declared at a POSITION, where §4 names it and §1's
    domain-scope rule resolves it, and nothing is minted.

    **So the home is the stating document the other stating documents ALREADY REACH**, and
    the arrow a restatement adds then runs the way the bundle's own references already run.
    Measured over this bundle, against two other orders that are equally functions of it:

    ======================================================  ==========================
    the home is                                             reference cycles the
                                                            catalogue edge closes
    ======================================================  ==========================
    the first stating position in bundle order                                       4
    the last                                                                         5
    **the document the most other stating documents reach**                      **0**
    ======================================================  ==========================

    A cycle is a VERDICT for every document on it (``emit.order``), so the two rejected
    orders do not emit a wrong answer -- they refuse 9 documents.  **This order is
    measured cycle-free and not cycle-free by construction**, which is exactly the
    difference §3a's layer buys and is why this function names it.
    """
    best = min(positions, key=lambda p: ranked(p, title))
    if (best.title == title and title is not None) or best.is_a_root:
        return best
    documents = {p.document for p in positions}

    def already_beneath(position: Stated) -> tuple[object, ...]:
        others = documents - {position.document}
        under = sum(1 for other in others if position.document in reaches.get(other, ()))
        # ``reached`` first, for :attr:`Stated.reached`'s own reason: a home the walk
        # lowers nothing from declares no class for anything to reference.
        return (not position.reached, -under, position.document, position.pointer)

    return min(positions, key=already_beneath)


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

    def of(self, document: str, node: object, stack: tuple[tuple[str, str], ...] = ()) -> object:
        """The decided key of one node, as a hashable structure."""
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
                if at is None:
                    out.append((word, ("unresolved", json.dumps(held))))
                elif at in stack:
                    out.append((word, (CYCLE, len(stack) - stack.index(at))))
                else:
                    try:
                        reached = bundle.node_at(self.document(at[0]), at[1])
                    except (KeyError, IndexError, TypeError, ValueError):
                        # A pointer naming no node: the reference is unresolvable in fact
                        # whatever its spelling, and ``bundle.record`` is what refuses the
                        # document for it.  A census is not a verdict (§3a), so the key
                        # carries the URI and the run reports the refusal.
                        out.append((word, ("unresolved", json.dumps(held))))
                    else:
                        out.append((word, self.of(at[0], reached, (*stack, at))))
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

    @property
    def is_a_root(self) -> bool:
        """Is this position the document's own ROOT?  :attr:`Stated.is_a_root`'s reason."""
        return self.pointer == ""


@dataclass(frozen=True)
class ShapeEntry:
    """One L2 entry: a structure, the name the bundle gives it, and where it is declared."""

    key: str
    #: The ``title`` the bundle states.  Never ``None``: an untitled structure is §3a's
    #: THIRD answer -- "separate types pending a name ... an upstream ask and not a local
    #: answer" -- and is carried by :attr:`Shapes.untitled` instead.
    title: str
    #: Every position that states this structure, in bundle order.
    positions: tuple[Shaped, ...]
    #: The position this entry is DECLARED at.
    at: Shaped

    @property
    def documents(self) -> frozenset[str]:
        return frozenset(p.document for p in self.positions)

    @property
    def restating(self) -> tuple[Shaped, ...]:
        """Every position that states this structure and is not the one that DECLARES it.

        §3a's whole job for a catalogue layer: "to stop every other position minting a
        copy".  The first three exclusions are :attr:`Entry.restating`'s, verbatim and for
        the same three reasons -- a document ROOT must declare because §1 says every
        portable document contributes a symbol; a position in the home's own document is
        §4's content dedup's and not this layer's; and the home itself declares.  The
        fourth is :attr:`Shaped.keeps_a_named_node` and is this layer's own.
        """
        home = (self.at.document, self.at.pointer)
        return tuple(
            p
            for p in self.positions
            if (p.document, p.pointer) != home
            and not p.is_a_root
            and p.document != self.at.document
            and not p.keeps_a_named_node
            and not p.of_a_root_union
        )

    @property
    def withheld(self) -> tuple[Shaped, ...]:
        """The positions this entry does NOT answer at, with the reason each carries.

        **Enumerated and never counted**, which is reading 4's own requirement of a
        separate-type decision.  Two reasons, and each is a standing rule of another
        section rather than a judgement of this one: :attr:`Shaped.of_a_root_union` is §3's
        and §4's union rows, and :attr:`Shaped.keeps_a_named_node` is §5's.
        """
        home = (self.at.document, self.at.pointer)
        return tuple(
            p
            for p in self.positions
            if (p.document, p.pointer) != home
            and not p.is_a_root
            and p.document != self.at.document
            and (p.keeps_a_named_node or p.of_a_root_union)
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
    (:attr:`restated`) or in several, and in the second case the bundle names it
    (:attr:`entries`), names it nowhere (:attr:`untitled`), gives it two names neither of
    which is a document's own (:attr:`conflicting`), or names it at nothing BUT document
    roots (:attr:`duplicated`).

    **The last of those is a part L0 has no members in and L2 does.**  Ten of this
    bundle's object structures are stated at exactly two positions, both of them a document
    ROOT, both carrying the SAME title -- the bundle ships one document at two paths, under
    ``core/async-response-refs/`` and under the domain's own directory.  §1 obliges both to
    export a symbol, so neither can become a reference to the other, and the decided key
    says they admit identically.  **The decided key does not settle it**, so it is reported
    and not chosen in: the local answer available is an ALIAS at the second root, which is
    §3a's "a restated title that a consumer needs is an alias at its position, never a
    second class", and the question of which root is the alias is §1's rather than this
    layer's.
    """

    #: key -> the entry, for a structure the bundle states in more than one document and
    #: names at exactly one name.
    entries: Mapping[str, ShapeEntry]
    #: The structures stated in more than one document with NO title anywhere.  §3a's THIRD
    #: answer -- separate types pending a name, an upstream ask, never a local answer.
    untitled: tuple[tuple[Shaped, ...], ...]
    #: §3a's conflict case, for the owner.
    conflicting: tuple[ShapeConflict, ...]
    #: The structures a SINGLE document states at more than one position.  §4's content
    #: dedup is the whole rule for them.
    restated: tuple[tuple[Shaped, ...], ...]
    #: The structures whose every stating position is a document ROOT.  See the class
    #: docstring: §1 and reading 4 give different answers and the key settles neither.
    duplicated: tuple[tuple[Shaped, ...], ...]
    #: The positions of an ENTRY this layer withholds the collapse at, as
    #: ``(entry title, position)`` -- :attr:`ShapeEntry.withheld`, flattened so a report
    #: and a check range over one list.  **Enumerated, never counted**, which is reading
    #: 4's requirement of every separate-type decision.
    withheld: tuple[tuple[str, Shaped], ...]
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
                document=entry.at.document, pointer=entry.at.pointer, title=entry.title
            )
            for position in entry.restating:
                out.setdefault(position.document, {})[position.pointer] = home
        return out


def shape_states(
    admitted: Admitted, layer: str, documents: Collection[str] | None = None
) -> Iterator[Shaped]:
    """Every position of the bundle that STATES an object type (``"L2"``) or an array
    type (``"L3"``).

    **L2 is a node holding a non-empty ``properties``**, which is what an object type IS
    and is the population the 42 row's split was asked of.  **L3 is a node whose ``items``
    is a schema**, which is what an array type is.

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
    """
    names = bundle.named_nodes(admitted.dir)
    for document in sorted(
        documents if documents is not None else bundle.portable(admitted.dir)
    ):
        doc = admitted.document(document)
        unreferenced = tuple(
            sorted(bundle.section_entries(doc) - names.get(document, frozenset()))
        )
        for pointer, node, position in bundle.nodes_at(doc):
            if position is keywords.Position.RULE:
                continue
            if any(pointer.startswith(entry) for entry in unreferenced):
                continue
            if layer == "L2":
                held = node.get("properties")
                if not isinstance(held, dict) or not held:
                    continue
            elif not isinstance(node.get("items"), dict):
                continue
            title = node.get("title")
            yield Shaped(
                document=document,
                pointer=pointer,
                position=position,
                key=admitted.key(document, node),
                title=title if isinstance(title, str) and title.strip() else None,
                keeps_a_named_node=any(
                    bundle.split_ref(spelled) == ("", named)
                    for _, sub in bundle.nodes(node)
                    if isinstance(spelled := sub.get("$ref"), str)
                    for named in names.get(document, frozenset())
                ),
                of_a_root_union=(
                    position is keywords.Position.BRANCH and pointer.count("/") == 2
                ),
            )


def shape_ranked(position: Shaped, title: str) -> tuple[object, ...]:
    """:attr:`ShapeEntry.at`'s order over the positions of one entry, best first.

    :func:`ranked` is L0's and this is the same order: a root carrying the entry's own
    title, then any position carrying it, then any root, then the bundle's own order.  §1
    is what puts the roots first -- "every portable document contributes a symbol", so a
    root cannot become a reference to another module's class and is the one position of its
    group that MUST declare.
    """
    return (
        not (position.is_a_root and position.title == title),
        position.title != title,
        not position.is_a_root,
        position.document,
        position.pointer,
    )


def collect_shapes(
    admitted: Admitted, layer: str, documents: Collection[str] | None = None
) -> Shapes:
    """One STRUCTURAL layer over the bundle: §3a's L2 or L3, under the decided key.

    §3a's three-way split, asked of each group of positions that state one structure and
    answered exactly as L0 answers it:

    * **one named type** where the bundle names the subject -- one title, or several of
      which exactly one belongs to a document ROOT (:func:`the_name`'s rule);
    * **separate types over one definition** where the names conflict
      (:attr:`Shapes.conflicting`) or where every position is a root the bundle obliges to
      declare (:attr:`Shapes.duplicated`);
    * **separate types pending a name** where the bundle titles the structure nowhere
      (:attr:`Shapes.untitled`), which is an upstream ask and never a local answer.
    """
    grouped: dict[str, list[Shaped]] = {}
    every: list[Shaped] = []
    for position in shape_states(admitted, layer, documents):
        every.append(position)
        grouped.setdefault(position.key, []).append(position)

    entries: dict[str, ShapeEntry] = {}
    untitled: list[tuple[Shaped, ...]] = []
    conflicting: list[ShapeConflict] = []
    restated: list[tuple[Shaped, ...]] = []
    duplicated: list[tuple[Shaped, ...]] = []

    for key, group in grouped.items():
        if len(group) < 2:
            continue
        if len({p.document for p in group}) == 1:
            restated.append(tuple(group))
            continue
        stated = frozenset(p.title for p in group if p.title is not None)
        if not stated:
            untitled.append(tuple(group))
            continue
        if len(stated) == 1:
            title = next(iter(stated))
        else:
            rooted = {p.title for p in group if p.is_a_root and p.title is not None}
            if len(rooted) != 1:
                conflicting.append(ShapeConflict(key, tuple(sorted(stated)), tuple(group)))
                continue
            title = next(iter(rooted))
        at = min(group, key=lambda p: shape_ranked(p, title))
        entry = ShapeEntry(key=key, title=title, positions=tuple(group), at=at)
        # Every position a ROOT: §1 obliges each to declare, so the entry has nothing to
        # stop minting and the question the key cannot settle is reported instead.
        if not entry.restating and not entry.withheld:
            duplicated.append(tuple(group))
            continue
        entries[key] = entry

    return Shapes(
        entries=entries,
        untitled=tuple(untitled),
        conflicting=tuple(conflicting),
        restated=tuple(restated),
        duplicated=tuple(duplicated),
        withheld=tuple(
            (entry.title, position)
            for entry in entries.values()
            for position in entry.withheld
        ),
        positions=tuple(every),
    )


def collect(bundle_dir: Path, documents: Collection[str] | None = None) -> Catalogue:
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
    """
    reaches = beneath(bundle_dir)
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
            at = declared_at(group, None, reaches)
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
        naming = declared_at(group, title, reaches)
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
