"""§5's ``allOf`` row: ``$ref`` conjuncts are BASES, inline conjuncts are fields and rules.

At EVERY position, in one arm: the conjunct list is the same list and the merge rule is the
same rule at every depth, and a document root reaches this very handler -- §5's "root and
non-root are one path".

**THE ROW'S DECISION IS HERE, whole**, which is ``docs/plan/architecture.md`` §5's "a
module whose body delegates to another module is not a module.  It is a name for one.  A
reader who opens ``lower/composition.py`` to learn what an ``allOf`` lowers to must find
the answer there".  This module was 39 lines delegating to ``lower_composition``;
``adcp-client-python-g4z``'s third move is what brought the row across.

**What the row is NOT, and both have modules of their own.**

* **§2's intersection over two DECLARATIONS is ``codegen/intersect.py``'s.**  §6: "
  ``restatement``, ``intersection`` and ``at_least_as_tight`` are pure functions over two
  nodes and stay so", and ``schema/nodes.py`` says why a conjunct is a
  :class:`codegen.schema.nodes.Conjunct` and not a node: the rule MERGES two declarations
  of one property and hands the merged one back to ``parse``, because the result has to be
  parsed as one node and not composed out of two decided ones.  So this row reads
  :attr:`nodes.Composition.conjuncts` -- declarations with their pointers -- and the
  merge's result goes through the parser like any other node.
* **The field builder and the class declarer are ``codegen/lower/objects.py``'s**, with
  the object row whose primary subject they are (§5).  Every class this row declares goes
  through them, which is what makes an ``allOf``'s class and a plain object's class the
  same kind of thing.

**THE FOUR CONCERNS the function's own branch conditions name, and where each is.**
``lower_composition`` was 1,438 lines, and the reason that is a finding rather than a
length is that no part of it could be asked a question on its own -- the only evidence any
of the four was right was that the emitted tree came out right.  Two are separated and
graded; two are not, and the reason is stated rather than left to a reader:

* **which kind a conjunct is** -- :func:`classify`, returning :class:`Conjunct`.  Four
  conditions that were stated inline once per arm, and whose partitioning nothing could
  see.  ``tests/test_conjunct_kinds.py``.
* **how an own field merges against an inherited one** -- ``codegen/lower/inherited.py``,
  with §2's requiredness overlay, which is one more arm of the same decision.  This was
  the deepest nesting here and the subtlest rule in it.
  ``tests/test_inherited_merge.py``.
* **which rules and facts the composed class carries** -- separated in HALF.  The three
  sibling screens are :func:`a_sibling_with_no_type_to_constrain`, one reading of §5's
  ``$ref`` row at three keywords, two of which have a population of 0 in this bundle and
  are therefore exactly the ones worth a test (``tests/test_conjunct_siblings.py``).  The
  ``uniqueItems`` arm and the per-conjunct collection are still inline.
* **what a ``$ref`` conjunct resolves to** -- NOT separated.  The arm writes to eight
  accumulators of the enclosing function (the inherited views, the extra, the
  description, the bases, the conjoined list), so separating it needs a carrier for the
  walk's per-conjunct state, and that is a design decision rather than a relocation.
  ``adcp-client-python-g4z`` carries the question.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import replace
from enum import StrEnum
from typing import Any

from codegen import compiler, intersect, ir, keywords
from codegen.keywords import Position

# ``inherited`` is also the name :func:`lower_composition` gives the map of what the
# ``$ref`` conjuncts' targets declare, which is the module's own argument -- so the module
# is aliased rather than the local renamed: the local is the name §2's rule is stated in.
from codegen.lower import inherited as inherited_row
from codegen.lower import objects
from codegen.refusal import BuildFailure, Kind, Refusal, first_refusal
from codegen.schema import nodes
from codegen.schema import parse as schema


def lower(node: nodes.Composition, mod: compiler.Module) -> ir.Decided | Refusal:
    """The composed class, declared at this node's POINTER, as a local type.

    A conjunct's refusal is returned upward unchanged (§6), naming the conjunct's own
    pointer rather than this node's.
    """
    declared = lower_composition(node, mod)
    if isinstance(declared, (Refusal, ir.Decided)):
        # A :class:`codegen.ir.Decided` is §5's ``$ref`` row at CONJ where the target is not a class
        # (§14 step 9): the node declares no fields, so there is no class to declare and
        # the target is the node's own TYPE.  It is returned unchanged -- this row's job
        # is to turn a declared class's POINTER into a type, and that answer already is
        # one.
        return declared
    return ir.Decided(ir.TypeRef(declared, local=True))


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
#: Both spellings, because :func:`as_enum` is the one reading of them -- "a ``const`` is a
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
#: because :func:`as_enum` makes it the same arm and leaving it out would be a second
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


class Conjunct(StrEnum):
    """Which arm of §5's ``allOf`` row one conjunct's KEY SET sends it to.

    The row has five answers for a conjunct and the function below is the whole of
    deciding which one a conjunct gets: it reads a SET OF KEYWORD NAMES and nothing else,
    so it is gradeable with a literal and no bundle, no module and no walk
    (``tests/test_conjunct_kinds.py``).  :func:`lower_composition`'s arms used to restate
    the set algebra inline, once per arm, which is the repetition
    ``docs/plan/architecture.md`` §3 forbids about a keyword decision and §5 forbids about
    a row's: four conditions in one loop, each the only statement of its own arm's
    membership, and no reader could see that they partition.
    """

    #: ``keys == {"$ref"}`` -- the conjunct is a BASE, and §5's ``$ref`` row at CONJ
    #: decides what it becomes.
    BASE = "base"
    #: ``"$ref" in keys and keys != {"$ref"}`` -- a reference AND something else.  Not an
    #: arm but a NORMALISATION: the constraining siblings compile to nothing and are
    #: reported, and what is left is :attr:`BASE`.
    REFERENCE_WITH_SIBLINGS = "reference with siblings"
    #: ``keys <= INLINE | screen | CONJ_COMPOSES`` -- an inline object, whose properties
    #: are this node's fields and whose rule sources are this node's rules.
    INLINE_OBJECT = "inline object"
    #: A conjunct carrying ``oneOf`` or ``anyOf`` -- a combinator of SHAPES, which §5
    #: decides elsewhere.
    COMBINATOR = "combinator"
    #: ``keys <= {"const", "enum"}``, non-empty -- §5's ``enum`` row at CONJ, where the
    #: conjunct constrains the node's own TYPE.
    VALUE_SET = "value set"
    #: Everything else, which refuses by name.
    UNREADABLE = "unreadable"


def classify(keys: AbstractSet[str], screen: AbstractSet[str]) -> Conjunct:
    """Which arm this conjunct's keys reach, in the ORDER :func:`lower_composition` asks.

    ``screen`` is the conjunct's own rule sources at CONJ
    (``compiler.declaration_rule_sources``), which is why the inline answer is not a
    function of ``keys`` alone: a conjunct stating ``{"properties": ..., "not": ...}`` is
    an inline object whose ``not`` is one of this node's rules, and which keywords are
    rule sources is the TABLE's reading and not this row's.

    The order is the arms' own and is load-bearing at one point: a conjunct stating both
    ``properties`` and ``oneOf`` is an :attr:`INLINE_OBJECT` and not a
    :attr:`COMBINATOR`, because ``oneOf`` is in ``screen`` wherever ``rules.presence_only``
    reads it as a presence clause, and the inline arm then claims the whole conjunct.
    Asked the other way round, that conjunct would refuse.
    """
    if "$ref" in keys and keys != {"$ref"}:
        return Conjunct.REFERENCE_WITH_SIBLINGS
    if keys == {"$ref"}:
        return Conjunct.BASE
    if keys <= INLINE | screen | CONJ_COMPOSES:
        return Conjunct.INLINE_OBJECT
    if any(k in keys for k in _COMBINATORS):
        return Conjunct.COMBINATOR
    if keys and keys <= _A_VALUE_SET:
        return Conjunct.VALUE_SET
    return Conjunct.UNREADABLE


def inert_beside_a_reference(
    node: Mapping[str, Any], pointer: str, position: Position, mod: compiler.Module | None = None
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
    meet it -- ``lower/references.py``'s arm of the one dispatch and
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
        compiler.report_inert(inert, pointer, mod)
    return inert


def _refuse_a_combinator_of_shapes(
    node: nodes.Base, screen: frozenset[str]
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
            kind=compiler.kind_for(node.combinator, node.position),
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


def _a_rule_the_target_states(uri: str, mod: compiler.Module) -> dict | None:
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
    declared = set(intersect.declaring(stating, Position.CONJ))
    if not declared or declared - set(compiler.declaration_rule_sources(stating, Position.CONJ)):
        return None
    return stating


def asserted_properties(
    node: nodes.Base, conjuncts: Sequence[nodes.Conjunct]
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


def surviving(
    asserted: Mapping[str, list[dict]], branches: compiler.TargetBranches
) -> compiler.TargetBranches:
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

    :func:`provably_empty` is the whole of the test, and its docstring carries why it is
    not :func:`restatement`'s ``None``.
    """
    return replace(
        branches,
        dropped=frozenset(
            index
            for index, branch in enumerate(branches.of)
            if any(
                intersect.provably_empty(stated, branch.declares.properties[key]) is not None
                for key, views in asserted.items()
                if key in branch.declares.properties
                for stated in views
            )
        ),
    )


