"""D2's ``const`` row: a node pinning one value becomes ``Literal[value]``.

A ``const`` is a single-member enumeration in JSON Schema's vocabulary, and
``Literal`` is the Python spelling of one.  The row is reached from
``emit._decide`` before ``type`` is read, for the same reason the ``enum`` branch is:
the pinned VALUE is what the node admits, and its own JSON type follows from the
value whether the document spells a ``type`` word or not.

Measured over ``schemas/cache/3.2`` (1,054 portable documents), at every schema
position ``bundle.nodes`` reaches, and each number is an input to a decision below
rather than a result of one:

* **1,486** ``const`` nodes over **347** documents;
* **0** of them at a document ROOT -- which is why this row is not an entry in
  ``emit.ROWS`` and adds no selector to ``codegen.bundle``.  A root carrying one is
  already selected by ``bundle.is_scalar_root`` (its ``type`` names a scalar and it
  declares no kind of its own) and would reach this branch through D2's alias row, so
  the upgrade path for a bundle that grows one is an exclusion clause rather than a
  new row;
* **0** carrying an ``enum`` beside the ``const``, so the two branches do not overlap
  and their order in ``_decide`` is not a precedence;
* the whole key vocabulary is ``const`` (826), ``const type`` (397),
  ``const description type`` (257) and ``const description`` (6).  **Nothing else
  appears beside a ``const`` anywhere in the bundle**, so :data:`CLAIMS` is two
  keywords and the screen has no constraint intersection to resolve;
* **1,310** string values, **161** boolean, **15** integer; no ``null``, no object
  and no array;
* **0** of the 76 pointers a ``$ref`` fragment NAMES land on a ``const`` node, so
  no referrer needs a symbol declared here.

**THE DOCUMENT'S ``type`` WORD IS NOT RESTATED BESIDE THE LITERAL, and restating
it is what would add a fact.**  Measured on the pinned ``pydantic==2.13.5``:
``Literal["x"]`` renders ``{"const": "x", "type": "string"}``, ``Literal[3]``
renders ``{"const": 3, "type": "integer"}`` and ``Literal[True]`` renders
``{"const": true, "type": "boolean"}`` -- it emits ``const`` rather than a
one-member ``enum``, and it emits the type word of its own accord.  So there is
nothing to restate; the only spelling that could add one
(``Annotated[Literal[...], WithJsonSchema(...)]``) would be the emitter writing the
model's schema by hand.

**No comparison row is needed for the 832 TYPELESS const nodes either**, and that
is a measurement rather than a hope.  ``const`` is already in ``harness.FACTS``, so
the document's own pin is compared in both directions; and where the document
states no ``type`` the model states one it does not, which
``harness._entails_type`` already derives FROM THE DOCUMENT'S OWN ``const``
(``_JSON_TYPE.get(type(doc["const"])) == value``).  That rule's docstring was
written for exactly this rendering, and it is gated on the value, so a model
claiming ``integer`` over a string ``const`` still reddens.  Nor does the resolver
undo it: ``canonicalish`` reduces an **enum** node to its ``enum`` alone, dropping
``type`` and ``description``, and leaves a **const** node whole -- probed on four
const shapes and on ``collection/collection-list-changed-webhook.json``, whose
``type`` and ``description`` both survive into the resolved document the package
carries.

**TWO REFUSALS.**  Both come from ``lower.union._literal``, which is where this row
lived while it was scoped to one branch property, and both have a population of 0 in
this bundle:

* a value the compiler has no ``Literal`` for -- an object, an array, a ``null`` or a
  FLOAT.  :data:`LITERALS` is the set and says where it comes from.  The refusal
  earns its keep by ATTRIBUTION rather than by preventing a wrong model: without it
  the run raises a pydantic ``ValidationError`` from inside dmcg, which names no
  document, no pointer and no keyword, and the bead's invariant is that a document
  this emitter cannot lower is refused by all three.  Probed by removing it and
  reading the crash;
* a ``const`` its own ``type`` REFUSES.  Such a node admits NOTHING, and a
  ``Literal`` of the value would be a model wider than its schema.  Decided by the
  document's own validator rather than by a type table of this module's, so there is
  no second reading of draft-07 here to drift from the schema half's.

**KNOWN CEILING**, named rather than coded against because this bundle does not
reach it: a node whose ``type`` word is a SUPERTYPE of the value's own -- the only
such pair left once ``float`` is refused is ``{"type": "number", "const": 3}`` --
passes that validator and renders ``type: integer``, which the comparison reports as
``differs``.  Measured exactly: **0 of the 1,486** const nodes state a ``type`` word
that a one-member ``Literal`` does not render, and 0 state a ``type`` LIST.  The
failure is a reddened gate rather than a silent widening, so the step whose
population reaches one decides between refusing the node and widening the
annotation; a check here today would need a second copy of ``harness._JSON_TYPE``,
which a lowering cannot import (D13) and which is the duplicate that costs more than
the ceiling.
"""

