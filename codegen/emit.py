"""The WALK: it reads a bundle document and decides what each node becomes.

The command is ``python -m codegen`` and it lives in ``codegen/__main__.py``,
which holds the argument parser and the refusal report and nothing else:

    python -m codegen --bundle schemas/cache/3.2 core/pagination-request.json

The committed tree is the same command over the steps' whole population, which is
derived from the bundle and never listed by hand.  The predicates it is the union of
live in ``tests/populations.py`` and ``tests/test_emit.py``'s ``population()`` is the
union -- ``docs/plan/architecture.md`` §5 puts them there ("the document-set predicates
a step's result was stated over are the tests' business and live under ``tests/``"), so
this package names no population and the one the tree is graded against is the one the
suite counts.

A document this command does not name is still emitted when a named one
REFERENCES it: a module cannot import a symbol from a module no run wrote, so
``emit`` walks ``$ref`` transitively and the run emits the closure.

**This module is the walk, and it decides; it writes no text at all.**
``docs/plan/rebuild-plan.md`` §1 puts the seam at the decision: the walk reads the
schema and decides what a node IS -- a class, a type, a field, a constraint, a
default, a name, what ``extra`` is -- and ``codegen.render`` takes that decision,
as ``codegen.ir``'s declarations, and hands it to ``datamodel-code-generator``'s
pydantic-v2 model layer, which writes the Python.  The generator's parser never runs.

**D13 divides the walk between this module and ``codegen.compiler``**, and the cut
is the layering rather than a taxonomy.  What is HERE is the RUN -- the dependency
closure, the per-document fold, the files and the report -- plus
:func:`_decide`, the ONE per-node dispatch, because the answer for an array, a
mapping or a multi-type node lives in a lowering.  There was a second dispatch beside
it, ``ROWS``, over a document's root KIND; ``docs/plan/architecture.md`` §14 step 5
deletes it, so a document is :func:`_decide` at ROOT and :func:`lower_document` adds
the module wrapper and nothing else (§5).  What is in ``compiler`` is everything a
lowering is handed: the field builder, the class declarer, the alias declarer, the
keyword screen, D3's name rules and the carriers.  The module TEXT -- the header, the
import block, the ``__all__`` -- is ``render.module``'s, because it is text (§7);
:func:`exported` stays here, because which names another module may ask for is a
decision about the bundle.

**The per-node decision used to be unreachable BY NAME from either of them, and
the entry-point module is what changed that.**  ``python -m codegen.emit`` executed
this file as ``__main__`` under ``runpy``, so any module that then reached
``codegen.emit`` by name held a SECOND module object -- a second dispatch table and a
second decider -- and the prohibition that prevented it cost three
callables carried on :class:`compiler.Module`, which is how a lowering decided a
child node and named a constraint.  ``codegen/__main__.py`` removes the reason: no
module of this compiler is ever bound as ``__main__``, so this module is imported
once, by name, on every path.  :func:`decide_type` is therefore reached through
``compiler.decide`` and :func:`name_the_constraint` through ``compiler.carried``,
and the context carries DATA rather than functions.  ``tests/test_import_rule.py``
is down to the two boundaries that are about design (§8, §9).

The bundle directory is an argument (D9) and there is no default, so no version
literal can enter this package.  The output path is a function of the document
path (D1): ``core/pagination-request.json`` ->
``src/adcp/types/_schemas/core/pagination_request.py``.  There is no module
table, and the path is private (P8), so it is never a contract.

**Each emitted class carries the schema it was generated from**, as a
``SchemaRef`` on ``__adcp_schema__`` (§2), and the run writes that document into
the package beside the module.  A root class names its document's root; a nested
class names its own node, because a nested class is a subschema and must grade
against that.  There is no binding table: the previous arrangement wrote one and
a separate adapter pointed the grader at a tree through it, and an adapter that
can be aimed can be aimed at the wrong tree.

This step lowers an object root with ``properties``, whose properties are
scalars (with their constraints and their format), nested objects, typeless, or
a ``$ref`` to another document; and a scalar root, as the ``Annotated`` alias
D2 gives it, because a reference TARGET is one.  A cross-document ``$ref``
becomes an IMPORT of the target's symbol (P2) -- the target declares its type
once and the referencing module names it, so no constraint of the target has a
second spelling to drift from.  Every other kind of node is a later step's row in D2, and a
document carrying one is REFUSED by name, pointer and keyword rather than emitted
approximately.  A refusal is the designed outcome of a keyword this emitter does
not lower: a model that quietly ignores a constraint is wider than its schema,
which is the defect class P3 exists to remove.

The emitter owns its own layout and writes no file twice (D8): there is no
formatter and no patch pass.  P7 is held by construction rather than tested:
``emit`` sorts its document set, ``render`` sorts the import set, and the JSON
artifacts are dumped with sorted keys, so the output is a function of
(bundle, document set, this package, the pinned compiler) and of nothing a
caller orders.  What a test CAN perturb is set iteration, and ``test_emit``
does, with two hash seeds.
"""

from __future__ import annotations

import functools
import json
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field, replace as dataclasses_replace
from pathlib import Path
from typing import Any

from adcp.types._base import Approximation
from codegen import bundle, compiler, harness, ir, render
from codegen.keywords import Position
from codegen import constraints as constraints_module
from codegen.compiler import (
    SCALAR,
    Decided,
    Module,
    Target,
    check_keywords,
    class_name,
    declare_alias,
)
from codegen.lower import const as lower_const
from codegen.lower import names as lower_names
from codegen.lower import enum as lower_enum
from codegen.lower import containers as lower_containers
from codegen.lower import rules as lower_rules
from codegen.lower import union as lower_union
from codegen import refusal
from codegen.refusal import BuildFailure, Kind, Refusal
from codegen.schema import nodes, parse as schema

#: Where a document's module lands, relative to the repository root.
TREE = Path("src") / "adcp" / "types" / "_schemas"
#: The import path of that tree, and of the hand-written base beside it.
PACKAGE = "adcp.types._schemas"

#: **The two file kinds the emitter writes, and so the only two :func:`write` will
#: delete.**  ``emit`` writes exactly these: a module per emitted document, the
#: document beside it, and an empty ``__init__.py`` per package -- which is why the
#: prune is bounded by suffix rather than deleting whatever a walk of the tree
#: finds.  Anything else under the tree is something no run of this emitter put
#: there, so the prune is not entitled to an opinion about it; a ``.pyc`` under
#: ``__pycache__`` is the case that exists today.
#:
#: Declared rather than derived from ``Emitted.files``, because a derived set has a
#: hole exactly where the prune matters most: a whole-population run that emitted
#: nothing would derive ``{".py"}`` from its lone ``__init__.py`` and silently leave
#: every stale document behind.
#: ``test_the_emitter_writes_only_the_file_kinds_the_prune_removes`` grades the
#: declaration against the committed tree, so it cannot drift from what ``emit``
#: produces.
EMITTED_SUFFIXES = frozenset({".py", ".json"})

# **``FORMAT_TYPES`` and ``URL_FORMATS`` are ``codegen/lower/scalars.py``'s now**, with
# ``_named_alias`` and ``name_the_constraint``.  They were here because the SCALAR TAIL of
# the per-node dispatch was, and section 14 step 5 makes each kind's row
# ``lower/<kind>.py``; nothing about any of them changed in the move.


def asserted_formats(doc: dict) -> frozenset[str]:
    """The formats the DOCUMENT'S OWN draft has an installed checker for.

    Derived, not listed: ``validator_for`` reads the draft off the document's
    ``$schema`` and ``FORMAT_CHECKER`` is that draft's own vocabulary, narrowed
    to what is installed.  Both halves of ``strict_validate`` assert through the
    same attribute, so the set this walk gates on and the set the runtime
    enforces are one set and cannot drift.
    """
    return frozenset(harness.validator_for(doc).FORMAT_CHECKER.checkers)

