# The goal: the emitted surface is the deliverable, and it is verified by census

**DRIVE the SDK's public surface to the point where a downstream application can replace the
upstream `adcp` wheel with ours.** The compiler is done — every portable document of bundle 3.2
emits. What is not done is the surface a consumer touches: what the classes are called, which
module they live in, whether they are exported, and whether every name an application uses today
still resolves.

## What is a goal, and what is not

A goal is **observable in the emitted artifact**. A consumer can see it; a script can dump it.

A property of `codegen/` that no consumer can observe — how many lines `compiler.py` has, which
modules import it, how many `Refusal(` sites the walk mints — **is not a goal and must not be
gated.** It is a maintainability preference, done when it pays for itself. Encoding code shape as
tests freezes the shape, blocks refactoring, and proves nothing about correctness: there are
infinite ways to write the internals wrongly and enumerating them is not a strategy.

## The two instruments, and they are both censuses

**1. The MANIFEST.** One derived file listing every emitted class: its name, its module, the
domain it is re-exported from, whether it is in `__all__`, and the document and pointer it came
from. Dumped from the emitted tree, not written by hand. A diff of the manifest is the review
surface for every change to the surface — a rename, a move, a new export shows up as a line.

**2. The CROSS-CHECK against upstream.** Every name the upstream wheel exposes publicly, against
ours. For each: present, renamed (and to what), relocated (and where), or **missing**. Missing is
the finding.

Both are derived. Neither asserts anything about `codegen/`.

### What the cross-check may and may not conclude

Upstream's tree carries bundles 2.5, 3.0, 3.1, 3.1.0, 3.1.15, 3.2 and 3.2.0, plus eager,
ergonomic, forward-compat, partial, legacy and POC-alias layers, and **no provenance key** — so
which schema produced which of its classes cannot be recovered. Do not attempt a class-for-class
table over its internals; it would be a number nobody can defend.

**Compare the PUBLIC surface**, which is enumerable: what the package exports and what an
application imports. That is the set a migration has to satisfy.

**A MISSING COUNTERPART IS A QUESTION, NEVER AN INSTRUCTION TO ADD A CLASS (decided 2026-10-30).**
This is the rule the whole cross-check hangs on, and getting it wrong turns the exercise into
copying a thing we rewrote because it was wrong. Upstream is not the specification. The schema is.
So an upstream name with no class of ours is **unresolved until it carries one of two verdicts**:

- **WE REPRESENT IT DIFFERENTLY.** A schema node exists that we fold into another class rather
  than giving a class of its own. **This is not a defect by itself** — a fold is frequently the
  correct answer and the reason their count is higher. It splits three ways, and the verdict says
  which:
  - *the fold keeps every fact the schema states and is comfortable to use* — **we are right and
    their class is redundant.** No work. This is the expected outcome for most of them.
  - *the fold keeps every fact but is awkward for a caller* — a DX question, answered by an export
    or a name, never by splitting the class. Not a correctness fix.
  - *the fold loses something the schema states* — **our defect**, and the fix is in the walk.

  **The two checks already answer which of the three it is, and upstream's opinion is not
  consulted.** If the fold dropped a constraint, the schema admits a payload we refuse, or refuses
  one we accept, and the draw finds it. If it dropped nothing, there is nothing to find. So an
  upstream class is a prompt to go and look at a node; it is never the evidence about that node.
- **THEY EMIT A CLASS THAT SHOULD NOT EXIST.** Three shapes, and the verdict must say which: two
  of their classes carry the same schema node (a duplicate); the class is not schema-derived at
  all but belongs to one of their hand-written ergonomic, eager, forward-compat, partial, legacy
  or POC-alias layers; or it comes from a bundle version that is not 3.2. None of these is work
  for us — the first two are findings against them, and the third is outside the population.

Neither verdict may be reached by reading the two class definitions side by side. **Name the
schema node, or say there isn't one.** A count of unmatched names with no verdicts attached is not
a result, and "upstream has it so we should too" is the specific mistake this rule exists to stop.

**Upstream GROUNDS us; it does not correct us.** Its value is that it was built from the same
schemas, so a difference is a cheap pointer at a node worth a second look. That is the whole of its
authority. Where we and upstream disagree about a node, the schema decides, and the schema is
consulted by drawing values — not by reading their class.

**And the migration layer comes AFTER.** A set of aliases letting an application keep its current
import spellings is owed and will be built, but it is not this work and must not be allowed to
shape it: designing the classes to make the aliases easy is how upstream's mistakes get copied in
through the back door. Build the correct surface, then map onto it.

And parity is **one-directional**. Every name upstream exposes needs a counterpart in ours.
The reverse is not required: upstream duplicates classes and is believed wrong about unions, so a
smaller count on our side is expected and a surplus on theirs is a candidate finding against them.
Where the two represent one node differently, **the document decides, proved against
`Draft7Validator` payload by payload** — not by reading the two class definitions, and not by
treating upstream as an oracle.

## What the surface must satisfy

Each of these is observable, and each is currently false:

- **The domain surface exists.** §1 says a consumer writes `from adcp.types.core import
  PaginationRequest` and that the domain is derived from the document's own path.
  `adcp.types.<domain>` does not exist; `types/__init__.py` says "until then this is the package
  marker". Every consumer import today is the private `_schemas` path.
- **A class a union can return is reachable and named for what it is.** `__all__` in
  `core/requirements/asset_requirements.py` names the union base and none of its twelve branches,
  so a caller who receives an `AssetRequirements` cannot name the branch it got. Nineteen classes
  over six documents are named `…Branch<N>` — and the target's class name is already in their own
  base list (`class AssetRequirementsBranch7(AssetRequirements, JavaScriptAssetRequirements)`).
- **One import path per class.** `.111`: `core/vendor_pricing_option.py` binds five names to two
  classes each in one namespace.
- **Every name an application uses today resolves.** Aliases are expected and must be designed
  against §1's one-path rule rather than bolted beside it.

## The traps, each measured on this project

- **A docstring claiming a property is not evidence it holds.** Seven stale censuses were found in
  this code; several docstrings described a defect as a decision; one comment was "true by luck";
  `compiler.py` still promises a dissolution nobody owns.
- **A count in a docstring or a bead goes stale on the next merge. State the READING.**
- **A row's diagnosis is a hypothesis.** Six refusal sentences in this epic were factually wrong
  about their own documents. Re-measure before believing one, including from the owner.
- **A gate that passes when nothing happens is not a gate.** The two architecture steps that never
  landed were the ones whose only check was "the emitted tree does not change" — true of a no-op.
  A check must fail before the work and pass after, and be shown doing so.
- **Where the honest floor is not zero, record the floor with its shapes.** A ratchet set below the
  truth gets exempted later, which is how a guard stops guarding.
- **A fact is DROPPED, never SUBSTITUTED**, and a model may be wider than its document and never
  tighter. 120 declared approximations rest on that holding.

## Reporting

Report the manifest's counts and the cross-check's four buckets, with **every missing name listed
individually**. Never report M of N items as progress. The compiler's own figures — `emitted`,
`refused` with its deferred/verdict split, `accounted`, primary/chained off `Refusal.kind`, never
summed — must not move for a surface change; if one moves, say so first.
