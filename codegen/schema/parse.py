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

#: Which constraint keywords each ``type`` word can carry, for the multi-type CUT, read
#: off :data:`codegen.keywords.ARM` -- which is where it now lives, because the cut is
#: not its only reader.  It was here, and before that in ``lower/containers.py``; the
#: verifier's fold from a model ``anyOf`` back to a document type list is the CUT'S
#: INVERSE and has to read the same declaration, and §9 forbids the verifier the walk.
#: So the table moved to the one module both halves may read and this is the name the
#: parse keeps using.
ARM: Mapping[str, frozenset[str]] = keywords.ARM

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
) -> nodes.Node:
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
    #
    # **A node's own NON-OBJECT ``type`` word claims it before the ``allOf`` arm too, for
    # the reason the union arm does** (``adcp-client-python-10l.64``).  "A node that
    # composes is a composition whatever else it declares" reads a composition as an
    # OBJECT -- bases, fields, ``extra``, rules -- and §5's ``$ref`` row at CONJ already
    # decides the other case by name: "Where it is not -- a scalar, an enum, **a
    # container**, or a union root ... the target is this node's own TYPE, and the other
    # conjuncts and the ``allOf``'s siblings constrain it, which is §2's intersection at a
    # node that declares no fields of its own."  A node stating ``type: array`` beside an
    # ``allOf`` is that clause with the type read off the node's own word instead of off a
    # reference: the array IS the type, and the conjuncts constrain it.  So the word claims
    # the node, the conjunct list travels on the kind the word selects
    # (:attr:`nodes.Array.conjuncts`, :attr:`nodes.Union.siblings`'s own arrangement) and
    # the kind's handler is the one reader of it.
    #
    # Measured over every node of the 1,054 portable documents: **4 composing nodes state
    # a non-object ``type`` word and all 4 state ``array``** -- the same 4
    # ``compiler.declare_object``'s type screen measured.  A word no handler claims the
    # keyword for refuses on ``allOf`` through that handler's own screen, with the kind the
    # cell gives it, which is loud and is not a verdict about the document.
    if "$ref" in raw:
        return _reference(raw, common, position)
    if "enum" in raw:
        return _enumeration(raw, common, position)
    if "const" in raw:
        # ``facts`` for :class:`nodes.Scalar`'s reason and by the same derivation: a
        # keyword that constrains this node's VALUE is decided by the pin, and the row
        # cannot ask whether ``"US"`` matches ``^[A-Z]{2}$`` without the expression.
        return nodes.Constant(
            value=raw["const"],
            word=raw.get("type"),
            facts=value_facts(raw, position),
            # ``format`` for :class:`nodes.Scalar`'s reason and read the same way: it is
            # excluded from :func:`value_facts` precisely because the kind consumes it in
            # a field of its own, so a kind that can state one carries the field.
            format=raw.get("format") if isinstance(raw.get("format"), str) else None,
            **common,
        )
    combinator = next((kw for kw in UNION if isinstance(raw.get(kw), list)), None)
    if combinator is not None and not presence_only(raw, position):
        return _union(raw, common, combinator, pointer, position, source)
    if isinstance(raw.get("allOf"), list) and raw.get("type") in (None, "object"):
        # **A combinator of SHAPES one of this node's own conjuncts carries**, which
        # draft-07 applies to the same instance, so §5's ``oneOf``/``anyOf`` row at CONJ
        # answers it: "one class per branch over the composed bases".  Read AFTER the
        # node's own combinator, for the arm order's own reason -- a node stating one
        # itself has already said which branch list is its instance's.
        #
        # **INSIDE the word gate ``adcp-client-python-10l.64`` put on this arm, and for
        # that row's own reason**: the cell answers "one class per branch", a node
        # stating ``type: array`` beside an ``allOf`` is a container whose conjuncts
        # constrain it, and a container has no branch classes.  Measured over the 1,054
        # portable documents: all 4 composing nodes stating a non-object word state
        # ``array`` and none of them carries a combinator in a conjunct, so the gate
        # moves no document -- it is written this way so the first that does is read by
        # the word rather than by this reading.
        borne = _borne_by_a_conjunct(raw, position)
        if borne is not None:
            return _union(raw, common, borne[1], pointer, position, source, borne=borne[0])
        return _composition(raw, common, pointer)

    word = raw.get("type")
    if word is None:
        # **A node stating no ``type`` word is an OBJECT where it states something about
        # an object's MEMBERS and an enclosing node applies ``object`` to the same
        # instance** -- §5 of the semantics document's ``type`` row, "absent beside
        # ``properties`` -> an object, where an enclosing node applies ``type: object`` to
        # the same instance".
        #
        # **The row's members are the property MAP and the REQUIREDNESS over it, and this
        # arm reads both** (``adcp-client-python-10l.58``).  It read ``properties`` alone,
        # so a node stating ``required`` and no map fell through to
        # :class:`nodes.Typeless` -- **which carries no ``required`` field** -- and the
        # names the document states reached no node field at all.  §5's ``required`` row
        # decides the fact at every one of those positions ("BRANCH -> the branch class's
        # requiredness"; "ROOT beside a union -> required on the base's fields"), and the
        # carrier is one :class:`nodes.Object` already has: ``compiler.lower_composition``
        # takes :attr:`nodes.Object.required` off every kind that can state one, so the
        # names reach the class that narrows them without a second reading anywhere.
        # ``_object`` reads a missing map as ``{}``, which is what such a node declares.
        #
        # **The requiredness half is asked of the CELL at this position, because that is
        # where §5 splits it**: ``required`` compiles to the node's own TYPE at every
        # position but RULE, where its cell is a presence RULE -- the ``RequiredGroups``
        # and ``ForbiddenGroups`` ``lower/rules.py`` writes on the ENCLOSING class.  A
        # node under a ``not``, an ``if`` or a ``then`` is at RULE and is not a class, so
        # it stays typeless and its names reach the rule reader that already has them.
        # Read off the table rather than by naming the position, so the split moves with
        # the row; measured, the three documents whose nested class names this clause
        # moved when it was asked unconditionally are all ``not``/``if``/``then`` nodes.
        #
        # A ``required`` that is not a list of names is NOT screened out here: it is a
        # SHAPE fault, :func:`_faults` carries it, and the object row is what raises it
        # (§4) -- routing the node by its own keyword is what gets the fault reported
        # instead of read as silence.
        #
        # **AND A BRANCH OF A ROOT UNION IS A CLASS WHATEVER IT STATES, so ``objectish``
        # ANSWERS THE FIRST HALF TOO** (``adcp-client-python-10l.37``).  That is §4's own
        # sentence and :attr:`nodes.Union.branches`' docstring already quotes it; what it
        # was carrying here was only the SECOND half -- "an enclosing node applies
        # ``type: object``" -- so a branch whose whole content is a presence RULE fell to
        # :class:`nodes.Typeless`, which has no ``required`` and no property map, and
        # ``lower.union._plan`` refused it with "section 5's type row reads such a node as
        # ``{}``, which IS true".  That reason is sound for a branch stating nothing and
        # false for one stating a ``not`` over ``required`` or a presence combinator: such
        # a branch narrows the base by exactly the rule it carries, which
        # ``compiler.declare_object`` writes for whatever node it declares.
        # ``formats/canonical/display_tag.json``, ``html5.json`` and ``image.json`` are
        # the measured case -- their "responsive" branch states ``anyOf`` over four
        # dimension names and their "none" branch states only a ``not`` over seven.
        #
        # **THE CLAUSE IS "EVERYTHING IT DECLARES IS A RULE HERE", and both halves are
        # measured.**  Not the bare flag: §5 reads the empty schema as ``true``, and a
        # branch admitting everything the base admits has no subclass to be, so a branch
        # declaring NOTHING keeps the refusal that says so.  And not "declares anything"
        # either -- a branch stating ``format`` or ``pattern`` and no ``type`` word states
        # a fact about a VALUE, which no class carries, and reading it as an object costs
        # 22 documents (measured: ``emitted`` 923 -> 901, all 22 chained behind the
        # branches that stopped being scalars).  A RULE is precisely the thing a class
        # with no fields can carry -- ``compiler.declare_object`` writes the tuple for
        # whatever node it declares -- so the test is that every declaration is one, read
        # off :attr:`nodes.Base.rules`, which is :func:`_rule_sources`' own answer at this
        # position and already includes a presence-only combinator.  Nothing is named
        # here: the set moves with the table and with ``presence_only``.
        #
        # Measured over the 1,054 portable documents: **6 branches in 3 documents** --
        # the "responsive" and "none" branches of ``display_tag``, ``html5`` and
        # ``image``.
        if (
            "properties" in raw
            or _requires_as_a_type(raw, position)
            or (objectish and common["declares"] and not set(common["declares"]) - set(common["rules"]))
        ) and (position is Position.ROOT or objectish or applied == "object"):
            return _object(raw, common, pointer, position, source)
        if not isinstance(applied, str) or applied == "object":
            # An APPLIED ``object`` is already answered, by the clause above: §5 of the
            # semantics document's ``type`` row is "absent beside ``properties`` -> an
            # object, where an enclosing node applies ``type: object`` to the same
            # instance", and a node stating neither a word nor a MEMBER keyword has
            # nothing for that row to read -- §5 reads it as ``{}``, which IS ``true``.
            # A non-object word has no such clause: the word alone decides.
            #
            # ``facts`` by the same derivation as :class:`nodes.Scalar`'s, and the kind
            # needs them because NOTHING here can decide them: ``Any`` is no type for a
            # constraint to bind to, so the row declares a widening and a declaration
            # carries the fact the DOCUMENT states (§9).  The node built from a
            # non-mapping above carries none, which is right: it is not a schema and
            # states no fact.
            return nodes.Typeless(facts=value_facts(raw, position), **common)
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


