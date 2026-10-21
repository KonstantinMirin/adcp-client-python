"""The hand-written pieces every emitted schema module imports.

Hand-written, and small on purpose: everything else in ``_schemas/`` is a
function of a bundle document.

``AdCPBaseModel`` carries the config a document says nothing about.  D7 derives
``extra`` from ``additionalProperties``, so a document declaring ``false`` or
``true`` gets ``forbid`` or ``allow`` on its own class and never reaches this
default.  ``ignore`` is what is left for a document that declares neither, and
there the two accepted sets agree: the schema admits the unknown key and so does
the model.  One retains it and one drops it, which is not a question about what
is accepted.

Acceptance is decided by ``strict_validate``, which validates a payload against
the DOCUMENT'S OWN JSON Schema and only then constructs through
``model_validate``.  One call, both answers: the verdict is the schema's and the
value is pydantic's.

``model_validate`` stays public, because pydantic exposes it and it cannot be
removed.  It constructs **without** consulting the schema.  Everything the
schema states and the annotation does not -- a ``minimum`` on a field pydantic
sees only as ``int``, an explicit ``null`` for a property declared
``{"type": "string"}``, a key the document forbids -- is invisible to it.  A
caller that wants the document's accepted set calls ``strict_validate``; a
caller that already knows its payload conforms, or that is rebuilding a value
this library produced, calls ``model_validate`` and takes the constructor.

So an optional property renders plain ``T | None = None`` (D4), and there is no
per-field validator refusing the null.  ``required`` governs presence and
``type`` governs value, which is the distinction the schema already draws and
the schema half already enforces: a validator re-stating it in Python would
re-implement a fact the document states exactly, on every one of the bundle's
~7,000 property annotations, and would cost pydantic's serialization fast path
to do it.  The ``None`` arm of the annotation is live either way, because the
attribute holds ``None`` for an omitted key, so ``x.field is None`` means "not
supplied".

``strict_alias`` is the same two halves for a node that has no class to put them
on: D2 makes a scalar ROOT a module-level ``Annotated`` alias, so the emitted
module binds ``strict_validate`` as a function instead of a classmethod.  Both
reach the document through ``_document_at`` and refuse through ``_refuse``, which
is what keeps a class and an alias from answering differently about what their
document accepts.

``docs/plan/rebuild-plan.md`` D4 carries the decision and the reasoning.
"""

from __future__ import annotations

import functools
import json
from collections.abc import Callable
from importlib import resources
from typing import Any, TypeVar

import jsonschema
from pydantic import BaseModel, ConfigDict, TypeAdapter
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError

#: The emitted binding table, and the package it lands in.  The emitter writes
#: one row per document it lowered -- the module, the symbol, and the document
#: itself, RESOLVED -- so a class can find the schema it was generated from with
#: nothing but its own name, and the bundle (124 MB, and a version in its path)
#: is a build-time input rather than a runtime dependency.
#:
#: Resolved because a row has to be DECIDABLE here, with no second input: a
#: ``$ref`` left in one sends ``jsonschema`` to the network to retrieve the
#: target, which is deprecated, slow (4.4 s per validation, measured) and simply
#: unavailable offline.  ``codegen.bundle.resolved`` inlines it at emit time and
#: ``codegen.adapter`` asserts the row equals the bundle's document resolved.
#: This is the one thing a reference does NOT become an import: the module
#: imports its target's type (P2), and the row carries its target's meaning.
#:
#: This is the one place a schema comes from.  Reading any other tree is how a
#: previous attempt came to grade 1,602 documents while generating nothing, so
#: there is deliberately no second lookup and no fallback: a class with no row
#: here has no schema, and ``strict_validate`` refuses rather than quietly
#: becoming ``model_validate``.
_BINDINGS = ("adcp.types._schemas", "_bindings.json")

ModelT = TypeVar("ModelT", bound="AdCPBaseModel")


@functools.lru_cache(maxsize=1)
def _documents() -> dict[tuple[str, str], tuple[str, dict]]:
    """``(module, symbol)`` -> ``(document path, document)``, read once.

    KNOWN CEILING: the whole table is parsed to validate against one document.
    At this step's N that is 34 rows and ~50 KB; over the bundle's 1,054 it
    would be read once and held, which is the point at which the emitter should
    write one schema file per module and this row should name it instead.
    """
    package, name = _BINDINGS
    table = json.loads(resources.files(package).joinpath(name).read_text())
    return {
        (row["module"], row["symbol"]): (document, row["schema"])
        for document, row in table.items()
    }


