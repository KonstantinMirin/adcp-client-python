"""D2's container rows: an array, a mapping, a multi-type node, and the roots that
are neither an object with properties nor a scalar.

A container is a node whose SHAPE is one fact and whose CONTENTS are another node.
So every row here is the same two halves -- the contents, lowered by recursing
through ``mod.decide``, and the container's own bound, carried on the FIELD
holding the container and not on what is inside it.  **Which half a keyword belongs
to is the whole of this module**, and getting it wrong is the defect class it exists
to remove: the generator this pipeline replaces read ``minItems`` on a named property
and carried it, read the same keyword on a mapping VALUE and dropped it, and read a
``minLength`` on a ``["object", "string"]`` node and applied it to the object arm.
The first makes a model wider than its schema and the third makes one narrower.

**What this module does not build, each with the population that says so.**  A
mechanism whose population is empty is green for free, so each of these refuses by
name instead, and the refusal carries what the document said:

* **D2's root-array ``RootModel[list[X]]`` row.**  All 5 root arrays of the bundle
  refuse on a keyword that is not this step's: 4 carry ``uniqueItems: true`` at the
  root (D6's rule, step 7) and ``media-buy/product-refinement.json`` refuses inside
  its ``items``.  So a ``RootModel`` base would be a class no document reaches and no
  pair grades.  :func:`root` lowers the element FIRST, so the refusal names the
  element type the row would have wrapped rather than just the shape.
* **An inner constraint this module cannot name.**  A constraint on what is INSIDE
  a container has no slot in the compiler's ``DataType``, and D5's answer is to
  resolve the inner type to a NAME -- one the bundle itself gives a titled root,
  then one pydantic gives, then an alias emitted in ``adcp.types.constraints``.
  **That module now exists** (``codegen/constraints.py``), so ``decide_type``
  hands this module an inner type whose constraints are already on the type and
  :func:`_inner` sees none: ``dict[str, StrMinLen1]`` and
  ``list[StrMatchingEFC12812]`` are plain references and need nothing from the
  compiler, which is what D5 says naming the type buys.  :func:`_inner` still
  refuses what is still unnameable -- a constraint keyword
  ``codegen.constraints.SPELLING`` has no word for, and a ``format`` no type is
  selected for -- because those would be DROPPED rather than carried, and the
  detail names the constraint so the refusal says what would have to be named.
* **A closed key set as a model.**  ``propertyNames`` with an ``enum`` closes the
  keys, and D5 reads a closed key set as a model whose keys are its fields.  Its one
  type-position site is ``core/store-item.json#/properties/hours``, and that document
  carries ``enum`` (step 3's keyword), so it refuses before any mapping is lowered.
  :func:`_key` refuses it by name with the key set in the detail.

**A MAPPING'S KEY IS A TYPE (§2), AND THE DOCUMENT'S TWO SPELLINGS OF A PATTERNED
KEY ARE ONE TYPE.**  ``propertyNames: {"pattern": P}`` beside
``additionalProperties: V`` and ``patternProperties: {P: V}`` beside
``additionalProperties: false`` both say "every key matches ``P`` and its value
matches ``V``", and ``dict[Annotated[str, StringConstraints(pattern=P)], V]`` is
that -- so :func:`_key` owns the key rule for both and :func:`mapping` only decides
where in the document the expression sits.  Both arms REFUSED as verdicts on the
ground that pydantic renders the key back as ``patternProperties`` and the schema
comparison could not grade it.  The ``patternProperties`` arm's premise was simply
wrong: ``patternProperties`` is the keyword that document states.  The
``propertyNames`` arm's obstruction was real and was an unwritten comparison row,
which §2 counts as a DEFERRAL and not a verdict -- and it is now written
(``harness._patterned_key``) rather than named, so neither arm refuses.

Measured over the 1,054 portable documents of the 3.2 bundle: **40 key sites in 28
documents** -- 26 ``propertyNames`` in 21 documents and 14 ``patternProperties`` in
9.  Of the 26, 13 constrain the key's TEXT (8 ``pattern`` alone, 5 ``pattern`` with
both length bounds), 3 constrain only its LENGTH, 5 name the key type by ``$ref``, 4
close the key set with an ``enum`` -- 3 of those at a RULE position, where
``propertyNames`` states nothing on the model and is admitted, and 1 at a type
position, which refuses -- and 1 is an ``anyOf`` union of key types, which is a row
of its own.  All 14 ``patternProperties`` sites state exactly one expression, so none
reaches the two-pattern refusal, and they split 5 / 7 / 2 on whether the document
CLOSES its keys (see :func:`mapping`'s ``additionalProperties`` arm).  **9 documents
name one of these as their FIRST refusal** (8 on the key ``pattern``, 1 on
``patternProperties``), and all 9 clear: 3 emit and 6 refuse further on, each on
another row's keyword.

**Typed ``additionalProperties`` is implemented and reaches one document**, which is
the opposite case and is why it is built rather than refused: it is this row's named
defect, so the mechanism exists and is graded on documents derived from the bundle's
own nodes with the later steps' keywords removed by name (``tests/test_emit.py``).
Measured: 727 documents mention ``additionalProperties`` and 51 carry a typed one.
"""

