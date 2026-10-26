"""One module per D2 row: what one kind of node becomes, and nothing else.

``docs/plan/rebuild-plan.md`` D13 and §5 Layout put the pieces here:
``codegen/__main__.py`` holds the command and the refusal report;
``codegen/emit.py`` holds the walk, the module writer and the dispatch table
``ROWS``; ``codegen/compiler.py`` drives the compiler and holds the machinery a
lowering is handed; and each lowering is a module in this package.

**A module here used to import ``codegen.compiler`` and ``codegen.refusal`` and
nothing else of this package, and that rule is retired.**  It was never about
design.  ``codegen.emit`` holds the table and names these lowerings, so an import
back the other way closes a cycle -- and under ``runpy`` (``python -m
codegen.emit``) that cycle resolved into TWO module objects rather than into an
``ImportError``, which is the failure D12 exists to prevent for ``Refusal``, one
layer in.  ``codegen/__main__.py`` removed the double binding, so there is one
``codegen.emit`` on every path and the prohibition has nothing left to prevent;
``tests/test_import_rule.py`` is down to the two boundaries that ARE about design
(``docs/plan/architecture.md`` §§8-10).

The cycle itself is still there -- ``emit.ROWS`` names ``bundle``'s selectors at
module level and ``bundle`` imports this package -- so the per-node decision is
reached through :func:`codegen.compiler.decide`, which defers the import to call
time.  §14 step 5 moves ``decide`` and the table in here and ends it.

So a row answers for its own node kind and is handed everything else:

* the NAME is an input (D3: "a name is an input to a lowering and is never
  computed inside one");
* the keyword SCREEN is run by the caller, over the set the row declares as
  a per-row CLAIMS set -- one screen for every row, reading ``codegen.keywords`` at
  the node's position, so a keyword cannot be silently dropped
  by one row's private copy of it;
* the nested-node decision is :func:`codegen.compiler.decide`, called by name --
  reference resolution still arrives on the :class:`codegen.compiler.Module` the
  row is handed, as ``mod.bind``, because that one is a closure over the RUN and
  not a function anything can name (§14 step 7);
* the MODULE text -- the header, the imports, the ``__all__`` -- is the module
  writer's.

A row's SELECTOR is its step's population test in ``codegen.bundle``, so a row
cannot come to claim a document its step does not count, and ``bundle`` may read a
lowering's own predicate to build one (``states_an_object_rule`` reads
``rules.presence_only``).  That direction is ``bundle`` -> ``lower``, and it is why
the reverse has to stay deferred: ``bundle`` is half-initialised while this package
loads, so a module-level import of ``emit`` from here reads a ``bundle`` whose
selectors do not exist yet.

A lane adds its module here, its selector to ``codegen.bundle``, and ONE row to
``codegen.emit.ROWS``.
"""
