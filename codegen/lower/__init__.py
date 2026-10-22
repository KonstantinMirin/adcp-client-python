"""One module per D2 row.

``docs/plan/rebuild-plan.md`` § Layout: ``codegen/emit.py`` holds the CLI, the module
writer and the refusal report, ``codegen/compiler.py`` drives the compiler, and each
lowering lives here.  A dispatch table of ``(selector, lowering)`` pairs in ``emit``
connects them, and a document selected by two rows is a build failure rather than a
question of precedence.
"""
