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

import collections
import argparse
import functools
import json
import sys
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from codegen import bundle, compiler, harness
from codegen import constraints as constraints_module
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
    lower_composition,
    lower_object,
)
from codegen.lower import const as lower_const
from codegen.lower import enum as lower_enum
from codegen.lower import containers as lower_containers
from codegen.lower import rules as lower_rules
from codegen.lower import union as lower_union
from codegen import refusal
from codegen.refusal import Kind, Refusal

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
#: **``uri`` SELECTS ITS TYPE FROM THE NODE, which is why this table holds
#: choosers rather than paths.**  D5 makes a ``format: uri`` field's type follow the
#: DOCUMENT'S OWN PATTERN -- ``AdCPUrl`` where the document restricts the scheme to
#: https, ``HttpUrl`` everywhere else -- so the answer is a function of the node and
#: not of the format alone.  ``date-time`` and ``date`` ignore their node, and they
#: are expressed as choosers too rather than as a second shape beside one: a table
#: with two kinds of value is a table every reader has to case-split.
#:
#: The former entry read ``uri`` -> ``AdCPUrl`` and it was WRONG, measured. D5 now
#: records the whole of it; the short form is below.
#:
#: **``AdCPUrl`` everywhere narrowed the SDK below the pinned spec.**  ``format: uri``
#: references RFC 3986, which admits every scheme, so a bare
#: ``{"type": "string", "format": "uri"}`` admits ``https://``, ``http://``, ``urn:``
#: and ``file:///`` alike -- and ``AdCPUrl`` refuses three of the four. Measured at
#: **228 of the bundle's 300 ``uri`` positions, in 128 of 160 documents**, and at
#: **26 of 27** positions in documents the emitter emits. End to end on a shipped
#: class: ``core/placement-evidence.json#/properties/url`` states only the bare pair,
#: the document admits ``{"url": "http://x.example/p"}``, and
#: ``PlacementEvidence.strict_validate`` raised ``URL scheme should be 'https'``.
#:
#: **No check saw it**, which is why it stood: ``allowed_schemes`` has no rendering in
#: pydantic's schema output, so the comparison has no keyword to compare; ``format``
#: is not a step keyword, so ``steps()`` returns ``[]``; and
#: ``hypothesis_jsonschema``'s ``uri`` strategy drew ``https`` in 200 of 200
#: derandomized examples. That instrument gap is ``salesagent-j3k2l.10``'s, not this
#: module's.
#:
#: **``HttpUrl``'s two ceilings are accepted deliberately and named at D5**: it still
#: refuses ``urn:`` and ``file:``, so 227 of 300 positions stay narrower than their
#: document, and it renders ``maxLength: 2083`` and ``minLength: 1`` that no document
#: states -- which ``harness.compare_schema`` admits with one hand-written row per
#: fact, each naming itself.
#:
#: What follows is the reasoning for the type being ours rather than pydantic's at
#: the https branch, which the amendment did not change.  D5 admits
#: a STANDARD type only when it states the document's own facts AND accepts the
#: document's own set, and no pydantic URL type passes: ``AnyUrl`` and
#: ``AnyHttpUrl`` both render a ``minLength: 1`` no ``format: uri`` document
#: states, ``HttpUrl`` adds a ``maxLength: 2083`` as well, and all three admit
#: ``http://``.  So the type is one we emit --
#: ``Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]``, declared once
#: in ``codegen.constraints`` -- and the ``minLength: 1`` it renders is admitted
#: by a comparison row of its own kind (``harness.compare_schema``) rather than
#: hidden with a ``WithJsonSchema``, which would make the model's rendered schema
#: a claim nobody graded.
#:
#: The document's own ``pattern`` stays with the SCHEMA half: the bundle states
#: eight distinct patterns across 73 of its 300 ``uri`` uses and
#: ``UrlConstraints`` expresses only the first (``^https://``, at 47 sites), so
#: letting the field type vary by how strict a schema author happened to be is
#: what this avoids.  ``strict_validate`` applies the document before the
#: constructor runs, so nothing widens.
#:
#: Each value is ``(node) -> dotted path``.  ``date-time`` and ``date`` ignore the
#: node; ``uri`` is ``constraints.url_type``, which reads the document's own
#: ``pattern``.
FORMAT_TYPES: dict[str, Callable[[Mapping[str, Any]], str]] = {
    "date-time": lambda node: "pydantic.AwareDatetime",
    "date": lambda node: "datetime.date",
    "uri": constraints_module.url_type,
}

