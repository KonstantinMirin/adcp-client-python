"""Emit Python types for bundle documents named on the command line.

    python -m codegen.emit --bundle schemas/cache/3.2 core/pagination-request.json

The committed tree is the same command over this step's whole population, which
is derived from the bundle and never listed by hand (``tests/test_emit.py``
byte-compares the tree against exactly this):

    python -m codegen.emit --bundle schemas/cache/3.2 $(python -c 'from pathlib \
      import Path; from codegen import bundle; b = Path("schemas/cache/3.2"); \
      print(*[d for d in bundle.portable(b) if bundle.is_leaf_object(bundle.read(b, d)) \
      or bundle.references_a_property(bundle.read(b, d))])')

A document this command does not name is still emitted when a named one
REFERENCES it: a module cannot import a symbol from a module no run wrote, so
``emit`` walks ``$ref`` transitively and the run emits the closure.

The bundle directory is an argument (D9) and there is no default, so no version
literal can enter this package.  The output path is a function of the document
path (D1): ``core/pagination-request.json`` ->
``src/adcp/types/_schemas/core/pagination_request.py``.  There is no module
table, and the path is private (P8), so it is never a contract.

This step lowers an object root with ``properties``, whose properties are
scalars (with their constraints and their format), nested objects, typeless, or
a ``$ref`` to another document; and a scalar root, as the ``Annotated`` alias
D2 gives it, because a reference TARGET is one.  A cross-document ``$ref``
becomes an IMPORT of the target's symbol (P2) -- the target declares its type
once and the referencing module names it, so no constraint of the target has a
second spelling to drift from.  Every other shape is a later step's row in D2, and a document
carrying one is REFUSED by name, pointer and keyword rather than emitted
approximately.  A refusal is the designed outcome of a keyword this emitter does
not lower: a model that quietly ignores a constraint is wider than its schema,
which is the defect class P3 exists to remove.

The emitter owns its own layout and writes no file twice (D8): there is no
formatter and no patch pass.  P7 is held by construction rather than tested:
``emit`` sorts its document set, ``render`` sorts the import set, and the two
JSON artifacts are dumped with sorted keys, so the output is a function of
(bundle, document set, this module) and of nothing a caller orders.  What a
test CAN perturb is set iteration, and ``test_emit`` does, with two hash seeds.
"""

from __future__ import annotations

import argparse
import json
import keyword
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from codegen import bundle

#: Where a document's module lands, relative to the repository root.
TREE = Path("src") / "adcp" / "types" / "_schemas"
#: The import path of that tree, and of the hand-written base beside it.
PACKAGE = "adcp.types._schemas"
BASE_MODULE = "adcp.types._base"

SCALAR = {"string": "str", "integer": "int", "number": "float", "boolean": "bool"}

#: JSON Schema keyword -> pydantic ``Field`` kwarg, for a scalar.
CONSTRAINTS = {
    "minimum": "ge",
    "maximum": "le",
    "exclusiveMinimum": "gt",
    "exclusiveMaximum": "lt",
    "multipleOf": "multiple_of",
    "minLength": "min_length",
    "maxLength": "max_length",
    "pattern": "pattern",
}

#: ``format`` -> the Python type that admits exactly the format's values, and
#: the import that names it.  A format is in this table only when such a type
#: exists and a document in the emitted population uses it.  ``hostname`` and
#: ``email`` are deliberately ABSENT: neither has a type narrower than ``str``
#: here without adding a dependency or hand-writing a checker, and ``str`` is
#: already the document's own accepted set, because draft-07 ``format`` is an
#: annotation that ``jsonschema`` asserts nothing for.  A format with no row
#: falls through to its ``type``.
FORMATS = {
    "date": ("datetime", "date"),
    "date-time": ("datetime", "datetime"),
    "uri": ("pydantic", "AnyUrl"),
}

#: Keywords that annotate a node without constraining an instance.  Read and
#: carried where there is somewhere to carry them; never a reason to refuse.
#: ``default`` is here and is NOT transcribed: an optional property renders
#: ``= None`` (D4), so an omitted key round-trips as omitted under
#: ``exclude_unset`` instead of being filled in with a value the sender never
#: sent, and a required property keeps no default at all.
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


class Refusal(Exception):
    """One document this emitter will not approximate, and why."""

    def __init__(self, kw: str, pointer: str, detail: str) -> None:
        super().__init__(f"{pointer or '/'}: {kw}: {detail}")
        self.keyword = kw
        self.pointer = pointer or "/"
        self.detail = detail


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


# --------------------------------------------------------------------------- #
# lowering
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