def _document_at(key: tuple[str, str]) -> tuple[str, dict]:
    try:
        return _documents()[key]
    except KeyError:
        raise LookupError(
            f"{key[0]}.{key[1]} is bound to no document in {_BINDINGS[0]}/{_BINDINGS[1]}: "
            "strict_validate has no schema to decide acceptance against. A nested class "
            "is a subschema and not a document; accepting the payload anyway would be "
            "model_validate under another name."
        ) from None


def _document_of(model: type[BaseModel]) -> tuple[str, dict]:
    return _document_at((model.__module__, model.__qualname__))


def _refuse(schema: dict, payload: Any, name: str) -> None:
    """Raise pydantic's ``ValidationError`` for every way ``schema`` refuses ``payload``.

    The schema check runs over the WHOLE payload before anything is constructed,
    which is what covers nesting: pydantic builds children, and an inner value
    the document refuses never reaches it.

    Shared by ``AdCPBaseModel.strict_validate`` and ``strict_alias`` so there is
    one refusal and one error shape.  An alias and a class differ only in how
    they are constructed afterwards; what the document accepts is the same
    question and must not get a second answer.
    """
    validator = jsonschema.validators.validator_for(schema, jsonschema.Draft7Validator)
    errors = sorted(
        validator(schema).iter_errors(payload),
        key=lambda e: [str(p) for p in e.absolute_path],
    )
    if not errors:
        return
    raise ValidationError.from_exception_data(
        name,
        [
            InitErrorDetails(
                type=PydanticCustomError(
                    e.validator if isinstance(e.validator, str) else "schema",
                    # A fixed template with the text in the context: a jsonschema
                    # message carries braces of its own ("{'a': 1} is not of type
                    # 'string'") and a message used AS the template would be read
                    # as placeholders.
                    "{detail}",
                    {"detail": e.message},
                ),
                loc=tuple(e.absolute_path),
                input=e.instance,
            )
            for e in errors
        ],
    )


def strict_alias(module: str, symbol: str, alias: Any) -> Callable[[Any], Any]:
    """The strict entry point for a module-level ``Annotated`` alias.

    D2 makes a scalar root an alias and not a class -- the document is a string,
    and a wrapper class would be a second name for the same node (P2) and would
    put an object on the wire.  So there is no ``AdCPBaseModel`` to carry
    ``strict_validate`` and no ``__qualname__`` to find the document by, and the
    emitted module binds this under its own name instead.

    The schema half is the SAME lookup, over the same binding table, raising the
    same error shape; only the construction half differs, and for an alias that
    is ``TypeAdapter``.  Which is exactly the fallback ``codegen.harness.accepting``
    warns about -- and the warning is about using it ALONE as the accepted set.
    Behind the schema check it is the constructor, which is all it was ever meant
    to be.

    The module's own row is read at CALL time, not here: a class finds its
    document when asked and so does this, so an alias module bound to no row
    raises ``LookupError`` the same way rather than failing to import.
    """
    adapter = TypeAdapter(alias)

    def strict_validate(payload: Any) -> Any:
        _, schema = _document_at((module, symbol))
        _refuse(schema, payload, symbol)
        return adapter.validate_python(payload)

    strict_validate.__doc__ = f"Validate against {module}'s document, then construct {symbol}."
    return strict_validate


class AdCPBaseModel(BaseModel):
    #: ``regex_engine`` is the accepted set of every ``pattern`` in the bundle.
    #: pydantic's default engine is Rust ``regex``, which has no look-around and
    #: REFUSES TO BUILD a pattern using it -- ``core/sla-window.json``'s
    #: ``^P(?!$)(\d+Y)?...`` is one, so the module would not import.  The
    #: document's own validator is ``jsonschema``, which compiles a pattern with
    #: Python ``re``, so ``python-re`` is the engine whose accepted set is the
    #: document's.  Choosing the other engine would be this model deciding that a
    #: pattern the schema admits is unrepresentable.
    model_config = ConfigDict(extra="ignore", regex_engine="python-re")

    @classmethod
    def strict_validate(cls: type[ModelT], payload: Any) -> ModelT:
        """Validate ``payload`` against this class's own document, then construct.

        The schema decides acceptance and pydantic builds the value.  A schema
        refusal raises pydantic's ``ValidationError``, with the JSON Schema
        KEYWORD that bit as the error ``type`` and the instance pointer as its
        ``loc``, so a caller reads one error shape whichever half refused.  The
        keyword is carried through ``PydanticCustomError``, which is the only way
        a name from another vocabulary reaches ``errors()[0]["type"]``.

        The refusal is ``_refuse``, shared with ``strict_alias`` (D2's root-scalar
        row, which has no class to put this method on).  One refusal, so a class
        and an alias cannot come to disagree about what their document accepts.
        """
        _, schema = _document_of(cls)
        _refuse(schema, payload, cls.__name__)
        return cls.model_validate(payload)
