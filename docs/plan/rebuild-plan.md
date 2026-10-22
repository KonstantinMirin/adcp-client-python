# Rebuild plan: walk the schema, let the compiler emit the class

## 0. The one place

`docs/plan/sdk-type-generation.md` is the design, P1–P13, and it is binding. This plan is
subordinate to it. Where the two disagree, the design wins and this file is wrong.

The previous revision of this plan declared the design binding on line 6 and voided P11 on
line 10. That is the error this rewrite exists to correct, and the rule that prevents a
repeat: **a plan may not retire a principle. It may only say how a principle is discharged.**
A measurement that appears to contradict a principle is reported and stopped on.

## 1. The split

Two halves, one seam, and the seam is a decision rather than a translation.

**We walk the JSON Schema.** Read the document, resolve references, collapse identical nodes,
decide what each node IS — a class, an annotation, a member of an enumeration, a rule — and
decide its name. Every judgement about the bundle lives here. This half is ours because it is
domain knowledge about AdCP's schemas and no library has it.

**`datamodel-code-generator` emits the class.** Once the walk has decided "a class with these
fields, these constraints, these defaults, this base", it hands that to dmcg's pydantic-v2
model layer and dmcg writes the Python. P11 names it the compiler, and it is.

```
schema document -> our walk -> a decided shape -> dmcg's model layer -> Python
                   (ours)                         (the compiler)
```

**dmcg's parser never runs.** The parser is the half that decides names and structure from a
schema, and that is our half. Driving the parser is what made the previous route comparison
expensive; driving the model layer is ~25 lines and carries defaults, descriptions and
constraints for free.

### How the compiler is driven, and the two gates

`datamodel_code_generator.model.pydantic_v2.BaseModel(reference=..., fields=[...],
base_classes=[], custom_base_class="adcp.types._base.AdCPBaseModel", description=...)`, then
`.render()`. Fields are `DataModelField(name=, data_type=, required=, default=, has_default=,
constraints=, extras=)`.

Two gates, both silent, both measured. Neither is a reason to avoid the compiler; they are how
it is driven:

1. **Constraints are spelled in JSON Schema, not pydantic.** `ConstraintsBase` declares every
   field under its JSON-Schema alias with no `populate_by_name`, so `Constraints(ge=1, le=100)`
   sets nothing — empty `model_fields_set`, empty dump. `Constraints(minimum=1, maximum=100)`
   renders `Field(ge=1, le=100)`. The previous revision of this plan recorded this gate at its
   line 32 and cited it as a cost of the route; it is the instruction for using the route, and
   the cost was paid once, by finding it.
2. **`extras` cannot carry a constraint.** `_EXCLUDE_FIELD_KEYS` strips `gt ge lt le
   multiple_of min_length max_length pattern` out of `extras`. Constraints go through
   `constraints=`, in JSON-Schema spelling, and nowhere else.

### What the compiler cannot express

Measured, so a step does not discover it late:

- **A constrained container as a mapping value.** A nested scalar carries its bound
  (`Dict[str, conint(ge=1, le=100)]` renders), a nested container does not: `DataType` has no
  `constraints` field and `min_items` on an array value is dropped to `List[Any]`. A
  field-level `Field(min_length=1)` there bounds the dict's key count, which is a different
  keyword on a different node. **A constrained container value gets its own symbol**, and the
  mapping names it — then the constraint sits on a declaration the compiler does express.
  53 documents use the construct.
- **A module-level statement beside an alias.** No alias template has a slot for a sibling
  line, so a module that needs one is written by our module writer around the compiler's
  output.
- **A union discriminated by requiredness.** `DataType.discriminator` renders
  `Annotated[A | B, Field(discriminator='type')]` and is sound on 63 of 156 union roots. The
  rest stay plain unions; requiredness has no expression in the compiler and is a rule (D5).

## 2. The architecture

Every emitted class inherits `AdCPBaseModel` and **carries a reference to the schema that
generated it**. That one fact makes both the runtime contract and the test instrument generic,
and it deletes the indirection that caused this project's two worst failures.

```python
class PaginationRequest(AdCPBaseModel):
    __adcp_schema__: ClassVar[SchemaRef] = SchemaRef("core/pagination-request.json", "#")
    max_results: Annotated[int | None, Field(description="...", ge=1, le=100)] = 50
    cursor: Annotated[str | None, Field(description="...")] = None
```

- **`strict_validate` is generic**, on the base, once: read `cls.__adcp_schema__`, validate the
  payload against that schema, then construct through `model_validate`. It already is generic;
  what changes is where it finds the schema.
