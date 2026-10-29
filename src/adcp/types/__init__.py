"""The generated types.

**The one path to a type FROM A DOCUMENT is private today**: the schema module under
``adcp.types._schemas``, at the document's own path with each segment spelled as a Python
identifier.  ``from adcp.types._schemas.core.pagination_request import
PaginationRequest`` is what resolves; there is no second spelling, and nothing
re-exports it publicly.

A PUBLIC module per domain is a stated goal and it has NOT arrived.  This docstring used
to announce it as imminent -- it said the surface was "generated from the binding table
in step 9" -- and ``docs/plan/architecture.md`` §14 step 9 is *the faithful rows*, which
has landed and owns no binding table.  Where the goal is actually written, with the
derivation of what is true instead and the check it still needs:
``docs/plan/surface-goal.md`` ("What the surface must satisfy", first bullet) and
``docs/plan/unimplemented.md`` item A-2.  ``docs/plan/execution-plan.md`` sequences "the
public surface" after the keyword waves.

**The reading that says it has not arrived, so a consumer can re-derive it rather than
trust this sentence**: ``pkgutil.iter_modules`` over ``adcp.types`` returns ``_base``,
``_runtime``, ``_schemas``, ``constraints`` and ``envelopes`` -- three private by the
leading underscore, and the two public ones named below.  A name there that is neither
underscored nor one of those two is a domain, and its appearance is the surface arriving.

Two modules ARE public already, because what they hold has no document to bind -- so
neither has a domain a surface could give it, and neither waits on one.  A consumer
annotating application code imports from them, and each is the only path to what it
holds: there is no flat root and no second spelling.

``adcp.types.constraints`` names a constrained type once (D5): a type derived from a
CONSTRAINT belongs to no document.

``adcp.types.envelopes`` carries a base for a repeated envelope the bundle spells
more than one way (``codegen/lower/envelope.py``).  A base there is a type to
PROGRAM AGAINST and not an authority on acceptance: it carries no
``__adcp_schema__``, nothing grades it, and the concrete class for a document -- the
one ``strict_validate`` runs -- is what decides whether a payload is valid.  The
documents of such a family do not agree about that, which is why no single schema
reference could stand for all of them.
"""
