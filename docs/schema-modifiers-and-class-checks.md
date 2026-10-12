# Schema modifiers and the class-level checks they become

A JSON Schema root says more than "here are my properties". It can say *one of these
combinations* (`anyOf`, `oneOf`), *if this field then that one* (`if`/`then`), *never these
two together* (`not`), *this field only alongside that one* (`dependencies`). A Python class
is a flat field set with per-field requiredness and cannot express any of them.

This document is the mapping: for each construct, what the generated class actually does
at validation time, what a refusal looks like, and what is **not** checked. It is a
description of today's behaviour, not a design proposal.

Counts here were measured on `integrate/8qela` at `3488ff9c3`. Where a number matters, the
command that produced it is named, because these move with every schema refresh.

**For how the tree is produced** — the pipeline, the pre-generation transforms, the
key-consuming reader, naming — see [`design/type-generation.md`](design/type-generation.md).
This document picks up where that one leaves off: what the emitted checks *do*.

## The one rule

| the root's branches | what is generated |
|---|---|
| partition by requiredness | one class per branch, a shared public base, the base dispatches to the branch a document satisfies |
| do not partition | a compiled `_require_schema_required_group` validator on the class |

Which side a root falls on is proved, not chosen: `scripts/schema_constraints.py`'s
`partitions_by_requiredness` requires the branches' required-field sets to be pairwise
disjoint in a way no document can satisfy two of, and `provably_disjoint` establishes it
from the branches themselves.

Populations today:

```
classes declaring _branch_models                19    (split roots, the public response
                                                       bases, and the canonical create request)
distinct branch classes                         49
generated modules with a compiled validator    215    git grep -l _require_schema_required_group
  of those, carrying a combinator refusal        43    git grep -l 'requires at least one of these field groups'
generated modules                             1083    git ls-files 'src/adcp/types/domains/**/*.py'
```

Count these with `git grep -l <pattern> <commit> -- src/adcp/types/domains/`, not with
`grep -r` over a working tree: `grep -r` matches `__pycache__/*.pyc` as well and returns
exactly double.

## `anyOf` / `oneOf` — branch classes

The root's public name stays a class. `BranchDispatchMixin`
(`src/adcp/types/_branch_dispatch.py`) gives the class that **declares** `_branch_models`
its branches' union as its core schema, so the name resolves to the branch a document
satisfies on every path pydantic validates through — by name, nested in another model, and
through a `TypeAdapter` — plus `__new__` for `Base(**data)`, which allocates before
validation and so cannot be reached by a schema at all.

