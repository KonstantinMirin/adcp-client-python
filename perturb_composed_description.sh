#!/bin/bash
# Break every gate on `harness._described_by_the_conjunct` on purpose, one at a time.
#
# That reading decides WHICH of two composed views states the `description` at a pointer
# (`docs/plan/rebuild-plan.md` §6, "a composed base's loses to the document's own").  It
# replaced a gap-fill whose answer was right at 277 of the 282 sites where two views
# disagree, so its correctness is almost entirely its SCOPE: a gate that widens by one
# case re-grades a description the document does state at its own pointer, and the
# symptom is a FALSE GREEN -- the re-graded text is whatever the model happens to say.
# A gate that cannot redden is not a gate.
#
# This is BANKED EVIDENCE and not a check: it is not collected by pytest, it is
# re-runnable, and `tests/test_comparison_document_side.py` is what the suite grades.
# Every case below names what it breaks and must print REDDENS.
#
#   ./perturb_composed_description.sh
#
# It edits the two files in place and restores them FROM A TEMPORARY COPY rather than
# with `git checkout --`, which is where this departs from
# `perturb_dump_exemptions.sh`: that script destroys uncommitted work in the files it
# touches and so refuses to run on a dirty tree, which makes it unusable at exactly the
# moment a gate is being written.  The copy is taken before the first edit and restored
# by a trap, so an interrupted run leaves the tree as it found it.
#
# A COLLECTION ERROR IS NOT A GREEN RUN.  The verdict matches "failed|error" for the
# reason `perturb_dump_exemptions.sh` gives at length: a perturbation that never ran
# prints no "failed", and a scraper reading that as green records a dead guard as a live
# one.
set -u
cd "$(dirname "$0")" || exit 1

H=codegen/harness.py
T=tests/test_comparison_document_side.py

BACKUP=$(mktemp -d)
trap 'cp "$BACKUP/harness.py" "$H"; cp "$BACKUP/test.py" "$T"; rm -rf "$BACKUP"' EXIT
cp "$H" "$BACKUP/harness.py"
cp "$T" "$BACKUP/test.py"

# Invoked directly rather than through `eval`: the perturbations are Python one-liners
# full of quotes and newlines, and `eval` re-splits them.
py() { PYTHONPATH=.:src CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync python "$@"; }

run() {  # run <label> <-k expression selecting the test(s) it should redden>
  out=$(py -m pytest "$T" -q -k "$2" 2>&1 | tail -3)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
  printf '%-58s %-12s %s\n' "$1" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*' | head -1)"
  cp "$BACKUP/harness.py" "$H"
  cp "$BACKUP/test.py" "$T"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

# --------------------------------------------------------------------------- #
# the GATES, one per case
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    if \"description\" not in conjunct:\n        return node\n';assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "a narrowing conjunct's SILENCE deletes the base's text" "conjunct_silent"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    if not _inside(_vocabulary(conjunct), _vocabulary(node)):';assert s.count(a)==1;p.write_text(s.replace(a,'    if not _inside(_vocabulary(node), _vocabulary(conjunct)):'))"
run "the direction reversed: the WIDER view takes the text" "node_is_narrower or narrowing_declaration"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    return all(_in_vocabulary(m, outer) for m in inner) and any(\n        not _in_vocabulary(m, inner) for m in outer\n    )';assert s.count(a)==1;p.write_text(s.replace(a,'    return all(_in_vocabulary(m, outer) for m in inner)'))"
run "strictness dropped: two EQUAL sets read as a narrowing" "same_set_reordered"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    return all(_in_vocabulary(m, outer) for m in inner) and any(';assert s.count(a)==1;p.write_text(s.replace(a,'    return any(_in_vocabulary(m, outer) for m in inner) and any('))"
run "containment weakened to OVERLAP" "overlapping or disjoint"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    return all(_in_vocabulary(m, outer) for m in inner) and any(\n        not _in_vocabulary(m, inner) for m in outer\n    )';assert s.count(a)==1;p.write_text(s.replace(a,'    return len(inner) < len(outer) and all(_in_vocabulary(m, outer) for m in inner)'))"
run "strictness by LENGTH, which a duplicate member fools" "duplicate_member"

# The DISJOINT row survives the overlap weakening above, because `any` is false for two
# sets with no member in common -- so the gate that holds it is the containment test
# EXISTING at all, and it needs a case of its own.  An empty intersection is a document
# that admits nothing, which is the emitter's refusal to make (§2), so the pair must
# report rather than be regraded under either view's description.
edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    return all(_in_vocabulary(m, outer) for m in inner) and any(\n        not _in_vocabulary(m, inner) for m in outer\n    )';assert s.count(a)==1;p.write_text(s.replace(a,'    return True  # perturbed: any two stated vocabularies count as a narrowing'))"
run "the containment test removed: DISJOINT sets regrade" "disjoint"

# And the two rows where NEITHER view states a vocabulary -- a narrowing bound, and a
# node with no value set at all -- are held by the None guard rather than by the
# containment test, so that guard is its own case.  The axis this reading is about is
# the VOCABULARY: a bound both views state has 0 sites with a disagreeing description,
# and an arm for it would be a derivation matching nothing.
edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    if inner is None or outer is None:\n        return False\n';assert s.count(a)==1;p.write_text(s.replace(a,'    if inner is None or outer is None:\n        return True  # perturbed\n'))"
run "the vocabulary axis dropped: a BOUND regrades too" "bound_narrows or no_vocabulary"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    if \"const\" in view:\n        return [view[\"const\"]]\n';assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "a const is not read as a one-member vocabulary" "const_INSIDE"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    return {k: v for k, v in node.items() if k != \"description\"}';assert s.count(a)==1;p.write_text(s.replace(a,'    return {k: v for k, v in node.items() if k not in (\"description\", \"default\")}'))"
run "widened to 'default', a derivation with no site" "default_two_views"

# --------------------------------------------------------------------------- #
# the WIRING.  Everything above grades the reading; this grades that `_composed`
# reaches it.  Not hypothetical: a reading written and never called is the shape every
# one of the cases above still passes.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='        out = _described_by_the_conjunct(out, c)\n';assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "_composed stops calling the reading at all" "narrowing_declaration or WIDER_descriptions"

# The POSITIVE side of the scope table: a predicate that answered 'node' to everything
# would pass all eight rows of OUTSIDE_THE_SCOPE, so the row that must redden when the
# reading stops firing is asserted too.
edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='def _described_by_the_conjunct(node: dict, conjunct: dict) -> dict:';assert s.count(a)==1;p.write_text(s.replace(a,'def _described_by_the_conjunct(node: dict, conjunct: dict) -> dict:\n    return node  # perturbed: the reading never fires'))"
run "the reading answers 'node' to everything" "not_vacuous or narrowing_declaration"
