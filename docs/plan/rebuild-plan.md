# Emit the AdCP types: walk the schema, let the compiler write the class

## 1. The split

**Our code walks the JSON Schema.** Read the document, resolve references, collapse identical
nodes, decide what each node becomes — a class, an annotation, an enumeration, or a rule — and
decide its name. Every judgement about the bundle lives here.

**`datamodel-code-generator` writes the class.** Our walk hands it a declaration — these
fields, these constraints, these defaults, this base — and it emits the Python.

```
schema document -> our walk -> a class declaration -> dmcg's model layer -> Python
                   (ours)                              (the compiler)
```

dmcg's **parser never runs**. Deciding names and structure from a schema is our half; the
compiler's half is rendering a declaration it is given.

## 2. Driving the compiler

```python
datamodel_code_generator.model.pydantic_v2.BaseModel(
    reference=..., fields=[...], base_classes=[],
    custom_base_class="adcp.types._base.AdCPBaseModel", description=...,
).render()
```

Fields are `DataModelField(name=, data_type=, required=, default=, has_default=, constraints=,
extras=)`.

**Constraints are spelled in JSON Schema.** `ConstraintsBase` declares each field under its
JSON-Schema alias and sets no `populate_by_name`, so `Constraints(ge=1, le=100)` sets nothing
and renders nothing. Write `Constraints(minimum=1, maximum=100)`, which renders
`Field(ge=1, le=100)`.

**Constraints travel in `constraints=` and nowhere else.** `_EXCLUDE_FIELD_KEYS` strips
`gt ge lt le multiple_of min_length max_length pattern` out of `extras`.

### What the compiler does not express

- **A constrained container as a mapping value.** A nested scalar carries its bound
  (`Dict[str, conint(ge=1, le=100)]` renders); a nested container does not — `DataType` has no
  `constraints` field, and `min_items` on an array value renders `List[Any]`. A field-level
  `Field(min_length=1)` bounds the mapping's key count instead, which is a different keyword on
  a different node. **A constrained container value gets its own symbol** and the mapping names
  it, so the constraint sits on a declaration the compiler does express. 53 documents use the
  construct.
- **A statement beside a module-level alias.** No alias template has a place for a sibling
  statement, so our module writer emits it around the compiler's output.
- **A union discriminated by requiredness.** `DataType.discriminator` renders
  `Annotated[A | B, Field(discriminator='type')]`, which is sound on 63 of 156 union roots —
  those where the tag is a `const` on every branch and required in every branch. The rest are
  plain unions with a rule (D5).

## 3. The emitted class

Every emitted class inherits `AdCPBaseModel` and carries a reference to the schema that
generated it.

```python
class PaginationRequest(AdCPBaseModel):
    __adcp_schema__: ClassVar[SchemaRef] = SchemaRef("core/pagination-request.json", "#")
    max_results: Annotated[int | None, Field(description="...", ge=1, le=100)] = 50
    cursor: Annotated[str | None, Field(description="...")] = None
```

`SchemaRef` is a document path plus a JSON pointer, because a nested class is a subschema and
answers for its own node rather than the whole document.

That reference makes two things generic:

- **`strict_validate`**, once on the base: read `cls.__adcp_schema__`, validate the payload
  against that schema, then construct through `model_validate`.
- **The harness**: take a class, read `__adcp_schema__`, grade the class against that document.

So there is **no adapter, no binding table, and no name-keyed lookup**. A class cannot be paired
with a document other than its own, and `codegen/adapter.py`, `_bindings.json`, `_documents()`,
`_document_at` and `_document_of` do not exist.

## 4. Decisions

A step that wants to change one of these reports it and stops.

- **D1 — the module is the document path.** `core/date-range.json` →
  `src/adcp/types/_schemas/core/date_range.py`. `_schemas/` is private; the public surface is
  generated in step 9.
- **D2 — what becomes a class.** An object with `properties` → a model. An `enum` node →
  `StrEnum`/`IntEnum`. A `oneOf`/`anyOf` → a base, one subclass per branch, and a union alias.
  Everything else is an annotation or a rule: scalar → an annotation; array → `list[X]`; typed
  `additionalProperties` → `dict[str, X]`; `const` → `Literal`; typeless → `Any`;
  `required`-only, `not`, conditional, `dependencies`, `min`/`maxProperties` and `uniqueItems` →
  a rule on the nearest class. A root array → `RootModel[list[X]]`; a root scalar or mapping →
  a module-level alias.
- **D3 — names.** Root: `pascal_case(title)`, keeping acronyms. Nested: parent name +
  `pascal_case(property)`. Union branch: title, else the discriminator `const`, else the sorted
  required set, else refuse the document by name and pointer. Nodes with identical content are
  one node; content equality is the only deduplication. A name is an input to a lowering and is
  never computed inside one.
- **D4 — the schema decides acceptance.** An optional renders plain, carrying its default.
  `strict_validate` validates against the class's own schema and then constructs. A schema
  refusal raises pydantic's `ValidationError` with the JSON Schema keyword as `type` and the
  instance pointer as `loc`. `model_validate` stays public and constructs without consulting
  the schema.
- **D5 — rules are after-validators, hand-written once** in `src/adcp/types/_runtime.py`,
  reading a class-level tuple the emitter writes. A rule narrows the constructor; acceptance
  stays with the schema.
- **D6 — bases are derived.** An `allOf` of `$ref`s makes those classes the bases. There is no
  marker-class policy: anything a caller wants to test with `isinstance` is a schema the
  document composes.
