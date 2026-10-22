# The AdCP types SDK: what it is, and how it is built

## 1. The artifact

The SDK is a set of pydantic classes, one per schema node that needs one, generated from the
AdCP schema bundle. A consumer reaches them through one import surface:

```python
from adcp.types.core import PaginationRequest     # the one import spelling
from adcp.types.enums import MatchType            # the domain says where it came from

req = PaginationRequest.strict_validate(payload)  # the schema decides, then construct
req = PaginationRequest(max_results=50)           # pydantic constructs, annotations only
mode = MatchType("broad")                         # a consumer uses these types directly
```

**The domain in the path is derived from the document's own path and carries meaning.**
`enums/match-type.json` is reachable as `adcp.types.enums.MatchType`, so a reader of application
code sees what kind of thing it is without looking it up, and `import adcp.types.enums as enums`
then `enums.MatchType` reads the same way. Nine domains exist today: `enums`, `core`,
`error_details`, `property`, `trusted_match`, `brand`, `media_buy`, `sponsored_intelligence`,
`pricing_options`. The SDK's types are for a consumer to construct and annotate with, not only
for the SDK to parse into, so the import path is part of the artifact rather than packaging
detail.

There is **one import path per class**, mirroring the document's own place in the bundle, and
**the SDK never offers a second way to reach the same class.** `adcp.types` is a package, not a
namespace holding a thousand names. Two spellings for one class is two things to keep in
agreement, and it makes an import non-deterministic in the only way that matters: a reader
cannot tell from the import which document a class came from.

The build emits a **mapping** from class name to its module, so a consumer migrating or
generating code can resolve a name mechanically. The mapping is a lookup table, not a second
import surface — nothing imports through it.

Three properties hold for every emitted class:

- It inherits `AdCPBaseModel`, which implements `strict_validate` once for every class.
- It carries `__adcp_schema__`, the document and JSON pointer it was generated from.
- It accepts exactly what its schema accepts, through `strict_validate`.

A union document gives a base class plus one subclass per branch, and **receiving a payload
resolves to the branch the document satisfies** — on every path, including through a consumer's
own subclass. §4 states that mechanism exactly.

## 2. The build

**Our code walks the JSON Schema.** Read the document, resolve references, collapse identical
nodes, decide what each node becomes — a class, an annotation, an enumeration, or a rule — and
decide its name. Every judgement about the bundle lives here.

**The compiler writes the class.** Our walk hands `datamodel-code-generator` a declaration —
these fields, these constraints, these defaults, this base — and it emits the Python.

```
schema document -> our walk -> a class declaration -> the compiler -> Python
                   (ours)                              (dmcg, pinned)
```

The compiler's **parser never runs**. Deciding names and structure from a schema is our half;
the compiler's half is rendering a declaration it is handed.

**A gap in the compiler is fixed in the compiler** (D10), never worked around in the emitted
output. **No gap is open**: naming a constrained type (D5) is what removed the one that looked
like a compiler limitation, because a named type is a plain reference wherever it appears.

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
the JSON-Schema spelling is the only one that sets anything, so write `minimum`/`maximum`.

### Where a gap is fixed

A gap in the compiler is fixed in the compiler (D10), never routed around in our walk and never
in the emitted output. Before calling something a gap, check whether it is one of these, which
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

**No gap is open.** Every limitation measured so far turned out to be one of the three above.
A real one — a rendering the compiler cannot produce from a declaration we can state — is fixed
by patching the compiler and offering the patch upstream, and a fork exists only once something
needs it. Until then it is a pinned dependency.

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
  as `loc`, so a caller reads the same error whichever half refused.
- **The harness**: take a class, read `__adcp_schema__`, grade the class against that document.

So there is **no adapter, no binding table, and no name-keyed lookup**. A class cannot be paired
with a document other than its own.

