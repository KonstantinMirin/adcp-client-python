"""The decision machinery a lowering is handed: a node in, a declaration out.

``docs/plan/rebuild-plan.md`` §1 splits the pipeline at a DECISION rather than at a
translation.  Our walk reads the JSON Schema and decides what each node becomes -- a
class, an annotation, an enumeration or a rule -- what it is called, which fields it has
and what constrains them.  This module is the shared half of that walk, and what it
produces is ``codegen.ir``: **nothing here holds a string of Python**
(``docs/plan/architecture.md`` §7), and ``codegen.render`` is the one module that turns a
declaration into text.

**D13 puts the shared machinery here and not in ``codegen.emit``**, and the reason
WAS an import rule rather than a preference.  A lowering under ``codegen/lower/``
could name this module and ``codegen.refusal`` and nothing else of this package: it
could not name ``codegen.emit``, because ``emit`` held the dispatch table that
named it, and an import back the other way closed a cycle that ``python -m
codegen.emit`` resolved into TWO module objects rather than into an ``ImportError``
-- the failure D12 already exists to prevent for ``Refusal``, one layer in.  A
``TYPE_CHECKING`` import hid that cycle from the type checker without removing
it, because the lowering needs the machinery at RUN time.  So the machinery moved,
which is what makes the one-directional import true rather than intended.

**That prohibition is RETIRED and ``codegen/lower/__init__.py`` records why.**
``codegen/__main__.py`` removed the double binding, so there is one ``codegen.emit``
on every path and the rule has nothing left to prevent: ``codegen/lower/decide.py``
imports eight handler modules of its own package by name.  The reading that survives
is the one ``tests/test_import_rule.py`` still holds, and it is down to the two
boundaries §§8-10 decide on their own merits -- no Pydantic in the walk, no walk in
the verifier.

What is here, in D13's own terms: the carriers a lowering is handed (:class:`Module`,
:class:`Shape`, :class:`Target`), the per-node entry (:func:`lower_node`), the keyword
screen (:func:`check_keywords`), the rule reader (:func:`rules_at`), and
:func:`declare_alias` for a root D2 makes an alias.

**NO ROW IS HERE ANY MORE**, which is ``adcp-client-python-g4z``'s whole subject.  §5:
"a row's decision lives in that row's ``lower/<kind>.py``, whole", and "a collaborator
several rows share lives with its PRIMARY subject and is imported by the others".  So:

* §2's intersection over two declarations is ``codegen/intersect.py``'s;
* the field builder and the class declarer are ``codegen/lower/objects.py``'s, with the
  object row -- ``fields``, ``declare_object``, ``_a_property_count_rides``,
  ``lower_object``;
* §5's ``allOf`` row is ``codegen/lower/composition.py``'s, whole -- ``lower_composition``
  and the eighteen helpers whose only production caller it was.

**WHAT IS STILL HERE AND IS NOT THE CONTEXT**, listed because the row that would move it
has to name a home for each and §5 names one for none of them: the keyword SCREEN
(:func:`check_keywords`, :func:`check_declaration`, :func:`kind_for`, which take a NODE
and so cannot join ``codegen/keywords.py`` without reversing §11's arrow), the rule reader
(:func:`rules_at` with :class:`Rules` and :class:`Dropped`), the three declaration writers
for a root D2 gives no class (:func:`declare_alias`, :func:`bind_without_a_model`,
:func:`declare_root_model`), :func:`local_reference`, :func:`carried`,
:func:`declaration_rule_sources`, :func:`stated_extra`, :class:`UnionBase`, and the two
report writers.  Each has a candidate and none has a DECISION, so this file is not renamed
and ``adcp-client-python-g4z``'s fourth move is open with that list as its content.

**The SEAM'S OWN TYPE is not here, which is §14 step 10's first move**
(``adcp-client-python-3be.6``).  :class:`codegen.ir.Decided` is what every handler
returns, and it is declared in ``codegen/ir.py`` -- the layer §7 gives "what the walk
DECIDED, as values" and the one module of this package that imports no other.  The three
carriers above are the walk's own mutable state and a decision is not: keeping the seam's
type beside them put it behind an import of ``compiler``, which is why ``lower/names.py``
-- whose arrow here is ``TYPE_CHECKING``-only, D13's direction -- could not construct one.

**The per-node ENTRY is here and the per-node DISPATCH is not** (§5, and
``adcp-client-python-3be.5``).  :func:`lower_node` is what a handler calls for a child,
and the exhaustive ``match`` it routes through is ``codegen.lower.decide``'s -- reached
by a deferred import, because that module imports every handler and a handler imports
this one, so the module-level arrow would close a cycle while D13 fixes the direction.
What :func:`lower_node` adds to the route is the three statements about a NODE AT A
POINTER that apply to every arm equally, and its own docstring is where they are read.

**§12 would dissolve this module, and NO ROW OWNS THAT.**  It is not a step a lane is
behind on, and this docstring used to say it was.  Most of what §12 names has already
moved and each piece has a READING a test holds rather than a line count:
``codegen/schema/parse.py`` is the only entry that reads a raw mapping
(``tests/test_import_rule.py::test_the_parser_is_the_only_entry_that_reads_a_raw_mapping``),
``codegen/lower/decide.py`` is the exhaustive ``match`` over the node kinds, and
``codegen/lower/names.py`` is the naming pass -- :func:`class_name` and
:func:`field_name` here are re-bindings of that module's, kept so every existing reader
has one spelling.  What is left in this file is a residue, and it is INTERNAL: no
consumer of ``src/adcp`` can observe how many lines it has or which modules import it.
``docs/plan/unimplemented.md`` Part B is where that is recorded and why it gets no
verdict -- a maintainability preference, done when it pays for itself, and explicitly
not a gate.

**The two debts the old wording named are PAID, which is why naming them here was
misleading.**  ``Module.bind`` -- the last callable carried on the context -- is gone and
:attr:`Module.targets` is the dependency-ordered map that replaced it.  And
:func:`field_name` no longer reads what pydantic's ``BaseModel`` carries: ``render.py``
derives the set (``render.RESERVED``), the run hands it to the walk as DATA, and
``names.field_name`` takes it as an argument -- so ``tests/test_import_rule.py``'s
``MODEL_LAYER_EXCEPTIONS`` is empty, and it may shrink and not grow.

**It reached that dispatch THROUGH ``codegen.emit`` until this row, and that was the one
§11 boundary substantively violated**: a deferred ``from codegen.emit import
decide_type`` inside this function put the RUN inside the per-node loop of every
document, where §11's arrows run ``lower <- emit`` and give the run "order, closure,
files, the report" and no node at all.  No test held it, because the test §11 writes for
that boundary ranges over ``schema/`` and ``lower/`` and the import was in neither:
``tests/test_import_rule.py`` now closes the population's imports TRANSITIVELY, so the
next module placed between a handler and the run reddens without being named.

**This module is NOT dissolved, and the reading is which pieces are still in it.**
§14 steps 5 and 7 said it would be, in a sentence this docstring carried while nothing
moved; what has actually gone is the naming -- ``class_name`` and ``field_name`` are
``codegen/lower/names.py``'s, re-exported below where a caller still spells them here,
and ``alias_for`` and ``name_the_node`` are that module's outright, called by name from
the one site each that is left -- the node kinds and the parser (``codegen/schema/``),
the root selector table,
and :attr:`Module.bind` -- a closure over the run, replaced by the dependency-ordered
:attr:`Module.targets`.  What step 5 assigned to the HANDLERS has gone too, under
``adcp-client-python-g4z``, and the paragraph above lists what has not.
``adcp-client-python-3be.6`` carries the rest; the line count and the importer count of
this file are not goals in themselves, and ratcheting either would freeze the shape rather
than move it.

**§2's INTERSECTION RULE IS ``codegen/intersect.py``'s**, the first of
``adcp-client-python-g4z``'s moves.  §5 is the sentence: "a pure function over two
declarations lives in a module of its own, because purity is exactly the property that
makes it gradeable alone", and §6 already classified ``restatement``, ``intersection`` and
``at_least_as_tight`` that way.  What went with them is everything those three compare or
hand back -- ``declaring``, ``_constraining``, the tightness and container readings,
``_restatement``, ``_provably_empty``, ``_parsed_property``, and §5's ``$ref``-row-at-CONJ
applications ``_the_conjuncts_own_type`` and ``intersected_at_a_branch``.

**The ARROWS run one way now**, which is what the third move bought and is worth stating
because two commits of this row did not have it: this module imports ``ir``, ``keywords``,
``refusal``, ``lower/names.py`` and ``schema``, and nothing of ``intersect``,
``lower/objects.py`` or ``lower/composition.py``.  :data:`Resolver` is the one piece that
came BACK here for it -- the type of :meth:`Module.resolve_node`, which the pure rule takes
as an argument, so it belongs with the thing it describes and not with the rule.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any, NamedTuple

from adcp.types._base import Approximation, SchemaRef
from adcp.types._runtime import ForbiddenGroups, Rule
from codegen import ir, keywords, refusal
from codegen.keywords import Position
from codegen.lower import names
from codegen.refusal import BuildFailure, Kind, Refusal
from codegen.schema import nodes
from codegen.schema import parse as schema

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


def report_inert(inert: Collection[str], pointer: str, mod: Module) -> None:
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


def report_reported_drops(drops: Collection[tuple[str, str]], mod: Module) -> None:
    """The REPORTED half of a cell whose :attr:`keywords.Cell.reported` is set.

    ``docs/plan/rebuild-plan.md`` §7 on ``errorMessage``: "it customises a validator's
    message and constrains no instance, so an annotation that omits it omits no fact.
    **The drop is reported, as it was**" -- and the position rule beside it, "the drop is
    reported at every position the keyword occupies, and not only where a conjunct
    encloses it".

    **A function of the DOCUMENT and not of the walk**, which is what that rule costs and
    is why ``drops`` is handed in rather than collected here.  ``bundle.reported_drops``
    is the census, over the one descent walk; this is the SENTENCE, here because §11 gives
    the declaration layer positions, keywords, cells and descent and denies it text.  The
    channel this replaces was ``lower_composition``'s conjunct worklist, which reported
    the one occurrence a conjunct enclosed and could not reach the one at ``/then`` --
    "a report that reaches one position and not another is a defect in the channel, not a
    second decision".

    Reported rather than silent, and on the MODULE rather than raised: a drop is not a
    refusal (the document still emits) and it is not nothing (a reader has to be able to
    see that the class does not carry the name).  :attr:`Module.carries_nothing` is that
    channel and ``emit`` prints it.
    """
    mod.carries_nothing.extend(
        f"{pointer or '/'}: {key}: section 6 admits this keyword by name and it "
        "constrains no instance, so the class carries nothing for it (section 2, 'a "
        "keyword we cannot express': a name that cannot constrain an instance compiles "
        "to nothing)"
        for pointer, key in drops
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
    #: document admits, so the dump lost every one of them.
    #:
    #: So this is read where the document-side fold puts the fact -- what the document
    #: states at the class's own pointer, which for a composing class is its own
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
    the document-side fold**".  ``harness._composed`` gap-fills -- a keyword only a
    conjunct states fills a gap and never overrides the node's own -- so the fold answers
    with the FIRST view that states one, and a lattice answers with something no document
    states at that pointer.  Measured on
    ``media-buy/decline-proposals-response.json#/anyOf/1``: the root
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


class ValuesImport(NamedTuple):
    """Where §3a's module-level VALUE LIST is importable from, for the position that is
    about to build a type over it.

    It is NOT an :class:`Importable`, and the difference is the second field that one
    carries: a DOCUMENT.  §3a's catalogue module has none -- "**A pseudo-document path is
    refused**: it names a file the bundle does not contain" -- and nothing downstream
    wants one, because a value list is not a symbol a third module can compose or
    re-export.  It is private to the modules that build a type from it, so the only fact
    that crosses is the spelling and the name.
    """

    module: str
    symbol: str


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


def target_kind(declared: ir.Declaration | None) -> TargetKind:
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
    #: referring pointer, so a chain that dropped it would lose a fact the document
    #: states at that very pointer.  The FIRST sibling along the chain, for
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
    declared: ir.Declaration | None, at: Callable[[str], Target]
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


def local_target(mod: Module, pointer: str) -> Target:
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
    mod: Module,
    position: Position,
    *,
    objectish: bool = False,
    of_a_root_union: bool = False,
) -> ir.Decided | Refusal:
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
    node: nodes.Node, mod: Module, *, of_a_root_union: bool = False
) -> ir.Decided | Refusal:
    """What one PARSED node is: §4's content dedup, the ONE dispatch, and a SYMBOL where
    another document names the node.

    **The walk's per-node entry, and it reaches the run on no path** (§11's third AST
    test, ``adcp-client-python-3be.5``).  It was ``from codegen.emit import decide_type``
    -- a deferred import, so every nested-node recursion went ``handler -> lower_node ->
    the run -> lower.decide.decide`` and the run layer sat inside the per-node loop.  §11
    gives the decision layer "``Node`` -> ``Lowering``" and says it "may not know ...
    files, the run"; the arrows run ``lower <- emit`` and that import ran the other way.
    What was in the run was this wrapper, and nothing else of it: the dispatch was
    ``lower.decide.decide``'s already.  ``tests/test_import_rule.py`` holds the boundary
    by REACHABILITY now, over the closure of ``schema/`` and ``lower/``, so the next
    module placed between a handler and the run reddens without being named.

    **Three statements about THE NODE AT A POINTER, which is what makes them a wrapper
    rather than an arm** (§5: the dispatch "contains no decision beyond the route"): adopt
    the class an EQUAL node declared, name the node where the bundle's ``$ref``\\ s name
    its pointer, and seed the content memo at it.  All three apply to every arm equally --
    an array, a scalar, a mapping and a multi-type node are all annotations with no name
    -- so they sit outside the ``match`` and above all twelve arms.

    **§4's content dedup: nodes with identical content are one node.**  The memo is
    consulted BEFORE the dispatch and seeded after it, so the second occurrence of a node
    decides to the symbol the first DECLARED and no second class is written for it.  The
    equality, the binding, what seeds the memo and what §4 decides about a group are all
    ``lower/names.py``'s (:func:`names.same_node`, :func:`names.adopt`); what is HERE is
    the CALL, and §7 cannot take it: a second occurrence's CHILDREN are never lowered, so
    a declaration the walk did not make has no name for a pass to derive, and the pruning
    is a decision about the walk.

    ``mod.named`` is a function of the BUNDLE (``bundle.named_nodes``), not of the run's
    document set, so whether a node gets a name does not depend on who else was emitted.
    A class or an enumeration comes back ``local`` already, having declared itself at this
    very pointer, so nothing is named twice and no second symbol appears for one node.

    ``of_a_root_union`` is the one fact §6 names as travelling DOWN the tree: "where a
    lowering needs to know something about the node ENCLOSING it, the enclosing handler
    passes it down -- a child never reconstructs its parent."  The union handler reads
    ``node.position`` and tells its branches, because "of a root union" is a statement
    about the UNION and not about the branch; ``lower.enum.resolves_no_name`` is the
    predicate that needs it, and it read ``pointer.split("/")`` before this.

    Imported on use, for the reason :func:`rules_at` and the extras store are:
    ``codegen.lower.decide`` imports this module at module level and D13 fixes that
    direction, so this side is the lazy one.  It is a LAYER DOWN and not the run.
    """
    from codegen.lower.decide import decide

    pointer = node.pointer
    collapsed = names.same_node(mod, node)
    if collapsed is not None:
        mod.adopted[pointer] = collapsed
        bound = names.adopt(mod, pointer, collapsed)
        return bound if isinstance(bound, Refusal) else ir.Decided(bound)
    decided = decide(node, mod, of_a_root_union=of_a_root_union)
    if isinstance(decided, Refusal):
        return decided
    if pointer in mod.named and not decided.type.local:
        named = names.name_the_node(mod, pointer, node, decided)
        if isinstance(named, Refusal):
            return named
        # The node's facts moved onto the ALIAS, so what the parent holds is the symbol
        # and nothing else: a constraint restated beside it would be the second spelling
        # P2 removes.
        decided = ir.Decided(named)
    if decided.type.local and decided.type.path == pointer:
        mod.collapsed.append((node, pointer))
    return decided


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
    #: **§3a's CATALOGUE, as the walk sees it: ``pointer -> the entry this position
    #: RESTATES``.**  Keyed by this document's own pointer, so the question a node asks
    #: is a lookup at its own position and nothing here is a reading of the bundle.
    #:
    #: §3a: "The catalogue is an INPUT to the walk, never a pass over its output -- a
    #: node's type is a REFERENCE to a catalogue entry, or a fresh type where the node is
    #: genuinely unique.  Rewriting emitted output to deduplicate it afterwards is the
    #: post-processing this project exists to refuse."  A pointer in this map is the
    #: first of those and every other enum position is the second.
    #:
    #: A :class:`Target` and not a catalogue value, because what the position needs is
    #: exactly what a ``$ref`` at the same position would need -- a module spelling, a
    #: symbol and §4's three outcomes -- and an enum entry is :attr:`TargetKind.ANNOTATION`
    #: like every other enumeration.  The run builds it (``emit.emit``) because the
    #: SPELLING is a function of the two document paths (D1) and this layer knows
    #: neither; ``codegen/catalogue.py`` names the home's NODE and derives no import.
    #:
    #: Empty by default, so a document lowered outside a run restates its vocabularies
    #: exactly as it did before this layer existed -- the same refusing default
    #: :attr:`targets` has, and for the same reason: §9 forbids a reading of the run, and
    #: a walk with no table minted no reference to invent.
    vocabularies: Mapping[str, Target] = field(default_factory=dict)
    #: **§3a's catalogue keyed on the VALUE LIST, for the positions no pointer reaches.**
    #: ``members -> the entry's home``, where a :class:`Target` is a home in ANOTHER
    #: module and a ``str`` is a POINTER of this one.
    #:
    #: :attr:`vocabularies` answers a position the BUNDLE states, which is a pointer this
    #: document's own text carries.  Two restating positions are not of that kind and both
    #: were measured leaving a second class over an entry's members:
    #:
    #: * **a node a COMPOSITION re-lowers.**  §2's intersection rule reads a base's
    #:   declaration beside this document's own, so a node the base alone declares is
    #:   lowered again here -- and ":attr:`inherited_targets`" says why no pointer key
    #:   reaches it: "the pointer it arrives at is this document's -- derived from the
    #:   restating conjunct -- and belongs to no edge of either document".  3 entries over
    #:   this bundle, all ``core/postal-area.json`` re-lowering
    #:   ``core/postal-country-system.json``'s per-country ``system`` branches.
    #: * **a position whose home is in this SAME module.**  §4's content dedup is the rule
    #:   there and its key is node EQUALITY, so two positions stating one value list under
    #:   different descriptions are two classes to it.  Where the catalogue has judged them
    #:   one subject across documents, the positions inside the home's own document are
    #:   part of that one subject too -- and the reference is LOCAL, which is why the value
    #:   is a pointer rather than an import.  7 entries over this bundle.
    #:
    #: **Asked only of a node carrying NO constraint beside its ``enum``**, which is the
    #: whole of the guard and is §3a's structural identity read at the one place it can
    #: still differ: a value list beside a ``pattern`` admits a subset of the members, so
    #: it is not the entry's vocabulary whatever its members spell.  The one node of this
    #: bundle that reaches that case is
    #: ``core/postal-country-system.json#/anyOf/3/properties/country``.
    restatements: Mapping[tuple[Any, ...], Target | str] = field(default_factory=dict)
    #: **§3a's SHARED VALUE LIST, keyed on the members**: ``members -> the module-level
    #: constant the value list is written under``, as a ``str`` where the constant is
    #: declared in this module and a :class:`ValuesImport` where it is declared in the
    #: namespace's catalogue module.
    #:
    #: The OTHER half of §3a's split, and it is the half :attr:`restatements` cannot be:
    #:
    #:     "the **VALUE LIST** is a module-level constant in the catalogue layer, written
    #:     once per distinct member set; the **NAMED TYPE** is constructed from it at each
    #:     position that needs one, keeping the name §4 derives and keeping the types
    #:     distinct."
    #:
    #: :attr:`restatements` answers "this position is the SAME TYPE as one declared
    #: elsewhere, so import it".  This answers "this position is a DIFFERENT TYPE over the
    #: same value list, so declare it and take the values from one place" -- which is
    #: ``codegen/vocabularies.py``'s ``DISTINCT`` and ``PENDING_A_NAME``, and §3a's two
    #: title conflicts where §1 obliges both documents to export a symbol.
    #:
    #: Empty by default, so a document lowered outside a run writes every value list in
    #: its own class bodies -- the same refusing default :attr:`vocabularies` has, and for
    #: the same reason.
    value_lists: Mapping[tuple[Any, ...], ValuesImport | str] = field(default_factory=dict)
    #: **§3a's catalogue layer L2, as this document's own rows**: ``pointer -> the home of
    #: the OBJECT TYPE this position restates``.
    #:
    #: :attr:`vocabularies` is the same table at L0 and the two differ in exactly one
    #: field.  An enumeration is :attr:`TargetKind.ANNOTATION` -- §4 makes it an
    #: ``Annotated`` alias and never a class -- and an object type is
    #: :attr:`TargetKind.CLASS`, which is what reading 4 ranges over at this layer: "a type
    #: stated at more than one position is written once and referenced, never restated --
    #: and this reading ranges over ALL FOUR of the catalogue's layers, not the first".
    #:
    #: A pointer in this map is §3a's "a REFERENCE to a catalogue entry" and every other
    #: object position is "a fresh type where the node is genuinely unique".  The key is
    #: ``codegen/catalogue.Admitted``'s -- the decided key, which holds the property names,
    #: ``required``, ``additionalProperties`` and every narrowing keyword, resolves
    #: references before keying, and holds no ``title``, ``description``, ``examples`` or
    #: order -- so **a group whose members differ in a keyword that NARROWS is two entries
    #: and never one**, which is §3a's guard held by the key rather than by a check.
    #:
    #: Empty by default, for :attr:`vocabularies`' own reason: §9 forbids a reading of the
    #: run, and a walk with no table minted no reference to invent.
    objects: Mapping[str, Target] = field(default_factory=dict)
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
    #: existed (``adcp-client-python-10l.26``, measured at
    #: ``core/daast-tracker-constraints.json`` and
    #: ``core/vast-tracker-constraints.json``).
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
    #: inlines that text at the referring pointer, so dropping it loses a fact the
    #: document states at that very pointer.
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
    #: **THE DOCUMENT OF RECORD this module is lowered from**, for the one reader that
    #: needs a pointer's ROOT rather than its node: §5's ``if`` row, which reads a
    #: condition through the local reference ``bundle.stored`` minted when it stored the
    #: subtree once (§8's sentence 3a, ``lower.rules.through_the_storage``).
    #:
    #: A storage reference resolves against the document ROOT, so no node and no
    #: enclosing node carries the answer -- which is why this is the record and not a
    #: second per-pointer map beside :attr:`local`.  It is the same object
    #: ``emit.lower_document`` is handed and already reads twice (:attr:`local`,
    #: :attr:`object_constrained`), so holding it costs nothing and nothing here copies
    #: the document.
    #:
    #: Empty by default, which is the arm that reads a reference AS WRITTEN: a document
    #: lowered outside a run has no storage to see through, so the condition behind one
    #: is unreadable and DECLARES -- the same refusing default :attr:`named` and
    #: :attr:`local` have, and for the same reason.
    record: Mapping[str, Any] = field(default_factory=dict)
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
    #: than declaring a second class for it.  Written and read by :func:`lower_node`,
    #: which is the one per-node walk.
    #:
    #: **The equality is §4's own**, and that is what §14 step 5 deleted the old
    #: ``content_key`` serialisation for: "two nodes are equal exactly when they state the
    #: same thing about an instance -- which is §4's content dedup read off the type system
    #: rather than off a JSON serialisation with a position bit appended".  So the memo is
    #: a SEQUENCE and not a mapping: a node carries mappings and is not hashable, and the
    #: alternative is a second spelling of what identical means, which is §9's own open
    #: question about two instruments disagreeing about identity.  **The READING is
    #: ``lower/names.py``'s already** (§14 step 7): ``names.same_node`` is the equality and
    #: ``names.adopt`` the binding, and what stays on the walk is this record and the call
    #: that consults it -- a second occurrence's children are never lowered, so the pruning
    #: is a decision about the walk.  Per MODULE, so the linear scan is over tens of
    #: entries.
    #:
    #: **A ``$ref`` is compared as a STRING and never followed, which is the CUT** §9 says
    #: an instrument has to state: :class:`codegen.schema.nodes.Reference` carries the
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
    collapsed: list[tuple[nodes.Base, str]] = field(default_factory=list)
    #: The other half of that record, and the half a check can read: ``pointer -> the
    #: symbol the node at it ADOPTED`` because an earlier node of identical content had
    #: already declared one.  ``collapsed`` is keyed by content, which says what was
    #: collapsed and not WHERE, and "where" is the only thing a grader can compare a
    #: node against -- so the dedup is graded by asking, of every adoption, whether the
    #: adopting pointer's content really equals the declaring pointer's.  Written by
    #: :func:`lower_node` on the same line that returns the adopted type, so an
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
    #: **It was EMPTY over the whole bundle at §14 step 8**, which was that step's exit
    #: condition: no cell widened, so no handler minted one and ``APPROXIMATED`` was 0.
    #: Step 10 widened the cells and handlers mint them now; ``./check``'s third line is
    #: the reading, and it is not zero.
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

    def needs_values(self, where: ValuesImport) -> str:
        """Record that this module imports §3a's value list from ``where``, and name it.

        **ONE half and not two, where :meth:`importing` writes both, and the asymmetry is
        the thing it says.**  :attr:`imported` exists so that a third module composing
        this one takes a symbol from its DECLARER rather than from here, which is §1's
        one-import-path rule across a chain.  A value list is private to the modules that
        build a type over it -- never a base, never a field's type, never re-exported --
        so there is no chain for a declarer to be named in, and the catalogue module it
        comes from has no document to name anyway (:class:`ValuesImport`).
        """
        self.imports.add((where.module, where.symbol))
        return where.symbol

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
            # at the CLASS's own pointer.  Routed through :func:`lower_node`, the
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
class Dropped:
    """One fact a rule source states and the class does not carry, at its own address.

    The four things ``lower.approximate.declare`` needs and nothing else: it mints the
    declaration, reads the rung off the cell at ``position``, and the caller supplies
    neither -- §3's "a handler never chooses a rung and never writes an attribution".
    """

    keyword: str
    #: Where the DOCUMENT states it.  The node's own pointer for the node's own sources,
    #: and the conjunct's for a conjunct's.
    pointer: str
    #: The position the cell is read at, which is the node's own or CONJ.
    position: Position
    #: What the document states for the keyword there, in the document's own spelling.
    fact: Any


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
    #: **Every fact a rule source states that the rules above do NOT carry**, each with
    #: the pointer and the position it is stated at, so the one caller that declares a
    #: class can declare them (``docs/plan/final-state.md`` reading 2, "every exception to
    #: reading 1 is a declared widening").  Fifth on this carrier for the reason the other
    #: four are here: a caller that read the rule tuple and forgot the drops would emit a
    #: class wider than its document with nothing in the report naming the pointer, which
    #: is what ``adcp-client-python-3bb`` and ``-6oe`` both measured.
    #:
    #: The POINTER is carried per entry because a conjunct's fact is stated at the
    #: conjunct's own pointer and not at the class's: §2 keeps a conjunct a DECLARATION,
    #: ``approximate.declare`` spells the pointer the way ``__adcp_schema__`` spells it,
    #: and a declaration at a pointer the document states nothing at is one
    #: ``harness.check_widening`` can never discharge.
    dropped: tuple[Dropped, ...] = ()
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


#: **The type of the resolver §2's intersection rule is HANDED**, which is why it lives
#: with the context and not with the rule.  :meth:`Module.resolve_node` is the one
#: implementation; ``intersect``'s predicates and :func:`rules_at` take one as an
#: ARGUMENT, so the alias belongs where the thing it describes does.  Named rather than
#: spelled at each site because ``intersect.declares_an_array`` is read by ``lower.rules``
#: too and the parameter it threads is this one.
Resolver = Callable[[str], dict | None] | None


def rules_at(
    node: nodes.Base,
    *also: Mapping[str, Any],
    position: Position = Position.ROOT,
    resolve: Resolver = None,
    at: Sequence[str] = (),
    keeps_every_key: bool | None = None,
    root: Mapping[str, Any] | None = None,
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

    **``resolve`` is here for ONE consumer and the other seven reductions never see
    it**: ``uniqueItems`` sits one level DOWN, on the array a property holds, and a
    property may declare that array through a COMPOSITION -- so ``_distinct``'s gate is
    :func:`declares_an_array`, which reads a conjunct through its ``$ref`` the way §2's
    intersection already reads one.  Every caller has ``mod`` in scope and passes
    ``mod.resolve_node``; a caller that passes nothing gets the gate's safe arm, which
    answers ``False`` for a composing declaration and leaves the keyword for the handler
    that claimed it to report or refuse.  Threaded as a parameter rather than read off a
    module-level anything because the resolver is a fact of the RUN and this function is
    a pure reading of a node.

    **Converted to node fields.**  The node's own reading is :attr:`nodes.Base.rules`
    (the rule sources, which the parser classified from the table at this position),
    :attr:`nodes.Base.declared` (``uniqueItems`` sits one level down, on the array a
    property holds) and whether it states ``additionalProperties`` (the ``minProperties``
    gate) -- and ``screen`` is the rule sources the node STATES, which is what a screen
    asks: the only keys a screen can admit are keys the node carries, and a rule source
    the node carries is in that mapping exactly when the table and ``presence_only``
    admit it here.  ``also`` stays RAW, because an ``allOf`` conjunct is a DECLARATION by
    §2's own decision.

    **``at`` is where each of ``also`` is STATED**, one pointer per conjunct in the same
    order, so :attr:`Rules.dropped` can carry a conjunct's fact at the conjunct's own
    address rather than at the class's.  Empty for a caller with no conjuncts, and a
    caller that passes conjuncts without pointers gets the node's own -- which is the
    fail-safe direction for everything but a declaration, and is why the one caller that
    declares passes them.

    **``keeps_every_key`` is the CLASS's extra policy, asked once for every view**
    (``adcp-client-python-6oe``): ``min``/``maxProperties`` are counted over the keys the
    class RETAINED, and one class carries every conjunct's rules, so the gate is a
    property of the class and not of whichever view stated the keyword.  ``None`` keeps
    each view's own reading, which is what every caller but :func:`declare_object` has to
    offer -- and :func:`declare_object` is the one that writes the tuple onto a class.

    **``root`` is the DOCUMENT OF RECORD this node belongs to**, for §8's sentence 3a:
    §5's ``if`` row reads a condition through the local reference the record minted when
    it stored the subtree once (``lower.rules.through_the_storage``).  Threaded for the
    same reason ``resolve`` is -- the record is a fact of the RUN and this function is a
    pure reading of a node -- and ``None`` is the arm that reads a reference as written,
    which is what a caller with no run in hand gets.
    """
    from codegen.lower import rules

    lowered = [
        rules.lower(
            node.rules,
            node.declared,
            ("additionalProperties" in node.declares)
            if keeps_every_key is None
            else keeps_every_key,
            resolve=resolve,
            root=root,
        ),
        *(
            rules.lower_declaration(
                c, position, resolve=resolve, extra_stated=keeps_every_key, root=root
            )
            for c in also
        ),
    ]
    #: The pointer and the position each view's facts are STATED at: the node's own for
    #: the node, and the conjunct's own at CONJ for each conjunct the caller located.
    sites = [
        (node.pointer, node.position),
        *((at[i] if i < len(at) else node.pointer, Position.CONJ) for i in range(len(also))),
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
        dropped=tuple(
            Dropped(keyword, pointer, stated_at, fact)
            for one, (pointer, stated_at) in zip(lowered, sites, strict=True)
            for keyword, fact in one.dropped
        ),
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
    never chosen at a raise site."  Two answers and each is the table's:

    * a key with NO ROW is a VERDICT: a keyword in none of §5, §6 or §7 is one the
      bundle did not use, so the obstruction is the document's -- there is no lowering
      to schedule and answering "a later row does" about it would promise an unscheduled
      row;
    * a key whose cell is a LOWERING effect and whose handler claims nothing is a
      DEFERRAL -- §9's first rule, because minting a verdict for unwritten code reports
      clearable work as finished.

    **There were three, and the third went with ``Effect.REFUSE``** (§14 step 8): "a key
    whose cell is REFUSE is a VERDICT -- the obstruction belongs to the document, which
    is what §7 of the semantics document decided about it".  §7 decided the opposite on
    2026-10-26 and is empty, so the arm has no cell that can reach it and the VERDICT
    answer is the no-row one alone.  A cell that CARRIES nothing mints nothing at all:
    the screen admits it and never reaches a refusal.

    *Why derived.*  The reviews record the two kinds assigned by hand at a raise site
    and the assignment coming out inverted in bulk: a cell the semantics document
    decides, written up as a verdict against the document.  A kind read off the table
    cannot say that, because the table is where the decision that the keyword compiles
    was made.  Measured on the base tree (``5d92cf2c0``, 406 emitted and 648 refused of
    1,054), the old reading -- "is the name in draft-07's meta-schema" -- called 11 of
    the 648 a verdict about a non-keyword: ``discriminator`` 7, ``notes`` 2,
    ``enumMetadata`` 1, ``last_updated`` 1.  The table admits all four (§6) and refuses
    none, so none of them mints a kind now and none is read off a meta-schema.
    """
    answer = keywords.cell(key, position)
    if answer is None:
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

def carried(decided: ir.Decided, pointer: str, what: str, mod: Module) -> ir.TypeRef | Refusal:
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
    mod: Module | None = None,
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
      carried nowhere by the screen.  **There is no arm that refuses on a cell**: §7 is
      empty and ``Effect.REFUSE`` is retired (§14 step 8), so the only keyword a
      document is refused on is one the table gives no row;
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
    mod: Module | None = None,
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
    keys: Collection[str],
    pointer: str,
    position: Position,
    handled: Collection[str],
    why: str | None,
    mod: Module | None,
) -> Refusal | None:
    """The admission reader itself, over keys already in the order the report wants."""
    for key in keys:
        # **``handled`` is asked FIRST**, before the cell, because a caller that claims
        # a key has already decided what happens to it, and the screen may not re-decide
        # it.  The clause that used to be here -- an ``errorMessage`` handed in by
        # ``lower_composition`` so that the key the drop accounted for was not then
        # refused on -- is gone with ``Effect.REFUSE``: a cell carrying NOTHING never
        # reaches a refusal in the first place, so nothing has to be claimed to protect
        # it.  Measured on ``media-buy/sync-catalogs-request.json``.
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
        # **No arm here refuses on a CELL.**  §7 is empty, so a key with a row is either
        # a fact this node's kind consumes -- a DEFERRAL below where the handler has not
        # claimed it -- or admitted.  A key whose drop is REPORTED is admitted here too:
        # the note is ``bundle.reported_drops``' and reaches every position, where an arm
        # in this screen would reach only the positions a walk arrives at
        # (``/then``'s subschema is a RULE source read raw, and the screen never sees it).
        if not keywords.lowers(answer):
            continue
        return Refusal(
            key,
            pointer,
            why or refusal.DEFERRED_TO_A_LATER_ROW,
            kind=kind_for(key, position),
        )
    return None


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
) -> ir.Decided | Refusal:
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

    It returns a :class:`codegen.ir.Decided` and not a pointer, because the three callers each want
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
    return ir.Decided(ir.TypeRef(pointer, local=True))


def local_reference(mod: Module, pointer: str, at: str) -> ir.Decided | Refusal:
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
        return ir.Decided(ir.TypeRef(pointer, local=True))
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
    # ``"linear"``.  §2 is why it cannot be declared instead: "a default is a value and
    # not a constraint, so it neither widens nor narrows what the class accepts", so
    # there is no fact about acceptance to drop and nothing to attribute.
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
    mod: Module, pointer: str, doc: nodes.Base, decided: ir.Decided
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
    return bind_without_a_model(mod, pointer, names.alias_for(pointer, doc, decided))
