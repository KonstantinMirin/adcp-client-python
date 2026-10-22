# Emit the AdCP SDK types from the schema bundle

Work the JSON schema, emit the files.

This tree is deliberately almost empty. It holds the bundle, one generic
grader, and the plan. Everything else is written by a step of the plan.

## What is here, and why only this

| | |
|---|---|
| `schemas/cache/3.2/` | 1,625 documents. The source of truth and the only input. |
| `codegen/harness.py` | Grades a (schema document, Python class) pair in both directions. Imports `jsonschema`, `hypothesis`, `hypothesis_jsonschema`, `pydantic` and **no sibling, no path, no filesystem, and no name from the vocabulary it is pointed at** — which is why it can grade output that does not exist yet. |
| `docs/plan/rebuild-plan.md` | Ten steps. The only work list. |
| `docs/plan/sdk-type-generation.md` | Design intent, P1–P13. Non-negotiable. |
| `docs/plan/defect-inventory.md` | The 21 verified defects in the *previous* generated output, each the named control of one step. |
| `docs/plan/spike/` | The worked Route B reference: 65 lines of emitter, 93 lines of emitted Python, graded green both directions by `grade.py b`. |

## What is deliberately absent

A previous attempt built 5,686 lines across eleven modules and emitted no type.
Its audit found six of seven findings MISSING and one WRONG. The two things that
made that possible are both absent here on purpose:

- **No adapter, and now no binding table either.** The old `adapter_adcp.py`
  encoded where a *previous* generated tree lived, how its modules were paired to
  documents by a `# filename:` header, and a binding census over it. It is the
  single file that kept pointing the harness at the generator being replaced,
  which is how a harness came to be green over the whole population while nothing
  was being generated. Step 1 removes the whole category: **every emitted class
  carries a `SchemaRef` on `__adcp_schema__`**, so `strict_validate` and the
  grader both read the pairing off the class and there is nothing to aim.

- **No naming or module-assignment layer.** Those were built upstream of the
  lowering, so "one node, one class" became "every node needs a name" and
  "refuse what you cannot derive" became "refuse the document for a node that
  should never have been a class" — 267 documents refused, 22 of 30 unnameable
  nodes manufactured by the rule rather than found in the bundle. Here each
  lowering names what it emits.

**`datamodel-code-generator` is present, and pinned (D10).** It was absent while
the route was still open; the plan's §1 settled it. Our walk decides the shape
and dmcg's pydantic-v2 MODEL layer renders the class — its parser never runs,
because the parser is the half that decides names and structure from a schema and
that is the half with the AdCP knowledge in it. The earlier comparison was
against driving the PARSER, which is a different and much larger thing. Driving
the model layer carries defaults, descriptions, constraints, aliases and the
import set for free; the renderer it replaced dropped 3 of 3 schema defaults and
all 142 property descriptions in the population it covered.

## The metric

**N = portable documents emitted by `codegen.emit` AND graded green by
`codegen.harness` against the schema the class itself names, on all three legs,
with `N + refused == 1,054` asserted and every refusal named by document,
pointer and keyword.**

N is **43** in this tree, over the 334 documents steps 1 and 2 name (85 leaf
objects, 249 referencing a property), with 331 refused. The third leg compares
each class's own `model_json_schema()` to its document and is what grades the
generated code: the two acceptance legs go through `strict_validate`, whose
schema half answers first, so a model with `Any` on every field passes both over
the same 75 instances a faithful one does.

## Getting started

```bash
uv sync --all-extras
# the worked reference, graded by the harness:
PYTHONPATH=. uv run --no-sync python docs/plan/spike/grade.py b
```

The emitter, over one document, which is the whole command (D9: the bundle
directory is an argument and there is no default):

```bash
PYTHONPATH=. uv run --no-sync python -m codegen.emit \
  --bundle schemas/cache/3.2 core/pagination-request.json
PYTHONPATH=. uv run --no-sync python -m pytest tests/test_emit.py
```

## Merging back

This is an orphan branch with no shared history, by design: an agent reading it
cannot be steered by code that a later measurement retired. The merge into
`sdk/generator-rebuild` happens once the metric is non-zero, and brings
`resolved_cache.py` and `node_graph.py` across at the step that first needs them
(step 2, the first cross-document `$ref`) rather than up front.
