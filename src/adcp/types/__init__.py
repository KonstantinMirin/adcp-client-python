"""The generated types.

The public surface -- what resolves on ``adcp.types`` and on ``adcp.types.<domain>``
-- is generated from the binding table in step 9.  Until then this is the package
marker, and the only supported path to a type FROM A DOCUMENT is the private
schema module the binding table names.

``adcp.types.constraints`` is the one exception and it is public already, because
what it holds has no document to bind: D5 names a constrained type once, and a
type derived from a constraint belongs to no document, so it has no domain for the
binding table to give it.  A consumer annotating application code imports from
there, and it is the only path to such a type -- there is no flat root and no
second spelling.
"""
