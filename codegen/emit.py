"""Emit Python types for bundle documents named on the command line.

    python -m codegen.emit --bundle schemas/cache/3.2 core/pagination-request.json

The committed tree is the same command over this step's whole population, which
is derived from the bundle and never listed by hand (``tests/test_emit.py``
grades the tree against exactly this):

    python -m codegen.emit --bundle schemas/cache/3.2 $(python -c 'from pathlib \
      import Path; from codegen import bundle; b = Path("schemas/cache/3.2"); \
      print(*[d for d in bundle.portable(b) if bundle.is_leaf_object(bundle.read(b, d)) \
      or bundle.references_a_property(bundle.read(b, d))])')

A document this command does not name is still emitted when a named one
REFERENCES it: a module cannot import a symbol from a module no run wrote, so
``emit`` walks ``$ref`` transitively and the run emits the closure.

**This module is the walk, and it decides; it writes no annotation text.**
``docs/plan/rebuild-plan.md`` §1 puts the seam at the decision: everything here
reads the schema and decides what a node IS -- a class, a type, a field, a
constraint, a default, a name, what ``extra`` is -- and ``codegen.compiler``
hands that decision to ``datamodel-code-generator``'s pydantic-v2 model layer,
which writes the Python.  dmcg's parser never runs.  What this module still owns
in the output is the MODULE around the classes: the header, the import block, the
``__all__``, and the two statements a root-scalar alias needs, because no
compiler template has a slot for a line beside an alias.

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
import keyword
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from adcp.types._base import SchemaRef
from codegen import bundle, compiler, harness
from codegen.refusal import Refusal

#: Where a document's module lands, relative to the repository root.
TREE = Path("src") / "adcp" / "types" / "_schemas"
#: The import path of that tree, and of the hand-written base beside it.
PACKAGE = "adcp.types._schemas"
BASE_MODULE = "adcp.types._base"

SCALAR = {"string": "str", "integer": "int", "number": "float", "boolean": "bool"}

#: The JSON Schema constraint keywords a scalar node can carry.  The spelling is
#: the DOCUMENT'S, and it stays the document's all the way into the compiler --
#: see ``compiler.CONSTRAINTS`` and gate 1 there.
CONSTRAINTS = compiler.CONSTRAINTS

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

#: Keywords that annotate a node without constraining an instance.  ``default``
#: and ``description`` are carried by the compiler (they are rendering, and
#: rendering is what the compiler is for); the rest have nowhere to go and are
#: never a reason to refuse.
ANNOTATIONS = frozenset(
    {
        "$schema",
        "$id",
        "$comment",
        "title",
        "description",
        "examples",
        "example",
        "default",
        "deprecated",
        "readOnly",
        "writeOnly",
    }
)


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
    while keyword.iskeyword(name) or name.startswith("model_") or hasattr(BaseModel, name):
        name += "_"
    return name


def schema_ref(document: str, pointer: str) -> SchemaRef:
    """The schema reference a class at ``pointer`` of ``document`` carries."""
    return SchemaRef(document, f"#{pointer}")


# --------------------------------------------------------------------------- #
# the walk: what each node IS
# --------------------------------------------------------------------------- #
def _no_binder(uri: str, pointer: str) -> tuple[str, str]:
    """The default binder: a document lowered on its own resolves no reference.

    ``emit`` supplies the real one, which owns the walk.  Lowering a document
    without it refuses its references by name rather than inventing an import, so
    there is no path on which a reference is silently dropped.
    """
    raise Refusal("$ref", pointer, f"no reference binder: {uri} cannot be resolved to a module")


@dataclass
class Module:
    document: str
    #: ``(uri, pointer) -> (import module, symbol)``; see ``emit``.
    bind: Callable[[str, str], tuple[str, str]] = _no_binder
    #: The formats this document's own draft asserts; see ``asserted_formats``.
    #: Empty by default, so a node lowered outside ``lower_document`` selects no
    #: format-derived type rather than one nothing checks.
    asserted: frozenset[str] = frozenset()
    imports: set[tuple[str, str]] = field(default_factory=set)  # (module, name)
    blocks: list[str] = field(default_factory=list)
    names: set[str] = field(default_factory=set)

    def declare(self, name: str, pointer: str, block: str) -> None:
        if name in self.names:
            raise Refusal(
                "title",
                pointer,
                f"two nodes in this document derive the class name {name!r}",
            )
        self.names.add(name)
        self.blocks.append(block)


def _check_keywords(
    node: dict,
    pointer: str,
    handled: set[str],
    why: str = "this step lowers no such keyword (a later D2 row does)",
) -> None:
    for key in sorted(node):
        if key in handled or key in ANNOTATIONS or key.startswith("x-"):
            continue
        raise Refusal(key, pointer, why)


@dataclass(frozen=True)
class Decided:
    """What the walk decided one schema node IS.

    ``format`` is set only when ``type`` does NOT already carry the format -- the
    compiler then states it as an annotation rather than as a type.  Keeping the
    two separate here is what makes the drop impossible to make by accident: a
    format is either in the type or in this field, and never nowhere.
    """

    type: compiler.Type
    constraints: dict[str, Any] = field(default_factory=dict)
    format: str | None = None


def decide_type(node: dict, pointer: str, name_hint: str, mod: Module) -> Decided:
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
        _check_keywords(node, pointer, {"$ref"}, "a sibling of $ref, which draft-07 ignores")
        module, symbol = mod.bind(node["$ref"], pointer)
        mod.imports.add((module, symbol))
        return Decided(compiler.Type(symbol, local=True))

    kind = node.get("type")

    if kind is None:
        _check_keywords(node, pointer, set())
        if set(node) & set(CONSTRAINTS):
            raise Refusal(
                "type", pointer, "a typeless node carrying a constraint has nothing to apply it to"
            )
        return Decided(compiler.Type("typing.Any"))  # D2's typeless row

    if isinstance(kind, list):
        raise Refusal("type", pointer, f"a multi-type node ({kind}) is step 6")

    if kind == "null":
        _check_keywords(node, pointer, {"type"})
        return Decided(compiler.Type("None"))

    if kind == "object":
        if "properties" not in node:
            raise Refusal("type", pointer, "an object node with no properties is a mapping, step 6")
        return Decided(compiler.Type(lower_object(node, name_hint, pointer, mod), local=True))

    if kind == "array":
        raise Refusal("type", pointer, "an array node is step 6")

    if kind not in SCALAR:
        raise Refusal("type", pointer, f"unknown type {kind!r}")

    _check_keywords(node, pointer, {"type", "format", *CONSTRAINTS})
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


def lower_object(
    node: dict,
    name: str,
    pointer: str,
    mod: Module,
    *,
    bases: tuple[str, ...] = (),
    decided: dict[str, Decided] | None = None,
    body_lines: tuple[str, ...] = (),
) -> str:
    """Append the class for an object node, children first, and return its name.

    The three keyword arguments are what a COMPOSITION needs and a leaf object does not,
    and each defaults to the leaf's answer, so step 1's and step 2's call sites are
    unchanged and so is every module they emit:

    * ``bases`` -- the classes this one derives from (``compiler.Class.bases``).  Empty
      leaves ``AdCPBaseModel``.  D7's ``allOf`` row and §4's union row both need it.
    * ``decided`` -- a per-property type the CALLER has already decided, by property key.
      It exists so a lowering that owns a keyword for one position can apply it there
      without claiming the keyword everywhere: §4's union row turns a branch's ``const``
      into a ``Literal``, and putting that into ``decide_type`` instead would emit a
      ``const`` row for step 1's and step 2's own populations too and collide with
      whichever step claims D2's ``const`` row in full.
    * ``body_lines`` -- lines appended to the class body after ``__adcp_schema__``, for a
      fact that is not recoverable at run time.
    """
    _check_keywords(node, pointer, {"type", "properties", "required", "additionalProperties"})
    if node.get("type") != "object":
        # A node carrying ``properties`` and no ``type`` ADMITS A NON-OBJECT: JSON Schema
        # applies ``properties`` only to objects and asserts nothing about anything else,
        # so `{"properties": {"a": {"type": "string"}}, "required": ["a"]}` admits
        # ``"hello"`` and ``42`` -- measured with `jsonschema` on exactly that node.  No
        # class can, so the model is NARROWER than its document, which is the defect P3
        # removes.
        #
        # This condition read ``in (None, "object")`` and 0 of the 43 documents emitted
        # before this step exercise the ``None`` arm -- every one of them declares
        # ``type: object`` -- so the tolerance was latent rather than relied on.  Step 5's
        # union BRANCHES are the first population to reach it, and they reach it in the
        # worst way: the accepts check reports ``model_type`` on a valid instance, which
        # is the model refusing a payload the document admits.
        raise Refusal(
            "type",
            pointer,
            f"an object node must declare type: object; this one declares "
            f"{node.get('type', '<absent>')!r}, so the document admits a non-object that "
            "no class can",
        )
    props = node["properties"]
    if not isinstance(props, dict) or not props:
        raise Refusal("properties", pointer, "an object node with no property declared")
    required = node.get("required", [])
    undeclared = [r for r in required if r not in props]
    if undeclared:
        raise Refusal(
            "required",
            pointer,
            f"required names no property declares: {undeclared} (step 7's rule, not a field)",
        )

    fields: list[compiler.Property] = []
    spelled: dict[str, str] = {}
    for key, sub in props.items():
        if not isinstance(sub, dict):
            raise Refusal("properties", f"{pointer}/properties/{key}", "property is not a schema")
        at = f"{pointer}/properties/{key}"
        fname = field_name(key)
        if fname in spelled:
            raise Refusal(
                "properties", at, f"{key!r} and {spelled[fname]!r} both spell the field {fname!r}"
            )
        spelled[fname] = key
        decided_type = (decided or {}).get(key) or decide_type(sub, at, name + class_name(key), mod)
        is_required = key in required
        default = compiler.MISSING
        if "default" in sub:
            if is_required:
                # No rendering carries it: a pydantic field with a default is not
                # required, so transcribing one here would widen the model's
                # accepted set to admit an instance omitting a key the document
                # demands -- and the schema half of `strict_validate` would hide
                # that in both acceptance directions.  5 of the bundle's 339
                # property defaults sit on a required property; none is in this
                # step's population, so this refusal is a guard rather than a
                # measured behaviour, and the step whose population reaches one
                # decides between `json_schema_extra` and refusing.
                raise Refusal(
                    "default",
                    at,
                    "a default on a REQUIRED property has no rendering that does not also "
                    "make the property optional",
                )
            default = sub["default"]
        doc = sub.get("description")
        fields.append(
            compiler.Property(
                name=fname,
                wire=key,
                type=decided_type.type,
                required=is_required,
                default=default,
                description=doc if isinstance(doc, str) and doc else None,
                constraints=decided_type.constraints,
                format=decided_type.format,
            )
        )

    if isinstance(node.get("additionalProperties"), dict):
        raise Refusal("additionalProperties", pointer, "a typed additionalProperties is step 6")
    description = node.get("description")
    rendered = compiler.render(
        compiler.Class(
            name=name,
            ref=schema_ref(mod.document, pointer),
            properties=tuple(fields),
            description=description if isinstance(description, str) and description else None,
            # D7; absent leaves the base's default in place
            extra={False: "forbid", True: "allow"}.get(node.get("additionalProperties")),
            bases=bases,
            body_lines=body_lines,
        )
    )
    mod.imports |= rendered.imports
    mod.declare(name, pointer, rendered.text)
    return name


# --------------------------------------------------------------------------- #
# the module text (D8: the emitter owns its layout)
# --------------------------------------------------------------------------- #
def _import_rank(module: str) -> int:
    """stdlib, the third-party library, this package's own base, then a sibling
    module of this tree (always relative, so always ``.``-prefixed)."""
    if module.startswith("."):
        return 3
    if module == BASE_MODULE:
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
# the dispatch table (§ Layout)
# --------------------------------------------------------------------------- #
#: A lowering: it appends this document's classes to the module and returns the symbol the
#: module exports.
Lowering = Callable[[dict, str, "Module"], str]


def _is_object_root(doc: dict) -> bool:
    """D2's object row: a root with ``properties``.

    The union exclusion is what keeps this row and step 5's DISJOINT, and it is not a
    precedence rule dressed up as a predicate: a root ``oneOf``/``anyOf`` makes the
    document a union whatever else it declares, and 88 of the bundle's 156 union roots
    also declare ``properties``.  Without the clause the table has two rows claiming 88
    documents, which § Layout calls a build failure.
    """
    return (
        "properties" in doc and doc.get("type") in (None, "object") and not bundle.union_root(doc)
    )


def _is_scalar_root(doc: dict) -> bool:
    """D2's root-scalar row.  Union-excluded for the same reason, and it is reached: the
    bundle has one union root declaring a non-object ``type``."""
    kind = doc.get("type")
    return isinstance(kind, str) and kind in SCALAR and not bundle.union_root(doc)


@functools.cache
def dispatch() -> tuple[tuple[Callable[[dict], bool], Lowering], ...]:
    """The ``(selector, lowering)`` pairs, UNORDERED.

    A document selected by two rows is a build failure and not a precedence puzzle, so the
    rows are disjoint by construction and :func:`lower_document` raises rather than
    choosing.  A selector is its step's own population test, which is what stops a row
    claiming a document its step does not count -- step 5's is ``bundle.union_root``, and
    the same function is what its lowering reads the keyword with.

    The lowering modules are imported HERE and not at module scope: each one imports this
    module for the walk it extends (``lower_object``, ``Module``, ``Decided``), so a
    module-scope import either way round is a cycle.  Cached, so the import happens once.
    """
    from codegen.lower import union

    return (
        (_is_object_root, _lower_object_root),
        (_is_scalar_root, _lower_scalar_root),
        (bundle.union_root, union.lower_union),
    )


def lower_document(
    document: str, doc: dict, bind: Callable[[str, str], tuple[str, str]] = _no_binder
) -> tuple[Module, str]:
    title = doc.get("title")
    if not isinstance(title, str) or not title:
        raise Refusal("title", "", "the document declares no title to derive a name from")
    symbol = class_name(title)
    if not symbol.isidentifier():
        raise Refusal("title", "", f"the title {title!r} derives {symbol!r}, not an identifier")
    mod = Module(document=document, bind=bind, asserted=asserted_formats(doc))
    chosen = [low for selector, low in dispatch() if selector(doc)]
    if len(chosen) > 1:
        raise RuntimeError(
            f"{document}: selected by {len(chosen)} dispatch rows "
            f"({', '.join(f.__name__ for f in chosen)}); the table is unordered, so this "
            "is a build failure and not a precedence question"
        )
    if not chosen:
        raise Refusal(
            "type", "", "no dispatch row selects this document: an object root with "
            "properties, a scalar root and a union root are the rows that exist"
        )
    chosen[0](doc, symbol, mod)
    return mod, symbol


def _lower_object_root(doc: dict, symbol: str, mod: Module) -> str:
    return lower_object(doc, symbol, "", mod)


def _lower_scalar_root(doc: dict, symbol: str, mod: Module) -> str:
    """D2's root-scalar row, which step 2 needs because a reference TARGET is one 100
    times over: ``core/creative-revision-id.json`` is a string with
    ``minLength``/``maxLength`` and has no field to hang itself on.  An alias, not a class
    -- a wrapper class would be a second name for the same node (P2) and would make every
    referencing model carry an object where the document carries a string.  A root array
    and a root mapping are step 6's rows and no row selects them.

    The ANNOTATION is still the compiler's: the same field rendering a class property gets,
    read off the field instead of out of a class body, so a constraint on an alias and a
    constraint on a property cannot come to be spelled two ways.  What is ours is the two
    module-level STATEMENTS, and §1 says why: no compiler template has a slot for a line
    beside an alias.

    KNOWN CEILING: an alias has no ``ConfigDict``, so it cannot carry the per-class
    ``regex_engine`` a look-around pattern needs, and ``strict_alias`` builds its
    ``TypeAdapter`` at import.  A scalar root carrying look-around would therefore fail to
    IMPORT once the base stops forcing ``python-re``.  Measured over step 2's population:
    5 scalar roots, 2 carrying a ``pattern`` (both ``^[a-z0-9_]+$``, which the default
    engine compiles) and 0 carrying look-around, so no document here reaches it.  The
    failure is an ImportError at the gate rather than a silent widening, so the upgrade
    path is for the step whose population reaches one: either refuse such a document by
    name, or wrap the alias in a ``RootModel`` that has a config slot.
    """
    decided_type = decide_type(doc, "", symbol, mod)
    description = doc.get("description")
    rendered = compiler.render_alias(
        symbol,
        decided_type.type,
        decided_type.constraints,
        description=description if isinstance(description, str) and description else None,
        format=decided_type.format,
    )
    mod.imports |= rendered.imports
    mod.imports.add((BASE_MODULE, "strict_alias"))
    ref = schema_ref(mod.document, "")
    mod.declare(
        symbol,
        "",
        f"__adcp_schema__ = {ref!r}\n\n"
        f"{rendered.text}\n\n\n"
        f'strict_validate = strict_alias(__adcp_schema__, "{symbol}", {symbol})',
    )
    return symbol


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
    lowered: dict[str, tuple[Module, str, dict]] = {}
    refused: dict[str, Refusal] = {}
    inflight: list[str] = []

    def bind(referencing: str) -> Callable[[str, str], tuple[str, str]]:
        def do(uri: str, pointer: str) -> tuple[str, str]:
            target = bundle.document_for(uri, known)
            if target is None:
                raise Refusal(
                    "$ref",
                    pointer,
                    f"{uri} names no document of this bundle (a fragment names a node "
                    "inside one, which needs a name of its own: a later step's row)",
                )
            try:
                _, symbol = lower(target)  # the target emits first, or this refuses with it
            except Refusal as r:
                raise Refusal("$ref", pointer, f"its target {target} is refused: {r}") from r
            return relative_module(referencing, target), symbol

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
            mod, symbol = lower_document(document, doc, bind(document))
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
    sys.exit(main())