from __future__ import annotations

from typing import Any

from codegen import compiler
from codegen.compiler import Decided, Module
from codegen.refusal import Kind, Refusal

#: An ARRAY's own bounds, in the document's spelling, and the ones a field holding
#: the array can carry.  ``uniqueItems`` is deliberately absent, and the reason is
#: measured rather than taken from D6: ``Constraints(uniqueItems=True)`` populates
#: dmcg's ``unique_items`` and the renderer emits NO ``Field`` at all -- bare
#: ``list[str]`` -- because pydantic v2 removed ``unique_items``.  Carrying the
#: keyword through ``constraints=`` would therefore be a model wider than its
#: document, silently.  D6 already puts ``uniqueItems`` in step 7's rule set; this
#: says what the alternative costs.
#:
#: It is absent from this set and ADMITTED BY THE SCREEN anyway
#: (:data:`_ARRAY_HANDLED`), so that :data:`_DISTINCT_HAS_NOWHERE_TO_LIVE` is what
#: reports it -- the ``union.ROOT_HANDLED`` shape, and for that comment's reason.
BOUNDS = ("minItems", "maxItems")

#: What the array row's screen ADMITS, which is its bounds plus the one keyword it
#: refuses by name.  ``uniqueItems`` is in here and lowered nowhere: left out, it
#: refused through ``compiler.check_keywords``, whose answer for a draft-07 keyword is
#: ``DEFERRED_TO_A_LATER_ROW`` -- a promise of a later row, which the two measurements
#: in :data:`_DISTINCT_HAS_NOWHERE_TO_LIVE` say will never be written.  Admitted here,
#: the explicit refusal below is what reports it, with the reason.
#:
#: ``contains`` is in here and lowered nowhere either, and for the OPPOSITE reason to
#: ``uniqueItems``: it is CARRIED rather than refused.  ``contains: S`` says at least one
#: element matches ``S``, which is a statement about which VALUES the array admits -- so
#: D4 leaves it to the schema half exactly as ``lower.rules.ON_A_VALUE`` leaves a ``not``
#: over a ``const`` and ``lower/rules.py`` leaves a conditional that narrows one.
#: ``strict_validate`` validates the payload against the document's own schema and
#: therefore enforces it; it is not in ``harness.FACTS``, so there is no fact for the
#: comparison to find missing; and pydantic has no spelling for it, so there is nothing
#: to render and nothing to drop.
#:
#: **The ceiling, named here rather than discovered later.**  The ``model_validate``
#: CONSTRUCTOR does not enforce it, and no D6 rule can: ``RuleBound`` reads
#: ``__pydantic_fields_set__``, which answers which KEYS are present, and ``contains``
#: is about an array's elements.  So ``X.model_validate(["a"])`` builds for a document
#: whose ``contains`` demands a ``"b"`` while ``X.strict_validate`` of the same payload
#: refuses -- the identical pair ``lower/rules.py`` records for
#: ``core/canvas-constraint.json``.
#:
#: Measured over every node of every portable document: 120 ``contains`` sites in 46
#: documents, **18 on a node whose ``type`` is ``array``** -- what this set admits -- and
#: 102 on a TYPELESS node, which is a ``contains``-only ``allOf`` conjunct or a node
#: inside another ``contains``.  Those 102 are not admitted here and are not this row's
#: position; no document of the deferred population is blocked at one.
_ARRAY_HANDLED = frozenset({"type", "items", "uniqueItems", "contains", *BOUNDS})