def module_path(document: str) -> str:
    """D1: the module is the document path with hyphens as underscores."""
    p = Path(document)
    return "/".join([*p.parent.parts, p.stem]).replace("-", "_")


def relative_module(frm: str, to: str) -> str:
    """D1 again: the import spelling is a function of the two document paths.

    ``error-details/creative-revision-content-mismatch.json`` referencing
    ``core/creative-revision-id.json`` imports from ``..core.creative_revision_id``:
    up to the nearest package both modules live under, then down.  No table, and
    nothing consults the tree -- a cross-document reference has one spelling and it
    is derived from the same two strings D1 derives the output paths from.

    Relative rather than absolute because ``_schemas`` is private (P8) and a
    relative import is the one spelling that cannot name it.  An absolute
    ``adcp.types._schemas.core...`` inside a generated module would publish the
    private path 690 times over.
    """
    src, dst = module_path(frm).split("/"), module_path(to).split("/")
    common = 0
    while common < len(src) - 1 and common < len(dst) - 1 and src[common] == dst[common]:
        common += 1
    return "." * (len(src) - common) + ".".join(dst[common:])


# --------------------------------------------------------------------------- #
# the walk: what each node IS
# --------------------------------------------------------------------------- #
# **``the_same_node`` and ``bind_the_same_node`` are ``codegen/lower/names.py``'s now**
# (§14 step 7): §4's content dedup is part of the naming pass, so the equality lookup
# (``names.same_node``) and the binding of a later position's own name to the first
# position's class (``names.adopt``) live beside §4's name rules and the stated SCOPE.
# What stays in the walk is the CALL, and it has to: a second occurrence's CHILDREN are
# never lowered, so a declaration the walk did not make has no name for a pass to
# derive, and the pruning is a decision about the walk.


def decide_type(
    node: nodes.Node, mod: Module, *, of_a_root_union: bool = False
) -> Decided | Refusal:
    """What one schema node IS, plus a SYMBOL where another document names the node.

    The decision is ``lower.decide.decide``'s, unchanged.  What is here is the two things a
    node reached by a fragment reference or by a second parent needs and a node
    reached once by its own parent does not: a name in this module, so the referring
    module imports a symbol rather than copying a schema (section 2's rule), and D3's
    content dedup.

    It wraps rather than living inside the dispatch because both apply to every arm
    equally -- an array, a scalar, a mapping and a multi-type node are all annotations
    with no name -- and §5 says the dispatch "contains no decision beyond the route", so
    the two tests sit outside it.  §14 step 7 moves both into ``lower/names.py`` as a pass
    over the finished module.  A class or an enumeration comes
    back ``local`` already, having declared itself under this very ``name_hint``, so
    nothing is named twice and no second symbol appears for one node.

    ``mod.named`` is a function of the BUNDLE (``bundle.named_nodes``), not of the
    run's document set, so whether a node gets a name does not depend on who else was
    emitted.

    **D3: nodes with identical content are one node.**  The memo is consulted BEFORE
    ``_decide`` and seeded after it, so the second occurrence of a node decides to the
    symbol the first DECLARED and no second class is written for it.  Three things
    make that the whole of the rule rather than an optimisation:

    * The memo is seeded only where the walk declared a symbol AT THIS NODE'S OWN
      POINTER (``mod.declared.get(pointer)``), which is exactly D2's class and
      enumeration rows and :func:`compiler.name_the_node`'s alias.  An annotation
      declares nothing, so an identical annotation is simply decided again -- to the
      same annotation, since the inputs are the same string -- and a ``$ref`` whose
      symbol this module IMPORTED is not seeded either, because the import is already
      in ``mod.imports`` and section 2's rule is an import of a symbol the TARGET
      declares.  A node that declares a symbol at its pointer and then decides to a
      CONTAINER over it is therefore not seeded; a nested union is the shape that would
      be, and it is covered anyway because its BRANCHES collapse through this very
      wrapper and two identical branch lists then decide to one annotation.  0 such
      pairs survive the run, and clause 1 of the check reddens by name if one appears.
    * **The CLASS is declared at the node's first position in the document's own key
      order, and every other position derives its own name and binds the same class**
      (:func:`bind_the_same_node`).  D3 derives a name PER POSITION, so a node at two
      positions has two derivations and no rule in the plan picks between them -- and it
      does not have to, because the dedup is about classes and a name bound to a class is
      not a second class.  Measured first, because the three readings that would need one
      name are all unavailable: naming the node from its own content is what D5 bans for
      an alias ("an alias names a constraint, never a concept") and for an enumeration the
      content is a member list rather than a name; naming it from the bundle reaches
      nothing, since 0 of the 1,271 identical-content groups have a bundle ROOT carrying
      that content; and refusing the document loses a class the bundle can state.
      ``tests/test_emit.py`` asserts that each position declares its OWN name and that
      every name in a group binds ONE object, so a flip in walk order reddens instead of
      renaming a public symbol.
    * **The adopting pointer IS declared**, under its own name, so a cross-document
      ``$ref`` naming the second position resolves to it -- ``emit.exported`` lists the
      symbol at every bundle-named pointer, so the import side and the export side still
      read one fact.  Before the alias this arm refused DEFERRED instead; 0 of the
      collapsed pointers are among the bundle's 216 named nodes, so the change closes a
      ceiling nothing reaches rather than moving a refusal.
    """
    from codegen.lower.decide import decide

    pointer = node.pointer
    collapsed = lower_names.same_node(mod, node)
    if collapsed is not None:
        mod.adopted[pointer] = collapsed
        bound = lower_names.adopt(mod, pointer, collapsed)
        return bound if isinstance(bound, Refusal) else Decided(bound)
    decided = decide(node, mod, of_a_root_union=of_a_root_union)
    if isinstance(decided, Refusal):
        return decided
    if pointer in mod.named and not decided.type.local:
        named = compiler.name_the_node(mod, pointer, node, decided)
        if isinstance(named, Refusal):
            return named
        decided = named
    if decided.type.local and decided.type.path == pointer:
        mod.collapsed.append((node, pointer))
    return decided


def _local_symbols(t: ir.TypeRef) -> set[str]:
    """Every symbol of the DECLARING module that one decided type names.

    A local bare symbol is this pipeline's own class or alias (``ir.TypeRef``), and
    a container carries its members in ``of`` with a mapping's key beside them -- so
    ``list[CanonicalFormatBaseSlotsItem] | None`` reaches the item through two levels
    and neither can be read off ``path``.
    """
    out = {t.path} if t.local and t.path.isidentifier() else set()
    for inner in (*t.of, *( (t.key,) if t.key is not None else () )):
        out |= _local_symbols(inner)
    return out


