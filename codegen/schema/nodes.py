"""The node kinds: one frozen dataclass per row of ``docs/plan/architecture.md`` §4.

A node is a **typed representation of a schema node, not the raw mapping**.  Each
kind carries exactly the keywords its kind can consume, already validated for shape
by :mod:`codegen.schema.parse`, and every node carries the four facts §4 names:

``pointer``
    the JSON Pointer of the node inside its document.
``position``
    the one of §3's nine positions the node is reached at.  **A field, never
    recovered from a pointer string** -- §6: "the parser assigned it from the
    structural keyword it descended through, so a handler never derives position
    from a pointer string, and the one place that did (``enum.resolves_no_name``
    reading ``hops[-2]``) becomes ``node.position is BRANCH``."
``applied``
    the type word an enclosing node asserts about the SAME instance, read by the
    rule ``adcp.types._base.applied_schema`` already states.  This is what
    ``compiler.Module.object_constrained`` was: a per-document set of pointers, read
    back per node.  Carried on the node, it is a fact about the node.
``annotations``
    every key the screen admitted and this kind does not consume -- ``title``,
    ``description``, ``default``, ``deprecated``, ``examples``, ``$comment``,
    ``$schema``, ``notes``, ``enumMetadata``, the admitted ``x-`` keys, and the
    definition sections.  One carrier, so a handler asking for a description does
    not read a mapping.

**``pointer`` and ``position`` are EXCLUDED from equality**, so two nodes are equal
exactly when they state the same thing about an instance -- which is §4's content
dedup read off the type system rather than off a JSON serialisation with a position
bit appended (``emit.content_key``, deleted).  Everything else a node carries IS
compared, including :attr:`Base.annotations` and :attr:`Base.applied`: a node
differing only in a ``$comment`` states a different thing to a reader, and a node
whose enclosing type word differs decides differently, which is the bit the old key
appended by hand.

**NO NODE CARRIES THE MAPPING IT WAS PARSED FROM.**  §14 step 5's staging allowed one
during the conversion -- "a node may carry its originating mapping ... the step is not
complete until that carrier is deleted" -- and it is deleted: ``Base.raw`` is gone and
with it ``emit.content_key``, the JSON serialisation the content dedup was keyed on.
A handler reads node fields.

What remains is a handful of readings the design keeps at the DECLARATION level, each
with its own typed carrier and each citing the decision that admits it -- and **the
carriers are :data:`RAW_CARRIERS`, below, rather than a list in this paragraph.**  One
place, because the list and the guard holding it have to agree BY DERIVATION: a list
kept in step by hand is how a census goes stale, and three such lists had already come
apart.  Measured: this module's prose named four carriers, ``parse.py``'s named four,
``tests/test_import_rule.py``'s named the same four as this one, and the two distinct
lists OVERLAP IN TWO -- six between them, against nine the parse actually builds.  So
the declaration carries the kind, the field and the sentence, and the test reads both
halves off it.

**The guard finds a carrier by what it HOLDS, not by what it is called.**  It is a
field holding, by identity, a mapping the document states at a SCHEMA POSITION --
``bundle.nodes_at``, the one declaration of what a schema position is, which the
document censuses and the reference inliner already read -- and the test asserts that
measured set EQUALS :data:`RAW_CARRIERS`'s keys.  Equality in both directions: a carrier
under ANY name is caught, and a declared carrier that stops carrying is caught too, so
the clause cannot go green by over-deletion.  The guard used to grep for the field name
``raw``, and under that reading a ``Union`` field holding four of the document's own
subtrees for no reader at all was invisible to it -- that field is deleted, not excepted,
because nothing read it and every one of its four keys has a typed carrier
(``adcp-client-python-3be.9``).

``tests/test_import_rule.py`` is where "nothing else reads a mapping" is held.

**Why frozen dataclasses and not a class hierarchy with a ``lower`` method.**  §2:
the kinds are closed (draft-07 fixes them and §4's table lists every one) and the
operation is one (a node is lowered).  A sum type plus one exhaustive match states
that in one place and the type checker proves the match total; a method per class
spreads one function over the files that read JSON and drags the IR and the keyword
table into them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from codegen.keywords import Position

#: The scalar type words and the Python type each one names.  ``docs/plan``'s §5
#: ``type`` row: "a scalar word -> ``str`` / ``int`` / ``float`` / ``bool``".
SCALAR = {"string": "str", "integer": "int", "number": "float", "boolean": "bool"}


@dataclass(frozen=True, kw_only=True)
class Base:
    """What every node carries, whatever its kind.

    ``kw_only`` throughout, so a kind's own fields need no defaults to sit after
    these and a reader of a construction sees which fact each argument is.
    """

    #: The bundle-relative path of the document the node is in.
    document: str
    #: The node's JSON Pointer.  Excluded from equality: see the module docstring.
    pointer: str = field(compare=False)
    #: One of §3's nine positions.  Excluded from equality for ``pointer``'s reason.
    position: Position = field(compare=False)
    #: The type word an enclosing node asserts about the same instance, or ``None``.
    applied: str | None = None
    #: Every admitted key this kind does not consume.
    annotations: Mapping[str, Any] = field(default_factory=dict)
    #: The rule sources this node carries: ``keyword -> the raw value``, for the
    #: keywords whose cell at this position compiles to a RULE.  ``lower/rules.py``
    #: is the only reader (§4).
    rules: Mapping[str, Any] = field(default_factory=dict)
    #: Every key this node STATES about an instance, sorted: ``keywords.declares`` at
    #: this node's own position, which is precisely the set §3's admission reader can
    #: refuse on -- a key with no row, or a lowering cell the kind's
    #: handler does not claim.  Names only and no values, because that is all the screen
    #: reads; a key that annotates without constraining is in :attr:`annotations`
    #: instead.  ``compiler.check_keywords`` and ``intersect.declaring``'s callers read
    #: this, so the screen is a reader of the node and of the table and of nothing else.
    declares: tuple[str, ...] = ()
    #: The keys in the ``x-`` namespace with no row in §6, sorted: admitted by the prefix
    #: alone and carried nowhere, which the screen REPORTS (§3, and the prefix rule once
    #: dropped ``x-enum-descriptions`` silently).  Kept apart from :attr:`declares`
    #: because the screen's answer for one is a line and for the other a refusal.
    extensions: tuple[str, ...] = ()
    #: The SHAPE faults §4 gives the parser -- "it validates shape: ``required`` is a
    #: list of names, ``properties`` is a mapping of schemas, ``items`` is one schema and
    #: not a list, and so on, each failure a VERDICT refusal because a malformed document
    #: is a property of the document" -- keyed by the keyword each one is about, with the
    #: detail as its value.  The kind's handler raises the one its own check raised
    #: before, at the same point in its own order, so the report stays a function of the
    #: document.  Excluded from equality: a node with a fault is refused.
    faults: Mapping[str, str] = field(default_factory=dict, compare=False)
    #: The property DECLARATIONS this node states, as the document wrote them.  The one
    #: declaration-level carrier the design keeps beside the typed one, for the two
    #: readers §6 names: §2's intersection rule, which merges two declarations of one
    #: property (:class:`compiler.Shape`), and D6's ``uniqueItems`` claim, which reads a
    #: property's array one level down (``lower.rules._distinct``).
    declared: Mapping[str, Any] = field(default_factory=dict)
    #: ``additionalProperties`` as the document states it: ``False``, ``True`` or the
    #: typed schema.  ``None`` where the document is silent, which §2 reads as ``ignore``
    #: -- absent and ``true`` are different statements, and ``"additionalProperties" in
    #: declares`` is how "stated at all" is asked.
    extra: Any = None

    @property
    def description(self) -> str | None:
        """The node's own ``description``, where it states one that renders."""
        text = self.annotations.get("description")
        return text if isinstance(text, str) and text else None

    @property
    def title(self) -> str | None:
        """The node's own ``title``, where it states one."""
        text = self.annotations.get("title")
        return text if isinstance(text, str) and text else None


