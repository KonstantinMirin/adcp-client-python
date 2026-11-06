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
# It edits the three files in place and restores them with `git checkout --`, so it
# REQUIRES A CLEAN TREE: uncommitted work in any of them is destroyed. It refuses to
# run otherwise, because that destruction happened once while this was being written.
#
# THE VERDICT IS KEYED ON PYTEST'S EXIT CODE AND NOT ON ITS OUTPUT, and that is the
# correction this version carries. The first version matched "N failed". A malformed
# perturbation left a SyntaxError, pytest reported "1 error", and the case scored
# STAYED GREEN -- so a perturbation that never ran was recorded as a guard that cannot
# redden, which is the exact opposite of what it measured. The second version matched
# "failed|error", which closes that one case and NOT the shape: an INTERNALERROR prints
# no count line at all, so a crash in a plugin or a conftest is again indistinguishable
# from a pass. Any scraper that reads a run as green by failing to match a word has the
# same hole.
#
# The exit code does not have it. pytest's codes are a closed set and each means one
# thing: 0 all passed, 1 tests failed, 2 interrupted, 3 internal error, 4 usage error,
# 5 nothing collected. So this script reports REDDENS for 1 alone, STAYED GREEN for 0
# alone, NOTHING COLLECTED for 5 -- which is a defect in the case's own `-k` and not
# evidence about the guard -- and PYTEST rc=N for everything else. A case that does not
# score REDDENS is never passed over as green, and the last two cases are the control:
# the clean tree is green, and a SyntaxError scores rc=4 rather than either verdict.
set -u
cd "$(dirname "$0")" || exit 1

E=codegen/dump_exemptions.py
T=tests/test_dump_exemptions.py
H=codegen/harness.py

if [ -n "$(git status --porcelain -- "$E" "$T" "$H")" ]; then
  echo "refusing to run: $E, $T or $H has uncommitted changes, which this would destroy" >&2
  exit 1
fi

# Invoked directly rather than through `eval`: the perturbations are Python
# one-liners full of quotes and newlines, and `eval` re-splits them.
py() { CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync python "$@"; }

run() {  # run <label> <-k expression selecting the ONE test it should redden>
  py -m pytest "$T" -q -k "$2" >/tmp/perturb_dump_exemptions.out 2>&1
  rc=$?
  case $rc in
    1) verdict=REDDENS ;;
    0) verdict="STAYED GREEN" ;;
    5) verdict="NOTHING COLLECTED" ;;
    *) verdict="PYTEST rc=$rc" ;;
  esac
  printf '%-58s %-18s %s\n' "$1" "$verdict" \
    "$(grep -oE '[0-9]+ (passed|failed|error)[a-z, ]*' /tmp/perturb_dump_exemptions.out | tail -1)"
  git checkout -- "$E" "$T" "$H"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

# --------------------------------------------------------------------------- #
# the SET: what may be in it, and what each entry has to say for itself
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='EXEMPT: tuple[Exemption, ...] = tuple(';assert s.count(a)==1;p.write_text(s.replace(a,'EXEMPT: tuple[Exemption, ...] = (Exemption(document=\"x/y.json\", pointer=\"/z\", keyword=\"minProperties\", value=1, reason=UPSTREAM),) + tuple('))"
run "an entry for a reason that is NOT a violating pattern" "only_shrinks"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='_RFC = (';assert s.count(a)==1;p.write_text(s.replace(a,'_RFC = \"no issue cited\" or ('))"
run "an entry whose reason cites no issue" "names_its_upstream_issue"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='ORIGIN_ONLY = \"^https://[^/?#@]+\$\"';assert s.count(a)==1;p.write_text(s.replace(a,'ORIGIN_ONLY = \"^https://[^/?#@]+/?\$\"'))"
run "upstream repairs the pattern: the value stops matching" "resolves_and_still_states"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='(\"core/attestation-reference.json\", \"/properties/issuer/oneOf/2/properties/origin\"),';assert s.count(a)==1;p.write_text(s.replace(a,'(\"core/attestation-reference.json\", \"/properties/issuer/oneOf/2/properties/nope\"),'))"
run "an entry pointer that no longer resolves" "resolves_and_still_states"

