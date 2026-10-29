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
* **0** of them at a document ROOT.  A root carrying one would reach this lowering
  through ``emit._decide``'s ``const`` arm like any other node -- §5's "root and
  non-root are one path" -- and ``emit.lower_document`` would then have no class to
  wrap, so the upgrade path for a bundle that grows one is the ROOT cell of this arm:
  §5's ``const`` row already decides it ("where EVERY branch of a root union is a
  scalar ... the root emits as an alias over the union of their types"), read at a bare
  root;
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
claiming ``integer`` over a string ``const`` still reddens.  Nor does resolution
undo it: ``bundle.record`` is this package's own inliner and copies a node with every
key it states, at the referrer as much as at the target -- which is what row .3
closed.  The delegated resolver it replaced reduced any FINITE value set to that set
alone and dropped every annotation at it while inlining, so a ``const`` node kept its
``type`` and ``description`` in its own packaged document and lost both inside a
document referencing it; ``tests/test_emit.py``'s
``test_a_const_node_inlined_through_a_ref_keeps_its_annotations`` is the measurement
on the pair that forced the comparison row now deleted (architecture §9).

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

from typing import Any

import jsonschema

from codegen import compiler, ir
from codegen.schema import nodes
from codegen.refusal import Kind, Refusal

#: The cells a ``const`` node consumes WHATEVER IT STATES -- the pin itself and the type
#: word, which is this row's own coverage independent of any node.  ``description`` is a
#: caller's concern (the parent's field carries it) and the table admits it as the
#: annotation §6 says it is.
#:
#: **The node's own :attr:`nodes.Constant.facts` are claimed BESIDE it**, and they are
#: not listed here because they are not a property of the row: they are whatever
#: constraint of its own value this node states, derived once by the parser from the
#: table (``parse.value_facts``).  :func:`lower` claims them because the PIN DECIDES THEM
#: -- see :func:`decides`.
#: **``format`` is the third, and it is claimed for the same reason the other two are:
#: the row consumes it.**  Measured over the nodes the WALK decides (not the raw bundle):
#: exactly **2** ``const`` nodes state a ``format``, both ``uri``, both at PROP, both
#: produced by §2's intersection rule merging ``core/attestation-reference.json``'s
#: ``claim_type`` -- ``{"type": "string", "format": "uri"}`` -- with a restatement that
#: pins it (``core/rights-constraint.json``, ``core/rights-attestation-evaluation.json``).
#: **0** ``enum`` nodes state one anywhere, which is why ``lower.enum`` grows no such
#: field.  Before this the screen answered them with
#: ``refusal.DEFERRED_TO_A_LATER_ROW`` -- "this step lowers no such keyword (a later D2
#: row does)" -- which is defect row ``10l.35``'s shape exactly: ``format``'s cell LOWERS
#: at every one of the nine positions, so the promised row cannot exist.  What the row
#: owes is :func:`lower`'s ``format`` arm, and the answer is §5's ``format`` row's own
#: fallback and not a deferral.
CLAIMS = frozenset({"type", "const", "format"})

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


def decides(node: nodes.Constant) -> dict[str, Any]:
    """The node's own statements about its value, as the draft-07 schema they are.

    The node's ``type`` word and its :attr:`nodes.Constant.facts` -- every keyword that
    constrains the pinned instance and holds no subschema, derived once by the parser
    from the table (``parse.value_facts``).  Written as a SCHEMA rather than as a set of
    names because the row's answer is a validation and not a reading: the document's own
    validator says whether the pin satisfies the node, so there is no second reading of
    draft-07 here to drift from the schema half's.

    ``{}`` where the node states a bare ``const``, which every value is valid against.

    **A ``format`` is one of these statements** (§5's ``const`` row, decided 2026-10-29,
    ``adcp-client-python-10l.70``): "A ``format`` beside the pin compiles to NOTHING and
    the pin alone is rendered, because a fixed value either satisfies the format or the
    node admits nothing: the pin is checked against the format."  It is not in
    :attr:`nodes.Constant.facts` -- ``parse.value_facts`` excludes it, because the kind
    carries it in a field of its own -- so it is read off that field here, which is the
    one place the node's statements about its value are collected.
    """
    stated = dict(node.facts)
    if node.word is not None:
        stated["type"] = node.word
    if node.format is not None:
        stated["format"] = node.format
    return stated


