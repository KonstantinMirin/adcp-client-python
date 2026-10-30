#!/bin/bash
# Break §14 step 6's gate on purpose, one case at a time -- including the collapse it
# is the gate FOR.
#
# `tests/test_type_checker.py` IS the test for the decision layer (§14 step 6: "The type
# checker is the test"), and §14 step 10 is what it has to catch: `decide` collapses to
# `Lowering`, and the sum type "is what turns every present deferral into a compile error
# the moment `Refusal` leaves the seam".  A gate that cannot redden proves none of that,
# and this one spent its life red for an unrelated reason -- so the first thing worth
# distrusting about it is whether its GREEN means anything.
#
# This is BANKED EVIDENCE and not a check: it is not collected by pytest, it is
# re-runnable, and `tests/test_type_checker.py` is what the suite grades.  Every case
# below names what it breaks and must print REDDENS.
#
#   ./perturb_seam.sh
#
# It edits files in place and restores them with `git checkout --`, so it REQUIRES A
# CLEAN TREE: uncommitted work in any of them is destroyed.  It refuses to run otherwise.
#
# **THE INVOCATION CARRIES PYTHONPATH=.:src AND THAT IS NOT COSMETIC.**  mypy's verdict
# over this tree DEPENDS on it: run without, `adcp` resolves through the shared .venv's
# editable .pth into whatever worktree installed it, and the checker reports 41 further
# errors in `codegen/harness.py` -- a module `[tool.mypy].files` does not name and this
# gate's own required-population test does not require.  Under the project's own
# invocation the reading is 0.  `./check`'s preamble carries the same warning for the
# same reason, and so does the bd memory on sibling worktrees.  A lane that measures this
# gate the other way will report a number that is about its PATH and not about this code.
#
# A COLLECTION ERROR IS NOT A GREEN RUN.  The verdict below matches "failed|error", for
# the reason `perturb_dump_exemptions.sh` records: a perturbation that leaves a
# SyntaxError never runs, and a scraper reading only "N failed" scores that as a guard
# that cannot redden -- the exact opposite of what it measured.
set -u
cd "$(dirname "$0")" || exit 1

T=tests/test_type_checker.py
C=codegen/compiler.py
D=codegen/lower/decide.py
E=codegen/emit.py
P=pyproject.toml

if [ -n "$(git status --porcelain -- "$T" "$C" "$D" "$E" "$P")" ]; then
  echo "refusing to run: one of $T $C $D $E $P has uncommitted changes" >&2
  exit 1
fi

py() { env PYTHONPATH=.:src ./.venv/bin/python "$@"; }

run() {  # run <label> <-k expression selecting the ONE test it should redden>
  out=$(py -m pytest "$T" -q -p no:randomly -k "$2" 2>&1 | tail -3)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)"; then verdict=REDDENS; else verdict="STAYED GREEN"; fi
  printf '%-58s %-12s %s\n' "$1" "$verdict" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*' | head -1)"
  git checkout -- "$T" "$C" "$D" "$E" "$P"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

echo "the gate, unperturbed:"
py -m pytest "$T" -q -p no:randomly 2>&1 | tail -1
echo

# --------------------------------------------------------------------------- #
# §14 STEP 10's OWN CASE: the seam collapsed where it is not yet total.
#
# This is the one the row is about.  Collapsing `decide`'s return to `ir.Decided`
# alone -- one annotation, no other edit -- makes every arm that can still hand back
# a `Refusal` a compile error.  That is "a deferral that no longer has anywhere to
# go", and it reddens the gate without anything else being touched.
#
# The error COUNT is the honest size of the first ring and not of the whole job: the
# handlers still answer `ir.Decided | Refusal`, so the checker can only see one ring
# at a time and the sites behind them appear as each ring in front is cleared.  That
# is exactly §2's claim about the sum type -- it is what FINDS them -- and it is also
# why no single measurement sizes the collapse up front.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$D');s=p.read_text();a='*, of_a_root_union: bool = False\n) -> ir.Decided | Refusal:';assert s.count(a)==1;p.write_text(s.replace(a,'*, of_a_root_union: bool = False\n) -> ir.Decided:'))"
run "the one dispatch collapsed to ir.Decided" "type_checks_clean"

edit "import pathlib;p=pathlib.Path('$C');s=p.read_text();a='    node: nodes.Node, mod: \"Module\", *, of_a_root_union: bool = False\n) -> ir.Decided | Refusal:';assert s.count(a)==1;p.write_text(s.replace(a,'    node: nodes.Node, mod: \"Module\", *, of_a_root_union: bool = False\n) -> ir.Decided:'))"
run "the walk's per-node entry collapsed to ir.Decided" "type_checks_clean"

