"""D6's six keyword families: what a document says about an instance AS A WHOLE.

``oneOf``/``anyOf`` over ``required``; ``if``/``then``/``else``; ``dependencies``;
``min``/``maxProperties``; ``uniqueItems``; ``not``.  None of them has a field to live
on, so none can be a ``Field`` kwarg.  Each becomes either an INSTANCE of one of
``adcp.types._runtime``'s frozen dataclasses -- which ``codegen.render`` writes into the
one class-level ``_adcp_rules`` tuple that ``adcp.types._runtime.RuleBound`` reads -- or,
when it is a statement about a VALUE rather than about which keys are present, an
instance of one of the runtime's VALUE-rule kinds, which ``codegen.render`` writes into
the value's own ``Annotated``.  **The rule kinds are declared once, in the runtime** (§2
of the semantics document, "rules are after-validators, written once"; §7 of the
architecture document for why the walk composes values and holds no text).

**§2's two places a rule hangs are :func:`lower` and :func:`on_a_value`, and they are in
one module on purpose**: "on the nearest class if there is one ... where no class sits
above the value -- a root array, a mapping value, a ``definitions`` entry, a union branch
-- the rule hangs off the value's own annotated type as an after-validator
(``AtLeastOne``, ``NotValue``, ``Distinct``)."  One reader decides which half a
document's statement takes, so the two cannot both claim it and neither can silently
drop it.

**§2's clause of 2026-10-28 adds the other axis, and :func:`as_the_object` is it**: "a
value-level rule may state which KEYS the value supplied, and the three kinds above are
not the limit ... at a position with no class above it, the value *is* the object."  So a
rule :func:`lower` wrote for a class may hang on the value's own type where there is no
class, and whether it may is a property of the KIND -- "a callable on the value, and all
it is" -- asked as ``isinstance(rule, ValueRule)`` and never as a list of names here.
The kinds that are not get NAMED back to the caller, which is why that function returns
two tuples rather than one.

**Nothing here refuses a document.**  That is D4, and it is the one judgement this
module makes, so it is stated once rather than per keyword.  The accepted set of every
emitted class is ``strict_validate``, which validates the payload against the
document's own schema and therefore refuses every one of these keywords already,
expressible as a rule or not.  A rule is NOT what makes the model as narrow as its
document; it is what makes the ``model_validate`` CONSTRUCTOR as narrow, on the subset
of statements that are about key presence.  Refusing a document for the rest would cost
the whole ``if`` population for constraints the accepted set enforces, and would buy no
narrowing anywhere.

What that trades away, named here so it is not discovered later:
``core/canvas-constraint.json``'s ``if unit == "percent" then x.maximum = 100`` gets no
rule, so ``CanvasConstraint.model_validate({"unit": "percent", "x": 101})`` builds while
``CanvasConstraint.strict_validate`` of the same payload refuses on ``maximum``.  That
pair is a committed test, so the ceiling is measured rather than claimed.

``uniqueItems`` is the one family whose keyword sits on a node BELOW the class that
carries the rule: the array a FIELD holds.  467 of the bundle's 485 occurrences are at a
``properties/<name>`` slot, so D2's *a rule on the nearest class* makes the class holding
the array the one that states it, and :func:`_distinct` reads it off this node's own
``properties``.  The array row's own keyword screen is left alone, which is the
decision rather than an omission: the 18 sites with no class above them are
:func:`on_a_value`'s, and the array row writes a :class:`adcp.types._runtime.Distinct`
onto the array's own annotated type there.  **That array row used to DECLARE AN
APPROXIMATION for each of them** -- 13 of the tree's 17 -- on the ground that "a rule has
nowhere to live there".  It was never true: ``Annotated[list[X], AfterValidator(…)]``
carries a rule, §2 always said so, and what was actually missing was the three kinds.
A ROOT array is the one of the four that still takes a rule TUPLE rather than a
validator, because it is a root model and a root model has one.

**A property that declares its array through a COMPOSITION is in the first group and not
the third**, which is §2's clause of 2026-10-29: "A composing DECLARATION is not a
position where no class encloses the value.  A property whose declaration is an ``allOf``
still sits in the class that holds the property, so the clause above is unchanged and the
rule is declared there -- the reader that writes it must see through the composition
rather than the rule move to the value's own type."  So :func:`_distinct`'s gate is
``intersect.declares_an_array``, which reads a conjunct through its ``$ref``, and the
resolver it needs is the one parameter :func:`lower` takes that is not a fact of the
node.

**The step-5 boundary, and why it is a predicate and not a precedence rule.**  A
``oneOf``/``anyOf`` whose branches are SHAPES is a union root: a base, one subclass per
branch, step 5's row.  A ``oneOf``/``anyOf`` whose every branch states only which keys
are PRESENT has no shape to subclass -- the branches declare no property at all -- so it
is a class plus a rule, which is this row.  :func:`presence_only` is that test, and
``populations.states_an_object_rule`` is the selector built on it, so the two rows cannot
both claim one document and the unordered dispatch table has no precedence question to
answer.

**A presence branch may also FORBID**, which is §5's "A union of presence-only branches
that also forbid" (decided 2026-10-27): branch *i* reads "every name in R*ᵢ* present and
no group of F*ᵢ* present".  Both halves belong to the branch, so they travel together in
one clause of one rule -- :class:`adcp.types._runtime.PresenceGroups` -- and
:func:`codegen.schema.parse.presence_clause` is the one reading of a branch that answers
both the boundary predicate and the clause values.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from adcp.types import _base
from adcp.types._runtime import (
    AtLeastOne,
    ConditionalRequired,
    Dependencies,
    Distinct,
    ForbiddenGroups,
    Match,
    NegatedConditional,
    NotValue,
    Presence,
    PresenceGroups,
    PropertyCount,
    RequiredGroups,
    Rule,
    UniqueItems,
    ValueRule,
)
from codegen import compiler, intersect
from codegen.keywords import Position
from codegen.schema import parse as schema

#: **ONE ``if`` CLAUSE, as the reduction hands it to :class:`adcp.types._runtime.Match`:**
#: ``(key, present, allowed values, forbidden values)``.
#:
#: Named because four readers pass it between them and a four-tuple spelled out at each
#: one is four places to go stale -- which is what the checker reported the moment §8
#: sentence 3b's complement widened ``present`` to three states and added the second value
#: set.  ``present is None`` is IMMATERIAL and ``forbidden`` is the complement of
#: ``allowed``; ``Match``'s own docstring is the declaration of what they mean.
Clause = tuple[str, bool | None, tuple[Any, ...] | None, tuple[Any, ...] | None]

#: Everything this module reads off a node with FIELDS: the keywords whose CELL
#: compiles to a RULE, read off ``codegen.keywords`` at the position asked about.
#:
#: Not a set here and not a set in ``compiler`` either: ``compiler.rule_sources`` is a
#: reading of the declaration, and ``compiler.rules_at`` is the screen a lowering
#: actually asks, because a combinator is a rule source only where
#: :func:`presence_only` holds -- a co-occurrence, which the table is not keyed by.
#: Three lowerings screen on it and two of them (the ``allOf`` row, the union row)
#: cannot import this module at all (D13), which is why the reading sits in
#: ``compiler``, below both packages.
KEYWORDS = compiler.rule_sources

#: Of those, the ones that can appear on a node with no object to carry a rule -- a
#: scalar, where a rule tuple has nowhere to live.  Measured over the 1,054 portable
#: documents: ``not`` and nothing else, and every one of those is
#: ``not: {"const": <value>}`` or ``not: {"enum": [...]}`` -- an excluded VALUE, and so
#: the schema's statement by the same reasoning as the rest of this module.
#: ``minProperties`` and ``uniqueItems`` say nothing about a scalar and do not appear on
#: one; a conditional and a combinator would, and do not.
ON_A_VALUE = frozenset({"not"})

#: The two combinators, and the order a rule tuple lists them in.
_COMBINATORS = ("oneOf", "anyOf")


@dataclass
class Lowered:
    """What one object node's rules come to.

    ``rules`` holds INSTANCES of the runtime's own frozen dataclasses, in document
    order, which is what makes the emitted tuple a function of the document rather than
    of a dict's iteration (P7).  They were constructor expressions as TEXT, and
    ``docs/plan/architecture.md`` §7 is why they are values: a rule kind is declared
    ONCE, in ``adcp.types._runtime``, and ``codegen.render`` writes the call and reports
    the names it uses -- so adding a kind adds a dataclass and a lowering and renames
    nothing.
    """

    rules: list[Rule] = field(default_factory=list)
    #: **Every keyword this node STATES whose fact no rule above carries, with the
    #: document's own value beside it** -- which is what §2 calls a WIDENING and what
    #: ``docs/plan/final-state.md`` reading 2 makes a DECLARATION rather than a silence.
    #:
    #: The module docstring above says a rule is "not what makes the model as narrow as
    #: its document" and names the ceiling it trades away; reading 2 is the other half of
    #: that sentence -- "every exception to reading 1 is a DECLARED widening" -- and this
    #: is the field that carries one out to the caller that can declare it.  §5's rows say
    #: the ANNOTATION is nothing here ("otherwise nothing, and the schema half answers"),
    #: which is a decision about what to render and not an exemption from declaring: a
    #: ``model_validate`` that builds a payload the document refuses is reading 1 failing,
    #: and §2 permits it only where the run says so at the pointer.
    #:
    #: ``(keyword, the value the DOCUMENT states for it)``, in the order the reductions
    #: ran, so the declaration carries the document's own spelling of the fact --
    #: ``lower.approximate``'s "``fact`` is a parameter and the caller passes what the
    #: DOCUMENT states, never a value the walk derived".
    dropped: list[tuple[str, Any]] = field(default_factory=list)
    #: The property keys whose array this node states is DISTINCT, in document order.
    #: Names only, because the keyword's two consequences belong to the compiler: it
    #: is stripped off the declaration before the array row sees it, and it is
    #: rendered onto the field as the ``json_schema_extra`` half of the fact the
    #: ``UniqueItems`` rule enforces (``lower.objects.fields``, ``ir.Field.distinct``).
    #: A declaration re-cut
    #: here instead would put the walk's input in two modules.
    distinct: tuple[str, ...] = ()


def lower(
    sources: Mapping[str, Any],
    declared: Mapping[str, Any] = {},  # read-only, and the empty mapping is the answer
    extra_stated: bool = False,
    *,
    resolve: intersect.Resolver = None,
    root: Mapping[str, Any] | None = None,
) -> Lowered:
    """Every rule one node states, off the three facts a node carries for it.

    ``sources`` is :attr:`codegen.schema.nodes.Base.rules` -- "the rule sources this node
    carries: ``keyword -> the raw value``, for the keywords whose cell at this position
    compiles to a RULE" -- and §4 makes this module its only reader.  Two facts are not
    rule sources and are read beside them, each for a reason stated at its own reduction:
    ``declared`` because ``uniqueItems`` sits on a node one level DOWN (the array a
    property holds) **and because a ``properties`` entry that ADMITS NOTHING is a
    statement about PRESENCE, which is :func:`_negated`'s rule and not a field**, and
    ``extra_stated`` because the ``minProperties`` minimum rides only where the class
    keeps every key the document would count.

    ``resolve`` is the fourth and belongs to the same reduction as the second:
    :func:`_distinct` has to answer "is this property an ARRAY" of a declaration that
    may say so through a ``$ref`` under an ``allOf``, and ``intersect.declares_an_array``
    is the one reading of that.  ``None`` is the safe arm -- a composing declaration is
    then not claimed, and the handler that claimed the keyword reports or refuses -- so a
    caller with no run to resolve against loses no fact silently.

    ``root`` is the fifth and belongs to §8's sentence 3a (decided 2026-11-03): **§5's
    ``if`` row reads through a LOCAL REFERENCE THE RECORD MINTED.**  The record stores
    each distinct subtree once under its own ``definitions`` (reading 5), so a condition --
    or a property declaration inside one -- may have been REPLACED by a reference naming a
    storage entry, and a reader that stops at the reference reads a node the document does
    not state.  ``architecture.md`` already decided the seam: *a reader asking what the
    document states reads through the storage*, which is
    :func:`adcp.types._base.through_the_store` and nothing else.  ``None`` is the safe arm
    -- a reference is then read as written, which is exactly what this module did before
    the storage existed -- so a caller with no record in hand loses no fact silently and
    declares instead.

    :func:`lower_declaration` is the same reading asked of a raw declaration, for §2's
    one declaration-level reader: an ``allOf`` conjunct.
    """
    out = Lowered()
    _depends(sources, out)
    _count(sources, out, extra_stated)
    _negated(sources, out, declared)
    _combinator(sources, out)
    _conditional(sources, out, root)
    _distinct(declared, out, resolve)
    return out


def lower_declaration(
    declaration: Mapping[str, Any],
    position: Position,
    *,
    resolve: intersect.Resolver = None,
    extra_stated: bool | None = None,
    root: Mapping[str, Any] | None = None,
) -> Lowered:
    """:func:`lower`, asked of a raw DECLARATION: an ``allOf`` conjunct's rules.

    The sources are ``compiler.declaration_rule_sources``, which is the one reading of
    them -- the conjunct SCREEN in ``lower_composition`` asks the same function for the
    same keys, so a conjunct's screen and its rule tuple cannot disagree about which
    keywords are rules at CONJ.

    **``extra_stated`` is the COMPOSED CLASS's answer where the caller has one, and the
    conjunct's own only where it does not** (``adcp-client-python-6oe``).  The gate
    :func:`_count` asks is "does the class keep every key the document would count", and
    that is a property of the CLASS the rule lands on: a draft-07 conjunct applies to the
    same instance, so one class carries every conjunct's rules and there is one extra
    policy for all of them.  Read off the conjunct alone the gate answered about a
    DIFFERENT object -- the conjunct's ``additionalProperties: true`` passed it while the
    composed class kept no key at all -- and the rule it admitted refused what the
    document admits.  ``None`` keeps the conjunct's own reading for a caller with no class
    in hand.
    """
    # Read ONCE into a local, so the ``isinstance`` narrows the value that is passed and
    # not a second ``get`` of the same key: two reads of one mapping are two values as
    # far as a type checker is concerned, and the second was typed ``Any | dict | None``
    # where this takes a ``Mapping``.  Same answer, one reading.
    declared = declaration.get("properties")
    return lower(
        compiler.declaration_rule_sources(declaration, position),
        declared if isinstance(declared, dict) else {},
        ("additionalProperties" in declaration) if extra_stated is None else extra_stated,
        resolve=resolve,
        root=root,
    )


# --------------------------------------------------------------------------- #
# §2's OTHER place a rule hangs: the value's own annotated type
# --------------------------------------------------------------------------- #
def on_a_value(
    sources: Mapping[str, Any],
    *,
    distinct: bool = False,
    contains: Any = None,
) -> tuple[ValueRule, ...]:
    """Every rule bound to a node's own TYPE, where no class above it can hold one.

    §2's "Where a rule hangs" has two halves and this is the second: "on the nearest
    class if there is one, because a class can read sibling fields.  Where no class sits
    above the value -- a root array, a mapping value, a ``definitions`` entry, a union
    branch -- the rule hangs off the value's own annotated type as an after-validator
    (``AtLeastOne``, ``NotValue``, ``Distinct``)."  :func:`lower` is the first half; this
    is the second, in the same module, so one reader decides which of the two a
    document's statement reaches and the two cannot both claim it.

    **WHICH half a keyword takes is the CELL's answer and not this function's**, which
    is why the three arguments are what they are and why the POSITION gate is the
    caller's:

    * ``uniqueItems`` -- "A ``UniqueItems`` rule on the class holding the array ... Where
      no class sits above the array → a ``Distinct`` after-validator on its own annotated
      type."  So ``distinct`` is passed only by a caller at such a position, and
      ``lower.containers.array`` is the one that knows which those are: a PROP array has
      the class whose field holds it and a ROOT array is a root model, which carries a
      rule tuple exactly as a class does.
    * ``contains`` -- "A field position → an ``AtLeastOne`` after-validator on the
      array's own annotated type."  There is no class-level kind for it at all, so it
      takes this half at EVERY position and the caller gates nothing.
    * ``not`` over a ``const`` or an ``enum`` -- "→ a ``NotValue`` after-validator on the
      value's own annotated type."  Also ungated, and for the same reason:
      :class:`ForbiddenGroups` is the class-level kind for the keyword's OTHER shape, a
      ``not`` over ``required``, and a statement about a VALUE has nowhere on a class to
      live.

    The order is fixed here -- distinct, contains, not -- rather than read off a mapping,
    so the rendered annotation is a function of the document's CONTENT and not of the key
    order a schema author happened to write (P7).  The three keywords are distinct, so
    there is no document order between them to preserve.

    Returns an empty tuple where the node states none of them, which is every node of the
    bundle but a few: a caller writes the tuple onto the type and an empty one renders
    nothing.
    """
    out: list[ValueRule] = []
    if distinct:
        out.append(Distinct())
    predicate = contains_predicate(contains)
    if predicate is not None:
        out.append(predicate)
    # Read ONCE into a local, so the ``isinstance`` narrows the value that is passed and
    # not a second ``get`` of the same key -- :func:`lower_declaration`'s own reason.
    negated = sources.get("not")
    excluded = _values(negated) if isinstance(negated, dict) else None
    if excluded:
        out.append(NotValue(excluded))
    return tuple(out)


@dataclass(frozen=True)
class AsTheObject:
    """§2's clause of 2026-10-28, asked of one node's CLASS-half rules: the ones its own
    annotated type can carry, and the ones it cannot.

    Two tuples and not one, because the second is what keeps the first from being a
    silent drop: a caller with no class writes ``carried`` onto the type and REFUSES for
    ``declined``, naming the kind.  §2 admits nothing by silence.
    """

    #: The rules that ARE callables on the value, in the order they were lowered -- so
    #: the annotation stays a function of the document's content and not of a set's
    #: iteration (P7).
    carried: tuple[ValueRule, ...] = ()
    #: The rules that are not, which have nowhere to live at a position with no class.
    declined: tuple[Rule, ...] = ()


def as_the_object(rules: Sequence[Rule]) -> AsTheObject:
    """§2's clause of 2026-10-28: which of a node's class-half rules its own VALUE carries.

    "**A value-level rule may state which KEYS the value supplied, and the three kinds
    above are not the limit.**  The distinction §2 draws is about where a rule HANGS, not
    about what it may read ... at a position with no class above it, the value *is* the
    object, so ``ForbiddenGroups``, ``RequiredGroups`` and ``PresenceGroups`` are
    admissible there as ``_runtime.ValueRule``s -- 'a callable on the value, and all it
    is' -- without a new kind."

    **This is §2's two places read a THIRD time and still by one reader.**  :func:`lower`
    is the class half and :func:`on_a_value` is the value half, and those two stay
    disjoint per keyword SHAPE: a ``not`` over a ``const`` is a statement about a value
    and a ``not`` over ``required`` is a statement about keys, and the reductions split
    them.  What this adds is the other axis -- a statement about KEYS at a position with
    no class -- and it re-reads no keyword to answer it: the rules are already lowered,
    and the question asked of each is whether the KIND is a value rule.

    **``isinstance(rule, ValueRule)`` and never a list of kind names**, which is the
    whole reason :class:`adcp.types._runtime.ValueRule` is ``runtime_checkable``: §2's
    clause says the admissible kinds are the ones that are "a callable on the value, and
    all it is", so admissibility is a property of the kind and a list here would be a
    second copy of the clause -- the one thing ``docs/plan/architecture.md`` §3 forbids.
    A kind that is not one (``Dependencies``, ``PropertyCount``,
    ``ConditionalRequired``, ``NegatedConditional``, ``UniqueItems``) reaches
    :attr:`AsTheObject.declined`, and the caller reports it.

    ``UniqueItems`` is the instructive decline: it names a SIBLING FIELD's array, so it
    reads the value's members through a name the value supplied rather than the value
    itself, and §2 already gives it the other kind at the other position
    (:class:`adcp.types._runtime.Distinct`).  A caller reaching it here has a
    ``uniqueItems`` with no class above it AND no array row to write the ``Distinct``,
    which is a shape no row writes.

    Measured over the 1,054 portable documents at ``adcp-client-python-10l.63``: the one
    caller is ``intersect._the_conjuncts_own_type``, 2 sites, both a ``ForbiddenGroups``
    from ``not``/``required`` -- ``core/canonical-product.json`` and
    ``core/product.json`` -- and ``declined`` is empty at every one of them.
    """
    carried: list[ValueRule] = []
    declined: list[Rule] = []
    for rule in rules:
        if isinstance(rule, ValueRule):
            carried.append(rule)
            continue
        declined.append(rule)
    return AsTheObject(tuple(carried), tuple(declined))


def contains_predicate(sub: Any) -> AtLeastOne | None:
    """§5's ``contains`` row as a PREDICATE, or ``None`` where it decides none.

    "The model states the **predicate**, not a transcription of the subschema.  Every
    position → an ``AtLeastOne`` after-validator on the array's own annotated type ...
    ``AtLeastOne(pinned=…)`` where the subschema requires properties pinned to a const,
    ``AtLeastOne(values=…)`` where it is a bare ``const`` or a one-member ``enum``.  Any
    other predicate -- a bound, a pattern, a nested ``contains``, a ``$ref`` -- → the
    keyword is CARRIED and the schema half answers alone: a transcription of the
    subschema is the thing this row declines to emit, and the first document to state
    such a predicate decides its rendering."

    ``None`` is that last clause, and the caller is what does something with it: the
    array row CARRIES such a ``contains`` exactly as it did before this function existed,
    which is D4 -- ``strict_validate`` enforces the keyword from the document and the
    constructor is wider.  **The distinction §5(b) draws is here and nowhere else**: a
    rule having nowhere to LIVE was never true, and a predicate having no decided
    RENDERING is.

    **Both readings are the ones this module already makes**, which is §11's "nothing
    repeats": a bare value is :func:`_values`, the same function an ``if`` clause reads a
    pinned property with, and the object predicate is :func:`_clauses`, the same function
    an ``if`` itself is read with -- a ``contains`` that requires properties pinned to a
    const IS an ``if``'s shape, asked about an element instead of about the instance.  A
    clause admitting more than one value is not a pin and the predicate is not decided,
    which is why every clause is checked for exactly one.
    """
    if not isinstance(sub, dict):
        return None
    bare = _values(sub)
    if bare is not None:
        return AtLeastOne(values=bare) if len(bare) == 1 else None
    clauses = _clauses(sub)
    if clauses is None:
        return None
    pinned: list[tuple[str, Any]] = []
    for clause in clauses:
        pin = _a_pinned_value(clause)
        if pin is None:
            return None
        pinned.append(pin)
    return AtLeastOne(pinned=tuple(pinned))


def _a_pinned_value(clause: Clause) -> tuple[str, Any] | None:
    """The ``(key, value)`` pair this clause pins, or ``None`` where it pins none.

    ``AtLeastOne(pinned=…)`` is a list of such pairs and says nothing else, so every part
    of the clause past those two has to be the part a pin would carry anyway: the key
    PRESENT, exactly one admitted value, and nothing forbidden.

    **The last two states are §8 sentence 3b's and are checked rather than assumed.**
    :func:`_clauses` can now return a clause whose presence is IMMATERIAL and whose value
    set is a COMPLEMENT -- *k is not v* -- and neither is a pin: an element satisfying
    *k is not v* has no pinned value to record, and recording ``v`` would invert the
    predicate and refuse every array the document admits.  A clause list this declines is
    the row's own "any other predicate", where the keyword is CARRIED and the schema half
    answers alone.

    **It returns the PAIR rather than answering yes or no**, so the value is read where it
    has been narrowed: a predicate returning ``bool`` leaves ``allowed`` an
    ``Optional[tuple]`` at the caller, and the checker is right to refuse the subscript
    the caller then writes.
    """
    key, present, allowed, forbidden = clause
    if present is not True or forbidden is not None:
        return None
    if allowed is None or len(allowed) != 1:
        return None
    return key, allowed[0]


def contains_source(declaration: Mapping[str, Any]) -> Any:
    """The ``contains`` a DECLARATION states, which is a rule source and so read HERE.

    **One line, and it is a module boundary rather than a convenience**
    (``adcp-client-python-10l.109``).  §4 keeps a node at RULE as a rule SOURCE on the
    enclosing node and "names this module its only reader", and ``tests/test_import_rule.py``'s
    ``MAY_READ_A_DECLARATION`` is that rule asserted: ``lower/containers.py`` read
    ``raw.get("contains")`` off an ``allOf`` conjunct's own declaration, and the set --
    which "may SHRINK and may not grow" -- reported it.  The keyword is a rule source at
    every position §5 gives it ("it takes this half at EVERY position and the caller gates
    nothing", :func:`on_a_value`), so the reader is this module and the gate is nobody's.

    **It is not in ``compiler.rule_sources(CONJ)``, and that is why a caller needed it.**
    The table lists ``contains`` as a rule source at RULE alone, so
    ``compiler.declaration_rule_sources`` filters it out of a conjunct's sources and a
    caller that wants §5's ``contains`` row at a conjunct has to ask for it separately.
    This is that ask, in the module the ask belongs to; whether the cell should list it at
    CONJ as well is §3's question and not this function's.
    """
    return declaration.get("contains")


# --------------------------------------------------------------------------- #
# the step-5 boundary, which is also the selector's per-node test
# --------------------------------------------------------------------------- #
def presence_only(node: Mapping[str, Any]) -> bool:
    """Is every combinator at ``node`` a statement about key PRESENCE?

    The one question that decides between step 5's row and this one, asked per node
    because a document can carry a combinator anywhere.  A ``oneOf``/``anyOf`` whose
    every branch states only which keys are present is a rule; a ``oneOf``/``anyOf`` of
    shapes is a union root.  Both predicates are read off the same branches, so no
    document satisfies both and the unordered table has nothing to arbitrate.

    **The reading is ``schema.parse``'s and this is the name the rows call it by.**
    §11's "nothing repeats" names ``parse``'s classification as the one owner of the
    kind -- "a combinator whose every branch is ``required``-only is not a ``Union`` but
    a rule source of the enclosing object (the ``presence_only`` reading, read once
    here)" -- and this module restated it until the branch shape grew a ``not``, at
    which point two readings of one §5 sentence would have had to grow it twice.  So
    there is one, and the walk's classification and the row's selector cannot disagree.

    Position RULE, which is what this module has always asked at: every node it reads is
    inside a conditional or a ``not``, and a key that annotates without constraining is
    not part of what a rule TESTS.

    ``if``/``then``/``else``, ``not``, ``dependencies``, ``min``/``maxProperties`` and
    ``uniqueItems`` are not asked about: no other D2 row claims a document for one of
    them, so there is no boundary to police, and D4 is what makes an unreadable one
    safe to carry rather than refuse.
    """
    return schema.presence_only(node, Position.RULE)


# --------------------------------------------------------------------------- #
# one reduction per keyword family
# --------------------------------------------------------------------------- #
def _depends(node: Mapping[str, Any], out: Lowered) -> None:
    """draft-07 ``dependencies``, the list-of-names form.

    Sorted by trigger: the keyword's value is a JSON object, so document order is dict
    order, and P7 wants the emitted tuple to be a function of the document's CONTENT.
    """
    dependencies = node.get("dependencies")
    if not isinstance(dependencies, dict):
        return
    for trigger in sorted(dependencies):
        requires = dependencies[trigger]
        if not isinstance(requires, list) or not all(isinstance(r, str) for r in requires):
            continue  # the schema-valued form: a conditional, and the schema's own
        names = tuple(r for r in requires if r != trigger)
        if names:
            out.rules.append(Dependencies(trigger, names))


def _count(node: Mapping[str, Any], out: Lowered, extra_stated: bool) -> None:
    """``minProperties`` / ``maxProperties``, counted over the keys that arrived.

    **The MINIMUM is written only where the class KEEPS every key the document would
    count**, and that is a correctness gate rather than a refinement.  D8 maps a
    silent ``additionalProperties`` to ``extra="ignore"``, so a key the document
    counts and the model drops is not counted by the rule -- and a ``minProperties``
    rule then REFUSES AN INSTANCE THE DOCUMENT ACCEPTS, which is a model narrower
    than its schema and the one direction D4 does not permit.  Measured, on the pair
    that found it: ``core/provenance.json``'s ``render_guidance`` states
    ``minProperties: 1`` and declares four properties, the document accepts
    ``{"": null}``, and the class dropped the undeclared key and refused on
    ``minProperties``.  So the minimum rides only where ``additionalProperties`` is
    STATED -- ``false`` gives ``forbid`` and every counted key is a declared field,
    ``true`` or a typed one gives ``allow`` and ``supplied`` reads the extras too.

    The MAXIMUM needs no gate, in either direction: a dropped key can only make the
    model's count LOWER than the document's, so the rule can under-refuse and never
    over-refuse.  Under-refusing is what D4 already says the constructor may do.

    **AND BOTH SIDES OF THAT PARAGRAPH ARE A WIDENING, so both are DECLARED**
    (``adcp-client-python-6oe``).  §5's gate decides what to RENDER and reading 2 decides
    what to SAY: a minimum the gate withholds is a fact the class does not state, and a
    maximum counting only the keys the class KEPT is a fact the class states over a
    smaller key set than the document counts over.  The cell proof at ``maxProperties``
    CONJ is the payload -- ``{"a": 1, "b": 2}`` against ``{"maxProperties": 1}``, which
    the document refuses and a class with ``extra="ignore"`` builds -- so neither half
    passes by being named in a docstring.  Where ``extra_stated`` holds, the class keeps
    every key the document counts (``allow``) or admits only declared fields
    (``forbid``), the two counts agree, and nothing is dropped in either direction.
    """
    lo, hi = (_whole(node.get(k)) for k in ("minProperties", "maxProperties"))
    if not extra_stated:
        # The class drops keys the document COUNTS, so neither bound is the document's
        # bound.  The minimum is withheld -- §5's gate, and §2 forbids the narrowing it
        # would otherwise be -- and the maximum rides on the smaller count, which
        # under-refuses.  Both are declared at the node's own pointer.
        if lo is not None:
            # **NOT DECLARED, AND NOW ALSO ALL BUT UNREACHABLE** --
            # ``adcp-client-python-gbo``, whose own figure is what kept it reachable.
            #
            # **THE FIGURE THAT STOOD HERE WAS WRONG BY THREE ORDERS OF MAGNITUDE AND IT
            # WAS THE WHOLE ARGUMENT.**  It read "the gate withholds the minimum at
            # **5,220 pointers in 209 documents**, because the record inlines one shared
            # node at every referring path", and concluded that §8 forbids a declaration
            # set of that shape and that the faithful fix -- the class KEEPING the keys the
            # document counts -- was a sentence only the design documents could move.  The
            # count was over the INLINED record and **the walk does not inline**: it
            # compiles each shared node once and imports the symbol.  Re-measured over the
            # same 1,054 portable documents by recording every call at which this gate
            # fires: **5 calls at 4 distinct (document, pointer)**, zero declarations on
            # either count keyword, and the minimum arm reaches three of the five.  Five is
            # well inside the regime ``tests/test_the_declared_backlog.py`` already pins,
            # so the cardinality objection does not survive its own denominator.
            #
            # **AND THE DESIGN DOCUMENTS DID MOVE IT**: §8 sentence 4's second consequence
            # (2026-11-03) decides that such a count "is answered by the class KEEPING the
            # keys the document counts.  Declaring it would be declaring a difference the
            # walk created."  ``lower.objects.declare_object`` takes that reversal at exactly
            # the nodes a count rides over, so ``extra_stated`` is now true wherever a
            # class carries one and this arm is reached by no class of this bundle.
            #
            # It is KEPT rather than deleted because the reversal is the caller's and this
            # is the reduction: a node reaching ``lower`` from a path that does not resolve
            # an extra policy still must not write a minimum over a smaller key set, which
            # would be a rule refusing what the document accepts and the narrowing §2
            # forbids outright.  Withheld and not declared, for the reason the sentence
            # gives: the difference would be the walk's own and not the document's.
            lo = None
        if hi is not None:
            out.dropped.append(("maxProperties", node["maxProperties"]))
    if lo is None and hi is None:
        return
    out.rules.append(PropertyCount(minimum=lo, maximum=hi))


def _negated(
    node: Mapping[str, Any],
    out: Lowered,
    declared: Mapping[str, Any] = {},  # read-only, and the empty mapping is the answer
) -> None:
    """Every group of key names this node forbids, from the keyword and from a property.

    **Two spellings of one fact, and ONE rule.**  ``not: {"required": [k]}`` is §5's
    ``not`` row, and a ``properties`` entry that admits nothing has exactly that accepted
    set -- draft-07 reaches such an entry only where the key is present, and then always
    refuses -- so §5's ``properties`` row sends it here rather than to a field.  They are
    merged into one :class:`adcp.types._runtime.ForbiddenGroups` and not appended as two,
    because a class body binds ``_adcp_rules`` once and two rules naming the same key
    would state one fact twice.

    **The bundle states both spellings AT ONE NODE, twice**, which is the measurement
    that makes the merge worth having rather than a tidiness: ``core/account.json`` at
    ``/`` and ``account/sync-accounts-response.json`` at
    ``/oneOf/0/properties/accounts/items`` each say
    ``not: {"required": ["destination_billing_entity"]}`` beside
    ``properties: {"destination_billing_entity": {"not": {}}}``.  Deduplicated, so those
    two documents' rule tuples do not move: the group is already there by the keyword,
    and the property adds nothing to it.  That is also why reading only the one site this
    row was filed for would have been wrong -- those two were green by the sibling
    keyword and the third had nothing to save it.

    The keyword's groups come first and the properties' follow in document order (P7):
    the emitted tuple is then a function of the document's content and not of which
    reduction ran.
    """
    groups = list(_required_groups(node.get("not")) or ())
    for key in schema.forbidden_keys(declared):
        if (key,) not in groups:
            groups.append((key,))
    if not groups:
        return
    out.rules.append(ForbiddenGroups(tuple(groups)))


def _combinator(node: Mapping[str, Any], out: Lowered) -> None:
    """``oneOf`` / ``anyOf`` whose branches state only which keys are present.

    Only that form, which is :func:`presence_only`'s test and the step-5 boundary.  A
    combinator of shapes is a union root and this writes nothing for it -- the document
    is step 5's and the selector does not claim it.

    **Two kinds and ONE reading of the branches**, which is §5's "A union of
    presence-only branches that also forbid" (decided 2026-10-27).  A branch is
    ``schema.presence_clause``'s pair -- the names it requires and the groups its ``not``
    forbids -- and the kind written is decided by whether any branch forbids anything:

    * no branch forbids → :class:`RequiredGroups`, which is the pair's degenerate case
      and the kind the bundle's existing rule tuples already carry, so they do not move;
    * some branch forbids → :class:`PresenceGroups`, whose clauses ARE the branches with
      both halves paired.

    Hoisting the ``not``\\ s into a :class:`ForbiddenGroups` beside a
    :class:`RequiredGroups` is the move this kind exists to refuse, and
    ``core/catchment.json`` is the measurement: each of its three branches forbids the
    other two methods, so the hoisted rule forbids all three and refuses every payload
    the document admits.  ``tests/test_emit.py``'s
    ``test_a_presence_clause_keeps_its_two_halves_paired_to_its_own_branch`` grades the
    document's verdict, the rule's and the perturbation, so a later row that collapses
    the pairing back into two rules reddens.
    """
    for keyword in _COMBINATORS:
        branches = node.get(keyword)
        if not isinstance(branches, list) or not branches:
            continue
        read = [schema.presence_clause(b, Position.RULE) for b in branches]
        clauses = tuple(Presence(*pair) for pair in read if pair is not None)
        if len(clauses) != len(read):
            continue
        if not any(c.require or c.forbid for c in clauses):
            continue
        # **:class:`RequiredGroups` is the degenerate case and the test for it is
        # DERIVED, not the forbid half alone** (§5's disjunctive required half, decided
        # 2026-10-29).  That kind holds a flat group list and counts the groups PRESENT;
        # a clause list holds the branches and counts the CLAUSES that hold.  The two say
        # the same thing exactly when every clause is one group: then "group i present"
        # and "clause i holds" are the same statement, and flattening is a spelling.
        # They come apart the moment a clause carries two groups -- under ``oneOf`` an
        # instance satisfying both of one clause's groups is ONE clause and TWO groups,
        # so the flat kind would report "2 of these groups are present, the document
        # admits exactly one" of a payload the document admits.  So a clause that is not
        # exactly one group takes the kind that can hold it, which is the same reason
        # ``core/catchment.json`` gives for not hoisting the ``not``\\ s.
        #
        # ``!= 1`` and not ``> 1``: a clause carrying NO group is a branch that only
        # forbids, which has no group to contribute to a flat list at all and whose whole
        # content would vanish from it.
        if any(c.forbid for c in clauses) or any(len(c.require) != 1 for c in clauses):
            out.rules.append(PresenceGroups(clauses, keyword))
            continue
        out.rules.append(RequiredGroups(tuple(c.require[0] for c in clauses), keyword))


def _distinct(
    declared: Mapping[str, Any], out: Lowered, resolve: intersect.Resolver = None
) -> None:
    """``uniqueItems: true`` on an array this node holds as a property.

    The one keyword here that is read one level down, because D2 puts the rule on the
    NEAREST CLASS and the keyword's node -- an array -- is never a class.  Document
    order, so the emitted tuple is a function of the document's content (P7).

    Gated on the declaration DECLARING AN ARRAY and on the value being exactly ``true``:
    draft-07 applies ``uniqueItems`` to an array and ignores it for every other instance,
    so a ``uniqueItems`` on a string property says nothing and must not become a rule,
    and ``uniqueItems: false`` is the keyword's own default and states nothing either.  A
    node this declines leaves the keyword on the declaration, where the array row
    refuses it by name.

    **The gate is ``intersect.declares_an_array`` and not this declaration's own ``type``
    word, because §2's clause of 2026-10-29 says a COMPOSING declaration is still a
    property of the class that holds it**: "A property whose declaration is an ``allOf``
    still sits in the class that holds the property ... the reader that writes it must
    see through the composition rather than the rule move to the value's own type."  So
    the array-ness may be stated behind a ``$ref`` under an ``allOf`` and this still
    claims the key -- the class holds the field either way.  Read through ``compiler``
    rather than here because ``lower_composition``'s own ``uniqueItems`` arm asks the
    same question of the same declaration, and a gate that claimed where that arm
    refused is the hole this closes.
    """
    claimed = [
        key
        for key, declaration in declared.items()
        if isinstance(declaration, dict)
        and intersect.declares_an_array(declaration, resolve)
        and declaration.get("uniqueItems") is True
    ]
    if not claimed:
        return
    out.distinct = tuple(claimed)
    out.rules.extend(UniqueItems(key) for key in claimed)


def _conditional(
    node: Mapping[str, Any], out: Lowered, root: Mapping[str, Any] | None = None
) -> None:
    """``if``/``then``/``else``, and every arm of it the class does not carry.

    §5's ``if`` row is "a ``Match`` clause list where it states ``required`` plus
    ``properties`` with ``const`` or ``enum`` values; otherwise nothing, and the schema
    half answers", and its ``then``/``else`` row is "``ConditionalRequired`` /
    ``NegatedConditional`` from its ``required`` and a single-name ``not``.  Its
    ``properties`` -> nothing on the model".  Both "nothing"s are a class that BUILDS a
    payload the document refuses, so both are declared (:attr:`Lowered.dropped`) --
    ``adcp-client-python-3bb``, whose payload is
    ``core/reporting-schedule-offering.json#/allOf/0/else`` reduced to two keywords: an
    ``if`` nested inside an ``else``, where the outer condition does not match, the inner
    one does, and the document requires a key the class does not.

    **A bare ``if`` is declared NOTHING, and a bare ``then``/``else`` is too**, because
    draft-07 says so: ``if`` with no arm constrains no instance, and ``then``/``else``
    with no ``if`` is ignored.  A declaration there would name a fact the document does
    not state, which is §9's "never approximate on a keyword the walk itself inserted"
    read from the other end -- ``harness.check_widening`` would walk the pointer, find
    the keyword stating nothing, and have nothing to draw against.

    Nine live cells fail on the two arms here, eight of them because the CONDITION is
    unreadable and three (``if``, ``then``, ``else`` at RULE) because a CONSEQUENT is a
    conditional of its own; the keyword each declaration names is the one the document
    writes at this pointer and not the keyword the cell is about, because the fact
    dropped belongs to the conditional.
    """
    arms = tuple(k for k in ("then", "else") if k in node and _states_presence(node[k]))
    when = _clauses(node.get("if"), root)
    if when is None:
        # **A CONDITION the reduction cannot read IS DECLARED, and §8 sentence 2 is what
        # made it affordable.**  §5's ``if`` row decides the lowering -- "a ``Match``
        # clause list where it states ``required`` plus ``properties`` with ``const`` or
        # ``enum`` values; otherwise nothing" -- and a condition with no ``required`` at
        # all cannot yield a clause: a clause tests a key that is PRESENT, so a condition
        # reduced from such a node would fire on instances the document's condition does
        # not match and the rule would refuse what the document admits, which §2 forbids
        # outright.  The complement (§8 sentence 3b) does not reach it either, for the
        # same reason: there is no key whose predicate the complement is of.
        #
        # So the model is wider here and §2 asks for a declaration.  **What stood in the
        # way was arithmetic, and it was the arithmetic §8 sentence 2 retires**
        # (``adcp-client-python-3bb``, second population): declaring it minted **4,635
        # sites in 97 documents from 112 distinct conditional facts**, because a
        # declaration was written once per pointer the record inlines the condition to --
        # 3,641 of them ONE logo-slot ``if`` under ``core/async-response-data.json`` and
        # its webhook twin.  §8 ruled that set out by name ("an approximation nothing can
        # demonstrate does not belong in the set") and the ratio 4,635 : 112 is the
        # measurement of the defect rather than of this drop.  Under §8 sentence 2 a fact
        # is declared ONCE, at the node the document states it, so what this mints is the
        # distinct conditional facts and nothing per referring path.
        #
        # **The KEYWORD is ``if`` and the FACT is the condition the document writes**, not
        # the keyword the cell is about: the fact dropped belongs to the conditional, and
        # §9 requires the declared fact to be the document's own.  Declared only where an
        # arm STATES PRESENCE, by the paragraph above -- an ``if`` whose arms say nothing
        # about which keys are present constrains nothing a rule could have carried, so
        # there is no difference for a declaration to describe.
        if arms and isinstance(node.get("if"), Mapping):
            out.dropped.append(("if", node["if"]))
        return
    clauses = tuple(Match(*clause) for clause in when)
    for keyword, kind in (("then", ConditionalRequired), ("else", NegatedConditional)):
        branch = _branch(node.get(keyword))
        if branch is None or not any(branch):
            if keyword in arms:
                out.dropped.append((keyword, node[keyword]))
            continue
        require, forbid = branch
        out.rules.append(kind(clauses, require=require, forbid=forbid))


def _states_presence(sub: Any, depth: int = 0) -> bool:
    """Does this ``then``/``else`` say anything about which KEYS are present?

    **The one question that tells a DROPPED RULE from a decided NOTHING**, and it is §2's
    own axis rather than a filter invented here: "a rule is NOT what makes the model as
    narrow as its document; it is what makes the ``model_validate`` CONSTRUCTOR as narrow,
    **on the subset of statements that are about key presence**" (this module's docstring).
    So a consequent stating ``required``, or a ``not`` over ``required``, states a fact one
    of the rule kinds CAN carry, and a class that carries none of it has dropped a rule --
    which reading 2 makes a declaration.  A consequent stating only ``properties`` narrows
    a VALUE, which §5 decides compiles to nothing ("its ``properties`` -> nothing on the
    model; the schema half narrows the value") and whose ceiling this module's docstring
    NAMES with its measurement (``core/canvas-constraint.json``) -- there is no rule kind
    for it at any position, so nothing was dropped that a declaration could describe.

    **Measured, and the measurement is why the distinction is drawn rather than declaring
    both**: over the 1,054 portable documents, declaring every unread consequent mints
    **40,275 ``then`` sites** against **1,069** that state a presence fact, because the
    record inlines a shared conditional at every referring path.  §8 is explicit that such
    a set is not a declaration set -- "an approximation nothing can demonstrate does not
    belong in the set" -- and a value a conditional narrows has no payload at the
    constructor to demonstrate it with, because D4 gives that decision to the schema half.

    RECURSIVE, because the shape ``adcp-client-python-3bb`` names is a conditional nested
    inside an arm: ``core/reporting-schedule-offering.json#/allOf/0/else`` holds an
    ``if``/``then`` whose inner ``then`` requires a key, and a reading that looked only at
    the arm's own ``required`` would report that fact as decided-nothing.  ``depth`` bounds
    it for §9's reason -- a fold with no base case is a crash, and a crash is not an
    outcome.
    """
    if not isinstance(sub, dict) or depth > _NESTED_DEPTH:
        return False
    if any(isinstance(name, str) for name in (sub.get("required") or [])):
        return True
    if _required_groups(sub.get("not")):
        return True
    return any(_states_presence(sub.get(arm), depth + 1) for arm in ("then", "else"))


#: How deep a conditional may nest inside another's arm before :func:`_states_presence`
#: stops looking.  The bundle's deepest is ONE (``core/reporting-schedule-offering.json``
#: at ``#/allOf/0/else``); the bound is here so the fold terminates on a document that
#: nests further, which §9 requires of every fold in this compiler.
_NESTED_DEPTH = 8


def _whole(value: Any) -> int | None:
    """``value`` if it is a JSON integer, which ``True`` is not."""
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _keys(sub: dict) -> set[str]:
    """The keys of ``sub`` that SAY something about an instance.

    ``intersect.declaring`` at RULE, because every node this module reads is inside a
    conditional or a ``not``: a key that annotates without constraining is not part of
    what a rule TESTS.
    """
    return set(intersect.declaring(sub, Position.RULE))


def _required_groups(sub: Any) -> list[tuple[str, ...]] | None:
    """``sub`` as a set of key groups, at RULE: ``schema.parse.required_groups``.

    The reduction is the PARSER's -- :func:`codegen.schema.parse.presence_clause` reads
    the same ``not`` to classify a branch, and §11's "nothing repeats" makes one keyword
    one reduction.  This is the name the three readers in this module call it by, and
    the position they ask at.

    ``partial=True``, which is ``adcp-client-python-10l.27``'s settled fix: both callers
    here read a ``not``, where every group dropped forbids LESS, so a disjunct the
    reduction cannot read contributes none and the ones it can read still contribute
    theirs.  All-or-nothing dropped the whole ``not`` and
    ``media-buy/sync-audiences-response.json``'s branches then carried no
    ``ForbiddenGroups``, so §4's second separator could not see a union the document
    separates.
    """
    return schema.required_groups(sub, Position.RULE, partial=True)


def through_the_storage(node: Any, root: Mapping[str, Any] | None) -> Any:
    """``node`` with a reference the RECORD MINTED followed, or ``node`` as written.

    **§8's sentence 3a (decided 2026-11-03), and it needs no new principle.**  The record
    stores each distinct subtree once under its own ``definitions`` and references it at
    every occurrence (reading 5), so the node a reader is handed at a position may be a
    reference to a storage entry rather than the content the document states there.
    ``architecture.md`` already settled what such a reader does: *a reader asking what the
    document states reads through the storage*, because "a reference to a storage entry is
    not a fact the document states but where the fact is kept".

    :func:`adcp.types._base.through_the_store` is that one hop and this is the name this
    module calls it by.  Two things follow from using it rather than a local-pointer
    resolver of this module's own, and both are the reason:

    * it follows ONLY a node whose single key is a ``$ref`` naming a ``Shared<N>`` entry,
      which is the only shape the hoisting writes.  **A document's OWN local reference is
      left exactly as written** -- ``bundle.record`` leaves one in, 1,158 of them carry a
      ``description`` beside the ``$ref``, and following those would change what every
      other reader of the same node sees for a storage decision that touches none;
    * it is the package's own declaration of the seam, so the walk and
      ``strict_validate`` dereference the record through one predicate rather than two.

    ``root`` is ``None`` for a caller with no record in hand -- a document lowered outside
    a run, a conjunct read with no module -- and the answer is then ``node`` itself, which
    is the arm that DECLARES rather than lowering a node it cannot see.
    """
    if root is None:
        return node
    return _base.through_the_store(node, root)


def _complement(
    inner: Any, root: Mapping[str, Any] | None = None
) -> list[Clause] | None:
    """A NEGATED condition as one complemented clause, or ``None``.

    **§8's sentence 3b (decided 2026-11-03), and it replaces a sentence that said such
    conditions DECLARE.**  The condition this bundle writes most often is

        not: {required: [k], properties: {k: {const: v}}}

    the inner schema being *"k is present AND equals v"*.  By De Morgan its negation is
    *"k is absent OR k differs from v"*, which was read as a disjunction no clause list
    can state, since a rule's ``when`` is a conjunction.  **The error was in where the
    disjunction sits:** it is not a disjunction of independent facts about different keys,
    it is ONE predicate about ONE key -- *k is not v, whether by absence or by value* --
    and :class:`adcp.types._runtime.Match` now says it, because its presence is
    three-state and its value set has a complement.

    So the inner condition is read by the SAME reduction that reads a positive one, and
    the complement is taken on its result.  Two cases and both are exact:

    * one clause carrying a value set → the key, presence IMMATERIAL, that set
      FORBIDDEN.  Absent satisfies, present-and-different satisfies,
      present-and-equal does not;
    * one clause with no value set (a bare ``not: {required: [k]}``) → the key
      ABSENT, which is the two-state flag's own ``present=False`` and needs no
      complement at all.

    **MORE THAN ONE CLAUSE IS ``None``, and that is the rule rather than a budget.**
    §8: *"A condition whose negation genuinely spans two keys still declares ... The test
    is whether the disjunction is inside one key's predicate or across several."*
    ``not (a present and b present)`` is *a absent OR b absent* -- a disjunction ACROSS
    keys, which a conjunction of clauses cannot state and which a per-key complement
    would state as *a absent AND b absent*, a rule strictly stronger than its document
    and the one direction §2 forbids outright.

    An inner ``type: "object"`` is carried by the inner reduction and costs nothing here:
    the negation of *"an object AND k present"* includes *"not an object"*, and every
    instance a rule ever runs on is an instance of the class, which is one.
    """
    inner = through_the_storage(inner, root)
    read = _clauses(inner, root)
    if read is None or len(read) != 1:
        return None
    key, _, allowed, forbidden = read[0]
    if forbidden is not None:
        # The inner condition is itself complemented, so its negation is a POSITIVE value
        # set -- but only where the inner states nothing else about the key, and a clause
        # carrying both sets says more than one De Morgan step can undo.  Left to declare
        # rather than guessed at: no node of this bundle reaches it.
        return None
    if allowed is None:
        return [(key, False, None, None)]
    return [(key, None, None, allowed)]


def _clauses(
    sub: Any, root: Mapping[str, Any] | None = None
) -> list[Clause] | None:
    """An ``if`` as ``(key, present, allowed values, forbidden values)`` clauses, or ``None``.

    Every clause must be about a key the ``if`` also REQUIRES.  A ``properties`` entry
    for a key the ``if`` does not require is satisfied by the key being ABSENT as well
    as by its value matching, and a clause cannot say "absent or one of these" -- so
    such an ``if`` reduces to nothing rather than to something stronger than the
    document.

    **A condition that is exactly a ``not`` is read by :func:`_complement`** (§8's
    sentence 3b), which takes the negation of what this function reads of the inner
    schema.  ``_keys`` is the test and not a membership check on the raw node, so an
    annotation beside the ``not`` does not take the arm: a key that annotates without
    constraining is not part of what a rule TESTS, which is the position this module
    reads everything at.

    **The condition and each property declaration inside it are read THROUGH the record's
    own storage** (:func:`through_the_storage`, §8's sentence 3a).  Both hops are needed
    and the measurement is why: over the 1,054 portable documents 2,804 record pointers
    state an ``if`` this reduction cannot read as written, **2,188 of them because the
    condition or a property declaration inside it had been replaced by a reference to a
    storage entry, and 1,971 of those lower exactly once the reference is followed** --
    declaring nothing, because the clause list then states what the document states.
    """
    sub = through_the_storage(sub, root)
    if not isinstance(sub, dict):
        return None
    keys = _keys(sub)
    if keys == {"not"}:
        return _complement(sub["not"], root)
    if sub.get("type") not in (None, "object"):
        return None
    if not keys <= {"required", "properties", "type"} or not isinstance(sub.get("required"), list):
        return None
    required = [n for n in sub["required"] if isinstance(n, str)]
    properties = sub.get("properties") or {}
    if not isinstance(properties, dict) or not set(properties) <= set(required):
        return None
    out: list[Clause] = []
    for name in required:
        declaration = through_the_storage(properties.get(name), root)
        allowed = None
        if isinstance(declaration, dict):
            allowed = _values(declaration)
            if allowed is None:
                return None
        out.append((name, True, allowed, None))
    return out or None


def _values(sub: dict) -> tuple[Any, ...] | None:
    """The values a property declaration admits, as a tuple, or ``None``.

    ``()`` is not a possible answer and ``None`` means "more than a listed set", which
    is why this cannot return an empty tuple for an unreadable declaration.  A bare
    ``{"type": ...}`` admits every value of that type, so it is ``None`` too: a clause
    testing it would hold for exactly the values the document's ``if`` holds for, which
    is the same statement, but there is nothing to list.
    """
    keys = _keys(sub)
    if "const" in keys and keys <= {"const", "type"}:
        return (sub["const"],)
    if "enum" in keys and keys <= {"enum", "type"} and isinstance(sub["enum"], list):
        return tuple(sub["enum"]) or None
    return None


def _branch(sub: Any) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    """A ``then``/``else`` as ``(must be present, must be absent)``, or ``None``.

    A ``properties`` in the branch is ignored rather than refused: it narrows a VALUE,
    which is the schema's statement and not a rule's (see the module docstring).  A
    ``not`` is read only when it forbids ONE name -- ``not: {"required": [a, b]}`` forbids the
    PAIR, and a list of individually-absent keys would be stronger than the document.
    """
    if not isinstance(sub, dict):
        return None
    require = tuple(n for n in (sub.get("required") or []) if isinstance(n, str))
    forbid: tuple[str, ...] = ()
    groups = _required_groups(sub.get("not"))
    if groups and all(len(g) == 1 for g in groups):
        forbid = tuple(g[0] for g in groups)
    return require, forbid