# --------------------------------------------------------------------------- #
# §4's table, one dataclass per row
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, kw_only=True)
class Reference(Base):
    """Selected by ``$ref``: the document half, the pointer half, the siblings.

    :attr:`inert` is §5's ``$ref`` row as the design owner settled it: "a
    CONSTRAINING sibling -> nothing, and REPORTED: draft-07 ignores every sibling of
    ``$ref``, so the keyword constrains no instance and the document's accepted set
    is the target's alone."  The parser decides the co-occurrence (§4) and names the
    siblings here; the handler reports them and lowers the reference alone.  An
    ANNOTATION sibling is not here -- it is in :attr:`Base.annotations`, and §5 gives
    it the other answer: the sibling's description wins.
    """

    #: The whole ``$ref`` string, for the binder and for a refusal's detail.
    uri: str
    #: The document half of the URI; empty for a LOCAL reference.
    head: str
    #: The pointer half, ``""`` for a reference naming a root.
    into: str
    #: The CONSTRAINING siblings, sorted.  Compiles to nothing and is reported.
    inert: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class Enumeration(Base):
    """Selected by ``enum``: the members, their descriptions, the applied word."""

    members: tuple[Any, ...]
    #: ``str(value) -> text``, read from either spelling of the keyword (§6: "two
    #: spellings of one keyword; both are read").
    descriptions: Mapping[str, Any] = field(default_factory=dict)
    #: The ``type`` word the node states, where it states one.  The BASE is read off
    #: the members and not off this, which is what admits the typeless enum nodes.
    word: Any = None
    #: :class:`Constant`'s field, for :class:`Constant`'s reason: a CLOSED value set
    #: decides every constraint of its own instance, member by member, so the ``enum``
    #: row answers a ``pattern`` beside the members by asking whether the members
    #: satisfy it.  Read by the same one derivation (``parse.value_facts``).
    facts: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class Constant(Base):
    """Selected by ``const``: the value it pins, and the constraints that value decides.

    :attr:`facts` is :class:`Scalar`'s field, read by the same one derivation
    (``parse.value_facts``), and it is here because a one-member value set DECIDES every
    constraint of its own instance: ``{v}`` intersected with any non-descending
    constraint is either ``{v}`` or empty, so the ``const`` row answers a ``pattern``, a
    ``minLength`` or a ``minimum`` beside the pin by asking whether the pin satisfies it
    -- which is exactly what the row already did with the node's own ``type`` word.  A
    node carries no mapping (see the module docstring), so the VALUES the row validates
    against travel as a field like every other fact.

    :attr:`format` is :class:`Scalar`'s field for :class:`Scalar`'s reason, and it is NOT
    one of :attr:`facts`: ``parse.value_facts`` excludes ``format`` because "the kind
    consumes it in a field of its own", and a kind that can state one needs the field to
    consume it in.  It is a separate field rather than a fact because the two get
    different answers from the ``const`` row -- a fact is DECIDED by the pin and then
    dropped, a ``format`` RIDES on the annotation (§5's ``format`` row: "Otherwise rides
    as ``json_schema_extra={"format": …}`` on the field") -- so a ``format`` folded into
    ``facts`` would be dropped by the row that validates them away.
    """

    value: Any
    word: Any = None
    facts: Mapping[str, Any] = field(default_factory=dict)
    format: str | None = None