def exported(
    mod: Module, named: ir.Module, composed: frozenset[str] = frozenset()
) -> list[str]:
    """The names the module declares that another module can ask it for: the root, the
    symbol at every pointer the BUNDLE names, and the field types of a class the bundle
    COMPOSES.

    **The import side and the export side read the same facts, so the emitter cannot
    disagree with itself about a module's public surface.**  The binder above resolves a
    fragment reference to ``mod.declared[into]`` -- section 2's rule is an import of a
    symbol the target DECLARES -- while this list used to be the root alone, and the
    tree then held 16 imports of a symbol the target module declared and did not export.
    Nothing raised, because Python does not consult ``__all__`` on import; the
    disagreement was about what the module says it offers.

    **A symbol crosses a module boundary in exactly two ways, and this list is the union
    of both.**  That is what makes it closed by CONSTRUCTION rather than by today's
    population, and the second way was found by salesagent-j3k2l.36 landing while the
    first was being fixed:

    1. **The binder answers a ``$ref`` fragment.**  ``bundle.named_nodes`` is computed
       from every ``$ref`` in the bundle and the binder only ever asks for a pointer that
       came from one, so what it can ask for is always in ``mod.named``.
    2. **A composing subclass RE-USES a base's decided field.**  Under ``allOf`` a
       subclass inherits the base's fields and may restate one, and the plan's
       description-authority clause 2 says a restatement is then the base's FIELD wearing
       this document's annotations -- so the base's own field TYPES cross into every
       module that composes it (``compiler.lower_composition``'s ``inherited_fields``, read off
       ``Target.shape.decided``).  ``formats/canonical/_base.py``'s
       ``CanonicalFormatBaseSlotsItem`` is one: 7 modules import it and no ``$ref``
       names it.  Re-deciding the base's node instead was measured and is wrong -- it
       declares a second ``...SlotsItem`` at a pointer the subclass's document does not
       have -- so the import is the plan's answer and the export has to match it.

    ``composed`` is the pointers some document's root ``allOf`` names in this one,
    ``#`` for a bare conjunct (257 of the bundle's 258) and the fragment for the one that
    carries one.  A Target is minted for the root or a named node and for nothing else,
    so no OTHER class's fields can cross, and ONE restatement is as deep as it goes: a
    subclass restates a key the base declares, and a field of a nested item is not a key
    of the subclass.

    **Every declared symbol would be wider than the demand and wrong about why.**
    Measured on the committed tree: the rule above is 717 names with 24 of 677 modules
    exporting more than one, and it meets the demand exactly -- every symbol the tree
    imports is in it.  Every declared symbol is 1,314 names over 228 modules, and the
    extra 597 are nested classes nothing can ask for, reached through their parent's own
    annotation.  Taking the annotations of EVERY root rather than a composed one is 1,053
    over 194, which is barely narrower and discriminates on nothing.

    The root goes FIRST, not sorted in with the rest: a reader wants the document's own
    class at the head of the list, and ``tests/test_emit.py`` reads the root off
    ``__all__``.
    """
    symbols = named.symbols
    declared = set(symbols.values())
    rest = {symbols[p] for p in mod.named if p in symbols}
    for pointer in composed:
        shape = mod.shapes.get(pointer)
        if shape is None:
            continue
        rest |= {
            name
            for prop in shape.decided.values()
            # The shape was recorded DURING the walk, so its decided fields name local
            # declarations by pointer; the symbol table is what binds them (§7).
            for name in _local_symbols(lower_names.resolved(prop.type, symbols))
            if name in declared
        }
    return [named.root, *sorted(rest - {named.root})]


# --------------------------------------------------------------------------- #
# **the dispatch table is GONE, and the one path is what replaced it**
# --------------------------------------------------------------------------- #
# ``ROWS`` was six ``(selector, lowering)`` pairs over a document's ROOT KIND, with
# ``bundle``'s six root selectors as the selectors and six wrappers here as the
# lowerings.  ``docs/plan/architecture.md`` §5 deletes it in one sentence: **"Root and
# non-root are one path.  There is no second table of root selectors.  A document is
# ``parse(raw, position=ROOT)`` followed by ``decide``.  The only thing ROOT adds is the
# module wrapper."**  §11's repetition table says the same thing as a repetition -- "the
# kind read in ``_decide``, in the root selectors, in ``union.keyword``, in
# ``rules.presence_only`` | ``parse``'s classification" -- so the table was the second
# reading of the kind, and the six wrappers were the ROOT cell of six arms :func:`_decide`
# already had.
#
# Where each row went, and every one of them is a cell at a POSITION rather than a row:
#
# * ``is_object_root`` -> :func:`_decide`'s ``type: object`` arm, plus its typeless arm
#   at ROOT for the ``properties``-with-no-``type`` shape the selector also claimed;
# * ``is_scalar_root`` and ``is_container_root``'s mapping and multi-type halves -> the
#   arms themselves, with the MODULE WRAPPER below.  §5 names it: "a root whose lowering
#   is an alias or an enumeration gets a ``RootBinding`` declaration from
#   ``lower_document``, which is the one function that knows a root is a root";
# * ``is_container_root``'s array half -> ``lower.containers.array`` at ROOT, which is
#   where D2's ``RootModel[list[X]]`` row is refused now;
# * ``is_enum_root`` -> the ``enum`` arm, with the wrapper below;
# * ``composes_at_the_root`` -> the ``allOf`` arm, which already took the position;
# * ``union_root`` -> the union arm at ROOT.
#
# What ``AmbiguousRoot`` guarded is unrepresentable rather than unchecked: a dispatch on
# a node's KIND reaches exactly one arm, so there is no table for two selectors to claim
# one document in.  It was a BUILD FAILURE, and a build failure with no way to occur is
# not a check that was dropped.
#
# ``ROOT_KIND`` goes with them.  It was "the order an UNCLAIMED root is reported by", and
# an unclaimed root is what no longer exists: a root reaches an arm, and the arm names the
# keyword.  The two shapes §4's table gives a root no row for say so at their own
# position -- a bare ``$ref`` root in the reference arm, and a root stating no kind in the
# typeless arm.

