"""The one refusal type, in a module that is never an entry point.  D12.

**Why it does not live in ``codegen/emit.py``.**  ``python -m codegen.emit`` runs
under ``runpy``, which executes the named module as ``__main__`` -- and a lowering
that imports ``codegen.emit`` for the exception imports it a SECOND time, under
its real name.  The class then has two identities: ``except Refusal`` in the
``__main__`` copy does not catch the ``Refusal`` a lowering raised from the
``codegen.emit`` copy, so the CLI writes nothing over the whole population while
the in-process path -- which imports the module once, by name -- stays green.

That failure was measured three times independently by three lanes, each
diagnosing it from scratch.  It is structural and the fix is structural: the
exception lives in a module that no ``-m`` invocation can name, so there is one
class object no matter how the run was started.  Nothing is imported here, which
is also what keeps the import graph acyclic once every lowering needs it.
"""

from __future__ import annotations


class Refusal(Exception):
    """One document this emitter will not approximate, and why.

    A refusal is the designed outcome of a keyword the emitter does not lower: a
    model that quietly ignores a constraint is wider than its schema, which is
    the defect class P3 exists to remove.  Every refusal names the document (the
    caller), the ``keyword`` that stopped it, and the ``pointer`` of the node
    that carried it, so the refusal report is actionable without re-running.
    """

    def __init__(self, kw: str, pointer: str, detail: str) -> None:
        super().__init__(f"{pointer or '/'}: {kw}: {detail}")
        self.keyword = kw
        self.pointer = pointer or "/"
        self.detail = detail
