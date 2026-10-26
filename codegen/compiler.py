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
from typing import Any

from pydantic import BaseModel as PydanticBaseModel

from adcp.types._base import SchemaRef
from adcp.types._runtime import Rule
from codegen import ir, keywords, refusal
from codegen.ir import MISSING
from codegen.keywords import Position
from codegen.refusal import Kind, Refusal

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
        mod.carries_nothing.extend(
            f"{pointer or '/'}: {k}: a constraining sibling of $ref, which draft-07 "
            "ignores, so the keyword constrains no instance and the document's accepted "
            "set is the target's alone (section 5's $ref row); the record keeps the key "
            "and section 8 does not grade it"
            for k in sorted(inert)
        )
    return inert



# --------------------------------------------------------------------------- #
# names (D3)
# --------------------------------------------------------------------------- #
def class_name(title: str) -> str:
    """``pascal_case`` that keeps an acronym: only the first letter of a word is
    touched, so ``TMPX Chunk`` stays ``TMPXChunk`` and does not become
    ``TmpxChunk``."""
    words: list[str] = []
    cur = ""
    for ch in title:
        if ch.isalnum():
            cur += ch
        elif cur:
            words.append(cur)
            cur = ""
    if cur:
        words.append(cur)
    return "".join(w[:1].upper() + w[1:] for w in words)


