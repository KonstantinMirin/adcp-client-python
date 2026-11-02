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

from codegen import bundle, keywords

#: The keys whose value does not change what a node ADMITS, so two nodes differing only in
#: one of them are one vocabulary (§3a).  §3a names six; the three beside them are the
#: bundle's own annotation spellings for an enumeration -- ``enumDescriptions`` and
#: ``x-enum-descriptions`` are §6's member-docstring row ("Two spellings of one keyword;
#: both are read") and ``enumMetadata`` is §6's row that carries nothing onto an
#: enumeration at all.  ``$schema`` and ``$id`` are a document's own declaration of the
#: draft it is read by and of where it lives, neither of which is an assertion about an
#: instance; ``discriminator`` is not a draft-07 keyword and asserts nothing.
#:
#: BY NAME and not by pattern, and the ``x-`` prefix is admitted beside the list for the
#: reason §6 admits it: "The ``x-`` namespace is admitted by prefix AND listed by name".
ANNOTATIONS = frozenset(
    {
        "description",
        "title",
        "examples",
        "example",
        "default",
        "$comment",
        "deprecated",
        "enumDescriptions",
        "enumMetadata",
        "readOnly",
        "writeOnly",
        "$schema",
        "$id",
        "discriminator",
    }
)

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

    identity: tuple[tuple[str, str], ...]
    #: The members in document order, read off the NAMING position so that the rendered
    #: order is a function of the document that names the concept.
    members: tuple[object, ...]
    #: ``"string"`` or ``"integer"``, in JSON Schema's words, which is ``ir.EnumDecl``'s
    #: own spelling of the base.
    kind: str
    #: The ``title`` the bundle states, exactly as it states it.
    title: str
    #: Every position that states this vocabulary, in bundle order.
    positions: tuple[Stated, ...]

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


@dataclass(frozen=True)
class Conflict:
    """A vocabulary the bundle gives MORE THAN ONE title: §3a's third naming case.

    Not collapsed, not named, and brought to the owner.  The titles and the positions are
    carried because that is what the decision needs: whether the two titles name one
    concept the bundle spells twice or two concepts whose value sets coincide.
    """

    identity: tuple[tuple[str, str], ...]
    titles: tuple[str, ...]
    positions: tuple[Stated, ...]


@dataclass(frozen=True)
class Catalogue:
    """Layer L0 over one bundle: the entries, and the two groups that are NOT entries."""

    #: identity -> the entry, for a vocabulary the bundle states in more than one document
    #: and gives exactly one title.
    entries: Mapping[tuple[tuple[str, str], ...], Entry]
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


def states(bundle_dir: Path, documents: Collection[str] | None = None) -> Iterator[Stated]:
    """Every position of the bundle that STATES a vocabulary this layer collects.

    ``documents`` is for a test that wants a named subset and defaults to
    :func:`bundle.portable`, which is the whole bundle.  **A caller that passes the RUN's
    document set here would be the census §9 forbids**, which is why the default is the
    bundle and the parameter is documented as a test's: the two readings differ and only
    one of them is a function of the pinned input.
    """
    for document in sorted(documents if documents is not None else bundle.portable(bundle_dir)):
        doc = bundle.read(bundle_dir, document)
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
            )


def titles(positions: Collection[Stated]) -> frozenset[str]:
    """The distinct titles the bundle gives this vocabulary, which decides §3a's case."""
    return frozenset(p.title for p in positions if p.title is not None)


def home(entry: Entry) -> str:
    """The NARROWEST namespace containing every position that states ``entry`` (§3a).

    One document → that document, as a bundle-relative path, which is the module the walk
    writes today.  One domain → that domain's name.  More than one → :data:`SHARED`.

    **It answers by §3a's rule even where :attr:`Entry.rooted` is non-empty**, and the
    module docstring states why that is reported rather than resolved here: for 13 of the
    15 entries §3a's rule and §4's root rule give different homes, and choosing between
    them moves -- or declines to move -- a name the domain surface exports today.
    """
    documents = entry.documents
    if len(documents) == 1:
        return next(iter(documents))
    domains = entry.domains
    return next(iter(domains)) if len(domains) == 1 else SHARED


def collect(bundle_dir: Path, documents: Collection[str] | None = None) -> Catalogue:
    """Layer L0 over the bundle: one pass, before naming (§3a).

    The three groups are a PARTITION of the identities stated at more than one position,
    and the partition is the thing a check ranges over: an identity is stated in one
    document (:attr:`Catalogue.restated`) or in several, and in the second case the bundle
    gives it one title (:attr:`Catalogue.entries`), none (:attr:`Catalogue.untitled`) or
    more than one (:attr:`Catalogue.conflicting`).  Nothing falls outside and nothing is
    counted twice.
    """
    grouped: dict[tuple[tuple[str, str], ...], list[Stated]] = {}
    every: list[Stated] = []
    for position in states(bundle_dir, documents):
        every.append(position)
        grouped.setdefault(position.identity, []).append(position)

    entries: dict[tuple[tuple[str, str], ...], Entry] = {}
    untitled: list[tuple[Stated, ...]] = []
    conflicting: list[Conflict] = []
    restated: list[tuple[Stated, ...]] = []
    for key, group in grouped.items():
        if len(group) < 2:
            continue
        if len({p.document for p in group}) == 1:
            restated.append(tuple(group))
            continue
        stated_titles = titles(group)
        if not stated_titles:
            untitled.append(tuple(group))
            continue
        if len(stated_titles) > 1:
            conflicting.append(
                Conflict(key, tuple(sorted(stated_titles)), tuple(group))
            )
            continue
        title = next(iter(stated_titles))
        # The NAMING position is the one the title is stated at, and its member order is
        # the entry's: §3a derives the name from the bundle, so the document that names
        # the concept is the one whose spelling of it the entry carries.
        naming = next(p for p in group if p.title == title)
        entries[key] = Entry(
            identity=key,
            members=naming.members,
            kind=KIND[type(naming.members[0])],
            title=title,
            positions=tuple(group),
        )
    return Catalogue(
        entries=entries,
        untitled=tuple(untitled),
        conflicting=tuple(conflicting),
        restated=tuple(restated),
        positions=tuple(every),
    )