def _enumeration(
    raw: Mapping[str, Any], common: dict, position: Position
) -> nodes.Enumeration:
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
        # ``facts`` for :class:`nodes.Constant`'s reason and by the same derivation: a
        # keyword constraining this node's value is decided by the closed member set,
        # and the row cannot ask whether ``"DE"`` matches ``^[A-Z]{2}$`` without the
        # expression.
        facts=value_facts(raw, position),
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
    children: dict[str, nodes.Node] = {}
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
) -> nodes.Node | None:
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
            # The keyword's value as the document wrote it, for §5(b)'s widening: the
            # expression alone is a projection of it and §9 asks the declared fact to be
            # the document's own spelling.
            patterned=patterned,
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
    ``contains`` predicate as stated, and the ``allOf`` conjuncts that constrain it.

    :attr:`nodes.Array.distinct` is the third rewrite retired on the array side:
    ``compiler.fields`` stripped ``uniqueItems`` off a property's declaration before the
    array row saw it, so the array was decided from a mapping the document does not state.
    The fact is read once here and the class holding the array reads it off the node.

    :attr:`nodes.Array.conjuncts` is the arm order's own clause, stated where that comment
    states it: a ``type: array`` beside an ``allOf`` is §5's ``$ref`` row at CONJ reached
    through the node's own word, so the conjunct list travels on the kind the word selects
    and ``lower.containers.array`` reads it.  Built exactly as :func:`_composition` builds
    it, with the CONJ pointer, so a refusal inside one names the conjunct's own node.
    """
    items = raw.get("items")
    return nodes.Array(
        conjuncts=tuple(
            nodes.Conjunct(pointer=f"{pointer}/allOf/{i}", raw=conjunct)
            for i, conjunct in enumerate(raw["allOf"])
        )
        if isinstance(raw.get("allOf"), list)
        else (),
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
    # **The node's own ``description`` travels into every arm**, which is §6's
    # description-authority rule read at the one position a node becomes TWO
    # declarations.  An arm "is the same instance re-read under one of its admissible
    # words", so the sentence the document states about that instance is the arm's too --
    # and the ``object`` arm is the one where it is load-bearing: §4 makes an object with
    # ``properties`` a CLASS, and a class's description is its DOCSTRING, which nothing
    # else can supply (``Shape.description``: "pydantic cannot be left to do it,
    # ``cls.__doc__`` is ``None`` for a subclass with no docstring of its own").
    #
    # Measured on ``core/delivery-metrics.json#/properties/quartile_data``, the bundle's
    # one emitted multi-type node whose ``object`` arm declares ``properties``: without
    # this the nested class carried no docstring and §8's comparison reported the
    # document's own ``/description`` as *missing* at the pair, while every other nested
    # class in the same document carries one.  The FIELD carried it either way -- §6
    # gives PROP a ``Field(description=…)`` -- so what was dropped was the class's half
    # and not the property's.
    #
    # It is not in :data:`ARM`, and deliberately: that table is "the keywords that type
    # can carry", a per-word CONSTRAINT question, and a description is a statement about
    # the instance that every word carries equally.  Putting it in ARM would also put it
    # in the screen ``lower.containers.multi_type`` admits a keyword by, so a document
    # could state a description a NON-OBJECT arm then carries into its own node -- and
    # it would put it in ``harness._type_list``'s liftable set, where it is the one key
    # that must not lift (it belongs to every arm equally, not to one).
    annotated = {k: v for k, v in raw.items() if k == "description"}
    members = tuple(
        parse(
            {
                "type": word,
                **annotated,
                **{k: v for k, v in raw.items() if k in ARM.get(word, frozenset())},
            },
            pointer=pointer,
            position=position,
            source=source,
        )
        for word in words
        if isinstance(word, str)
    )
    # **``stated`` went with the constrained-arm refusal.**  It carried "the keywords
    # this node states that SOME arm carries", and its one reader was the refusal
    # ``lower.containers.multi_type`` took where such a keyword sat beside two live arms.
    # That refusal is retired -- ``harness._type_list`` folds a constrained arm, so the
    # node is graded -- and a node field no reader reads is a second copy of ``set(raw) &
    # carried`` waiting to disagree with the screen that derives it.
    return nodes.MultiType(words=tuple(words), members=members, **common)


def _borne_by_a_conjunct(
    raw: Mapping[str, Any], position: Position
) -> tuple[int, str] | None:
    """The one ``allOf`` conjunct of ``raw`` that states a combinator of SHAPES and
    nothing else, as ``(index, keyword)`` -- or ``None`` where no conjunct does, where
    two do, or where the one that does states something else beside it.

    **Draft-07 conjoins a conjunct with the node that holds it**, which is the same
    reading :func:`applies_to_one_instance` makes for §4's disjointness derivation and
    the reason ``compiler.lower_composition`` takes a conjunct's ``properties`` as the
    composed node's fields.  So a conjunct stating ``oneOf``/``anyOf`` states it about
    THIS node's instance, and §5's ``oneOf``/``anyOf`` row has the cell for it: "CONJ ->
    one class per branch over the composed bases".  The classification is the parser's
    for §11's reason -- the kind is decided once, here -- and nothing is rewritten: the
    branch list travels as :attr:`nodes.Union.branch_raw` with its own pointers, and the
    conjunct's index is kept so every other conjunct keeps the pointer the document
    gives it.

    ``presence_only`` is the same gate the node's own arm uses, so a conjunct stating a
    combinator of presence GROUPS is a rule source of the composed class exactly as it
    is today (``declaration_rule_sources`` at CONJ) and never reaches here.

    **Three ways this declines, each leaving the node a :class:`nodes.Composition` and
    its refusal exactly where it is today.**  Nothing is admitted on a guess:

    * no conjunct states one -- the ordinary composing node;
    * TWO conjuncts do, or the node states one itself beside a conjunct that does: the
      instance is then described by two branch lists at once and there is no single
      class-per-branch answer.  Measured over the 1,054 portable documents: **0 nodes**;
    * the conjunct states anything else beside the combinator.  Then the conjunct also
      contributes to the composed class, and the conjunction of ITS contribution with
      its own branch list is the thing ``compiler._refuse_a_combinator_of_shapes``
      refuses for having no pointer.  Measured: **0 of the 7 sites** -- every conjunct
      carrying a combinator of shapes in this bundle states the keyword and annotations
      alone.

    Measured over the 1,054 portable documents: **7 sites in 6 documents** state a
    combinator of shapes in a conjunct -- ``adagents.json`` at ``/oneOf/1/allOf/0``,
    ``formats/canonical/display_tag.json``, ``html5.json`` and ``image.json`` at
    ``/allOf/1``, ``governance/check-governance-request.json`` at ``/allOf/1`` and at
    ``/allOf/13/if/allOf/1``, and ``protocol/get-adcp-capabilities-response.json`` at
    ``/allOf/11/if/allOf/1``.  The last two sit under an ``if``, which §4 keeps as a rule
    SOURCE and never hands to :func:`parse`, so five nodes reach this.
    """
    found: tuple[int, str] | None = None
    for i, conjunct in enumerate(raw["allOf"]):
        if not isinstance(conjunct, Mapping):
            continue
        declared = {k for k in conjunct if keywords.declares(k, Position.CONJ)}
        combinator = next((kw for kw in UNION if isinstance(conjunct.get(kw), list)), None)
        if combinator is None or presence_only(conjunct, Position.CONJ):
            continue
        if declared != {combinator} or found is not None:
            return None
        found = (i, combinator)
    if found is not None and any(isinstance(raw.get(kw), list) for kw in UNION):
        # The node states a branch list of its own as well.  Its own arm has already
        # answered -- it runs first -- unless that one is presence-only, and then the
        # node is a rule source AND a union of shapes at once, which no cell answers.
        return None
    return found


def _union(
    raw: Mapping[str, Any],
    common: dict,
    combinator: str,
    pointer: str,
    position: Position,
    source: Source,
    *,
    borne: int | None = None,
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
    # **WHERE the keyword is stated, which is not always this node** (``borne``): a
    # conjunct carrying it states it about the same instance, so the branch pointers are
    # the conjunct's and the conjunct list this node composes is the rest.
    stated_at = pointer if borne is None else f"{pointer}/allOf/{borne}"
    branches = (raw if borne is None else raw["allOf"][borne])[combinator]
    conjuncts = tuple(
        nodes.Conjunct(pointer=f"{pointer}/allOf/{i}", raw=conjunct)
        for i, conjunct in enumerate(raw["allOf"] if isinstance(raw.get("allOf"), list) else ())
        if i != borne
    )
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
        stated_at=stated_at,
        conjuncts=conjuncts,
        branches=tuple(
            parse(
                branch,
                pointer=f"{stated_at}/{combinator}/{i}",
                position=Position.BRANCH,
                source=source,
                objectish=position is Position.ROOT,
                applied=inherits,
            )
            for i, branch in enumerate(branches)
        ),
        branch_raw=tuple(branches),
        # §5's ``required`` row at ROOT beside a union -- "required on the base's
        # fields, and the names recorded in ``_ROOT_REQUIRED``" -- read the way every
        # other kind that can state one reads it, so ``compiler.lower_composition``
        # takes the node's requiredness off one field name whatever kind it is handed.
        required=tuple(raw["required"]) if isinstance(raw.get("required"), list) else (),
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
def _value(raw: Any, pointer: str, source: Source) -> nodes.Node | None:
    """A mapping's VALUE schema, parsed at MAPV; ``None`` for ``true`` and for ``{}``.

    §5: "The empty schema ``{}`` IS ``true`` and is read as ``true`` everywhere below,
    never as a typed value schema", and ``true`` on a mapping is the VALUE type ``Any`` --
    which is no node at all rather than a node stating nothing.
    """
    if raw is True or raw == {} or not isinstance(raw, Mapping):
        return None
    return parse(raw, pointer=pointer, position=Position.MAPV, source=source)


def _key(raw: Any, pointer: str, source: Source) -> nodes.Node | None:
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
def _requires_as_a_type(raw: Mapping[str, Any], position: Position) -> bool:
    """Does this node state a ``required`` that compiles to its OWN type here?

    §5's ``required`` row splits on exactly one position: at RULE it is "a presence rule:
    ``RequiredGroups``, ``ForbiddenGroups`` under ``not``, the keys a ``Match`` clause
    tests under ``if``, ``ConditionalRequired`` / ``NegatedConditional`` under ``then`` /
    ``else``" -- a fact about the ENCLOSING class, which ``lower/rules.py`` writes and
    which needs no node of its own.  Everywhere else the row is the requiredness OF the
    node ("BRANCH -> the branch class's requiredness", "ROOT beside a union -> required on
    the base's fields"), which is :attr:`nodes.Object.required` and
    ``compiler.lower_composition``'s reading of it.

    So the split is the CELL's ``effect`` and this is a reader of the table, the way
    :func:`_rule_sources` and :func:`presence_only` are -- not a position named here,
    which would be a second copy of the row for the two to disagree through (§11).
    """
    answer = keywords.cell("required", position)
    return "required" in raw and answer is not None and answer.effect is keywords.Effect.TYPE


def _rule_sources(raw: Mapping[str, Any], position: Position) -> dict[str, Any]:
    """The keywords on this node whose cell at ``position`` compiles to a RULE, plus a
    combinator the node states only to say which KEYS are present.

    §4: a node at RULE is "kept on the enclosing node as a rule source", and this is the
    carrier.  The combinators join the set only where every branch states which keys are
    PRESENT -- a CO-OCCURRENCE and not a position, so the cell cannot answer it and
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

    §5's ``oneOf``/``anyOf`` row: a branch stating only which keys are present → one
    rule naming the combinator; a combinator of SHAPES is a union.  Both predicates are
    read off the same branches, so no node satisfies both and the classification has
    nothing to arbitrate.

    It is the PARSER's because the classification is (§11), and ``lower/rules.py`` reads
    it from here rather than restating it -- a lowering importing the reading layer is the
    direction §11's arrow points.  :func:`presence_clause` is the whole of the reading and
    this is its quantifier, so the predicate that selects the row and the values the row
    lowers cannot come apart.
    """
    for combinator in UNION:
        branches = raw.get(combinator)
        if branches is None:
            continue
        if not isinstance(branches, list) or not branches:
            return False
        if not all(presence_clause(branch, position) is not None for branch in branches):
            return False
    return True


#: One branch read as a presence statement: the names it REQUIRES, and the groups it
#: FORBIDS.  A plain pair and not a runtime dataclass, because ``schema/`` reads the
#: document and ``adcp.types._runtime`` is the model layer's side of the seam -- the
#: lowering builds :class:`adcp.types._runtime.Presence` out of this.
Clause = tuple[tuple[tuple[str, ...], ...], tuple[tuple[str, ...], ...]]


def presence_clause(branch: Any, position: Position) -> Clause | None:
    """``branch`` as a presence statement, or ``None`` if it says anything else.

    **§5, "A union of presence-only branches that also forbid" (decided 2026-10-27).** A
    branch of a presence-only union states its requiredness and, optionally, a ``not``
    over ``required`` groups: "at least one group of R present in full and no group of F
    present in full".  Both halves belong to the SAME branch, which is why they are read
    together and returned paired -- a ``not`` lifted off its branch and stated beside the
    combinator forbids its groups unconditionally, and ``core/catchment.json`` is the
    measurement: it states three methods and forbids the other two per method, so a rule
    holding the union of the three ``not``\\ s forbids all three and refuses every
    payload the document admits.

    **BOTH HALVES ARE GROUPS** (§5, "A presence clause whose required half is a
    disjunction of groups", decided 2026-10-29).  ``required: [a, b]`` is the single
    group ``((a, b),)`` and an ``anyOf`` over ``required`` is the groups it states, which
    is the reading ``forbid`` already had and for the same reason -- a group is what is
    satisfied, and a name on its own is not.  Measured over every combinator node of the
    1,054 portable documents: **3 branches state the disjunctive spelling** and all three
    are the ``responsive`` arm of one size mutex, at ``/allOf/1/oneOf/2`` of
    ``formats/canonical/{image,html5,display_tag}.json``.  **0 branches state
    ``required: []``**, so routing the required half through :func:`required_groups` --
    which answers ``None`` for an empty name list -- takes no clause out that the
    conjunctive reading admitted, and the rule tuples the bundle already carries do not
    move.

    A branch whose ``not`` does not reduce to groups is NOT a presence clause: it
    constrains something a rule cannot say, so the node is a combinator of shapes and
    §5's union row answers it.  Reading it as a clause and dropping the ``not`` would
    make the rule say less than the branch with nothing to report it.

    **A branch that FORBIDS and requires nothing is a presence clause, and its required
    half carries NO GROUP** (``adcp-client-python-10l.64``).  §5's row is "each clause
    carries its OWN required group and its own forbidden groups, because the ``not`` is
    per branch", and the section's own reason for the kind is "every branch constrains
    which keys are present and nothing else, so it is a rule on the root's class and not
    a branch class" -- which a branch stating only a ``not`` over required groups
    satisfies.  Nothing in either sentence asks the required half to be non-empty, and
    :meth:`adcp.types._runtime.Presence.holds` reads an empty ``require`` as the
    requirement over no groups that it is: the clause is then exactly "no group of F
    present", which is the branch.  Under GROUPS that case is a written term of
    ``holds`` rather than a vacuous ``all(())``, because ``any(())`` is False -- the one
    way this generalisation could have silently broken a clause it already admitted.

    A branch declaring NOTHING at all stays out, and that is the gate this keeps: §5's
    ``type`` row reads such a node as ``{}``, "which IS true", so it is not a statement
    about presence and ``lower.union``'s own row is what reports it.

    Measured over every combinator node of the 1,054 portable documents: **2 sites
    change**, and they are the two this row cleared -- ``core/forecast-point.json`` and
    ``core/canonical-forecast-point.json`` at ``/properties/viewability``, whose ``anyOf``
    is "forbid all four measurement keys, or require ``standard``".
    """
    if not isinstance(branch, Mapping):
        return None
    declared = {k for k in branch if keywords.declares(k, position)}
    if not declared:
        return None
    # **BOTH HALVES REACH ONE DERIVATION, from the two sides of one branch** (§5, "A
    # presence clause whose required half is a disjunction of groups", 2026-10-29; §11's
    # one reading with two readers).  The ``not`` half was always
    # :func:`required_groups`; the REQUIRED half is the same function asked of everything
    # the branch declares BESIDE its ``not``, so ``required: [a, b]`` is the single group
    # ``((a, b),)`` and an ``anyOf`` over ``required`` is the groups it states.  The
    # screen is that function's own -- it admits ``required``, an ``anyOf`` of groups and
    # an ``allOf`` of single-group conjuncts, and answers ``None`` for anything else --
    # so this function keeps no parser and no keyword set of its own.  The set it used to
    # carry, ``declared <= {"required", "not"}``, is what kept the four documents of
    # ``adcp-client-python-10l.75`` out: a branch spelling its requirement
    # DISJUNCTIVELY was read as a union of SHAPES, of a node where no branch declares a
    # property, a type word or any value constraint.
    demanded = declared - {"not"}
    require: tuple[tuple[str, ...], ...] = ()
    if demanded:
        # **A branch that FORBIDS and requires nothing keeps its empty ``require``**
        # (``adcp-client-python-10l.64``), which is this arm being skipped rather than
        # ``required_groups`` being asked about an empty mapping -- that call answers
        # ``None`` and would take the clause out.
        groups = required_groups({k: branch[k] for k in demanded}, position)
        if groups is None:
            return None
        require = tuple(groups)
    if "not" not in declared:
        return (require, ())
    forbid = required_groups(branch["not"], position)
    if forbid is None:
        return None
    return (require, tuple(forbid))


def required_groups(
    sub: Any, position: Position, *, partial: bool = False
) -> list[tuple[str, ...]] | None:
    """``sub`` as a set of key groups, or ``None`` if it says anything else.

    A group is a set of names whose simultaneous presence satisfies ``sub``, so an
    enclosing ``not`` forbids it.  ``anyOf`` of branches is the union of their groups
    (any branch satisfied satisfies ``sub``); ``allOf`` is the PRODUCT of its conjuncts'
    group lists with the names unioned per combination, because conjunction distributes
    over disjunction -- so an ``allOf`` of single-group conjuncts is the one group their
    names union to, and that case is the product over one-element lists (§5, decided
    2026-10-29).  ``oneOf`` is deliberately absent: its negation is "not exactly one",
    which no list of forbidden groups expresses.

    The PARSER's, because :func:`presence_clause` is the classification and needs it, and
    ``lower/rules.py`` reads it from here for its ``not`` and its ``then``/``else`` --
    one reduction of one keyword, which is what §11's "nothing repeats" asks of it.

    **``partial`` makes the ``anyOf`` arm keep the disjuncts it CAN read**
    (``adcp-client-python-10l.27``, settled 2026-10-27).  ``not (A or B or C)`` is
    ``not A and not B and not C``, so a disjunct this reduction cannot read contributes
    NO group and the others still contribute theirs -- which is a WEAKER rule, and §2
    permits a model looser than its document while forbidding a tighter one.
    All-or-nothing dropped the whole ``not``: measured at
    ``media-buy/sync-audiences-response.json``, whose branch 1 forbids ``errors`` and
    ``task_id`` beside one disjunct stating ``properties`` as well, so the branch carried
    no ``ForbiddenGroups`` at all and §4's second separator could not see that branch 2
    requires ``task_id``.

    **It is a PARAMETER and not the rule, because the direction of safety depends on who
    asks.**  Every reader of this function today asks about a ``not``, where fewer groups
    forbid less; :func:`presence_clause` also uses the answer to CLASSIFY a branch, and a
    branch whose ``not`` is only partly readable is a branch stating something a rule
    cannot say -- reading it as a clause would drop that branch's shape precision with
    nothing to report it, which is that function's own sentence.  The ``allOf`` arm never
    takes it: ``not (A and B)`` with ``B`` dropped is ``not A``, which is STRONGER, and
    the same holds of the product -- dropping a conjunct leaves FEWER names in each group
    and a smaller group forbids MORE.  §5 states that asymmetry at the product arm too.
    """
    if not isinstance(sub, Mapping):
        return None
    keys = {k for k in sub if keywords.declares(k, position)}
    if keys == {"required"} and isinstance(sub["required"], list):
        names = tuple(n for n in sub["required"] if isinstance(n, str))
        return [names] if names else None
    if keys == {"anyOf"} and isinstance(sub["anyOf"], list):
        out: list[tuple[str, ...]] = []
        for branch in sub["anyOf"]:
            groups = required_groups(branch, position, partial=partial)
            if groups is None:
                if partial:
                    continue
                return None
            out.extend(groups)
        return out or None
    if keys == {"allOf"} and isinstance(sub["allOf"], list):
        # **A conjunction of a group with a DISJUNCTION of groups distributes** (§5, "A
        # conjunction of a group with a disjunction of groups DISTRIBUTES into a
        # disjunction of groups", decided 2026-10-29).  An ``allOf`` conjoins its
        # conjuncts, so the groups that satisfy it are the PRODUCT of the conjuncts' own
        # group lists with the names unioned per combination -- ``A and (B or C)`` is
        # ``(A and B) or (A and C)``.  The single-group case this arm used to be is that
        # product over one-element lists, so the arm is one derivation and not two.
        #
        # ``None`` from any conjunct still takes the whole ``allOf``, and the product arm
        # NEVER takes ``partial``: dropping an unreadable conjunct leaves FEWER names in
        # each group, and under a ``not`` a smaller group forbids MORE instances -- a rule
        # stronger than its document, which is the narrowing §2 refuses.  The ``anyOf``
        # arm above takes ``partial`` for the mirror reason, and that asymmetry is the
        # whole of this function's ``partial`` docstring.
        product: list[tuple[str, ...]] = [()]
        for branch in sub["allOf"]:
            groups = required_groups(branch, position)
            if groups is None:
                return None
            product = [(*combination, *group) for combination in product for group in groups]
        # A group is a SET of names, so a name two conjuncts both require appears ONCE,
        # and the product can reach one combination by two routes when their group lists
        # overlap -- both readers compare groups, so a second spelling of one group is a
        # second group to them and a ``ForbiddenGroups`` would restate what it holds.
        # Deduplicated in FIRST-OCCURRENCE order and never sorted: the group's order is
        # the document's, and sorting would rewrite every ``ForbiddenGroups`` literal the
        # tree already carries for a fact that did not change.
        groups_out = [tuple(dict.fromkeys(g)) for g in product if g]
        return list(dict.fromkeys(groups_out)) or None
    return None


def applies_to_one_instance(node: Any, position: Position) -> list[Mapping[str, Any]]:
    """``node`` and every node its ``allOf`` applies to the SAME instance.

    Draft-07 conjoins an ``allOf`` conjunct with the node that holds it, so a fact a
    conjunct states is a fact about the instance the node describes -- which is D7's own
    wording and the reason ``compiler.lower_composition`` reads a conjunct's
    ``properties`` as the composing node's fields and hands its rule sources to
    ``compiler.rules_at`` as that node's own.  Every reading of a BRANCH's declaration
    owes the same descent, and §4's disjointness derivation is three of them: what the
    branch requires, what it forbids, and what it declares while admitting nothing else.

    **The measured case, and why the descent is not optional**:
    ``account/sync-accounts-request.json#/properties/accounts/items/oneOf`` states its
    two branches' guards as ``allOf: [{"not": {"required": ["account"]}}, ...]`` rather
    than at the branch's top level, and ``brand.json``'s catch-all branch 4 carries a
    ``not`` forbidding every sibling's discriminant inside ``allOf[0]``.  Read at the top
    level alone both branch pairs are inseparable and the document's own idiom says they
    are not.

    A conjunct that is a ``$ref`` contributes NOTHING, which is the conservative
    direction and the one §4 already takes for a bare ``$ref`` branch: the fact is in the
    target, resolving it is not a reading of this node, and "a pair the derivation cannot
    separate is treated as overlapping, because admitting a union on an unproven
    disjointness is the defect this source exists to avoid".  Flattened to any depth,
    because an ``allOf`` of an ``allOf`` conjoins just the same.
    """
    if not isinstance(node, Mapping):
        return []
    out = [node]
    if "allOf" in {k for k in node if keywords.declares(k, position)}:
        conjuncts = node["allOf"]
        if isinstance(conjuncts, list):
            for conjunct in conjuncts:
                if isinstance(conjunct, Mapping) and "$ref" not in conjunct:
                    out.extend(applies_to_one_instance(conjunct, position))
    return out


def demanded_names(node: Any, position: Position) -> frozenset[frozenset[str]]:
    """Each set of names at least ONE of which every instance of ``node`` carries.

    §4's second separator asks "a ``required`` name one branch declares and another
    forbids", and the name a branch declares is not always one name: a branch stating
    ``anyOf: [{"required": ["brands"]}, {"required": ["brand_refs"]}]`` beside its own
    ``required`` does require one of the two, so a sibling that forbids BOTH -- by name,
    or by being closed and declaring neither -- is disjoint from it.  That is the
    quantity, and it is returned as a set of SETS because the separator is a question
    about each alternative group and not about one name:
    :func:`codegen.lower.union.separates` separates the pair where every name of some
    group is forbidden, which for a singleton group is exactly the reading it already had.

    Three sources, each over :func:`applies_to_one_instance` so a conjunct's statement
    counts:

    * ``required: [a, b]`` -> ``{a}`` and ``{b}``, two groups, because each name is
      present on its own;
    * a ``oneOf``/``anyOf`` of branches that each guarantee a name -> ONE group, the
      union of what the branches guarantee.  Whichever branch an instance satisfies, that
      branch's names are present and they are inside the union, so the union has a member
      present.  A branch guaranteeing NOTHING -- ``{"properties": {...}}`` with no
      ``required`` -- makes the whole combinator guarantee nothing, which is why
      ``adagents.json``'s 6-branch ``anyOf`` yields no group: its first branch states a
      property map and no ``required``, so an instance can satisfy the combinator while
      carrying none of the other five names.
    * a conjunct of either shape, recursively.

    **The DUAL of :func:`required_groups` and not a second copy of it.**  That function
    reduces a subschema to the groups whose presence SATISFIES it, which is what an
    enclosing ``not`` negates; this one reads an ASSERTED node for what it guarantees.
    The two answers differ at the keyword that matters most: ``required: [a, b]``
    satisfies as one group ``(a, b)`` and guarantees two, ``{a}`` and ``{b}``.  Reading
    one through the other would make the separator weaker than the document at every
    branch that states a plain ``required``.
    """
    out: set[frozenset[str]] = set()
    for view in applies_to_one_instance(node, position):
        declared = {k for k in view if keywords.declares(k, position)}
        required = view.get("required")
        if "required" in declared and isinstance(required, list):
            out |= {frozenset({n}) for n in required if isinstance(n, str)}
        for combinator in UNION:
            if combinator not in declared or not isinstance(view.get(combinator), list):
                continue
            guaranteed: set[str] = set()
            for branch in view[combinator]:
                names = {n for group in demanded_names(branch, position) for n in group}
                if not names:
                    guaranteed = set()
                    break
                guaranteed |= names
            if guaranteed:
                out.add(frozenset(guaranteed))
    return frozenset(out)


def closed_maps(node: Any, position: Position) -> tuple[frozenset[str], ...]:
    """For each view of ``node`` that admits only what it declares, the names it declares.

    ``additionalProperties: false`` says an instance's members lie inside that node's own
    ``properties``, so a name the node never declares is a name it REFUSES -- which is
    §4's second separator read off closure rather than off a ``not``.  A
    ``patternProperties`` beside it takes the closure back for whatever the pattern
    matches, so such a view admits names this cannot enumerate and is not one.

    One entry per closed view, because closure is a fact about the NODE and not about the
    conjunction: a conjunct stating ``additionalProperties: false`` beside its own
    ``properties`` closes the instance over THAT map, and the node's other views do not
    widen it.  So a demanded name outside ANY ONE of these maps is refused, and the
    separator asks the question of each in turn.
    """
    return tuple(
        frozenset(view.get("properties") or {})
        for view in applies_to_one_instance(node, position)
        if view.get("additionalProperties") is False and "patternProperties" not in view
    )


def element_word(node: Any, position: Position) -> tuple[Any, bool]:
    """The ``type`` this node applies to every ELEMENT, and whether it refuses ``[]``.

    §4's fourth separator is "scalar branches of different ``type``", and an array branch
    states its instance's type one level down: ``items`` describes every member, so two
    array branches whose elements are a string and an object are told apart by any
    member.  ``brand.json#/definitions/localized_string_list`` is the bundle's case --
    two ``type: array`` branches, one of strings and one of entries.

    **The EMPTY ARRAY is why the second half of the answer is here.**  ``[]`` satisfies
    ``items`` vacuously, so two arrays of disjoint element types both admit it and the
    pair is NOT disjoint on the element word alone.  ``minItems`` of 1 or more is what
    refuses it, and a pair where neither branch refuses it overlaps at exactly that one
    value -- which §4's "a pair the derivation cannot separate is treated as overlapping"
    makes a refusal to separate rather than a judgement call.

    The word is ``None`` where ``items`` states none, which includes an ``items`` that is
    a ``$ref``: the fact is in the target and resolving it is not a reading of this node
    (:func:`applies_to_one_instance`'s own rule).
    """
    if not isinstance(node, Mapping):
        return None, False
    items = node.get("items")
    word = items.get("type") if isinstance(items, Mapping) else None
    minimum = node.get("minItems")
    return word, isinstance(minimum, int) and not isinstance(minimum, bool) and minimum >= 1


def forbidden_values(sub: Any, position: Position) -> dict[str, Any]:
    """Each ``(key, value)`` pair ``sub``'s ``not`` forbids, read off a PINNED property.

    **§4's FOURTH separator** (decided 2026-10-27): "one branch forbidding a VALUE another
    pins".  ``not: {"properties": {"status": {"const": "submitted"}}, "required":
    ["status"]}`` says no instance carries ``status == "submitted"`` -- the ``required``
    is what makes the member a statement about the VALUE rather than one satisfied by the
    key being absent -- and ``anyOf``/``allOf`` of such members forbid each of them,
    because ``not (A or B)`` is ``not A and not B`` and every member of an ``allOf`` under
    a ``not``... is NOT read, for the reason :func:`required_groups`' own ``allOf`` arm
    gives: ``not (A and B)`` leaves either one, so a member of a conjunction forbids
    nothing by itself.

    A member pinning MORE than one property is read the same way, member by member: it
    forbids the whole combination and not each pair, so it contributes nothing -- the same
    distinction ``required_groups`` draws between a singleton group and a longer one.

    The PARSER's, beside :func:`required_groups`, because it is the second reduction of
    one keyword and §11's "nothing repeats" puts both where the first one is.  A member
    the reading cannot take contributes nothing and the others still contribute theirs,
    which is ``required_groups``' ``partial`` rule for the same reason: under a ``not``,
    forbidding less is the safe direction.

    **Read over every view of ``sub``** (:func:`applies_to_one_instance`), because a
    branch's guard sits inside one of its ``allOf`` conjuncts as often as at its top
    level and draft-07 conjoins the two: a ``not`` a conjunct states is a statement about
    the instance the branch describes.  The same descent the other two readings of a
    branch's declaration take.
    """
    out: dict[str, Any] = {}

    def member(node: Any) -> None:
        if not isinstance(node, Mapping):
            return
        keys = {k for k in node if keywords.declares(k, position)}
        if keys == {"anyOf"} and isinstance(node["anyOf"], list):
            for one in node["anyOf"]:
                member(one)
            return
        if keys != {"properties", "required"} or not isinstance(node.get("properties"), Mapping):
            return
        required = node.get("required")
        if not isinstance(required, list) or len(required) != 1:
            return
        (name,) = required
        declaration = node["properties"].get(name)
        if set(node["properties"]) != {name} or not isinstance(declaration, Mapping):
            return
        if "const" in declaration:
            out[name] = declaration["const"]
        elif isinstance(declaration.get("enum"), list) and len(declaration["enum"]) == 1:
            out[name] = declaration["enum"][0]

    for view in applies_to_one_instance(sub, position):
        member(view.get("not"))
    return out


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