def lower_document(
    document: str,
    doc: dict,
    targets: Mapping[tuple[str, str], Target | Refusal] | None = None,
    named: frozenset[str] = frozenset(),
    roots: Mapping[str, dict] | None = None,
    reserved: frozenset[str] = frozenset(),
    asked: set[tuple[str, str]] | None = None,
) -> tuple[Module, str] | Refusal:
    """One document's module and root symbol, or the refusal the walk returned.

    **This is where §6's "a document refused by a child's refusal produces NO
    declarations at all" is held, and the TYPE is what holds it.**  The walk hands this
    function one value: a decision, or a refusal.  On a refusal there is no ``(Module,
    str)`` to hand the run, so the partially-populated module cannot be written -- the
    partial model §2 of the semantics document forbids is not something a caller could
    reach for and then decide not to use, because the two answers are different types
    and nothing holds both.
    """
    mod = Module(
        document=document,
        # §5's ``targets``, as DATA: the run resolved every reference site of this
        # document before parsing it, in the dependency order §10 computes, so a
        # cross-document reference is a lookup and never a callback.
        targets=targets if targets is not None else {},
        roots=roots if roots is not None else {},
        reserved=reserved,
        # The run's own record of which sites this walk asked about, handed IN so that
        # it survives a refusal: a document that refuses has no module to hand back, and
        # the sites it reached before refusing are what decide whether their targets are
        # documents this run owes (:attr:`compiler.Module.asked`).
        asked=asked if asked is not None else set(),
        asserted=asserted_formats(doc),
        named=named,
        # The SUBSCHEMA behind each named pointer, read off ``bundle.nodes`` -- the one
        # schema-position walk ``bundle.named_nodes`` itself read the references off, so
        # the pointer spelling (``~0``/``~1`` in a key included) is produced once and a
        # local reference cannot miss a node because two walks escaped a key
        # differently.  Keyed by pointer and narrowed to ``named``, which is what says
        # this is for resolving a reference and not a general index of the document:
        # a node nothing names needs no entry, and 11 of this bundle's 157 local-section
        # entries are in that position (``compiler.local_reference``).
        local={p: n for p, n in bundle.nodes(doc) if p in named},

        object_constrained=bundle.constrained_to_object(doc),
    )
    # **ONE PATH, and it is now §5's sentence verbatim: "A document is ``parse(raw,
    # position=ROOT)`` followed by ``decide``."**  The second dispatch on a root's KIND
    # went in part two; the parser is what this commit adds, so the raw document is read
    # ONCE, here, into a node tree, and the dispatch routes the root node by its kind.
    #
    # :func:`decide` and not :func:`decide_type`, and the difference is the two things a
    # ROOT does not have.  ``mod.named`` never holds the root's pointer
    # (``bundle.named_nodes`` skips a reference with no fragment), so there is nothing for
    # :func:`compiler.name_the_node` to name; and the CONTENT MEMO is empty at the root and
    # would be SEEDED with the whole document's content by the wrapper -- which §7 moves
    # into ``lower/names.py`` as a pass over the finished module anyway.  So the wrapper's
    # two jobs are both absent here and calling it would add one: a nested node of content
    # identical to the document root would adopt the root's own symbol.
    from codegen.lower.decide import decide

    root = schema.parse(doc, pointer="", position=Position.ROOT, source=mod.source)
    # **The module's SYMBOL is read off the root NODE**, and that is the last reading this
    # function made of the raw mapping: §4 makes ``codegen/schema/parse.py`` the one
    # function that reads one, and ``title`` at ROOT is a NAME cell, so the parser puts it
    # in :attr:`nodes.Base.annotations` and :attr:`nodes.Base.title` is the reading.  The
    # module is therefore built before the symbol is known and ``mod.root`` is written
    # after it: nothing between the two reads it -- ``parse`` does not, and
    # ``compiler.local_reference``, which does, runs inside ``decide`` below.
    title = root.title
    if title is None:
        return Refusal(
            "title",
            "",
            "the document declares no title to derive a name from",
            kind=Kind.VERDICT,
        )
    symbol = class_name(title)
    if not symbol.isidentifier():
        return Refusal(
            "title",
            "",
            f"the title {title!r} derives {symbol!r}, not an identifier",
            kind=Kind.VERDICT,
        )
    mod.root = symbol
    # **§4's ROOT rule as a HOP**, and the root's is the only hop no parent records: the
    # document has no enclosing node to hang off, so the title is the fact and
    # ``lower/names.py`` is what applies ``pascal_case`` to it.  The identifier check
    # stays here because it is a check on the DOCUMENT and the refusal is the document's
    # -- and because every derived name is a concatenation onto this one, so the proof
    # that a nested name is an identifier rests on it (``compiler.local_reference``).
    mod.hops[""] = lower_names.Root(title)
    decided = decide(root, mod)
    if isinstance(decided, Refusal):
        # §6, returned upward unchanged: the refusal names the innermost node that
        # carried the keyword, and this function adds nothing to it.  The module it was
        # building is dropped with it -- no declaration of a refused document is written,
        # which is §2's "a partial model is worse than none" made unrepresentable rather
        # than merely avoided.
        return decided

    # **THE MODULE WRAPPER, which is the only thing ROOT adds** (§5).  A class carries
    # ``strict_validate`` by inheritance, so a root the dispatch declared under this
    # module's own symbol is finished.  The two root shapes with no class are the ones
    # §5 names, and both bind the same two module-level statements through
    # ``ir.RootBinding``:
    #
    # * an ENUMERATION.  The ``enum`` arm declared the ``ir.EnumDecl`` itself, because
    #   that is what the arm answers at every position; the ROOT wrapper is what puts the
    #   binding around it.  ``Enum.jinja2`` has no ``class_body_lines`` slot, so the
    #   reference cannot be written into the class (D9 forbids writing one in
    #   afterwards) and the statements go beside it.
    # * an ALIAS.  A scalar, a mapping and a multi-type root have no field to hang
    #   themselves on, and a wrapper class would be a second name for the same node (P2).
    #   ``compiler.declare_alias`` is the one spelling of those statements and it is what
    #   the deleted ``_scalar_root`` and ``containers.root`` both called.
    #
    # A class, an alias and an enumeration therefore cannot come to answer differently
    # about what their own document accepts, which is what put the two statements in one
    # declaration in the first place.
    if "" not in mod.at:
        bound = declare_alias(mod, "", root, decided)
        if isinstance(bound, Refusal):
            return bound
        return mod, symbol
    # The declaration travels WITH its index, so the ``isinstance`` that found it is
    # what the wrapper is handed: re-reading ``mod.declarations[held]`` is a second read
    # of one slot, and a reader -- the type checker included -- cannot tell that the two
    # reads see one object.  :class:`codegen.ir.RootBinding` takes an alias or an
    # enumeration and nothing else, which is the fact the single read carries.
    held = next(
        (
            (i, d)
            for i, d in enumerate(mod.declarations)
            if isinstance(d, ir.EnumDecl) and d.name == ""
        ),
        None,
    )
    if held is not None:
        at, enumeration = held
        mod.declarations[at] = ir.RootBinding(
            compiler.schema_ref(document, ""), "", enumeration
        )
        mod.at[""] = mod.declarations[at]
    return mod, symbol


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
@dataclass
class Emitted:
    files: dict[str, str] = field(default_factory=dict)  # path -> text
    #: Files written BESIDE the tree, in the package the tree lives in, keyed by a
    #: path relative to THAT directory.  D5's alias module is the whole population:
    #: an alias belongs to no document, so it has no domain and cannot live under
    #: ``_schemas/<domain>/``, and it is PUBLIC -- ``adcp.types.constraints`` is the
    #: one path a consumer reaches an alias at -- so it cannot live inside the
    #: private tree either.  A second dict rather than a ``..`` key in
    #: :attr:`files`, so no caller of :func:`write` can be handed a path that
    #: escapes the directory it passed.
    beside: dict[str, str] = field(default_factory=dict)
    #: document -> the module it was written to.  The run's own record of what it
    #: emitted, for the refusal arithmetic and the CLI report.  It is NOT a
    #: binding table and nothing reads it at runtime: a class finds its schema
    #: through its own ``__adcp_schema__``.
    emitted: dict[str, str] = field(default_factory=dict)
    refusals: dict[str, dict[str, str]] = field(default_factory=dict)
    #: document -> ``Module.declared``, which is pointer -> the symbol declared for the
    #: node at it.  The run's own record of WHERE each symbol came from, and the only
    #: thing D3's content dedup can be graded over: the question "do two declared
    #: symbols name nodes of identical content" is asked of pointers, and the emitted
    #: TEXT has none -- a reader of the module sees two class statements and cannot say
    #: which node each one lowered.  Written from the one map every declaration passes
    #: through (:meth:`Module.declare`), so the check and the collapse read one record
    #: and cannot disagree about what was declared.
    declared: dict[str, dict[str, str]] = field(default_factory=dict)
    #: document -> ``Module.adopted``: pointer -> the symbol the node at it adopted under
    #: D3's content dedup, because an earlier node of identical content declared it.
    #: With :attr:`declared` this is the whole of what the dedup did, and it is what
    #: ``tests/test_emit.py`` grades it over -- in both directions, since an adoption
    #: whose two nodes are NOT identical is the failure that matters more than a missed
    #: collapse.
    adopted: dict[str, dict[str, str]] = field(default_factory=dict)
    #: Section 5's ``default`` row, the REPORTED half: ``document -> {pointer -> the
    #: value dropped}``, for a default the document states on a REQUIRED property.
    #: Dropping it changes no accepted set -- the key is in every admitted instance,
    #: so the default can never apply -- but a fact the emitter discards in silence is
    #: the one defect nothing else here catches, so it leaves the run by name and
    #: pointer.  A document with no such default has no entry, so the mapping names
    #: exactly the drops rather than every document emitted.
    drops: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: document -> ``Module.carries_nothing``: what the document states at a pointer and
    #: the class carries nothing for, because the name asserts nothing about any
    #: instance.  A document with one still EMITS, so this is not part of the partition
    #: and is not counted anywhere -- it is the report section 7's ``errorMessage`` row
    #: asks for, and the CLI prints it beside the refusals.
    #:
    #: Separate from :attr:`drops` for the reason
    #: :attr:`compiler.Module.carries_nothing` states: two channels, two names.
    carries_nothing: dict[str, list[str]] = field(default_factory=dict)
    #: document -> §2's approximations for it, in document order.  A THIRD channel beside
    #: :attr:`drops` and :attr:`carries_nothing`, and §10 forbids printing it with either:
    #: "a carries-nothing line says a keyword constrained nothing, and an approximation
    #: says a keyword constrained something the annotation does not carry.  Printing them
    #: in one list would sum two different things."
    #:
    #: A document with none has no entry, so the mapping names exactly the documents
    #: carrying one -- which is §10's ``D``, a different figure over a different
    #: denominator from the ``K`` facts, and the report never adds them.
    #:
    #: **This is the report's copy and not the grader's.**  §9 forbids the verifier the
    #: walk, so what the GRADER reads is ``__adcp_approximations__`` off the emitted class
    #: (§7); this is the same data on the run's own channel, for the three figures the CLI
    #: prints.  A disagreement between the two is a defect in ``render`` and
    #: ``tests/test_approximation.py`` is where it is caught.
    approximations: dict[str, list[Approximation]] = field(default_factory=dict)


