"""The decision machinery a lowering is handed: a node in, a declaration out.

``docs/plan/rebuild-plan.md`` §1 splits the pipeline at a DECISION rather than at a
translation.  Our walk reads the JSON Schema and decides what each node becomes -- a
class, an annotation, an enumeration or a rule -- what it is called, which fields it has
and what constrains them.  This module is the shared half of that walk, and what it
produces is ``codegen.ir``: **nothing here holds a string of Python**
(``docs/plan/architecture.md`` §7), and ``codegen.render`` is the one module that turns a
declaration into text.

**D13 puts the shared machinery here and not in ``codegen.emit``**, and the reason
is an import rule rather than a preference.  A lowering under ``codegen/lower/``
imports this module and ``codegen.refusal`` and nothing else of this package: it
never imports ``codegen.emit``, because ``emit`` holds the dispatch table that
names it, and an import back the other way closes a cycle that ``python -m
codegen.emit`` resolves into TWO module objects rather than into an ``ImportError``
-- the failure D12 already exists to prevent for ``Refusal``, one layer in.  A
``TYPE_CHECKING`` import hides that cycle from the type checker without removing
it, because the lowering needs the machinery at RUN time.  So the machinery moves,
which is what makes the one-directional import true rather than intended.

What is here, in D13's own terms: the field builder (:func:`fields`), the class
declarer (:func:`declare_object`, and :func:`declare_alias` beside it for a root
D2 makes an alias), and the carriers a lowering is handed (:class:`Module`,
:class:`Shape`, :class:`Target`, :class:`Decided`), with the keyword screen
(:func:`check_keywords`), the name rules (D3) and :func:`lower_object` -- which is
:func:`fields` plus :func:`declare_object` and has nothing else in it -- alongside.

**What did NOT move is the per-node dispatch.**  ``emit.decide_type`` answers "what
IS this node", and for an array, a mapping or a multi-type node the answer lives in
``codegen.lower.containers``, so putting it here would make this module import a
lowering.  It used to arrive the way reference resolution still arrives, as a
callable on :class:`Module` with a refusing default, because reaching ``emit`` by
name was forbidden while ``python -m codegen.emit`` bound that file twice under
``runpy``.  ``codegen/__main__.py`` ended that, and :func:`decide` is the name:
one function, one deferred import, and a :class:`Module` carrying data.

**§14 steps 5 and 7 dissolve this module.**  The node kinds and the one parser take
:func:`check_keywords`, the applied-type reading and the per-node dispatch
(``codegen/schema/``); the naming pass takes :func:`class_name`, :func:`field_name` and
:attr:`Module.declared` (``codegen/lower/names.py``); the handlers take
:func:`lower_object` and :func:`lower_composition` (``codegen/lower/<kind>.py``).  Two
things follow that are named rather than hidden: :attr:`Module.bind` is still a CLOSURE
over the run, which step 7 replaces with a dependency-ordered ``targets`` map; and
:func:`field_name` still reads what pydantic's ``BaseModel`` carries, which is the one
model-layer import left outside ``codegen.render`` and which step 7 has to answer when
the name rules move into ``lower/`` -- ``tests/test_import_rule.py`` names it and the
set it sits in may only shrink.
"""

from __future__ import annotations

import keyword
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any, NamedTuple

from adcp.types._base import Approximation, SchemaRef
from adcp.types._runtime import ForbiddenGroups, Rule
from codegen import ir, keywords, refusal
from codegen.ir import MISSING
from codegen.keywords import Position
from codegen.lower import names
from codegen.refusal import BuildFailure, Kind, Refusal, first_refusal
from codegen.schema import nodes, parse as schema

SCALAR = {"string": "str", "integer": "int", "number": "float", "boolean": "bool"}


# --------------------------------------------------------------------------- #
# the machinery a lowering is handed (D13)
# --------------------------------------------------------------------------- #
# **``rule_sources``, ``combinators`` and ``declares`` are ``codegen/keywords.py``'s
# now.**  Each is a predicate over a CELL, so each belongs to the layer §11 gives
# "positions, keywords, cells, descent" -- and ``codegen/schema/parse.py``'s
# classification (§4) asks all three while being forbidden to import this module: §11's
# arrow is ``keywords <- ir <- schema <- lower``.  Re-bound here under their own names so
# that every existing reader keeps one spelling of each.
rule_sources = keywords.rule_sources
combinators = keywords.combinators
declares = keywords.declares


def declaring(node: Mapping[str, Any], position: Position) -> dict[str, Any]:
    """``node`` less every key that annotates without constraining.

    One reading for the four callers that used to subtract a hand-written annotation
    set and the ``x-`` prefix by hand.
    """
    return {k: v for k, v in node.items() if declares(k, position)}


def inert_beside_a_reference(
    node: Mapping[str, Any], pointer: str, position: Position, mod: "Module | None" = None
) -> frozenset[str]:
    """§5's ``$ref`` row: the CONSTRAINING siblings, which compile to NOTHING and are
    REPORTED.

    **Settled by the design owner on 2026-10-25, in both documents.**  §5's ``$ref``
    row now reads: "A CONSTRAINING sibling → nothing, and REPORTED: draft-07 ignores
    every sibling of ``$ref``, so the keyword constrains no instance and the document's
    accepted set is the target's alone.  The record keeps the key, because §3 drops
    none; the declaration's cell says it compiles to nothing at this co-occurrence, so
    §8 does not grade it; and the report names it, because a key that reads as a
    constraint and is inert is worth reading once.  Refusing it instead would refuse a
    document whose accepted set its own draft decides, and letting the referring value
    win would make the record state an acceptance fact the bundle does not."
    ``docs/plan/architecture.md`` §13 item 2 carries the reasoning and limits §13.2's
    "referring node wins" to ANNOTATION siblings.

    So this is the co-occurrence, decided in ONE place and read by the two arms that
    meet it -- ``emit._decide``'s reference arm and
    :func:`lower_composition`'s ``$ref``-conjunct arm.  Both refused as VERDICTS on
    the sibling before, which is the self-undermining reason the epic recorded: if
    draft-07 ignores the keyword it constrains no instance, so the obstruction belongs
    to neither the document, nor pydantic, nor the pointer space -- and a verdict
    claims it belongs to one of the three.

    **A key with NO ROW still refuses, and a REFUSE cell still refuses.**  Neither is a
    constraining sibling in the sense the row decides: §9 says a keyword in none of §5,
    §6 or §7 is one the bundle did not use and the first document to carry one is loud
    rather than ignored, and §7's own keywords are refused wherever they appear.  What
    this names is exactly the keys whose CELL LOWERS at this position -- the ones that
    read as a constraint -- and the caller hands them to the screen as claimed.

    An ANNOTATION sibling is not here: §5 gives it the other answer (the sibling's
    description wins), the table admits it at every position, and
    ``bundle.record._beside`` is what keeps it beside the inlined copy.
    """
    inert = frozenset(
        k
        for k in node
        if k != "$ref"
        and (answer := keywords.cell(k, position)) is not None
        and keywords.lowers(answer)
    )
    if mod is not None:
        report_inert(inert, pointer, mod)
    return inert


def report_inert(inert: "Collection[str]", pointer: str, mod: "Module") -> None:
    """The REPORTED half of §5's ``$ref`` row, for a caller that already has the set.

    ``codegen/lower/references.py`` reads :attr:`nodes.Reference.inert` -- the parser's
    one reading of the co-occurrence (§4) -- so it needs the report and not the reading;
    :func:`inert_beside_a_reference` is still the reading for ``lower_composition``'s
    ``$ref``-conjunct arm, which meets the co-occurrence on a DECLARATION.
    """
    mod.carries_nothing.extend(
        f"{pointer or '/'}: {k}: a constraining sibling of $ref, which draft-07 "
        "ignores, so the keyword constrains no instance and the document's accepted "
        "set is the target's alone (section 5's $ref row); the record keeps the key "
        "and section 8 does not grade it"
        for k in sorted(inert)
    )



# --------------------------------------------------------------------------- #
# names (D3) are ``codegen/lower/names.py``'s now
# --------------------------------------------------------------------------- #
# **``class_name`` and ``field_name`` moved with §4's name rules** (§14 step 7, and §7's
# "naming is a pass over the module, not a thread through the walk").  Re-bound here
# under their own names so that every existing reader keeps one spelling, the way
# ``rule_sources`` and ``declares`` are -- and ``field_name`` takes the reserved set as
# an argument now, which is how the one model-layer import left outside
# ``codegen/render.py`` was answered: the set is DERIVED in the renderer
# (``render.RESERVED``) and the run hands it to the walk, so no module under ``lower/``
# names pydantic and ``tests/test_import_rule.py``'s exception set shrinks to nothing.
class_name = names.class_name
field_name = names.field_name


def schema_ref(document: str, pointer: str) -> SchemaRef:
    """The schema reference a class at ``pointer`` of ``document`` carries."""
    return SchemaRef(document, f"#{pointer}")


# **``escape_key`` and ``node_at`` are ``codegen/bundle.py``'s now.**  A JSON Pointer
# segment speller and its inverse are the SOURCE layer's, which is where
# ``docs/plan/architecture.md`` §11 puts them, and they sat here only because this
# module is the one every walk and both halves of the verifier already imported.
# That accident was the one import the VERIFIER made of the WALK, which §9 forbids
# outright, and §14 step 5 is the row that moves the pair: the move is correct only
# once ``bundle.py`` imports no lowering, which is what deleting the root selectors
# did.


# --------------------------------------------------------------------------- #
# the carriers
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Shape:
    """One class's own field set: each property key's schema node, and which keys
    are required.

    Written by :func:`declare_object` for every class the emitter declares, and
    carried to a lowering by :class:`Target`, so it is produced in ONE place and
    a second copy cannot disagree about what a class declares.

    Read by TWO of D2's rows, not one: the ``allOf`` row, and the union row for a
    branch whose root composes as well -- a subclass has to know what it inherits
    in order not to restate it.

    TRANSITIVE by construction: a class that itself composes records its inherited
    keys here too, so a subclass reads one map rather than walking a chain of base
    documents.

    ``decided`` is the FIELD each key came out as, beside the node it came from, and
    it exists for one shape the node alone cannot answer: a subclass restating a key
    with nothing but annotations keeps the base's TYPE, and that type cannot be
    re-decided from the base's node here.  Re-deciding it declares the nested classes
    again, in the subclass's module and **at a pointer the subclass's document does not
    have** -- measured, ``formats/canonical/image_carousel.json``'s merged ``slots``
    emits a second ``...SlotsItem`` stamped
    ``#/properties/slots/items``, where that document's own ``properties/slots`` carries
    only a ``default`` and a ``description`` and ``schema_at`` raises ``KeyError``.  So
    the field is REUSED rather than re-derived.

    **Where a re-used field's type is IMPORTABLE from is not here and is
    :attr:`Target.imports`'s.**  It was: ``declares``, the symbols the class's own module
    had declared by the time the class was, which a reuser subtracted the wanted symbols
    from and refused the remainder as a re-export.  That reading answered the wrong
    question -- a symbol the base merely imported is not unreachable, it is reachable
    from the module that DECLARES it -- and the question it answers belongs to a MODULE
    rather than to one class's field set, so it is asked and answered where the two
    document paths are known (``emit.resolve``).
    """

    properties: Mapping[str, dict]
    required: frozenset[str]
    #: ``key -> ir.Field``; see above.  Overlaid by :func:`declare_object` with the
    #: props it is handed, so every declaring row records it in one place.
    decided: Mapping[str, ir.Field] = field(default_factory=dict)
    #: The class's own ``description``, which is the description its NODE states.
    #: Written by :func:`declare_object` beside :attr:`decided`, for the reason that
    #: one exists: a subclass cannot read it off the base's node, because it does not
    #: have the base's node.  §6's description-authority rule clause 3 -- silence
    #: inherits -- read at a CLASS rather than at a field: a composing class whose own
    #: node states no description states the one its base does, because that is what
    #: the COMPOSED document states at the composing node's pointer and
    #: ``harness._composed`` folds it in there.  pydantic cannot be left to do it:
    #: ``cls.__doc__`` is ``None`` for a subclass with no docstring of its own, so the
    #: fact reaches ``model_json_schema()`` only if the emitter writes it.
    description: str | None = None
    #: The ``extra`` policy the class RESOLVED -- ``"forbid"``, ``"allow"`` or ``None``
    #: where the document gives it none.  Written by :func:`declare_object` beside
    #: :attr:`decided` and :attr:`description`, and carried for exactly their reason: a
    #: subclass cannot read it off the base's node, because it does not have the base's
    #: node.
    #:
    #: **§5's ``additionalProperties`` row, "a class DECLARES the ``extra`` the document
    #: gives it and never inherits it"** (decided 2026-10-29,
    #: ``adcp-client-python-10l.80``).  pydantic merges ``model_config`` along the MRO,
    #: so a class composing TWO bases takes whichever value the LATER one happens to
    #: carry -- and ``absent -> ignore`` on that base silently overrides an ``allow`` the
    #: document states.  Measured on
    #: ``content-standards/get-content-standards-response.json#/oneOf/0``: the union base
    #: resolves ``allow`` from the root's envelope conjunct, the composed target
    #: ``ContentStandards`` carries the model base's default ``ignore``, it arrives second
    #: in the bases tuple, and the branch class resolved ``ignore`` -- dropping keys the
    #: document admits, which §8 reported as ``missing /additionalProperties``.
    #:
    #: So this is read where §8's pairing fold puts the fact -- what the document states
    #: at the class's own pointer, which for a composing class is its own
    #: ``additionalProperties`` and, failing that, its bases' resolved value -- and
    #: WRITTEN on the class, so MRO order decides nothing a document states.  TRANSITIVE
    #: by construction like the other two: a class that composes records what it
    #: resolved, so a subclass reads one value rather than walking a chain.
    extra: str | None = None


def stated_extra(first: str | None, *rest: str | None) -> str | None:
    """The ``extra`` policy of a class composing views that each resolved one: the FIRST
    that states one, in the order the document states them.

    **Not a lattice over the values, and that was measured.**  A first cut made
    ``forbid`` win on §5's CONJ sentence ("``false`` on any conjunct closes the composed
    object"), which is draft-07's own conjunction and is the TIGHTER reading -- and §5's
    ``additionalProperties`` row does not send this to draft-07, it sends it to the fold:
    "the value is read from what the document states at the class's own pointer **after
    §8's pairing fold**".  ``harness._composed`` gap-fills -- a keyword only a conjunct
    states fills a gap and never overrides the node's own -- so the fold answers with the
    FIRST view that states one, and a lattice answers with something the grader does not
    read.  Measured on ``media-buy/decline-proposals-response.json#/anyOf/1``: the root
    states ``additionalProperties: false`` and the branch's ``$ref`` target states
    ``true``, the fold yields ``true``, and the lattice resolved ``forbid`` -- a model
    REFUSING keys the document admits, which is the one direction §2 forbids outright.

    So this is :attr:`Shape.description`'s own rule at the same seam and for the same
    reason, which is why that attribute's docstring already says it: "the description the
    FIRST base that states one states ... because that is what ``harness._composed``
    gap-fills on the document side -- ``if kw not in out`` over the conjuncts in order --
    and the two halves have to read one composed document the same way."  One rule, two
    keywords, one reading of the composed document.
    """
    for value in (first, *rest):
        if value is not None:
            return value
    return None


class Importable(NamedTuple):
    """Where ONE symbol is importable from, for the module that is about to name it.

    ``module`` is the spelling that module writes, which D1 derives from the two
    document paths and ``emit.relative_module`` is the one derivation of.  ``document``
    is the bundle document whose module DECLARES the symbol, and it is here because the
    spelling alone cannot be handed on: a third module composing the second needs the
    symbol's own declarer, and re-deriving a spelling from a spelling is a second copy of
    D1.  Carrying the document means every module in a chain imports from the SAME place,
    which is §1's "one import path per class, and never a second way to reach the same
    class" read across more than two modules.
    """

    module: str
    document: str


class TargetKind(StrEnum):
    """What a resolved ``$ref``'s target IS, which is the one question every row that
    wants it as a BASE asks of it.

    Three kinds, because §4 "What becomes what" gives a document root three outcomes and
    a base decision answers differently for each:

    * :attr:`ANNOTATION` -- a scalar root, an enumeration or a container.  Not a class at
      all: D2 makes it an ``Annotated`` alias and subclassing one is a ``TypeError`` at
      import, so every row refuses it as a base.
    * :attr:`CLASS` -- a class declaring a flat field set, which is what a base supplies
      and what :class:`Shape` carries.
    * :attr:`UNION` -- a class too (``BranchDispatchMixin`` plus the model base), but one
      whose INSTANCE is one of its branches.  §5's ``$ref`` row at CONJ keeps it out of a
      reuser's bases -- "it is not a class a model can extend: the target is this node's
      own TYPE" -- while §4's union row makes it the first base of a ``$ref`` BRANCH, "the
      target, which supplies the fields".  Two positions, two answers, one fact.

    **It is a FIELD of :class:`Target` and not a reading of whether ``shape`` is
    ``None``.**  A union root has a :class:`Shape` -- ``declare_object`` records one for
    every class -- so "has no shape" and "is not a class" are different questions, and the
    gate that conflated them refused ``core/assets/asset-union.json``'s ``$ref`` branch
    onto ``VASTAsset`` with a sentence about a scalar alias (``adcp-client-python-10l.55``).
    """

    ANNOTATION = "annotation"
    CLASS = "class"
    UNION = "union"


def target_kind(declared: "ir.Declaration | None") -> TargetKind:
    """Which of :class:`TargetKind`'s three a node's DECLARATION makes it.

    THE ONE DERIVATION, read by the two sites that have a declaration to read it off:
    ``emit.answer``, which builds the :class:`Target` for a cross-document reference, and
    ``lower.union._inherited``, whose LOCAL arm resolves a ``#/...`` branch against the
    declarations this module has already made.  Asked of the declaration rather than of
    the node, because what a node BECAME is the walk's answer and re-deriving it from the
    schema would be a second one.

    ``ir.ClassDecl.branches`` is the fact that says the instance is one of the branches --
    the same field ``render`` writes ``_branch_models`` off -- so a union root is told
    apart from a flat class by what its own declaration carries and never by a flag beside
    it.  Anything that is not a class declaration at all is an annotation: an alias, an
    enumeration, a container, or a pointer this module declared nothing at.
    """
    if not isinstance(declared, ir.ClassDecl):
        return TargetKind.ANNOTATION
    return TargetKind.UNION if declared.branches is not None else TargetKind.CLASS


@dataclass(frozen=True)
class Target:
    """What a resolved ``$ref`` gives the lowering that asked for it.

    ``module`` and ``symbol`` are what an ANNOTATION needs.  ``kind`` is what every row
    that wants the target as a BASE reads, and :class:`TargetKind` carries the reasoning:
    a row asks which of §4's three outcomes the target's root is, and it asks a FIELD
    rather than inferring it from ``shape``.

    ``shape`` is the field set the target's class DECLARES, and it is ``None`` exactly
    where ``kind`` is :attr:`TargetKind.ANNOTATION`: an alias declares no fields.  A union
    root carries one like any other class -- §4's "a branch composes its own with them"
    needs it -- and which positions may stand on it is ``kind``'s question and not this
    field's.

    ``document`` is the bundle path ``module`` was derived from, so a lowering that
    records the import also records WHO declares the symbol (:class:`Importable`).
    """

    module: str
    symbol: str
    shape: Shape | None = None
    document: str = ""
    #: KEYWORD-ONLY AND WITH NO DEFAULT, which is deliberate: a default would make every
    #: construction site that forgot it one of §4's three outcomes by accident, and the
    #: whole of this field is that the answer is STATED rather than inferred.  Measured --
    #: with ``ANNOTATION`` as the default, ``tests/test_emit_product.py``'s hand-built
    #: target for a class was read as an annotation and the restatement row never ran.
    kind: TargetKind = field(kw_only=True)
    #: **Every symbol the target's module can hand this one, and where each is
    #: importable FROM**: the symbols that module declares, mapped to the target itself,
    #: and the symbols it imported, mapped to the documents that declare THOSE.  §1 gives
    #: a class one import path, so a reuser of an inherited field takes each symbol the
    #: field's type names from its declarer and never from the base as a re-export --
    #: which is the same rule ``emit.resolve`` applies to a fragment ``$ref``, written
    #: once and read by :func:`_reused`.
    #:
    #: Built by ``emit.resolve``, because the spelling is a function of the two DOCUMENT
    #: paths (D1) and the walk knows neither: a lowering reads this table and derives no
    #: import.  Empty for a document lowered outside a run, which refuses by name rather
    #: than inventing one.
    imports: Mapping[str, Importable] = field(default_factory=dict)
    #: **§4 "Names"'s three branch facts, where this target is itself a BRANCH of a union
    #: root**, and ``None`` where it is not.  Carried rather than re-read: the declaring
    #: module read them off the branch's own declaration when it recorded the branch's
    #: hop (``lower.names.Branch``), and the one row that distributes over a union
    #: target's branches declares a class per branch in ANOTHER module -- so it has to
    #: name each one, and the branch's declaration is not its to read.  The FACTS cross
    #: and not the mapping, which is the same cut ``lower.names.Branch`` already states.
    naming: names.Branch | None = None
    #: **Every branch of a UNION target, with the two facts its base carries about them**
    #: (:class:`TargetBranches`), and ``None`` for every other kind.  Read by §5's
    #: ``$ref`` row at CONJ where the node declares fields of its own: the conjunction
    #: distributes, and distributing needs each branch's symbol, its :class:`Shape` and
    #: its name.  Built from :attr:`codegen.ir.ClassDecl.branches`, which already carries
    #: the branch POINTERS on the declaring side -- so nothing of the IR is widened and
    #: what is new is only that the fact crosses the module boundary.
    branches: TargetBranches | None = None
    #: **The ``description`` a CHAIN HOP carried, and ``None`` where the reference
    #: reached its declarer in one hop.**  §5's ``$ref`` row resolves a fragment whose
    #: node is itself a ``$ref`` to the module that DECLARES the symbol
    #: (``emit._declaring_site``), and the node it passed THROUGH may state a
    #: ``description`` sibling -- which the same row gives the other answer, "the
    #: sibling's description wins".  ``bundle.record`` inlines exactly that text at the
    #: referring pointer, so a chain that dropped it would make the model *missing* a
    #: fact at a pointer the comparison reaches.  The FIRST sibling along the chain, for
    #: the record's own precedence: the referrer's own wins over this, and this over the
    #: declarer's.
    described: str | None = None

    # **The target's own NODE is not here and is ``Module.referenced``'s now.**  §2's
    # intersection rule asked of two declarations that are each a bare ``$ref`` is the
    # one reader that needs the target's schema rather than its symbol, and it holds a
    # DECLARATION and not a node -- so it has no pointer to ask a site with, and the
    # run keys that one answer by the URI alone (:func:`Module.resolve_node`).

    @property
    def declares(self) -> Shape:
        """The field set this target's class declares, for a row standing it as a BASE.

        Asked only PAST A GATE ON :attr:`kind`: every reader refuses
        :attr:`TargetKind.ANNOTATION` first, and the two class kinds are exactly the nodes
        :func:`declare_object` recorded a :class:`Shape` for -- it writes the shape and the
        declaration together, at one pointer, and both halves of this pair are read off
        those two records in one place (``emit.answer`` across a module boundary,
        :func:`local_target` inside one).

        A kind that says CLASS with no shape beside it is therefore those two records
        disagreeing, which is a defect in this compiler and not in any document -- so it
        raises §2's one exception, which no layer catches, rather than returning a field
        set nobody declared or a refusal charged to a document.
        """
        if self.shape is None:
            raise BuildFailure(
                f"{self.symbol!r} is a {self.kind} with no Shape recorded beside it: "
                "declare_object writes a class's shape and its declaration at one "
                "pointer, so the two records disagree"
            )
        return self.shape

    @property
    def where(self) -> Importable:
        """Where :attr:`symbol` itself is importable from.

        The target's own symbol is one its document DECLARES -- ``emit.resolve`` reads it
        off the target module's symbol table and refuses a fragment whose node carries
        none -- so the declarer is the target, and this is the pair every site recording
        the import hands :meth:`Module.importing`.
        """
        return Importable(self.module, self.document)

    @property
    def crosses_a_module(self) -> bool:
        """Whether reaching :attr:`symbol` from the module being written crosses a MODULE
        BOUNDARY, which is the one question every import screen on a base asks.

        Read off :attr:`module`, which :func:`local_target` leaves EMPTY and for the reason
        this property states: a local ``#/...`` reference resolves inside the document being
        written, so the symbol is one THIS module declares and there is no module to import
        it from.  Stated once, here, because the two carriers a base arrives in answer it
        differently and both answers are the same fact: §4's union base arrives with no
        :class:`Target` at all, and a local-pointer conjunct base arrives with one whose
        module is empty.  :func:`_reused` is the reader.
        """
        return bool(self.module)


@dataclass(frozen=True)
class TargetBranches:
    """A UNION target's BRANCHES, as the one row that distributes over them reads them.

    §5's ``$ref`` row at CONJ: "A UNION root beside a node that DOES declare fields
    distributes: conjunction distributes over disjunction, so ``(A | B) and C`` is
    ``(A and C) | (B and C)``, and the node is a union whose branches each take one of the
    target's branches as a base and add the node's own fields."  So the composing node
    declares one class per branch, and each one needs the branch's SYMBOL, its
    :class:`Shape` and §4's naming facts -- which is a :class:`Target` per branch, the
    same carrier a ``$ref`` BRANCH of a root union already stands on.

    ``combinator`` and ``discriminator`` are the two facts the target's own BASE carries
    about its branches (:attr:`codegen.ir.ClassDecl.combinator`,
    :attr:`codegen.ir.ClassDecl.discriminator`), and they cross for the reason the branch
    list does: the target DERIVED them -- §4's dispatch derivation over its own branches
    -- and the distributed union is over those same branches pinning those same consts, so
    re-deriving either here would be a second answer to a question already answered.
    """

    combinator: str
    discriminator: str
    #: One per branch, in the target's own branch order, which is the order
    #: :attr:`codegen.ir.ClassDecl.branches` records and the order the document lists.
    of: tuple[Target, ...]
    #: The INDICES in :attr:`of` whose intersection with what the composing node asserts
    #: is provably empty, and which §5's distribution clause therefore DROPS.
    #:
    #: Recorded as a set of indices rather than by filtering :attr:`of`, and the reason
    #: is the POINTER: a branch class sits at ``<conjunct>/<combinator>/<index>``
    #: (:func:`_distributed_pointer`), which is the target's own branch position in the
    #: document of record -- so a dropped branch must not renumber the ones after it, or
    #: §8 would pair every surviving class against the wrong branch node.  Keeping the
    #: list whole and the drop beside it makes that impossible to get wrong, and it keeps
    #: the drop READABLE: a refusal and a report can say which branches went and why.
    dropped: frozenset[int] = frozenset()

    @property
    def live(self) -> tuple[tuple[int, Target], ...]:
        """The surviving branches, each with its index in the target's own list."""
        return tuple((i, b) for i, b in enumerate(self.of) if i not in self.dropped)


def branches_of(
    declared: "ir.Declaration | None", at: Callable[[str], Target]
) -> TargetBranches | None:
    """The branches of a UNION declaration, as :class:`Target`\\ s, or ``None``.

    **THE ONE DERIVATION, and it reads the IR rather than widening it.**  Rows ``.34``,
    ``.55`` and ``.59`` each expected to widen :class:`codegen.ir.ClassDecl` and each found
    it already served; this one does too.  ``ClassDecl.branches`` is §7's fourth
    union-base slot -- the base's branches as ``TypeRef``\\ s, each naming a branch by
    POINTER until ``lower/names.py`` binds it -- so the declaring module already holds
    WHICH pointers its branches sit at, and what was missing is only that the fact cross
    the module boundary.  ``at`` is the caller's reading of one pointer as a
    :class:`Target`, which is the same expression it builds the root's own answer with:
    ``emit.answer`` for a cross-document reference and :func:`local_target` for a local
    one, so a branch and a root are one construction and cannot come to disagree.

    It TERMINATES on any declaration: a branch of a root union is a class and not a union
    root (:attr:`codegen.ir.ClassDecl.branches` is ``None`` on it), so the recursion
    through ``at`` is one level deep by construction and a second level would be a target
    whose branch is itself a union base, which :func:`declare_object` writes for no node.
    """
    if not isinstance(declared, ir.ClassDecl) or declared.branches is None:
        return None
    return TargetBranches(
        declared.combinator or "",
        declared.discriminator or "",
        tuple(at(branch.path) for branch in declared.branches),
    )


@dataclass(frozen=True)
class Decided:
    """What the walk decided one schema node IS.

    ``format`` is set only when ``type`` does NOT already carry the format -- the
    compiler then states it as an annotation rather than as a type.  Keeping the
    two separate here is what makes the drop impossible to make by accident: a
    format is either in the type or in this field, and never nowhere.
    """

    type: ir.TypeRef
    constraints: dict[str, Any] = field(default_factory=dict)
    format: str | None = None


#: What a reference site answers when the run resolved none: a document lowered on its
#: own resolves no reference.  A SENTENCE and not a refusal, because the site's own
#: pointer is what a refusal has to name and only the asking node holds it -- so the
#: reading is :func:`unresolved`, below, and this is the text it carries.
NO_TARGET = (
    "the run resolved no target for this reference, so there is no module to import a "
    "symbol from: a reference is an IMPORT of the target's symbol (section 2's rule), "
    "and a document lowered outside a run has no other document to import from"
)


def unresolved(uri: str, pointer: str) -> Refusal:
    """The answer at a reference site the run supplied no target for.

    ``emit`` builds :attr:`Module.targets` from ``bundle.edges`` -- the same descent the
    parser reads the reference off -- so every site the walk reaches has an entry, and a
    site with none is a document lowered outside a run.  That is the shape the refusing
    default binder had, and it is a refusal by name rather than an invented import, so
    there is no path on which a reference is silently dropped.
    """
    return Refusal("$ref", pointer, f"{NO_TARGET} -- {uri}", kind=Kind.VERDICT)


def local_target(mod: "Module", pointer: str) -> Target:
    """The node at ``pointer`` of THIS module, as the :class:`Target` a row reads.

    A LOCAL ``#/...`` reference resolves inside the document being written, so there is no
    module to import from and no symbol table to bind against: ``module`` is empty and
    ``symbol`` is the POINTER that ``lower/names.py`` binds a name to (§7), which is what
    :func:`local_reference` already decides a local reference to.

    What a row wanting the target as a BASE needs is the other two fields, and both come
    off the two records :func:`declare_object` writes together -- the declaration
    (:attr:`Module.at`) and the shape (:attr:`Module.shapes`), at one pointer.  So the
    LOCAL arm and the cross-document arm of a base decision read one carrier and one
    invariant: ``emit.answer`` builds the other instance off the same pair of records, and
    :attr:`Target.declares` states the invariant once rather than once per arm.

    **A THIRD record joins the pair for a UNION target** -- :attr:`Module.hops`, which is
    where §4's three branch-naming facts were recorded when the branch was declared -- and
    it is read through the same key: a class's declaration, its shape and the hop its name
    is derived through are all written at one pointer.  :func:`branches_of` is the one
    reading of which pointers a union's branches sit at, and this arm hands it the same
    construction it is itself, so a local union target and a cross-document one give the
    distributing row one answer.
    """
    hop = mod.hops.get(pointer)
    return Target(
        "",
        pointer,
        mod.shapes.get(pointer),
        mod.document,
        kind=target_kind(mod.at.get(pointer)),
        naming=hop if isinstance(hop, names.Branch) else None,
        branches=branches_of(mod.at.get(pointer), lambda p: local_target(mod, p)),
    )


def decide(
    raw: Any,
    pointer: str,
    mod: "Module",
    position: Position,
    *,
    objectish: bool = False,
    of_a_root_union: bool = False,
) -> Decided | Refusal:
    """PARSE one raw subschema at a position, then dispatch on the kind the parser decided.

    **ONE caller is left and it is the one re-entry §5 names**: :func:`local_reference`,
    for a ``definitions`` / ``$defs`` entry at DEF.  §5 of the semantics document makes
    that section "nothing by itself: a bag of named subschemas.  Each entry is declared on
    demand when a ``$ref`` names it", and "an entry nothing references is not declared"
    means the parser does not descend one -- so an entry is parsed when a reference asks
    for it, which is a re-entry at a position and not a second traversal of one mapping.

    Every other caller was a descent §14 step 5 staged, and all of them are gone with the
    carrier: a handler takes its children off node fields.

    ``position`` is the node's own, passed by the caller because it is a structural fact
    of the caller -- a ``definitions`` entry is at DEF -- and never recovered from the
    pointer string, which cannot tell a RULE reference from a PROP one.

    ``objectish`` is §6's "a child never reconstructs its parent": a branch of a ROOT
    union is a class whatever it states, because §4 of the semantics document emits one
    class per branch, and the UNION is what knows that about itself and tells the branch.
    It is the parser's descent now (:attr:`nodes.Union.branches`) and survives here for
    the signature, which a DEF entry does not use.
    """
    return lower_node(
        schema.parse(
            raw, pointer=pointer, position=position, source=mod.source, objectish=objectish
        ),
        mod,
        of_a_root_union=of_a_root_union,
    )


def lower_node(
    node: nodes.Node, mod: "Module", *, of_a_root_union: bool = False
) -> Decided | Refusal:
    """What one PARSED node is: ``emit.decide_type``, reached by name.

    ``of_a_root_union`` is the one fact §6 names as travelling DOWN the tree: "where a
    lowering needs to know something about the node ENCLOSING it, the enclosing handler
    passes it down -- a child never reconstructs its parent."  The union handler reads
    ``node.position`` and tells its branches, because "of a root union" is a statement
    about the UNION and not about the branch; ``lower.enum.resolves_no_name`` is the
    predicate that needs it, and it read ``pointer.split("/")`` before this.
    """
    from codegen.emit import decide_type

    return decide_type(node, mod, of_a_root_union=of_a_root_union)