@dataclass(frozen=True, kw_only=True)
class Conjunct:
    """One ``allOf`` member, at CONJ, as the declaration the merge rule reads.

    Not a :class:`Base`: §2's intersection rule merges DECLARATIONS and hands the
    merged one back to the parser, so a conjunct is read as a declaration and the
    node it becomes is the composed node.  The pointer travels with it, so a refusal
    inside a conjunct names the conjunct's own node.

    **:attr:`pointer` is EXCLUDED from equality, for the reason :attr:`Base.pointer` is**
    (2026-10-26, found by the dedup check grading §4's equality).  It compared, and that
    made two :class:`Composition` nodes whose conjunct DECLARATIONS are identical unequal
    whenever the two sit at different pointers -- while ``emit.content_key``, the function
    the collapse is actually keyed on, called them one node and collapsed them.  Two
    instruments disagreeing about whether two nodes are identical is §9's own open
    question, and the module docstring above already decides which way: "``pointer`` and
    ``position`` are EXCLUDED from equality, so two nodes are equal exactly when they
    state the same thing about an instance."  A conjunct's pointer is where it sits, not
    something it states about an instance.  Excluding it costs the refusal nothing -- a
    refusal READS the field, it does not compare it.
    """

    pointer: str = field(compare=False)
    #: The conjunct AS STATED, which is not always a schema: ``allOf: [3]`` is a
    #: malformed document and the ``allOf`` row refuses it by name, so the entry travels
    #: as the document wrote it and the conjunct list stays aligned with the pointers.
    raw: Any