# **``_composed_nodes`` is ``bundle.composed`` now**, and the move is §11's row for it:
# the pointers another document's root ``allOf`` composes are a fact about the bundle's
# reference GRAPH, which §11 gives to the layer that knows "files, paths, ``$ref`` URIs,
# edges, the record".  It also read every portable document a SECOND time, after
# ``named_nodes``'s own pass, and the merge of the two scans its docstring named as the
# upgrade path is ``bundle.edges``: both readings are projections of ONE scan now.


def _bound_shape(shape: compiler.Shape, symbols: Mapping[str, str]) -> compiler.Shape:
    """One :class:`compiler.Shape` with every symbol it carries bound by the declaring
    module's own table.

    A shape is recorded during the walk, where a local declaration is a POINTER (§7), and
    it is read by ANOTHER document -- a composing row's re-used field, and the set of
    symbols that row may import from the base.  The target was named before this document
    was parsed (§10's order), so the binding is a lookup and never a second derivation.
    """
    return dataclasses_replace(
        shape,
        decided={
            key: dataclasses_replace(f, type=lower_names.resolved(f.type, symbols))
            for key, f in shape.decided.items()
        },
        declares=frozenset(symbols[p] for p in shape.declares if p in symbols),
    )


def closure(documents: Collection[str], sites: Mapping[str, Sequence[bundle.Edge]]) -> list[str]:
    """``documents`` and every document one of them references, transitively.

    §10: "takes the transitive closure of the named documents over them (a module cannot
    import from a module no run wrote)".  Over the EDGES and not over the walk: the
    closure is computed before any document is parsed, which is what lets the run order
    it and hand each document its targets as data instead of calling back into itself
    from inside a lowering.

    Sorted, so the run is order-independent (P7).  A site whose URI names no document of
    this bundle contributes nothing here and refuses at the site, which is where the
    pointer that carried it is.
    """
    out: set[str] = set()
    unread = sorted(set(documents))
    while unread:
        document = unread.pop()
        if document in out:
            continue
        out.add(document)
        unread += [
            edge.target
            for edge in sites.get(document, ())
            if edge.target is not None and edge.target not in out
        ]
    return sorted(out)


def order(
    documents: Sequence[str], sites: Mapping[str, Sequence[bundle.Edge]]
) -> tuple[list[str], dict[str, Refusal]]:
    """``documents`` ordered so every document follows the documents it references, and
    the refusal for each document on a reference CYCLE.

    §10's second sentence, and §2's reason for it: "the run's own state -- which
    documents are lowered, which refused -- is a fold in ``emit.py`` over a dependency
    order computed before any document is lowered, so no handler ever calls back into
    the run."  The order is what makes ``ctx.targets`` possible at all: a document's
    targets are finished modules by the time it is parsed.

    **A cycle is a VERDICT for every document ON it**, which is the answer the in-flight
    stack gave one document at a time: two modules importing each other's symbol at
    module scope is an ``ImportError``, not a type.  Measured over the 1,054 portable
    documents: 3,124 cross-document edges and **0 cycles**, so this is the rule rather
    than a measurement -- and a document that merely REFERENCES a cycle is not on it and
    refuses through the chain, as it does for any refused target.

    Depth-first in sorted order, so the order is a function of the bundle and of the
    document set and of nothing a caller iterates (P7).
    """
    ready: list[str] = []
    cycles: dict[str, Refusal] = {}
    held = set(documents)
    #: ``None`` not yet reached, ``False`` in flight, ``True`` finished -- the three
    #: colours a cycle check needs, as data rather than as two sets.
    done: dict[str, bool] = {}

    def visit(document: str, stack: list[str]) -> None:
        if done.get(document) is True:
            return
        if done.get(document) is False:
            on = [*stack[stack.index(document):], document]
            for member in on[:-1]:
                cycles.setdefault(
                    member,
                    Refusal(
                        "$ref",
                        "",
                        f"a reference cycle: {' -> '.join(on)}",
                        kind=Kind.VERDICT,
                    ),
                )
            return
        done[document] = False
        stack.append(document)
        for edge in sites.get(document, ()):
            if edge.target is not None and edge.target in held:
                visit(edge.target, stack)
        stack.pop()
        done[document] = True
        ready.append(document)

    for document in sorted(held):
        visit(document, [])
    return [d for d in ready if d not in cycles], cycles