#: Why ``uniqueItems`` on an array NO CLASS HOLDS is a VERDICT and not a deferral.
#:
#: D6's rule is where the keyword lives (``lower.rules._distinct``), and a rule lives on
#: a CLASS: ``compiler.fields`` strips the keyword off a property's declaration and
#: carries it on ``Property.distinct``, so 467 of the bundle's 485 sites never reach this
#: row at all.  The 18 that do are the positions with no class above them -- a document
#: root, a ``definitions`` entry, a mapping value, a combinator branch -- and
#: ``lower/rules.py``'s own docstring already states that those keep refusing by name
#: "because a rule has nowhere to live there".
#:
#: The other half is this module's :data:`BOUNDS` comment, measured on the pinned
#: compiler: pydantic v2 removed ``unique_items``, so ``Constraints(uniqueItems=True)``
#: renders bare ``list[str]`` and carrying the keyword through ``constraints=`` would be
#: a model wider than its document, silently.
#:
#: So there is no row to schedule: the one mechanism that enforces the keyword needs a
#: class the position does not have, and the one annotation channel drops it. Measured
#: over every node of every portable document: 485 sites, **all 485 state ``True``**, so
#: there is no ``uniqueItems: false`` arm here and none is written -- a ``false`` is the
#: keyword's own default and would state nothing, and a branch for it would be a
#: derivation matching nothing (D14).  The 18 break down as **4 at a document root, 6 at
#: a mapping value, 5 inside a combinator branch and 3 at a ``definitions``/``$defs``
#: entry**, which is the position list this refusal names, measured rather than copied
#: from ``lower/rules.py``.  19 documents report it as their first refusal.
_DISTINCT_HAS_NOWHERE_TO_LIVE = (
    "uniqueItems is enforced by D6's rule on the CLASS holding the array "
    "(lower.rules._distinct, and compiler.fields strips the keyword off the "
    "declaration to carry it there), and this array has no class above it -- it is a "
    "document root, a definitions entry, a mapping value or a combinator branch, which "
    "is 18 of the bundle's 485 sites.  The one other channel is the annotation, and "
    "pydantic v2 removed unique_items: Constraints(uniqueItems=True) renders bare "
    "list[X], so carrying it there would be a model wider than its document and "
    "silently so.  Neither mechanism reaches this position, so this is a keyword no "
    "row lowers rather than one a later row will"
)

#: A MAPPING's own bounds -- how many keys it may carry -- in the document's spelling,
#: and the ones a field holding the mapping can carry.  The same shape as
#: :data:`BOUNDS` and for the same reason: a bound on the container is the container's,
#: so it rides on the field rather than on ``K`` or ``V``.
#:
#: **Translated by the compiler and not here** (``compiler.KEY_COUNT``), because the
#: translation is pydantic's rather than the document's: dmcg's ``Constraints`` has no
#: ``minProperties`` field at all and silently sets nothing for one, while its length
#: channel renders ``Field(min_length=..., max_length=...)``, which pydantic renders
#: back as ``minProperties``/``maxProperties`` on a ``dict`` -- the document's own
#: spelling, so the comparison needs no row.  Measured on pydantic 2.13.5:
#: ``Annotated[dict[str, int], Field(min_length=1, max_length=4)]`` renders
#: ``{"type": "object", "minProperties": 1, "maxProperties": 4}`` and refuses ``{}``
#: and a five-key object while accepting a one-key one.
#:
#: These are NOT D6 rules even though :data:`compiler.RULE_KEYWORDS` names them, and
#: the difference is the position: D6's ``PropertyCount`` reads a model's
#: ``__pydantic_fields_set__``, and a mapping has no fields -- it is a ``dict`` -- so
#: the rule cannot carry this node's bound and the annotation is the only place it can
#: live.  A node with ``properties`` goes the other way and is step 7's.
KEY_BOUNDS = ("minProperties", "maxProperties")

#: Which constraint keywords each ``type`` can carry, for a node whose ``type`` is a
#: LIST.  draft-07 applies a constraint keyword only to an instance OF the type it is
#: defined for and ignores it for every other type, so a multi-type node means "this
#: keyword on this arm" -- and a keyword no arm can carry constrains nothing at all,
#: so it is refused rather than dropped.  Applying it to every arm instead is the
#: narrowing half of the same defect.
_NUMERIC = frozenset({"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"})
ARM = {
    "string": frozenset({"format", "minLength", "maxLength", "pattern"}),
    "integer": _NUMERIC,
    "number": _NUMERIC,
    "boolean": frozenset(),
    "null": frozenset(),
    "array": frozenset({"items", "uniqueItems", *BOUNDS}),
    "object": frozenset({"properties", "required", "additionalProperties", "propertyNames"}),
}


def _inner(decided: Decided, pointer: str, what: str, mod: Module) -> compiler.Type:
    """The decided type of something INSIDE a container, named where it needs to be.

    A constraint or a format on an inner node has nowhere to go: the compiler's
    ``DataType`` carries neither, so putting the node inside ``list[...]`` or
    ``dict[str, ...]`` would drop the fact and widen the model.  Section 2's answer is
    to NAME the inner type, and ``compiler.carried`` is the one place the three
    positions with no field ask for that name -- an ELEM and a MAPV here, and a union
    BRANCH in ``lower.union``.  A shape the alias module cannot spell still refuses
    there rather than being dropped.  This module's docstring carries the population.
    """
    return compiler.carried(decided, pointer, what, mod)