@dataclass
class Module:
    document: str
    #: The symbol the document's ROOT binds, which is D3's parent for a name derived
    #: inside the module: :func:`local_reference` qualifies an entry's own key with it,
    #: the way :func:`fields` qualifies a property's.  ``emit.lower_document`` sets it
    #: from the title before the row runs.  Empty by default, so a document lowered
    #: outside it derives a bare, unqualified name rather than one naming a root that
    #: is not there -- the same shape as ``asserted`` and ``named`` being empty.
    root: str = ""
    #: **§5's ``targets``: every document this one references, already lowered by the
    #: run in dependency order, so a cross-document reference is a LOOKUP and never a
    #: callback.**  This was ``bind``, the last CALLABLE carried here -- a closure over
    #: the run's lowered/refused/in-flight documents and over ``emit.lower``'s own
    #: recursion -- and §14 step 7 is what retires it: ``emit`` computes the reference
    #: closure and the dependency order up front, so a target is finished before the
    #: document referencing it is parsed and the answer is data.
    #:
    #: **Keyed by the reference SITE, ``(uri, pointer)``, and not by the target
    #: document**, which is §5's table read for its content rather than for its key.
    #: Two things follow and both are the reason: no lowering reads a ``#`` or a bundle
    #: path, so ``bundle.split_ref`` and ``document_for`` stay in the source layer where
    #: §11 puts them; and the refusal a site earns -- a URI naming no document of this
    #: bundle, a target that refused, a fragment the target declares no symbol at --
    #: names THAT SITE's pointer, which only the site identifies.  The sites are
    #: ``bundle.edges``, the same descent the parser reads the reference off, so a site
    #: the walk reaches and this map has no entry for is a document lowered outside a
    #: run (:func:`unresolved`).
    targets: Mapping[tuple[str, str], Target | Refusal] = field(default_factory=dict)
    #: **The sites this document's BASES spell, resolved for this document and keyed by
    #: the URI alone** -- the other half of what :attr:`referenced` is here for.
    #:
    #: §2's intersection rule reads a BASE's declaration beside this document's own
    #: (:func:`_intersection`), so every key the base alone declares reaches the composed
    #: node -- and a key the base declares as a ``$ref`` carries a reference this
    #: document's own text does not spell.  The site is real: draft-07 applies both
    #: conjuncts to the same instance, so the composed class holds that property and
    #: must IMPORT its type rather than copy it (P2).  It has no pointer either map can
    #: be keyed by, because the pointer it arrives at is this document's -- derived from
    #: the restating conjunct -- and belongs to no edge of either document.
    #:
    #: Read only where :attr:`targets` has no entry for the site, so a reference the
    #: document spells itself is answered by its own site and this map cannot shadow one.
    inherited_targets: Mapping[str, Target | Refusal] = field(default_factory=dict)
    #: **The reference sites this document's walk ASKED about**, written by
    #: :meth:`target` and read by the run.  It is what decides which documents the run
    #: WRITES, and §10's own sentence is the reason: "a module cannot import from a
    #: module no run wrote", so the documents a run owes are the ones some module it
    #: attempted actually referenced.
    #:
    #: The closure and the dependency order range over a STATIC reading
    #: (``bundle.lowered_references``), which is what lets a target be a finished module
    #: before its referrer is parsed -- and that reading is an over-approximation of what
    #: the walk reaches, because a document that refuses stops before its later sites.
    #: Measured on the suite's population of 991: taking the order's visit set as the
    #: output writes 11 modules nothing imports and nobody named.  A set rather than a
    #: count, because the fixed point the run takes is over the TARGETS.
    asked: set[tuple[str, str]] = field(default_factory=set)
    #: ``$ref`` URI -> the NODE it names, for the one reader that needs the target's
    #: schema rather than its symbol: §2's intersection rule asked of two declarations
    #: that are each a bare ``$ref`` (:func:`Module.resolve_node`).  Keyed by the URI
    #: alone, because that reader holds a declaration and not a node and so has no
    #: pointer to ask with.
    #:
    #: **It held document ROOTS and holds NODES** (``adcp-client-python-10l.72``).  Two
    #: spellings reach one beside the root: a FRAGMENT URI, which names a node of
    #: another document, and a pointer LOCAL TO A BASE'S OWN DOCUMENT, which names a node
    #: of a document this one composes.  The run resolves both (``emit.referenced`` and
    #: ``emit.based_nodes``) and the rule reads one map, because whether one declaration
    #: narrows another is a fact about the two TARGETS and a reference this could not
    #: read was a declaration the rule had to refuse.
    referenced: Mapping[str, dict] = field(default_factory=dict)
    #: The formats this document's own draft asserts; see ``emit.asserted_formats``.
    #: Empty by default, so a node lowered outside ``lower_document`` selects no
    #: format-derived type rather than one nothing checks.
    asserted: frozenset[str] = frozenset()
    #: The pointers of THIS document's nodes that a ``$ref`` NAMES -- from elsewhere in
    #: the bundle, or from this very document; see ``bundle.named_nodes``.  Empty by
    #: default, so a document lowered outside ``lower_document`` names no node for a
    #: referrer that is not there -- the same reason ``asserted`` is empty by default.
    named: frozenset[str] = frozenset()
    #: The SUBSCHEMA at each of those pointers, for the ones a LOCAL reference reaches:
    #: ``pointer -> node``.  A local reference resolves against the REFERRING document,
    #: so the node it names is in this file and :func:`local_reference` needs it without a
    #: binder and without a second reading of the document.  Keyed by the pointer
    #: ``bundle.nodes`` yields, which is the same walk ``bundle.named_nodes`` read the
    #: reference off, so there is no second pointer navigator and no second escaping
    #: rule for a ``~0``/``~1`` in a key.  Empty by default: a document lowered outside
    #: ``lower_document`` resolves no local reference rather than inventing a symbol.
    local: Mapping[str, dict] = field(default_factory=dict)
    #: **The ``default`` a LOCAL ``$ref``'s TARGET states, keyed by the REFERRING node's
    #: pointer.**  Draft-07 replaces a ``$ref`` node with its target, so the target's
    #: ``default`` IS the referring node's -- and §5's ``default`` row then says "PROP ->
    #: the field's default".  :func:`local_reference` is the one writer, because it is the
    #: one place the resolution happens, and :func:`fields` is the one reader; the field
    #: rendered ``default: None`` where the document says ``"linear"`` until this carrier
    #: existed, which is a *differs* and §8 pins that at zero
    #: (``adcp-client-python-10l.26``, measured at ``core/daast-tracker-constraints.json``
    #: and ``core/vast-tracker-constraints.json``).
    #:
    #: Keyed by the REFERRER and not by the target, because one target may be named from
    #: two properties and the fact belongs to each field that resolves it.  A ``default``
    #: is a VALUE and not a constraint (§2: "it neither widens nor narrows what the class
    #: accepts"), so this cannot be declared as an approximation and has to be carried.
    referred: dict[str, Any] = field(default_factory=dict)
    #: **The ``description`` a CHAINED remote ``$ref`` carried, keyed by the REFERRING
    #: node's pointer** -- :attr:`referred`'s sibling, written by ``lower.references``
    #: and read by :func:`fields`, with the node's OWN sibling winning where it states
    #: one.  §5's ``$ref`` row resolves a fragment whose node is itself a ``$ref`` to the
    #: module that declares the symbol, and the node passed THROUGH may state a
    #: ``description`` sibling the same row makes authoritative; ``bundle.record``
    #: inlines that text at the referring pointer, so dropping it is a *missing* fact at
    #: a pointer the comparison reaches.
    #:
    #: A second map rather than a wider :attr:`referred`, because the two carry different
    #: facts from different resolutions -- a ``default`` from a LOCAL target, a
    #: ``description`` from a REMOTE chain -- and one map holding both would need a reader
    #: to know which resolution put each key there.
    described: dict[str, str] = field(default_factory=dict)

    #: The pointers of this document's nodes an ENCLOSING node already constrains to
    #: ``type: "object"``; see ``bundle.constrained_to_object``.  A fact about the
    #: DOCUMENT, computed once per document rather than re-derived per node, which is
    #: the same arrangement as ``named`` and for the same reason: a lowering reads a
    #: set and no two readings of the enclosing structure can disagree.
    #:
    #: Empty by default, which refuses rather than admits -- a node lowered outside
    #: ``lower_document`` states its own ``type`` or is refused, which is exactly what
    #: :func:`lower_object` did before this set existed.
    object_constrained: frozenset[str] = frozenset()
    #: **What the MODEL LAYER carries**, so a property key spelling one of pydantic's
    #: own attributes is carried under an alias rather than shadowing it
    #: (``lower.names.field_name``).  DERIVED in ``codegen/render.py`` (``RESERVED``) and
    #: handed in by the run, because §8 makes that the one module allowed to read the
    #: model layer and §14 step 7 moved §4's name rules into ``lower/``, which the same
    #: section bans ``pydantic`` from.  Empty by default, which spells a key under its
    #: own name unless Python's own keyword list refuses it.
    reserved: frozenset[str] = frozenset()
    imports: set[tuple[str, str]] = field(default_factory=set)  # (module, name)
    #: **Symbol -> the bundle DOCUMENT that declares it**, for every symbol this
    #: module imported from another one.  The other half of :attr:`imports`, which holds
    #: the SPELLING: a spelling is relative to this document and says nothing to a third
    #: module, and the declarer is what §1's one-import-path rule is about.  Written by
    #: :meth:`importing` and by no other path, so a symbol in one map and not the other
    #: is unrepresentable; read by ``emit.resolve``, which turns it into the
    #: :class:`Importable` table a module composing this one is handed.
    imported: dict[str, str] = field(default_factory=dict)
    #: **Every declaration this module holds, in DECLARATION ORDER**
    #: (``docs/plan/architecture.md`` §7).  This was a list of rendered text BLOCKS, and
    #: a module accumulating text beside its decision memo is the two-layers-one-object
    #: shape §7 replaces: the renderer is the only reader of the model layer now, and a
    #: change of rendering touches ``codegen.render`` alone.
    #:
    #: :meth:`declare` appends and records the symbol; a declaration that binds NO name
    #: -- :class:`codegen.ir.UnionInstall`, whose two statements are about symbols the
    #: module already declares -- is appended here directly.
    declarations: list[ir.Declaration] = field(default_factory=list)
    #: JSON Pointer -> its :class:`Shape`, for a class declared in THIS module.
    #: Keyed by POINTER and not by class name, because a name is not computed until
    #: ``lower/names.py`` runs (§7).
    shapes: dict[str, Shape] = field(default_factory=dict)
    #: JSON Pointer -> the declaration made for the node at it.  Written by
    #: :meth:`declare`, which EVERY declaration passes through, so a fragment reference
    #: reads one map rather than a second record something could forget to write.  It is
    #: also :func:`local_reference`'s MEMO, which is why that function needs no record of
    #: its own: a node declared because the walk reached it and a node declared because a
    #: local reference asked for it are one entry here.
    #:
    #: **It held the SYMBOL and now holds the declaration**, because the walk computes no
    #: symbol: ``lower/names.py`` turns this map's keys into §7's symbol table in one pass
    #: over the finished module, and until then the IR's own name slots hold pointers.
    at: dict[str, ir.Declaration] = field(default_factory=dict)
    #: JSON Pointer -> the HOP §4's nested rule derives this node's name through:
    #: ``<Parent><Property>`` at PROP, ``<Parent>Item`` at ELEM, ``<Parent>Value`` at
    #: MAPV, ``<Root><Key>`` at DEF, §4 "Names"'s three rules at BRANCH.  **The hop is
    #: what the walk records INSTEAD of a name** (§7): a handler states the structural
    #: fact -- which node this one hangs off, and through which keyword -- and
    #: ``lower/names.py`` folds the hops to the root.  A child the parser builds at its
    #: PARENT's own pointer (a ``type``-list member, an extras store) records none and
    #: inherits the entry already there, which is what keeps one name per pointer.
    hops: dict[str, names.Hop] = field(default_factory=dict)
    #: D3's content dedup: ``(the node, the symbol declared for the FIRST node equal to
    #: it)``, in the order the walk declared them.  Two nodes with identical content are
    #: ONE node, so the second occurrence decides to the symbol the first declared rather
    #: than declaring a second class for it.  Written and read by ``emit.decide_type``,
    #: which is the one per-node walk.
    #:
    #: **The equality is §4's own**, and that is what §14 step 5 deletes
    #: ``emit.content_key`` for: "two nodes are equal exactly when they state the same
    #: thing about an instance -- which is §4's content dedup read off the type system
    #: rather than off a JSON serialisation with a position bit appended".  So the memo is
    #: a SEQUENCE and not a mapping: a node carries mappings and is not hashable, and the
    #: alternative is a second spelling of what identical means, which is §9's own open
    #: question about two instruments disagreeing about identity.  §14 step 7 is where the
    #: memo becomes a pass over the finished module (``lower/names.py``) and the linear
    #: scan goes with it; it is per MODULE, so the sequence is tens of entries long.
    #:
    #: **A ``$ref`` is compared as a STRING and never followed, which is the CUT** §9 says
    #: the comparison has to state: :class:`codegen.schema.nodes.Reference` carries the
    #: URI and its two halves and no target, so a cycle through a reference is cut at the
    #: reference, at depth 0, on every node and not only on a cyclic one.  The cost is a
    #: measured population: two nodes naming ONE target through two spellings of the same
    #: reference are not equal, and the bundle has 17 such targets -- 968 distinct
    #: reference strings over 4,200 sites, 0 of them relative, 17 ``(document, pointer)``
    #: pairs reached both by a local ``#/definitions/x`` and by the document's own
    #: absolute URI carrying the same fragment.  Not collapsing them is the conservative
    #: direction: two classes where one would do, never one class where the document
    #: means two.
    #:
    #: Per MODULE, which is per document (D1).  Two documents that inline identical
    #: content keep a class each: collapsing them would need a rule for which module owns
    #: the survivor, D1 gives a node exactly one home, and 0 of the bundle's 1,271
    #: identical-content groups have a ROOT carrying that content for a ``$ref`` to reach.
    collapsed: list[tuple["nodes.Base", str]] = field(default_factory=list)
    #: The other half of that record, and the half a check can read: ``pointer -> the
    #: symbol the node at it ADOPTED`` because an earlier node of identical content had
    #: already declared one.  ``collapsed`` is keyed by content, which says what was
    #: collapsed and not WHERE, and "where" is the only thing a grader can compare a
    #: node against -- so the dedup is graded by asking, of every adoption, whether the
    #: adopting pointer's content really equals the declaring pointer's.  Written by
    #: ``emit.decide_type`` on the same line that returns the adopted type, so an
    #: adoption that went unrecorded is an adoption that did not happen.  It held the
    #: SYMBOL and holds the DECLARING POINTER, which is §7's own spelling of the table
    #: ("the adoption table pointer -> declaring pointer") and what lets the naming pass
    #: decide both names.
    adopted: dict[str, str] = field(default_factory=dict)
    #: The pointers :func:`local_reference` is in the middle of declaring, innermost last.
    #: A pointer meeting itself here is a local reference CYCLE, which refuses by name
    #: rather than recurring -- the same shape, and the same reason, as ``emit.emit``'s
    #: ``inflight`` list for a cross-document cycle.
    resolving: list[str] = field(default_factory=list)

    #: D5's rung 3: ``alias symbol -> (the document's type word, its constraints)``
    #: for every constrained scalar this module resolved to a name in
    #: ``adcp.types.constraints``.  Recorded on the module the walk met it in, and
    #: the RUN unions them -- the alias module is one module for the whole run, and
    #: a per-document record is the only place the walk can write one without the
    #: decider taking run-level state.  The IMPORT needs nothing from here: a
    #: dotted path on :class:`Type` produces it through the field, like
    #: ``pydantic.AwareDatetime``.
    aliases: dict[str, tuple[str, dict[str, Any], str | None]] = field(default_factory=dict)
    #: Section 5's ``default`` row: ``pointer -> the value DROPPED`` at it, for a
    #: default on a REQUIRED property.  The row is "dropped and REPORTED", and this is
    #: the report: the drop happens inside the walk, where nothing is printed, so the
    #: fact rides out on the module the way :attr:`aliases` and :attr:`adopted` do and
    #: ``emit.emit`` collects it per document for the CLI and for the suite.  A list
    #: and not a count, because the pointer is what makes it auditable: a reader can
    #: go to the node and see the default the model does not carry.
    drops: dict[str, Any] = field(default_factory=dict)

    #: What this document STATES and the class carries nothing for, one line each, as
    #: ``"<pointer>: <name>: <why>"``.  The channel section 7's ``errorMessage`` row
    #: needs: a name draft-07 does not define asserts nothing about an instance, so
    #: dropping it cannot widen the class and the document still emits -- which makes it
    #: neither a refusal nor nothing.  A refusal would lose the document for a name that
    #: constrains no instance; silence is how a reader comes to believe the class
    #: carries it.  ``emit`` collects these per document and the CLI prints them.
    #:
    #: **Separate from :attr:`drops`, which is one keyword's own rule.**  ``drops``
    #: carries section 5's ``default``-on-a-required-property, keyed by pointer and
    #: holding the value; this carries any name the walk admits and renders nothing for.
    #: The two were one attribute for the length of one merge -- this row and the
    #: ``default`` row each added a ``Module.drops``, with different types -- and a
    #: dataclass takes the second declaration silently, so the earlier writer's
    #: ``mod.drops[pointer] = value`` met a list.  One name per channel.
    carries_nothing: list[str] = field(default_factory=list)

    #: **Section 2's approximations, accumulated in DOCUMENT ORDER.**  Every fact this
    #: document's annotations do not carry, as :class:`adcp.types._base.Approximation`
    #: values minted by :func:`codegen.lower.approximate.approximate` -- the one producer.
    #:
    #: ``docs/plan/architecture.md`` §2: "a refusal was an ABSORBING element -- anything
    #: composed with one was that one, which is how a child's refusal killed a document --
    #: and an approximation is an ADDITIVE one: composition is total, the parent always
    #: gets a ``Lowering``, and what travels upward is accumulated rather than
    #: propagated."  On this tree the accumulator is the module rather than a ``Lowering``
    #: value, so "accumulated" is an append here and the order is the one §6 names: "the
    #: parser built each node's children in document order, and concatenation preserves
    #: it."
    #:
    #: **A THIRD channel beside :attr:`drops` and :attr:`carries_nothing`, and §10 says
    #: why it may not be either of them**: "An approximation is NOT one of them: a
    #: carries-nothing line says a keyword constrained nothing, and an approximation says
    #: a keyword constrained something the annotation does not carry.  Printing them in
    #: one list would sum two different things."  It is also the only one of the three the
    #: GRADER reads, which is why it rides into the emitted module (§7) where the other
    #: two ride out to the report.
    #:
    #: **Empty over the whole bundle at §14 step 8**, which is that step's exit condition:
    #: no cell widens, so no handler mints one, and ``APPROXIMATED`` is 0.
    approximations: list[Approximation] = field(default_factory=list)

    #: What the PARSER is handed about this document: its path and the pointers an
    #: enclosing node constrains to ``type: "object"``.  Built here rather than passed,
    #: so there is one Source per module and the ``carries_nothing`` report the parser
    #: writes is the one this module collects.  §11 keeps the run out of the reading
    #: layer, and a Source carries no run: a path and a pointer set are the document.
    source: schema.Source = field(init=False)

    def __post_init__(self) -> None:
        self.source = schema.Source(
            document=self.document,
            applied_at=self.object_constrained,
            report=self.carries_nothing,
        )

    def resolve_node(self, uri: str) -> dict | None:
        """The schema a reference names, or ``None``.

        For section 2's intersection rule and for nothing else: two declarations that are each
        a bare ``$ref`` state the same KIND of thing about an instance and whether one
        narrows the other is a fact about the two TARGETS, which no amount of reading
        the two references can answer.  Measured on the one site:
        ``core/media-buy-frequency-cap-requirement.json`` at
        ``/allOf/1/properties/supported_control_modes/items`` references a one-member
        enumeration where the base it composes references a three-member one, and the
        one member IS one of the three -- a narrowing the reference pair cannot show.

        ``None`` for anything undecidable -- a URI naming no document of this bundle, a
        pointer naming no node, a target that refuses -- and the caller then treats the
        pair as not ordered and refuses the document.  That is the safe direction: a
        reference the merge rule cannot read is a declaration it must not claim is
        narrower.

        **A FRAGMENT and a BASE'S OWN LOCAL POINTER are no longer among the undecidable,
        and that is ``adcp-client-python-10l.72``.**  Both name a node as squarely as a
        no-fragment URI does, and answering ``None`` for them made the rule refuse a pair
        of references it could have read -- measured on
        ``core/tracker-execution-selector.json``, whose ``/oneOf/1`` names four nodes of
        ``core/vast-tracker-constraints.json`` ABSOLUTELY where the base it composes
        declares the same four as pointers into its own text.  The same node, written two
        ways.  A spelling relative to another document cannot be keyed by the URI alone
        across the whole run, so the run resolves the base's half PER DOCUMENT
        (``emit.based_nodes``) and hands the two readings in as one map.

        **A LOCAL pointer of THIS document is still ``None``, and that is scope and not
        an oversight**: the field a local reference decides is
        :func:`local_reference`'s, this map is the merge rule's, and a composing
        document's own local spelling is screened OUT of the base's half so that it
        cannot answer for the base's.

        **A reference is never DEREFERENCED into the field**, only into the predicate
        (:func:`_restatement`).  The field is decided from the document's own ``$ref``,
        because a cross-document reference is an IMPORT and not a copy (P2) -- the thing
        ``test_a_cross_document_reference_is_an_import_and_not_a_copy`` exists to catch.

        **The ``try``/``except Refusal`` that stood here is the one §2 retires**, and
        what replaced it is the same two answers read off a value: the binder RETURNS a
        refusal now, so "undecidable" is an ``isinstance`` arm rather than a caught
        exception.  Nothing about the reading changed -- a refused target was ``None``
        before and is ``None`` here -- which is what makes it a relocation.

        **And the binder itself is gone** (§14 step 7): :attr:`referenced` is the same
        two answers as DATA, built by the run from the documents it has already lowered,
        so a missing entry is every one of the undecidable cases at once -- a reference
        local to this document, a target that refuses, a URI naming no document of this
        bundle, a pointer naming no node of the document it does name -- and the caller
        treats the pair as unordered and refuses, which is the safe direction.
        """
        return self.referenced.get(uri)

    def target(self, uri: str, pointer: str) -> Target | Refusal:
        """What the run resolved the reference at ``pointer`` to.

        The lookup that replaced ``bind``'s call (§14 step 7): the answer was computed
        before this document was parsed, so there is no recursion to re-enter and no
        in-flight stack to consult.  A site with no entry is a document lowered outside
        a run (:func:`unresolved`), which is the refusing default the binder had.
        """
        self.asked.add((uri, pointer))
        return (
            self.targets.get((uri, pointer))
            # **A site §2's intersection rule produced, answered by URI**
            # (:attr:`inherited_targets`): a conjunct restating a property the base
            # declares carries every key the base alone declares, so a key the base
            # spells as a ``$ref`` reaches a pointer no edge of this document has.
            # Asked second, so a site the document spells itself keeps its own answer.
            or self.inherited_targets.get(uri)
            or unresolved(uri, pointer)
        )

    def importing(self, symbol: str, where: Importable) -> str:
        """Record that this module imports ``symbol`` from ``where``, and return it.

        **The one writer of both halves.**  :attr:`imports` is what the renderer writes
        the ``from ... import`` line off; :attr:`imported` is what a module composing
        this one reads to take the same symbol from the same declarer rather than from
        here, which would be a re-export and §1's second way to reach one class.  Two
        records written on one line, so neither can be the one a caller forgot.
        """
        self.imports.add((where.module, symbol))
        self.imported[symbol] = where.document
        return symbol

    def declare(self, pointer: str, declaration: ir.Declaration) -> Refusal | None:
        """Record one declaration at its POINTER, or say why not.

        ``None`` is the success answer and a :class:`Refusal` is the other, which is the
        shape §2 gives every total function of this walk: a caller that ignores the
        result is declaring a collision cannot happen, and a caller that returns it is
        refusing the document the collision belongs to.

        **It took a SYMBOL as well and checked both** (§14 step 7): a symbol already
        declared, and a pointer already declared.  The first check is
        ``lower/names.py``'s now, because the walk computes no symbol -- two POINTERS
        deriving one name is the same refusal with the same sentence, made where the
        names are.  What is left here is the pointer, which is a fact about the walk and
        not about §4's rules.

        Taking the declaration rather than its text is the whole of §7's gate at this
        seam -- the imports a declaration needs are reported by ``render.declaration``
        when the module is written, so a caller cannot declare a block and forget to
        merge its imports because there is no block to declare.
        """
        if pointer in self.at:
            # The symmetric failure to the one above, and the same kind of thing: a
            # pointer names ONE node of a document, so two symbols at one pointer
            # means a fragment reference to it would import whichever the walk
            # happened to declare last.  So this refuses rather than ordering them.
            #
            # **The population is 0 and it has been 1, which is the measurement worth
            # keeping** (``adcp-client-python-857``, and ``10l.53``, which filed the
            # stale "measured 0 times" this comment used to carry).  Every nested
            # declaration sits at its own node and the root's pointer is written once
            # by the row -- with ONE exception, and §4 puts it there deliberately: the
            # extras store of a class with a typed ``additionalProperties`` is parsed
            # at the CLASS's own pointer.  Routed through ``emit.decide_type``, the
            # store took that pointer's name entry and declared an ``AliasDecl`` at it
            # moments before :func:`declare_object` declared the ``ClassDecl``, and
            # this arm fired once over the 1,054 portable documents: ``brand.json`` at
            # ``/definitions/colors``, whose twelve properties and whose typed
            # ``additionalProperties`` are all the same local ``$ref``.  The fix is in
            # :func:`declare_object`, where the store now reaches THE DISPATCH rather
            # than the walk wrapper, because the three things the wrapper adds are
            # statements about the node that OWNS the pointer and the store does not
            # own this one.  A figure claiming 0 where the population is not 0 invites
            # a later row to delete a reachable arm, so the reading is written out
            # rather than the number alone.
            return Refusal(
                "$ref",
                pointer,
                "two nodes are declared at this pointer: "
                f"{type(self.at[pointer]).__name__} and {type(declaration).__name__}, so "
                "a reference to it would import whichever came last",
                kind=Kind.VERDICT,
            )
        self.at[pointer] = declaration
        self.declarations.append(declaration)
        return None


@dataclass(frozen=True)
class Rules:
    """What one node's D6 rules come to, as the four things a lowering needs.

    ONE carrier and one call (:func:`rules_at`), because the four answers are read
    off one reading of the node and a lowering that took three of them would be a
    lowering that could take one and forget the other -- which is exactly what
    happened: the object row read them all, the ``allOf`` row read none, and the
    documents in this bead's population refused at a keyword whose mechanism was
    complete three modules away.

    * ``screen`` is what a keyword check may ADMIT at this node.  It is not
      :func:`rule_sources` flat, and the difference is load-bearing: a
      ``oneOf``/``anyOf`` is a rule only where every branch states which keys are
      PRESENT (``rules.presence_only``, the published step-5/step-7 test).  A
      combinator of SHAPES is a nested union, ``rules.lower`` writes nothing for it,
      and admitting it would emit a class that drops the combinator silently -- a model
      wider than its document.  **Re-measured at ``adcp-client-python-onq``, with the
      probe STATED so the next row can repeat it**: over the 1,054 portable documents,
      every node carrying ``properties`` beside a combinator ``presence_only`` answers
      no for is **68 nodes in 60 documents**, where the same probe read 77 in 69 before
      §5's "A union of presence-only branches that also forbid" (2026-10-27) taught the
      branch reading to carry a ``not``.  The screen is what keeps those refused BY
      NAME rather than dropped.
    * ``rules`` are the INSTANCES of ``adcp.types._runtime``'s own frozen dataclasses
      this node's rule sources come to (``docs/plan/architecture.md`` §7).  Empty where
      the node states no rule this lowering can express, which D4 makes correct rather
      than a refusal (``codegen.lower.rules``' module docstring is the one place that
      judgement is stated).  It was the class-body LINE and its imports; the renderer
      writes the constructor expressions and reports the names they use, so a rule kind
      is declared once -- in the runtime -- and the walk composes values.
    * ``distinct`` are the property keys whose array this node states is DISTINCT.
      D6 has claimed their ``uniqueItems``, so :func:`fields` strips the keyword off
      the declaration before the array row sees it and renders the fact onto the
      field instead (``ir.Field.distinct``).  It travels on this carrier for the
      reason the other three do: a caller that reads the rule tuple and forgets the
      strip emits a class whose ``uniqueItems`` reaches a row that refuses it by
      name, which loses the document the rule was written for.
    """

    screen: frozenset[str]
    rules: tuple[Rule, ...]
    distinct: tuple[str, ...]
    #: The names this node forbids ONE AT A TIME, read off the ``ForbiddenGroups`` the
    #: rules above already reduced the node's ``not`` to: a SINGLETON group says the
    #: name is not present at all, where a longer one says only that the group is not
    #: present IN FULL and so forbids no single name.
    #:
    #: Read here and not in the lowering that needs it, for the reason the other four
    #: are: §4's third dispatch source asks "a ``required`` name one branch declares and
    #: another FORBIDS", and the reduction of ``not``/``anyOf``/``allOf`` over
    #: ``required`` into groups is ``lower.rules``' one reading -- a lowering cannot
    #: import it (§11) and a second reduction of the same keyword is the second copy §3
    #: forbids.  So the dispatch derivation reads the rule the branch already carries.
    forbids: frozenset[str] = frozenset()


def rules_at(
    node: "nodes.Base", *also: Mapping[str, Any], position: Position = Position.ROOT
) -> Rules:
    """D6's reading of a node, for a lowering that cannot import the rules module.

    Imported on use, because ``codegen.lower.rules`` imports this module for
    :func:`rule_sources` and :func:`declares` -- the one place the two halves
    meet, and the lowering's direction is the one D13 fixes, so this side is the lazy
    one.  The same lazy import ``lower_object`` already used, now in one place.

    ``screen`` is READ OFF THE TABLE at ``position``: a rule source is a keyword whose
    cell compiles to a RULE there, and the two combinators join it only where every
    branch is ``required``-only -- a co-occurrence, which is this caller's question and
    not the cell's.  The eight rule sources are the same at every position a class can
    sit at, so the default is ROOT and a caller at another position says so.

    **``also`` is the other nodes whose rules belong to THIS class**, which is what a
    draft-07 ``allOf`` conjunct is: it applies to the same instance, so it is not a
    separate object and its rule is this node's rule, exactly as a conjunct's
    ``properties`` are this node's fields (:func:`lower_composition`).  They are one
    ``Rules`` and not one per node because a class body can bind ``_adcp_rules``
    ONCE -- two lines would make the second silently replace the first -- so the
    sources are concatenated and the tuple is written once.

    ``screen`` is ``node``'s alone and deliberately not merged: a keyword screen is
    asked about one node, and each conjunct is screened by its own call at its own
    pointer, which is what keeps a refusal pointing at the node that caused it.

    **Converted to node fields.**  The node's own reading is :attr:`nodes.Base.rules`
    (the rule sources, which the parser classified from the table at this position),
    :attr:`nodes.Base.declared` (``uniqueItems`` sits one level down, on the array a
    property holds) and whether it states ``additionalProperties`` (the ``minProperties``
    gate) -- and ``screen`` is the rule sources the node STATES, which is what a screen
    asks: the only keys a screen can admit are keys the node carries, and a rule source
    the node carries is in that mapping exactly when the table and ``presence_only``
    admit it here.  ``also`` stays raw, because an ``allOf`` conjunct is a DECLARATION by
    §2's own decision.
    """
    from codegen.lower import rules

    lowered = [
        rules.lower(node.rules, node.declared, "additionalProperties" in node.declares),
        *(rules.lower_declaration(c, position) for c in also),
    ]
    screen = frozenset(node.rules)
    distinct: list[str] = []
    for one in lowered:
        distinct += [key for key in one.distinct if key not in distinct]
    written = tuple(rule for one in lowered for rule in one.rules)
    return Rules(
        screen=screen,
        rules=written,
        distinct=tuple(distinct),
        forbids=frozenset(
            group[0]
            for rule in written
            if isinstance(rule, ForbiddenGroups)
            for group in rule.groups
            if len(group) == 1
        ),
    )


def kind_for(key: str, position: Position) -> Kind:
    """The KIND of the refusal this key mints, read off the CELL.

    ``docs/plan/architecture.md`` §3: "a refusal's kind is derived from the cell and
    never chosen at a raise site."  Three answers and each is the cell's:

    * a key whose cell is REFUSE is a VERDICT -- the obstruction belongs to the
      document, which is what §7 of the semantics document decided about it;
    * a key with NO ROW is a VERDICT too, and for a different reason worth keeping
      apart: a keyword in none of §5, §6 or §7 is one the bundle did not use, so there
      is no lowering to schedule and answering "a later row does" about it would
      promise an unscheduled row;
    * a key whose cell is a LOWERING effect and whose handler claims nothing is a
      DEFERRAL -- §9's first rule, because minting a verdict for unwritten code reports
      clearable work as finished.

    *Why derived.*  The reviews record the two kinds assigned by hand at a raise site
    and the assignment coming out inverted in bulk: a cell the semantics document
    decides, written up as a verdict against the document.  A kind read off the table
    cannot say that, because the table is where the decision that the keyword compiles
    was made.  Measured on the base tree (``5d92cf2c0``, 406 emitted and 648 refused of
    1,054), the old reading -- "is the name in draft-07's meta-schema" -- called 11 of
    the 648 a verdict about a non-keyword: ``discriminator`` 7, ``notes`` 2,
    ``enumMetadata`` 1, ``last_updated`` 1.  Of those four names the table admits three
    (§6) and refuses one (§7), so the same four reach three different answers now and
    none of them is read off a meta-schema.
    """
    answer = keywords.cell(key, position)
    if answer is None or answer.effect is keywords.Effect.REFUSE:
        return Kind.VERDICT
    return Kind.DEFERRED


#: What a refusal says about a key the table gives no row at all.  A SENTENCE and not a
#: classification: :func:`kind_for` carries the classification, so nothing here is read
#: to decide anything.
NO_SUCH_KEYWORD = (
    "sections 5, 6 and 7 of docs/plan/rebuild-plan.md name every keyword the bundle "
    "uses, and none of them names this one; the first document to carry a new keyword "
    "refuses by name rather than being emitted with it ignored"
)

def carried(decided: Decided, pointer: str, what: str, mod: Module) -> ir.TypeRef | Refusal:
    """The type of a node at a position with NO FIELD to carry its facts.

    Three positions ask: an array's ELEM and a mapping's MAPV
    (``lower.containers._contents``), and a union BRANCH (``lower.union.nested``).  One
    function for the three, because it is one question -- *this node's ``format`` or
    its bound has no slot in the annotation above it; what carries it?* -- and two
    copies of the answer is how two positions come to drop a fact differently.  The two
    refusals this replaced were already the same sentence twice, each naming the same
    module as the row that would lower it.

    Section 2 is the answer and it is the same at all three: **constraints bind to the
    type, not the field.**  A named type nests into ``list[...]``, into a mapping value
    and into a union branch, carrying its bound with it;
    ``emit.name_the_constraint`` is where the name comes from.  On a BRANCH the
    alternative is not merely unavailable but wrong: the field holds the other branches
    too, so a bound written there refuses values the document accepts.

    A shape with no name REFUSES, and the detail names the keyword that would have to
    be named.  It is a DEFERRAL: the obstruction is a spelling ``codegen.constraints``
    does not have yet, which is unwritten code and not a property of the document, of
    pydantic or of the pointer space.
    """
    if not (decided.constraints or decided.format is not None):
        return decided.type
    # Function-scope for :func:`decide`'s reason, and the name is reached at all for
    # :func:`decide`'s reason: the spellings are ``codegen.constraints``'s, that module
    # imports this one, and ``emit.name_the_constraint`` is the one function that pairs
    # a resolved spelling with the record of the alias it resolved to.
    from codegen.lower.scalars import name_the_constraint

    named = name_the_constraint(decided, mod)
    if named is not None:
        # **The rules bound to the type survive the naming**, which is the whole of why
        # they are on the :class:`codegen.ir.TypeRef` and not beside it: a bound is
        # carried by a SHARED alias (``NonEmptyList[T]``, reached by every node stating
        # ``minItems: 1``) and a rule is this SITE's, so the alias becomes the inner type
        # and this node's ``Annotated`` wraps it.  Written into the alias's own
        # declaration instead, one document's ``uniqueItems`` would narrow every other
        # node that happens to share its bound.
        return replace(named, validators=decided.type.validators)
    stated = {
        **decided.constraints,
        **({"format": decided.format} if decided.format else {}),
    }
    return Refusal(
        sorted(stated)[0],
        pointer,
        f"{what} states {stated} and ir.TypeRef carries no constraint, so the "
        "keyword would reach the field holding this node and bind every other node "
        "under it; section 2 binds a constraint to the TYPE, and the alias module "
        "codegen.constraints has no spelling for this shape",
        kind=Kind.DEFERRED,
    )


def check_keywords(
    node: nodes.Base,
    handled: Collection[str] = (),
    why: str | None = None,
    mod: "Module | None" = None,
) -> Refusal | None:
    """The first keyword this NODE states that the TABLE does not admit here, as a
    refusal -- or ``None`` where every key is admitted.

    **Converted to node fields.**  :attr:`nodes.Base.declares` is the set §3's admission
    reader can refuse on -- ``keywords.declares`` at the node's own position, computed
    once by the parser -- and :attr:`nodes.Base.extensions` is the ``x-`` keys it
    reports.  The two are walked in one sorted pass, which is the order the raw mapping's
    keys were walked in, so the keyword a document is refused on does not move.  The
    POSITION is the node's own field (§6: "the parser assigned it from the structural
    keyword it descended through"), and ``handled`` stays the CALLER's: §3 gives the
    lowering reader "the cells this handler writes", and §14 step 8 is what closes it.

    :func:`check_declaration` is the same screen asked of a raw DECLARATION, for the one
    reader §2 keeps at that level -- an ``allOf`` conjunct, which the intersection rule
    merges as a declaration.

    ``docs/plan/architecture.md`` §3's admission reader is exactly these arms:

    * a cell that carries NOTHING, ANNOTATES or names (``NAME``) is admitted and
      carried nowhere by the screen;
    * a cell that is REFUSE refuses the document, and :func:`kind_for` makes it a
      VERDICT;
    * a key with NO ROW refuses the document as a VERDICT naming a keyword the bundle
      did not use before -- unless it is in the ``x-`` namespace, which is admitted by
      PREFIX because a vendor extension cannot be a schema keyword, and REPORTED,
      because the prefix rule once dropped ``x-enum-descriptions`` silently and that
      key carries member docstrings;
    * a cell with a lowering effect is a fact the node's kind consumes: ``handled``
      names the ones this caller has written, and anything else is a DEFERRAL.

    ``handled`` is therefore the caller's own COVERAGE and no longer an admission list:
    what is left in it at each call site is the set of cells that handler writes, which
    is the LOWERING reader §3 gives to ``lower/*`` and §14 step 8 closes.  Everything
    those sets used to carry for admission alone -- the annotations, the definition
    sections, the ``x-`` prefix, ``enumMetadata``, ``discriminator`` -- is the table's
    answer now and is gone from all of them.

    **The KIND is never chosen here.**  A caller may pass its own ``why``, which is
    prose for a reader, and the classification still comes from :func:`kind_for`: a
    sentence and a kind decided together at one production site is how a cell the
    semantics document decides came to be written up as a verdict against the document.

    **The screen RETURNS its refusal** (§2), so a handler's first line is
    ``if (refused := check_keywords(...)) is not None: return refused`` and the type
    checker is what says a handler cannot forget it: a handler that drops the result
    goes on to read node fields it has not admitted.
    """
    return _screen(
        sorted((*node.declares, *node.extensions)),
        node.pointer,
        node.position,
        handled,
        why,
        mod,
    )


def check_declaration(
    declaration: Mapping[str, Any],
    pointer: str,
    position: Position,
    handled: Collection[str] = (),
    why: str | None = None,
    mod: "Module | None" = None,
) -> Refusal | None:
    """:func:`check_keywords`, asked of a raw DECLARATION rather than of a node.

    The one reader at that level is §2's intersection rule, which merges two declarations
    of one property and hands the merged one back to the parser, so an ``allOf`` conjunct
    is a :class:`codegen.schema.nodes.Conjunct` and not a node -- and a conjunct is
    screened at its own pointer and at CONJ.  Nothing else calls this, and
    ``tests/test_import_rule.py`` is where that is held.
    """
    return _screen(sorted(declaration), pointer, position, handled, why, mod)


def _screen(
    keys: "Collection[str]",
    pointer: str,
    position: Position,
    handled: Collection[str],
    why: str | None,
    mod: "Module | None",
) -> Refusal | None:
    """The admission reader itself, over keys already in the order the report wants."""
    for key in keys:
        # **``handled`` is asked FIRST**, before the cell, because a caller that claims
        # a key has already decided what happens to it -- including a key the table
        # REFUSES: ``lower_composition`` hands its ``foreign`` set here precisely so
        # that an ``errorMessage`` on a conjunct is DROPPED AND REPORTED, which is §7's
        # own answer for it, rather than refused on the very name the drop accounted
        # for.  Measured on ``media-buy/sync-catalogs-request.json``.
        if key in handled:
            continue
        answer = keywords.cell(key, position)
        if answer is None:
            if keywords.admitted_by_prefix(key):
                # Admitted by shape, and READ ONCE rather than assumed to be metadata.
                if mod is not None:
                    mod.carries_nothing.append(
                        f"{pointer or '/'}: {key}: a key in the x- namespace with no "
                        "row in section 6, so it is admitted by the prefix alone and "
                        "nothing has read it"
                    )
                continue
            return Refusal(key, pointer, NO_SUCH_KEYWORD, kind=kind_for(key, position))
        if answer.effect is keywords.Effect.REFUSE:
            return Refusal(key, pointer, why or answer.compiles, kind=kind_for(key, position))
        if not keywords.lowers(answer):
            continue
        return Refusal(
            key,
            pointer,
            why or refusal.DEFERRED_TO_A_LATER_ROW,
            kind=kind_for(key, position),
        )
    return None


