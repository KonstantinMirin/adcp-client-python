"""One module per D2 row: what one kind of node becomes, and nothing else.

``docs/plan/rebuild-plan.md`` D13 and §5 Layout put the pieces here:
``codegen/__main__.py`` holds the command and the refusal report;
``codegen/emit.py`` holds the run and the ONE per-node dispatch;
``codegen/ir.py`` declares what a decision IS and ``codegen/render.py`` is the one
module that turns one into text (``docs/plan/architecture.md`` §7 and §8);
``codegen/compiler.py`` holds the machinery a lowering is handed; and each lowering
is a module in this package.

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

**The cycle itself is gone, at §14 step 5.**  ``emit.ROWS`` named ``bundle``'s root
selectors at module level while ``bundle`` imported this package, so the per-node
decision had to be reached through :func:`codegen.compiler.decide`, which defers the
import to call time.  §5 deletes the table -- "root and non-root are one path.  There
is no second table of root selectors" -- and the two selectors that read a lowering
(``union_root`` and ``states_an_object_rule``) are ``tests/populations.py``'s, so
``bundle`` imports nothing of this package and the deferral has nothing left to break.
What remains of step 5 is moving ``decide`` itself in here, as the exhaustive ``match``
over ``codegen/schema/nodes.py``'s kinds, which needs ``schema/parse.py``.

So a row answers for its own node kind and is handed everything else:

* the NAME is not an input at all.  §7 reads D3's rule strictly -- "the walk computes
  no name, which is the semantics document's own rule that a name is an input to a
  lowering and is never computed inside one -- read strictly, it is not an input
  either: it is assigned after" -- so a row declares at a POINTER and
  ``codegen/lower/names.py`` assigns every symbol in one pass over the finished module;
* the keyword SCREEN is run by the caller, over the set the row declares as
  a per-row CLAIMS set -- one screen for every row, reading ``codegen.keywords`` at
  the node's position, so a keyword cannot be silently dropped
  by one row's private copy of it;
* the nested-node decision is :func:`codegen.compiler.decide`, called by name, and
  reference resolution is a LOOKUP on the :class:`codegen.compiler.Module` the row is
  handed (``mod.target``): §14 step 7 computes the closure and the dependency order in
  ``emit`` up front, so every target is finished before this document is parsed and
  the context carries DATA and no callable;
* the MODULE text -- the header, the imports, the ``__all__`` -- is the module
  writer's.

**A row has no SELECTOR any more.**  Each step's population test was a predicate in
``codegen.bundle`` doubling as the selector of a table row, which §11 names as the
second reading of a node's kind; the populations are measurements and live in
``tests/populations.py`` (§5), and the walk reads a node's kind once, in
``emit._decide``, at the node's own position.  So a lane adds its module here and the
ARM its kind reaches, and nothing anywhere claims a document.
"""
