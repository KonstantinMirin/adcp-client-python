"""THE NODE-KEYED ALIASES, and the clause that decides how many are owed.

``survey/probes/`` carries a committed node-keyed map from ``(upstream module, name)`` to a
declaration of ours, built by ``survey/dropin_blocking.py``'s own four rules: upstream's
defining module names the DOCUMENT, our declarations compiled from that document are the
candidates, **identity is a GATE on that candidate set and never the proposal**, and a row
no rule resolves is left UNRESOLVED.  ``adcp-client-python-qma6`` asks for those rows to
stop being a PROBE fact and become a TREE fact — alias statements with their migration
entries, by the same rule ``survey/mechanical_aliases.py`` applies to the 1:1 bucket.

**AND THE COUNT THAT IS OWED IS SMALLER THAN THE MAP, WHICH IS READING 10 CORRECTING THE
BEAD RATHER THAN THE BEAD BEING APPROXIMATED.**  ``docs/plan/final-state.md`` reading 10:

    **THE TARGET IS A NAME AT A CANONICAL MODULE, NEVER A SPELLING.**  Upstream's wheel
    exposes one name at several modules, and most of its public modules declare no
    ``__all__`` at all — so the set of spellings is several times the set of names.
    *Reproducing spellings would put one object at several export paths and break reading 6
    outright.*

    **AND THE SET THIS READING RANGES OVER IS THE DELIBERATE SURFACE.**  A name reachable
    only because a module forgot to declare what it exports is not a name an application
    was invited to import, and *treating it as one makes upstream's omission our
    obligation.*  Where the two sets differ, say so and state which one a figure is over —
    the undisciplined count is the larger and the less meaningful.

The map is keyed at ``adcp.types.domains.<document>`` — their GENERATED LAYOUT, which is a
spelling and not a name, and which no ``__all__`` of theirs declares.  Those spellings are
already served in the tree, by a RULE and not a table (``adcp.types._dropin``, on the
drop-in branch).  What the ALIAS LAYER owes is the FLAT word, and the deliberate flat
surface is ``adcp/types/__init__.py``'s own ``__all__`` — the list upstream wrote by hand.
So this instrument states both figures and never one: the map's name count, and the subset
that is on their declared flat surface.

**A WORD TWO ROWS DISAGREE ABOUT GETS NO ALIAS**, which is ``adcp-client-python-r482``'s
rule and reading 10's own: "a name resolves to a DIFFERENT class of ours depending on which
upstream module the import came from, so one flat alias cannot serve both."  One flat
namespace cannot hold two meanings for one word, so such a word is reported and takes a
migration note — never an arbitrary pick.

**AND THE PAIR IS THE UNIT.**  "An alias whose entry is missing is a reading 10 FAILURE and
not partial credit."  This instrument writes both halves from one row and cannot write one
without the other, and a row whose word is MINTED from the structure rather than titled by
the bundle is recorded ``PROVISIONAL`` in ``compat.__adcp_provisional__`` with the node it
is minted at — the same rule, read off the same ``alias_surface.bundle_index``.

Run::

    PYTHONPATH=.:src ./.venv/bin/python survey/node_keyed_aliases.py --report
    PYTHONPATH=.:src ./.venv/bin/python survey/node_keyed_aliases.py --write
"""

from __future__ import annotations

import argparse
import ast
import collections
import importlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import mechanical_aliases as mech  # noqa: E402  -- the pair writer, reused and not copied

#: The committed node-keyed map.  Built by ``survey/probes/build_map.py``; the file is the
#: artefact and this instrument never rebuilds it, so a figure here is over the same rows a
#: reader can open.
MAP = HERE / "probes" / "probe_map.json"

#: Upstream's own hand-written flat ``__all__``, which is the DELIBERATE surface reading 10
#: ranges over.  Read as TEXT from their 9.6.1 ``adcp/types/__init__.py``, because importing
#: it would import their generated tree, and read as an AST literal rather than by regex.
SURFACE = HERE / "upstream-flat-surface-9.6.1.txt"