# --------------------------------------------------------------------------- #
# the field builder and the class declarer
# --------------------------------------------------------------------------- #
def fields(
    props: Mapping[str, nodes.Node],
    required: Collection[str],
    pointer: str,
    mod: Module,
    *,
    inherited: Collection[str] = (),
    declared_at: Mapping[str, str] | None = None,
    distinct: Collection[str] = (),
    reuse: Mapping[str, ir.Field] | None = None,
    carried: Collection[str] = (),
) -> list[ir.Field] | Refusal:
    """The decided properties for one property map, children declared first.

    Shared with a composing row, which builds ONE property map out of a root's
    own ``properties`` and an inline ``allOf`` conjunct's.  How a property is
    decided is the same question wherever it was declared, and a second copy of
    this loop is how two declarations of one field come to disagree about the
    answer.

    **``required`` is read IN ORDER, so the caller owns that order** (P7): the names no
    declaration declares come out of a comprehension over it, and each one becomes a
    FIELD below, so the argument's order is the emitted class's field order and
    therefore part of the artifact.  A caller passing the document's own ``required``
    tuple passes document order; a caller holding a ``set`` -- the composing row, which
    unions the node's own names with a base's ``frozenset`` -- sorts before it passes,
    because a set of strings iterates in hash order and the emitted tree must be a
    function of the bundle.  It was the REFUSAL SENTENCE's order before those names
    became fields; the same argument now decides a line of rendered Python, which is a
    stronger reason for the same rule.

    ``inherited`` names the keys a BASE CLASS already declares.  They are not
    decided here -- the field is inherited, and a subclass that restated it would
    shadow the base's type with whatever its own restatement happens to say --
    but they do satisfy ``required``, because an inherited field is present on
    the class.  The row decides what goes in it (the narrowing rule); this
    function only honours it.  ``declared_at`` gives the pointer a key was
    declared at where that is not ``<pointer>/properties/<key>``, which it is not
    for a key that came from a conjunct.

    ``reuse`` names the keys whose FIELD is one an enclosing class already decided,
    and hands it over: its type, its constraints, its format and its ``uniqueItems``.
    Everything else about the field is still read off ``props`` here -- the default,
    the description, the requiredness, the attribute spelling -- so a reused key is a
    field of this class stating the DOCUMENT's own annotations over an inherited type.

    **This is not the ``decided`` argument that was removed, and the reason it was
    removed does not reach it.**  That one carried a per-property type the caller had
    already decided so the union row could turn a branch's ``const`` into a
    ``Literal``; it went because ``decide_type`` reaches ``codegen.lower.const`` for
    every node, so the type WAS derivable here and two lowerings had to agree about
    one keyword.  A reused type is the other case: it is not derivable here, because
    deciding it declares the nested classes AGAIN and in this module, at a pointer
    **this document does not have** -- measured on
    ``formats/canonical/image_carousel.json``, whose merged ``slots`` emits a second
    ``...SlotsItem`` stamped ``#/properties/slots/items`` where that document's own
    ``properties/slots`` carries a ``default`` and a ``description`` and nothing else,
    and ``schema_at`` raises ``KeyError: 'items'``.  There is still exactly one
    lowering of the node: the base's.

    ``distinct`` is the same "one position, not everywhere" shape that ``decided``
    had, and it survives because its keyword has no such row: it names the keys whose
    array D6's rule lowering has CLAIMED the ``uniqueItems`` of
    (``lower.rules._distinct``).  The keyword is stripped off the declaration here so
    the array row never sees it -- which is what leaves that row's screen refusing an
    array no class holds rather than widening it -- and :attr:`codegen.ir.Field.distinct`
    carries the fact onto the field, where ``_field`` renders it.  A key named here
    whose declaration is not an array with ``uniqueItems: true`` is a caller defect,
    so nothing is silently stripped: the strip is read off the declaration and the
    flag off this set, and the two agreeing is asserted by the rules lowering's own
    gate.  A REUSED key takes the flag off the field it reuses instead: the
    ``uniqueItems`` was claimed by the rule on the class that decided it, which a
    subclass inherits, so the subclass's own rules do not name the key.

    ``carried`` names the required keys whose presence the CLASS enforces by something
    that is NOT a field of its own, so they are not undeclared and get no field here --
    which is the one thing that keeps the ``Any``-field answer below off a union base.
    **One caller passes a non-empty one and §5's ``required`` row is the whole of why**:
    at a ROOT beside a union the row reads "required on the base's fields, and the names
    recorded in ``_ROOT_REQUIRED``, so a refusal can separate a field the root requires
    from one that SELECTS A BRANCH" -- which presupposes that a name selecting a branch
    is not a field of the base.  ``core/product-format-declaration.json`` is that
    sentence's own shape: its root requires ``format_kind`` (the discriminator §4
    derives) and ``params``, its 15 root properties declare neither, and each of its 16
    branches declares AND requires both -- so the branch classes are what hold the
    fields, the branches' own requiredness is what enforces the presence, and
    :attr:`adcp.types._base.BranchDispatchMixin._ROOT_REQUIRED` is what names the two in
    the DOCUMENT's vocabulary when no branch admits a payload
    (``_base.BranchDispatchMixin._no_branch``, which reads the raw mapping and not the
    model).  Measured over every node of the 1,054 portable documents: **2 union nodes
    state a ``required`` naming a key their own ``properties`` do not declare** --
    ``core/product-format-declaration.json`` at ``/`` and
    ``creative/validate-input-request.json`` at ``/properties/targets/items`` -- and in
    BOTH every branch declares and requires every such name.

    **``position`` is GONE with the refusal it was here for.**  It existed so the
    undeclared-``required`` refusal could read its kind off the ``required`` cell at the
    node's own position (:func:`kind_for`) rather than name one; that refusal is now a
    field, and nothing else in this function asked the question.  Every position a class
    can sit at reads the same ``TYPE`` cell, so the answer never moved anyway, which is
    why removing it changes no caller's meaning.
    """
    held = (*inherited, *carried)
    undeclared = [r for r in required if r not in props and r not in held]

    built: list[ir.Field] = []
    spelled: dict[str, str] = {}
    where = declared_at or {}
    reuse = reuse or {}
    # **The loop returns on the FIRST refusal, in the property map's own order**, which
    # is the document's own key order because the parser built the map by walking it
    # (``schema.parse``).  That is :func:`codegen.refusal.first_refusal` fused with the
    # map that would have produced the sequence, and §6's "earliest refusal in document
    # order" is what the fusion preserves: the loop cannot reach a later property's
    # refusal before an earlier property's.  Fused rather than separate because the body
    # is SEQUENCED -- a dropped default is recorded on the module as the field is built --
    # so a batch of results would record drops for properties after the refusing one.
    for key, child in props.items():
        at = where.get(key, f"{pointer}/properties/{key}")
        fname = names.field_name(key, mod.reserved)
        if fname in spelled:
            return Refusal(
                "properties", at, f"{key!r} and {spelled[fname]!r} both spell the field {fname!r}"
            , kind=Kind.VERDICT)
        spelled[fname] = key
        is_distinct = key in distinct
        if key in reuse:
            held = reuse[key]
            # The REUSED field's type ALREADY states its bound and its format (§2, and
            # :attr:`codegen.ir.TypeRef.facts`), so it is taken whole: splitting the
            # three back out and recombining them is what two carriers of one fact
            # invites, and the base decided this type at its own pointer.
            field_type = held.type
            is_distinct = held.distinct
        else:
            # **§4's nested name rule as a HOP and not as a name** (§7): what this
            # records is the structural fact -- this child hangs off the class at
            # ``pointer`` through the property ``key`` -- and ``lower/names.py`` is what
            # turns it into ``<Parent><Property>``.  The child's own pointer is the key,
            # which for a key that came from an ``allOf`` conjunct is the conjunct's
            # (``declared_at``) and never this node's.
            mod.hops[child.pointer] = names.Property(pointer, key)
            decided_type = lower_node(child, mod)
            if isinstance(decided_type, Refusal):
                return decided_type
            # §2: **constraints bind to the TYPE, not the field.**  A :class:`Decided`
            # carries the three apart because a format is either IN the type or beside
            # it and never in both; the field carries one type that states all of them,
            # so the same bound reached through a list, a mapping value or a union
            # branch is the same value.
            field_type = replace(
                decided_type.type,
                facts=decided_type.constraints,
                format=decided_type.format,
            )
        is_required = key in required
        default = MISSING
        # **Through a LOCAL ``$ref`` the target's ``default`` is this field's**, which is
        # draft-07 replacing the node with its target read by §5's ``default`` row:
        # :attr:`Module.referred` is where :func:`local_reference` put it, and the node's
        # OWN sibling wins where it states one -- the same precedence §5's ``$ref`` row
        # gives a ``description`` sibling.
        stated = child.annotations.get("default", mod.referred.get(child.pointer, MISSING))
        # **And through a CHAINED remote ``$ref`` the hop's ``description`` is this
        # field's** (:attr:`Module.described`), by the same precedence and for the same
        # reason: §5's ``$ref`` row makes a sibling's ``description`` authoritative, and
        # ``bundle.record`` inlines the hop's text at this very pointer -- so the node's
        # OWN sibling wins and the chain's stands where the node is silent.
        described = (
            child.description
            if child.description is not None
            else mod.described.get(child.pointer)
        )
        if stated is not MISSING:
            if is_required:
                # Section 5's ``default`` row: **on a REQUIRED property, dropped and
                # reported, because no rendering makes a field both required and
                # defaulted.**  A pydantic field with a default is not required, so
                # transcribing one here would widen the model's accepted set to admit
                # an instance omitting a key the document demands -- and the schema
                # half of ``strict_validate`` would hide that in both acceptance
                # directions.
                #
                # Dropping it changes NO accepted set, which is why the row drops it
                # rather than refusing the document: the key is present in every
                # instance the document admits, so the default can never be applied
                # and a model that omits it accepts and rejects exactly what the
                # document does.  ``harness._constrains_nothing`` says the same thing
                # on the grading side, gated on the same shape, so the fact is folded
                # rather than reported as a drop the model got wrong.
                #
                # REPORTED, and that half is not optional: a fact the document states
                # and the emitter silently discards is the one failure this pipeline
                # has no other guard against.  :attr:`Module.drops` carries it out to
                # ``emit.emit``, which prints it and hands it to the suite.  5 of the
                # bundle's 339 property defaults sit on a required property.
                mod.drops[at] = stated
            else:
                default = stated
        built.append(
            ir.Field(
                name=fname,
                wire=key,
                type=field_type,
                required=is_required,
                default=default,
                description=described,
                distinct=is_distinct,
            )
        )
    # **A required name NO declaration declares is a required field of type ``Any``**,
    # which §8's empty-schema clause decides and which is EXACT rather than wide:
    # ``required: ["x"]`` with no entry for ``x`` admits an object carrying ``x`` with
    # any value, and ``Any`` is what §5's ``type`` row already gives an absent type
    # word.  Nothing is widened, nothing is dropped and no declaration is owed, so this
    # appends a field and declares no approximation.
    #
    # **It was a refusal, and the refusal was a conflict between two of this compiler's
    # own decisions rather than anything a document got wrong.**  §5's ``required`` row
    # called such a name "a presence rule with no field"; a rule renders no ``required``
    # into a model's JSON schema while the keyword's own cell is ``rendered=True``, so
    # the rule half reported ``differs`` at this pointer's ``/required`` -- and the field
    # half reported the model-only ``properties`` entry as ``added``, which §8 had no
    # fold for.  Both halves were red, so neither was written.  §8 now folds the entry
    # (``harness._states_no_graded_fact``, reading the empty schema the way §5's
    # ``additionalProperties`` row already reads it), and with the fold the field half is
    # the faithful one.  27 of the 95 refusals, 5 of them primary.
    #
    # ``held`` is why this fires only where NOTHING holds the name: a key an INHERITED
    # field declares is the base's, and a CARRIED one is the union row's -- at a ROOT
    # beside a union the branches declare and require the name and
    # ``_ROOT_REQUIRED`` enforces it, which
    # ``test_a_root_required_the_branches_declare_is_root_required_and_not_a_field``
    # asserts a field would get wrong.
    #
    # In ``required``'s own order, which is the CALLER's (see the note above on P7):
    # these keys have no ``properties`` entry, so the document states no key order for
    # them and ``required`` is the only order it states.  That order is now the emitted
    # class's FIELD order and not just a sentence's, which is why the composing caller
    # sorts before it passes.
    for key in undeclared:
        fname = names.field_name(key, mod.reserved)
        if fname in spelled:
            return Refusal(
                "required",
                pointer,
                f"{key!r} is required with no declaration and {spelled[fname]!r} is "
                f"declared, and both spell the field {fname!r}",
                kind=Kind.VERDICT,
            )
        spelled[fname] = key
        built.append(ir.Field(name=fname, wire=key, type=ir.TypeRef("typing.Any"), required=True))
    return built


def declare_object(
    node: "nodes.Base",
    pointer: str,
    mod: Module,
    props: Sequence[ir.Field],
    shape: Shape,
    position: Position = Position.ROOT,
    *,
    extras: nodes.Node | None = None,
    bases: tuple[ir.TypeRef, ...] = (),
    branches: tuple[ir.TypeRef, ...] | None = None,
    rule_nodes: Sequence[Mapping[str, Any]] = (),
    description: str | None = None,
    root_required: tuple[str, ...] | None = None,
    discriminator: str | None = None,
    combinator: str | None = None,
) -> str | Refusal:
    """Assemble one class out of decided properties, and record what it declares.

    The other half shared with a composing row: D8's ``extra``, the description,
    the ``__adcp_schema__`` the renderer writes, and the :class:`Shape` a later
    subclass reads.  ``bases`` is empty for a node that composes nothing, and
    then the base is ``AdCPBaseModel``; a composing row passes the symbols its
    ``$ref`` conjuncts bound (D7 -- a base is DERIVED from what the document
    composes, never classified by hand), and ``AdCPBaseModel`` arrives through
    them.

    **D6's rule tuple is written HERE**, for the node being declared, and that is what
    makes "a rule attaches to the nearest class" true of every row rather than of the
    one that remembered.  This is the one funnel a class WITH FIELDS passes through --
    the object row, the ``allOf`` row and a union BRANCH all arrive here -- so the
    ``allOf`` row gets its root's ``not``/``dependencies``/``minProperties`` by passing
    through rather than by repeating the object row's call.  A rule renders nothing in a
    model's JSON schema, so the symmetric comparison neither gains nor loses a fact by
    this; the only instrument that observes one is a direct ``model_validate``, which
    is what ``src/adcp/types/_runtime.py`` records.

    ``rule_nodes`` are the OTHER nodes whose rules are this class's -- an ``allOf``
    conjunct, which draft-07 applies to the same instance.  Empty for every row but
    the composing one.

    ``extras`` is the extras STORE as a parsed node -- the ``dict[K, V]`` §5 says a typed
    ``additionalProperties`` on a class is -- or ``None`` where the document states
    ``false``, ``true``, the empty schema or nothing.  The parser builds it
    (``schema.parse.extras_store``) and the three callers that can meet one pass it.

    ``root_required``, ``discriminator`` and ``combinator`` are §4's three facts a UNION
    BASE carries and no other class does, so all three are ``None`` for every row but
    the union row.  They are declared on the class rather than formatted into a body
    line, which is §7's gate at this seam: ``render._union_base_lines`` writes the four
    statements and nothing before it holds one.

    ``description`` is §6's description-authority rule clause 3, handed DOWN by the two
    rows that compose: a class whose own node states none states the one its base does,
    which the composed document states at this pointer.  Passed rather than merged into a
    declaration, because the node is a node now and §6 makes silence the enclosing
    reading rather than a rewritten mapping (``lower_composition`` and the union's
    ``$ref`` branch, which is a composition of the union base and the target).
    """
    stated = rules_at(node, *rule_nodes, position=position)
    # D8's typed row: a property the class does not DECLARE is validated against
    # the document's own value schema, through pydantic's ``__pydantic_extra__``.
    # The TYPE is the same ``dict[K, V]`` a mapping node lowers to, decided by the
    # same row -- the node is handed to :func:`decide` as the mapping it is, with
    # whatever the node says about its KEYS carried across (D5 types the key too),
    # so an extras store and a mapping cannot come to read ``additionalProperties``
    # two different ways.  :func:`decide` rather than an import of the container row,
    # because the per-node dispatch is one function and a second entrance to the
    # container row would be a second reading of which row a node belongs to.
    ap = node.extra
    # **§2's SECOND node rewrite, retired.**  This built a synthetic
    # ``{"type": "object", "additionalProperties": ap, "propertyNames": ...}`` and handed
    # it to the dispatch -- a node the document does not have.  The extras STORE is now a
    # ``nodes.Mapping_`` the PARSER builds, at the class's own pointer, with its value at
    # MAPV and its key at KEY (``schema.parse.extras_store``), so the extras store and a
    # mapping cannot come to read ``additionalProperties`` two different ways because
    # there is one reading of it and the parser makes it.
    extra_type = None
    if extras is not None:
        # No hop: the parser builds the extras store at the CLASS's own pointer, because
        # it is the same instance re-read (§4), so it inherits the class's own name entry
        # and its VALUE hangs off that pointer like any mapping's.
        #
        # **THE DISPATCH AND NOT THE WALK WRAPPER, and §4's shared pointer is the whole
        # reason.**  ``lower_node`` is ``emit.decide_type``, which is the dispatch plus
        # three statements about THE NODE AT A POINTER -- adopt the class an earlier
        # node of identical content declared at it, name the node where the bundle's
        # ``$ref``\\ s name its pointer, and seed the content memo at it.  A pointer
        # names ONE node, and the store is the one node in the tree that does not own
        # the pointer it carries: §4 hands it the CLASS's, so all three of those
        # statements are about the class standing here and none is about the store.
        # Routed through the wrapper they fire on the store, which declares an alias at
        # the class's own pointer moments before this function declares the class --
        # ``Module.declare``'s collision, measured on ``brand.json`` at
        # ``/definitions/colors``, a bundle-named class whose twelve properties and
        # whose typed ``additionalProperties`` are all one local ``$ref``.  The alias
        # would also be WRONG where it did not collide: a ``$ref`` to
        # ``#/definitions/colors`` names the object, so the symbol at that pointer is
        # the class and never the ``dict[K, V]`` its extras store comes to.
        #
        # The store's own CHILDREN keep the wrapper: its value sits at MAPV under
        # ``<pointer>/additionalProperties`` and its key at KEY, each at a pointer it
        # owns, and ``containers.mapping`` reaches both through ``lower_node`` as any
        # mapping's children are reached.  So a named or collapsed node inside the
        # store is named and collapsed exactly as it would be anywhere else.
        #
        # Imported on use, for the reason :func:`rules_at` is: ``codegen.lower.decide``
        # imports this module, and D13 fixes the direction, so this side is the lazy one.
        from codegen.lower.decide import decide as dispatch

        store = dispatch(extras, mod)
        if isinstance(store, Refusal):
            return store
        extra_type = store.type
    #: What the DOCUMENT gives this class for ``extra``, read where §8's pairing fold
    #: puts the fact: this node's own ``additionalProperties`` first, and the value its
    #: BASES resolved where the node states none (:attr:`Shape.extra`, which carries the
    #: whole reason).  Written onto the class unconditionally below, so pydantic's
    #: ``model_config`` merge along the MRO cannot decide it.
    #:
    #: ``None`` only where neither the node nor anything it composes states one, and then
    #: ``AdCPBaseModel``'s own ``extra="ignore"`` is the answer -- one value, fixed by the
    #: model base rather than by which base happened to arrive second, so there is
    #: nothing for an MRO order to decide and nothing for this class to state.  That is
    #: the one case the row's "never inherits" does not reach, and it is written here
    #: rather than left implicit: the clobber is a disagreement between two bases, and
    #: silence everywhere is not one.
    resolved_extra = (
        "allow"
        if extra_type is not None
        else {False: "forbid", True: "allow"}.get(ap, shape.extra)
    )
    described = node.description if node.description is not None else description
    declaration = ir.ClassDecl(
        # **The POINTER in the name slot, until the pass runs** (§7, and
        # ``lower/names.py``'s own docstring): the walk computes no symbol, so what a
        # declaration carries is where it sits and ``names.assign`` binds the name §4
        # derives for it.
        name=pointer,
        ref=schema_ref(mod.document, pointer),
        fields=tuple(props),
        description=described,
        # D8, and §5's ``additionalProperties`` row: **a class DECLARES the ``extra``
        # the document gives it and never inherits it** (:attr:`Shape.extra`, which
        # carries the measurement).  It read the node's own value alone and left
        # ``None`` -- "absent leaves the base's default in place" -- and that sentence
        # is the defect: pydantic merges ``model_config`` along the MRO, so a class
        # composing TWO bases took whichever value the later one carried and a default
        # ``ignore`` silently overrode an ``allow`` the document states.  A TYPED
        # ``additionalProperties`` is ``allow`` with the type beside it: the properties
        # are part of the document, so they are retained, and ``__pydantic_extra__`` is
        # what validates them.
        extra=resolved_extra,
        extras=extra_type,
        bases=bases,
        rules=stated.rules,
        root_required=root_required,
        discriminator=discriminator,
        combinator=combinator,
        branches=branches,
    )
    # :attr:`Shape.decided` is written HERE and by no caller, for the reason the rule
    # tuple above is: this is the one funnel a class with fields passes through, so a
    # row cannot forget to record what it decided.
    # The caller's own ``decided`` is what the class INHERITS (a composing row passes
    # its bases'), and the props it is handed are this class's own and win the key.
    #
    # **It recorded the module's declared POINTERS here too and no longer does.**  That
    # set was read in one place -- a reuser asking whether a symbol was importable from
    # the base -- and the answer it gave was a snapshot of one moment in another
    # module's walk.  Where a symbol is importable from is a fact about two DOCUMENTS,
    # so ``emit.resolve`` answers it off the target's finished symbol table and its
    # :attr:`Module.imported` record (:attr:`Target.imports`).
    #
    # **A UNION BASE records one too, and what it is NOT allowed to do is CROSS A
    # MODULE BOUNDARY.**  §5's ``$ref`` row at CONJ decides a union root by name --
    # "where it is not a class declaring fields -- a scalar, an enum, a container, or a
    # UNION ROOT, whose instance is one of its branches -- it is not a class a model can
    # extend" -- and that is a statement about a REUSER in another document.  Inside the
    # declaring module the base's shape is exactly what §4's "a branch composes its own
    # with them" needs: a branch class subclasses the base, so the base's declarations
    # and decided fields are what it inherits.  So the record is written here for every
    # class and ``emit.resolve`` is what declines to hand a union base's across, keyed
    # on :attr:`codegen.ir.ClassDecl.branches` -- the fact that says the instance is one
    # of the branches, read where the :class:`Target` is built.
    mod.shapes[pointer] = replace(
        shape,
        decided={**shape.decided, **{p.wire: p for p in props}},
        description=described,
        # TRANSITIVE for :attr:`Shape.decided`'s reason: a subclass of THIS class reads
        # one value rather than walking a chain of base documents to find who last
        # stated an ``additionalProperties``.
        extra=resolved_extra,
    )
    collision = mod.declare(pointer, declaration)
    if collision is not None:
        return collision
    return pointer


def _parsed_property(declaration: Any, at: str, mod: Module) -> nodes.Node | Refusal:
    """One property DECLARATION as the node it states, at the pointer it was declared at.

    The shape guard that stood inside :func:`fields` -- "property is not a schema" -- is
    here, because a property map reaching that function is a map of NODES now and a node
    is a schema by construction.  A VERDICT: a property that is not a schema is a
    malformed document, which is a property of the document (§4).
    """
    if not isinstance(declaration, Mapping):
        return Refusal("properties", at, "property is not a schema", kind=Kind.VERDICT)
    return schema.parse(declaration, pointer=at, position=Position.PROP, source=mod.source)


def lower_object(
    node: nodes.Object,
    mod: Module,
    *,
    bases: tuple[ir.TypeRef, ...] = (),
    inherits: "Shape | None" = None,
) -> str | Refusal:
    """Append the class for an object NODE, children first, and return its POINTER.

    **Converted to node fields** for everything structural: the properties are the child
    nodes the parser built at PROP, in the document's own key order; the extras store is
    :attr:`nodes.Object.extras`; ``propertyNames`` is :attr:`nodes.Object.key`; the type
    word is :attr:`nodes.Object.word` and the word an enclosing node applies to the same
    instance is :attr:`nodes.Base.applied`, which is what ``mod.object_constrained`` was
    read as per node.  The ADMISSION SCREEN is :attr:`nodes.Base.declares` at the node's
    own position and the ``required`` shape is :attr:`nodes.Base.faults`, which §4 makes
    the parser's; :class:`Shape` takes :attr:`nodes.Base.declared`, the property
    DECLARATIONS, because that is what §2's intersection rule merges.

    ``bases`` is what a COMPOSITION and a union BRANCH need and a leaf object does not,
    and it defaults to the leaf's answer -- no base, so the base is ``AdCPBaseModel`` --
    so the object row's call sites are unchanged and so is every module they emit.  It is
    :class:`codegen.ir.ClassDecl`'s own.  Two others are gone: ``decided``, with the union
    row's private ``const`` lowering (:func:`fields` says why), and ``body_lines``, with
    the text itself (§7) -- a rule is :attr:`Rules.rules` and a union base's facts are
    :func:`declare_object`'s own three arguments.
    """
    # D6's six families are handled HERE and not refused: a rule attaches to the
    # nearest class, so a node with fields is the only node that can carry one.  The
    # reading is :func:`rules_at`'s, which is also where the TUPLE is written
    # (:func:`declare_object`) -- so this row and the ``allOf`` row and a union branch
    # all admit the same keywords and all write the same rule.
    pointer, position = node.pointer, node.position
    stated = rules_at(node, position=position)
    refused = check_keywords(
        node,
        # The cells an OBJECT node consumes, which is what is left of a ``handled``
        # set once the table admits everything it used to carry for admission alone.
        {
            "type",
            "properties",
            "required",
            "additionalProperties",
            "propertyNames",
            *stated.screen,
        },
        mod=mod,
    )
    if refused is not None:
        return refused
    declared = node.word
    if declared != "object" and not (declared is None and node.applied == "object"):
        # A node carrying ``properties`` and no ``type`` ADMITS A NON-OBJECT: JSON
        # Schema applies ``properties`` only to objects and asserts nothing about
        # anything else, so ``{"properties": {"a": {"type": "string"}}, "required":
        # ["a"]}`` admits ``"hello"`` and ``42`` -- measured with ``jsonschema`` on
        # exactly that node.  No class can, so the model is NARROWER than its
        # document, which is the defect P3 removes.
        #
        # This condition read ``in (None, "object")`` and 0 of the 43 documents
        # emitted before step 5 exercise the ``None`` arm -- every one of them
        # declares ``type: object`` -- so the tolerance was latent rather than
        # relied on.  Step 5's union BRANCHES are the first population to reach it,
        # and they reach it in the worst way: the accepts check reports
        # ``model_type`` on a valid instance, which is the model refusing a payload
        # the document admits.
        #
        # **``mod.object_constrained`` is what keeps it from reading the node in
        # ISOLATION, which was the other half of the defect.**  draft-07 applies a
        # root's assertions and its combinator branch's to the SAME instance, so
        # ``{"type": "object", "oneOf": [{"properties": ...}]}`` admits only objects
        # and the branch at ``/oneOf/0`` restates nothing: there is no non-object for
        # the class to be narrower than.  This refusal fired for 11 documents whose
        # own root declares ``type: object`` three lines above the branch, and for 33
        # whose node is a PROPERTY's own schema -- where nothing constrains the value
        # and the refusal is right.  ``bundle.constrained_to_object`` is the one
        # reading of which is which.
        #
        # A node declaring a type that is NOT ``object`` is still refused whatever
        # encloses it: a conjunction of ``object`` and ``string`` admits nothing, and
        # a class for it would accept what the document refuses.
        return Refusal(
            "type",
            pointer,
            f"an object node must declare type: object; this one declares "
            f"{node.word if node.word is not None else '<absent>'!r} and nothing enclosing it constrains the "
            "instance to an object, so the document admits a non-object that no class can",
            kind=Kind.VERDICT,
        )
    if not node.properties:
        return Refusal(
            "properties",
            pointer,
            "an object node with no property declared",
            kind=Kind.VERDICT,
        )
    if "required" in node.faults:
        return Refusal("required", pointer, node.faults["required"], kind=Kind.VERDICT)
    required = node.required
    built = fields(node.properties, required, pointer, mod, distinct=stated.distinct)
    if isinstance(built, Refusal):
        return built
    return declare_object(
        node,
        pointer,
        mod,
        built,
        # :attr:`nodes.Base.declared` is the property DECLARATIONS, which is what a
        # :class:`Shape` is: §2's intersection rule merges declarations of one property
        # and §4 "Names" reads a branch's own ``const`` pin off one.
        # **``extra`` is the one thing this row INHERITS, and §5's
        # ``additionalProperties`` row is why it has to** (2026-10-29): the branch arm of
        # ``lower.union`` reaches this row for a branch whose base declares no property,
        # and a base declaring none can still have resolved an ``allow`` -- a root
        # stating ``additionalProperties: true`` beside its combinator and no
        # ``properties``.  Left out, the class states nothing and pydantic's
        # ``model_config`` merge decides, which is the clobber :attr:`Shape.extra`
        # records.  Nothing else of a base is read here, because a base that declares a
        # property sends the branch to ``lower_composition`` instead.
        Shape(
            node.declared,
            frozenset(required),
            extra=None if inherits is None else inherits.extra,
        ),
        position,
        extras=node.extras,
        bases=bases,
    )


# --------------------------------------------------------------------------- #
# the conjunct reader, which two rows read and therefore neither owns
# --------------------------------------------------------------------------- #

#: What a conjunct may carry and still be an inline object declaring fields.
#: ``additionalProperties`` is absent on purpose: D8 derives ``extra`` from the
#: ROOT's, and a conjunct carrying a second one would be a second source for one
#: class attribute.  There are 0 such conjuncts over the population, so this
#: refuses rather than choosing between them.
INLINE = frozenset({"type", "properties", "required"})

#: **A conjunct whose whole content is a VALUE SET**, which section 5's ``enum`` row at CONJ
#: decides: "beside a ``$ref`` whose target is an enumeration -> section 2's intersection of
#: the two vocabularies, rendered as a ``Literal`` over the TARGET's MEMBERS".
#:
#: Both spellings, because :func:`_as_enum` is the one reading of them -- "a ``const`` is a
#: one-member ``enum``, and that is a rewrite rather than a rung" -- so the intersection is
#: ONE computation over ``const`` vs ``const``, ``const`` vs ``enum`` and ``enum`` vs
#: ``enum``, exactly as the restatement predicate makes it.
#:
#: **Population ONE, and that is measured over the whole shape rather than over this
#: keyword** (``adcp-client-python-10l.84``): of every ``allOf`` in the bundle whose
#: conjuncts are a bare ``$ref`` plus an inline conjunct stating none of ``type``,
#: ``properties``, ``required``, ``additionalProperties`` or ``allOf`` -- 186 sites --
#: ``if``/``then`` is 142, ``not`` 34, ``anyOf`` 3, ``oneOf`` 3, ``else``/``if``/``then``
#: 2, ``errorMessage`` with ``not`` 1, and ``enum`` **1**.  Every one but the ``enum`` is a
#: rule or a combinator and reaches a reader already (:func:`_a_rule_the_target_states`,
#: ``lower.rules.on_a_value``, the combinator arm), so this is the only value-level
#: conjunct the bundle states and ``const`` is the arm with no population -- written
#: because :func:`_as_enum` makes it the same arm and leaving it out would be a second
#: reading of a pin.
_A_VALUE_SET = frozenset({"enum", "const"})

#: What a conjunct may carry BESIDE its fields and its rules, each part lowered by the
#: decision covering it.  Section 5 decides both, per keyword and at CONJ:
#:
#: * ``additionalProperties`` -- "CONJ -> ``true`` is the identity and contributes
#:   nothing, ``false`` on any conjunct closes the composed object, and two typed ones
#:   intersect their value schemas; a typed conjunct beside a ``true`` one is a widening
#:   and refuses."  Measured over the 1,054 portable documents: **5 conjuncts state the
#:   keyword and all 5 state ``true``**, so the identity is the only reading with a
#:   population and the other three are not written.  A conjunct stating anything else
#:   refuses, as a DEFERRAL naming the clause -- the obstruction is unwritten code, not
#:   the document.  (``INLINE`` left the keyword out on the ground that a conjunct
#:   carrying one would be a second source for one class attribute, which is true of
#:   ``false`` and of a typed value and is not true of the identity.)
#: * ``allOf`` -- section 5's ``allOf`` row, "CONJ -> the same rule applied to the
#:   conjunct's own conjuncts".  A conjunct IS a node, so one carrying its own conjunct
#:   list contributes what those contribute, at their own pointers.  Measured: **3 sites
#:   over 3 documents** -- ``adagents.json`` at
#:   ``/oneOf/1/properties/formats/items/allOf/1``,
#:   ``core/demographic-targeting-intent.json`` at ``/properties/age/allOf/1`` and
#:   ``core/geo-delivery-metrics.json`` at ``/allOf/1`` -- and every nested conjunct of
#:   all three states ``if``/``then`` and nothing else.
CONJ_COMPOSES = frozenset({"additionalProperties", "allOf"})

#: What the composing node itself may carry beside its conjunct list.
#:
#: D6's rule families are NOT listed here and are added per node by
#: :func:`rules_at`, because the admissible set is a function of the node: a
#: ``oneOf``/``anyOf`` is a rule only where every branch is ``required``-only, and a
#: combinator of shapes admitted here would emit a class that drops it silently.
COMPOSING = frozenset({"type", "allOf", "properties", "required", "additionalProperties"})

#: The two combinators, asked about by name because a composing node can carry one.
_COMBINATORS = ("oneOf", "anyOf")


@dataclass(frozen=True)
class UnionBase:
    """§4's facts a union BASE carries and no other class does, as one argument.

    :func:`declare_object` already takes the four separately, because it is the one
    funnel every class passes through and a union base is one of them.  This carries
    them across :func:`lower_composition`, which is the reader §5's union row names for
    the root's own siblings -- "every keyword beside the combinator compiles onto the
    base ... so they compile as they would on any class -- fields, ``extra``, bases,
    rules" -- and the ``allOf`` row's "beside a union → the same, onto the base".

    One carrier rather than four parameters, for :class:`Rules`' reason: the four are
    read off one reading of the union node, and a caller that passed three of them
    would have declared a base that dispatches to nothing.  Its presence is also what
    tells that function the combinator beside the conjuncts is the CALLER's business --
    ``lower.union`` is declaring the branches -- rather than the unreportable
    conjunction :func:`_refuse_a_combinator_of_shapes` refuses.
    """

    #: The names the ROOT requires, as opposed to the ones that select a branch.
    root_required: tuple[str, ...]
    #: §4's derived dispatch property, empty where the branches pin none.
    discriminator: str
    #: ``oneOf`` or ``anyOf`` -- the keyword a runtime refusal has to name.
    combinator: str
    #: The branch classes, by pointer until ``lower/names.py`` binds them.
    branches: tuple[ir.TypeRef, ...]


def _refuse_a_combinator_of_shapes(
    node: "nodes.Base", screen: frozenset[str]
) -> Refusal | None:
    """A node that COMPOSES and also carries a combinator of SHAPES.

    Both halves are conjunctions with the same instance in draft-07 -- that is D7's own
    wording for ``allOf`` -- and a class can carry the conjuncts, as bases and as fields,
    while nothing on a class carries the combinator: the branches are satisfied by SOME
    instance, so neither a base nor a field states one.  So this is ``union.ROOT_CONJUNCTS``
    read from the other side, and the refusal is the same shape: emitting it needs a row
    that can NAME the conjunction of a conjunct list with a branch list, and there is no
    JSON pointer to that conjunction for the class to name.

    **Asked of ``rules_at``'s own screen and not of a second predicate.**  A
    ``oneOf``/``anyOf`` is a RULE where every branch states only which keys are present
    and a union of shapes otherwise; ``rules.presence_only`` is that one test and
    :func:`rules_at` subtracts the two combinators from the screen when it fails.
    Reading the screen is how this row asks the question without importing a sibling
    lowering (D13), and it is why there is no second reading to drift from.

    **What this changes is the REASON and not the accepted set.**  A combinator the screen
    subtracted was already refused by ``check_keywords`` below -- with
    ``DEFERRED_TO_A_LATER_ROW``, which promises a row for a position that needs a
    pointer no document has.

    **The one document this measured is gone, and §5's "A union of presence-only
    branches that also forbid" (2026-10-27) is what took it.**
    ``creative/list-creatives-response.json`` ``#/properties/creatives/items`` was the
    deferred population here, and its two branches are ``{"required": [...], "not":
    {...}}`` -- every one of which constrains only which keys are present, so what sent
    it down this path was the branch reading admitting ``{"required"}`` ALONE.
    ``schema.presence_clause`` now reads both halves of such a branch and the node is a
    rule, which released the document onto its next keyword (a VERDICT at
    ``#/properties/creatives/items/properties/assets`` on ``additionalProperties``).
    The widening moved ``rules.presence_only`` and with it
    ``populations.states_an_object_rule``, a row's selector, which is why it was a change
    to a population rather than to this row -- it was made as one, and this row's
    accepted set did not move: the refusal fires 0 times on the 1,054 portable documents
    before and after.

    **THE KIND IS THE PARSER'S FIRST, and the screen reading second**
    (``adcp-client-python-10l.37``).  A node whose combinator sits in an ``allOf``
    CONJUNCT states it about the same instance -- draft-07 conjoins a conjunct with the
    node that holds it -- so ``schema.parse`` classifies it a :class:`nodes.Union` and
    the keyword is NOT in :attr:`nodes.Base.declares`, which reads this node's own keys.
    Asked of ``declares`` alone this arm answered "no combinator here" and the composed
    class was built with the branch list DROPPED and nothing reported, which is the one
    outcome §2 forbids outright.  The parser's classification is the question's real
    subject -- "is this node a union nobody is declaring the branches of" -- and
    :attr:`nodes.Union.stated_at` is the pointer the document states the keyword at, so
    the refusal names where it is written rather than where it applies.

    **Its population is 0 and it is written anyway, which is the point of a backstop.**
    The one node that reached it was ``adagents.json`` at ``/oneOf/1``, whose
    ``/oneOf/1/allOf/0`` is a 6-branch ``anyOf``; ``adcp-client-python-10l.66`` landed
    §5's own answer for a branch that is ITSELF a union -- ``lower.union``'s branch loop
    recurses into ``lower_union`` with the enclosing base -- and that arm is read BEFORE
    the composing one, so such a branch no longer arrives here.  Measured after that
    merge by tracing every call: **0 of the 1,054 portable documents reach
    ``lower_composition`` with a :class:`nodes.Union` and no ``UnionBase``.**  The arm
    stays because what it refuses is not a shape the bundle happens to state but a
    CALLER that forgot the branches: a fact dropped with nothing to report it is the one
    outcome §2 does not permit at any rung, and the two arms are not duplicates -- one
    is §5's answer and this is the assertion that the answer was taken.

    :func:`kind_for` reads the cell for the kind rather than this site minting one, which
    is ``docs/plan/architecture.md`` §3's rule and holds whether or not a document is
    ever reported by it.
    """
    if isinstance(node, nodes.Union):
        return Refusal(
            node.combinator,
            node.stated_at,
            f"this node composes AND its {node.combinator} is a combinator of SHAPES "
            "whose branches nobody is declaring: section 5's row gives one class per "
            "branch over the "
            "composed bases, and the caller that declares them passes its UnionBase "
            "here.  Reached without one, the branch list would be dropped from the "
            "composed class with nothing to report it",
            kind=kind_for(node.combinator, node.position),
        )
    for keyword in _COMBINATORS:
        if keyword in node.declares and keyword not in screen:
            return Refusal(
                keyword,
                node.pointer,
                f"this node composes AND carries a {keyword} whose branches are shapes "
                "rather than presence groups (rules.presence_only), and both are "
                "conjunctions with the same instance: a class carries the conjuncts as "
                "bases and fields, and nothing on a class carries a branch list, because "
                "a branch is satisfied by SOME instance.  There is no pointer to the "
                "conjunction of the two for the class to name, which is what "
                "union.ROOT_CONJUNCTS refuses a root union's own conjuncts for",
                kind=Kind.VERDICT,
            )
    return None


