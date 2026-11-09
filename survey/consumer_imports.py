"""Re-derive the consumer-import census, independently of any earlier run.

CORPUS (consumer-facing code, i.e. code upstream itself offers a reader as the
way to use the package): examples/, README.md, llms.txt, docs/**.md fences,
MIGRATION*.md fences, skills/**.

Every `import adcp...` is parsed with `ast`.  Each imported NAME is attributed
to the module that DEFINES it, read off the INSTALLED wheel (not the checkout),
because packaging is what decides what a consumer gets.

Run on an interpreter that has UPSTREAM `adcp` installed -- never the shared `.venv`,
which carries ours:

    uv venv /tmp/up && uv pip install --python /tmp/up/bin/python adcp
    /tmp/up/bin/python survey/consumer_imports.py <upstream checkout>

It writes `consumer-census.json` beside the working directory and prints the table the
README's first section quotes.
"""

from __future__ import annotations

import ast
import collections
import importlib
import importlib.metadata as md
import json
import pkgutil
import re
import sys
from pathlib import Path

RAISED: dict[tuple[str, str], str] = {}

FENCE = re.compile(r"```(?:python|py)\n(.*?)```", re.DOTALL)


def corpus(root: Path) -> list[tuple[str, str]]:
    """(label, python source) for every consumer-facing fragment."""
    out: list[tuple[str, str]] = []
    for p in sorted(root.glob("examples/**/*.py")):
        out.append((str(p.relative_to(root)), p.read_text(errors="replace")))
    for p in sorted(root.glob("skills/**/*.py")):
        out.append((str(p.relative_to(root)), p.read_text(errors="replace")))
    docs = (
        sorted(root.glob("README.md"))
        + sorted(root.glob("llms.txt"))
        + sorted(root.glob("MIGRATION*.md"))
        + sorted(root.glob("docs/**/*.md"))
        + sorted(root.glob("skills/**/*.md"))
    )
    for p in docs:
        text = p.read_text(errors="replace")
        for i, block in enumerate(FENCE.findall(text)):
            out.append((f"{p.relative_to(root)}#fence{i}", block))
    return out