# A deferral reintroduced at a seam that is ALREADY total.  The three edits land
# together: the signature says the function cannot refuse, the body refuses, and the
# kind is imported so that the ONE error is about the refusal and not about a name.  A
# reader's eye passes over that; the checker does not, and it says so in its own words:
#
#   codegen/lower/decide.py:79: error: Incompatible return value type
#       (got "Refusal", expected "Decided")  [return-value]
#
# which is distinguishable from the eleven ring errors beside it -- those read
# `got "Decided | Refusal"`, the arms that have not been converted yet, and this one
# reads `got "Refusal"`, a deferral minted where there is nowhere to put it.
edit "import pathlib;p=pathlib.Path('$D');s=p.read_text();a='*, of_a_root_union: bool = False\n) -> ir.Decided | Refusal:';assert s.count(a)==1;s=s.replace(a,'*, of_a_root_union: bool = False\n) -> ir.Decided:');k='from codegen.refusal import Refusal';assert s.count(k)==1;s=s.replace(k,'from codegen.refusal import Kind, Refusal');b='        case nodes.Null():\n            return scalars.null(node, mod)';assert s.count(b)==1;p.write_text(s.replace(b,'        case nodes.Null():\n            return Refusal(\"type\", node.pointer, \"a later row\", kind=Kind.DEFERRED)'))"
run "a DEFERRED minted into a seam with nowhere to put it" "type_checks_clean"

# --------------------------------------------------------------------------- #
# THE SIX ERRORS THE ROW CLEARED, one reintroduced.  The gate was red on these at
# 5207c796 -- 1 failed, 2 passed -- so this is the case that proves the green is this
# code's and not the checker's indifference.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$C');s=p.read_text();a='            reused = reuse[key]';assert s.count(a)==1;p.write_text(s.replace(a,'            held = reuse[key]').replace('            field_type = reused.type\n            is_distinct = reused.distinct','            field_type = held.type\n            is_distinct = held.distinct'))"
run "fields() binds an ir.Field onto the names tuple again" "type_checks_clean"

edit "import pathlib;p=pathlib.Path('$C');s=p.read_text();a='def _constraining(node: Mapping[str, Any]) -> dict[str, Any]:';assert s.count(a)==1;p.write_text(s.replace(a,'def _constraining(node: dict) -> dict:'))"
run "_constraining narrowed back to dict under a Mapping caller" "type_checks_clean"

edit "import pathlib;p=pathlib.Path('$C');s=p.read_text();a='        if not a_conjunct_declares_an_array((c.raw for c in conjuncts), mod.resolve_node):';assert s.count(a)==1;p.write_text(s.replace(a,'        if not a_conjunct_declares_an_array((c.raw for c in node.conjuncts), mod.resolve_node):'))"
run "node.conjuncts read off a nodes.Base again" "type_checks_clean"

edit "import pathlib;p=pathlib.Path('$E');s=p.read_text();a='        return {uri: node for uri, (_edge, node) in based_edges(document).items()}';assert s.count(a)==1;p.write_text(s.replace(a,'        return {\n            uri: node\n            for uri, (edge, _n) in based_edges(document).items()\n            if (node := _node_or_none(lowered[edge.target][2], edge.into)) is not None\n        }'))"
run "based_nodes indexes lowered by a str | None target again" "type_checks_clean"

# --------------------------------------------------------------------------- #
# THE TWO CONTROLS.  A checker with every error suppressed is green for free, and a
# checker over three files is green for free too, so the gate's other two tests are
# what make the first one mean anything.  Each is perturbed on its own terms.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$D');s=p.read_text();a='from codegen.schema import nodes';assert s.count(a)==1;p.write_text(s.replace(a,'from typing import cast\n\nfrom codegen.schema import nodes\n\n_ = cast(int, 1)'))"
run "a cast over the decision layer" "holds_no_suppression"

edit "import pathlib;p=pathlib.Path('$D');s=p.read_text();a='    match node:';assert s.count(a)==1;p.write_text(s.replace(a,'    _unused = node.pointer  # type: ignore[attr-defined]\n    match node:'))"
run "an inline type: ignore over the decision layer" "holds_no_suppression"

edit "import pathlib;p=pathlib.Path('$D');s=p.read_text();a='    match node:';assert s.count(a)==1;p.write_text(s.replace(a,'    assert isinstance(node, nodes.Base)\n    match node:'))"
run "an assert isinstance standing in for the branch" "holds_no_suppression"

edit "import pathlib;p=pathlib.Path('$P');s=p.read_text();a='    \"codegen/lower\",';assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "codegen/lower dropped from the graded population" "ranges_over_the_decision_layer"

edit "import pathlib;p=pathlib.Path('$P');s=p.read_text();a='    \"codegen/compiler.py\",';assert s.count(a)==1;p.write_text(s.replace(a,''))"
run "codegen/compiler.py dropped from the graded population" "ranges_over_the_decision_layer"
