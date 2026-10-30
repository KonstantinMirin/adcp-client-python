#!/bin/bash
# Break every gate in `tests/test_the_comparison_census.py` on purpose, one at a time.
#
# That file is §8's comparison moved out from behind the suite's pole
# (`adcp-client-python-3be.23`), and the state it was written in is the one this script
# exists to make impossible to return to: the pin it replaces held 0 ENTRIES against a
# live 155 red pairs carrying 1,086 facts, with nothing red anywhere, because both of its
# readers sat behind `graded_reports()` -- 6-7 hours and twice killed by the kernel.  A
# gate that cannot redden is not a gate, and a gate nothing runs is the same thing by
# another route.
#
# So every case below must print REDDENS, and the first of them IS the found state: the
# pin emptied, which is what six rows of this epic were graded against.
#
# This is BANKED EVIDENCE and not a check: it is not collected by pytest, it is
# re-runnable, and `tests/test_the_comparison_census.py` is what the suite grades.
#
#   ./perturb_comparison_census.sh
#
# It edits the two files in place and restores them FROM A TEMPORARY COPY rather than with
# `git checkout --`, for `perturb_composed_description.sh`'s reason: that destroys
# uncommitted work in the files it touches, which makes it unusable at exactly the moment
# a gate is being written.  The copy is taken before the first edit and restored by a
# trap, so an interrupted run leaves the tree as it found it.
#
# A COLLECTION ERROR IS NOT A GREEN RUN.  The verdict matches "failed|error" because a
# perturbation that never ran prints no "failed", and a scraper reading that as green
# records a dead guard as a live one.
#
# Each case is one pass of the census (~50 s: 5 s to import the 919-module fresh tree and
# ~45 s to compare), so the whole script is about eight minutes.  That is the argument the
# row is about, measured from the other side: the same evidence over the pole would be a
# day.
set -u
cd "$(dirname "$0")" || exit 1

T=tests/test_the_comparison_census.py
C=tests/compared.py

BACKUP=$(mktemp -d)
trap 'cp "$BACKUP/test.py" "$T"; cp "$BACKUP/compared.py" "$C"; rm -rf "$BACKUP"' EXIT
cp "$T" "$BACKUP/test.py"
cp "$C" "$BACKUP/compared.py"

# PYTHONPATH carries BOTH roots: "." for codegen and "src" for adcp.  PYTHONPATH=. alone
# resolves adcp from an editable .pth naming whatever worktree installed it, which grades
# a mix of two trees -- see the bd memory on sibling worktrees, and `check`'s preamble.
py() { PYTHONPATH=.:src ./.venv/bin/python "$@"; }