def field_name(key: str) -> str:
    """The Python field name for a property key, which is the key itself unless
    pydantic cannot carry a field under that name.

    A key is carried as-is or it is carried under an ALIAS, never dropped.  The
    bundle has keys a Python attribute cannot spell (``$schema``) and keys
    pydantic reads as something other than a field: a leading underscore makes a
    private attribute and no field at all, so
    ``core/truncation-sentinel.json``'s required ``_truncation`` was silently
    absent from the model -- the model refused the document's own instance AND
    accepted an instance omitting the required key, in the same class.

    The alias is the ONLY accepted spelling (no ``populate_by_name``), so the
    model's accepted set stays the document's: the wire name is accepted and the
    Python name is not a second way in.
    """
    name = "".join(c if c.isalnum() or c == "_" else "_" for c in key).lstrip("_")
    if not name or name[0].isdigit():
        name = f"f_{name}"
    while (
        keyword.iskeyword(name) or name.startswith("model_") or hasattr(PydanticBaseModel, name)
    ):
        name += "_"
    return name


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

    ``declares`` is the set of symbols the class's own module declared by the time the
    class was, which is what lets a reuser tell a symbol it may import from the base's
    module from one that module merely imported itself -- a re-export, which section 2's
    import rule refuses (``emit.emit``'s binder refuses the same shape for a fragment
    ``$ref``, and for the same reason).
    """

    properties: Mapping[str, dict]
    required: frozenset[str]
    #: ``key -> ir.Field``; see above.  Overlaid by :func:`declare_object` with the
    #: props it is handed, so every declaring row records it in one place.
    decided: Mapping[str, ir.Field] = field(default_factory=dict)
    #: The symbols the declaring module had declared; see above.
    declares: frozenset[str] = frozenset()
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


@dataclass(frozen=True)
class Target:
    """What a resolved ``$ref`` gives the lowering that asked for it.

    ``module`` and ``symbol`` are what an ANNOTATION needs.  ``shape`` is what an
    ``allOf`` conjunct needs, and it is ``None`` when the target is not a class --
    D2's root-scalar row is an ``Annotated`` alias, and subclassing one is a
    ``TypeError`` at import, so a lowering refuses it as a base rather than
    writing a module that cannot be imported.
    """

    module: str
    symbol: str
    shape: Shape | None = None
    #: The target's own ROOT NODE, for the ONE reader that needs the schema rather than
    #: the symbol: section 2's intersection rule asked of two declarations that are each a bare
    #: ``$ref`` (:func:`Module.resolve_node`).  ``None`` for a reference carrying a
    #: FRAGMENT, which is the scope rather than an omission -- the binder has already
    #: looked the fragment's SYMBOL up and a node navigator here would be a second
    #: pointer walk -- so such a pair stays undecidable and refuses.
    node: dict | None = None


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


def _no_binder(uri: str, pointer: str) -> Target:
    """The default binder: a document lowered on its own resolves no reference.

    ``emit`` supplies the real one, which owns the walk.  Lowering a document
    without it refuses its references by name rather than inventing an import, so
    there is no path on which a reference is silently dropped.
    """
    raise Refusal(
        "$ref",
        pointer,
        f"no reference binder: {uri} cannot be resolved to a module",
        kind=Kind.VERDICT,
    )


def decide(
    node: dict, pointer: str, name_hint: str, mod: "Module", position: Position
) -> Decided:
    """What one schema node IS: ``emit.decide_type``, reached by NAME.

    ``position`` is the node's own, passed by the caller because it is a STRUCTURAL
    fact of the caller -- a property's value is at PROP, an array's element at ELEM, a
    mapping's value at MAPV, a branch at BRANCH, a ``definitions`` entry at DEF -- and
    never recovered from the pointer string, which cannot tell a RULE reference from a
    PROP one.

    This used to be a callable carried on :attr:`Module.decide`, because reaching
    ``emit`` by name was forbidden: ``python -m codegen.emit`` executed that file as
    ``__main__`` under ``runpy``, so an importer of ``codegen.emit`` held a SECOND
    module object with a second dispatch table and a second decider.
    ``codegen/__main__.py`` is the fix -- no module of this compiler is ever bound as
    ``__main__`` -- so the decision is a function with one name again and the
    :class:`Module` carries data rather than functions.

    **The import is function-scope, and the cycle that forced it is GONE.**
    ``emit.ROWS`` read ``bundle``'s root selectors at MODULE level and ``bundle``
    imported the lowerings for two of them, so a module-level import of ``emit`` from
    anywhere the lowerings reach made ``import codegen.bundle`` an ``AttributeError`` on
    a partially initialised ``bundle`` -- measured, not theorised.  §14 step 5 deleted
    the table and moved those two predicates to ``tests/populations.py``, so ``bundle``
    imports nothing of ``lower`` and nothing of ``emit``.  What still retires the shim
    is the other half of that step: ``decide`` becomes ``lower/decide.py``'s exhaustive
    ``match`` over ``schema/nodes.py``'s kinds, and a lowering then imports it directly.
    Until then the one deferred import is here rather than at each of its call sites.
    """
    from codegen.emit import decide_type

    return decide_type(node, pointer, name_hint, mod, position)


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
    #: ``(uri, pointer) -> Target``; see ``emit.emit``.  The last callable carried
    #: here, and the one the entry-point module does not retire: it is a CLOSURE over
    #: the run's lowered/refused/in-flight documents and over ``emit.lower``'s own
    #: recursion, so there is no module-level function to reach by name in its place.
    #: ``docs/plan/architecture.md`` §14 step 7 is where it goes, by computing the
    #: reference closure and the dependency order up front and passing ``targets``
    #: through this context as data.
    bind: Callable[[str, str], Target] = _no_binder
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
    imports: set[tuple[str, str]] = field(default_factory=set)  # (module, name)
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
    names: set[str] = field(default_factory=set)
    #: class name -> its :class:`Shape`, for a class declared in THIS module.
    shapes: dict[str, Shape] = field(default_factory=dict)
    #: JSON Pointer -> the symbol declared for the node at it.  Written by
    #: :meth:`declare`, which EVERY declaration passes through, so a fragment
    #: reference reads one map rather than a second record something could forget to
    #: write.  This is how a ``$ref`` carrying a pointer finds the symbol to import.
    #: It is also :func:`local_reference`'s MEMO, which is why that function needs no
    #: record of its own: a node declared because the walk reached it and a node
    #: declared because a local reference asked for it are one entry here.
    declared: dict[str, str] = field(default_factory=dict)
    #: D3's content dedup: ``the key of a node's content -> the symbol declared for the
    #: FIRST node with that content``.  Two nodes with identical content are ONE node, so
    #: the second occurrence decides to the symbol the first declared rather than
    #: declaring a second class for it.  Written and read by ``emit.decide_type``, which
    #: is the one per-node walk, and keyed by ``emit.content_key`` -- which is where the
    #: equality, and the place it cuts a reference cycle, is stated.
    #:
    #: Per MODULE, which is per document (D1).  Two documents that inline identical
    #: content keep a class each: collapsing them would need a rule for which module owns
    #: the survivor, D1 gives a node exactly one home, and 0 of the bundle's 1,271
    #: identical-content groups have a ROOT carrying that content for a ``$ref`` to reach.
    collapsed: dict[str, str] = field(default_factory=dict)
    #: The other half of that record, and the half a check can read: ``pointer -> the
    #: symbol the node at it ADOPTED`` because an earlier node of identical content had
    #: already declared one.  ``collapsed`` is keyed by content, which says what was
    #: collapsed and not WHERE, and "where" is the only thing a grader can compare a
    #: node against -- so the dedup is graded by asking, of every adoption, whether the
    #: adopting pointer's content really equals the declaring pointer's.  Written by
    #: ``emit.decide_type`` on the same line that returns the adopted symbol, so an
    #: adoption that went unrecorded is an adoption that did not happen.
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

    def resolve_node(self, uri: str) -> dict | None:
        """The schema a cross-document reference names, or ``None``.

        For section 2's intersection rule and for nothing else: two declarations that are each
        a bare ``$ref`` state the same KIND of thing about an instance and whether one
        narrows the other is a fact about the two TARGETS, which no amount of reading
        the two references can answer.  Measured on the one site:
        ``core/media-buy-frequency-cap-requirement.json`` at
        ``/allOf/1/properties/supported_control_modes/items`` references a one-member
        enumeration where the base it composes references a three-member one, and the
        one member IS one of the three -- a narrowing the reference pair cannot show.

        ``None`` for anything undecidable -- a local reference, a fragment, a target
        that refuses -- and the caller then treats the pair as not ordered and refuses
        the document.  That is the safe direction: a reference the merge rule cannot
        read is a declaration it must not claim is narrower.

        **A reference is never DEREFERENCED into the field**, only into the predicate
        (:func:`_restatement`).  The field is decided from the document's own ``$ref``,
        because a cross-document reference is an IMPORT and not a copy (P2) -- the thing
        ``test_a_cross_document_reference_is_an_import_and_not_a_copy`` exists to catch.
        """
        try:
            return self.bind(uri, "").node
        except Refusal:
            return None

    def declare(self, name: str, pointer: str, declaration: ir.Declaration) -> None:
        """Record one declaration under its symbol and its pointer.

        The two names a module can collide on are checked here, and nowhere else: a
        SYMBOL already declared, and a POINTER already declared.  Taking the declaration
        rather than its text is the whole of §7's gate at this seam -- the imports a
        declaration needs are reported by ``render.declaration`` when the module is
        written, so a caller cannot declare a block and forget to merge its imports
        because there is no block to declare.
        """
        if name in self.names:
            raise Refusal(
                "title",
                pointer,
                f"two nodes in this document derive the class name {name!r}",
                kind=Kind.VERDICT,
            )
        if pointer in self.declared:
            # The symmetric failure to the one above, and the same kind of thing: a
            # pointer names ONE node of a document, so two symbols at one pointer
            # means a fragment reference to it would import whichever the walk
            # happened to declare last.  Measured 0 times over the whole population
            # -- the root's pointer is written once, by the row, and every nested
            # declaration sits at its own node -- so this refuses rather than
            # ordering them.
            raise Refusal(
                "$ref",
                pointer,
                f"two nodes are declared at this pointer: {self.declared[pointer]!r} "
                f"and {name!r}, so a reference to it would import whichever came last",
                kind=Kind.VERDICT,
            )
        self.names.add(name)
        self.declared[pointer] = name
        self.declarations.append(declaration)


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
      ``oneOf``/``anyOf`` is a rule only where every branch is ``required``-only
      (``rules.presence_only``, the published step-5/step-7 test).  A combinator of
      SHAPES is a nested union, ``rules.lower`` writes nothing for it, and admitting
      it would emit a class that drops the combinator silently -- a model wider than
      its document.  Measured on the 3.2 bundle: 72 object nodes carry a
      non-presence-only combinator, and 0 of them sit in a document that emits
      today, so the object row's former unconditional admission was latent rather
      than live -- and this step makes more documents emit, which is what would have
      reached it.
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


def rules_at(node: dict, *also: dict, position: Position = Position.ROOT) -> Rules:
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
    """
    from codegen.lower import rules

    lowered = [rules.lower(n) for n in (node, *also)]
    screen = rule_sources(position)
    if rules.presence_only(node):
        screen |= combinators(position)
    distinct: list[str] = []
    for one in lowered:
        distinct += [key for key in one.distinct if key not in distinct]
    return Rules(
        screen=frozenset(screen),
        rules=tuple(rule for one in lowered for rule in one.rules),
        distinct=tuple(distinct),
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

def carried(decided: Decided, pointer: str, what: str, mod: Module) -> ir.TypeRef:
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
    from codegen.emit import name_the_constraint

    named = name_the_constraint(decided, mod)
    if named is not None:
        return named
    stated = {
        **decided.constraints,
        **({"format": decided.format} if decided.format else {}),
    }
    raise Refusal(
        sorted(stated)[0],
        pointer,
        f"{what} states {stated} and ir.TypeRef carries no constraint, so the "
        "keyword would reach the field holding this node and bind every other node "
        "under it; section 2 binds a constraint to the TYPE, and the alias module "
        "codegen.constraints has no spelling for this shape",
        kind=Kind.DEFERRED,
    )


def check_keywords(
    node: Mapping[str, Any],
    pointer: str,
    position: Position,
    handled: Collection[str] = (),
    why: str | None = None,
    mod: "Module | None" = None,
) -> None:
    """Refuse the first keyword at this node the TABLE does not admit here.

    **The screen is a reader of ``codegen.keywords`` and holds no keyword set of its
    own.**  Every key is looked up at the node's POSITION, which the caller passes
    because it is a structural fact of the caller -- a property's value is at PROP, an
    array's element at ELEM, a branch at BRANCH -- and never recovered from the pointer
    string, which cannot tell a RULE reference from a PROP one.  The cell then decides,
    and ``docs/plan/architecture.md`` §3's admission reader is exactly these arms:

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
    sentence and a kind decided together at one raise site is how a cell the semantics
    document decides came to be written up as a verdict against the document.
    """
    for key in sorted(node):
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
            raise Refusal(key, pointer, NO_SUCH_KEYWORD, kind=kind_for(key, position))
        if answer.effect is keywords.Effect.REFUSE:
            raise Refusal(key, pointer, why or answer.compiles, kind=kind_for(key, position))
        if not keywords.lowers(answer):
            continue
        raise Refusal(
            key,
            pointer,
            why or refusal.DEFERRED_TO_A_LATER_ROW,
            kind=kind_for(key, position),
        )


# --------------------------------------------------------------------------- #
# the field builder and the class declarer
# --------------------------------------------------------------------------- #
def fields(
    props: Mapping[str, Any],
    required: Collection[str],
    pointer: str,
    name: str,
    mod: Module,
    *,
    inherited: Collection[str] = (),
    declared_at: Mapping[str, str] | None = None,
    distinct: Collection[str] = (),
    reuse: Mapping[str, ir.Field] | None = None,
) -> list[ir.Field]:
    """The decided properties for one property map, children declared first.

    Shared with a composing row, which builds ONE property map out of a root's
    own ``properties`` and an inline ``allOf`` conjunct's.  How a property is
    decided is the same question wherever it was declared, and a second copy of
    this loop is how two declarations of one field come to disagree about the
    answer.

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
    """
    undeclared = [r for r in required if r not in props and r not in inherited]
    if undeclared:
        raise Refusal(
            "required",
            pointer,
            f"required names no property declares: {undeclared} (step 7's rule, not a field)",
            kind=Kind.DEFERRED,
        )

    built: list[ir.Field] = []
    spelled: dict[str, str] = {}
    where = declared_at or {}
    reuse = reuse or {}
    for key, sub in props.items():
        at = where.get(key, f"{pointer}/properties/{key}")
        if not isinstance(sub, dict):
            raise Refusal("properties", at, "property is not a schema", kind=Kind.VERDICT)
        fname = field_name(key)
        if fname in spelled:
            raise Refusal(
                "properties", at, f"{key!r} and {spelled[fname]!r} both spell the field {fname!r}"
            , kind=Kind.VERDICT)
        spelled[fname] = key
        is_distinct = key in distinct
        if is_distinct:
            # D6 owns the keyword at this position, so the walk below must not see it:
            # the array row carries no ``uniqueItems`` and refuses one by name, which
            # is what keeps an array NO class holds refused rather than widened.
            sub = {k: v for k, v in sub.items() if k != "uniqueItems"}
        if key in reuse:
            held = reuse[key]
            # The REUSED field's type ALREADY states its bound and its format (§2, and
            # :attr:`codegen.ir.TypeRef.facts`), so it is taken whole: splitting the
            # three back out and recombining them is what two carriers of one fact
            # invites, and the base decided this type at its own pointer.
            field_type = held.type
            is_distinct = held.distinct
        else:
            decided_type = decide(sub, at, name + class_name(key), mod, Position.PROP)
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
        if "default" in sub:
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
                mod.drops[at] = sub["default"]
            else:
                default = sub["default"]
        doc = sub.get("description")
        built.append(
            ir.Field(
                name=fname,
                wire=key,
                type=field_type,
                required=is_required,
                default=default,
                description=doc if isinstance(doc, str) and doc else None,
                distinct=is_distinct,
            )
        )
    return built


def declare_object(
    node: dict,
    name: str,
    pointer: str,
    mod: Module,
    props: Sequence[ir.Field],
    shape: Shape,
    position: Position = Position.ROOT,
    *,
    bases: tuple[str, ...] = (),
    rule_nodes: Sequence[dict] = (),
    root_required: tuple[str, ...] | None = None,
    discriminator: str | None = None,
    combinator: str | None = None,
) -> str:
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

    ``root_required``, ``discriminator`` and ``combinator`` are §4's three facts a UNION
    BASE carries and no other class does, so all three are ``None`` for every row but
    the union row.  They are declared on the class rather than formatted into a body
    line, which is §7's gate at this seam: ``render._union_base_lines`` writes the four
    statements and nothing before it holds one.
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
    ap = node.get("additionalProperties")
    extra_type = None
    if isinstance(ap, dict) and ap:
        extra_type = decide(
            {
                "type": "object",
                "additionalProperties": ap,
                **{k: node[k] for k in ("propertyNames",) if k in node},
            },
            pointer,
            name,
            mod,
            position,
        ).type
    description = node.get("description")
    declaration = ir.ClassDecl(
        name=name,
        ref=schema_ref(mod.document, pointer),
        fields=tuple(props),
        description=description if isinstance(description, str) and description else None,
        # D8; absent leaves the base's default in place.  A TYPED
        # ``additionalProperties`` is ``allow`` with the type beside it: the
        # properties are part of the document, so they are retained, and
        # ``__pydantic_extra__`` is what validates them.
        extra="allow" if extra_type is not None else {False: "forbid", True: "allow"}.get(ap),
        extras=extra_type,
        bases=bases,
        rules=stated.rules,
        root_required=root_required,
        discriminator=discriminator,
        combinator=combinator,
    )
    # :attr:`Shape.decided` and :attr:`Shape.declares` are written HERE and by no
    # caller, for the reason the rule tuple above is: this is the one funnel a class
    # with fields passes through, so a row cannot forget to record what it decided.
    # The caller's own ``decided`` is what the class INHERITS (a composing row passes
    # its bases'), and the props it is handed are this class's own and win the key.
    mod.shapes[name] = replace(
        shape,
        decided={**shape.decided, **{p.wire: p for p in props}},
        declares=frozenset(mod.declared.values()) | {name},
        description=description if isinstance(description, str) and description else None,
    )
    mod.declare(name, pointer, declaration)
    return name


def lower_object(
    node: dict,
    name: str,
    pointer: str,
    mod: Module,
    position: Position,
    *,
    bases: tuple[str, ...] = (),
) -> str:
    """Append the class for an object node, children first, and return its name.

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
    stated = rules_at(node, position=position)
    check_keywords(
        node,
        pointer,
        position,
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
    declared = node.get("type")
    if declared != "object" and not (declared is None and pointer in mod.object_constrained):
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
        raise Refusal(
            "type",
            pointer,
            f"an object node must declare type: object; this one declares "
            f"{node.get('type', '<absent>')!r} and nothing enclosing it constrains the "
            "instance to an object, so the document admits a non-object that no class can",
            kind=Kind.VERDICT,
        )
    props = node["properties"]
    if not isinstance(props, dict) or not props:
        raise Refusal(
            "properties",
            pointer,
            "an object node with no property declared",
            kind=Kind.VERDICT,
        )
    required = node.get("required", [])
    if not isinstance(required, list) or not all(isinstance(r, str) for r in required):
        raise Refusal(
            "required",
            pointer,
            f"required is {required!r}, not a list of names",
            kind=Kind.VERDICT,
        )
    built = fields(props, required, pointer, name, mod, distinct=stated.distinct)
    return declare_object(
        node,
        name,
        pointer,
        mod,
        built,
        Shape(props, frozenset(required)),
        position,
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


def _refuse_a_combinator_of_shapes(doc: dict, pointer: str, screen: frozenset[str]) -> None:
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
    pointer no document has.  Measured: ``creative/list-creatives-response.json``
    ``#/properties/creatives/items`` is the one document of the deferred population here,
    and its two branches are ``{"required": [...], "not": {...}}`` -- every one of which
    constrains only which keys are present, so what sends it down this path is
    ``rules._required_only`` admitting ``{"required"}`` ALONE.  Widening that predicate
    moves ``rules.presence_only``, which ``populations.states_an_object_rule`` is BUILT ON as a
    row's selector, so it is a change to a population and not to this row.
    """
    for keyword in _COMBINATORS:
        if isinstance(doc.get(keyword), list) and keyword not in screen:
            raise Refusal(
                keyword,
                pointer,
                f"this node composes AND carries a {keyword} whose branches are shapes "
                "rather than presence groups (rules.presence_only), and both are "
                "conjunctions with the same instance: a class carries the conjuncts as "
                "bases and fields, and nothing on a class carries a branch list, because "
                "a branch is satisfied by SOME instance.  There is no pointer to the "
                "conjunction of the two for the class to name, which is what "
                "union.ROOT_CONJUNCTS refuses a root union's own conjuncts for",
                kind=Kind.VERDICT,
            )


def lower_composition(
    doc: dict,
    name: str,
    pointer: str,
    mod: Module,
    position: Position,
    *,
    bases: tuple[str, ...] = (),
) -> str:
    """Append the class for an ``allOf`` node and return its name.

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
    """
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
    if doc.get("type") not in (None, "object"):
        raise Refusal(
            "type",
            pointer,
            f"an allOf of type {doc['type']!r} composes no object",
            kind=Kind.VERDICT,
        )
    stated = rules_at(doc, position=position)
    _refuse_a_combinator_of_shapes(doc, pointer, stated.screen)
    check_keywords(doc, pointer, position, COMPOSING | stated.screen, mod=mod)

    conjunct_bases: list[str] = []
    inherited: dict[str, dict] = {}
    inherited_required: set[str] = set()
    #: The FIELD each inherited key came out as on the base that declares it, and the
    #: base it came from.  Read only by the annotation-only arm below, which re-uses
    #: the field rather than re-deciding the node; :attr:`Shape.decided` says why.
    inherited_fields: dict[str, ir.Field] = {}
    inherited_from: dict[str, Target] = {}
    #: Every LOCAL declaration that won its key, and where it was declared.  The
    #: root's own properties and an inline conjunct's land in the SAME map,
    #: because draft-07 applies both to the same instance.
    local: dict[str, dict] = {}
    at: dict[str, str] = {}
    required: set[str] = set(_required(doc, pointer))
    #: The conjuncts that state a RULE of this node rather than a base or fields.
    conjunct_rules: list[dict] = []
    #: The description the FIRST base that states one states, for a composing node that
    #: states none of its own (:attr:`Shape.description`).  First and not last, and not
    #: a merge, because that is what ``harness._composed`` gap-fills on the document
    #: side -- ``if kw not in out`` over the conjuncts in order -- and the two halves
    #: have to read one composed document the same way.
    inherited_description: str | None = None

    def declare(key: str, node: Any, where: str) -> None:
        prior = local.get(key)
        if prior is None:
            local[key], at[key] = node, where
            return
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
            raise Refusal(
                _disagreeing(node, prior),
                where,
                f"{key!r} is declared at {at[key]} and again here, and neither "
                "declaration narrows the other",
                kind=Kind.VERDICT,
            )

    for key, sub in (doc.get("properties") or {}).items():
        declare(key, sub, f"{pointer}/properties/{key}")

    #: The conjuncts still to read, each with the pointer it sits at.  A WORKLIST
    #: rather than an ``enumerate`` because of :data:`CONJ_COMPOSES`' second entry: a
    #: conjunct carrying its own ``allOf`` pushes those conjuncts here, so ONE loop
    #: reads every depth, the keyword screen is asked once per node, and a refusal
    #: points at the pointer that carried the keyword rather than at the outermost
    #: conjunct.  Breadth-first, which is document order within each depth.
    unread: list[tuple[str, Any]] = [
        (f"{pointer}/allOf/{i}", c) for i, c in enumerate(doc["allOf"])
    ]
    while unread:
        where, conjunct = unread.pop(0)
        if not isinstance(conjunct, dict):
            raise Refusal("allOf", where, "a conjunct that is not a schema", kind=Kind.VERDICT)
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
                raise Refusal(
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
            target = mod.bind(conjunct["$ref"], where)
            if target.shape is None:
                # **The KIND is read off the cell and is a DEFERRAL, not a verdict.**
                # §5's ``$ref`` row at CONJ decides this very case -- "a BASE where the
                # target is a class declaring fields.  Where it is not -- a scalar, an
                # enum, a container, or a union root, whose instance is one of its
                # branches -- it is not a class a model can extend: the target is this
                # node's own TYPE, and the other conjuncts and the ``allOf``'s siblings
                # constrain it" -- and §14 step 8 is the step that writes it ("a scalar
                # or alias target as the type of a composing node").  So the
                # compilation is DECIDED and merely unwritten, which §9's first rule
                # makes a deferral: a verdict claims the obstruction belongs to the
                # document, to pydantic or to the pointer space, and it belongs to none
                # of the three here.  ``kind_for`` is the derivation and the only place
                # the two are told apart.
                raise Refusal(
                    "allOf",
                    where,
                    f"{target.symbol} is not a class, so it cannot be a base "
                    "(D2 makes a scalar root an Annotated alias, and subclassing "
                    "one is a TypeError at import); section 5's $ref row at CONJ makes "
                    "the target this node's own TYPE, which section 14 step 8 writes",
                    kind=kind_for("allOf", Position.CONJ),
                )
            mod.imports.add((target.module, target.symbol))
            conjunct_bases.append(target.symbol)
            inherited.update(target.shape.properties)
            inherited_fields.update(target.shape.decided)
            inherited_from.update(dict.fromkeys(target.shape.properties, target))
            inherited_required |= target.shape.required
            if inherited_description is None:
                inherited_description = target.shape.description
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
        screen = rules_at(conjunct, position=Position.CONJ).screen
        if keys <= INLINE | screen | CONJ_COMPOSES:
            # ``foreign`` is handed to the screen as CLAIMED, because this arm has
            # already decided what happens to it: it is dropped and reported.  Left
            # out, ``check_keywords`` walks ``sorted(node)`` and refuses on the very
            # name the drop above accounted for, which loses the document and leaves
            # the drop record unwritten -- measured on
            # ``media-buy/sync-catalogs-request.json``.
            check_keywords(
                conjunct,
                where,
                Position.CONJ,
                set(INLINE) | screen | set(CONJ_COMPOSES) | foreign,
                mod=mod,
            )
            if conjunct.get("type") not in (None, "object"):
                raise Refusal(
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
                raise Refusal(
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
                    raise Refusal(
                        "allOf",
                        where,
                        f"a conjunct whose allOf is {inner!r}, not a non-empty list of "
                        "schemas",
                        kind=Kind.VERDICT,
                    )
                unread.extend((f"{where}/allOf/{j}", c) for j, c in enumerate(inner))
            if "properties" in keys:
                if not isinstance(conjunct["properties"], dict) or not conjunct["properties"]:
                    raise Refusal(
                        "properties",
                        where,
                        "a conjunct declaring no property",
                        kind=Kind.VERDICT,
                    )
                for key, sub in conjunct["properties"].items():
                    declare(key, sub, f"{where}/properties/{key}")
            required |= set(_required(conjunct, where))
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
            # measured over every such conjunct in this bundle -- 7 documents, 28
            # branches -- **0 branches pin a const**, so ``union.discriminator``
            # intersects empty pin maps and answers "" for all 7.  Section 4's third
            # source, branches no instance satisfies twice, is what decides 6 of them
            # and it lives in ``codegen/lower/union.py``.
            #
            # 5 of the 7 have every branch constraining only key presence and reducible
            # through ``rules._required_groups`` today, which is the same row's cheaper
            # answer -- a ``RequiredGroups`` rule -- blocked only by
            # ``rules._required_only`` admitting ``{"required"}`` ALONE.  Widening it
            # moves ``populations.states_an_object_rule``, a row's selector, which is why
            # that is a change to a population rather than to this reader (the
            # measurement is :func:`_refuse_a_combinator_of_shapes`' docstring, taken
            # for this exact branch shape).
            #
            # Reported on the combinator rather than on ``min(keys)``: attribution is
            # the point of a refusal report, and ``sorted`` put ``not`` and
            # ``properties`` ahead of the keyword that is the reason.
            raise Refusal(
                combinator,
                where,
                f"a conjunct carrying a {combinator} of SHAPES rather than presence "
                "groups.  Section 5 says CONJ -> one class per branch over the composed "
                "bases, and section 4 says a payload reaches its branch only through a "
                "derived dispatch: no branch of any such conjunct in this bundle pins a "
                "const, so section 4's first source derives none and the third -- "
                "branches no instance satisfies twice -- is the one that decides them, "
                "in codegen/lower/union.py (salesagent-j3k2l.60, salesagent-j3k2l.67).  "
                "Where every branch constrains only key presence the same row's "
                "RequiredGroups rule is the cheaper answer, and it needs "
                "rules._required_only to admit more than {'required'} alone, which moves "
                "bundle.states_an_object_rule (salesagent-j3k2l.58)",
                kind=Kind.DEFERRED,
            )
        raise Refusal(
            min(keys) if keys else "allOf",
            where,
            "this step lowers a $ref conjunct (a base) or an inline conjunct whose parts "
            "are properties, required, rule keywords, an additionalProperties identity "
            "and a nested allOf; a later row lowers this one",
            kind=Kind.DEFERRED,
        )

    stated = rules_at(doc, *conjunct_rules, position=position)

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
    for key, node in local.items():
        if key not in inherited:
            own[key] = node
            continue
        verdict = _restatement(node, inherited[key], mod.resolve_node)
        if verdict is None:
            raise Refusal(
                _disagreeing(node, inherited[key]),
                at[key],
                f"the restatement of {key!r} neither matches nor narrows the "
                f"inherited declaration: inherited states {sorted(_constraining(inherited[key]))}, "
                f"this states {sorted(_constraining(node))}",
                kind=Kind.VERDICT,
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
            # The INTERSECTION where it NARROWS (section 2, :func:`_intersection`), and the node
            # itself where only the requiredness moved: there the content is the base's
            # already, so there is nothing of the base's to merge back in.
            own[key] = (
                _intersection(node, inherited[key], mod.resolve_node) if verdict else node
            )
            if _constraining(own[key]).get("uniqueItems") is True and not _constraining(
                node
            ).get("uniqueItems"):
                inherited_distinct.add(key)
        elif _annotates_differently(node, inherited[key]):
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
            own[key] = _intersection(node, inherited[key], mod.resolve_node)
            if not _constraining(node):
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
                reuse[key] = _reused(key, inherited_fields, inherited_from, at[key], mod)
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
        reuse[key] = _reused(
            key, inherited_fields, inherited_from, f"{pointer}/properties/{key}", mod
        )
        own[key] = dict(inherited[key])

    decided = fields(
        own,
        required | (inherited_required & set(own)),
        pointer,
        name,
        mod,
        inherited=set(inherited),
        declared_at=at,
        # D6 has claimed the ``uniqueItems`` of these keys, whether the node stating
        # it is this one or a rule-bearing conjunct: the rule tuple and the strip are
        # two halves of one claim, so the row that writes the tuple passes the keys.
        distinct=(*stated.distinct, *sorted(inherited_distinct - set(stated.distinct))),
        reuse=reuse,
    )
    return declare_object(
        # §6's description-authority rule, clause 3, at a CLASS: this node's own
        # description where it states one, and the base's where it is silent.  The
        # composed document states the base's at this pointer -- ``harness._composed``
        # folds it in -- and pydantic will not supply it, because ``cls.__doc__`` is
        # ``None`` for a subclass with no docstring.  Measured: 5 ``missing`` facts over
        # 4 pairs, every one a bare ``/description`` at a composing node whose own
        # declaration has none (``core/collection-selection.json``'s items and
        # ``core/canonical-media-buy-action.json``'s three branches).
        doc if doc.get("description") or inherited_description is None else {**doc, "description": inherited_description},
        name,
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
        ),
        position,
        bases=(*bases, *conjunct_bases),
        rule_nodes=conjunct_rules,
    )


def _required(node: dict, pointer: str) -> list[str]:
    req = node.get("required", [])
    if not isinstance(req, list) or not all(isinstance(r, str) for r in req):
        raise Refusal(
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
) -> ir.Field:
    """The inherited field an annotation-only restatement re-states, importable here.

    A re-used type names symbols, and each one has to be IMPORTABLE from this module
    or the class is an undefined name at import.  The only module this row knows for
    the key is the one its ``$ref`` conjunct bound, so a symbol that module DECLARES
    is imported from it and anything else refuses by name.  The second case is a
    re-export -- the base merely imported the symbol itself -- and section 2's import
    rule is an import of a symbol the target declares; ``emit.emit``'s binder refuses
    the same shape for a fragment ``$ref``, with the same reasoning.

    Measured over this step's population: 3 keys re-use a field, all 3 on
    ``formats/canonical/_base.json`` -- ``experimental`` and ``v1_translatable`` name
    no symbol at all (``bool``), and ``slots`` names ``CanonicalFormatBaseSlotsItem``,
    which ``_base`` declares.  **0** re-use a type naming a re-exported symbol, so the
    refusal below fires on nothing today and is the loud answer when a document first
    reaches one.
    """
    held, source = inherited_fields.get(key), inherited_from.get(key)
    if held is None or source is None:
        raise Refusal(
            "properties",
            pointer,
            f"{key!r} restates an inherited declaration with nothing but annotations, "
            f"and the base declaring it recorded no decided field for it, so there is "
            f"no type to re-use and lowering the restatement alone would type it Any",
            kind=Kind.VERDICT,
        )
    wanted = ir.symbols(held.type)
    unplaceable = sorted(wanted - source.shape.declares) if source.shape else sorted(wanted)
    if unplaceable:
        raise Refusal(
            "properties",
            pointer,
            f"{key!r} re-uses the field of {source.symbol}, whose type names "
            f"{unplaceable} -- symbols that module imports rather than declares, so "
            f"importing them from it would be a re-export",
            kind=Kind.VERDICT,
        )
    mod.imports |= {(source.module, symbol) for symbol in wanted}
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
    if keyword in _BOUNDS:
        if isinstance(c, bool) or isinstance(b, bool):
            return False  # draft-04's boolean exclusiveMinimum: a different keyword
        if not isinstance(c, int | float) or not isinstance(b, int | float):
            return False
        return c >= b if _BOUNDS[keyword] > 0 else c <= b
    if keyword == "items":
        # An overlay under ``items``: the rule holds at any depth, and the
        # recursion is the rule rather than a second one.  A LIST-valued ``items`` is
        # draft-07's tuple form, where position matters and two different lists are not
        # ordered by this predicate -- so it falls through to False.
        return (
            isinstance(c, dict) and isinstance(b, dict) and _restatement(c, b, resolve) is not None
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
        if not _at_least_as_tight(kw, c[kw], b[kw], resolve):
            merged[kw] = b[kw]
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
    based = (
        {**_dereferenced(base, resolve), **base}
        if "$ref" in b and "$ref" not in merged
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
    be inherited.  It refuses because the arm has no site: re-measured after this rule
    landed, **3 of the 1,054 portable documents are refused by this predicate** --
    ``governance/check-governance-response.json``'s ``action_binding``,
    ``media-buy/get-media-buys-response.json``'s ``indicators`` and
    ``signals/get-signals-response.json``'s ``range`` -- and none of the three is a
    looser bound.  An arm for one would be a derivation matching nothing.

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
    if not all(_at_least_as_tight(k, c[k], b[k], resolve) for k in set(c) & set(b)):
        return None
    # It narrows when the INTERSECTION says more than the base does.  Asked of the
    # intersection and not of the child, because that is what the field carries: a
    # child restating a strict SUBSET of the base's keywords with the same values
    # intersects to the base itself, states no new fact, and is the inherited field
    # (``_annotates_differently`` then decides whether the annotations differ).
    return _as_enum(_constraining(_intersection(dc, db, resolve))) != b


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


def _disagreeing(child: dict, base: dict) -> str:
    """The keyword a refusal is reported on: the first the two do not agree about."""
    c, b = _constraining(child), _constraining(base)
    return min({k for k in set(c) | set(b) if c.get(k) != b.get(k)} or {"allOf"})


def bind_without_a_model(
    mod: Module, symbol: str, declaration: ir.AliasDecl | ir.EnumDecl
) -> str:
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
    mod.declare(
        symbol,
        "",
        ir.RootBinding(schema_ref(mod.document, ""), symbol, declaration),
    )
    return symbol


def _alias_for(symbol: str, node: dict, decided: Decided) -> ir.AliasDecl:
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
    description = node.get("description")
    return ir.AliasDecl(
        symbol,
        replace(decided.type, facts=decided.constraints, format=decided.format),
        description=description if isinstance(description, str) and description else None,
    )


def name_the_node(mod: Module, symbol: str, pointer: str, node: dict, decided: Decided) -> Decided:
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

    The name is the walk's own ``name_hint``, which is D3's nested rule (parent +
    ``pascal_case(property)``) already computed at the call site.  D3 says a name is an
    input to a lowering and is never computed inside one, so none is computed here.
    """
    mod.declare(symbol, pointer, _alias_for(symbol, node, decided))
    return Decided(ir.TypeRef(symbol, local=True))


def local_reference(mod: Module, pointer: str, at: str) -> Decided:
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
    if pointer in mod.declared:
        return Decided(ir.TypeRef(mod.declared[pointer], local=True))
    if pointer in mod.resolving:
        raise Refusal(
            "$ref",
            at,
            f"a local reference cycle: #{' -> #'.join([*mod.resolving, pointer])}",
            kind=Kind.VERDICT,
        )
    node = mod.local.get(pointer)
    if node is None:
        raise Refusal("$ref", at, f"#{pointer} names no node of this document", kind=Kind.VERDICT)
    key = pointer.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~")
    symbol = mod.root + class_name(key)
    mod.resolving.append(pointer)
    try:
        return decide(node, pointer, symbol, mod, Position.DEF)
    finally:
        mod.resolving.pop()


def declare_alias(mod: Module, symbol: str, doc: dict, decided: Decided) -> str:
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
    return bind_without_a_model(mod, symbol, _alias_for(symbol, doc, decided))