**The regex engine is derived per class.** pydantic's default Rust engine is the one to want —
it is faster and it refuses to compile a pattern it cannot honour rather than quietly
mis-matching. It has no look-around, and 4 of the bundle's 111 distinct patterns use look-around
at 107 sites across 27 documents, so a class carrying one of those sets
`regex_engine="python-re"` and every other class takes the default. No pattern in the bundle
uses a backreference or a named group, so look-around is the whole of the incompatibility and
107 of 111 patterns compile under Rust.

Both engines agree with the schema's own accepted set for those 102, and the schema half
compiles with Python `re` in either case, so the split costs no divergence: a class uses the
weaker engine exactly when its own patterns require it.

### A union root: the base, the branches, and how a payload reaches the right one

A `oneOf`/`anyOf` root emits a **base** carrying `BranchDispatchMixin` plus **one subclass per
branch**, and the base's name is what every referrer imports. Four things make it work, and
each exists because one of the others does not reach a path.

**`__get_pydantic_core_schema__` on the mixin returns the branches' union** instead of the
base's own model schema. That covers every path pydantic validates *through*: a nested field, a
`TypeAdapter`, `model_validate`. Overriding `model_validate` instead reaches only one of those
three, and most union roots are nested, which is where an override leaves a document satisfying
no branch to parse as a loose base.

**`__new__` on the mixin covers `Base(**data)`**, which no schema can reach — `BaseModel.
__init__` validates with `self_instance=self`, so the object is already allocated by the time
validation runs and direct construction returns a base instance whose serializer is the union.
`__new__` asks the base's own validator, which is that union, so all four paths refuse
identically. Direct construction therefore validates twice and is idempotent; `model_validate`
stays single-pass.

**Which class gets the union is decided by `"_branch_models" not in cls.__dict__`** — the base
is the class that *declares* `_branch_models`, and a class that inherits it keeps its own
schema. That is the whole of subclass support: a branch keeps its own schema, and so does a
consumer's refinement declared elsewhere. Membership (`cls in branches`) is not enough, because
it admits both "is a branch" and "is an unrelated subclass", and only the second matters once
the schema is being replaced.

**The union is the validator and not the serializer.** Put it in the serializer slot and the
class has no serializer for an instance of itself: the union's serializer matches no branch,
falls back to inferring a model, finds the same union and recurses — `model_dump(mode="json")`
raises, and `mode="python"` silently returns the model instance instead of a dict. So the
`serialization` slot carries a wrap serializer built from `handler(source)`, the plain model
schema the class would have had, which terminates. It is set on the schema the wrapper *holds*:
most roots come back as a `definitions` node wrapping the `function-wrap`, and a `serialization`
key on a `definitions` node is not consulted.

Two facts the emitter writes onto the base because they are not recoverable at runtime:

- **`_ROOT_REQUIRED`**, the fields the root requires as opposed to the ones that select a
  branch. A combinator refusal reports every absent field with the two kinds mixed together, and
  no intersection over those errors separates them.
- **`_branch_combinator()`**, `anyOf` or `oneOf`, because a refusal has to name a JSON Schema
  keyword and a document satisfying no branch fails each branch at field validation, where
  pydantic reports `missing` — which is not in that vocabulary.

The branches subclass the base, so they do not exist while the base is being built: the hook
returns the base's own schema then, and the declaring module calls `model_rebuild(force=True)`
after the branches are defined to install the union.

A root scalar is an annotation and not a class (D2), so it has no class to carry
`strict_validate`. Its module binds the same two halves as a module-level function over the same
`SchemaRef`, so a class and an alias cannot disagree about what their document accepts.

## 5. Decisions

A step that wants to change one of these reports it and stops.

- **D1 — the module is the document path, and it is private.** `core/date-range.json` →
  `src/adcp/types/_schemas/core/date_range.py`. The public surface is generated (step 10) and
  keyed on the class name, which comes from the schema `title`. A consumer's import therefore
  survives an upstream file rename; the document path is a build input, not an API.
