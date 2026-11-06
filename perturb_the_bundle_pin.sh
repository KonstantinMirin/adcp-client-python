#!/bin/bash
# Break the bundle-pin gate on purpose, one BUNDLE edit at a time.
#
# `tests/test_a_bundle_states_which_upstream_it_is.py` compares a committed record
# against a directory that nothing in a normal week touches -- which is exactly the
# gate that passes because nothing happened. This file is the evidence that it does
# not: every case below edits `schemas/cache/3.2` or `schemas/cache/3.3` and must
# print REDDENS, and the two cases that must print STAYED GREEN are measurements
# about what the digest deliberately does not range over.
#
# The perturbations are BUNDLE perturbations and never record perturbations, except
# where a case says so: a gate proved by editing the thing it reads out of is proved
# of nothing. Nothing under `codegen/` or `src/` moves, so `./check`'s three numbers
# are untouched throughout.
#
# This is BANKED EVIDENCE and not a check: it is not collected by pytest, it is
# re-runnable, and the test file is what the suite grades.
#
#   ./perturb_the_bundle_pin.sh
#
# It edits committed files in place and restores them with `git checkout --`, so it
# REQUIRES A CLEAN BUNDLE: uncommitted work under `schemas/` is destroyed. It refuses
# to run otherwise.
#
# A COLLECTION ERROR IS NOT A GREEN RUN, and INTERNALERROR IS A THIRD SHAPE -- the
# verdict matches "failed|error|INTERNALERROR" for the reason `perturb_the_wheel.sh`
# measured: a run that never executed prints no "N failed" line at all, and a scraper
# keyed on "failed" alone records that as a guard that cannot redden.
set -u
cd "$(dirname "$0")" || exit 1

T=tests/test_a_bundle_states_which_upstream_it_is.py

if [ -n "$(git status --porcelain -- schemas tests/provenance.py "$T")" ]; then
  echo "refusing to run: schemas/ or the gate has uncommitted changes, which this would destroy" >&2
  exit 1
fi

py() { CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync python "$@"; }

# `-n 0`: thirteen tests over 2,766 files is 0.8 s in one process, and one worker is
# the only way the verdict names one run.
run() {  # run <label> <-k expression selecting the test it should redden>
  out=$(py -m pytest "$T" -q -n 0 -p no:randomly -k "$2" 2>&1 | tail -4)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)|INTERNALERROR"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
  printf '%-58s %-12s %s\n' "$1" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*|INTERNALERROR.*' | head -1)"
  git checkout -- schemas "$T" 2>/dev/null
  git clean -qfd schemas 2>/dev/null
}

echo "=== ONE DOCUMENT, ONE BYTE: the case the whole gate exists for ==="

# A `description` that gained a word. Not a deletion and not a reformat -- the edit a
# hand makes while reading, which is the one a reviewer of a 1,625-document diff
# misses. Both bundles, because the goal's claim is about 3.3 as much as 3.2 and a
# gate wired to one directory says nothing about the other.
py -c "import pathlib;p=pathlib.Path('schemas/cache/3.2/core/assets/url-asset.json');s=p.read_text();assert '\"type\"' in s;p.write_text(s.replace('\"type\"','\"type\" ',1))"
run "3.2: one byte added to one of 1,625 documents" "digest_states_the_bundle"

py -c "import pathlib;p=pathlib.Path('schemas/cache/3.3/core/assets/url-asset.json');s=p.read_text();assert '\"type\"' in s;p.write_text(s.replace('\"type\"','\"type\" ',1))"
run "3.3: one byte added to one of 1,141 documents" "digest_states_the_bundle"

echo
echo "=== A DOCUMENT THAT LEAVES, AND ONE THAT MOVES ==="

# A deletion moves the count as well as the digest, so both tests are asked -- the
# count is the figure every cost reading here is divided by.
py -c "import pathlib;pathlib.Path('schemas/cache/3.2/core/assets/url-asset.json').unlink()"
run "3.2: one document deleted (digest)" "digest_states_the_bundle"
py -c "import pathlib;pathlib.Path('schemas/cache/3.2/core/assets/url-asset.json').unlink()"
run "3.2: one document deleted (count)" "counts_the_documents"

# THE CASE A CONTENT-ONLY DIGEST MISSES. Same bytes, same count, new path: every
# `$ref` that names the old path now resolves to nothing, and a digest that folded
# contents without their names would call this no change.
py -c "import pathlib;p=pathlib.Path('schemas/cache/3.2/core/assets/url-asset.json');p.rename(p.with_name('url-asset-renamed.json'))"
run "3.2: one document renamed, bytes and count unchanged" "digest_states_the_bundle"

echo
echo "=== A RE-COPY THAT PRESERVES MEANING, which MUST redden here ==="

# Appending the trailing newline `json.dumps` omitted changes no value any validator
# reads -- and `adcp-client-python-lzzj.8` measured that 854 of the 22,338 published-
# vs-patched differences were exactly this byte. The accepts corpus is keyed on what a
# document ADMITS precisely so this costs nothing there. Here it must cost: the 90
# approximated facts in 57 documents were measured over THESE bytes, so a reformat is
# an event that asks for a re-measurement rather than one to be absorbed.
py -c "
import pathlib
for p in sorted(pathlib.Path('schemas/cache/3.2').rglob('*.json'))[:50]:
    b=p.read_bytes()
    if not b.endswith(b'\n'): p.write_bytes(b+b'\n')
