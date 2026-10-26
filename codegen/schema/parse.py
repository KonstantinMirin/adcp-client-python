"""**The ONE traversal of a raw mapping**, and the one place a node's KIND is decided.

``docs/plan/architecture.md`` §4: "``codegen/schema/parse.py`` is the one function that
reads a raw mapping."  §6: "The parser walks the raw document once and builds the whole
tree; after it, no layer walks a mapping.  ``decide`` recurses over the tree."  So this
module is handed a document's root mapping and returns the root :class:`~codegen.schema.nodes.Base`
of a tree whose children are nodes, each carrying its own POINTER, its own POSITION and
the type word an enclosing node applies to the same instance.

**What a node does NOT carry a child for, and why each one is a DECLARATION rather than
an omission.**  Four kinds of subschema stay as the document wrote them, and
``nodes.py`` declares all four:

* a subschema at RULE -- inside ``not``, ``if``, ``then`` or ``else`` -- is a rule SOURCE
  on the enclosing node (:attr:`nodes.Base.rules`).  §4: "A node at RULE is parsed like
  any other, kept on the enclosing node as a rule source, and is never handed to
  ``decide``", and §3 of the semantics document says why: under a conditional a keyword
  describes what a rule TESTS, so no type is lowered from it.  ``lower/rules.py`` is its
  only reader;
* a ``definitions`` / ``$defs`` section is in :attr:`nodes.Base.annotations`, raw.  §5:
  "Nothing by itself: a bag of named subschemas.  Each entry is declared on demand when a
  ``$ref`` names it" -- so an entry is parsed when a reference asks for it, by a
  re-entrant call to :func:`parse` at DEF, and "an entry nothing references is not
  declared" means no traversal reaches it at all;
* an ``allOf`` conjunct is a :class:`nodes.Conjunct`, which is a DECLARATION and not a
  node: §2's intersection rule MERGES two declarations of one property and hands the
  merged one back here to be parsed as one node, so a conjunct is read as a declaration
  and the node it becomes is the composed node;
* a ``contains`` predicate is :attr:`nodes.Array.contains`, as stated.  §5 makes the
  model state the PREDICATE and not a transcription of the subschema, so there is no
  type lowered from it and nothing to descend into.

Everything else is a child node: ``properties`` at PROP, ``items`` at ELEM,
``additionalProperties`` and the one ``patternProperties`` schema at MAPV,
``propertyNames`` at KEY, a combinator's branches at BRANCH.

**The three node rewrites §2 names are readings made HERE, once, at the position that
implies them.**  A handler never sees a mapping the document does not state:

* the key schema given a ``type`` word -- ``propertyNames`` applies to a KEY and a JSON
  key is a string, so :func:`_key` supplies the word at KEY and §9's "never refuse a
  keyword the walk itself inserted" is why that reading is the parser's;
* the extras store rebuilt as a mapping -- a typed ``additionalProperties`` on a class is
  the ``dict[K, V]`` §5 says a typed one is, and :attr:`nodes.Object.extras` is that
  mapping NODE, built here, where ``compiler.declare_object`` built a synthetic
  ``{"type": "object", "additionalProperties": ap, ...}`` and handed it to the dispatch;
* the multi-type cut -- one member per type word, each holding only the keywords that
  word can carry (:data:`ARM`), which is draft-07's own semantics.

**The screen and the classification INTERLEAVE, and §4 is where that is decided** (settled
2026-10-26, after this row found that the section's "four things … in this order" could not
be taken literally).  §4 now says it: three admission arms answer from
``cell(keyword, position)`` alone -- a key with no row, a REFUSE cell, a NOTHING cell -- and
run before anything is classified; the fourth cannot, because §3's reader ends "any other
effect is a fact the node's kind consumes" and whether a lowering effect is CLAIMED or is a
DEFERRAL is a question about which kind owns the node, so that arm runs after the
classification it depends on.  "A node is classified once and screened once, and the
dependency runs one way… Nothing is screened twice and no mapping is traversed twice, which
is what §4 is actually protecting."  :func:`parse` classifies, and the one screen pass over
``sorted(raw)`` answers all four arms in the order the cell and the kind make available.

**§14 STEP 5 IS COMPLETE AND ITS MIGRATION CARRIER IS DELETED.**  The step's end state
is "``parse`` is the only reader of a raw mapping, and a handler reads node fields", and
the step staged the conversion rather than softening it: "during this step a node may
carry its originating mapping, ``parse`` performs the one traversal, and each handler
converts to node fields one kind at a time -- each conversion its own commit, each
checked by the byte compare.  **The step is not complete until that carrier is
deleted.**"  ``nodes.Base.raw`` was that carrier and it is gone, along with
``emit.content_key``, the JSON serialisation the content dedup was keyed on.  All twelve
kinds take their node, and `lower/rules.py` plus §2's intersection rule are the only
readers left of a declaration -- each with a typed carrier ``nodes.py`` declares.

So this function refuses nothing and raises nothing, and the two things a kind's handler
needs in order to refuse are FIELDS:

* the ADMISSION SCREEN reads :attr:`nodes.Base.declares` -- ``keywords.declares`` at the
  node's own position, which is exactly the set §3's admission reader can refuse on --
  and :attr:`nodes.Base.extensions` for the ``x-`` keys it reports.  ``handled`` stays the
  caller's, which is the LOWERING reader §3 gives to ``lower/*``;
* the SHAPE VALIDATION is :attr:`nodes.Base.faults` for the one fault no field answers
  and a field everywhere else: an ``items`` that is not a schema is
  :attr:`nodes.Array.element` being ``None`` beside ``items`` in ``declares``, an
  ``enum`` that is not a list is :attr:`nodes.Enumeration.members` being empty, and a
  ``patternProperties`` with the wrong number of entries is
  :attr:`nodes.Mapping_.patterns`.  Each failure is a VERDICT, because a malformed
  document is a property of the document (§4), and the kind's handler raises it at the
  point its own check raised it -- so the report stays a function of the document and not
  of where the reading happens.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from codegen import bundle, keywords
from codegen.keywords import Position
from codegen.schema import nodes
from codegen.schema.nodes import SCALAR

#: The two combinator keywords, read off the descent column rather than named: they are
#: the keywords whose subschemas occupy a BRANCH, which is what a combinator IS.
#: ``keywords.combinators`` is the one reading and this is its value at any position (the
#: descent column does not vary by position).
UNION = tuple(
    k for k, p in keywords.descends_at(Position.ROOT).items() if p is Position.BRANCH
)

#: Which constraint keywords each ``type`` word can carry, for the multi-type cut.
#: draft-07 applies a constraint keyword only to an instance OF the type it is defined
#: for and ignores it for every other type, so a ``type`` LIST means "this keyword on
#: this arm" -- which is the reading :attr:`nodes.MultiType.members` is, made once here
#: rather than by a handler re-cutting the node.  Moved from ``lower/containers.py``
#: unchanged in substance: §2's third node rewrite is retired by MOVING the cut to the
#: parser, not by restating it.
_NUMERIC = frozenset({"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"})
ARM: Mapping[str, frozenset[str]] = {
    "string": frozenset({"format", "minLength", "maxLength", "pattern"}),
    "integer": _NUMERIC,
    "number": _NUMERIC,
    "boolean": frozenset(),
    "null": frozenset(),
    "array": frozenset({"items", "uniqueItems", "minItems", "maxItems"}),
    "object": frozenset({"properties", "required", "additionalProperties", "propertyNames"}),
}

#: An ARRAY's own bounds and a MAPPING's own bounds, in the document's spelling: how long
#: the list may be, and how many keys the mapping may carry.  Both are the CONTAINER's
#: own fact, which is why each rides on the container's node rather than on its contents.
_ITEM_BOUNDS = ("minItems", "maxItems")
_KEY_BOUNDS = ("minProperties", "maxProperties")


@dataclass(frozen=True)
class Source:
    """What :func:`parse` knows about the DOCUMENT, and nothing it knows about the run.

    §11 gives the reading layer "raw mapping → ``Node``; admission; applied type;
    positions; pointers" and denies it the IR, Python types, text and the run.  So the
    parser takes the document's path, for the pointers and the refusals that name it, and
    the one per-document fact the applied word is read off.
    """

    #: The bundle-relative path of the document being parsed.
    document: str
    #: The pointers of this document's nodes that an ENCLOSING node already constrains to
    #: ``type: "object"`` -- ``bundle.constrained_to_object``, which is
    #: ``adcp.types._base.applied_schema``'s own rule read over the one node walk.  §11
    #: says :attr:`nodes.Base.applied` is "set by ``parse`` through ``applied_schema``'s
    #: rule", and reading the set is how that happens with ONE spelling of "which hop
    #: keeps the instance": a second derivation here would be the divergence
    #: ``constrained_to_object``'s own docstring says would arrive silently.
    applied_at: frozenset[str] = frozenset()
    #: The lines a key admitted and carried nowhere leaves the parse by, which
    #: ``compiler.Module.carries_nothing`` collects.  A list, because the report is a
    #: sequence and the parser is otherwise a pure function.
    report: list[str] = field(default_factory=list)


def parse(
    raw: Any,
    *,
    pointer: str,
    position: Position,
    source: Source,
    objectish: bool = False,
    applied: str | None = None,
) -> nodes.Base:
    """One raw subschema as the node its keys and its type select.

    ``position`` is the node's own, assigned by the CALLER because it is a structural
    fact of the descent -- a property's value is at PROP, an array's element at ELEM, a
    branch at BRANCH -- and never recovered from the pointer string, which cannot tell a
    RULE reference from a PROP one.  Every recursive call below is this module's own, so
    after the root call the position is the parser's and nobody else's.

    ``objectish`` is §6's rule that **a child never reconstructs its parent**: "where a
    lowering needs to know something about the node ENCLOSING it, the enclosing handler
    passes it down."  §5 of the semantics document's ``type`` row reads "absent beside
    ``properties`` → an object, where an enclosing node applies ``type: object`` to the
    same instance, and refused otherwise", and the two positions where the enclosing
    structure answers that for a node stating no type are the document ROOT -- nothing
    encloses it, so it is the row's "refused otherwise" and :class:`nodes.Object`'s
    handler says so by name -- and a BRANCH of a ROOT union, which §4 of the semantics
    document makes a class whatever it states, because a union root emits one class per
    branch.  Told, not inferred.

    ``applied`` is §6's rule again, for the OTHER fact an enclosing node states about the
    same instance: the ``type`` word.  §4 of the semantics document makes a root
    ``type`` an assertion about the instance every branch sees -- "a ``type: object``
    beside ``oneOf`` is a union whose branches inherit the applied word" -- so the union
    TELLS each branch, which is ``_base.applied_schema``'s own rule read at the hop
    rather than re-derived from the document.  Where no caller says, it is
    ``bundle.constrained_to_object``'s answer for this pointer, which is the same rule
    read over the one node walk.  A node's own ``type`` always wins (``applied_schema``
    again), so this decides a kind only where the node states none.
    """
    if not isinstance(raw, Mapping):
        # Not a schema.  The kind that can hold the value and let the handler name the
        # keyword is :class:`nodes.Typeless`, whose own answer is ``Any``; every caller
        # that can be handed a non-mapping refuses it by the document's own keyword
        # (``containers._value``, ``compiler.fields``), which is a reading the kind's
        # conversion moves here.
        return nodes.Typeless(
            document=source.document, pointer=pointer, position=position
        )

    if applied is None:
        applied = "object" if pointer in source.applied_at else None
    declared = raw.get("properties")
    common: dict[str, Any] = {
        "document": source.document,
        "pointer": pointer,
        "position": position,
        "applied": applied,
        "annotations": {k: v for k, v in raw.items() if not keywords.declares(k, position)},
        "rules": _rule_sources(raw, position),
        "declares": tuple(sorted(k for k in raw if keywords.declares(k, position))),
        "extensions": tuple(
            sorted(
                k
                for k in raw
                if keywords.cell(k, position) is None and keywords.admitted_by_prefix(k)
            )
        ),
        "declared": declared if isinstance(declared, Mapping) else {},
        "extra": raw.get("additionalProperties"),
        "faults": _faults(raw),
    }

    # **The arm order is the classification, and it is §5's decision rather than a
    # measurement.**  ``$ref`` closes the node (draft-07 ignores every sibling); an
    # ``enum`` and a ``const`` close the VALUE SET, and their base is read off the
    # members rather than off ``type``, which is what admits the typeless ones; a union
    # keyword beside a ``type`` word is a conjunction with every branch, so reading
    # ``type`` first would lower the type and drop the branches; and a draft-07 ``allOf``
    # applies to the whole instance, so a node that composes is a composition whatever
    # else it declares.  ``nodes.Union.siblings`` is where ``allOf`` goes when a union
    # claims the node, which is why the union arm is read before the ``allOf`` arm (§5's
    # ``allOf`` row: "beside a union → the same, onto the base").
    if "$ref" in raw:
        return _reference(raw, common, position)
    if "enum" in raw:
        return _enumeration(raw, common)
    if "const" in raw:
        return nodes.Constant(value=raw["const"], word=raw.get("type"), **common)
    combinator = next((kw for kw in UNION if isinstance(raw.get(kw), list)), None)
    if combinator is not None and not presence_only(raw, position):
        return _union(raw, common, combinator, pointer, position, source)
    if isinstance(raw.get("allOf"), list):
        return _composition(raw, common, pointer)

    word = raw.get("type")
    if word is None:
        if "properties" in raw and (position is Position.ROOT or objectish or applied == "object"):
            return _object(raw, common, pointer, position, source)
        if not isinstance(applied, str) or applied == "object":
            # An APPLIED ``object`` is already answered, by the clause above: §5 of the
            # semantics document's ``type`` row is "absent beside ``properties`` -> an
            # object, where an enclosing node applies ``type: object`` to the same
            # instance", and a node stating neither a word nor a property map has no
            # property map for that row to read -- §5 reads it as ``{}``, which IS
            # ``true``.  A non-object word has no such clause: the word alone decides.
            return nodes.Typeless(**common)
        # **The word an enclosing node asserts about the SAME instance decides the kind
        # where the node states none** -- §4 of the semantics document's ``type`` row and
        # ``_base.applied_schema``'s own rule, which is what the SCHEMA half of every
        # graded pair already reads.  ``lower.union._alias`` built the conjunction by
        # hand, as a mapping per branch handed back to the dispatch; the reading is the
        # parser's and it is made here, once, at the hop that implies it.
        word = applied
    if isinstance(word, list):
        return _multi_type(raw, common, word, pointer, position, source)
    if word == "null":
        return nodes.Null(**common)
    if word == "object":
        if "properties" in raw:
            return _object(raw, common, pointer, position, source, word)
        return _mapping(raw, common, pointer, source, word)
    if word == "array":
        return _array(raw, common, pointer, source, word)
    # A scalar word, and the one word that is none of the above: an unknown ``type`` is a
    # contradiction in the document and the scalar handler refuses it by name, so the
    # word travels on the node rather than being classified away here.
    return nodes.Scalar(
        word=word,
        facts=value_facts(raw, position),
        format=raw.get("format") if isinstance(raw.get("format"), str) else None,
        **common,
    )


# --------------------------------------------------------------------------- #
# the kinds that hold no subschema
# --------------------------------------------------------------------------- #
def _reference(raw: Mapping[str, Any], common: dict, position: Position) -> nodes.Reference:
    """``$ref``: the document half, the pointer half, and §5's CONSTRAINING siblings.

    The co-occurrence is decided here and nowhere else (§4).  A sibling whose cell LOWERS
    at this position reads as a constraint and compiles to NOTHING -- draft-07 ignores
    every sibling of ``$ref``, so the keyword constrains no instance and the document's
    accepted set is the target's alone -- and the handler REPORTS it.  An ANNOTATION
    sibling is not here: it is in :attr:`nodes.Base.annotations`, and §5 gives it the
    other answer, the sibling's description wins.
    """
    uri = raw["$ref"]
    head, into = bundle.split_ref(uri) if isinstance(uri, str) else ("", "")
    return nodes.Reference(
        uri=uri if isinstance(uri, str) else "",
        head=head,
        into=into,
        inert=tuple(
            sorted(
                k
                for k in raw
                if k != "$ref"
                and (answer := keywords.cell(k, position)) is not None
                and keywords.lowers(answer)
            )
        ),
        **common,
    )


#: The two spellings of one keyword, in the order §6 of the semantics document lists
#: them: "``enumDescriptions``, ``x-enum-descriptions`` | Member docstrings on the
#: enumeration, keyed by the member's value.  **Two spellings of one keyword; both are
#: read.**"  ``enum.decide`` read the first alone, so ``enums/signal-value-type.json`` --
#: which states the second and only the second -- emitted with no member docstrings.
#: §14's preamble settles what the *bytes* mark forbids: an UNDECLARED change, and not
#: conforming to a sentence the semantics document already decided.
DESCRIPTIONS = ("enumDescriptions", "x-enum-descriptions")


def _enumeration(raw: Mapping[str, Any], common: dict) -> nodes.Enumeration:
    """``enum``: the members, their descriptions from EITHER spelling, the stated word.

    The spellings are merged rather than chosen between, and the order is §6's own: a
    node stating both has ``x-enum-descriptions`` win the key, which is the later
    spelling of the two and the one the ``x-`` row exists to stop dropping.  Measured
    over the portable population: 137 nodes state ``enumDescriptions``, 1 states
    ``x-enum-descriptions`` alone, and 0 state both -- so the merge order decides nothing
    today and is written down so that it does not have to be decided later.
    """
    texts: dict[str, Any] = {}
    for spelling in DESCRIPTIONS:
        stated = raw.get(spelling)
        if isinstance(stated, Mapping):
            texts.update(stated)
    members = raw.get("enum")
    return nodes.Enumeration(
        members=tuple(members) if isinstance(members, list) else (),
        descriptions=texts,
        word=raw.get("type"),
        **common,
    )


# --------------------------------------------------------------------------- #
# the kinds that hold subschemas
# --------------------------------------------------------------------------- #
def _object(
    raw: Mapping[str, Any],
    common: dict,
    pointer: str,
    position: Position,
    source: Source,
    word: Any = None,
) -> nodes.Object:
    """``type: object`` (stated or applied) with ``properties``: the fields, and the two
    readings §2 names as node rewrites.

    :attr:`nodes.Object.properties` holds the CHILD NODES, in the document's own key
    order, so the class's field order is the document's.  The pointer of a property is
    ``<pointer>/properties/<key>`` -- the spelling ``compiler.fields`` already used, so a
    refusal inside a property names the pointer it named before.

    :attr:`nodes.Object.extras` is the second rewrite retired.  A TYPED
    ``additionalProperties`` on a class is the ``dict[K, V]`` §5 says a typed one is, and
    the mapping is built HERE as a :class:`nodes.Mapping_` at the class's own pointer --
    where ``declare_object`` synthesised ``{"type": "object", "additionalProperties": ap,
    "propertyNames": ...}`` and handed it to the dispatch, which is a node the document
    does not have.  Its KEY is the class's own ``propertyNames`` node, the same object, so
    the key schema is parsed ONCE however many fields read it.
    """
    props = raw.get("properties")
    children: dict[str, nodes.Base] = {}
    if isinstance(props, Mapping):
        children = {
            key: parse(
                sub,
                pointer=f"{pointer}/properties/{key}",
                position=Position.PROP,
                source=source,
            )
            for key, sub in props.items()
        }
    required = raw.get("required")
    key = _key(raw.get("propertyNames"), f"{pointer}/propertyNames", source)
    extras = extras_store(raw, pointer, position, source)
    return nodes.Object(
        properties=children,
        required=tuple(required) if isinstance(required, list) else (),
        extras=extras,
        key=key,
        word=word,
        **common,
    )


def extras_store(
    raw: Mapping[str, Any], pointer: str, position: Position, source: Source
) -> nodes.Base | None:
    """The extras STORE of a class with a typed ``additionalProperties``: §2's SECOND
    node rewrite, retired.

    ``compiler.declare_object`` synthesised ``{"type": "object", "additionalProperties":
    ap, "propertyNames": ...}`` and handed it to the dispatch -- a node the document does
    not have, which is exactly the defect §2 names.  The reading is the parser's and it is
    made here: a typed ``additionalProperties`` on a class is the ``dict[K, V]`` §5 says a
    typed one is, at the CLASS's own pointer and position (which is where the class's
    ``__pydantic_extra__`` annotation sits), with its VALUE at MAPV and its KEY at KEY.

    ``None`` for ``false``, ``true``, the empty schema and silence: §5 reads ``{}`` as
    ``true`` everywhere, and ``true`` is the extra POLICY rather than a value type.

    Public, because two callers meet the shape: :func:`_object`, which is the converted
    reading, and ``compiler.declare_object`` for the composing row and the union branch
    that still read their own declaration (§14 step 5's staging).  One construction, two
    call sites -- never two constructions.
    """
    extra = raw.get("additionalProperties")
    if not isinstance(extra, Mapping) or not extra:
        return None
    return nodes.Mapping_(
        document=source.document,
        pointer=pointer,
        position=position,
        applied="object" if pointer in source.applied_at else None,
        value=_value(extra, f"{pointer}/additionalProperties", source),
        key=_key(raw.get("propertyNames"), f"{pointer}/propertyNames", source),
        extra=extra,
        word="object",
    )


def _mapping(
    raw: Mapping[str, Any], common: dict, pointer: str, source: Source, word: Any = None
) -> nodes.Mapping_:
    """``type: object`` without ``properties``: ``dict[K, V]``, in either spelling.

    ``propertyNames: {"pattern": P}`` beside ``additionalProperties: V`` and
    ``patternProperties: {P: V}`` beside ``additionalProperties: false`` say the same
    thing, so the two reach ONE node: :attr:`nodes.Mapping_.pattern` records which
    spelling the document used and :attr:`nodes.Mapping_.key` is the key type either way.
    """
    patterned = raw.get("patternProperties")
    if isinstance(patterned, Mapping) and len(patterned) == 1:
        expression, inner = next(iter(patterned.items()))
        return nodes.Mapping_(
            value=_value(
                inner,
                f"{pointer}/patternProperties/{bundle.escape_key(expression)}",
                source,
            ),
            # **The key schema given a ``type`` word: §2's FIRST node rewrite, retired.**
            # The expression constrains the KEY and a key is a type (§2), so the parser
            # supplies the word once -- a JSON key is a string -- at the position that
            # implies it.
            key=_key({"pattern": expression}, f"{pointer}/patternProperties", source),
            pattern=expression if isinstance(expression, str) else None,
            patterns=1,
            bounds={k: raw[k] for k in _KEY_BOUNDS if k in raw},
            word=word,
            **common,
        )
    return nodes.Mapping_(
        value=_value(raw.get("additionalProperties", True), f"{pointer}/additionalProperties", source),
        key=_key(raw.get("propertyNames"), f"{pointer}/propertyNames", source),
        patterns=_pattern_count(raw),
        bounds={k: raw[k] for k in _KEY_BOUNDS if k in raw},
        word=word,
        **common,
    )


def _array(
    raw: Mapping[str, Any], common: dict, pointer: str, source: Source, word: Any = None
) -> nodes.Array:
    """``type: array``: the element at ELEM, the LIST's own bound, ``distinct``, the
    ``contains`` predicate as stated.

    :attr:`nodes.Array.distinct` is the third rewrite retired on the array side:
    ``compiler.fields`` stripped ``uniqueItems`` off a property's declaration before the
    array row saw it, so the array was decided from a mapping the document does not state.
    The fact is read once here and the class holding the array reads it off the node.
    """
    items = raw.get("items")
    return nodes.Array(
        element=(
            parse(items, pointer=f"{pointer}/items", position=Position.ELEM, source=source)
            if isinstance(items, Mapping)
            else None
        ),
        bounds={k: raw[k] for k in _ITEM_BOUNDS if k in raw},
        distinct=raw.get("uniqueItems") is True,
        contains=raw.get("contains"),
        word=word,
        **common,
    )


def _multi_type(
    raw: Mapping[str, Any],
    common: dict,
    words: list,
    pointer: str,
    position: Position,
    source: Source,
) -> nodes.MultiType:
    """A ``type`` LIST: **§2's second node rewrite, retired.**

    The walk cut the node into one mapping per type word and handed each back to the
    dispatch.  The cut is a reading the parser makes once, at the position that implies
    it, and each member is a node of its own kind -- which is draft-07's own semantics,
    since a constraint keyword applies to instances of the type it is defined for and is
    ignored for every other type.  A member sits at the node's OWN pointer and position,
    because it is the same instance re-read under one of its admissible words.
    """
    members = tuple(
        parse(
            {"type": word, **{k: v for k, v in raw.items() if k in ARM.get(word, frozenset())}},
            pointer=pointer,
            position=position,
            source=source,
        )
        for word in words
        if isinstance(word, str)
    )
    carried = frozenset().union(*(ARM.get(w, frozenset()) for w in words)) if words else frozenset()
    return nodes.MultiType(
        words=tuple(words),
        members=members,
        stated=tuple(sorted(set(raw) & carried)),
        **common,
    )


def _union(
    raw: Mapping[str, Any],
    common: dict,
    combinator: str,
    pointer: str,
    position: Position,
    source: Source,
) -> nodes.Union:
    """``oneOf`` / ``anyOf`` whose branches are shapes.

    The branches are parsed at BRANCH, so a branch's own kind is what the handler
    dispatches on rather than a second reading of its keys, and
    :attr:`nodes.Union.branch_raw` is the declaration §4's "Names" rules and the dispatch
    derivation read -- a branch's ``const`` pin, its ``required`` set, its title.

    **The union knows its own position and TELLS its branches** (§6).  A branch of a ROOT
    union becomes a class whatever it states, because §4 of the semantics document emits
    one class per branch; a branch of a NESTED union is a member type and a branch that
    states ``properties`` with no ``type`` word is refused there, exactly as any other
    nested node stating one is.  That is the fact the enum branch is handed too:
    :attr:`nodes.Union.position` is where "of a root union" is read, and no child
    reconstructs its parent.
    """
    branches = raw[combinator]
    word = raw.get("type")
    # **The union TELLS its branches the two things it knows about them** (§6, "a child
    # never reconstructs its parent"): that a branch of a ROOT union is a class whatever
    # it states (§4 of the semantics document emits one class per branch), and the
    # ``type`` word the document applies to the same instance every branch sees (§4 of
    # the semantics document: "every keyword beside the combinator compiles onto the
    # base, and every branch inherits it"; ``_base.applied_schema``'s own rule, which is
    # what the SCHEMA half of each graded pair reads).  Both were read by the union row --
    # as an ``objectish`` argument and as a mapping per branch built by hand -- and both
    # are the parser's descent now.
    inherits = word if isinstance(word, str) else None
    return nodes.Union(
        combinator=combinator,
        branches=tuple(
            parse(
                branch,
                pointer=f"{pointer}/{combinator}/{i}",
                position=Position.BRANCH,
                source=source,
                objectish=position is Position.ROOT,
                applied=inherits,
            )
            for i, branch in enumerate(branches)
        ),
        branch_raw=tuple(branches),
        siblings={
            k: raw[k]
            for k in ("allOf", "properties", "required", "additionalProperties")
            if k in raw
        },
        word=word,
        **common,
    )


def _composition(raw: Mapping[str, Any], common: dict, pointer: str) -> nodes.Composition:
    """``allOf``: the conjuncts at CONJ, as DECLARATIONS, plus the node's own fields.

    A conjunct is a :class:`nodes.Conjunct` and not a node, and ``nodes.py`` says why:
    §2's intersection rule merges two DECLARATIONS of one property and hands the merged
    one back to :func:`parse`, because the result has to be parsed as one node rather than
    composed out of two decided ones.  The pointer travels with the conjunct, so a refusal
    inside one names the conjunct's own node.
    """
    return nodes.Composition(
        conjuncts=tuple(
            nodes.Conjunct(pointer=f"{pointer}/allOf/{i}", raw=conjunct)
            for i, conjunct in enumerate(raw["allOf"])
        ),
        required=tuple(raw["required"]) if isinstance(raw.get("required"), list) else (),
        word=raw.get("type"),
        **common,
    )


# --------------------------------------------------------------------------- #
# the two readings a container's contents take
# --------------------------------------------------------------------------- #
def _value(raw: Any, pointer: str, source: Source) -> nodes.Base | None:
    """A mapping's VALUE schema, parsed at MAPV; ``None`` for ``true`` and for ``{}``.

    §5: "The empty schema ``{}`` IS ``true`` and is read as ``true`` everywhere below,
    never as a typed value schema", and ``true`` on a mapping is the VALUE type ``Any`` --
    which is no node at all rather than a node stating nothing.
    """
    if raw is True or raw == {} or not isinstance(raw, Mapping):
        return None
    return parse(raw, pointer=pointer, position=Position.MAPV, source=source)


def _key(raw: Any, pointer: str, source: Source) -> nodes.Base | None:
    """A mapping's KEY schema, parsed at KEY, with the type word supplied.

    **§2's first node rewrite, retired.**  ``propertyNames`` applies to a key and a JSON
    key is a string, so the word is the parser's to supply -- at the position that implies
    it -- and §9's "never refuse a keyword the walk itself inserted" is why it cannot be a
    handler's.  A key schema naming its type by ``$ref`` is left alone: draft-07 ignores
    every sibling of ``$ref``, so adding one would state a fact the reference's own target
    decides.

    ``None`` where the document says nothing about keys, which is a READING and not a
    default: the key is every string.
    """
    if not isinstance(raw, Mapping):
        return None
    if "$ref" in raw:
        return parse(raw, pointer=pointer, position=Position.KEY, source=source)
    return parse({"type": "string", **raw}, pointer=pointer, position=Position.KEY, source=source)


# --------------------------------------------------------------------------- #
# the shape validation §4 gives the parser
# --------------------------------------------------------------------------- #
def _faults(raw: Mapping[str, Any]) -> dict[str, str]:
    """Every SHAPE fault this declaration states, keyed by the keyword it is about.

    §4: "it validates shape: ``required`` is a list of names, ``properties`` is a mapping
    of schemas, ``items`` is one schema and not a list, and so on, each failure a VERDICT
    refusal because a malformed document is a property of the document."  The faults a
    kind can read off its own fields are NOT here -- an ``items`` that is not a schema is
    :attr:`nodes.Array.element` being ``None`` beside ``items`` in
    :attr:`nodes.Base.declares`, and an ``enum`` that is not a list is
    :attr:`nodes.Enumeration.members` being empty -- so this carries only the ones whose
    answer is neither a field nor derivable from one.

    The kind's handler RAISES the fault at the point its own check raised it, which is
    what keeps the report a function of the document rather than of where the reading
    happens: ``required``'s shape is checked after the ``type`` and ``properties`` checks
    in the object row and after the conjunct list in the ``allOf`` row.
    """
    out: dict[str, str] = {}
    if "required" in raw:
        required = raw["required"]
        if not isinstance(required, list) or not all(isinstance(r, str) for r in required):
            out["required"] = f"required is {required!r}, not a list of names"
    return out


def _pattern_count(raw: Mapping[str, Any]) -> int | None:
    """How many ``patternProperties`` entries the node states; see
    :attr:`nodes.Mapping_.patterns`."""
    if "patternProperties" not in raw:
        return None
    stated = raw["patternProperties"]
    return len(stated) if isinstance(stated, Mapping) else -1


# --------------------------------------------------------------------------- #
# the classification the table answers
# --------------------------------------------------------------------------- #
def _rule_sources(raw: Mapping[str, Any], position: Position) -> dict[str, Any]:
    """The keywords on this node whose cell at ``position`` compiles to a RULE, plus a
    combinator the node states only to say which KEYS are present.

    §4: a node at RULE is "kept on the enclosing node as a rule source", and this is the
    carrier.  The combinators join the set only where every branch is ``required``-only --
    a CO-OCCURRENCE and not a position, so the cell cannot answer it and
    :func:`presence_only` is the parser's own classification (§11: "the kind read in
    ``_decide``, in the root selectors, in ``union.keyword``, in ``rules.presence_only`` |
    ``parse``'s classification").
    """
    sources = keywords.rule_sources(position)
    if presence_only(raw, position):
        sources |= keywords.combinators(position)
    return {k: raw[k] for k in raw if k in sources}


def presence_only(raw: Mapping[str, Any], position: Position = Position.ROOT) -> bool:
    """Is every combinator at this node a statement about key PRESENCE?

    §5's ``oneOf``/``anyOf`` row: "Presence-only, every branch ``required``-only → a
    ``RequiredGroups`` rule naming the combinator"; a combinator of SHAPES is a union.
    Both predicates are read off the same branches, so no node satisfies both and the
    classification has nothing to arbitrate.

    It is the PARSER's because the classification is (§11), and ``lower/rules.py`` reads
    it from here rather than restating it -- a lowering importing the reading layer is the
    direction §11's arrow points.
    """
    for combinator in UNION:
        branches = raw.get(combinator)
        if branches is None:
            continue
        if not isinstance(branches, list) or not branches:
            return False
        if not all(_required_only(branch, position) for branch in branches):
            return False
    return True


def _required_only(branch: Any, position: Position) -> bool:
    """A branch that says nothing but which keys are present."""
    if not isinstance(branch, Mapping):
        return False
    declared = {k for k in branch if keywords.declares(k, position)}
    return declared == {"required"} and isinstance(branch["required"], list)


#: The type words whose ARM row holds constraints of a VALUE: the four scalars and the
#: array.  ``object``'s row is excluded because its keys constrain the KEYS of an
#: instance rather than the instance itself, and ``null`` carries nothing.
_VALUE_WORDS = ("string", "integer", "number", "boolean", "array")


def value_facts(raw: Mapping[str, Any], position: Position) -> dict[str, Any]:
    """Every key on this node that is a constraint of its VALUE, in the document's own
    spelling -- which is what ``ir.FACTS`` was, DERIVED.

    §11 says the set should be derived from the table and §3 declares no single column
    that answers it: a cell's ``effect`` is TYPE for ``type``, ``enum``, ``const`` and
    ``format`` as well, and ``uniqueItems`` is RULE.  The classification that answers it
    is the parser's, and it is three readings of the declaration at once -- a fact is a
    key that

    * some type word can carry (:data:`ARM`, draft-07's own rule that a constraint keyword
      applies to instances of the type it is defined for), of the words whose constraints
      are constraints of the instance (:data:`_VALUE_WORDS`);
    * whose cell LOWERS at this position, so a keyword that states nothing here is not a
      fact here -- which is what makes a RULE position carry none;
    * and that holds NO SUBSCHEMA, which is what separates ``minItems`` from ``items``.

    ``format`` is excluded because the kind consumes it in a field of its own.

    **Measured against the tuple it replaces**: at each of the eight positions the walk
    decides a node at -- every position but RULE -- this derivation yields exactly
    ``ir.FACTS``'s eleven keywords, with no key on either side the other lacks.  So the
    tuple is deleted and nothing moves.
    """
    carried = frozenset().union(*(ARM[w] for w in _VALUE_WORDS))
    return {
        k: v
        for k, v in raw.items()
        if k != "format"
        and k in carried
        and (answer := keywords.cell(k, position)) is not None
        and keywords.lowers(answer)
        and answer.descends is None
    }