def decidable(
    bundle_dir: Path,
    document: str,
    doc: dict,
    targets: Mapping[tuple[str, str], Target | Refusal],
    named: frozenset[str],
    roots: Mapping[str, dict],
    reserved: frozenset[str],
    asked: set[tuple[str, str]],
) -> tuple[Module, ir.Module] | Refusal:
    """One document lowered, NAMED, and its carried record checked, as one value.

    **The naming pass runs here** (§7, §14 step 7): ``lower/names.py`` takes the module
    the walk built -- declarations keyed by pointer, every local type naming one by
    pointer -- and returns :class:`codegen.ir.Module` with §4's symbol table bound.  It
    is one call and it is the only place a symbol of this module is decided.

    Split out of the fold so that the lowering and the two checks each read in one
    place, and what this returns is the document's whole outcome.  It was the body of a
    ``try``/``except Refusal``/``finally``, which is what §2 retires, and then the body
    of a memoising closure, which is what §14 step 7's dependency order retires: a
    document is lowered once, when the order reaches it, so there is no memo to consult
    and no in-flight stack to push.
    """
    outcome = lower_document(document, doc, targets, named, roots, reserved, asked)
    if isinstance(outcome, Refusal):
        return outcome
    mod, _ = outcome
    bound = lower_names.assign(mod)
    if isinstance(bound, Refusal):
        # §4's two naming refusals, both VERDICTS of the document: two pointers deriving
        # one class name, and a branch with no identity.  Returned from here because this
        # is where every other refusal of a document is recorded.
        return bound
    # **The document the package will carry has to be DECIDABLE, and that is
    # checked here because a refusal belongs where every other one is.**  A
    # ``$ref`` at a position the package's own validation reaches is a schema
    # nothing local can decide, so ``jsonschema`` fetches the target over the
    # network; the write loop below says what that costs.  ``bundle.record``
    # is the one resolution, and what survives it is a LOCAL reference: it
    # inlines every cross-document ``$ref``, at every position the table's
    # descent column reaches, which includes a ``definitions``/``$defs`` entry.
    #
    # **WHICH OF THOSE SURVIVORS IS A DEFECT IS DECIDED BY DECLARATION, AND
    # ``bundle.undecidable_references`` IS THE PREDICATE.**  Section 5 makes a
    # section "nothing by itself", each entry "declared on demand when a
    # ``$ref`` names it", and section 3 adds "an entry nothing references is
    # not declared" -- which ``compiler.local_reference`` already reads: an entry is
    # declared only where a reference names it, so a dead one is not.  So a reference inside an entry
    # nothing names is at a position no class grades and no enclosing node's
    # assertions descend into, while a reference inside an entry a ``$ref``
    # DOES name is owed resolution, because a class is declared at that
    # pointer and validates through it.
    #
    # This check read "the document holds an absolute ``$ref``" and refused
    # both alike, with the note that narrowing it would be "a check relaxed to
    # fit".  The narrowing is not to reachability-as-observed-today, which is
    # what that note refuses and rightly: it is to the on-demand DECLARATION
    # set the emitter is already handed, so what is admitted is exactly what
    # section 3 says is never declared.  Measured: ``a2ui/si-catalog.json``'s
    # carried document decides with the network removed -- with
    # ``socket.socket`` replaced by a constructor that raises, ``jsonschema``
    # accepts ``{"catalogId": "si-standard", "components": ["Text"]}`` and
    # refuses ``{"catalogId": "other"}``, ``{"components": "Text"}`` and
    # ``{"catalogId": 1}`` on ``const`` and ``type`` -- so refusing it was
    # refusing a document that IS locally decidable.  Of the bundle's 101
    # remote references under a section, 77 in 18 documents sit in a named
    # entry and are still counted; those 24 are the whole of what this admits.
    #
    # A LOCAL reference is decidable at every position and is counted at none:
    # it names a node of the very document the package carries, so
    # ``jsonschema`` resolves it against the referrer and fetches nothing.
    #
    # **0 SITES SINCE ``bundle.record`` BECAME THIS PACKAGE'S OWN INLINER, and
    # the check is kept as the guard that says so.**  The record inlines every
    # cross-document reference the descent column reaches, sections included, so
    # the only reference left in one is local and this predicate selects none.
    # ``core/requirements/catalog-field-binding.json`` was the one document it
    # refused -- a reference at ``/definitions/ScalarBinding/properties/ext``,
    # inside an entry a ``$ref`` names, which the delegated resolver did not
    # descend to -- and that is an emission delta of this row and not a check
    # relaxed to fit: nothing here is narrower, the record is wider.  Firing
    # again would mean ``record`` left a reference at a position the package's
    # own validation decides through, which is a defect in the inliner.
    rec = bundle.record(bundle_dir, document)
    if isinstance(rec, Refusal):
        # §4: a reference whose target is not a bundle document, and a
        # cross-document cycle, make the record undefined for this document.
        # The refusal is the one ``record`` minted, RETURNED from here because this
        # is where every other refusal of a document is recorded.  ``bundle.record``
        # is the precedent §3 names for a verdict a document earns on its own terms:
        # it returned a refusal as a value before this row, and every other producer
        # now does the same.
        return rec
    unresolved = bundle.undecidable_references(rec, named)
    if unresolved:
        pointer, uri = unresolved[0]
        # **NO KIND IS MINTED HERE, because §3 retires the one this had.**
        # ``Kind.UNRESOLVED`` "named a reference the delegated resolver did not
        # reach, and the resolver in §4 reaches every position" -- and the comment
        # above says what firing means now that ``bundle.record`` IS that resolver:
        # "a defect in the inliner".  Two readings inside this compiler then
        # disagree about which positions validation reaches, which is a property of
        # the COMPILER and not of any document, so §2's rule applies and it is a
        # :class:`codegen.refusal.BuildFailure` that no layer catches.  Measured
        # over the 1,054 portable documents at ``d048658``: ``unresolved`` is 0 and
        # the kind was carried by no refusal, so nothing moves.
        raise BuildFailure(
            f"{document}: {uri} at {pointer or '/'} {refusal.UNRESOLVED_TARGET}, at a "
            f"position the package's own validation decides through ({len(unresolved)} "
            "here): bundle.record inlines every cross-document reference the descent "
            "column reaches, so a survivor is the inliner and "
            "bundle.undecidable_references disagreeing about which positions validation "
            "reaches -- a defect in this compiler and not an outcome of this document"
        )
    return mod, bound


