"""A consumer-facing base for a DRIFTED family: one type the family's classes share.

The bundle repeats one envelope at 26 nodes and spells it twelve ways.  Every one of them
states exactly ``{context, errors, ext}`` with ``required: ["errors"]``; ``ext`` is
byte-identical at all 26 and ``context`` is the same bare ``$ref`` at all 26 once an
annotation sibling is dropped, so the pattern is uniform by intent.  ``errors`` is not:
``minItems: 1`` at 21 of them and absent at 5 (every one under ``content-standards/``),
and ``items`` a bare ``$ref`` to ``core/error.json`` at 25 with one composing it.

**So the 26 do not share an accepted set, and the divergence is real on a real
instance.**  Measured against the branch node the pairing grades a branch class at
(``harness.Pair``, through ``applied_schema``):
``brand/creative-approval-response.json#/oneOf/3`` REFUSES
``{"errors": [], "status": "completed"}`` and
``content-standards/calibrate-content-response.json#/oneOf/1`` ACCEPTS it.  A base
claiming to be the authority for all 26 would therefore be wrong about 21 of them in one
direction or 5 in the other, whichever way it spelled the bound.

What this module declares is a base that claims nothing about acceptance: it carries
``context``, ``errors`` and ``ext`` and **no** ``__adcp_schema__``, so the pairing --
``issubclass(value, SchemaBound) and "__adcp_schema__" in value.__dict__``, over the
modules of ``adcp.types._schemas`` -- never reaches it, on any of three counts: it
declares no ``__adcp_schema__``, it is not a ``SchemaBound`` at all (:data:`MODEL`), and
it is not in that package.  It is not graded, it is not a conformance claim, and
``strict_validate`` does not resolve on it.
The 26 concrete classes keep their own ``__adcp_schema__``, their own ``strict_validate``
and their own ``minItems`` -- 21 tight, 5 loose, each faithful to its own document -- and
those are the things a pair grades.  **A consumer gets ergonomics; the concrete class still
decides acceptance.**

*Why not normalise the bundle instead.*  Giving the five the ``minItems: 1`` the other 21
state makes ``strict_validate`` for them accept ``{"errors": []}``, which their documents
refuse -- the SDK would accept what the protocol rejects.  §1 of the semantics document
draws exactly that line ("a patch that changes acceptance is not a patch, it is a fork of
the protocol") and §3 says the record is the bundle's document with its references inlined
and NOTHING else changed.  The upstream half is filed as ``adcontextprotocol/adcp#8516``;
these classes are needed before it lands, and when it lands the 26 nodes become equal,
§4's content dedup collapses them to one class with no further work, and this base becomes
redundant rather than needing to be unwound.

*Why nothing is approximated.*  Nothing is dropped.  Every member keeps its own constraint
on its own class, so no annotation is wider than its document and there is no fact to
declare.  The base's own annotations are graded against nothing, because the base names no
document.

**THE SET IS DERIVED AND THE MEMBERSHIP TEST IS THE SHAPE.**  ``bundle.is_an_envelope`` is
a predicate over ONE node -- its ``properties`` keys and its ``required`` list -- and
``bundle.envelopes`` is the set, a function of the BUNDLE in the way ``bundle.named`` is
and never of the run's document set.  So a member's module is the same text whether the
run emits one document or the whole bundle (§9: "do not decide one document's output by a
census over the run"), and a 27th envelope added upstream joins the family by stating the
shape rather than by being added to a list.  The derivation lives in the SOURCE layer
because §11 puts "every fact derived from a document" there and §4 makes
``schema/parse.py`` the one reader of a raw mapping; this module holds values and
declarations and no mapping at all.

**The base's own shape is derived too, by one rule at every property**
(``bundle.envelope_shape``): the base states the SHORTEST descent path at whose end every
member references one and the same bundle document, and the type is that document's symbol
wrapped in the containers the path's positions name (:data:`CONTAINERS`).  Measured over
bundle 3.2:

| property | path | document | the base states |
| --- | --- | --- | --- |
| ``errors`` | ``(ELEM,)`` | ``core/error.json`` | ``list[Error]`` |
| ``context`` | ``()`` | ``core/context.json`` | ``ContextObject \\| None`` |
| ``ext`` | ``()`` | ``core/ext.json`` | ``ExtensionObject \\| None`` |

``media-buy/sync-catalogs-response.json`` is the member whose ``errors`` element COMPOSES
``core/error.json`` rather than referencing it bare: its path is ``(ELEM, CONJ)``, which
has the family's ``(ELEM,)`` as a prefix, and §2's ``allOf`` row makes that conjunct a
BASE -- so its element class is a SUBCLASS of ``Error`` (asserted, not assumed) and the
base's annotation is a supertype of its own rather than a claim about it.  That is the
whole reason the rule takes a prefix: a member may say MORE about a property than the
family agrees on, and saying more is subclassing.

Every keyword the members do not agree on -- ``minItems``, each one's ``description``, the
conditional refinement on one element -- is simply not among the facts the rule reads, so
the base states none of them.  **That is what a consumer can and cannot rely on**, and it
is the drift made visible rather than papered over.

*Scope: this family and no other.*  126 property-key sets in the bundle are shared by
non-identical nodes and at least two more look like the same drift.  Generalising needs a
derivable rule for WHICH families qualify, and a hand-written list of families is the
defect §9 names.  One family, by its shape.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import replace

from adcp.types._base import SchemaRef
from codegen import ir
from codegen.bundle import Agreed, Envelope
from codegen.keywords import Position
from codegen.lower import names
from codegen.refusal import BuildFailure

#: The symbol every member's class takes as a base, and the module it is declared in.
#: The package is :data:`codegen.ir.BASE_MODULE`'s, so the dotted path has one declaration
#: between its three readers: :func:`adopt`'s import, the run's file name, and
#: ``render._import_rank``'s grouping.
#:
#: It is PUBLIC, beside ``adcp.types.constraints``, for the reason §1 of the semantics
#: document gives that module: what it holds has no document, so there is no document
#: module for it to be reached through, and a consumer annotating application code has
#: one path to it and no second spelling.
BASE = "FailedResponse"
MODULE = f"{ir.BASE_MODULE.rsplit('.', 1)[0]}.envelopes"

#: **The base's own base: the model layer's plain ``BaseModel``, and NOT
#: ``AdCPBaseModel``.**  Named and not imported, which §8 permits ("naming a symbol is
#: not a Pydantic idiom; constructing a ``Field``, a ``ConfigDict``, an ``Annotated`` or
#: a ``DataType`` is").
#:
#: ``AdCPBaseModel`` IS the schema binding -- it carries ``__adcp_schema__``,
#: ``strict_validate`` and the rule tuple, and the pairing's predicate is
#: ``issubclass(value, SchemaBound)`` -- so a base that must never be a pair must not be
#: one.  Three consequences and every one of them is wanted: the base is outside the
#: pairing by TYPE and not only by a missing attribute; ``strict_validate`` does not
#: resolve on it at all rather than resolving onto a reference it does not have; and its
#: ``model_config`` is EMPTY.
#:
#: The third is measured and it is why the row could not take the obvious base.
#: Pydantic merges a model's bases' configs in order and the last one wins, and
#: ``AdCPBaseModel`` states §2's ``extra: ignore`` explicitly -- so an ``AdCPBaseModel``
#: appended to a branch's bases imposes ``ignore`` on every member whose own node states
#: no ``additionalProperties``, and the three emitted members of the loose group lost the
#: ``additionalProperties: true`` their own documents state.
#: A base that states a policy no document of the family states is §2's
#: "no generated class carries a policy that is not in its document", and an empty config
#: is what not stating one means.
MODEL = "BaseModel"
MODEL_MODULE = "pydantic"

#: The container a descent hop puts around the type below it, keyed by the position the
#: table's descent column assigned the hop.  ELEM is "an array's ``items``" (§3), so the
#: holder is a list; a path through any other position has no decided rendering here and
#: is a ``BuildFailure`` rather than a guess.
CONTAINERS: Mapping[Position, str] = {Position.ELEM: "list"}

#: The base's docstring, which is what a consumer reads first and so says both halves:
#: what the type is for, and what it is not.  Written here rather than in ``render.py``
#: because it is a statement about the FAMILY, and the renderer writes text about nothing.
DESCRIPTION = (
    "The envelope a failed response carries, as one type to program against. "
    "A CONSUMER CONVENIENCE and not a conformance claim: it carries no __adcp_schema__, "
    "so nothing grades it and strict_validate does not resolve on it. The concrete class "
    "for a document decides what that document accepts, and the documents do not agree -- "
    "21 of them require at least one error and 5 accept none, so a base claiming to be "
    "the authority for all of them would be wrong about one group or the other. What this "
    "states is what every document of the family states alike: an errors list of Error, "
    "an optional context and an optional ext. What it does not state is any document's "
    "own bound on errors, which lives on the concrete class -- the same class "
    "strict_validate runs. Upstream: adcontextprotocol/adcp#8516."
)


def base(
    shape: Sequence[Agreed],
    binding: Mapping[str, tuple[str, str]],
    reserved: frozenset[str] = frozenset(),
) -> tuple[ir.ClassDecl, frozenset[tuple[str, str]]]:
    """The base's declaration and the imports its annotations name.

    ``shape`` is ``bundle.envelope_shape``'s answer -- what every member states alike --
    and ``binding`` is ``document -> (module, symbol)`` for every document it reached,
    handed IN by the run: the source layer decides the family, this module decides the
    DECLARATION, and the run already knows where it writes a document's module and what
    symbol it declares there, so neither path nor symbol is derived twice.  ``reserved``
    is the model layer's own attribute set, handed in the same way and for
    ``names.field_name``'s reason: a property key spelling one of them is carried under an
    alias, and ``render.RESERVED`` is the one reading of what the model layer carries.

    ``ref`` is ``None``, which is the whole of the row: a declaration with no
    ``SchemaRef`` names no document, so ``render.klass`` writes no ``__adcp_schema__``
    line and the pairing has nothing to reach.
    """
    fields: list[ir.Field] = []
    imports: set[tuple[str, str]] = {(MODEL_MODULE, MODEL)}
    for one in shape:
        module, symbol = binding[one.target]
        imports.add((module, symbol))
        decided = ir.TypeRef(symbol, local=True)
        for position in reversed(one.path):
            container = CONTAINERS.get(position)
            if container is None:
                raise BuildFailure(
                    f"the envelope family reaches {one.target} at {one.key!r} through "
                    f"{position}, which names no container a base can write"
                )
            decided = ir.TypeRef(container=container, of=(decided,))
        fields.append(
            ir.Field(
                name=names.field_name(one.key, reserved),
                wire=one.key,
                type=decided,
                required=one.required,
                default=ir.MISSING if one.required else None,
            )
        )
    return (
        ir.ClassDecl(
            name=BASE,
            ref=None,
            fields=tuple(fields),
            description=DESCRIPTION,
            # Named as a LOCAL symbol, which is what a base always is here: the renderer
            # writes the name and the module writer supplies the import, exactly as it
            # does for a base another document declares.
            bases=(ir.TypeRef(MODEL, local=True),),
        ),
        frozenset(imports),
    )


def adopt(module: ir.Module, members: Collection[Envelope]) -> ir.Module:
    """Every member class of ``module`` takes the family's base.

    A pass over the FINISHED module, in the shape ``lower/names.py`` is one, and it runs
    there rather than inside a handler because the fact is a property of a class's whole
    node and not of any one keyword on it.  ``members`` is ``bundle.envelopes``' answer
    narrowed to nothing in particular -- the whole family -- and a declaration is a member
    when the node its own ``SchemaRef`` NAMES is in it, so the test is the shape at the
    very node the class is graded against.  Nothing here reads a document.

    The base goes LAST among the bases, because §4 puts the union's base first -- it is
    what supplies the dispatch -- and every one of the 26 members is a union branch.

    A module with no member is returned unchanged, so no module gains an import of a
    symbol it does not name.
    """
    taken = ir.TypeRef(BASE, local=True)
    at = frozenset(members)
    declarations: list[ir.Declaration] = []
    found = False
    for declaration in module.declarations:
        if isinstance(declaration, ir.ClassDecl) and _site(declaration.ref) in at:
            declaration = replace(declaration, bases=(*declaration.bases, taken))
            found = True
        declarations.append(declaration)
    if not found:
        return module
    return replace(
        module,
        declarations=tuple(declarations),
        imports=module.imports | {(MODULE, BASE)},
    )


def _site(ref: SchemaRef | None) -> Envelope | None:
    """A declaration's reference as the ``(document, pointer)`` the family is keyed by.

    ``SchemaRef`` spells a pointer with the document's own ``#`` in front
    (``compiler.schema_ref``) and ``bundle.nodes`` spells one without, so the one character
    is dropped here -- the same reading the verifier makes of the same field.  A
    declaration with no reference is no document's node and so no member: that is the
    envelope base itself, which must not take itself as a base.
    """
    if ref is None:
        return None
    return Envelope(ref.document, ref.pointer.lstrip("#"))
