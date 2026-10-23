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


# --------------------------------------------------------------------------- #
# the three kinds of refusal, named where the refusal type lives
# --------------------------------------------------------------------------- #
# The exit condition asks for every document EMITTED, or REFUSED BY NAME,
# POINTER AND KEYWORD.  Only one of the three sentences below is such a refusal.
# The other two say "not built yet", and while they were unnamed the metric
# counted them as refusals: 404 + 41 of 476 on the tree that first measured this,
# so 93% of "refused" was pending work and ``emitted + refused == 1054`` was
# green throughout.
#
# These are CONSTANTS AND NOT A CLASSIFIER so that a reader of a refusal is
# comparing against the string its producer emits, not against a spelling a
# grader invented.  Each has exactly one producer, named beside it.  A fourth
# kind means a fourth constant here, not a regex somewhere else.

#: A draft-07 keyword no row lowers YET, and a later D2 row is expected to.
#: NOT a verdict -- the document is pending.  Producer: ``compiler.why_refused``.
DEFERRED_TO_A_LATER_ROW = "this step lowers no such keyword (a later D2 row does)"

#: A ``$ref`` whose target is itself refused, so this document clears when its
#: target does.  NOT a verdict.  Matched as a substring because the producer
#: names the URI first.  Producer: ``emit`` at the unresolved-reference check.
UNRESOLVED_TARGET = "is still unresolved after bundle.resolved"


def is_a_verdict(detail: str) -> bool:
    """True when this refusal is final: a keyword this emitter will not lower.

    False for the two pending kinds.  Read by the metric, so that "refused"
    cannot absorb "not built yet" without the count moving.
    """
    return detail != DEFERRED_TO_A_LATER_ROW and UNRESOLVED_TARGET not in detail