#: Words upstream's OWN flat surface resolves to a class their HAND-WRITTEN layer declares,
#: read off their `_eager.py` -- the module their `adcp/types/__init__.py` resolves every flat
#: `__getattr__` through, so it is the authority for what a flat word means on their wheel.
#: Reading 10: "AND WHERE UPSTREAM'S NAME MEANS A DIFFERENT SET OF VALUES, AN ALIAS IS A DEFECT
#: AND NOT A BRIDGE ... An alias there hands a caller something that silently is not what it
#: asked for, which is worse than an import error.  That name takes a migration note naming
#: both sets."  Proved per element on the leading case: their `canonical_creative.Format`
#: requires [format_kind, params] and `core/format.json` requires [format_id, name] -- no
#: shared required element, so disjoint on its face.  **MEASURED COST OF NOT HAVING THIS
#: GUARD: the first write claimed `Format`, and `from adcp.types import Format` then handed
#: back our generated class where upstream means their boundary record -- 148 of their
#: behavioural tests, and a silent substitution rather than an import error.**
HAND_WRITTEN = HERE / "upstream-hand-written-words-9.6.1.tsv"

SECTION = "## §11. The node-keyed aliases, on upstream's declared flat surface"
FENCE = "<!-- GENERATED by survey/node_keyed_aliases.py -- do not edit between the fences -->"
END = "<!-- END GENERATED -->"


def deliberate_surface() -> list[str]:
    """Upstream's declared flat names, one per line, as committed."""
    return [line.strip() for line in SURFACE.read_text(encoding="utf-8").split() if line.strip()]


def hand_written() -> dict[str, str]:
    """``word -> their declaring module``, for every word their hand-written layer owns."""
    out = {}
    for line in HAND_WRITTEN.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or line.startswith("word\t") or not line.strip():
            continue
        word, _, module = line.partition("\t")
        out[word] = module
    return out


def hand_written_from_source(path: Path) -> dict[str, str]:
    """Read it off upstream's own ``_eager.py``, for refreshing the committed table.

    A word bound from ``_generated``, ``domains.**``, ``aliases`` or ``_forward_compat`` names
    a GENERATED class and the alias is owed.  ``_forward_compat`` is on the generated side
    because it re-exports the generated class after patching it rather than declaring one.  A
    word bound from any OTHER module of theirs names a class their hand-written layer declares.
    """
    generated = (
        "adcp.types._generated",
        "adcp.types.domains",
        "adcp.types.aliases",
        "adcp.types._forward_compat",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("adcp.types"):
            if any(node.module == g or node.module.startswith(g + ".") for g in generated):
                continue
            for alias in node.names:
                word = alias.asname or alias.name
                if not word.startswith("_"):
                    out[word] = node.module
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            value = node.value
            if isinstance(target, ast.Name) and isinstance(value, ast.Attribute):
                root = value
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name) and root.id.startswith("_canonical"):
                    out[target.id] = "adcp.types.canonical_creative"
    return {w: m for w, m in out.items() if w[:1].isupper()}


def surface_from_source(path: Path) -> list[str]:
    """``__all__`` read off upstream's own ``adcp/types/__init__.py``, for refreshing the file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", None) == "__all__" for t in node.targets
        ):
            return [e.value for e in node.value.elts if isinstance(e, ast.Constant)]
    raise SystemExit(f"no __all__ in {path}")


def decide() -> dict[str, object]:
    """One verdict per upstream NAME, over the deliberate surface, and never a pick."""
    import alias_surface

    rows = json.loads(MAP.read_text(encoding="utf-8"))
    titles = alias_surface.bundle_index(mech.BUNDLE)["titles"]
    surface = mech.public_surface()
    bound = mech.already_bound()
    declared = set(deliberate_surface())
    theirs = hand_written()

    targets: dict[str, set[tuple[str, str]]] = collections.defaultdict(set)
    spellings: dict[str, set[str]] = collections.defaultdict(set)
    for key, row in rows.items():
        their_module, _, name = key.rpartition(":")
        targets[name].add((row[0], row[1]))
        spellings[name].add(their_module)

    pairs: list[dict[str, str]] = []
    disagree: dict[str, list[str]] = {}
    present: list[str] = []
    needs_export: list[dict[str, str]] = []
    unresolvable: list[dict[str, str]] = []
    off_surface = sorted(set(targets) - declared)

    withheld_hand_written: dict[str, str] = {}
    for name in sorted(set(targets) & declared):
        if name in theirs:
            withheld_hand_written[name] = theirs[name]
            continue
        if len(targets[name]) > 1:
            disagree[name] = sorted(f"{m}.{w}" for m, w in targets[name])
            continue
        module, word = next(iter(targets[name]))
        try:
            obj = getattr(importlib.import_module(module), word)
        except Exception as error:  # noqa: BLE001 -- recorded, never swallowed
            unresolvable.append({"name": name, "target": f"{module}.{word}",
                                 "why": f"{type(error).__name__}: {error}"})
            continue
        paths = surface.get(id(obj))
        if not paths:
            needs_export.append({"name": name, "target": f"{module}.{word}",
                                 "why": "reaches no adcp.types.<domain> export"})
            continue
        if name in bound:
            present.append(name)
            continue
        record = getattr(obj, "__adcp_schema__", None)
        node = (record.document + record.pointer) if record is not None else ""
        pairs.append(
            {
                "name": name,
                "ours": sorted(paths)[0],
                "word": word,
                "declared_at": f"{module}.{word}",
                "spellings": " ".join(sorted(spellings[name])),
                "node": node,
                "verdict": "TITLED" if word.lower() in titles else "PROVISIONAL",
            }
        )
    return {
        "map_rows": len(rows),
        "map_names": len(targets),
        "deliberate_surface": len(declared),
        "on_surface": len(set(targets) & declared),
        "off_surface": off_surface,
        "pairs": pairs,
        "their_hand_written_layer_owns_the_word": withheld_hand_written,
        "name_resolves_to_two_of_ours": disagree,
        "already_resolves_flat": present,
        "target_owes_an_export": needs_export,
        "target_does_not_resolve": unresolvable,
    }


def guide_section(report: dict[str, object]) -> str:
    pairs: list[dict[str, str]] = report["pairs"]  # type: ignore[assignment]
    provisional = [p for p in pairs if p["verdict"] == "PROVISIONAL"]
    titled = [p for p in pairs if p["verdict"] == "TITLED"]
    head = f"""{SECTION}