def annotation(node: dict, pointer: str, name_hint: str, mod: Module) -> str:
    """The annotation text for one schema node.

    Nullability is NOT a question here (D4).  This returns the node's own type,
    and ``lower_object`` adds the ``| None`` arm an OPTIONAL property needs for
    the value an omitted key leaves on the attribute -- which is a fact about
    presence, not a claim that the document admits an explicit null.
    ``AdCPBaseModel.strict_validate`` asks the document about that.
    """
    if "$ref" in node:
        # P2: a reference is a REFERENCE.  The target's own module declares its
        # type once and this one names it; nothing of the target's shape is read
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
        return symbol

    kind = node.get("type")

    if kind is None:
        _check_keywords(node, pointer, set())
        if set(node) & set(CONSTRAINTS):
            raise Refusal(
                "type", pointer, "a typeless node carrying a constraint has nothing to apply it to"
            )
        mod.imports.add(("typing", "Any"))
        return "Any"  # D2's typeless row; the schema admits every value

    if isinstance(kind, list):
        raise Refusal("type", pointer, f"a multi-type node ({kind}) is step 6")

    if kind == "null":
        _check_keywords(node, pointer, {"type"})
        return "None"

    if kind == "object":
        if "properties" not in node:
            raise Refusal("type", pointer, "an object node with no properties is a mapping, step 6")
        return lower_object(node, name_hint, pointer, mod)

    if kind == "array":
        raise Refusal("type", pointer, "an array node is step 6")

    if kind not in SCALAR:
        raise Refusal("type", pointer, f"unknown type {kind!r}")

    _check_keywords(node, pointer, {"type", "format", *CONSTRAINTS})
    kwargs = [f"{CONSTRAINTS[k]}={node[k]!r}" for k in CONSTRAINTS if k in node]
    ann = SCALAR[kind]
    fmt = node.get("format")
    if isinstance(fmt, str) and fmt in FORMATS and not kwargs:
        # The format's own type, but only with no constraint beside it: a
        # `min_length` belongs to a string and means nothing on a `date`.  With
        # one present the node keeps its scalar type and its constraints, which
        # is the document's accepted set either way.
        module, ann = FORMATS[fmt]
        mod.imports.add((module, ann))
    if kwargs:
        mod.imports.add(("typing", "Annotated"))
        mod.imports.add(("pydantic", "Field"))
        ann = f"Annotated[{ann}, Field({', '.join(kwargs)})]"
    return ann


def lower_object(node: dict, name: str, pointer: str, mod: Module) -> str:
    """Append the class for an object node, children first, and return its name."""
    _check_keywords(node, pointer, {"type", "properties", "required", "additionalProperties"})
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

    lines: list[str] = []
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
        ann = annotation(sub, at, name + class_name(key), mod)
        if key not in required and ann not in ("None", "Any"):
            # D4: an optional renders plain ``T | None = None``.  The ``None`` arm
            # is the attribute's value for an omitted key, not a claim that the
            # document admits an explicit null -- ``strict_validate`` asks the
            # document about that.  Two annotations are left alone because they
            # already carry the arm: ``Any | None`` evaluates to ``Any`` (live,
            # one site: ``core/response.json``'s ``data``), and ``None`` cannot be
            # unioned with itself at all -- ``eval("None | None")`` is a TypeError,
            # so a ``{"type": "null"}`` optional would not import.  That second
            # arm matches no document in this step's population and is therefore
            # ungraded here; it is a guard against a latent import failure, not a
            # measured behaviour.
            ann = f"{ann} | None"
        if fname == key:
            lines.append(f"    {key}: {ann}" + ("" if key in required else " = None"))
            continue
        mod.imports.add(("pydantic", "Field"))
        default = "" if key in required else "default=None, "
        lines.append(f'    {fname}: {ann} = Field({default}alias="{key}")')

    if isinstance(node.get("additionalProperties"), dict):
        raise Refusal("additionalProperties", pointer, "a typed additionalProperties is step 6")
    mod.imports.add((BASE_MODULE, "AdCPBaseModel"))
    body: list[list[str]] = []
    doc = node.get("description")
    if isinstance(doc, str) and doc:
        # json.dumps of a str is a valid Python string literal, so a description
        # carrying a quote or a newline needs no escaping of its own here.
        body.append(["    " + json.dumps(doc)])
    extra = {False: "forbid", True: "allow"}.get(node.get("additionalProperties"))
    if extra:  # D7; absent leaves the base's default in place
        mod.imports.add(("pydantic", "ConfigDict"))
        body.append([f'    model_config = ConfigDict(extra="{extra}")'])
    body.append(lines)
    block = f"class {name}(AdCPBaseModel):\n" + "\n\n".join("\n".join(s) for s in body)
    mod.declare(name, pointer, block)
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


