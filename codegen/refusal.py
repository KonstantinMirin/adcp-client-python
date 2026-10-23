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

#: A ``$ref`` whose target is itself refused, which QUOTES THE TARGET'S OWN
#: REFUSAL after this prefix.  Whether this document is pending or final is
#: therefore not a property of its own sentence at all -- it is whatever the
#: target's is.  Producer: ``emit`` at the cross-document reference, as
#: ``f"its target {wanted} is refused: {r}"``.
CHAINED_TO_A_REFUSED_TARGET = "is refused: "


def is_a_verdict(detail: str) -> bool:
    """True when this refusal is final: a keyword this emitter will not lower.

    **A chained refusal is a verdict if and only if what it is chained to is
    one.**  That is TRANSITIVITY and not a third constant, which is why the
    comment above -- "a fourth kind means a fourth constant here" -- was right
    about the rule and wrong about this case.  The producer embeds the target's
    whole refusal after ``is refused: ``, so the answer is already in the string
    and this recurses into it rather than asking a new question of it.

    **Measured, and this was wrong for as long as the function existed.** On
    ``4a596febe``, 170 of 380 refusals quote a target's refusal. Reading only the
    outer sentence called every one of them a verdict:

        is_a_verdict as it was   674 emitted + 331 verdicts = 1005 accounted
        resolving the chain      674 emitted + 301 verdicts =  975 accounted
        overstated by 30, and pending understated 48 -> 79

    The bias was on every tree the epic has reported, so the DELTAS between rows
    were right and the absolutes were not.
    """
    head, _, rest = detail.partition(CHAINED_TO_A_REFUSED_TARGET)
    if rest and head.startswith("its target "):
        # The target's refusal is quoted whole, with its own pointer prefix
        # (``/allOf/0: $ref: ...``).  Strip to the detail and ask again: a chain
        # of any depth resolves because each link quotes the next.
        return is_a_verdict(rest.split(": ", 2)[-1] if ": " in rest else rest)
    return detail != DEFERRED_TO_A_LATER_ROW and UNRESOLVED_TARGET not in detail
