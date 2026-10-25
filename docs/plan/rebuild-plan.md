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

**A `SchemaRef` names a node AS THE DOCUMENT APPLIES IT**, not the subschema read alone. The
pairing was fixed at `(document, pointer)` without saying how the pointer RESOLVES, and a bare
pointer walk is a different schema from the one the document applies at that location: draft-07
applies a root's `type: object` to every `oneOf` branch beneath it, so a branch read alone
admits a non-object its document refuses. That gap was latent while it could not be reached —
for every class emitted before union branches existed, the bare node and the applied node
coincided, because each either declares its own `type` or sits under a `properties` hop. Ten
documents reached it: each declares `type: "object"` at its root and was refused one combinator
hop below for not restating it.

**The consequence is that a check and a resolution must agree, or relaxing either one is a
defect.** Admitting the branch while the resolution still returned the bare node produced four
pairs reporting `accepts:model_refused_valid` with an `added` fact apiece — the model saying
`object` where the resolved schema said nothing. Given that resolution the original refusal was
CORRECT, so fixing only the check would have been the forbidden relaxation reached from the
other side.

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
  required set, else **the branch's own root type word**, else refuse the document by name and
  pointer. **A branch named by anything other than its own title is qualified by its base's
  name**, because a discriminator `const` yields `ById` and a required set yields
  `ExplicitPackagesWithFixedAllocation` — names that collide across documents and carry nothing
  of the root they belong to.

  **The type-word rung carries a second unnamed branch at one node.** The first three rungs read
  a name off the branch's own content, and a node may hold two branches that state none of them.
  Such a branch takes its own root type word, qualified by the base's name.
  `governance/reported-outcome-error.json#/definitions/bounded_value_level_3` is an `anyOf` of
  three untitled branches: a `$ref`, an array stating `maxItems: 32`, and an object stating
  `maxProperties: 32`. The `$ref` needs no name; the other two each need a carrier under D5's
  third rung, and they are `BoundedValueLevel3Array` and `BoundedValueLevel3Object`.

  The word is the schema's own, so it is derived rather than invented. **Two branches of the same
  root type refuse**: the rung names a branch only where the root types differ. An index or an
  ordinal would name every branch after nothing the schema states.

  **A branch that cannot be named is refused, never wrapped**, because a wrapper changes what the
  class is called and leaves the naming problem untouched.

  Nodes with identical content are one node; content equality is the only deduplication. A name
  is an input to a lowering and is never computed inside one.

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

  **This decision names the rendering, so a refusal here asserts that none exists.**
  `core/reporting-delivery-config.json` — one of the four leaves measured above — is refused at
  `/properties/active` saying "a default on a REQUIRED property has no rendering that does not
  also make the property optional". The rendering is the one chosen here: no default, and the
  drop reported.