#: The mixin §4 puts FIRST on a union base, as the one spelling both sites name it by.
DISPATCH_MIXIN = "BranchDispatchMixin"


def dispatching_bases(bases: tuple[ir.TypeRef, ...], mod: compiler.Module) -> tuple[ir.TypeRef, ...]:
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


def _carries_the_mixin(base: ir.TypeRef, mod: compiler.Module, seen: frozenset[str]) -> bool:
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
    decided: ir.Decided,
    stated: Sequence[tuple[str, Mapping[str, Any]]],
    reference: nodes.Reference,
    mod: compiler.Module,
) -> ir.Decided | Refusal:
    """§5's ``enum`` row at CONJ: the TYPE :func:`the_conjuncts_own_type` decided,
    narrowed to the intersection of the target's vocabulary with the conjuncts' own.

    "Beside a ``$ref`` whose target is an enumeration → §2's intersection of the two
    vocabularies, rendered as a ``Literal`` over the TARGET's MEMBERS and not over their
    raw values.  The two accept and dump identically -- a member's value IS the raw
    value -- so the accepts draw and the round trip see the same instance either way, and
    the member form keeps the imported symbol a caller can name: where no check can tell
    two renderings apart, DX decides."

    **The intersection is computed over DECLARATIONS and the ORDER is the TARGET'S**, both
    of which are §2's and neither of which is a preference.  The declaration is read
    through :meth:`Module.resolve_node` -- the one reader §2's intersection rule has for a
    reference -- because the symbol the reference was bound to carries no vocabulary, and
    the whole of this row is a fact about the two value sets.  The order is the target's so
    that the rendered annotation is a function of the document's content (P7) and not of
    which conjunct the walk read first; the conjuncts are a FILTER over it.

    **``const`` and ``enum`` are one computation** (:func:`as_enum`, and
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
            kind=compiler.kind_for("enum", Position.CONJ),
        )
    surviving = list(members)
    for _at, conjunct in stated:
        vocabulary = intersect.as_enum(intersect.constraining(conjunct)).get("enum")
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
            kind=compiler.kind_for("enum", Position.CONJ),
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
            kind=compiler.kind_for("enum", Position.CONJ),
        )
    return replace(decided, type=replace(decided.type, members=tuple(names)))


def _conjunct_base(
    conjunct: Mapping[str, Any], where: str, mod: compiler.Module
) -> tuple[compiler.Target, nodes.Reference] | Refusal:
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
            f"{type(parsed).__name__}, so lower_composition's conjunct screen and "
            "schema.parse's arm order disagree about what a $ref node is"
        )
    if parsed.head or parsed.into not in mod.local:
        # **A local spelling that names NO NODE OF THIS DOCUMENT is not a local reference
        # of this document at all** (``adcp-client-python-97w``).  It is a reference the
        # COMPOSITION carried in: §5's ``properties`` row composes two object declarations
        # as an ``allOf`` of the two, so where a base spells its half as a pointer into its
        # own text, :func:`intersection` plants that very pointer as a conjunct of a node
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
    decided = compiler.local_reference(mod, parsed.into, where)
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
            kind=compiler.kind_for("$ref", Position.CONJ),
        )
    return compiler.local_target(mod, decided.type.path), parsed


def _carries_nothing(word: str, position: Position) -> bool:
    """Whether the TABLE gives ``word`` no effect at all at ``position``.

    §3: "a keyword's answer is the cell's".  :data:`keywords.Effect.NOTHING` is the one
    effect a lowering neither compiles nor carries, so a node whose every annotation is
    one of these states nothing a class could hold -- and a keyword with no row is not
    admitted here either, because the screen that refuses it by name has already run and
    this function must not quietly answer for a cell that does not exist.
    """
    answer = keywords.cell(word, position)
    return answer is not None and answer.effect is keywords.Effect.NOTHING


def states_nothing_but_a_reference(
    node: nodes.Base,
    *,
    conjunct_bases: Sequence[ir.TypeRef],
    bases: Sequence[ir.TypeRef],
    union: compiler.UnionBase | None,
    inherits: compiler.Shape | None,
    base_if_none_composes: ir.TypeRef | None,
    local: Mapping[str, Any],
    required: AbstractSet[str],
    conjunct_rules: Sequence[Mapping[str, Any]],
    conjunct_values: Sequence[object],
    conjoined: Sequence[object],
    contains: Any | None,
    facts: Mapping[str, Any],
) -> bool:
    """Whether this node composes ONE class base and says nothing else about an instance.

    ``docs/plan/final-state.md`` reading 4: *"a type stated at more than one position is
    written once and referenced, never restated"*, and reading 4's own test for which of
    the two a position is -- *"whether the bundle REFERENCES one node from the others or
    RESTATES it is the question that tells our defect from the schema's own duplication"*.
    A node whose whole content is ``{"allOf": [{"$ref": X}]}`` is the bundle REFERENCING,
    so a class declared at it is a second declaration of X's type under a second name, and
    that is ours.

    **EVERY ARGUMENT IS A WAY FOR THIS NODE TO SAY SOMETHING**, and the predicate is the
    conjunction that there is none -- which is why they are parameters rather than a
    re-reading of the node.  ``local`` and ``required`` are what the node and its inline
    conjuncts declare about keys; ``conjunct_rules``, ``conjunct_values``, ``contains`` and
    ``facts`` are §5's "the other conjuncts and the ``allOf``'s siblings constrain it", one
    carrier each; ``conjoined`` is a second ``$ref`` whose target is not a class; ``bases``,
    ``inherits``, ``union`` and ``base_if_none_composes`` are the CALLER's contributions,
    and a union root or a union branch arrives with one, so none of them is in this row.
    The node's own three are read off :class:`nodes.Base`: ``declares`` holds every key it
    states about an instance, ``annotations`` every admitted key it carries without
    constraining, and ``rules`` its own rule sources.

    **``annotations`` IS IN THE CONJUNCTION BY ITS EFFECT AND NOT BY A LIST OF NAMES, and
    ``description`` is why there is a screen at all.**  §6's description-authority rule
    makes the node's own ``description`` authoritative at its own pointer, and a type that
    IS the target carries no statement of this document's -- so a node stating one is
    restating something, even though what it restates admits nothing.  So the admitted
    annotations are the ones :data:`keywords.Effect.NOTHING` names: read off the TABLE at
    this node's own position, which is §3's rule that a keyword's answer is the cell's.
    ``x-adcp-schema-uri`` is NOTHING at PROP and ``description`` is ANNOTATION, which is
    the whole of the difference between the 7 nodes below and the 50 beside them.

    Measured over the 1,054 portable documents: **235 nodes state an ``allOf`` of exactly
    one ``$ref``**, 108 of them at a document root; of the 127 at a non-root position
    **7 state nothing else that is not NOTHING** -- 3 ``push_notification_config`` and 4
    ``context``, in four ``media-buy`` requests, each carrying ``x-adcp-schema-uri`` and
    nothing more -- and the next largest sibling set is a bare ``description`` at 50
    positions.  Admitting those 50 would drop a description the document states at a
    pointer, which is a different row and the opposite of this one.

    **The 7 are not 7 classes, and the 4 that are not say what this predicate adds.**
    ``core/context.json``'s root is not a class, so :func:`intersect.the_conjuncts_own_type`
    already answers those four with the target's symbol -- the same answer, through §5's
    other arm.  The 3 that reach here compose ``core/push-notification-config.json``, which
    IS a class, and are the group ``tests/test_one_node_is_one_declaration.py`` reports as
    four declarations of one type: the root's own and three empty subclasses of it.
    """
    return (
        node.position is not Position.ROOT
        and len(conjunct_bases) == 1
        and not bases
        and union is None
        and inherits is None
        and base_if_none_composes is None
        and set(node.declares) <= {"allOf"}
        and all(_carries_nothing(word, node.position) for word in node.annotations)
        and not node.rules
        and node.extra is None
        and getattr(node, "extras", None) is None
        and not local
        and not required
        and not conjunct_rules
        and not conjunct_values
        and not conjoined
        and contains is None
        and not facts
    )


def lower_composition(
    node: nodes.Base,
    mod: compiler.Module,
    *,
    bases: tuple[ir.TypeRef, ...] = (),
    union: compiler.UnionBase | None = None,
    inherits: compiler.Shape | None = None,
    base_if_none_composes: ir.TypeRef | None = None,
) -> str | ir.Decided | Refusal:
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
    :func:`codegen.lower.decide.decide`, which is §5's "root and non-root are one path":
    there was a table
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
    no constraint at all.  :func:`restatement` is the whole of that decision, and it is
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
    annotations of ``salesagent-j3k2l.36`` and two of them inversions.

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
    # was rebuilt here out of the keyword mapping a ``nodes.Union`` used to carry beside
    # its branches, which was a second reading of
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
    stated = compiler.rules_at(node, position=position, resolve=mod.resolve_node, root=mod.record)
    # **EVERY FACT A RULE SOURCE STATES AND THIS NODE DOES NOT CARRY IS DECLARED HERE, AND
    # THIS IS WHERE :attr:`Rules.dropped`'s FOURTH PRODUCER FOUND ITS CONSUMER**
    # (``docs/plan/final-state.md`` reading 2; ``adcp-client-python-gbo``'s sibling defect).
    # The set had four producers and ONE consumer -- :func:`declare_object`'s funnel -- and
    # this function read ``screen``, ``rules`` and ``distinct`` off the same carrier and
    # never ``dropped``, so a fact dropped on a route that does not reach a class was
    # recorded and discarded.  Measured: ``maxProperties: 20`` at ``/properties/ext`` in
    # ``core/account-change.json`` and ``core/account-change-recorded-webhook.json``, where
    # the node composes a reference to a document with no ``properties`` and this function
    # answers with a MAPPING type before any class is declared.
    #
    # **A DECLARATION NEEDS NO CLASS AT ITS OWN NODE, which is why this is a fix and not a
    # sentence.**  ``render.declared_at`` pairs a declaration with a class by a PREFIX test
    # on the pointer -- "a declaration at ``#/properties/x/maxLength`` is reached from the
    # root class's node as well as from the nested class's own" -- so a fact at
    # ``#/properties/ext`` is carried by the enclosing class the walk did declare, and the
    # widening obligation walks it from there.  The arm §5's row names for a mapping is a
    # different question and is still unreachable; what this closes is the declaration.
    #
    # Here rather than at every ``return`` below, because the drop is known the moment
    # ``rules_at`` answers and this function has many exits: a declaration per exit is the
    # arrangement that let one of them discard the set in the first place.  A node that goes
    # on to be a class declares the same facts again at :func:`declare_object`'s funnel and
    # ``emit.declared_once`` collapses the pair -- §8 sentence 2's identity is
    # ``(stating document, stating pointer, keyword)`` and two producers of one identity are
    # one declaration.
    if stated.dropped:
        from codegen.lower.approximate import declare as _declare_widening

        for drop in stated.dropped:
            _declare_widening(mod, drop.pointer, drop.keyword, drop.position, drop.fact)

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
    #: **The node's own VALUE CONSTRAINTS, which are the SAME siblings read by the same
    #: clause** (:attr:`nodes.Composition.facts`).  §5's ``$ref`` row at CONJ: "the target
    #: is this node's own TYPE, and the other conjuncts **and the ``allOf``'s siblings**
    #: constrain it", and §5's group (a) names the half that was missing -- "the refusals
    #: reading '*X* is not a class, so it cannot be a base' are the unimplemented half of
    #: that sentence".  A ``minLength`` beside an ``allOf`` is one of those siblings.
    #:
    #: CLAIMED here and read by :func:`the_conjuncts_own_type`, which is the pair §3
    #: requires of a lowering cell -- ``minLength``'s and ``minItems``' cells are a
    #: lowering effect at every position the walk decides a node at, so a screen that
    #: drops one promises "a later D2 row does" for a row that would have to be this one.
    #: It reached that promise, measured on both documents the field has a population at:
    #: ``core/catalog-selection.json`` refused on ``minLength`` at ``/properties/query``
    #: with ``DEFERRED_TO_A_LATER_ROW``, carrying 5 chained documents with it, and
    #: ``trusted-match/context-match-response.json`` on ``minItems``.
    facts: Mapping[str, Any] = getattr(node, "facts", {})
    claimed = COMPOSING | stated.screen | ({union.combinator} if union is not None else set())
    if contains is not None:
        claimed = claimed | {"contains"}
    claimed = claimed | set(facts)
    screened = compiler.check_keywords(node, claimed, mod=mod)
    if screened is not None:
        return screened

    conjunct_bases: list[ir.TypeRef] = []
    #: **§5's ``$ref`` row at CONJ where the target is NOT a class**: the symbol is this
    #: node's own TYPE and not a base, with the conjunct's own pointer beside it so the
    #: refusal for a shape this row does not answer can name the conjunct that carried
    #: it.  The TARGET and not its symbol alone, because the refusal for a node that
    #: declares fields has to name WHICH of §5's non-class targets this one is
    #: (:data:`_NOT_A_BASE`) and :attr:`Target.kind` is the one derivation of that.
    #: Read once, by :func:`the_conjuncts_own_type`, after the worklist.  The parsed
    #: REFERENCE rides beside the two, because a distributed branch is declared from it
    #: (:func:`_conjunct_base`).
    conjoined: list[tuple[str, compiler.Target, nodes.Reference]] = []
    inherited: dict[str, dict] = {}
    inherited_required: set[str] = set()
    #: The ``extra`` policy the FIRST of this node's bases that resolved one resolved, in
    #: the order the document composes them -- the caller's own base first and the ``$ref``
    #: conjuncts after, which is the order :attr:`Shape.description` is gap-filled in and
    #: for that attribute's reason: ``harness._composed`` reads the composed document that
    #: way and the two halves have to read it the same.  So the value
    #: :func:`declare_object` writes where this node states no ``additionalProperties`` is
    #: the composed document's, not whichever base pydantic's ``model_config`` merge
    #: happens to reach last.
    #:
    #: **FIRST-WINS HERE AND CLOSED-WINS AT A BRANCH, and the asymmetry is the scope of
    #: what was measured** (:func:`compiler.stated_extra`, ``adcp-client-python-szfx``).  A
    #: BRANCH's two views are the enclosing ROOT and the branch's own ``$ref`` target, and
    #: draft-07 applies both to the same instance -- so ``false`` on either closes, which
    #: 6 pairs put to ``jsonschema`` at their own pointers.  A COMPOSING node is a
    #: different question and no pair has asked it: among this node's views is a ``$ref``
    #: target that may itself be a union whose BRANCHES close while the target's own root
    #: states nothing, and closing this node on a branch's word would be a class refusing
    #: what the composed document admits.  So the gap-fill stands here until something
    #: measures it, which is the direction §2 forbids guessing in.
    inherited_extra: str | None = None
    #: The FIELD each inherited key came out as on the base that declares it, and the
    #: base it came from.  Read only by the annotation-only arm below, which re-uses
    #: the field rather than re-deciding the node; :attr:`Shape.decided` says why.
    inherited_fields: dict[str, ir.Field] = {}
    inherited_from: dict[str, compiler.Target] = {}
    #: :attr:`Shape.nested` from the same bases, read by the one arm that needs a base's
    #: field set ONE LEVEL DOWN: a restatement that narrows a property and is SILENT about
    #: that property's own nested keys (``adcp-client-python-8212``).
    inherited_nested: dict[str, compiler.Shape] = {}
    if inherits is not None:
        # §4's "a branch composes its own with them", seeded before the conjunct list:
        # the caller's own ``bases`` already declare these keys, so they are INHERITED
        # in exactly the sense a ``$ref`` conjunct's are, and every reading below -- the
        # restatement rule, the requiredness overlay, the re-use of a decided field --
        # is the one §2 states for a base.  ``inherited_from`` is left empty on purpose:
        # the base is in this module, so there is nothing to import (:func:`_reused`).
        inherited.update(inherits.properties)
        inherited_fields.update(inherits.decided)
        inherited_nested.update(inherits.nested)
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
    #: Each of those conjuncts' own POINTER, in the same order.  Carried for the
    #: DECLARATION and nothing else: a fact a conjunct states and the composed class does
    #: not carry is declared where the document states it, which is the conjunct's pointer
    #: and not this node's (``adcp-client-python-3be.29`` is the same defect read from the
    #: other end).
    #:
    #: **``None`` where the rule is the TARGET's and not this document's**, which is §8
    #: sentence 2 read at the one conjunct that can state a rule it did not write: a
    #: ``$ref`` whose target declares only a rule (:func:`_a_rule_the_target_states`)
    #: contributes the TARGET's node, so the stating site is in the target's document and
    #: this pointer states nothing but the reference.  The target is itself a portable
    #: document and its own walk declares the fact at its own pointer; a declaration minted
    #: here would be "once per pointer the record inlines it to", which §8 forbids by name
    #: and which ``emit.stated_where_declared`` catches as a ``BuildFailure`` --
    #: ``core/targeting.json#/allOf/0``, a ``$ref`` to
    #: ``core/targeting-unknown-age-eligibility-constraint.json`` whose root is an
    #: ``if``/``then``, is the pointer that measured it.  :func:`compiler.rules_at` reads
    #: the ``None`` as "this view's drops are not this document's to declare".
    conjunct_sites: list[str | None] = []
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
        # **A declaration that ADMITS NOTHING claims no field here either**, which is §5's
        # ``properties`` row read at the composing row's own property map.  ``_object``
        # drops it on the object row and this is the other place a property map is built
        # -- ``account/sync-accounts-response.json`` at
        # ``/oneOf/0/properties/accounts/items`` is the measured site, a node stating
        # ``properties`` beside an ``allOf``, so it reaches THIS loop and not that one and
        # it kept emitting ``destination_billing_entity: Any | None`` after the object row
        # stopped.  The presence half is :func:`rules_at`'s, off
        # :attr:`nodes.Base.declared`, which stays the document's own map -- so the key is
        # dropped from the FIELDS at both of the two places they are claimed and from
        # nothing else.
        #
        # The intersection is not consulted and the VERDICT does not need it: where one
        # declaration of a key admits nothing the composed accepted set forbids the key
        # whatever the other declaration says, and the rule that refuses it is written
        # off the map that still holds the forbidding declaration.  So a second
        # declaration winning the field cannot widen the class -- it can only make the
        # annotation of a key no payload may carry read as though a value were possible,
        # which is not an acceptance fact.  No node of the bundle states two declarations
        # of one key with either of them forbidding.
        if schema.admits_nothing(node):
            return None
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
        if intersect.restatement(node, prior, mod.resolve_node):
            # The INTERSECTION and not the narrower node alone (section 2, :func:`intersection`):
            # both declarations apply to the same instance, so a keyword only the wider
            # one states is still the composed node's.
            local[key], at[key] = intersect.intersection(node, prior, mod.resolve_node), where
        elif intersect.restatement(prior, node, mod.resolve_node) is None:
            return Refusal(
                intersect.disagreeing(node, prior),
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
        # **A key whose cell carries NOTHING is not in ``keys`` at all**, so this loop
        # has nothing to subtract and nothing to report.  It used to hold both: a set of
        # names whose cell said REFUSE, dropped from ``keys`` and reported here, with
        # ``errorMessage`` at ``media-buy/sync-catalogs-request``'s ``/allOf/1`` the one
        # occurrence.  The cell is NOTHING now (§7, 2026-10-26), so ``keywords.declares``
        # answers no for it and ``declaring`` leaves it out -- and the REPORT moved to
        # ``bundle.reported_drops``, which is the whole of §7's position rule: this
        # worklist reads CONJ and the same document states the keyword at ``/then`` as
        # well, where no conjunct encloses it and this channel could never have reached.
        keys = set(intersect.declaring(conjunct, Position.CONJ))
        # **The conjunct's rule sources, read BEFORE the arms rather than between two of
        # them**, because :func:`classify` needs them to answer and a classification that
        # ran twice would be two readings of one conjunct.  It is a pure projection of the
        # declaration by the table's own columns, so asking it of a bare ``$ref`` conjunct
        # that will not use it costs a dict comprehension and settles nothing twice.
        screen = frozenset(compiler.declaration_rule_sources(conjunct, Position.CONJ))
        kind = classify(keys, screen)
        if kind is Conjunct.REFERENCE_WITH_SIBLINGS:
            # A conjunct that is a ``$ref`` AND something else.  **The CONSTRAINING
            # siblings compile to nothing and are REPORTED** -- §5's ``$ref`` row as
            # the design owner settled it on 2026-10-25, read through
            # :func:`inert_beside_a_reference` so that this arm and
            # ``lower/references.py``'s arm decide one co-occurrence once.  The
            # conjunct is then the bare ``$ref`` it effectively is, and the base arm
            # below binds it.
            #
            # What is left refuses by name: a key with NO ROW is a keyword the bundle
            # did not use before and could constrain anything (§9).  That is the ONLY
            # thing left to refuse on -- §7 is empty, so no cell can be the answer here.
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
                    kind=compiler.kind_for(min(remaining), Position.CONJ),
                )
            keys = {"$ref"}
            kind = Conjunct.BASE
        if kind is Conjunct.BASE:
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
            if target.kind is not compiler.TargetKind.CLASS:
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
                # and :func:`the_conjuncts_own_type` below is what answers with it once
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
                    # ``None``: the rule is the TARGET's node, so the stating site is in
                    # the target's document and the target's own walk declares it
                    # (:data:`conjunct_sites`, §8 sentence 2).
                    conjunct_sites.append(None)
                    continue
                if target.branches is not None:
                    # **§5's distribution clause drops a branch whose intersection with
                    # what this node asserts is PROVABLY empty, and the drop is decided
                    # HERE because it can be** -- it is a question about DECLARATIONS
                    # (:func:`asserted_properties`), which §2 is where every intersection
                    # is computed, and the raw declarations are all read before this loop
                    # starts.  The two answers that depend on the whole conjunct list are
                    # still :func:`the_conjuncts_own_type`'s and are unchanged.
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
                    asserted = asserted_properties(node, conjuncts)
                    live = surviving(asserted, target.branches)
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
                            kind=compiler.kind_for("allOf", Position.CONJ),
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
            inherited_nested.update(target.declares.nested)
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
        if kind is Conjunct.INLINE_OBJECT:
            # The claim set is this arm's own coverage and nothing else.  It carried a
            # ``foreign`` set too -- the names whose cell said REFUSE, handed in as
            # CLAIMED so that ``check_declaration`` did not refuse on the very name this
            # loop had just dropped and reported.  With §7 empty there is no such name:
            # a cell carrying NOTHING is admitted by the screen on its own, and the drop
            # is reported by ``bundle.reported_drops`` at every position the document
            # states it at rather than at the ones a conjunct encloses.
            unadmitted = compiler.check_declaration(
                conjunct,
                where,
                Position.CONJ,
                set(INLINE) | screen | set(CONJ_COMPOSES),
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
            if "additionalProperties" in keys and inherited_extra is None:
                # **``true`` IS the identity for the composed value schema and it is NOT
                # the identity for the class's ``extra``, which is the asymmetry
                # ``adcp-client-python-6oe`` measured.**  §5's ``additionalProperties``
                # row says the value "is read from what the document states at the class's
                # own pointer AFTER THE DOCUMENT-SIDE FOLD -- which is where the root's
                # conjunct arrives", and ``harness.FOLDED_FACTS`` carries the keyword, so
                # the document-side reading already puts a conjunct's ``true`` at this
                # pointer.  The walk dropped it, and the two halves then disagreed about
                # what the document states here -- which is the one thing §9's two
                # spellings exist to prevent.
                #
                # It is not a cosmetic difference: ``absent -> ignore`` drops every key
                # the document counts, so §5's ``minProperties`` gate ("written only where
                # ``additionalProperties`` is stated") passed on the conjunct's word while
                # the class it wrote the rule onto kept none of the keys -- a
                # ``PropertyCount(minimum=…)`` refusing what the document admits, which is
                # the one direction §2 forbids outright.
                #
                # First-wins over the conjunct list and after the caller's own bases, which
                # is exactly the order ``inherited_extra`` is already filled in and the
                # order ``harness._composed`` gap-fills in -- so the two readings of "what
                # does the document state here" cannot come apart.  ``true`` is the only
                # value reachable: anything else refused two lines above.
                inherited_extra = "allow"
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
                conjunct_sites.append(where)
            continue
        if kind is Conjunct.COMBINATOR:
            combinator = next(k for k in _COMBINATORS if k in keys)
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
        if kind is Conjunct.VALUE_SET:
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
            # :func:`the_conjuncts_own_type` is: whether this conjunct narrows a TYPE or
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

    if node.rules.get("uniqueItems") is True:
        # **THE NODE'S OWN ``uniqueItems``, WHICH THIS HANDLER CLAIMS**, split into the
        # three arms draft-07's keyword semantics give it and §2's clause of 2026-10-29
        # sorts.
        #
        # ``rules_at``'s ``screen`` is ``frozenset(node.rules)`` -- every key whose cell
        # is RULE here, claimed whatever came of it -- while the rule itself is
        # ``lower.rules._distinct``, which reads a ``uniqueItems`` ONE LEVEL DOWN, off the
        # array a PROPERTY of the class ABOVE this node holds.  So the question is whose
        # claim this keyword is, and §2 answers it: "A composing DECLARATION is not a
        # position where no class encloses the value.  A property whose declaration is an
        # ``allOf`` still sits in the class that holds the property, so the clause above
        # is unchanged and the rule is declared there -- the reader that writes it must
        # see through the composition rather than the rule move to the value's own type."
        #
        # **The arm is chosen by what the conjuncts make the INSTANCE and by whether a
        # class encloses it**, and the first half is :func:`declares_an_array` -- the
        # same function ``_distinct``'s gate is, asked of the same declaration in the
        # spelling this row holds it, so the gate cannot claim a key this arm refuses or
        # refuse one the gate claimed:
        #
        # * the conjuncts do NOT make the instance an array -- all class bases, a scalar
        #   target, an enumeration -- and draft-07 applies ``uniqueItems`` to an ARRAY and
        #   ignores it for every other instance, so the keyword constrains nothing here
        #   and the drop is EXACT.  Dropped and REPORTED, which is §7's own shape for a
        #   name that cannot constrain an instance, and not refused.  0 sites over the
        #   portable population.
        # * they DO, and this node is a PROP: the class holding the field states the rule,
        #   which is §5's ``uniqueItems`` row's first clause and ``_distinct``'s claim.
        #   Nothing is carried here -- the rule tuple is on the enclosing class and
        #   :attr:`codegen.ir.Field.distinct` renders the fact onto the field, exactly as
        #   it is for an array that spells its own ``type`` word at this position
        #   (``lower.containers.array``'s PROP gate).  **3 sites**, all in
        #   ``core/catalog-selection.json``.
        # * they DO and no class encloses the value -- a ROOT, a mapping value, a
        #   ``definitions`` entry, a union branch.  §5's row's SECOND clause is the answer
        #   there and the ``Distinct`` would hang on the composition's own annotated type;
        #   that is unwritten, so this is a DEFERRAL naming it.  **0 sites** over the
        #   portable population, written so the first one is loud rather than dropped.
        #
        # Measured over the 1,054 portable documents, on the documents' own text: **3
        # composing nodes state ``uniqueItems``, all three in ``core/catalog-selection.json``
        # at ``/properties/ids``, ``/properties/gtins`` and ``/properties/tags``, each a
        # bare ``$ref`` to an array property of ``core/catalog.json``.**  With neither
        # half claiming them the document emitted and all three were dropped: the class
        # carried no ``UniqueItems`` rule and the fields no ``json_schema_extra``, over
        # the document and the 5 that reference it -- a model accepting duplicates its
        # document refuses, with no declaration.  That is what the gate reading a
        # conjunct closes.
        # ``conjuncts`` and not ``node.conjuncts``: this parameter is a ``nodes.Base`` and
        # three kinds declare the field, so the ONE reading this function makes of it is
        # the ``getattr`` above -- the direct access was §14 step 6's sixth error and the
        # local is also the safer spelling, answering ``()`` where the kind has none
        # rather than raising an ``AttributeError`` that names no document.
        if not intersect.a_conjunct_declares_an_array((c.raw for c in conjuncts), mod.resolve_node):
            mod.carries_nothing.append(
                f"{pointer}: uniqueItems: this node's conjuncts put no array at its "
                "instance, and draft-07 applies uniqueItems to an array and ignores it "
                "for every other instance -- the keyword constrains no instance here and "
                "the class carries nothing for it"
            )
        elif position is not Position.PROP:
            return Refusal(
                "uniqueItems",
                pointer,
                "this node composes an array and states uniqueItems at a position no "
                "class encloses: section 5's uniqueItems row puts the rule on the nearest "
                "class and there is none, so its second clause -- a Distinct on the "
                "value's own annotated type -- is the answer, and for a COMPOSITION that "
                "clause is unwritten.  Dropping it would widen the model to accept "
                "duplicates the document refuses",
                kind=compiler.kind_for("uniqueItems", position),
            )

    sibling = a_sibling_with_no_type_to_constrain(
        contains=contains,
        conjunct_values=conjunct_values,
        facts=facts,
        conjoined=conjoined,
        pointer=pointer,
        position=position,
    )
    if sibling is not None:
        return sibling

    if states_nothing_but_a_reference(
        node,
        conjunct_bases=conjunct_bases,
        bases=bases,
        union=union,
        inherits=inherits,
        base_if_none_composes=base_if_none_composes,
        local=local,
        required=required,
        conjunct_rules=conjunct_rules,
        conjunct_values=conjunct_values,
        conjoined=conjoined,
        contains=contains,
        facts=facts,
    ):
        # **A SUBCLASS THAT ADDS NOTHING IS NOT A BASE, IT IS A SECOND NAME FOR ONE
        # TYPE**, which is ``docs/plan/final-state.md`` reading 4 read at this row's own
        # limit: "a type stated at more than one position is written once and referenced,
        # never restated".  §5's ``$ref`` row at CONJ gives "a BASE where the target is a
        # class DECLARING FIELDS", and the clause the predicate above holds the compiler
        # to is the one §5 states for the row's other arm -- "at a node that declares no
        # fields of its own" -- which is a property of THIS node and not of the target's
        # kind.  Where it holds and the target is a class, the base would supply every
        # field, every rule, every ``extra`` and the description, and the subclass would
        # state nothing: so the target is this node's own TYPE here exactly as it is where
        # the target is a scalar, and the answer is one return rather than a second shape.
        #
        # **ROOT is excluded and that is §1 and D5 rather than a caution.**
        # ``lower.references._root`` already decided the same question for a bare ``$ref``
        # at a document root and answered SUBCLASS: "binding this module's symbol to
        # another module's class would be a second way to reach one class, against §1",
        # and D5 fixes a root's symbol so the module must declare one.  A non-root
        # position declares no symbol of its own -- the field's annotation is the imported
        # name -- so there is nothing for a second reach to be.
        return ir.Decided(conjunct_bases[0])


    #: §5's DISTRIBUTION clause, where the row above answered with the target's BRANCHES:
    #: the conjunct's own pointer, the branches, and the node each branch class is
    #: declared from.  ``None`` at every other node, which is what the tail below reads to
    #: tell a class from a union base.
    distributing: tuple[str, compiler.TargetBranches, nodes.Reference] | None = None
    if conjoined:
        # **§5's ``$ref`` row at CONJ, read after the WHOLE list** (§14 step 9): the
        # answer is a TYPE and not a class, and whether the row holds depends on what the
        # other conjuncts contribute -- so it cannot be decided at the conjunct that
        # carried the reference.  ``local`` is every key some view of this node declares,
        # which is the "declares no fields of its own" clause asked of the node and its
        # conjuncts together.
        answered = intersect.the_conjuncts_own_type(
            node,
            conjoined,
            fields_declared=set(local) | set(inherited) | required,
            bases=(*bases, *conjunct_bases),
            # **The node's own ``contains`` joins the conjuncts' rule sources**, which is
            # §5's ``$ref`` row at CONJ read whole: "the other conjuncts AND THE
            # ``allOf``'s SIBLINGS constrain it".  One list and not two, because
            # :func:`the_conjuncts_own_type` already folds its sources into a single
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
            # **And the node's own BOUNDS are the same clause's other siblings**
            # (:attr:`nodes.Composition.facts`): "the other conjuncts AND THE ``allOf``'s
            # SIBLINGS constrain it".  A ``contains`` is a sibling that becomes a RULE and
            # a bound is one that becomes a CONSTRAINT, so the two travel in the two
            # carriers §2 already keeps apart -- :attr:`ir.TypeRef.validators` and
            # :attr:`codegen.ir.Decided.constraints` -- rather than in one list the callee splits.
            facts=facts,
            # The document of record, for §8's sentence 3a -- the ``if`` row's reading
            # through the storage.  Passed rather than read off a module here because this
            # callee takes no module (§11: a pure reading of a node).
            record=mod.record,
        )
        if isinstance(answered, ir.Decided) and conjunct_values:
            # **§5's ``enum`` row at CONJ, applied to the type the row above decided.**
            # The reference is the one that supplied the type, which is the same
            # ``conjoined[0]`` the row reads, and the narrowing is §2's intersection over
            # DECLARATIONS -- the TARGET's vocabulary read through
            # :meth:`Module.resolve_node`, not the symbol it was bound to.
            return _the_vocabularys_intersection(
                answered, conjunct_values, conjoined[0][2], mod
            )
        if not isinstance(answered, compiler.TargetBranches):
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
        union = compiler.UnionBase(
            # §5's ``required`` row at ROOT beside a union.  Every name here is one this
            # node's own views declare, so none of them selects a branch -- the branches'
            # own requiredness is the TARGET's and reaches each branch class through its
            # target base -- and ``fields`` holds a field for each.
            root_required=tuple(sorted(required)),
            discriminator=branches.discriminator,
            combinator=branches.combinator,
            branches=tuple(
                ir.TypeRef(distributed_pointer(where, branches, j), local=True)
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

    stated = compiler.rules_at(
        node,
        *conjunct_rules,
        position=position,
        resolve=mod.resolve_node,
        at=tuple(conjunct_sites),
        root=mod.record,
    )
    merged = inherited_row.merge(
        local,
        inherited,
        at=at,
        pointer=pointer,
        required=required,
        inherited_required=inherited_required,
        inherited_fields=inherited_fields,
        inherited_nested=inherited_nested,
        inherited_from=inherited_from,
        mod=mod,
    )
    if isinstance(merged, Refusal):
        return merged
    own, reuse, inherited_distinct = merged.own, merged.reuse, merged.distinct

    # **§3a's PASS B: a property this class RESTATES with a pin the base's enumeration
    # already contains.**  "``core/registry-event.json`` states ``enum: [...]`` at its
    # root's ``event_type`` and ``const: 'property.created'`` at its branch's.  One
    # vocabulary, two keywords" -- and this is the one site in the compiler where both
    # spellings are in hand at once: ``own[key]`` is §2's intersection of the two
    # declarations, ``inherited[key]`` is the base's own, and ``inherited_fields[key]`` is
    # the enumeration the base DECIDED for it.
    #
    # **Imported on use, for ``lower_node``'s reason**: ``codegen.lower.normalise`` imports
    # ``codegen.lower.enum`` for the one ``member_name`` the declaring side minted the
    # members with, and that module imports this one, so a module-level arrow here would
    # close a cycle.  It is a LAYER DOWN and not the run.
    #
    # The decision is ``normalise.pins_a_member``'s and the IMPORT is ``_reused``'s: where
    # the base is another module's, the symbol the narrowed type names has to be importable
    # here or the class is an undefined name, and that function is the one reader of
    # :attr:`Target.imports`.  It is called only where the row fires, so a key the
    # normalisation declines imports nothing.
    from codegen.lower import normalise

    pinned: dict[str, ir.TypeRef] = {}
    for key in sorted(set(own) & set(inherited) - set(reuse)):
        narrowed = normalise.pins_a_member(
            intersect.constraining(own[key]),
            intersect.constraining(intersect.dereferenced(inherited[key], mod.resolve_node)),
            inherited_fields.get(key),
        )
        if narrowed is None or not _placeable(narrowed.path, mod):
            continue
        pinned[key] = narrowed

    # **The merged declarations go through the PARSER**, which is ``schema/nodes.py``'s
    # own sentence about why a conjunct is a declaration: §2's intersection rule merges
    # two declarations of one property and "hands the merged declaration back to
    # :func:`codegen.schema.parse.parse`", because the result has to be parsed as ONE node
    # rather than composed out of two decided ones.  So the one reader of a raw mapping
    # reads these too, at the pointer the key was declared at.
    parsed_own = {
        key: intersect.parsed_property(declaration, at.get(key, f"{pointer}/properties/{key}"), mod)
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
    decided = objects.fields(
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
        # §3a's Pass B, decided above and applied to the lowered pin.
        pinned=pinned,
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
    declared = objects.declare_object(
        node,
        pointer,
        mod,
        decided,
        # ``decided`` is what this class INHERITS; ``declare_object`` overlays the
        # fields it is handed, which are this class's own.  Passing the inherited ones
        # is what makes :attr:`Shape.decided` transitive the way ``properties`` is, so
        # a sub-subclass restating a key its grandparent declares reads one map.
        compiler.Shape(
            {**inherited, **own},
            frozenset(required | inherited_required),
            decided=inherited_fields,
            nested=inherited_nested,
            extra=inherited_extra,
        ),
        position,
        extras=getattr(node, "extras", None),
        # The same map ``fields`` read above: a key a CONJUNCT declared sits at the
        # conjunct's own pointer, which is where its child shape was recorded.
        declared_at=at,
        # The model base only where NOTHING composes; see ``base_if_none_composes``.
        bases=(
            (*bases, *conjunct_bases)
            if conjunct_bases or base_if_none_composes is None
            else (*bases, base_if_none_composes)
        ),
        rule_nodes=conjunct_rules,
        rule_sites=conjunct_sites,
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
        # ``None`` for a subclass with no docstring.  Measured: 5 such descriptions over
        # 4 pairs, every one a bare ``/description`` at a composing node whose own
        # declaration has none (``core/collection-selection.json``'s items and
        # ``core/canonical-media-buy-action.json``'s three branches).
        description=inherited_description,
    )
    if distributing is None or isinstance(declared, Refusal):
        return declared
    return _distribute(
        declared, *distributing, asserted=asserted_properties(node, conjuncts), mod=mod
    )


def a_sibling_with_no_type_to_constrain(
    *,
    contains: Any | None,
    conjunct_values: Sequence[tuple[str, Mapping[str, Any]]],
    facts: Mapping[str, Any],
    conjoined: Sequence[object],
    pointer: str,
    position: Position,
) -> Refusal | None:
    """§5's ``$ref`` row at CONJ read at the three SIBLINGS, where every conjunct is a base.

    The row's answer for a sibling of the conjunct list is "the target is this node's own
    TYPE, and the other conjuncts and the ``allOf``'s siblings constrain it".  That answer
    needs a type to constrain, and a node whose conjuncts are all CLASS bases has none: an
    instance of a class is not a member of a vocabulary, and a bound on a string or a list
    says nothing about one.

    Three siblings reach it and the three comments below are one reading at three keywords,
    which is why they are one function: a ``contains``, a conjunct that is a VALUE SET, and
    a BOUND.  Each refuses rather than dropping the keyword, because dropping it widens the
    model past its document and none of the three has a declaration to be widened AS.

    ``conjoined`` is the list of ``$ref`` conjuncts whose target IS a class; the screen is
    about the case where it is EMPTY, which is what "every conjunct is a base" means from
    this side.  Measured over the 1,054 portable documents: **0 sites** for the value set
    and 0 for the bound, so both are written to make the first one loud, and the
    ``contains`` arm is the one with a population.
    """
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
            kind=compiler.kind_for("contains", Position.CONJ),
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
            min(intersect.declaring(conjunct, Position.CONJ)),
            where,
            "a conjunct states a VALUE SET beside conjuncts that are all class bases: "
            "section 5's enum row at CONJ narrows the TYPE a non-class target supplies, "
            "and this node's type is a composed class -- an instance of a class is not a "
            "member of a vocabulary, so there is nothing here for the intersection to "
            "narrow and dropping the keyword would lose the document's own value set",
            kind=compiler.kind_for("enum", Position.CONJ),
        )
    if facts and not conjoined:
        # **A BOUND beside conjuncts that are all BASES, which §5's row does not reach
        # either**, and the reasoning is the two arms' above read at a third sibling: the
        # row's answer is the TARGET as this node's own TYPE, constrained; a node whose
        # conjuncts are classes has no such type, and a ``minLength`` or a ``minItems``
        # says nothing about an instance of a class -- draft-07 applies a constraint
        # keyword only to instances of the type it is defined for.  0 sites over the
        # portable population: both nodes that state one compose a non-class target, so
        # this is written so the first one is loud rather than emitted with the bound
        # dropped.
        return Refusal(
            min(facts),
            pointer,
            f"this node states {sorted(facts)} beside conjuncts that are all class "
            "bases: section 5's $ref row at CONJ makes a sibling constrain the TYPE a "
            "non-class target supplies, and this node's type is a composed class -- a "
            "bound on a string or a list says nothing about an instance of a class, so "
            "there is nothing here for it to constrain and dropping it would lose the "
            "document's own bound",
            kind=compiler.kind_for(min(facts), position),
        )
    return None


def distributed_pointer(where: str, branches: compiler.TargetBranches, index: int) -> str:
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


def _distribute(
    base: str,
    where: str,
    branches: compiler.TargetBranches,
    reference: nodes.Reference,
    *,
    asserted: Mapping[str, list[dict]],
    mod: compiler.Module,
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
        pointer = distributed_pointer(where, branches, index)
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
                kind=compiler.kind_for("allOf", Position.CONJ),
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
        # shadows the other (:func:`intersected_at_a_branch`).
        own = intersect.intersected_at_a_branch(
            asserted, branch.declares, branch.symbol, pointer, base_shape.required, mod
        )
        if isinstance(own, Refusal):
            return own
        made = objects.declare_object(
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
            compiler.Shape(
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
                # two bases sit in decides nothing.  **For this keyword the order decides
                # nothing in a second sense**: a view that CLOSES wins wherever it sits,
                # because draft-07 applies the root's closure and the branch's own to the
                # same instance (:func:`compiler.stated_extra`).
                extra=compiler.stated_extra(branch.declares.extra, base_shape.extra),
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


def _placeable(symbol: str, mod: compiler.Module) -> bool:
    """Is ``symbol`` NAMEABLE in this module -- declared here, or imported and recorded?

    §3a's Pass B names a member OF a symbol, so the symbol has to resolve in the module
    that writes the annotation or the class is an undefined name at import.  Three ways it
    does, and this asks all three because a base's field type reaches them by three
    different routes:

    * the symbol is a POINTER this module declares (:attr:`Module.at`) -- §4's union base
      is in this module, so its enumeration travels as a pointer until
      ``lower/names.py`` binds it, and a pointer is nameable by construction;
    * a declaration of this module already carries the name;
    * this module already IMPORTS it (:attr:`Module.imported`), which is the record
      :meth:`Module.importing` wrote when some other row named it.

    **It adds no import of its own, and that is the decision.**  Pass B narrows a type the
    BASE decided; it does not reach for a symbol this module had no other reason to name.
    Where the enumeration is two hops away -- a branch over a local union base whose own
    base in another module declares the field, which is ``core/protocol-envelope.json``'s
    ``status`` and 14 sites of it -- the narrowing is DECLINED rather than an import
    invented for it.  Measured: declining costs 14 of the 145 sites and keeps the rule that
    an import is derived from two document paths by ``emit.resolve`` and never by a
    lowering (D1, and :attr:`Target.imports`' own note).  The alternative was a search over
    every target the run resolved for a module that happens to offer the name, which is a
    second derivation of §1's one import path and is exactly what ``_reused``'s refusal
    exists to prevent.
    """
    if symbol in mod.at or symbol in mod.imported:
        return True
    return any(
        getattr(declaration, "name", None) == symbol for declaration in mod.declarations
    )