def _a_rule_the_target_states(uri: str, mod: Module) -> dict | None:
    """The target's own DECLARATION where everything it states is a RULE of the composing
    node, and ``None`` where it states anything else.

    **§2's intersection, computed over DECLARATIONS, asked of a ``$ref`` conjunct.**  "An
    ``allOf`` of ``$ref``s makes those classes the bases.  Where two composed schemas
    constrain the same property, the field carries the intersection" -- and the
    intersection is a function over two DECLARATIONS, which is why ``$ref`` conjuncts and
    inline conjuncts are one list and one merge in :func:`lower_composition`.  A target
    whose root declares only rule sources declares no property to intersect and no field
    set to inherit: what it says about the instance is a RULE, and §2's "rules are
    after-validators" puts a rule on the nearest class, which a draft-07 conjunct makes
    THIS node -- exactly as an inline conjunct stating the same keywords does.  So the
    declaration joins ``conjunct_rules`` and the node keeps its own class, rather than
    reaching §5's "the target is this node's own TYPE" with a type that has no field set
    to be.

    **One reading of which keywords those are, and it is the table's.**
    :func:`declaring` says which keys constrain an instance at CONJ and
    :func:`declaration_rule_sources` says which of those compile to a rule there -- the
    two functions the inline arm's own screen asks -- so a conjunct's contribution cannot
    be decided one way by a ``$ref`` arm and another way by an inline arm.  A target
    stating ONE key the pair does not pair up falls through, because a key the rule
    families do not claim would be dropped by this arm in silence (§2).

    ``mod.resolve_node`` is the reader, which is the one place a lowering holds a target's
    schema rather than its symbol, and its scope is exactly this rule's: a no-fragment
    cross-document reference, keyed by the URI.  ``None`` for anything else -- a local
    reference, a fragment, a target that refused -- and the caller then takes §5's other
    answer, which is the safe direction.

    Measured over the 1,054 portable documents: **2 conjuncts in 2 documents**, both a
    reference to a root stating ``if``/``then`` and nothing else --
    ``core/targeting.json`` and ``core/targeting-input.json``, at ``/allOf/0`` and
    ``/allOf/1``, naming ``core/targeting-unknown-age-eligibility-constraint.json`` and
    ``core/targeting-verified-age-basis-constraint.json``.  Each of those targets is §4's
    "a root stating no schema keyword at all" read through §5's ``if`` row -- a permissive
    root model -- so taking it as a base would have given the composing class a field set
    of ``root: Any``.
    """
    stating = mod.resolve_node(uri)
    if stating is None:
        return None
    declared = set(declaring(stating, Position.CONJ))
    if not declared or declared - set(declaration_rule_sources(stating, Position.CONJ)):
        return None
    return stating


#: **Which of §5's non-class targets this one IS**, for a refusal at CONJ that has to name
#: it.  The row names four -- "a scalar, an enum, a container, or a union root, whose
#: instance is one of its branches" -- and :class:`TargetKind` tells the union root from
#: the other three, so the sentence states the kind rather than asserting flatly that the
#: target "is not a class".  That assertion is false for a union root, which is a class
#: (``BranchDispatchMixin`` plus the model base), and it is the same misreading
#: ``adcp-client-python-10l.55`` found one position over in ``lower.union._inherited``.
_NOT_A_BASE: Mapping[TargetKind, str] = {
    TargetKind.UNION: "is a union root, whose instance is one of its branches and which "
    "is therefore not a class a model can extend",
    TargetKind.ANNOTATION: "is a scalar, an enumeration, a container or a root model, "
    "which declares no field set a model can inherit",
}


def _asserted_properties(
    node: "nodes.Base", conjuncts: Sequence["nodes.Conjunct"]
) -> dict[str, list[dict]]:
    """Every DECLARATION this node and its conjuncts state about each property key.

    §2 computes an intersection over DECLARATIONS, so the question "does this node's
    statement about ``type`` admit anything a branch's does" is asked here, of the raw
    declarations, and not of decided fields -- which is also what makes it answerable
    BEFORE the field loop has run (:func:`lower_composition`'s own order).

    A LIST per key and not a merge, because the reading below needs no merge:
    ``(V1 and V2 and B)`` admits nothing as soon as ANY ``(Vi and B)`` does, so asking
    each view separately is sound and avoids computing an intersection this function has
    no reason to compute.  Flattened through a nested ``allOf`` for the reason
    ``schema.parse.applies_to_one_instance`` states: an ``allOf`` of an ``allOf``
    conjoins just the same.
    """
    out: dict[str, list[dict]] = {}

    def collect(declared: Any) -> None:
        if not isinstance(declared, Mapping):
            return
        for key, declaration in declared.items():
            if isinstance(declaration, dict):
                out.setdefault(key, []).append(declaration)

    def descend(raw: Any) -> None:
        if not isinstance(raw, Mapping):
            return
        collect(raw.get("properties"))
        nested = raw.get("allOf")
        if isinstance(nested, list):
            for one in nested:
                descend(one)

    collect(getattr(node, "declared", {}))
    for conjunct in conjuncts:
        descend(conjunct.raw)
    return out


def _surviving(
    asserted: Mapping[str, list[dict]], branches: TargetBranches
) -> TargetBranches:
    """``branches`` with every branch whose intersection with what this node asserts is
    PROVABLY empty recorded as dropped.

    §5's ``$ref`` row at CONJ: "A distributed branch whose intersection is EMPTY is
    DROPPED, and the node refuses only where every branch is: ``(A | B | C) and D`` with
    ``A and D`` empty is exactly ``(B and D) | (C and D)``, so the accepted set is
    unchanged and nothing is approximated."  Dropping an empty disjunct is an EXACT
    simplification in both directions -- it admits nothing the document admits and
    refuses nothing the document refuses -- which is why no approximation is declared
    for one and why §5's empty-intersection row says this is not the node that row is
    about.

    The drop is recorded and the list is kept whole, for the reason
    :attr:`TargetBranches.dropped` states: the branch class's pointer is its index in the
    target's own branch list, so renumbering would pair every survivor against the wrong
    branch node.

    :func:`_provably_empty` is the whole of the test, and its docstring carries why it is
    not :func:`_restatement`'s ``None``.
    """
    return replace(
        branches,
        dropped=frozenset(
            index
            for index, branch in enumerate(branches.of)
            if any(
                _provably_empty(stated, branch.declares.properties[key]) is not None
                for key, views in asserted.items()
                if key in branch.declares.properties
                for stated in views
            )
        ),
    )


def _distributes(
    where: str,
    branches: TargetBranches,
    fields_declared: Collection[str],
    conj: Kind,
) -> TargetBranches | Refusal:
    """§5's DISTRIBUTION clause, and the arms that no longer stand in front of it.

    "(A | B) and C is (A and C) | (B and C), and the node is a union whose branches each
    take one of the target's branches as a base and add the node's own fields."  The
    distribution puts the node's fields on the BASE and the branch's on the branch, which
    is two classes and one instance -- so the node's statements have to be the NODE'S OWN.
    The refusal is a DEFERRAL off ``allOf``'s own cell at CONJ: what obstructs it is
    unwritten code and not anything a document did (§9's first rule).

    **A key the node and a BRANCH both declare used to refuse here and is WRITTEN**
    (``adcp-client-python-10l.76``, and §5's own clause at ``d504150d``): "A property the
    node and the target's branch BOTH declare is one field taking §2's intersection ...
    the node's declaration does not shadow the branch's."  The screen's reading of the
    defect was right -- the base's field is the one the MRO finds, so the branch's own
    declaration was shadowed and ``core/audience-evidence.json``'s three branches all
    pinned ``type: 'resource'``, which made the base's own dispatch raise "Value
    'resource' for discriminator 'type' mapped to multiple choices".  What it had wrong is
    that there was "nothing here to intersect": the branch's DECLARATION crosses the
    module boundary on :attr:`Shape.properties`, beside the symbol and the field set, so
    §2's intersection has both sides and :func:`_intersected_at_a_branch` computes it with
    the same two functions every other restatement passes through.

    **2. A SECOND ARM STOOD HERE AND IS GONE, because the pairing gap it named is
    closed** (``adcp-client-python-10l.37``'s fourth fix, lifted here by
    ``adcp-client-python-10l.76``).  It refused a node carrying a field its OWN
    declaration does not state -- one a sibling conjunct or a base contributes -- on the
    ground that "``_base.applied_schema`` drops the outer conjunct siblings at a second
    cut", so the field was on the class and not at the branch's pointer and the pair
    reported it ``added``.  That sentence was true of the walk and is not true of it now:
    the drop is scoped to a second ``allOf`` CUT, and a ``oneOf``/``anyOf``/``then``/
    ``else`` hop moves to no other instance, so the sibling conjunct holds against the
    branch in the spelling it already has.  §8's third pairing rule followed as far as the
    pointer goes, which is what the ``not same_instance`` arm beside it already did
    through a KEY hop.

    **Measured by ABLATION rather than by reading the sentence**, which is what this arm
    cost twice over: emitted with the screen lifted, all **14 pairs of
    ``core/vendor-pricing-option.json``'s closure pass all three checks**, the five
    distributed branch pairs comparing 47-53 facts each.  With the ``applied_schema``
    scope put back and nothing else changed, the same five report exactly what this arm
    claimed -- 3 ``added`` properties, ``differs /required`` and
    ``accepts:model_refused_valid`` -- and the other nine still pass.  So the arm's
    population was one document, its reason was one line of the verifier, and the two are
    the same fact seen from both sides.

    The ``bases`` half of that arm is lifted on the same reason and has **population 0**:
    no node of the bundle reaches this function with a base and no restated key
    (``core/postal-area.json`` at ``/anyOf/0/allOf/0`` carries one and is claimed by arm 1
    above).  A base's fields come from a sibling ``$ref`` conjunct, which
    ``bundle.record`` inlines, so the walk conjoins them at the branch's pointer by the
    same descent -- and the first document to state one is graded by §8 rather than
    refused by a guess, which is loud in the direction §2 wants: an ``added`` is never
    declarable and every emitted class is graded.

    **BOTH ARMS ARE GONE, each for its own measured reason, and they left by different
    merges.**  Arm 1 refused a property this node and a target branch both declare,
    because "the branch's declaration is the target's rather than this module's, so there
    is nothing here to intersect".  ``adcp-client-python-10l.74`` computes that
    intersection (``_restatement`` decides, ``_intersection`` computes, asked in both
    directions as ``declare`` already does), so the premise is false and the refusal is
    replaced by the answer §2 always gave.  Arm 2 left for the reason above.  Nothing
    screens this clause now: a node reaching it distributes, and what it distributes TO is
    graded pair by pair.

    ``core/package-signal-targeting.json`` and ``core/product-filters.json``'s
    ``/properties/signal_targeting/items`` reached neither arm and grade clean;
    ``core/vendor-pricing-option.json`` and ``core/audience-evidence.json`` each reached
    one, and both emit.
    """
    return branches


def _the_conjuncts_own_type(
    node: "nodes.Base",
    conjoined: Sequence[tuple[str, Target, "nodes.Base"]],
    *,
    fields_declared: Collection[str],
    bases: Sequence[ir.TypeRef],
    rule_nodes: Sequence[Mapping[str, Any]],
) -> Decided | Refusal | TargetBranches:
    """§5's ``$ref`` row at CONJ where the target is NOT a class: the node's own TYPE.

    "Where it is not -- a scalar, an enum, a container, or a union root, whose instance
    is one of its branches -- it is not a class a model can extend: the target is this
    node's own TYPE, and the other conjuncts and the ``allOf``'s siblings constrain it,
    which is §2's intersection at a node that declares no fields of its own."

    So the answer is the target's symbol as this node's type, and the clause's own last
    phrase is the whole of the screen below: the row holds **at a node that declares no
    fields of its own**.  A node declaring one is a different shape -- the instance must
    be the target AND carry those properties, and a Python type that is the target
    cannot state a property.  **WHAT THE NODE DECLARES sorts the two arms, and the
    target's KIND does not** -- a census here would say which documents reached each arm
    on the day it was taken, and this one moved twice before the reading was written down.
    The two arms are:

    * the node declares no fields -- the target is this node's own type, which is the
      clause above.  An ANNOTATION target is always here, because it has no field set to
      compose with;
    * the node declares fields -- §5's distribution clause, because a UNION root has one
      field set per branch and conjunction distributes over disjunction.

    **THE 4 DISTRIBUTE, and §5's ``$ref`` row says so** (53cb6100, and
    ``adcp-client-python-10l.68``) -- 2 of them all the way, and 2 as far as
    :func:`_distributes`' two screens, which name what each still waits on: "A UNION root
    beside a node that DOES declare fields
    distributes: conjunction distributes over disjunction, so ``(A | B) and C`` is
    ``(A and C) | (B and C)``, and the node is a union whose branches each take one of the
    target's branches as a base and add the node's own fields.  Each branch of a union
    root is a class declaring fields, so this is the CONJ rule above applied once per
    branch and not a second answer."  So the answer for that shape is neither a type nor a
    refusal: it is the target's BRANCHES, handed back to :func:`lower_composition`, which
    declares this node as a union base over one subclass per branch.  Every branch takes a
    TARGET BRANCH as its base and never the union base -- subclassing the base alone is
    the widening row ``.59`` measured, because §4 part 3 gives a class that inherits
    ``_branch_models`` its OWN plain schema, so ``PackageSignalTargeting
    (SignalTargetingExpression)`` would accept ``{}`` where every branch requires
    ``signal_ref``, ``value_type`` and ``value``.

    A union target with NO branch list is the one shape left here, and it refuses by name:
    the distribution needs the branches and :attr:`Target.branches` is where the declaring
    module puts them, so an empty one is a target this run did not resolve as a union base.

    **The kind every refusal here carries is the CELL's** (``docs/plan/architecture.md``
    §3, "a refusal's kind is derived from the cell and never chosen at a raise site").
    ``allOf``'s cell at CONJ is a lowering effect -- "the same rule applied to the
    conjunct's own conjuncts" -- so :func:`kind_for` answers DEFERRED, and all four raise
    sites below read it once rather than each naming a kind.  **Two of the four hand-wrote
    ``Kind.VERDICT`` and that was §9's first mistake**: a verdict minted for unwritten code
    reports clearable work as finished, and the one for a union root beside declared fields
    carried chained verdicts with it (``adcp-client-python-10l.38``).  The other two
    hand-wrote the answer the cell gives, so their reading is unchanged and now has one
    source.

    Two more screens, each for a shape §5 decides elsewhere:

    * **TWO non-class targets** would be §2's intersection of two Python types, and §2
      computes an intersection over DECLARATIONS rather than over decided types -- there
      is no slot on an :class:`codegen.ir.TypeRef` for the conjunction of two.  0 nodes
      over the population, and the two that used to reach it were the intersection asked
      of the wrong thing: ``core/targeting.json`` and ``core/targeting-input.json``
      compose two roots stating ``if``/``then`` and nothing else, so what each contributes
      is a RULE and :func:`_a_rule_the_target_states` is where §2's intersection over
      declarations reads them.
    * **A conjunct stating a RULE beside the type** is §2's "where a rule hangs", and it
      is WRITTEN: with no class above the value the rule hangs off the value's own
      annotated type, which is :attr:`codegen.ir.TypeRef.validators`, and ``lower.rules``
      is asked both of §2's questions so that nothing here decides which half a keyword
      takes.  Re-measured over the 1,054 portable documents at
      ``adcp-client-python-10l.59``: **11 of the 35 nodes** that reach this row state a
      rule beside the type -- 10 of them a ``not``, in the three shapes §5's ``not`` row
      already separates, and 1 an inline ``if``/``then`` conjunct --
      ``core/localized-creative-asset.json`` at ``/allOf/0``, beside a ``$ref`` to
      ``AssetVariant`` -- which takes the same second half as the third shape below.  The
      three shapes, as the row that wrote them measured each:

      - **6 over a ``const`` or an ``enum``** -- a ``$ref`` to an enumeration beside
        ``not: {enum: [...]}`` -- which is a ``NotValue`` on the value's own type and the
        half this row writes.  ``core/agent-notification-config.json`` and
        ``core/agent-notification-config-state.json`` (``event_types`` items),
        ``core/assets/vast-tracker-asset.json``, ``core/assets/daast-tracker-asset.json``,
        ``core/macro-resolution-capability.json`` and
        ``core/delivery-metric-aggregate.json``.
      - **2 over ``required``** -- ``core/canonical-product.json`` and
        ``core/product.json``, whose ``publisher_properties`` items state
        ``not: {"required": ["publisher_domains"]}`` beside a union root -- which §5's row
        decides as ``ForbiddenGroups``, a rule on a CLASS this node does not have.  **§2's
        clause of 2026-10-28 is what these two were waiting for** and it is not a fourth
        kind: "a value-level rule may state which KEYS the value supplied, and the three
        kinds above are not the limit ... at a position with no class above it, the value
        *is* the object, so ``ForbiddenGroups``, ``RequiredGroups`` and ``PresenceGroups``
        are admissible there as ``_runtime.ValueRule``s".  So the rule hangs on
        ``PublisherPropertySelector``, this node's own type, and
        ``lower.rules.as_the_object`` is the one reading of which of a class's rules may
        -- ``isinstance(rule, ValueRule)``, a property of the kind.  The refusal these two
        carried asked for "a value-level presence kind that section 2 does not name";
        nothing was missing but the sentence (``adcp-client-python-10l.63``).
      - **1 over another shape** -- ``core/budget-allocation.json``'s
        ``optimization_goals`` items -- which is §5's ``not`` row's own last clause,
        "nothing on the model; the schema half answers and the ceiling is named", and the
        same answer ``lower.scalars`` gives the same statement beside a scalar's own type.
    """
    conj = kind_for("allOf", Position.CONJ)
    if len(conjoined) > 1:
        return Refusal(
            "allOf",
            conjoined[1][0],
            "two conjuncts resolve to something that is not a class a model can extend -- "
            + ", ".join(f"{t.symbol} ({t.kind})" for _, t, _n in conjoined)
            + " -- so section 5's $ref row at CONJ makes each of them this node's own "
            "TYPE and the node has one type: the conjunction of two decided types is "
            "section 2's intersection, which is computed over DECLARATIONS and has no "
            "slot on an ir.TypeRef",
            kind=conj,
        )
    where, target, _reference = conjoined[0]
    symbol = target.symbol
    if fields_declared or bases:
        # **§5's DISTRIBUTION clause, and the kind of the target is what selects it.**
        # A union root is the one non-class target whose own content is a DISJUNCTION, so
        # it is the one the conjunction can be distributed over; a scalar, an enumeration
        # and a container state one thing about the instance and there is nothing to
        # distribute, which is why the sentence below still refuses those.
        if target.kind is TargetKind.UNION and target.branches is not None:
            return _distributes(where, target.branches, fields_declared, conj)
        return Refusal(
            "allOf",
            where,
            f"{symbol} {_NOT_A_BASE[target.kind]}, so section 5's $ref row at CONJ makes "
            f"it this node's own TYPE -- and that clause holds at a node declaring no "
            f"fields of its own, where this node declares {sorted(fields_declared)} and "
            f"composes {[b.path for b in bases]}: the instance must be {symbol} AND carry "
            "those properties, and a Python type that IS the target has no slot for a "
            "property",
            kind=conj,
        )
    # **§2's "Where a rule hangs", read at CONJ**: one conjunct states the TYPE and
    # another a RULE, so §2's intersection has to compose the two before either reaches
    # a :class:`codegen.ir.TypeRef` -- and with no class above the value, the half that
    # answers is "the rule hangs off the value's own annotated type as an
    # after-validator", which is :attr:`codegen.ir.TypeRef.validators`.
    #
    # **``lower.rules`` is asked BOTH of §2's questions and nothing here decides which
    # half a keyword takes**, which is that module's own rule ("one reader decides which
    # of the two a document's statement reaches and the two cannot both claim it") and
    # is why there is no reading of the ``not`` in this function: :func:`rules_at` is the
    # class half and ``on_a_value`` is the value half, and the answer is which of them
    # came back non-empty.  The deferred import is :func:`rules_at`'s own, for the cycle
    # D13 fixes.
    from codegen.lower import rules as lower_rules

    beside: dict[str, Any] = {}
    for one in rule_nodes:
        for key, stating in one.items():
            if key == "additionalProperties" and stating is True:
                # §5's ``additionalProperties`` row at CONJ: "``true`` is the identity and
                # contributes nothing".  The conjunct arm above admits no other value.
                continue
            if key in beside:
                # Two conjuncts stating one rule keyword: the merge is §2's intersection
                # of two rule statements, which no row writes -- and taking either would
                # DROP the other silently, which §2 forbids ("nothing is approximated by
                # silence").  0 sites over the portable population; written so the first
                # one is loud.
                return Refusal(
                    "allOf",
                    where,
                    f"two conjuncts state {key!r} beside {symbol}, this node's own TYPE "
                    "(section 5's $ref row at CONJ): the conjunction of two rule "
                    "statements about one value is section 2's intersection, which is "
                    "computed over DECLARATIONS, and reading either alone would drop the "
                    "other without declaring it",
                    kind=conj,
                )
            beside[key] = stating
    if beside:
        # §2's clause of 2026-10-28, which is what this position needed and the reason
        # the two documents below stopped refusing: "a value-level rule may state which
        # KEYS the value supplied, and the three kinds above are not the limit ... at a
        # position with no class above it, the value IS the object, so ForbiddenGroups,
        # RequiredGroups and PresenceGroups are admissible there as _runtime.ValueRules
        # -- 'a callable on the value, and all it is' -- without a new kind".  So a rule
        # the CLASS half wrote still hangs here, on the value's own annotated type, and
        # ``lower.rules.as_the_object`` is the one reading of which of them may: the test
        # is ``isinstance(rule, ValueRule)``, a property of the KIND, so this arm carries
        # no list of the kinds §2's clause names.
        #
        # 2 sites over the portable population, both a ``$ref`` to
        # ``core/publisher-property-selector.json`` beside
        # ``not: {"required": ["publisher_domains"]}``:
        # ``core/canonical-product.json`` and ``core/product.json``, at
        # ``/properties/publisher_properties/items/allOf/0``, each now carrying
        # ``ForbiddenGroups((('publisher_domains',),))`` on ``PublisherPropertySelector``.
        at_the_value = lower_rules.as_the_object(
            rules_at(node, *rule_nodes, position=node.position).rules
        )
        if at_the_value.declined:
            # A kind that is NOT a callable on the value: it reads the keys an instance
            # supplied through a class, so it has nowhere to live at a position with no
            # class, and §2 admits no drop by silence.  0 sites over the portable
            # population -- every rule this arm lowers is one of §2's clause's three --
            # so this is written so the first one is loud, exactly as the two-conjuncts
            # arm above is.  ``UniqueItems`` is the instructive one: it names a SIBLING
            # field's array, which is a name the VALUE supplied and not the value.
            return Refusal(
                "allOf",
                where,
                f"{symbol} is this node's own TYPE (section 5's $ref row at CONJ) and a "
                f"conjunct states {sorted(beside)} beside it, which lowers to "
                f"{', '.join(sorted(type(r).__name__ for r in at_the_value.declined))} -- "
                "a rule on a CLASS, and this node has none.  Section 2's value-level "
                "clause admits a rule on the value's own annotated type where the KIND "
                "is a callable on the value, and this one is not: it reads the keys an "
                "instance supplied through a class, so hanging it here would drop it",
                kind=conj,
            )
        # §2's SECOND half, which is the one this position takes: the rule hangs off the
        # value's own annotated type.  An empty tuple here is §5's ``not`` row's own last
        # clause -- "Any other shape -> nothing on the model; the schema half answers and
        # the ceiling is named" -- and is the same answer ``lower.scalars`` already gives
        # for the same statement beside a scalar's own type: ``not``'s cell is
        # ``rendered=False``, so section 8 compares no fact at this pointer and the
        # document's own ``strict_validate`` is what enforces it.
        #
        # The two orders are CONCATENATED and not merged, because the two halves are
        # disjoint per keyword shape and one of them is always empty: ``on_a_value``
        # reads a statement about a VALUE (a ``not`` over a ``const`` or an ``enum``, a
        # ``contains``) and ``as_the_object`` carries a statement about which KEYS
        # arrived, and the reductions in ``lower.rules`` are what split them.  Each half
        # is already a function of the document's content (P7).
        return Decided(
            ir.TypeRef(
                symbol,
                local=True,
                validators=(
                    *lower_rules.on_a_value(beside, contains=beside.get("contains")),
                    *at_the_value.carried,
                ),
            )
        )
    return Decided(ir.TypeRef(symbol, local=True))


#: The mixin §4 puts FIRST on a union base, as the one spelling both sites name it by.
DISPATCH_MIXIN = "BranchDispatchMixin"


def dispatching_bases(bases: tuple[ir.TypeRef, ...], mod: "Module") -> tuple[ir.TypeRef, ...]:
    """``bases`` with :data:`DISPATCH_MIXIN` named FIRST, or unchanged where a base in it
    already carries the mixin.

    **§5, "The dispatch mixin is named where no base already carries it" (decided
    2026-10-29).**  The mixin has to come first so the MRO finds its
    ``__get_pydantic_core_schema__``, and a union base already carries it -- so naming it
    beside such a base puts a class before its own subclass and Python refuses to build
    the module.  **The suppression is a function of the BASE LIST and not of the route that
    reached it**, which is the one reading both routes can ask: this function is the point
    the list is built, and it is the same shape as ``base_if_none_composes`` at the same
    seam -- that one says "what the base would be if nothing composed", this one "what the
    mixin is if nothing already carries it".

    The alternative was a guard at the route, and it is wrong for §11's reason.
    ``lower.union.Enclosing`` is constructed at ONE place, inside the enclosing union's
    branch loop under the arm that claims a branch the parser classified
    :class:`nodes.Union`; a nested union reaching ``lower_union`` through the DISPATCH
    instead arrives with no carrier, and a second guard there would be a second copy of
    the reading that carrier was built to hold once.  ``Enclosing`` keeps its other job --
    the enclosing base's :class:`Shape`, so a property both declare takes §2's
    restatement rule -- which no base list states.

    **Transitive, because a base's base carries it too.**  A branch class of a union is
    declared with the union's base among its own bases, so a node composing that BRANCH
    inherits the mixin two hops up; asking only the immediate list would name it again.
    A declaration travels by POINTER in its name slot until ``lower/names.py`` binds a
    symbol (§7), so the lookup is by pointer over what this module has declared so far --
    no census over the run, and nothing outside this module is consulted.

    **A base another MODULE declares is not followed, and the population says why.**  Such
    a base arrives as an imported symbol with no declaration here to read, and the one
    shape that would need following is a conjunct whose target is a union ROOT -- which
    :func:`lower_composition` DISTRIBUTES rather than naming as a base, so the symbol that
    reaches a base list is a target's BRANCH and a branch does not carry the mixin by
    itself.  Measured: with this function in force, 0 of the 1,006 modules of the tree has
    an inconsistent MRO, asserted by importing every one of them.
    """
    if any(_carries_the_mixin(base, mod, frozenset()) for base in bases):
        return bases
    mod.imports.add((ir.BASE_MODULE, DISPATCH_MIXIN))
    return (ir.TypeRef(DISPATCH_MIXIN, local=True), *bases)


def _carries_the_mixin(base: ir.TypeRef, mod: "Module", seen: frozenset[str]) -> bool:
    """Does this ONE base carry :data:`DISPATCH_MIXIN`, itself or through its own bases?

    ``seen`` is the pointers already on this walk, so a declaration naming itself among
    its bases answers once rather than recurring.  The population is 0 -- a base is always
    an ancestor -- and it is written because a fold with no base case is a crash and §9
    says a crash is not an outcome.
    """
    if base.path == DISPATCH_MIXIN:
        return True
    if base.path in seen:
        return False
    declared = next(
        (
            d
            for d in mod.declarations
            if isinstance(d, ir.ClassDecl) and d.name == base.path
        ),
        None,
    )
    if declared is None:
        return False
    return any(
        _carries_the_mixin(b, mod, seen | {base.path}) for b in declared.bases
    )


def _the_vocabularys_intersection(
    decided: Decided,
    stated: Sequence[tuple[str, Mapping[str, Any]]],
    reference: "nodes.Reference",
    mod: "Module",
) -> Decided | Refusal:
    """§5's ``enum`` row at CONJ: the TYPE :func:`_the_conjuncts_own_type` decided,
    narrowed to the intersection of the target's vocabulary with the conjuncts' own.

    "Beside a ``$ref`` whose target is an enumeration → §2's intersection of the two
    vocabularies, rendered as a ``Literal`` over the TARGET's MEMBERS and not over their
    raw values.  The two dump identically -- ``{"enum": [the members], "type":
    "string"}`` -- so §8 compares the same fact either way, and the member form keeps the
    imported symbol a caller can name: where §8 cannot tell two renderings apart, DX
    decides."

    **The intersection is computed over DECLARATIONS and the ORDER is the TARGET'S**, both
    of which are §2's and neither of which is a preference.  The declaration is read
    through :meth:`Module.resolve_node` -- the one reader §2's intersection rule has for a
    reference -- because the symbol the reference was bound to carries no vocabulary, and
    the whole of this row is a fact about the two value sets.  The order is the target's so
    that the rendered annotation is a function of the document's content (P7) and not of
    which conjunct the walk read first; the conjuncts are a FILTER over it.

    **``const`` and ``enum`` are one computation** (:func:`_as_enum`, and
    :data:`_A_VALUE_SET` says why): a ``const`` is a one-member vocabulary, so a pin
    narrowing a target's members and a vocabulary narrowing them are the same intersection
    asked twice.

    Three refusals, each by name:

    * **the target states no vocabulary** -- a value set beside a scalar, a container or a
      union root.  The intersection has nothing to intersect WITH: §2 computes it over
      declarations, and a declaration that enumerates nothing offers no member set, so
      reading the conjunct's own vocabulary alone would state a fact the target does not
      and reading neither would drop the document's.  0 sites.
    * **the intersection is EMPTY** -- §5(b)'s empty-intersection row, which is the rung
      :data:`_RUNG_AT` already puts on this very cell: "two disjoint enums.  The node
      admits nothing, which is a contradiction in the document.  Rung TOP."  Attribution
      upstream, and reported here rather than widened because the node admits no instance
      at all.  0 sites.
    * **two surviving members spell ONE Python name** -- the rendering names a MEMBER of
      the target's class, so a collision means the target did not render as a class at all
      (§5's ``enum`` row: two colliding spellings → a ``Literal`` and not an enum) and
      ``Symbol.NAME`` would name nothing.  Read with the SAME ``member_name`` the
      declaring side minted the names with, which is why that function is shared rather
      than re-derived.  0 sites.

    Where the intersection is the target's whole vocabulary the type is returned
    UNCHANGED: the conjunct restates what the target already says, narrows nothing, and a
    ``Literal`` over every member would render the same acceptance under a second spelling
    (§1's one way to reach one class).
    """
    from codegen.lower.enum import member_name

    where = stated[0][0]
    target = mod.resolve_node(reference.uri)
    members = target.get("enum") if isinstance(target, dict) else None
    if not isinstance(members, list) or not members:
        return Refusal(
            "enum",
            where,
            f"a conjunct states a value set beside {reference.uri!r}, whose declaration "
            "enumerates nothing: section 5's enum row at CONJ is section 2's intersection of "
            "TWO vocabularies and there is only one here, so neither reading is the "
            "document's -- the conjunct's alone states a set the target does not, and "
            "dropping it loses the set the document does state",
            kind=kind_for("enum", Position.CONJ),
        )
    surviving = list(members)
    for _at, conjunct in stated:
        vocabulary = _as_enum(_constraining(conjunct)).get("enum")
        if not isinstance(vocabulary, list):
            return Refusal(
                "enum",
                where,
                f"a conjunct's value set is {vocabulary!r}, not a list of members",
                kind=Kind.VERDICT,
            )
        surviving = [m for m in surviving if m in vocabulary]
    if not surviving:
        return Refusal(
            "enum",
            where,
            f"the conjunct's value set and {reference.uri!r}'s intersect to nothing: "
            "section 5's empty-intersection row says the node admits no instance at all, "
            "which is a contradiction in the document and not a fact a model can widen to",
            kind=kind_for("enum", Position.CONJ),
        )
    if surviving == list(members):
        return decided
    names = [member_name(m) for m in surviving]
    if len(set(names)) != len(names):
        return Refusal(
            "enum",
            where,
            f"two of the surviving members {surviving!r} spell one Python name "
            f"{sorted(names)!r}, so {reference.uri!r} did not render as an enum class "
            "(section 5's enum row gives a colliding pair a Literal of the values) and "
            "there is no member for this row's Literal to name",
            kind=kind_for("enum", Position.CONJ),
        )
    return replace(decided, type=replace(decided.type, members=tuple(names)))


def _conjunct_base(
    conjunct: Mapping[str, Any], where: str, mod: "Module"
) -> tuple[Target, "nodes.Reference"] | Refusal:
    """The :class:`Target` a ``$ref`` conjunct names, by whichever of the TWO resolutions
    its DOCUMENT HALF makes it, **and the NODE it named it with**.

    The node travels beside the target because the one row that distributes a union target
    declares a class per branch, and a class is declared FROM a node
    (:func:`declare_object` reads its ``extra``, its ``description`` and its rule
    sources).  The node of this document that stands for a distributed branch is this very
    conjunct -- the reference whose target holds the branch -- which states nothing of its
    own, so every fact the branch class carries comes from its two bases.  Returned rather
    than re-parsed by the caller, because ``schema.parse`` is the one reader of a raw
    mapping (§3) and parsing it twice is two readings of one node.

    **The DOCUMENT HALF decides which resolution this is, and the reading is the
    PARSER'S** -- ``bundle.split_ref``'s one reading of the ``#``, taken off
    :attr:`nodes.Reference.head` as a field.  ``$ref`` closes a node in ``schema.parse``'s
    arm order ("draft-07 ignores every sibling"), so parsing the conjunct at its own
    pointer is how this arm gets the two halves without reading a delimiter itself, and
    the inert siblings the caller has already reported travel on the node unread.

    This is the route ``adcp-client-python-10l.43`` is: ``lower_composition``'s conjunct
    arm asked :meth:`Module.target` for every reference, and a LOCAL one -- a pointer into
    the document being written -- is not a binding at all.  The run answers such a site
    by name (``emit.answer``'s local arm), so the conjunct arm got that sentence as a
    document's VERDICT, which charged two documents for a routing gap:
    ``core/account-identity-change-preview.json`` at
    ``/definitions/nonblocking_impacts/items/allOf/0`` and ``core/registry-event.json``
    at ``/oneOf/0/properties/payload/allOf/0``, plus 2 more through the chain.  A local
    pointer as a conjunct is an ordinary draft-07 document and the walk already has the
    resolver: :func:`local_reference`, which ``lower.references.lower`` reaches by
    branching on the same field.

    **Both arms hand back ONE carrier**, which is the arrangement ``lower.union._inherited``
    already has: :func:`local_target` wraps the two records :func:`declare_object` wrote
    for a node of THIS module in the same :class:`Target` the run built for a node of
    another, so the kind is one derivation (:func:`target_kind`) and the shape one
    invariant (:attr:`Target.declares`), and §5's ``$ref`` row at CONJ reads them once.

    **The IMPORT is recorded here, because this is the one place that knows which
    resolution it made.**  A remote target's symbol is one this module imports; a local
    one's is one this module DECLARES, and recording an import for it would name
    :attr:`Target.module` -- empty for a local target -- as the module to import from.
    The caller's two sub-arms differ in what they do with the symbol and not in whether
    they need it, so one call covers both, exactly as ``lower.references.lower`` makes it.

    **``decided.type.local`` is asked FIRST, before the lookup**, for
    ``_inherited``'s own measured reason: a container's :attr:`ir.TypeRef.path` is ``""``,
    which is also the pointer of the document's ROOT, so a lookup keyed on the path would
    hand this conjunct the root's own class.  Population 0 over the portable set -- every
    local pointer reached through a conjunct names an object entry -- so the arm refuses by
    name rather than being left out.
    """
    parsed = schema.parse(conjunct, pointer=where, position=Position.CONJ, source=mod.source)
    if not isinstance(parsed, nodes.Reference):
        # The caller's gate is ``keys == {"$ref"}`` and ``schema.parse`` selects the
        # reference arm on ``"$ref" in raw`` before any other, so the two readings can
        # only disagree if one of them changes -- a defect in this compiler and not an
        # outcome of any document (``docs/plan/architecture.md`` §2), so it raises the one
        # exception no layer catches rather than refusing a document.
        raise BuildFailure(
            f"{where}: a conjunct whose only declaring key is $ref parsed as "
            f"{type(parsed).__name__}, so compiler.lower_composition's conjunct screen and "
            "schema.parse's arm order disagree about what a $ref node is"
        )
    if parsed.head or parsed.into not in mod.local:
        # **A local spelling that names NO NODE OF THIS DOCUMENT is not a local reference
        # of this document at all** (``adcp-client-python-97w``).  It is a reference the
        # COMPOSITION carried in: §5's ``properties`` row composes two object declarations
        # as an ``allOf`` of the two, so where a base spells its half as a pointer into its
        # own text, :func:`_intersection` plants that very pointer as a conjunct of a node
        # belonging to this document -- and ``emit.based_edges`` is what resolves it, by
        # re-stating it as the fragment reference into the base that it is.
        # :meth:`Module.target` already has the arm (:attr:`inherited_targets`, asked by
        # URI for exactly the sites a composition produces).
        #
        # **Asked of :attr:`local`, which is the pointers a local reference of this
        # document can REACH, and never of the pointer's spelling**: the question is
        # whether this document holds the node, which only the document can answer, and
        # :func:`local_reference` asks the same map one line in.  Routed here rather than
        # on ``local_reference``'s refusal, so the two resolvers keep one condition each
        # and neither is reached by the other's failure.
        #
        # Measured over the 1,054 portable documents: 0 sites move off the local arm that
        # the document's own text spells -- row ``10l.43``'s two,
        # ``core/account-identity-change-preview.json#/definitions/impact`` and
        # ``core/registry-event.json#/$defs/propertyPayload``, both name a node of their
        # own document and keep the local resolution.
        target = mod.target(parsed.uri, where)
        if isinstance(target, Refusal):
            return target
        mod.importing(target.symbol, target.where)
        return target, parsed
    decided = local_reference(mod, parsed.into, where)
    if isinstance(decided, Refusal):
        return decided
    if not decided.type.local:
        return Refusal(
            "$ref",
            where,
            f"this conjunct references {parsed.uri}, which the walk lowers to the "
            f"annotation {decided.type.path or decided.type.container or 'Any'!r} rather "
            "than to a symbol: section 5's $ref row at CONJ gives a BASE where the target "
            "is a class and this node's own TYPE where it is not, and an annotation with "
            "no name is neither -- there is no symbol for either arm to carry",
            # **THE KIND IS THE CELL'S AND NOT THIS SITE'S** (``docs/plan/architecture.md``
            # §3, "a refusal's kind is derived from the cell and never chosen at a raise
            # site").  ``$ref`` at CONJ compiles to a type, so its cell is a LOWERING
            # effect whose answer for this shape is unwritten, and :func:`kind_for` reads
            # DEFERRED -- which is also the honest kind: §9's first rule says a refusal for
            # code nobody has written is a deferral, and what obstructs this arm is the
            # unwritten half of §5's ``$ref`` row at CONJ, not anything the document did.
            kind=kind_for("$ref", Position.CONJ),
        )
    return local_target(mod, decided.type.path), parsed


