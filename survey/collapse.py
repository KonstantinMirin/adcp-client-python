"""Words upstream keeps APART that our surface answers with ONE object, and which are defects.

    PYTHONPATH=.:src ./.venv/bin/python -m survey collapse --wheel <their site-packages>

**THE OBVIOUS TEST IS WRONG, AND THAT IS THE WHOLE POINT OF THIS MODULE.**  "Two of
upstream's words resolve to one object of ours" is not a defect -- it is the design.  They
emit a class per POSITION and we emit one per SUBJECT (architecture §3a), so a subject
reached from ten positions carries ten of their names and one of ours, and the N:1 table
exists to bind all ten.  Measured over upstream's 853 flat class words: 37 of our objects
answer for several of their distinct classes, and declaring those 37 defects would condemn
the relation the project is built on.

**WHAT SEPARATES A COLLAPSE FROM A DEFECT IS THE FIELD SET.**  Two of their classes that
state the SAME properties are one subject wearing two words; two that state DIFFERENT
properties are two subjects, and answering both with one object hands a caller a type whose
fields are not the ones it asked for.  So the reading is the overlap, and it sorts the 37
into three bands rather than two:

* **identical field sets** -- one subject, several positions.  The design, no action.
* **nested or near-identical** -- almost always ours carrying the document's FULL statement
  where upstream split a deprecated property into a ``Legacy*`` variant.  ``LegacyProduct``
  has 60 fields and ``Product`` 59, and ours has 60: ``core/product.json`` STATES
  ``format_ids`` with ``deprecated: true``, and CLAUDE.md's rule is that "deprecated is
  metadata, not absence" -- a class that suppressed it would be narrower than its document.
  Ours is right and the collapse is right.
* **disjoint, or nearly** -- the defect.  ``BuildCreativeCreative`` states 7 properties and
  ``ListCreativesCreative`` 28 with NOTHING shared, and one object of ours answers for both.

**AND THE FLAT SURFACE IS NOT THE WHOLE QUESTION.**  The defect that prompted this module
is in ``adcp.types.capabilities``, where ``Features`` (10 fields, media_buy) and
``SignalsFeatures`` (1 field, signals) are two objects of upstream's and one of ours -- and
it does NOT appear in a census of the flat namespace, because the flat surface resolves
those words elsewhere.  ``--module`` runs the same reading over one of upstream's own module
paths, which is where their machinery actually imports from.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import subprocess
import sys

#: How much overlap still reads as "one subject".  A pair differing by ONE property out of
#: thirty is the ``Legacy*`` shape above; a pair sharing nothing is two subjects.  The
#: threshold is reported with every row so a reader can move it rather than trust it.
NESTED = 0.75

_DUMP = """
import json, importlib
mod = importlib.import_module({module!r})
out = {{}}
for word in dir(mod):
    if word.startswith("_"):
        continue
    try:
        found = getattr(mod, word)
    except Exception:
        continue
    if isinstance(found, type):
        out[word] = {{
            "target": found.__module__ + "." + found.__qualname__,
            "fields": sorted(getattr(found, "model_fields", {{}}) or {{}}),
        }}
print(json.dumps(out))
"""


def theirs(wheel: pathlib.Path, module: str) -> dict[str, dict]:
    """Upstream's words for ``module``, read in THEIR interpreter.

    A subprocess and not an import: both packages are named ``adcp``, so one process cannot
    hold the two.  The wheel's own ``bin/python`` is the interpreter that can see it.
    """
    python = wheel.parent.parent.parent / "bin" / "python"
    if not python.exists():  # a site-packages path given directly
        python = pathlib.Path("/tmp/upwheel/bin/python")
    # **PYTHONPATH MUST NOT REACH THEIR INTERPRETER.**  The caller runs with
    # ``PYTHONPATH=.:src`` so that OUR tree is importable, and a subprocess inherits it --
    # so upstream's own python imported OUR ``adcp`` from ``src`` and this module compared
    # the tree to itself, reporting "4123 of upstream's 4123 words resolve here" and zero
    # collapses.  Both packages are named ``adcp``; which one an interpreter sees is
    # decided by the environment, so the environment is stated here rather than inherited.
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
    done = subprocess.run(
        [str(python), "-c", _DUMP.format(module=module)],
        capture_output=True,
        text=True,
        env=env,
    )
    if done.returncode != 0:
        raise SystemExit(f"could not read upstream's {module}:\n{done.stderr[-600:]}")
    return json.loads(done.stdout)


def bands(
    their_words: dict[str, dict], module: str
) -> tuple[list, list, list, int]:
    """``(design, nested, defects, words we bind)`` for one module."""
    import importlib

    mine = importlib.import_module(module)
    ours: dict[str, type] = {}
    for word in their_words:
        try:
            found = getattr(mine, word)
        except Exception:
            continue
        if isinstance(found, type):
            ours[word] = found

    by_object: dict[int, list[str]] = collections.defaultdict(list)
    for word, found in ours.items():
        by_object[id(found)].append(word)

    design: list = []
    nested: list = []
    defects: list = []
    for words in by_object.values():
        if len(words) < 2:
            continue
        if len({their_words[w]["target"] for w in words}) < 2:
            continue  # one class of theirs under several words: nothing collapsed
        sets = {w: frozenset(their_words[w]["fields"]) for w in words}
        distinct = set(sets.values())
        row = (sorted(words), ours[words[0]], sets)
        if len(distinct) == 1:
            design.append(row)
            continue
        widest = max(distinct, key=len)
        narrowest = min(distinct, key=len)
        overlap = len(widest & narrowest) / len(widest) if widest else 1.0
        (nested if overlap >= NESTED else defects).append((*row, overlap))
    return design, nested, defects, len(ours)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--wheel", required=True, help="upstream's installed site-packages")
    parser.add_argument(
        "--module",
        action="append",
        default=None,
        help="an upstream module path to read (repeatable); default adcp.types",
    )
    ns = parser.parse_args(argv)
    sys.path.insert(0, "src")

    total_defects = 0
    for module in ns.module or ["adcp.types"]:
        their_words = theirs(pathlib.Path(ns.wheel), module)
        design, nested, defects, bound = bands(their_words, module)
        print(f"\n== {module}")
        print(f"   {bound} of upstream's {len(their_words)} class words resolve here")
        print(f"   {len(design):4d}  identical field sets -- one subject, several positions")
        print(
            f"   {len(nested):4d}  nested (>= {NESTED:.0%} shared) -- ours carries the"
            " fuller statement"
        )
        print(f"   {len(defects):4d}  DISJOINT -- two subjects answered by one object")
        total_defects += len(defects)
        for words, cls, sets, overlap in sorted(defects, key=lambda r: r[3]):
            mine = len(getattr(cls, "model_fields", {}) or {})
            print(f"\n   {overlap:.0%} shared -> {getattr(cls, '__name__', cls)} ({mine} fields)")
            for word in words:
                target = their_words[word]["target"]
                print(f"        {word:46s} {len(sets[word]):3d} fields   {target}")
    read = len(ns.module or ["adcp.types"])
    print(f"\n{total_defects} disjoint collapse(s) over {read} module(s)")
    return 1 if total_defects else 0


if __name__ == "__main__":
    raise SystemExit(main())