- **D5 — constraints bind to the type, not the field.** `Annotated[int, Field(ge=1, le=100)]`,
  never `Field(None, ge=1, le=100)` as a default. A constrained type nests into `list[...]` and
  `dict[str, ...]`, can be aliased and reused, and works under `TypeAdapter` on its own; a
  field-bound constraint does none of those. It also keeps `= 50` meaning a default rather than
  conflating the default with metadata.

  **A constrained type is named once and referenced.** The walk resolves every constrained
  scalar and container it meets to one type, in this order: a type the bundle itself names — a
  titled root carrying those constraints, reached by `$ref` as an import; then a type pydantic
  names, where one qualifies; and otherwise an alias we emit in one module.

  **The third rung is a decision, not a fallback, and the walk stops at the second.** Five
  documents are refused for having no type at the first two rungs, which is the condition the
  third rung exists to answer:

  - `{"type": "string", "format": "hostname"}` under `items`, in the three
    `core/requirements/*-asset-requirements.json` documents. No bundle root carries that
    format and pydantic names no type for it, so the alias is
    `Annotated[str, WithJsonSchema({"type": "string", "format": "hostname"})]` and the field is
    `list[Hostname]`.
  - `{"minItems": 1}` on one branch of a `oneOf`, in the two `get-media-buy*-request.json`
    documents. The bound belongs to the array branch alone: carried on the field holding the
    union it also binds the enum branch, so the field refuses a single status the document
    accepts. The branch's own type takes it —
    `Annotated[list[MediaBuyStatus], Field(min_length=1)]` — and the refusal names this
    module while declining to use it.

  **A standard type qualifies only when it states the document's own facts and accepts the
  document's own set.** Both halves are required and the schema comparison enforces the first,
  so this is a rule rather than a list of blessed types. Measured against pydantic's set:
  `NonNegativeInt` for `{integer, minimum: 0}` and `NonNegativeFloat` for `{number, minimum: 0}`
  both render `minimum: 0` and qualify. `PositiveInt` for `{integer, minimum: 1}` renders
  `exclusiveMinimum: 0` — the same integers, a different fact, so it does not qualify.
  `PositiveFloat` for `{number, minimum: 1}` renders the same and **accepts `0.5`, which the
  document refuses**, so it is a widening and is banned rather than merely unqualified.
  `AnyUrl` adds `minLength: 1`, which its document does not state.

  **A `format: uri` field's type follows the document's own `pattern`.** Where the document
  restricts the scheme to https — `^https://`, 47 of the bundle's 300 `uri` positions — the field
  is **`AdCPUrl`**, defined once in `adcp.types.constraints` as
  `Annotated[AnyUrl, UrlConstraints(allowed_schemes=["https"])]`. There the type and the document
  agree. Named for provenance rather than after a standard: pydantic exports 22 URL types and
  none is https-only, so a name like `HttpsUrl` would read as an upstream export a reader cannot
  find. Everywhere else the field is **`HttpUrl`**.

  **`AdCPUrl` everywhere was measured and withdrawn.** A document stating only
  `{"type": "string", "format": "uri"}` admits `https://`, `http://`, `urn:` and `file:///` alike
  — `format: uri` is RFC 3986. `AdCPUrl` refuses three of those four, which narrowed the SDK
  below the pinned spec at **228 of 300 positions in 128 of 160 documents**, and at **26 of 27**
  positions in documents the emitter emits today. End to end on a shipped class:
  `core/placement-evidence.json#/properties/url` states only the bare pair, the document admits
  `{"url": "http://x.example/p"}`, and `PlacementEvidence.strict_validate` raises
  `URL scheme should be 'https'` — a buyer sending a payload the spec admits refused at the entry
  point D4 makes public. One position is sharper still: `core/macro-bearing-url.json#/anyOf/1` is
  the only one whose author wrote `^https?://`, admitting `http` deliberately.

  **No check saw it, and that is why it ran this long.** `compare_schema` passes, because
  `allowed_schemes` has no rendering in pydantic's schema output at all — there is no keyword on
  either side to compare. `format` is not a step keyword, so `steps()` returns `[]` and the
  refuses check never visits the position. And `hypothesis-jsonschema`'s `uri` strategy drew
  `https` in 200 of 200 derandomized examples, so the accepts check never tried another scheme.
  A narrowing invisible to all three checks is the one the schema comparison exists to catch, and
  reaching it needs a generator that does not honour `format`.

  **`HttpUrl` carries two named ceilings, both accepted deliberately.** It admits `http://`, which
  removes the sharpest case, and it still refuses `urn:` and `file:` — so **227 of 300 positions
  stay narrower than their document**. It also renders `maxLength: 2083` and `minLength: 1`,
  neither of which any document states, so the comparison needs a hand-written row for each; a
  row that names itself can be audited, and a derived rule admitting a widening would be
  invisible and permanent.

  **Type plus `pattern` is not representable in this stack**, so "the pattern stays with the
  schema half" is an either/or rather than a preference. `Annotated[AnyUrl, Field(pattern=...)]`
  does not drop the pattern — pydantic raises
  `Unable to apply constraint 'pattern' … for schema of type 'function-wrap'` while building the
  core schema, so the class does not exist. It was found as an `ImportError` at the gate when
  `core/platform_extension_ref.py` failed to import, which is where a future attempt will find it
  too.

  **A document's `pattern` on such a field is not carried on the annotation**, whichever of the
  two types the field takes. The bundle states eight distinct patterns across 73 of its 300 `uri`
  uses, and `UrlConstraints` expresses only the first — `^https://` at 47 sites. The other 26 say
  things it has no field for: no userinfo, not `localhost`, not an IP literal, host-only, a single
  pinned host. The pattern stays with the schema half.

  **The https arm is the 47 patterns that are EXACTLY `^https://`, as a literal set and not as a
  rule about regexes.** Three populations are easy to conflate here, and the difference is 47
  against 72: 47 patterns are exactly `^https://`; 25 more begin with it and then say more; 1 is
  `^https?://` and admits http on purpose. Only the first set takes `AdCPUrl`.

  This is deliberately a smaller set than "the document restricts the scheme to https" would
  select, for two reasons. **It costs nothing**, because at those 25 positions the document
  already refuses every non-https value, so `strict_validate` refuses one on either arm and
  neither type is narrower than its document there — only the bare constructor's strictness
  differs, and D4 already says what the constructor does. And **a literal set can be audited
  where a predicate cannot**: deciding "does this regex restrict the scheme" is a new mechanism
  with no falsifiable population, and it would quietly take in the `^https?://` position whose
  author admitted http deliberately.

  **Nothing widens, because `strict_validate` validates against the document first.** Measured
  against the strictest of the eight patterns: `https://localhost/x`, `https://10.0.0.1/x` and
  `https://user@evil.test/x` are all REFUSED by the schema half while the bare constructor
  accepts them — which is what D4 already says the constructor does. Request-forgery defence is
  a layer of its own in the SDK and in the consuming application, not a job the annotation does.

  **Known ceiling: `AdCPUrl` does not round-trip.** `https://x.example` validates to
  `https://x.example/`, and `https://A.example/Path/MiXeD?Q=1#F` to
  `https://a.example/Path/MiXeD?Q=1#F`. Lowercasing the host is RFC 3986-equivalent; the
  appended trailing slash is a different string, so a consumer that compares, signs or keys on
  the value sees something the sender did not send. Accepted, because a parsed URL is what the
  field is for and the alternative is a bare `str` that states less. The upgrade path, if a
  consumer ever needs the exact bytes, is to carry the sender's string beside the parsed value
  rather than to weaken the type.

  **This needs a comparison row of a new kind, and it is weaker than the others.** The enum rows
  admit a fact the document's own members *imply*. This one admits a fact the model does not
  state at all, on the ground that the entry point enforces it — so the row is "the schema half
  enforces this keyword and the annotation does not restate it", gated on the keyword being a
  `pattern` on a `format: uri` field whose model is a URL type, with `minLength: 1` admitted as
  implied by any URL type. Write it as its own category. Collapsing it into the implied-fact
  rows would make a genuine omission look like a derivation.

  **`format` selects a type, and the schema half asserts it.** `format: date-time` references
  RFC 3339, where the offset is mandatory, so the schema does require a timezone and
  `AwareDatetime` states the document's own rule. `jsonschema` asserts nothing for `format`
  without a checker, so `strict_validate` and the harness both pass one, and the SDK depends on
  the packages that make the bundle's formats checkable: `rfc3339-validator` for `date-time`
  and `rfc3987` for `uri`, beside the `date`, `email`, `ipv4`, `ipv6`, `regex`, `time` and
  `uuid` checkers `jsonschema` carries. Without them 749 of the bundle's 807 format uses go
  ungraded — `date-time` 438, `uri` 300, `hostname` 10, `uri-template` 1,  — and a format-derived type is then narrower
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

  **The key census, re-measured.** At TYPE positions, two independent instruments agree on `propertyNames` with a `pattern`
  (13), with a length bound (3), with an `anyOf` (1), and with an `enum` (1), and differ on
  `propertyNames` with a `$ref` (5 or 7), `patternProperties` (12 or 14) and the sites saying
  nothing about keys (63 or 128). Where they differ the plan carries the range, because a
  figure two instruments disagree about is not a fact yet.

  **The mechanism's reachable population is zero today.** Over the keyword-clean documents the
  emitter currently reaches there are 0 `propertyNames` and 0 `patternProperties` sites, so
  every mapping in the emitted tree is `dict[str, ...]` — which is each document's own reading
  rather than a default. The key rule is live code graded on constructed documents, and it
  starts deciding real output as later steps make more documents emittable. Typed
  `additionalProperties` is the same: 51 documents carry one, 0 reach an emittable document, and
  `__pydantic_extra__` appears in no emitted module.

  **A mapping's key is typed from the schema too, and `str` is the last resort.** The key type
  comes from `propertyNames` where the document has one: a `$ref` names it, so the key is that
  type; a `pattern`, `minLength` or `maxLength` constrains it, so the key is an annotated
  `str`; an `anyOf` makes it a union of those. A `patternProperties` key carries the pattern
  that selected it. Only where the document says nothing about keys is the key `str`, and that
  is a faithful reading rather than a default: typing it further would be the SDK inventing a
  constraint. The counts, and the one row where two instruments disagree, are in D5.

  **An `enum` under `propertyNames` closes the key set, and the document is refused by name
  with the key set in the detail.** Its single TYPE-position site is `core/store-item.json#/properties/hours`, and that
  document refuses on another keyword before any mapping is lowered — so the model would reach
  no document and no pair would grade it, which is the same reasoning that refuses the
  root-array row rather than emitting a class nothing reaches. Build it when a document reaches
  it.
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

  **A conjunct contributes every part of itself, and each part lowers by the decision that
  covers it.** A conjunct is a schema the composed node satisfies in full, so a conjunct of
  `$ref`s gives bases and a conjunct of `properties` gives fields by the intersection rule
  above — and a conjunct holding anything else is not an unhandled case. D2 already says what
  every construct becomes; the conjunct reader applies it there. Three combinations follow, and
  each had no case in the reader:

  - **Fields and a rule in one conjunct** contribute both, independently. The fields merge by
    the rule above; the rule attaches to the composed class by D2.
    `core/media-buy-frequency-cap-requirement.json` at `/allOf/1` states `properties` beside a
    rule, and a reader matching `properties` alone passes it by.
  - **A conjunct whose content is a `oneOf` or `anyOf`** gives one subclass per branch, each
    inheriting the bases the composition derives: D2's union rule applied after this
    decision's base rule, in that order. The composed node satisfies one branch and every other
    conjunct, which is what a branch subclass over the composed bases states.
  - **A conjunct carrying a keyword draft-07 does not define** contributes nothing, and the
    walk reports the drop. `media-buy/sync-catalogs-request.json` carries `errorMessage`, from
    ajv-errors: it customizes a validator's message and constrains no instance, so dropping it
    cannot change what the class accepts. It joins the `_constrains_nothing` fold on the
    comparison's document side (§6), because a keyword constraining nothing is not a fact the
    model is missing.

  **A reason naming a later row is this rule's absence, not a refusal.** Thirteen of the
  thirty-eight directly pending documents carry one sentence — "this step lowers a `$ref`
  conjunct (a base) or an inline conjunct with properties; a later D2 row lowers this one" —
  across `required`, `not`, `anyOf`, `oneOf`, `additionalProperties` and `errorMessage`. The
  walk reaches every one of those nodes. No later row was ever specified, because the gap is
  the cross product of this decision and D2 that nobody took: D2 enumerates outcomes per
  construct, this decision states a rule for composition, and the intersections went unwritten.

  **The requiredness overlay is this decision's own case and the reader refuses it.**
  `core/collection-selection.json` at `/oneOf/0/properties/collections/items` is
  `{"allOf": [{"$ref": "core/collection-selector.json"}, {"required": ["collection_ids"]}]}` —
  the pattern named above as the clearest instance, where the subclass redeclares the field
  with the base's type and no default. Four documents sit there, refused by a reader that has
  no case for a conjunct holding neither a `$ref` nor `properties`.

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