def lower_composition(
    node: "nodes.Base",
    mod: Module,
    *,
    bases: tuple[ir.TypeRef, ...] = (),
    union: UnionBase | None = None,
    inherits: Shape | None = None,
    base_if_none_composes: ir.TypeRef | None = None,
) -> str | Decided | Refusal:
    """Append the class for an ``allOf`` node and return its POINTER.

    **CONVERTED to node fields, and ``schema/nodes.py`` says which half of this row stays
    at the DECLARATION level and why**: §6 keeps ``restatement``, ``intersection`` and
    ``at_least_as_tight`` as pure functions over DECLARATIONS, because the merge of two
    declarations of one property has to be parsed as one node and not composed out of two
    decided ones -- so a :class:`nodes.Conjunct` is a declaration by the design's own
    decision, and so is :attr:`nodes.Base.declared`, this node's own property map.  The
    node's OWN facts are fields: :attr:`nodes.Composition.word`,
    :attr:`nodes.Composition.required`, :attr:`nodes.Base.extra`,
    :attr:`nodes.Base.rules`, and :attr:`nodes.Base.declares` for the screen.

    The reference conjuncts become BASES, and the rest becomes fields of the node
    itself.  D2's product row, and **shared machinery rather than a lowering**: a
    union BRANCH composes at its own node too, and D13 forbids one lowering from
    importing another, so the reader that binds a conjunct list
    lives here and both rows reach it through the import they already have.  That is
    the same reason :func:`lower_object` is here and not in a lowering, and
    ``bases`` is the same parameter for the same purpose: the caller's own bases are
    prepended to the ones the conjuncts name, so a branch keeps the union base its
    ``isinstance`` depends on FIRST and gains whatever it composes after it.

    **The node need not be a root**, and this never asked that it be one: it takes
    ``(node, name, pointer, module)`` like every other lowering (D13), reads the pointer
    it is handed, and ``declare_object`` names whatever node that is.  A document ROOT
    and a composition at a property or deeper reach it through the SAME arm of
    ``emit._decide``, which is §5's "root and non-root are one path": there was a table
    of root selectors above this and §14 step 5 deleted it, because dispatching on a
    root's KIND is the second reading of the one the walk makes per node (§11).
    Measured over the 3.2 bundle: of the 67 documents whose composition this step was
    deferring, 41 carry it at a root -- all 41 counted by step 5's population and not by
    this step's -- 10 at a property and 16 deeper.

    Two things come out of one conjunct list, and a third is deliberately absent:

    * a conjunct that is a ``$ref`` and nothing else is a BASE CLASS.  D7: a base is
      DERIVED from what the document composes, so there is no marker policy and no
      filename to classify.  Anything a caller wants to ``isinstance`` against is a
      schema the document composes, which is also how ``AdcpRequest``/``AdcpResponse``
      reach a task message -- through ``index.json``'s task registry naming the
      document, never through its path;
    * a conjunct carrying ``properties`` declares fields of THIS node, because a
      draft-07 ``allOf`` conjunct applies to the same instance -- it is not a separate
      object and gets no class of its own;
    * a ``required``-only conjunct is the plan's third output here and is NOT built:
      there are **0** of them at a root over the whole bundle (measured, asserted in
      the suite), so the arm would be a derivation matching nothing, which is green
      for free and says nothing.

    Anything else refuses by name, pointer and keyword.

    **A subclass never restates an inherited field's TYPE.**  That is this module's one
    merge rule: a restatement states the field only when it NARROWS, meaning it keeps
    every keyword the inherited declaration states, with the same value, and adds at
    least one more.  A restatement that says something DIFFERENT about the instance is a
    conflict and the document is refused.  A restatement that says the same thing or
    nothing is the subclass's field by its annotations alone, over the base's own type:
    the node where the two agree, the base's decided field where the restatement states
    no constraint at all.  :func:`_restatement` is the whole of that decision, and it is
    SYMMETRIC, so there is no order-dependent "last wins" to come back to -- a generator
    that let the later conjunct win made its accepted set a function of member order.

    MEASURED over this step's 287 documents, 100 sites restate an inherited property:
    51 restate it identically, 31 state nothing but ``default`` and ``description``,
    16 point a ``$ref`` at a fragment of the base's own node, and 2 add a keyword.
    **The 31 are this step's highest-value defect** -- in the previous generated tree
    they were 31 of 42 ``Any`` fields, each one shadowing a typed base field across 15
    classes.  ``formats/canonical/responsive_creative.json`` is the control shape:
    it restates ``experimental``, ``v1_translatable`` and ``slots`` with nothing but a
    default and a description, while ``formats/canonical/_base.json`` types them
    ``boolean``, ``boolean`` and ``array``, so a restatement lowered on its own is
    ``Any | None`` shadowing a typed base field.  **Re-using the base's decided field
    makes the shadow unspellable AND carries the document's own annotation**, which
    inheriting the field entirely did not: that left the class stating the BASE's
    ``default`` and ``description`` at a pointer its own document declares, the 28
    ``differs`` of ``salesagent-j3k2l.36`` and two of them inversions.

    The same rule closes the inventory's "41 subclass fields optional where their base
    requires them" by construction: a field the subclass does not declare keeps the
    base's requiredness, because there is nothing of the subclass's to override it.  A
    field it DOES narrow keeps it too -- the inherited required set is unioned in.

    **The node's own D6 rules reach the class through** ``declare_object``, which
    writes the tuple for whatever node it is declaring -- so this row states nothing
    about rules beyond admitting the keywords.  Documents refused here on ``not``,
    ``dependencies`` or ``minProperties`` at a composing node whose mechanism was
    complete three modules away: the rule kinds, the emitter's tuple and the one
    after-validator all existed, and only the object row consulted them.

    A property the node declares only inside a conditional is merged in for the
    reason :class:`Rules` states: a rule naming a key the class has no field for
    refuses a payload the document admits.

    **``union`` and ``inherits`` are §14 step 9's union row, and both say that a UNION
    is read here rather than beside here.**  §5's union row compiles the root's
    ``properties``, ``required``, ``additionalProperties`` and ``allOf`` "onto the base
    ... as they would on any class -- fields, ``extra``, bases, rules", so the base is a
    class this function declares and :class:`UnionBase` is the four facts it carries
    beyond one.  ``inherits`` is the other half of the same sentence -- "a branch
    composes its own with them": a branch class's bases include the union base, so the
    base's declarations and decided fields are INHERITED exactly as a ``$ref``
    conjunct's are, and §2's restatement rule is what decides a branch that declares a
    property the root also declares.  Without it a branch lowered from its own node
    alone shadows the base's field, which is measurable and was measured: over the 61
    documents §14 step 9 unblocks, 135 restatements drop a ``description`` the root
    states and 79 drop a ``required`` the root states, in 14 and 4 documents.

    ``inherits`` is a :class:`Shape` and not a :class:`Target` because the base is in
    THIS module; :func:`_reused` says what that changes, which is one screen and
    nothing else.

    **``base_if_none_composes`` is :func:`declare_object`'s own sentence, made
    available to a caller that supplies a base of its own.**  That sentence is "``bases``
    is empty for a node that composes nothing, and then the base is ``AdCPBaseModel``; a
    composing row passes the symbols its ``$ref`` conjuncts bound ... and
    ``AdCPBaseModel`` arrives through them" -- and it holds because an empty ``bases``
    is what the renderer's ``custom_base_class`` answers.  A union base is the one class
    with a base of its OWN that is not a model class: ``BranchDispatchMixin`` has to come
    FIRST, so its ``__get_pydantic_core_schema__`` is the one the MRO finds.  Passing the
    model base beside it is what MRO-conflicts a root that also composes --
    ``(BranchDispatchMixin, AdCPBaseModel, AdCPVersionEnvelope, ProtocolEnvelope)`` puts
    a class before two of its own subclasses and Python refuses to build it, measured on
    ``account/get-account-financials-response.json`` and nine more.  So the caller says
    what the base would be if nothing composed, and this function -- the one place that
    knows whether anything did -- writes it only there.
    """
    # Any kind may arrive -- a hand-written probe states ``allOf`` beside a combinator and
    # the parser classifies it a ``Union``, which is §5's own arm order -- so the fields
    # read below are ``nodes.Base``'s and not the one kind this row is dispatched for.
    pointer, position = node.pointer, node.position
    # §5's ``allOf`` row BESIDE A UNION: "the same, onto the base".  A node stating both
    # is a :class:`nodes.Union` by §5's own arm order, so its conjunct list is a sibling
    # of the combinator rather than its kind -- and a conjunct is read at its own CONJ
    # pointer either way, so there is one reading of what a conjunct list contributes
    # and not one per kind that can state one.
    #
    # **The LIST is the parser's, for both kinds** (``adcp-client-python-10l.37``).  It
    # was rebuilt here out of :attr:`nodes.Union.siblings`, which was a second reading of
    # ``allOf`` and could only ever yield ``enumerate``'s indices -- and a union whose
    # combinator is borne by one of those very conjuncts composes the OTHERS, at the
    # pointers the document gives them.  :attr:`nodes.Union.conjuncts` is that list, so
    # the one place that saw the document decides which conjuncts compose.
    conjuncts: tuple[nodes.Conjunct, ...] = getattr(node, "conjuncts", ())
    # **The TYPE first, BEFORE the keyword screen**, and the order is measured rather
    # than preferred: a node stating a non-object ``type`` composes no object whatever
    # else it states, so the type is the reason and a keyword it carries is not.  It sat
    # after the screen, and :func:`check_keywords` walks ``sorted(node)`` -- so
    # ``media-buy/legacy-purchase-continuation-input.json#/properties/accepted_losses``,
    # a composing ARRAY, was reported on ``items`` with "a later D2 row does", which
    # promises a row for an array keyword at a node no array row will ever see.  The same
    # misattribution ``union.ROOT_CLAIMS`` measured at 55 of 156 and fixed the same way.
    # Measured over every node of every portable document: **4 composing nodes state a
    # non-object type and all 4 state ``array``**; all 4 already refused here, so the
    # order moves no document and changes the reported keyword for one.
    word = getattr(node, "word", None)
    if word not in (None, "object"):
        return Refusal(
            "type",
            pointer,
            f"an allOf of type {word!r} composes no object",
            kind=Kind.VERDICT,
        )
    stated = rules_at(node, position=position)
    if union is None:
        # A node that composes AND carries a combinator of shapes, where nobody is
        # declaring the branches: the conjunction of a conjunct list with a branch list
        # has no pointer for a class to name.  With ``union`` supplied the caller IS
        # declaring one class per branch (§4), each at its own ``#/<kw>/<i>`` pointer,
        # and §8's pairing rule reads a branch node under the root's siblings -- so the
        # conjunction has a pointer and a grader, which is exactly what the refusal said
        # it lacked.
        combinator_of_shapes = _refuse_a_combinator_of_shapes(node, stated.screen)
        if combinator_of_shapes is not None:
            return combinator_of_shapes
    #: **The node's own ``contains``, which §5's ``$ref`` row at CONJ counts among the
    #: siblings that constrain the target** (:attr:`nodes.Composition.contains`, and §5's
    #: "Two ARRAY declarations under one ``allOf``").  CLAIMED here and read below, which
    #: is the pair §3 requires of a lowering cell: the cell says ``contains`` lowers at
    #: CONJ, so a screen that drops it promises "a later row does" for a row that would
    #: have to be this one.  It reached that promise, measured: the merged ``dimensions``
    #: declaration of ``core/signal-coverage-forecast.json`` refused with
    #: ``DEFERRED_TO_A_LATER_ROW`` on this very keyword.
    contains = getattr(node, "contains", None)
    claimed = COMPOSING | stated.screen | ({union.combinator} if union is not None else set())
    if contains is not None:
        claimed = claimed | {"contains"}
    screened = check_keywords(node, claimed, mod=mod)
    if screened is not None:
        return screened

    conjunct_bases: list[ir.TypeRef] = []
    #: **§5's ``$ref`` row at CONJ where the target is NOT a class**: the symbol is this
    #: node's own TYPE and not a base, with the conjunct's own pointer beside it so the
    #: refusal for a shape this row does not answer can name the conjunct that carried
    #: it.  The TARGET and not its symbol alone, because the refusal for a node that
    #: declares fields has to name WHICH of §5's non-class targets this one is
    #: (:data:`_NOT_A_BASE`) and :attr:`Target.kind` is the one derivation of that.
    #: Read once, by :func:`_the_conjuncts_own_type`, after the worklist.  The parsed
    #: REFERENCE rides beside the two, because a distributed branch is declared from it
    #: (:func:`_conjunct_base`).
    conjoined: list[tuple[str, Target, nodes.Reference]] = []
    inherited: dict[str, dict] = {}
    inherited_required: set[str] = set()
    #: The ``extra`` policy the FIRST of this node's bases that resolved one resolved
    #: (:func:`stated_extra`), in the order the document composes them -- the caller's
    #: own base first and the ``$ref`` conjuncts after, which is the order
    #: :attr:`Shape.description` is gap-filled in and for that attribute's reason:
    #: ``harness._composed`` reads the composed document that way and the two halves have
    #: to read it the same.  So the value :func:`declare_object` writes where this node
    #: states no ``additionalProperties`` is the composed document's, not whichever base
    #: pydantic's ``model_config`` merge happens to reach last.
    inherited_extra: str | None = None
    #: The FIELD each inherited key came out as on the base that declares it, and the
    #: base it came from.  Read only by the annotation-only arm below, which re-uses
    #: the field rather than re-deciding the node; :attr:`Shape.decided` says why.
    inherited_fields: dict[str, ir.Field] = {}
    inherited_from: dict[str, Target] = {}
    if inherits is not None:
        # §4's "a branch composes its own with them", seeded before the conjunct list:
        # the caller's own ``bases`` already declare these keys, so they are INHERITED
        # in exactly the sense a ``$ref`` conjunct's are, and every reading below -- the
        # restatement rule, the requiredness overlay, the re-use of a decided field --
        # is the one §2 states for a base.  ``inherited_from`` is left empty on purpose:
        # the base is in this module, so there is nothing to import (:func:`_reused`).
        inherited.update(inherits.properties)
        inherited_fields.update(inherits.decided)
        inherited_required |= inherits.required
        if inherited_extra is None:
            inherited_extra = inherits.extra
    #: Every LOCAL declaration that won its key, and where it was declared.  The
    #: root's own properties and an inline conjunct's land in the SAME map,
    #: because draft-07 applies both to the same instance.
    local: dict[str, dict] = {}
    at: dict[str, str] = {}
    if "required" in node.faults:
        return Refusal("required", pointer, node.faults["required"], kind=Kind.VERDICT)
    required: set[str] = set(getattr(node, "required", ()))
    #: The conjuncts that state a RULE of this node rather than a base or fields.
    conjunct_rules: list[dict] = []
    #: **The conjuncts whose whole content is a VALUE SET** (:data:`_A_VALUE_SET`), with
    #: each one's own pointer, for §5's ``enum`` row at CONJ.  A value set constrains this
    #: node's own TYPE, so it is read after the whole list beside the reference that
    #: supplied the type -- :func:`_the_vocabularys_intersection`.
    conjunct_values: list[tuple[str, Mapping[str, Any]]] = []
    #: The description the FIRST base that states one states, for a composing node that
    #: states none of its own (:attr:`Shape.description`).  First and not last, and not
    #: a merge, because that is what ``harness._composed`` gap-fills on the document
    #: side -- ``if kw not in out`` over the conjuncts in order -- and the two halves
    #: have to read one composed document the same way.
    inherited_description: str | None = None

    def declare(key: str, node: Any, where: str) -> Refusal | None:
        prior = local.get(key)
        if prior is None:
            local[key], at[key] = node, where
            return None
        # Two local declarations of one key: the root's own and a conjunct's, or
        # two conjuncts'.  Decided by the SAME rule as a restatement of an
        # inherited field, and that rule is symmetric, so which was read first
        # cannot change the answer.  The narrower declaration wins; neither
        # narrowing the other refuses.  One site over the population:
        # ``formats/canonical/image.json`` states ``motion_level`` as a ``$ref``
        # at the root and as an ``enum`` in a conjunct, which is the enum
        # narrowing and refuses here -- the intersection needs step 3's enum
        # lowering and cannot be stated from this row.
        if _restatement(node, prior, mod.resolve_node):
            # The INTERSECTION and not the narrower node alone (section 2, :func:`_intersection`):
            # both declarations apply to the same instance, so a keyword only the wider
            # one states is still the composed node's.
            local[key], at[key] = _intersection(node, prior, mod.resolve_node), where
        elif _restatement(prior, node, mod.resolve_node) is None:
            return Refusal(
                _disagreeing(node, prior),
                where,
                f"{key!r} is declared at {at[key]} and again here, and neither "
                "declaration narrows the other",
                kind=Kind.VERDICT,
            )
        return None

    for key, sub in node.declared.items():
        conflict = declare(key, sub, f"{pointer}/properties/{key}")
        if conflict is not None:
            return conflict

    #: The conjuncts still to read, each with the pointer it sits at.  A WORKLIST
    #: rather than an ``enumerate`` because of :data:`CONJ_COMPOSES`' second entry: a
    #: conjunct carrying its own ``allOf`` pushes those conjuncts here, so ONE loop
    #: reads every depth, the keyword screen is asked once per node, and a refusal
    #: points at the pointer that carried the keyword rather than at the outermost
    #: conjunct.  Breadth-first, which is document order within each depth.
    unread: list[tuple[str, Any]] = [(c.pointer, c.raw) for c in conjuncts]
    while unread:
        where, conjunct = unread.pop(0)
        if not isinstance(conjunct, dict):
            return Refusal("allOf", where, "a conjunct that is not a schema", kind=Kind.VERDICT)
        keys = set(declaring(conjunct, Position.CONJ))
        # **A key whose CELL refuses contributes nothing to a conjunct, and the walk
        # says so.**  Section 7's ``errorMessage`` row states it for the one name that
        # occurs: "it has no Pydantic rendering, and a conjunct carrying one
        # contributes nothing, so the drop is reported rather than silent".
        # ``media-buy/sync-catalogs-request`` at ``/allOf/1`` states it beside a
        # ``not``, and ``min(keys)`` reported the document on ``errorMessage`` with
        # ``DEFERRED`` -- a deferral promising a row for a name no row can ever lower.
        #
        # Read off the cell rather than off draft-07's meta-schema, which is what this
        # asked before: the meta-schema answers "is this a keyword", and the question
        # is "does this keyword contribute anything here".  A key with NO ROW is not
        # dropped -- it refuses below, because a keyword the bundle did not use before
        # could constrain anything.
        #
        # Reported rather than silent, and reported on the MODULE rather than raised: a
        # drop is not a refusal (the document still emits) and it is not nothing (a
        # reader has to be able to see that the class does not carry the name).
        # :attr:`Module.carries_nothing` is that channel and ``emit`` prints it.
        foreign = {
            k
            for k in keys
            if (c := keywords.cell(k, Position.CONJ)) is not None
            and c.effect is keywords.Effect.REFUSE
        }
        if foreign:
            mod.carries_nothing.extend(
                f"{where}: {k}: section 7 refuses this keyword, so it constrains no "
                "instance and the class carries nothing for it (section 2, 'a keyword "
                "we cannot express': a name that cannot constrain an instance compiles "
                "to nothing)"
                for k in sorted(foreign)
            )
            keys -= foreign
        if "$ref" in keys and keys != {"$ref"}:
            # A conjunct that is a ``$ref`` AND something else.  **The CONSTRAINING
            # siblings compile to nothing and are REPORTED** -- §5's ``$ref`` row as
            # the design owner settled it on 2026-10-25, read through
            # :func:`inert_beside_a_reference` so that this arm and
            # ``emit._decide``'s reference arm decide one co-occurrence once.  The
            # conjunct is then the bare ``$ref`` it effectively is, and the base arm
            # below binds it.
            #
            # What is left refuses by name: a key with NO ROW is a keyword the bundle
            # did not use before and could constrain anything (§9).  A REFUSE cell is
            # §7's own answer and ``foreign`` above has already dropped and reported
            # it, so it never reaches here.
            inert = inert_beside_a_reference(conjunct, where, Position.CONJ, mod)
            remaining = keys - {"$ref"} - inert
            if remaining:
                return Refusal(
                    min(remaining),
                    where,
                    "a sibling of $ref, which draft-07 ignores, and which the table "
                    "gives no row -- so it is not a keyword section 5's $ref row "
                    "decides compiles to nothing, and the first document to carry a "
                    "keyword the bundle did not use before is loud rather than ignored",
                    kind=kind_for(min(remaining), Position.CONJ),
                )
            keys = {"$ref"}
        if keys == {"$ref"}:
            # **Which of the two resolutions a reference is, is NOT this arm's reading**
            # (``adcp-client-python-10l.43``): :func:`_conjunct_base` branches on the
            # parser's own document half and routes a LOCAL pointer through
            # :func:`local_reference`, so the carrier below is the same :class:`Target`
            # either way and the import is recorded once, inside it.
            based = _conjunct_base(conjunct, where, mod)
            if isinstance(based, Refusal):
                # The RUN's own answer, returned upward unchanged (§6): a target that
                # refuses makes this conjunct's base undecidable, and the CHAIN is the
                # run's to mint because it is the one that knows the target's refusal.
                return based
            target, reference = based
            if target.kind is not TargetKind.CLASS:
                # **§5's ``$ref`` row at CONJ, the half that was never written** (§14
                # step 9): "a BASE where the target is a class declaring fields.  Where
                # it is not -- a scalar, an enum, a container, or a union root, whose
                # instance is one of its branches -- it is not a class a model can
                # extend: the target is this node's own TYPE, and the other conjuncts
                # and the ``allOf``'s siblings constrain it, which is §2's intersection
                # at a node that declares no fields of its own."
                #
                # **The gate is :attr:`Target.kind` and not ``shape is None``**
                # (``adcp-client-python-10l.55``).  The row's own sentence names FOUR
                # targets and only three of them declare no fields: a union root records a
                # :class:`Shape` like every other class, so the question "may this stand
                # as a base HERE" is the kind's and the shape's absence answers a
                # different one.  CONJ's answer is unchanged -- a scalar, an enum, a
                # container and a union root all become this node's own type -- and the
                # BRANCH position's differs, which is why it reads the same field.
                #
                # So the symbol is recorded as a CONJOINED TYPE rather than as a base,
                # and :func:`_the_conjuncts_own_type` below is what answers with it once
                # every conjunct has been read -- after, because the answer depends on
                # what the OTHER conjuncts contribute: a type beside a field is not this
                # row's shape at all, and the reading has to see the whole list before it
                # can say so.  **The IMPORT is :func:`_conjunct_base`'s**
                # (``adcp-client-python-10l.43``), because that is the one place that knows
                # a local pointer's symbol is declared HERE and imported from nowhere --
                # the two arms differ in what they do with the symbol rather than in
                # whether they need it, so it is recorded where the resolution is MADE.
                #
                # **A target that declares only a RULE takes §2's intersection over
                # DECLARATIONS instead, and reaches the same list an inline rule-stating
                # conjunct does** (:func:`_a_rule_the_target_states`,
                # ``adcp-client-python-10l.59``).  It is not one of §5's four: it declares
                # no property to intersect and no field set to inherit, so "the target is
                # this node's own TYPE" has no type to name -- what it says about the
                # instance is a rule, and a draft-07 conjunct applies to the same
                # instance, so the nearest class holding it is THIS node's.
                #
                # The two rows met on these lines and the resolution keeps both. Note the
                # ORDER it forces: ``_conjunct_base`` has already recorded the import by
                # the time the rule-only arm declines to name the target, so a rule-only
                # conjunct records an import of a symbol its module does not spell.
                # Measured after the merge over the whole emitted tree rather than
                # reasoned about; the result is recorded at the merge commit.
                stating = _a_rule_the_target_states(conjunct["$ref"], mod)
                if stating is not None:
                    conjunct_rules.append(stating)
                    continue
                if target.branches is not None:
                    # **§5's distribution clause drops a branch whose intersection with
                    # what this node asserts is PROVABLY empty, and the drop is decided
                    # HERE because it can be** -- it is a question about DECLARATIONS
                    # (:func:`_asserted_properties`), which §2 is where every intersection
                    # is computed, and the raw declarations are all read before this loop
                    # starts.  The two answers that depend on the whole conjunct list are
                    # still :func:`_the_conjuncts_own_type`'s and are unchanged.
                    #
                    # **One survivor is not a distribution at all**: "(A | B | C) and D"
                    # with two disjuncts empty is "(C and D)", a conjunction of two
                    # declarations and nothing more -- so the branch is a class declaring
                    # fields and §5's CONJ rule for one applies as stated, "a BASE where
                    # the target is a class declaring fields".  It falls through to the
                    # arm below with no special case, which is the coordinator's own
                    # reading of the clause: one class and no dispatch.  §2's restatement
                    # rule then decides every key the node and the survivor both declare,
                    # through the machinery that already answers it for every other class
                    # base -- so nothing shadows anything and no second intersection is
                    # written.
                    asserted = _asserted_properties(node, conjuncts)
                    live = _surviving(asserted, target.branches)
                    if not live.live:
                        # Every disjunct empty, which is the node §5's empty-intersection
                        # row IS about: "the node admits nothing, which is a contradiction
                        # in the document".  0 sites over the portable population.
                        return Refusal(
                            "allOf",
                            where,
                            f"every branch of {target.symbol} intersects to nothing with "
                            f"what this node asserts about {sorted(asserted)}: section 5's "
                            "$ref row distributes the conjunction over the target's "
                            "branches and drops an empty one, and with every branch empty "
                            "the node admits no instance at all",
                            kind=kind_for("allOf", Position.CONJ),
                        )
                    if len(live.live) > 1:
                        conjoined.append((where, replace(target, branches=live), reference))
                        continue
                    # The one survivor stands as a BASE, so its own symbol is what this
                    # module imports -- the UNION ROOT's, which ``_conjunct_base``
                    # recorded, is no longer named anywhere.
                    target = live.live[0][1]
                    mod.importing(target.symbol, target.where)
                else:
                    conjoined.append((where, target, reference))
                    continue
            # A base another MODULE declares, carried as the symbol the module writer
            # imported: §7 makes ``bases`` ``TypeRef``s so one slot holds that beside a
            # base this module declares, which travels by pointer until the pass runs.
            conjunct_bases.append(ir.TypeRef(target.symbol, local=True))
            inherited.update(target.declares.properties)
            inherited_fields.update(target.declares.decided)
            inherited_from.update(dict.fromkeys(target.declares.properties, target))
            inherited_required |= target.declares.required
            if inherited_extra is None:
                inherited_extra = target.declares.extra
            if inherited_description is None:
                inherited_description = target.declares.description
            continue
        # **EVERY PART OF THE CONJUNCT CONTRIBUTES, and each part lowers by the decision
        # covering it** (section 2, "composition merges by intersection").  One arm
        # rather than three, because three arms is what produced the gap: a conjunct
        # whose parts fell under two of them matched neither, and 13 documents waited on
        # a row the refusal promised and nobody had scheduled.  The parts, and the
        # decision each is read by:
        #
        # * ``properties`` -- fields of THIS node, because a draft-07 conjunct applies to
        #   the same instance; merged with the node's own by :func:`declare`, which is
        #   section 2's intersection rule and is symmetric.
        # * ``required`` -- this node's requiredness.  **On its own that is section 2's
        #   requiredness overlay**, the ONLY redeclaration of an inherited field
        #   section 2 permits: ``core/collection-selection.json`` at
        #   ``/oneOf/0/properties/collections/items/allOf/1`` is
        #   ``{"allOf": [{"$ref": ...}, {"required": [...]}]}``, and the subclass
        #   redeclares the field with the base's type and no default (the ``verdict or
        #   (key in required and key not in inherited_required)`` branch below).  The
        #   arm was omitted on a measurement -- 0 ``required``-only conjuncts AT A ROOT
        #   -- and every one of them is at a property or deeper, so the measurement was
        #   true and answered a different question.
        # * a rule keyword (section 2, "rules are after-validators") -- a rule of THIS
        #   node, for the same draft-07 reason the fields are: a conjunct is not a
        #   separate object and gets no class of its own.  Measured when this was its
        #   own arm: all 20 documents whose ROOT carries a rule keyword ALSO carry a
        #   rule-bearing conjunct, so admitting the root's on its own emitted none of
        #   them.  The two positions are one unit.
        #
        # **And a conjunct carrying BOTH fields and a rule contributes both**, which no
        # arm reached: ``core/media-buy-frequency-cap-requirement.json`` at ``/allOf/1``
        # states ``properties`` beside a ``not``, and a reader matching ``properties``
        # ALONE passed it by.
        #
        # Screened by the conjunct's OWN ``screen`` at its OWN pointer, so a conjunct
        # carrying a combinator of SHAPES is not admitted here and refuses below --
        # rather than being emitted with the combinator dropped.
        screen = frozenset(declaration_rule_sources(conjunct, Position.CONJ))
        if keys <= INLINE | screen | CONJ_COMPOSES:
            # ``foreign`` is handed to the screen as CLAIMED, because this arm has
            # already decided what happens to it: it is dropped and reported.  Left
            # out, ``check_keywords`` walks ``sorted(node)`` and refuses on the very
            # name the drop above accounted for, which loses the document and leaves
            # the drop record unwritten -- measured on
            # ``media-buy/sync-catalogs-request.json``.
            unadmitted = check_declaration(
                conjunct,
                where,
                Position.CONJ,
                set(INLINE) | screen | set(CONJ_COMPOSES) | foreign,
                mod=mod,
            )
            if unadmitted is not None:
                return unadmitted
            if conjunct.get("type") not in (None, "object"):
                return Refusal(
                    "type",
                    where,
                    f"a conjunct of type {conjunct['type']!r} is not one",
                    kind=Kind.VERDICT,
                )
            if "additionalProperties" in keys and conjunct["additionalProperties"] is not True:
                # Not the identity, so it is one of the clause's other three readings
                # and none of them is written: ``false`` closes the composed object,
                # two typed conjuncts intersect their value schemas, and a typed one
                # beside a ``true`` one is a widening.  All 5 conjuncts that state the
                # keyword over the portable population state ``true``, so this is the
                # arm with no population -- a DEFERRAL and not a verdict, because what
                # obstructs it is unwritten code (:data:`CONJ_COMPOSES`).
                return Refusal(
                    "additionalProperties",
                    where,
                    f"a conjunct states additionalProperties: "
                    f"{conjunct['additionalProperties']!r}, which is not the identity; "
                    "section 5's additionalProperties row decides it at CONJ -- false "
                    "closes the composed object, two typed conjuncts intersect their "
                    "value schemas, a typed one beside a true one is a widening -- and "
                    "none of the three is written, because all 5 conjuncts stating the "
                    "keyword over this bundle state true",
                    kind=Kind.DEFERRED,
                )
            if "allOf" in keys:
                # Section 5's ``allOf`` row, CONJ: the same rule applied to the
                # conjunct's own conjuncts.  Pushed onto the worklist at their own
                # pointers rather than lowered here, so a nested conjunct is screened by
                # its OWN ``rules_at`` at its OWN pointer -- the property that keeps a
                # nested conjunct carrying a combinator of shapes refused where it sits.
                inner = conjunct["allOf"]
                if not isinstance(inner, list) or not inner:
                    return Refusal(
                        "allOf",
                        where,
                        f"a conjunct whose allOf is {inner!r}, not a non-empty list of "
                        "schemas",
                        kind=Kind.VERDICT,
                    )
                unread.extend((f"{where}/allOf/{j}", c) for j, c in enumerate(inner))
            if "properties" in keys:
                if not isinstance(conjunct["properties"], dict) or not conjunct["properties"]:
                    return Refusal(
                        "properties",
                        where,
                        "a conjunct declaring no property",
                        kind=Kind.VERDICT,
                    )
                for key, sub in conjunct["properties"].items():
                    conflict = declare(key, sub, f"{where}/properties/{key}")
                    if conflict is not None:
                        return conflict
            names = _required(conjunct, where)
            if isinstance(names, Refusal):
                return names
            required |= set(names)
            # Read by ``rules_at`` as one of THIS node's rule sources whenever the
            # conjunct contributes anything at all, and not only when it states a rule
            # keyword: ``rules._distinct`` reads a ``uniqueItems`` off the array a
            # PROPERTY holds, so a conjunct whose properties are this node's fields has
            # its ``uniqueItems`` claimed by the rule families exactly as the node's
            # own properties do.
            # Gated on the conjunct contributing, so an annotations-only conjunct adds
            # no source and renders nothing.
            if keys:
                conjunct_rules.append(conjunct)
            continue
        combinator = next((k for k in ("oneOf", "anyOf") if k in keys), None)
        if combinator is not None:
            # **A conjunct carrying a combinator of SHAPES, reported on the combinator
            # and against the rows that own what it needs.**  Section 5's
            # ``oneOf``/``anyOf`` row says CONJ -> one class per branch over the
            # composed bases, and writing the classes is not the half that blocks: a
            # payload reaches its branch only through a dispatch section 4 DERIVES, and
            # measured over every ``allOf`` conjunct of the 1,054 portable documents
            # carrying a combinator ``schema.presence_only`` answers no for -- **7
            # sites in 6 documents, 24 branches, and 0 branches pin a const** -- so
            # ``union.discriminator`` intersects empty pin maps and answers "" for every
            # one.  Section 4's third source, branches no instance satisfies twice, is
            # what decides them and it lives in ``codegen/lower/union.py``.
            #
            # **Re-measured at section 5's "A union of presence-only branches that also
            # forbid" (2026-10-27), which moved three of them off this reader.**  The
            # probe read 10 sites in 8 documents and 35 branches before:
            # ``formats/canonical/seller_rendered_stateful_display.json`` (two sites, 6
            # branches) and ``media-buy/build-creative-request.json`` ``/allOf/4`` (5
            # branches) state ``required`` plus a ``not`` over ``required`` on every
            # branch, so ``schema.presence_clause`` reads them and the same row's rule
            # answers them -- a ``PresenceGroups``, whose clauses keep each branch's two
            # halves paired.  The live refusals here went 6 -> 4 with it.
            #
            # Reported on the combinator rather than on ``min(keys)``: attribution is
            # the point of a refusal report, and ``sorted`` put ``not`` and
            # ``properties`` ahead of the keyword that is the reason.
            return Refusal(
                combinator,
                where,
                f"a conjunct carrying a {combinator} of SHAPES rather than presence "
                "groups.  Section 5 says CONJ -> one class per branch over the composed "
                "bases, and section 4 says a payload reaches its branch only through a "
                "derived dispatch: no branch of any such conjunct in this bundle pins a "
                "const, so section 4's first source derives none and the third -- "
                "branches no instance satisfies twice -- is the one that decides them, "
                "in codegen/lower/union.py (salesagent-j3k2l.60, salesagent-j3k2l.67).  "
                "Where every branch constrains only key presence the same row's rule is "
                "the cheaper answer and schema.presence_clause already reads it; these "
                "branches constrain a value, so there is no clause to read",
                kind=Kind.DEFERRED,
            )
        if keys and keys <= _A_VALUE_SET:
            # **§5's ``enum`` row at CONJ: a conjunct that is a VALUE SET constrains the
            # node's own TYPE** (:data:`_A_VALUE_SET`).  It is not a field, not a rule and
            # not a base, so it belongs to the same reading §5's ``$ref`` row gives every
            # other conjunct here -- "the target is this node's own TYPE, and the other
            # conjuncts and the ``allOf``'s siblings constrain it, which is §2's
            # intersection at a node that declares no fields of its own" -- and §2 states
            # the intersection for this keyword in its own words: "an enum is the
            # intersection of the members".
            #
            # Collected and read AFTER the whole list, for the reason
            # :func:`_the_conjuncts_own_type` is: whether this conjunct narrows a TYPE or
            # has nothing to narrow depends on what the other conjuncts turned out to be,
            # which the conjunct carrying the value set cannot know.
            conjunct_values.append((where, conjunct))
            continue
        return Refusal(
            min(keys) if keys else "allOf",
            where,
            "this step lowers a $ref conjunct (a base) or an inline conjunct whose parts "
            "are properties, required, rule keywords, an additionalProperties identity "
            "and a nested allOf; a later row lowers this one",
            kind=Kind.DEFERRED,
        )

    if contains is not None and not conjoined:
        # **A ``contains`` beside conjuncts that are all BASES.**  §5's row makes the
        # sibling constrain the TYPE a non-class target supplies, and a node whose
        # conjuncts are classes has no such type: ``contains`` quantifies over the MEMBERS
        # of a list and a composed class is not a list, so there is nothing for the
        # ``AtLeastOne`` to range over.  0 sites over the portable population -- the one
        # node reaching the carrier at all composes a bare ``$ref`` to an array document
        # -- so this is written so the first one is loud rather than emitted with the
        # keyword dropped.
        return Refusal(
            "contains",
            pointer,
            "this node states contains beside conjuncts that are all class bases: "
            "section 5's contains row makes it an AtLeastOne over the members of a LIST, "
            "and this node's type is a composed class, so the predicate has nothing to "
            "range over and dropping it would lose the document's own existential",
            kind=kind_for("contains", Position.CONJ),
        )
    if conjunct_values and not conjoined:
        # **A value set beside conjuncts that are all BASES, which §5's row does not
        # reach.**  The row's answer is the TARGET as this node's own TYPE, narrowed; a
        # node whose conjuncts are classes has no such type -- the instance must satisfy
        # those classes AND be one of the enumerated values, and a class is not a member
        # of a vocabulary.  0 sites over the portable population (the one value-level
        # conjunct in the bundle sits beside a ``$ref`` to an enumeration), so this is
        # written so the first one is loud rather than emitted with the keyword dropped.
        where, conjunct = conjunct_values[0]
        return Refusal(
            min(declaring(conjunct, Position.CONJ)),
            where,
            "a conjunct states a VALUE SET beside conjuncts that are all class bases: "
            "section 5's enum row at CONJ narrows the TYPE a non-class target supplies, "
            "and this node's type is a composed class -- an instance of a class is not a "
            "member of a vocabulary, so there is nothing here for the intersection to "
            "narrow and dropping the keyword would lose the document's own value set",
            kind=kind_for("enum", Position.CONJ),
        )
    #: §5's DISTRIBUTION clause, where the row above answered with the target's BRANCHES:
    #: the conjunct's own pointer, the branches, and the node each branch class is
    #: declared from.  ``None`` at every other node, which is what the tail below reads to
    #: tell a class from a union base.
    distributing: tuple[str, TargetBranches, nodes.Reference] | None = None
    if conjoined:
        # **§5's ``$ref`` row at CONJ, read after the WHOLE list** (§14 step 9): the
        # answer is a TYPE and not a class, and whether the row holds depends on what the
        # other conjuncts contribute -- so it cannot be decided at the conjunct that
        # carried the reference.  ``local`` is every key some view of this node declares,
        # which is the "declares no fields of its own" clause asked of the node and its
        # conjuncts together.
        answered = _the_conjuncts_own_type(
            node,
            conjoined,
            fields_declared=set(local) | set(inherited) | required,
            bases=(*bases, *conjunct_bases),
            # **The node's own ``contains`` joins the conjuncts' rule sources**, which is
            # §5's ``$ref`` row at CONJ read whole: "the other conjuncts AND THE
            # ``allOf``'s SIBLINGS constrain it".  One list and not two, because
            # :func:`_the_conjuncts_own_type` already folds its sources into a single
            # ``beside`` and hands that to ``lower.rules.on_a_value`` -- which is the one
            # reader of a ``contains`` over a value, at every position, by §5's
            # ``contains`` row ("an ``AtLeastOne`` after-validator on the array's own
            # annotated type, because no class has a kind for it").  Appended LAST so a
            # conjunct stating one is met first and the two-sources refusal names the
            # conjunct's pointer rather than the node's.
            rule_nodes=(
                [*conjunct_rules, {"contains": contains}]
                if contains is not None
                else conjunct_rules
            ),
        )
        if isinstance(answered, Decided) and conjunct_values:
            # **§5's ``enum`` row at CONJ, applied to the type the row above decided.**
            # The reference is the one that supplied the type, which is the same
            # ``conjoined[0]`` the row reads, and the narrowing is §2's intersection over
            # DECLARATIONS -- the TARGET's vocabulary read through
            # :meth:`Module.resolve_node`, not the symbol it was bound to.
            return _the_vocabularys_intersection(
                answered, conjunct_values, conjoined[0][2], mod
            )
        if not isinstance(answered, TargetBranches):
            return answered
        # **The DISTRIBUTION, and the whole of it on this side is that the node becomes a
        # UNION BASE** (``adcp-client-python-10l.68``).  §5's ``$ref`` row: "the node is a
        # union whose branches each take one of the target's branches as a base and add
        # the node's own fields" -- so the class this function was already about to
        # declare IS the base that adds the node's own fields, and what it gains is §4's
        # three union-base facts plus the branch list.  Nothing below changes: the
        # restatement loop, the requiredness overlay and :func:`fields` all run as they do
        # for any composing class, which is §5's union row read the same way
        # ``lower.union.lower_union`` reads it -- "the root's siblings compile onto the
        # base as they would on any class".
        #
        # ``combinator`` and ``discriminator`` are the TARGET's, carried rather than
        # re-derived (:class:`TargetBranches`): the distributed branches are the target's
        # branches with this node's fields added, so they pin the same ``const`` on the
        # same property and §4's dispatch derivation has already answered for them.
        where, branches, reference = conjoined[0][0], answered, conjoined[0][2]
        distributing = (where, branches, reference)
        union = UnionBase(
            # §5's ``required`` row at ROOT beside a union.  Every name here is one this
            # node's own views declare, so none of them selects a branch -- the branches'
            # own requiredness is the TARGET's and reaches each branch class through its
            # target base -- and ``fields`` holds a field for each.
            root_required=tuple(sorted(required)),
            discriminator=branches.discriminator,
            combinator=branches.combinator,
            branches=tuple(
                ir.TypeRef(_distributed_pointer(where, branches, j), local=True)
                for j in range(len(branches.of))
            ),
        )
        # The mixin FIRST so the MRO finds its ``__get_pydantic_core_schema__``, and the
        # model base only where this node composes nothing else -- the same arrangement
        # ``lower.union.lower_union`` passes and for the same measured reason
        # (``base_if_none_composes``).  **Through :func:`dispatching_bases`, which is the
        # one reading of "is it already carried"**: this arm's ``bases`` may already hold
        # the enclosing union's base, because a BRANCH of a root union that distributes a
        # union target arrives here with that base passed down -- and naming the mixin
        # beside it puts a class before its own subclass.  That is ``core/postal-area.json``
        # at ``/anyOf/0``, which is this route and not the carrier's.
        bases = dispatching_bases(bases, mod)
        base_if_none_composes = ir.TypeRef("AdCPBaseModel", local=True)
        mod.imports.add((ir.BASE_MODULE, "AdCPBaseModel"))
        mod.imports.add(("typing", "ClassVar"))

    stated = rules_at(node, *conjunct_rules, position=position)

    own: dict[str, dict] = {}
    #: The keys whose field is the inherited one wearing this document's annotations.
    reuse: dict[str, ir.Field] = {}
    #: The keys whose INTERSECTION took its ``uniqueItems`` from the base, so the rule
    #: families have already claimed the keyword on the class that decided the base's field and this
    #: subclass inherits that rule.  ``fields`` strips the keyword and renders the fact
    #: onto the field, exactly as it does for a REUSED key and for the reason its
    #: docstring gives there: the array row carries no ``uniqueItems`` and refuses one by
    #: name, which is what keeps an array NO class holds refused rather than widened.
    #:
    #: Measured on ``core/product-execution-requirement.json`` at
    #: ``/oneOf/2/properties/connection/allOf/1/properties/required_for``, whose
    #: restatement is a bare ``{"contains": {...}}``: the intersection merges the base's
    #: ``type``, ``items`` and ``uniqueItems`` back in, and the merged declaration was
    #: then decided FRESH -- so the keyword reached the array row and refused the
    #: document on a fact its base already states as a rule.
    inherited_distinct: set[str] = set()
    for key, stating in local.items():
        if key not in inherited:
            own[key] = stating
            continue
        verdict = _restatement(stating, inherited[key], mod.resolve_node)
        if verdict is None:
            # **THE KIND IS THE CELL'S AND NOT THIS SITE'S** (architecture §3, "a
            # refusal's kind is derived from the cell and never chosen at a raise
            # site"), and the hand-written ``Kind.VERDICT`` that stood here was §9's
            # first mistake: ``docs/plan/rebuild-plan.md`` §5(b) DECIDES this row --
            # "an ``allOf`` restatement that neither matches nor narrows ... rung
            # KEYWORD: the field takes the base's declaration and the restatement's
            # extra facts are dropped" -- so what is missing is a written case and not
            # an obstruction belonging to the document.  A verdict minted for unwritten
            # code reports clearable work as finished, which is exactly what the pinned
            # verdict set recorded: eleven of the fourteen documents that JOINED it at
            # this row's third instalment resolve here.
            #
            # :func:`kind_for` answers DEFERRED for every keyword this arm reports on,
            # and it answers that off the cell: ``properties``, ``items``,
            # ``additionalProperties`` and ``$ref`` all compile to a TYPE at PROP, and a
            # lowering effect whose handler claims nothing is a deferral.  An UNROWED
            # key still answers VERDICT through the same lookup, so the one arm that
            # really is the document's keeps its kind without a second reading.
            #
            # PROP and not ``position``: a restatement is a PROPERTY's declaration
            # against the base's, which is the same reason :func:`_constraining` reads
            # every declaration this arm compares at PROP.  The position is the restated
            # node's own and is taken from the structure, not recovered from the pointer.
            #
            # **WHY §5(b)'S RUNG IS NOT YET WRITTEN, measured rather than asserted**
            # (``adcp-client-python-10l.21``, fourth instalment).  The widening itself
            # is sound and lands: implemented over the 1,054 portable documents it takes
            # emitted 885 -> 910 and refused 169 -> 144.  What it cannot do is be
            # GRADED.  §2 defines the one gradeable kind as "WIDENED -- ... §8's
            # comparison sees every one of these, because the document states a fact the
            # model does not", and §8's fifth outcome is the same direction:
            # "*approximated* -- the document states the fact, the model does not".  The
            # facts this row drops are NESTED facts the base's own declaration states a
            # WIDER value for, so the comparison reports them in the two directions §8
            # has no declared form for -- measured over the graded tree, 18 pairs report
            # ``added /../field/enum`` beside the ``missing /../field/const`` a
            # declaration could carry, ``core/assets/display-tag-asset.json#/oneOf/2``
            # reports ``differs /../field/enum`` alone, and
            # ``governance/check-governance-response.json`` reports ``differs
            # ../action_binding/required``, ``differs ../action_id/type`` and ``added
            # ../action_id/default``.  21 of the 25 freed documents therefore carry a
            # fact no declaration can absorb, and the three that carry NONE are wider
            # than their documents invisibly, which ``census.stale`` reports as a
            # declaration nothing earns.  A rung is written when §8 has a form for the
            # direction it drops in, and that is a decision §8 makes rather than this
            # arm.
            disagreeing = _disagreeing(stating, inherited[key], mod.resolve_node)
            # **The sentence states its own obstruction, which means the DEREFERENCED
            # reading and the two values at the keyword that failed** (``10l.92``).  It
            # printed ``sorted(_constraining(...))`` of the RAW declarations, so a base
            # whose whole content is a bare reference read as "inherited states
            # ['$ref']" -- true of the text and not of what was compared, since
            # :func:`_restatement` resolves such a base before it compares anything.
            # Three refusals here said that, and the keyword they named was the
            # reference they had already resolved past.
            inherited_read = _constraining(_dereferenced(inherited[key], mod.resolve_node))
            stating_read = _constraining(_dereferenced(stating, mod.resolve_node))
            return Refusal(
                disagreeing,
                at[key],
                f"the restatement of {key!r} neither matches nor narrows the "
                f"inherited declaration at {disagreeing!r}: inherited says "
                f"{inherited_read.get(disagreeing)!r}, this says "
                f"{stating_read.get(disagreeing)!r}.  inherited states "
                f"{sorted(inherited_read)}, this states {sorted(stating_read)}, and the "
                "keyword above is the first the two SHARE that this one does not say at "
                "least as much at -- a keyword only the inherited declaration states is "
                "never the obstruction, because under allOf the base's statement applies "
                "wherever the restatement is quiet.  "
                "docs/plan/rebuild-plan.md section 5(b) decides this row at rung "
                "KEYWORD -- the field takes the base's declaration and the "
                "restatement's extra facts are dropped -- and the facts it drops are "
                "nested ones the base states a WIDER value for, which section 8's "
                "approximated outcome has no direction for: it reads 'the document "
                "states the fact, the model does not'",
                kind=kind_for(disagreeing, Position.PROP),
            )
        if verdict or (key in required and key not in inherited_required):
            # It narrows, so the subclass is the one that states it -- and **a
            # REQUIREDNESS the base does not have is a narrowing too**, which is the
            # half this read for as long as requiredness lived in ``required`` rather
            # than in the declaration ``_restatement`` compares.  Left inherited, the
            # field keeps the base's optionality while the composing document's own
            # ``required`` names it, so the class ACCEPTS A PAYLOAD THE DOCUMENT
            # REFUSES and renders a ``default: None`` the document does not state.
            # Measured on this tree: 2 documents and 2 pairs --
            # ``core/tasks-get-response.json`` and
            # ``protocol/get-task-status-response.json``, whose ``task_id`` is optional
            # on ``core/protocol-envelope.json`` and required at their own root -- and
            # they were the last 2 ``added`` facts of the symmetric comparison.
            #
            # The INTERSECTION, in BOTH halves (``adcp-client-python-10l.103``).
            #
            # **This read the node ITSELF where only the requiredness moved, on the
            # ground that "the content is the base's already, so there is nothing of the
            # base's to merge back in" -- and that is true of an EQUAL restatement and
            # false of one stating LESS.**  Once silence stopped being a loosening
            # (:func:`_restatement`), a restatement that does not narrow can state
            # strictly less than the base, and lowering THAT node alone drops every fact
            # the base states.  The arm below already carries the sentence, for the same
            # shape reached without a requiredness move: "a restatement can reach this
            # arm stating LESS than the base ... and lowering THAT node alone drops the
            # base's bound, which is the shadow this whole rule exists to make
            # unspellable."
            #
            # Measured on ``adagents.json``, where its four union branches state
            # ``{"properties": {"formats": {"minItems": 1}}, "required": ["formats"]}``
            # over a base declaring ``formats`` as an array of
            # ``ProductFormatDeclaration`` with ``minItems: 1`` already: the restatement
            # matches, so ``verdict`` is false, the requiredness moved, and the field was
            # redeclared from ``{"minItems": 1}`` alone -- emitting ``formats: Any`` over
            # the base's ``list[FormatsItem]``.  Three defects in one line: a
            # TYPE-changing redeclaration of an inherited field, which this module's own
            # rule calls a build failure; the base's ``type`` and ``items`` dropped with
            # no declaration at all; and the ``minItems`` that WAS declared declared at
            # rung KEYWORD -- "drop the one keyword, keep the type" -- while the output
            # took ``Any``.  The asymmetry is the proof: the two sibling branches that
            # state no ``required`` reached the arm below and kept the base's type and
            # bound.
            own[key] = _intersection(stating, inherited[key], mod.resolve_node)
            if not _constraining(stating) or _constraining(own[key]) == _constraining(
                _dereferenced(inherited[key], mod.resolve_node)
            ):
                # **The restatement says nothing about the instance the base does not,
                # so this is section 2's REQUIREDNESS OVERLAY and takes its answer**:
                # "Where composition makes an inherited field required, the subclass
                # redeclares it with the base's type and no default."  The overlay loop
                # below implements exactly that and reaches only a key NO view declares;
                # a key that is both restated and newly required falls between the two,
                # and this is the half that was missing.
                #
                # Reusing the base's DECIDED field rather than re-deciding the
                # intersection is what keeps the KNOWN CEILING below unreached: the
                # intersection takes the base's ``items`` with it, and re-deciding
                # declares that nested class again at a pointer this document does not
                # have, which is what ``schema_at`` raises on when the pair is graded.
                held = _reused(
                    key, inherited_fields, inherited_from, f"{pointer}/properties/{key}", mod
                )
                if isinstance(held, Refusal):
                    return held
                reuse[key] = held
                own[key] = dict(inherited[key])
            if _constraining(own[key]).get("uniqueItems") is True and not _constraining(
                stating
            ).get("uniqueItems"):
                inherited_distinct.add(key)
        elif _annotates_differently(stating, inherited[key]):
            # **It states the same thing about the INSTANCE and a different thing to the
            # READER**, so the subclass states the field: a document's own declaration
            # governs the annotation at its own pointer (the description-authority rule,
            # ``docs/plan/rebuild-plan.md`` §6), and a base's must not stand where the
            # document declares one itself.
            #
            # ``_restatement`` returned False here, so the restatement's own
            # constraining content is either EQUAL to the base's or EMPTY, and the two
            # reach the base's content by different routes:
            #
            # * **EQUAL** -- the node says what the base says about the instance, so
            #   ``decide_type`` reading the node decides the base's own type and there
            #   is no shadow to be had.  15 pairs and 15 documents, every one a response
            #   root composing ``core/protocol-envelope.json`` and declaring ``context``
            #   itself as a bare ``$ref`` to ``core/context.json``: the envelope states
            #   the long "Relationship to per-task body-level ``context`` declarations"
            #   text as a SIBLING of its own ``$ref``, the 15 documents state the
            #   target's own short text at the pointer the comparison grades, and they
            #   were 15 of the 43 ``differs``.
            # * **EMPTY** -- the node says nothing about the instance, so it is the
            #   inherited FIELD that stands and only the annotations are this
            #   document's.  A previous reading left this shape inherited entirely, on
            #   the ground that lowering the restatement ALONE types it ``Any`` and
            #   drops every fact the base states.  That is true of the restatement
            #   alone, and the answer is to not lower it alone: the base's decided
            #   field is re-used (:attr:`Shape.decided`, and ``fields``' ``reuse``
            #   says why the node cannot simply be merged and re-decided).  Measured as
            #   the whole of ``salesagent-j3k2l.22``'s residue: 28 ``differs`` over 7
            #   ``formats/canonical/*.json`` at ``experimental``, ``v1_translatable``
            #   and ``slots``, two of them INVERSIONS where the base defaults a boolean
            #   the opposite way from the document's own declaration.
            #
            # **The two also differ about SILENCE**, and each takes the reading under
            # which the model states what the COMPOSED DOCUMENT states at that pointer.
            # An EQUAL restatement's node resolves to something of its own -- all 15 are
            # a bare ``$ref``, and the resolved document carries the target's
            # annotations inline there -- so the document's conjunction gap-fills
            # nothing and the base's annotation must not stand
            # (:func:`_annotates_differently`).  An EMPTY one resolves to nothing of its
            # own, so under ``allOf`` the base's declaration is the one that applies
            # where the restatement is silent, and the composed document states it:
            # measured on ``formats/canonical/responsive_creative.json``, whose
            # ``slots`` restates a ``default`` and no ``description``, where reading the
            # restatement's silence as an answer left the base's description reported
            # ``missing`` instead of zero facts.
            # **The INTERSECTION here too, and the arm below is no longer "the node
            # states nothing" but "the intersection is the base's".**  Once silence
            # stopped being a loosening (:func:`_restatement`), a restatement can reach
            # this arm stating LESS than the base -- ``{"type": "integer"}`` over
            # ``{"type": "integer", "minimum": 3}`` says the same thing about every
            # instance and differs only in its annotations -- and lowering THAT node
            # alone drops the base's bound, which is the shadow this whole rule exists
            # to make unspellable.  The intersection is the base's content wearing this
            # document's annotations, and it is the same expression the EMPTY case used,
            # so there is one answer for both.
            own[key] = _intersection(stating, inherited[key], mod.resolve_node)
            if not _constraining(stating):
                # The node has no type of ITS OWN, so the field is the base's DECIDED
                # field: re-deciding declares the nested classes again, in this module,
                # at a pointer this document does not have (:attr:`Shape.decided`).
                #
                # The condition is "the NODE constrains nothing" and deliberately not
                # "the INTERSECTION is the base's", which is the same thing for this
                # shape and NOT the same thing for an EQUAL restatement: an equal one
                # intersects to the base's content too, and §6's clause 2 says its own
                # node is what the field is decided from -- all 15 of them are a bare
                # ``$ref`` whose resolved target carries its own annotations, and
                # reusing there put the base's annotation back at a pointer the document
                # declares itself.  Measured: 17 documents stopped emitting.
                #
                # KNOWN CEILING for the PARTIAL shape between the two -- a restatement
                # stating less than the base and the same -- whose intersection is
                # lowered as a node: a subschema-valued keyword it takes from the base
                # (an ``items``, a nested ``properties``) is declared at a pointer this
                # document does not have, and ``schema_at`` raises when the pair is
                # graded.  0 such sites in the emitted population, and the failure is
                # loud rather than silent, which is why this is named rather than coded.
                held = _reused(key, inherited_fields, inherited_from, at[key], mod)
                if isinstance(held, Refusal):
                    return held
                reuse[key] = held
        # Otherwise it adds nothing and the field is INHERITED: no line, no shadow.

    # **SECTION 2's REQUIREDNESS OVERLAY: the composition makes an inherited field
    # required and nothing else, so the subclass redeclares that field with the base's
    # type and no default.**  Section 2 calls this the only permitted redeclaration and
    # the sentence is verbatim; the loop above reaches only a key some view DECLARES,
    # and an overlay declares none -- ``core/collection-selection.json`` at
    # ``/oneOf/0/properties/collections/items/allOf/1`` is ``{"required":
    # ["collection_ids"]}`` and nothing more.
    #
    # Left out, the requiredness went into ``required`` where the inherited field
    # SATISFIED it (``fields``' ``inherited`` argument) and no line was written, so the
    # class kept the base's OPTIONAL field and rendered ``= None`` -- a default the
    # document does not state, reported as an ``added`` fact at
    # ``/properties/collection_ids/default``, and a class that ACCEPTS A PAYLOAD THE
    # DOCUMENT REFUSES.  That is the same defect the ``key in required and key not in
    # inherited_required`` branch above fixes for a key that IS declared locally; this
    # is its other half.
    #
    # The TYPE is the base's decided field (``reuse``) rather than a second decision of
    # the base's node: re-deciding declares the nested classes again, in this module, at
    # a pointer this document does not have (:func:`fields`' ``reuse`` says why).
    #
    # **Section 2 also says "and no default", and that half is NOT written here**, because it
    # has no population: measured over every node of every one of the 1,054 portable
    # documents, 25 nodes carry a ``required``-only conjunct and **0 of them compose a
    # base that declares a ``default`` for a name the conjunct requires**.  An arm for it
    # would be a derivation matching nothing, which is green for free (the same ground
    # this row's own docstring refuses a ``required``-only conjunct arm AT A ROOT on, and
    # a stripped ``default`` was measured as unobservable: the perturbation that kept it
    # left the suite green).  If such a base ever appears, ``fields`` refuses the
    # document BY NAME -- "a default on a REQUIRED property has no rendering that does
    # not also make the property optional" -- which is the accurate answer and already
    # written.
    for key in sorted(required - inherited_required - set(own)):
        if key not in inherited:
            continue  # ``fields`` refuses a required name no view declares, by name
        # **The pointer names the PROPERTY and not the composing node.**  An overlay's
        # key is not in ``at`` -- no view of this document declares it, which is what
        # makes it an overlay -- so the pointer has to be built, and this passed
        # ``pointer`` itself.  At a ROOT that is ``""``, which ``Refusal`` renders
        # ``/``, so a refusal :func:`_reused` raises for one property was reported
        # against the whole document: measured on
        # ``core/product-signal-targeting-option.json``, whose ``signal_ref`` re-uses a
        # field whose type the base module imports rather than declares, and which
        # ``tests/test_emit_product.py`` caught as the one refusal left at ``/`` after
        # every other one had moved inside its document.
        overlaid = _reused(
            key, inherited_fields, inherited_from, f"{pointer}/properties/{key}", mod
        )
        if isinstance(overlaid, Refusal):
            return overlaid
        reuse[key] = overlaid
        own[key] = dict(inherited[key])

    # **The merged declarations go through the PARSER**, which is ``schema/nodes.py``'s
    # own sentence about why a conjunct is a declaration: §2's intersection rule merges
    # two declarations of one property and "hands the merged declaration back to
    # :func:`codegen.schema.parse.parse`", because the result has to be parsed as ONE node
    # rather than composed out of two decided ones.  So the one reader of a raw mapping
    # reads these too, at the pointer the key was declared at.
    parsed_own = {
        key: _parsed_property(declaration, at.get(key, f"{pointer}/properties/{key}"), mod)
        for key, declaration in own.items()
    }
    # **:func:`codegen.refusal.first_refusal` over the whole batch**, which is §2's one
    # combinator in the shape it was written for: the parses are independent, so the
    # sequence exists before any of them is consumed and the earliest refusal in it is
    # the earliest in DOCUMENT order -- ``own`` is keyed in the order the declarations
    # were read, the node's own properties first and each conjunct's in its own order
    # after them.  The surviving nodes are then narrowed by ``isinstance``, which is
    # what a signature promising to strip the refusals out would have needed a cast for.
    malformed = first_refusal(parsed_own.values())
    if malformed is not None:
        return malformed
    own_nodes = {key: n for key, n in parsed_own.items() if not isinstance(n, Refusal)}
    decided = fields(
        own_nodes,
        # **SORTED, because this is where the set becomes an order** (P7).  ``required``
        # and ``inherited_required`` are both ``set[str]`` here -- the node's own
        # ``required`` tuple went into a set at the top of this function so the conjuncts'
        # names could be unioned into it, and a base's arrives as the ``frozenset`` on
        # :attr:`Shape.required` -- and :func:`fields` READS this argument in order: the
        # names no declaration declares are a comprehension over it, and each becomes an
        # ``Any`` FIELD.  A set of strings iterates in hash order, so without the sort the
        # emitted class's field order changes with ``PYTHONHASHSEED`` -- measured 32/32
        # over seeds 0..63 while the order decided a refusal sentence, which it no longer
        # does -- and the artifact stops being a function of the bundle.
        #
        # Here and not inside :func:`fields`: the order of this argument is the CALLER's,
        # which is why that function's other caller passes ``node.required`` and gets the
        # document's own order.  Sorting inside it would overrule that caller and put the
        # choice in the layer that builds the field rather than the one that holds the
        # set.  It is the same reading the two other places this function's sets
        # become sequences already take -- the requiredness overlay's
        # ``sorted(required - inherited_required - set(own))`` above and ``distinct``
        # below -- and the one :func:`codegen.lower.names` takes of ``Shape.required``
        # when it spells a branch's name.
        sorted(required | (inherited_required & set(own))),
        pointer,
        mod,
        inherited=set(inherited),
        declared_at=at,
        # D6 has claimed the ``uniqueItems`` of these keys, whether the node stating
        # it is this one or a rule-bearing conjunct: the rule tuple and the strip are
        # two halves of one claim, so the row that writes the tuple passes the keys.
        distinct=(*stated.distinct, *sorted(inherited_distinct - set(stated.distinct))),
        reuse=reuse,
        # **§5's ``required`` row at ROOT beside a union, which is the one place a
        # required name is neither a field of this class nor undeclared**: the row puts
        # the root's own names in ``_ROOT_REQUIRED`` precisely "so a refusal can
        # separate a field the root requires from one that SELECTS A BRANCH", and a
        # name selecting a branch is declared by the BRANCH classes this caller is
        # declaring -- not by the base.  :attr:`UnionBase.root_required` is the same
        # tuple :func:`declare_object` writes onto the class, so the names the base
        # does not hold a field for and the names it reports on are one reading.
        # Empty for every other row, where a required name no view declares has
        # nothing to carry it and :func:`fields` gives it an ``Any`` field of its own.
        carried=() if union is None else union.root_required,
    )
    if isinstance(decided, Refusal):
        return decided
    declared = declare_object(
        node,
        pointer,
        mod,
        decided,
        # ``decided`` is what this class INHERITS; ``declare_object`` overlays the
        # fields it is handed, which are this class's own.  Passing the inherited ones
        # is what makes :attr:`Shape.decided` transitive the way ``properties`` is, so
        # a sub-subclass restating a key its grandparent declares reads one map.
        Shape(
            {**inherited, **own},
            frozenset(required | inherited_required),
            decided=inherited_fields,
            extra=inherited_extra,
        ),
        position,
        extras=getattr(node, "extras", None),
        # The model base only where NOTHING composes; see ``base_if_none_composes``.
        bases=(
            (*bases, *conjunct_bases)
            if conjunct_bases or base_if_none_composes is None
            else (*bases, base_if_none_composes)
        ),
        rule_nodes=conjunct_rules,
        # §4's three facts a union base carries and no other class does, and the
        # branch list §7 gives the base's fourth slot: ``None`` for every node that is
        # not one, which is what :func:`declare_object` reads to tell a base from a
        # class (and, through ``branches``, what tells it to record no reusable shape).
        root_required=None if union is None else union.root_required,
        discriminator=None if union is None else union.discriminator,
        combinator=None if union is None else union.combinator,
        branches=None if union is None else union.branches,
        # §6's description-authority rule, clause 3, at a CLASS: this node's own
        # description where it states one, and the base's where it is silent.  The
        # composed document states the base's at this pointer -- ``harness._composed``
        # folds it in -- and pydantic will not supply it, because ``cls.__doc__`` is
        # ``None`` for a subclass with no docstring.  Measured: 5 ``missing`` facts over
        # 4 pairs, every one a bare ``/description`` at a composing node whose own
        # declaration has none (``core/collection-selection.json``'s items and
        # ``core/canonical-media-buy-action.json``'s three branches).
        description=inherited_description,
    )
    if distributing is None or isinstance(declared, Refusal):
        return declared
    return _distribute(
        declared, *distributing, asserted=_asserted_properties(node, conjuncts), mod=mod
    )


