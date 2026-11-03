"""The WALK: it reads a bundle document and decides what each node becomes.

The command is ``python -m codegen`` and it lives in ``codegen/__main__.py``,
which holds the argument parser and the refusal report and nothing else:

    python -m codegen --bundle schemas/cache/3.2 core/pagination-request.json

The committed tree is the same command over ``bundle.portable(BUNDLE)``: every
document of the bundle that can be emitted at all, derived from the bundle and never
listed by hand.  ``tests/test_emit.py``'s ``tree_population()`` is that reading and is
what regenerates the tree; it is NOT the union of the seven STEP selectors
(``population()``, whose predicates live in ``tests/populations.py``), because a step is
a phase of the rebuild and the tree is an ARTIFACT -- a population drawn from the phases
made the tree's contents depend on which documents an earlier run happened to reach
through a ``$ref`` (``adcp-client-python-10l.73``).
``docs/plan/architecture.md`` §5 puts the STEP predicates under ``tests/`` ("the
document-set predicates a step's result was stated over are the tests' business and live
under ``tests/``") and they are still there; the tree's population is the bundle's own
and is read by the one predicate this package already has.  So this package still names
no population, and the one the tree is graded against is the one the suite counts.

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
closure, the per-document fold, the files and the report -- plus :func:`decide_type`,
which wraps the ONE per-node dispatch.  **The dispatch itself is
``codegen/lower/decide.py``'s**, an exhaustive ``match`` over
``codegen/schema/nodes.py``'s kinds; this paragraph used to call it ``_decide`` and put
it here, and §14 step 5 moved it.  There was a second dispatch beside it, ``ROWS``, over
a document's root KIND; step 5 deleted that too, so a document is one ``decide`` call at
ROOT and :func:`lower_document` adds the module wrapper and nothing else (§5).  What is
in ``compiler`` is everything a
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
once, by name, on every path.  ``lower.scalars.name_the_constraint`` is therefore
reached through ``compiler.carried``, and the context carries DATA rather than
functions.

**The per-node decision was then reached through THIS module and is not any more**
(``adcp-client-python-3be.5``).  Being nameable made the deferred import legal and left
it pointing the wrong way: §11's arrows run ``lower <- emit``, and a wrapper here that
``compiler.lower_node`` imported put the run inside the per-node loop.  It is
``compiler.lower_node`` now and the banner below carries the reading.
``tests/test_import_rule.py`` holds §11's third boundary transitively as well as §8 and
§9, so three of its four AST tests are graded and the fourth is the ``raise`` ban.

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
from codegen import bundle, catalogue, compiler, harness, ir, keywords, render, store
from codegen.keywords import Position
from codegen import constraints as constraints_module
from codegen.compiler import (
    SCALAR,
    Module,
    Target,
    ValuesImport,
    check_keywords,
    class_name,
    declare_alias,
)
from codegen.lower import approximate as lower_approximate
from codegen.lower import const as lower_const
from codegen.lower import envelope as lower_envelope
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

#: **The positions a BASE is named at**, for the reference sites a composing document
#: inherits (``inherited_sites``).  ``CONJ`` is the ``allOf`` conjunct §5's row is
#: written for; the other two are §2's intersection rule read one level down, and they
#: are DERIVED from the same declaration the rule's recursion is --
#: :data:`compiler.HOLDS`, whose keywords' subschemas sit at ``ELEM`` (``items``) and
#: ``PROP`` (``properties``).  A restatement composing a base's declaration of a
#: property or of an element composes whatever that declaration names, so the target it
#: names is a base of the composed class exactly as a conjunct's target is.
#:
#: Read off :attr:`bundle.Edge.position` and never recovered from a pointer string
#: (``docs/plan/architecture.md`` §3), and derived rather than listed, so the set cannot
#: disagree with the rule whose recursion produced the site.
BASE_POSITIONS: frozenset[Position] = frozenset({Position.CONJ}) | frozenset(
    answer.descends
    for keyword in compiler.HOLDS
    if (answer := keywords.cell(keyword, Position.PROP)) is not None
    and answer.descends is not None
)

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


def _node_or_none(doc: dict, into: str) -> dict | None:
    """The MAPPING a ``$ref``'s pointer half names in ``doc``, or ``None``.

    The reading :attr:`referenced` and :func:`based_nodes` both fill through, so §2's
    intersection rule resolves a fragment the same way ``bundle.record`` inlines one --
    one pointer navigator (``bundle.node_at``) and one escaping rule.

    ``None`` for a pointer naming no node, and for one naming a node that is not a
    mapping: the rule compares two DECLARATIONS, and the answer it does something with
    is a schema.  That is the same undecidable arm ``Module.resolve_node`` already has,
    and refusing is the direction it points -- a reference the merge rule cannot read is
    a declaration it must not claim is narrower.
    """
    try:
        node = bundle.node_at(doc, into)
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    return node if isinstance(node, dict) else None


def module_path(document: str) -> str:
    """D1: the module is the document path with hyphens as underscores.

    **The NAME's path and not always the FILE's.**  A document whose path is also a
    directory's is that package's root and its file is ``<this>/__init__.py``
    (:func:`module_file`), but a package's ``__init__`` IS the package, so the name
    Python imports it under is this and nothing is appended to it.  The two readings
    are :func:`module_name` and :func:`module_file` and there are no others.
    """
    p = Path(document)
    return "/".join([*p.parent.parts, p.stem]).replace("-", "_")


def domain(document: str) -> str:
    """§1's DOMAIN for a document: the first segment of D1's module path.

    "re-exported from ``adcp.types.<domain>``, where the domain is derived from the
    document's own path" -- so it is derived here, from :func:`module_path`, and there is
    no table.  A new document appears in its domain with nothing edited, and a document at
    the tree's ROOT is a domain of its own: ``adagents.json`` has no directory beside it,
    so the derivation answers 23 domains where the 22 directories suggest 22, which §1
    confirms ("§10's layout rule is untouched -- that rule is about a document whose path
    is ALSO a directory's, and this one has no directory").
    """
    return module_domain(module_path(document))


def module_domain(module: str) -> str:
    """§1's DOMAIN for one MODULE of the tree: the first segment of its path.

    **The reading the export record takes now that it is keyed on the MODULE** (§3a,
    2026-11-02): "The readers that take a document to answer a domain or a path take the
    module instead, which is what they were always asking about."  §3a's catalogue module
    has no document, so :func:`domain` has nothing to ask about it, and the derivation §1
    states -- "the domain is derived from the document's own path" -- was already a
    reading of the MODULE path by way of :func:`module_path`.  So this is the one
    derivation and :func:`domain` is it composed with D1.
    """
    return module.split("/")[0]


@functools.lru_cache(maxsize=None)
def domain_roots(bundle_dir: Path) -> dict[str, frozenset[str]]:
    """Per §1 DOMAIN, the ROOT symbol of every portable document in it.

    **The half of §1's domain-scope collision rule that needs no lowering**, and the whole
    of what ``lower/names.py``'s ``surface`` argument is fed for the six branch-vs-root
    collisions.  A root's name is ``class_name(title)`` and a title is a fact of the
    document's own mapping, so this is a PARSE and not a compile: **measured over the 1,054
    portable documents, reading and parsing every raw document at ROOT costs 0.23 s**,
    against 66 s to build their records and ~100 s to lower them.  The two branch-vs-branch
    and two alias-vs-alias collisions need the nested names and so need the walk; they are
    not this function's.

    **A function of the BUNDLE and never of the run's document set**, which is what makes
    it legal at all: it ranges over ``bundle.portable(bundle_dir)`` whatever the run was
    asked for, so a one-document command and a whole-population emission read the same set
    and derive the same name.  §9's own ruling is the authority -- "the RUN is not the
    BUNDLE ... a name derived from a bundle-wide reading is the SAME name in both, which is
    exactly the property this rule protects" -- and ``bundle.composed`` is the precedent
    with the same sentence in its docstring.  ``lru_cache`` so a run pays the 0.23 s once;
    the key is the bundle directory, which is the only thing the answer depends on.

    **The RAW document and not the record, which is measured rather than assumed.**
    ``bundle.record`` inlines a cross-document ``$ref``, so a root that was a bare
    reference would take its target's ``title`` into the record -- and the walk reads the
    record.  Over all 1,054 documents the two readings agree on the title and on the
    symbol, **0 differences**, and :func:`decidable` asserts the agreement per document on
    every run rather than leaving it to this docstring: the walk's own ``mod.root`` is
    compared against this answer, so a bundle where the two diverge is a build failure at
    the document rather than a wrong public name.

    A document whose record carries no title, or whose title derives no identifier,
    REFUSES in :func:`lower_document` and exports no symbol, so it contributes none here.
    """
    out: dict[str, set[str]] = {}
    for document in bundle.portable(bundle_dir):
        node = schema.parse(
            bundle.read(bundle_dir, document),
            pointer="",
            position=Position.ROOT,
            source=schema.Source(document=document),
        )
        title = node.title
        if title is None:
            continue
        symbol = lower_names.class_name(title)
        if symbol.isidentifier():
            out.setdefault(domain(document), set()).add(symbol)
    return {known: frozenset(symbols) for known, symbols in out.items()}


@functools.lru_cache(maxsize=None)
def domain_exports(
    bundle_dir: Path, domains: frozenset[str]
) -> dict[str, dict[str, frozenset[str]]]:
    """PASS ONE of §1's domain-scope collision rule: per domain, every name the surface
    exports and the documents that want it.

    **It is a WALK and the §9 ruling says why it has to be.**  The ROOT half of this
    answer is a title and :func:`domain_roots` reads 1,054 of them in 0.23 s; a NESTED
    name is not, because what it needs is ``mod.hops`` -- which positions exist and what
    kind each one is -- and that is the WALK's decision.  An untitled ``enum`` branch
    becomes a ``Literal`` and declares no class; §5's widenings drop a position; §4's
    bare-``$ref`` branch rung takes the TARGET's distinguishing remainder, so the target
    had to be named first (§10's order).  A parse answering any of that would
    re-implement three rules, which is the second derivation §3 forbids.

    **The population is the DOMAIN and never the run** (§9's ruling, 2026-10-30): the
    collision scope is the domain, a domain's membership is a function of the bundle, so
    this ranges over ``bundle.portable`` filtered to ``domains`` whatever the run was
    asked for.  A one-document command and a whole-population emission therefore read
    one census and derive one name, which is the property §9 protects -- the RUN is not
    the BUNDLE.

    **IT IS A FIXED POINT, which is §4's own "and the step repeats" one scope out.**  §4's
    rule inside a module is "where N positions derive the same name, ALL N lengthen ... and
    the step repeats until every name in the module is unique", and ``_lengthened``
    implements the repetition by recomputing the groups each round.  The same repetition is
    owed here, and the measurement is why: resolving the first round took this bundle's
    domain collisions from 18 to **2**, and both survivors were two branches of
    ``content_standards`` that had lengthened onto one NEW name --
    ``CalibrationExemplarsFailItemUrl`` and ``…PassItemUrl``, wanted by
    ``create-content-standards-request`` and ``update-content-standards-request`` alike.  A
    single round cannot see them, because the name they collided on is one neither position
    wanted before the round moved it.

    The census ACCUMULATES rather than being replaced, and that is what makes it terminate
    rather than oscillate.  A round's names are a function of the census it was given, so
    replacing the census would let a position return to a name an earlier round had freed:
    round two frees ``FailItemUrl``, round three would take it back, and the loop would
    alternate forever.  Accumulating is monotone -- the set of taken names only grows, and
    the rungs and depths a position can spell are finite -- so the loop stops.  Measured on
    this bundle it stops after **three** rounds with every domain collision resolved, and
    the accumulation costs nothing: the names dropped on the way are each wanted by two
    positions that both moved off them, so no position is pushed off a name another document
    finally exports.

    Keyed by the DOMAIN SET and memoised, so a run pays pass one once however many
    documents it was given.  The symbols are keyed to the documents that want them
    because :func:`decidable` has to subtract its OWN: a name only this document exports
    is not a collision, and §4 settles a name inside one module already.

    **AND HELD ON DISK UNDER A CONTENT ADDRESS, which is §9's own answer to what that
    costs** (``codegen/store.py``, which carries the measurement and the correctness
    argument).  ``lru_cache`` does not cross a process, and the process that matters is the
    one-document loop: measured on ``4eff4354``, a run naming
    ``compliance/comply-test-controller-request.json`` paid **144.1 s** where its own
    closure walk is 34.5 s, because the domains that closure touches reach ``core`` and §4's
    repetition walks them three times.  §9 names the remedy rather than a shortcut -- "the
    export symbols are a function of the bundle, so they key on the bundle's content exactly
    as ``tests/compiled.py`` keys a compile.  A miss costs the walk, a hit costs nothing,
    and a content address cannot go stale" -- so the second layer keys on exactly what this
    answer is a function of: the bundle, the domain set, and every ``.py`` under
    ``codegen/``.  It can cost time and never a name, which is the property
    ``tests/test_the_domain_surface.py``'s export set is the gate on.
    """
    return store.held(
        bundle_dir,
        sorted(domains),
        lambda: _the_domains_exports(bundle_dir, domains),
    )


def _the_domains_exports(
    bundle_dir: Path, domains: frozenset[str]
) -> dict[str, dict[str, frozenset[str]]]:
    """:func:`domain_exports`' answer, computed -- the fixed point its docstring states.

    Split out so the two layers above it are each one thing: ``lru_cache`` is the memo
    inside a process, ``store.held`` is the content address between them, and this is the
    walk neither of them is allowed to change the answer of.
    """
    wanted = sorted(d for d in bundle.portable(bundle_dir) if domain(d) in domains)
    census: dict[str, dict[str, frozenset[str]]] = {}
    while True:
        round_of = emit(bundle_dir, wanted, naming_census=census)
        # **The stop condition is read off THIS ROUND's names and never off the
        # accumulated census.**  §4's rule is "the step repeats until every name is
        # unique", so what ends the loop is a round in which no two documents of one
        # domain export one name.  Reading the ACCUMULATION instead is wrong in both
        # directions and both were measured: growth runs one whole round past the answer,
        # because the round that resolves the last collision still contributes its new
        # names; and a round's names compared against the accumulated takers never settles
        # at all, because a name an earlier round gave up still has that round's document
        # recorded against it.
        this_round: dict[str, dict[str, set[str]]] = {}
        # **Over the round's DOCUMENTS and not over the record's keys**, because what a
        # domain's census holds is the documents that want each symbol and
        # ``decidable`` subtracts its OWN.  The record is keyed on the MODULE (§3a), so
        # the question is asked the way round: a document names its module (D1) and the
        # record answers with that module's exports.  §3a's catalogue module is on the
        # record with no document and exports nothing, so it is absent from both sides.
        for document in round_of.emitted:
            held = this_round.setdefault(domain(document), {})
            for symbol in round_of.surface.get(module_path(document), {}):
                held.setdefault(symbol, set()).add(document)
        shared = any(
            len(takers) > 1 for held in this_round.values() for takers in held.values()
        )
        grown = {known: {s: set(d) for s, d in held.items()} for known, held in census.items()}
        for known, held in this_round.items():
            into = grown.setdefault(known, {})
            for symbol, takers in held.items():
                into.setdefault(symbol, set()).update(takers)
        census = {
            known: {symbol: frozenset(docs) for symbol, docs in held.items()}
            for known, held in grown.items()
        }
        if not shared:
            return census


def module_name(document: str) -> str:
    """D1's module as the DOTTED name Python imports it under.

    The one reader: ``f"{PACKAGE}.{module_path(d).replace('/', '.')}"`` was spelled at
    three sites and in the suite, and a package root is the case where a second
    spelling would have gone wrong -- ``brand/__init__`` dotted is
    ``...brand.__init__``, which imports a SECOND module object for the package's own
    body and executes it twice.  ``__init__`` is never in the name because a package's
    ``__init__`` is the package.
    """
    return f"{PACKAGE}.{module_path(document).replace('/', '.')}"


def module_file(document: str, packages: Collection[str]) -> str:
    """D1's module as the FILE that holds it, without the ``.py``.

    ``docs/plan/architecture.md``, the layout rule beside ``write`` (2026-10-29):
    where the bundle holds both a document at path ``P`` and a directory at path
    ``P``, the two are one namespace and the document is its ROOT, so it is written to
    ``P/__init__.py`` and the directory's documents are its submodules.  ``packages``
    is ``bundle.package_roots``, a function of the bundle and never of the run.

    The measured alternative is what this replaces: ``brand.py`` holding 113 classes
    beside a 0-byte ``brand/__init__.py``, where Python resolves the name to the
    package and the module is UNIMPORTABLE while the run reports the document as
    emitted.
    """
    rel = module_path(document)
    return f"{rel}/__init__" if document in packages else rel


def relative_module(frm: str, to: str, packages: Collection[str]) -> str:
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

    **The two sides read D1 differently and that asymmetry is the whole of the
    package-root rule here.**  The LEADING DOTS count hops up from the importing
    module, which is a fact about where its FILE sits -- ``brand/__init__.py`` is one
    level below ``_schemas``, so its ten imports are ``..core.brand_ref`` and not
    ``.core.brand_ref``, and that is the arithmetic that goes wrong first.  The TAIL
    names the target, which is a NAME: a package root is spelled as the package, so a
    module under ``brand/`` reaches it as ``..brand`` and never as ``.__init__`` --
    which would import the package's body a second time under a second name.
    """
    return relative_to_module(frm, module_path(to), packages)


def relative_to_module(frm: str, to: str, packages: Collection[str]) -> str:
    """:func:`relative_module` where the TARGET is a module path and not a document.

    Split out for §3a's catalogue module, which has no document to derive a path from:
    "**A pseudo-document path is refused**: it names a file the bundle does not contain,
    and every reader that resolves a record from a key would then be lying about where
    the schema came from."  A function taking a document and a module path cannot be
    handed one.

    The arithmetic is :func:`relative_module`'s own and is stated there; both sides of
    the asymmetry it describes hold unchanged, because the only thing that changed is
    where the TAIL comes from -- and a catalogue module is never a package root, so the
    package-root clause has nothing to say about it.
    """
    src, dst = module_file(frm, packages).split("/"), to.split("/")
    common = 0
    while common < len(src) - 1 and common < len(dst) - 1 and src[common] == dst[common]:
        common += 1
    return "." * (len(src) - common) + ".".join(dst[common:])


# --------------------------------------------------------------------------- #
# the walk: what each node IS -- and it is NOT here
# --------------------------------------------------------------------------- #
# **``decide_type`` is ``compiler.lower_node`` now** (``adcp-client-python-3be.5``), and
# the reading is §11's third AST test rather than a tidier home.  This module is the RUN:
# §11 gives it "order, closure, files, the report" and says it "may not know ... kinds,
# cells, nodes".  The wrapper read a node's pointer against ``mod.named`` and consulted
# §4's content memo, which are both statements about a NODE, and ``compiler.lower_node``
# reached it by a deferred ``from codegen.emit import decide_type`` -- so every
# nested-node recursion of every document passed through this module and the run sat
# inside the per-node loop.  The arrow §11 draws is ``lower <- emit``, one way.
#
# What moved with it: ``name_the_node`` and ``alias_for`` are ``codegen/lower/names.py``'s
# (§7's pass owns a name bound to a statement), as ``same_node`` and ``adopt`` already
# were.  What did NOT move is the CALL, and it cannot: a second occurrence's CHILDREN are
# never lowered, so a declaration the walk did not make has no name for a pass to derive,
# and the pruning is a decision about the walk.  So the walk's own entry holds it.
#
# A ROOT still reaches ``lower.decide.decide`` from here, below, and the difference is the
# two things a root does not have (:func:`lower_document` carries the reading).


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
    referenced: Mapping[str, dict] | None = None,
    reserved: frozenset[str] = frozenset(),
    asked: set[tuple[str, str]] | None = None,
    inherited: Mapping[str, Target | Refusal] | None = None,
    vocabularies: Mapping[str, Target] | None = None,
    restatements: Mapping[tuple[object, ...], Target | str] | None = None,
    value_lists: Mapping[tuple[object, ...], ValuesImport | str] | None = None,
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
        # §2's intersection rule: the sites this document's BASES spell, resolved for
        # this document and keyed by URI (``inherited_sites``).  Empty for a document
        # lowered outside a run, exactly as ``targets`` is.
        inherited_targets=inherited if inherited is not None else {},
        # **§3a's catalogue, as this document's own rows** (:attr:`Module.vocabularies`).
        # Empty for a document lowered outside a run, exactly as ``targets`` is: §9
        # forbids a reading of the run and a walk with no table mints no reference.
        vocabularies=vocabularies if vocabularies is not None else {},
        # The same table keyed on the VALUE LIST, for the restating positions no pointer
        # of this document's own text reaches (:attr:`Module.restatements`).
        restatements=restatements if restatements is not None else {},
        # §3a's OTHER half: the value lists this document DECLARES a type over and does
        # not write (:attr:`Module.value_lists`).  Empty by the same rule -- a document
        # lowered outside a run writes every value list in its own class bodies.
        value_lists=value_lists if value_lists is not None else {},
        referenced=referenced if referenced is not None else {},
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
        # **The DOCUMENT OF RECORD itself**, for §8's sentence 3a: a storage reference
        # resolves against the document ROOT, so §5's ``if`` row needs the root and not a
        # node.  The same object ``local`` and ``object_constrained`` are read off, handed
        # in rather than re-read, so there is one record per module and the walk sees the
        # text the package carries beside it (:attr:`compiler.Module.record`).
        record=doc,
    )
    # **§7's REPORTED DROPS, at every position the document states one at.**  "The drop is
    # reported at every position the keyword occupies, and not only where a conjunct
    # encloses it [...] a report that reaches one position and not another is a defect in
    # the channel, not a second decision."  So the channel is a function of the DOCUMENT,
    # read off ``bundle.reported_drops`` -- the one descent walk -- and written here,
    # beside ``object_constrained`` and ``asserted``, which are the document's other
    # derived facts.  Not in the walk: the walk arrives at the positions it lowers from,
    # and a ``then``'s subschema is a RULE source that ``lower.rules`` reads RAW, so no
    # screen is asked there and the one occurrence at ``/then`` reached no reader at all.
    compiler.report_reported_drops(bundle.reported_drops(doc), mod)
    # **ONE PATH, and it is now §5's sentence verbatim: "A document is ``parse(raw,
    # position=ROOT)`` followed by ``decide``."**  The second dispatch on a root's KIND
    # went in part two; the parser is what this commit adds, so the raw document is read
    # ONCE, here, into a node tree, and the dispatch routes the root node by its kind.
    #
    # ``decide`` and not ``compiler.lower_node``, and the difference is the two things a
    # ROOT does not have.  ``mod.named`` never holds the root's pointer
    # (``bundle.named_nodes`` skips a reference with no fragment), so there is nothing for
    # ``names.name_the_node`` to name; and the CONTENT MEMO is empty at the root and would
    # be SEEDED with the whole document's content by the walk's entry.  So its two jobs
    # are both absent here and calling it would add one: a nested node of content
    # identical to the document root would adopt the root's own symbol.
    #
    # It is the ONE place this module names the dispatch, and the import is deferred for
    # the same reason ``compiler``'s is -- ``lower.decide`` imports every handler and a
    # handler imports ``compiler``, so the module-level arrow would close a cycle.
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
    #: **MODULE** -> ``ir.Module.exports``: §1's export set for it, symbol -> the kind the
    #: surface exports it under (``root``, ``branch`` or ``alias``).
    #:
    #: **KEYED ON THE MODULE AND NOT ON THE DOCUMENT** (§3a, 2026-11-02): "A vocabulary
    #: with no naming position needs a module of its own, and that module has no document
    #: behind it.  **A pseudo-document path is refused** ... The honest relocation is one
    #: level up -- every document already maps to the module it produced, so the key
    #: becomes that module and a catalogue module is simply one with no document.  The
    #: readers that take a document to answer a domain or a path take the module instead,
    #: which is what they were always asking about."  Both readers did exactly that:
    #: :func:`domain_modules` spelled ``module_path(document)`` and the domain surface's
    #: check spelled it again, and neither wanted the document for anything else.
    #:
    #: So the record is every module the run WROTE, and §3a's catalogue module is on it
    #: with an EMPTY export set -- which is a fact about that module and not an absence:
    #: nothing in it is a type, so §1's surface has nothing of it to re-export.
    #:
    #: **The run's own record of what the DOMAIN SURFACE re-exports**, and the only thing
    #: §1's domain-scope collision rule can be graded over: §1 forbids
    #: ``adcp.types.<domain>.<Name>`` naming two declarations, and the question is asked of
    #: an export set that the emitted TEXT does not state -- a reader of a module sees
    #: class statements and cannot say which of them a nested ``A | B`` union declared.
    #: Measured, that is not hypothetical: deriving "branch" from the base list misses
    #: every arm of a nested bare union, and two of §1's collisions are exactly those.
    #:
    #: Written from the one place a position's hop and its declaration are both in hand
    #: (``lower/names.py``'s ``the_surface_exports``), so the rule, the surface and the
    #: check read one record and cannot disagree about what is exported.
    surface: dict[str, dict[str, str]] = field(default_factory=dict)
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
    #: document -> the reference SITES its walk asked about, each ``(uri, pointer)``.  The
    #: walk's OWN record of which references it lowered a type or an import from, which is
    #: what §10's prune is already computed over: "a run owes the documents it was NAMED,
    #: and every document one of those actually REFERENCED, transitively -- and the sites a
    #: walk asked about are the record of that".
    #:
    #: It is on the result because the STATIC reading the closure and the order range over
    #: (``bundle.lowered_references``) is an OVER-APPROXIMATION of it, and a reader that
    #: wants the ImportError claim -- every cross-document reference the walk lowers names
    #: an emitted document -- has to range over the walk's record and not over the static
    #: one.  Two things make the static reading wider: a document that REFUSES stops before
    #: its later sites, and §5(b)'s ``patternProperties`` widening drops a value schema, so
    #: a ``$ref`` inside it is at a position no class names and emits no import.
    asked: dict[str, set[tuple[str, str]]] = field(default_factory=dict)


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
    it is read by ANOTHER document -- a composing row's re-used field.  The target was
    named before this document was parsed (§10's order), so the binding is a lookup and
    never a second derivation.

    **Where those symbols are importable from is NOT bound here**: that is a fact about
    two DOCUMENT paths rather than about one class's fields, and it is
    :func:`_importable`'s, on the :class:`compiler.Target` beside the shape.
    """
    return dataclasses_replace(
        shape,
        decided={
            key: dataclasses_replace(f, type=lower_names.resolved(f.type, symbols))
            for key, f in shape.decided.items()
        },
    )



def _importable(
    asking: str,
    target: str,
    symbols: Mapping[str, str],
    imported: Mapping[str, str],
    packages: Collection[str],
) -> dict[str, compiler.Importable]:
    """Every symbol ``target``'s module can hand ``asking``, and where each comes from.

    **§1's "one import path per class" across more than two modules.**  ``symbols`` is
    the target's own symbol table, so every name in it is one the target DECLARES and
    the declarer is the target.  ``imported`` is the target's record of what it imported
    and from WHICH DOCUMENT, so a symbol reaching the target by import reaches this
    module from the same declarer -- never from the target, which would be a re-export
    and the second path §1 forbids.

    The two document paths are both here and the spelling is :func:`relative_module`'s
    (D1), which is why this is the run's and not the walk's: a lowering reads the table
    and derives no import.  A symbol the target both declares and imported is
    impossible -- one module, one namespace -- and the declaration wins if one ever is,
    because the target is then itself the declarer.
    """
    declares = compiler.Importable(relative_module(asking, target, packages), target)
    return {
        **{
            s: compiler.Importable(relative_module(asking, d, packages), d)
            for s, d in imported.items()
        },
        **dict.fromkeys(symbols.values(), declares),
    }


#: How many times :func:`repointed` re-reads its own output before it stops.  A local
#: reference whose target is itself a local reference moves a declaration twice, and a
#: chain of them moves it once per hop; the bundle's deepest chain is 2, and
#: ``compiler.local_reference`` already refuses a cycle by name, so this is a bound on a
#: terminating walk rather than a guard against one that does not terminate.  Same
#: constant style as ``harness``'s fold depths, and for the same reason: a traversal cut
#: at an unstated depth disagrees with its own reader about node identity (§9).
_TRAVEL_DEPTH = 8

#: The keywords whose subschemas are CONJUNCTS, DERIVED from the descent column rather
#: than named: ``keywords.descends_at`` is "the ONE descent table", and a keyword whose
#: subschemas sit at CONJ is exactly what a conjunction is.  Read at ROOT, where the
#: derivation enters; the column's answer is the same at every position that gives one.
_CONJUNCTS = frozenset(
    k for k, p in keywords.descends_at(Position.ROOT).items() if p is Position.CONJ
)


def _under(pointer: str, into: str) -> bool:
    """Whether ``pointer`` names the node at fragment ``into`` or one inside it.

    ``pointer`` is an :class:`adcp.types._base.Approximation`'s, so it carries the ``#``
    ``schema_ref`` spells; ``into`` is a :attr:`bundle.Edge.into`, which does not.  One
    spelling is reconciled here and in no second place, which is the whole reason this is
    a function: the widening obligation walks a declaration's own ``(pointer, keyword)``
    into the document (``harness.check_widening``), and a second ``#``-stripping is how a
    declaration and the node it is about come to sit at two pointers.
    """
    base = f"#{into}"
    return pointer == base or pointer.startswith(f"{base}/")


def _travelled(document: str, one: Approximation, referrer: str, into: str) -> Approximation:
    """``one`` re-pointed from the fragment ``into`` to the referring pointer.

    The suffix below the fragment is kept exactly, because the resolution kept it: a
    declaration at ``#/definitions/x/items`` carried to a reference at
    ``#/properties/y`` is a declaration at ``#/properties/y/items``, which is the pointer
    ``harness.check_widening`` walks once the resolution has replaced the node.

    The attribution is RE-MINTED rather than carried, and §2 is why: an upstream
    attribution "is a property of a document and a pointer rather than of a keyword", so a
    declaration arriving at a new document and a new pointer is a new SITE and
    ``codegen.attribution``'s registry is what answers for it.  Carrying the target's
    string would make ``harness.unattributed`` compare the artifact against a registry
    lookup for a site the artifact does not name.
    """
    pointer = f"#{referrer}{one.pointer[len(into) + 1 :]}"
    return one._replace(
        document=document,
        pointer=pointer,
        attribution=lower_approximate.attribution_for(document, pointer, one.keyword),
    )


def _folded(document: str, one: Approximation, declared: Collection[str]) -> Approximation:
    """``one`` re-pointed off any ``allOf`` CONJUNCT the walk composed into a class.

    The third of §8's four resolutions, under the same rule as the other two: a conjunct's
    facts are the composed node's -- ``compiler.lower_composition`` folds them into one
    class and ``harness._composed`` folds them on the document side -- so a declaration
    about one of those facts belongs at the composed node's pointer, or the walk that
    proves it reaches a node the document states no such keyword at.  Measured:
    ``core/account-with-authorization.json`` and ``account/list-accounts-response.json``
    both minted a widening one ``allOf/1`` hop below the class the conjunct composes.

    **The evidence that the walk composed is the walk's own symbol table**, and that is why
    ``declared`` is a parameter: a conjunct hop whose PREFIX is a pointer this module
    declared a class at is a conjunct that was folded into that class.  A hop with no class
    above it was not folded and keeps its pointer, which is the fail-safe direction -- the
    declaration then stands where the document states the fact, which is a pointer the
    obligation's own walk still reaches.
    """
    segments = [s for s in one.pointer.lstrip("#").split("/") if s]
    for _ in range(_TRAVEL_DEPTH):
        hop = next(
            (
                i
                for i in range(len(segments) - 1)
                if segments[i] in _CONJUNCTS
                and segments[i + 1].isdigit()
                and "".join(f"/{s}" for s in segments[:i]) in declared
            ),
            None,
        )
        if hop is None:
            break
        segments = [*segments[:hop], *segments[hop + 2 :]]
    pointer = "#" + "".join(f"/{s}" for s in segments)
    if pointer == one.pointer:
        return one
    return one._replace(
        pointer=pointer,
        attribution=lower_approximate.attribution_for(document, pointer, one.keyword),
    )


def repointed(
    document: str,
    own: Sequence[Approximation],
    edges: Sequence[bundle.Edge],
    finished: Mapping[str, Sequence[Approximation]],
    declared: Collection[str] = (),
) -> tuple[Approximation, ...]:
    """**§8: a declaration travels with the fact it is about.**

    "A reference carries its target's declarations to the referring pointer, re-pointed by
    the same resolution that carried the facts.  The record already inlines a deep copy of
    a target's facts at the referring node; a declaration about those facts is re-pointed
    by that same operation, because a fact and the record of what could not be rendered
    for it must move together or the two sides cannot agree about where either is."

    Here and not in a lowering, for §10's reason: the dependency order finishes every
    target before a referrer is parsed, so this reads a FINISHED module's declarations
    rather than re-deriving a resolution.  A handler holds one node and cannot know who
    references it.

    **The two resolutions move a declaration differently, and each one's own behaviour is
    what decides it.**  There is no third rule and no flag:

    * a REMOTE reference is inlined by ``bundle.record`` as a deep COPY, and the target
      document emits its own module and is graded by its own pairs -- so the declaration
      is COPIED to the referring pointer and the target keeps its own.
    * a LOCAL reference is left in the record and resolved by the document-side reading
      (``harness._normalize``), which REPLACES the referring node with its target -- so
      the fact is read at the referring pointer and at no other, and the declaration
      MOVES.  An entry left behind would name a pointer that reading resolves away, and
      the widening obligation reports such a declaration unproved rather than passing it.

    ``own`` is this document's own declarations in document order and ``finished`` is
    document -> the declarations of a document the order has already finished.  A target
    outside ``finished`` contributes nothing: it refused, so it has no module and no
    declaration, and the referring site refused with it.
    """
    # ``into`` empty on a LOCAL reference is ``$ref: "#"`` -- a document naming itself,
    # which is a recursive type ``compiler.local_reference`` refuses by name.  Excluded
    # here so the fixed point below cannot be handed a fragment that contains every
    # declaration including the ones it produces.
    local = [e for e in edges if e.local and e.into]
    carried = list(own)
    for _ in range(_TRAVEL_DEPTH):
        moved: list[Approximation] = []
        for one in carried:
            sites = [e for e in local if _under(one.pointer, e.into)]
            moved += (
                [one]
                if not sites
                else [_travelled(document, one, e.pointer, e.into) for e in sites]
            )
        if moved == carried:
            break
        carried = moved
    out: dict[tuple[str, str], Approximation] = {(a.pointer, a.keyword): a for a in carried}
    for edge in edges:
        if edge.local or edge.target is None:
            continue
        for one in finished.get(edge.target, ()):
            if _under(one.pointer, edge.into):
                travelled = _travelled(document, one, edge.pointer, edge.into)
                out.setdefault((travelled.pointer, travelled.keyword), travelled)
    # LAST, because a reference's own site may sit INSIDE a conjunct: the fold is one hop
    # further up than the re-pointing and reads its output.
    folded: dict[tuple[str, str], Approximation] = {}
    for one in out.values():
        travelled = _folded(document, one, declared)
        folded.setdefault((travelled.pointer, travelled.keyword), travelled)
    return tuple(folded.values())


def needs(
    sites: Mapping[str, Sequence[bundle.Edge]],
    homes: Mapping[str, Collection[str]] = {},
) -> dict[str, frozenset[str]]:
    """document -> every OTHER document whose module it will import a symbol from.

    The one reading :func:`closure` and :func:`order` both range over, so the set a run
    must write and the order it writes them in cannot disagree about what an edge is.

    **Two kinds of edge and §3a adds the second.**  A ``$ref`` is the first
    (``bundle.Edge``).  A position that RESTATES a vocabulary the bundle names is the
    second: §3a's catalogue makes its type "a REFERENCE to a catalogue entry", and the
    entry lives in the module of the position that NAMES it -- so the importing module
    cannot be written before that one, exactly as a ``$ref``'s cannot, and the symbol
    cannot be imported from a module no run wrote.

    ``homes`` is :meth:`codegen.catalogue.Catalogue.restating` read for its home
    documents, and it is a function of the BUNDLE: a one-document command and a
    whole-population run are handed the same map, which is §9's rule and the whole
    reason §3a's collection is permitted at all.
    """
    out: dict[str, frozenset[str]] = {}
    for document in {*sites, *homes}:
        reached = {
            edge.target
            for edge in sites.get(document, ())
            if edge.target is not None and edge.target != document
        }
        out[document] = frozenset(reached | {h for h in homes.get(document, ()) if h != document})
    return out


def closure(documents: Collection[str], sites: Mapping[str, frozenset[str]]) -> list[str]:
    """``documents`` and every document one of them references, transitively.

    §10: "takes the transitive closure of the named documents over them (a module cannot
    import from a module no run wrote)".  Over the EDGES and not over the walk: the
    closure is computed before any document is parsed, which is what lets the run order
    it and hand each document its targets as data instead of calling back into itself
    from inside a lowering.

    Sorted, so the run is order-independent (P7).  A site whose URI names no document of
    this bundle contributes nothing here and refuses at the site, which is where the
    pointer that carried it is.

    **It takes :func:`needs`' reading and not the edges**, so §3a's catalogue edge is in
    the closure by construction rather than by a second loop here: a module importing a
    catalogue entry's symbol needs that entry's document written, for the same reason a
    ``$ref`` does.
    """
    out: set[str] = set()
    unread = sorted(set(documents))
    while unread:
        document = unread.pop()
        if document in out:
            continue
        out.add(document)
        unread += [target for target in sorted(sites.get(document, ())) if target not in out]
    return sorted(out)


def order(
    documents: Sequence[str], sites: Mapping[str, frozenset[str]]
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
        for target in sorted(sites.get(document, ())):
            if target in held:
                visit(target, stack)
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
    referenced: Mapping[str, dict],
    reserved: frozenset[str],
    carriers: frozenset[str],
    asked: set[tuple[str, str]],
    inherited: Mapping[str, Target | Refusal],
    census: Mapping[str, frozenset[str]],
    vocabularies: Mapping[str, Target] = {},
    restatements: Mapping[tuple[object, ...], Target | str] = {},
    value_lists: Mapping[tuple[object, ...], ValuesImport | str] = {},
    judged: Mapping[str, str] = {},
    *,
    known: Collection[str],
) -> tuple[Module, ir.Module] | Refusal:
    """One document lowered, NAMED, and its carried record checked, as one value.

    ``known`` is the bundle's document set, which :func:`emit` reads ONCE and hands down
    for ``bundle.record`` below: ``docs/plan/architecture.md``, "a set derived from the
    directory is also an argument".  It is threaded rather than read here because this
    function is reached once per document and a scan here is a scan per document -- which
    is the cost ``record``'s own docstring measures.

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
    outcome = lower_document(
        document,
        doc,
        targets,
        named,
        referenced,
        reserved,
        asked,
        inherited,
        vocabularies,
        restatements,
        value_lists,
    )
    if isinstance(outcome, Refusal):
        return outcome
    mod, _ = outcome
    # **§1's domain-scope collision rule: the names ANOTHER document of this domain's
    # surface exports.**  ``census`` is :func:`domain_exports`' answer for this domain,
    # symbol -> the documents that want it, and what this module is compared against is
    # that set minus the symbols only IT wants: a name no other document of the domain
    # exports is not a domain collision, and §4 settles a name inside one module already.
    #
    # Empty on pass one, which is what makes the recursion finite and is not a second
    # answer: pass one is this compiler with the rule switched off, so each position
    # reports its own rung-0 spelling, which is the question the rule asks.
    #
    # The ROOT half is checked against the cheap reading of it as well, because the two
    # must agree: :func:`domain_roots` parses the RAW document where the walk read the
    # RECORD, and ``bundle.record`` inlines a title into a bare-``$ref`` root.  Measured 0
    # disagreements over the bundle and asserted here per document rather than trusted --
    # a disagreement is a property of the inliner and of no document, so §2 makes it a
    # raise.
    if mod.root not in domain_roots(bundle_dir).get(domain(document), frozenset()):
        raise BuildFailure(
            f"{document}: the walk derived the root symbol {mod.root!r} from the record "
            f"and emit.domain_roots derived something else from the raw document, so the "
            f"domain's exported names and this module's own are two readings that "
            f"disagree -- a defect in this compiler and not an outcome of this document"
        )
    elsewhere = frozenset(
        symbol
        for symbol, wanted in census.items()
        if wanted - {document}
    )
    bound = lower_names.assign(mod, carriers, elsewhere, judged)
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
    rec = bundle.record(bundle_dir, document, known)
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


def emit(
    bundle_dir: Path,
    documents: list[str],
    *,
    naming_census: Mapping[str, Mapping[str, frozenset[str]]] | None = None,
) -> Emitted:
    """Lower every named document, and every document one of them references.

    ``naming_census`` is a ROUND of §1's domain-scope collision rule pass one
    (:func:`domain_exports`) and nothing else: the names already known to be taken in
    each domain, which this run resolves against instead of computing them.  ``None`` is
    pass TWO -- the run a caller wants -- and it computes the fixed point first.  Passing
    one is what makes the recursion finite, and it is the only argument here that is not
    the bundle or the document set, because there is only one thing a round needs to be
    told.  Everything else is identical -- the same closure, the same order, the same
    record checks, the same refusals -- so a document that refuses in a round refuses in
    the final run, and the two range over one document set.  What a round does NOT do is
    write text: no module, no record beside it, no alias module, because its one reader
    opens no file.

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
    #: The documents whose own path is also a DIRECTORY of the bundle, so the document
    #: is that package's ROOT and is written to ``<path>/__init__.py`` (the layout rule
    #: beside :func:`write`).  Read from the BUNDLE and bound once, for the reason
    #: ``named`` below is: a module's PATH -- and therefore every import spelling that
    #: names it, and every leading dot in its own import block -- must not depend on
    #: which other documents this run was given.
    package_roots = bundle.package_roots(bundle_dir)
    #: THE BUNDLE'S DOCUMENT SET, read once by the caller that knows the run and threaded
    #: to every reader of it below -- ``bundle.record`` through :func:`decidable` and again
    #: in the write loop, ``bundle.envelope_shape``, ``bundle.declaring_site``.
    #: ``docs/plan/architecture.md``: "a callee that needs the set of a bundle's documents
    #: ... must be **told** it, not go and find it.  Finding it is a directory scan, and a
    #: callee reached once per node performs that scan once per node ... So the set is
    #: computed once per run, by the caller that knows the run, and threaded to every
    #: reader that needs it."  **This function is that caller**: it is handed the bundle
    #: directory and the run's documents, so it is the one frame that knows both.
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
    # **The drifted envelope family, read off the BUNDLE for the reason the three
    # readings above are** (``codegen/lower/envelope.py``): a member's class takes the
    # family's base, so a set derived from the run's document set would make one
    # document's module depend on who else was named, which is §9's own prohibition.
    # Two readers, and both are here: :func:`_envelope_bases` writes the base, and
    # ``lower_envelope.adopt`` gives it to the member classes of each module.
    family = bundle.envelopes(bundle_dir)
    envelope_shape = bundle.envelope_shape(family, known)
    members = frozenset(site for site, _ in family)
    #: The reference sites of each document, in document order: every ``$ref`` the
    #: document states, including a LOCAL one.  A local reference is in the map so that
    #: the one caller that can meet one without going through ``nodes.Reference.head``
    #: is answered by name rather than by the absence of an entry, which is the arm the
    #: binder closure kept for exactly this reason.  **That caller is
    #: ``lower.union._targeted``** -- §4's dispatch derivation asking a QUESTION about a
    #: branch rather than declaring it -- and it was
    #: ``compiler.lower_composition``'s ``$ref``-conjunct arm as well until
    #: ``adcp-client-python-10l.43`` routed that one through ``compiler.local_reference``
    #: (``compiler._conjunct_base``).  Measured after the routing, over the 1,054 portable
    #: documents: **31 sites in 6 documents ask by a local URI, every one of them at a
    #: ``oneOf``/``anyOf`` BRANCH, and all 6 emit** -- ``_targeted`` reads the refusal as
    #: "names no class" and answers ``None``, which is the derivation's own allowed
    #: answer, so no document is charged for it.  0 are at a conjunct.
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
    #: **§3a's CATALOGUE, layer L0, read off the BUNDLE before any document is parsed.**
    #: "This places the catalogue before naming, which §9's census rule permits and §1's
    #: domain-scope collision rule already requires: both read the BUNDLE, which is
    #: pinned and is an input to every run alike, and neither reads the run's document
    #: set."  The call takes ``bundle_dir`` and nothing else, which is that rule held by
    #: the signature -- a collection handed ``documents`` would be the census §9 forbids.
    l0 = catalogue.collect(bundle_dir)
    #: document -> pointer -> the entry that position RESTATES, which is the one thing
    #: the walk consults (``compiler.Module.vocabularies``).  22 positions over 21
    #: documents for this bundle's 15 named vocabularies.
    restating = l0.restating()
    #: The two reference kinds as one reading (:func:`needs`), so the closure and the
    #: order range over §3a's catalogue edge exactly as they range over a ``$ref``'s.
    reaches = needs(
        lowering,
        {d: {home.document for home in rows.values()} for d, rows in restating.items()},
    )
    ordered, refused = order(closure(documents, reaches), reaches)
    #: §1's domain-scope collision rule, PASS ONE's answer, per domain: symbol -> the
    #: documents of that domain whose surface wants it (:func:`domain_exports`).  The
    #: DOMAINS are the ones this run's closure touches and the MEMBERS of each are the
    #: bundle's, which is §9's ruling -- the scope is the domain, a domain's membership is
    #: a function of the bundle, and nothing here reads the run's document set.
    #:
    #: Empty on pass one, which is the recursion's base case.
    census: Mapping[str, Mapping[str, frozenset[str]]] = (
        naming_census
        if naming_census is not None
        else domain_exports(bundle_dir, frozenset(domain(d) for d in ordered))
    )

    lowered: dict[str, tuple[Module, ir.Module, dict]] = {}
    #: document -> the declarations its walk MINTED, before :func:`repointed` moved any.
    #: A remote reference naming a FRAGMENT needs the pointer the declaration was minted
    #: at, because that is the pointer ``bundle.record`` inlines the node from: the local
    #: move has already carried the target's own entry to the target's own referring
    #: property, and a referrer naming ``#/definitions/x`` directly would then match
    #: neither spelling.  Both are offered and :func:`repointed` dedupes by site, so each
    #: referrer re-points off whichever pointer its own fragment names.  Measured at
    #: ``formats/canonical/audio_daast.json`` and
    #: ``core/requirements/daast-asset-requirements.json``, which name
    #: ``core/daast-tracker-constraints.json#/definitions/daast_versions`` and carried
    #: their declaration at a pointer the document states no such keyword at until this
    #: map existed.
    minted: dict[str, tuple[Approximation, ...]] = {}
    #: ``$ref`` URI -> the NODE it names, for §2's intersection rule
    #: (:meth:`compiler.Module.resolve_node`).  **Run-level and not per document**, and
    #: the reason is whose declaration that rule reads: it compares two property
    #: DECLARATIONS, and one of them is a BASE's, so the URI it asks about is a site of
    #: the base's document and not of the one being lowered.  Filled as the order
    #: finishes each document, which is early enough by construction -- a base precedes
    #: the document composing it, and the base's own targets precede the base.
    #:
    #: **A FRAGMENT URI is in here too, and it held only document ROOTS until
    #: ``adcp-client-python-10l.72``.**  The rule is about the two TARGETS, and a
    #: reference naming ``…/vast-tracker-constraints.json#/definitions/vast_versions``
    #: names one as squarely as a reference naming a root does; answering ``None`` for it
    #: made the predicate read a pair of resolvable references as two it could not read,
    #: and refuse.  ``bundle.node_at`` is the one pointer navigator, so the fragment half
    #: is resolved by the same reading ``bundle.record`` inlines a target with.
    referenced: dict[str, dict] = {}
    #: document -> the reference sites its walk ASKED about, kept whatever the outcome:
    #: a refused document has no module to hand back and the sites it reached before
    #: refusing are what say whether their targets are documents this run owes.
    asked: dict[str, set[tuple[str, str]]] = {}
    #: target document -> the ``(URI, pointer)`` pairs that name a node of it, so the
    #: fill above is a lookup rather than a scan per document.  A reference with no
    #: fragment carries the empty pointer and names the root.
    spellings: dict[str, set[tuple[str, str]]] = {}
    for edge in found:
        if edge.target is not None:
            spellings.setdefault(edge.target, set()).add((edge.uri, edge.into))

    def answer(document: str, edge: bundle.Edge) -> Target | Refusal:
        """What ONE reference site resolves to, for the document that is about to
        write the import.

        ``document`` is the REFERRING document and is a parameter rather than the
        edge's own, because the two differ at exactly the sites §2's intersection rule
        reaches: a declaration a composing document inherits carries the BASE's
        references, and the module spelling and the importables are then a function of
        the composing document and the base's target (D1).  Everything else is read off
        the edge.
        """
        if edge.local:
            # A LOCAL reference names a node of the document being written, so there
            # is no module to import from and nothing for a binding to resolve:
            # ``references.lower`` branches on the empty document half first and asks
            # ``compiler.local_reference`` for the symbol this module declares.  This
            # stays as the loud answer for the one caller that reaches a reference
            # another way -- ``lower.union._targeted``, §4's dispatch derivation, which
            # reads it as "this branch names no class" and answers ``None`` -- rather
            # than being left out and reporting a pointer as a document the bundle
            # does not hold.
            #
            # **It is NOT a BuildFailure, and the reason is measured**
            # (``adcp-client-python-10l.43``).  ``lower_composition``'s conjunct arm used
            # to reach here too, and its documents were charged a VERDICT for a routing
            # gap -- ``core/account-identity-change-preview.json`` and
            # ``core/registry-event.json``, plus 2 through the chain; all 4 emit now that
            # ``compiler._conjunct_base`` branches on the parser's document half.  What is
            # left is ``_targeted``'s 31 sites in 6 documents, all at a ``oneOf``/``anyOf``
            # BRANCH and all 6 emitting, so the arm has a live caller and raising §2's
            # exception here would fail the build on 6 documents that are fine.  It also
            # cannot raise on a lazy caller's behalf: :func:`resolve` computes this map
            # EAGERLY over every edge, so the 405 local reference sites of this bundle all
            # pass through here whether or not anyone reads the answer.
            return Refusal(
                "$ref",
                edge.pointer,
                f"{edge.uri} is a pointer into this document, which is not a binding "
                "at all -- the walk resolves one through compiler.local_reference and "
                "never through a binder",
                kind=Kind.VERDICT,
            )
        if edge.target is None:
            return Refusal(
                "$ref",
                edge.pointer,
                f"{edge.uri} names no document of this bundle",
                kind=Kind.VERDICT,
            )
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
            return Refusal(
                "$ref",
                edge.pointer,
                f"{edge.uri}: the dependency order has not reached its target, "
                "because no reference the walk lowers a type or an import from "
                "reaches this position (bundle.lowered_references: a reference at a "
                "RULE position lowers nothing, and one inside a definitions entry "
                "nothing names is at a position no class names)",
                kind=Kind.VERDICT,
            )
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
            return Refusal(
                "$ref",
                edge.pointer,
                f"its target {wanted} is refused: {r}",
                kind=Kind.CHAINED,
                through=r,
            )
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
            #    symbol the target DECLARES.  **So the CHAIN is followed to the
            #    module that declares it** (``bundle.declaring_site``), which is the
            #    answer the comment standing here deferred to "the step whose
            #    population reaches one" -- and this is that step.  Following it is
            #    the OPPOSITE of a re-export: the symbol is taken from its declarer,
            #    one import path per class, which is section 1's own rule.
            if edge.into not in bound.symbols:
                hop = bundle.declaring_site(bundle_dir, known, edge)
                if hop is not None:
                    #: The chain's own answer, plus the ``description`` the hop carried:
                    #: §5's ``$ref`` row makes a sibling's description authoritative and
                    #: ``bundle.record`` inlines it at the REFERRING pointer, so it
                    #: travels with the resolution (:attr:`compiler.Target.described`)
                    #: and ``lower.references`` records it for the field.
                    chained, described = hop
                    resolved = answer(document, chained)
                    if isinstance(resolved, Refusal) or described is None:
                        return resolved
                    return dataclasses_replace(resolved, described=described)
                return Refusal(
                    "$ref",
                    edge.pointer,
                    f"{edge.uri}: its target {edge.target} declares no symbol at "
                    f"{edge.into} (the walk either does not reach that node, or the "
                    "node is itself a $ref whose symbol that module imports rather "
                    "than declares)",
                    kind=Kind.DEFERRED,
                )
            symbol = bound.symbols[edge.into]
        # ``kind`` is WHICH of §4's three outcomes the target's node became
        # (:func:`compiler.target_kind`), and it is what every row wanting the target as
        # a BASE reads.  ``shape`` is ``None`` for a target that is not a class at all --
        # D2's root-scalar alias, and a named node that is not one either -- which is
        # what lets a composing row refuse it as a base rather than writing a
        # module that cannot be imported.
        #
        # **The SHAPE crosses the module boundary with its symbols BOUND**, which is
        # what makes a shape recorded by pointer readable in another module: the
        # target was named before this document was parsed (§10's order), so its own
        # symbol table is what binds the re-used field's type.  WHERE each of those
        # symbols is importable from crosses beside it (:func:`_importable`), which
        # is the same table ``symbol`` above is read off and the record of what the
        # target imported -- so a composing subclass takes each symbol from its
        # declarer, which is §1's one import path per class.
        #
        # **A UNION BASE CROSSES AS ``TargetKind.UNION``, and the shape crosses with
        # it** (``adcp-client-python-10l.55``).  §5's ``$ref`` row at CONJ is one
        # sentence -- "where it is not a class declaring fields -- a scalar, an enum,
        # a container, or a UNION ROOT, whose instance is one of its branches -- it is
        # not a class a model can extend: the target is this node's own TYPE" -- and
        # §4's union row is another: a ``$ref`` BRANCH is "a class with two bases: the
        # target, which supplies the fields, and the union's base, which supplies the
        # dispatch".  The two positions give a union root OPPOSITE answers, so what
        # crosses is the FACT and not one position's verdict on it: this builds the
        # kind off ``ClassDecl.branches`` -- the field that says the instance is one of
        # the branches, and the one ``render`` writes ``_branch_models`` off -- and
        # each row reads the kind its own position decides on.
        #
        # Nulling the shape here was that verdict baked in, and it was read by a third
        # position as "not a class": §4's branch row refused
        # ``core/assets/asset-union.json`` at ``/oneOf/3`` because ``VASTAsset`` had no
        # shape, with a sentence about a scalar alias that ``VASTAsset`` is not.
        #
        # **A UNION BASE'S BRANCHES CROSS WITH IT, as one :class:`compiler.Target` each**
        # (``adcp-client-python-10l.68``).  §5's ``$ref`` row at CONJ distributes a union
        # target over a node that declares fields of its own, and the composing module
        # then declares one class per branch -- so it needs each branch's symbol, its
        # shape and §4's three naming facts, none of which it can read off the target's
        # declarations.  ``compiler.branches_of`` is the one derivation and it reads
        # ``ClassDecl.branches``, which already names the branch POINTERS; this closure is
        # what turns a pointer of the target's module into a :class:`compiler.Target`, and
        # the ROOT's own answer is built by the same call, so a branch and a root cannot
        # be assembled two different ways.
        #
        # ``declarer`` is bound once, past the ``edge.target is None`` screen above: the
        # closure is what
        # carries it into every branch's answer, and a narrowing a closure cannot see is
        # exactly what the type checker reports here.
        declarer = edge.target
        module = relative_module(document, declarer, package_roots)
        importables = _importable(
            document, declarer, bound.symbols, mod.imported, package_roots
        )

        def at(pointer: str, spelled: str) -> Target:
            shape = mod.shapes.get(pointer)
            hop = mod.hops.get(pointer)
            declared = mod.at.get(pointer)
            return Target(
                module,
                spelled,
                None if shape is None else _bound_shape(shape, bound.symbols),
                declarer,
                kind=compiler.target_kind(declared),
                imports=importables,
                naming=hop if isinstance(hop, lower_names.Branch) else None,
                branches=compiler.branches_of(
                    declared, lambda p: at(p, bound.symbols[p])
                ),
            )

        return at(edge.into, symbol)

    def resolve(document: str) -> dict[tuple[str, str], Target | Refusal]:
        """This document's reference sites, resolved: §5's ``targets``.

        Every answer the binder closure returned, computed here instead -- and computed
        BEFORE the document is parsed, which is what the dependency order buys: each
        target is either in ``lowered`` or in ``refused``, so nothing recurses and no
        stack says which documents are in flight.
        """
        return {(e.uri, e.pointer): answer(document, e) for e in sites.get(document, ())}

    def inherited_sites(document: str) -> dict[str, Target | Refusal]:
        """The reference sites this document inherits from the classes it COMPOSES,
        resolved for this document and keyed by URI alone.

        **§2's intersection rule is what asks for it, and ``referenced`` already carries
        the other half of the same answer.**  That map's own reason -- "the URI it asks
        about is a site of the base's document and not of the one being lowered" -- is
        this one's: where a conjunct restates a property the base declares, the field
        carries the INTERSECTION, so every key the base alone declares reaches the
        composed node, and a key the base declares as a ``$ref`` carries a reference
        the composing document does not spell.  The site is real -- draft-07 applies
        both conjuncts to the same instance, so the composed class holds that property
        and must import its type -- and it is the base's, which is why it is keyed by
        the URI and not by a pointer: the pointer it arrives at is the COMPOSING
        document's, derived from the restating conjunct, and no edge of either document
        carries it.

        Keyed by URI alone is sound because a no-fragment URI resolves to one target
        and a fragment URI to one node of one target, so the answer is a function of
        the URI and the referring document -- the pointer appears in this map's answers
        only inside a refusal's text, and a refused base is a refused composition.

        **CONJ and not every reference**, read off :attr:`bundle.Edge.position` rather
        than recovered from a pointer string: a base is what a conjunct names, so the
        declarations this document inherits are the ones its ``allOf`` conjuncts' targets
        declare -- transitively, because :class:`compiler.Shape` is transitive and a
        base's own base contributes keys to it. A reference at any other position names
        a target this document holds as a TYPE, and a type crosses as an import the
        walk already has a site for.
        """
        out: dict[str, Target | Refusal] = {}
        for base in sorted(composes.get(document, ())):
            for uri, edge in sorted(composes_sites.get(base, {}).items()):
                out.setdefault(uri, answer(document, edge))
        # **A BASE's own LOCAL spelling, read from here as the fragment reference it is**
        # (:func:`based_edges`, ``adcp-client-python-97w``).  ``composes_sites`` excludes a
        # local edge by construction, and the composed node needs the answer: §5's
        # ``properties`` row composes two object declarations as an ``allOf`` of the two,
        # so where the base spells its half as a pointer into its own text,
        # ``compiler._intersection`` plants that very pointer as a conjunct of a node
        # belonging to THIS document.  Asked LAST, so a URI either the document or a
        # base's absolute text spells keeps the answer it already has.
        for uri, (edge, _node) in sorted(based_edges(document).items(), key=lambda kv: kv[0]):
            out.setdefault(uri, answer(document, edge))
        return out

    def based_edges(document: str) -> dict[str, tuple[bundle.Edge, dict]]:
        """Each ``$ref`` LOCAL TO A BASE'S OWN DOCUMENT, re-based as the FRAGMENT
        reference it is when read from ``document``.

        **THE ONE RE-BASING, and both halves of §2's rule read it**
        (``adcp-client-python-10l.72`` for the predicate, ``adcp-client-python-97w`` for
        the field).  §2's intersection rule reads a base's declaration beside this
        document's own, and a base may declare a property as a pointer into ITS OWN text:
        ``core/vast-tracker-constraints.json`` declares ``vast_versions`` as
        ``{"$ref": "#/definitions/vast_versions"}``, and
        ``core/response-payload-jws-envelope.json`` declares ``payload`` as
        ``{"$ref": "#/definitions/response_payload"}``.  A spelling relative to another
        document is relative to another document, so neither :attr:`referenced` nor
        ``composes_sites`` can hold one: both are keyed by the URI alone, across the run.

        Read from the composing document, such a spelling is an ORDINARY fragment
        reference into the base -- which is what this returns, and the whole of the
        re-basing: ``local`` goes false, ``target`` becomes the base, and ``into`` is the
        pointer half ``bundle.split_ref`` reads.  Nothing is rewritten and no URI is
        constructed; the edge is the same reference STATED from the standpoint that can
        resolve it, so :func:`answer` and ``bundle.node_at`` each do what they already do.
        The two readers take the two halves they need: :func:`based_nodes` the NODE, for
        the predicate, and :func:`inherited_sites` the TARGET, for the import the composed
        field needs (P2: a cross-document reference is an import and not a copy).

        **Per DOCUMENT and not run-level, which is exactly the split
        :func:`inherited_sites` already is**, and for the same reason: the answer is a
        function of the composing document, because it is that document's BASES whose
        text these spellings belong to.

        **A spelling this document ITSELF writes is left out, and one two bases resolve
        DIFFERENTLY is dropped.**  One resolver answers both sides of the comparison, so a
        spelling that names two nodes in the documents in view has no single answer and
        ``None`` is the undecidable arm -- the safe direction, which refuses.  Measured
        over the 1,054 portable documents: **0 such collisions**, in either form -- 45 of
        the documents a composition reaches spell a local reference and no composing
        document shares one of those spellings with a base.  The screens are here because
        the guarantee is the bundle's and not the rule's.
        """
        own = {edge.uri for edge in sites.get(document, ()) if edge.local}
        out: dict[str, tuple[bundle.Edge, dict]] = {}
        seen: dict[str, dict] = {}
        collided: set[str] = set()
        for base in sorted(composes.get(document, ())):
            if base == document or base not in lowered:
                continue
            for edge in sites.get(base, ()):
                if not edge.local or edge.uri in own:
                    continue
                into = bundle.split_ref(edge.uri)[1]
                node = _node_or_none(lowered[base][2], into)
                if node is None:
                    continue
                if seen.setdefault(edge.uri, node) != node:
                    collided.add(edge.uri)
                    continue
                out.setdefault(
                    edge.uri, (edge._replace(local=False, target=base, into=into), node)
                )
        return {uri: pair for uri, pair in out.items() if uri not in collided}

    def based_nodes(document: str) -> dict[str, dict]:
        """The node each of :func:`based_edges`'s re-based references names, for §2's
        intersection rule reading a BASE's declaration (``compiler.Module.referenced``).

        The NODE half of the one re-basing, resolved by the same reading the run resolves
        every other fragment with -- so a base's local pointer and a composing document's
        absolute reference to the same node are one answer, which is the whole of
        ``adcp-client-python-10l.72``.

        **The node is the one :func:`based_edges` already resolved**, carried beside the
        edge rather than resolved a second time here.  It was resolved twice, and the
        second reading indexed ``lowered`` by ``edge.target`` -- a ``str | None``, because
        :attr:`codegen.bundle.Edge.target` is ``None`` for a LOCAL reference -- which was
        §14 step 6's fifth error.  The re-based edge's target is a base's document by
        construction, and carrying the pair says that where a narrowing of the field could
        only assert it.
        """
        return {uri: node for uri, (_edge, node) in based_edges(document).items()}

    #: document -> the documents its ``allOf`` conjuncts compose, transitively.  Filled
    #: as the order finishes each document, which is early enough by construction: a
    #: base precedes the document composing it.
    composes: dict[str, frozenset[str]] = {}
    #: document -> every non-local reference site of its own text, by URI.  What a
    #: composing document inherits one of (:func:`inherited_sites`).
    composes_sites: dict[str, dict[str, bundle.Edge]] = {
        document: {e.uri: e for e in edges if not e.local and e.target is not None}
        for document, edges in sites.items()
    }
    for document, edges in sites.items():
        direct = {e.target for e in edges if e.position in BASE_POSITIONS and e.target}
        # **A document INHERITS FROM ITSELF**, and that is §8's union-branch pairing read
        # as a reference site rather than as a fact: "a sibling beside a union lowers by
        # COMPOSITION -- the siblings become a base class; each branch becomes a subclass
        # narrowing what it narrows", so a branch restating a property the ROOT declares
        # composes the root's own declaration, and a key the root declares through a
        # ``$ref`` carries a reference at a pointer the branch's composition arrives at
        # and no edge of any document has.  The document whose sites that reference
        # belongs to is THIS one, which is why self is in the set.
        #
        # It cannot shadow a site the document spells: :meth:`compiler.Module.target`
        # asks :attr:`compiler.Module.targets` first and reads this map only where that
        # has no entry for the ``(uri, pointer)`` pair.
        composes[document] = frozenset(direct) | {document}
    # The transitive step, taken to a fixed point: a base's own bases contribute keys to
    # the :class:`compiler.Shape` a composing document reads, so their sites are
    # inherited too.  Over this bundle it settles in a handful of passes.
    while True:
        grown = {
            d: b | frozenset().union(*(composes.get(t, frozenset()) for t in b))
            for d, b in composes.items()
        }
        if grown == composes:
            break
        composes = grown


    def vocabularies(document: str) -> dict[str, Target]:
        """§3a's catalogue entries this document RESTATES, as the walk's own table.

        The three things the walk cannot derive, derived in the one place that knows
        them: the SPELLING, which D1 makes a function of the two document paths; the
        SYMBOL, which is §4's and belongs to the module that DECLARED it (§10's order
        puts that module in ``lowered`` before this one is parsed, so this is a lookup);
        and the DOCUMENT, so a third module composing this one takes the symbol from its
        declarer rather than from here (:class:`compiler.Importable`).

        **A home whose own document REFUSED contributes nothing**, and the position then
        declares its own class exactly as it does today.  That is the conservative
        direction and the only one available: a refused document writes no module, so
        there is no symbol to import, and refusing this document too would charge it for
        a defect in another.  Measured over the 1,054 portable documents: 0 refusals, so
        the clause selects nothing and is the guard that says so.
        """
        out: dict[str, Target] = {}
        for pointer, home in sorted(restating.get(document, {}).items()):
            if home.document == document:
                continue
            held = lowered.get(home.document)
            if held is None:
                continue
            symbol = held[1].symbols.get(home.pointer)
            if symbol is None:
                continue
            out[pointer] = Target(
                # ``package_roots`` and not the run's ``packages``, which is the same
                # reading §5's ``$ref`` row already takes (:func:`resolve`'s own
                # ``relative_module`` call): the LEADING DOTS count hops up from the
                # importing module's FILE, and a document whose own path is also a
                # directory of the bundle is written to ``<path>/__init__.py`` one level
                # down.  The run's ``packages`` set is accumulated as files are written
                # and is EMPTY while the fold is still lowering, so reading it here
                # spelled ``brand/__init__.py``'s import of *Update Frequency* as
                # ``.enums.update_frequency`` -- one dot short, and an ImportError that
                # took the whole ``brand`` package out of the import census with it.
                module=relative_module(document, home.document, package_roots),
                symbol=symbol,
                document=home.document,
                # §3a's L0 is a VOCABULARY, and §4 makes an enumeration an annotation and
                # never a class: "D2 makes it an ``Annotated`` alias and subclassing one
                # is a ``TypeError`` at import, so every row refuses it as a base".
                kind=compiler.TargetKind.ANNOTATION,
            )
        return out

    def restatements(document: str) -> dict[tuple[object, ...], Target | str]:
        """§3a's catalogue keyed on the VALUE LIST, for this document's own walk.

        :attr:`compiler.Module.restatements` states what the two kinds of row are for and
        measures each.  What is derived here is the same three things
        :func:`vocabularies` derives -- the spelling, the symbol and the home's document --
        plus the one answer that is not a Target at all: where the home is a position of
        THIS document, the reference is local and the value is the home's POINTER, which
        ``lower/names.py`` resolves to a symbol in the same pass that names the home.

        **The home's own pointer is never a key**, which is what keeps the home declaring:
        a map whose entry pointed its own home at itself would leave the value list
        declared nowhere.

        **It is NOT narrowed to the documents that STATE the entry**, and that is the
        composed case's whole requirement: ``core/postal-area.json`` states none of the
        three per-country vocabularies and re-lowers all three.  Nothing is widened by
        that, because this collection sees every position of the bundle that states a
        value list -- so an enum node in a document that states none of them is a node
        some base stated and this document re-derived, which is the same vocabulary by
        construction rather than by coincidence.
        """
        out: dict[tuple[object, ...], Target | str] = {}
        homes: list[tuple[tuple[object, ...], catalogue.Stated]] = [
            (entry.members, entry.naming) for entry in l0.entries.values()
        ]
        # **A value list the bundle states at EXACTLY ONE position is homed there too**
        # (:attr:`catalogue.Catalogue.alone`), and the one case that reaches is the one
        # ``codegen/vocabularies.py`` records as refused there: ``["DE", "CH", "AT"]`` is
        # stated once, at ``core/postal-country-system.json``'s ``anyOf`` branch, and
        # ``core/postal-area.json`` re-lowers that very node under §2's intersection rule
        # and declared a second class over it.  One position, so §3a's three-way naming
        # split has nothing to decide and nothing is judged: what is needed is a HOME, and
        # a single stating position is one by construction.
        #
        # **Only where the home is ANOTHER document**, which is what keeps §4's own scope
        # intact: a LOCAL pointer here would collapse two positions of one document by
        # VALUE LIST, and §4's key is node equality -- "widening §4's key from node
        # equality to the value list is a change to THAT rule and is not taken here".  The
        # same-document case is ``lower/names.py``'s ``the_value_lists``, which writes the
        # value list once and leaves both types standing.
        homes += [
            (at.members, at) for at in l0.alone.values() if at.document != document
        ]
        for members, home in homes:
            if home.document == document:
                out[members] = home.pointer
                continue
            held = lowered.get(home.document)
            if held is None:
                continue
            symbol = held[1].symbols.get(home.pointer)
            if symbol is None:
                continue
            out[members] = Target(
                module=relative_module(document, home.document, package_roots),
                symbol=symbol,
                document=home.document,
                kind=compiler.TargetKind.ANNOTATION,
            )
        return out

    def value_lists(document: str) -> dict[tuple[object, ...], ValuesImport | str]:
        """§3a's SHARED VALUE LIST, for the positions this document DECLARES a type at.

        The other half of §3a's split, and the half :func:`restatements` is not: that one
        says "this position is the same type as one declared elsewhere, so import it", and
        this one says "this position is a DIFFERENT type over the same value list, so
        declare it and take the values from one place".

            "the **VALUE LIST** is a module-level constant in the catalogue layer, written
            once per distinct member set; the **NAMED TYPE** is constructed from it at each
            position that needs one, keeping the name §4 derives and keeping the types
            distinct."

        Every shared value list of the bundle is offered to every document, for
        :func:`restatements`' own reason: a document that STATES none of them can still
        declare a type over one, because §2's intersection rule hands a base's node back
        and the composing document lowers it again.  A document that declares no type over
        a value list writes no import for it, so the table is wider than the answer by
        construction and never by coincidence.

        Only a ``ValuesImport``: §3a's catalogue module is never the module being lowered,
        because a document's module is the module of a DOCUMENT and the catalogue's has
        none.  The same-module case has its own answer and its own pass
        (``lower/names.py``'s ``the_value_lists``), which is why the walk's table takes a
        ``str`` at all -- the type says the two cases share one slot on the module.
        """
        return {
            shared.members: ValuesImport(
                module=relative_to_module(
                    document,
                    vocabularies_module(catalogue.namespace(shared.documents)),
                    package_roots,
                ),
                symbol=lower_enum.values_name(shared.members),
            )
            for shared in l0.shared.values()
        }

    def judged(document: str) -> dict[str, str]:
        """§3a's JUDGED NAME for the catalogue entries this document DECLARES.

        ``codegen/vocabularies.py``'s rows, read at the one pointer each entry is declared
        at (``catalogue.Entry.naming``).  §3a's table is what admits them -- "a name is the
        bundle's when every token in it is stated at that vocabulary's own positions" --
        and ``lower/names.py``'s ``assign`` takes them as an extra FIRST RUNG, so §4's
        collision rule still decides and a judged name that collides falls to the chain
        the position would have been named by anyway.

        Empty for every entry the bundle TITLES: there the title is the name §4 already
        derives at the naming position, measured at all of them, so a row would be a second
        statement of the same answer.
        """
        return {
            entry.naming.pointer: entry.name
            for entry in l0.entries.values()
            if entry.name is not None and entry.naming.document == document
        }

    for document in ordered:
        doc = bundle.read(bundle_dir, document)
        outcome = decidable(
            bundle_dir,
            document,
            doc,
            resolve(document),
            named.get(document, frozenset()),
            # The run's own reading of every reference spelled absolutely, and beside it
            # the spellings that are relative to a BASE's document (:func:`based_nodes`).
            # The base's half is asked SECOND the way ``inherited_targets`` is, so a URI
            # the run already resolves keeps the run's answer.
            {**based_nodes(document), **referenced},
            render.RESERVED,
            render.CARRIERS,
            asked.setdefault(document, set()),
            inherited_sites(document),
            census.get(domain(document), {}),
            vocabularies(document),
            restatements(document),
            value_lists(document),
            judged(document),
            known=known,
        )
        if isinstance(outcome, Refusal):
            refused[document] = outcome
            continue
        mod, bound = outcome
        # **§8's "a declaration travels with the fact it is about"**, applied where §10's
        # order makes it a lookup: every target this document references is finished, so
        # its declarations are read rather than re-derived (:func:`repointed`).
        minted[document] = bound.approximations
        bound = dataclasses_replace(
            bound,
            approximations=repointed(
                document,
                bound.approximations,
                lowering.get(document, ()),
                {
                    d: (*minted.get(d, ()), *held[1].approximations)
                    for d, held in lowered.items()
                },
                frozenset(bound.symbols),
            ),
        )
        # **The drifted envelope family's base, given to every member class of this
        # module** (``codegen/lower/envelope.py``).  A pass over the FINISHED module, in
        # the shape ``lower/names.py``'s is one, and it runs here rather than inside a
        # handler because the fact is a property of a class's whole node and not of any
        # one keyword on it.  The membership test is the SHAPE at the node the
        # declaration names, so this adds nothing that depends on which documents the run
        # includes (§9), and a module with no member is returned unchanged.
        bound = lower_envelope.adopt(bound, members)
        lowered[document] = (mod, bound, doc)
        # The node each reference to this document names, for §2's intersection rule and
        # for nothing else.  Written when the document FINISHES, so a refused document
        # contributes none and the rule treats such a pair as unordered -- which is the
        # safe direction and is what the binder answered for a refused target before.
        #
        # A pointer naming no node is left out rather than raised on: the same reading
        # answers ``None`` for it, which is this map's own undecidable arm, and
        # ``bundle.record`` is where a reference naming no node earns its refusal.
        for uri, into in sorted(spellings.get(document, ())):
            node = _node_or_none(doc, into)
            if node is not None:
                referenced[uri] = node

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
        rel = module_file(document, package_roots)
        if naming_census is not None:
            # **A ROUND answers one question and writes no file.**  §1's rule needs the
            # export set and nothing else, so the TEXT is skipped -- ``render.module``
            # over 1,054 modules, the record dumped beside each one, and D5's alias
            # module.  What is kept is everything the export set is a function of: the
            # walk, the naming pass, the record checks and the refusals, so pass one and
            # pass two range over one document set and agree about every name.
            out.surface[module_path(document)] = dict(bound.exports)
            out.emitted[document] = module_name(document)
            continue
        out.files[f"{rel}.py"] = render.module(
            bound, exported(mod, bound, composed.get(document, frozenset()))
        )
        out.emitted[document] = module_name(document)
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
        # §1's export set, carried through from the naming pass unchanged: this is a
        # record and not a second derivation (:attr:`Emitted.surface`).
        out.surface[module_path(document)] = dict(bound.exports)
        if mod.drops:
            out.drops[document] = dict(mod.drops)
        if mod.carries_nothing:
            out.carries_nothing[document] = list(mod.carries_nothing)
        if bound.approximations:
            out.approximations[document] = list(bound.approximations)
        out.asked[document] = set(asked.get(document, ()))
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
        record = bundle.record(bundle_dir, document, known) if bundle.references(doc) else doc
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
    # ``setdefault``, because a package whose bundle path is ALSO a document's has
    # already had its ``__init__.py`` written above -- that document IS the package's
    # root (the layout rule beside :func:`write`).  A plain assignment here replaced
    # ``brand/__init__.py``'s 113 classes with the empty marker, which is the same
    # unimportable-module defect the rule removes, arriving from the other side.
    if naming_census is not None:
        # A round's whole answer is :attr:`Emitted.surface`; the package markers, D5's
        # alias module and the envelope bases are TEXT and no reader of a round opens a
        # file (:func:`domain_exports`).
        return out
    # **§3a's CATALOGUE modules, over the BUNDLE and not over the run** -- the same scope
    # ``_envelope_bases`` below has and for the same sentence: a value list's namespace is
    # a function of the positions that state it, which is a reading of the pinned bundle,
    # so a one-document command writes the same file as a whole-population emission (§9).
    #
    # Written for every namespace the catalogue names, whether or not THIS run lowered a
    # document that references one.  The alternative is a module whose content depends on
    # who else was named, which is the defect §9 exists to prevent and the one thing a
    # module with no document could still be made to have.
    #
    # It goes on the EXPORT RECORD with an empty export set, which is §3a's own reason for
    # moving that record's key: "every document already maps to the module it produced, so
    # the key becomes that module and a catalogue module is simply one with no document."
    # Nothing in it is a type, so there is nothing for §1's surface to re-export, and
    # :func:`domain_modules` reads that absence rather than being told about it.
    for namespace, declarations in sorted(vocabularies_modules(l0).items()):
        rel = vocabularies_module(namespace)
        out.files[f"{rel}.py"] = render.vocabularies_module(declarations)
        out.surface.setdefault(rel, {})
        parts = rel.split("/")[:-1]
        packages.update("/".join(parts[: i + 1]) for i in range(len(parts)))
    for pkg in packages:
        out.files.setdefault(f"{pkg}/__init__.py", "")
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
    # **§1's DOMAIN SURFACE: one public module per domain, re-exporting every name §1's
    # export set holds** (:func:`domain_modules`).  Beside the tree rather than inside it
    # because ``_schemas`` is private (P8) and this is the one path a consumer reaches a
    # type at.
    out.beside.update(domain_modules(out.surface))
    # **The envelope bases, over the BUNDLE and not over the run** -- which is the one
    # way this artifact differs from the alias module beside it.  ``constraints.py``
    # holds the shapes a run resolved, so it is a function of the run's document set;
    # a family's base is derived from every node of the bundle that states the family's
    # shape, so its text is the same whichever documents a run was named, and the
    # member modules that import it are the same text too (§9).
    #
    # Written on every run for the reason the alias module's ``URL_LINE`` is: a consumer
    # imports the base to annotate their own code, so it is declared whatever a run met.
    out.beside[f"{lower_envelope.MODULE.rsplit('.', 1)[1]}.py"] = _envelope_bases(
        bundle_dir, envelope_shape
    )
    # The refusal REPORT is not a file in the tree.  It was, and the documented
    # one-document command then rewrote it with that run's refusals -- which are
    # none -- so running the command in the README damaged the committed tree and
    # reddened the gate.  A report about documents this package does NOT contain
    # has no place inside the shipped package anyway: `main` prints it, and the
    # suite reads `Emitted.refusals` from the run it just made.
    return out


#: §3a's CATALOGUE module, as the last segment of its path inside its namespace.
#: PRIVATE, like ``_schemas`` itself and for the same reason (P8): nothing here is a type
#: a consumer writes, so there is no public path for one to be reached at.
VOCABULARIES = "_vocabularies"


def vocabularies_module(namespace: str) -> str:
    """D1's module for §3a's CATALOGUE in one namespace, as a path under the tree.

    **There is no document, and that is the point rather than a gap** (§3a, 2026-11-02):
    "A vocabulary with no naming position needs a module of its own, and that module has
    no document behind it.  **A pseudo-document path is refused**: it names a file the
    bundle does not contain, and every reader that resolves a record from a key would
    then be lying about where the schema came from."

    Inside the namespace's own directory, so :func:`module_domain` answers the namespace
    with no second derivation -- §1's domain is the first segment of a module's path and
    this module's first segment IS the namespace §3a's scope rule named.  For the SHARED
    namespace that directory is ``common``, which §3a fixes: "The shared namespace is
    ``adcp.types.common``, one place and not one per layer."
    """
    return f"{namespace}/{VOCABULARIES}"


def vocabularies_modules(l0: catalogue.Catalogue) -> dict[str, tuple[ir.ValuesDecl, ...]]:
    """namespace -> the VALUE LISTS §3a writes once in that namespace's catalogue module.

    §3a: "the **VALUE LIST** is a module-level constant in the catalogue layer, written
    once per distinct member set", and :func:`catalogue.namespace` is where it lives --
    "an entry lives in the NARROWEST namespace that contains every position referencing
    it ... from one domain → that domain; from more than one domain → the shared
    namespace".

    **A function of the BUNDLE and never of the run** (§9), which is what makes a
    one-document command write the same file as a whole-population emission: the argument
    is ``codegen/catalogue.py``'s reading of the bundle and nothing here sees the
    document set.  It is the same scope ``_envelope_bases`` already has and for the same
    sentence.

    The ORDER inside a module is the value list's own spelling, which is a function of
    the value lists alone -- not of the order a mapping was built in (P7) and not of
    which document the walk reached first.

    The list carries no MEMBER NAME and no DESCRIPTION, and both are measured rather than
    overlooked.  A member NAME is a class-body statement at each type over the list, which
    is what a consumer's type checker reads (:attr:`ir.EnumDecl.values`).  A block
    ``enumDescriptions`` is stated per POSITION, and the two positions of this bundle that
    state one over a shared value list -- *Canonical Media Buy Action Mode* and *Media Buy
    Action Mode* -- describe their members DIFFERENTLY, so a description belongs to the
    type and the class body is where the renderer puts it.
    """
    held: dict[str, dict[str, ir.ValuesDecl]] = {}
    for shared in sorted(l0.shared.values(), key=lambda s: (s.kind, repr(s.members))):
        into = held.setdefault(catalogue.namespace(shared.documents), {})
        spelled = lower_enum.values_name(shared.members)
        if spelled in into:
            raise BuildFailure(
                f"{spelled!r} is the name both {list(into[spelled].values)!r} and "
                f"{list(shared.members)!r} spell for their value list: the separator is a "
                "character a member name can hold, so the two are not told apart -- which "
                "is a defect in this compiler and not an outcome of any document"
            )
        into[spelled] = ir.ValuesDecl(
            name=spelled, kind=shared.kind, values=shared.members
        )
    return {
        namespace: tuple(by_name[name] for name in sorted(by_name))
        for namespace, by_name in held.items()
    }


def domain_modules(surface: Mapping[str, Mapping[str, str]]) -> dict[str, str]:
    """§1's DOMAIN SURFACE: ``<domain>.py`` per domain plus ``__init__.py``, as text.

    §1: "a document compiles to a module at its own path under a private tree ... **and is
    re-exported from** ``adcp.types.<domain>``, where the domain is derived from the
    document's own path".  This is that re-export, and it is **GENERATED from the same walk
    as everything else** -- the names come from :attr:`Emitted.surface`, which is
    ``lower/names.py``'s own record of §1's export set -- so a new document appears in its
    domain with nobody editing a list.

    **A RE-EXPORT and never a declaration**, which is the half §1's one-path rule turns on:
    ``from ... import X as X`` binds the very class the private module built, so
    ``adcp.types.core.AssetRequirementsJavaScript is
    adcp.types._schemas.core.requirements.asset_requirements.AssetRequirementsJavaScript``
    and a consumer's ``isinstance`` is true against the object the runtime validates into.
    A module that DECLARED its own would satisfy "exactly one import path" and hand back a
    second class with a second ``__adcp_schema__`` to keep in agreement.

    ``X as X`` and not a bare import because that is what makes the name an EXPORT rather
    than an incidental binding -- the re-export convention a type checker reads -- and
    ``__all__`` is written as the literal list beside it, because §1 fixes the set and a
    module that leaves it implicit makes a reader derive it.

    **RELATIVE imports**, for the reason ``relative_module`` already gives: ``_schemas`` is
    private, and an absolute ``adcp.types._schemas...`` here would publish the private path
    once per name.

    **``adcp/types/__init__.py`` is NOT among these and cannot be**, which is a fact about
    Python and not a decision: ``tests/fresh.py`` grades a fresh tree by putting its
    directory in front of ``adcp.types.__path__``, and ``__path__`` decides where a
    package's CHILDREN come from.  A package's own ``__init__`` IS the package, so it is
    already bound before any path entry is consulted and no fresh copy of it could ever be
    the one graded.  It stays hand-written, it names no type, and §1's reason is that a
    flat ``from adcp.types import PaginationRequest`` would be the second spelling §1
    forbids -- the import is meant to tell a reader which document a class came from.

    Keyed relative to the package directory, like D5's alias module, so no caller of
    :func:`write` can be handed a path that escapes the directory it passed -- and written
    only on a run that passes ``package``, which is the scope both artifacts need.
    """
    held: dict[str, dict[str, str]] = {}
    for module, exported in surface.items():
        if not exported:
            # **A module that exports NOTHING contributes no domain**, which is the one
            # thing keying the record on the module adds here: §3a's catalogue module is
            # on the record because the run wrote it, and it declares no type a consumer
            # writes -- "Nothing here is a type" -- so a ``<namespace>.py`` re-exporting
            # it would be a public module with an empty ``__all__``.  §1's surface is
            # stated over what is exported, and this is that sentence read in the one
            # case where the two readings differ.
            continue
        into = held.setdefault(module_domain(module), {})
        for symbol in exported:
            into[symbol] = module.replace("/", ".")
    out: dict[str, str] = {}
    for known in sorted(held):
        by_module: dict[str, list[str]] = {}
        for symbol, module in sorted(held[known].items()):
            by_module.setdefault(module, []).append(symbol)
        out[f"{known}.py"] = render.domain_module(known, by_module)
    return out


def _envelope_bases(bundle_dir: Path, shape: Sequence[bundle.Agreed]) -> str:
    """The text of ``adcp/types/envelopes.py``: one base per family the bundle states.

    The run's half of ``codegen/lower/envelope.py`` is the BINDING -- which module each
    document the family reaches is written to, and which symbol it declares there -- and
    this is the one place that knows both, because :func:`module_path` is this module's
    and the symbol is §4's ``pascal_case(title)``.  The family is ``bundle.envelopes``',
    the declaration is the lowering's, the path and the name are the run's, and none of
    the three is derived twice.

    **The symbol is read off the target document's own ``title``** and not off the run's
    lowered modules, which is what keeps this artifact a function of the bundle: a run
    over one document that happens not to reference ``core/error.json`` still writes the
    same base.  It is the same expression :func:`lower_document` applies at every root, so
    the two cannot name one document's class differently; a title that derives no
    identifier is a ``BuildFailure``, because the run refuses that document and the base
    would then name a symbol no module declares.

    **An empty shape writes a module with no base**, because a bundle stating no member
    of the family earns none (``bundle.envelope_shape``).  The file is still written, for
    the reason the alias module beside it always is: ``write`` compares the set of files
    a run intends, and an artifact that appears and disappears with the bundle's content
    is one more thing for a reader to account for.
    """
    binding: dict[str, tuple[str, str]] = {}
    for one in shape:
        title = bundle.read(bundle_dir, one.target).get("title")
        symbol = class_name(title) if isinstance(title, str) else ""
        if not symbol.isidentifier():
            raise BuildFailure(
                f"the envelope family reaches {one.target} at {one.key!r} and its title "
                f"{title!r} derives {symbol!r}, not an identifier, so no module declares "
                "a symbol the base could name"
            )
        binding[one.target] = (module_name(one.target), symbol)
    if not shape:
        return render.envelopes_module((), frozenset())
    declaration, imports = lower_envelope.base(shape, binding, render.RESERVED)
    return render.envelopes_module([declaration], imports)


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
