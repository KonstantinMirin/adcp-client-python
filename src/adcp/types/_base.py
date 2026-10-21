"""The two hand-written pieces every emitted schema module imports.

Hand-written, and small on purpose: everything else in ``_schemas/`` is a
function of a bundle document.

``AdCPBaseModel`` carries the config a document says nothing about.  D7 derives
``extra`` from ``additionalProperties``, so a document declaring ``false`` or
``true`` gets ``forbid`` or ``allow`` on its own class and never reaches this
default.  ``ignore`` is what is left for a document that declares neither, and
there the two accepted sets agree: the schema admits the unknown key and so does
the model.  One retains it and one drops it, which is not a question about what
is accepted.

``Absent`` is D4 and P12: an optional property is absent or valid, never null.
``required`` governs presence and ``type`` governs value, so a property declared
``{"type": "string"}`` refuses an explicit ``null`` whether or not it is
required.  One annotated alias carries both facts --

    omitted        -> accepted, the attribute is None, absent from model_fields_set
    explicit null  -> REFUSED
    a value        -> accepted
    read type      -> T | None

The ``None`` arm stays in the annotation because the attribute holds ``None``
for an omitted key, so ``x.field is None`` is live code meaning "not supplied";
an annotation that denied it would make every correct guard unreachable.

It must be an ``AfterValidator``.  A validator placed before the declared type
forces pydantic-core to materialize parsed JSON as Python objects, which
collapses a repeated JSON key anywhere under an optional property and loses a
refusal the buyer should see.  An ``AfterValidator`` runs on the already-parsed
value and carries none of that.  Neither validator runs for an absent key:
pydantic does not validate a default, which is exactly the presence/value
distinction the schema draws.

A property whose schema ADMITS null -- ``type`` absent, or ``type`` listing
``"null"`` -- does not use this alias.  It renders ``T | None`` plainly, because
there the schema does accept the null and P3 is what binds.
"""

from __future__ import annotations

from typing import Annotated, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict

T = TypeVar("T")


def refuse_null(value: T) -> T:
    """Refuse an explicitly supplied ``null`` for a property whose type forbids it."""
    if value is None:
        raise ValueError("expected the property to be absent or valid, not null")
    return value


Absent = Annotated[T | None, AfterValidator(refuse_null)]


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
