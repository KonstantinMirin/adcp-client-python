#!/bin/bash
# Break reading 9's upstream half on purpose, one claim at a time.
#
# `docs/plan/final-state.md` reading 9: "Each declared fact is ours with a decision
# recorded, or upstream with an issue that exists ... Decided by every `upstream`
# attribution naming a live issue, and by that registry's equality in both
# directions."
#
# Measured on this tree: all 90 declared facts are OURS -- every attribution is a
# cell address in `docs/plan/rebuild-plan.md` §5 and not an issue reference -- so
# `attribution.REGISTRY` is empty and the clause had nothing to range over. What the
# repository DOES have is nine upstream references it cites in its own sentences,
# one of them in a generated module that ships in the wheel. Those are the
# population `attribution.VERIFIED` is compared against, in both directions, and the
# cases below are what say so.
#
# This is BANKED EVIDENCE and not a check: it is not collected by pytest, it is
# re-runnable, and `tests/test_decision_set.py` is what the suite grades. Every case
# names what it breaks and must print REDDENS.
#
#   ./perturb_the_attribution.sh
#
# READ-ONLY UPSTREAM. Nothing here touches anyone's tracker: every case edits a
# local file. `survey/upstream_issues.py` is the only thing in this repository that
# talks to GitHub and it only VIEWS.
#
# It edits three files in place and restores them with `git checkout --`, so it
# REQUIRES A CLEAN TREE: uncommitted work in any of them is destroyed. It refuses to
# run otherwise.
#
# A COLLECTION ERROR IS NOT A GREEN RUN, and INTERNALERROR IS A THIRD SHAPE. The
# verdict matches "failed|error|INTERNALERROR", because a malformed perturbation
# leaves a run that never executed and a scraper matching only "failed" records that
# as a guard that cannot redden. The third shape was measured here: a perturbation
# that cut a dict entry at the wrong closing paren left a SyntaxError, pytest printed
# INTERNALERROR with no "N failed" line at all, and the case scored STAYED GREEN with
# an empty verdict column. Any scraper over pytest output needs all three.
set -u
cd "$(dirname "$0")" || exit 1

A=codegen/attribution.py
T=tests/test_decision_set.py
R=src/adcp/types/_schemas/core/pagination_request.py

if [ -n "$(git status --porcelain -- "$A" "$T" "$R")" ]; then
  echo "refusing to run: one of $A $T $R has uncommitted changes, which this destroys" >&2
  exit 1
fi

py() { CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync python "$@"; }

# `-k` selects the ONE reading each case should move. The narrowing half of this file
# grades §5's whole cell table and takes four minutes; none of these cases touches it,
# so selecting is what keeps this script re-runnable rather than a thing nobody runs.
run() {  # run <label> <-k expression selecting the reading it should redden>
  out=$(py -m pytest "$T" -q -n 0 -p no:randomly -k "$2" 2>&1 | tail -4)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)|INTERNALERROR"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
  printf '%-60s %-12s %s\n' "$1" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*|INTERNALERROR.*' | head -1)"
  git checkout -- "$A" "$T" "$R"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

# The attribution entry every case below plants, as one Python literal. The site is a
# real document and a pointer nothing declares, so the planted entry moves the CITATION
# readings and not the declared-facts one -- which is the point: a reference enters the
# tree the moment somebody types it, whether or not a fact is attributed to it yet.
PLANT='REGISTRY: Mapping[Site, Issue] = {\n    ("core/pagination-request.json", "#/properties/max_results", "maximum"): Issue(\n        "adcontextprotocol/adcp#99999999",\n        "the document should state this bound",\n    ),\n}'

echo "=== AN ATTRIBUTION NAMING AN ISSUE THAT DOES NOT EXIST ==="

# The case the brief asks for. The reference enters the citation census the moment it is
# written, and no sighting records it, so the FORWARD direction reports it by name.
edit "import pathlib;p=pathlib.Path('$A');s=p.read_text();a='REGISTRY: Mapping[Site, Issue] = {}';assert s.count(a)==1;p.write_text(s.replace(a,'''$PLANT'''.replace('\\\\n','\n')))"
run "an attribution naming #99999999, no sighting" "cites_has_a_sighting"

# And the same attribution with the sighting somebody would actually have written after
# looking: the look found nothing, so the record says ABSENT and `absent()` reports it.
# This is the direction that cannot be satisfied by writing an entry: a sighting is what
# was SEEN, and `survey/upstream_issues.py` is what re-derives it from the tracker.
edit "import pathlib;p=pathlib.Path('$A');s=p.read_text();a='REGISTRY: Mapping[Site, Issue] = {}';assert s.count(a)==1;p.write_text(s.replace(a,'''$PLANT'''.replace('\\\\n','\n')))"
edit "import pathlib;p=pathlib.Path('$A');s=p.read_text();a='VERIFIED: Mapping[str, Sighting] = {';assert s.count(a)==1;p.write_text(s.replace(a,a+'\n    \"adcontextprotocol/adcp#99999999\": Sighting(\n        reference=\"adcontextprotocol/adcp#99999999\",\n        state=\"ABSENT\",\n        title=\"\",\n        seen=\"2026-11-05\",\n    ),'))"
run "the same attribution, sighted and recorded ABSENT" "cites_has_a_sighting"

