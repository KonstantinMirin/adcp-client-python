"""One module per D2 row: the decisions a node kind needs, and nothing else.

``docs/plan/rebuild-plan.md`` §5 Layout puts the walk's per-kind judgements here,
the compiler's rendering in ``codegen/compiler.py``, and the CLI, the module
writer and the dispatch table in ``codegen/emit.py``.

**A module here imports ``codegen.compiler`` and ``codegen.refusal``, and nothing
else of this package.**  That is a constraint and not an accident: the dispatch
table lives in ``codegen.emit`` and names these lowerings, so an import back the
other way is a cycle -- and under ``runpy`` (``python -m codegen.emit``) it is a
cycle that resolves into TWO module objects rather than into an ImportError, which
is the failure D12 already exists to prevent for ``Refusal``.

So a row answers for its own node kind and is handed everything else:

* the NAME is an input (D3: "a name is an input to a lowering and is never
  computed inside one");
* the keyword SCREEN is run by the caller, over the set the row declares as
  ``HANDLED`` -- one screen for every row, so a keyword cannot be silently
  dropped by one row's private copy of it;
* the MODULE text -- the header, the imports, the ``__all__`` -- is the module
  writer's.
"""