- **D7 — `extra` is derived.** `additionalProperties: false` → `forbid`; `true` → `allow`;
  absent → the base default; typed → `allow` with a typed `__pydantic_extra__`.
- **D8 — no patch pass.** `make validate-generated` byte-compares the committed tree to a fresh
  run. A defect is fixed in our walk, in the compiler's configuration, or in a compiler
  extension. Nothing rewrites emitted output.
- **D9 — the bundle directory is an argument.** `python -m codegen.emit --bundle <dir>`. No
  version literal in `codegen/`.
- **D10 — the compiler is pinned and stays.** The pipeline is `f(schemas, pinned compiler)`.
- **D11 — `Refusal` lives in the package every lowering imports**, never in a module that is
  also an entry point. Under `runpy`, `python -m codegen.emit` binds the emitter twice, so an
  exception class defined there has two identities and `except Refusal` misses the one a
  lowering raised.

**Layout.** `codegen/emit.py` holds the CLI, the module writer and the refusal report;
`codegen/lower/<kind>.py` is one module per D2 row. A dispatch table of `(selector, lowering)`
pairs connects them, and a document selected by two rows is a build failure rather than a
question of precedence. A selector is its step's population test, so a row cannot claim a
document its step does not count.

## 5. The metric

> **N = the number of portable bundle documents (of 1,054) whose class `codegen.emit` emits and
> `codegen.harness` grades green against the schema the class itself names, with
> `N + refused == 1,054` asserted and every refusal named by document, pointer and keyword.**

The harness runs three checks, two of which keep the names the code gives them.

1. **The accepts check** (`check_accepts`), schema → payload → model: the class accepts every
   instance the document accepts.
2. **The refuses check** (`check_refuses`), model → mutated keyword → schema: the class refuses
   every instance the document refuses.
3. **The schema comparison**: the class's own `model_json_schema()` against the document
   `__adcp_schema__` names.

The first two call `strict_validate`, whose schema half refuses whatever the document refuses,
so neither exercises the annotations: a class carrying `Any` on every field passes both, with a
refuses-check denominator of zero instances. **The schema comparison is what grades the
generated code**, and it is also the only check that sees a default or a description, because
neither changes the accepted set. 626 of 1,625 documents carry a `default`; 137 enum nodes
carry `enumDescriptions`.

**A zero denominator is a refusal, not a pass.** No pair is reportable with
`accepted_invalid + refused == 0` in the refuses check.

## 6. The steps

Each step ends with Python that `codegen.emit` emitted and that passes all three checks against
the schema each class names. Steps 3–7 share only the dispatch table.

| # | step | done when | parallel |
|---|---|---|---|
| 1 | **One leaf object document, end to end** — `core/pagination-request.json`: our walk decides what the node becomes, the compiler renders it, the class carries `__adcp_schema__`, `strict_validate` reads it, the harness runs all three checks off it | the module imports; `max_results` carries `ge=1, le=100` **and `= 50`**; the schema comparison passes; all three checks are generic over any class | no — trunk |
| 2 | **A cross-document `$ref`** — the referencing module imports its target's type and copies no constraint, asserted on the AST; the target emits as an alias | both documents pass all three checks | no — trunk |
| 3 | **Enumerations**, root and inline — members upper-cased, since `pass` and `global` are live values and a lower-cased member emits a module that does not parse; the injectivity check binds to the name function the compiler runs | 213 of 214 root enums emit; `enumDescriptions` carried | yes — `lower/enum.py` |
| 4 | **`allOf` roots** — `$ref` conjuncts become bases, and a subclass never redeclares an inherited field | the `Optional[Any]` shadow is gone (31 of 42 `Any` fields shadow a typed base field, across 15 classes); `version-envelope`'s `ge=1, le=99` inherits | yes — `lower/product.py` |
| 5 | **Union roots** — base, branches, alias; `discriminator` where sound (63 of 156), plain union otherwise; the root name binds the base, never the alias | nodes whose only untitled branch has no derivable name are refused by name (6 documents, 9 nodes) | yes — `lower/union.py` |
| 6 | **Containers and mappings** — a constrained container value gets its own symbol (§2); a multi-type property applies each keyword to its own branch | the `dict[str, <array with minItems>]` widening is gone across its 53 documents | yes — `lower/containers.py` |
| 7 | **Rules** — `not`, conditionals, `dependencies`, `min`/`maxProperties` and `uniqueItems` as class-level tuples read by `_runtime.py` | the harness steps `uniqueItems` (479 sites over 198 documents) | yes — `lower/rules.py` |
| 8 | **The whole population** — `--all` emits or refuses every portable document | `N + refused == 1,054` asserted; every refusal named | after 3–7 |
| 9 | **Public surface** — `adcp/types/__init__.py` and per-domain packages generated, PEP 562 lazy; a root name bound to two nodes is a build failure | `from adcp.types import X` and `from adcp.types.core import X` are the same object | after 8 |
| 10 | **Closeout** — the bundle version derived rather than written; `make validate-generated` wired; the defect inventory re-run against the emitted tree | the inventory reports 0; `tox` green | last |

**Order is by risk.** Step 1 comes first because it is the only step that can invalidate the
split: if our walk cannot hand the compiler a declaration it renders faithfully on the simplest
document in the bundle, nothing after it matters. `strict_validate` has no step of its own —
it is generic, so it lands in step 1.