#: The formats whose selected type is a URL type, which is what the one refusal
#: below is gated on.  DERIVED by asking each chooser rather than listed: a format
#: whose chooser answers inside the alias module's namespace is a URL format, and a
#: second list to keep in step would be a second place for this to drift.
URL_FORMATS = frozenset(
    fmt
    for fmt, choose in FORMAT_TYPES.items()
    if choose({}).startswith(f"{constraints_module.MODULE}.")
)


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
def content_key(node: dict, pointer: str, mod: Module) -> str:
    """D3's content equality, AND the statement of where it cuts a reference cycle.

    Two nodes are the same node when this returns the same string for both.  It is
    the node's own JSON with every mapping ordered -- so a key order no instance can
    observe is not a difference -- plus the one fact about the node's POSITION that
    the decision reads.

    **A ``$ref`` is compared as a STRING and is never followed, and that is the cut.**
    §9 records that two instruments once disagreed about whether two nodes were
    identical entirely because each cut a reference cycle somewhere else, and D3 says
    the comparison has to state its rule.  Here there is no recursion to cut: the node
    is read as the document wrote it, so a cycle through a ``$ref`` is cut at the
    reference, at depth 0, on every node and not only on a cyclic one.

    **The cost of that cut is a measured population, not a hypothetical.**  Two nodes
    that name ONE target through two spellings of the same reference are NOT equal
    here, and the bundle has 17 such targets: 968 distinct reference strings over 4,200
    sites, 0 of them relative, and 17 (document, pointer) pairs reached both by a local
    ``#/definitions/x`` and by the document's own absolute URI carrying the same
    fragment.  Those pairs are not collapsed, which is the conservative direction --
    two classes where one would do, never one class where the document means two -- and
    following the reference to compare the targets is the thing §9 says has to state
    its cut before anything does it.

    **The POSITION bit is ``mod.object_constrained``, and the key is wrong without
    it.**  ``bundle.constrained_to_object`` is a set of POINTERS: a node stating no
    ``type`` of its own is lowered as an object where an enclosing node applies
    ``type: "object"`` to the same instance, and is refused where none does.  So two
    nodes of byte-identical JSON at two such positions decide DIFFERENTLY, and a key
    over the JSON alone would hand the refused position the class the admitted one
    declared -- a model stating what that position's document does not.  1,390 of the
    bundle's nodes declare ``properties`` with no ``type``, 556 of them in that set and
    834 outside it, so both sides of the bit are populated.  Nothing else the decision
    reads is per-pointer: ``mod.asserted`` and ``mod.root`` are per document, and
    ``mod.named`` is handled by :func:`decide_type` itself.
    """
    return json.dumps(
        [node, pointer in mod.object_constrained], sort_keys=True, separators=(",", ":")
    )