- **D13 — the dispatch seam.**

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
- **D14 — a check is exhaustive over a population, or it does not exist.** The suite contains
  the harness grading every class against the schema it names, and assertions computed over the
  whole bundle or the whole emitted tree. Nothing else.

  **A check that matches a spelling is deleted rather than extended.** There are infinitely many
  ways to write the thing it bans and it tests one, so it buys nothing and costs a parse.

  **A check over a CLOSED set of forms is a population check and survives.** The distinction is
  whether the set of ways to do the banned thing can be enumerated. The import rule is the worked
  case, and the measurement settles it: reaching another module has exactly two forms in Python,
  a static import statement and a dynamic import call, so the set is closed. `test_import_rule`
  grades all six modules of `codegen/lower/` with its denominator asserted non-empty, and
  catches all three static spellings — `from codegen import emit`, `import codegen.emit`,
  `from codegen.bundle import x`. It is **blind to both dynamic forms**,
  `importlib.import_module("codegen.emit")` and `__import__("codegen.emit")`, so it covers one of
  the two and is extended to cover the other rather than deleted.

  That gap is not hypothetical: step 6's lowering shipped an `_emit()` run-time accessor built
  precisely to reach `codegen.emit` without a static import, and the seam merge removed it. The
  next one spelled with `import_module` would pass the check as it stands.

  **Moving the machinery removed the NEED to import `emit`, not the ABILITY.** Three of the five
  lanes imported it, and under `runpy` that import resolves into two module objects rather than
  an `ImportError`, so the failure is silent. There is no structural way in Python to make a
  module unable to import another, which is why this rule is asserted rather than trusted.

  **A behaviour asserted on one example is upgraded or deleted.** If a `date-time` with no
  offset must be refused by the schema half, that is a claim about every format-bearing site,
  and it is asserted over all of them or not at all. One worked example is an illustration, not
  a check.

  This bounds the suite permanently: nobody adds a check because something went wrong once. A
  defect either shows up in the harness's own verdict over the population, or the thing that
  prevents it is structural, or it is accepted and named in §9.

**Layout.** `codegen/emit.py` holds the CLI, the module writer and the refusal report;
`codegen/compiler.py` drives the compiler AND holds the lowerings two rows read -- the object
row and the conjunct reader -- for the reason D13 gives; `codegen/lower/<kind>.py` is one module
per D2 row that only one row reads. A
dispatch table of `(selector, lowering)` pairs connects them, and a document selected by two
rows is a build failure rather than a question of precedence. A selector is its step's
population test, so a row cannot claim a document its step does not count.

## 6. The metric

> **Every document in the bundle is either emitted as a class the harness grades green against
> that document, or refused by name, pointer and keyword. Emitted plus refused equals the
> bundle's own size, asserted at run time — and the emitted count never decreases.**

The bundle size is read from the bundle, never written here. N is the emitted count and the
refusal list is its complement.

**The second term exists because the first one makes refusing a legal way to finish a row.**
A refusal is a designed outcome, so a partition that counts a refusal and a class alike is
satisfied either way: a row that emits its common case and refuses its edge leaves the figure
green and the SDK short. That is not hypothetical and it is not a lapse by one step. Ten
documents are refused today by a decision §5 already took — four by D7's requiredness overlay,
one by D4's `default` drop, five by D5's third rung — and three of those refusals **cite the
decision by number** while declining to apply it. The implementer knew the rule, and the
measurement charged nothing for refusing instead.

So the emitted count is pinned to grow, and **the two pins are coupled rather than
independent**. Two separate bounds do not have the property this needs: `emitted >= 691`
beside `pending <= 66` are both satisfied by refusing a pending document, because emitted
stays 691 while pending falls to 65. The signs are opposite only once clearing a pending
document COSTS an emission, so every document the pending count loses appears in the
emitted count:

```python
assert len(out.emitted) >= emitted_pin + max(0, pending_pin - pending)
```

`max(0, ...)` carries the never-decreases half, for a bundle that grows its own pending
set. A pin set at the current tree cannot fail on a row that already landed, so the
formulation reads the delta from where the row STARTED — which is the only reading that
refuses the trade below. Measured instance:
`salesagent-j3k2l.40` moved pending from 87 to 66 while emitted rose by 5 and verdicts by 16 —
sixteen of its twenty-one documents were resolved by deciding never to generate them, under a
metric that read the row as the largest step of the day.

**Two figures are both right and they count different things, so say which one you mean.** The
PARTITION is total and disjoint — `emitted | refusals == portable`, 0 unaccounted — and that is
**1054**. The GOAL is `emitted + VERDICTS`, because the condition above is "refused by name,
pointer and keyword" and a refusal still waiting on something is not a verdict; that is
**988**. Measured together on `sdk/j3k2l40-conjunct-reader`: portable 1054, emitted 691,
refused 363, of which 297 are verdicts and 66 are pending (65 `DEFERRED`, 1 `UNRESOLVED`).
Reporting 1054 for the goal overstates it by 66 and reporting 988 for the partition looks like
66 lost documents; both have been said of the same run.

**A refusal's KIND is an argument its producer passes (`refusal.Kind`) and is never read off
its detail.** Four separate readings of that English each made this number too high — see
§7.1 — so `refusal.is_a_verdict` now takes a `Kind` and holds no string at all, and a chained
refusal carries the refusal it chains to rather than quoting it for a parser.

**Every measurement in this build is taken over `schemas/cache/<version>/` excluding the
`bundled/` and `mcp/` directories.** Those two are projections of the same documents, so
counting them multiplies every figure. A number quoted without that exclusion is void.

Three further rules for any count, because each has produced a wrong figure:

- **Walk `$defs` and `definitions`.** A walk that descends only `properties`, `items`,
  `additionalProperties`, `not`, `propertyNames`, `allOf`, `anyOf`, `oneOf`, `if`, `then`,
  `else`, `patternProperties` and `contains` is blind to the internal nodes of 46 documents.
- **Count TYPE positions separately from rule positions.** Under `not`, `if`, `then` or `else`
  a keyword is a rule (D6) and no type is lowered from it, so a census that mixes the two is
  counting two different things.
- **A figure two instruments disagree about is not a fact.** Carry the range and say both, or
  leave the number out. Do not pick one.

The harness runs three checks, two of which keep the names the code gives them.

