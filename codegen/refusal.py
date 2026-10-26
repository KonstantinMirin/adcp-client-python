"""The one refusal type, in a module that is never an entry point.  D12.

**A refusal is a VALUE and nothing raises one** (``docs/plan/architecture.md`` §2:
"``decide(node, ctx)`` returns ``Lowering | Refusal``.  Every handler has that
signature.  A refusal is a VALUE a parent returns upward unchanged; nothing raises one
and nothing catches one").  :class:`Refusal` therefore does not subclass ``Exception``:
the class cannot be raised at all, so the rule is held by the type system rather than by
a convention a reader has to keep.  §13 item 4 settles the sentence of the semantics
document that said otherwise -- "``Refusal`` lives in the package every lowering imports,
so any step can raise one" -- as "the reason holds unchanged; 'raise' becomes 'return'".

What that buys is §9's "a crash is not an outcome", mechanically: a caller that reads a
:class:`codegen.compiler.Decided` field off a result the walk may have refused is a TYPE
ERROR, because a ``Decided`` and a ``Refusal`` are different types and nothing holds
both.  The partial model §2 of the semantics document forbids -- a document emitting
some declarations and then refusing -- is unrepresentable for the same reason.

**The one exception that stays an exception is :class:`BuildFailure`**, and the division
is whose property the fault is: a refusal is a property of a DOCUMENT, a build failure is
a property of the COMPILER.  §2: "a defect in the compiler itself -- two selectors
claiming one node, two constraints deriving one alias name -- stays an exception
(``BuildFailure``) that no layer catches, because it is not an outcome of any document
and the run must stop on it."  So there is no ``try`` around a refusal anywhere, and the
one ``try`` left in this compiler is around nothing.

**Why this module is not ``codegen/emit.py``, which outlives the exception.**  The
command was once ``python -m codegen.emit``, which runs under ``runpy`` -- that executes
the named module as ``__main__``, and a lowering that imports ``codegen.emit`` for the
class imports it a SECOND time, under its real name.  The class then has two identities,
and a comparison across that boundary -- ``except Refusal`` then, ``isinstance(x,
Refusal)`` now -- answers no.  That failure was measured three times independently by
three lanes, each diagnosing it from scratch, and it is structural: the class lives in a
module no ``-m`` invocation can name, so there is one class object no matter how the run
was started.  Nothing of this package is imported here, which is also what keeps the
import graph acyclic once every lowering needs it.

``codegen/__main__.py`` now holds the command and the same rule is general: no module of
this compiler is ever bound as ``__main__``, so no module of it has two identities.  This
one keeps its own guarantee regardless of where the entry point sits, which is what makes
it unconditional rather than a consequence of today's command line.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum


class Kind(StrEnum):
    """What a refusal MEANS, read off the TABLE CELL for the keyword at the position.

    ``docs/plan/architecture.md`` §3, "Where the kind of a refusal comes from": "a
    refusal's kind is derived from the cell and never chosen at a raise site".
    :func:`codegen.compiler.kind_for` is that derivation and it reads
    ``keywords.cell(keyword, position)``; a document that CONTRADICTS ITSELF, or a
    malformed one, is a verdict on its own terms and does not go through the table, which
    is the division ``bundle.record`` already draws.

    **The kind is never a reading of the detail.**  Four times the
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
    This one is fixed by not reading it: the kind travels as a field, and
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

    # **``UNRESOLVED`` IS RETIRED, and §3 is the sentence**: "UNRESOLVED disappears.  It
    # named a reference the delegated resolver did not reach, and the resolver in §4
    # reaches every position."  ``bundle.record`` became this package's own inliner at
    # §14 step 3 and it inlines every cross-document reference the descent column
    # reaches, sections included -- so a reference surviving at a position the package's
    # own validation decides through is not an outcome of any document, it is the
    # inliner disagreeing with ``bundle.undecidable_references`` about which positions
    # validation reaches.  That is a property of the COMPILER, so ``emit``'s check for
    # it raises :class:`BuildFailure` and no kind is minted.  Measured over the 1,054
    # portable documents at ``d048658``: the kind was carried by **0** refusals, so the
    # retirement moves no document.  §13 item 5 records that the kind "is not in the
    # document" at all.

    #: Neither, and that is the point: this refusal is whatever the refusal it is
    #: chained to is.  A producer raising one passes ``through=`` the target's
    #: refusal, and :attr:`Refusal.resolved` carries the target's answer.
    CHAINED = "chained"


#: The kinds that are FINAL -- a document refused with one is accounted for.
FINAL_KINDS = frozenset({Kind.VERDICT})

#: The kinds that are PENDING -- the document is not refused, it is waiting.
PENDING_KINDS = frozenset({Kind.DEFERRED})

#: The kinds that DELEGATE -- the answer is the target's, never their own.
DELEGATING_KINDS = frozenset({Kind.CHAINED})

#: Every kind a RESOLVED refusal can carry.  A delegating kind is not one: it is
#: resolved to the target's before anything counts it.
RESOLVED_KINDS = FINAL_KINDS | PENDING_KINDS