def _distributed_pointer(where: str, branches: TargetBranches, index: int) -> str:
    """Where the class for one DISTRIBUTED branch sits, as a pointer of this document.

    ``<the conjunct>/<the target's combinator>/<index>``, and it is **a pointer the
    document of record HOLDS** rather than one this row invents (§9: "do not decide a
    position the bundle does not hold from a view of it").  §3 inlines every
    cross-document ``$ref`` unchanged, so the conjunct's own pointer carries the target's
    root in the record and the target's branch list hangs off it there -- which is also
    what makes the branch class GRADEABLE: ``_base.applied_schema`` resolves that pointer
    to the branch node and conjoins what the enclosing node asserts about the same
    instance, so the fields the branch inherits from this node's base are facts its node
    states (§8's pairing rule).

    Built and never parsed: the index is the position in the target's own branch list and
    the keyword is :attr:`TargetBranches.combinator`, both held as values, so no reader
    recovers a position from the string (``docs/plan/architecture.md`` §3).
    """
    return f"{where}/{branches.combinator}/{index}"


def _intersected_at_a_branch(
    asserted: Mapping[str, list[dict]],
    branch: Target,
    pointer: str,
    required: Collection[str],
    mod: Module,
) -> list[ir.Field] | Refusal:
    """The fields ONE distributed branch declares of its own: §2's intersection of what
    the node asserts with what the branch declares, at every key both state.

    §5's ``$ref`` row at CONJ: "A property the node and the target's branch BOTH declare
    is one field taking §2's intersection, exactly as the ``properties`` row at CONJ
    states it for two conjuncts -- **the node's declaration does not shadow the
    branch's**, and two ``const``\\ s intersect to the pin where they agree and to
    nothing where they differ."

    **Why the field has to be on the BRANCH and cannot be left to the two bases.**  A
    distributed branch's bases are ``(this node's class, the target's branch)`` in that
    order, so the MRO finds the NODE's field and the branch's own declaration is
    shadowed -- which is the one defect §2's restatement rule exists to make
    unspellable, and which is measurable: before this, ``core/audience-evidence.json``
    pinned ``type: 'resource'`` on all three branches and the base's dispatch raised
    "Value 'resource' for discriminator 'type' mapped to multiple choices".  Declaring
    the intersection on the branch is what beats both bases with the one declaration the
    document actually states there.

    **The decision is :func:`_restatement`'s and the value is :func:`_intersection`'s**,
    which are the same two functions every other restatement in this module passes
    through -- so a shared key at a distributed branch and a shared key at a flat base
    cannot come to disagree about what §2's intersection IS.  The three answers:

    * it NARROWS -- the branch declares the field, decided from the intersection;
    * it says the SAME thing or nothing -- no field, and the shadow is harmless because
      the node's field and the branch's are then one field.  ``type`` at
      ``core/audience-evidence.json`` is this case: the node states ``{const: resource}``
      and the branch ``{type: string, const: resource}``;
    * it is INCOMPATIBLE -- the caller refuses, and it must NOT drop the branch.
      :func:`_provably_empty` is what licenses a drop and its docstring says why this is
      not that question: an intersection this compiler cannot ORDER is §5's restatement
      row, and a branch dropped for one admits instances the document admits, which is a
      model narrower than its document.

    A key more than one view of the node asserts would need those views merged before
    this intersection, which is §2's intersection one level up and which no caller
    computes: 0 sites over the portable population, so it refuses rather than reading the
    first view and dropping the rest.
    """
    out: list[ir.Field] = []
    for key in branch.declares.properties:
        views = asserted.get(key)
        if not views:
            continue
        if len(views) > 1:
            return Refusal(
                "properties",
                f"{pointer}/properties/{key}",
                f"{len(views)} declarations of {key!r} reach this node, and a distributed "
                f"branch intersects ONE of them with {branch.symbol}'s: merging them first "
                "is section 2's intersection one level up, which no row computes here",
                kind=kind_for("properties", Position.CONJ),
            )
        stated, theirs = views[0], branch.declares.properties[key]
        # **The predicate is asked in BOTH directions and the merge takes whichever
        # narrowed**, which is ``declare``'s own arrangement for two local declarations of
        # one key -- the rule is symmetric, so which side the walk read first cannot
        # change the answer.  Either direction gives the same intersection; what the
        # direction decides is which declaration is the child of the merge.
        if _restatement(stated, theirs, mod.resolve_node):
            intersected = _intersection(stated, theirs, mod.resolve_node)
        elif _restatement(theirs, stated, mod.resolve_node):
            # **The BRANCH's declaration is the tighter one, and the field is still
            # declared here.**  §2 has the field carry the intersection, which at this
            # position the branch already states -- but the distributed class's FIRST base
            # is this node's, so the node's wider declaration is what the MRO finds and
            # the branch's narrowing would be lost.  Declaring the intersection on the
            # branch is what keeps it.  Measured: ``core/postal-area.json#/anyOf/0``
            # declares ``system`` as a ``$ref`` to the whole ``postal-system``
            # enumeration and each of the target's ten branches narrows it to that
            # country's own members -- ``{"enum": ["zip", "zip_plus_four"]}`` for
            # ``PostalCountrySystemUS`` -- so without this arm every branch would carry
            # the full vocabulary.
            intersected = _intersection(theirs, stated, mod.resolve_node)
        elif _restatement(stated, theirs, mod.resolve_node) is None:
            return Refusal(
                _disagreeing(stated, theirs),
                f"{pointer}/properties/{key}",
                f"what this node asserts about {key!r} and {branch.symbol}'s declaration "
                "of it neither match nor narrow one another in either direction, so "
                "section 2's intersection of the two is not computable -- and a branch is "
                "DROPPED only where the intersection is PROVABLY empty (disjoint consts, "
                "enums or type words), which this is not: dropping it would refuse "
                "instances the document admits",
                kind=kind_for("properties", Position.CONJ),
            )
        else:
            # Says the same thing, or nothing: the node's field and the branch's are one
            # field, so the base's declaration shadowing the branch's loses nothing.
            continue
        merged = _parsed_property(intersected, f"{pointer}/properties/{key}", mod)
        if isinstance(merged, Refusal):
            return merged
        decided = fields({key: merged}, [key] if key in required else (), pointer, mod)
        if isinstance(decided, Refusal):
            return decided
        out += decided
    return out


def _distribute(
    base: str,
    where: str,
    branches: TargetBranches,
    reference: "nodes.Reference",
    *,
    asserted: Mapping[str, list[dict]],
    mod: Module,
) -> str | Refusal:
    """§5's distribution, written: one subclass per branch of the target, over the base.

    "The node is a union whose branches each take one of the target's branches as a base
    and add the node's own fields.  **Each branch of a union root is a class declaring
    fields, so this is the CONJ rule above applied once per branch and not a second
    answer**" -- and that last clause is the whole of ``bases`` below: §5's ``$ref`` row
    at CONJ gives "a BASE where the target is a class declaring fields", so each branch
    class takes its TARGET BRANCH as a base.  The union BASE is never a branch's base on
    its own: §4 part 3 gives a class that inherits ``_branch_models`` its own plain
    schema, so a class subclassing ``SignalTargetingExpression`` alone would accept
    ``{}`` where every branch requires ``signal_ref``, ``value_type`` and ``value``
    (``adcp-client-python-10l.59`` measured it).  The node's own fields arrive through
    the OTHER base, which is this node's class -- the same two-base arrangement §4 gives
    a ``$ref`` BRANCH of a root union, read here across a module boundary.

    **Nothing of the target is COPIED**, which is the clause of the same row this one has
    to keep: a branch class declares no field of its own, and its symbol is imported from
    the declarer ``emit.resolve`` named (:attr:`Target.where`).  What crosses is the same
    three things a ``$ref`` conjunct's base already crosses with -- a symbol, a
    :class:`Shape` and where to import it from -- plus §4's naming facts, which cross
    because the branch is named HERE and its declaration is not this module's to read.

    The :class:`Shape` recorded for a branch is the union of the base's and the target
    branch's, the target winning a shared key, which is ``lower.union``'s own reading of
    §4's "a branch composes its own with them": a later reuser of this branch reads one
    map.  The DESCRIPTION is §6's clause 3 at a branch -- silence inherits -- and the one
    it inherits is the target branch's, because that is what the composed document states
    at the branch's own pointer.
    """
    base_shape = mod.shapes[base]
    declared: list[ir.TypeRef] = []
    # **The LIVE branches, and the index is the target's own** -- §5's distribution
    # clause drops a branch whose intersection is provably empty, and
    # :attr:`TargetBranches.dropped` says why the dropped one is skipped rather than
    # filtered out: the index IS the pointer, so renumbering would pair every survivor
    # against the wrong branch node.
    for index, branch in branches.live:
        pointer = _distributed_pointer(where, branches, index)
        if branch.naming is None:
            # §4 "Names" derives a branch's name from its own declaration, and the facts
            # that declaration states were recorded by the module that declared it.  A
            # branch with none is a union base whose branches this run did not name,
            # which is a defect in this compiler rather than in any document -- but the
            # refusal is charged to the document anyway, because the alternative is an
            # exception at a pointer no report names.  0 sites over the portable
            # population.
            return Refusal(
                "allOf",
                pointer,
                f"{branch.symbol} is a branch of {where}'s target and carries none of "
                "section 4's three naming facts, so the class this node's distribution "
                "declares for it has no name to derive: the declaring module records "
                "them with the branch's hop and this run resolved none",
                kind=kind_for("allOf", Position.CONJ),
            )
        # ``refuses`` was deleted at ``adcp-client-python-10l.41``, which replaced the
        # flag with the PRESENCE of ``names.Branch.index``.  Nothing is passed in its
        # place: this docstring's own sentence says the naming facts "were recorded by
        # the module that declared it", so the target branch's hop already carries the
        # index its declaring module gave it, and restating one here would overwrite a
        # recorded fact with this loop's position.
        mod.hops[pointer] = replace(branch.naming, parent=base)
        mod.importing(branch.symbol, branch.where)
        inherited = branch.declares.description
        # §5's intersection clause at a distributed branch: a key the node and this
        # branch both declare is ONE field, and it is declared HERE so that neither base
        # shadows the other (:func:`_intersected_at_a_branch`).
        own = _intersected_at_a_branch(
            asserted, branch, pointer, base_shape.required | branch.declares.required, mod
        )
        if isinstance(own, Refusal):
            return own
        made = declare_object(
            # **The node is the ``$ref`` CONJUNCT**, which is the node of THIS document
            # that names the branch, and it states nothing of its own -- so the branch
            # class gets no ``extra``, no description and no rule of its own, and every
            # fact it carries comes from its two bases.  The node's own ``extra`` and
            # rules are the BASE's and reach the branch by inheritance; reading them
            # again here would state each of them twice.
            reference,
            pointer,
            mod,
            own,
            Shape(
                {**base_shape.properties, **branch.declares.properties},
                base_shape.required | branch.declares.required,
                decided={**base_shape.decided, **branch.declares.decided},
                # The TARGET BRANCH's first, then the base's -- the same order the
                # three lines above give a shared PROPERTY, and for the same reason this
                # docstring already states: "the target wins a shared key, because the
                # target is the branch's own declaration".  This class states no
                # ``additionalProperties`` of its own (the node is the ``$ref``
                # conjunct), so what it DECLARES is what the composed document states at
                # its pointer -- and :func:`declare_object` writes it, so the order the
                # two bases sit in decides nothing.
                extra=stated_extra(branch.declares.extra, base_shape.extra),
                description=inherited,
            ),
            Position.BRANCH,
            bases=(ir.TypeRef(base, local=True), ir.TypeRef(branch.symbol, local=True)),
            description=inherited,
        )
        if isinstance(made, Refusal):
            return made
        declared.append(ir.TypeRef(pointer, local=True))
    # §4's rebuild: the branches subclass the base, so they do not exist while the base is
    # built and the module tells pydantic afterwards.  The same declaration
    # ``lower.union.lower_union`` appends, from the same expression the base's own
    # ``branches`` slot was built from.
    mod.declarations.append(ir.UnionInstall(ir.TypeRef(base, local=True), tuple(declared)))
    return base