run() {  # run <label> <-k expression selecting the test(s) it should redden>
  out=$(py -m pytest "$T" -q -p no:randomly -k "$2" 2>&1 | tail -3)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
  printf '%-62s %-12s %s\n' "$1" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*' | head -1)"
  cp "$BACKUP/test.py" "$T"
  cp "$BACKUP/compared.py" "$C"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

ONE="core/geo-place-requirement.json#"
FACT="missing /properties/systems/propertyNames"

# --------------------------------------------------------------------------- #
# THE PIN.  The state this row found, then one fact, one direction, one pair.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();i=s.index('COMPARISON_FACTS: dict[str, list[str]] = {');j=s.index('\n}\n',i);p.write_text(s[:i]+'COMPARISON_FACTS: dict[str, list[str]] = {'+s[j+1:])"
run "THE FOUND STATE: the pin emptied against the live 155" "census_is_the_set"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a=\"        '$FACT',\n\";assert s.count(a)>=1;p.write_text(s.replace(a,'',1))"
run "one fact dropped from one pair" "census_is_the_set"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a=\"        '$FACT',\n\";assert s.count(a)>=1;p.write_text(s.replace(a,\"        'added /properties/systems/propertyNames',\n\",1))"
run "one fact's DIRECTION flipped, missing -> added" "census_is_the_set"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a=\"    '$ONE': [\n        '$FACT',\n    ],\n\";assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "one whole red pair removed from the pin" "census_is_the_set"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='COMPARISON_FACTS: dict[str, list[str]] = {\n';assert s.count(a)==1;p.write_text(s.replace(a,a+\"    'core/pagination-request.json#': ['missing /nothing'],\n\"))"
run "a pair pinned red that the comparison passes" "census_is_the_set"

# --------------------------------------------------------------------------- #
# THE POPULATION.  A census over a set nobody named is a census over however many
# pairs there turned out to be, including none -- `tests/nodeset.py`'s whole subject.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$C');s=p.read_text();a='    return out\n';assert s.count(a)==1;p.write_text(s.replace(a,'    return out[:50]  # perturbed: the census ranges over a SLICE\n'))"
run "the pairing silently truncated to 50 pairs" "census_is_the_set or verdicts"

edit "import pathlib;p=pathlib.Path('$C');s=p.read_text();a='    pkg = fresh.schemas()\n    if pkg is None:\n        return []\n';assert s.count(a)==1;p.write_text(s.replace(a,'    pkg = fresh.schemas()\n    if pkg is not None:\n        return []\n'))"
run "no pair at all: every assertion over the set holds vacuously" "comparison_census"

# --------------------------------------------------------------------------- #
# THE `added` DIRECTION, which §2 forbids outright: the eight pairs and the reading
# that says none of them is a real narrowing.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a=\"    'core/mcp-webhook-payload.json#': (\";assert s.count(a)==1;i=s.index(a);j=s.index('    ),\n',i);p.write_text(s[:i]+s[j+7:])"
run "one of the eight narrowing pairs left unclassified" "real_narrowing"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='        conjoined = any(\n            isinstance(one, dict) and one.get(\"type\") == \"object\" for one in arm.get(\"allOf\") or []\n        )\n';assert s.count(a)==1;p.write_text(s.replace(a,'        conjoined = False  # perturbed: an arm stating it in a CONJUNCT is not read\n'))"
run "the arm-by-arm reading stops following a conjunct" "real_narrowing"

# The branch list READ, not the assertion over it: a reading pointed at the node's own
# (absent) ``oneOf`` is an empty list, and every per-branch assertion then holds zero
# times -- which is the shape ``nodeset.claimed`` exists to refuse.
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='    hoisted = node[\"allOf\"][0][\"allOf\"][0][\"oneOf\"]\n';assert s.count(a)==1;p.write_text(s.replace(a,'    hoisted = node.get(\"oneOf\") or []  # perturbed: the conjuncts are not followed\n'))"
run "the dropped conjunct's branches read off the wrong node" "real_narrowing"

# --------------------------------------------------------------------------- #
# THE PAIRS THE DOCUMENT CANNOT BE READ AT.  Not a pass, and not a population a
# fifth one may join quietly (`adcp-client-python-3be.15`).
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();i=s.index('UNREADABLE_PAIRS: dict[str, str] = {');j=s.index('\n}\n',i);p.write_text(s[:i]+'UNREADABLE_PAIRS: dict[str, str] = {'+s[j+1:])"
run "the unreadable pairs unpinned: a fifth joins silently" "cannot_be_read_at"

edit "import pathlib;p=pathlib.Path('$C');s=p.read_text();a='            unreadable[name] = f\"{type(e).__name__}: {e}\"[:200]\n            continue\n';assert s.count(a)==1;p.write_text(s.replace(a,'            continue\n'))"
run "an unreadable pair swallowed instead of recorded" "cannot_be_read_at"

# --------------------------------------------------------------------------- #
# THE VERDICTS THAT CARRY NO FACT.  §8's sixth outcome, a model whose schema cannot be
# built, and a pair whose document states nothing: all three have an empty
# added/missing/differs, so a census read off the facts alone calls them a pass.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$C');s=p.read_text();a='        if result.outcome != \"pass\":\n            verdicts[name] = result.outcome\n';assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "the non-pass verdicts stop being recorded at all" "verdicts or fact_carrying"

# INJECTED, because the live population has none: all three fact-less verdicts are at
# zero today, so the only way to show the gate can fire is to hand it one.  §8's sixth
# outcome is the one that matters most -- "a declaration that outlives its widening hides
# the next real gap at the same pointer" -- and it carries no fact, so the facts pin
# cannot see it.
edit "import pathlib;p=pathlib.Path('$C');s=p.read_text();a='        if result.outcome != \"pass\":\n';assert s.count(a)==1;p.write_text(s.replace(a,'        if name == \"core/pagination-request.json#\":\n            verdicts[name] = \"declaration_outlived_its_widening\"  # perturbed: injected\n        if result.outcome != \"pass\":\n'))"
run "one injected fact-less verdict: §8's sixth outcome" "fact_carrying or verdicts"
