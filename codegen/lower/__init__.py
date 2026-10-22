"""One module per D2 row, connected to the walk by the dispatch table in
``codegen.emit``.

A row here decides what one KIND of node becomes.  It reads the schema, refuses a
keyword it does not lower, and hands the compiler a decided type -- it writes no
annotation text, which is the seam ``docs/plan/rebuild-plan.md`` §1 draws.
"""