@dataclass(frozen=True, kw_only=True)
class Composition(Base):
    """Selected by ``allOf``: conjuncts at CONJ, own fields, extra policy, rules.

    The node's own ``properties`` are :attr:`Base.declared` and its
    ``additionalProperties`` is :attr:`Base.extra`, which is where every kind that can
    state one carries it.
    """

    conjuncts: tuple[Conjunct, ...]
    required: tuple[str, ...] = ()
    #: **The ``contains`` predicate this node states BESIDE its conjunct list**, as the
    #: document states it, and ``None`` where it states none.
    #:
    #: §5's ``$ref`` row at CONJ says the siblings count -- "the target is this node's own
    #: TYPE, and the other conjuncts **and the ``allOf``'s siblings** constrain it" -- and
    #: §5's "Two ARRAY declarations under one ``allOf``" (decided 2026-10-29) is what
    #: brings a ``contains`` here: §2's intersection spells the composition of a bare
    #: ``$ref`` base with an array restatement as ``{**child, "allOf": […, base]}``, so a
    #: restatement whose whole content is a ``contains`` arrives as a conjunct list with
    #: that keyword beside it.
    #:
    #: :attr:`Array.contains` is the precedent and the shape is deliberately the same: a
    #: kind that claims the node before :func:`parse`'s ``allOf`` arm -- or, here, BY that
    #: arm -- carries the keyword its handler is the one reader of.  The module docstring's
    #: rule is that no node carries the mapping it was PARSED FROM; a typed field holding
    #: one subschema is the answer that rule points to, which is what
    #: :attr:`Array.contains` and :attr:`Base.rules` already are.
    #:
    #: Measured over the 1,054 portable documents: **1 node**,
    #: ``core/signal-coverage-forecast.json`` at
    #: ``/properties/points/items/allOf/1/properties/dimensions``, whose restatement is a
    #: bare ``{"contains": {...}}`` over ``core/forecast-point.json``'s ``{"$ref":
    #: core/forecast-point-dimensions.json}``.  0 nodes state one in the bundle's own
    #: text, so every node reaching this field is one §2's intersection rule composed.
    contains: Any = None
    #: **The VALUE constraints this node states BESIDE its conjunct list**, in the
    #: document's own spelling, by the same classification every value-carrying kind's
    #: facts take (``parse.value_facts``) -- less the keys that are RULE sources at this
    #: position, which :attr:`Base.rules` already carries and ``lower.rules`` is the one
    #: reader of.
    #:
    #: §5's ``$ref`` row at CONJ is what reads them: "the target is this node's own TYPE,
    #: and the other conjuncts **and the ``allOf``'s siblings** constrain it, which is
    #: §2's intersection at a node that declares no fields of its own", and §5's group (a)
    #: names the sentence's unwritten half -- "the refusals reading '*X* is not a class, so
    #: it cannot be a base' are the unimplemented half of that sentence".  A bound stated
    #: beside the ``allOf`` is one of those siblings, so it constrains the type the
    #: conjuncts supply; a node whose conjuncts are all class BASES has no such type and
    #: ``lower.composition.lower_composition`` refuses there, exactly as it does for a ``contains``
    #: and for a value set.
    #:
    #: :attr:`contains` is the precedent and the arrangement is deliberately the same: the
    #: arm that claims the node carries the siblings its handler is the one reader of.
    #:
    #: Measured over the 1,054 portable documents, on the documents' own text: **12
    #: composing nodes state a key of this classification beside an ``allOf``, and 2 of
    #: them reach this field** -- ``core/catalog-selection.json`` at ``/properties/query``
    #: (``minLength: 1`` over a ``$ref`` to a string) and
    #: ``trusted-match/context-match-response.json`` at
    #: ``/properties/signals_by_provider/additionalProperties/properties/targeting_kvs``
    #: (``minItems: 1`` over a local ``$ref`` to an array).  Of the other 10, 4 state
    #: ``type: array`` and are claimed by the array kind before the ``allOf`` arm
    #: (``adcp-client-python-10l.64``), and 6 state only a key that is a RULE here --
    #: ``uniqueItems``, ``minProperties``, ``maxProperties``.
    facts: Mapping[str, Any] = field(default_factory=dict)
    word: Any = None


#: **The keywords a ROOT states beside a combinator that compile onto the union's BASE**,
#: in the order a root carrying them is REPORTED on.  §4 of the semantics document: "every
#: keyword beside the combinator compiles onto the base, and every branch inherits it."
#:
#: Declared here, beside the kind whose root states them, because it was
#: written twice -- once in ``schema/parse.py`` and once as
#: ``lower.union.ROOT_CONJUNCTS`` -- and the two had to agree about the ORDER as well as
#: the membership (``adcp-client-python-3be.8``).  The order is load-bearing and
#: ``ROOT_CONJUNCTS``' own comment says why: "FIRST in the tuple, so the keyword each of
#: those documents is reported on does not move: ``allOf`` is the structural fact (the
#: document composes) where the other three are the root's own inline facts."
#:
#: **Not a cell of ``keywords.py``**, and the test of that is §3's own: the table is keyed
#: by keyword × POSITION, and "beside a union" is a CO-OCCURRENCE rather than a position --
#: which §3 says "belongs to the sentence of the cell it qualifies", and each of the four
#: cells at ROOT states its own clause for it.  So the sentence is in the table and the
#: four names are the SHAPE the parser builds, which is this layer's.
#: ``tests/test_keywords.py`` holds the four against those cells.
ROOT_SIBLINGS: tuple[str, ...] = ("allOf", "properties", "required", "additionalProperties")


