#!/bin/bash
# Break "grading reads a fresh emit" on purpose, from both sides, and show WHAT reddens.
#
# `docs/plan/architecture.md` (2026-10-29): "Grading therefore reads the tree a fresh run
# emits. The committed tree is an ARTIFACT, verified by one byte-compare, and is never the
# subject." `tests/fresh.py` is the mechanism and `tests/conftest.py` is where it is
# applied, and neither has a verdict of its own -- every check in the suite is green with
# the two trees equal, which they are whenever the byte-compare is green. So without this
# script nothing says the arrangement could ever be red, and §9's rule applies: a rule
# nothing can break is a finding about the rule.
#
# THE CLAIM IS TWO-PART AND BOTH PARTS ARE MEASURED HERE:
#
#   1. COLLECTION STAYS WHOLE. The failure this row removed was not a red test, it was
#      2,442 tests that never ran: `graded()` is called at PARAMETRIZE time, so one
#      committed module that did not import collected ZERO tests from
#      `tests/test_emit.py` -- including the obligation that exists to report it. Every
#      case below therefore asserts the collection COUNT first, and a case that reddens a
#      test while erroring collection has not passed.
#
#   2. THE NAMED TEST REDDENS, and which one it is says which tree was read. Corrupt the
#      COMMITTED tree and only the byte-compare may move, because nothing else reads it.
#      Make the COMPILER emit a broken module and the import obligations move, because
#      that is the tree the grading reads.
#
# This is BANKED EVIDENCE and not a check: it is not collected by pytest, it is
# re-runnable, and the suite is what grades the arrangement. Each case names what it
# breaks and must print REDDENS beside a WHOLE collection.
#
#   ./perturb_fresh_grading.sh
#
# It edits files in place and restores them with `git checkout --`, so it REQUIRES A CLEAN
# TREE for the files it touches: uncommitted work in them is destroyed, and it refuses to
# run otherwise.
#
# CASE 2 IS SLOW BY CONSTRUCTION, ~3-6 minutes: perturbing `codegen/` moves
# `tests/compiled.py`'s key, which is the whole point of that key, so the bundle is
# recompiled and the tree rewritten. A cheap version of this case would be one that did
# not go through the compiler, and it would not be this case.
#
# A COLLECTION ERROR IS NOT A GREEN RUN -- `perturb_dump_exemptions.sh`'s header records
# the day that hole scored a perturbation that never ran as a guard that cannot redden.
# The verdict here matches "failed|error" for the same reason, and the collection count is
# asserted separately so an errored collection cannot read as a whole one.
set -u
cd "$(dirname "$0")" || exit 1

R=codegen/render.py
M=src/adcp/types/_schemas/a2ui/bound_value.py

if [ -n "$(git status --porcelain -- "$R" "$M")" ]; then
  echo "refusing to run: $R or $M has uncommitted changes, which this would destroy" >&2
  exit 1
fi

py() { env PYTHONPATH=.:src ./.venv/bin/python "$@"; }

# The whole collection, with the tree unperturbed: the number every case is compared
# against. Derived rather than written down, so a row that adds a test does not have to
# re-point this script.
WHOLE=$(py -m pytest tests/ --collect-only -q 2>&1 | grep -oE '[0-9]+ tests collected' | grep -oE '^[0-9]+')
if [ -z "${WHOLE:-}" ]; then
  echo "refusing to run: the unperturbed collection does not report a count" >&2
  exit 1
fi
printf 'unperturbed collection: %s tests\n\n' "$WHOLE"

# The collection verdict, and it has THREE values and not two. ERRORED is the failure this
# row removed: a module that raised while pytest was building a parametrize list, which
# takes whole files down and reports nothing about the module. A count BELOW the whole
# that errored nothing is not that failure and is not a defect -- a tree with one
# unimportable module carries fewer pairs, and a run with no tree at all carries none, so
# the parametrised items legitimately go with them. Only ERRORED is the regression, which
# is why the two are never collapsed into "not WHOLE".
collection_of() {
  out=$(py -m pytest tests/ --collect-only -q 2>&1)
  n=$(echo "$out" | grep -oE '[0-9]+ tests? collected' | grep -oE '^[0-9]+')
  if echo "$out" | grep -qE '[0-9]+ errors? (during collection|in )'; then
    echo "ERRORED (${n:-0} of $WHOLE)"
  elif [ "${n:-0}" = "$WHOLE" ]; then
    echo "whole ($WHOLE)"
  else
    echo "${n:-0} of $WHOLE, no error"
  fi
}

