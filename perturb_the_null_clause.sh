#!/bin/bash
# Break every guard over reading 1's two new clauses on purpose, one at a time.
#
# The clauses:
#
#   * for every emitted field that is optional and whose document property does not
#     admit `null`, `model_validate` with that key set to an explicit `null` must
#     REFUSE -- not merely `strict_validate` (`adcp-client-python-4yhb`);
#   * reading 1 at a BRANCH pointer is measured against the conjunction the class
#     enforces, never the bare fragment (`adcp-client-python-0ejo`).
#
# Both were unstated, and the cost of the first was the whole model half of the tree:
# 13,790 of the 13,961 graded optional fields admitted a value their own document
# refuses, in 1,819 classes, declared nowhere -- and the instrument that should have
# said so DREW NO EXPLICIT NULL at a declared property, so the column read green.
#
# THE PERTURBATION IS IN THE PRODUCER AND NEVER IN THE EMITTED TREE. Two source-side
# perturbations in this project read GREEN and were discarded as worthless, because
# `tests/fresh.py` emits the tree the suite grades: an edit to `src/adcp/types/_schemas`
# is overwritten before a single assertion runs. So every case below edits
# `codegen/render.py`, `codegen/ir.py`, `codegen/harness.py` or
# `src/adcp/types/_base.py` -- the four files that DECIDE the emitted text and the
# comparand -- and the fresh emission then carries the perturbation.
#
# This is BANKED EVIDENCE and not a check: it is not collected by pytest, it is
# re-runnable, and the three test files named below are what the suite grades. Every
# case names what it breaks and must print REDDENS.
#
#   ./perturb_the_null_clause.sh
#
# It edits the four files in place and restores them with `git checkout --`, so it
# REQUIRES A CLEAN TREE: uncommitted work in any of them is destroyed. It refuses to
# run otherwise.
#
# THE VERDICT IS KEYED ON THE RUN'S OWN JUNIT REPORT AND NEVER ON ITS PROSE, which is
# `perturb_dump_exemptions.sh`'s measured rule and the reasoning is its header's: a
# scraper over "N failed" cannot tell a run that never happened from a run that passed,
# and neither can pytest's exit code -- a SyntaxError in a test file collects nothing and
# exits 1, the same code a real failure exits with. The junit report COUNTS the three
# outcomes separately, so:
#
#   no report file       NOT RUN         (the process died before it could write one)
#   errors > 0           NOT RUN         (collected nothing, or a fixture blew up)
#   tests == 0           NOTHING COLLECTED (a defect in the case's own -k, not evidence)
#   failures > 0         REDDENS
#   otherwise            STAYED GREEN
#
# The last two cases are the CONTROL: the clean tree scores STAYED GREEN, and a
# SyntaxError in a test file scores NOT RUN.
set -u
cd "$(dirname "$0")" || exit 1

R=codegen/render.py
I=codegen/ir.py
H=codegen/harness.py
B=src/adcp/types/_base.py
TE=tests/test_emit.py
TR=tests/test_refuses_check.py
TA=tests/test_applied_schema.py
OUT=/tmp/perturb_the_null_clause.out
XML=/tmp/perturb_the_null_clause.xml

if [ -n "$(git status --porcelain -- "$R" "$I" "$H" "$B" "$TE" "$TR" "$TA")" ]; then
  echo "refusing to run: one of the perturbed files has uncommitted changes" >&2
  exit 1
fi

py() { env PYTHONPATH=.:src ./.venv/bin/python "$@"; }

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
counts = ' '.join(f'{k}={v}' for k, v in n.items())
if n['errors']:
    print(f'NOT RUN|{counts}')
elif not n['tests']:
    print(f'NOTHING COLLECTED|{counts}')
elif n['failures']:
    print(f'REDDENS|{counts}')
else:
    print(f'STAYED GREEN|{counts}')
"
}