def emit(bundle_dir: Path, documents: list[str]) -> Emitted:
    """Lower every named document, and every document one of them references.

    **A FOLD OVER A DEPENDENCY ORDER** (§10), which is what replaced the recursive
    binder: ``bundle.edges`` is the reference graph, :func:`closure` is the set a run
    must write (a module cannot import a symbol from a module no run wrote),
    :func:`order` sorts it so every document follows the documents it references, and
    each document is then handed its TARGETS as data.  The walk is over ``$ref``
    strings and nothing else -- an import edge is ``(referencing path, target path)``,
    which is what D1 already derives a module path from -- so there is no resolution
    here and no node graph.  Resolution does the OPPOSITE of what an import needs: it
    substitutes the target's contents for the reference, leaving nothing to emit an
    import from.

    Sorted at every step, so the run is order-independent (P7).  Nothing is memoised
    and nothing is in flight: a document is lowered once, when the order reaches it,
    and a target is a finished module by then.
    """
    out = Emitted()
    packages: set[str] = set()
    known = set(bundle.portable(bundle_dir))
    # **ONE SCAN of the bundle, and three readings of it** (``bundle.edges``): the
    # per-document ``named`` set, the pointers a root ``allOf`` composes, and the
    # reference graph the order is computed over.  Read from the BUNDLE rather than from
    # ``documents``: a module's content must not depend on who else was named
    # (``bundle.named``), which is §10's own sentence about why one document's module is
    # the same text whether it is emitted alone or with the whole bundle.
    found = bundle.edges(bundle_dir)
    named = bundle.named(found)
    composed = bundle.composed(found)
    #: The reference sites of each document, in document order: every ``$ref`` the
    #: document states, including a LOCAL one.  A local reference is in the map so that
    #: the one caller that can meet one without going through ``nodes.Reference.head``
    #: -- ``compiler.lower_composition``'s ``$ref``-conjunct arm -- is answered by name
    #: rather than by the absence of an entry, which is the arm the binder closure kept
    #: for exactly this reason.
    sites: dict[str, list[bundle.Edge]] = {}
    for edge in found:
        sites.setdefault(edge.document, []).append(edge)
    #: **The edges the WALK LOWERS a type or an import from, which is what the closure
    #: and the order range over.**  ``bundle.lowered_references`` is the derived reading
    #: and its docstring is the argument: §3's RULE position lowers no type, so a
    #: reference under a conditional emits no import and its target is legitimately not
    #: emitted; and §5's ``definitions`` row makes a section "nothing by itself", so a
    #: reference inside an entry nothing names is at a position no class names.  Taking
    #: the closure over EVERY edge instead would emit a module for a target no module
    #: imports -- measured on the suite's own population: 22 documents more than the
    #: committed tree, which is exactly the set those two sentences exclude.
    lowering: dict[str, list[bundle.Edge]] = {}
    for document, edges in sites.items():
        reached = {
            pointer
            for pointer, _ in bundle.lowered_references(
                bundle.read(bundle_dir, document), named.get(document, frozenset())
            )
        }
        lowering[document] = [e for e in edges if e.pointer in reached]
    ordered, refused = order(closure(documents, lowering), lowering)

    lowered: dict[str, tuple[Module, ir.Module, dict]] = {}
    #: ``$ref`` URI -> the ROOT NODE of the document it names, for §2's intersection
    #: rule (:meth:`compiler.Module.resolve_node`).  **Run-level and not per document**,
    #: and the reason is whose declaration that rule reads: it compares two property
    #: DECLARATIONS, and one of them is a BASE's, so the URI it asks about is a site of
    #: the base's document and not of the one being lowered.  Filled as the order
    #: finishes each document, which is early enough by construction -- a base precedes
    #: the document composing it, and the base's own targets precede the base.
    roots: dict[str, dict] = {}
    #: document -> the reference sites its walk ASKED about, kept whatever the outcome:
    #: a refused document has no module to hand back and the sites it reached before
    #: refusing are what say whether their targets are documents this run owes.
    asked: dict[str, set[tuple[str, str]]] = {}
    #: target document -> the no-fragment URIs that name it, so the fill above is a
    #: lookup rather than a scan per document.
    spellings: dict[str, set[str]] = {}
    for edge in found:
        if edge.target is not None and not edge.into:
            spellings.setdefault(edge.target, set()).add(edge.uri)

    def resolve(document: str) -> dict[tuple[str, str], Target | Refusal]:
        """This document's reference sites, resolved: §5's ``targets``.

        Every answer the binder closure returned, computed here instead -- and computed
        BEFORE the document is parsed, which is what the dependency order buys: each
        target is either in ``lowered`` or in ``refused``, so nothing recurses and no
        stack says which documents are in flight.
        """
        answers: dict[tuple[str, str], Target | Refusal] = {}
        for edge in sites.get(document, ()):
            site = (edge.uri, edge.pointer)
            if edge.local:
                # A LOCAL reference names a node of the document being written, so there
                # is no module to import from and nothing for a binding to resolve:
                # ``references.lower`` branches on the empty document half first and asks
                # ``compiler.local_reference`` for the symbol this module declares.  This
                # stays as the loud answer for the one caller that reaches a reference
                # another way -- ``compiler.lower_composition``'s conjunct arm -- rather
                # than being left out and reporting a pointer as a document the bundle
                # does not hold.
                answers[site] = Refusal(
                    "$ref",
                    edge.pointer,
                    f"{edge.uri} is a pointer into this document, which is not a binding "
                    "at all -- the walk resolves one through compiler.local_reference and "
                    "never through a binder",
                    kind=Kind.VERDICT,
                )
                continue
            if edge.target is None:
                answers[site] = Refusal(
                    "$ref",
                    edge.pointer,
                    f"{edge.uri} names no document of this bundle",
                    kind=Kind.VERDICT,
                )
                continue
            if edge.target not in lowered and edge.target not in refused:
                # **A target the order has not reached, which happens at exactly the
                # sites the walk lowers NOTHING from.**  The closure and the order range
                # over ``bundle.lowered_references``, so a site outside that reading --
                # a reference at a RULE position, or one inside a ``definitions`` entry
                # nothing names -- constrains no order and its target may come later.
                # The walk never asks at such a site; this is the loud answer if it ever
                # does, because the two readings of which positions lower a type would
                # then disagree, which is a defect in this compiler and not in any
                # document.
                answers[site] = Refusal(
                    "$ref",
                    edge.pointer,
                    f"{edge.uri}: the dependency order has not reached its target, "
                    "because no reference the walk lowers a type or an import from "
                    "reaches this position (bundle.lowered_references: a reference at a "
                    "RULE position lowers nothing, and one inside a definitions entry "
                    "nothing names is at a position no class names)",
                    kind=Kind.VERDICT,
                )
                continue
            if edge.target in refused:
                r = refused[edge.target]
                # **The fragment is NAMED here, not only the document.**  A message
                # naming only the document sends the reader to a file without saying
                # which of its nodes was wanted.  Bundle-relative, so it reads as a
                # pointer into this bundle rather than as the URI's own base; a
                # reference with no fragment is unchanged.
                #
                # **``through=r`` is the classification and the quoted text is for the
                # reader.**  Whether this document is pending or final is not a property
                # of its own sentence at all, it is whatever the target's is --
                # ``Refusal.resolved`` takes the target's, so a chain of any depth is one
                # attribute read and no sentence is parsed.
                wanted = f"{edge.target}#{edge.into}" if edge.into else edge.target
                answers[site] = Refusal(
                    "$ref",
                    edge.pointer,
                    f"its target {wanted} is refused: {r}",
                    kind=Kind.CHAINED,
                    through=r,
                )
                continue
            mod, bound, _ = lowered[edge.target]
            symbol = bound.root
            if edge.into:
                # The fragment names a NODE, so the symbol is the one the target
                # module declared AT THAT POINTER rather than its root.  The target
                # declares one because ``bundle.named`` told it to.
                #
                # Two kinds of pointer have no symbol, and both are REFUSED with the
                # fragment named rather than bound to the root -- binding to the root
                # would import a class for the WHOLE document where the document names
                # one node of it, which is a model wider than its schema and silent:
                #
                #  * a pointer the target's walk never reaches.  17 of the bundle's 76
                #    named nodes are ``definitions`` entries, which no row descends.
                #  * a pointer whose node is ITSELF a ``$ref``.  The symbol there is
                #    one the target module IMPORTED rather than declared, so binding it
                #    would make this a re-export, and section 2's rule is an import of a
                #    symbol the target DECLARES.  10 of the 76, in 3 documents, all 3
                #    refused on a keyword of their own -- so 0 are reachable and the
                #    step whose population reaches one decides whether the chain is
                #    followed to the declaring module.
                if edge.into not in bound.symbols:
                    answers[site] = Refusal(
                        "$ref",
                        edge.pointer,
                        f"{edge.uri}: its target {edge.target} declares no symbol at "
                        f"{edge.into} (the walk either does not reach that node, or the "
                        "node is itself a $ref whose symbol that module imports rather "
                        "than declares)",
                        kind=Kind.DEFERRED,
                    )
                    continue
                symbol = bound.symbols[edge.into]
            # ``shape`` is ``None`` for a target that is not a class -- D2's
            # root-scalar alias, and a named node that is not one either -- which is
            # what lets a composing row refuse it as a base rather than writing a
            # module that cannot be imported.
            #
            # **The SHAPE crosses the module boundary with its symbols BOUND**, which is
            # what makes a shape recorded by pointer readable in another module: the
            # target was named before this document was parsed (§10's order), so its own
            # symbol table is what binds the re-used field's type and the set of symbols
            # a composing subclass may import from it (``compiler._reused``).
            shape = mod.shapes.get(edge.into)
            answers[site] = Target(
                relative_module(document, edge.target),
                symbol,
                None if shape is None else _bound_shape(shape, bound.symbols),
            )
        return answers

    for document in ordered:
        doc = bundle.read(bundle_dir, document)
        outcome = decidable(
            bundle_dir,
            document,
            doc,
            resolve(document),
            named.get(document, frozenset()),
            roots,
            render.RESERVED,
            asked.setdefault(document, set()),
        )
        if isinstance(outcome, Refusal):
            refused[document] = outcome
            continue
        mod, bound = outcome
        lowered[document] = (mod, bound, doc)
        # The target's own root node, for §2's intersection rule and for nothing else.
        # Written when the document FINISHES, so a refused document contributes none and
        # the rule treats such a pair as unordered -- which is the safe direction and is
        # what the binder answered for a refused target before.
        for uri in sorted(spellings.get(document, ())):
            roots[uri] = doc

    # **WHAT THE RUN WRITES is §10's own sentence and not everything the order
    # visited**: "a module cannot import from a module no run wrote".  So a run owes the
    # documents it was NAMED, and every document one of those actually REFERENCED,
    # transitively -- and the sites a walk asked about are the record of that
    # (``compiler.Module.asked``).
    #
    # The closure and the order range over a STATIC reading
    # (``bundle.lowered_references``), which is what lets a target be finished before its
    # referrer is parsed; that reading is an over-approximation of what the walk reaches,
    # because a document that refuses stops before its later sites.  Measured on the
    # suite's population of 991: taking the order's visit set as the output writes 11
    # modules nothing imports and nobody named -- ``core/collection.json`` and 10 like
    # it, every one reached only from a document that refused.
    #
    # Written as a FIXED POINT over the run's own record, so it is a function of
    # (bundle, named set, this package) and of nothing a caller orders.
    sited = {(e.uri, e.pointer): e.target for e in found}
    wanted = set(documents)
    unread = sorted(wanted)
    while unread:
        document = unread.pop()
        for site in sorted(asked.get(document, ())):
            target = sited.get(site)
            if target is not None and target not in wanted:
                wanted.add(target)
                unread.append(target)
    lowered = {d: held for d, held in lowered.items() if d in wanted}
    refused = {d: r for d, r in refused.items() if d in wanted}

    for document in sorted(lowered):
        mod, bound, doc = lowered[document]
        rel = module_path(document)
        out.files[f"{rel}.py"] = render.module(
            bound, exported(mod, bound, composed.get(document, frozenset()))
        )
        out.emitted[document] = f"{PACKAGE}.{rel.replace('/', '.')}"
        # **The two halves of what §4's dedup did, derived from one table.**  §7's symbol
        # table holds every pointer a type resolves at, which is the DECLARED pointers
        # plus the adopting ones that bound a class by identity with no declaration of
        # their own -- and those are exactly the ones whose symbol IS the declaring
        # pointer's.  So ``declared`` is the table minus them and needs no second record.
        out.declared[document] = {
            p: n
            for p, n in bound.symbols.items()
            if p not in bound.adopted or n != bound.symbols[bound.adopted[p]]
        }
        out.adopted[document] = {
            p: bound.symbols[at] for p, at in bound.adopted.items() if at in bound.symbols
        }
        if mod.drops:
            out.drops[document] = dict(mod.drops)
        if mod.carries_nothing:
            out.carries_nothing[document] = list(mod.carries_nothing)
        if bound.approximations:
            out.approximations[document] = list(bound.approximations)
        # The document travels WITH the module, at its own bundle-relative path,
        # because ``__adcp_schema__`` names that path and ``strict_validate``
        # reads it to decide acceptance (D4).  The bundle is a build-time input
        # -- 124 MB, with a version in its path -- so it cannot be the runtime
        # source.  Written here, by the run that lowered it, which is what makes
        # P10's compare cover the schemas the runtime asks and not only the
        # modules.
        #
        # THE DOCUMENT OF RECORD: a reference is an import in the MODULE (P2), but a
        # `$ref` left in the DOCUMENT is a schema nothing local can decide, so
        # `jsonschema` fetches the target over the network -- deprecated, 4.4 s
        # per validation measured, and simply unavailable offline.  See
        # ``bundle.record``; a document with no reference records as itself, and the
        # record is the bundle's document with its references inlined and nothing
        # else changed (``docs/plan/rebuild-plan.md`` §3).
        #
        # The ``isinstance`` arm cannot be reached here: ``lower`` above takes the
        # record of every document it lowers and raises the refusal, so a document
        # whose record is undefined is in ``refused`` and not in ``lowered``.  It is
        # written rather than asserted because this is the call that produces the FILE,
        # and a mapping is the only thing that can be written to one.
        record = bundle.record(bundle_dir, document) if bundle.references(doc) else doc
        if isinstance(record, Refusal):
            # **UNREACHABLE, and a BUILD FAILURE rather than a refusal.**  ``decidable``
            # above takes the record of every document it lowers and returns that very
            # refusal, so a document whose record is undefined is in ``refused`` and not
            # in ``lowered``.  Reaching it means the two calls disagreed about one
            # document, which is a property of the COMPILER (§2) and not of the
            # document; it is written rather than asserted because this is the call that
            # produces the FILE, and a mapping is the only thing that can be written to
            # one.
            raise BuildFailure(
                f"{document}: its record is undefined here ({record}) and defined where "
                "`decidable` read it, so the two readings of one document disagree"
            )
        out.files[document] = json.dumps(record, indent=2, sort_keys=True) + "\n"
        parts = rel.split("/")[:-1]
        packages.update("/".join(parts[: i + 1]) for i in range(len(parts)))

    for document in sorted(refused):
        r = refused[document]
        # ``kind`` is what the producer DECLARED and ``resolved`` is what counts: they
        # differ only for a delegating kind, which has already followed its chain.  Both
        # are recorded because the first says which producer to go and read and the
        # second is the metric's own input, and collapsing them to one loses the chain.
        out.refusals[document] = {
            "keyword": r.keyword,
            "pointer": r.pointer,
            "detail": r.detail,
            "kind": r.kind,
            "resolved": r.resolved,
        }
    for pkg in packages:
        out.files[f"{pkg}/__init__.py"] = ""
    out.files["__init__.py"] = ""
    # D5's alias module, unioned over the run.  A shape resolved in two documents
    # is one symbol, and ``check_injective`` (inside ``declare``) fails the build
    # if two shapes ever derive one name -- which would annotate two fields with
    # one alias, one of them stating a constraint its document does not.
    aliases: dict[str, constraints_module.Shape] = {}
    for document in sorted(lowered):
        for name, (kind, cons, fmt) in lowered[document][0].aliases.items():
            constraints_module.record(aliases, name, kind, cons, format=fmt)
    out.beside[f"{constraints_module.MODULE.rsplit('.', 1)[1]}.py"] = render.constraints_module(
        aliases
    )
    # The refusal REPORT is not a file in the tree.  It was, and the documented
    # one-document command then rewrote it with that run's refusals -- which are
    # none -- so running the command in the README damaged the committed tree and
    # reddened the gate.  A report about documents this package does NOT contain
    # has no place inside the shipped package anyway: `main` prints it, and the
    # suite reads `Emitted.refusals` from the run it just made.
    return out


