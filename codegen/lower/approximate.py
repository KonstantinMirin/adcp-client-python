"""**The ONE place a widening is minted**, reading its rung off the cell.

``docs/plan/architecture.md`` section 2, "The handler's own obligation":
"``approximate(node, keyword)`` is to an approximation what ``Refusal``'s constructors
were to a kind: the ONE place a widening is minted, reading the rung off the cell
(section 3).  A handler never chooses a rung and never writes an attribution, for the
reason the reviews recorded for refusal kinds -- a decision made at the site that needs
it is a decision nobody can audit against the table that was supposed to hold it."

Section 3 states the four readings this function makes, and it makes no fifth:

* "the rung is ``cell(keyword, node.position).widens_to``, read by ``approximate`` and by
  nothing else";
* "a cell whose ``widens_to`` is ``None`` cannot be approximated, and a handler that asks
  for one is a ``BuildFailure`` -- the keyword states no fact, so a widening against it
  would be a declaration with nothing to declare, and section 8 would report it as
  *over-declared* forever";
* "a key with no row takes TOP, because an unrowed keyword's reach is unknown and TOP is
  the one rung that is safe without knowing it";
* "the attribution is ``Ours`` at the cell's own address unless ``attribution.py`` holds
  an entry for this document, pointer and keyword, in which case it is that entry's
  issue.  One lookup, no precedence to get wrong."

**Why derived** (section 3 again): "a handler that chose its own rung would choose the one
that makes its own output look best, and nothing could audit it against the table that was
supposed to hold the decision.  A rung read off the table cannot say that, because the
table is where the decision that the keyword compiles was made."

**The FACT is the document's own, and section 9 is why**: "Never approximate on a keyword
the walk itself inserted.  An approximation must name something the document states, or
the document is blamed for the compiler's own rewriting -- and the declaration then cannot
be checked, because section 8 looks for the fact in the document and does not find it."
So ``fact`` is a parameter and the caller passes what the DOCUMENT states, never a value
the walk derived; :func:`approximate` cannot check that for the caller, which is what
section 8's two set equalities are pointed at from the other side.

**No handler calls this yet, and that is section 14 step 8's exit condition.**  The step
is "the approximation, end to end, with no cell widened": the instrument exists and is
graded, ``APPROXIMATED`` is 0, and the first call site is step 9's and step 10's.
``tests/test_approximation.py`` exercises every arm here directly, because an instrument
with no production call site is otherwise graded by nothing.
"""

from __future__ import annotations

from adcp.types._base import SchemaRef

from codegen import attribution, ir, keywords
from codegen.keywords import Position, Rung
from codegen.refusal import BuildFailure


def rung_for(keyword: str, position: Position) -> Rung:
    """Which rung dropping ``keyword`` at ``position`` takes.  The cell's answer.

    A key with NO ROW takes :attr:`Rung.TOP`, which is the semantics document's section 7:
    "``Any`` and not a narrower rung, because an unrowed keyword's reach is unknown:
    draft-07 ignores it, so the document may be narrower than ``Any`` and can never be
    wider, and ``Any`` is the one rung that is safe without knowing what the keyword does."

    A cell whose ``widens_to`` is ``None`` raises, and the exception is a
    :class:`codegen.refusal.BuildFailure` rather than a refusal because it is a defect in
    the COMPILER: the cell says the keyword states no fact about an instance, so a handler
    asking to widen against it has asked for a declaration with nothing to declare, and
    section 8 would report that as *over-declared* for as long as it stood.
    """
    answer = keywords.cell(keyword, position)
    if answer is None:
        return Rung.TOP
    if answer.widens_to is None:
        raise BuildFailure(
            f"{keyword!r} at {position} compiles to {answer.effect} and states no fact "
            "about an instance, so its cell carries no rung and there is nothing for a "
            "widening to drop (architecture section 3).  A handler that cannot render "
            "this keyword has nothing to declare: either the cell is wrong, or the "
            "handler is widening against the wrong keyword"
        )
    return answer.widens_to


def attribution_for(document: str, pointer: str, keyword: str) -> str:
    """OURS or UPSTREAM's, by section 2's choice of two -- in ONE lookup.

    Section 2 of the semantics document: "**Ours.**  The design decided this widening; the
    sentence is the keyword's own row in section 5, 6 or 7.  The attribution is therefore
    the **cell's own address** and is derived, not stored ... **Upstream.**  The document
    could state the fact and does not, or states something no draft-07 reading can carry.
    The attribution is an **issue reference**, and it is a property of a document and a
    pointer rather than of a keyword."

    Section 3 of the architecture document settles the precedence in one sentence: "a
    site-level entry is more specific than a keyword-level one", so the registry is asked
    first and the cell's address is the answer where it holds nothing.
    """
    issue = attribution.issue_for(document, pointer, keyword)
    if issue is not None:
        return issue.attribution
    return keywords.address(keyword)


def approximate(
    ref: SchemaRef,
    keyword: str,
    position: Position,
    fact: object,
    *,
    kind: str = ir.WIDENED,
) -> ir.Approximation:
    """The declaration for one fact an annotation does not carry.

    ``ref`` is the node's own address, built by ``compiler.schema_ref`` -- the one
    function that spells a pointer the way ``__adcp_schema__`` spells it.  **One spelling
    and one producer**, which is what lets the verifier pair a declaration with a class by
    comparing a pointer to a pointer: a class carries ``SchemaRef(document, "#/properties/x")``
    and a declaration inside it carries a pointer under that prefix, so containment is a
    prefix test on one spelling rather than a reconciliation of two.

    ``fact`` is what the DOCUMENT states for ``keyword`` at that pointer, in the document's
    own spelling (section 2, and section 9's "never approximate on a keyword the walk
    itself inserted").

    ``kind`` defaults to ``WIDENED`` because that is every row's answer but one: section 2
    gives ``UNDERDETERMINED`` exactly one instance, "a union whose branches section 4's
    dispatch cannot separate", and section 6 of the architecture document has the union
    handler declare it at the union's own pointer.  A default and not a required argument,
    because the one caller that needs the other value is naming a specific row and every
    other caller would be restating the common case.
    """
    if kind not in ir.KINDS:
        raise BuildFailure(
            f"{kind!r} is not one of section 2's two kinds of approximation, "
            f"{ir.KINDS}: a third kind would be a figure nothing in section 8 grades"
        )
    return ir.Approximation(
        document=ref.document,
        pointer=ref.pointer,
        keyword=keyword,
        kind=kind,
        rung=rung_for(keyword, position).value,
        fact=fact,
        attribution=attribution_for(ref.document, ref.pointer, keyword),
    )
