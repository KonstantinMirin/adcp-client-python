"""One module per D2 row: the lowering that decides what a kind of node becomes.

A lowering reads a schema node and returns a declaration -- never Python text and
never a patch over somebody else's output.  ``codegen.emit`` owns the walk that
reaches a node and the module around the classes; ``codegen.compiler`` renders the
declaration.

``rules``  D6's six keyword families: what a document says about an instance as a
           whole rather than about one of its values.  A rule is class-level data,
           read by the one after-validator in ``adcp.types._runtime``.

This package imports nothing from ``codegen`` -- it sits at the bottom of the
import graph, so ``bundle`` (the selectors) and ``emit`` (the walk) can both read
a lowering's reading without a cycle.
"""
