"""The generated types.

**One import path per class, and it is a DOMAIN module.**  ``docs/plan/rebuild-plan.md``
§1: a document compiles to a module at its own path under a private tree --
``core/pagination-request.json`` -> ``adcp.types._schemas.core.pagination_request`` -- and
is re-exported from a module named for its DOMAIN, which is the first segment of the
document's own path.  That module is the path a consumer uses::

    from adcp.types.core import PaginationRequest, AssetRequirements
    from adcp.types.core import AssetRequirementsJavaScript
    from adcp.types.enums import MatchType

    req = PaginationRequest.strict_validate(payload)   # the schema decides
    req = PaginationRequest(max_results=50)            # pydantic constructs
    isinstance(held, AssetRequirementsJavaScript)      # a union hands a branch back

**There is no flat root and no second spelling.**  This module exports no type: a
``from adcp.types import PaginationRequest`` would be the second path §1 forbids, and the
domain in the import is what tells a reader of application code which document a class
came from without looking it up.

**The re-export is the class, not a copy of it.**  A domain module binds
``from ._schemas... import X as X``, so the object a consumer imports IS the one the
private module built and the one ``strict_validate`` validates into -- ``isinstance``
against a branch imported from here is true, and there is no second ``__adcp_schema__``
to keep in agreement.

**WHAT IS EXPORTED, which §1 fixes and the compiler derives**: every document ROOT, every
union BRANCH and every type ALIAS.  Not every class the tree declares -- an inner shape
stated once by one document is reached through the field whose annotation names it, and a
surface exporting all of them would make ``core.Status`` mean one of fourteen things.  Not
the per-module ``strict_validate`` helper either; a caller reaches one through its class.

**The reading a consumer can re-derive, so none of the above has to be trusted**:
``pkgutil.iter_modules`` over ``adcp.types`` returns the private children ``_base``,
``_runtime`` and ``_schemas``, the two public modules named below, and one module per
domain -- and each domain module's own ``__all__`` is its names as a literal list.  Over
bundle 3.2 that is 23 domains carrying 1,951 names, each resolving at exactly one of them.

**The domain modules are GENERATED from the same walk as the classes**
(``codegen/emit.py``'s ``domain_modules``, from the compiler's own record of what it
exported), so a document added upstream appears in its domain with nothing edited.  This
file is not: a package's own ``__init__`` is the package, so it is bound before
``__path__`` is consulted and no generated copy of it could be the one a test grades.  It
therefore names no type and carries no list.

Two modules are public and are not domains, because what they hold has no document to
bind -- so neither has a domain a surface could give it, and neither waits on one.

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
