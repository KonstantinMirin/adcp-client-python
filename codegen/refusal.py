"""The one refusal type, in a module that is never an entry point.  D12.

**Why it does not live in ``codegen/emit.py``.**  the command was once ``python -m
codegen.emit``, which runs under ``runpy`` -- that executes the named module as
``__main__``, and a lowering that imports ``codegen.emit`` for the exception
imports it a SECOND time, under its real name.  The class then has two
identities: ``except Refusal`` in the
``__main__`` copy does not catch the ``Refusal`` a lowering raised from the
``codegen.emit`` copy, so the CLI writes nothing over the whole population while
the in-process path -- which imports the module once, by name -- stays green.

That failure was measured three times independently by three lanes, each
diagnosing it from scratch.  It is structural and the fix is structural: the
exception lives in a module that no ``-m`` invocation can name, so there is one
class object no matter how the run was started.  Nothing is imported here, which
is also what keeps the import graph acyclic once every lowering needs it.

``codegen/__main__.py`` now holds the command and the same rule is general: no
module of this compiler is ever bound as ``__main__``, so no module of it has two
identities.  This one keeps its own guarantee regardless of where the entry point
sits, which is what makes it unconditional rather than a consequence of today's
command line.
"""

from __future__ import annotations

from enum import StrEnum


class Kind(StrEnum):
    """What a refusal MEANS, declared by the producer that raises it.

    **The kind is an ARGUMENT and not a reading of the detail.**  Four times the
    epic's headline number was wrong, always optimistically, and every time
    because the kind of a refusal was decided by reading its English:

    1. ``emitted + refused == 1054`` was green while 385 documents waited on rows
       nobody had written -- "refused" admitted "not built yet".
    2. A regex over the detail read 609 accounted against the producers' own
       877: the pattern matched ``"D2 row"`` inside the VERDICT sentence and
       reclassified 268 verdicts as deferrals.
    3. The classifier read a refusal's own sentence only, so 170 refusals
       QUOTING another document's refusal counted as verdicts: 1005 -> 975.
    4. 86 refusals the classifier called verdicts state in their own text that
       the lowering for the position has not been written -- "a later D2 row
       lowers this one", "a branch composes once that reader is shared",
       "the harness's row": 1053 -> 967.

    The first three were each fixed by making the SENTENCE more carefully read.
    This one is fixed by not reading it: a producer passes its kind, and
    :func:`is_a_verdict` consults nothing else, so the question stops being
    answerable by grep.
    """

    #: Final.  A keyword this emitter will not lower, because the obstruction is
    #: a property of the document, of pydantic, or of the pointer space -- not of
    #: what has been written.  THIS is the kind the exit condition counts.
    VERDICT = "verdict"

    #: Pending.  The lowering for this position has not been written, or cannot
    #: be reached from this row.  The refusal names the row, step, module or
    #: mechanism that would clear it.
    DEFERRED = "deferred"

    #: Pending.  A ``$ref`` the bundle's one resolution did not reach, so the
    #: document the package would carry is not locally decidable.
    UNRESOLVED = "unresolved"

    #: Neither, and that is the point: this refusal is whatever the refusal it is
    #: chained to is.  A producer raising one passes ``through=`` the target's
    #: refusal, and :attr:`Refusal.resolved` carries the target's answer.
    CHAINED = "chained"


#: The kinds that are FINAL -- a document refused with one is accounted for.
FINAL_KINDS = frozenset({Kind.VERDICT})

#: The kinds that are PENDING -- the document is not refused, it is waiting.
PENDING_KINDS = frozenset({Kind.DEFERRED, Kind.UNRESOLVED})

#: The kinds that DELEGATE -- the answer is the target's, never their own.
DELEGATING_KINDS = frozenset({Kind.CHAINED})

#: Every kind a RESOLVED refusal can carry.  A delegating kind is not one: it is
#: resolved to the target's before anything counts it.
RESOLVED_KINDS = FINAL_KINDS | PENDING_KINDS


class Refusal(Exception):
    """One document this emitter will not approximate, and why.

    A refusal is the designed outcome of a keyword the emitter does not lower: a
    model that quietly ignores a constraint is wider than its schema, which is
    the defect class P3 exists to remove.  Every refusal names the document (the
    caller), the ``keyword`` that stopped it, the ``pointer`` of the node that
    carried it, and its :class:`Kind`, so the refusal report is actionable and
    CLASSIFIED without re-running and without re-reading its sentence.

    ``kind`` is required and has no default.  A default is how a fourth category
    gets silently absorbed into a third: a producer that forgets to say what its
    refusal means would be counted as whatever the default says, which is the
    defect :class:`Kind` exists to close.
    """

    def __init__(
        self,
        kw: str,
        pointer: str,
        detail: str,
        kind: Kind,
        *,
        through: Refusal | None = None,
    ) -> None:
        super().__init__(f"{pointer or '/'}: {kw}: {detail}")
        self.keyword = kw
        self.pointer = pointer or "/"
        self.detail = detail
        self.kind = kind
        if (kind in DELEGATING_KINDS) != (through is not None):
            raise TypeError(
                f"a {kind} refusal {'needs' if through is None else 'takes no'} "
                "through=: a delegating kind carries the refusal it delegates to, "
                "and a kind that answers for itself carries none"
            )
        #: The kind that COUNTS, which is never a delegating one.  Resolved at
        #: construction by carrying the target's, so a chain of any depth is one
        #: attribute read and no sentence is parsed.
        self.resolved: Kind = kind if through is None else through.resolved


def is_a_verdict(kind: Kind) -> bool:
    """True when a refusal is final.  Reads the KIND and nothing else.

    There is no string in this function and no constant for it to compare
    against, which is the whole of the fix: the four instances in
    :class:`Kind`'s docstring were all a reading of English, and the last two
    were a reading of English by this very function.

    A delegating kind is a caller error here rather than a case to handle --
    :attr:`Refusal.resolved` has already followed it, so a caller holding one
    has read ``kind`` where it meant ``resolved``.
    """
    if kind in DELEGATING_KINDS:
        raise ValueError(f"{kind} delegates: ask Refusal.resolved, which has followed it")
    return kind in FINAL_KINDS


# --------------------------------------------------------------------------- #
# the sentences, which are now ONLY sentences
# --------------------------------------------------------------------------- #
# These were a classifier: a reader of a refusal compared its detail against the
# string its producer emits.  They are no longer, because :class:`Kind` is, and
# what is left of them is what they always were -- the TEXT two producers write,
# named here so a reworded message moves in one place.  Nothing decides anything
# by comparing against one.

#: A draft-07 keyword no row lowers YET, and a later D2 row is expected to.
#: Producer: ``compiler._why``, which pairs it with ``Kind.DEFERRED``.
DEFERRED_TO_A_LATER_ROW = "this step lowers no such keyword (a later D2 row does)"

#: A ``$ref`` the bundle's resolution did not reach.  Producer: ``emit`` at the
#: unresolved-reference check, which pairs it with ``Kind.UNRESOLVED``.
UNRESOLVED_TARGET = "is still unresolved after bundle.record"

#: The prefix a chained refusal quotes its target's whole refusal after.
#: Producer: ``emit`` at the cross-document reference, as
#: ``f"its target {wanted} is refused: {r}"``, paired with ``Kind.CHAINED`` and
#: ``through=`` that target's refusal.  The quoted text is for the READER; the
#: classification travels through ``through=``.
CHAINED_TO_A_REFUSED_TARGET = "is refused: "
