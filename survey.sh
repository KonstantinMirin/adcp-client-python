#!/bin/sh
# A shell preamble, not a python shebang: the interpreter must be the project's own
# .venv and PYTHONPATH must carry BOTH roots -- "." for codegen and survey, "src" for
# adcp. Same reason as ./check, measured the same way.
"""true" 2>/dev/null
exec env PYTHONPATH=.:src "$(dirname "$0")/.venv/bin/python" "$0" "$@"
"""
"""THE INDEX OF EVERY INSTRUMENT, so a question is answered by CALLING one rather than
by writing a script.

**Why this exists.**  Eighteen instruments were written and then not found again.  The
union census was built, measured the bucket sizes this project quoted by hand for days,
and sat unmerged on a branch while a row was filed to BUILD it.  A tool nobody can
enumerate is a tool nobody uses, and the cost is paid every time in a fresh throwaway
script whose predicate is subtly different from the last one's -- which is how four
figures came to be wrong in a single session.

::

    ./survey.sh                      every instrument, what it answers, what it needs
    ./survey.sh unions               run one, with its own arguments
    ./survey.sh unions --help        its arguments

**THE LIST IS GLOBBED AND NEVER WRITTEN DOWN.**  A hand-maintained index goes stale on
the first new instrument, which is the failure this file exists to end -- so the set is
the filesystem's answer and the one-line purpose is read from each module's own
docstring.  An instrument that drops its docstring loses its description and says so,
rather than silently reading as having none.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

#: Directories holding instruments. A directory and not a list of files, for the reason
#: in the module docstring.
WHERE = ("survey", "tools/parity")


def _purpose(path: Path) -> str:
    """The first line of the module docstring, or the sentence saying there is none."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover -- an unreadable file is a real answer
        return f"(unreadable: {exc.strerror})"
    mark = text.find('"""')
    if mark < 0:
        return "(no docstring -- this instrument does not say what it answers)"
    body = text[mark + 3 :]
    end = body.find('"""')
    first = (body[:end] if end >= 0 else body).strip().splitlines()
    return first[0].strip() if first and first[0].strip() else "(docstring opens empty)"


def _needs(path: Path) -> str:
    """What a caller must supply, read off the module's own argparse calls."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    wanted = [flag for flag in ("--bundle", "--tree", "--wheel", "--tsv", "--check")
              if f'"{flag}"' in text or f"'{flag}'" in text]
    return " ".join(wanted)


def instruments() -> dict[str, Path]:
    """Every runnable instrument, keyed on the short name a caller types."""
    found: dict[str, Path] = {}
    for where in WHERE:
        for path in sorted((ROOT / where).glob("*.py")):
            if path.name.startswith("_"):
                continue
            if "__main__" not in path.read_text(encoding="utf-8", errors="replace"):
                continue
            # the short name drops a trailing _census/_collisions/_surface noise word
            # only where that leaves something unambiguous; otherwise the stem stands.
            stem = path.stem
            short = stem.rsplit("_", 1)[0] if stem.endswith(("_census", "_collisions")) else stem
            found[short if short not in found else stem] = path
    return found


def main(argv: list[str]) -> int:
    found = instruments()
    if not argv or argv[0] in ("-h", "--help", "list"):
        print(f"{len(found)} instruments. Call one rather than writing a script.\n")
        width = max(len(k) for k in found)
        for name, path in sorted(found.items()):
            needs = _needs(path)
            print(f"  {name:<{width}}  {_purpose(path)[:84]}")
            print(f"  {'':<{width}}  {path.relative_to(ROOT)}"
                  + (f"   needs: {needs}" if needs else ""))
        print("\n  ./survey.sh <name> [args]      run one")
        print("  ./survey.sh <name> --help     its arguments")
        print("\nAnd ./check is the fast loop: the three emission numbers in under a second.")
        return 0

    name, rest = argv[0], argv[1:]
    if name not in found:
        close = [k for k in found if name in k or k in name]
        print(f"no instrument named {name!r}", file=sys.stderr)
        if close:
            print(f"did you mean: {', '.join(sorted(close))}", file=sys.stderr)
        print("run ./survey.sh with no arguments for the list", file=sys.stderr)
        return 2

    env = dict(os.environ, PYTHONPATH=f"{ROOT}:{ROOT / 'src'}")
    return subprocess.call([sys.executable, str(found[name]), *rest], env=env, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
