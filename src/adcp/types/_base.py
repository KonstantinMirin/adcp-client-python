"""The hand-written pieces every emitted schema module imports.

Hand-written, and small on purpose: everything else in ``_schemas/`` is a
function of a bundle document.

**Every emitted class carries a reference to the schema that generated it.**
``__adcp_schema__`` is a ``SchemaRef`` -- the document's bundle-relative path
plus a JSON pointer -- and that one fact is what makes everything below generic.
``strict_validate`` reads it off ``cls``; the test harness reads it off the same
class; neither consults a table, a module header, a filename convention or a
name-keyed lookup.  The previous arrangement had all four, through a
``_bindings.json`` the emitter wrote and a ``codegen/adapter.py`` that aimed the
harness at a tree -- and an adapter that can be aimed at a tree can be aimed at
the WRONG tree, which is how a previous attempt came to grade 1,602 documents
green while generating nothing.  A class that carries its own schema cannot be
aimed at someone else's output.

The pointer is there because a nested class is a SUBSCHEMA of its document and
has to grade against its own node rather than against the whole file.  A root
class names ``"#"``.

``AdCPBaseModel`` carries the config a document says nothing about.  D8 derives
``extra`` from ``additionalProperties`` alone: ``false`` -> ``forbid``, ``true``
-> ``allow``, and a document that declares neither gets this base's ``ignore``.

**Absent and ``true`` are different statements.**  ``true`` says an additional
property is part of the document, so it is retained; silence says only that one
is permitted, so it is accepted and dropped.  Retaining a property the document
never mentions would be this SDK adding a claim the schema does not make.  Both
answers accept the same payloads, so the choice is about retention and not about
the accepted set.

**Nothing here reads an environment and no generated class carries a policy its
document does not state.**  A consumer wanting stricter or looser behaviour than
the schema sets it on a subclass.  In this step's population exactly ONE object
node is silent on ``additionalProperties`` (23 declare ``true``, 15 declare
``false``), so this default decides one class and the other 43 decide
themselves.

Acceptance is decided by ``strict_validate``, which validates a payload against
the DOCUMENT'S OWN JSON Schema and only then constructs through
``model_validate``.  One call, both answers: the verdict is the schema's and the
value is pydantic's.

``model_validate`` stays public, because pydantic exposes it and it cannot be
removed.  It constructs **without** consulting the schema.  Everything the
schema states and the annotation does not -- an explicit ``null`` for a property
declared ``{"type": "string"}``, a key the document forbids -- is invisible to
it.  A caller that wants the document's accepted set calls ``strict_validate``;
a caller that already knows its payload conforms, or that is rebuilding a value
this library produced, calls ``model_validate`` and takes the constructor.

So an optional property renders plain ``T | None``, with its own default (D4),
and there is no per-field validator refusing the null.  ``required`` governs
presence and ``type`` governs value, which is the distinction the schema already
draws and the schema half already enforces: a validator re-stating it in Python
would re-implement a fact the document states exactly, on every one of the
bundle's ~7,000 property annotations, and would cost pydantic's serialization
fast path to do it.  The ``None`` branch of the annotation is live either way,
because the attribute holds ``None`` for an omitted key, so ``x.field is None``
means "not supplied".

``strict_alias`` is the same two halves for a node that has no class to put them
on: D2 makes a scalar ROOT a module-level ``Annotated`` alias, so the emitted
module binds ``strict_validate`` as a function instead of a classmethod.  Both
reach the document through ``schema_at`` and refuse through ``_refuse``, which
is what keeps a class and an alias from answering differently about what their
document accepts.

``docs/plan/rebuild-plan.md`` §2 and D4 carry the decisions and the reasoning.
"""

from __future__ import annotations

import functools
import json
from collections.abc import Callable
from importlib import resources
from typing import Any, ClassVar, Literal, NamedTuple, TypeVar

import jsonschema
from pydantic import BaseModel, ConfigDict, TypeAdapter
from pydantic_core import InitErrorDetails, PydanticCustomError, ValidationError

#: The package the emitter writes both the modules and the documents into.  One
#: JSON file per document, at the document's own bundle-relative path, so
#: ``SchemaRef.document`` is simultaneously the identity of the schema and the
#: resource that holds it.  The bundle itself (124 MB, with a version in its
#: path) is a build-time input and cannot be the runtime source.
PACKAGE = "adcp.types._schemas"

ModelT = TypeVar("ModelT", bound="AdCPBaseModel")

