"""Upstream's published WORDS, indexed by the structure they were published at -- §4's seam.

    PYTHONPATH=.:src python -m survey published_structures --revision 2954b258b

**WHY THIS EXISTS.**  ``codegen/lower/names.py``'s title rule needs no artifact: upstream's
spelling of a document ROOT is derivable from the bundle's own title, and the rule is graded
against their tree afterwards.  The positions that rule does NOT reach -- a union branch
leaf, an array element, a nested model, a nested enumeration -- were named by upstream's
generator from the FIELD PATH and numbered by traversal order (``Assets``, ``Assets9`` ...),
and ``adcp-client-python-zwqa`` measured that no rule reproduces those: the best available
one is wrong two times in three.  So the word is READ off the tree that published it, and
the key is structure (``codegen/structure.STRUCTURAL_IDENTITY``).

**THE INPUT IS A REVISION OF THIS REPOSITORY'S OWN HISTORY**, which is what makes the index
re-derivable rather than remembered: upstream's entire 9.6.1 emitted tree is at
``2954b258b:src/adcp/types/domains``.  Nothing is downloaded, nothing is installed, and the
revision this index was read from is written INTO it, so a reader can re-run the one command
and compare.

**NOTHING HERE DECIDES A BINDING.**  This writes upstream's side of the join only: each
published module, each word it declares, and that word's structural identity.  The join
itself is ``codegen.structure.bind``, run by the compiler, so the index cannot carry a
decision and cannot be edited into one -- an entry is a structure and a word, and a word
with no counterpart of ours simply finds nothing.
"""

from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
import tarfile
from io import BytesIO
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from codegen import structure  # noqa: E402

#: The path inside the revision that holds upstream's generated tree.  A module keys as
#: ``core/format`` -- ``codegen.emit.module_path``'s own spelling, hyphens already
#: underscores in both layouts -- which is what lets the run look an entry up by the module
#: it is writing, with no second reading of either tree's layout.
TREE = "src/adcp/types/domains"


def tree_of(revision: str, repo: Path) -> dict[str, str]:
    """``core.format`` -> that module's source text, out of ``revision``.

    ``git archive`` and not a worktree checkout: the revision is read without touching the
    working tree, so this command is safe to run from inside any lane's own checkout.
    """
    blob = subprocess.run(
        ["git", "archive", revision, TREE],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    out: dict[str, str] = {}
    with tarfile.open(fileobj=BytesIO(blob)) as archive:
        for member in archive.getmembers():
            if not member.name.endswith(".py"):
                continue
            handle = archive.extractfile(member)
            if handle is None:
                continue
            rel = member.name[len(TREE) + 1 : -len(".py")]
            if rel.endswith("__init__"):
                rel = rel[: -len("__init__")].rstrip("/")
            if not rel:
                continue
            out[rel] = handle.read().decode()
    return out


def describe(revision: str, repo: Path) -> str:
    """What ``revision`` resolves to, written into the index beside the structures."""
    return subprocess.run(
        ["git", "rev-parse", revision],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def index(revision: str, repo: Path) -> dict[str, Any]:
    """The whole index: the header that says what it was read from, and the structures."""
    sources = tree_of(revision, repo)
    modules = {
        module: {word: blob for word, blob in structure.from_source(text).items()}
        for module, text in sorted(sources.items())
    }
    kinds: collections.Counter[str] = collections.Counter(
        (blob or {}).get("kind", "none") for words in modules.values() for blob in words.values()
    )
    return {
        "revision": describe(revision, repo),
        "named": revision,
        "tree": TREE,
        "identity": structure.STRUCTURAL_IDENTITY,
        "modules_read": len(modules),
        "words_read": sum(len(w) for w in modules.values()),
        "by_kind": dict(sorted(kinds.items())),
        "modules": modules,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--revision",
        default="2954b258b",
        help=f"the revision of this repository whose {TREE} is upstream's published tree",
    )
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument(
        "--out",
        type=Path,
        default=structure.PUBLISHED,
        help="where the index is written; the compiler reads this path",
    )
    args = parser.parse_args()
    blob = index(args.revision, args.repo)
    args.out.write_text(json.dumps(blob, indent=1, sort_keys=True) + "\n")
    print(
        f"{blob['words_read']} published words in {blob['modules_read']} modules at "
        f"{blob['revision'][:9]} ({blob['named']}); by kind {blob['by_kind']} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
