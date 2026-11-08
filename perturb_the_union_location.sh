#!/bin/bash
# Break the location a union's refusal names, one way at a time, and watch it redden.
#
# `docs/plan/final-state.md` reading 3: "A union is emitted as a base and one class per
# branch precisely so that a caller learns WHICH FIELD was wrong", "it is the whole path,
# through every hop", and "the 'no branch determined' refusal owes a location too". The
# location is not diagnostics -- `core/error.json` types `Error.field` as a JSONPath-lite
# pointer derived from the pydantic `loc`, so an empty `loc` publishes an empty
# `Error.field`. `adcp.types._base.BranchDispatchMixin` is where that happens, in three
# places that are three different refusals, and the gate is
#
#   tests/test_union_dispatch.py::test_a_union_refusal_names_the_position_it_refuses_at
#   tests/test_union_dispatch.py::test_a_union_refusal_names_a_nested_position_through_a_list_and_a_model
#   tests/test_union_dispatch.py::test_a_keyless_dispatch_refusal_names_the_position_the_document_refuses_at
#
# The first ranges over EVERY union base the tree emits, offering each the committed
# accepts floor's own instance with its deepest scalar position replaced by a value no
# scalar admits, and requires the refusal to name a position at or under the fault. The
# second writes out the hard case -- `('packages', 0, 'targeting_overlay',
# 'geo_countries', 0)`, through a list index, into a nested model, into another list --
# and asserts the WHOLE report, so a repair that prepends the dispatch's own position and
# truncates the branch's inner path is caught there and nowhere else. The third is over
# `_undetermined`, the keyless screen, whose witnesses have to be DERIVED: the four
# payloads `adcp-client-python-84a9` is about are each refused by the document at the
# ROOT, so that row cannot tell a screen that reports the pointer from one that discards
# it.
#
# So the question this script answers is the only one that matters about either: can a
# dispatch that has lost the location pass them?
#
#   ./perturb_the_union_location.sh
#
# This is BANKED EVIDENCE and not a check: pytest does not collect it. It edits a tracked
# file in place and restores it with `git checkout --`, so it REQUIRES A CLEAN TREE and
# refuses to run otherwise.
#
# THE VERDICT IS KEYED ON THE RUN'S OWN JUNIT REPORT AND NEVER ON ITS PROSE, which is
# `perturb_the_null_clause.sh`'s measured rule and the reasoning is its header's: a
# scraper over "N failed" cannot tell a run that never happened from a run that passed,
# and neither can pytest's exit code -- a SyntaxError in a test file collects nothing and
# exits 1, the same code a real failure exits with. So:
#
#   no report file       NOT RUN         (the process died before it could write one)
#   errors > 0           NOT RUN         (collected nothing, or a fixture blew up)
#   tests == 0           NOTHING COLLECTED (a defect in the case's own -k, not evidence)
#   failures > 0         REDDENS
#   otherwise            STAYED GREEN
#
# AND WHICH CLAUSE REDDENED IS PRINTED, because that is the evidence rather than the
# count. Two of these five read GREEN on the first run against the gate as it stood, and
# neither green was the dispatch being right: case 2 was absorbed by an UNCAPPED cell, and
# case 5 had no witness able to tell the two answers apart. Both are now owned -- case 2
# by the cell's ceiling and case 5 by the derived keyless witnesses -- and a case that
# still read green would be reported as green, because a run that printed only the reds
# would be claiming coverage the three clauses do not have.
set -u
cd "$(dirname "$0")" || exit 1

B=src/adcp/types/_base.py
GATE=tests/test_union_dispatch.py
#: All three clauses: "names_the_position" is the tree-wide row and the keyless row,
#: "nested_position" is the exact-pointer row.
SELECT="names_the_position or nested_position"
OUT=/tmp/perturb_the_union_location.out
XML=/tmp/perturb_the_union_location.xml

if [ -n "$(git status --porcelain -- "$B")" ]; then
  echo "refusing to run: $B has uncommitted changes -- this script edits it in place" >&2
  exit 1
fi

py() { env PYTHONPATH=.:src PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python "$@"; }