#: The engine every ``pattern`` in this package is compiled with, named once
#: because a class reads it off ``AdCPBaseModel`` and an alias has to be handed
#: it (see ``strict_alias``), and two spellings of one engine is one place for
#: them to come apart -- which is exactly how the defect below shipped.
#:
#: **``python-re`` is the engine whose accepted set is the DOCUMENT'S.**  The
#: document's own validator is ``jsonschema``, which compiles every pattern with
#: Python ``re``, so any other engine is this package deciding that a string the
#: schema admits is unrepresentable.
#:
#: pydantic's default is the Rust engine, which is faster and which refuses to
#: build a pattern it cannot honour rather than mis-matching one, so it is the
#: one to want -- and it was adopted here and then measured.  **The two engines
#: do not agree, and look-around is not the reason.**  Python's ``$`` matches at
#: the end of the string OR just before a trailing newline; Rust's ``$`` matches
#: only at the end of the haystack.  So for every ``$``-anchored pattern the
#: document admits a value ending in ``\n`` that a Rust-engine model refuses.
#: Measured over the 1,054 portable documents of the 3.2 bundle: 105 of 110
#: distinct patterns contain ``$``, at 768 of 830 sites, against 4 distinct
#: look-around patterns at 18 sites.  The Rust engine's accepted set is the
#: document's for **5 of 110** distinct patterns, not 102.
#:
#: Scoping it per class therefore buys 5 patterns and costs a narrowing at 105,
#: and no rewrite of the pattern is available either: the schema comparison
#: grades ``pattern`` as a fact the document states, so translating ``$`` would
#: redden it.
REGEX_ENGINE: Literal["python-re"] = "python-re"


class SchemaRef(NamedTuple):
    """The schema a generated class was generated from.

    ``document`` is bundle-relative (``"core/pagination-request.json"``) and is
    also the resource path inside :data:`PACKAGE`.  ``pointer`` is a JSON
    pointer into it: ``"#"`` for a root class, ``"#/properties/x"`` for the
    nested class a property declares inline.

    A ``NamedTuple`` for three reasons: it is hashable, so the read below can be
    memoized per document instead of per table; it is immutable, so a class
    cannot be re-pointed at another document after import; and its ``repr`` is a
    valid Python expression naming this type, which is how the emitter writes
    the ``ClassVar`` line without any template of its own.
    """

    document: str
    pointer: str = "#"


@functools.lru_cache(maxsize=None)
def _document(document: str) -> dict:
    """One document, read from the package and held.

    Per DOCUMENT, which is the fix the previous whole-table cache's own docstring
    named: that one parsed every row to validate against one of them, so its
    cost grew with the size of the population rather than with the number of
    documents a process actually validates against.  This one is bounded by the
    number of distinct documents the caller touches, and a process that
    validates against one reads one.
    """
    resource = resources.files(PACKAGE)
    for part in document.split("/"):
        resource = resource.joinpath(part)
    return json.loads(resource.read_text())


def schema_at(ref: SchemaRef) -> dict:
    """The subschema ``ref`` names.

    The pointer is resolved here and not at emit time, because the document is
    what the package carries: a nested class's node is part of its document's
    meaning, and writing each node out separately would put the same subschema
    in the package twice and let the two drift.
    """
    node: Any = _document(ref.document)
    for part in ref.pointer.lstrip("#").lstrip("/").split("/"):
        if part == "":
            continue
        part = part.replace("~1", "/").replace("~0", "~")
        node = node[int(part)] if isinstance(node, list) else node[part]
    if not isinstance(node, dict):
        raise LookupError(f"{ref.document}{ref.pointer} is {type(node).__name__}, not a schema")
    return node