# --------------------------------------------------------------------------- #
# the DERIVED EQUALITY, in both directions and over both pointer spaces
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='        (\"core/attestation-reference.json\", \"/properties/issuer/oneOf/2/properties/origin\"),\n';assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "a position the tree states DROPPED from the table" "origin_only_part"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='    ORIGIN_ONLY: (\n';assert s.count(a)==1;p.write_text(s.replace(a,a+'        (\"core/pagination-request.json\", \"/properties/limit\"),\n'))"
run "a position the tree does NOT state added to the table" "origin_only_part"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='        (\"core/audience-evidence-selection.json\", \"/definitions/Shared11/properties/issuer/oneOf/2/properties/origin\"),\n';assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "the HOISTED position dropped from the table" "hoisted_position"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='VIOLATING: dict[str, str] = {ORIGIN_ONLY: _RFC, PERCENT_FREE: _PCT}';assert s.count(a)==1;p.write_text(s.replace(a,'VIOLATING: dict[str, str] = {ORIGIN_ONLY: _RFC, PERCENT_FREE: _PCT, \"^https://\": _RFC}'))"
run "a pattern DECLARED violating that does not violate" "violating_uri_pattern"

# --------------------------------------------------------------------------- #
# the CROSSING between the two pointer spaces, which is what this row added.
# Every case here was green before `_occurrences` existed, because `applying_to`
# answered () for a hoisted position and there was nothing left to break.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='        hopped = through_the_store(node, root)';assert s.count(a)==1;p.write_text(s.replace(a,'        hopped = node  # perturbed: the storage hop is not taken'))"
run "_occurrences stops dereferencing the record's storage" "hoisted_position"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='        if text in wanted:';assert s.count(a)==1;p.write_text(s.replace(a,'        if False and text in wanted:  # perturbed'))"
run "_occurrences answers nothing for every position" "hoisted_position"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='            visit(hopped, applied, (STORE_SECTION, entry))';assert s.count(a)==1;p.write_text(s.replace(a,'            visit(hopped, applied, (*text, STORE_SECTION, entry))  # perturbed'))"
run "_occurrences keys a stored position on the OCCURRENCE" "hoisted_position"

# --------------------------------------------------------------------------- #
# the STRIKE: what it removes, where, and what it leaves alone
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='    found = _strikes(ref_document, ref_pointer)';assert s.count(a)==1;p.write_text(s.replace(a,'    found = ()  # perturbed'))"
run "struck() strikes nothing" "strike_explains"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='            del node[entry.keyword]';assert s.count(a)==1;p.write_text(s.replace(a,'            node.clear()'))"
run "struck() clears the whole node, not the keyword" "removes_only_the_named"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='    if not found:\n        return schema';assert s.count(a)==1;p.write_text(s.replace(a,'    if not found:\n        return copy.deepcopy(schema)'))"
run "struck() copies a pair that has no entry" "returned_by_identity"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='    return harness._wire_dump(pair.accept(seen[-1]))';assert s.count(a)==1;p.write_text(s.replace(a,'    return seen[-1]'))"
run "the DUMP replaced by the input: the premise goes dead" "strike_explains"

# The test file's own walk, which is where this row found a VACUOUS gate: `_walk`
# yielded the MAPPINGS only, so the pointer naming a struck `pattern` was yielded by
# nothing and `before - after` was the empty set. Three assertions of
# `removes_only_the_named` were true of a strike that removed nothing at all.
edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();a='    yield ptr, node\n    if isinstance(node, dict):';assert s.count(a)==1;p.write_text(s.replace(a,'    if isinstance(node, (dict, list)):\n        yield ptr, node\n    if isinstance(node, dict):'))"
run "_walk yields the mappings only: the difference goes empty" "removes_only_the_named"

# --------------------------------------------------------------------------- #
# the WIRING. Everything above grades the set and the strike; these two grade
# that check_pair reaches them. The first is not hypothetical: before the ref was
# threaded, every other case in this file passed while the suite's own verdict for
# the exempt pairs was unchanged.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='        seen=accepted,\n        ref=pair.ref,';assert s.count(a)==1;p.write_text(s.replace(a,'        seen=accepted,'))"
run "check_pair stops threading the pair's ref" "check_pair_passes_the_exempt"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='    return [f\"{e.document}#{e.pointer}/{e.keyword}\" for e in applying_to(ref_document, ref_pointer)]';assert s.count(a)==1;p.write_text(s.replace(a,'    return []'))"
run "the exemption applied but NOT reported" "check_pair_passes_the_exempt"

# --------------------------------------------------------------------------- #
# the CONTROLS, which are what make the verdicts above readable: an unperturbed
# run is GREEN, and a run that never executed is neither green nor red.
# --------------------------------------------------------------------------- #
run "the clean tree (expected: STAYED GREEN)" "dump_exemptions or strike or entry or pair"

edit "import pathlib;p=pathlib.Path('$T');s=p.read_text();p.write_text('def (\n'+s)"
run "a SyntaxError in the test file (expected: not a verdict)" "strike_explains"
