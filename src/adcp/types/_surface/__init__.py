"""The compiler's own aggregators, one module per domain.

Nothing here is a path a consumer writes.  Each module re-exports one domain's
names from the private per-document tree, and the public module of that domain
composes this one with a single star re-export -- which is what lets a public
path serve an emitted name set beside a hand-written one without either file
holding the other's text.

This package declares no name of its own.
"""