- **The harness is generic**: take a class, read `__adcp_schema__`, grade the class against
  that document. No adapter, no module header, no binding table, no name-keyed lookup.
- **There is no `codegen/adapter.py`.** The pairing is intrinsic to the class. The previous
  attempt's harness was pointed at a tree it had not emitted by exactly such an adapter; a
  class that carries its own schema cannot be aimed at someone else's output.
- **`_bindings.json` goes**, with `_documents()`, `_document_at`, `_document_of` and the
  `lru_cache` whose ceiling the base class already documents. A class with no
  `__adcp_schema__` cannot be constructed by the emitter, so the "bound to no document" refusal
  has no site.

`SchemaRef` is the document path plus a JSON pointer, because a nested class is a subschema of
its document and must grade against its own node rather than the whole file.

## 3. Decisions

Fixed before step 1. A step that wants to re-decide one reports it and stops.

- **D1 — the module is the document path.** `core/date-range.json` →
  `src/adcp/types/_schemas/core/date_range.py`. P8 makes `_schemas/` private, so the path is
  never a contract; the public surface is generated in step 8.
- **D2 — what becomes a class.** An object with `properties` → a model; an `enum` node →
  `StrEnum`/`IntEnum`; a `oneOf`/`anyOf` → a base plus one subclass per branch plus a union
  alias. Nothing else: scalar → an annotation, array → `list[X]`, typed
  `additionalProperties` → `dict[str, X]`, `const` → `Literal`, typeless → `Any`, and
  `required`-only / `not` / conditional / `dependencies` / `min`/`maxProperties` /
  `uniqueItems` → a rule on the nearest class. A root array → `RootModel[list[X]]`; a root
  scalar or mapping → a module-level alias. P2.
- **D3 — names.** Root: `pascal_case(title)`, keeping acronyms. Nested: parent +
  `pascal_case(property)`. Union branch: title → discriminator `const` → sorted required set →
  refuse by document and pointer. Identical nodes (same content, two URIs) are one node, and
  content equality is the only dedup. The name is an INPUT to a lowering, never computed
  inside one. P1, P5.
- **D4 — the schema decides acceptance.** An optional renders plain, with its default.
  `strict_validate` validates against the class's own schema, then constructs. A schema
  refusal raises pydantic's `ValidationError` with the keyword as `type`. `model_validate`
  stays public and constructs without consulting the schema. Discharges P12's obligation.
- **D5 — rules are after-validators, hand-written once** in `src/adcp/types/_runtime.py`,
  reading a class-level tuple the emitter writes. A rule narrows the constructor; acceptance
  stays with the schema half.
- **D6 — bases are derived.** An `allOf` of `$ref`s makes those classes the bases. No
  marker-class policy keyed on filenames; anything a caller wants to `isinstance` against is a
  schema the document composes.
- **D7 — `extra` is derived.** `false` → `forbid`, `true` → `allow`, absent → the base
  default, typed → `allow` with a typed `__pydantic_extra__` (a compiler feature).
- **D8 — no patch pass.** The committed tree is byte-compared to a fresh run. A defect is
  fixed in our walk, in the compiler's configuration, or in a compiler extension — P11's
  layers, earliest that reaches it — and nothing rewrites output.
- **D9 — the bundle directory is an argument.** `python -m codegen.emit --bundle <dir>`. No
  version literal in `codegen/`.
- **D10 — the compiler is pinned and stays.** `datamodel-code-generator` is an argument of
  `f(schemas, pinned compiler)`. Removing it is removing half of P11's function.
- **D11 — `Refusal` lives in the package every lowering imports, never in a module that is
  also an entry point.** `python -m codegen.emit` under `runpy` binds the emitter twice, so an
  exception class defined in it has two identities and `except Refusal` misses the one a
  lowering raised. Measured three times independently; this is the structural fix.

Layout: `codegen/emit.py` (CLI, module writer, the refusal report), `codegen/lower/<shape>.py`
one per D2 row, and a dispatch **table** of `(selector, lowering)` pairs where a document
selected by two rows is a build failure rather than a precedence puzzle. A selector is its
step's population test, so a row cannot claim a document its step does not count.

## 4. The metric

> **N = the number of portable bundle documents (of 1,054) whose class is emitted by
> `codegen.emit` and graded green by `codegen.harness` against the schema the class itself
> names, with `N + refused == 1,054` asserted and every refusal named by document, pointer and
> keyword.**

The harness grades in three legs. The first two are the existing both-directions acceptance
check; the third exists because of a measurement.

1. **Acceptance, schema → payload → model.** Through `strict_validate`, which is the
   production entry point.