def _contents(node: dict, pointer: str, symbol: str, what: str, mod: Module) -> compiler.Type:
    """The type of a container's CONTENTS -- its element, or its mapping's value.

    One function for the two, because the two are the same question asked at two
    pointers: the node is a schema of its own, at a pointer of its own, and the
    container is one type word above it.  A container's KEY and a multi-type ARM are
    not that question and do not come here -- an arm is the node RE-CUT to one type,
    so its annotations are the node's own and the field holding the union already
    carries them, and a ``propertyNames`` node is a statement about a key rather than
    a value at a pointer the comparison reads.

    **An ANNOTATION on an inner node had nowhere to go either, and unlike a constraint
    it was dropped in SILENCE.**  :func:`_inner` refuses a constraint and a ``format``
    by name because dropping one would widen the model; a ``description`` narrows
    nothing, so it was dropped with no refusal and no rendering -- and §6 says a
    ``description`` is never folded and that where the comparison reports one the
    EMITTER is what changes.  Measured: ``comparison.missing`` was **4 facts over 4
    pairs**, every one of them ``.../additionalProperties/description`` and every one
    of them ``'Component properties'`` -- ``a2ui/component.json``,
    ``a2ui/surface.json`` and the two ``sponsored-intelligence`` responses that compose
    a surface (``salesagent-j3k2l.28``).

    **The node is NAMED, which is the mechanism this pipeline already has for a node
    whose facts need a carrier.**  ``compiler.name_the_node`` declares the
    ``Annotated`` alias a fragment-referenced node already gets, from the same
    ``_alias_for`` -- so the annotation a container's contents carry and the annotation
    a referenced node carries have ONE spelling, and ``dict[str, X]`` where ``X`` is a
    local symbol is a plain reference the compiler needs nothing extra for.  The name
    is D3's nested rule, already computed by the caller and passed in, so none is
    derived here.

    Gated on the type not being LOCAL already: a node D2 makes a class, or one the walk
    has named, carries its own description in its own declaration, and a second alias
    over it would be a second name for one node (P2).  ``compiler.Module.declare``
    refuses a symbol or a pointer twice by name, so a collision is a refusal rather
    than a silent overwrite.

    What this still drops is every annotation ``_alias_for`` does not carry -- a
    ``default`` on an inner node has no slot on an alias and would still read as
    ``missing``, which is the safe direction and is visible.  0 inner nodes of the
    bundle state one.
    """
    decided = mod.decide(node, pointer, symbol, mod)
    description = node.get("description")
    if not decided.type.local and isinstance(description, str) and description:
        # **The node's OWN name is asked for FIRST, and the order is the P2 rule rather
        # than a preference.**  A described node is named here anyway, and
        # ``_alias_for`` puts the description, the constraints and the ``format`` on
        # that one alias -- so asking :func:`_inner` first would resolve a SECOND name
        # for the same node in ``adcp.types.constraints``, which this declaration then
        # does not reference: two names for one node, and a line in a public module
        # nothing reads.  Measured on ``trusted-match/publisher-tmpx-config.json``,
        # whose described mapping value recorded ``DictMinProperties1MaxProperties2``
        # and then rendered its bound inline under its own name.
        return compiler.name_the_node(mod, symbol, pointer, node, decided).type
    return _inner(decided, pointer, what, mod)


# --------------------------------------------------------------------------- #
# the rows
# --------------------------------------------------------------------------- #
def array(node: dict, pointer: str, name_hint: str, mod: Module) -> Decided:
    """``list[X]``, with ``minItems``/``maxItems`` on the LIST and not on ``X``.

    The bound comes back in the document's own spelling and rides on the field
    holding the list, where dmcg renders it ``Field(min_length=...)`` -- pydantic
    spells a list's length bound the way it spells a string's, and the document does
    not, which is exactly why the two are decided here and spelled by the compiler.
    """
    compiler.check_keywords(node, pointer, set(_ARRAY_HANDLED))  # the walk's own check
    if "uniqueItems" in node:
        # AFTER the screen, so an array carrying BOTH this and a keyword no row lowers
        # is reported on the other one: this refusal is final and that one may not be.
        raise Refusal("uniqueItems", pointer, _DISTINCT_HAS_NOWHERE_TO_LIVE, kind=Kind.VERDICT)
    bounds = {k: node[k] for k in BOUNDS if k in node}
    items = node.get("items")
    if items is None:
        # ``{"type": "array"}`` admits a list of anything, and ``Any`` is that set --
        # the same reading D2 gives a typeless node.  A bound on the list is still
        # the list's, so it is carried.
        return Decided(
            compiler.Type(container="list", of=(compiler.Type("typing.Any"),)), bounds
        )
    if not isinstance(items, dict):
        raise Refusal(
            "items",
            pointer,
            "items is a list, which is draft-07 tuple validation: each position is its "
            "own schema and the shape is a fixed-length tuple, not a list[X]",
            kind=Kind.VERDICT,
        )
    at = f"{pointer}/items"
    element = _contents(items, at, name_hint + "Item", "the element", mod)
    return Decided(compiler.Type(container="list", of=(element,)), bounds)