- **D2 — what becomes a class.** An object with `properties` → a model. An `enum` node →
  `StrEnum`/`IntEnum`. A `oneOf`/`anyOf` → a base, one subclass per branch, and a union alias.
  Everything else is an annotation or a rule: scalar → an annotation; array → `list[X]`; typed
  `additionalProperties` or `patternProperties` → a mapping (D5 types its key); `const` →
  `Literal`; typeless → `Any`;
  `required`-only, `not`, conditional, `dependencies`, `min`/`maxProperties` and `uniqueItems` →
  a rule on the nearest class. A root array → `RootModel[list[X]]`; a root scalar or mapping →
  a module-level alias.

  **A `RootModel` is avoided wherever anything else will do, and is admissible only when it
  wraps exactly one value.** A root array is that case: the document IS a list and there is no
  field to hang it on. Everywhere else a wrapper is a second name for a node that already has
  one — so a scalar root is an `Annotated` alias and never `RootModel[str]`, and a node whose
  only untitled branch has no derivable name **refuses** rather than being wrapped, because a
  wrapper changes what the class is called and leaves the naming problem untouched. Needing a
  name produces the wrapper, not the constraint.
- **D3 — names.** Root: `pascal_case(title)`, keeping acronyms. Nested: parent name +
  `pascal_case(property)`. Union branch: title, else the discriminator `const`, else the sorted
  required set, else refuse the document by name and pointer. **A branch named by anything other
  than its own title is qualified by its base's name**, because a discriminator `const` yields
  `ById` and a required set yields `ExplicitPackagesWithFixedAllocation` — names that collide
  across documents and carry nothing of the root they belong to. Nodes with identical content
  are one node; content equality is the only deduplication. A name is an input to a lowering and
  is never computed inside one.

  **Two nodes are compared by content, never by title**, and the comparison must say where it
  cuts a reference cycle. Two instruments that cut differently disagree about whether two nodes
  are the same, and the fix is to fix the cycle rule in one instrument rather than to prefer
  an answer.

  **A name that shadows a Python builtin never claims the bare public slot.** `Warning`,
  `Error`, `Format`, `Type` and `Id` are schema titles; the class keeps its schema name inside
  its own module, and nothing exports a bare name that resolves to a builtin for a caller who
  did not import it.

  **Every public binding is derived by one rule, and the build refuses what the rule cannot
  derive.** A refusal is the designed outcome, not a failure: it names the document and pointer
  and is counted. There is no per-name table, no allowlist, and no hand-assigned exception.
- **D4 — the schema decides acceptance.** `strict_validate` validates against the class's own
  schema and then constructs. `model_validate` and the constructor stay public and build without
  consulting the schema, so a caller that already has a conforming payload pays nothing.

  **A required property is emitted with no default**, whatever `default` the document states for
  it, and the drop is reported. A default makes a field optional and the document says it is
  not, so carrying both would make the model accept an absence the schema refuses. Measured: 5
  sites state a `default` for a property their own node requires. Four are leaves —
  `core/product.json`, `core/reporting-capabilities.json`,
  `core/reporting-delivery-config.json`, `formats/canonical/seller_rendered_stateful_display.json`.
  The fifth is `core/format.json#/$defs/baseGroupAsset`, whose `required` lists a property
  literally named `required` that carries `default: false`, and that node is `$ref`'d **21
  times as an `allOf/0` base** inside its own document — so emitting it optional makes all 21
  branches accept a document the schema refuses.
