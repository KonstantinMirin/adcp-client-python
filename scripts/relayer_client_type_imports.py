"""Move upstream's test imports of LIBRARY types off the compiler's namespace.

``adcp.types`` is where the compiler emits and nothing else lives there.  Upstream filed
their hand-written SDK types under ``types/`` too, so their own tests reach for them at
``from adcp.types import AgentConfig, Protocol`` -- and that is the single largest cause
of collection failure in the substituted tree: eleven test modules abort on
``cannot import name 'AgentConfig' from 'adcp.types'`` before a single assertion runs.

**THE REWRITE IS KEYED ON WHAT FAILS TO RESOLVE, NEVER ON THE WORD.**  Eight of the
twenty-one client names are ALSO emitted -- ``TaskStatus``, ``Policy``,
``PolicyExemplars``, ``PolicyHistory``, ``PolicyRevision``, ``PolicySummary``,
``ResolvedBrand``, ``ResolvedProperty`` -- and for those ``from adcp.types import X``
already resolves, to OUR class.  ``adcp.types.TaskStatus`` is the nine-member enum from
``enums/task-status.json``; ``adcp.TaskStatus`` is upstream's five-member one.  Rewriting
a name that already resolves would silently swap the class under a passing test, which is
a behaviour change wearing an import fix's clothes.  So the population is exactly the
names that do NOT resolve at ``adcp.types`` today, and the rewrite cannot alter the
meaning of any import that works.

Destination, per name, preferring upstream's own documented public path:

* ``adcp`` -- where upstream's own ``tests/test_public_api.py::
  test_client_types_are_exported`` already asserts the name lives (``adcp.AgentConfig``,
  ``adcp.Protocol``).  This is a rewrite TOWARD upstream's contract, not away from it.
* ``adcp.core`` -- for the names upstream never re-exported at top level
  (``Activity``, ``DebugInfo``, ``is_loopback_http_uri`` and the rest).

Run ``--check`` to print the plan and touch nothing.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import pathlib
import sys
import typing

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
NAMESPACE = "adcp.types"

#: ``line-length`` in ``pyproject.toml``, which governs ruff and black alike.
LIMIT = 100


def client_names() -> dict[str, str]:
    """Each client-library name that does NOT resolve at ``adcp.types``, to its home.

    Derived from the three loaded modules rather than listed, so a name a later upstream
    release adds or drops moves through here with nothing edited.
    """
    core = importlib.import_module("adcp.core")
    top = importlib.import_module("adcp")
    surface = importlib.import_module(NAMESPACE)

    out: dict[str, str] = {}
    for name, obj in vars(core).items():
        if name.startswith("_"):
            continue
        if isinstance(obj, typing.TypeVar):
            # `T = TypeVar("T")` is a PARAMETER, not a name any consumer imports. Keeping
            # it put `from adcp.core import T` in the plan for a word no test ever writes.
            continue
        if getattr(obj, "__module__", None) != "adcp.core" and name != "DEFAULT_MAX_RESPONSE_BYTES":
            continue
        if getattr(surface, name, None) is not None:
            continue  # already resolves -- and to the EMITTED class; do not touch it
        out[name] = "adcp" if getattr(top, name, None) is obj else "adcp.core"
    return out


def plan(path: pathlib.Path, homes: dict[str, str]) -> list[tuple[int, int, list[str]]]:
    """``(start, end, replacement lines)`` for every ``from adcp.types import`` to split."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []
    edits: list[tuple[int, int, list[str]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != NAMESPACE or node.level:
            continue
        moving = [a for a in node.names if a.name in homes]
        if not moving:
            continue
        staying = [a for a in node.names if a.name not in homes]
        pad = " " * node.col_offset

        def spell(aliases: list[ast.alias], home: str) -> list[str]:
            """One line, or the parenthesized form when one line would exceed the limit.

            ``line-length = 100`` in ``pyproject.toml`` governs both ruff and black here, so
            a collapsed nine-name import is a new E501 the rewrite would be introducing.
            """
            words = [
                a.name if not a.asname else f"{a.name} as {a.asname}"
                for a in sorted(aliases, key=lambda a: a.name)
            ]
            flat = f"{pad}from {home} import {', '.join(words)}"
            if len(flat) <= LIMIT:
                return [flat]
            return [
                f"{pad}from {home} import (",
                *(f"{pad}    {word}," for word in words),
                f"{pad})",
            ]

        lines: list[str] = []
        for home in ("adcp", "adcp.core"):
            group = [a for a in moving if homes[a.name] == home]
            if group:
                lines.extend(spell(group, home))
        if staying:
            lines.extend(spell(staying, NAMESPACE))
        edits.append((node.lineno, node.end_lineno or node.lineno, lines))
    return edits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="print the plan, write nothing")
    args = ap.parse_args()

    homes = client_names()
    if not homes:
        print("no unresolvable client-library name found -- nothing to relayer", file=sys.stderr)
        return 1
    print(f"{len(homes)} client names do not resolve at {NAMESPACE}:")
    for name, home in sorted(homes.items()):
        print(f"    {name:<28} -> {home}")

    touched = 0
    moved = 0
    for path in sorted(TESTS.rglob("*.py")):
        edits = plan(path, homes)
        if not edits:
            continue
        touched += 1
        moved += len(edits)
        rel = path.relative_to(ROOT)
        print(f"\n  {rel}")
        original = path.read_text(encoding="utf-8").splitlines()
        for start, end, lines in edits:
            for old in original[start - 1 : end]:
                print(f"    - {old}")
            for new in lines:
                print(f"    + {new}")
        if args.check:
            continue
        for start, end, lines in sorted(edits, reverse=True):
            original[start - 1 : end] = lines
        path.write_text("\n".join(original) + "\n", encoding="utf-8")

    verb = "would rewrite" if args.check else "rewrote"
    print(f"\n{verb} {moved} import statements across {touched} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
