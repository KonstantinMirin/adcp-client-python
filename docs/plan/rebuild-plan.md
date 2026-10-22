# The AdCP types SDK: what it is, and how it is built

## 1. The artifact

The SDK is a set of pydantic classes, one per schema node that needs one, generated from the
AdCP schema bundle. A consumer reaches them through one import surface:

```python
from adcp.types import PaginationRequest          # or
from adcp.types.core import PaginationRequest     # the same object

req = PaginationRequest.strict_validate(payload)  # the schema decides, then construct
req = PaginationRequest(max_results=50)           # pydantic constructs, annotations only
```

Three properties hold for every emitted class:

- It inherits `AdCPBaseModel`.
- It carries `__adcp_schema__`, the document and JSON pointer it was generated from.
- It accepts exactly what its schema accepts, through `strict_validate`.

## 2. The build

**Our code walks the JSON Schema.** Read the document, resolve references, collapse identical
nodes, decide what each node becomes — a class, an annotation, an enumeration, or a rule — and
decide its name. Every judgement about the bundle lives here.

**The compiler writes the class.** Our walk hands `datamodel-code-generator` a declaration —
these fields, these constraints, these defaults, this base — and it emits the Python.

```
schema document -> our walk -> a class declaration -> the compiler -> Python
                   (ours)                             (our fork of dmcg)
```

The compiler's **parser never runs**. Deciding names and structure from a schema is our half;
the compiler's half is rendering a declaration it is handed.

**The compiler is a fork we own** (D10). When it cannot express something, we add the
expression to the fork and offer it upstream. Nothing is ever worked around in the emitted
output.

## 3. Driving the compiler

```python
datamodel_code_generator.model.pydantic_v2.BaseModel(
    reference=..., fields=[...], base_classes=[],
    custom_base_class="adcp.types._base.AdCPBaseModel", description=...,
).render()
```

Fields are `DataModelField(name=, data_type=, required=, default=, has_default=, constraints=,
extras=, alias=)`. Each input has exactly one channel:

- The type goes in `data_type`.
- Constraints go in `constraints=`, in JSON-Schema spelling:
  `Constraints(minimum=1, maximum=100)`.
- A description goes in `extras={"description": ...}`.
- A default goes in `default=` with `has_default=True`.
- A property key Python cannot carry goes in `alias=`.

`Constraints` declares each field under its JSON-Schema alias with `populate_by_name` off, so
the JSON-Schema spelling is the only one that sets anything. The fork may add
`populate_by_name` so both spellings work; until it does, write `minimum`/`maximum`.

### Where a gap is fixed

A gap in the compiler is fixed in the fork (D10), never routed around in our walk and never in
the emitted output. Before reaching for the fork, check whether the gap is one of these, which
are not compiler gaps at all:

- **A constraint that will not nest.** Naming the type is the fix, not a compiler change.
  `DataType` carries no constraints, so an inline `min_items` on an array used as a mapping
  value renders `List[Any]` and loses the bound — but under D5 that type has a symbol, so
  `dict[str, Tags]` is a plain reference. A field-level constraint is never the fix here: on a
  mapping field it bounds the key count, which is a different keyword on a different node.
- **A statement beside a module-level alias.** Our module writer owns module text, so it emits
  the statement around the compiler's output.
- **A union discriminated by requiredness.** `DataType.discriminator` expresses a union tagged
  by a `const` property that every branch declares and requires. Requiredness as a discriminant
  is not a rendering problem; it is a rule (D6).

A fork change is therefore the answer to a rendering the compiler genuinely cannot produce. No
such gap is open: the one convenience available is teaching `Constraints` to accept the pydantic
spelling as well as the JSON-Schema one, which the specification does not need because §3 fixes
the spelling.

## 4. The emitted class

```python
class PaginationRequest(AdCPBaseModel):
    __adcp_schema__: ClassVar[SchemaRef] = SchemaRef("core/pagination-request.json", "#")
    max_results: Annotated[int | None, Field(description="...", ge=1, le=100)] = 50
    cursor: Annotated[str | None, Field(description="...")] = None
```

`SchemaRef` is a document path plus a JSON pointer, because a nested class is a subschema and
answers for its own node rather than the whole document.

That reference is what makes the runtime contract and the test instrument generic:

- **`strict_validate`**, once on `AdCPBaseModel`: read `cls.__adcp_schema__`, validate the
  payload against that schema, then construct through `model_validate`. A schema refusal raises
  pydantic's `ValidationError` with the JSON Schema keyword as `type` and the instance pointer
  as `loc`, so a caller reads one error shape whichever half refused.
- **The harness**: take a class, read `__adcp_schema__`, grade the class against that document.

