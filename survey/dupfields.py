"""The DUPLICATE FIELD-SET figure, read off the emitted tree's own text.

Reading 4's measure: how many classes the tree writes, how many distinct field sets more
than one class writes, and how many classes those cover.  Parsed with ``ast`` over
``Emitted.files`` rather than from a record the emitter keeps, because the claim is about
what a CONSUMER reads -- two class statements with one field set -- and the text is what a
consumer has.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))

BUNDLE = Path("schemas/cache/3.2")


def field_sets(files: dict[str, str]) -> dict[tuple[str, ...], list[tuple[str, str]]]:
    """field set -> every ``(module, class)`` that writes it, over the whole tree."""
    out: dict[tuple[str, ...], list[tuple[str, str]]] = {}
    for path, text in sorted(files.items()):
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.ClassDef):
                continue
            # The PROTOCOL fields and not the machinery: a name beginning with ``_`` is
            # the emitter's own (``__adcp_schema__``, ``_BRANCH_DISCRIMINATOR``,
            # ``_adcp_rules``), it is stated by every class of its kind, and counting it
            # would report the emitter's uniformity as the bundle's duplication.
            fields = tuple(
                sorted(
                    s.target.id
                    for s in node.body
                    if isinstance(s, ast.AnnAssign)
                    and isinstance(s.target, ast.Name)
                    and not s.target.id.startswith("_")
                )
            )
            out.setdefault(fields, []).append((path, node.name))
    return out


def main() -> int:
    from codegen import bundle

    from compiled import compiled

    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    sets = field_sets(out.files)
    classes = sum(len(v) for v in sets.values())
    repeated = {k: v for k, v in sets.items() if len(v) > 1 and k}
    covered = sum(len(v) for v in repeated.values())
    print(f"classes {classes}")
    print(f"distinct field sets {len(sets)}")
    print(f"field sets written more than once {len(repeated)}")
    print(f"classes those cover {covered}")
    widest = sorted(repeated.items(), key=lambda kv: -len(kv[1]))[:8]
    for fields, where in widest:
        print(f"  {len(where):3d} classes  {{{', '.join(fields)}}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