#: The draft's OWN format checker, which is what makes :func:`decides`'s ``format``
#: entry a check rather than a comment: ``jsonschema`` treats ``format`` as a pure
#: annotation unless it is handed one, so ``Draft7Validator({"format": "uri"})`` is
#: valid for ``"not a uri at all"`` and the row would be ASSUMING the pin satisfies the
#: format -- which is the one thing §5's clause says it must not do.
#:
#: ``Draft7Validator.FORMAT_CHECKER`` and deliberately not ``jsonschema.FormatChecker()``,
#: which is ``harness._validating``'s own reading and for its reason: the global registry
#: carries every checker any draft defines, so it would assert ``uuid`` against a draft-07
#: document, which draft-07 does not define as a format -- the SDK inventing a constraint.
#: The two halves therefore decide this keyword with one vocabulary without this module
#: importing the verifier.
_FORMATS = jsonschema.Draft7Validator.FORMAT_CHECKER

#: Which formats that checker can actually DECIDE, which depends on what is installed
#: (``pyproject`` names ``rfc3339-validator`` and ``rfc3987`` for this bundle's own).
#: Measured on the pinned environment: ``date``, ``date-time``, ``email``, ``idn-email``,
#: ``ipv4``, ``ipv6``, ``iri``, ``iri-reference``, ``regex``, ``time``, ``uri``,
#: ``uri-reference`` -- and ``uri`` is the only one any ``const`` node of this bundle
#: states.  A format OUTSIDE it makes the validator vacuous, so the row refuses rather
#: than reading "valid" off a check that was never made.
_DECIDABLE = frozenset(_FORMATS.checkers)


