#!/bin/bash
# Break every guard over the dump exemptions on purpose, one at a time.
#
# `codegen/dump_exemptions.py` carries the positions where a document refuses the
# SDK's own correct output, and section 6 says widening the comparison removes the
# only check that reads the generated code. So the guards around that set are the
# ones most worth distrusting, and a guard that cannot redden is not a guard.
#
# This is BANKED EVIDENCE and not a check: it is not collected by pytest, it is
# re-runnable, and `tests/test_dump_exemptions.py` is what the suite grades. Every
# case below names what it breaks and must print REDDENS.
#
#   ./perturb_dump_exemptions.sh
#
# It edits the two files in place and restores them with `git checkout --`, so it
# REQUIRES A CLEAN TREE: uncommitted work in either file is destroyed. It refuses to
# run otherwise, because that destruction happened once while this was being written.
#
# A COLLECTION ERROR IS NOT A GREEN RUN. The first version of the verdict matched
# only "N failed", so a malformed perturbation that left a SyntaxError was reported
# as STAYED GREEN and hid the fact that it had not applied. The verdict counts errors.
set -u
cd "$(dirname "$0")" || exit 1

E=codegen/dump_exemptions.py
T=tests/test_dump_exemptions.py

if [ -n "$(git status --porcelain -- "$E" "$T")" ]; then
  echo "refusing to run: $E or $T has uncommitted changes, which this would destroy" >&2
  exit 1
fi

# Invoked directly rather than through `eval`: the perturbations are Python
# one-liners full of quotes and newlines, and `eval` re-splits them.
py() { CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync python "$@"; }

run() {  # run <label> <-k expression selecting the ONE test it should redden>
  out=$(py -m pytest "$T" -q -k "$2" 2>&1 | tail -3)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
  printf '%-56s %-12s %s\n' "$1" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*' | head -1)"
  git checkout -- "$E" "$T"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='    Exemption(\n        document=\"core/provenance.json\"';assert s.count(a)==1;p.write_text(s.replace(a,'    Exemption(document=\"x/y.json\", pointer=\"/z\", keyword=\"pattern\", value=1, reason=UPSTREAM),\n'+a))"
run "a fifth entry added to the set" "only_shrinks"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='_D8 = (';assert s.count(a)==1;p.write_text(s.replace(a,'_D8 = \"no issue cited\" or ('))"
run "an entry whose reason cites no issue" "names_its_upstream_issue"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='ORIGIN_ONLY = \"^https://[^/?#@]+\$\"';assert s.count(a)==1;p.write_text(s.replace(a,'ORIGIN_ONLY = \"^https://[^/?#@]+/?\$\"'))"
run "upstream repairs the pattern: the value stops matching" "resolves_and_still_states"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='/properties/disclosure/properties/jurisdictions/items/properties/render_guidance';assert s.count(a)>=1;p.write_text(s.replace(a,'/properties/disclosure/properties/nope',1))"
run "an entry pointer that no longer resolves" "resolves_and_still_states"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='assert len(copies) == 90';assert s.count(a)==1;p.write_text(s.replace(a,'assert len(copies) == 91'))"
run "the minProperties exposure count moves" "pairs_own_root"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='assert len(patterns) == 8';assert s.count(a)==1;p.write_text(s.replace(a,'assert len(patterns) == 7'))"
run "the uri pattern population count moves" "population_is_the_one_d5_states"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();h='    Exemption(\n        document=\"core/attestation-capabilities.json\",\n        pointer=\"/properties/accepted_issuers/items/properties/credential_origins';i=s.index(h);e=s[i:];e=e[:e.index('    ),\n')+len('    ),\n')];assert s.count(e)==1;p.write_text(s.replace(e,''))"
run "the LATENT entry dropped from the set" "violating_uri_pattern"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='    found = applying_to(ref_document, ref_pointer)';assert s.count(a)==1;p.write_text(s.replace(a,'    found = ()  # perturbed'))"
run "struck() strikes nothing" "strike_explains"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='            del node[entry.keyword]';assert s.count(a)==1;p.write_text(s.replace(a,'            node.clear()'))"
run "struck() clears the whole node, not the keyword" "removes_only_the_named"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='    if not found:\n        return schema';assert s.count(a)==1;p.write_text(s.replace(a,'    if not found:\n        return copy.deepcopy(schema)'))"
run "struck() copies a pair that has no entry" "returned_by_identity"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='    return harness._wire_dump(pair.accept(seen[-1]))';assert s.count(a)==1;p.write_text(s.replace(a,'    return seen[-1]'))"
run "the DUMP replaced by the input: the premise goes dead" "strike_explains"