1. **The accepts check** (`check_accepts`), schema → payload → model: the class accepts every
   instance the document accepts.
2. **The refuses check** (`check_refuses`), model → mutated keyword → schema: the class refuses
   every instance the document refuses.
3. **The schema comparison**: the class's own `model_json_schema()` against the document
   `__adcp_schema__` names.

**The accepts check draws its instances and replays the document's own.** `hypothesis-jsonschema`
generates against the document, and 168 schema positions across 142 of the 1,057 documents also
carry `examples`, holding 553 payloads the spec states are valid. Those payloads are a
population, so the check feeds every one of them rather than sampling. `strict_validate`'s schema
half answers first, which splits the two outcomes without extra machinery: a published payload
the DOCUMENT refuses is a spec defect, reported by document and pointer and never charged to the
class; one the document accepts and the class refuses is ours. Generated instances stay sampled
at a stated `max_examples`, and `Phase.explicit` is not in the phase list because no `@example`
exists for it to run.

The first two call `strict_validate`, whose schema half answers first, so neither exercises the
annotations. A class carrying `Any` on every field and a faithful one produce **identical
reports**: on `core/pagination-request.json`, both accept, both refuse 75 of 75 instances, both
record no wrong acceptance. Dropping `extra="forbid"` and dropping a `pattern` measure the same
way. No reading of those two checks separates a faithful class from a widened one, and the
denominator is healthy in both, so nothing looks wrong.

**The schema comparison is what grades the generated code.** It is also the only check that
sees a default or a description, because neither changes the accepted set.

**So the harness grades one class against one schema, and it does not iterate over keywords.**
Per class: resolve the document once, draw a payload the schema accepts, construct the class
from it, dump the instance, and compare the dump against the schema. One payload the schema
refuses goes through the class's own validation. That is the whole harness, 1,055 units of work
rather than 13,140, and the only recursion anywhere in it belongs to reference resolution.

**Per-keyword step sites are removed, and the reason is stronger than their cost.** The refuses
check mutated one keyword at a time, drew an instance the mutated schema accepts, and passed it
to `strict_validate` — which runs `_refuse(schema_at(ref), payload, symbol)`, validating against
THE DOCUMENT and only then constructing. So a step site asserts that `jsonschema` rejects a
payload violating the schema it was handed. The generated class takes no part in the outcome,
which is why the paragraph above finds a class carrying `Any` on every field indistinguishable
from a faithful one. 27,791 of those sites is the suite's entire wall clock, spent on a
property of a third-party validator. The count grows with the emitted population; an earlier
revision quoted 13,140, measured before the population grew.

**PYDANTIC IS DELIBERATELY LESS STRICT THAN THE SCHEMA, so neither path makes a refusal
informative.** D4 is unchanged and correct: the schema decides acceptance and pydantic builds
the value. A model's job is to hold the document's types and to emit the document's schema, not
to reimplement every JSON Schema keyword — which is exactly why `strict_validate` exists. So a
payload the schema refuses tells you nothing about the generated code on either route.
`model_validate` MAY accept it, by design, and that is not a defect. `strict_validate` refuses
it because the document answered, and that is not a measurement of the class.

**So the refuses direction is a LIVENESS check on the wiring, needed once per class.** One
refused payload through `strict_validate` proves that class's schema half is connected and that
`__adcp_schema__` resolves to the document it names. That is worth asserting once, and it is
what the per-keyword sweep was already asserting 13,140 times.

**The conformance claim is carried entirely by the comparison.** `model_json_schema()` equal to
the document is the statement that every constraint reaching the model is the document's own and
no other — which is the only sense in which a generated class can be faithful, given that the
model is not the validator. A keyword the model does not carry shows up as `missing`, and a
constraint the model invents shows up as `added`. Nothing a per-keyword refusal sweep can
discover is absent from those two lists.

**Reference resolution happens once per bundle, and the packaged documents carry no `$ref` at
all** — 682 files, 0 occurrences, measured. So resolution is already done before the harness
runs, and it is NOT the reason canonicalisation repeats.

**Canonicalisation repeats inside the library's own recursion, and sharing it within one call is
required.** `hypothesis_jsonschema`'s `merged` re-enters `canonicalish` for every subschema it
sorts (`_canonicalise.py:631`), so a single `from_schema` call on one fully resolved document
re-canonicalises the same subtrees. Nothing upstream of the library can remove that. Measured on
`core/macro-declaration.json#` (18,301 bytes, one pair, one process, no pytest, no profiler):

| from_schema | time | memo entries | memory |
|---|---|---|---|
| sharing within the call | 43.58 s | 504 | 142 MB |
| no sharing at all | >600 s, stopped while still building | — | — |

One pair without sharing costs more than the whole population costs with it, so deleting the
sharing is not an option and an earlier revision of this section was wrong to require it.

**What is banned is the process-global form, not sharing.** `_CANON_MEMO` was a module-global
dict with no eviction, keyed on a serialized schema and holding a canonicalised copy per key: it
grew by roughly 340 entries per pair, retained everything for the life of the process, and
pushed a ten-worker run into a kernel kill at 83% with no summary. `_install_canon_memo` made it
worse by rebinding every holder at import time, from shipped code, after a `sys.modules` scan
that silently misses any later import.

**The sharing is scoped to one call**: a context manager around the accepts check that installs,
yields, and restores in a `finally`. It is bounded by one document's subschemas — 504 at the
measured worst — its lifetime is one call, it is discarded on return and on raise, and its size
is a figure rather than an unknown. A cache with a measured hit rate and no measured size is the
defect; a cache whose bound is one document and whose lifetime is one call is not that.

**The comparison folds out the RESOLVER's canonicalizations, and that is a named category
rather than a series of patches.** The harness grades against the document as
`hypothesis-jsonschema`'s own resolver inlines it — deliberately, so the schema the runtime
decides with is the schema the harness grades — and that resolver rewrites while it inlines. So
a faithful model can read as dropping a fact the DOCUMENT never stated. Four are known:

1. `_closed` — `additionalProperties` as the resolver spells it.
2. The `additionalProperties: true` branch of `_narrows_nothing`.
3. The finite-type rewrite (`_uncanonicalized`): a type whose value set is finite is written out
   as that set and **every annotation at the node is dropped** — `{"type": "boolean",
   "description": ...}` resolves to `{"enum": [false, true]}`. The `type` is restored because
   `enum: [false, true]` IS `type: boolean`; the `description` cannot be and is **not** copied
   off the model, because a fixture derived from the thing it grades falsifies nothing.
4. `uniqueItems: true` over a countable item set derives a `maxItems`: a two-member `enum` with
   `uniqueItems` resolves to the same node plus `maxItems: 2`.

**Each fold-out is GATED to its own shape and is not a licence.** The rule is that the fold
applies only where the resolver's rewrite is provably what produced the difference — the
finite-type fold admits a model-only `description` at a rewritten node and nowhere else, and the
`maxItems` fold applies only where the value equals exactly the item set's distinct-value count
beside `uniqueItems: true`. A fold that cannot state the equality it rests on is a widening
wearing this category's clothes.

**Every fold applies to both sides, and that is what makes the comparison symmetric.** Symmetry
is a construction, not a property to assert: `_normalize` serves the model side and the document
side from one body of code, each supplied its own `$ref` root, and a fold it applies to one side
it finds on the other — including one level down, inside a branch it folded. A fold running on
one side alone reports a faithful class as narrower than its own document, which is the `added`
direction and the only one that makes a correct SDK refuse valid traffic. Three instances existed
because `_normalize` was written for the side that visibly needed canonicalizing:

1. **A type list.** `creative/creative-feature-result.json` at `/properties/value` states
   `{"oneOf": [{"type": "boolean"}, {"type": "number"}, {"type": "string"}]}`. The class is
   `bool | float | str` and the fold rewrites pydantic's rendering of it as a type list, while
   the document keeps its `oneOf` — so the restored facts arrive as facts the model adds. A
   nested combinator states those facts inside a branch, which is where the document-side fold
   has to look for them.
2. **A local `$ref`.** `bundle.resolved` inlines a remote reference and leaves a local one, and
   the fold resolves a `$ref` on the model's side, so every fact the class correctly carries
   reads as added. Measured: 0 graded pairs of the committed tree hold a document-side local
   `$ref`, and the two documents this admits produce 43 added facts over 4 pairs.
3. **A conditional.** Conjuncts fold and conditionals do not, so the field a conditional needs
   in order to read its key reads as a property the document does not state.

**A class the comparison cannot grade is not emitted, and the comparison is not relaxed to
admit it.** A class no check grades satisfies the partition and demonstrates nothing, and
widening the comparison removes the only check that reads the generated code. The obligation
runs the other way — the harness row lands first, then the document emits and is graded. Such a
document stays pending, and its pending belongs to the harness rather than to a keyword row.
The instrument comes before the product.

**All three are closed, and two of them were closed by the harness row that had already
landed.** `salesagent-j3k2l.32` and `.33` made `_normalize` serve both sides with a per-side
`$ref` root and taught it to read `oneOf` as well as `anyOf` and to read each branch through
the finite-type rewrite one level down — so 1 and 2 were already answered while the refusals
that cited them stayed in place, each stating as its reason a claim about a harness that had
since changed. **A refusal's reason is a measurement and goes stale like one.** Measured by
lifting each guard and grading the whole population (`salesagent-j3k2l.28`): the local-`$ref`
guard cost **8 documents** and produced **0 reports of any kind** once lifted — its 43 `added`
facts have no site left — and the type-list guard cost **9**, both of whose fold arms grade
green. Number 3 is different: its refusal names "the field a conditional needs in order to read
its key", and no such field is ever emitted. `Rules.properties` collected a conditional-only
property declaration and **nothing ever turned one into a field** — the refusal was its only
reader — so the `added` fact it refused to risk had no producer, and `si-ui-element.json` with
its two referrers grades green. The guard, the carrier and the collector are gone together.
Together the three took emitted from **691 to 705 of 1054 portable**, and `added` stayed 0.

**And the local-`$ref` guard DID still hold, for a reason it never stated — which is why the
comparison is one of three checks and not the whole verdict.** Its stated reason was about the
comparison and was stale; what was still true is that a NODE is not a resolution scope.
`SchemaRef(document, "#/definitions/box_decoration")` names a node whose own
`{"$ref": "#/definitions/rectangle"}` is a pointer into the DOCUMENT ROOT, so given the node
alone the PRODUCT raised `PointerToNowhere` and `strict_validate` refused **every** payload
including the ones the document accepts, while the INSTRUMENT's generator raised
`_RefResolutionError` and the accepts check labelled it `model_error` — a statement about the
generator wearing the model's name. Both were invisible to the comparison, which reported
`added` 0 / `missing` 0 / `differs` 0 over all 1,085 pairs on the same tree. **A count is
evidence for its own instrument and for no other.**

Both halves are answered by giving the node its document as the scope, and the two answers must
agree because §6 grades the schema the runtime decides with. `_base._refuse_at` reads the
document once and evolves a document-rooted validator onto the node — one call, so a caller
cannot supply a node without its root — and `harness.check_pair` resolves the node against
`pair.document` for the two INSTANCE checks. The COMPARISON keeps the UNRESOLVED node on
purpose: what it grades is what the document STATES at that pointer, and `_normalize`'s
both-sided `$ref` reading has exactly these pairs as its bundle population, so grading the
inlined node would take that reading back to 0 sites. Measured: **0** graded pairs held a
document-side local `$ref` before this row, which is what made the outcome pin green for free,
and it is now **24 sites over 2 documents**.

**Number 3 is applied to an `allOf` CONJUNCT as well as to the node, and before the conjunct's
facts are folded in.** A conjunct is an inlined base and arrives already resolved, so the
rewrite has dropped the `type` off any boolean the base declared. Gap-filling that conjunct's
`enum` left the merged node carrying an enum and no type — neither spelling of the fact, and a
shape no document states — so the rewrite could be undone at neither end: `_uncanonicalized`
matches an exactly-canonical node and the fifth fold's gate correctly demands
`type == "boolean"`. Measured at 9 facts over 5 `formats/canonical` documents, each restating an
inherited boolean with nothing but a `default` and a `description`
(`salesagent-j3k2l.28`). Reading the conjunct through the same canonicalization hands the fold
`{"type": "boolean"}` — the document's own spelling of the same accepted set — and the pair
grades the accepted set as a `type`. **This is the fold moving to the canonicalization that owns
the rewrite, not a gate being widened**; the fifth fold's `enum` arm is left exactly as it was,
and its bundle population is now 0 because all 5 of its sites were conjunct-supplied enums
(`/properties/replayed`, five response documents). The arm stays for the shape it is for — a
document stating the pair in its own node, which draft-07 permits — graded by its 3 positive and
12 negative hand-written cases rather than by the bundle.

**Expect more of these, and expect each to appear when a document first reaches it.** Number 3
was unreachable until a referenced plain boolean emitted and number 4 until a document carrying
`uniqueItems` did, so the arrival of a fifth is a sign the emitted population grew rather than
that the comparison is wrong.

**One arrived on cue, and it is the one fold that CANNOT be a one-sided restoration.**
`canonicalish` writes a one-member `enum` out as a `const` — the same mechanism as number 3, at
a set of one rather than at a type's whole domain, and dropping the node's `type` and
`description` the same way. Measured on the pair that first reached it:
`creative/audit-observation.json`'s own resolved `code` node is
`{"type": "string", "enum": ["OVERSIGHT_DISCLOSURE_CARVEOUT_CLAIMED"], "description": ...}` and
the copy inlined into `creative/get-creative-features-terminal-success.json` is
`{"const": "OVERSIGHT_DISCLOSURE_CARVEOUT_CLAIMED"}` — so a class faithful to the spelling its
own document wrote reported as both dropping a `const` and adding an `enum`, 3 facts in each
direction over 1 pair (`salesagent-j3k2l.28`).

**A restoration cannot answer it, because after resolution the two cases are the same bytes.**
A document that wrote `const: v` and one that wrote `enum: [v]` both reach the comparison as
`{"const": v}`, and the resolver dropped the keys that would have told them apart — so no gate
can ask which it was, and numbers 3 and 4's exact-node discipline has nothing to match on.
What is available is the equality itself: `const: v` and `enum: [v]` admit the same instance,
so `_one_member_enum` writes the one-member spelling as the `const` it is **on both sides and
on an `allOf` conjunct too**, which is this section's own rule applied to a spelling rather than
to a rewrite. Toward `const` and not toward `enum`, because the rows that answer the dropped
`type` and the dropped `description` at a one-member set are already there and keyed on a
`const` — `_entails_type`'s `const` derivation over **832 typeless const nodes** and
`_narrows_nothing`'s `const` row — and folding the other way would have left both answering
nothing while a second derivation over the `enum` answered instead.

