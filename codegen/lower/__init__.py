"""One module per D2 row: what one kind of node becomes, and nothing else.

``docs/plan/rebuild-plan.md`` D13 and §5 Layout put the pieces here:
``codegen/emit.py`` holds the CLI, the module writer, the refusal report and the
dispatch table ``ROWS``; ``codegen/compiler.py`` drives the compiler and holds the
machinery a lowering is handed; and each lowering is a module in this package.

**A module here imports ``codegen.compiler`` and ``codegen.refusal``, and nothing
else of this package.**  That is a constraint, not a convention, and
``tests/test_import_rule.py`` resolves the imports of every module here by AST and
fails on any other name under ``codegen``.

The reason is not style.  ``codegen.emit`` holds the table and names these
lowerings, so an import back the other way closes a cycle -- and under ``runpy``
(``python -m codegen.emit``) that cycle resolves into TWO module objects rather
than into an ``ImportError``, which is the failure D12 already exists to prevent
for ``Refusal``, one layer in.  A ``TYPE_CHECKING`` import hides the cycle from the
type checker without removing it, because the lowering needs the machinery at RUN
time.  Moving the machinery into ``compiler`` is what makes the one-directional
import true rather than merely intended.

So a row answers for its own node kind and is handed everything else:

* the NAME is an input (D3: "a name is an input to a lowering and is never
  computed inside one");
* the keyword SCREEN is run by the caller, over the set the row declares as
  ``HANDLED`` -- one screen for every row, so a keyword cannot be silently dropped
  by one row's private copy of it;
* the nested-node decision arrives on the :class:`codegen.compiler.Module` the row
  is handed, as ``mod.decide``, the same way reference resolution arrives as
  ``mod.bind`` -- so a lowering decides a child without naming ``emit``;
* the MODULE text -- the header, the imports, the ``__all__`` -- is the module
  writer's.

A row's SELECTOR is its step's population test in ``codegen.bundle``, so a row
cannot come to claim a document its step does not count, and ``bundle`` may read a
lowering's own predicate to build one (``states_an_object_rule`` reads
``rules.presence_only``).  That direction is ``bundle`` -> ``lower``, which the
import rule above permits; the reverse would be a lowering importing this package's
other half.

A lane adds its module here, its selector to ``codegen.bundle``, and ONE row to
``codegen.emit.ROWS``.
"""