Membership is a fact about the class, not a registration: `"_branch_models" in cls.__dict__`.
A branch inherits the method and must get its own shape back, and so must a refinement
declared elsewhere — which is why a subclass of a split root gets a flat schema rather than
the union. That non-inheritance is load-bearing in three places and should not be "tidied":
it was the defect in salesagent-8qela.76 (a subclass inherited none of the root's compiled
constraints), it is the protection in .69 (a canonical refinement cannot inherit a stub JSON
schema), and it is the only working mechanism for .90 (a throwaway subclass renders the
root's own object schema, self-contained).

### What a refusal reports

`_conditions.name_the_combinator` wraps the union and decides what the caller sees:

- **no branch satisfied its own requiredness** → one `PydanticCustomError` whose type is the
  root's combinator keyword (`anyOf`/`oneOf`), message `requires at least one of these field
  groups: <title> | <title>`, with the absent field names in the error context. The keyword
  matters: `core/error.json` requires every `issues[]` entry to carry a keyword from the JSON
  Schema vocabulary, and the `missing` pydantic reports by itself is not in it.
- **one branch got past its requiredness and failed on content** → that branch's errors, at
  **document paths**, with the union's choice label removed. A branch that refuses the shape
  at its own root — `missing` at depth one, or a whole-document error from `_c.absent`
  refusing a key it forbids — counts as not reached.

A union's `loc` is not a document path: pydantic prefixes the label of the choice that
produced each error. Dropping it is why `issues[].pointer` resolves against the buyer's
document (salesagent-8qela.22, .28).

### The hazard: a wrap collapses every label

The selector groups a union's errors by `loc[0]` to decide which branch was reached. That
assumes pydantic gives each choice a **distinct** label, which nothing guarantees. Measured
on two branches:

| branch schema | labels |
|---|---|
| plain | `['First', 'Second']` — distinct |
| after-validator only | `['function-after[f(), First]', 'function-after[f(), Second]']` — distinct |
| **wrap only** | `['function-wrap[f()]']` — **degenerate** |
| **after over wrap** | `['function-after[f(), function-wrap[f()]]']` — **degenerate** |

So **any wrap validator in a branch's schema collapses all of them to one label.** When that
happens the grouping carries no information, and `_errors_of_the_reached_branch` asks the
branches directly — for *selection only*, matching on `loc` alone, because a branch asked
directly answers in python mode (`model_attributes_type`) where the union parsing JSON says
`dict_type` at the same path. The reported errors still come from the union, in the caller's
input mode.

The same table is in `_conditions.py` beside that fallback. If you add a validator to a
branch class, check it against the table rather than against the one case that exposed this.

## `if` / `then` — a conditional binds only a carried key

The pin states a conditional consequent as `then: {"properties": {"x": {...}}}`, and
`properties` applies **only to an instance that carries the key**. An instance omitting `x`
satisfies the conditional vacuously.

Two schemas condition the response envelope's `status` on another field —
`protocol/sync-principal-response.json` and `protocol/get-principal-response.json`, both
`if result.kind == "failed" then status in ["failed","rejected"]`.

**A class-emitted default makes the key carried.** `_conditions.supplied` answers from
`model_fields_set` *and* from the serializer, because a default the class emits is on the
document just as a supplied value is — the two dumps are byte-identical, so a constraint
whose verdict differs between them would be grading something the wire cannot express.
`post_generate_fixes.fix_protocol_envelope_status_default` gives the envelope
`status = TaskStatus.completed` "for ergonomic construction" even though
`core/protocol-envelope.json` makes `status` required with no default, so a response built
without one carries `completed` — and the conditional then binds it. Before presence
included emitted defaults, such a document passed because the key read as absent.

So: **a default is not a free convenience on a field some conditional constrains.** Supply
the field, as `server/principal.py` does at both of its failed-result sites.

## `allOf` and root conjuncts — a compiled check

Everything a root states beyond its merged properties is compiled by
`scripts/compile_conditions.py` into one `model_validator(mode="after")` named
`_require_schema_required_group`, as an expression over the primitives in
`src/adcp/types/_conditions.py`. Two conventions run through all of them:

- **presence is what the document carries** — `model_fields_set` membership plus what the
  serializer emits; an explicit null is a supplied value, and on an AdCP 3.2 mutation input
  it is the command to clear;
- **every predicate is vacuous off-type** — JSON Schema applies a keyword only to instances
  of the type it grades, so a primitive handed the wrong shape returns `True`.

A conjunct's refusal names the schema file and the conjunct's **index**, plus the fields the
condition reads: `Product violates a constraint its schema states outside its properties
(core/product.json, root conjunct 0) over format_ids, format_options`. The field names come
from `compile_conditions.named_fields`, which walks the condition tree.

## `dependencies` — a root conjunct, and the source of a bound

`dependencies` / `dependentRequired` / `dependentSchemas` compile into root conjuncts like
any other root content. **27** per-domain pinned schemas carry one — including
`core/account.json`, `core/canvas-constraint.json` and `account/sync-accounts-request.json`.
`core/product.json` carries none, which matters for the next section.

## `_COMBINATOR_FIELDS` — what a consumer that filters a model must keep

A root combinator makes its fields *individually optional and collectively required*, which
per-field `is_required()` cannot express. So the generator declares them on the class:

```python
_COMBINATOR_FIELDS: ClassVar[frozenset[str]] = frozenset({'format_ids', 'format_options'})
```

A consumer that drops fields must keep these, or it produces a document the model refuses.
`get_products`' fields projection reads it for exactly that reason: it kept the seven
individually-required `Product` fields, dropped `format_options` as optional-and-unrequested,
and the re-validation then failed `core/product.json`'s own
`sent(format_ids) or sent(format_options)`.

**The name is the bound.** This is the combinator's fields, **not** the complete set a root
constraint can require. A disjunction with a negated presence arm —
`(not supplied(A)) or supplied(B)` — goes false when `B` is dropped and `A` is kept, and the
combinator never names those fields. That shape lives in the 27 schemas above and not in
`core/product.json`. The complete rule is "every field whose absence can flip a predicate",
which needs a polarity walk over the condition tree; if it is ever needed it arrives as a
second attribute without changing what this one means.

## `additionalProperties` — four states, not two

| where | policy |
|---|---|
| `AdCPBaseModel` | `ignore` — forward compatible by default |
| a schema that is open, or types `additionalProperties` | `allow` |
| a closed object schema | `forbid` |
| explicitly ignoring | `ignore` |

Measured over the 2674 generated model classes: `allow` 1196, `forbid` 997, `ignore` 400,
and 81 inheriting.

The policy decides where a branch's *forbids* can live. A branch class types a field it
forbids as `None`, which makes the combination a type error for a typed caller — but a raw
document needs more, and the reason is the `allow` tier rather than the `forbid` one: under
`extra="allow"` an undeclared key is filed under extras and accepted, and a *declared* one
arrives as a `None` the branch does not forbid at a nullable position. So the refusal is a
`mode="before"` validator, `_refuse_keys_this_shape_forbids`, calling `_c.absent` — which is
also why that refusal reaches a caller as a whole-document error rather than one at the
offending field, and why the branch selector above treats it as "this branch was never
reached".

## Two tiers: canonical and legacy

`adcp.types` exposes the **canonical** models — legacy creative identity absent from their
declared fields, JSON Schema and serialized output at every nesting depth. The
wire-faithful generated roots, which retain that identity through the AdCP 3.x transition,
are exposed from `adcp.types.legacy`.

This is why the public `CreativeManifest` and `CreativeAsset` are refinements rather than
the generated roots, and why moving one between tiers is an export change rather than a
design change. It is stated in `canonical_creative.py`'s module docstring; this is the only
other place it is written down.

## The advertised `inputSchema` is a different artifact from the pinned document

An MCP client reads a tool's `inputSchema`, and that projection has its **own** contract:
`_model_to_json_schema` in `src/adcp/server/mcp_tools.py` requires an unconditional object
root, because a discovery client has to render a form.
`tests/test_mcp_schema_drift.py::test_every_input_discovery_schema_has_unconditional_object_root`
asserts it.

The pinned document is not that shape: `media-buy/create-media-buy-request.json` carries
`properties`, `required`, `anyOf` **and** `allOf` together at its root. So a pin-faithful
projection is exactly what the advertised-schema guard refuses, and "match the pin" is the
wrong instruction for this function.

For a split root the advertised schema is therefore built from what the union already
carries: each branch's `$defs` entry is a complete object schema, so properties are unioned
and `required` is intersected, and a field's declaration is the union of its branches' —
sound because a branch only ever *narrows*. Taking the first branch's declaration instead
advertises one branch's narrowing as the contract of all of them. The result is permissive
about *which* branch a document must satisfy, deliberately: the advertised schema's job is
to let a client build a candidate, and the server's job is to refuse a wrong one. The
branches are still enforced on arrival.

## What nothing checks

**No grader compares `model_json_schema()` against the pinned document — anywhere.**
`test_mcp_schema_drift` compares a tool's advertised schema to `model_json_schema()`, model
against model. `tests/conformance/test_schema_model_parity.py` grades accept/refuse verdicts
on synthesized documents, not the schema's own shape. The three suites that read both a
pinned file and call `model_json_schema()` — `test_code_generation`, `test_rc6_adoption`,
`test_version_scoped_models` — assert on individual properties, not on the document.

A reviewer who does not know this will assume the generated schema is checked against the
pin. It is not. Four divergences follow from that, all open as salesagent-8qela.90:

- `allOf` is dropped from a split root's generated schema entirely, so a root's conditional
  rules are not expressed in it (they *are* enforced at runtime by the compiled validator —
  this is a documentation divergence, not a validation one);
- the `anyOf` branches lose the inline `not` the pin states for each;
- `brand/verify-brand-claim-request.json` is a `oneOf` with a `discriminator` in the pin and
  an `anyOf` without one in the generated schema. `anyOf` accepts a document satisfying two
  branches where `oneOf` refuses it, so the generated schema is **weaker** than the protocol
  states — sound only because the branches are pairwise disjoint, and that proof lives in
  the generator rather than in the emitted document;
- `discriminator` and `dependencies` are dropped.

A guard comparing the two documents per split root — top-level keyword sets, properties,
`required`, and the combinator keyword — would have caught all four at once.

## Known gaps, by bead

| gap | bead |
|---|---|
| a split root's generated JSON schema diverges from the pin in four ways, and nothing grades it | salesagent-8qela.90 |
| a generated root requires keys its schema root does not, masking the combinator refusal | salesagent-8qela.80 |
| a genuine union's generated member name reaches `error.field` | salesagent-8qela.46 |
| a compiled refusal's keyword outside the JSON Schema vocabulary | salesagent-8qela.94 |