def mapping(node: dict, pointer: str, name_hint: str, mod: Module) -> Decided:
    """``dict[K, V]`` for an object node that declares no property.

    The node has no field to hang a class on and no property name to derive a class
    name from, so D2 makes it an annotation.  Its VALUE comes from
    ``additionalProperties`` or from the one ``patternProperties`` schema, and its KEY
    from the document (:func:`_key`) -- ``str`` only where the document says nothing
    about keys, which is a faithful reading and not a default.

    **How many keys it may carry is the mapping's own bound**, so it rides on the field
    holding the mapping (:data:`KEY_BOUNDS`), which is where every container bound in
    this module goes.
    """
    compiler.check_keywords(  # the walk's own check
        node,
        pointer,
        {"type", "additionalProperties", "patternProperties", "propertyNames", *KEY_BOUNDS},
    )
    bounds = {k: node[k] for k in KEY_BOUNDS if k in node}
    patterned = node.get("patternProperties")
    if patterned is not None:
        if not isinstance(patterned, dict) or len(patterned) != 1:
            raise Refusal(
                "patternProperties",
                pointer,
                f"{len(patterned) if isinstance(patterned, dict) else '?'} patterns, and a "
                "mapping has one key type: two patterns are a union of key types whose "
                "value types differ per branch, which is a rule and not a dict[K, V]",
                kind=Kind.VERDICT,
            )
        if node.get("additionalProperties", True) is not False:
            # TWO DOCUMENT SHAPES, ONE REFUSAL, and the second arm was dead until
            # this row made the ``patternProperties`` node lower at all.  §5 refuses
            # a non-``false`` ``additionalProperties`` beside ``patternProperties``,
            # and ABSENT is draft-07's ``true``: a key the pattern does not match is
            # then admitted with no value schema, while a typed key REFUSES it -- so
            # a dict[Annotated[str, pattern], V] would be narrower than its document,
            # which is the direction P3 exists to remove.  A typed one is the other
            # arm: two value schemas for one mapping value type.
            #
            # Both are properties of the DOCUMENT, so both are verdicts.  Measured
            # over the 1,054 portable documents, the 14 ``patternProperties`` sites
            # split 5 / 7 / 2: **5 state ``additionalProperties: false``** and are the
            # ones this row lowers; **7 state ``true``**, which this arm already
            # refused before the absent case was added to it; and **2 state nothing**,
            # both at a RULE position (``core/creative-manifest.json
            # #/allOf/1/then/properties/assets`` and
            # ``core/creative-representation.json#/allOf/2/then/properties/assets``),
            # which §5 lowers to nothing anyway -- so the ABSENT arm costs no document
            # and closes a hole rather than refusing one.
            raise Refusal(
                "additionalProperties",
                pointer,
                f"{node.get('additionalProperties', True)!r} beside patternProperties: a "
                "typed one leaves two value schemas for one mapping value type, and a true "
                "or absent one admits every key the pattern does not match, which a typed "
                "key refuses -- the model would be narrower than its document",
                kind=Kind.VERDICT,
            )
        if "propertyNames" in node:
            # Two statements about ONE key type, and the dict carries one.  Not in the
            # bundle at any node, and refused rather than left out: this row reads the
            # ``patternProperties`` expression AS the key (below), so a
            # ``propertyNames`` beside it would be dropped in silence -- the model
            # wider than its document, which is §2's named failure.
            raise Refusal(
                "propertyNames",
                pointer,
                "beside patternProperties, which is two statements about one key type; "
                "a dict[K, V] has one K and this row reads the pattern expression as it",
                kind=Kind.VERDICT,
            )
        # **The expression constrains the KEY, and the key is a type (§2).**  So the
        # expression is handed to :func:`_key`, which is where D5 resolves a key's
        # annotated ``str`` -- one owner for the key rule, so a ``propertyNames``
        # pattern and a ``patternProperties`` pattern cannot come to be read two
        # different ways.  What this row adds over the ``propertyNames`` spelling is
        # only WHERE the expression sits in the document.
        #
        # The two spellings say the same thing and pydantic renders both back as
        # ``patternProperties``, which for THIS one is the document's own keyword --
        # measured on pydantic 2.13.5: ``dict[Annotated[str,
        # StringConstraints(pattern="^x_")], int]`` renders ``{"type": "object",
        # "patternProperties": {"^x_": {"type": "integer"}}}``.  The
        # ``additionalProperties: false`` the document states beside it (5 of the
        # bundle's 14 sites) is what makes the two equivalent -- it closes the keys to
        # the ones the pattern matches, which is what a typed key already says -- and
        # ``harness`` reads both sides into that one shape so the value schema and the
        # key expression are each GRADED rather than excused.
        expr, inner = next(iter(patterned.items()))
        at = f"{pointer}/patternProperties/{compiler.escape_key(expr)}"
        key = _key({"pattern": expr}, f"{pointer}/patternProperties", mod)
        return Decided(
            compiler.Type(
                container="dict",
                of=(_value(inner, at, name_hint, mod, keyword="patternProperties"),),
                key=key,
            ),
            bounds,
        )

    ap = node.get("additionalProperties", True)
    if ap is False:
        raise Refusal(
            "additionalProperties",
            pointer,
            "an object declaring no property and refusing every additional one admits "
            "only the empty object, which is a rule on a value and not a type",
            kind=Kind.VERDICT,
        )
    key = _key(node.get("propertyNames"), f"{pointer}/propertyNames", mod)
    value = _value(ap, f"{pointer}/additionalProperties", name_hint, mod)
    return Decided(compiler.Type(container="dict", of=(value,), key=key), bounds)