def decide_type(node: dict, pointer: str, name_hint: str, mod: Module) -> Decided:
    """What one schema node IS, plus a SYMBOL where another document names the node.

    The decision is :func:`_decide`'s, unchanged.  What is here is the two things a
    node reached by a fragment reference or by a second parent needs and a node
    reached once by its own parent does not: a name in this module, so the referring
    module imports a symbol rather than copying a schema (section 2's rule), and D3's
    content dedup.

    It wraps rather than living inside ``_decide`` because both apply to every arm
    equally -- an array, a scalar, a mapping and a multi-type node are all annotations
    with no name -- and ``_decide`` returns from ten places, so putting the tests in
    there would be twenty tests or one more wrapper.  A class or an enumeration comes
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
    * **The surviving symbol is the one D3's nested rule derives at the node's FIRST
      position, in the document's own key order**, and that is the choice this row
      states rather than leaves to be read off whichever key is walked first.  D3
      derives a name PER POSITION, so a node at two positions has two derivations and
      no rule picks between them; the alternative readings are both worse.  Naming it
      from its own content is what D5 bans for an alias ("an alias names a constraint,
      never a concept") and for an enumeration the content is a member list, not a
      name.  Naming it from the bundle is unavailable and measured so: 0 of the 1,271
      identical-content groups have a bundle ROOT carrying that content, so D5's first
      rung reaches none of them.  And refusing the document loses a class the bundle
      can state.  ``tests/test_emit.py`` asserts the survivor against the first
      position, so a flip in walk order reddens instead of renaming a public symbol.
    * **No pointer is registered for the collapsed node**, so a cross-document ``$ref``
      naming the second position refuses DEFERRED by name -- the loud outcome
      ``emit.emit``'s binder already mints for a pointer the walk declares no symbol
      at.  Measured: the walk collapses 8 pointers (7 content groups over 15 positions),
      and 0 of the 8 are among the bundle's 216 named nodes -- so the arm is unreachable
      today and the step whose population reaches one decides whether the reference
      follows the collapse.
    """
    key = content_key(node, pointer, mod)
    collapsed = mod.collapsed.get(key)
    if collapsed is not None:
        mod.adopted[pointer] = collapsed
        return Decided(compiler.Type(collapsed, local=True))
    decided = _decide(node, pointer, name_hint, mod)
    if pointer in mod.named and not decided.type.local:
        decided = compiler.name_the_node(mod, name_hint, pointer, node, decided)
    if mod.declared.get(pointer) == decided.type.path:
        mod.collapsed[key] = decided.type.path
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
        # **The DOCUMENT HALF decides which of the two resolutions this is**, and the
        # reading is ``bundle.split_ref``'s one reading of the ``#``.  An EMPTY half is
        # a pointer into the document being written: there is no module to import from,
        # and the symbol is one THIS module declares -- so it is a lookup in
        # ``mod.declared`` rather than a binding, and ``compiler.local_reference`` declares
        # the node if the walk has not reached it yet.  The branch is here and not
        # inside ``emit.emit``'s binder, where it used to refuse, because a binder
        # resolves a reference to a MODULE and a local reference names none; handing one
        # to the binder was what made "a node of the module being written has no symbol
        # to import yet" the answer for all 45 documents carrying one.
        head, into = bundle.split_ref(node["$ref"])
        if not head:
            return compiler.local_reference(mod, into, pointer)
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

    if "const" in node:
        # D2's ``const`` row, IN FULL, and reached before ``type`` is read for the
        # enum branch's reason: a ``const`` pins the VALUE, and the value's own JSON
        # type is what the node admits whether the document spells a ``type`` word or
        # not -- 832 of the bundle's 1,486 const nodes spell none.  A ``const`` is a
        # single-member enumeration in JSON Schema's vocabulary and nothing in this
        # bundle writes both (0 of the 1,486 carry an ``enum`` beside it), so the two
        # branches do not overlap and their order here is not a precedence.  The same
        # holds against the composition arm below, measured over the portable
        # population: 0 nodes carry both a ``const`` and an ``allOf``, so the order of
        # the two moves no document.  It is written this way round because a ``const``
        # pins the whole value and a conjunct list cannot widen a pinned value.
        check_keywords(node, pointer, lower_const.HANDLED)
        return lower_const.decide(node, pointer)

    if isinstance(node.get("allOf"), list):
        # **D7's composition, at a node that is NOT a root.**  The same lowering the
        # root reaches through :data:`ROWS` -- the conjunct list is the same list and
        # the merge rule is the same rule at every depth -- and it is reached here
        # rather than through a seventh row because ``ROWS`` dispatches on ROOT KIND
        # and is a partition by it: a keyword that does not appear at a root has no
        # row to be and no selector to select it.  Measured on the 3.2 bundle: of the
        # 67 documents whose composition the product row was deferring, 26 carry it
        # at a property or deeper and 0 of those 26 are claimed by
        # ``composes_at_the_root``, so a row would have claimed none of them.
        #
        # Read BEFORE ``type``, for the reason ``bundle.declares_its_own_root_kind``
        # reads a root's ``allOf`` before its ``type``: a draft-07 ``allOf`` applies
        # to the whole instance, so a node that composes is a composition whatever
        # else it declares, and lowering the ``properties`` without the conjuncts
        # would drop the bases.  After ``$ref`` and ``enum``, which both close the
        # node ahead of it: a ``$ref``'s siblings are ignored by draft-07 (the branch
        # above refuses one), and an ``enum`` closes the value set.
        #
        # **Every position this reaches is one whose INSTANCE is its own**, which is
        # what makes reading the node here the node the DOCUMENT applies: a
        # ``properties``, ``items`` or ``definitions`` entry is applied to a value one
        # level down, where an ``allOf`` conjunct, a union branch and an ``if``/``then``
        # position share the enclosing node's instance and so inherit its ``type``.
        # Measured over the whole portable population: 307 compositions are lowered,
        # 287 at a root and 20 below one, and **0 of the 20 sit at a shared-instance
        # position** -- 12 at ``properties/<key>``, 7 at an ``items`` and 1 at a
        # ``definitions`` entry.  The nearest miss is
        # ``core/budget-allocation.json#/oneOf/1/properties/optimization_goals/items``,
        # whose pointer crosses a branch two instances up and whose own node is an
        # array element.
        return Decided(
            compiler.Type(
                lower_composition(node, name_hint, pointer, mod), local=True
            )
        )

    if lower_union.keyword(node) is not None and not lower_rules.presence_only(node):
        # **D2's union keyword at a node that is NOT a root**, reached here rather than
        # through a seventh row for the ``allOf`` arm's reason above: ``ROWS`` dispatches
        # on ROOT KIND and is a partition by it, so a keyword at a position no root
        # selector sees has no row to be.  Measured on the 3.2 bundle, and the
        # measurement is about the NODE'S POSITION rather than about the document:
        # of the 32 deferred nested combinators, **0 sit at a root** -- every one is at a
        # ``properties``, an ``items``, a ``definitions`` entry or inside a branch -- so
        # no root selector sees any of them and a row would have claimed none.
        #
        # **Asked of the DOCUMENT the answer is different, which is why it is asked of
        # the node:** 2 of the 32 documents have a root ``bundle.union_root`` already
        # claims (``core/creative-item.json``, whose combinator is at
        # ``/oneOf/1/properties/content``, and ``core/placement-selection.json`` at
        # ``/oneOf/0/properties/placement_refs/items``) and 14 have one
        # ``composes_at_the_root`` claims.  A row claiming the document says nothing
        # about the position inside it, which is the whole of why ROWS partitions by
        # root kind.
        #
        # It is a TYPE and not the root row's base-plus-subclasses -- see
        # ``lower.union.nested`` -- and ``lower_union.keyword`` is the one reading of
        # which keyword a node carries, shared with ``bundle.union_root``, so this arm
        # and the root selector cannot disagree about what a union is.
        #
        # Read AFTER ``$ref``, ``enum``, ``const`` and ``allOf``, each of which closes
        # the node ahead of it, and BEFORE ``type``: a union keyword beside a ``type``
        # word is a CONJUNCTION with every branch, which ``nested``'s sibling screen
        # refuses by name -- reading ``type`` first would lower the type and drop the
        # branches, which is a model wider than its document.
        #
        # **``presence_only`` is the gate and it is the published step-5/step-7 boundary,
        # not a precedence rule invented here.**  A combinator whose every branch is
        # ``required``-only says which KEYS are present, which is D6's rule on the
        # nearest class (``lower.rules``, reached through ``compiler.rules_at`` by the
        # object row below) -- not a union of shapes.  ``bundle.states_an_object_rule``
        # asks the same predicate of a ROOT, so the two positions read one definition.
        #
        # Measured: without this gate the arm claimed every presence-only node too and
        # **emitted fell 674 -> 620**, because a class-plus-rule became a union whose
        # sibling ``properties`` then refused.  The predicate is read HERE, at the
        # dispatch, because ``lower.union`` imports ``compiler`` and ``refusal`` and
        # nothing else of this package (D13) and so cannot ask step 7's question.
        return lower_union.nested(node, pointer, name_hint, mod)

    kind = node.get("type")

    if kind is None:
        # ``rules.ON_A_VALUE`` for the SCALAR arm's reason, which does not depend on the
        # type word being present: a ``not`` is a statement about which VALUES the node
        # admits, so D4 leaves it to the schema half, and a node with no ``type`` has no
        # less of a value than a node with one.  The set was admitted on the scalar arm
        # alone because every site measured for it spelled a type; this bundle has one
        # that does not (``core/account.json#/properties/destination_billing_entity``,
        # whose whole schema is ``{"not": {}}``), and refusing it there while carrying
        # ``not: {"const": ...}`` here would be the same keyword read two ways by the
        # presence of a word that changes nothing about it.
        check_keywords(node, pointer, {*lower_rules.ON_A_VALUE})
        if set(node) & set(CONSTRAINTS):
            raise Refusal(
                "type", pointer, "a typeless node carrying a constraint has nothing to apply it to"
            , kind=Kind.VERDICT)
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
        raise Refusal("type", pointer, f"unknown type {kind!r}", kind=Kind.VERDICT)

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
        selected = FORMAT_TYPES[fmt](node)
        if fmt in URL_FORMATS and constraints:
            # **A URL type carries NO string constraint, and that is a measurement
            # rather than a choice.**  ``Annotated[AnyUrl, Field(pattern=...)]``
            # raises at validation -- "Unable to apply constraint 'pattern' ... for
            # schema of type 'function-wrap'" -- so the class does not even build,
            # which is how this was found: the module failed to import.  It is a
            # loud failure and not a silent drop, so type-plus-pattern is genuinely
            # unavailable.
            #
            # D5 decides the either/or: the ``pattern`` SELECTS the type (see
            # ``constraints.url_type``) and then stays with the SCHEMA half, which
            # ``strict_validate`` applies before the constructor runs.
            # ``harness.compare_schema``'s URL-type rows grade the omission, and the
            # one that admits a dropped keyword is gated on ``pattern`` ALONE -- so
            # any OTHER string constraint has no decision covering it and refuses by
            # name rather than going missing.
            #
            # Measured over the bundle's 300 ``uri`` positions: 227 state no string
            # constraint, 69 state a ``pattern``, and **4 state a ``maxLength``
            # beside the pattern** -- all four ``maxLength: 2048``, none of them in a
            # document the emitter reaches today. Those four are what this refuses,
            # and a ``maxLength: 2048`` document against ``HttpUrl``'s rendered
            # ``maxLength: 2083`` would be a ``differs`` rather than a silent drop,
            # so refusing is the only answer that is neither wrong nor invisible.
            unowned = sorted(set(constraints) - {"pattern"})
            if unowned:
                raise Refusal(
                    unowned[0],
                    pointer,
                    f"a format: uri node states {unowned}, and a URL type carries no "
                    "string constraint at all -- pydantic refuses to apply one -- while "
                    "the comparison's URL-type rows admit only a dropped pattern and "
                    "the two bounds a URL type renders of its own, so this keyword "
                    "would go missing or differ ungraded",
                    kind=Kind.VERDICT,
                )
            return Decided(compiler.Type(selected))
        return Decided(compiler.Type(selected), constraints)
    # D5: **a constrained type is NAMED once and referenced.**  The name is a pure
    # function of (the document's type word, its constraints) -- rung 2 where a
    # pydantic type qualifies on both halves, rung 3 otherwise -- so the same shape
    # in two documents is the same symbol without any census over the run, and the
    # constraints then ride on the TYPE rather than on the field.  Two things follow
    # from the constraints coming back empty, and both are D5's own point rather
    # than a side effect: a bound inside ``list[...]`` or ``dict[str, ...]`` now has
    # somewhere to go (``lower.containers._inner`` refused exactly this), and so
    # does a bound on one arm of a multi-type node.
    #
    # ``resolve`` returns ``None`` for a shape it has no spelling for, and the site
    # then stays inline, which is what every site did before this row existed.
    path = constraints_module.resolve(kind, constraints)
    if path is not None:
        if path.startswith(f"{constraints_module.MODULE}."):
            constraints_module.record(mod.aliases, path.rsplit(".", 1)[1], kind, constraints)
        return Decided(compiler.Type(path), format=fmt)
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
    if module in (BASE_MODULE, lower_rules.RUNTIME_MODULE, constraints_module.MODULE):
        return 2
    return 1 if module == "pydantic" else 0


