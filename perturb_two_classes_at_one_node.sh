#!/bin/bash
# Make THE EMITTER declare two classes at one schema node, and measure which gate sees it.
#
# `docs/plan/final-state.md` reading 4: "a type stated at more than one position is written
# once and referenced, never restated".  `adcp-client-python-qpzf` reported that defect over
# 17 `(document, pointer)` pairs carrying 35 classes and the report was a NAME count -- every
# one of the 17 nodes carries ONE class object under two or three names, which is
# `lower/names.adopt`'s own clause working ("one class, as many names as the node has
# positions").  So the state the bead describes has never existed in this tree, and the thing
# worth distrusting is whether anything WOULD SEE IT if it did.
#
# `tests/test_one_node_is_one_declaration.py` answers that, and the answer before
# `test_one_schema_node_is_declared_by_at_most_one_class` was NO: both gates there group by
# the five-part key, and two classes at one node that state different content are SEPARATED
# by part 1 of it.  The clause was missing, not merely unexercised.
#
# A SOURCE-SIDE PERTURBATION WOULD PROVE NOTHING HERE.  Two of them on this project read
# green and were discarded as worthless gates, and the reason is structural: the gates range
# over the tree a fresh run EMITS (`tests/fresh.py`), so the only input that can move them is
# the compiler.  Every case below edits `codegen/` and nothing else.
#
# This is BANKED EVIDENCE and not a check: it is not collected by pytest, it is re-runnable,
# and `tests/test_one_node_is_one_declaration.py` is what the suite grades.
#
#   ./perturb_two_classes_at_one_node.sh
#
# It edits files in place and restores them with `git checkout --`, so it REQUIRES A CLEAN
# TREE: uncommitted work in those files is destroyed.  It refuses to run otherwise.
#
# **EVERY CASE IS THREE VERDICTS AND THAT IS THE POINT.**  A clause that reddens where an
# existing one also reddens is a second spelling of it and buys nothing.  So each perturbation
# is run against all three readings and every verdict is printed:
#
#   case A -- the wrong reference handed to a declaration, i.e. two classes at ONE node:
#             node gate REDDENS, key gate STAYS GREEN.
#   case B -- §4's content dedup off, i.e. a second class at a SECOND node and no aliases at
#             all: node gate STAYS GREEN, key gate REDDENS.
#
# **THE SWAP IN THE FIRST AND LAST COLUMNS IS THE WHOLE MEASUREMENT.**  Case A is the defect
# reading 4 names and the key gate does not see it; case B is the defect the key gate exists
# for and the node gate does not see it.  Neither is a spelling of the other, and that is what
# could not be established by running one of them.
#
# The MIDDLE column reddens on both and is not a discriminator, by construction: the name
# reading hands the same function a SUPERSET of the gate's population, so anything that
# reddens the gate reddens it too.  What it adds is the other direction -- case B emits no
# aliases at all, so its 17-node population is gone and `claimed` fires rather than passing
# vacuously.  That is why it is a test of its own and not a clause inside the gate: its red
# direction is the emitter STOPPING, which is the opposite defect, and one test holding both
# reddens on either without saying which.
#
# **PYTHONPATH=.:src IS NOT COSMETIC.**  PYTHONPATH=. alone resolves `adcp` through the shared
# .venv's editable .pth into whatever worktree installed it, which grades a mix of two trees.
# `./check`'s own preamble carries the same warning.
#
# A COLLECTION ERROR IS NOT A GREEN RUN, which is why the verdict matches "failed|error":
# a perturbation that leaves a SyntaxError never runs, and a reader scoring only "N failed"
# would read that as a guard that cannot redden -- the opposite of what it measured.
set -u
cd "$(dirname "$0")" || exit 1

T=tests/test_one_node_is_one_declaration.py
O=codegen/lower/objects.py
N=codegen/lower/names.py

NODE_GATE="one_schema_node_is_declared_by_at_most_one_class"
NAME_READING="a_second_name_at_a_node_is_not_a_second_declaration"
KEY_GATE="no_two_declarations_of_one_document_are_one_type"

if [ -n "$(git status --porcelain -- "$T" "$O" "$N")" ]; then
  echo "refusing to run: one of $T $O $N has uncommitted changes" >&2
  exit 1
fi

py() { env PYTHONPATH=.:src ./.venv/bin/python "$@"; }

one() {  # one <label> <-k expression> -> prints "REDDENS" or "STAYED GREEN" and the count
  out=$(py -m pytest "$T" -q -p no:randomly -k "$2" 2>&1 | tail -3)
  if echo "$out" | grep -qE "[0-9]+ (failed|error)"; then v=REDDENS; else v="STAYED GREEN"; fi
  printf '    %-14s %-12s %s\n' "$1" "$v" "$(echo "$out" | grep -oE '[0-9]+ (passed|failed|error).*' | head -1)"
}

all_three() {
  one "node gate" "$NODE_GATE"
  one "name reading" "$NAME_READING"
  one "key gate" "$KEY_GATE"
}

under() {  # under <label>
  printf '%s\n' "$1"
  all_three
  git checkout -- "$T" "$O" "$N"
}

edit() { py -c "$1" || { echo "perturbation did not apply: $1" >&2; exit 1; }; }

echo "unperturbed, all three:"
all_three
echo

# --------------------------------------------------------------------------- #
# CASE A: the reference handed to the WRONG declaration, which is the state the bead
# describes -- two classes at one `(document, pointer)`.
#
# `declare_object` writes `ref=schema_ref(mod.document, pointer)` on every object class, so
# a home or a relocation that derived the wrong pointer looks exactly like this: the class is
# DECLARED at its own node (which is what `Module.declare`'s collision arm guards) and
# CARRIES another node's reference, which nothing guarded.  The two adagents branches it
# collides are `authorized_agents/items/oneOf/0` and `/oneOf/1` -- the six branches
# `adcp-client-python-qpzf` named -- and they state DIFFERENT properties, so the pair is one
# node and two types.  That is what the key gate cannot see.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$O');s=p.read_text();a='        ref=compiler.schema_ref(mod.document, pointer),';assert s.count(a)==1;p.write_text(s.replace(a,'''        ref=compiler.schema_ref(
            mod.document,
            pointer[: -len(\"/oneOf/1\")] + \"/oneOf/0\"
            if mod.document == \"adagents.json\"
            and pointer.endswith(\"/properties/authorized_agents/items/oneOf/1\")
            else pointer,
        ),'''))"
under "A. the adagents oneOf/1 branch carries its oneOf/0 sibling's reference"

# --------------------------------------------------------------------------- #
# CASE B: THE CONTROL, and it is the other direction of the same 2x2.  §4's content dedup
# switched off at its memo lookup: the second occurrence of a node is lowered again and
# declares its own class at ITS OWN pointer, so the tree gains a second class at a SECOND
# node of the same document.  That is the key gate's defect and not this clause's, and the
# verdicts must swap.  `lower/names.adopt`'s docstring names the failure this is:
# `WholesaleFeedEvent1` through `WholesaleFeedEvent9` in the upstream v9 SDK.
# --------------------------------------------------------------------------- #
edit "import pathlib;p=pathlib.Path('$N');s=p.read_text();a='    return next((at for other, at in mod.collapsed if other == node), None)';assert s.count(a)==1;p.write_text(s.replace(a,'    return None  # PERTURBED: section 4 content dedup off'))"
under "B. section 4's content dedup switched off (a second class at a second node)"