@dataclass(frozen=True, kw_only=True)
class Union(Base):
    """Selected by ``oneOf``/``anyOf`` whose branches are shapes.

    :attr:`branches` are parsed at BRANCH, so a branch's own kind is what the handler
    dispatches on rather than a second reading of its keys.

    **The keywords stated BESIDE the combinator have one carrier each, and no carrier for
    the lot.**  §4 of the semantics document -- "every keyword beside the combinator
    compiles onto the base, and every branch inherits it" -- used to arrive here as a
    ``siblings`` mapping holding four of them AS THE DOCUMENT STATES THEM.  Each is a
    field: :attr:`conjuncts` is the ``allOf`` (§5's ``allOf`` row beside a union, "the
    same, onto the base"), :attr:`Base.declared` the ``properties``, :attr:`required` the
    ``required``, :attr:`Base.extra` the ``additionalProperties``.  The mapping was a
    fifth reading of those four and **nothing in ``codegen/`` read it**:
    ``lower.composition.lower_composition`` took the conjunct list off :attr:`conjuncts` the day
    the parser built it (``adcp-client-python-10l.37``) and the other three were never
    read out of it at all.  So it carried the document's own subtrees for no reader, and
    ``adcp-client-python-3be.9`` deleted it on that measurement -- the guard that should
    have caught it grepped for the field name ``raw``, and is :data:`RAW_CARRIERS`'s
    derived equality now.

    **The union knows its own position and TELLS its branches** (§6, settled
    2026-10-26): a branch of a ROOT union is a class whatever it states, because §4 of
    the semantics document emits one class per branch, so the branches of a root union
    are parsed ``objectish`` and ``lower.enum.resolves_no_name`` is HANDED "of a root
    union" rather than reconstructing it from a pointer.  A child never reconstructs its
    parent.

    **THE COMBINATOR IS NOT ALWAYS AT THIS NODE'S OWN POINTER** (§5's
    ``oneOf``/``anyOf`` row at CONJ, ``adcp-client-python-10l.37``).  Draft-07 applies an
    ``allOf`` conjunct to the SAME instance the node describes -- which is what
    :func:`codegen.schema.parse.applies_to_one_instance` already reads for §4's
    disjointness derivation -- so a conjunct stating a combinator of shapes states it
    about this node, and §5's cell answers "CONJ -> one class per branch over the
    composed bases".  :attr:`stated_at` is where the keyword sits and :attr:`conjuncts`
    is the conjunct list MINUS the one that carries it, each at the index the document
    gives it, so the branch pointers and the remaining conjuncts' pointers are both the
    document's own.
    """

    combinator: str
    #: The pointer of the node that STATES :attr:`combinator` -- this node's own, or the
    #: ``allOf`` conjunct that carries it.  A FIELD and not a reading of the branch
    #: pointers, because a refusal about the keyword has to name the pointer the document
    #: states it at and the parser is the one layer that saw where that was.
    stated_at: str = ""
    #: The ``allOf`` conjuncts that contribute to the COMPOSED class, each at the pointer
    #: the document gives it.  Built HERE, by the one layer that saw the document, rather
    #: than re-derived by the handler out of the keyword list: the conjunct carrying the
    #: branch list contributes nothing to the composition -- the branches are
    #: :attr:`branches` -- and dropping it from the list without keeping the indices would
    #: re-point every conjunct after it.
    conjuncts: tuple[Conjunct, ...] = ()
    #: Every branch, parsed at BRANCH, in document order -- including one that is not a
    #: schema, which parses to :class:`Typeless` and whose own declaration below is what
    #: the ``oneOf``/``anyOf`` row refuses it by.  Aligned 1:1 with :attr:`branch_raw`,
    #: because §4's dispatch derivation and §4 "Names" index the two together.
    branches: tuple[Node, ...] = ()
    #: The branch declarations, in document order, for the readings §4 "Names" and
    #: §4's dispatch derivation make over a branch's own property map -- a branch's
    #: ``const`` pin, its ``required`` set, its title.  §6 keeps those readings at the
    #: declaration level, which is why this is the one carrier beside the parsed nodes.
    branch_raw: tuple[Any, ...] = ()
    #: **§4's SECOND dispatch source, read by the parser because the classification is
    #: the parser's**: one presence CLAUSE per branch -- the groups it requires and the
    #: groups it forbids -- where the branches differ only in which keys are present and
    #: a base plus children expresses that (``parse.presence_branches``, the owner's
    #: correction of 2026-11-07, ``adcp-client-python-j0fr``).  Empty at every union
    #: whose branches are shapes, which is every union of this bundle but 8.
    #:
    #: Aligned 1:1 with :attr:`branch_raw` and :attr:`branches` where it is non-empty,
    #: and that alignment is what the lowering pairs a clause with a branch CLASS by.
    #:
    #: **A FIELD and not a second reading of :attr:`branch_raw` in the lowering**, for
    #: §11's reason and for a measured one.  The reading is position-dependent --
    #: ``schema.presence_clause`` asks ``keywords.declares`` at the position asked about
    #: -- and the position this node was classified at is not recoverable from a branch
    #: declaration alone, so a lowering re-reading the branches would have to pick one
    #: and could pick a different one from the predicate that routed the node here.  The
    #: same predicate's answer travels instead, which is :attr:`branches`' own
    #: arrangement one axis over: the union knows a thing about its branches and TELLS
    #: them rather than having it reconstructed.
    presence: tuple[Any, ...] = ()
    #: The node's own ``required``, in the document's own order.  A field of its own and
    #: never read back out of the keyword mapping ``siblings`` was, for the reason
    #: :attr:`Base.declared` and :attr:`Base.extra` are fields too: §5's ``required``
    #: row at ROOT beside a union is "required on the base's fields, and the names
    #: recorded in ``_ROOT_REQUIRED``", and the reader of that is
    #: ``lower.composition.lower_composition``, which takes this field off every kind that can
    #: state one (:attr:`Composition.required`, :attr:`Object.required`).  So one
    #: spelling serves the three kinds, and :attr:`conjuncts` carries what is left of
    #: §4's "every keyword beside the combinator".
    required: tuple[str, ...] = ()
    #: The node's own ``type`` word, where it states one.  §4 of the semantics document
    #: makes a root ``type`` an assertion about the same instance every branch sees, so
    #: this is what a branch stating none of its own inherits (``lower.union``'s applied
    #: reading, which is ``_base.applied_schema``'s rule at one hop).
    word: Any = None


