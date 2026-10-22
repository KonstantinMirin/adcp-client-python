"""Emit Python types for bundle documents named on the command line.

    python -m codegen.emit --bundle schemas/cache/3.2 core/pagination-request.json

The committed tree is the same command over this step's whole population, which
is derived from the bundle and never listed by hand (``tests/test_emit.py``
grades the tree against exactly this):

    python -m codegen.emit --bundle schemas/cache/3.2 $(python -c 'from pathlib \
      import Path; from codegen import bundle; b = Path("schemas/cache/3.2"); \
      print(*[d for d in bundle.portable(b) if bundle.is_leaf_object(bundle.read(b, d)) \
      or bundle.references_a_property(bundle.read(b, d)) \
      or bundle.composes_at_the_root(bundle.read(b, d))])')

A document this command does not name is still emitted when a named one
REFERENCES it: a module cannot import a symbol from a module no run wrote, so
``emit`` walks ``$ref`` transitively and the run emits the closure.

**This module is the walk, and it decides; it writes no annotation text.**
``docs/plan/rebuild-plan.md`` §1 puts the seam at the decision: the walk reads the
schema and decides what a node IS -- a class, a type, a field, a constraint, a
default, a name, what ``extra`` is -- and ``codegen.compiler`` hands that decision
to ``datamodel-code-generator``'s pydantic-v2 model layer, which writes the
Python.  dmcg's parser never runs.

**D13 divides the walk between this module and ``codegen.compiler``**, and the cut
is the import rule rather than a taxonomy.  What is HERE is the CLI, the module
writer (the header, the import block, the ``__all__``), the refusal report,
:func:`decide_type` -- the per-node dispatch, because the answer for an array, a
mapping or a multi-type node lives in a lowering -- and :data:`ROWS`, the dispatch
table.  What is in ``compiler`` is everything a lowering is handed: the field
builder, the class declarer, the alias declarer, the keyword screen, D3's name
rules and the carriers.  A lowering under ``codegen/lower/`` therefore imports
``codegen.compiler`` and ``codegen.refusal`` and never this module, which is what
keeps ``python -m codegen.emit`` from binding this module twice under ``runpy``;
``tests/test_import_rule.py`` asserts it by AST.

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

import argparse
import functools
import json
import sys
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from codegen import bundle, compiler, harness
from codegen.compiler import (
    BASE_MODULE,
    CONSTRAINTS,
    SCALAR,
    Decided,
    Module,
    Target,
    _no_binder,
    check_keywords,
    class_name,
    declare_alias,
    lower_object,
)
from codegen.lower import enum as lower_enum
from codegen.lower import product as lower_product
from codegen.lower import containers as lower_containers
from codegen.lower import rules as lower_rules
from codegen.lower import union as lower_union
from codegen.refusal import Refusal

#: Where a document's module lands, relative to the repository root.
TREE = Path("src") / "adcp" / "types" / "_schemas"
#: The import path of that tree, and of the hand-written base beside it.
PACKAGE = "adcp.types._schemas"

#: **``format`` SELECTS A TYPE, and the schema half asserts it** (D5).
#:
#: ``format: date-time`` references RFC 3339, where the time offset is MANDATORY,
#: so the document itself requires a timezone and ``AwareDatetime`` states the
#: document's own rule rather than a stricter one.  That reading only holds
#: because the schema half now PASSES A FORMAT CHECKER (``_base._refuse``,
#: ``harness._validating``): a draft-07 ``format`` that nothing checks asserts
#: nothing, and a type derived from one would be narrower than its document as
#: graded -- which is the state a previous lane correctly backed these types out
#: of, and the apparent disagreement was the grader rather than the types.
#: Measured both ways on the same checker: of six RFC 3339 edge values --
#: offsetless, lowercase ``t``/``z``, a leap second, a ``+05:30`` offset,
#: nanosecond precision -- ``AwareDatetime`` and ``rfc3339-validator`` agree on
#: all six, including refusing the leap second.
#:
#: A row exists only where the draft's own checker can DECIDE the format, which
#: :func:`asserted_formats` reads off the document's declared draft.  So removing
#: ``rfc3339-validator`` from the dependencies does not leave an unasserted
#: narrowing behind: the row stops selecting and the node falls back to its own
#: scalar type with the format as an annotation.
#:
#: **``uri`` is not here on purpose, and the omission is a decision.**  D5 admits
#: a standard type only when it states the document's own facts AND accepts the
#: document's own set, and ``AnyUrl`` fails both halves.  It renders
#: ``minLength: 1``, which no ``format: uri`` document states, so the SYMMETRIC
#: schema comparison reports it as a fact the model adds -- a narrowing.  It also
#: NORMALIZES (``HTTP://A.example/X`` comes back ``http://a.example/X``), so the
#: SDK would hand a consumer a value the sender did not send.  And ``uri`` is the
#: one format in this bundle that co-occurs with a string constraint -- at 1 of
#: this population's 5 ``uri`` sites and 73 of the bundle's 300 -- where a
#: ``pattern`` has no rendering against a URL type at all.  So ``uri`` keeps the
#: node's own ``str`` with the format as an annotation, which states exactly the
#: document's two facts and accepts exactly the set ``rfc3987`` decides.
#: Silencing the comparison instead -- a ``WithJsonSchema`` hiding the
#: ``minLength`` -- would make the model's rendered schema a claim nobody graded.
FORMAT_TYPES = {
    "date-time": "pydantic.AwareDatetime",
    "date": "datetime.date",
}


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
def decide_type(node: dict, pointer: str, name_hint: str, mod: Module) -> Decided:
    """What one schema node IS, plus a SYMBOL where another document names the node.

    The decision is :func:`_decide`'s, unchanged.  What is here is the one thing a
    node reached by a fragment reference needs and a node reached only by its parent
    does not: a name in this module, so the referring module imports a symbol rather
    than copying a schema (section 2's rule).

    It wraps rather than living inside ``_decide`` because it applies to every arm
    equally -- an array, a scalar, a mapping and a multi-type node are all annotations
    with no name -- and ``_decide`` returns from ten places, so putting the test in
    there would be ten tests or one more wrapper.  A class or an enumeration comes
    back ``local`` already, having declared itself under this very ``name_hint``, so
    nothing is named twice and no second symbol appears for one node.

    ``mod.named`` is a function of the BUNDLE (``bundle.named_nodes``), not of the
    run's document set, so whether a node gets a name does not depend on who else was
    emitted.
    """
    decided = _decide(node, pointer, name_hint, mod)
    if pointer in mod.named and not decided.type.local:
        return compiler.name_the_node(mod, name_hint, pointer, node, decided)
    return decided


def _decide(node: dict, pointer: str, name_hint: str, mod: Module) -> Decided:
    """What one schema node IS: a Python type, and what constrains it.

    Nullability is NOT a question here (D4).  This returns the node's own type,
    and the compiler adds the ``| None`` branch an OPTIONAL property needs for the
    value an omitted key leaves on the attribute -- which is a fact about
    presence, not a claim that the document admits an explicit null.
    ``AdCPBaseModel.strict_validate`` asks the document about that.

    The constraints come back in the DOCUMENT'S spelling and are passed through
    unchanged: ``compiler.CONSTRAINTS`` gate 1 is that the compiler's
    ``Constraints`` reads JSON Schema names and silently ignores pydantic ones.
    """
    if "$ref" in node:
        # P2: a reference is a REFERENCE.  The target's own module declares its
        # type once and this one names it; nothing of the target's own schema is read
        # here, so nothing of it can be copied.
        #
        # A sibling beyond an annotation refuses, and the keyword it refuses on is
        # the sibling.  draft-07 says a `$ref` IGNORES its siblings, so a sibling
        # constraint would be a constraint the document does not apply -- and
        # `resolve_all_refs`, which the harness resolves with, MERGES it instead.
        # Emitting the import alone is the draft-07 reading and would then be
        # graded against the stricter merged one, so the document is refused by
        # name rather than graded against a schema it does not mean.
        check_keywords(node, pointer, {"$ref"}, "a sibling of $ref, which draft-07 ignores")
        target = mod.bind(node["$ref"], pointer)
        mod.imports.add((target.module, target.symbol))
        return Decided(compiler.Type(target.symbol, local=True))

    if "enum" in node:
        # D2's enumeration row, reached before ``type`` is read at all: the base
        # comes from the members (``lower.enum.BASES``), which is what admits the
        # bundle's 164 typeless enum nodes.  A root enum reaches the same row
        # through the dispatch table below.
        check_keywords(node, pointer, lower_enum.HANDLED)
        decided = lower_enum.decide(node, name_hint, pointer)
        mod.add(name_hint, pointer, compiler.render_enum(decided))
        return Decided(compiler.Type(name_hint, local=True))

    kind = node.get("type")

    if kind is None:
        check_keywords(node, pointer, set())
        if set(node) & set(CONSTRAINTS):
            raise Refusal(
                "type", pointer, "a typeless node carrying a constraint has nothing to apply it to"
            )
        return Decided(compiler.Type("typing.Any"))  # D2's typeless row

    if isinstance(kind, list):
        return lower_containers.multi_type(node, pointer, name_hint, mod)

    if kind == "null":
        check_keywords(node, pointer, {"type"})
        return Decided(compiler.Type("None"))

    if kind == "object":
        if "properties" not in node:
            return lower_containers.mapping(node, pointer, name_hint, mod)
        return Decided(compiler.Type(lower_object(node, name_hint, pointer, mod), local=True))

    if kind == "array":
        return lower_containers.array(node, pointer, name_hint, mod)

    if kind not in SCALAR:
        raise Refusal("type", pointer, f"unknown type {kind!r}")

    # ``rules.ON_A_VALUE`` is the step-7 keyword that can land on a node with no
    # object to carry a rule tuple: a ``not`` over a ``const`` or an ``enum`` is an
    # excluded VALUE, which D4 leaves to the schema half exactly as it leaves a
    # conditional that narrows one.  Carrying it is not refusing it.
    check_keywords(node, pointer, {"type", "format", *CONSTRAINTS, *lower_rules.ON_A_VALUE})
    constraints = {k: node[k] for k in CONSTRAINTS if k in node}
    fmt = node.get("format") if isinstance(node.get("format"), str) else None
    # A format SELECTS a type where one is named for it and the document's own
    # draft can decide it (D5, and the comment above FORMAT_TYPES).  The type
    # then states the format in its own rendered schema, so ``format`` is left
    # unset here and the compiler adds no annotation -- which is what keeps the
    # fact in exactly one place.  Where no type is selected the format rides as
    # an annotation on the node's own scalar type, and the schema comparison
    # grades it there.
    if fmt is not None and fmt in mod.asserted and fmt in FORMAT_TYPES:
        return Decided(compiler.Type(FORMAT_TYPES[fmt]), constraints)
    return Decided(compiler.Type(SCALAR[kind]), constraints, format=fmt)


# --------------------------------------------------------------------------- #
# the module text (D8: the emitter owns its layout)
# --------------------------------------------------------------------------- #
def _import_rank(module: str) -> int:
    """stdlib, the third-party library, this package's own hand-written modules,
    then a sibling module of this tree (always relative, so always
    ``.``-prefixed)."""
    if module.startswith("."):
        return 3
    if module in (BASE_MODULE, lower_rules.RUNTIME_MODULE):
        return 2
    return 1 if module == "pydantic" else 0


def render(mod: Module, symbol: str) -> str:
    groups: list[list[str]] = [[], [], [], []]
    by_module: dict[str, set[str]] = {}
    for module, name in mod.imports:
        by_module.setdefault(module, set()).add(name)
    for module in sorted(by_module):
        names = ", ".join(sorted(by_module[module]))
        groups[_import_rank(module)].append(f"from {module} import {names}")
    out = [
        f"# Generated by codegen.emit from {mod.document}. Do not edit.",
        "from __future__ import annotations",
        "",
    ]
    for g in groups:
        if g:
            out += [*g, ""]
    classes = "\n\n\n".join(mod.blocks)
    return "\n".join([*out, "", classes, "", "", f'__all__ = ["{symbol}"]', ""])


# --------------------------------------------------------------------------- #
# the dispatch table (D13, and §5 Layout)
# --------------------------------------------------------------------------- #
def _object_root(doc: dict, name: str, pointer: str, mod: Module) -> str:
    """D2's object row: a root declaring ``properties`` is a model named by its
    title.  ``lower_object`` is the whole of it, and it is the compiler's because a
    nested object is the same job at a different pointer."""
    return lower_object(doc, name, pointer, mod)


def _scalar_root(doc: dict, name: str, pointer: str, mod: Module) -> str:
    """D2's root-scalar row, which steps 1 and 2 need because a reference TARGET is
    one 100 times over: ``core/creative-revision-id.json`` is a string with
    ``minLength``/``maxLength`` and has no field to hang itself on.  An alias, not a
    class -- a wrapper class would be a second name for the same node (P2) and would
    make every referencing model carry an object where the document carries a
    string.  ``compiler.declare_alias`` holds the rest, including its known
    ceiling."""
    return declare_alias(mod, name, doc, decide_type(doc, pointer, name, mod))


def _enum_root(doc: dict, name: str, pointer: str, mod: Module) -> str:
    """D2's enumeration row at a document root (step 3).

    The same decision an inline enum gets -- :func:`decide_type` reaches
    ``lower.enum`` too -- with the module-level binding a root needs around it,
    because ``Enum.jinja2`` has no ``class_body_lines`` slot for the
    ``__adcp_schema__`` line and D9 forbids writing one in afterwards.
    """
    check_keywords(doc, pointer, lower_enum.HANDLED)
    return compiler.bind_without_a_model(
        mod, name, compiler.render_enum(lower_enum.decide(doc, name, pointer))
    )


def _union_root(doc: dict, name: str, pointer: str, mod: Module) -> str:
    """D2's union row (step 5): the base carrying ``BranchDispatchMixin``, one
    subclass per branch, and the module trailer that installs the union."""
    return lower_union.lower_union(doc, name, pointer, mod)


#: **D2's rows, as the ``(selector, lowering)`` pairs D13 states, and the table is
#: UNORDERED.**
#:
#: A selector reads a DOCUMENT and says whether this row lowers its root; the
#: lowering declares the module and returns the symbol it exports.  A selector IS
#: its step's population test in ``codegen.bundle``, so a row cannot come to claim
#: a document its step does not count, and there is no second definition of a
#: population to drift from.
#:
#: Unordered is the decision, not an omission.  :func:`lower_document` FAILS on a
#: document two rows select rather than letting the table's order decide, because
#: an ordered chain makes precedence a property of where a lane happened to insert
#: its row -- invisible in review, and the same "last wins" this project refuses of
#: an ``allOf`` member list.  Disjointness is a fact about the SELECTORS and belongs
#: there: a collision is a selector defect and gets fixed in ``codegen.bundle``.
#:
#: Dispatch is on the ROOT KIND and not on the document's whole content, which is
#: what makes the table a partition rather than a precedence puzzle: a root is
#: exactly one kind.  The per-NODE walk is :func:`decide_type`, which every row
#: shares and which reaches the nested rows; those arms are not rows here for the
#: same reason ``decide_type`` is not one -- they are the walk, not a root's owner.
#:
#: ``emit`` imports each lowering, and no lowering imports ``emit`` (D13).
ROWS: tuple[tuple[Callable[[dict], bool], Callable[[dict, str, str, Module], str]], ...] = (
    (bundle.is_object_root, _object_root),
    (bundle.is_scalar_root, _scalar_root),
    (bundle.is_enum_root, _enum_root),
    (bundle.composes_at_the_root, lower_product.lower_root),
    (bundle.union_root, _union_root),
    (bundle.is_container_root, lower_containers.root),
)


class AmbiguousRoot(Exception):
    """Two D2 rows select one document.

    A BUILD FAILURE and not a ``Refusal``: a refusal is the designed outcome of a
    keyword this emitter does not lower, and this is the emitter disagreeing with
    itself about which row owns a root kind.  Recording it as a refusal would file
    it against the document, where it would read as the bundle's fault, and the
    build would pass.
    """


def lower_document(
    document: str,
    doc: dict,
    bind: Callable[[str, str], Target] = _no_binder,
    named: frozenset[str] = frozenset(),
) -> tuple[Module, str]:
    # D2's shape rows dispatch through ``codegen.lower.ROWS``, one module per row.
    # Imported inside the function because a row's module imports this module's
    # ``fields``/``declare_object`` by name: one direction is lazy, so the two
    # never form an import cycle whichever is loaded first.
    from codegen import lower

    title = doc.get("title")
    if not isinstance(title, str) or not title:
        raise Refusal("title", "", "the document declares no title to derive a name from")
    symbol = class_name(title)
    if not symbol.isidentifier():
        raise Refusal("title", "", f"the title {title!r} derives {symbol!r}, not an identifier")
    mod = Module(
        document=document,
        bind=bind,
        decide=decide_type,
        asserted=asserted_formats(doc),
        named=named,
    )
    claimed = [(selects, lower) for selects, lower in ROWS if selects(doc)]
    if len(claimed) > 1:
        raise AmbiguousRoot(
            f"{document}: {', '.join(s.__name__ for s, _ in claimed)} all select this root; "
            "the table is unordered, so two selectors claiming one document is a defect in "
            "the selectors and the metric would count it twice"
        )
    if not claimed:
        raise Refusal("type", "", "no D2 row selects this root (a later step's row does)")
    claimed[0][1](doc, symbol, "", mod)
    return mod, symbol


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
@dataclass
class Emitted:
    files: dict[str, str] = field(default_factory=dict)  # path -> text
    #: document -> the module it was written to.  The run's own record of what it
    #: emitted, for the refusal arithmetic and the CLI report.  It is NOT a
    #: binding table and nothing reads it at runtime: a class finds its schema
    #: through its own ``__adcp_schema__``.
    emitted: dict[str, str] = field(default_factory=dict)
    refusals: dict[str, dict[str, str]] = field(default_factory=dict)


def emit(bundle_dir: Path, documents: list[str]) -> Emitted:
    """Lower every named document, and every document one of them references.

    Sorted, so the run is order-independent (P7).  Transitive emission is the walk
    a reference forces: a module cannot import a symbol from a module no run wrote,
    so a named document's targets are emitted whether or not they were named.  The
    walk is over ``$ref`` strings and nothing else -- an import edge is
    ``(referencing path, target path)``, which is what D1 already derives a module
    path from, so there is no resolution here and no node graph.  Resolution does
    the OPPOSITE of what an import needs: it substitutes the target's contents for
    the reference, leaving nothing to emit an import from.

    It terminates on a memo, and a document reached while its own lowering is in
    flight is a reference CYCLE, which refuses by name: two modules importing each
    other's symbol at module scope is an ImportError, not a type.
    """
    out = Emitted()
    packages: set[str] = set()
    known = set(bundle.portable(bundle_dir))
    # Read once per run, from the BUNDLE rather than from ``documents``: a module's
    # content must not depend on who else was named (see ``bundle.named_nodes``).
    named = bundle.named_nodes(bundle_dir)
    lowered: dict[str, tuple[Module, str, dict]] = {}
    refused: dict[str, Refusal] = {}
    inflight: list[str] = []

    def bind(referencing: str) -> Callable[[str, str], Target]:
        def do(uri: str, pointer: str) -> Target:
            # A reference is a (document, node) pair, and the node half is what a
            # FRAGMENT carries.  Both halves come from one reading of the ``#``
            # (``bundle.split_ref``), the same one ``bundle.resolved`` keys its store
            # on, so the binder and the resolver cannot disagree about which document
            # a reference names.
            head, into = bundle.split_ref(uri)
            if not head:
                # A LOCAL reference: it names a node of THIS document, so there is no
                # module to import from and the symbol would have to be one this
                # module is in the middle of writing.  Refused by name, pointer and
                # the pointer it carries.  0 of the documents that lower reach this:
                # all 45 carrying one refuse on ``definitions``/``$defs``, which is
                # the keyword such a reference points through, so the import path for
                # it is built by the step whose population reaches one.
                raise Refusal(
                    "$ref",
                    pointer,
                    f"{uri} is a pointer into this document, and a node of the module "
                    "being written has no symbol to import yet (a later step's row)",
                )
            target = bundle.document_for(head, known)
            if target is None:
                raise Refusal(
                    "$ref", pointer, f"{uri} names no document of this bundle"
                )
            try:
                mod, symbol = lower(target)  # the target emits first, or this refuses with it
            except Refusal as r:
                raise Refusal("$ref", pointer, f"its target {target} is refused: {r}") from r
            if into:
                # The fragment names a NODE, so the symbol is the one the target
                # module declared AT THAT POINTER rather than its root.  The target
                # declares one because ``bundle.named_nodes`` told it to.
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
                if into not in mod.declared:
                    raise Refusal(
                        "$ref",
                        pointer,
                        f"{uri}: its target {target} declares no symbol at {into} "
                        "(the walk either does not reach that node, or the node is "
                        "itself a $ref whose symbol that module imports rather than "
                        "declares)",
                    )
                symbol = mod.declared[into]
            # ``shape`` is ``None`` for a target that is not a class -- D2's
            # root-scalar alias, and a named node that is not one either -- which is
            # what lets a composing row refuse it as a base rather than writing a
            # module that cannot be imported.
            return Target(relative_module(referencing, target), symbol, mod.shapes.get(symbol))

        return do

    def lower(document: str) -> tuple[Module, str]:
        if document in lowered:
            mod, symbol, _ = lowered[document]
            return mod, symbol
        if document in refused:
            raise refused[document]
        if document in inflight:
            raise Refusal("$ref", "", f"a reference cycle: {' -> '.join([*inflight, document])}")
        inflight.append(document)
        doc = bundle.read(bundle_dir, document)
        try:
            mod, symbol = lower_document(
                document, doc, bind(document), named.get(document, frozenset())
            )
        except Refusal as r:
            refused[document] = r
            raise
        finally:
            inflight.pop()
        lowered[document] = (mod, symbol, doc)
        return mod, symbol

    for document in sorted(set(documents)):
        try:
            lower(document)
        except Refusal:
            continue  # recorded in `refused`, reported below by name and keyword

    for document in sorted(lowered):
        mod, symbol, doc = lowered[document]
        rel = module_path(document)
        out.files[f"{rel}.py"] = render(mod, symbol)
        out.emitted[document] = f"{PACKAGE}.{rel.replace('/', '.')}"
        # The document travels WITH the module, at its own bundle-relative path,
        # because ``__adcp_schema__`` names that path and ``strict_validate``
        # reads it to decide acceptance (D4).  The bundle is a build-time input
        # -- 124 MB, with a version in its path -- so it cannot be the runtime
        # source.  Written here, by the run that lowered it, which is what makes
        # P10's compare cover the schemas the runtime asks and not only the
        # modules.
        #
        # RESOLVED: a reference is an import in the MODULE (P2), but a `$ref`
        # left in the DOCUMENT is a schema nothing local can decide, so
        # `jsonschema` fetches the target over the network -- deprecated, 4.4 s
        # per validation measured, and simply unavailable offline.  See
        # ``bundle.resolved``; a document with no reference resolves to itself.
        schema = bundle.resolved(bundle_dir, document) if bundle.references(doc) else doc
        out.files[document] = json.dumps(schema, indent=2, sort_keys=True) + "\n"
        parts = rel.split("/")[:-1]
        packages.update("/".join(parts[: i + 1]) for i in range(len(parts)))

    for document in sorted(refused):
        r = refused[document]
        out.refusals[document] = {"keyword": r.keyword, "pointer": r.pointer, "detail": r.detail}
    for pkg in packages:
        out.files[f"{pkg}/__init__.py"] = ""
    out.files["__init__.py"] = ""
    # The refusal REPORT is not a file in the tree.  It was, and the documented
    # one-document command then rewrote it with that run's refusals -- which are
    # none -- so running the command in the README damaged the committed tree and
    # reddened the gate.  A report about documents this package does NOT contain
    # has no place inside the shipped package anyway: `main` prints it, and the
    # suite reads `Emitted.refusals` from the run it just made.
    return out


def write(out: Emitted, tree: Path) -> None:
    """Write this run's files, and delete nothing.

    A stale module -- one emitted by an earlier run over a different document set
    -- is a real defect: it stays importable while no document produces it any
    more.  Pruning it here was tried and removed, because it makes the
    one-document command above destroy the other modules of the committed tree,
    and a command whose demonstration wipes the tree gets run once.

    The file SET is checked where P10 puts a check, against the inputs rather
    than against a previous output: ``test_emit`` compares the whole committed
    tree with a fresh emission of the derived population, so a file no run
    produces is a failure at the gate and never a silent survivor.  Probed by
    planting one.
    """
    for rel in sorted(out.files):
        path = tree / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(out.files[rel])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="codegen.emit", description=__doc__)
    ap.add_argument("--bundle", type=Path, required=True, help="the schema bundle directory")
    ap.add_argument("--tree", type=Path, default=TREE, help="where the modules are written")
    ap.add_argument("document", nargs="+", help="bundle-relative document paths")
    ns = ap.parse_args(argv)

    out = emit(ns.bundle, ns.document)
    write(out, ns.tree)
    for document in sorted(out.refusals):
        r = out.refusals[document]
        print(f"refused {document} at {r['pointer']} on {r['keyword']}: {r['detail']}")
    print(
        f"emitted {len(out.emitted)} / refused {len(out.refusals)}; "
        f"{len(set(ns.document))} named, the rest reached through a $ref"
    )
    return 1 if out.refusals else 0


if __name__ == "__main__":
    # Through the PACKAGE, not through this copy of it.  ``python -m codegen.emit``
    # executes this file as ``__main__`` under ``runpy``, so anything that reached
    # ``codegen.emit`` by name would hold a SECOND module object.  D13 removed the
    # one importer that did -- a lowering now imports ``codegen.compiler``, where
    # ``Module``, ``Shape``, ``Target`` and ``Decided`` live, and ``Refusal``
    # already lives in a module no ``-m`` can name (D12).  This re-entry is what
    # keeps that true for ``ROWS`` and :func:`decide_type` as well: one entry
    # point, so there is one of every row and one decider.
    from codegen.emit import main as _main

    sys.exit(_main())
