# Emit the AdCP SDK types from the schema bundle

Work the JSON schema, emit the files.

This tree is deliberately almost empty. It holds the bundle, one generic
grader, and the plan. Everything else is written by a step of the plan.

## What is here, and why only this

| | |
|---|---|
| `schemas/cache/3.2/` | 1,625 documents. The source of truth and the only input. |
| `codegen/harness.py` | Grades a (schema document, Python class) pair in both directions. Imports `jsonschema`, `hypothesis`, `hypothesis_jsonschema`, `pydantic` and **no sibling, no path, no filesystem, and no name from the vocabulary it is pointed at** — which is why it can grade output that does not exist yet. |
| `docs/plan/rebuild-plan.md` | Eleven steps. The only work list. |
| `docs/plan/sdk-type-generation.md` | Design intent, P1–P13. Non-negotiable. |
| `docs/plan/defect-inventory.md` | The 21 verified defects in the *previous* generated output, each the named control of one step. |
| `docs/plan/spike/` | The worked Route B reference: 65 lines of emitter, 93 lines of emitted Python, graded green both directions by `grade.py b`. |

## What is deliberately absent

A previous attempt built 5,686 lines across eleven modules and emitted no type.
Its audit found six of seven findings MISSING and one WRONG. The two things that
made that possible are both absent here on purpose:

- **No adapter.** The old `adapter_adcp.py` encoded where a *previous* generated
  tree lived, how its modules were paired to documents by a `# filename:`
  header, and a binding census over it. It is the single file that kept pointing
  the harness at the generator being replaced, which is how a harness came to be
  green over the whole population while nothing was being generated. The step
  that first has a tree writes the adapter that points at **its own** output.

- **No naming or module-assignment layer.** Those were built upstream of the
  lowering, so "one node, one class" became "every node needs a name" and
  "refuse what you cannot derive" became "refuse the document for a node that
  should never have been a class" — 267 documents refused, 22 of 30 unnameable
  nodes manufactured by the rule rather than found in the bundle. Here each
  lowering names what it emits, and the emitter writes the binding table itself
  because it is the thing that knows.

Also absent: `datamodel-code-generator`. The route decision was measured, not
assumed — see the plan's §1. Driving its model layer cost 104 lines against 65,
39 of them pure conformance, and rendered a `mode='before'` validator that P12
rejects.

## The metric

**N = portable documents emitted by `codegen.emit` AND graded green by the
harness against the emitting document, both directions, with
`N + refused == 1,054` asserted and every refusal named.**

N is 0 in this tree. A missing emitter scores 0 — which the previous metric,
"the harness green over the full document population", did not, because it was
satisfied by grading the tree being deleted.

## Getting started

```bash
uv sync --all-extras
# the worked reference, graded by the harness:
PYTHONPATH=. uv run --no-sync python docs/plan/spike/grade.py b
```

Then step 1 of the plan: `core/pagination-request.json` end to end. It has no
`$ref` and no composition, so it needs neither resolution nor a node graph —
read the document, walk its properties, emit a class, grade it.

## Merging back

This is an orphan branch with no shared history, by design: an agent reading it
cannot be steered by code that a later measurement retired. The merge into
`sdk/generator-rebuild` happens once the metric is non-zero, and brings
`resolved_cache.py` and `node_graph.py` across at the step that first needs them
(step 2, the first cross-document `$ref`) rather than up front.