- **D5 — constraints bind to the type, not the field.** `Annotated[int, Field(ge=1, le=100)]`,
  never `Field(None, ge=1, le=100)` as a default. A constrained type nests into `list[...]` and
  `dict[str, ...]`, can be aliased and reused, and works under `TypeAdapter` on its own; a
  field-bound constraint does none of those. It also keeps `= 50` meaning a default rather than
  conflating the default with metadata.

  **A constrained type is named once and referenced.** The walk resolves every constrained
  scalar and container it meets to one type, in this order: a type the bundle itself names — a
  titled root carrying those constraints, reached by `$ref` as an import; then a type pydantic
  names, where one qualifies; and otherwise an alias we emit in one module.

  **A standard type qualifies only when it states the document's own facts and accepts the
  document's own set.** Both halves are required and the schema comparison enforces the first,
  so this is a rule rather than a list of blessed types. Measured against pydantic's set:
  `NonNegativeInt` for `{integer, minimum: 0}` and `NonNegativeFloat` for `{number, minimum: 0}`
  both render `minimum: 0` and qualify. `PositiveInt` for `{integer, minimum: 1}` renders
  `exclusiveMinimum: 0` — the same integers, a different fact, so it does not qualify.
  `PositiveFloat` for `{number, minimum: 1}` renders the same and **accepts `0.5`, which the
  document refuses**, so it is a widening and is banned rather than merely unqualified.
  `AnyUrl` adds `minLength: 1`, which its document does not state.

  **`format` selects a type, and the schema half asserts it.** `format: date-time` references
  RFC 3339, where the offset is mandatory, so the schema does require a timezone and
  `AwareDatetime` states the document's own rule. `jsonschema` asserts nothing for `format`
  without a checker, so `strict_validate` and the harness both pass one, and the SDK depends on
  the packages that make the bundle's formats checkable: `rfc3339-validator` for `date-time`
  and `rfc3987` for `uri`, beside the `date`, `email`, `ipv4`, `ipv6`, `regex`, `time` and
  `uuid` checkers `jsonschema` carries. Without them 749 of the bundle's 807 format uses go
  ungraded — `date-time` 438, `uri` 300, `hostname` 10, `uri-template` 1, counted over the
  1,057 documents outside `bundled/` and `mcp/` — and a format-derived type is then narrower
  than its document, which no check reports because the accepts check draws through
  `hypothesis_jsonschema` and that honours the format when generating.

  So `date-time` is `AwareDatetime`, `date` is `datetime.date`, and `uri` is a URL type. A
  format with no checker available does not select a type.

  **An alias names a constraint, never a concept.** Its name is derived from the constraint it
  carries, never from a property name or a domain word, because two fields sharing a bound are
  not thereby the same idea.

  **An alias we emit has no document, so it has no domain, and it lives in
  `adcp.types.constraints`.** Every other type is reachable at `adcp.types.<domain>.<Name>`
  where the domain is the document's own path, but a type derived from a repeated constraint
  belongs to no document and inventing a domain for it would be naming it after a concept. One
  module holds them, and a consumer annotating application code imports from there. The module
  is named for what it holds rather than for `Annotated`, which is only the mechanism — a
  constraint expressed some other way later does not make the name a lie. Naming the type is also what keeps a constrained container usable
  as a mapping value: once it has a symbol, `dict[str, Tags]` is a plain reference and needs
  nothing from the compiler.

  **A mapping's key is typed from the schema too, and `str` is the last resort.** The key type
  comes from `propertyNames` where the document has one: a `$ref` names it, so the key is that
  type; a `pattern`, `minLength` or `maxLength` constrains it, so the key is an annotated
  `str`; an `anyOf` makes it a union of those. A `patternProperties` key carries the pattern
  that selected it. An `enum` under `propertyNames` closes the key set, and **a closed key set
  is a model and not a mapping** — the keys are its fields. Only where the document says
  nothing about keys is the key `str`, and that is a faithful reading rather than a default:
  typing it further would be the SDK inventing a constraint. Measured over the bundle, a key is
  constrained at roughly 176 mapping sites and unconstrained at 193.
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
- **D7 — bases are derived, and composition merges by intersection.** An `allOf` of `$ref`s
  makes those referenced classes the bases, so every base an emitted class has is a schema its
  document composes.

  **A composed class's `required` is the union of its own and every base's.** Where a
  composition makes an inherited field required, the subclass **redeclares that field with the
  base's type and no default** — and that is the ONLY case in which an emitted class redeclares
  an inherited field. A redeclaration that changes the type or adds a default is a build
  failure. Measured over the node that OWNS the `allOf`, at any depth, with refs resolved and
  `not`/`if`/`then`/`else` positions excluded: **47 composition sites, 79 field tightenings, 31
  documents**. `core/canonical-product.json#/properties/collections/items` is the clearest —
  an overlay with no `properties` at all, only a requiredness change. Concentrated in
  `core/registry-event.json` (14), `media-buy/get-media-buy-delivery-response.json` (11) and
  the twelve `*-delivery-metrics.json` documents (2 each, all the same shape), then a tail of
  one.

  **A `required` under `not`, `if`, `then` or `else` is a rule and not a field** (D6), so this
  exception does not reach it and nothing is redeclared there. A further 12 sites tighten inside
  such a position and belong to the rules step.

  **Where composed schemas constrain the same property, the field carries the INTERSECTION**,
  never the union: an enum is the intersection of the members, a bound is the tighter one, a
  `const` must agree. This holds at any depth, including an overlay under `items`. An empty
  intersection refuses the document by name and pointer. Unioning an enum's vocabularies makes
  the model accept a member the schema forbids, which is the defect this prevents.

  A response composing the two envelopes inherits them:

  ```python
  class CreateMediaBuyResponse1(AdcpResponse, AdcpVersionEnvelope, ProtocolEnvelope): ...
  ```

  `AdcpVersionEnvelope` and `ProtocolEnvelope` are generated from `core/version-envelope.json`
  and `core/protocol-envelope.json` like any other document. The root `allOf` applies to the
  whole document in draft-07, so it reaches **every branch** of a root `oneOf` — a generator
  that applies the bases to some branches and not others is wrong, and that is the defect §4's
  dispatch and this row exist together to prevent.

  **`AdcpRequest` and `AdcpResponse` are the SDK's own markers, and membership is derived.**
  `index.json` carries the task registry — `schemas/<domain>/tasks`, each task naming
  `request: {$ref}` and `response: {$ref}` — which is 77 tasks over 77 request documents and 77
  response documents, disjoint. A document the registry names as a task's request gets
  `AdcpRequest`; a response gets `AdcpResponse`. Nothing is classified by filename, and a
  document the registry does not name gets neither.

  Both markers derive from `_AdcpMessage`, and all three are hand-written in
  `src/adcp/types/_base.py` beside `AdCPBaseModel`:

  - **A marker declares no fields and is not a `BaseModel`.** A field there would land on every
    task message's wire type — `adcp_version` would appear on a request whose schema declares no
    version field, inventing a spec field.
  - **The envelope pins are read through methods, never properties.** pydantic does not let a
    model field shadow a property of the same name: the value is stored and `model_dump` shows
    it, while attribute access returns the property, so every tool declaring `context` would
    read `None` silently.
  - **`version_fields()`, `protocol_fields()` and `payload_fields()` answer from the MRO**, not
    from a per-class table, so fields stay flat exactly as on the wire and provenance is which
    ancestor declared them. Each is empty unless the class actually descends from that envelope,
    because a schema that *inlines* `adcp_version` shares the name but not the stratum. A class
    with no envelope ancestry answers the empty set, and the answer changes by itself when its
    schema starts composing the envelope.
  - **`issubclass(model, AdcpRequest)` is the registration-time proof** that a model is
    spec-derived rather than a hand-written parallel: a field test passes for a forged model,
    descent does not. That is what lets a consumer's registry be generic in the request type.
  - The envelope classes are imported into `_base.py` **lazily**, because every generated module
    imports `_base` and a module-level import of the generated tree there is a cycle.

  **Envelope and payload are two strata, and the bundle states both.** Over the registry's 77
  tasks: 76 of 77 requests compose `version-envelope`, and 70 responses compose
  `version-envelope` with 67 also composing `protocol-envelope`. So a task message is its
  envelope bases plus its own properties, and the three classifiers read that partition off the
  MRO rather than off a list. The residue is small and named rather than papered over: 1 request
  and 5 responses compose nothing, 7 responses omit the version envelope and 10 the protocol
  envelope.

  **The SDK never adds an envelope a document does not compose.** Where a document composes
  none, its envelope strata are empty and everything is payload — the honest answer, and one
  that changes by itself if the bundle starts composing. A missing envelope is a bundle defect
  to fix upstream, never a field the generator invents.

  A consumer refines on top by mixing in its own class —
  `class GetProductsRequest(BuyerRequest, LibraryGetProductsRequest)` — and the declaring-class
  test in §4 is what makes that hold: a subclass declared elsewhere is not the base, so it keeps
  its own schema rather than being replaced by a union. **An emitted class must stay
  subclassable for exactly this reason**, which is a constraint on the generator rather than a
  convenience.