echo
echo "=== THE REGISTRY'S EQUALITY, BOTH DIRECTIONS ==="

# FORWARD: a reference the repository cites with its sighting taken away. #8516 is the
# one that SHIPS -- `src/adcp/types/envelopes.py` tells a consumer "Upstream:
# adcontextprotocol/adcp#8516" -- so this is the direction that covers a claim made to
# somebody who installed the wheel.
edit "import pathlib,re;p=pathlib.Path('$A');s=p.read_text();r=re.compile(r'^    \"adcontextprotocol/adcp#8516\": Sighting\(.*?^    \),\n', re.S|re.M);assert len(r.findall(s))==1;p.write_text(r.sub('',s))"
run "the sighting for the reference the WHEEL cites, removed" "cites_has_a_sighting"

# BACKWARD: a sighting nothing cites. This is what stops the registry becoming an
# allowlist that grows and never shrinks -- an entry leaves when the last sentence that
# cited it is deleted, and nothing else has to notice.
edit "import pathlib;p=pathlib.Path('$A');s=p.read_text();a='VERIFIED: Mapping[str, Sighting] = {';assert s.count(a)==1;p.write_text(s.replace(a,a+'\n    \"adcontextprotocol/adcp#4242\": Sighting(\n        reference=\"adcontextprotocol/adcp#4242\",\n        state=\"OPEN\",\n        title=\"an issue nothing in this repository cites\",\n        seen=\"2026-11-05\",\n    ),'))"
run "a sighting no sentence of ours cites" "cites_has_a_sighting"

echo
echo "=== THE EXCLUSION, which is the only place a citation could hide ==="

# `CARRIED` hides the bundle and the emitted records, because a reference in a protocol
# document is upstream citing upstream. A citation of OURS written into a record would
# be hidden by that rule -- so the rule requires every reference a record cites to appear
# in the BUNDLE too, and this is that requirement put to the test.
edit "import pathlib;p=pathlib.Path('$R');s=p.read_text();assert '99999999' not in s;p.write_text(s.rstrip()+'\n\n# Upstream: adcontextprotocol/adcp#99999999\n')"
run "a citation of ours written into an emitted record" "cites_has_a_sighting"

echo
echo "=== AN ATTRIBUTION ON AN ISSUE UPSTREAM HAS CLOSED ==="

# An attribution says "the document does not state this fact and here is the open ask
# that would make it". Upstream closing the ask takes that sentence's reason away and
# leaves the widening in place, which nothing else reports.
edit "import pathlib;p=pathlib.Path('$A');s=p.read_text();a='REGISTRY: Mapping[Site, Issue] = {}';assert s.count(a)==1;p.write_text(s.replace(a,'REGISTRY: Mapping[Site, Issue] = {\n    (\"core/pagination-request.json\", \"#/properties/max_results\", \"maximum\"): Issue(\n        \"adcontextprotocol/adcp#7959\",\n        \"a settled ask carrying a live attribution\",\n    ),\n}'))"
run "an attribution naming the CLOSED #7959" "rests_on_an_issue_upstream_has_closed"

echo
echo "=== THE POPULATIONS, so a census that selects nothing cannot read as green ==="

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='        for number in sorted(set(CITATION.findall(text))):';assert s.count(a)==1;p.write_text(s.replace(a,'        for number in []:'))"
run "the citation census finds nothing" "cites_has_a_sighting"

edit "import pathlib;p=pathlib.Path('$A');s=p.read_text();a='VERIFIED: Mapping[str, Sighting] = {';i=s.index(a);e=s[i:];e=e[:e.index('\n}\n')+len('\n}\n')];p.write_text(s.replace(e,'VERIFIED: Mapping[str, Sighting] = {}\n'))"
run "the sighting registry emptied" "cites_has_a_sighting"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='    shut = claimed(\"sightings recording a closed issue\", attribution.closed())';assert s.count(a)==1;p.write_text(s.replace(a,'    shut = claimed(\"sightings recording a closed issue\", ())'))"
run "no sighting records a closed issue any more" "rests_on_an_issue_upstream_has_closed"

echo
echo "=== THE SIGHTING ITSELF, which is where 'somebody looked' becomes a value ==="

edit "import pathlib;p=pathlib.Path('$A');s=p.read_text();a='        if self.state not in STATES:';assert s.count(a)==1;p.write_text(s.replace(a,'        if False:'))"
run "a state outside the three a look can find is admitted" "refuses_a_record_nobody_could_have_made"

edit "import pathlib;p=pathlib.Path('$A');s=p.read_text();a='        if self.state == \"ABSENT\" and self.title.strip():';assert s.count(a)==1;p.write_text(s.replace(a,'        if False:'))"
run "an ABSENT sighting may carry a title it never saw" "refuses_a_record_nobody_could_have_made"

edit "import pathlib;p=pathlib.Path('$A');s=p.read_text();a='        if not self.seen.strip():';assert s.count(a)==1;p.write_text(s.replace(a,'        if False:'))"
run "a sighting with no date, which cannot go stale" "refuses_a_record_nobody_could_have_made"

echo
echo "EVERY LINE ABOVE MUST PRINT REDDENS. There is no control here that stays green:"
echo "the vacuous halves of this file -- the site-level attribution readings and the"
echo "narrowings registry's unused direction -- are stated in their own docstrings and"
echo "are not perturbable, because an empty registry has no entry to break."
