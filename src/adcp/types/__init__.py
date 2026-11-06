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

**THE SCHEMA-DERIVED SURFACE HAS NO FLAT ROOT AND NO SECOND SPELLING.**  This module
declares no type of its own: a ``from adcp.types import PaginationRequest`` reaching a
class §1 placed at a domain would be the second path §1 forbids, and the domain in the
import is what tells a reader of application code which document a class came from
without looking it up.

**WHAT IT DOES CARRY IS READING 10's ALIAS LAYER, AND THAT IS AN EXPERIMENT ON THIS
BRANCH** (``adcp-client-python-2m5.6``, measured and not decided).  ``final-state.md``
reading 10 says "``adcp.types`` flat -- the compatibility surface: an alias for every name
an application actually imports today", and the owner's goal calls the layer a DROP-IN for
the v9.6 classes -- which is defined by the import an application has already written.
The aliases are declared at ``adcp.types.compat`` and were reachable from here at none of
their upstream spellings, so ``from adcp.types import <UpstreamName>`` raised.

:func:`__getattr__` is how they are reached, and it is **LAZY by necessity and not by
taste**: an eager ``from adcp.types.compat import *`` here would import every domain
module -- and through them ``adcp.types._schemas`` -- while this package's own body runs,
which is before ``tests/conftest.py`` can put a fresh tree in front of ``__path__``.
Measured: the suite then reports "the generated half of adcp.types is already bound
outside the fresh tree" and grades the committed artifact instead
(``tests/fresh.py::_bound``).  So nothing is imported until a name is asked for, and the
name list is ``adcp.types.compat.__all__`` read at that moment rather than a second copy
of it written here.

**AND IT IS A NAME AND NEVER A SECOND TYPE.**  ``getattr`` over the alias module returns
the object the alias module itself re-exported, so
``adcp.types.X is adcp.types.compat.X is adcp.types.<domain>.<OurName>`` and ``isinstance``
holds across all three spellings.  Nothing is declared here, so reading 6's count of
declarations does not move.

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


def __getattr__(name: str) -> object:
    """Reading 10's flat compatibility surface, resolved through the alias module.

    A name this package does not itself bind is looked for in ``adcp.types.compat``, the
    one module ``adcp-client-python-2m5.2`` declares every alias at.  What is returned is
    whatever that module holds, which is whatever the domain module holds, which is the
    class the walk emitted -- three spellings, one object.

    **AND THE FLAT SURFACE IS LARGER THAN THAT MODULE'S ``__all__``, which is reading 10's
    amendment of 2026-11-06**: "'already resolves' is measured at the SPELLING A CONSUMER
    WRITES, never at the module that declares it ... a name counted present because its
    domain path matches owes a flat alias exactly as a relocated one does."  So a name the
    alias module declines to bind -- because ours already carries it at
    ``adcp.types.<domain>`` under upstream's own word -- is resolved HERE through
    ``compat.__adcp_flat_only__``, which names that module.  It gains the one path a
    consumer writes and no path at ``compat``.

    ``AttributeError`` for anything the alias layer does not decide, because that is what
    ``from adcp.types import X`` must raise for a name with no subject: reading 10's "a
    name with no schema subject gets a migration note and never a class", and an
    ``ImportError`` a reader can act on rather than a class that silently is not theirs.
    """
    if name == "compat" or (name.startswith("__") and name != "__all__"):
        # Not routed through the alias module.  A dunder probe (``__path__`` during a
        # partial import, ``__wrapped__``, ``__bases__``) must stay an ``AttributeError``
        # and must not import a thousand names to answer one -- and ``compat`` itself must
        # stay one so that the import system goes on to import the SUBMODULE.
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    compat = _alias_module()
    if name == "__all__":
        return sorted({*compat.__all__, *compat.__adcp_flat_only__})
    try:
        return getattr(compat, name)
    except AttributeError:
        pass
    where = compat.__adcp_flat_only__.get(name)
    if where is not None:
        import importlib

        return getattr(importlib.import_module(where), name)
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}; the generated surface is "
        f"adcp.types.<domain> and the upstream spellings are this namespace's -- see "
        f"docs/migration-from-upstream.md for a name with no document behind it"
    )


def _alias_module():
    """``adcp.types.compat``, reached WITHOUT a ``getattr`` on this package.

    ``from adcp.types import compat`` would not do: the import system answers a fromlist
    entry by asking ``hasattr`` on the parent first, which re-enters
    :func:`__getattr__` and recurses until the stack ends.  ``import_module`` returns the
    entry in ``sys.modules`` and never consults this package's attributes.
    """
    import importlib

    return importlib.import_module("adcp.types.compat")


def __dir__() -> list[str]:
    """This package's own names plus every upstream spelling the alias layer decides."""
    compat = _alias_module()
    return sorted(set(globals()) | set(compat.__all__) | set(compat.__adcp_flat_only__))