**What that costs is a difference `salesagent-j3k2l.33` pinned as a rendering question, and
this section settles it the other way.** A document stating `const: x` whose class renders a
one-member enumeration no longer reports, and the pin that required it to
(`test_a_const_at_a_named_node_is_a_rendering_question_and_is_not_silenced`) is replaced by one
that requires every different ACCEPTED SET to report. The ground is this section's own: a test
that fails while the emitted behaviour is unchanged is grading a spelling, and D14 says a check
asserts what a class accepts, refuses or states about itself and never the text that expresses
it. `{"const": "x", "type": "string"}` and `{"enum": ["x"], "type": "string"}` are the same
statement about every instance.

**A `description` is NEVER folded, and this is the one difference the comparison must keep.**
A fold hides every future divergence at the pointer it covers, and a description is the one fact
in these documents a human reads. Where the comparison reports one, the emitter is wrong and the
emitter is what changes.

**The last `missing` in the comparison was the emitter changing, and what it changed was a
CARRIER rather than a rule.** An annotation on a node INSIDE a container had nowhere to go, and
unlike a constraint it was dropped in silence: `containers._inner` refuses a constraint or a
`format` it cannot carry BY NAME, because dropping one would widen the model, while a
`description` narrows nothing and so went nowhere with no refusal and no rendering. That was the
whole of `comparison.missing` — **4 facts over 4 pairs**, every one
`.../additionalProperties/description` and every one `'Component properties'`
(`a2ui/component.json`, `a2ui/surface.json`, and the two `sponsored-intelligence` responses that
compose a surface). The fix is the mechanism this pipeline already has for a node whose facts
need a carrier: `containers._contents` NAMES such a node through the same
`compiler.name_the_node` a fragment-referenced node goes through, so the annotation on a
container's contents and the annotation on a referenced node have one spelling, and
`dict[str, X]` over a local symbol is a plain reference the compiler needs nothing extra for.
It applies at an array's element and a mapping's value and nowhere else: a multi-type ARM is the
node re-cut, so its annotations are the node's own and the field holding the union already
carries them, and a `propertyNames` node is a statement about a key. Measured cost: **2 lines in
one emitted module**, and `missing` reached 0 over 1085 graded pairs.

**The description-authority rule: a document's own declaration carries the description at its
own pointer.** Three documents can state a description for one field — the `$ref` target, the
referring node as a SIBLING of its `$ref`, and a composed base's declaration of the same key —
and the model renders one. The rule, in the order it resolves:

1. **The referring node's own sibling beats its `$ref` target's.** Draft-07 says a `$ref`
   IGNORES its siblings; this bundle plainly intends them, 147 documents state a body-level
   `context` that `$ref`s `core/context.json`, and `core/protocol-envelope.json`'s own text
   discusses the relationship. The resolver the harness grades through MERGES a `$ref`'s
   siblings with the OUTER keys winning, so taking the sibling is also the only reading under
   which the two halves agree. Draft-07's reading is why a CONSTRAINT sibling refuses by name
   (`emit.decide_type`) rather than being silently dropped: an accepted set cannot be read two
   ways, where an annotation can and this says which.
2. **A composed base's declaration of the same key loses to the document's own.** Where a
   subclass declares a key its base also declares and says the same thing about the INSTANCE,
   the field is the base's field and the annotation is the document's: a class must not state,
   at a pointer its own document declares, a description that document does not carry. Measured
   on trunk `9e9da67e1`: 15 of 43 `differs`, every one at `/properties/context/description`, a
   response root composing `core/protocol-envelope.json` whose envelope states the long
   "Relationship to per-task body-level `context` declarations" text as a `$ref` sibling.
3. **Silence inherits.** A subclass that does not declare the key declares no field, and the
   base's annotation is the one there is.

Clause 2 is gated on the restatement's constraining content being NON-EMPTY and equal to the
base's, which is what keeps it from becoming the shadow §4 forbids: equal constraining content
lowers to the base's own type, so the field is the inherited field with a different annotation.
A restatement stating ONLY annotations over a typed base is the other shape and still inherits —
lowering it alone types it `Any` and drops every fact the base states. The 28 remaining `differs`
(14 `description`, 14 `default`, over 7 `formats/canonical/*.json`) are that shape, and
`salesagent-j3k2l.22` owns them; two of the 14 defaults are inversions, where the model's boolean
default is the opposite of the document's.

**The export rule: a module's `__all__` names every symbol that can cross a module boundary, and
a symbol crosses in exactly two ways.** `emit.exported` is the whole of it: the root, the symbol
at every pointer the BUNDLE names, and the field types of a class the bundle COMPOSES. The import
side and the export side then read the same facts, so the emitter cannot disagree with itself
about what a module offers.

It disagreed for a while, and that is why this is written down. The binder resolves a fragment
reference to `mod.declared[into]`, section 2's rule being an import of a symbol the target
DECLARES, while the writer exported the root alone: measured on `ac9175209`, **16 of the
committed tree's 957 relative-import aliases** named a symbol the target module declared and did
not export. Nothing raised, because Python does not consult `__all__` on import, and
importability is already graded by the whole-tree import in `tests/test_emit.py` — so the
defect was invisible to everything except a check on what a module DECLARES, which is what
`test_the_emitted_tree_still_declares_every_module_it_imports` is for.

**The symbols are exported rather than the imports removed**, and the alternative is excluded on
this plan's own grounds rather than by a measurement. Its two readings are *reach the alias
through its owning module*, which is the import under discussion and so is not a change, and
*emit the alias where it is used*, which is a second name for one document node (P2). And the
thing copied is in most cases not an alias at all: the 16 name 8 distinct symbols, 4 of them
`StrEnum` CLASSES accounting for 9 of the 16 imports, one of which
(`ReportingDeliveryOfferingReportingFeedPurpose`) is imported by 6 modules — so copying would be
7 classes for one document node, which is the flatten-a-`$ref`-into-a-copy defect
`test_a_cross_document_reference_is_an_import_and_not_a_copy` exists to catch.

**The second way a symbol crosses was found by the same assertion, one row later.**
`salesagent-j3k2l.36` landed a subclass that re-uses a composed base's decided field, and
`formats/canonical/_base.py`'s `CanonicalFormatBaseSlotsItem` then crossed into 7 modules with no
`$ref` naming it — the bundle-named clause cannot reach it, because the lowering and not a
reference created the edge. Under `allOf` a subclass inherits the base's fields and may restate
one, and the description-authority rule's clause 2 says a restatement is then the base's FIELD
wearing this document's annotations, so the base's own field types necessarily cross into every
module that composes it. Re-deciding the base's node instead was measured and is wrong: it
declares a second `...SlotsItem` at a pointer the subclass's document does not have. So the
import is this plan's own answer and the export has to match it. `emit._composed_nodes` is the
companion to `bundle.named_nodes` and the same kind of fact — one scan of the bundle, not of the
run — and ONE restatement is as deep as it goes, because a subclass restates a key the base
declares and a field of a nested item is not a key of the subclass. A `Target` is minted for the
root or a named node and for nothing else, so no other class's fields can cross.