@dataclass(frozen=True, kw_only=True)
class Object(Base):
    """``type: object`` (stated or applied) with ``properties``.

    :attr:`properties` holds the CHILD NODES, parsed at PROP, in the document's own
    key order.  :attr:`extras` is ``additionalProperties`` read ONCE, here, as the
    typed value schema §5 says a typed one is -- which is the second of §2's three
    node rewrites, retired: ``lower.objects.declare_object`` built a synthetic
    ``{"type": "object", "additionalProperties": ap, ...}`` mapping and handed it to
    the dispatch, which is a node the document does not have.  :attr:`key` is
    ``propertyNames`` at KEY, read once here for the same reason.
    """

    properties: Mapping[str, Node]
    required: tuple[str, ...] = ()
    #: The VALUE schema of a typed ``additionalProperties``, parsed at MAPV.  ``None``
    #: for ``false``, ``true``, the empty schema and silence.
    extras: Node | None = None
    #: ``propertyNames``, parsed at KEY.  A class with declared ``properties``
    #: carries it nowhere (§5), so this is what the check reads.
    key: Node | None = None
    word: Any = None


@dataclass(frozen=True, kw_only=True)
class Mapping_(Base):
    """``type: object`` without ``properties``: ``dict[K, V]``.

    Named with a trailing underscore because ``collections.abc.Mapping`` is the
    annotation every node field uses; ``nodes.Mapping_`` is the kind and §4's table
    calls it ``Mapping``.

    :attr:`key` is the first of §2's three node rewrites, retired: the key schema was
    given a ``type`` word and handed back to the dispatch as if the document stated
    one.  The parser supplies the word ONCE, at KEY -- ``propertyNames`` applies to a
    key and a JSON key is a string -- and §9's "never refuse a keyword the walk
    itself inserted" is why that reading is the parser's and not a handler's.
    """

    #: The value schema, parsed at MAPV.  ``None`` for ``true`` and the empty schema,
    #: which §5 says IS ``true``: the value is ``Any``.
    value: Node | None = None
    #: The key schema, parsed at KEY.  ``None`` where the document says nothing about
    #: keys, which is a reading and not a default: the key is every string.
    key: Node | None = None
    #: The ``patternProperties`` expression, where the mapping is spelled that way.
    pattern: str | None = None
    #: ``patternProperties`` AS THE DOCUMENT STATES IT, the way :attr:`Base.extra` carries
    #: ``additionalProperties``.  ``None`` where the document states the keyword not at
    #: all.  It exists because §5(b)'s widening declares the keyword and §9 requires the
    #: declared fact to be the DOCUMENT's own spelling -- "an approximation must name
    #: something the document states, or the document is blamed for the compiler's own
    #: rewriting" -- and the expression alone is a projection of that value, not the
    #: value.  Recorded by the parser, which already read it, so no handler re-reads a
    #: raw mapping for it.
    patterned: Mapping[str, Any] | None = None
    #: How many ``patternProperties`` entries the node states: ``None`` where it states
    #: the keyword not at all, ``-1`` where the value is not a mapping, and the count
    #: otherwise.  §5 gives a mapping ONE key type, so anything but a single entry
    #: refuses -- and the refusal has to say how many it found.
    patterns: int | None = None
    #: ``minProperties``/``maxProperties``: how many keys the mapping may carry.
    bounds: Mapping[str, Any] = field(default_factory=dict)
    word: Any = None