read_report() {
  py -c "
import pathlib, xml.etree.ElementTree as ET
path = pathlib.Path('$XML')
if not path.exists():
    print('NOT RUN|no junit report: the run died before writing one'); raise SystemExit
try:
    suites = list(ET.parse(path).iter('testsuite'))
except ET.ParseError as exc:
    print(f'NOT RUN|unparseable junit report: {exc}'); raise SystemExit
n = {k: sum(int(s.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
cases = list(ET.parse(path).iter('testcase'))
red = sorted(c.get('name') for c in cases if c.find('failure') is not None)
green = sorted(c.get('name') for c in cases if c.find('failure') is None)
counts = ' '.join(f'{k}={v}' for k, v in n.items())
if n['errors']:
    verdict = 'NOT RUN'
elif not n['tests']:
    verdict = 'NOTHING COLLECTED'
elif n['failures']:
    verdict = 'REDDENS'
else:
    verdict = 'STAYED GREEN'
print(f'{verdict}|{counts}')
for name in red:
    print('     RED   ' + name)
for name in green:
    print('     green ' + name)
"
}

run() {  # run <label>
  rm -f "$XML"
  py -m pytest "$GATE" -q -p no:cacheprovider -p no:randomly -k "$SELECT" \
    --junitxml="$XML" >"$OUT" 2>&1
  rc=$?
  report=$(read_report)
  head=$(printf '%s' "$report" | head -1)
  printf '%-62s %-18s rc=%-3s %s\n' "$1" "${head%%|*}" "$rc" "${head#*|}"
  printf '%s\n' "$report" | tail -n +2
  git checkout -- "$B"
}

swap() {
  py - "$1" "$2" <<'PY' || { echo "perturbation did not apply" >&2; git checkout -- src/adcp/types/_base.py; exit 1; }
import sys, pathlib
path = pathlib.Path("src/adcp/types/_base.py")
text = path.read_text()
old, new = sys.argv[1], sys.argv[2]
assert text.count(old) == 1, f"anchor appears {text.count(old)} times: {old!r}"
path.write_text(text.replace(old, new))
PY
}

echo "CONTROL (expected: STAYED GREEN)"
run "0. the tree as committed"

# 1. The branches' own agreed pointer is thrown away, which is the defect
#    adcp-client-python-jgsf was filed for: every union refusal became the combinator.
echo
swap "        return agreed" "        return []"
run "1. _agreed answers with nothing -- the inner pointer discarded"

# 2. The combinator keeps answering but at no position, which is the half of the defect
#    that survives when the branches agree on nothing. GREEN before the cell it moves
#    sites into carried a ceiling, and that is what the ceiling is for.
echo
swap "loc=cls._common_position(value, err)," "loc=(),"
run "2. the combinator at loc=() instead of the agreed position"

# 3. Both at once: the dispatch exactly as it behaved before the repair.
echo
swap "        return agreed" "        return []"
swap "loc=cls._common_position(value, err)," "loc=(),"
run "3. BOTH -- the dispatch exactly as it was before the repair"

# 4. THE FAILURE MODE A SHALLOW WITNESS CANNOT SEE: the branch's inner path truncated to
#    its first segment, which is right on a one-level union and wrong on the asserted one.
echo
swap 'agreed.append({**row, "loc": below})' 'agreed.append({**row, "loc": below[:1]})'
run "4. the inner path truncated to one segment"

# 5. The keyless screen's own refusal. Its SENTENCE names the branch, the absent
#    discriminator and the document's reason, and a good sentence is not a location.
#    GREEN against adcp-client-python-84a9's own row, whose four payloads the document
#    refuses at the ROOT -- which is why the keyless clause derives its own witnesses.
echo
swap 'loc=tuple(why["loc"]),' "loc=(),"
run "5. _undetermined keeps its sentence and loses its position"

# 6. THE CONTROL FOR THE INSTRUMENT ITSELF: a SyntaxError collects nothing and exits 1,
#    the same code a real failure exits with, and must not be read as a failure -- which
#    is the whole reason the verdict is keyed on the junit report.
echo
swap "    @classmethod
    def _agreed" "    def (
    @classmethod
    def _agreed"
run "6. a SyntaxError in the dispatch  (expected: NOT RUN)"

echo
echo "RESTORED:"
git status --porcelain -- "$B"
echo "(empty above means the tree is back as committed)"