- **D8 — `extra` follows the schema, and nothing else.** `additionalProperties: false` →
  `forbid`; `true` → `allow`; typed → `allow` with a typed `__pydantic_extra__`; **absent →
  `ignore`**. Absent and `true` are different statements: `true` says additional properties are
  part of the document, so they are retained, and silence says only that they are permitted, so
  they are accepted and dropped. Retaining a property the document never mentions would be the
  SDK adding a claim the schema does not make.

  A consumer who wants stricter or looser behaviour than the schema sets it on a subclass. The
  SDK does not read an environment to decide, and no generated class carries a policy that is
  not in its document.

  **No test-only setting either.** Harness instances are drawn by `hypothesis_jsonschema` from
  the same document the class was generated from, so an undeclared field has nowhere to come
  from. The one place one appears is where the refuses check deliberately adds it to a document
  declaring `additionalProperties: false`, and the `forbid` derived from that document is what
  refuses it.
- **D9 — nothing rewrites emitted output.** A defect is fixed in the schema input before the
  compiler reads it, or in the compiler. `make validate-generated` byte-compares the committed tree
  to a fresh run.
- **D10 — the compiler is pinned, and a gap in it is fixed in it.** The pipeline is
  `f(schemas, pinned compiler)` and both arguments are ours to change: a defect is fixed in the
  schema we hand it or in the compiler itself, never in the output. A fix we carry is offered
  upstream as a pull request, and a fork exists only once something needs one. No gap is open
  today, so the pin is an ordinary released version.