from __future__ import annotations

import jsonschema

from codegen import compiler
from codegen.refusal import Kind, Refusal

#: The cells a ``const`` node CONSUMES -- this row's own coverage, which is what a
#: screen's second argument is once the table decides admission.  Two keywords, because
#: two keywords is the whole vocabulary the bundle writes beside a ``const``;
#: ``description`` is a caller's concern (the parent's field carries it) and the table
#: admits it as the annotation §6 says it is.
CLAIMS = frozenset({"type", "const"})

#: The value types the COMPILER can spell as a ``Literal``, which is where the one
#: refusal about the value itself comes from.  dmcg's ``DataType.literals`` is
#: annotated ``list[Strict[bool] | Strict[int] | Strict[str]]`` on the pinned 0.86.0,
#: so an object, an array, a ``null`` or a FLOAT raises a pydantic ``ValidationError``
#: from inside ``datamodel_code_generator/reference.py`` -- a build crash naming no
#: document, no pointer and no keyword.  Named here with the annotation quoted rather
#: than unpacked from it, because D10 pins the compiler exactly so the set cannot move
#: without a pin bump; ``tests/test_emit.py`` reads the annotation and asserts the two
#: agree, which is the half that cannot go stale.
#:
#: ``null`` has a second reason of its own, and it is why admitting it would be wrong
#: even if the slot took it: ``{"const": null}`` and ``{"type": "null"}`` are ONE node
#: kind written two ways, and ``_decide``'s own ``null`` branch owns it.
#:
#: Measured over the bundle's 1,486 const nodes: 1,310 ``str``, 161 ``bool``, 15
#: ``int`` -- so both refusals have a population of 0 and are reached only by a
#: hand-built node.
LITERALS = (bool, int, str)


def decide(node: dict, pointer: str) -> compiler.Decided:
    """What one ``const`` node IS: the value it pins.

    The ``Literal`` TEXT is the compiler's -- ``compiler.Type.literals`` carries the
    value and dmcg writes the annotation, escapes the value and reports the
    ``typing.Literal`` import.  This row builds no annotation text and takes no
    ``Module``, which is also what fixed a mangling the hand-built spelling had: see
    :attr:`codegen.compiler.Type.literals`.
    """
    value = node["const"]
    if not isinstance(value, LITERALS):
        raise Refusal(
            "const",
            pointer,
            f"a const of {type(value).__name__} has no Literal: the compiler's own slot "
            f"takes {', '.join(t.__name__ for t in LITERALS)} and raises on anything else, "
            "with no document, pointer or keyword in the message",
            kind=Kind.VERDICT,
        )
    if not jsonschema.Draft7Validator(node).is_valid(value):
        raise Refusal(
            "const",
            pointer,
            f"const {value!r} is not a {node.get('type')!r}: the node admits nothing",
            kind=Kind.VERDICT,
        )
    return compiler.Decided(compiler.Type(literals=(value,)))
