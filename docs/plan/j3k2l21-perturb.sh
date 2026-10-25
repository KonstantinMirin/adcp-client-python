#!/bin/bash
# Perturb each clause of
# test_a_union_root_is_a_base_or_an_alias_and_the_document_decides_which
# and record that it reddens.  Exit 0 from pytest means the perturbation was NOT
# caught, which is the finding; every other exit code is classified and printed,
# so an ERRORED run (collection error, usage error, internal error) is never read
# as a caught perturbation.
set -u
cd /Users/konst/projects/acp-j3k2l21 || exit 1
T=tests/test_emit.py
U=codegen/lower/union.py
MINE='a_union_root_is_a_base_or_an_alias'
ARITH='every_union_root_the_step_does_not_emit'

run() {   # run(<name>, <-k expr>)
  out=$(CCM_INDEX_BYPASS=1 env -u VIRTUAL_ENV uv run --no-sync python -m pytest "$T" \
        -k "$2" -p no:randomly -n0 -q 2>&1)
  code=$?
  line=$(printf '%s\n' "$out" | grep -E '^(FAILED|ERROR)|[0-9]+ (passed|failed|error)' | tail -2 | tr '\n' ' ')
  case $code in
    0) verdict="GREEN (BASE is the control and SHOULD be green; for a P- row this means NOT CAUGHT)" ;;
    1) verdict="RED (test failure)" ;;
    2) verdict="RED (interrupted)" ;;
    3) verdict="RED (internal error)" ;;
    4) verdict="RED (usage error)" ;;
    5) verdict="RED (no tests collected)" ;;
    *) verdict="RED (exit $code)" ;;
  esac
  printf '%-4s exit=%s  %s\n     %s\n' "$1" "$code" "$verdict" "$line"
  # the first assertion that fired, which is how a clause is attributed
  printf '%s\n' "$out" | grep -E '^E  +(AssertionError|assert)' | head -2 | sed 's/^/     /'
}

restore() { git checkout -- "$T" "$U"; }

echo "=== baseline"
run BASE "$MINE"

echo
echo "=== P-A  clause 1 (disjointness): declares_a_class answers True for every branch"
python3 - <<'EOF'
import pathlib
p = pathlib.Path("codegen/lower/union.py"); s = p.read_text()
s = s.replace('    return "properties" in doc_branch or "allOf" in doc_branch',
              '    return True  # PERTURBED', 1)
p.write_text(s)
EOF
run P-A "$MINE"; restore

echo
echo "=== P-B  clause 2 (both halves non-empty): no root is alias-shaped"
python3 - <<'EOF'
import pathlib
p = pathlib.Path("tests/test_emit.py"); s = p.read_text()
s = s.replace('''    return lower_union.states_a_scalar_instance(doc, "", kw) and not any(''',
              '''    return False and lower_union.states_a_scalar_instance(doc, "", kw) and not any(''', 1)
p.write_text(s)
EOF
run P-B "$MINE"; restore

echo
echo "=== P-C  clause 3 (the base half is pinned apart from the total): one alias root"
echo "         moves back into the base half, leaving 39 / 1 against the pinned 38 / 2"
python3 - <<'EOF'
import pathlib
p = pathlib.Path("tests/test_emit.py"); s = p.read_text()
s = s.replace('''    return lower_union.states_a_scalar_instance(doc, "", kw) and not any(''',
              '''    return document != "core/start-timing.json" and lower_union.states_a_scalar_instance(doc, "", kw) and not any(''', 1)
p.write_text(s)
EOF
run P-C "$MINE"; restore

echo
echo "=== P-D  clause 4 (an alias binds an alias, not a class): the clause is pointed at"
echo "         the BASE half, which must redden because those roots ARE classes"
python3 - <<'EOF'
import pathlib
p = pathlib.Path("tests/test_emit.py"); s = p.read_text()
s = s.replace('''    # Clause 4, on both instruments.
    for document in emitted_union_aliases():''',
              '''    # Clause 4, on both instruments.
    for document in emitted_union_bases():''', 1)
p.write_text(s)
EOF
run P-D "$MINE"; restore

echo
echo "=== P-E1 clause 5 (the null populations): the site count moved by one"
python3 - <<'EOF'
import pathlib
p = pathlib.Path("tests/test_emit.py"); s = p.read_text()
s = s.replace("    assert null_in_a_type_list == 57, null_in_a_type_list",
              "    assert null_in_a_type_list == 56, null_in_a_type_list", 1)
p.write_text(s)
EOF
run P-E1 "$MINE"; restore

echo
echo "=== P-E2 clause 5: the null-BRANCH test is relaxed to any typed branch, so the"
echo "         population it asserts is empty stops being empty"
python3 - <<'EOF'
import pathlib
p = pathlib.Path("tests/test_emit.py"); s = p.read_text()
s = s.replace('''            isinstance(b, dict) and b.get("type") == "null"''',
              '''            isinstance(b, dict) and b.get("type") is not None''', 1)
p.write_text(s)
EOF
run P-E2 "$MINE"; restore

echo
echo "=== P-F  the FEATURE: the alias dispatch is removed from the lowering, so the two"
echo "         alias roots stop emitting.  Both this row's check and the step's"
echo "         arithmetic must redden."
python3 - <<'EOF'
import pathlib
p = pathlib.Path("codegen/lower/union.py"); s = p.read_text()
s = s.replace('''    if states_a_scalar_instance(doc, pointer, kw) and not any(''',
              '''    if False and states_a_scalar_instance(doc, pointer, kw) and not any(''', 1)
p.write_text(s)
EOF
run P-F "$MINE"
echo
echo "=== P-F also against the step's arithmetic (42 / 84)"
run P-F2 "$ARITH"; restore

echo
echo "=== P-G  D2's Literal amendment: resolves_no_name answers False, so an untitled"
echo "         enum branch claims a name again and the geo-place pair refuses"
python3 -c "
import pathlib
p = pathlib.Path('codegen/lower/enum.py'); s = p.read_text()
old = '    if node.get(\"title\"):'
assert s.count(old) == 1
p.write_text(s.replace(old, '    return False  # PERTURBED\n' + old, 1))
"
run P-G "$MINE"; git checkout -- codegen/lower/enum.py

echo
echo "=== P-H  the widened DRY walk: lower_enum dropped from the module list, which is"
echo "         the exact blind spot this row would otherwise have left behind"
python3 -c "
import pathlib
p = pathlib.Path('tests/test_emit.py'); s = p.read_text()
old = '            (\"enum\", lower_enum),\n'
assert s.count(old) == 1
p.write_text(s.replace(old, '', 1))
"
run P-H "const_row_has_exactly_one_lowering"; restore

echo
echo "=== restored; working tree:"
git status --short "$T" "$U" codegen/lower/enum.py