def _refuse(schema: dict, payload: Any, name: str) -> None:
    """Raise pydantic's ``ValidationError`` for every way ``schema`` refuses ``payload``.

    The schema check runs over the WHOLE payload before anything is constructed,
    which is what covers nesting: pydantic builds children, and an inner value
    the document refuses never reaches it.

    Shared by ``AdCPBaseModel.strict_validate`` and ``strict_alias`` so there is
    one refusal and one error shape.  An alias and a class differ only in how
    they are constructed afterwards; what the document accepts is the same
    question and must not get a second answer.

    **``format`` IS ASSERTED, and the checker comes from the document's own
    draft.**  ``jsonschema`` treats ``format`` as a pure annotation unless it is
    handed a ``FormatChecker``, so without this the SDK accepted a ``date-time``
    with no offset -- which RFC 3339 forbids and the document therefore forbids
    -- and any Python type derived from a format was narrower than its own
    document.  D5 lets a format select a type exactly because this line exists.
    The checker is ``validator.FORMAT_CHECKER``, the one the draft the document
    DECLARES defines, so the asserted vocabulary is the document's rather than a
    set named here: a ``uuid`` is not a draft-07 format and is not asserted under
    one, and the two installed checker packages (``rfc3339-validator``,
    ``rfc3987``) are what put ``date-time`` and ``uri`` into it.  A format with
    no checker installed asserts nothing, silently, which is why
    ``codegen.emit`` gates its type selection on the same set rather than on a
    list of formats someone wrote down.
    """
    validator = jsonschema.validators.validator_for(schema, jsonschema.Draft7Validator)
    errors = sorted(
        validator(schema, format_checker=validator.FORMAT_CHECKER).iter_errors(payload),
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


def strict_alias(ref: SchemaRef, symbol: str, alias: Any) -> Callable[[Any], Any]:
    """The strict entry point for a module-level ``Annotated`` alias.

    D2 makes a scalar root an alias and not a class -- the document is a string,
    and a wrapper class would be a second name for the same node (P2) and would
    put an object on the wire.  So there is no ``AdCPBaseModel`` to carry
    ``strict_validate`` and no class attribute to hold the ``SchemaRef``, and the
    emitted module binds this under its own name instead, with the ref passed in.

    The schema half is the SAME read and the same refusal a class gets; only the
    construction half differs, and for an alias that is ``TypeAdapter``, which
    is the alias's constructor and not its accepted set.  Behind the schema check
    it is the constructor, which is all it was ever meant to be.

    **The adapter is built with the config, and that closed a live narrowing.**
    ``regex_engine`` is a MODEL config, so an ``Annotated`` alias has nowhere to
    carry one: a bare ``TypeAdapter`` took pydantic's default Rust engine while
    every emitted CLASS took ``python-re`` off ``AdCPBaseModel``, and the two
    engines disagree about ``$`` (see :data:`REGEX_ENGINE`).  Measured on the
    emitted tree: ``core/brand-id.json`` states ``pattern: ^[a-z0-9_]+$``, its
    document ADMITS ``"abc\\n"``, and ``BrandID.strict_validate("abc\\n")``
    refused it with ``string_pattern_mismatch`` -- a CONSTRUCTOR refusal of a
    value the schema half had just admitted, which is a model narrower than its
    own document at 2 of this population's 5 scalar roots.  None of the three
    checks reported it: ``compare_schema`` sees the same ``pattern`` fact on both
    sides, and the accepts check did not draw a trailing newline in 25 examples.
    ``config=`` is also the only channel here, because pydantic refuses a
    ``config=`` on a ``TypeAdapter`` over a ``BaseModel`` -- which is why a class
    takes it off the class and an alias takes it here.
    """
    adapter = TypeAdapter(alias, config=ConfigDict(regex_engine=REGEX_ENGINE))

    def strict_validate(payload: Any) -> Any:
        _refuse(schema_at(ref), payload, symbol)
        return adapter.validate_python(payload)

    strict_validate.__doc__ = f"Validate against {ref.document}, then construct {symbol}."
    return strict_validate


class AdCPBaseModel(BaseModel):
    model_config = ConfigDict(extra="ignore", regex_engine=REGEX_ENGINE)

    #: Declared and not assigned: every emitted class writes its own, and a
    #: subclass of this base that writes none has no schema to be validated
    #: against, so reading it is an ``AttributeError`` at the one call below
    #: rather than a silent fall back to ``model_validate``.
    __adcp_schema__: ClassVar[SchemaRef]

    @classmethod
    def strict_validate(cls: type[ModelT], payload: Any) -> ModelT:
        """Validate ``payload`` against this class's own document, then construct.

        The schema decides acceptance and pydantic builds the value.  A schema
        refusal raises pydantic's ``ValidationError``, with the JSON Schema
        KEYWORD that bit as the error ``type`` and the instance pointer as its
        ``loc``, so a caller reads one error shape whichever half refused.  The
        keyword is carried through ``PydanticCustomError``, which is the only way
        a name from another vocabulary reaches ``errors()[0]["type"]``.

        The schema is the one this class names.  There is no lookup to get wrong
        and no second place to read one from.
        """
        _refuse(schema_at(cls.__adcp_schema__), payload, cls.__name__)
        return cls.model_validate(payload)