- **D11 — the bundle directory is an argument.** `python -m codegen.emit --bundle <dir>`. No
  version literal in `codegen/`.
- **D12 — `Refusal` lives in the package every lowering imports**, never in a module that is
  also an entry point. Under `runpy`, `python -m codegen.emit` binds the emitter twice, so an
  exception class defined there has two identities and `except Refusal` misses the one a
  lowering raised.

- **D13 — the dispatch seam, stated exactly.** Three lanes invented three seams because an
  earlier revision named a table that did not exist. The seam is:

  - **The table lives in `codegen/emit.py`** as `ROWS`, a tuple of `(selector, lowering)` pairs,
    unordered. `emit` imports each lowering.
  - **A lowering under `codegen/lower/` imports `codegen.compiler` and `codegen.refusal`, and
    nothing else of this package.** It never imports `codegen.emit`.
  - **Shared machinery lives in `codegen/compiler.py`**, not in `emit.py`: the field builder,
    the class declarer, and the carriers a lowering is handed.
  - **One signature.** A lowering takes the node, its name, its pointer and the module being
    written, and returns the declared name.

  The import rule decides the other two. A lowering that imports `emit` closes a cycle, and
  under `runpy` — `python -m codegen.emit` — that cycle resolves into **two module objects**
  rather than an `ImportError`, which is the failure D12 exists to prevent for `Refusal`. A
  `TYPE_CHECKING` import hides the cycle from the type checker without removing it, because the
  lowering still needs the shared machinery at run time. Moving that machinery into
  `compiler.py` is what makes the one-directional import true rather than merely intended.

  A row's selector is its step's population test in `codegen.bundle`, so a row cannot claim a
  document its step does not count, and `lower_document` **fails** on a document two rows select
  rather than letting insertion order decide.