def declaration_rule_sources(
    declaration: Mapping[str, Any], position: Position
) -> dict[str, Any]:
    """The rule sources a raw DECLARATION states: ``schema.parse._rule_sources``, asked
    of a declaration.

    An ``allOf`` conjunct is a declaration by §2's own decision, so its rule sources are
    read the way the parser reads a node's -- the table at the conjunct's own position,
    plus the two combinators where every branch states only which keys are present, which
    is a CO-OCCURRENCE the cell cannot answer.  **ONE reading, and two things read it**:
    :func:`lower_composition`'s conjunct screen, which wants the key SET, and
    ``lower.rules.lower_declaration``, which wants the values -- so a conjunct's screen
    and a conjunct's rule tuple cannot come to disagree about which keywords are rules
    there, which is the second copy of a keyword decision §3 forbids.
    """
    from codegen.lower import rules

    sources = rule_sources(position)
    if rules.presence_only(declaration):
        sources |= combinators(position)
    return {k: v for k, v in declaration.items() if k in sources}


def _required(node: Mapping[str, Any], pointer: str) -> list[str] | Refusal:
    req = node.get("required", [])
    if not isinstance(req, list) or not all(isinstance(r, str) for r in req):
        return Refusal(
            "required",
            pointer,
            f"required is {req!r}, not a list of names",
            kind=Kind.VERDICT,
        )
    return req


def _reused(
    key: str,
    inherited_fields: Mapping[str, ir.Field],
    inherited_from: Mapping[str, Target],
    pointer: str,
    mod: Module,
) -> ir.Field | Refusal:
    """The inherited field an annotation-only restatement re-states, importable here.

    A re-used type names symbols, and each one has to be IMPORTABLE from this module or
    the class is an undefined name at import.  **Each is taken from the module that
    DECLARES it** -- :attr:`Target.imports` is the base's whole offer, its own
    declarations beside the declarers of everything it imported -- which is §1's "one
    import path per class, and never a second way to reach the same class": the base's
    import of a symbol and this module's import of the same symbol name one module, so
    there is one path to the class and no re-export anywhere.

    **It read ``Shape.declares`` and refused the rest as a re-export, and that refusal
    is what ``adcp-client-python-81c`` answers.**  The sentence was right about what it
    refused -- importing a symbol FROM the base, which the base only imported, is the
    second path §1 forbids -- and wrong that there was nothing else to do.  The base's
    own import names the declaring module, the run holds it
    (:attr:`Module.imported`), and taking the symbol from there is one import path and
    not a relaxation of anything.

    **Its population was NOT 0, which is this row's own finding.**  The sentence it
    replaced read "0 re-use a type naming a re-exported symbol, so the refusal below
    fires on nothing today", and that figure is stale at ``18474e55``: the PUBLISHED
    bundle reaches it in two documents -- ``core/media-buy-frequency-cap-capability.json``
    at ``/properties/max_impressions_constraints``
    (``FrequencyCapImpressionConstraints``) and ``core/product-signal-targeting-option``
    ``.json`` at ``/properties/signal_ref`` (``SignalRef``).  The patch set for upstream
    #8525 adds the third: ``core/domain-name.json`` is extracted,
    ``core/placement-ref.json``'s ``publisher_domain`` becomes a ``$ref`` to it,
    ``core/placement-selection.json`` composes that base under ``{required:
    [publisher_domain]}``, and the subclass restates the key with the base's type.

    **Measured at this row, both bundles, over the portable set.**  70 keys reach this
    function.  9 take the arm below (the base is this module's own).  61 cross a module
    boundary, and of those 17 re-use a type naming a symbol -- 18 over the patched
    bundle.  The symbols resolve to 5 declaring documents: 13 to
    ``formats/canonical/_base.json``, which is the base itself, and 4 to a document the
    base IMPORTED -- ``core/frequency-cap-impression-constraints.json``,
    ``core/frequency-cap-interval-constraints.json``, ``enums/reach-unit.json`` and
    ``core/signal-ref.json`` -- with ``core/domain-name.json`` the fifth over the patched
    bundle.  0 refuse, over either.

    What is left to refuse is a symbol the base's module neither declares nor imported
    from a document of this bundle -- nothing of the run can name it, so there is no
    module to import it from and no judgement to make about which one.  Population 0
    over both bundles.
    """
    held, source = inherited_fields.get(key), inherited_from.get(key)
    if held is None:
        return Refusal(
            "properties",
            pointer,
            f"{key!r} restates an inherited declaration with nothing but annotations, "
            f"and the base declaring it recorded no decided field for it, so there is "
            f"no type to re-use and lowering the restatement alone would type it Any",
            kind=Kind.VERDICT,
        )
    if source is None or not source.crosses_a_module:
        # **The base is declared in THIS module**, which is §4's union base: a branch
        # composes with it and the base is not a ``$ref`` conjunct, so there is no
        # :class:`Target` for it and nothing to import -- the field's type names this
        # module's own declarations by pointer and ``lower/names.py`` binds them.  The
        # import screen below is about crossing a module boundary, and this does not
        # cross one.
        #
        # **TWO carriers, ONE question** (``adcp-client-python-10l.43``).  A base reached
        # through a LOCAL ``$ref`` conjunct is in this module too, and it arrives with a
        # :class:`Target` -- ``compiler.local_target``'s, wrapping the two records
        # ``declare_object`` wrote for a node of THIS document -- so ``source is None``
        # stopped being the whole of "the base is here".  The question is
        # :attr:`Target.crosses_a_module` and it is stated on the carrier, once.
        # Measured: ``core/registry-event.json`` composes ``#/$defs/propertyPayload`` at
        # ``/oneOf/0/properties/payload/allOf/0`` and re-uses its ``classification``,
        # whose type names ``/$defs/classification`` -- a POINTER this module declares and
        # ``lower/names.py`` binds, which the screen below reported as "symbols no
        # document this run lowered declares".
        #
        # **Re-measured at ``adcp-client-python-81c``: 9 branches reach here**, over both
        # bundles -- 6 on ``account/list-account-changes-response.json`` and 3 on
        # ``core/brand-response-authorization-result.json``.  This read "0 branches reach
        # here, so this arm is written for the first document that does rather than
        # discovered by it", which was true when it was written and is not now; the arm
        # is exercised and ``/properties/reason``'s re-used type reaches it still
        # carrying a POINTER, which is exactly the case it declines to screen.
        return held
    wanted = ir.symbols(held.type)
    unplaceable = sorted(wanted - set(source.imports))
    if unplaceable:
        return Refusal(
            "properties",
            pointer,
            f"{key!r} re-uses the field of {source.symbol}, whose type names "
            f"{unplaceable} -- symbols no document this run lowered declares, so there "
            f"is no module to import them from",
            kind=Kind.VERDICT,
        )
    for symbol in sorted(wanted):
        mod.importing(symbol, source.imports[symbol])
    return held


def _constraining(node: dict) -> dict:
    """What a declaration says about the INSTANCE.

    ``default``, ``description`` and every other key whose CELL carries nothing
    annotate the node without constraining anything, so a declaration holding only
    those says nothing and cannot narrow.  That is precisely the shadow: the three
    ``responsive_creative.json`` restatements are a ``default`` plus a
    ``description`` and nothing else.

    Read at PROP, which is the position every caller asks it at: a restatement is a
    property's declaration against the base's.
    """
    return declaring(node, Position.PROP)


#: The annotations a FIELD renders, so the two a restatement can differ about in a way
#: the comparison sees.  :func:`fields` reads exactly these off the declaration --
#: ``description`` into ``Field(description=...)`` and ``default`` into the field's
#: default -- and the rest of the keys whose cell carries nothing (``title``,
#: ``$comment``,
#: ``$schema``) reach nothing on a field, so a restatement differing only in one of
#: those renders the same field and states nothing to anyone.
RENDERED = ("default", "description")


def _annotates_differently(child: dict, base: dict) -> bool:
    """Would the two declarations render a different FIELD?

    Asked only of a restatement that says the same thing about the instance, where it
    is the whole of the difference.  An annotation the child does not state counts as
    a difference, because the child's silence is itself an answer: the field then
    carries whatever its own node resolves -- for a bare ``$ref``, the target's --
    and not the base's.
    """
    return any(child.get(k) != base.get(k) for k in RENDERED)


#: The ordering keywords, and the direction a NARROWER value moves in.  ``+1`` means a
#: narrower restatement states a LARGER number (a floor rises), ``-1`` a smaller one (a
#: ceiling falls).  ``exclusiveMinimum``/``exclusiveMaximum`` are draft-07's numeric
#: form and compare the same way as the inclusive pair; draft-04's boolean form does not
#: appear in this bundle and would not compare, so a non-number refuses below.
_BOUNDS = {
    "minimum": 1,
    "exclusiveMinimum": 1,
    "minLength": 1,
    "minItems": 1,
    "minProperties": 1,
    "maximum": -1,
    "exclusiveMaximum": -1,
    "maxLength": -1,
    "maxItems": -1,
    "maxProperties": -1,
}


class Holds(StrEnum):
    """How a subschema-valued keyword holds the subschemas it holds."""

    #: One subschema, which is the whole value: ``items`` in draft-07's single-schema
    #: form.
    ONE = "one"
    #: One subschema per NAME: ``properties``, whose value is a key -> schema map.
    PER_KEY = "per key"


#: **The subschema-valued keywords §2's intersection rule recurses into, and how each
#: holds its subschemas.**  §2's "this holds at ANY DEPTH, including an overlay under
#: ``items``" and §5's ``properties`` row are the two sentences, and this is the ONE
#: declaration the readers take them from: :func:`_at_least_as_tight`, which asks whether
#: the pair at such a keyword composes, and :func:`_intersection`, which writes the
#: composition at both of them.  The pair of keywords was spelled in both functions,
#: which is the second copy of one keyword decision ``docs/plan/architecture.md`` §3
#: forbids.
#:
#: **The GAP at ``items`` is CLOSED** (``adcp-client-python-10l.21``, seventh
#: instalment).  The predicate recursed there and the merge took the CHILD's element
#: declaration whole, so a base that declares its element as a ``$ref`` had the
#: reference dropped and the restatement's bare overlay stood alone -- 14 sites share
#: ``items`` with different values and 8 of them lost a base's element declaration that
#: way, which refused ``core/assets/vast-asset.json``,
#: ``core/assets/daast-asset.json`` and the 9 documents chained behind them.
#: :func:`_intersection` writes the composition at ``Holds.ONE`` now, the base's
#: reference survives it as a ``$ref`` CONJUNCT where both sides declare an object, and
#: §8's pairing carries the enclosing statement DOWN by key instead of dropping it at
#: the first hop that moves to another instance (``adcp.types._base.applied_schema``) so
#: that the composition can be graded.  Measured: emitted 897 -> 908, 0 documents
#: stopped, 0 previously-emitted module modified, 0 facts red in any direction.
#:
#: Not the table's ``descends`` column, which is a wider reading: that column answers
#: where the subschemas a structural keyword holds SIT (``codegen.keywords.descends_at``,
#: for the parser and the reference walk), and it holds ``patternProperties``,
#: ``definitions``, the combinators and the conditionals too -- keywords §2's rule has
#: no recursion for, and whose values this rule would then have to tell apart by shape
#: anyway.  What this names is the narrower fact: the two keywords whose composition IS
#: the rule applied one level down.
HOLDS: Mapping[str, Holds] = {"items": Holds.ONE, "properties": Holds.PER_KEY}


def _at_least_as_tight(
    keyword: str, c: Any, b: Any, resolve: Callable[[str], dict | None] | None = None
) -> bool:
    """Does ``c`` say at least what ``b`` says about the instance, at ``keyword``?

    Section 2's intersection rule, per keyword and in the three spellings it names: "an enum
    is the intersection of the members, a bound is the tighter one, a ``const`` must
    agree", plus "this holds at ANY DEPTH, including an overlay under ``items``".  The
    predicate is what :func:`_restatement` needs and all it needs: where the child's
    statement subsumes the base's, the child IS the intersection and the field decided
    from it carries it.

    Equality first, because it is the dominant case and because every rung below is a
    statement about two DIFFERENT values.  A keyword this cannot read is not tight
    enough and the caller refuses -- never admitted on the ground that it is probably
    fine, which would be a model wider than its document at a keyword nobody looked at.
    """
    if c == b:
        return True
    if keyword == "enum":
        return (
            isinstance(c, list) and isinstance(b, list) and all(member in b for member in c)
        )
    if keyword == "required":
        # **A ``required`` pair is ALWAYS ordered, because its composition is the UNION
        # and neither side can loosen it** -- which is §2's intersection rule read at this
        # keyword and not a new rung.  ``required`` names the keys an instance must
        # supply, ``allOf`` applies both conjuncts to that same instance, so an instance
        # satisfying the composition supplies every key EITHER list names: the composed
        # accepted set is the intersection of the two, spelled as the union of the two
        # lists (:func:`_intersection`'s own arm, which is where the union is written).
        #
        # So a child naming FEWER keys than the base is not a loosening, for exactly the
        # reason silence is not one (:func:`_restatement`): under ``allOf`` the base's
        # ``required`` applies wherever the child's does not name a key.  Without this
        # arm two different lists share a keyword neither ordering reads, the pair is
        # unordered and the caller refuses a document whose composition §2 decides.
        #
        # Measured over the 1,054 portable documents: it is the whole of what refused
        # ``brand/verify-brand-claim-response.json`` and
        # ``brand/verify-brand-claims-response.json`` at
        # ``/definitions/signed_response/allOf/1/properties/payload`` -- the restatement
        # requires ``task`` and ``response``, ``core/response-payload-jws-envelope.json``'s
        # ``response_payload`` requires eight, and ``properties`` and ``type`` both
        # ordered (``adcp-client-python-97w``).
        #
        #
        # **It is also the only keyword that blocked the ``action_binding`` restatement in
        # ``core/audience-evidence-selection.json`` and
        # ``governance/check-governance-response.json``** (``adcp-client-python-10l.82``),
        # whose refusals were REPORTED on ``anyOf`` and on ``additionalProperties``
        # because :func:`_disagreeing` names the first key of the whole disagreeing set
        # and the base states both of those where the child is silent -- silence that is
        # not a loosening and was never the obstruction.  One shape under two keyword
        # headings, which is why a row grouped by ``Refusal.keyword`` is grouped by a
        # report and not by a cause.
        #
        # A non-list is draft-07-invalid at this keyword and falls to False with
        # everything else this predicate cannot read.
        return isinstance(c, list) and isinstance(b, list)
    # **``contains`` HAS NO ARM, DELIBERATELY, and that is the one clause of §5's "Two
    # ARRAY declarations under one ``allOf``" this compiler does not write**
    # (``adcp-client-python-10l.83``).  The row: "Every ``contains`` is kept: two
    # ``contains`` predicates are two independent ``AtLeastOne`` rules over the same
    # value, never merged into one, because ``contains: A`` and ``contains: B`` demand a
    # member satisfying each and a single merged predicate would demand one member
    # satisfying both."
    #
    # A DECLARATION holds one ``contains`` key, so two facts cannot be spelled in the
    # merged declaration :func:`_intersection` hands back to the parser; keeping both
    # means ``lower.rules.on_a_value`` taking several predicates where its signature takes
    # one (``contains: Any = None``).  Falling through to the closing ``False`` is
    # therefore the right answer for now and not an oversight: the caller refuses BY NAME
    # on this keyword -- which keeps both facts visible and merges nothing, the
    # prohibition the clause exists for -- rather than taking either predicate and
    # dropping the other silently.
    #
    # **Measured over the 1,054 portable documents: 0 property pairs state ``contains`` on
    # both sides**, so the signature change would be a derivation matching nothing.  The
    # bundle's only two declarations of one ``contains`` are at
    # ``creative/preview-creative-request.json#/allOf/6/not/anyOf/2/properties/requests``,
    # under a ``not`` -- a RULE position §5's ``not`` row owns and this rule never
    # reaches.  The first document to compose two is what buys the change.
    if keyword in _BOUNDS:
        if isinstance(c, bool) or isinstance(b, bool):
            return False  # draft-04's boolean exclusiveMinimum: a different keyword
        if not isinstance(c, int | float) or not isinstance(b, int | float):
            return False
        return c >= b if _BOUNDS[keyword] > 0 else c <= b
    if keyword == "$ref":
        # **Two whole-content references are ordered by their TARGETS and by nothing
        # else**, which is :meth:`Module.resolve_node`'s one documented site: "two
        # declarations that are each a bare ``$ref`` state the same KIND of thing about
        # an instance and whether one narrows the other is a fact about the two TARGETS,
        # which no amount of reading the two references can answer."
        #
        # :func:`_restatement` reads a bare reference through :func:`_dereferenced`
        # before it compares anything, so at the NODE level this question is already
        # answered.  It arrives here from one level down: :func:`_intersection`'s
        # composition at ``items`` meets two element declarations that are each a bare
        # reference, and the keyword they SHARE is ``$ref`` itself.  Without this arm the
        # pair is unordered, the loop takes the BASE's reference as the tighter value,
        # and the composition is LOOSER than the restatement -- measured on
        # ``core/media-buy-frequency-cap-requirement.json``, whose
        # ``/allOf/1/properties/supported_control_modes/items`` references a one-member
        # enumeration where the base it composes references a three-member one: the
        # field left the class entirely, and three emitted modules changed.  6 sites,
        # all in that document.
        #
        # ``None`` from the resolver is every undecidable case at once -- a URI naming no
        # document, a pointer naming no node, a target that refused, a reference local to
        # the document being written -- and it answers False here, which is this
        # predicate's own rule: "a keyword this cannot read is not tight enough and the
        # caller refuses."  A FRAGMENT and a pointer local to a BASE's document are no
        # longer in that list and are read like any other reference
        # (:meth:`Module.resolve_node`, ``adcp-client-python-10l.72``).
        if resolve is None or not isinstance(c, str) or not isinstance(b, str):
            return False
        target_c, target_b = resolve(c), resolve(b)
        return (
            isinstance(target_c, dict)
            and isinstance(target_b, dict)
            and _restatement(target_c, target_b, resolve) is not None
        )
    held = HOLDS.get(keyword)
    if held is not None:
        # **An overlay under a SUBSCHEMA-VALUED keyword: the rule holds at any depth,
        # and the recursion is the rule rather than a second one** (§2, "this holds at
        # ANY DEPTH, including an overlay under ``items``"; §5's ``properties`` row at
        # CONJ, "A property two conjuncts declare is one field: its constraints intersect
        # by §2, and two object declarations compose as an ``allOf`` of the two at that
        # property").  So the question asked of each held subschema is the question asked
        # of the node: is the child's declaration compatible with the base's.
        #
        # A key only the CHILD declares says something more about the same instance, and
        # a key only the BASE declares is one the child is silent about -- and silence is
        # not a loosening under ``allOf`` (:func:`_restatement`), because the base's
        # declaration applies wherever the child is quiet.  Neither can make the
        # composition looser, so only the shared keys are asked about.
        #
        # A LIST-valued ``items`` is draft-07's tuple form, where position matters and
        # two different lists are not ordered by this predicate -- so it falls through
        # to False with every other non-mapping value.
        if not isinstance(c, dict) or not isinstance(b, dict):
            return False
        pairs = [(c, b)] if held is Holds.ONE else [(c[k], b[k]) for k in set(c) & set(b)]
        return all(
            isinstance(x, dict)
            and isinstance(y, dict)
            and _restatement(x, y, resolve) is not None
            for x, y in pairs
        )
    return False


def _intersection(
    child: dict, base: dict, resolve: Callable[[str], dict | None] | None = None
) -> dict:
    """The declaration a NARROWING restatement's field is decided from.

    Section 2 in its own words: "where composed schemas constrain the same property, the field
    carries the INTERSECTION".  Under ``allOf`` both declarations apply to the same
    instance, so every keyword either one states is the composed node's -- the child's
    value where both state one (:func:`_restatement` has already decided it is at least
    as tight), the base's where only the base does.

    **The RENDERED annotations compose the same way, and §6's own rule says which wins:**
    the child's where it states one (a document's own declaration carries the
    description at its own pointer) and the base's where it is silent (clause 3, "silence
    inherits").  That is the gap-fill ``harness._composed`` performs on the DOCUMENT side,
    so reading it the other way here is the two halves disagreeing: measured on
    ``core/forecast-rate-range.json``, whose ``low``/``mid``/``high`` narrow
    ``core/forecast-range.json``'s bounds and state no description, where the child
    alone reported the base's three descriptions ``missing``.

    **"Silent" means silent AFTER RESOLUTION, and that is the whole of §6's clause 2.**
    A child that is a bare ``$ref`` states no description in the document's TEXT and
    states its target's at the pointer the comparison grades, because ``bundle.record``
    inlines the target there -- so gap-filling the base's over it puts a description the
    document does not carry at a pointer the document declares itself.  Measured at 17
    ``differs``, every one ``/properties/context/description``: a response root composing
    ``core/protocol-envelope.json``, whose envelope states the long "Relationship to
    per-task body-level ``context`` declarations" text as a ``$ref`` sibling while the
    document's own node resolves to ``core/context.json``'s own short text.
    :func:`_dereferenced` is what makes the two readings one.

    **This is a no-op at every site that narrowed before section 2's intersection rule landed**,
    and that is why it is safe: the old predicate required the child to state every
    keyword the base states, so ``{**base, **child}`` was ``child``.  What it changes is
    the newly-admitted narrowings, where the two state DIFFERENT keywords and the child
    alone would be wider than the document: measured on
    ``core/product-execution-requirement.json`` at
    ``/oneOf/2/properties/connection/allOf/1/properties/required_for``, whose
    restatement is a bare ``{"contains": {"const": "create_media_buy"}}`` over a base's
    ``{"type": "array", "items": {...}, "uniqueItems": true}`` -- decided alone it is a
    TYPELESS node the array row cannot read, and decided as the intersection it is an
    array that carries the ``contains`` (``lower.containers._ARRAY_CLAIMS``).

    **A keyword is dropped from the base where the child states the same AXIS and not
    only the same KEY**, which is :data:`_AXES` and is what keeps the merge from writing
    a node no row can read.  ``core/canonical-media-buy-action.json`` at
    ``/oneOf/0/properties/task`` is the measured one: the base states
    ``{"type": "string", "enum": [3 members]}`` and the branch restates
    ``{"const": "control_media_buy"}``, and a key-wise merge keeps BOTH -- a wide
    ``enum`` beside the ``const`` that narrows it, which is a shape no document states
    and which refused on ``const`` with "a later row does".
    """
    c, b = _constraining(child), _constraining(base)
    covered = set(c)
    for axis in _AXES:
        if covered & axis:
            covered |= axis
    if covered - {"$ref"}:
        # **A ``$ref`` is not merged into a child that constrains the instance
        # itself, and that is §9's rule rather than a preference.**  A ``$ref`` is
        # the WHOLE schema of the node it sits at, so it is not one axis beside
        # another: merging the base's into a child stating a ``const`` writes
        # ``{"$ref": T, "const": v}``, which draft-07 reads as ``T`` ALONE.  That is a
        # node no document states, and §9 names it twice -- "never refuse a keyword the
        # walk itself inserted" and "do not decide a position the bundle does not hold
        # from a view of it".
        #
        # The consequence used to be a REFUSAL on the inserted co-occurrence: the
        # 5 documents the epic lists as "const beside $ref" refused as verdicts at a
        # pointer whose own node states no ``$ref`` at all --
        # ``core/compact-task-submitted.json#/properties/status`` is
        # ``{"type": "string", "const": "submitted"}``, and the ``$ref`` came from
        # ``core/protocol-envelope.json``'s declaration of the same key.  With §5's
        # ``$ref`` row now compiling a constraining sibling to nothing, the same merge
        # DROPS the ``const`` instead, and the comparison reports the document's own
        # fact missing at that very pointer -- measured on all 5.
        #
        # So the base's ``$ref`` is left out and the field is decided from the child's
        # own declaration.  The model is then LOOSER than the base's conjunct and §2
        # permits exactly that ("a model may be looser than its document without being
        # wrong, because the schema half already refused the payload"); what it forbids
        # is tighter, and dropping a base's reference cannot tighten anything.
        covered.add("$ref")
    merged = {**{k: v for k, v in b.items() if k not in covered}, **c}
    # **At a keyword BOTH state, the TIGHTER value and not the child's**, which is what
    # makes this function symmetric in its constraining content rather than only in the
    # direction :func:`_restatement` admits.  ``declare`` asks the predicate in both
    # directions and then merges in whichever one narrowed, so a merge that preferred the
    # first argument would make the result a function of which view the walk read first
    # -- the "last wins" this rule exists to have no reading of.
    for kw in set(c) & set(b):
        if (
            HOLDS.get(kw) is Holds.PER_KEY
            and isinstance(c[kw], dict)
            and isinstance(b[kw], dict)
        ):
            # **At ``properties`` neither value is the tighter one WHOLESALE, and §5's
            # row at CONJ says why: "two object declarations compose as an ``allOf`` of
            # the two at that property".**  The composition is therefore taken PER KEY
            # -- this same intersection, one level down -- and a key only one of them
            # declares is carried through as it stands, because under ``allOf`` every
            # key either object declares constrains the same instance.
            #
            # Taking the child's object whole is what this arm replaces, and it is the
            # shadow §2 forbids: ``core/assets/url-asset.json`` restates ``location`` as
            # ``{"properties": {"field": {"const": "url"}}}`` over
            # ``core/macro-declaration.json``'s three-property object, so the child's
            # object alone drops ``occurrence`` and ``context`` -- two properties the
            # base REQUIRES -- and the model would accept a payload the document
            # refuses.  Per key, ``field`` intersects to ``{"type": "string", "const":
            # "url"}`` (``"url"`` is a member of the base's five-member ``enum``, so
            # ``_AXES`` lets the ``const`` replace it), and the other two are the
            # base's.
            merged[kw] = {
                **b[kw],
                **c[kw],
                **{
                    k: _intersection(c[kw][k], b[kw][k], resolve)
                    for k in set(c[kw]) & set(b[kw])
                    if isinstance(c[kw][k], dict) and isinstance(b[kw][k], dict)
                },
            }
        elif (
            HOLDS.get(kw) is Holds.ONE
            and isinstance(c[kw], dict)
            and isinstance(b[kw], dict)
        ):
            # **At ``items`` the composition is written too, for the reason the
            # ``properties`` arm above gives**: §2's intersection rule "holds at ANY
            # DEPTH, including an overlay under ``items``", so the element declaration
            # of the composition is the intersection of the two element declarations
            # and not the tighter one WHOLESALE.  :data:`HOLDS` is the one declaration
            # of which keywords recurse and the two arms are now the same rule read at
            # ``Holds.ONE`` and at ``Holds.PER_KEY``.
            #
            # Taking the child's element whole is what this arm replaces, and it is the
            # same shadow: ``core/assets/vast-asset.json``'s ``/oneOf/0`` restates
            # ``macro_declarations`` as ``{"items": {"properties": {"location": ...}}}``
            # over the root's ``{"items": {"$ref": T}}``, so the child's element alone
            # is a TYPELESS node declaring one property -- every fact behind ``T``
            # dropped -- and the array row refuses it on ``properties``.  Measured
            # before this arm: 14 sites share ``items`` with different values and 8 of
            # them lose a base's element declaration, which refused
            # ``core/assets/vast-asset.json``, ``core/assets/daast-asset.json`` and the
            # 9 documents chained behind them.
            #
            # A LIST-valued ``items`` is draft-07's tuple form, where position matters
            # and the two lists are not composed by this rule, so it falls through to
            # the tightness arm below with every other non-mapping value.
            merged[kw] = _intersection(c[kw], b[kw], resolve)
        elif kw == "required" and isinstance(c[kw], list) and isinstance(b[kw], list):
            # **At ``required`` neither value is the tighter one either, and the
            # composition is the UNION** -- §2's intersection rule read at the one keyword
            # whose value is a set of KEYS rather than a constraint on one instance.
            # ``allOf`` applies both conjuncts to the same instance, so an instance
            # satisfying the composition supplies every key either list names, and the
            # union is what the composed declaration states.
            #
            # **This is the arm the predicate's own ``required`` rung needs beside it**
            # (:func:`_at_least_as_tight`): that rung says the pair is always ordered, and
            # it is only sound because the composition written here is the union.  Left to
            # the tightness fallback below, the merge would take the BASE's list and drop
            # the keys the child requires -- a model looser than its document at the
            # keyword the document was most explicit about.  Measured on
            # ``brand/verify-brand-claim-response.json``, whose restatement requires
            # ``task`` and ``response`` over ``response_payload``'s eight: the union is
            # ten, the base's alone is eight, and the child's alone is two
            # (``adcp-client-python-97w``).
            #
            # The BASE's order first and the child's new keys appended, so the composed
            # list is document-ordered and a key either side already named keeps its
            # place.  A non-list falls to the tightness arm with every other value this
            # rule has no composition for.
            merged[kw] = [*b[kw], *(k for k in c[kw] if k not in b[kw])]
        elif kw == "uniqueItems":
            # **``uniqueItems`` HOLDS WHERE EITHER CONJUNCT STATES IT** -- §5's "Two ARRAY
            # declarations under one ``allOf``" (decided 2026-10-29), "because a
            # conjunction of constraints is satisfied only by an instance satisfying
            # both".  So it is an OR and neither value is "the tighter one": the tightness
            # fallthrough below reads an unordered pair as the BASE's, which takes
            # ``false`` over a base's ``true`` in one direction and is the one direction
            # §2 forbids -- a model admitting duplicates the document refuses.
            #
            # The ASYMMETRIC case needs no arm and never did: a key only one declaration
            # states is carried through by the merge above, so the OR already held
            # wherever one side was silent.  Measured over the 1,054 portable documents:
            # **0 property pairs state the keyword on both sides**, so this arm is the one
            # written for the first one rather than a derivation matching something.
            merged[kw] = bool(c[kw]) or bool(b[kw])
        elif not _at_least_as_tight(kw, c[kw], b[kw], resolve):
            merged[kw] = b[kw]
    # **The base's reference SURVIVES as a ``$ref`` CONJUNCT where both declarations
    # declare ``properties``**, which is §5's ``properties`` row at CONJ read where the
    # base spells its whole content as a reference: "two object declarations compose as
    # an ``allOf`` of the two at that property".  The arm above drops the base's
    # ``$ref`` because draft-07 reads ``{"$ref": T, "const": v}`` as ``T`` alone -- and
    # that is right for a child constraining the instance ITSELF, where there is no
    # spelling of the conjunction at the node.  Where both sides declare an object there
    # is one, and it is the document's own: an ``allOf`` member.
    #
    # Appended BESIDE the child's own keywords, ``{**child, "allOf": [*child's
    # conjuncts, base]}``, and never as ``{"allOf": [base, child]}``.  Wrapped the other
    # way the child's declarations sit under a synthetic ``…/allOf/1`` and every nested
    # class is stamped at a pointer the document does not have, so
    # ``adcp.types._base.applied_schema`` raises ``KeyError: 'allOf'`` when the pair is
    # graded.  Appended, only the conjunct's OWN index is synthetic and that costs
    # nothing: a bare ``$ref`` conjunct declares no class, so no pointer below it is
    # ever stamped.
    #
    # The measured site is ``core/assets/vast-asset.json`` and
    # ``core/assets/daast-asset.json`` at ``/oneOf/N/properties/macro_declarations``,
    # whose element overlay ``{"properties": {"location": ...}}`` composes with the
    # root's ``{"$ref": core/macro-declaration.json}``.
    # ``core/assets/display-tag-asset.json`` is the control: it SPELLS the same
    # composition in its own branch text (:func:`_conjoins`), its element declares
    # ``allOf`` and not ``properties``, so this arm does not fire and the document's own
    # conjunct list is what stands.
    #
    # **"Declares an object" is not "declares ``properties``", and reading it that way
    # left the arm's own rule unwritten for two further shapes** (``…10l.82``).  The
    # clause is about a CONTAINER the two declarations agree on -- §5's ``properties``
    # row at CONJ for an object, §2's "this holds at ANY DEPTH, including an overlay
    # under ``items``" for an array -- and a container is declared by any of its
    # keywords, not by one of them.  :func:`_container_kind` is the reading, and it is
    # what makes the two measured shapes below the same site as the two above:
    #
    # * ``core/signal-coverage-forecast.json`` at
    #   ``/properties/points/items/allOf/1/properties/dimensions``, whose restatement is
    #   a bare ``{"contains": {...}}`` over ``core/forecast-point.json``'s ``{"$ref":
    #   core/forecast-point-dimensions.json}``.  Both declare an ARRAY; the reference
    #   dropped, the merge is a TYPELESS node and the ``contains`` row refused it for
    #   having no type to lower onto -- a type the document states behind the reference.
    # * ``media-buy/get-reporting-status-response.json`` at
    #   ``/oneOf/0/oneOf/1/properties/pagination``, whose restatement is ``{"type":
    #   "object", "required": ["has_more", "total_count"]}`` over a base's bare
    #   reference.  Both declare an OBJECT and neither name is a property the merge
    #   declares, so §5's ``required`` row refused it as "a presence rule with no field"
    #   -- the two fields being behind the dropped reference.
    #
    # The ``const``-beside-``$ref`` five are the control and are UNCHANGED: a ``{"type":
    # "string", "const": v}`` restatement declares no container, so the arm does not
    # fire, the reference is dropped as the paragraph above decides, and the model is
    # looser than the base's conjunct where §2 permits it.
    conjoined_the_reference = (
        set(b) == {"$ref"}
        and "$ref" not in merged
        and _container_kind(c) is not None
        and _container_kind(c) == _container_kind(_constraining(_dereferenced(base, resolve)))
    )
    # **The APPEND IS IDEMPOTENT, because ``allOf`` is: a conjunct already in the list
    # states nothing a second time.**  §2's rule is "composition merges by intersection"
    # and §5's ``allOf`` row reads every member as applying to the same instance, so
    # ``A ∧ A`` is ``A`` and a conjunct list that names one member twice says exactly
    # what the list naming it once says.  The list is still a LIST and not a set -- the
    # paragraph above decides the ORDER, and the pointer a nested class is stamped at
    # depends on it -- so what is written here is idempotence at the one member this arm
    # appends, not a dedup of the list.
    #
    # **Why the arm fires twice at one node, which is the defect this clause closes**
    # (``adcp-client-python-10l.98``).  Two declarations can reach one node with the SAME
    # bare reference at the same key, and each is a separate, correct merge: the node's
    # OWN declaration meets a conjunct's in :func:`declare`, and the result then meets the
    # INHERITED one in the restatement loop.  Both merges see ``b == {"$ref": T}``, both
    # satisfy the gate -- the first append leaves the reference under ``allOf`` and not
    # under ``$ref``, so ``"$ref" not in merged`` still holds -- and the second wrote
    # ``{"allOf": [{"$ref": T}, {"$ref": T}]}``.
    #
    # That is a node NO DOCUMENT STATES, and §9 is why it must not be written rather than
    # repaired downstream: "do not decide a position the bundle does not hold from a view
    # of it".  Its visible consequence was a base list naming one class twice, which
    # Python refuses to build -- but the base list is the SYMPTOM and the declaration is
    # the defect, so a dedup beside ``dispatching_bases`` would have left the malformed
    # declaration for §8's document-side fold and for every refusal pointer below it.
    #
    # Measured over the 1,054 portable documents: the arm fired on an already-present
    # conjunct at 4 merges, over 2 nodes, both of them ``core/indicator.json`` reached
    # through ``core/indicator-bearing.json`` beside a node that declares the same
    # ``items`` reference itself --
    # ``creative/list-creatives-response.json#/properties/creatives/items/properties/assignments/properties/assigned_packages/items``
    # and
    # ``media-buy/get-media-buys-response.json#/properties/media_buys/items/properties/packages/items/properties/creative_approvals/items``.
    # The second is not in the committed tree, which is why one unimportable module was
    # found and not two.
    #
    # The equality is on the CONJUNCT this arm would write and not on the target it names:
    # the claim is "this arm has already written this member", which is the one claim
    # idempotence needs.  A conjunct carrying the same reference with a SIBLING is a
    # different declaration and §5's ``$ref`` row reads it differently; 0 of the 4
    # measured sites is that shape, so no site rests on the wider reading.
    if conjoined_the_reference:
        own_conjuncts = merged.get("allOf")
        own_conjuncts = own_conjuncts if isinstance(own_conjuncts, list) else []
        if {"$ref": b["$ref"]} not in own_conjuncts:
            merged["allOf"] = [*own_conjuncts, {"$ref": b["$ref"]}]
    resolved = _dereferenced(child, resolve)
    # **The BASE is gap-filled THROUGH ITS OWN REFERENCE, for the same reason the child
    # is read through one.**  §6's description-authority clause 3 is "silence
    # inherits", and silence means silent AFTER RESOLUTION on both sides: a base
    # declaring a key as a bare ``$ref`` states its target's annotations at that
    # pointer, because ``bundle.record`` inlines the target there and
    # ``harness._composed`` folds the conjunct in -- so reading the base's own TEXT
    # alone reports the composed document's description missing.
    #
    # Measured on ``media-buy/control-media-buy-response.json`` at
    # ``/oneOf/0/properties/warnings/items/properties/code``: ``core/warning.json``
    # declares ``code`` as ``{"$ref": "enums/warning-code.json"}`` and nothing else, the
    # conjunct restates ``{"const": "inventory_shortfall_forecast"}``, and the
    # description the comparison grades is ``warning-code.json``'s own root one.  2
    # pairs, both of them ``/properties/code/description``.
    # Gated on the base's reference having been DROPPED above, and the gate is
    # measured: read unconditionally, the base's target annotations also reach a
    # restatement whose own node resolves to something of its own, which is §6 clause
    # 2's case and the 17 ``differs`` :func:`_restatement` records -- re-measured here
    # at 11 extra red pairs over the three checks.  Where the reference was dropped
    # there is nothing of the base's left for the child to disagree with, so the
    # annotation is the only thing the base still contributes.
    # **And the base's OWN annotation sibling wins over its target's**, which is §5's
    # ``$ref`` row ("an annotation sibling → the sibling's description wins") and
    # architecture §13 item 2's settled reading, applied one level up.  Measured on
    # ``core/protocol-envelope.json``, whose ``status`` is
    # ``{"$ref": "core/task-status.json", "description": "Current AdCP task state or
    # structured outcome..."}``: read target-first, 11 pairs reported the TARGET's
    # description where the composed document states the envelope's own.
    # The gate reads "the base's reference reaches the composed node NOWHERE", so the
    # conjunct arm above satisfies it the way a surviving ``$ref`` key does: where the
    # reference is still there, the base's own declaration is what applies and the
    # child has something to disagree with, which is this gate's own reason.
    based = (
        {**_dereferenced(base, resolve), **base}
        if "$ref" in b and "$ref" not in merged and not conjoined_the_reference
        else base
    )
    annotated = {
        **{k: v for k, v in based.items() if k in RENDERED and k not in resolved},
        **{k: v for k, v in child.items() if k not in merged},
    }
    return {**annotated, **merged}


