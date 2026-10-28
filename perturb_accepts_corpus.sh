#!/bin/bash
# Break the held accepts corpus on purpose, one way at a time, and watch it redden.
#
# `tests/corpus.py` holds the instances the accepts check drew, keyed by
# `harness.corpus_key`, so the suite stops re-drawing the same payloads from the same
# pinned records on every run. That is a cache in front of the one check that PROVES a
# widening rather than believing it (`docs/plan/rebuild-plan.md` section 8), and
# `pyproject.toml`'s own invariant says what that costs: "A faster suite that grades
# something else would not be faster." So the question this script answers is the only
# one that matters about it -- can a wrong corpus pass?
#
# Two of the cases are the ones the row was asked to demonstrate by name:
#
#   * A STALE KEY. A packaged record moves by one byte; the key moves with it; the held
#     instance is still on disk and is NOT used. The pair draws and grades.
#   * A MISSING ENTRY. The entry is deleted; the pair draws and grades. A miss costs and
#     never passes on nothing.
#
# Neither of those reddens, and that is the correct answer for both: a miss is work, not
# a defect. What MUST redden is a held entry that cannot stand in, and the three shapes
# of that are the rest of the cases.
#
#   ./perturb_accepts_corpus.sh
#
# This is BANKED EVIDENCE and not a check: pytest does not collect it, and
# `tests/test_accepts_corpus.py` is what the suite grades. It edits tracked files and a
# packaged record in place and restores them with `git checkout --`, so it REQUIRES A
# CLEAN TREE and refuses to run otherwise.
#
# A COLLECTION ERROR IS NOT A GREEN RUN. The verdict below matches "failed|error" for
# that reason, which is `perturb_dump_exemptions.sh`'s own lesson: a malformed
# perturbation that never ran once scored as a guard that cannot redden.
set -u
cd "$(dirname "$0")" || exit 1

H=codegen/harness.py
C=tests/corpus.py
R=src/adcp/types/_schemas/core/pagination-request.json
PAIR='core/pagination-request.json#'
STORE=.accepts-corpus

if [ -n "$(git status --porcelain -- "$H" "$C" "$R")" ]; then
  echo "refusing to run: $H, $C or $R has uncommitted changes, which this would destroy" >&2
  exit 1
fi

py() { PYTHONPATH=.:src .venv/bin/python "$@"; }

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
try:
    node = harness.resolve(pair.schema, store={}, referrer=pair.document)
except Exception:
    node = pair.schema
print(harness.corpus_key(node, examples=1, custom_formats=te.FORMAT_STRATEGIES))
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
# One byte of the packaged record, which is what a changed schema -- or a changed
# DEPENDENCY, since the record inlines its closure -- produces once re-emitted.
BEFORE=$(key)
py - <<PY
import json, pathlib
p = pathlib.Path("$R")
doc = json.loads(p.read_text())
doc["description"] = doc.get("description", "") + " (perturbed)"
p.write_text(json.dumps(doc, indent=2))
PY
AFTER=$(key)
if [ "$BEFORE" = "$AFTER" ]; then
  echo "*** the record moved and the key did not: $BEFORE"
else
  echo "the record moved by one byte: key $BEFORE -> $AFTER"
fi
# The OLD entry is still on disk under the old key, and nothing asks for it.
one "a stale key -- the held instance is not used" GREEN
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
  git checkout -- "$H" "$C"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    if not isinstance(held, list) or len(held) != examples:';assert s.count(a)==1;p.write_text(s.replace(a,'    if False:'))"
guard "corpus_defect stops counting the instances" "cover_the_obligation or empty_entry"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='        if conforms(schema, instance, validator_cls=cls) is False:';assert s.count(a)==1;p.write_text(s.replace(a,'        if False:'))"
guard "corpus_defect stops asking the document" "document_refuses"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='            \"schema\": schema,';assert s.count(a)==1;p.write_text(s.replace(a,'            \"schema\": sorted(schema),'))"
guard "the key hashes the node's KEYS and not its bytes" "dependencys_own_bytes"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='            \"examples\": examples,';assert s.count(a)==1;p.write_text(s.replace(a,''))"
guard "the key drops the example count" "every_input_to_the_draw"

edit "import pathlib;p=pathlib.Path('$C');s=p.read_text();a='            if json.loads(text) != instances:';assert s.count(a)==1;p.write_text(s.replace(a,'            if False:'))"
guard "the store holds a value it cannot read back" "hold_faithfully"

rm -rf "$STORE"