**Layout.** `codegen/emit.py` holds the CLI, the module writer and the refusal report;
`codegen/compiler.py` drives the compiler; `codegen/lower/<kind>.py` is one module per D2 row. A
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
annotations. A class carrying `Any` on every field and a faithful one produce **identical
reports**: on `core/pagination-request.json`, both accept, both refuse 75 of 75 instances, both
record no wrong acceptance. Dropping `extra="forbid"` and dropping a `pattern` measure the same
way. No reading of those two checks separates a faithful class from a widened one, and the
denominator is healthy in both, so nothing looks wrong.

**The schema comparison is what grades the generated code.** It is also the only check that
sees a default or a description, because neither changes the accepted set.

**Determinism is a precondition of grading, not something to fix later.** Two runs over the
same bundle emit the same bytes, and a run that does not is ungraded rather than nearly right.

**A test that fails while the emitted behaviour is unchanged is grading a spelling**, and it is
the test that is wrong. A check asserts what a class accepts, refuses, or states about itself —
never the text that expresses it.

**A subclass inherits its parent's validators, and that is graded.** A consumer subclasses an
emitted class to refine it, so a check confirms the parent's constraints still refuse what they
refused. A subclass that silently loses a validator is the defect this catches.

**A zero denominator is a refusal, not a pass.** A pair with
`accepted_invalid + refused == 0` in the refuses check never reports `pass`, because no instance
reached the class. That guards a pair nothing exercised; it does not catch a widening.

## 7. The steps

Each step ends with Python that `codegen.emit` emitted and that passes all three checks against
the schema each class names. Steps 3–7 share only the dispatch table.

| # | step | done when | parallel |
|---|---|---|---|
| 1 | **One leaf object document, end to end** — `core/pagination-request.json`: our walk decides what the node becomes, the compiler renders it, the class carries `__adcp_schema__`, `strict_validate` reads it, the harness runs all three checks off it | the module imports; `max_results` carries `ge=1, le=100` **and `= 50`**; the schema comparison passes; all three checks are generic over any class | no — runs alone |
| 2 | **A cross-document `$ref`** — the referencing module imports its target's type and copies no constraint, asserted on the AST; the target emits as an alias | both documents pass all three checks | no — runs alone |
| 3 | **Enumerations**, root and inline — members upper-cased, since `pass` and `global` are live values and a lower-cased member emits a module that does not parse; the injectivity check binds to the name function the compiler runs | every root enum emits or is refused by name; `enumDescriptions` carried | yes — `lower/enum.py` |
| 4 | **`allOf` roots** — `$ref` conjuncts become bases; composed constraints on one property intersect; a requiredness-tightening overlay redeclares the field with the base's type and no default, and that is the only permitted redeclaration (D7) | no emitted field shadows a typed base field EXCEPT a requiredness tightening, which 37 documents need; a composed `ge`/`le` inherits; a composed enum is the intersection of its members and an empty one refuses | yes — `lower/product.py` |
| 5 | **Union roots** — the base carries `BranchDispatchMixin` and declares `_branch_models`, `_ROOT_REQUIRED` and `_branch_combinator`; one subclass per branch; the declaring module calls `model_rebuild(force=True)`; the root name binds the base (§4) | a payload resolves to its branch on all four paths — nested field, `TypeAdapter`, `model_validate`, `Base(**data)`; a consumer's subclass of the base keeps its own schema; `model_dump_json` on a base instance does not raise; a branch with no derivable name refuses its document by name and pointer | yes — `lower/union.py` |
| 6 | **Containers and mappings** — a constrained container value is a named type (D5), so a mapping is a plain reference; a mapping's key is typed from `propertyNames`; a multi-type property applies each keyword to its own branch | a mapping value's bound survives into the annotation, and a key the document constrains is not `str` | yes — `lower/containers.py` |
| 7 | **Rules** — D6's six keyword families as class-level tuples read by `_runtime.py` | the harness steps every one of the six | yes — `lower/rules.py` |
| 8 | **Name a constrained type once** — the resolution order in D5, with `adcp.types.constraints` holding the aliases that belong to no document; a standard type admitted only with both its measurements shown | the emitted tree's inline repeats drop to the shapes that occur once; N does not drop | after 3–7 |
| 9 | **The whole bundle** — `--all` emits or refuses every document | emitted plus refused equals the bundle size, asserted; every refusal named | after 8 |
| 10 | **Public surface** — one per-domain package per bundle directory, generated, PEP 562 lazy; no aggregate re-export; a class name bound to two nodes in one domain is a build failure; the build emits a class-name-to-module mapping as a lookup table | `from adcp.types.<domain> import X` is the only spelling that reaches a class, and the mapping resolves any class name to exactly one module | after 8 |
| 11 | **Closeout** — the bundle version derived rather than written; `make validate-generated` wired; any compiler patch we carry filed upstream | `tox` green | last |

