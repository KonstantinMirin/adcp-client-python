"""Build-time instruments. Not shipped.

This package sits OUTSIDE ``src/`` deliberately: ``packages.find`` globs
``where = ["src"]``, and ``harness`` imports ``hypothesis`` and
``hypothesis_jsonschema``, which are dev-only. Under ``src/adcp/`` it would be
an installed module raising ``ModuleNotFoundError`` for every user of the SDK.

  ``harness``   runs three checks over a (JSON Schema document, Python class)
                pair: the ACCEPTS check generates an instance the schema admits
                and requires the entry point to admit it; the REFUSES check
                mutates one keyword at a time and requires it to refuse; and the
                SCHEMA COMPARISON compares the class's own
                ``model_json_schema()`` to the document. Imports
                ``jsonschema``, ``hypothesis``, ``hypothesis_jsonschema`` and
                ``pydantic`` and nothing else — no sibling, no path, no
                filesystem, and no name from the vocabulary it is pointed at.
  ``bundle``    which documents the bundle holds, and reading one.
  ``__main__``  the one entry point, so ``python -m codegen`` is the command and
                no module of this package is ever bound as ``__main__``. Owns the
                argument parser and the refusal report, and nothing else.
  ``emit``      the WALK: it reads a document and decides what each node becomes.
                Owns the module around the classes.
  ``compiler``  the seam. A class declaration in, Python out, rendered by
                ``datamodel-code-generator``'s pydantic-v2 model layer.
  ``refusal``   the one refusal type, in a module no ``-m`` can name (D12).

The harness's genericity is why nothing points it at a tree: an emitted class
carries the schema it was generated from, so the pairing is read off the class.
The adapter that used to carry it is gone, and with it the failure where a
grader was aimed at a tree the run had not emitted.
"""