@dataclass(frozen=True, kw_only=True)
class Array(Base):
    """``type: array``: the element at ELEM, the bounds, distinct, contains.

    :attr:`distinct` is the third of §2's three node rewrites, retired on the array
    side: ``lower.objects.fields`` stripped ``uniqueItems`` off a property's declaration
    before the array row saw it, so the array was decided from a mapping the document
    does not state.  The fact is read once, here, and the class holding the array
    reads it off the node.
    """

    #: The element schema, parsed at ELEM.  ``None`` for ``{"type": "array"}``, which
    #: admits a list of anything.
    element: Node | None = None
    #: ``minItems``/``maxItems``: the LIST's own bound, never its elements'.
    bounds: Mapping[str, Any] = field(default_factory=dict)
    #: ``uniqueItems: true``.  §5 puts the rule on the class holding the array.
    distinct: bool = False
    #: The ``contains`` predicate, as the document states it.
    contains: Any = None
    #: The ``allOf`` conjuncts, at CONJ, where the node states a ``type`` word of its
    #: own that is not ``object``.  §5's ``$ref`` row at CONJ names **a container**
    #: among the targets that are not a class a model can extend -- "the target is this
    #: node's own TYPE, and the other conjuncts and the ``allOf``'s siblings constrain
    #: it, which is §2's intersection at a node that declares no fields of its own" --
    #: and an array stating its own ``items`` is that clause with the type read off the
    #: node's own word instead of off a reference.  So the array is the TYPE and the
    #: conjuncts constrain it, which is what ``lower.containers.array`` reads them as:
    #: rules, declared where §2 declares a rule over a value.
    #:
    #: Carried the way :attr:`Union.conjuncts` carries the same keyword for the same
    #: reason -- a kind that claims the node before ``parse``'s ``allOf`` arm has to
    #: carry the conjunct list, and its handler is the one reader of it.  Empty for
    #: every array that states no ``allOf``, which is all but 4 of the bundle's.
    conjuncts: tuple[Conjunct, ...] = ()
    word: Any = None


@dataclass(frozen=True, kw_only=True)
class Scalar(Base):
    """One scalar type word: the constraint facts in the document's spelling.

    :attr:`facts` is what ``ir.FACTS`` was -- a keyword tuple §11 says should be
    derived and which §3's columns cannot answer, because a cell's ``effect`` is TYPE
    for ``type``, ``enum``, ``const`` and ``format`` as well and ``uniqueItems`` is
    RULE.  The parser classifies a node's keys from the table AT ITS POSITION and the
    node carries its own facts, which is what the tuple is replaced by: a fact here is
    a key whose cell LOWERS at this position and that the kind does not otherwise
    consume.
    """

    word: str
    facts: Mapping[str, Any] = field(default_factory=dict)
    format: str | None = None


@dataclass(frozen=True, kw_only=True)
class MultiType(Base):
    """A ``type`` LIST: one member per word, each holding only what that word carries.

    :attr:`members` is the second of §2's three node rewrites, retired: the walk cut
    the node into one mapping per type word and handed each back to the dispatch.  The
    cut is a reading the parser makes ONCE, at the position that implies it, and each
    member is a node of its own kind -- which is draft-07's own semantics, since a
    constraint keyword applies to instances of the type it is defined for and is
    ignored for every other type.
    """

    #: The ``type`` list AS STATED, which is not always a set of type names: an empty
    #: list, a repeated word and a non-string entry are each a malformed document and
    #: the row refuses them by name, so the list travels as the document wrote it.
    words: tuple[Any, ...]
    #: One member per entry that IS a type name, in document order; equal in length to
    #: :attr:`words` exactly when every entry is one, which is the only case the row
    #: reaches the members at all.
    members: tuple[Node, ...]


@dataclass(frozen=True, kw_only=True)
class Null(Base):
    """``type: null``: nothing."""


@dataclass(frozen=True, kw_only=True)
class Typeless(Base):
    """No type and no kind keyword: a ``not`` over a value, or nothing.

    :attr:`facts` is :class:`Scalar`'s field, read by the same one derivation
    (``parse.value_facts``), and the kind needs it for the OPPOSITE reason the value-set
    kinds do.  A ``const`` carries its facts so the PIN can decide them; a typeless node
    carries them because nothing can decide them -- §5's ``type`` row makes this node
    ``Any``, §2 binds a constraint to the type, and ``Any`` is no type to bind to.  So
    the row's answer is §2's ladder, and a widening is DECLARED with the fact the
    document states: ``approximate.declare`` takes that value, and §9 forbids
    approximating on anything but the document's own (``codegen.lower.scalars.typeless``).
    Without the field the row would have the keyword's NAME off :attr:`Base.declares` and
    not its value, and a declaration naming no fact is one §8 cannot grade.
    """

    facts: Mapping[str, Any] = field(default_factory=dict)


#: **The closed sum.**  §5's dispatch is an exhaustive ``match`` over exactly these,
#: and ``assert_never`` is what makes the type checker refuse a kind the match does
#: not cover.  Written here, beside the kinds, so the dispatch has one declaration of
#: what it must cover.
Node = (
    Reference
    | Enumeration
    | Constant
    | Composition
    | Union
    | Object
    | Mapping_
    | Array
    | Scalar
    | MultiType
    | Null
    | Typeless
)