**Every row below is a PAIR, and the pair is the unit** — `docs/plan/final-state.md` reading
10: "an alias whose entry is missing is a reading 10 FAILURE and not partial credit."

**WHAT DECIDED THE TARGET IS THE DOCUMENT NODE, WITH IDENTITY AS A GATE.** Upstream's
defining module names the document; our declarations compiled from *that document* are the
candidates; the class's identity — the field set read by wire alias, or the enum's value
list — is a **gate on that candidate set and never the proposal**, because the error-envelope
field set is shared by forty classes of ours and identity alone over the whole tree "matches"
everything. A name no rule resolved is left out and reported, never minted
(`survey/probes/build_map.py`, `survey/dropin_blocking.py`).

**AND THE COUNT IS OVER THE DELIBERATE SURFACE, WHICH IS THE LARGER FIGURE CORRECTED.** The
map carries **{report["map_rows"]} rows over {report["map_names"]} distinct names**, keyed at
`adcp.types.domains.<document>` — upstream's *generated layout*, which reading 10 calls a
spelling and not a name, and which no `__all__` of theirs declares. Upstream's own
hand-written flat `__all__` holds **{report["deliberate_surface"]}** names, and
**{report["on_surface"]}** of the map's names are on it. The other
**{len(report["off_surface"])}** are reachable only through their generated layout: reading
10 is explicit that "a name reachable only because a module forgot to declare what it exports
is not a name an application was invited to import, and treating it as one makes upstream's
omission our obligation." Those spellings are served in the tree by a RULE and not a table,
and they get no flat word here.

**{len(pairs)} pairs written**, {len(titled)} plain and {len(provisional)} PROVISIONAL. The
difference is whose word *ours* is: where the bundle **titles** our word the row is plain;
where it titles nothing at that node our word is derived from the parent and the key, so the
alias *records* upstream's commitment and the row says PROVISIONAL. The upstream ask is the
same sentence for every provisional row and is stated once: **give the node at that pointer a
`title`.**

| upstream's word | our surface name | the node the document states it at | status |
|---|---|---|---|
"""
    body = "".join(
        f"| `{p['name']}` | `{p['ours']}` | `{p['node'] or '—'}` | {p['verdict']} |\n"
        for p in pairs
    )
    tail = f"""
**WHAT IS WITHHELD, AND WHY — counted, not omitted.**

* **{len(report["name_resolves_to_two_of_ours"])} words on their declared surface reach two
  different declarations of ours** depending on which module of theirs the import came from.
  Reading 10: "a name resolves to a *different* class of ours depending on which upstream
  module the import came from, so one flat alias cannot serve both." These take a migration
  note and no alias (`adcp-client-python-r482`).