def _value(
    node: Any,
    pointer: str,
    name_hint: str,
    mod: Module,
    *,
    keyword: str = "additionalProperties",
) -> compiler.Type:
    """A mapping's value type; ``Any`` for ``true`` and for the empty schema.

    ``true`` and ``{}`` are the same schema -- every value -- and ``Any`` is that set.

    ``keyword`` is which of the two spellings the value was read off, and it exists
    so a refusal names THE DOCUMENT'S OWN WORD: a mapping's value comes from
    ``additionalProperties`` or from the one ``patternProperties`` schema, and a
    refusal reading "additionalProperties is not a schema" at a document that states
    no such keyword is a refusal a reader cannot act on.
    """
    if node is True or node == {}:
        return compiler.Type("typing.Any")
    if not isinstance(node, dict):
        raise Refusal(keyword, pointer, f"not a schema: {node!r}", kind=Kind.VERDICT)
    return _contents(node, pointer, name_hint + "Value", "the value", mod)


def _key(node: Any, pointer: str, mod: Module) -> compiler.Type:
    """A mapping's key type, from the document (D5), with ``str`` the last resort.

    The order is the document's own: a ``$ref`` NAMES the key type, so the key is
    that type and the module imports it; an ``enum`` CLOSES the key set, which D5
    reads as a model rather than a mapping; anything that constrains the key's text
    is a named annotated ``str``, which is D5's alias module (see this module's
    docstring); and silence means ``str``.

    Silence is a reading and not a fallback: the document says nothing about keys, so
    the key is every string, and typing it further would be the SDK inventing a
    constraint the document does not state.

    **A key's LENGTH and a key's PATTERN both lower, and the split that used to be
    here was a statement about the GRADER rather than about the key.**  Both go
    through the walk, so D5's rung 3 names the shape and no spelling is invented
    here.  What differs is only what pydantic renders the resulting ``dict`` as,
    measured on 2.13.5:

    * ``dict[Annotated[str, StringConstraints(min_length=1)], V]`` renders
      ``{"additionalProperties": ..., "propertyNames": {"minLength": 1}}`` -- the
      document's own two keywords, both of them.
    * ``dict[Annotated[str, StringConstraints(pattern=...)], V]`` renders
      ``{"patternProperties": {"<expr>": ...}}`` -- which is the document's own
      keyword where the document spells it ``patternProperties`` (:func:`mapping`),
      and pydantic's own equivalent spelling where the document spells it
      ``propertyNames`` plus ``additionalProperties``.

    The pattern arm REFUSED, as a verdict, on the second of those: the rendering is
    not the document's spelling, so the symmetric comparison reported a rewrite.  Two
    things were wrong with that.  The kind, first -- a class the comparison cannot
    grade is an unwritten comparison row and so a DEFERRAL, never a verdict, which
    names a document's own property.  And then the premise: the two spellings state
    the same thing, so there is one shape to read and the comparison reads it
    (``harness._patterned_key``), which is what §8 means by grading the pair rather
    than excusing it.  The bound ENFORCES either way (``{"AB": 1}`` accepted,
    ``{"abc": 1}`` refused for ``^[A-Z]{2}$``), so what moved is the instrument and
    not the model.
    """
    if node is None:
        return compiler.Type("str")
    if not isinstance(node, dict):
        raise Refusal("propertyNames", pointer, f"not a schema: {node!r}", kind=Kind.VERDICT)
    if "$ref" in node:
        # The one key kind that needs no alias: the bundle already names the type, so
        # P2 applies unchanged -- an import, and no constraint of the target copied.
        return _inner(mod.decide(node, pointer, "", mod), pointer, "the key", mod)
    if "enum" in node:
        raise Refusal(
            "enum",
            pointer,
            f"propertyNames closes the key set to {sorted(map(repr, node['enum']))}, which "
            "D5 reads as a MODEL whose keys are its fields rather than a mapping; its one "
            "type-position site in this bundle is core/store-item.json#/properties/hours, "
            "whose document refuses on enum, so the model would reach no document",
            kind=Kind.VERDICT,
        )
    # Through the walk, so the key is D5's named shape and this row spells nothing: a
    # length-bounded key resolves to ``constraints.StrMinLen1`` and is recorded there,
    # and a key the alias module has no spelling for comes back with its constraints
    # still on it and ``_inner`` refuses by name.  ``type: string`` is supplied where
    # the document leaves it out, because ``propertyNames`` applies to a key and a JSON
    # key is a string: without it the node is typeless and the walk reads it as
    # ``Any``, which would drop the bound.
    return _inner(
        mod.decide({"type": "string", **node}, pointer, "", mod), pointer, "the key", mod
    )


