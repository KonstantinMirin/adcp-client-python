"""**A PUBLISHED NAME THAT DISAPPEARED WITHOUT A ROW IS RED.**

A consumer ports off upstream `adcp` by spelling the names their application already
imports.  Every one of those names either resolves on this package's surface or owes the
consumer a sentence saying what to write instead -- and the failure mode this file exists
to stop is the third case, which has happened: a name vanished, nothing failed, and the
consumer got an `AttributeError` with nothing to grep for.  `verdicts/missing-names.md`
is the report of fifteen such names, found by hand; `verdicts/name-mapping.md` is the
verdict for the 113 that upstream's own code imports.

**THE POPULATION IS DERIVED, AND THERE IS NO LIST OF NAMES IN THIS FILE.**  That is the
whole design, for a measured reason recorded in `verdicts/missing-names.md`:
`survey/alias-surface-9.6.1.tsv` is a COMMITTED table whose header states a population of
7,118 names while the file carries 3,300 rows, and **11 of the 15 names that exercise
found are not in it** -- so a gate written over the committed table would have passed
while saying nothing about the names it exists for.  This gate reads what upstream
PUBLISHES instead, so it catches the 114th name when a bundle or an upstream pin moves,
with nobody editing a list.

**The surface it reads, and why it is the deliberate one.**  `docs/plan/final-state.md`
reading 10: "THE SET THIS READING RANGES OVER IS THE DELIBERATE SURFACE.  A name reachable
only because a module forgot to declare what it exports is not a name an application was
invited to import."  Upstream's deliberate surface is the hand-written `__all__` of
`src/adcp/types/__init__.py` and `src/adcp/__init__.py` -- 1,197 names between them at the
pinned rev -- and it is read by AST out of GIT, at the rev
`survey/upstream-machinery-9.6.1.tsv` records, because this branch REPLACED that tree and
the two cannot share an interpreter (`survey/alias_surface.py`'s three-phase note).
`tests_emit/test_prose_resolves.py` reads upstream the same way, for the same reason.

**And resolution is asked of the NAME, not of each of upstream's spellings.**  Reading 10:
"THE TARGET IS A NAME AT A CANONICAL MODULE, NEVER A SPELLING.  Reproducing spellings
would put one object at several export paths and break reading 6 outright."  So a name
counts as served when `adcp.types` or `adcp` answers for it, whichever upstream module it
was published at.

**What a migration entry has to carry.**  A mention is not an entry.
:func:`noted_with_a_reason` counts a name only where the guide gives it a REASON -- either
its own, in the last cell of the guide's three-column row, or its SECTION'S, where the
section opens with a ruling and then lists the names it rules on.  The second is the
guide's own design and not a relaxation: §1 states one ruling for 360 machinery names and
a per-name rule would demand that paragraph be copied 360 times.  A name listed under a
section that states nothing is a casualty list and not a row a consumer can act on, and
:func:`test_the_rule_rejects_a_mention_with_no_reason` perturbs the harvester on exactly
that difference.

**NO ALLOWLIST, AND THE GATE IS RED TODAY.**  Measured on this tree: of the 1,197
published names, 211 do not resolve and 146 of those have no entry in
`docs/migration-from-upstream.md`.  Those 146 are the work list -- 63 of them are rows of
`verdicts/name-mapping.md` and the rest are names nothing of upstream's own code imports
but a consumer still may.  An allowlist of names here would be the very artifact this gate
replaces, so there is none: the number falls as aliases and entries land.

**AND A RUN WITHOUT THE INSTRUMENT RAISES RATHER THAN SKIPS** (`docs/plan/final-state.md`:
a gate that disappears with its own instrument reports green).  If the recorded rev is
missing from this repository, or the blobs do not parse, or the derived surface is
implausibly small, this file fails with that as the message.
"""

from __future__ import annotations

import ast
import functools
import importlib
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: The committed record of WHICH upstream this tree was read against.  Its first line is
#: `# survey/upstream_machinery.py over upstream <rev>`, and `test_prose_resolves.py`
#: reads the rev off the same header.  A pin moves here and the population moves with it.
MACHINERY_TABLE = ROOT / "survey" / "upstream-machinery-9.6.1.tsv"

#: The two modules whose `__all__` upstream wrote BY HAND, which is what makes them the
#: deliberate surface rather than whatever a generated module happens to bind.
PUBLISHING_MODULES = ("src/adcp/types/__init__.py", "src/adcp/__init__.py")

#: Where ours answers.  A name is served when either module resolves it.
SERVING_MODULES = ("adcp.types", "adcp")

GUIDE = ROOT / "docs" / "migration-from-upstream.md"

#: Below this the derivation is broken rather than the surface small -- upstream's two
#: `__all__` lists carry 1,197 names at the pinned rev.
FLOOR = 800


def recorded_rev() -> str:
    """The upstream rev this tree records itself as read against.  Raises if absent."""
    if not MACHINERY_TABLE.exists():
        raise RuntimeError(f"the instrument is missing: {MACHINERY_TABLE} does not exist")
    header = MACHINERY_TABLE.read_text().splitlines()[0]
    if "over upstream " not in header:
        raise RuntimeError(f"{MACHINERY_TABLE} states no upstream rev: {header!r}")
    return header.rsplit(" ", 1)[1].strip()