#: Keywords that say the SAME KIND of thing about an instance, so a child stating one of
#: them answers for every member of the set and the base's are not merged in beside it.
#:
#: One set, ``{"const", "enum"}``: a ``const`` is a one-member vocabulary (the rewrite
#: :func:`_as_enum` makes for the tightness predicate), so a ``const`` that narrows a
#: base's ``enum`` REPLACES it rather than joining it.  The bounds are deliberately NOT
#: axes: ``minItems`` and ``maxItems`` constrain the same instance from opposite sides
#: and a child stating one says nothing about the other, so merging the base's is
#: correct and is what section 2's "a bound is the tighter one" means per keyword.
_AXES: tuple[frozenset[str], ...] = (frozenset({"const", "enum"}),)


#: **The keywords that DECLARE a container, by the container they declare it to be.**
#: §5's object and array sections are the two lists and this is a reading of them: every
#: keyword whose row constrains an object is in the first set and every keyword whose row
#: constrains an array is in the second, so a declaration stating any of them has said
#: which container the instance is -- as surely as a ``type`` word does, and §8's own
#: comparison makes the same derivation on the document side.
#:
#: Read by :func:`_container_kind` and by nothing else.  Not a second copy of
#: :data:`HOLDS`, which names the two keywords §2's intersection RECURSES into; this names
#: the wider fact that a keyword belongs to a container's row group, which is what decides
#: whether two declarations are two declarations of ONE container.
_CONTAINER_KEYWORDS: Mapping[str, frozenset[str]] = {
    "object": frozenset(
        {
            "properties",
            "required",
            "additionalProperties",
            "patternProperties",
            "propertyNames",
            "minProperties",
            "maxProperties",
            "dependencies",
        }
    ),
    "array": frozenset(
        {"items", "additionalItems", "contains", "minItems", "maxItems", "uniqueItems"}
    ),
}


def _container_kind(constraining: Mapping[str, Any]) -> str | None:
    """Which container a declaration declares -- ``"object"``, ``"array"`` or neither.

    The ``type`` word where it states one, and otherwise the keyword group its own
    keywords fall in (:data:`_CONTAINER_KEYWORDS`): a node stating ``contains`` has said
    the instance is an array as surely as ``type: array`` does, and draft-07's keyword
    groups are what make that an entailment rather than a guess.

    ``None`` where the declaration names neither container and where it names BOTH --
    a ``type`` list spanning the two, or a node stating ``properties`` beside ``items``.
    Both are declarations this cannot read as one container, and the caller's rule is
    that two declarations compose as a conjunct only where they agree on which container
    they are about.
    """
    words = _type_words(constraining.get("type")) & {"object", "array"}
    if len(words) == 1:
        return next(iter(words))
    if words:
        return None
    found = {kind for kind, group in _CONTAINER_KEYWORDS.items() if group & set(constraining)}
    return next(iter(found)) if len(found) == 1 else None


def _type_words(stated: Any) -> frozenset[str]:
    """A ``type`` keyword's words as a set: one word, a list of words, or nothing.

    ``frozenset()`` for a ``type`` the node does not state and for one whose value is
    neither a word nor a list of them, which is what makes :func:`_provably_empty`
    answer "not provably" rather than "empty" for a malformed declaration.
    """
    if isinstance(stated, str):
        return frozenset({stated})
    if isinstance(stated, list):
        return frozenset(w for w in stated if isinstance(w, str))
    return frozenset()


def _provably_empty(child: dict, base: dict) -> str | None:
    """The keyword at which two declarations of ONE property intersect to NOTHING, or
    ``None`` where this cannot prove they do.

    §5's ``$ref`` row at CONJ, distribution clause: "A distributed branch whose
    intersection is EMPTY is DROPPED ... **The emptiness must be PROVED from the pins the
    two sides state** -- disjoint ``const``\\ s, disjoint ``enum``\\ s, disjoint type
    words -- which is the same test the empty-intersection row names; an intersection
    this compiler cannot compute is the restatement row and not this one."

    **That last clause is the whole of why this is a predicate of its own and not
    ``_restatement(...) is None``.**  :func:`_restatement` answers ``None`` for every
    pair it cannot ORDER, which is a strictly larger set than the pairs it can prove
    admit nothing -- its own docstring names the case: "a shared keyword where the CHILD
    is LOOSER refuses, where §2 would have the field carry the base's", and
    ``minimum: 1`` beside a base's ``minimum: 3`` admits every value from 3 up.  A branch
    dropped on that answer would be dropped for a conjunction that admits something,
    which is a model NARROWER than its document -- the one direction §2 forbids outright
    and the defect this whole clause is fenced against.  So the two questions are asked
    by two functions: "can I order these" is :func:`_restatement`'s and "do these admit
    nothing" is this one's, and nothing here is reused to answer the other.

    Two proofs, and deliberately no third:

    * **Disjoint vocabularies.**  Read through :func:`_as_enum`, which is the same
      rewrite :func:`_at_least_as_tight` compares through -- a ``const`` is a one-member
      ``enum`` -- so ``const`` against ``const``, ``const`` against ``enum`` and ``enum``
      against ``enum`` are one reading and not three.  No member in common means no
      instance satisfies both, which is a proof and not an estimate.
    * **Disjoint type words.**  draft-07's ``type`` is the instance's JSON type, so two
      sets of words with no word in common admit no instance between them.  A node
      stating no ``type`` states nothing to be disjoint FROM, which is why
      :func:`_type_words` answers with an empty set and an empty set proves nothing.

    A bound, a pattern, a ``required`` naming a key the other forbids: each of these CAN
    make a conjunction empty and none of them is read here, because the reading would be
    an inference rather than a pin.  This function being incomplete is safe in exactly
    one direction -- a branch it fails to drop is kept, and a kept branch that admits
    nothing is a model WIDER than its document, which §2 permits and ``strict_validate``
    refuses the payload for.
    """
    c, b = _as_enum(_constraining(child)), _as_enum(_constraining(base))
    if isinstance(c.get("enum"), list) and isinstance(b.get("enum"), list):
        if not [member for member in c["enum"] if member in b["enum"]]:
            return "enum"
    words_c, words_b = _type_words(c.get("type")), _type_words(b.get("type"))
    if words_c and words_b and not words_c & words_b:
        return "type"
    return None


def _restatement(
    child: dict, base: dict, resolve: Callable[[str], dict | None] | None = None
) -> bool | None:
    """The merge rule as one decision about one restated property.

    ``True`` -- it NARROWS: everything ``base`` says about the instance it says at
    least as tightly (:func:`_at_least_as_tight`), and it says something more.  The
    subclass states it, and what it states IS the intersection.

    ``False`` -- it says nothing, or says exactly the same thing.  The field is
    inherited and the subclass declares no field at all.

    ``None`` -- it is INCOMPATIBLE: at a keyword BOTH state it says something that is
    not at least as tight.  Under ``allOf`` both declarations apply, so the effective
    accepted set is their intersection, and a declaration that LOOSENS one the base
    already made is a statement the document does not make at that pointer.  The caller
    refuses.

    **The comparison was keyword-value EQUALITY and section 2's rule is not.**  "The field
    carries the intersection -- an enum is the intersection of the members, a bound is
    the tighter one, a ``const`` must agree" admits narrowings an equality test reads as
    a conflict, and they go live the moment the conjunct cases land:
    ``core/product-execution-requirement.json`` at
    ``/oneOf/2/properties/connection/allOf/1/properties/status`` restates
    ``{"const": "unknown"}`` over a base's ``{"enum": [...], "type": "string"}``, and
    its ``required_for`` restates a bare ``{"contains": {...}}`` over a base's
    ``{"type": "array", "items": {...}, "uniqueItems": true}``.  Both reported "neither
    matches nor narrows".

    **KNOWN CEILING: a shared keyword where the CHILD is LOOSER refuses, where section 2 would
    have the field carry the base's.**  "A bound is the tighter one" says the
    intersection of ``minimum: 1`` over a base's ``minimum: 3`` is 3, and the comparison
    reads it that way too (``harness._tighter``), so such a pair is gradeable and could
    be inherited.  It refuses because the arm has no site.

    **RE-MEASURED at ``adcp-client-python-97w``, and the three documents the comment here
    named are gone from it.**  The old sentence read "3 of the 1,054 portable documents
    are refused by this predicate -- ``governance/check-governance-response.json``'s
    ``action_binding``, ``media-buy/get-media-buys-response.json``'s ``indicators`` and
    ``signals/get-signals-response.json``'s ``range``".  Probed by recording which pairs
    reach the shared-keyword loop's ``None``: immediately before this row, **6
    documents** -- the two it named last are not among them, because each now refuses
    earlier in its own chain and never reaches this predicate -- and **5 of the 6 were
    one keyword, ``required``**, which is the rung this row wrote (the arm above).  After
    it: **1**, ``core/postal-area.json`` at ``enum``, and that document is refused on
    ``title`` at ``/anyOf/0`` regardless, so the arm is the SOLE reason for none.

    So the ceiling stands and the reason does: the one live pair is not a looser bound
    either, and an arm for a looser bound would still be a derivation matching nothing.
    What the stale count hid was a keyword that measured FIVE documents, which is the
    lesson rather than the number -- a population named once and not re-probed stops
    being a measurement.

    **SILENCE IS NOT A LOOSENING, and that half had to wait for the output to be the
    intersection.**  The old rule demanded the child keep every keyword the base states,
    for a sound reason at the time: the field was decided from the CHILD ALONE, so a
    keyword the child did not restate was a keyword the annotation dropped.  Now
    :func:`_intersection` is what the field is decided from, every keyword either
    declaration states reaches it, and the demand measures nothing -- under ``allOf``
    the base's statement applies wherever the child is quiet.  The two halves are one
    change and neither is correct without the other.
    """
    # Both declarations read through :func:`_dereferenced`, and EVERY comparison below
    # made on that same reading -- including the novelty test, which is the one that
    # went wrong when it was not.  Comparing a RAW intersection against a DEREFERENCED
    # base made two ``$ref``s to one target read as a narrowing, and the field then
    # carried the base's annotation at a pointer the document declares itself: measured
    # at 17 ``differs``, every one ``/properties/context/description``, which is §6's
    # description-authority clause 2 and the 15 facts it was written for.
    dc, db = _dereferenced(child, resolve), _dereferenced(base, resolve)
    c, b = _as_enum(_constraining(dc)), _as_enum(_constraining(db))
    # **A ``const`` is a one-member ``enum``, and that is a rewrite rather than a rung**
    # (:func:`_as_enum`, applied before anything is compared).  section 2's "a ``const`` must
    # agree" is the intersection of a pinned value with a vocabulary, and writing the
    # two into one spelling is what lets ONE predicate answer ``const`` vs ``const``,
    # ``const`` vs ``enum`` and ``enum`` vs ``enum``.  Toward ``enum`` and not toward
    # ``const`` because a ``const`` is the degenerate case: folding the other way has
    # nothing to say about a two-member vocabulary.
    if not c:
        return False
    if _conjoins(child, base):
        # **The restatement SPELLS the composition itself, so it says everything the
        # base says by construction**: draft-07 applies every conjunct of an ``allOf``
        # to the same instance, so a conjunct list holding the base's own declaration
        # says at least what that declaration says, and the rest of the list is what it
        # adds.  :func:`_conjoins` carries the measurement and why the question has to
        # be asked of the base's OWN declaration rather than of its dereferenced
        # reading.
        return True
    if "$ref" in b and b.get("$ref") != c.get("$ref"):
        # **The base's whole constraining content is a ``$ref`` this predicate could
        # NOT resolve, so whether the restatement narrows it is unanswerable** -- and
        # :func:`_at_least_as_tight`'s own rule decides that: "a keyword this cannot
        # read is not tight enough and the caller refuses -- never admitted on the
        # ground that it is probably fine, which would be a model wider than its
        # document at a keyword nobody looked at."  ``$ref`` was the one keyword that
        # escaped it, because an unresolved reference leaves the two declarations
        # SHARING NO KEYWORD at all: the loop below then has nothing to range over, the
        # novelty test says the child adds something, and the field is decided from the
        # child alone with every fact behind the reference dropped.
        #
        # **RE-MEASURED over the 1,054 portable documents: 0 sites, down from 3, and the
        # 3 were one defect** (``adcp-client-python-10l.72``).  The comment here read
        # "1 site" and named one of them; the arm had 3, and every one was a pointer
        # LOCAL TO THE BASE'S OWN DOCUMENT:
        #
        # * ``core/tracker-execution-selector.json`` at ``/oneOf/1``, whose
        #   ``vast_versions``, ``vast_event``, ``target`` and ``offset`` each name a node
        #   of ``core/vast-tracker-constraints.json`` ABSOLUTELY where the base it
        #   composes declares the same four as ``{"$ref": "#/definitions/…"}``.  THE SAME
        #   NODE, written once absolutely and once relative to the base's own document --
        #   so the pair was never unreadable, it was unread.
        # * ``brand/verify-brand-claim-response.json`` and
        #   ``brand/verify-brand-claims-response.json`` at
        #   ``/definitions/signed_response``, whose conjunct restates ``payload`` with two
        #   properties over ``core/response-payload-jws-envelope.json``'s ``{"$ref":
        #   "#/definitions/response_payload"}``.
        #
        # :meth:`Module.resolve_node` reads both spellings now, so no pair in this bundle
        # reaches this clause.  **It stays, and a population of 0 is not "a derivation
        # matching nothing" here**: it is not an arm producing an outcome for a shape no
        # document has, it is the one place :func:`_at_least_as_tight`'s refuse-what-you-
        # cannot-read rule is spelled for ``$ref``, and deleting it ADMITS the unreadable
        # pair rather than refusing it -- :func:`_intersection` then drops the base's
        # reference (its ``covered`` arm) and the field is decided from the child alone
        # with every fact behind the reference gone.  Measured before the resolver read
        # the two spellings: emitted, the brand class dropped 6 of the 8 properties
        # ``payload`` requires and the comparison reported 4 ``missing`` and 2
        # ``differs``, which is a model wider than its document.
        #
        # **The two ``brand`` documents EMIT now, and they left through the clause below
        # rather than through this one** (``adcp-client-python-97w``).  Once the base
        # dereferenced to its object, ``properties`` composed per key and ``type``
        # matched; what was left unordered was ``required``, and the rung for it is in
        # :func:`_at_least_as_tight` where §2 already put it.
        return None
    if not all(_at_least_as_tight(k, c[k], b[k], resolve) for k in set(c) & set(b)):
        return None
    # It narrows when the INTERSECTION says more than the base does.  Asked of the
    # intersection and not of the child, because that is what the field carries: a
    # child restating a strict SUBSET of the base's keywords with the same values
    # intersects to the base itself, states no new fact, and is the inherited field
    # (``_annotates_differently`` then decides whether the annotations differ).
    return _as_enum(_constraining(_intersection(dc, db, resolve))) != b


def _conjoins(child: dict, base: dict) -> bool:
    """Is ``child`` a CONJUNCTION one of whose conjuncts is ``base``'s own declaration,
    with something beside it?

    Then it narrows, and the answer costs no comparison: ``allOf`` applies every
    conjunct to the same instance, so the list says at least what the conjunct that IS
    the base says, and the other conjuncts are what it says more.  ``something beside
    it`` is what makes it a narrowing rather than a restatement of nothing -- a list
    holding the base and no other constraining conjunct says exactly what the base says,
    which is :func:`_restatement`'s ``False``.

    **Asked of the base's OWN declaration and never of its dereferenced reading**, which
    is the whole point of the arm.  The conjunct and the base here are the SAME ``$ref``,
    and :func:`_dereferenced` replaces the base's with the target's whole schema -- the
    target's own ``allOf`` of conditionals included.  The predicate then meets two values
    at ``allOf`` that have nothing to say to each other, ``_at_least_as_tight`` has no
    ordering for a conjunct list, and the document is refused for restating the reference
    VERBATIM.

    Measured over the 1,054 portable documents: **1 site**,
    ``core/assets/display-tag-asset.json`` at ``/oneOf/0/properties/macro_declarations``,
    whose branch spells in full the composition ``vast-asset.json`` and
    ``daast-asset.json`` spell as a bare overlay --
    ``{"items": {"allOf": [{"$ref": T}, {"properties": ...}]}}`` over the root's
    ``{"items": {"$ref": T}}``, where ``T`` is ``core/macro-declaration.json`` and its
    own root carries six ``if``/``then`` conjuncts.  It was the only ``allOf`` pair
    ``_at_least_as_tight`` was ever asked about and the only one it answered False for.
    """
    conjuncts = _constraining(child).get("allOf")
    if not isinstance(conjuncts, list):
        return False
    stated = [_constraining(c) for c in conjuncts if isinstance(c, dict)]
    b = _constraining(base)
    return b in stated and any(s and s != b for s in stated)


def _dereferenced(
    declaration: dict, resolve: Callable[[str], dict | None] | None
) -> dict:
    """A declaration that is nothing but a ``$ref``, read as what it references.

    For the PREDICATE and never for the field: :func:`Module.resolve_node` says why, and
    the asymmetry is the point -- whether one declaration narrows another is a fact
    about the two TARGETS, while the field is an IMPORT of the symbol the document
    names (P2).

    Only a declaration whose whole constraining content is the reference.  A ``$ref``
    with a constraint beside it is draft-07 ignoring its sibling, which the whole
    pipeline refuses by name rather than reading two ways (``emit.decide_type``,
    :func:`lower_composition`'s sibling arm), so there is nothing here to resolve.
    """
    if resolve is None:
        return declaration
    content = _constraining(declaration)
    if set(content) != {"$ref"}:
        return declaration
    target = resolve(content["$ref"])
    return target if isinstance(target, dict) else declaration


#: The draft-07 type word each JSON value has.  ``bool`` before ``int`` because
#: ``isinstance(True, int)`` is true in Python and ``true`` is not an integer in JSON.
_JSON_TYPES: tuple[tuple[type | tuple[type, ...], str], ...] = (
    (bool, "boolean"),
    (int, "integer"),
    (float, "number"),
    (str, "string"),
    (list, "array"),
    (dict, "object"),
)


def _entailed_type(members: list) -> str | None:
    """The one ``type`` every member of a vocabulary has, or ``None``.

    An enumerated value set ENTAILS a type: ``{"const": "unknown"}`` says the instance
    is a string as surely as ``{"type": "string"}`` does.  Deriving it is what lets a
    ``const`` restatement be read as keeping a base's ``type`` instead of dropping it --
    without it, ``{"const": "unknown"}`` over ``{"enum": [...], "type": "string"}``
    reads as incompatible for a fact it states by implication.  The same derivation the
    comparison already makes on the document side (``harness._entails_type``'s ``const``
    row, 832 typeless const nodes), made here because the two halves have to read one
    declaration the same way.
    """
    found = {
        word for member in members for cls, word in _JSON_TYPES if isinstance(member, cls)
    }
    # One word, and the FIRST match per member: ``_JSON_TYPES`` is ordered so a bool
    # answers ``boolean`` and not ``integer``, and the set comprehension above would
    # collect both -- so a bool present at all makes this ambiguous rather than wrong.
    if not members or any(isinstance(m, bool) for m in members) and len(found) > 1:
        return None
    return next(iter(found)) if len(found) == 1 else None


def _as_enum(constraining: dict) -> dict:
    """``{"const": v}`` read as ``{"enum": [v]}`` plus the ``type`` it entails.

    So ONE predicate answers ``const`` against ``const``, ``const`` against ``enum``
    and ``enum`` against ``enum``, and a vocabulary is read as stating the type its
    members have (:func:`_entailed_type`).

    The ``const`` rewrite applies only where the declaration does not state both: a
    node stating ``const`` AND ``enum`` says two things, and collapsing them would drop
    one.  draft-07 permits it and this bundle has none, so such a node keeps both keys
    and compares by equality.
    """
    out = constraining
    if "const" in out and "enum" not in out:
        out = {**{k: v for k, v in out.items() if k != "const"}, "enum": [out["const"]]}
    if "type" not in out and isinstance(out.get("enum"), list):
        word = _entailed_type(out["enum"])
        if word is not None:
            out = {**out, "type": word}
    return out


def _disagreeing(
    child: dict, base: dict, resolve: Callable[[str], dict | None] | None = None
) -> str:
    """The keyword a refusal is reported on: **the first SHARED one the restatement does
    not say at least as much at**, read through the same two lenses
    :func:`_restatement` compares through.

    **It was ``min()`` over every key the two differ about, and that set contains keys
    only the BASE states -- which can never be the obstruction** (``10l.92``).  Under
    ``allOf`` the base's declaration applies wherever the child is quiet, so the child's
    silence at a keyword is not a loosening and :func:`_restatement` does not read it as
    one: the predicate ranges over ``set(c) & set(b)`` alone.  A refusal naming a
    base-only key therefore attributes itself to a keyword nothing looked at.

    **Measured, and it cost a whole row its shape** (``adcp-client-python-10l.82``).
    ``core/audience-evidence-selection.json`` and
    ``governance/check-governance-response.json`` restate one property, ``action_binding``,
    and were blocked by one keyword, ``required`` -- and reported under ``anyOf`` and
    under ``additionalProperties``, both base-only keys that sort first.  The row was
    handed to a lane as two keyword headings and is one shape.  The three that still
    refuse here all reported ``$ref``, because ``$`` sorts before every letter and the
    base's whole content is a bare reference that :func:`_dereferenced` RESOLVES before
    anything is compared -- so the reported keyword was one the comparison never reads.
    Their obstructions, measured and now reported: ``required`` for both
    ``brand/verify-brand-claim-response.json`` and
    ``brand/verify-brand-claims-response.json`` (the restatement requires two names where
    the base's target requires eight), and ``additionalProperties`` for
    ``media-buy/get-reporting-status-response.json``'s ``adcp_error`` (``false`` over the
    target's ``true``).

    **The fallback is one arm and not a guess.** :func:`_restatement` answers ``None`` at
    exactly two places: the tightness loop, which by construction leaves a failing shared
    keyword for this to find, and the arm for a base whose whole content is a ``$ref``
    this could not resolve -- where there is no shared keyword at all, the obstruction
    really is the unreadable reference, and the union reading below names it.
    """
    dc, db = _dereferenced(child, resolve), _dereferenced(base, resolve)
    c, b = _as_enum(_constraining(dc)), _as_enum(_constraining(db))
    failing = sorted(k for k in set(c) & set(b) if not _at_least_as_tight(k, c[k], b[k], resolve))
    if failing:
        return failing[0]
    return min({k for k in set(c) | set(b) if c.get(k) != b.get(k)} or {"allOf"})


def bind_without_a_model(
    mod: Module, pointer: str, declaration: ir.AliasDecl | ir.EnumDecl
) -> str | Refusal:
    """The module-level half of a root that is not an ``AdCPBaseModel``.

    D2 gives two root kinds no class to hang ``strict_validate`` on: a scalar root
    is an ``Annotated`` alias, and an enumeration cannot carry a class-body line at
    all because ``Enum.jinja2`` has no ``class_body_lines`` slot and D9 forbids
    writing one in afterwards.  Both therefore bind the SAME two halves at module
    scope -- the reference, and ``strict_alias`` over it -- so a class, an alias and
    an enumeration cannot come to answer differently about what their own document
    accepts.  ``strict_alias`` reaches the document through ``schema_at`` and
    refuses through ``_refuse``, which is exactly what
    ``AdCPBaseModel.strict_validate`` does.

    One function and not two, because the rows differ only in the DECLARATION between
    the statements, which is why :class:`codegen.ir.RootBinding` carries it rather than
    sitting beside it.  ``tests/test_emit.py`` reads the pairing off the module for both.
    """
    collision = mod.declare(
        pointer,
        ir.RootBinding(schema_ref(mod.document, pointer), pointer, declaration),
    )
    if collision is not None:
        return collision
    return pointer


def declare_root_model(
    mod: Module,
    pointer: str,
    node: nodes.Base,
    decided: ir.TypeRef,
    rules: tuple[Rule, ...] = (),
) -> Decided | Refusal:
    """§4's THIRD root shape: a root that is neither a class nor an alias.

    ``docs/plan/rebuild-plan.md`` §4's table gives three rows to one: "an array at a
    root -> ``RootModel[list[X]]``", "a ``oneOf``/``anyOf`` at a root mixing a scalar
    branch with a class branch -> a root model over the union of the branches' types",
    and "a root stating no schema keyword at all -> a permissive root model".  §7 of the
    architecture document gives them one declaration, :class:`codegen.ir.RootModelDecl`,
    and §8 gives them one runtime base, ``AdCPRootModel``.

    **One function for the three, which is :func:`bind_without_a_model`'s own reason
    read at a different shape.**  That one binds the two module-level statements a root
    with NO class takes; this one declares the class a root model IS, so the schema half
    arrives by inheritance from ``AdCPRootModel`` exactly as it does for a class.  A
    class, a root model, an alias and an enumeration therefore cannot come to answer
    differently about what their own document accepts, which is §8's requirement in
    those words: "each must carry ``__adcp_schema__``, ``strict_validate`` and a rule
    tuple exactly as a class does."

    ``rules`` is §2's "where a rule hangs" at a root that is not a class: "where no class
    sits above the value -- a root array, a mapping value, a ``definitions`` entry, a
    union branch -- the rule hangs off the value's own annotated type."  A root model IS
    the value's own type, and it carries a rule tuple, so the rule reaches it -- measured
    on the runtime: ``_runtime.supplied`` reads ``__pydantic_fields_set__``, a root
    model's one field is ``root``, and a rule keyed on ``"root"`` is evaluated exactly as
    a class's rule keyed on a property is (``AdCPRootModel``'s docstring carries the
    three MRO measurements).

    It returns a :class:`Decided` and not a pointer, because the three callers each want
    the node's TYPE back: the root model is a local symbol like any class the walk
    declares, and ``lower/names.py`` binds the pointer to it.
    """
    collision = mod.declare(
        pointer,
        ir.RootModelDecl(
            # The POINTER in the name slot until ``names.assign`` binds it (§7).
            name=pointer,
            ref=schema_ref(mod.document, pointer),
            type=decided,
            description=node.description,
            rules=rules,
        ),
    )
    if collision is not None:
        return collision
    return Decided(ir.TypeRef(pointer, local=True))


def _alias_for(pointer: str, node: nodes.Base, decided: Decided) -> ir.AliasDecl:
    """One node's own decision, as the alias that names it.

    Shared by the TWO rows that declare an alias -- a root (:func:`declare_alias`) and
    a node another document names (:func:`name_the_node`) -- because "the annotation
    for this node, under this name" is the same question in both and a second copy of
    it is how the two come to carry a node's ``format`` or its ``description``
    differently.  They differ only in what wraps the statement, which is each row's
    own and stays there.

    The bound and the ``format`` ride on the alias's own TYPE, exactly as a field's do
    (§2, and :attr:`codegen.ir.TypeRef.facts`): one carrier, so an alias and a property
    cannot come to spell one ``minLength`` two ways.
    """
    return ir.AliasDecl(
        # The POINTER in the name slot until ``names.assign`` binds it (§7).
        pointer,
        replace(decided.type, facts=decided.constraints, format=decided.format),
        description=node.description,
    )


def name_the_node(
    mod: Module, pointer: str, node: nodes.Base, decided: Decided
) -> Decided | Refusal:
    """Give a node a SYMBOL in its own module, because a ``$ref`` elsewhere names it.

    A fragment reference resolves to an import of a symbol the target module
    declares, never to a copy (section 2's rule).  A node D2 makes a CLASS already
    has one -- the walk declared it and ``decided.type.local`` says so -- and this is
    the other case: an array, a scalar or a mapping is an annotation with no name, so
    the target module has nothing to export and the reference has nothing to import.

    **The node's type BECOMES the symbol**, which is why this returns a ``Decided``
    rather than only declaring: the alias carries the constraints and the referring
    property then references it, so the node's facts have ONE spelling in the module.
    Declaring the alias and leaving the parent's field to restate the same
    ``minLength`` inline would be the copy P2 removes, two spellings deep in one file.

    Not :func:`declare_alias`, which is a ROOT's whole module -- the reference, the
    alias and the bound ``strict_validate``, all at module scope, where there is room
    for exactly one of each.  A named node is INSIDE a document that already has a
    root, so it takes the alias statement alone.  It therefore carries no
    ``__adcp_schema__`` of its own, and that is the existing arrangement rather than
    a gap: every nested node that is not a class is ungraded on its own today, and
    this one is graded twice over anyway -- inside its own document's pair, which
    names the whole document, and inside its referrer's, whose resolved schema inlines
    this very node at the pointer the reference carries.

    **No name is computed here and none is passed in** (§7, and §14 step 7): the
    declaration is made at the node's own POINTER, and ``lower/names.py`` binds it to
    the name §4's nested rule derives for that position -- which is the hop the node's
    parent recorded when it lowered this child.
    """
    collision = mod.declare(pointer, _alias_for(pointer, node, decided))
    if collision is not None:
        return collision
    return Decided(ir.TypeRef(pointer, local=True))


def local_reference(mod: Module, pointer: str, at: str) -> Decided | Refusal:
    """What a LOCAL ``$ref`` decides to: the node of THIS document that it names.

    :func:`name_the_node`'s sibling, and the division is which document the reference
    resolves against.  An ABSOLUTE fragment reference names a node of ANOTHER document,
    so the referring module imports a symbol that module declared and
    ``emit.emit``'s binder does the work.  A local one (``#/definitions/x`` -- an empty
    document half, which ``bundle.split_ref`` is what hands back) names a node of the
    document being written, so there is no module to import from and no binder to ask:
    the symbol is one THIS module declares, and if it has not declared it yet, this is
    what makes it.

    **Declared when a reference asks, not ahead of time**, and three things follow that
    an eager pass over the section would have to solve one at a time:

    * a FORWARD reference costs nothing.  20 of the bundle's local references name an
      entry the document lists after the one referring to it, in 4 documents; declaring
      on demand puts every symbol in the module before its user by construction, where
      an eager pass in document order would need a topological sort over the section.
    * an entry nothing references is NOT declared, which is the decision rather than an
      omission.  ``definitions`` and ``$defs`` assert nothing about an instance, so an
      entry no reference reaches cannot change what the document accepts or refuses --
      declaring it would emit a class no field names, nothing imports and ``__all__``
      does not export, whose only reachable effect is that a keyword inside a DEAD
      section could refuse the whole document.  Measured: 11 of the 157 entries in the
      40 documents this step unblocks, all 11 in ``a2ui/si-catalog.json``, whose 24
      ``$ref``\\ s all sit inside the dead section.
    * a CYCLE refuses by name instead of recurring, through ``mod.resolving``.  0
      documents are in that position today, which is why this is the rule rather than a
      forward-declaration scheme: two entries naming each other is a recursive type,
      and nothing here has a spelling for one.

    **The NODE ITSELF decides what it becomes, and the decision is returned rather than
    looked back up.**  :func:`decide` is the one per-node walk, so an object entry is a
    class, an enumeration is an enumeration, and a scalar or an array is an annotation
    that :func:`name_the_node` gives this very symbol to -- the pointer is in
    ``mod.named``, which is what put it in ``mod.local`` in the first place.  Each one
    therefore carries ITS OWN pointer: a class through :func:`declare_object`'s
    ``schema_ref(mod.document, pointer)``, and nothing is written against the referring
    document's.

    Returning the decision is what makes the ONE case with no declaration correct
    instead of a ``KeyError``: an entry that is ITSELF a ``$ref`` decides to the symbol
    the module IMPORTED for its target, which nothing declared here.  That is the right
    answer within one module -- the import is already in the module and there is no
    export to re-export -- and it is the opposite of the cross-module case, where
    section 2's rule demands the symbol be one the TARGET declares and ``emit.emit``'s
    binder refuses a pointer at such a node.  It is also why ``mod.declared`` is a
    sufficient memo rather than a required one: such an entry is simply re-decided, to
    the same imported symbol, and ``mod.imports`` is a set.  Measured, so the arm is
    known live rather than defensive: 4 of the bundle's 405 local reference sites name
    such an entry, in 2 documents (``brand.json#/definitions/logo_slot`` and
    ``core/registry-event.json#/$defs/badgeRole``, each named twice).

    The NAME is D3's nested rule with the document as the parent: the root's symbol plus
    ``class_name`` of the entry's own key, which is the pointer's last segment
    unescaped.  **No identifier check here, and that is a proof rather than an
    omission**: ``class_name`` returns alphanumerics only, ``emit.lower_document``
    refuses a title that derives no identifier before any row runs, so ``mod.root``
    always begins with a letter and the concatenation is always an identifier.  What
    CAN go wrong is two keys deriving one name (``a_b`` and ``a.b``), and
    :meth:`Module.declare` already fails the build naming both -- including the key
    whose characters are all non-alphanumeric, which derives the root's own name.
    Measured spellable for all 163 of the bundle's entry keys.
    """
    if pointer in mod.at:
        return Decided(ir.TypeRef(pointer, local=True))
    if pointer in mod.resolving:
        return Refusal(
            "$ref",
            at,
            f"a local reference cycle: #{' -> #'.join([*mod.resolving, pointer])}",
            kind=Kind.VERDICT,
        )
    node = mod.local.get(pointer)
    if node is None:
        return Refusal(
            "$ref", at, f"#{pointer} names no node of this document", kind=Kind.VERDICT
        )
    # **The target's ``default`` travels to the REFERRING node** (``adcp-client-python
    # -10l.26``).  Draft-07 replaces a ``$ref`` node with its target, so the target's
    # ``default`` IS the referring node's, and §5's ``default`` row then gives it to the
    # field; without this the field rendered ``default: None`` where the document says
    # ``"linear"``, which the comparison reports as *differs* and §8 pins at zero.  §2 is
    # why it cannot be declared instead: "a default is a value and not a constraint, so it
    # neither widens nor narrows what the class accepts", so there is no fact about
    # acceptance to drop and nothing to attribute.
    #
    # Written HERE because this is the one place the local resolution happens, and keyed by
    # the REFERRER so two properties naming one entry each get it.  It is recorded before
    # the decision below, so a target that refuses leaves the record untouched by anyone
    # who then never builds a field from it.
    if "default" in node:
        mod.referred[at] = node["default"]
    # **§4's DEF rule as a HOP**: ``<Root><Key>``, the key being the entry's own, which
    # ``names.entry_key`` reads off the pointer's last segment because the pointer IS
    # that key.  The NAME is ``lower/names.py``'s, so nothing here concatenates one.
    mod.hops[pointer] = names.Entry(names.entry_key(pointer))
    # **The ``try``/``finally`` is gone with the raise**, and that is the second half of
    # §2's "the one ``try`` left in the compiler is around nothing": the stack had to be
    # unwound on an exception as well as on a return, and now there is no exception to
    # unwind for -- a refusal RETURNS through this line like any other decision, and a
    # :class:`codegen.refusal.BuildFailure` stops the run rather than being recovered
    # from, so nothing observes the stack after one.
    mod.resolving.append(pointer)
    decided = decide(node, pointer, mod, Position.DEF)
    mod.resolving.pop()
    return decided


def declare_alias(
    mod: Module, pointer: str, doc: nodes.Base, decided: Decided
) -> str | Refusal:
    """Declare the module for a root D2 makes an ALIAS rather than a class.

    A scalar root takes this shape, and so does every other root with no field to
    hang itself on: a class would be a second name for the same node (P2) and
    would put an object on the wire where the document carries a string or a map.
    One function for all of them because the module shape is identical -- the
    reference, the alias, and the bound ``strict_validate`` -- and two copies of it
    would be two places for the ``strict_validate`` line to drift.

    The ANNOTATION is still the renderer's: the same field rendering a class
    property gets, read off the field instead of out of a class body, so a
    constraint on an alias and a constraint on a property cannot come to be spelled
    two ways.  What is ours is the two module-level STATEMENTS, and §1 says why: no
    compiler template has a slot for a line beside an alias.

    KNOWN CEILING: an alias has no ``ConfigDict``, so it cannot carry the per-class
    ``regex_engine`` a look-around pattern needs, and ``strict_alias`` builds its
    ``TypeAdapter`` at import.  A root carrying look-around would therefore fail to
    IMPORT once the base stops forcing ``python-re``.  Measured over steps 1 and 2's
    population: 5 scalar roots, 2 carrying a ``pattern`` (both ``^[a-z0-9_]+$``,
    which the default engine compiles) and 0 carrying look-around, so no document
    there reaches it.  The failure is an ImportError at the gate rather than a
    silent widening, so the upgrade path is for the step whose population reaches
    one: either refuse such a document by name, or wrap the alias in a
    ``RootModel`` that has a config slot.
    """
    return bind_without_a_model(mod, pointer, _alias_for(pointer, doc, decided))