* **{len(report["their_hand_written_layer_owns_the_word"])} words are THEIRS, declared by a
  hand-written module of theirs and not by their generated tree** — read off their own
  `_eager.py`, which is what their `adcp/types/__init__.py` resolves every flat `__getattr__`
  through. Reading 10: "where upstream's name means a different set of values, an alias is a
  DEFECT and not a bridge ... that name takes a migration note naming both sets." Their
  `canonical_creative.Format` requires `[format_kind, params]`; `core/format.json` requires
  `[format_id, name]`; **no shared required element, so disjoint on its face.** Measured cost
  of writing them anyway: `from adcp.types import Format` handed back our generated class and
  148 of their behavioural tests failed on a silent substitution.
* **{len(report["already_resolves_flat"])} already resolve flat** and owe nothing.
* **{len(report["target_owes_an_export"])} targets reach no `adcp.types.<domain>` export.**
  §4's own remedy applies and it is not this layer's: "an EXPORT or a NAME, never a split.
  The alias layer cannot reach a private name."
* **{len(report["target_does_not_resolve"])} targets do not resolve at all**, which is a
  defect of the map and is reported rather than skipped.

Re-derivable with `survey/node_keyed_aliases.py --report`, which prints each by name.
"""
    return head + body + tail


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--refresh-surface", type=Path,
                        help="upstream's own adcp/types/__init__.py, to rewrite the committed list")
    parser.add_argument("--refresh-hand-written", type=Path,
                        help="upstream's own adcp/types/_eager.py, to rewrite the withheld table")
    args = parser.parse_args()

    if args.refresh_hand_written:
        found = hand_written_from_source(args.refresh_hand_written)
        head = HAND_WRITTEN.read_text(encoding="utf-8").split("word\t")[0]
        HAND_WRITTEN.write_text(
            head + "word\ttheir declaring module\n"
            + "".join(f"{w}\t{m}\n" for w, m in sorted(found.items())),
            encoding="utf-8",
        )
        print(f"{HAND_WRITTEN.name}: {len(found)} words their hand-written layer owns")
        return

    if args.refresh_surface:
        names = surface_from_source(args.refresh_surface)
        SURFACE.write_text("\n".join(sorted(names)) + "\n", encoding="utf-8")
        print(f"{SURFACE.name}: {len(names)} declared flat names")
        return

    report = decide()
    pairs: list[dict[str, str]] = report["pairs"]  # type: ignore[assignment]
    print(f"map rows                       {report['map_rows']}")
    print(f"map distinct NAMES             {report['map_names']}")
    print(f"upstream's declared flat names  {report['deliberate_surface']}")
    print(f"  of the map's names, ON it    {report['on_surface']}")
    print(f"  off it (a spelling, not a name) {len(report['off_surface'])}")
    print(f"PAIRS to write                 {len(pairs)}")
    print(f"  TITLED                       {sum(1 for p in pairs if p['verdict'] == 'TITLED')}")
    print(f"  PROVISIONAL                  {sum(1 for p in pairs if p['verdict'] == 'PROVISIONAL')}")
    print(f"already resolves flat          {len(report['already_resolves_flat'])}")
    print(f"name -> two of ours            {len(report['name_resolves_to_two_of_ours'])}")
    print(f"target owes an export          {len(report['target_owes_an_export'])}")
    print(f"target does not resolve        {len(report['target_does_not_resolve'])}")
    print(f"their hand-written layer owns it {len(report['their_hand_written_layer_owns_the_word'])}")
    if args.json:
        args.json.write_text(json.dumps(report, indent=1, default=str))
    if args.report:
        for name, where in sorted(report["their_hand_written_layer_owns_the_word"].items()):  # type: ignore[union-attr]
            print(f"  THEIRS      {name}: declared by {where}, a migration note and no alias")
        for name, where in sorted(report["name_resolves_to_two_of_ours"].items()):  # type: ignore[union-attr]
            print(f"  TWO-OF-OURS {name}: {' | '.join(where)}")
        for row in report["target_owes_an_export"]:  # type: ignore[union-attr]
            print(f"  OWES-EXPORT {row['name']} -> {row['target']}")
        for row in report["target_does_not_resolve"]:  # type: ignore[union-attr]
            print(f"  UNRESOLVED  {row['name']} -> {row['target']}: {row['why']}")
    if not args.write:
        return

    mech.write_pairs(pairs, SECTION, FENCE, END, guide_section(report))
    print(f"compat.py and the guide's §11 written with {len(pairs)} pairs")


if __name__ == "__main__":
    main()
