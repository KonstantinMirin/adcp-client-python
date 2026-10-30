#!/bin/bash
# Break the held accepts corpus on purpose, one way at a time, and watch it redden.
#
# `tests/corpus.py` holds the instances the accepts check drew, keyed by
# `harness.corpus_key`, so the suite stops re-drawing the same payloads from the same
# pinned documents on every run. That is a cache in front of the one check that PROVES a
# widening rather than believing it (`docs/plan/rebuild-plan.md` section 8), and
# `pyproject.toml`'s own invariant says what that costs: "A faster suite that grades
# something else would not be faster." So the question this script answers is the only
# one that matters about it -- can a wrong corpus pass?
#
# Three of the cases are the ones the rows were asked to demonstrate by name:
#
#   * A STALE KEY. A RAW BUNDLE document moves by one byte; the key moves with it; the
#     held instance is still on disk and is NOT used. The pair draws and grades.
#   * A MISSING ENTRY. The entry is deleted; the pair draws and grades. A miss costs and
#     never passes on nothing.
#   * OUR OWN INLINING MOVES AND THE KEY DOES NOT. The packaged record is what
#     `bundle.record` renders, so a change to how we inline moves its bytes while no
#     document has moved. Keyed on the record that redrew the inlining share of the
#     bundle for nothing; keyed on the document's own bytes it is a hit, and
#     `corpus_defect` re-offers the held instance to the moved record on the way in.
#
# None of those reddens, and that is the correct answer for all three: a miss is work,
# not a defect, and a hit under an unchanged document is the point. What MUST redden is
# a held entry that cannot stand in, and the three shapes of that are the rest of the
# cases.
#
#   ./perturb_accepts_corpus.sh
#
# This is BANKED EVIDENCE and not a check: pytest does not collect it, and
# `tests/test_accepts_corpus.py` is what the suite grades. It edits tracked files and a
# packaged record in place and restores them with `git checkout --`, so it REQUIRES A
# CLEAN TREE and refuses to run otherwise.
#
# A COLLECTION ERROR IS NOT A GREEN RUN. The verdict below matches "failed|error" for
# that reason: a malformed perturbation never runs, prints no "failed", and a scraper
# reading that as green scores a dead guard as a live one.
set -u
cd "$(dirname "$0")" || exit 1

H=codegen/harness.py
C=tests/corpus.py
R=src/adcp/types/_schemas/core/pagination-request.json
D=schemas/cache/3.2/core/pagination-request.json
B=codegen/bundle.py
E=tests/test_emit.py
PAIR='core/pagination-request.json#'

if [ -n "$(git status --porcelain -- "$H" "$C" "$B" "$E" "$R" "$D")" ]; then
  echo "refusing to run: one of $H $C $B $E $R $D has uncommitted changes, which this would destroy" >&2
  exit 1
fi

py() { PYTHONPATH=.:src .venv/bin/python "$@"; }

# A SCRATCH corpus, because the real one is shared by every worktree on this box and the
# cases below empty and delete entries. `ADCP_CACHE` moves BOTH caches, so the COMPILE
# cache is linked back in: this script perturbs the corpus, and paying a cold compile per
# case would cost minutes per invocation for nothing.
SCRATCH=$(mktemp -d /tmp/perturb-accepts.XXXXXX) || exit 1
trap 'rm -rf "$SCRATCH"' EXIT
ln -s "$(py -c 'import sys; sys.path.insert(0, "tests"); import compiled; print(compiled.STORE)')" \
   "$SCRATCH/emit-cache"
export ADCP_CACHE=$SCRATCH
STORE=$SCRATCH/accepts-corpus

one() {  # one <label> <expected verdict: REDDENS|GREEN>
  out=$(py -m pytest tests/test_emit.py -q -p no:randomly -n0 \
          -k "test_every_class_passes_all_three_checks and pagination-request" 2>&1 | tail -4)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)"; then verdict=REDDENS; else verdict=GREEN; fi
  if [ "$verdict" = "$2" ]; then mark="as designed"; else mark="*** UNEXPECTED ***"; fi
  printf '%-52s %-9s %-18s %s\n' "$1" "$verdict" "$mark" \
    "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*' | head -1)"
}

key() {  # the key the live pair asks for, printed by the harness's own function
  py - <<'PY'
import sys
sys.path.insert(0, "tests")
import test_emit as te
from adcp.types._base import SchemaRef
from codegen import harness
g = next(x for x in te.graded() if x.ref == SchemaRef("core/pagination-request.json", "#"))
pair = te.pair_of(g)
print(harness.corpus_key(pair.identity, examples=1, custom_formats=te.FORMAT_STRATEGIES))
PY
}

held() { echo "$STORE/${1:0:2}/$1.json"; }

echo "the pair: $PAIR"
rm -rf "$STORE"