run() {  # run <label> <test file> <-k expression>
  rm -f "$XML"
  py -m pytest "$2" -q -n 4 -p no:randomly -k "$3" --junitxml="$XML" >"$OUT" 2>&1
  rc=$?
  read=$(read_report)
  printf '%-62s %-18s rc=%-3s %s\n' "$1" "${read%%|*}" "$rc" "${read#*|}"
  git checkout -- "$R" "$I" "$H" "$B" "$TE" "$TR" "$TA"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

CLAUSE="every_optional_field_refuses_an_explicit_null"
WITNESS="the_explicit_null_witness_is_derived"
BRANCH="a_branch_pointer_is_the_base_and_the_branch"

# --------------------------------------------------------------------------- #
# the EMITTER's decision: which fields take the marker
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$R');s=p.read_text();a='omits_null=not decided.required and not ir.admits_null(decided.type),';assert s.count(a)==1;p.write_text(s.replace(a,'omits_null=False,'))"
run "the emitter never writes the marker (the defect itself)" "$TE" "$CLAUSE"

edit "import pathlib;p=pathlib.Path('$R');s=p.read_text();a='omits_null=not decided.required and not ir.admits_null(decided.type),';assert s.count(a)==1;p.write_text(s.replace(a,'omits_null=not decided.required,'))"
run "the marker on EVERY optional: a narrowing at the 171" "$TE" "$CLAUSE"

edit "import pathlib;p=pathlib.Path('$R');s=p.read_text();a='omits_null=not decided.required and not ir.admits_null(decided.type),';assert s.count(a)==1;p.write_text(s.replace(a,'omits_null=not ir.admits_null(decided.type),'))"
run "a REQUIRED field takes the marker too" "$TE" "$CLAUSE"

edit "import pathlib;p=pathlib.Path('$I');s=p.read_text();a='    return decided.container == \"union\" and any(admits_null(arm) for arm in decided.of)';assert s.count(a)==1;p.write_text(s.replace(a,'    return any(admits_null(arm) for arm in decided.of)'))"
run "admits_null descends a list: a nullable ELEMENT read as the field" "$TE" "$CLAUSE"

# --------------------------------------------------------------------------- #
# the RENDERING: the marker has to reach the annotation by BOTH of the pinned
# generator's two paths. With only the `annotated` property overridden the rendered
# class body carried no marker at all, which is why both are written and both here.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$R');s=p.read_text();a='        return assignment, self._marked(plan.rendered or \"\")';assert s.count(a)==1;p.write_text(s.replace(a,'        return assignment, annotated'))"
run "the built-in template's path stops writing the marker" "$TE" "$CLAUSE"

# `_marked` writing NO marker is not one of these: `parts` goes empty for a field with no
# `Field(...)` call, the module renders `Annotated[int | None, ]`, and the fresh emission
# does not parse -- a crash, which this script's own doctrine says is not evidence about a
# guard. The shape that DOES produce a tree is the marker reaching only the fields the
# layer already annotates, which is a subset of the right set.
edit "import pathlib;p=pathlib.Path('$R');s=p.read_text();a='        return self.omits_null and not self.is_class_var and self.use_annotated';assert s.count(a)==1;p.write_text(s.replace(a,'        return self.omits_null and not self.is_class_var and bool(str(self))'))"
run "the marker reaches only the fields the layer annotates" "$TE" "$CLAUSE"

# --------------------------------------------------------------------------- #
# the RUNTIME's two halves
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$B');s=p.read_text();a='    kind = schema[\"type\"]\n    if kind == \"nullable\":\n        return schema[\"schema\"]';assert s.count(a)==1;p.write_text(s.replace(a,'    kind = schema[\"type\"]\n    if False and kind == \"nullable\":\n        return schema[\"schema\"]'))"
run "the VALIDATION half: the null arm is not struck" "$TE" "$CLAUSE"

edit "import pathlib;p=pathlib.Path('$B');s=p.read_text();a='def _is_absent(value: Any) -> bool:\n    \"\"\"';assert s.count(a)==1;p.write_text(s.replace(a,'def _is_absent(value: Any) -> bool:\n    return False\n    \"\"\"'))"
run "the SERIALISATION half: exclude_if never fires" "$TE" "$CLAUSE"

# --------------------------------------------------------------------------- #
# the INSTRUMENT: the witness that found the defect, and the walk it reads keys off
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='        for key in declared_keys(schema):';assert s.count(a)==1;p.write_text(s.replace(a,'        for key in ():'))"
run "refused_witnesses draws no explicit null (the blind column)" "$TR" "$WITNESS"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='                {**instance, key: None},';assert s.count(a)==1;p.write_text(s.replace(a,'                {**instance, key: 1},'))"
run "the witness is not a null: the derivation stops naming the fact" "$TR" "$WITNESS"

edit "import pathlib;p=pathlib.Path('$H');s=p.read_text();a='    conjuncts = schema.get(\"allOf\")\n    if isinstance(conjuncts, list):\n        for conjunct in conjuncts:\n            for key, subs in property_declarations(conjunct, depth + 1, branches=branches).items():';assert s.count(a)==1;p.write_text(s.replace(a,'    conjuncts = ()\n    if isinstance(conjuncts, list):\n        for conjunct in conjuncts:\n            for key, subs in property_declarations(conjunct, depth + 1, branches=branches).items():'))"
run "property_declarations stops folding the allOf conjuncts" "$TE" "$CLAUSE"

# --------------------------------------------------------------------------- #
# the BRANCH COMPARAND (adcp-client-python-0ejo)
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$B');s=p.read_text();a='SAME_INSTANCE_RULES = (\n    \"if\",';assert s.count(a)==1;p.write_text(s.replace(a,'SAME_INSTANCE_RULES = (\n    \"_perturbed_away\",'))"
run "the base's rule keywords stop reaching the branch node" "$TA" "$BRANCH"

edit "import pathlib;p=pathlib.Path('$B');s=p.read_text();a='        if through in (\"anyOf\", \"oneOf\")';assert s.count(a)==1;p.write_text(s.replace(a,'        if through in (\"anyOf\", \"oneOf\", \"allOf\", \"then\", \"else\")'))"
run "the rules reach every same-instance hop, not only a branch" "$TA" "$BRANCH"

edit "import pathlib;p=pathlib.Path('$B');s=p.read_text();a='    for keyword in assembling:\n        if keyword not in node:\n            continue';assert s.count(a)==1;p.write_text(s.replace(a,'    own = {k: v for k, v in node.items() if k not in _ANNOTATES_THE_POINTER_THAT_STATES_IT}\n    for keyword in assembling:\n        if keyword not in node:\n            continue'))"
run "the conjunct is the whole base node: its union keyword re-asked" "$TA" "$BRANCH"

# --------------------------------------------------------------------------- #
# the CONTROLS
# --------------------------------------------------------------------------- #
run "the clean tree, the clause  (expected: STAYED GREEN)" "$TE" "$CLAUSE"
run "the clean tree, the witness (expected: STAYED GREEN)" "$TR" "$WITNESS"
run "the clean tree, the branch  (expected: STAYED GREEN)" "$TA" "$BRANCH"

edit "import pathlib;p=pathlib.Path('$TR');s=p.read_text();p.write_text('def (\n'+s)"
run "a SyntaxError in the test file (expected: NOT RUN)" "$TR" "$WITNESS"