def write(out: Emitted, tree: Path, package: Path | None = None) -> None:
    """Write this run's files, and -- on a WHOLE-POPULATION run -- delete the files
    it no longer intends.

    **A stale module is an integrity defect and not untidiness**, which is why the
    deletion is here and not in a step a human remembers.  A document that stops
    emitting leaves a ``.py`` and a ``.json`` that are INDISTINGUISHABLE from a real
    emission to everything that reads the tree: the class still imports, still
    carries ``__adcp_schema__``, and still answers ``strict_validate``, so the
    harness can grade a class the current compiler would not produce.  §2 binds
    every class to its document precisely so that it is impossible to point the
    grader at a tree this run did not emit, and a stale file is that tree one file
    at a time.

    The enforcement used to be a RED TEST and a hand deletion:
    ``test_the_committed_tree_is_what_a_fresh_run_emits`` compares file SETS, so it
    fails on a stale file -- but it fails at the gate, leaving the operator to
    derive the stale set and remove it.  Two lanes did that by hand
    (``salesagent-j3k2l.22``, which turned 32 documents into verdicts and removed 4
    files, and ``.26``), which is two for two: every change that ADDS a refusal was
    a two-step job and nothing enforced the second step.

    **``package`` is the run's SCOPE, and it gates both whole-run effects.**  It is
    required for :attr:`Emitted.beside` because D5's alias module is ONE file over
    the WHOLE run: a run over one document resolves that document's shapes and no
    others, so writing it would replace the committed module with a shorter one and
    leave every other module importing a symbol that is gone.  The prune is the same
    fact asked of the tree -- a one-document run INTENDS one document's files, so an
    ungated prune would delete the other 676 modules of the committed tree.  That is
    why a prune was tried here before and removed: a command whose demonstration
    wipes the tree gets run once.  Gating it on the discriminator already present
    means the README's whole-tree command prunes with no change to it and its
    one-document command cannot, and no second flag exists for anyone to forget.

    **The intended set comes from this run's result, never from a pattern over the
    directory**: :attr:`Emitted.files` is the set ``write`` just wrote, so a file
    under ``tree`` that is not in it is a file no run produces.  Deletion is bounded
    to :data:`EMITTED_SUFFIXES`, the two kinds ``emit`` itself writes.

    Known ceiling: a directory left EMPTY by the prune stays.  It is inert -- no
    ``__init__.py``, so it is not a package, holds no class and cannot be graded --
    and removing directories is the one way this could reach something no run of
    this emitter created.  The upgrade, if an empty domain directory ever matters,
    is a bottom-up ``rmdir`` of the directories the prune emptied.
    """
    for rel in sorted(out.files):
        path = tree / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(out.files[rel])
    if package is None:
        return
    for rel in sorted(out.beside):
        path = package / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(out.beside[rel])
    # Only ``tree``.  ``package`` holds the hand-written ``_base.py`` beside the
    # alias module and is nobody's population: ``Emitted.beside`` names one file in
    # it, not its contents.
    intended = {tree / rel for rel in out.files}
    for path in sorted(tree.rglob("*")):
        if path.suffix in EMITTED_SUFFIXES and path not in intended and path.is_file():
            path.unlink()