# ------------------------------------------------------------------ the baseline
one "cold, no corpus at all" GREEN
K=$(key)
echo "  key $K  held: $(cat "$(held "$K")" 2>/dev/null)"
one "warm, the held instance replayed" GREEN

# ------------------------------------------------------- a held entry that is empty
echo '[]' > "$(held "$K")"
one "the entry is emptied -- zero instances graded" REDDENS

# -------------------------------------------- a held instance the document refuses
echo '[{"limit": "not an integer"}]' > "$(held "$K")"
one "the entry holds a payload the document refuses" REDDENS

# ------------------------------------------------- a held entry short of the count
echo '[]' > "$(held "$K")"
py - <<PY
import json, pathlib
p = pathlib.Path("$(held "$K")")
p.write_text(json.dumps([{"limit": 1}, {"limit": 2}][:0]))
PY
one "the entry cannot cover the obligation" REDDENS

# --------------------------------------------------------------- a MISSING entry
rm -f "$(held "$K")"
one "the entry is deleted -- a miss draws, and costs" GREEN

# ------------------------------------------------------------------ a STALE key
# One byte of the RAW BUNDLE document, which is the only kind of change that may move a
# key: an upstream edit. A change to a DEPENDENCY moves it too, because
# `bundle.source_identities` takes the reference closure over the raw documents.
BEFORE=$(key)
py - <<PY
import json, pathlib
p = pathlib.Path("$D")
doc = json.loads(p.read_text())
doc["description"] = doc.get("description", "") + " (perturbed)"
p.write_text(json.dumps(doc, indent=2))
PY
AFTER=$(key)
if [ "$BEFORE" = "$AFTER" ]; then
  echo "*** the document moved and the key did not: $BEFORE"
else
  echo "the document moved by one byte: key $BEFORE -> $AFTER"
fi
# The OLD entry is still on disk under the old key, and nothing asks for it.
one "a stale key -- the held instance is not used" GREEN
git checkout -- "$D"

# ------------------------------------- OUR OWN INLINING, which may NOT move the key
# The packaged record is `bundle.record`'s output, so perturbing it is what a change to
# how this package inlines produces once re-emitted. No document moved, so the question
# the draw asks has not moved either, and the held instance is still evidence --
# `corpus_defect` re-offers it to the perturbed record before it counts.
BEFORE=$(key)
py - <<PY
import json, pathlib
p = pathlib.Path("$R")
doc = json.loads(p.read_text())
doc["\$comment"] = "an inlining this package spells differently"
p.write_text(json.dumps(doc, indent=2))
PY
AFTER=$(key)
if [ "$BEFORE" = "$AFTER" ]; then
  echo "the record moved and the key did NOT, as designed: $BEFORE"
else
  echo "*** the record moved the key: $BEFORE -> $AFTER -- the key is on our rendering again"
fi
one "our rendering moved -- the held instance is replayed" GREEN
git checkout -- "$R"

# ------------------------------------------- and the guards themselves, broken
rm -rf "$STORE"
py -m pytest tests/test_emit.py -q -p no:randomly -n0 \
   -k "test_every_class_passes_all_three_checks and pagination-request" > /dev/null 2>&1
K=$(key)

guard() {  # guard <label> <-k expression selecting the test it should redden>
  out=$(py -m pytest tests/test_accepts_corpus.py -q -p no:randomly -n0 -k "$2" 2>&1 | tail -3)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
  printf '%-52s %-9s %-18s %s\n' "$1" "$verdict" "" \
    "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*' | head -1)"
  git checkout -- "$H" "$C" "$B" "$E"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    if not isinstance(held, list) or len(held) != examples:';assert s.count(a)==1;p.write_text(s.replace(a,'    if False:'))"
guard "corpus_defect stops counting the instances" "cover_the_obligation or empty_entry"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='        if conforms(schema, instance, validator_cls=cls) is False:';assert s.count(a)==1;p.write_text(s.replace(a,'        if False:'))"
guard "corpus_defect stops asking the document" "document_refuses"

edit "import pathlib;p=pathlib.Path('$B');s=p.read_text();a='        for member in sorted(reached):';assert s.count(a)==1;p.write_text(s.replace(a,'        for member in [document]:'))"
guard "the identity drops the reference closure" "dependencys_own_raw_bytes"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='        \"source\": source_identities()[ref.document],';assert s.count(a)==1;p.write_text(s.replace(a,'        \"source\": json.dumps(bundle.record(BUNDLE, ref.document), sort_keys=True),'))"
guard "the identity goes back to OUR rendering" "inlining_moves_the_record"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='            \"examples\": examples,';assert s.count(a)==1;p.write_text(s.replace(a,''))"
guard "the key drops the example count" "every_input_to_the_draw"

edit "import pathlib;p=pathlib.Path('$C');s=p.read_text();a='            if json.loads(text) != instances:';assert s.count(a)==1;p.write_text(s.replace(a,'            if False:'))"
guard "the store holds a value it cannot read back" "hold_faithfully"

rm -rf "$STORE"