def lower(node: nodes.Constant, mod: compiler.Module) -> compiler.Decided | Refusal:
    """What one ``const`` node IS: the value it pins.

    The ``Literal`` TEXT is the RENDERER's -- ``ir.TypeRef.literals`` carries the
    value and the model layer writes the annotation, escapes the value and reports the
    ``typing.Literal`` import.  This row builds no annotation text and takes no
    ``Module``, which is also what fixed a mangling the hand-built spelling had: see
    :attr:`codegen.ir.TypeRef.literals`.

    **A CONSTRAINT BESIDE THE PIN IS DECIDED BY THE PIN, and that is one check and not a
    second lowering of the keyword.**  The ``pattern`` cell at PROP lowers ("``pattern``
    on the type, as a named alias"), and a handler answering "a later D2 row does" for it
    promises a row that cannot exist -- the keyword already lowers at every position.
    What the row owes is the intersection, and a one-member value set makes it trivial:
    ``{v}`` intersected with any non-descending constraint is ``{v}`` where the pin
    satisfies the constraint and EMPTY where it does not.  So

    * the pin satisfies it -> ``Literal[v]`` is exactly the document's own set.  Nothing
      is dropped and no approximation is declared, because nothing is approximated: the
      constraint narrows nothing the ``const`` has not already decided, so a model that
      restates it and one that does not admit the same instances.  **KNOWN CEILING, named
      because this bundle does not reach it**: a ``Literal`` renders ``const`` and a type
      word and no ``pattern``, so §8 would report the document's own ``pattern`` as
      *missing* at a pair -- the entailment that already derives a type word FROM the
      ``const`` (``harness._entails_type``) has no clause for a constraint the ``const``
      satisfies.  Population 0 today: the one node the intersection rule reaches is in a
      document refused on its branch names, so no emitted pair carries one, and the step
      whose population reaches one adds the comparison's own row rather than this one
      hiding the fact with a ``WithJsonSchema``;
    * the pin does not -> the node admits NOTHING, and a ``Literal`` of the value would
      be a model wider than its schema.  That is the refusal the row already had for the
      ``type`` word alone, now asked of everything the node states, because the ``type``
      word was never special: it is one of the node's statements about its own value.

    Measured on ``core/postal-country-system.json``: §2's intersection rule merges the
    root's ``{"type": "string", "pattern": "^[A-Z]{2}$"}`` for ``country`` with a branch's
    ``{"const": "US"}``, so the merged node states a ``pattern`` beside the pin -- which
    is why the module docstring's "nothing else appears beside a ``const`` anywhere in the
    bundle" is a measurement of the RAW bundle and not of the nodes the walk decides.
    """
    pointer = node.pointer
    # The node's own facts are claimed BESIDE :data:`CLAIMS`, because the pin decides
    # them: the keyword is consumed here and not deferred to a row that cannot exist.
    refused = compiler.check_keywords(node, CLAIMS | set(node.facts), mod=mod)
    if refused is not None:
        return refused
    value = node.value
    if not isinstance(value, LITERALS):
        return Refusal(
            "const",
            pointer,
            f"a const of {type(value).__name__} has no Literal: the compiler's own slot "
            f"takes {', '.join(t.__name__ for t in LITERALS)} and raises on anything else, "
            "with no document, pointer or keyword in the message",
            kind=Kind.VERDICT,
        )
    # **The node's own statements are the only thing left that can refuse the value.**
    # The screen above admits exactly :data:`CLAIMS`, the node's own facts and the cells
    # that constrain no instance, so by here the node states ``const``, a ``type`` word,
    # its value constraints and annotations -- and a ``const`` validates against its own
    # ``const``.  So the question is whether the rest of the node admits the value, which
    # is what :func:`decides` is.  The keyword each statement is REPORTED by is the
    # document's own, in sorted order, so the report is a function of the document and not
    # of the order a mapping was built in.
    stated = decides(node)
    if node.format is not None and node.format not in _DECIDABLE:
        # **A format the draft's own checker cannot decide leaves the pin UNCHECKED**, and
        # §5's clause rests on the check: "the pin is checked against the format, and
        # where it satisfies it the ``Literal`` is already strictly tighter".  With no
        # checker for the word the validator below is vacuous, so the row would be
        # claiming a drop costs nothing on the strength of a check it never made.  The
        # kind is the CELL's (``format``'s cell lowers at every position), which makes it
        # a DEFERRAL: what is missing is this project's ability to decide the word, not
        # anything the document did.  0 sites over the portable population -- the only
        # format any ``const`` node of this bundle states is ``uri``.
        return Refusal(
            "format",
            pointer,
            f"the pin {value!r} states format {node.format!r} beside it, and section 5's "
            "const row compiles the format to nothing only because the pin IS checked "
            f"against it -- which the draft's own checker cannot do for {node.format!r} "
            f"(it decides {sorted(_DECIDABLE)}), so dropping the keyword here would rest "
            "on a check that was never made",
            kind=compiler.kind_for("format", node.position),
        )
    for keyword, fact in sorted(stated.items()):
        # **The checker is passed, and it is what makes the ``format`` entry a check**
        # (:data:`_FORMATS`).  Every other keyword here is decided by the vocabulary
        # alone; ``format`` is the one draft-07 leaves as an annotation unless a checker
        # is handed over, and a vacuous "valid" is the one answer this loop must not take.
        if jsonschema.Draft7Validator({keyword: fact}, format_checker=_FORMATS).is_valid(
            value
        ):
            continue
        return Refusal(
            "const",
            pointer,
            f"const {value!r} does not satisfy the {keyword} {fact!r} stated beside it: "
            "the node admits nothing",
            kind=Kind.VERDICT,
        )
    # **A ``format`` BESIDE THE PIN COMPILES TO NOTHING and the pin alone is rendered**,
    # which is §5's ``const`` row as decided on 2026-10-29 (``adcp-client-python-10l.70``):
    # "because a fixed value either satisfies the format or the node admits nothing: the
    # pin is checked against the format, and where it satisfies it the ``Literal`` is
    # already strictly tighter than any type the format would select, while where it does
    # not the node is §5's empty intersection and refuses upstream.  So no fact is dropped
    # and §8 grades the ``format`` as not rendered at this co-occurrence."
    #
    # **This REPLACES the arm that rode it** as ``json_schema_extra={"format": …}``, and
    # the two readings differ on one question: is the ``format`` a fact the pin DROPS?
    # The riding arm said it was not dropped because it was rendered.  §5's answer is that
    # there is nothing to drop -- the check above has already proved the pinned value
    # satisfies the format, so the set the ``format`` admits intersected with ``{v}`` IS
    # ``{v}``, and ``Literal[v]`` is that set exactly.  A rendered ``format`` beside it
    # states a constraint of a WIDER set than the one the node has, which is a fact about
    # no instance this node admits.
    #
    # So the ``format`` reaches :func:`decides` instead of :attr:`compiler.Decided.format`,
    # and the division between the two carriers is gone: every statement this node makes
    # about its value is one thing, checked in one loop, and the pin decides all of it.
    return compiler.Decided(ir.TypeRef(literals=(value,)))