def _local_symbols(t: compiler.Type) -> set[str]:
    """Every symbol of the DECLARING module that one decided type names.

    A local bare symbol is this pipeline's own class or alias (``compiler.Type``), and
    a container carries its members in ``of`` with a mapping's key beside them -- so
    ``list[CanonicalFormatBaseSlotsItem] | None`` reaches the item through two levels
    and neither can be read off ``path``.
    """
    out = {t.path} if t.local and t.path.isidentifier() else set()
    for inner in (*t.of, *( (t.key,) if t.key is not None else () )):
        out |= _local_symbols(inner)
    return out


def exported(mod: Module, symbol: str, composed: frozenset[str] = frozenset()) -> list[str]:
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
    rest = {mod.declared[p] for p in mod.named if p in mod.declared}
    for pointer in composed:
        base = mod.declared.get(pointer)
        shape = mod.shapes.get(base or "")
        if shape is None:
            continue
        rest |= {
            name
            for prop in shape.decided.values()
            for name in _local_symbols(prop.type)
            if name in mod.names
        }
    return [symbol, *sorted(rest - {symbol})]


def render(mod: Module, symbol: str, composed: frozenset[str] = frozenset()) -> str:
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
    names = ", ".join(f'"{n}"' for n in exported(mod, symbol, composed))
    return "\n".join([*out, "", classes, "", "", f"__all__ = [{names}]", ""])


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
    (bundle.composes_at_the_root, lower_composition),
    (bundle.union_root, _union_root),
    (bundle.is_container_root, lower_containers.root),
)