def lower_document(
    document: str, doc: dict, bind: Callable[[str, str], tuple[str, str]] = _no_binder
) -> tuple[Module, str]:
    title = doc.get("title")
    if not isinstance(title, str) or not title:
        raise Refusal("title", "", "the document declares no title to derive a name from")
    symbol = class_name(title)
    if not symbol.isidentifier():
        raise Refusal("title", "", f"the title {title!r} derives {symbol!r}, not an identifier")
    mod = Module(document=document, bind=bind)
    kind = doc.get("type")
    if "properties" in doc and kind in (None, "object"):
        lower_object(doc, symbol, "", mod)
    elif isinstance(kind, str) and kind in SCALAR:
        # D2's root-scalar row, which this step needs because a reference TARGET is
        # one 100 times over: `core/creative-revision-id.json` is a string with
        # `minLength`/`maxLength` and has no field to hang itself on.  An alias,
        # not a class -- a wrapper class would be a second name for the same node
        # (P2) and would make every referencing model carry an object where the
        # document carries a string.  A root array and a root mapping are step 6's
        # rows and still refuse below.
        #
        # D4 puts acceptance on ``strict_validate``, and an alias has no class to
        # carry one, so the module carries it: ``strict_alias`` is the same schema
        # lookup and the same refusal ``AdCPBaseModel.strict_validate`` uses, over
        # the same binding table, bound to this module's own row.  Without it the
        # harness would fall back to ``TypeAdapter`` -- the alias's CONSTRUCTOR --
        # and ``codegen.adapter`` refuses a binding whose entry point is that.
        ann = annotation(doc, "", symbol, mod)
        mod.imports.add((BASE_MODULE, "strict_alias"))
        mod.declare(
            symbol,
            "",
            f'{symbol} = {ann}\n\n\nstrict_validate = strict_alias(__name__, "{symbol}", {symbol})',
        )
    else:
        raise Refusal(
            "type", "", "this step emits an object root with properties, or a scalar root"
        )
    return mod, symbol


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #
@dataclass
class Emitted:
    files: dict[str, str] = field(default_factory=dict)  # path -> text
    bindings: dict[str, dict[str, Any]] = field(default_factory=dict)
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
    #: document -> (module, symbol, the document itself).  The document is kept
    #: because the binding row carries it (D4), and the row must carry the SAME
    #: read the lowering used rather than a second one.
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
        # The document travels WITH the binding: ``strict_validate`` decides
        # acceptance against the schema the class was generated from (D4), and
        # the bundle is a build-time input -- 124 MB, with a version in its path
        # -- so it cannot be the runtime source.  Written here, by the run that
        # lowered it, which is what makes P10's byte compare cover the schemas
        # the runtime asks and not only the modules.
        #
        # RESOLVED, and that is this step's correction to the row rather than a
        # preference: a reference is an import in the MODULE (P2), but a `$ref`
        # left in the ROW is a schema nothing local can decide, so `jsonschema`
        # fetches the target over the network -- see ``bundle.resolved``.  A
        # document with no reference resolves to itself, so the 34 rows step 1
        # wrote are unchanged by this.
        out.bindings[document] = {
            "module": f"{PACKAGE}.{rel.replace('/', '.')}",
            "symbol": symbol,
            "schema": bundle.resolved(bundle_dir, document) if bundle.references(doc) else doc,
        }
        parts = rel.split("/")[:-1]
        packages.update("/".join(parts[: i + 1]) for i in range(len(parts)))

    for document in sorted(refused):
        r = refused[document]
        out.refusals[document] = {"keyword": r.keyword, "pointer": r.pointer, "detail": r.detail}
    for pkg in packages:
        out.files[f"{pkg}/__init__.py"] = ""
    out.files["__init__.py"] = ""
    out.files["_bindings.json"] = json.dumps(out.bindings, indent=2, sort_keys=True) + "\n"
    out.files["_refusals.json"] = json.dumps(out.refusals, indent=2, sort_keys=True) + "\n"
    return out


def write(out: Emitted, tree: Path) -> None:
    """Write this run's files, and delete nothing.

    A stale module -- one emitted by an earlier run over a different document set
    -- is a real defect: it stays importable while no document produces it any
    more.  Pruning it here was tried and removed, because it makes the
    one-document command above destroy the other 33 modules of the committed
    tree, and a command whose demonstration wipes the tree gets run once.

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
        f"emitted {len(out.bindings)} / refused {len(out.refusals)}; "
        f"{len(set(ns.document))} named, the rest reached through a $ref"
    )
    return 1 if out.refusals else 0


if __name__ == "__main__":
    sys.exit(main())
