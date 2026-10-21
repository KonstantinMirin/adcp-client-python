"""Build-time instruments. Not shipped.

This package sits OUTSIDE ``src/`` deliberately: ``packages.find`` globs
``where = ["src"]``, and ``harness`` imports ``hypothesis`` and
``hypothesis_jsonschema``, which are dev-only. Under ``src/adcp/`` it would be
an installed module raising ``ModuleNotFoundError`` for every user of the SDK.

  ``harness``  grades a (JSON Schema document, Python class) pair in BOTH
               directions: direction 1 generates an instance the schema admits
               and requires the class to admit it; direction 2 mutates one
               keyword at a time and requires the class to refuse it. Imports
               ``jsonschema``, ``hypothesis``, ``hypothesis_jsonschema`` and
               ``pydantic`` and nothing else — no sibling, no path, no
               filesystem, and no name from the vocabulary it is pointed at.

That genericity is the reason this file is the only one here: the harness can be
pointed at whatever the emitter produces without knowing anything about it.
Every other module in this package is written by a step of
``docs/plan/rebuild-plan.md``, and an adapter that points the harness at a tree
is written by the step that first has a tree to point it at.
"""