#: The keywords a root's KIND is read from, and the order an UNCLAIMED root is
#: reported by.  **Not a dispatch table and not a precedence list**: ``ROWS`` is the
#: dispatch and a root any row claims never reaches this.  It exists so that a root
#: no row claims is refused on the keyword that would have decided it, rather than
#: on the emitter's failure to find a row -- which is a fact about the emitter and
#: tells a reader nothing about the document in front of them.
ROOT_KIND = ("$ref", "if", "oneOf", "anyOf", "allOf", "enum", "properties", "type")

#: Root keys that state no kind, so a refusal reporting what the root declares
#: leaves them out: they are the same on every document and carry no signal.
_ANNOTATIONS = frozenset({"$schema", "$id", "$comment", "title", "description"})


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
        raise Refusal(
            "title",
            "",
            "the document declares no title to derive a name from",
            kind=Kind.VERDICT,
        )
    symbol = class_name(title)
    if not symbol.isidentifier():
        raise Refusal(
            "title",
            "",
            f"the title {title!r} derives {symbol!r}, not an identifier",
            kind=Kind.VERDICT,
        )
    mod = Module(
        document=document,
        root=symbol,
        bind=bind,
        decide=decide_type,
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
    claimed = [(selects, lower) for selects, lower in ROWS if selects(doc)]
    if len(claimed) > 1:
        raise AmbiguousRoot(
            f"{document}: {', '.join(s.__name__ for s, _ in claimed)} all select this root; "
            "the table is unordered, so two selectors claiming one document is a defect in "
            "the selectors and the metric would count it twice"
        )
    if not claimed:
        # **Refused on the keyword the root's KIND is read from, and with no promise
        # of a row.**  This said "no D2 row selects this root (a later step's row
        # does)", which names no keyword and asserts a schedule -- and for the seven
        # documents it is now down to, the promise is simply false: four of them are
        # DATA documents carrying no schema keyword at all, so no row will ever read
        # them.  A refusal that points at a file without saying what in it stopped
        # the emitter sends the reader back to re-run.
        kw = next((k for k in ROOT_KIND if k in doc), None)
        declared = sorted(k for k in doc if k not in _ANNOTATIONS)
        if kw is None:
            raise Refusal(
                "type",
                "",
                f"the root declares no kind keyword at all: {declared} are data keys, not "
                "schema keywords, so there is no type, no properties and no composition "
                "for a row to read -- and a class over them would state what no part of "
                "this document declares",
                kind=Kind.VERDICT,
            )
        raise Refusal(
            kw,
            "",
            f"a root is exactly one kind, this one's is read from {kw!r} (the root declares "
            f"{declared}), and no D2 row lowers that kind at a root",
            kind=Kind.VERDICT,
        )
    claimed[0][1](doc, symbol, "", mod)
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


def _composed_nodes(bundle_dir: Path, known: set[str]) -> dict[str, frozenset[str]]:
    """For each document, the pointers of its nodes that another document's root
    ``allOf`` COMPOSES.

    The companion to :func:`bundle.named_nodes`, and the same kind of fact: a function
    of the BUNDLE and not of the run's document set, so a module's ``__all__`` does not
    depend on who else was emitted (P7) and the one-document command writes the bytes the
    whole-population run writes.  :func:`exported` says what it is for -- a composing
    subclass re-uses the base's decided field, so the base's field types cross the module
    boundary while no ``$ref`` fragment names them.

    A bare conjunct composes the target's ROOT, whose pointer is ``""``; the one conjunct
    in this bundle that carries a fragment
    (``core/package-delivery-metric-value.json`` -> ``core/delivery-metric-aggregate.json#/oneOf/0``)
    composes that node, and it is recorded at its own pointer rather than folded into the
    root -- a branch's fields are not the union base's.

    **It sits here and not in ``codegen/bundle.py``, where it belongs**, only because
    this lane owns this module and not that one; moving it is one cut and one import.
    Known ceiling: it reads every portable document a second time, after
    ``named_nodes``'s own pass, which is ~2 s on the 3.2 bundle against a ~60 s run.
    Merging the two scans is the upgrade path, and it is the reason to move it.
    """
    out: dict[str, set[str]] = {}
    for document in sorted(known):  # sorted, like ``portable``: P7
        doc = bundle.read(bundle_dir, document)
        if not bundle.composes_at_the_root(doc):
            continue
        for conjunct in doc.get("allOf", []):
            uri = conjunct.get("$ref") if isinstance(conjunct, dict) else None
            if not isinstance(uri, str):
                continue
            head, into = bundle.split_ref(uri)
            # A LOCAL conjunct composes a node of this very document, whose symbol the
            # module already declares and never imports, so it is this document's own
            # entry -- the same reason ``named_nodes`` keys a local reference against the
            # referring document.
            target = bundle.document_for(head, known) if head else document
            if target is not None:
                # The ROOT's pointer is ``""`` in ``Module.declared`` and a node's is
                # ``/oneOf/0`` -- ``bundle.split_ref``'s own spelling, which is what
                # ``bundle.named_nodes`` produces and what ``decide_type`` matches
                # against.  ``"#"`` here would look right and match nothing.
                out.setdefault(target, set()).add(into)
    return {d: frozenset(p) for d, p in out.items()}


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
    composed = _composed_nodes(bundle_dir, known)
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
                # A LOCAL reference never arrives here.  It names a node of the
                # document being written, so there is no module to import from and
                # nothing for a binder to resolve: ``decide_type`` branches on the
                # empty document half first and asks ``compiler.local_reference`` for the
                # symbol this module declares.  This stays as the loud answer for a
                # caller that reaches the binder another way, rather than being
                # deleted and leaving ``document_for`` to return ``None`` and report a
                # pointer as a document the bundle does not hold.
                raise Refusal(
                    "$ref",
                    pointer,
                    f"{uri} is a pointer into this document, which is not a binding at "
                    "all -- the walk resolves one through compiler.local_reference and "
                    "never through a binder",
                    kind=Kind.VERDICT,
                )
            target = bundle.document_for(head, known)
            if target is None:
                raise Refusal(
                    "$ref", pointer, f"{uri} names no document of this bundle"
                , kind=Kind.VERDICT)
            try:
                mod, symbol = lower(target)  # the target emits first, or this refuses with it
            except Refusal as r:
                # **The fragment is NAMED here, not only the document.**  The chain
                # fires before the node is looked up -- the target refuses as a whole,
                # so the reference never reaches the node -- and a message naming only
                # the document sends the reader to a file without saying which of its
                # nodes was wanted.  Bundle-relative, so it reads as a pointer into
                # this bundle rather than as the URI's own base; a reference with no
                # fragment is unchanged, which is all 214 of the existing chains.
                #
                # **``through=r`` is the classification and the quoted text is for the
                # reader.**  Whether this document is pending or final is not a property
                # of its own sentence at all, it is whatever the target's is -- and that
                # used to be answered by parsing the target's refusal back out of the
                # string this line writes.  It is answered by carrying the object
                # instead: ``Refusal.resolved`` takes the target's, so a chain of any
                # depth is one attribute read and no sentence is parsed.
                wanted = f"{target}#{into}" if into else target
                raise Refusal(
                    "$ref",
                    pointer,
                    f"its target {wanted} is refused: {r}",
                    kind=Kind.CHAINED,
                    through=r,
                ) from r
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
                        kind=Kind.DEFERRED,
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
            raise Refusal(
                "$ref",
                "",
                f"a reference cycle: {' -> '.join([*inflight, document])}",
                kind=Kind.VERDICT,
            )
        inflight.append(document)
        doc = bundle.read(bundle_dir, document)
        try:
            mod, symbol = lower_document(
                document, doc, bind(document), named.get(document, frozenset())
            )
            # **The document the package will carry has to be DECIDABLE, and that is
            # checked here because a refusal belongs where every other one is.**  A
            # ``$ref`` left in it is a schema nothing local can decide, so
            # ``jsonschema`` fetches the target over the network; the write loop below
            # says what that costs.  ``bundle.resolved`` is the one resolution, and it
            # does not reach every position: ``resolve_all_refs`` descends
            # ``SCHEMA_KEYS`` and ``SCHEMA_OBJECT_KEYS`` only, and ``definitions`` and
            # ``$defs`` are in NEITHER -- by its own design, since a section asserts
            # nothing about an instance and a generator has no reason to look inside
            # one.  So a reference under a section survives resolution.
            #
            # Refused rather than shipped, and refused rather than excused: the
            # emitter cannot certify that a position nothing validates through TODAY
            # stays inert, and the alternative readings all weaken something -- a
            # second resolver (forbidden, D10 and ``bundle.resolved``'s own reason), a
            # post-generation strip of the section (forbidden, D9), or narrowing the
            # invariant to reachable positions, which is a check relaxed to fit.
            #
            # Measured over the whole bundle: 1 of 1,054 documents has every reference
            # under a section (``a2ui/si-catalog.json``, 24 of them), nothing in the
            # bundle references it, and no ``$ref`` names any of its nodes -- so this
            # refuses exactly one document and cascades to none.  It is reachable at
            # all only because salesagent-j3k2l.20 declares section entries and D2's
            # ``const`` row lowers the keyword that used to stop this document first.
            #
            # **CROSS-DOCUMENT only, and that is what makes the reason above true.**  A
            # LOCAL reference names a node of the very document the package carries, so
            # ``jsonschema`` resolves it against the referrer and fetches nothing --
            # ``bundle.resolved`` skips adding one to the store for exactly that reason.
            # It survives resolution under a section just as a cross-document one does,
            # and refusing it would be refusing a document that IS locally decidable.
            # Probed: without this clause the check refused ``core/chain.json``, the
            # fixture salesagent-j3k2l.20 wrote for a forward local reference, on
            # ``#/definitions/second``.
            unresolved = [
                (p, u)
                for p, u in bundle.references(bundle.resolved(bundle_dir, document))
                if bundle.split_ref(u)[0]
            ]
            if unresolved:
                pointer, uri = unresolved[0]
                raise Refusal(
                    "$ref",
                    pointer,
                    f"{uri} {refusal.UNRESOLVED_TARGET}, which leaves a "
                    f"reference under a definitions/$defs section untouched ({len(unresolved)} "
                    "here): the document the package would carry is not locally "
                    "decidable, and jsonschema would fetch the target over the network",
                    kind=Kind.UNRESOLVED,
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
        out.files[f"{rel}.py"] = render(mod, symbol, composed.get(document, frozenset()))
        out.emitted[document] = f"{PACKAGE}.{rel.replace('/', '.')}"
        out.declared[document] = dict(mod.declared)
        out.adopted[document] = dict(mod.adopted)
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
    aliases: dict[str, tuple[str, dict[str, Any]]] = {}
    for document in sorted(lowered):
        for name, (kind, cons) in lowered[document][0].aliases.items():
            constraints_module.record(aliases, name, kind, cons)
    out.beside[f"{constraints_module.MODULE.rsplit('.', 1)[1]}.py"] = constraints_module.declare(
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="codegen.emit", description=__doc__)
    ap.add_argument("--bundle", type=Path, required=True, help="the schema bundle directory")
    ap.add_argument("--tree", type=Path, default=TREE, help="where the modules are written")
    ap.add_argument(
        "--package",
        type=Path,
        default=None,
        help="where D5's alias module is written; a WHOLE-RUN artifact, so a run over "
        "part of the population must leave it out (see `write`)",
    )
    ap.add_argument("document", nargs="+", help="bundle-relative document paths")
    ns = ap.parse_args(argv)

    out = emit(ns.bundle, ns.document)
    write(out, ns.tree, ns.package)
    if ns.package is None:
        print(
            f"not written: {', '.join(sorted(out.beside))} "
            f"(D5's alias module is a whole-run artifact; pass --package to write it)"
        )
    for document in sorted(out.refusals):
        r = out.refusals[document]
        print(
            f"refused {document} ({r['resolved']}) at {r['pointer']} "
            f"on {r['keyword']}: {r['detail']}"
        )
    # **The report names the KINDS and not "refused" alone.**  "refused" admits "not
    # built yet", which is how `emitted + refused == 1054` stayed green over 385
    # documents waiting on rows nobody had written, so the one figure the exit
    # condition counts -- emitted plus VERDICTS -- is printed beside the partition
    # rather than left to a reader to assemble.
    counted = collections.Counter(r["resolved"] for r in out.refusals.values())
    verdicts = sum(counted[k] for k in refusal.FINAL_KINDS)
    print(
        f"emitted {len(out.emitted)} / refused {len(out.refusals)} "
        f"({', '.join(f'{k} {n}' for k, n in sorted(counted.items()))}); "
        f"accounted {len(out.emitted) + verdicts}; "
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