So there is **no adapter, no binding table, and no name-keyed lookup**. A class cannot be paired
with a document other than its own.

`AdCPBaseModel` also sets `regex_engine="python-re"`. pydantic's default Rust engine refuses to
compile a pattern using look-around and the bundle contains such patterns, so the default engine
makes those modules fail to import. The document's own validator compiles patterns with Python
`re`, so `python-re` is the engine whose accepted set matches the schema's.

A root scalar is an annotation and not a class (D2), so it has no class to carry
`strict_validate`. Its module binds the same two halves as a module-level function over the same
`SchemaRef`, so a class and an alias cannot disagree about what their document accepts.

## 5. Decisions

A step that wants to change one of these reports it and stops.

- **D1 — the module is the document path, and it is private.** `core/date-range.json` →
  `src/adcp/types/_schemas/core/date_range.py`. The public surface is generated (step 9) and
  keyed on the class name, which comes from the schema `title`. A consumer's import therefore
  survives an upstream file rename; the document path is a build input, not an API.
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
- **D4 — the schema decides acceptance.** `strict_validate` validates against the class's own
  schema and then constructs. `model_validate` and the constructor stay public and build without
  consulting the schema, so a caller that already has a conforming payload pays nothing.
- **D5 — constraints bind to the type, not the field.** `Annotated[int, Field(ge=1, le=100)]`,
  never `Field(None, ge=1, le=100)` as a default. A constrained type nests into `list[...]` and
  `dict[str, ...]`, can be aliased and reused, and works under `TypeAdapter` on its own; a
  field-bound constraint does none of those. It also keeps `= 50` meaning a default rather than
  conflating the default with metadata.

  **A constrained type is named once and referenced.** The walk resolves every constrained
  scalar and container it meets to one type, in this order: a type the bundle itself names — a
  titled root carrying those constraints, reached by `$ref` as an import; then a type pydantic
  names, such as `PositiveInt` for `{integer, minimum: 1}`, `NonNegativeInt`, `PositiveFloat`,
  `NonNegativeFloat`, `AnyUrl` for `{string, format: uri}` and `AwareDatetime` for
  `{string, format: date-time}`, a standard type always in preference to one of ours; and
  otherwise an alias we emit in one module.

  **An alias names a constraint, never a concept.** Its name is derived from the constraint it
  carries, never from a property name or a domain word, because two fields sharing a bound are
  not thereby the same idea. Naming the type is also what keeps a constrained container usable
  as a mapping value: once it has a symbol, `dict[str, Tags]` is a plain reference and needs
  nothing from the compiler.
- **D6 — rules are after-validators, hand-written once** in `src/adcp/types/_runtime.py`,
  reading a class-level tuple the emitter writes. A rule exists only for a keyword that has no
  field-level annotation, which is exactly the set spanning fields or collections: `oneOf` and
  `anyOf` over `required` (exactly one, or at least one, of these field groups is present);
  `if`/`then`/`else` (a field is required only when another holds a given value);
  `dependencies` (if A is present, B is required); `minProperties` and `maxProperties` (a bound
  on the count of set fields); `uniqueItems` (a list's items are distinct); and `not` (a
  subschema that must not match). Those six are the whole population. Everything else is an
  annotation, which pydantic enforces on the constructor without a rule. A rule narrows the
  constructor; acceptance stays with the schema (D4).
- **D7 — bases are derived.** An `allOf` of `$ref`s makes those classes the bases. There is no
  marker-class policy: anything a caller wants to test with `isinstance` is a schema the
  document composes.
- **D8 — `extra` follows the schema, and nothing else.** `additionalProperties: false` →
  `forbid`; `true` → `allow`; typed → `allow` with a typed `__pydantic_extra__`; **absent →
  `allow`**, because JSON Schema permits additional properties by default. `allow` rather than
  `ignore`, so a field a newer sender adds survives a round trip instead of being dropped.

  A consumer who wants stricter or looser behaviour than the schema sets it on a subclass. The
  SDK does not read an environment to decide, and no generated class carries a policy that is
  not in its document.

  **No test-only setting either.** Harness instances are drawn by `hypothesis_jsonschema` from
  the same document the class was generated from, so an undeclared field has nowhere to come
  from. The one place one appears is where the refuses check deliberately adds it to a document
  declaring `additionalProperties: false`, and the `forbid` derived from that document is what
  refuses it.
- **D9 — nothing rewrites emitted output.** A defect is fixed in the schema input before the
  compiler reads it, or in the fork. `make validate-generated` byte-compares the committed tree
  to a fresh run.
- **D10 — the compiler is our fork, pinned by commit.** The pipeline is `f(schemas, pinned
  compiler)` and both arguments are ours to change. An extension that proves itself is offered
  upstream as a pull request; the fork is where it lands first, not where it stays.