**Every declared symbol would be wider than the demand and wrong about why.** Measured on the
committed tree at `2360ff7f1`: the rule above is **717 names with 24 of 677 modules exporting
more than one**, and it meets the demand exactly — every symbol the tree imports is in it, 0 of
964 aliases unexported. Every declared symbol is **1,314 names over 228 modules**, and the extra
597 are nested classes nothing can ask for, reached through their parent's own annotation. Taking
the annotations of every root rather than a composed one is **1,053 over 194**, barely narrower
and discriminating on nothing. Both facts the rule reads are functions of (bundle, document) and
not of the run's document set, so P7 holds and the one-document command writes the same bytes as
the whole-population run. The root goes first in the list.

**The alias population is re-measured at every step and never carried**: 910 at `0130e5fc9`, 957
at `ac9175209`, 964 at `2360ff7f1`. It is a property of the committed tree, so it belongs to the
`population()` run — 677 modules — and not to the 686-of-1054 metric run.

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

**This table listed eleven steps and the work is twenty.** The eleven below do not reach the
population §6's exit condition declares: measured on the bundle, **385 documents refused with a
detail saying a later row would cover them, and no later row existed** — step 9 adds no lowering
rule by its own text, step 10 is the public surface and step 11 is closeout. So after step 11
the generator would have stopped near 400 of 1,054 with `emitted + refused == 1,054` asserted and
green. Nine more rows close that gap, filed as `salesagent-j3k2l.16` through `.24` and each
gating step 9:

| row | keyword, and where it sits | measured refusals |
|---|---|---|
| `.16` | `const`, at a property or nested — never at a root | 82 |
| `.17` | `if`/`then`/`else`, in a conjunct or at a root | 76 |
| `.18` | the `allOf` shapes step 4's row defers | 68 |
| `.19` | `uniqueItems`, at a property or a root | 50 |
| `.20` | `definitions` and `$defs` — **closed**; a section is not a root kind, so it is the walk and not a row | 40 |
| `.21` | a root `type` list, and the declared-`null` arm the comparison could not tell from an optional | 24 |
| `.22` | `not`, `dependencies`, and the remaining object-size keywords | 60 |
| `.23` | a bundle annotation (`notes`, `enumMetadata`, `last_updated`) is IGNORED, not lowered — there is nothing to lower | 4 |
| `.24` | read a branch's type from its root before refusing the branch — **closed**; a bug, not a row | 10 |

### 7.1 Where the metric actually stands, and the counts above are not it

**The counts in the table above are the refusals each row was FILED against, not the work
remaining.** They were measured on different trees over several days, they overlap (one document
is refused once but blocked by several rows), and four of the rows have since closed. Read them
as the reason each row exists. Read the table below as the state.

Measured on `sdk/j3k2l40-conjunct-reader`, by **the `refusal.Kind` each producer declares**
— never by reading a detail string, and no longer by comparing one against a constant either:

| | documents | |
|---|---|---|
| emitted and graded | 691 | |
| refused by a VERDICT naming a keyword this emitter will not lower | 297 | |
| **accounted for** | **988** | of 1,054 |
| deferred — the lowering for the position is not written, or is not reachable from this row | 65 | pending, not refused |
| unresolved — a `$ref` the bundle's one resolution did not reach | 1 | pending |

Of the 363 refusals, 155 DECLARE `VERDICT`, 38 declare `DEFERRED`, 1 declares `UNRESOLVED`
and 169 declare `CHAINED`; a chained refusal carries the target's refusal (`through=`), so its
`resolved` kind is the target's and the 169 split 142 verdict / 27 deferred.

**967 → 988 and 87 → 66 is `salesagent-j3k2l.40`**, which moved the conjunct reader into
`codegen/compiler.py` so that a union BRANCH that composes could reach it — D13's own rule,
which says shared machinery lives there. All 10 documents waiting on "a branch composes once
that reader is shared" cleared that row (3 emitted, 6 accounted as verdicts, 1 moved on to the
conjunct-SHAPE gap the product row's 12 are on, taking it to 13), and 12 chained refusals
released with them. `comparison.added` stays 0, measured over every pair of the regenerated
tree. The remaining 66 are enumerated in `docs/plan/j3k2l40-prediction.md`.

**`emitted + refused == 1054` is green and has been all along, which is why it is not the
condition.** "Refused" admits "not built yet": the metric's own arithmetic held while part of
that 476 was unwritten work. `test_a_refusal_that_is_a_verdict_is_counted_apart_from_one_that_is_pending`
now partitions it, with `deferred` and `unresolved` pinned shrink-only and `accounted` grow-only,
so a row landing moves all three one way and anything else reddens.

**THE FOURTH ROW IS A CORRECTION, AND EVERY ABSOLUTE THIS PLAN PREVIOUSLY CARRIED WAS
OVERSTATED.** `refusal.is_a_verdict` read a refusal's own sentence and nothing else, so a
refusal reading `its target X is refused: <X's whole refusal>` matched neither pending
constant and counted as a verdict however X's refusal read. Measured: **170 of 380 refusals
are chained that way.** Resolving the chain — a chained refusal is a verdict if and only if
what it is chained to is one — moves accounted from 1005 to 975 and pending from 48 to 79.

The bias was present on every tree this epic reported, so **1005, 951 and 877 were all
overstated** while the DELTAS between rows were right. `refusal.py`'s own rule, "a fourth
kind means a fourth constant here, not a regex somewhere else", was right about the rule and
wrong about this case: this is not a fourth constant but TRANSITIVITY, and the producer
already embeds the target's whole refusal after `is refused: `, so the answer was in the
string the whole time.

**THE FIFTH IS THE SAME CORRECTION A FOURTH TIME, AND IT IS THE LAST ONE OF ITS KIND.** The
four instances above all read the same way: a refusal meaning "no row does this yet" counted
as one meaning "this emitter never will". Each was fixed by reading the refusal's English more
carefully — a constant instead of a regex, then a recursion through the quoted chain — and
each time a category the reading did not know about landed in whichever bucket its sentence
happened not to match. Of the 367 verdicts the third fix left, **86 state in their own text
that the lowering for the position has not been written**: "a later D2 row lowers this one",
"a branch composes once that reader is shared", "the harness's row", "step 6", "step 7's
rule". 47 say it directly and 39 chain onto one that does.

`salesagent-j3k2l.37` stops reading the sentence. Every producer passes a `refusal.Kind`,
`refusal.is_a_verdict` takes one and holds no string, and a chained refusal carries the target
REFUSAL rather than quoting its text for a parser. **Accounted falls 1053 → 967 and pending
rises 1 → 87.** Nothing about what emits moved: 686 emitted and every emitted byte identical
to `d9989750c`, every refusal's keyword, pointer and detail identical, `comparison.added` 0.
A number that falls when the instrument improves is the instrument working.

The partition can no longer absorb a sixth category. `Kind`'s members are covered exactly by
three named sets — final, pending, delegating — and the partition test's FIRST assertion is
that coverage, so a new member reddens before a document is counted. Probed both ways: a new
`Kind` named in no set fails that assertion with the member named, and a live producer raising
a new PENDING kind drops accounted to 966 and fails the grow-only pin.
The per-producer classification is `docs/plan/j3k2l37-prediction.md`.

The deferrals partition by the keyword each waits on, and every one is owned. The counts
below are the pre-`.22` reading and `.22` has since cleared four of these families entirely
(`not`, `dependencies`, `minProperties`, `maxProperties` are all 0 now); the current
deferral set is `oneOf` 23, `anyOf` 10, `uniqueItems` 7, `contains` 5, `enum` 2, `items` 1,
all of them `.26`'s:

| keyword | documents | owner |
|---|---|---|
| `anyOf` | 26 | `.26` |
| `not` | 22 | `.22` |
| `oneOf` | 12 | `.26` |
| `dependencies` | 10 | `.22` |
| `minProperties` | 7 | `.22` |
| `if` | 7 | `.17` |
| `uniqueItems` | 6 | `.26` |
| `maxProperties` | 5 | `.22` |
| the remainder | 7 | `.26`, `.17` |

`.26` exists because **`ROWS` partitions by ROOT KIND.** Every keyword it owns already has a
CLOSED row — `.5` for union roots, `.19` for `uniqueItems`, `.3` for enums, `.12` for named
constrained types — and those rows are not defective. A row selected on a root claims a document
whose root composes; the same keyword at `/properties/x/items` is a different position that no
root selector sees. Do not reopen a closed row to swallow both.

### 7.2 The rows that are not keyword rows

Four issues were filed after this table and none of them adds a lowering:

| | what it is | state |
|---|---|---|
| `.25` | the suite's wall-clock: the `canonicalish` memo, 1.27× measured | superseded in part by `.27` |
| `.27` | two tests per class instead of 25 per step site — **63× on the reference pair** | the constructed-witness upgrade is deferred, not cancelled |
| `.28` | the symmetric comparison is red: 10 no-op facts to fold by shape, 13 `description` divergences to fix | open |
| `.26` | the keywords above, below a root | open |

**`.27` is why any of this is verifiable.** `refuses_examples` is per STEP SITE, so 25 over the
13,123 sites this suite steps drew 328,075 instances and the suite ran about six hours at eight
workers. Three full-suite runs were launched and killed in one day, and `.21` was committed with
its verification explicitly in flight. The ceiling that buys the 63× is stated on `check_pair`
itself: a site whose single instance does not happen to violate the stepped keyword reports as a
control rather than a grade.

**`.28` is a fidelity gap and not a safety defect, and the distinction is the whole of it.**
`added` is **0** over the whole population — the model narrows nothing anywhere, which is the
half that could admit an invalid instance. The 10 missing facts are `required: []` and
`enum: [false, true]` on a boolean, which constrain nothing; the 13 differs are all
`/properties/context/description`, where the emitter takes the `$ref` target's description
instead of the referring document's. Attribution was measured, not assumed: pre-`.21` trunk
graded 734 pairs with 1 discrepancy, post-`.21` grades 808 with 23, so `.21` made 74 more
documents emittable and they exercise a defect that was already there.

**A row's refusal count is not its value.** Measured by an independent audit over the 179
`-request`/`-response` documents — the only ones a consumer imports — `notes` is rank 20 by
refusal count and **gates 35** of the 167 uncovered, while `const` is rank 1 and gates 3. Two
leaf documents gate 65 of the 167: `core/protocol-envelope.json` on `notes` and
`core/brand-ref.json` on `uniqueItems`.

**And the rows compose multiplicatively on that surface, not additively.** A tool document needs
EVERY blocker in its `$ref` chain cleared, so a single row moves the bundle count while the task
surface stays flat, then jumps when the last blocker falls. Measured: `.19` removes
`core/brand-ref.json`'s `uniqueItems` blocker and the document still does not emit, because its
next blocker is a `const` that `.16` owns — the 30 documents it gates need both rows and neither
alone buys one. A step-by-step bundle count cannot show this, which is why §6 reports the
refusal partition and the task surface beside the total.

| # | step | done when | parallel |
|---|---|---|---|
| 1 (`salesagent-j3k2l.1`) | **One leaf object document, end to end** — `core/pagination-request.json`: our walk decides what the node becomes, the compiler renders it, the class carries `__adcp_schema__`, `strict_validate` reads it, the harness runs all three checks off it | the module imports; `max_results` carries `ge=1, le=100` **and `= 50`**; the schema comparison passes; all three checks are generic over any class | no — runs alone |
| 2 (`salesagent-j3k2l.2`) | **A cross-document `$ref`** — the referencing module imports its target's type and copies no constraint, asserted on the AST; the target emits as an alias | both documents pass all three checks | no — runs alone |
| 3 (`salesagent-j3k2l.3`) | **Enumerations**, root and inline — members upper-cased, since `pass` and `global` are live values and a lower-cased member emits a module that does not parse; the injectivity check binds to the name function the compiler runs | every root enum emits or is refused by name; `enumDescriptions` carried | yes — `lower/enum.py` |
| 4 (`salesagent-j3k2l.4`) | **`allOf` roots** — `$ref` conjuncts become bases; composed constraints on one property intersect; a requiredness-tightening overlay redeclares the field with the base's type and no default, and that is the only permitted redeclaration (D7) | no emitted field shadows a typed base field EXCEPT a requiredness tightening, which 37 documents need; a composed `ge`/`le` inherits; a composed enum is the intersection of its members and an empty one refuses | yes — `compiler.lower_composition` (it was `lower/product.py` until `salesagent-j3k2l.40`, which moved it where D13 puts machinery two rows read) |
| 5 (`salesagent-j3k2l.5`) | **Union roots** — the base carries `BranchDispatchMixin` and declares `_branch_models`, `_ROOT_REQUIRED` and `_branch_combinator`; one subclass per branch; the declaring module calls `model_rebuild(force=True)`; the root name binds the base (§4) | a payload resolves to its branch on all four paths — nested field, `TypeAdapter`, `model_validate`, `Base(**data)`; a consumer's subclass of the base keeps its own schema; `model_dump_json` on a base instance does not raise; a branch with no derivable name refuses its document by name and pointer | yes — `lower/union.py` |
| 6 (`salesagent-j3k2l.6`) | **Containers and mappings** — a constrained container value is a named type (D5), so a mapping is a plain reference; a mapping's key is typed from `propertyNames`; a multi-type property applies each keyword to its own branch | a mapping value's bound survives into the annotation, and a key the document constrains is not `str` | yes — `lower/containers.py` |
| 7 (`salesagent-j3k2l.7`) | **Rules** — D6's six keyword families as class-level tuples read by `_runtime.py` | the harness steps every one of the six | yes — `lower/rules.py` |
| 8 (`salesagent-j3k2l.12`) | **Name a constrained type once** — the resolution order in D5, with `adcp.types.constraints` holding the aliases that belong to no document; a standard type admitted only with both its measurements shown | the emitted tree's inline repeats drop to the shapes that occur once; N does not drop | after 3–7 |
| 9 (`salesagent-j3k2l.8`) | **The whole bundle** — `--all` emits or refuses every document | emitted plus refused equals the bundle size, asserted; every refusal named | after 8 |
| 10 (`salesagent-j3k2l.9`) | **Public surface** — one per-domain package per bundle directory, generated, PEP 562 lazy; no aggregate re-export; a class name bound to two nodes in one domain is a build failure; the build emits a class-name-to-module mapping as a lookup table | `from adcp.types.<domain> import X` is the only spelling that reaches a class, and the mapping resolves any class name to exactly one module | after 8 |
| 11 (`salesagent-j3k2l.11`) | **Closeout** — the bundle version derived rather than written; `make validate-generated` wired; any compiler patch we carry filed upstream | `tox` green | last |

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

**`docs/plan/sdk-type-generation.md` P8 does not bind.** It makes the flat root a second total
import path, `adcp.types.<Class>` resolving for every class alongside the per-domain one. This
specification keeps one path (§1) and that clause of P8 is superseded; the rest of P8 binds,
including its collision rule — a class name bound to two nodes is a build failure naming both,
never a rename table.

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