2. **Acceptance, model → mutated keyword → schema.** The same entry point, the other way.
3. **Faithfulness: the class against its schema.** Compare the class's own
   `model_json_schema()` to the document `__adcp_schema__` names.

**Leg 3 is not optional, and here is the measurement that forces it.** Legs 1 and 2 go through
`strict_validate`, whose schema half refuses everything the document refuses — so the
annotations are never exercised. On `core/pagination-request.json`, a model with `Any` on
every field grades GREEN in both directions with a direction-2 denominator of **0 instances**,
and so does deleting the base classes. A faithful model grades green with a denominator of 75.
Three lanes found this independently by widening their own lowerings and staying green. Leg 3
is what grades the generated code; legs 1 and 2 grade the entry point.

Leg 3 also catches what no acceptance test can, because it does not change the accepted set:
**3 of 3 schema defaults in the first 43 emitted modules were dropped**, against 626 of 1,625
documents carrying one. 137 enum nodes carry `enumDescriptions`, also dropped. The compiler
carries both for free, which is one of the reasons it is the compiler.

**A zero denominator is a refusal, not a pass.** No pair is reportable with
`accepted_invalid + refused == 0` in leg 2.

## 5. The steps

Each step ends with Python emitted by `codegen.emit` and graded green on all three legs
against the schema each class names. Steps 3–7 share only the dispatch table.

| # | step | done when | parallel |
|---|---|---|---|
| 1 | **The spine, on one leaf document** — `core/pagination-request.json`: our walk decides the shape, dmcg renders it, the class carries `__adcp_schema__`, `AdCPBaseModel.strict_validate` reads it, the harness grades all three legs off it. `_bindings.json` and `codegen/adapter.py` do not exist. | the module imports, `max_results` carries `ge=1, le=100` **and `= 50`**, leg 3 green, and the three legs are generic over any class | no — the trunk |
| 2 | **A cross-document `$ref`** — the referencing module imports its target's type and copies no constraint (asserted on the AST); the target emits as an alias | both graded, three legs | no — the trunk |
| 3 | **Enumerations** — root and inline. Member spelling upper-cased (`pass` and `global` are live values and lower-casing emits a module that does not parse); the injectivity check binds to whatever name function the compiler runs, or it is vacuous | 213 of 214 root enums emit; `enumDescriptions` carried | yes — `lower/enum.py` |
| 4 | **`allOf` roots** — `$ref` conjuncts become bases; a subclass never redeclares an inherited field | the `Optional[Any]` shadow is gone (31 of 42 `Any` fields shadowing a typed base field across 15 classes); `version-envelope`'s `ge=1, le=99` inherits | yes — `lower/product.py` |
| 5 | **Union roots** — base plus branches plus alias; `discriminator` where sound (63 of 156), plain union otherwise; the root name binds the base, never the alias | sole-untitled-branch nodes refused by name (6 documents, 9 nodes) | yes — `lower/union.py` |
| 6 | **Containers and mappings** — a constrained container value gets its own symbol (§1); multi-type properties apply each keyword to its own branch | the `dict[str, <array with minItems>]` widening is gone across its 53 documents | yes — `lower/containers.py` |
| 7 | **Rules** — `not`, conditionals, `dependencies`, `min`/`maxProperties`, `uniqueItems` as class-level tuples read by `_runtime.py` | `uniqueItems` is stepped by the harness (479 sites over 198 documents, previously 0 graded) | yes — `lower/rules.py` |
| 8 | **The whole population** — `--all` emits or refuses every portable document | `N + refused == 1,054` asserted; every refusal named | after 3–7 |
| 9 | **Public surface** — `adcp/types/__init__.py` and per-domain packages generated, PEP 562 lazy; a root name bound to two nodes is a build failure | `from adcp.types import X` and `from adcp.types.core import X` are the same object | after 8 |
| 10 | **Closeout** — P9 version derivation wired, byte compare in `make validate-generated`, the defect inventory re-run against the new tree expecting 0 | `tox` green | last |

**Order is by risk.** Step 1 is first because it is the only step that can still invalidate
the split: if our walk cannot hand the compiler a shape it renders faithfully on the simplest
document in the bundle, nothing after it matters. There is no step for `strict_validate` —
it is generic and lands in step 1, which is the point of §2.

**What the previous eleven steps had that these ten do not:** a step to remove the compiler, a
step to build `strict_validate` separately, and a rendering half in every shape lane. The
lanes' schema-reading work transfers; their text generation does not, and that was measured
per file at roughly 124 lines of judgement to 37 of text in the largest case.