def parse(label: str, src: str) -> list[tuple[str, str, str]]:
    """(module, name, label) for every adcp import.  name '' = module import."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "adcp" or a.name.startswith("adcp."):
                    found.append((a.name, "", label))
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level:  # relative import inside the checkout, not a consumer spelling
                continue
            if mod == "adcp" or mod.startswith("adcp."):
                for a in node.names:
                    if a.name == "*":
                        continue
                    found.append((mod, a.name, label))
    return found


def build_index() -> dict[int, str]:
    """id(object) -> shortest adcp module path that holds it."""
    import adcp

    index: dict[int, str] = {}
    mods = ["adcp"]
    for m in pkgutil.walk_packages(adcp.__path__, "adcp."):
        mods.append(m.name)
    for name in mods:
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        for v in vars(mod).values():
            try:
                key = id(v)
            except Exception:
                continue
            prev = index.get(key)
            if prev is None or len(name) < len(prev):
                index[key] = name
    return index


def defining_module(mod_name: str, name: str, index: dict[int, str]) -> str | None:
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return None
    if not name:
        return mod_name
    try:
        obj = getattr(mod, name)
    except Exception as exc:  # upstream's root __getattr__ raises ImportError for removed names
        RAISED[(mod_name, name)] = f"{type(exc).__name__}: {str(exc).splitlines()[0][:120]}"
        return None
    own = getattr(obj, "__module__", None)
    if isinstance(own, str) and (own == "adcp" or own.startswith("adcp.")):
        return own
    if isinstance(obj, type(sys)):  # a submodule
        return getattr(obj, "__name__", mod_name)
    hit = index.get(id(obj))
    if hit:
        return hit
    return mod_name  # declared only where it is imported from


def subpackage(defining: str | None) -> str:
    if defining is None:
        return "<unresolvable>"
    parts = defining.split(".")
    return parts[1] if len(parts) > 1 else "adcp (root)"


#: The verdict buckets a flat spelling can carry, and what each one means for the gate.
#:
#: `docs/plan/final-state.md` reading 10, amended 2026-11-06: **"the clause is graded over
#: what consumer code actually writes, not over the table's own rows"** -- "a table can be
#: complete against itself and leave the written import failing".  So this census is the
#: DENOMINATOR of the drop-in clause, and the three OWED buckets are the ones that must
#: resolve at `from adcp.types import <Name>`.
#:
#: The five refusals are each a reason a reader can act on, and the last two are about the
#: VERSION SKEW this census cannot wish away: the corpus on this box is upstream's 9.2.0
#: checkout and the alias surface is derived against 9.6.1, so a name 9.2.0's examples write
#: that 9.6.1 does not deliberately export is not a name we owe -- reading 10's "a name that
#: raises on upstream's own wheel is not a name we owe", read one version later.
FLAT_VERDICTS = {
    "PRESENT": "owed flat; ours carries the word at adcp.types.<domain>",
    "RELOCATED": "owed flat; ours carries the word at another module",
    "RENAMED": "owed flat; a name of ours holds the subject under another word",
    "MEANING-DIFFERS": "refused: we carry the word for a different subject",
    "ABSENT-SUBJECT-NO-WORD": "refused: identity equal under a word the bundle never gives",
    "ABSENT": "refused: no subject of ours; docs/migration-from-upstream.md owns it",
    "NOT-A-TYPE": "refused: upstream's object is a function, module or constant",
    "NOT-DELIBERATE-UPSTREAM": "refused: reachable on upstream only because a module declares no __all__",
    "NOT-ON-UPSTREAM": "refused: the corpus's version spells it and the target version does not",
}

#: The three of those that must resolve at the flat namespace.
FLAT_OWED = ("PRESENT", "RELOCATED", "RENAMED")


def flat_spellings(root: Path) -> dict[str, set[str]]:
    """Every `from adcp.types import <Name>` the consumer corpus writes -> the fragments.

    `corpus` is the one declaration of what consumer-facing code IS and is reused rather
    than restated, which is the whole reason this lives in this file: a second definition
    of the corpus is a second denominator for the drop-in clause.
    """
    out: dict[str, set[str]] = {}
    for label, src in corpus(root):
        for mod, name, where in parse(label, src):
            if mod == "adcp.types" and name:
                out.setdefault(name, set()).add(where)
    return out


def write_flat_table(
    out_path: Path,
    root: Path,
    verdicts: dict[str, dict],
    upstream: dict,
    corpus_version: str,
    target_version: str,
) -> None:
    """The committed census: one row per flat spelling, with the verdict that explains it.

    **COMMITTED, because a gate reading a path outside this repository is a dangling
    pointer** -- the lesson `survey/alias-surface-9.6.1.tsv` is already in the repository
    for. The corpus is upstream's own checkout and lives on whatever box derived this; the
    gate reads this file and needs neither the checkout nor an upstream wheel.

    **BOTH VERSIONS ARE IN THE HEADER AND ONE IS IN THE FILENAME.**  The corpus and the
    alias surface are not the same release, and a census that did not say so would be the
    error `adcp-client-python-2m5` corrected in itself.
    """
    found = flat_spellings(root)
    rows = []
    for name in sorted(found):
        got = verdicts.get(name)
        if got is not None:
            verdict = got["bucket"]
            why = got.get("why") or FLAT_VERDICTS[verdict]
        elif name not in upstream["names"]:
            verdict = "NOT-ON-UPSTREAM"
            why = f"not a public name of adcp {target_version} at all"
        elif not upstream["names"][name]["deliberate"]:
            verdict = "NOT-DELIBERATE-UPSTREAM"
            why = f"adcp {target_version} exposes it only where no __all__ is declared"
        else:
            raise SystemExit(
                f"{name} is on {target_version}'s deliberate surface, is written by "
                "consumer code, and the join gave it no verdict -- which is a gap in the "
                "derivation and not a row to invent"
            )
        if verdict not in FLAT_VERDICTS:
            raise SystemExit(f"{name}: {verdict} is not one of FLAT_VERDICTS")
        rows.append((name, len(found[name]), verdict, why, min(found[name])))
    fragments = len({f for s in found.values() for f in s})
    counted = "  ".join(f"{v}={sum(1 for r in rows if r[2] == v)}" for v in sorted(FLAT_VERDICTS))
    where = "examples/, skills/, README.md, llms.txt, MIGRATION*.md and docs/**.md fences"
    corpus_line = (
        f"# Corpus: upstream adcp {corpus_version}, {len(found)} names over "
        f"{fragments} fragments of {where}.\n"
    )
    lines = [
        "# Flat spellings consumer code writes: `from adcp.types import <Name>`.\n",
        corpus_line,
        f"# Verdicts joined against the alias surface derived for adcp {target_version}.\n",
        f"# {counted}\n",
        "name\tfragments\tverdict\twhy\tfirst_fragment\n",
    ]
    lines += [f"{n}\t{c}\t{v}\t{w}\t{f}\n" for n, c, v, w, f in rows]
    out_path.write_text("".join(lines))
    owed = sum(1 for r in rows if r[2] in FLAT_OWED)
    print(f"{len(rows)} flat spellings, {owed} owed at adcp.types -> {out_path}")


def main() -> None:
    if "--flat-table" in sys.argv:
        import argparse

        parser = argparse.ArgumentParser(description="the flat-spelling census")
        parser.add_argument("--flat-table", type=Path, required=True)
        parser.add_argument("--corpus", type=Path, required=True, help="upstream's own checkout")
        parser.add_argument("--corpus-version", required=True)
        parser.add_argument(
            "--verdicts",
            type=Path,
            required=True,
            help="survey/alias_surface.py --report's output: every name's bucket",
        )
        parser.add_argument("--upstream", type=Path, required=True, help="--dump-upstream's output")
        args = parser.parse_args(sys.argv[1:])
        report = json.loads(args.verdicts.read_text())
        up = json.loads(args.upstream.read_text())
        write_flat_table(
            args.flat_table,
            args.corpus,
            report["verdicts"],
            up,
            args.corpus_version,
            up["version"],
        )
        return
    root = Path(sys.argv[1])
    frags = corpus(root)
    rows: list[tuple[str, str, str]] = []
    for label, src in frags:
        rows.extend(parse(label, src))

    index = build_index()

    names: dict[str, set[str]] = collections.defaultdict(set)  # name -> modules spelled
    sites = collections.Counter()  # module -> import sites
    unresolvable: list[tuple[str, str]] = []
    for mod, name, _label in rows:
        sites[mod] += 1
        if name:
            names[name].add(mod)

    # attribute each DISTINCT name once, by the module it is most often spelled at
    by_sub: collections.Counter[str] = collections.Counter()
    attribution: dict[str, str] = {}
    for name, mods in names.items():
        defining = None
        for m in sorted(mods):
            defining = defining_module(m, name, index)
            if defining:
                break
        if defining is None:
            unresolvable.append((name, sorted(mods)[0]))
        sub = subpackage(defining)
        by_sub[sub] += 1
        attribution[name] = f"{defining or '<unresolvable>'}"

    total = len(names)
    print(f"corpus fragments: {len(frags)}")
    print(f"  python files   : {sum(1 for l, _ in frags if l.endswith('.py'))}")
    print(f"  doc fences     : {sum(1 for l, _ in frags if '#fence' in l)}")
    print(f"import statements parsed: {len(rows)}")
    print(f"DISTINCT NAMES: {total}   DISTINCT MODULES SPELLED: {len(sites)}")
    print()
    print("distinct names by DEFINING subpackage:")
    for sub, n in by_sub.most_common():
        print(f"  {sub:22s} {n:5d}  ({100.0*n/total:.1f}%)")
    print()
    print("modules by import SITES:")
    for mod, n in sites.most_common(8):
        print(f"  {mod:34s} {n:5d}")
    print()
    print(f"unresolvable against the installed wheel: {len(unresolvable)}")
    for name, mod in sorted(unresolvable)[:20]:
        print(f"  {mod}.{name}")
    print()
    print(f"names that RAISE on upstream's own wheel: {len(RAISED)}")
    for (m, n), err in sorted(RAISED.items()):
        print(f"  {m}.{n} -> {err}")

    # top-level subpackages / modules a consumer reaches at all
    reached_tops = sorted({m.split(".")[1] for m in sites if m != "adcp" and "." in m})
    print()
    print(f"top-level adcp children a consumer SPELLS in an import path: {len(reached_tops)}")
    print("  " + ", ".join(reached_tops))
    defining_tops = sorted(by_sub)
    print(f"top-level adcp children that DEFINE an imported name: {len(defining_tops)}")
    print("  " + ", ".join(defining_tops))

    Path("consumer-census.json").write_text(
        json.dumps(
            {
                "upstream_version": md.version("adcp"),
                "fragments": len(frags),
                "statements": len(rows),
                "distinct_names": total,
                "distinct_modules": len(sites),
                "by_subpackage": dict(by_sub),
                "sites": dict(sites),
                "attribution": attribution,
                "unresolvable": unresolvable,
                "raised": {f"{m}.{n}": e for (m, n), e in RAISED.items()},
                "reached_tops": reached_tops,
                "defining_tops": defining_tops,
            },
            indent=1,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
