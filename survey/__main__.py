"""The index of every instrument, so a question is answered by CALLING one.

``python -m survey`` lists them; ``python -m survey union --bundle …`` runs one.
Same entry-point shape as ``python -m codegen``, for the same reason: a package
that is runnable says so in ``__main__.py`` and needs no second convention.

**Why this exists.**  Eighteen instruments were written and then not found again.
``survey/union_census.py`` was built, measured the bucket sizes this project
quoted by hand for days, and sat unmerged on a branch while a row was filed to
BUILD it.  A tool nobody can enumerate is a tool nobody uses, and the cost is
paid every time in a throwaway script whose predicate differs subtly from the
last one's -- which is how four figures came to be wrong in a single session:
names counted as objects, bindings as declarations, bundle contents as bundle
origin, shared structure as shared subject.

**THE LIST IS GLOBBED AND NEVER WRITTEN DOWN.**  A hand-maintained index goes
stale on the first new instrument, which is the failure this file exists to end
-- so the set is the filesystem's answer, the one-line purpose is read from each
module's own docstring, and the flags a caller must supply are read off its own
``argparse`` calls.  An instrument that drops its docstring loses its description
and SAYS SO, rather than silently reading as having none.

**It runs an instrument in THIS interpreter** (``runpy``), not in a subprocess:
the caller already chose the interpreter and the import path by invoking
``python -m survey``, and spawning a second one would let the two disagree --
which ``tests/compiled.py`` records as a measured hazard elsewhere in this tree.
"""

from __future__ import annotations

import argparse
import ast
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Where instruments live.  Directories, not a list of files, for the reason above.
WHERE = ("survey", "tools/parity")

#: The flags worth showing beside a name, because a caller cannot run without them.
NOTABLE = ("--bundle", "--tree", "--wheel", "--tsv")


def _module(path: Path) -> ast.Module | None:
    """The parsed module, or ``None`` where it does not parse."""
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return None


def _purpose(tree: ast.Module | None) -> str:
    """The first line of the module docstring, read from the AST and not by regex."""
    if tree is None:
        return "(does not parse)"
    doc = ast.get_docstring(tree)
    if not doc:
        return "(no docstring -- this instrument does not say what it answers)"
    first = doc.strip().splitlines()[0].strip()
    return first or "(docstring opens empty)"


def _runnable(tree: ast.Module | None) -> bool:
    """Does the module guard a ``__main__`` block?  Read structurally, not by text."""
    if tree is None:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            for sub in ast.walk(node.test):
                if isinstance(sub, ast.Constant) and sub.value == "__main__":
                    return True
    return False


def _flags(tree: ast.Module | None) -> list[str]:
    """The notable flags, read off the module's own ``add_argument`` calls."""
    if tree is None:
        return []
    calls = (
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
    )
    return sorted(
        {
            arg.value
            for call in calls
            for arg in call.args
            if isinstance(arg, ast.Constant) and arg.value in NOTABLE
        }
    )


def instruments() -> dict[str, tuple[Path, str, list[str]]]:
    """Every runnable instrument, keyed on the short name a caller types."""
    found: dict[str, tuple[Path, str, list[str]]] = {}
    for where in WHERE:
        for path in sorted((ROOT / where).glob("*.py")):
            if path.name.startswith("_"):
                continue
            tree = _module(path)
            if not _runnable(tree):
                continue
            stem = path.stem
            short = stem.rsplit("_", 1)[0] if stem.endswith(("_census", "_collisions")) else stem
            key = short if short not in found else stem
            found[key] = (path, _purpose(tree), _flags(tree))
    return found


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m survey",
        description=__doc__.strip().splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("instrument", nargs="?", help="which one to run; omit to list")
    parser.add_argument("rest", nargs=argparse.REMAINDER, help="its own arguments")
    args = parser.parse_args(argv)

    found = instruments()
    if args.instrument is None:
        print(f"{len(found)} instruments. Call one rather than writing a script.\n")
        width = max(len(name) for name in found)
        for name, (path, purpose, flags) in sorted(found.items()):
            print(f"  {name:<{width}}  {purpose[:86]}")
            tail = f"   needs: {' '.join(flags)}" if flags else ""
            print(f"  {'':<{width}}  {path.relative_to(ROOT)}{tail}")
        print("\n  python -m survey <name> [args]     run one")
        print("  python -m survey <name> --help    its arguments")
        print("\n./check is the fast loop: the three emission numbers in under a second.")
        return 0

    if args.instrument not in found:
        near = sorted(k for k in found if args.instrument in k or k in args.instrument)
        print(f"no instrument named {args.instrument!r}", file=sys.stderr)
        if near:
            print(f"did you mean: {', '.join(near)}", file=sys.stderr)
        print("run `python -m survey` for the list", file=sys.stderr)
        return 2

    path, _, _ = found[args.instrument]
    sys.argv = [str(path), *args.rest]
    runpy.run_path(str(path), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