run() {  # run <label> <node id or -k expression> <files to restore...>
  label=$1; select=$2; shift 2
  collection=$(collection_of)
  out=$(py -m pytest $select -q 2>&1 | tail -3)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
  printf '%-52s %-12s collection %-24s %s\n' "$label" "$verdict" "$collection" \
    "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*' | head -1)"
  git checkout -- "$@"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

# --------------------------------------------------------------------------- #
# CASE 1. The COMMITTED tree carries a module that cannot be imported -- which is
# `adcp-client-python-10l.98`'s own shape, `TypeError: duplicate base class`, written into
# `src/` where that row found it. At the base of this row it collected 0 tests from
# `tests/test_emit.py` and errored ~2,442, because `graded()` imported `src/` at
# parametrize time. Nothing in the suite imports `src/` now, so the ONE test that may read
# it is the one that moves.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$M');s=p.read_text();a='class A2UIBoundValue(BranchDispatchMixin, AdCPBaseModel):';assert s.count(a)==1;p.write_text(s.replace(a,'class A2UIBoundValue(BranchDispatchMixin, AdCPBaseModel, BranchDispatchMixin):'))"
run "a COMMITTED module that cannot be imported" \
    "tests/test_emit.py::test_the_committed_tree_is_what_a_fresh_run_emits" "$M"

# And the same perturbation against the checks that read the FRESH tree: they must not
# notice it at all, which is the other half of "the committed tree is never the subject".
#
# Named node ids and not the two FILES, because `test_the_tree_imports.py` carries a
# failure that pre-exists this row -- `test_no_document_of_the_bundle_reaches_the_
# duplicate_base_guard` pins seven refusals where the compiler now has none -- and a case
# whose selection includes a test that was already red cannot tell a perturbation it
# caught from one it did not.
edit "import pathlib;p=pathlib.Path('$M');s=p.read_text();a='class A2UIBoundValue(BranchDispatchMixin, AdCPBaseModel):';assert s.count(a)==1;p.write_text(s.replace(a,'class A2UIBoundValue(BranchDispatchMixin, AdCPBaseModel, BranchDispatchMixin):'))"
run "  the same, against the FRESH-tree checks (STAYS GREEN)" \
    "tests/test_the_tree_imports.py::test_the_tree_the_whole_suite_grades_is_one_a_fresh_run_wrote \
     tests/test_the_tree_imports.py::test_every_module_a_fresh_run_emits_imports_and_every_class_of_it_is_defined \
     tests/test_emit.py::test_no_module_of_the_graded_tree_failed_to_import" "$M"

# --------------------------------------------------------------------------- #
# CASE 2. The COMPILER emits a module that cannot be imported. The guard at
# `ir.ClassDecl.__post_init__` refuses a duplicate in a declaration's base list, so this
# goes in at the RENDERER, one layer past it -- which is also what makes it a test of the
# grading rather than of the guard: the compile succeeds, the tree is written, and one
# module of it raises `TypeError: duplicate base class` on import.
#
# `a2ui/bound-value.json` because its root class is the one shape with a real base list of
# more than one name -- §4's union row, `(BranchDispatchMixin, AdCPBaseModel)` -- so the
# duplicate is the live defect's shape and not an invention.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$R');s=p.read_text();a='            for b in decl.bases\n';assert s.count(a)==1;p.write_text(s.replace(a,'            for b in ((*decl.bases, decl.bases[0]) if decl.bases and decl.ref is not None and decl.ref.document == \"a2ui/bound-value.json\" else decl.bases)\n'))"
run "the COMPILER emits an unimportable module" \
    "tests/test_the_tree_imports.py::test_every_module_a_fresh_run_emits_imports_and_every_class_of_it_is_defined tests/test_emit.py::test_no_module_of_the_graded_tree_failed_to_import" "$R"

# --------------------------------------------------------------------------- #
# CASE 3. No fresh tree at all: the compile RAISES. `tests/fresh.py` is imported from a
# conftest hook, so a raise there would error the collection of the whole suite. It records
# the reason instead and one named test reads it -- which is what the REDDENS below is.
#
# THE COLLECTION IS EXPECTED TO ERROR HERE AND THAT IS NOT THE DEFECT THIS ROW REMOVED.
# With the compiler not running there is no tree, and the four files that import a
# generated module at MODULE scope cannot be collected; pytest interrupts on a collection
# error, so the count collapses. `tests/fresh.py` argues the alternative and why it is
# worse: letting `src/` answer would keep the collection whole and grade a dozen checks
# against an artifact nothing produced. The failure this row removed is CASE 2 -- one
# unimportable module of 1,054 -- and that one errors nothing.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$R');s=p.read_text();a='def constraints_module(';assert s.count(a)==1;p.write_text(s.replace(a,'def constraints_module(*_perturbed, **__perturbed):\n    raise RuntimeError(\"perturbed: the compiler does not run\")\n\n\ndef _unreachable_constraints_module('))"
run "the compile RAISES: no fresh tree exists" \
    "tests/test_the_tree_imports.py::test_the_tree_the_whole_suite_grades_is_one_a_fresh_run_wrote" "$R"

git checkout -- "$R" "$M"