def _blob(path: str, rev: str) -> str:
    """Upstream's own file at ``rev``, out of git.  Raises if the rev or path is gone."""
    done = subprocess.run(
        ["git", "cat-file", "-p", f"{rev}:{path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        raise RuntimeError(
            f"cannot read {path} at upstream rev {rev}: {done.stderr.strip()} -- "
            "this gate ranges over upstream's published surface and cannot run without it"
        )
    return done.stdout


def _declared_all(source: str) -> list[str]:
    """Every name in a module's ``__all__``, by AST, including `+=` extensions.

    Upstream's `types/__init__.py` builds its list in several statements, so a reading
    that took the first assignment would silently range over part of the surface.
    """
    out: list[str] = []
    for node in ast.walk(ast.parse(source)):
        target = None
        if isinstance(node, ast.Assign) and node.targets:
            target = node.targets[0]
        elif isinstance(node, ast.AugAssign):
            target = node.target
        if target is None or getattr(target, "id", None) != "__all__":
            continue
        try:
            out += [str(name) for name in ast.literal_eval(node.value)]
        except (ValueError, TypeError):  # a comprehension or a name; not a stated list
            continue
    return out


@functools.cache
def published_surface() -> frozenset[str]:
    """Upstream's DELIBERATE public names at the recorded rev.  Derived, never listed."""
    rev = recorded_rev()
    names: set[str] = set()
    for path in PUBLISHING_MODULES:
        found = _declared_all(_blob(path, rev))
        if not found:
            raise RuntimeError(f"{path} at {rev} declares no __all__ this reading can see")
        names |= set(found)
    if len(names) < FLOOR:
        raise RuntimeError(
            f"derived surface is {len(names)} names, under the floor of {FLOOR}: "
            "the derivation is broken, and a broken derivation must not report green"
        )
    return frozenset(names)


@functools.cache
def _serving() -> tuple[object, ...]:
    return tuple(importlib.import_module(name) for name in SERVING_MODULES)


def resolves(name: str) -> bool:
    """Does OUR surface answer for ``name`` at any canonical module?"""
    for module in _serving():
        try:
            getattr(module, name)
        except Exception:  # noqa: BLE001 -- an attribute that raises is not an answer
            continue
        return True
    return False


#: A backticked dotted path or bare word in the guide's prose.
_TICKED = re.compile(r"`([A-Za-z_][\w.]*)`")


#: A section whose own prose is thinner than this states no reason, so the names under it
#: are mentions and not entries.  Every section of the guide today opens with its ruling.
RULING = 200


def noted_with_a_reason(text: str) -> dict[str, str]:
    """Every name the guide gives a REASON for, name -> the reason it gives.

    **THE REASON MAY BE THE SECTION'S, AND THAT IS THE GUIDE'S OWN DESIGN.**  §1 states one
    ruling for 360 machinery names ("There is no replacement for any of them here and
    there will not be: none is stated by a bundle document") and then lists them, grouped,
    one bullet per defining module.  A rule demanding a per-name sentence would demand that
    paragraph be copied 360 times, so a name counts when it appears under a section whose
    PROSE states a reason -- and a section that lists names and says nothing contributes
    nothing, which is what :func:`test_the_rule_rejects_a_mention_with_no_reason` perturbs.

    Where the guide DOES give a per-name reason -- its own table shape, "the name, as
    consumer code spells it | what upstream's wheel does | what this package has" -- that
    cell is recorded as the reason instead, so a reader of this dict sees which kind each
    entry carries.

    **The REPLACEMENT column is not harvested.**  Its names are OURS, and recording them
    would let a sentence about `adcp.types.core.MediaBuy` silently answer for an upstream
    name that merely shares the word.  A name is keyed by its last dotted segment as well
    as its full spelling, because a consumer's spelling is `adcp.types.CoreMediaBuy` and
    upstream published `CoreMediaBuy`.
    """
    noted: dict[str, str] = {}

    def record(token: str, reason: str) -> None:
        for key in {token, token.rsplit(".", 1)[-1]}:
            noted.setdefault(key, reason)

    def cells_of(line: str) -> list[str] | None:
        if not line.startswith("|"):
            return None
        return [cell.strip() for cell in line.strip("|").split("|")]

    sections: list[tuple[str, list[str]]] = [("(preamble)", [])]
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        else:
            sections[-1][1].append(line)

    for heading, lines in sections:
        prose = 0
        for line in lines:
            if cells_of(line) is not None or line.startswith(("-", "*", "#", "<!--")):
                continue
            prose += len(_TICKED.sub("", line))
        if prose < RULING:
            continue
        reason_of_section = f"§ {heading}"
        for line in lines:
            cells = cells_of(line)
            if cells is not None:
                if len(cells) >= 3 and len(cells[-1]) >= 12:
                    reason, searched = cells[-1], cells[:-1]
                else:
                    reason, searched = reason_of_section, cells
                for cell in searched:
                    for token in _TICKED.findall(cell):
                        record(token, reason)
                continue
            for token in _TICKED.findall(line):
                record(token, reason_of_section)
    return noted


def unserved() -> dict[str, str]:
    """Published name -> why it is unserved, for every name that is neither."""
    if not GUIDE.exists():
        raise RuntimeError(f"the guide is missing: {GUIDE}")
    noted = noted_with_a_reason(GUIDE.read_text())
    out: dict[str, str] = {}
    for name in sorted(published_surface()):
        if resolves(name):
            continue
        if name in noted:
            continue
        out[name] = "resolves nowhere on our surface and has no entry in the guide"
    return out


def test_the_population_is_derived_from_upstreams_own_publication() -> None:
    """The instrument, graded before the rule it feeds, so a silent derivation fails here.

    Reading the surface is the only thing this file does that can go wrong QUIETLY: an
    empty population makes the rule below vacuous and green.
    """
    rev = recorded_rev()
    assert re.fullmatch(r"[0-9a-f]{7,40}", rev), rev
    surface = published_surface()
    assert len(surface) >= FLOOR, len(surface)
    # Both publishing modules contribute, and neither is the whole surface.
    types_all = set(_declared_all(_blob(PUBLISHING_MODULES[0], rev)))
    package_all = set(_declared_all(_blob(PUBLISHING_MODULES[1], rev)))
    assert types_all - package_all, "the type surface contributes nothing"
    assert package_all - types_all, "the package surface contributes nothing"
    assert surface == types_all | package_all


def test_every_published_name_resolves_or_is_noted() -> None:
    """**Every name upstream published either resolves here or has a reason in the guide.**

    No allowlist: a name admitted here by spelling would be the committed list this gate
    exists to replace.  The message is the work list, grouped so it is readable at the
    size it currently has.
    """
    missing = unserved()
    if not missing:
        return
    surface = published_surface()
    sample = sorted(missing)
    lines = [
        f"{len(missing)} of upstream's {len(surface)} published names resolve nowhere on "
        "our surface AND have no entry in docs/migration-from-upstream.md.",
        "Each owes either an alias (one subject, two spellings) or an entry saying what "
        "to write instead -- see verdicts/name-mapping.md for the 113 that upstream's own "
        "code imports.",
        *(f"  {name}" for name in sample),
    ]
    pytest.fail("\n".join(lines))


#: A ruling paragraph, long enough to pass :data:`RULING`, for the perturbations below.
_RULING_PROSE = (
    "These names have no replacement in this package and there will not be one: not one of "
    "them is stated by a document of the pinned bundle, so there is nothing here to derive "
    "a type from, and upstream's own wheel still carries every one of them unchanged at the "
    "module named beside it. Keep upstream's wheel if your application is built on them."
)


def test_the_rule_rejects_a_mention_with_no_reason() -> None:
    """Perturbed: the harvester must not accept a name the guide merely NAMES.

    A rule nothing can break is a finding about the rule.  Four cases: the guide's two
    shapes, the one that shipped as a near-miss (a bullet list of casualties under no
    ruling), and the replacement column, which must NOT answer for an upstream name.
    """
    ruled = f"## §9. The names\n\n{_RULING_PROSE}\n\n"

    row = (
        "| `adcp.types.Gone` | `AttributeError` | **`adcp.types.core.Here`**, from "
        "`core/here.json`, because the document titles it that way |"
    )
    per_name = noted_with_a_reason(ruled + row)
    assert "Gone" in per_name, "a table row with its own reason cell is an entry"
    assert per_name["Gone"].startswith("**`adcp.types.core.Here`**")
    assert "Here" not in per_name, "the replacement column must not answer for a name"

    bullet = "- `adcp.module` — `Gone` · `AlsoGone`"
    under_ruling = noted_with_a_reason(ruled + bullet)
    assert {"Gone", "AlsoGone"} <= set(under_ruling), "a bullet under a ruling is an entry"
    assert under_ruling["Gone"] == "§ §9. The names"

    # The near-miss: the same bullet under a section that states nothing.
    assert noted_with_a_reason("## §9. The names\n\n" + bullet) == {}
    assert noted_with_a_reason(bullet) == {}

    # And a section whose prose is a sentence fragment rather than a ruling.
    thin = "## §9. The names\n\nGone, and the rest.\n\n" + bullet
    assert noted_with_a_reason(thin) == {}


def test_a_missing_instrument_raises_rather_than_skipping(monkeypatch: pytest.MonkeyPatch) -> None:
    """A gate that disappears with its own instrument reports green, so this one raises."""
    monkeypatch.setattr(
        sys.modules[__name__], "MACHINERY_TABLE", ROOT / "survey" / "no-such-table.tsv"
    )
    with pytest.raises(RuntimeError, match="the instrument is missing"):
        recorded_rev()

    monkeypatch.undo()
    with pytest.raises(RuntimeError, match="cannot read"):
        _blob("src/adcp/types/__init__.py", "0" * 40)
