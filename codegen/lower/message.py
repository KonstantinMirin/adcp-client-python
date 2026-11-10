"""The two MESSAGE bases: one type every request shares and one every response shares.

``codegen/lower/envelope.py`` is the row this one is written beside, and the difference
between them is where the set comes from.  An envelope's family is derived from a NODE's
shape, because the bundle states the envelope twenty-six times and names it nowhere.  A
task message is the opposite: the bundle NAMES it, in ``manifest.json``'s tools map, and
``manifest.schema.json`` makes ``request_schema`` and ``response_schema`` required on
every entry -- so the set is read off the registry and the shape is not consulted at all.
``codegen/bundle.REGISTRY_SCOPE`` is the sentence, and ``lower/composition.py``'s D7 row
wrote it before there was a reader: "a base is DERIVED from what the document composes,
so there is no marker policy and no filename to classify ... which is also how
``AdcpRequest``/``AdcpResponse`` reach a task message -- through the task registry naming
the document, never through its path."

**THE BASES STATE NO FIELD, AND THAT IS THE ROW RATHER THAN A SHORTCUT.**  Every one of
the 78 requests already composes ``core/version-envelope.json`` or states its fields
inline, and 78 responses compose ``core/protocol-envelope.json``; those two are
GENERATED classes from their own documents and they already arrive as bases by §2's
``allOf`` row.  A field restated here would be the same fact in two classes, which is
exactly what §4 forbids -- "a type stated at more than one position is written once and
referenced, never restated".  So what these two add is a NOMINAL supertype and nothing
else: ``isinstance(x, AdcpRequest)`` answers "is this the request half of a task", which
no composed envelope answers, because a response composes the version envelope too.

*Why nothing is approximated.*  Nothing is dropped and nothing is stated.  A base with no
field says nothing about any instance, so no annotation is wider than its document and
there is no fact to declare.  The figure the gate reports cannot move for this row, and
if it does the move is a defect and not a consequence.

**NEITHER BASE IS A PAIR**, for ``lower/envelope.py``'s three reasons and measured the
same way: ``ref`` is ``None`` so ``render.klass`` writes no ``__adcp_schema__``;
:data:`MODEL` is pydantic's plain ``BaseModel`` so neither is a ``SchemaBound`` and
``strict_validate`` does not resolve on it; and both are declared beside ``_schemas``
rather than inside it, which is the package the pairing walks.  The empty
``model_config`` matters here for the same measured reason it matters there: six of the
78 requests state no ``additionalProperties`` of their own and base on ``AdCPBaseModel``
directly, and a base carrying §2's ``extra: ignore`` would impose a policy their
documents do not state.

**THE BASE GOES LAST**, which is ``lower/envelope.py``'s rule and is load-bearing here on
a measured failure: four request roots carry ``BranchDispatchMixin`` first because they
are union roots, and one carries a second composed base, and a model base placed ahead of
a composed one "puts a class before two of its own subclasses and Python refuses to build
it" (``lower/composition.py``'s own measurement over ten response documents).
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import replace

from adcp.types._base import SchemaRef
from codegen import ir
from codegen.lower import envelope

#: The two symbols, and the module they are declared in -- which is ``envelopes.py``,
#: beside ``_schemas`` and not inside it.  One beside-file holds every base that belongs
#: to no document: a second module would be a second import path for a consumer to learn
#: and a second artifact for ``tests/fresh.py`` to account for, and the thing the two rows
#: have in common -- a base with no ``__adcp_schema__`` -- is the thing the module is.
REQUEST = "AdcpRequest"
RESPONSE = "AdcpResponse"
MODULE = envelope.MODULE

#: **UPSTREAM'S OWN TWO MARKERS, RE-EXPORTED AND NOT SUBCLASSED**
#: (`adcp-client-python-1zmw`, extended; the subclass was measured first and the
#: measurement is what overturned it).  ``adcp/types/base.py`` is upstream's hand-written
#: file restored at upstream's own path byte for byte, and it declares these same two
#: words.
#:
#: **A SECOND DECLARATION OF ONE WORD IS A SECOND TYPE, WHICH IS THE ONE THING THE ALIAS
#: CLAUSE FORBIDS** -- "an alias is a name and never a second type".  A subclass here
#: satisfies ``issubclass`` and still fails IDENTITY, so
#: ``adcp.types.AdcpRequest is adcp.types.base.AdcpRequest`` was false and
#: ``tests_emit/test_the_restored_flat_surface.py`` said so.  Re-exporting is the stronger
#: property and the smaller artifact at once: one object per word, identity by
#: construction, and a declaration DELETED rather than added.
#:
#: **AND IT COSTS NOTHING, measured rather than argued.**  What a declaration of ours
#: added over upstream's was ``model_fields == {}``, ``model_config == {}``, no
#: ``__adcp_schema__`` and not a ``SchemaBound`` -- that is, nothing but being a
#: ``BaseModel``.  Nothing needs that: every one of the roots that takes one of these
#: already carries ``AdCPBaseModel``, so the marker is never the only model base.
#:
#: **UPSTREAM'S OWN TREE IS THE PROOF THAT A PLAIN MIXIN WORKS HERE.**  Their
#: ``_AdcpMessage`` docstring says it "declares no fields and is not a ``BaseModel``", and
#: their generated ``media_buy/create_media_buy_response.py`` still writes
#: ``class CreateMediaBuyResponse1(AdcpResponse, AdcpVersionEnvelope, ProtocolEnvelope)``.
#: A plain mixin beside a pydantic base is their shipped arrangement, not an experiment.
#:
#: That also retires this row's reading of ``envelope.MODEL``: there is no base of OURS
#: left for a ``model_config`` to leak out of, so §2's "no generated class carries a
#: policy that is not in its document" holds here by there being no class.
#:
#: The word equals the symbol, which is what makes the import a RE-EXPORT rather than a
#: use: ``render._import_block`` writes ``X as X`` for a triple whose word is its symbol,
#: which is also PEP 484's spelling of a deliberate re-export.
UPSTREAM_MODULE = "adcp.types.base"
UPSTREAM = (REQUEST, RESPONSE)

#: The model base a root is given when it composes nothing, which is the default
#: ``render.klass`` hands the generator as ``custom_base_class`` -- said here because
#: naming any base at all replaces that default (:func:`adopt`, and
#: ``ir.ClassDecl.bases``' own docstring).  It is ``AdCPBaseModel`` and NOT
#: ``envelope.MODEL``: this is a document ROOT carrying ``__adcp_schema__``, so §2's
#: pairing has to be able to reach it, and the pairing's predicate is
#: ``issubclass(value, SchemaBound)``.  The opposite choice is the right one for an
#: envelope BASE, which must never be a pair, and ``lower/envelope.MODEL``'s docstring is
#: that reading -- the two rows differ because one names a document and the other names
#: none.
MODEL = "AdCPBaseModel"

#: What a consumer reads first, so each says both halves -- what the type is for and what
#: it is not.  Here rather than in ``render.py`` because it is a statement about the
#: REGISTRY, and the renderer writes text about nothing.
#:
#: MODULE PROSE and no longer a class docstring, because the thing it describes is no
#: longer a class of ours (:data:`UPSTREAM`).  The facts are the registry's either way --
#: which documents the manifest names at a tool's ``request_schema``, and that the 39 at
#: ``async_response_schemas`` are a task RESULT rather than the answer to the call -- and
#: a reader of ``envelopes.py`` needs them whether the name there is declared or imported.
#: WRAPPED at the source, because this text becomes LINES of an emitted docstring and the
#: artifact is linted like every other file in the tree -- a paragraph assembled from
#: implicitly concatenated fragments arrives as one 300-column line.
PROSE = "\n".join(
    [
        "**The two task-message markers are UPSTREAM'S OWN, re-exported here.**  They are",
        "declared in ``adcp.types.base``, which is upstream's hand-written module restored",
        "at upstream's own path, and the name here IS that object -- not a subclass of it --",
        "so ``isinstance`` and identity both hold against either spelling.",
        "",
        "``AdcpRequest`` is the request half of a task.  Every document the bundle's",
        "``manifest.json`` names at a tool's ``request_schema`` takes it as a base, so",
        "``isinstance(x, AdcpRequest)`` answers 'is this a call' -- which no composed",
        "envelope answers, because a response composes the version envelope too.  It states",
        "no field, because every field a request shares is already stated by",
        "``core/version-envelope.json`` and restating it would be one fact in two classes.",
        "",
        "``AdcpResponse`` is the response half.  Every document the manifest names at a",
        "tool's ``response_schema`` takes it; every field a response shares is already",
        "stated by ``core/protocol-envelope.json`` and ``core/version-envelope.json``,",
        "which arrive as bases from the document's own ``allOf``.  The 39 documents the",
        "manifest names at ``async_response_schemas`` are a task RESULT rather than the",
        "answer to the call and do not take this base.",
        "",
        "Neither carries ``__adcp_schema__``, so nothing grades either and",
        "``strict_validate`` does not resolve on them; the concrete class for a document",
        "decides what that document accepts.",
    ]
)


def bases() -> tuple[frozenset[tuple[str, ...]], str]:
    """The two RE-EXPORTS and the prose that explains them -- and no declaration at all.

    No argument, which is the row: an envelope's base needs its family's agreed shape
    handed in because its fields are derived from it, and these two state no field, so
    there is nothing about the bundle for this function to be told.  The SET the bases are
    given to is still the registry's and still a function of the bundle
    (``bundle.task_messages``); it is :func:`adopt` that reads it.

    **IT RETURNS NO ``ClassDecl``**, which is :data:`UPSTREAM`'s whole point and is the
    one way this row stopped resembling ``lower/envelope.py``'s.  A re-export is
    ``(module, symbol, word)`` with the word equal to the symbol -- the form
    ``render._import_block`` writes as ``X as X`` -- and ``render.envelopes_module`` puts
    that word in ``__all__``, so the module still PROMISES both names while declaring
    neither.  The declared-class count therefore falls by two and the emitted count
    cannot move: a class that declared nothing was never a document's emission.
    """
    return (
        frozenset((UPSTREAM_MODULE, name, name) for name in UPSTREAM),
        PROSE,
    )


def adopt(
    module: ir.Module, requests: Collection[str], responses: Collection[str]
) -> ir.Module:
    """Every ROOT class of ``module`` whose document the registry names takes its base.

    A pass over the FINISHED module, in the shape ``lower/names.py`` is one, for
    ``lower/envelope.adopt``'s reason: the fact is a property of which document a class
    is the root of and not of any keyword on it.

    **The ROOT and only the root**, which is the one way the membership test differs from
    the envelope family's.  The registry names a DOCUMENT, and the thing a task sends is
    that document's root -- an inner node of a request document is a component of the
    call and not the call.  A root's ``SchemaRef`` spells its pointer ``"#"``
    (``compiler.schema_ref``), so the test is that the stripped pointer is empty, and a
    declaration with no reference is no document's node at all.

    The base goes LAST among the bases (``lower/envelope.adopt``'s rule), and the two
    sets are disjoint by ``bundle.task_messages``' own refusal, so no module adds both to
    one declaration.

    **AND A ROOT WITH NOTHING TO COMPOSE IS GIVEN :data:`MODEL` EXPLICITLY, because
    naming any base at all replaces the default one.**  ``ir.ClassDecl.bases`` says so in
    its own docstring -- "Empty leaves ``custom_base_class``, which is ``AdCPBaseModel``
    ... a non-empty tuple replaces it, and ``AdCPBaseModel`` arrives through the bases
    because every base is itself an emitted class ... a caller that wants
    ``AdCPBaseModel`` in the list says so".  Upstream's marker is the first base this
    emitter ever appended that is NOT an emitted class, so this row is the first that has
    to say so, and the two documents it reaches are the only two task messages that
    compose no envelope: ``creative/validate-input-request.json`` and
    ``brand/search-brands-request.json``.

    Measured, and the reason this clause is not cosmetic: without it those two roots
    carried upstream's plain marker as their ONLY base, so they were not pydantic models
    at all -- no ``model_fields``, no ``model_validate``.  It was latent before the marker
    became upstream's, because ours happened to subclass ``BaseModel``; what was NOT
    latent even then is that both roots carry ``__adcp_schema__`` and were never
    ``SchemaBound``, so ``strict_validate`` did not resolve on either and §2's pairing
    never graded those two documents.  This clause closes both.

    Their own ``model_config`` states ``extra='allow'``, so :data:`MODEL`'s policy cannot
    reach them -- which is the measured hazard ``lower/envelope.MODEL`` is about, checked
    here rather than assumed: a census of all emitted classes moves no ``extra`` value.

    A module with no named document is returned unchanged, so no module gains an import
    of a symbol it does not name.
    """
    wanted = {REQUEST: frozenset(requests), RESPONSE: frozenset(responses)}
    declarations: list[ir.Declaration] = []
    taken: set[str] = set()
    supplied = False
    for declaration in module.declarations:
        if isinstance(declaration, ir.ClassDecl):
            at = _root_document(declaration.ref)
            for name, documents in wanted.items():
                if at is not None and at in documents:
                    composed = declaration.bases
                    if not composed:
                        composed = (ir.TypeRef(MODEL, local=True),)
                        supplied = True
                    declaration = replace(
                        declaration, bases=(*composed, ir.TypeRef(name, local=True))
                    )
                    taken.add(name)
        declarations.append(declaration)
    if not taken:
        return module
    # **THE IMPORT FOR :data:`MODEL` IS REPORTED HERE** and only where a root actually
    # took it.  The renderer adds no import for a base -- ``ir.TypeRef.local``'s own rule,
    # "a cross-document import is the module writer's" -- and measured, the two modules
    # this clause reaches differ: ``creative/validate_input_request`` already imports
    # ``AdCPBaseModel`` for an inner class, and ``brand/search_brands_request`` has no
    # other class that names it, so without this line that module raised
    # ``NameError: name 'AdCPBaseModel' is not defined`` at import.
    owed = {(MODULE, name) for name in taken}
    if supplied:
        owed.add((ir.BASE_MODULE, MODEL))
    return replace(module, declarations=tuple(declarations), imports=module.imports | owed)


def _root_document(ref: SchemaRef | None) -> str | None:
    """The document a declaration is the ROOT class of, or ``None`` if it is not one.

    ``SchemaRef`` spells a pointer with the document's own ``#`` in front
    (``compiler.schema_ref``), so the root's is ``"#"`` and every inner node's is
    ``"#/..."``; the one character is dropped here, the same reading
    ``lower/envelope._site`` makes of the same field.  A declaration with no reference is
    the base itself, which must not take itself as a base.
    """
    if ref is None or ref.pointer.lstrip("#") != "":
        return None
    return ref.document
