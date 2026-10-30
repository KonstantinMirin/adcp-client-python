"""Derive the facts the architecture audit grades, from the AST and never from prose.

Instruments, one per architectural goal of docs/plan/architecture.md:

  imports    -- the module-level import graph over codegen/ and src/adcp, so §11's
                arrow diagram can be checked edge by edge and cycles found.
  pydantic   -- every module importing pydantic / pydantic_core /
                datamodel_code_generator (§8's one-way boundary).
  dispatch   -- every `match` subject and every isinstance over codegen.schema.nodes
                kinds outside lower/decide.py (§5's one dispatch).
  keywords   -- the reader census of codegen.keywords: who imports it, and every
                string-literal set/frozenset of draft-07 keywords outside it (§3).
  text       -- modules before render.py whose code builds Python source text:
                suspicious string constants / f-strings carrying `def `, `class `,
                `import ` (§7's complete IR).

Run:  PYTHONPATH=.:src python survey/arch_audit.py <instrument>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# every first-party module under audit, by dotted name
def modules() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for base, prefix in ((ROOT / "codegen", "codegen"), (ROOT / "src" / "adcp", "adcp")):
        for p in sorted(base.rglob("*.py")):
            if "_schemas" in p.parts or "__pycache__" in p.parts:
                continue
            rel = p.relative_to(base).with_suffix("")
            dotted = prefix + ("." + ".".join(rel.parts) if rel.parts != ("__init__",) else "")
            dotted = dotted.removesuffix(".__init__")
            out[dotted] = p
    return out


def imports_of(path: Path, *, top_only: bool = False) -> set[str]:
    """Modules imported, split by depth: top-level only, or everything.

    A module-level import is a structural edge; a function-level one is the
    deferred import architecture.md §10 step 1 says is deleted, so the two are
    reported apart. ``if TYPE_CHECKING:`` blocks at module level count as
    top-level (the type checker sees them), and are tagged by the caller.
    """
    tree = ast.parse(path.read_text())
    found: set[str] = set()

    def record(node: ast.stmt) -> None:
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module)
            for a in node.names:
                found.add(node.module + "." + a.name)

    if top_only:
        for node in tree.body:
            record(node)
            if isinstance(node, ast.If):  # TYPE_CHECKING blocks
                for sub in node.body:
                    record(sub)
    else:
        for node in ast.walk(tree):
            record(node)
    return found


def graph(*, top_only: bool = False) -> dict[str, set[str]]:
    mods = modules()
    g: dict[str, set[str]] = {}
    for name, path in mods.items():
        raw = imports_of(path, top_only=top_only)
        g[name] = {m for m in raw if m in mods and m != name}
    return g


def cmd_imports() -> None:
    top = graph(top_only=True)
    full = graph()
    for src in sorted(full):
        for dst in sorted(full[src]):
            tag = "" if dst in top[src] else "   [deferred]"
            print(f"{src} -> {dst}{tag}")
    g = top
    # cycle check by DFS
    WHITE, GREY, BLACK = 0, 1, 2
    color = dict.fromkeys(g, WHITE)
    stack: list[str] = []

    def dfs(n: str) -> None:
        color[n] = GREY
        stack.append(n)
        for m in g.get(n, ()):
            if color.get(m) == GREY:
                print(f"CYCLE: {' -> '.join(stack[stack.index(m):])} -> {m}")
            elif color.get(m) == WHITE:
                dfs(m)
        stack.pop()
        color[n] = BLACK

    for n in list(g):
        if color[n] == WHITE:
            dfs(n)


FOREIGN = ("pydantic", "pydantic_core", "datamodel_code_generator")


def cmd_pydantic() -> None:
    for name, path in sorted(modules().items()):
        hits = {m.split(".")[0] for m in imports_of(path)} & set(FOREIGN)
        if hits:
            print(f"{name}: {sorted(hits)}")


NODE_KINDS = {
    "Reference", "Enumeration", "Constant", "Composition", "Union", "Object",
    "Mapping", "Array", "Scalar", "MultiType", "Null", "Typeless",
}


def cmd_dispatch() -> None:
    for name, path in sorted(modules().items()):
        if not name.startswith("codegen"):
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Match):
                # does any case pattern name a node kind class?
                kinds = set()
                for case in node.cases:
                    for sub in ast.walk(case.pattern):
                        if isinstance(sub, ast.Name) and sub.id in NODE_KINDS:
                            kinds.add(sub.id)
                        if isinstance(sub, ast.Attribute) and sub.attr in NODE_KINDS:
                            kinds.add(sub.attr)
                if kinds:
                    print(f"match-over-kinds {name}:{node.lineno} covers {len(kinds)}: {sorted(kinds)}")
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "isinstance":
                arg = node.args[1] if len(node.args) == 2 else None
                names = set()
                for sub in ast.walk(arg) if arg else ():
                    if isinstance(sub, ast.Name) and sub.id in NODE_KINDS:
                        names.add(sub.id)
                    if isinstance(sub, ast.Attribute) and sub.attr in NODE_KINDS:
                        names.add(sub.attr)
                if names:
                    print(f"isinstance-over-kinds {name}:{node.lineno}: {sorted(names)}")


DRAFT07 = {
    "type", "properties", "required", "items", "enum", "const", "allOf", "anyOf",
    "oneOf", "not", "if", "then", "else", "pattern", "format", "minLength",
    "maxLength", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "minItems", "maxItems", "uniqueItems", "contains", "additionalProperties",
    "patternProperties", "propertyNames", "minProperties", "maxProperties",
    "dependencies", "definitions", "$defs", "$ref", "default", "title",
    "description", "examples",
}


#: The census's own threshold: a collection counts where it names at least this many
#: draft-07 keywords and NOTHING but draft-07 keywords.  Three, because a one- or
#: two-name ``in (...)`` is a per-keyword dispatch arm rather than a table of keywords --
#: at one name there are 78 of them and the census stops being an instrument.
FLOOR = 3


def keyword_collections() -> list[tuple[str, int, bool, tuple[str, ...]]]:
    """The §3 census: ``(module, line, is a dict's keys, the keywords)`` per site.

    **The one derivation of it**, so the CLI below and
    ``tests/test_keywords.py::test_the_keyword_set_literal_census_is_the_sites_named_here``
    cannot report two different numbers.  A census printed by one reader and gated by
    another is how seven of this epic's censuses went stale
    (``adcp-client-python-3be.8``).
    """
    out: list[tuple[str, int, bool, tuple[str, ...]]] = []
    for name, path in sorted(modules().items()):
        if name == "codegen.keywords" or not name.startswith("codegen"):
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
                elements, keys = node.elts, False
            elif isinstance(node, ast.Dict):
                elements, keys = node.keys, True
            else:
                continue
            vals = [e.value for e in elements if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            hits = tuple(v for v in vals if v in DRAFT07)
            # ``len(hits) == len(vals)`` and NOT ``== len(elements)``: a claim set
            # written ``{"type", "properties", *stated.screen}`` spreads a derived set
            # beside its literal names, and the literal names are what the census is
            # about.  Tightening this to the whole collection silently dropped three
            # sites when it was tried.
            if len(hits) >= FLOOR and len(hits) == len(vals):
                out.append((name, node.lineno, keys, hits))
    return out


def cmd_keywords() -> None:
    mods = modules()
    print("# importers of codegen.keywords")
    for name, path in sorted(mods.items()):
        if any(m == "codegen.keywords" or m.startswith("codegen.keywords.") for m in imports_of(path)):
            print(f"  {name}")
    sites = keyword_collections()
    print(
        f"# literal keyword collections (>={FLOOR} draft-07 keywords) outside "
        f"codegen/keywords.py: {len(sites)}"
    )
    for name, line, keys, hits in sites:
        print(f"  {name}:{line}{' (dict keys)' if keys else ''}: {list(hits)}")


PY_MARKERS = ("def ", "class ", "import ", "from ", " = Field(", "model_config")


def cmd_text() -> None:
    walk_modules = [n for n in modules() if n.startswith(("codegen.schema", "codegen.lower", "codegen.ir", "codegen.bundle", "codegen.keywords", "codegen.compiler", "codegen.constraints"))]
    for name in sorted(walk_modules):
        path = modules()[name]
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                v = node.value
                if any(m in v for m in PY_MARKERS) and not v.strip().startswith(("#", '"')) and len(v) < 400:
                    # skip docstrings: those are Expr statements' values; approximate by col 0 blocks
                    print(f"  {name}:{node.lineno}: {v[:90]!r}")


if __name__ == "__main__":
    {"imports": cmd_imports, "pydantic": cmd_pydantic, "dispatch": cmd_dispatch,
     "keywords": cmd_keywords, "text": cmd_text}[sys.argv[1]]()
