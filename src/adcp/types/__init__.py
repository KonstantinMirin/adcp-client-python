"""The generated types.

The public surface -- what resolves on ``adcp.types`` and on ``adcp.types.<domain>``
-- is generated from the binding table in step 9.  Until then this is the package
marker, and the only supported path to a type FROM A DOCUMENT is the private
schema module the binding table names.

Two modules are the exception and both are public already, because what they hold
has no document to bind, so neither has a domain for the binding table to give it.
A consumer annotating application code imports from them, and each is the only path
to what it holds -- there is no flat root and no second spelling.

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