"
run "3.2: 50 documents gain the trailing newline" "digest_states_the_bundle"

echo
echo "=== A FILE THAT IS NOT A DOCUMENT ==="

# `codegen.bundle.portable` compiles `bundle.rglob(\"*.json\")`, so a `.json` dropped
# into the bundle root becomes a document; anything else becomes a note nobody reads.
# The digest ranges over every regular FILE so that both arrivals redden, and the
# second has its own named test so the message says which happened.
py -c "import pathlib;pathlib.Path('schemas/cache/3.2/NOTES.txt').write_text('a note\n')"
run "3.2: a non-document file appears in the bundle (digest)" "digest_states_the_bundle"
py -c "import pathlib;pathlib.Path('schemas/cache/3.2/NOTES.txt').write_text('a note\n')"
run "3.2: a non-document file appears in the bundle (named)" "nothing_but_json"

echo
echo "=== A BUNDLE WITH NO RECORD, which is the state this row was filed about ==="

# The pre-row state, reproduced: a directory under `schemas/cache/` that nothing names.
py -c "import pathlib,shutil;shutil.move('schemas/cache/3.3.provenance.json','/tmp/adcp-pin-perturb-record.json')"
out=$(py -m pytest "$T" -q -n 0 -p no:randomly -k "has_a_record_beside_it" 2>&1 | tail -4)
if echo "$out" | grep -qE "[0-9]+ (failed|error)|INTERNALERROR"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
printf '%-58s %-12s %s\n' "3.3: the record removed, the bundle kept" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*|INTERNALERROR.*' | head -1)"
py -c "import shutil;shutil.move('/tmp/adcp-pin-perturb-record.json','schemas/cache/3.3.provenance.json')"

# A THIRD bundle copied in with no record. The population is discovered rather than
# listed for this case alone, so it is the one that proves the discovery.
py -c "import pathlib;d=pathlib.Path('schemas/cache/3.4');d.mkdir();(d/'core').mkdir();(d/'core'/'x.json').write_text('{}')"
run "a third bundle copied in with no record at all" "has_a_record_beside_it"

echo
echo "=== AND AN EXCEPTION THAT STOPS NAMING ANYTHING ==="

# The records except 5 documents from the byte-reproduction claim because a
# `--release` build stamps wall-clock time into them. An exception that names no
# document reads as a known limitation and is a stale note -- the rot
# `codegen/patch.py` already refuses in its exclusions.
py -c "import pathlib;p=pathlib.Path('schemas/cache/3.3/manifest.json');p.rename(p.with_name('manifest-moved.json'))"
run "3.3: an excepted document is no longer in the bundle" "excepted_from_the_reproduction"

echo
echo "=== STAYED GREEN, AND SAID SO ==="

# TWO measurements about what the digest does not range over, each correct:
#
# The record's PROSE is not digested. Rewriting `vendor_transform` cannot redden a
# gate whose subject is the bundle, and that is the right division -- the prose is
# read by a person and the digest by the gate. It is stated here so a reader does not
# mistake a green run for "the record was verified in full": nothing mechanical checks
# that `build_command` is the command that ran. The evidence for THAT is the measured
# reproduction counts, which live in `reproduction` and in the lane's verdict file.
py -c "import json,pathlib;p=pathlib.Path('schemas/cache/3.3.provenance.json');d=json.loads(p.read_text());d['vendor_transform']='a sentence that is no longer true';p.write_text(json.dumps(d,indent=2)+'\n')"
out=$(py -m pytest "$T" -q -n 0 -p no:randomly -k "digest_states_the_bundle or names_a_commit" 2>&1 | tail -4)
if echo "$out" | grep -qE "[0-9]+ (failed|error)|INTERNALERROR"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
printf '%-58s %-12s %s\n' "  NOT GRADED: the record's prose rewritten" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*|INTERNALERROR.*' | head -1)"
git checkout -- schemas

# And a `patches/` set edited: the OVERLAY moves, the published bundle does not. The
# patched bundle a run reads is a different directory (`codegen.patch.for_build`
# writes it into the cache), and `codegen.patch._patch_set_digest` is what keys on
# these files. A gate that reddened here would be grading the wrong artifact.
py -c "import pathlib;p=pathlib.Path('patches/8735/manifest.json');s=p.read_text();p.write_text(s.replace('\"additions\"','\"additions\" ',1))"
out=$(py -m pytest "$T" -q -n 0 -p no:randomly -k "digest_states_the_bundle" 2>&1 | tail -4)
if echo "$out" | grep -qE "[0-9]+ (failed|error)|INTERNALERROR"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
printf '%-58s %-12s %s\n' "  NOT GRADED: a patch set edited, the bundle untouched" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*|INTERNALERROR.*' | head -1)"
git checkout -- patches

git checkout -- schemas patches "$T" 2>/dev/null
git clean -qfd schemas 2>/dev/null

echo
echo "EVERY LINE MUST PRINT REDDENS EXCEPT THE TWO MARKED 'NOT GRADED', and each of"
echo "those two is a division of labour rather than a gap: the prose is for a reader,"
echo "and a patch set is keyed by codegen.patch._patch_set_digest and not by this gate."
echo
echo "TREE AFTER THIS RUN (must be empty):"
git status --porcelain -- schemas patches "$T"
