"""D2's container rows: an array, a mapping, a multi-type node, and the roots that
are neither an object with properties nor a scalar.

A container is a node whose SHAPE is one fact and whose CONTENTS are another node.
So every row here is the same two halves -- the contents, lowered by recursing
through ``emit.decide_type``, and the container's own bound, carried on the FIELD
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
* **D5's shared alias module for a constraint the bundle does not name.**  A
  constraint on what is INSIDE a container has no slot in the compiler's
  ``DataType``, and D5's answer is to resolve the inner type to a name: one the
  bundle itself gives a titled root, then one pydantic gives, then an alias we emit
  in one module.  Measured over the reachable population: **1 distinct constraint at
  3 sites in 3 documents**, ``{"type": "string", "pattern": "^[A-Z]{2}$"}`` under
  ``brand/rights-terms.json``, ``brand/search-brands-request.json`` and
  ``property/property-list-filters.json``.  The bundle names it at no titled scalar
  root (checked by content equality over all 229 of them, which is D3's only
  deduplication) and pydantic names no type for it, so only the third rung covers it
  -- a new emitted module, a new import path, and a name D5 requires to be derived
  from the constraint and never from a concept.  Landing that for one constraint is
  the wrong size for this row, so an inner constraint refuses by name with the
  constraint in the detail and D5's alias module is its own step.
* **A closed key set as a model.**  ``propertyNames`` with an ``enum`` closes the
  keys, and D5 reads a closed key set as a model whose keys are its fields.  Its one
  type-position site is ``core/store-item.json#/properties/hours``, and that document
  carries ``enum`` (step 3's keyword), so it refuses before any mapping is lowered.
  :func:`_key` refuses it by name with the key set in the detail.

**Typed ``additionalProperties`` and a typed KEY are implemented and reach no
document**, which is the opposite case and is why they are built rather than refused:
they are this row's named defects, so the mechanism exists and is graded on documents
derived from the bundle's own nodes with the later steps' keywords removed by name
(``tests/test_emit.py``).  Measured: 727 documents mention ``additionalProperties``,
51 carry a typed one, and 0 typed sites and 0 key-constraining sites sit inside a
document this step can emit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from codegen import compiler
from codegen.refusal import Refusal

if TYPE_CHECKING:  # annotations only, so the cycle below has no runtime edge
    from codegen.emit import Decided, Module

#: An ARRAY's own bounds, in the document's spelling, and the ones a field holding
#: the array can carry.  ``uniqueItems`` is deliberately absent, and the reason is
#: measured rather than taken from D6: ``Constraints(uniqueItems=True)`` populates
#: dmcg's ``unique_items`` and the renderer emits NO ``Field`` at all -- bare
#: ``list[str]`` -- because pydantic v2 removed ``unique_items``.  Carrying the
#: keyword through ``constraints=`` would therefore be a model wider than its
#: document, silently.  D6 already puts ``uniqueItems`` in step 7's rule set; this
#: says what the alternative costs.  Absent from this set, it falls through
#: ``emit._check_keywords`` with no special case, which is where every keyword a row
#: does not lower is refused.
BOUNDS = ("minItems", "maxItems")

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


def _emit() -> Any:
    """``codegen.emit``, imported on use rather than at module scope.

    The dispatch is a CYCLE by design -- ``emit`` names these rows and these rows
    lower their children through ``emit.decide_type`` -- and a cycle spelled at
    module scope with ``from x import y`` raises under whichever of the two import
    orders reaches the half-initialised module first.  One accessor, so the reason is
    written once rather than once per function.
    """
    from codegen import emit

    return emit


def _inner(decided: Decided, pointer: str, what: str) -> compiler.Type:
    """The decided type of something INSIDE a container, or a refusal.

    A constraint or a format on an inner node has nowhere to go: the compiler's
    ``DataType`` carries neither, so putting the node inside ``list[...]`` or
    ``dict[str, ...]`` would drop the fact and widen the model.  D5's answer is to
    name the inner type; this module's docstring says why that module is not built
    here and what its population is.  Refusing names the constraint, so the detail
    says what would have to be named.
    """
    if decided.constraints or decided.format is not None:
        stated = {**decided.constraints, **({"format": decided.format} if decided.format else {})}
        raise Refusal(
            sorted(stated)[0],
            pointer,
            f"{what} states {stated} and the compiler carries no constraint inside a "
            "container, so D5 would have to name the type; the bundle names no titled "
            "root with these facts and pydantic names no type for them, so D5's shared "
            "alias module is the row that lowers it",
        )
    return decided.type


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
    emit = _emit()
    emit._check_keywords(node, pointer, {"type", "items", *BOUNDS})  # noqa: SLF001 -- the walk's own check
    bounds = {k: node[k] for k in BOUNDS if k in node}
    items = node.get("items")
    if items is None:
        # ``{"type": "array"}`` admits a list of anything, and ``Any`` is that set --
        # the same reading D2 gives a typeless node.  A bound on the list is still
        # the list's, so it is carried.
        return emit.Decided(
            compiler.Type(container="list", of=(compiler.Type("typing.Any"),)), bounds
        )
    if not isinstance(items, dict):
        raise Refusal(
            "items",
            pointer,
            "items is a list, which is draft-07 tuple validation: each position is its "
            "own schema and the shape is a fixed-length tuple, not a list[X]",
        )
    at = f"{pointer}/items"
    element = _inner(emit.decide_type(items, at, name_hint + "Item", mod), at, "the element")
    return emit.Decided(compiler.Type(container="list", of=(element,)), bounds)


def mapping(node: dict, pointer: str, name_hint: str, mod: Module) -> Decided:
    """``dict[K, V]`` for an object node that declares no property.

    The node has no field to hang a class on and no property name to derive a class
    name from, so D2 makes it an annotation.  Its VALUE comes from
    ``additionalProperties`` or from the one ``patternProperties`` schema, and its KEY
    from the document (:func:`_key`) -- ``str`` only where the document says nothing
    about keys, which is a faithful reading and not a default.
    """
    emit = _emit()
    emit._check_keywords(  # noqa: SLF001 -- the walk's own check
        node, pointer, {"type", "additionalProperties", "patternProperties", "propertyNames"}
    )
    patterned = node.get("patternProperties")
    if patterned is not None:
        if not isinstance(patterned, dict) or len(patterned) != 1:
            raise Refusal(
                "patternProperties",
                pointer,
                f"{len(patterned) if isinstance(patterned, dict) else '?'} patterns, and a "
                "mapping has one key type: two patterns are a union of key types whose "
                "value types differ per branch, which is a rule and not a dict[K, V]",
            )
        if "additionalProperties" in node and node["additionalProperties"] is not False:
            raise Refusal(
                "additionalProperties",
                pointer,
                "beside patternProperties, which leaves two value schemas for one "
                "mapping value type",
            )
        (expr, value_node), = patterned.items()
        key = _key({"type": "string", "pattern": expr}, f"{pointer}/patternProperties", mod)
        at = f"{pointer}/patternProperties/{expr.replace('~', '~0').replace('/', '~1')}"
        value = _value(value_node, at, name_hint, mod)
        return emit.Decided(compiler.Type(container="dict", of=(value,), key=key))

    ap = node.get("additionalProperties", True)
    if ap is False:
        raise Refusal(
            "additionalProperties",
            pointer,
            "an object declaring no property and refusing every additional one admits "
            "only the empty object, which is a rule on a value and not a type",
        )
    key = _key(node.get("propertyNames"), f"{pointer}/propertyNames", mod)
    value = _value(ap, f"{pointer}/additionalProperties", name_hint, mod)
    return emit.Decided(compiler.Type(container="dict", of=(value,), key=key))


def _value(node: Any, pointer: str, name_hint: str, mod: Module) -> compiler.Type:
    """A mapping's value type; ``Any`` for ``true`` and for the empty schema.

    ``true`` and ``{}`` are the same schema -- every value -- and ``Any`` is that set.
    """
    emit = _emit()
    if node is True or node == {}:
        return compiler.Type("typing.Any")
    if not isinstance(node, dict):
        raise Refusal("additionalProperties", pointer, f"not a schema: {node!r}")
    return _inner(emit.decide_type(node, pointer, name_hint + "Value", mod), pointer, "the value")


def _key(node: Any, pointer: str, mod: Module) -> compiler.Type:
    """A mapping's key type, from the document (D5), with ``str`` the last resort.

    The order is the document's own: a ``$ref`` NAMES the key type, so the key is
    that type and the module imports it; an ``enum`` CLOSES the key set, which D5
    reads as a model rather than a mapping; anything that constrains the key's text
    needs a named annotated ``str``, which is D5's alias module (see this module's
    docstring); and silence means ``str``.

    Silence is a reading and not a fallback: the document says nothing about keys, so
    the key is every string, and typing it further would be the SDK inventing a
    constraint the document does not state.
    """
    emit = _emit()
    if node is None:
        return compiler.Type("str")
    if not isinstance(node, dict):
        raise Refusal("propertyNames", pointer, f"not a schema: {node!r}")
    if "$ref" in node:
        # The one key kind that needs no alias: the bundle already names the type, so
        # P2 applies unchanged -- an import, and no constraint of the target copied.
        return _inner(emit.decide_type(node, pointer, "", mod), pointer, "the key")
    if "enum" in node:
        raise Refusal(
            "enum",
            pointer,
            f"propertyNames closes the key set to {sorted(map(repr, node['enum']))}, which "
            "D5 reads as a MODEL whose keys are its fields rather than a mapping; its one "
            "type-position site in this bundle is core/store-item.json#/properties/hours, "
            "whose document refuses on enum, so the model would reach no document",
        )
    emit._check_keywords(node, pointer, {"type"})  # noqa: SLF001 -- every key constraint refuses below
    return compiler.Type("str")


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

    **And an arm that DOES carry a constraint refuses too, which is the same compiler
    gap D5 names and not a third rule.**  The split only exists if the constraint can
    sit on the arm -- ``Annotated[str, Field(min_length=4)] | int`` -- and the
    compiler's ``DataType`` carries no constraints, so the keyword would reach the
    FIELD instead and bound the whole union: ``Annotated[str | int,
    Field(min_length=4)]``, which applies the string's bound to the integer arm.
    Measured on a constructed ``["string", "integer"]`` with ``minLength: 4``, which
    is exactly the narrowing this row exists to remove, so it refuses until D5's
    alias module can name the arm.  It costs nothing today: both multi-type sites in
    the emitted population are bare ``["number", "string"]`` with no other keyword,
    and the 31 others sit in documents refused for another reason.

    **A ``null`` arm REFUSES, and the reason is the grader rather than the
    rendering.**  ``None`` is a perfectly good arm and the compiler folds it with
    D4's own ``| None`` on an optional property, so ``str | None`` comes out either
    way.  What has no answer is grading it: the schema comparison reads a model's
    ``anyOf`` with one ``null`` branch as D4's rendering of ABSENCE and unwraps it,
    because that is what it is at every site the bundle has -- so a document that
    genuinely declares ``["string", "null"]`` and a model that merely has an
    optional property compare identically, and a model that dropped the declared
    null would pass.  Emitting a node no check can grade is the widening this
    pipeline exists to remove, so it refuses by name.  Measured: 0 of the 2
    multi-type sites in the emitted population carry ``null`` (both are
    ``["number", "string"]``), and 31 more sit in documents refused for another
    reason, so this costs no document today.  It is lifted by teaching the
    comparison to tell a declared null from D4's, which needs the DOCUMENT at the
    normalization and is the harness's row, not this one's.
    """
    emit = _emit()
    kinds = node["type"]
    if not kinds or len(set(kinds)) != len(kinds) or not all(isinstance(k, str) for k in kinds):
        raise Refusal("type", pointer, f"not a set of type names: {kinds!r}")
    unknown = sorted(set(kinds) - set(ARM))
    if unknown:
        raise Refusal("type", pointer, f"unknown type(s) {unknown}")
    if "null" in kinds and len(kinds) > 1:
        raise Refusal(
            "type",
            pointer,
            f"{sorted(kinds)} declares null beside {len(kinds) - 1} other type(s), and the "
            "schema comparison cannot tell a DECLARED null from D4's rendering of an "
            "optional property -- it unwraps a single null branch as absence -- so the "
            "node would be emitted ungraded",
        )
    carried = frozenset().union(*(ARM[k] for k in kinds))
    emit._check_keywords(  # noqa: SLF001 -- the walk's own check
        node,
        pointer,
        {"type", *carried},
        f"no arm of {sorted(kinds)} can carry it, so it constrains nothing",
    )
    arms: list[compiler.Type] = []
    for kind in kinds:
        cut = {"type": kind, **{k: v for k, v in node.items() if k in ARM[kind]}}
        at = f"{pointer}/type/{kind}"  # not a real pointer; it names the ARM that refused
        arms.append(_inner(emit.decide_type(cut, pointer, name_hint, mod), at, f"the {kind!r} arm"))
    unique = tuple(dict.fromkeys(arms))  # document order, deduped
    if len(unique) == 1:
        return emit.Decided(unique[0])
    return emit.Decided(compiler.Type(container="union", of=unique))


# --------------------------------------------------------------------------- #
# the dispatch row: a root that is a container
# --------------------------------------------------------------------------- #
def root(doc: dict, symbol: str, mod: Module) -> None:
    """Declare the module for a document whose ROOT is a container.

    A mapping root and a multi-type root have no field to hang themselves on, so D2
    makes each a module-level ``Annotated`` alias -- the same row a scalar root takes,
    and for the same reason: a wrapper class would be a second name for the same node
    (P2) and would put an object on the wire where the document carries a map.

    An array root is D2's ``RootModel[list[X]]`` row and refuses, after lowering its
    element so the refusal reports the element type the row would have wrapped.  This
    module's docstring carries the measurement.
    """
    emit = _emit()
    decided = emit.decide_type(doc, "", symbol, mod)
    if doc.get("type") == "array":
        raise Refusal(
            "type",
            "",
            f"a root array is D2's RootModel[list[X]] row and {decided.type.of[0].path or '<a '
            'class>'} is the element type it would wrap; the row is unimplemented because "
            "all five root arrays of this bundle refuse on a keyword of a later step, so "
            "no document would grade it",
        )
    emit.declare_alias(mod, symbol, doc, decided)
