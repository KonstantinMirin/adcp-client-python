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

**:attr:`Base.raw` is the declaration the node was parsed from, and it is excluded
from equality too.**  Two readings are declaration-level by the design's own
decision and neither is a second reading of what a node IS:

* §6 keeps ``restatement``, ``intersection`` and ``at_least_as_tight`` as "pure
  functions over two nodes" -- section 2's intersection rule, which MERGES two
  declarations of one property and hands the merged declaration back to
  :func:`codegen.schema.parse.parse`.  The merge is over declarations because the
  result has to be parsed as one node, not composed out of two decided ones;
* ``lower/rules.py`` reads the rule sources a node carries (:attr:`Base.rules`),
  which are the raw subschemas at RULE -- §4: "a node at RULE is parsed like any
  other, kept on the enclosing node as a rule source, and is never handed to
  ``decide``".

Nothing else reads it, and ``tests/test_import_rule.py`` is where that is held.

**These kinds have no reader yet.**  ``schema/parse.py`` is what builds them and it
is the half of §14 step 5 row ``adcp-client-python-10l.5`` did not land; the package
docstring says why and on what precedent.  So this is a DECLARATION, in the layer §11
gives it, and every sentence below is the decision a reader will have to agree with
rather than a description of code that runs.

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
    #: The declaration this node was parsed from.  Excluded from equality; the two
    #: declaration-level readers are named in the module docstring.
    raw: Mapping[str, Any] = field(default_factory=dict, compare=False)

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


@dataclass(frozen=True, kw_only=True)
class Constant(Base):
    """Selected by ``const``: the value it pins."""

    value: Any
    word: Any = None


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
    raw: Mapping[str, Any]


@dataclass(frozen=True, kw_only=True)
class Composition(Base):
    """Selected by ``allOf``: conjuncts at CONJ, own fields, extra policy, rules."""

    conjuncts: tuple[Conjunct, ...]
    #: The node's OWN ``properties``, as declarations: the merge reads them.
    properties: Mapping[str, Any] = field(default_factory=dict)
    required: tuple[str, ...] = ()
    #: ``additionalProperties`` as the document states it.
    extra: Any = None
    word: Any = None


@dataclass(frozen=True, kw_only=True)
class Union(Base):
    """Selected by ``oneOf``/``anyOf`` whose branches are shapes.

    :attr:`branches` are parsed at BRANCH, so a branch's own kind is what the handler
    dispatches on rather than a second reading of its keys.  :attr:`siblings` is what
    the root states beside the combinator, which §5's union row compiles onto the
    base; the handler is the one reader of it.
    """

    combinator: str
    branches: tuple[Base, ...]
    #: The branch declarations, in document order, for the readings §4 "Names" and
    #: §4's dispatch derivation make over a branch's own property map.
    branch_raw: tuple[Mapping[str, Any], ...] = ()
    #: The keywords the root states beside the combinator, as the document states
    #: them: ``allOf``, ``properties``, ``required``, ``additionalProperties``.
    siblings: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class Object(Base):
    """``type: object`` (stated or applied) with ``properties``.

    :attr:`properties` holds the CHILD NODES, parsed at PROP, in the document's own
    key order.  :attr:`extras` is ``additionalProperties`` read ONCE, here, as the
    typed value schema §5 says a typed one is -- which is the second of §2's three
    node rewrites, retired: ``compiler.declare_object`` built a synthetic
    ``{"type": "object", "additionalProperties": ap, ...}`` mapping and handed it to
    the dispatch, which is a node the document does not have.  :attr:`key` is
    ``propertyNames`` at KEY, read once here for the same reason.
    """

    properties: Mapping[str, Base]
    required: tuple[str, ...] = ()
    #: ``additionalProperties`` as the document states it: ``False``, ``True`` or the
    #: typed schema.  ``None`` where the document is silent, which §2 reads as
    #: ``ignore`` -- absent and ``true`` are different statements.
    extra: Any = None
    #: The VALUE schema of a typed ``additionalProperties``, parsed at MAPV.  ``None``
    #: for ``false``, ``true``, the empty schema and silence.
    extras: Base | None = None
    #: ``propertyNames``, parsed at KEY.  A class with declared ``properties``
    #: carries it nowhere (§5), so this is what the check reads.
    key: Base | None = None
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
    value: Base | None = None
    #: The key schema, parsed at KEY.  ``None`` where the document says nothing about
    #: keys, which is a reading and not a default: the key is every string.
    key: Base | None = None
    #: The ``patternProperties`` expression, where the mapping is spelled that way.
    pattern: str | None = None
    #: ``additionalProperties`` as stated, for the refusals §5 decides beside it.
    extra: Any = None
    #: ``minProperties``/``maxProperties``: how many keys the mapping may carry.
    bounds: Mapping[str, Any] = field(default_factory=dict)
    word: Any = None


@dataclass(frozen=True, kw_only=True)
class Array(Base):
    """``type: array``: the element at ELEM, the bounds, distinct, contains.

    :attr:`distinct` is the third of §2's three node rewrites, retired on the array
    side: ``compiler.fields`` stripped ``uniqueItems`` off a property's declaration
    before the array row saw it, so the array was decided from a mapping the document
    does not state.  The fact is read once, here, and the class holding the array
    reads it off the node.
    """

    #: The element schema, parsed at ELEM.  ``None`` for ``{"type": "array"}``, which
    #: admits a list of anything.
    element: Base | None = None
    #: ``minItems``/``maxItems``: the LIST's own bound, never its elements'.
    bounds: Mapping[str, Any] = field(default_factory=dict)
    #: ``uniqueItems: true``.  §5 puts the rule on the class holding the array.
    distinct: bool = False
    #: The ``contains`` predicate, as the document states it.
    contains: Any = None
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

    words: tuple[str, ...]
    members: tuple[Base, ...]
    #: The keywords the node states that SOME arm carries, for the one refusal §5's
    #: own rows do not decide (a constrained arm beside another live arm).
    stated: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class Null(Base):
    """``type: null``: nothing."""


@dataclass(frozen=True, kw_only=True)
class Typeless(Base):
    """No type and no kind keyword: a ``not`` over a value, or nothing."""


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