**Order is by risk.** Step 1 comes first because it is the only step that can invalidate the
split: if our walk cannot hand the compiler a declaration it renders faithfully on the simplest
document in the bundle, nothing after it matters. `strict_validate` has no step of its own — it
is generic, so it lands in step 1.

## 8. What must not change

- **A class keeps the name its schema title gives it.** A naming rule names branches and nested
  nodes, never a root, so no root is renamed by any step here.
- **`BranchDispatchMixin`'s four-path dispatch, and the `anyOf`/`oneOf` keyword on its
  refusals.** 19 roots carry it today. A step adds roots to it; no step removes one, and no step
  reduces it to fewer than four paths.
- **The lazy loading of the public surface.** Step 10 generates the contents of a package's
  `__init__`, not the mechanism by which it loads.

**One rule is deliberately superseded.** An earlier design made the flat root a second total
import path — `adcp.types.<Class>` resolving for every class, alongside the per-domain path.
This specification keeps **one** path (§1): a class is reachable at
`adcp.types.<domain>.<Class>` and nowhere else, with a generated class-name-to-module mapping
for mechanical resolution. Two spellings for one class make an import non-deterministic in the
way that matters. The collision rule from that design survives intact: a class name bound to
two nodes is a build failure naming both nodes, never a rename table.

## 9. Not settled

Open questions. None is a licence to guess, and none is settled by this document.

- **Where a reference-cycle comparison cuts.** Two instruments disagreed about whether two nodes
  were identical, entirely because each cut a cycle at a different place. D3's content equality
  has to state its rule.
- **Whether any consumer outside this repository relies on a looser enum acceptance** than an
  `allOf` intersection produces. Not examined.
- **Whether the bundle declares one enum node or two** where the generated difference is only
  suffixed duplicate members. The generated side looks spurious; the schema side was never
  pinned.
- **Why `account` is optional on `compliance/comply-test-controller-request.json`**, whose root
  mixes `allOf`, `properties` and `required`. Eleven of 113 accepted-set disagreements in one
  earlier measurement were this one file, and the mechanism is unknown.

Settled since that list was written: `hypothesis-jsonschema` closes the positive-side gap, and
the accepts check draws through it. 944 of 1,057 roots carry no `examples`, which was the size
of the gap it closes.