class Refusal:
    """One document this emitter will not approximate, and why -- as a VALUE.

    A refusal is the designed outcome of a keyword the emitter does not lower: a
    model that quietly ignores a constraint is wider than its schema, which is
    the defect class P3 exists to remove.  Every refusal names the document (the
    caller), the ``keyword`` that stopped it, the ``pointer`` of the node that
    carried it, and its :class:`Kind`, so the refusal report is actionable and
    CLASSIFIED without re-running and without re-reading its sentence.

    **It is not an ``Exception`` and cannot be raised** (``docs/plan/architecture.md``
    §2; this module's own docstring carries the reasoning).  A handler RETURNS one and a
    parent returns it upward unchanged, so the walk's own type says that a result is
    either a decision or a refusal -- and a caller that reads a decision's field without
    handling the other branch does not type-check.  :func:`first_refusal` is the one
    combinator over a sequence of child results.

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
        #: The one-line rendering, which ``Exception.__init__`` used to hold.  A
        #: refusal that quotes another one reads it through ``str`` (``emit``'s chained
        #: ``$ref``), so the sentence has to survive the class ceasing to be an
        #: exception -- :meth:`__str__` is where it now lives.
        self.message = f"{pointer or '/'}: {kw}: {detail}"
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

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"Refusal({self.message!r}, kind={self.kind}, resolved={self.resolved})"


class BuildFailure(Exception):
    """A defect in the COMPILER, which is not an outcome of any document.

    ``docs/plan/architecture.md`` §2: "a defect in the compiler itself -- two selectors
    claiming one node, two constraints deriving one alias name -- stays an exception
    (``BuildFailure``) that no layer catches, because it is not an outcome of any
    document and the run must stop on it."  So this is the one thing in the compiler that
    is still raised, and nothing anywhere catches it: a run that reaches one writes no
    tree and reports no refusal, because there is no document to report it against.

    **The division is whose property the fault is**, and it is the whole of why there
    are two types.  A :class:`Refusal` says the obstruction is in the DOCUMENT (or in
    pydantic, or in the pointer space), names it by document, pointer and keyword, and is
    counted -- so filing a compiler defect as one would file it against a bundle that
    did nothing wrong and let the build pass.  The two instances §2 names are the two
    the compiler has: :class:`codegen.constraints.AliasCollision` subclasses this, and
    the ambiguous-root case became unrepresentable when §5 deleted the root selector
    table (``emit``'s own comment carries that measurement).
    """


def first_refusal(results: Iterable[object]) -> Refusal | None:
    """The EARLIEST refusal among a sequence of child results, or ``None``.

    ``docs/plan/architecture.md`` §2 makes this "the one combinator over a sequence of
    child results", and §6 states its contract: "A document refused by a child's refusal
    is refused once, on the earliest refusal in document order, which keeps the report a
    function of the document and not of the walk's iteration."

    **Document order is the ARGUMENT's order and not a comparison made here**, and that
    is the whole of why there is no sort: a pointer STRING cannot be ordered -- ``/10``
    sorts before ``/2``, and a property map's order is the document's own insertion order
    and not its sorted one -- so the only thing that knows document order is the parser,
    which built each node's children in the order the document states them.  This reads
    that order off the sequence it is handed.  §14 step 5's own note says what that
    settles: the present report follows "the walk's iteration", which is "what this step
    exists to remove", so a sequence a caller assembles in any other order is the
    caller's defect and not something a combinator could repair.

    A handler that lowers its children in a LOOP and returns the first refusal it sees is
    this function FUSED with the map that produced the sequence, and gives the same
    answer for the same reason: the loop runs in the children's own order.

    **Which form a caller takes is decided by whether the map is PURE, and the rule was
    measured rather than preferred.**  Both forms answer with the earliest refusal in
    document order; only the fused one STOPS at it.  So where producing a child's result
    has an effect -- resolving a reference emits the target's module into the run,
    building a field records a dropped default on the module -- the batch form runs the
    effects of children AFTER the refusing one, and the run then carries a document the
    refused one never reaches.  Measured on this tree at ``lower.union.lower_union``:
    planning every branch before reading the earliest refusal emitted
    ``core/assets/webhook-asset.json`` into the committed population's tree, one module
    more than the run before it and with the refusal report unchanged -- a side effect
    of the walk's iteration, which is the thing §6's rule exists to keep out of the
    answer.  The batch form is therefore for a pure map and the fused loop for one with
    effects; each caller says which it is.

    Typed over ``object`` rather than over a type variable, because what it answers is a
    question about the SEQUENCE and not about the surviving values: a caller that needs
    those keeps them, and ``isinstance`` is what narrows them.  That is deliberate -- a
    signature promising to strip the refusals out would need a cast to deliver it, and
    §14 step 6 admits none.
    """
    return next((r for r in results if isinstance(r, Refusal)), None)


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

#: A ``$ref`` the bundle's one resolution did not reach.  Producer: ``emit`` at the
#: unresolved-reference check -- which mints NO KIND, because §3 retires
#: ``Kind.UNRESOLVED`` and what the check now reports is the inliner disagreeing with
#: ``bundle.undecidable_references``, a property of the compiler and so a
#: :class:`BuildFailure`.  The sentence stays here because this is where the compiler's
#: refusal and build-failure texts are named once each.
UNRESOLVED_TARGET = "is still unresolved after bundle.record"

#: The prefix a chained refusal quotes its target's whole refusal after.
#: Producer: ``emit`` at the cross-document reference, as
#: ``f"its target {wanted} is refused: {r}"``, paired with ``Kind.CHAINED`` and
#: ``through=`` that target's refusal.  The quoted text is for the READER; the
#: classification travels through ``through=``.
CHAINED_TO_A_REFUSED_TARGET = "is refused: "
