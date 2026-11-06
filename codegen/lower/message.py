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

#: The bases' own base, and the reason is :data:`codegen.lower.envelope.MODEL`'s entire
#: docstring: a base that must never be graded as a pair must not be a ``SchemaBound``,
#: and an empty ``model_config`` is what stating no policy means.
MODEL = envelope.MODEL
MODEL_MODULE = envelope.MODEL_MODULE

#: What a consumer reads first, so each says both halves -- what the type is for and what
#: it is not.  Here rather than in ``render.py`` because it is a statement about the
#: REGISTRY, and the renderer writes text about nothing.
DESCRIPTIONS = {
    REQUEST: (
        "The request half of a task, as one type to program against. Every document the "
        "bundle's manifest.json names at a tool's request_schema takes this base, so "
        "isinstance(x, AdcpRequest) answers 'is this a call' -- which no composed "
        "envelope answers, because a response composes the version envelope too. "
        "A NOMINAL supertype and not a conformance claim: it states no field, because "
        "every field a request shares is already stated by core/version-envelope.json "
        "and restating it would be one fact in two classes. It carries no "
        "__adcp_schema__, so nothing grades it and strict_validate does not resolve on "
        "it; the concrete class for a document decides what that document accepts."
    ),
    RESPONSE: (
        "The response half of a task, as one type to program against. Every document the "
        "bundle's manifest.json names at a tool's response_schema takes this base. "
        "A NOMINAL supertype and not a conformance claim: it states no field, because "
        "every field a response shares is already stated by core/protocol-envelope.json "
        "and core/version-envelope.json, which arrive as bases from the document's own "
        "allOf. It carries no __adcp_schema__, so nothing grades it and strict_validate "
        "does not resolve on it. The 39 documents the manifest names at "
        "async_response_schemas are a task RESULT rather than the answer to the call and "
        "do not take this base."
    ),
}


def bases() -> tuple[tuple[ir.ClassDecl, ...], frozenset[tuple[str, str]]]:
    """The two declarations and the one import they name.

    No argument, which is the row: an envelope's base needs its family's agreed shape
    handed in because its fields are derived from it, and these two state no field, so
    there is nothing about the bundle for this function to be told.  The SET the bases are
    given to is still the registry's and still a function of the bundle
    (``bundle.task_messages``); it is :func:`adopt` that reads it.
    """
    return (
        tuple(
            ir.ClassDecl(
                name=name,
                ref=None,
                fields=(),
                description=DESCRIPTIONS[name],
                # A LOCAL symbol, which is what a base always is here: the renderer
                # writes the name and the module writer supplies the import, exactly as
                # it does for a base another document declares.
                bases=(ir.TypeRef(MODEL, local=True),),
            )
            for name in (REQUEST, RESPONSE)
        ),
        frozenset({(MODEL_MODULE, MODEL)}),
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

    A module with no named document is returned unchanged, so no module gains an import
    of a symbol it does not name.
    """
    wanted = {REQUEST: frozenset(requests), RESPONSE: frozenset(responses)}
    declarations: list[ir.Declaration] = []
    taken: set[str] = set()
    for declaration in module.declarations:
        if isinstance(declaration, ir.ClassDecl):
            at = _root_document(declaration.ref)
            for name, documents in wanted.items():
                if at is not None and at in documents:
                    declaration = replace(
                        declaration, bases=(*declaration.bases, ir.TypeRef(name, local=True))
                    )
                    taken.add(name)
        declarations.append(declaration)
    if not taken:
        return module
    return replace(
        module,
        declarations=tuple(declarations),
        imports=module.imports | {(MODULE, name) for name in taken},
    )


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