- **D11 — the bundle directory is an argument.** `python -m codegen.emit --bundle <dir>`. No
  version literal in `codegen/`.
- **D12 — `Refusal` lives in the package every lowering imports**, never in a module that is
  also an entry point. Under `runpy`, `python -m codegen.emit` binds the emitter twice, so an
  exception class defined there has two identities and `except Refusal` misses the one a
  lowering raised.

**Layout.** `codegen/emit.py` holds the CLI, the module writer and the refusal report;
`codegen/compiler.py` drives the fork; `codegen/lower/<kind>.py` is one module per D2 row. A
dispatch table of `(selector, lowering)` pairs connects them, and a document selected by two
rows is a build failure rather than a question of precedence. A selector is its step's
population test, so a row cannot claim a document its step does not count.

## 6. The metric

> **Every document in the bundle is either emitted as a class the harness grades green against
> that document, or refused by name, pointer and keyword. Emitted plus refused equals the
> bundle's own size, asserted at run time.**

The bundle size is read from the bundle, never written here. N is the emitted count and the
refusal list is its complement.

The harness runs three checks, two of which keep the names the code gives them.

1. **The accepts check** (`check_accepts`), schema → payload → model: the class accepts every
   instance the document accepts.
2. **The refuses check** (`check_refuses`), model → mutated keyword → schema: the class refuses
   every instance the document refuses.
3. **The schema comparison**: the class's own `model_json_schema()` against the document
   `__adcp_schema__` names.

The first two call `strict_validate`, whose schema half answers first, so neither exercises the
annotations: a class carrying `Any` on every field passes both, with a refuses-check denominator
of zero instances. **The schema comparison is what grades the generated code.** It is also the
only check that sees a default or a description, because neither changes the accepted set.

**A zero denominator is a refusal, not a pass.** No pair is reportable with
`accepted_invalid + refused == 0` in the refuses check.

## 7. The steps

Each step ends with Python that `codegen.emit` emitted and that passes all three checks against
the schema each class names. Steps 3–7 share only the dispatch table.

| # | step | done when | parallel |
|---|---|---|---|
| 1 | **One leaf object document, end to end** — `core/pagination-request.json`: our walk decides what the node becomes, the compiler renders it, the class carries `__adcp_schema__`, `strict_validate` reads it, the harness runs all three checks off it | the module imports; `max_results` carries `ge=1, le=100` **and `= 50`**; the schema comparison passes; all three checks are generic over any class | no — trunk |
| 2 | **A cross-document `$ref`** — the referencing module imports its target's type and copies no constraint, asserted on the AST; the target emits as an alias | both documents pass all three checks | no — trunk |
| 3 | **Enumerations**, root and inline — members upper-cased, since `pass` and `global` are live values and a lower-cased member emits a module that does not parse; the injectivity check binds to the name function the compiler runs | every root enum emits or is refused by name; `enumDescriptions` carried | yes — `lower/enum.py` |
| 4 | **`allOf` roots** — `$ref` conjuncts become bases, and a subclass never redeclares an inherited field | no emitted field shadows a typed base field; a composed `ge`/`le` inherits | yes — `lower/product.py` |
| 5 | **Union roots** — base, branches, alias; `discriminator` where the tag is a `const` present and required on every branch, plain union with a rule otherwise; the root name binds the base, never the alias | a branch with no derivable name refuses its document by name and pointer | yes — `lower/union.py` |
| 6 | **Containers and mappings** — the fork carries a constraint on a nested container (§3); a multi-type property applies each keyword to its own branch | a mapping value's bound survives into the annotation | yes — `lower/containers.py` |
| 7 | **Rules** — D6's six keyword families as class-level tuples read by `_runtime.py` | the harness steps every one of the six | yes — `lower/rules.py` |
| 8 | **The whole bundle** — `--all` emits or refuses every document | emitted plus refused equals the bundle size, asserted; every refusal named | after 3–7 |
| 9 | **Public surface** — `adcp/types/__init__.py` and per-domain packages generated, PEP 562 lazy; a class name bound to two nodes is a build failure | `from adcp.types import X` and `from adcp.types.<domain> import X` are the same object | after 8 |
| 10 | **Closeout** — the bundle version derived rather than written; `make validate-generated` wired; the fork's extensions filed upstream | `tox` green | last |

**Order is by risk.** Step 1 comes first because it is the only step that can invalidate the
split: if our walk cannot hand the compiler a declaration it renders faithfully on the simplest
document in the bundle, nothing after it matters. `strict_validate` has no step of its own — it
is generic, so it lands in step 1.
