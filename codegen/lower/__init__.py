"""One module per D2 row: what one kind of node becomes, and nothing else.

``docs/plan/rebuild-plan.md`` D13 and §5 Layout put the pieces here:
``codegen/__main__.py`` holds the command and the refusal report;
``codegen/emit.py`` holds the run; ``codegen/lower/decide.py`` holds the ONE per-node
dispatch; ``codegen/ir.py`` declares what a decision IS and ``codegen/render.py`` is the
one module that turns one into text (``docs/plan/architecture.md`` §7 and §8);
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
decision had to be reached through a deferred import.  §5 deleted the table -- "root and
non-root are one path.  There is no second table of root selectors" -- and the two
selectors that read a lowering (``union_root`` and ``states_an_object_rule``) are
``tests/populations.py``'s, so ``bundle`` imports nothing of this package and the
deferral has nothing left to break.

**``decide`` is in here, and this docstring said for a while that moving it was what
remained of step 5.**  ``codegen/lower/decide.py`` is the exhaustive ``match`` over
``codegen/schema/nodes.py``'s kinds, with ``assert_never`` on the last arm, and
``codegen/schema/parse.py`` is the parser it needs -- so the sentence a lane picking up
step 5 would have read first was the stalest one in the package.  Step 5's own exit
condition is the carrier deletion, and
``tests/test_import_rule.py::test_no_node_carries_the_mapping_it_was_parsed_from`` is
what holds it; that file is green.  What is still open in ``codegen/`` is §12's
dissolution of ``compiler.py``, which ``docs/plan/unimplemented.md`` Part B records as
INTERNAL and gives no verdict and no owner.

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
* the nested-node decision is :func:`codegen.lower.decide.decide`, called by name on a
  node the parser already built -- :func:`codegen.compiler.decide` is the ONE re-entry
  §5 names, a ``definitions`` entry parsed at DEF when a ``$ref`` asks for it -- and
  reference resolution is a LOOKUP on the :class:`codegen.compiler.Module` the row is
  handed (:meth:`codegen.compiler.Module.target`): the closure and the dependency order
  are computed in ``emit`` up front, so every target is finished before this document is
  parsed and the context carries DATA and no callable;
* the MODULE text -- the header, the imports, the ``__all__`` -- is the module
  writer's.

**A row has no SELECTOR any more.**  Each step's population test was a predicate in
``codegen.bundle`` doubling as the selector of a table row, which §11 names as the
second reading of a node's kind; the populations are measurements and live in
``tests/populations.py`` (§5), and the walk reads a node's kind once, in
:func:`codegen.lower.decide.decide`, at the node's own position.  So a lane adds its
module here and the ARM its kind reaches, and nothing anywhere claims a document.
"""