def multi_type(node: dict, pointer: str, name_hint: str, mod: Module) -> Decided:
    """``X | Y`` for a node whose ``type`` is a list, each keyword on its OWN arm.

    An arm is the node re-cut to one type, carrying only the keywords that type can
    carry (:data:`ARM`), and lowered by the same ``decide_type`` as any other node --
    so a string arm gets its ``minLength`` and the ``number`` arm beside it does not.
    That is draft-07's own semantics: a constraint keyword applies to instances of the
    type it is defined for and is ignored for every other type.

    A keyword no arm can carry constrains nothing, and it refuses by name: dropping it
    silently makes the model wider than its document, and applying it to every arm
    makes it narrower.  Both halves of that are this row's named defect.

    **And an arm that DOES carry a constraint refuses, but no longer for the
    rendering's sake.**  The split only exists if the constraint can sit on the arm,
    and the compiler's ``DataType`` carries none -- so before D5's alias module the
    keyword reached the FIELD and bounded the whole union, ``Annotated[str | int,
    Field(min_length=4)]``, applying the string's bound to the integer arm. The alias
    module removed that: ``StrMinLen4 | int`` is what it lowers to, and that model's
    accepted set IS the document's. The refusal stands on the GRADER instead, and the
    body below carries the measurement.

    **A ``null`` arm is an ARM, and it used to refuse on the grader.**  ``None``
    was always a perfectly good arm and the compiler always folded it with D4's own
    ``| None`` on an optional property, so ``str | None`` came out either way; what
    had no answer was GRADING it.  The schema comparison read a model's ``anyOf``
    with one ``null`` branch as D4's rendering of ABSENCE and unwrapped it, so a
    document declaring ``["string", "null"]`` and a document with a merely optional
    ``{"type": "string"}`` compared identically -- and a model that dropped the
    declared null compared identically too.  That is the instrument defect
    ``salesagent-j3k2l.21`` names, and it is fixed where it lived: the comparison
    reads the DOCUMENT at the normalization (``harness._declares_null``) and folds
    the branch into the type list where the document declares one.  So the node is
    graded and the refusal is retired rather than restated with a new reason.

    It was worth 3 documents -- ``core/delivery-metrics.json``,
    ``core/error.json`` and ``core/webhook-activity-record.json`` -- and
    ``["string", "null"]`` is ``str | None``, the most ordinary thing pydantic has.
    """
    kinds = node["type"]
    if not kinds or len(set(kinds)) != len(kinds) or not all(isinstance(k, str) for k in kinds):
        raise Refusal("type", pointer, f"not a set of type names: {kinds!r}", kind=Kind.VERDICT)
    unknown = sorted(set(kinds) - set(ARM))
    if unknown:
        raise Refusal("type", pointer, f"unknown type(s) {unknown}", kind=Kind.VERDICT)
    carried = frozenset().union(*(ARM[k] for k in kinds))
    compiler.check_keywords(  # the walk's own check
        node,
        pointer,
        {"type", *carried},
        f"no arm of {sorted(kinds)} can carry it, so it constrains nothing",
    )
    stated = sorted(set(node) & carried)
    live = [k for k in kinds if k != "null"]
    if stated and len(live) > 1:
        # **A CONSTRAINED arm refuses WHERE MORE THAN ONE ARM IS LIVE, and the reason
        # is the GRADER rather than the rendering.**  D5's alias module removed the
        # rendering obstacle -- the arm's own type carries its own bound, so
        # ``StrMinLen4 | int`` is what this lowers to and the string's keyword no
        # longer reaches the field and bounds the integer arm.  Measured: that
        # model's accepted set IS the document's.
        #
        # What has no answer is grading THAT shape.  ``harness._normalize`` folds a
        # model's ``anyOf`` back into the document's ``type`` LIST only where EVERY
        # branch is a bare ``{"type": X}`` -- a constrained branch is not one, and
        # folding it would throw that branch's constraint away -- so the comparison
        # reads such a model as stating neither the ``type`` list nor the constraint,
        # and reports a faithful node as dropping two facts.  Re-measured on
        # ``{"type": ["string", "integer"], "minLength": 4}`` and on the same node
        # with a ``null`` beside it: ``model_drops_a_fact`` both times, missing
        # ``/type`` and ``/minLength``.
        #
        # **``len(live) > 1`` is the whole of what changed, and it is a measurement.**
        # With exactly ONE live arm the node is ``T | None``, which is case 1 of the
        # fold rather than case 2 -- and case 1 keeps the live branch's OWN keys, so
        # the constraint is compared where it sits.  Measured in both directions on
        # the two documents this gains: ``{"type": ["number", "null"], "minimum": 0,
        # "maximum": 1}`` passes against a faithful model, reports ``/minimum`` and
        # ``/maximum`` against one that drops them and ``/maximum`` against one that
        # widens to ``ge=0`` alone; ``{"type": ["string", "null"], "format":
        # "date-time"}`` passes against ``AwareDatetime | None`` and reports
        # ``/format`` against ``str | None``.  So the node is graded in that shape and
        # refusing it would refuse a document the instrument reads.
        #
        # Emitting a node no check can grade is the widening this pipeline exists to
        # remove, and it still costs no document in the blind shape: 0 multi-type node
        # with two live arms and a constraint sits in a document the emitter reaches.
        # It is lifted the rest of the way by teaching the comparison to compare a
        # constrained union branch-wise, which is the harness's row and not this one's.
        raise Refusal(
            stated[0],
            pointer,
            f"{sorted(kinds)} states {stated} with {len(live)} live arms, which D5's "
            "alias module can now put on an arm's own type -- but the schema "
            "comparison folds a model's anyOf back into a type LIST only where every "
            "branch is a bare type, so a constrained branch beside another live arm "
            "reads as dropping both the type list and the constraint and the node "
            "would be emitted ungraded",
            kind=Kind.DEFERRED,
        )
    arms: list[compiler.Type] = []
    for kind in kinds:
        cut = {"type": kind, **{k: v for k, v in node.items() if k in ARM[kind]}}
        at = f"{pointer}/type/{kind}"  # not a real pointer; it names the ARM that refused
        arms.append(
            _inner(mod.decide(cut, pointer, name_hint, mod), at, f"the {kind!r} arm", mod)
        )
    unique = tuple(dict.fromkeys(arms))  # document order, deduped
    if len(unique) == 1:
        return Decided(unique[0])
    return Decided(compiler.Type(container="union", of=unique))


# --------------------------------------------------------------------------- #
# the dispatch row: a root that is a container
# --------------------------------------------------------------------------- #
def root(doc: dict, symbol: str, pointer: str, mod: Module) -> str:
    """Declare the module for a document whose ROOT is a container.

    A mapping root and a multi-type root have no field to hang themselves on, so D2
    makes each a module-level ``Annotated`` alias -- the same row a scalar root takes,
    and for the same reason: a wrapper class would be a second name for the same node
    (P2) and would put an object on the wire where the document carries a map.

    An array root is D2's ``RootModel[list[X]]`` row and refuses, after lowering its
    element so the refusal reports the element type the row would have wrapped.  This
    module's docstring carries the measurement.
    """
    decided = mod.decide(doc, pointer, symbol, mod)
    if doc.get("type") == "array":
        raise Refusal(
            "type",
            pointer,
            f"a root array is D2's RootModel[list[X]] row and {decided.type.of[0].path or '<a '
            'class>'} is the element type it would wrap; the row is unimplemented because "
            "all five root arrays of this bundle refuse on a keyword of a later step, so "
            "no document would grade it",
            kind=Kind.DEFERRED,
        )
    return compiler.declare_alias(mod, symbol, doc, decided)