#: **Every field of a kind above that holds a mapping the document states at a SCHEMA
#: POSITION, with the decision that admits each one.**  The module docstring's rule is
#: that no node carries the mapping it was parsed from; this is the whole of what the
#: design keeps at the DECLARATION level instead, written beside the kinds for the reason
#: :data:`Node` is -- one declaration, so the rule and the guard that holds it cannot come
#: apart.  ``tests/test_import_rule.py`` asserts the MEASURED set of such fields equals
#: these keys, in both directions, and that every sentence here cites a section.
#:
#: Keyed by the class that DECLARES the field, so a reading shared by every kind is one
#: entry: :class:`Base`'s four are on every node of §4's table.  This mapping may shrink
#: and may not grow without a sentence, and an entry whose field stops carrying is as red
#: as a field that starts -- the equality is what makes "``Conjunct.raw`` is asserted
#: PRESENT" true of all nine rather than of the one it was written for.
RAW_CARRIERS: Mapping[tuple[type, str], str] = {
    (Base, "annotations"): (
        "A ``definitions`` / ``$defs`` section rides here raw.  §5: \"Nothing by itself: "
        "a bag of named subschemas.  Each entry is declared on demand when a ``$ref`` "
        "names it\" -- so an entry is parsed by a re-entrant call at DEF, and \"an entry "
        "nothing references is not declared\" means no traversal reaches the rest at all.  "
        "One carrier for every key the screen admitted and the kind does not consume, so "
        "a handler asking for a description does not read a mapping."
    ),
    (Base, "declared"): (
        "§6 keeps ``restatement``, ``intersection`` and ``at_least_as_tight`` as pure "
        "functions over DECLARATIONS, because §2's intersection rule MERGES two "
        "declarations of one property and hands the merged declaration back to "
        ":func:`codegen.schema.parse.parse`: the result has to be parsed as one node, not "
        "composed out of two decided ones.  D6's ``uniqueItems`` claim is the second "
        "reader, one level down a property's array (``lower.rules._distinct``)."
    ),
    (Base, "extra"): (
        "``additionalProperties`` as the document STATES it, because §2 reads silence as "
        "``ignore`` and absent and ``true`` are different statements -- the typed schema "
        "is the one value of the three that is a subschema, and :attr:`Object.extras` is "
        "the node parsed from it at MAPV.  Both, because the policy and the value type "
        "are different facts and §5 gives them different answers."
    ),
    (Base, "rules"): (
        "The raw subschemas at RULE.  §4: \"a node at RULE is parsed like any other, kept "
        "on the enclosing node as a rule source, and is never handed to ``decide``\", and "
        "§3 of the semantics document says why -- under a conditional a keyword describes "
        "what a rule TESTS, so no type is lowered from it.  ``lower/rules.py`` is its only "
        "reader."
    ),
    (Conjunct, "raw"): (
        "A conjunct is a DECLARATION and not a node, by §2's intersection rule, which is "
        "the same sentence :attr:`Base.declared` carries: the merged declaration goes back "
        "to the parser.  And the entry is not always a schema -- ``allOf: [3]`` is a "
        "malformed document the ``allOf`` row refuses by name -- so it travels as the "
        "document wrote it and the conjunct list stays aligned with the pointers."
    ),
    (Union, "branch_raw"): (
        "§4 \"Names\"'s three rules and §4's dispatch derivation are readings of a "
        "branch's own DECLARATION: its title, its ``const`` pin, its ``required`` set.  §6 "
        "keeps those at the declaration level, which is why this is the one carrier beside "
        "the parsed branches, aligned 1:1 with them."
    ),
    (Array, "contains"): (
        "The ``contains`` predicate, as the document states it.  §5 makes the model state "
        "the PREDICATE and not a transcription of the subschema, so there is no type "
        "lowered from it and nothing to descend into -- which is why the parser builds no "
        "child here and the array's own handler is the one reader."
    ),
    (Composition, "contains"): (
        ":attr:`Array.contains`'s sentence at a composing node, by §5's \"Two ARRAY "
        "declarations under one ``allOf``\" (decided 2026-10-29): §2's intersection spells "
        "the composition of a bare ``$ref`` base with an array restatement as "
        "``{**child, \"allOf\": [..., base]}``, so a restatement whose whole content is a "
        "``contains`` arrives as a conjunct list with that keyword beside it.  0 nodes "
        "state one in the bundle's own text, so every node reaching the field is one §2's "
        "rule composed -- which is why the guard's population states one itself."
    ),
    (Mapping_, "patterned"): (
        "``patternProperties`` AS THE DOCUMENT STATES IT, the way :attr:`Base.extra` "
        "carries ``additionalProperties``: §5(b)'s widening DECLARES the keyword and §9 "
        "requires the declared fact to be the document's own spelling -- \"an "
        "approximation must name something the document states, or the document is blamed "
        "for the compiler's own rewriting\" -- and :attr:`Mapping_.pattern`, the "
        "expression alone, is a projection of that value and not the value."
    ),
}
