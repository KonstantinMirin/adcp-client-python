# Rebuild plan: work the schema, emit the files

Written at `42b63fcc4` on `analysis/rebuild-plan`, in this worktree's own venv
(`env -u VIRTUAL_ENV uv sync --all-extras`). Inputs: `docs/analysis/design-audit.md`,
`docs/design/type-generation-rebuild.html` (a record of decisions, not a specification),
`sa-land-324/docs/design/sdk-type-generation.md` (P1–P13, binding), and
`docs/analysis/defect-inventory.md`. Every number here was re-derived in this tree; the
scripts are in `docs/analysis/spike/`.

## 1. The route: emit directly from the node graph (Route B). The dmcg pin goes.

The spike (`docs/analysis/spike/`) lowers three hand-written schemas — an object with
constraints and `extra='forbid'`, a string enum, and a `oneOf` over required sets rendered as
base + branches + union alias — once into dmcg's `DataModel` layer (`route_a.py`) and once
straight to text (`route_b.py`). Both outputs were graded by `codegen.harness.check_pair`
against the same three schemas (`grade.py`). The verdict is identical: all three pass in both
directions (direction 1: 25/3/25 examples accepted; direction 2: 7/1/5 keyword sites, every
mutation refused, 0 `no_evidence`).

| measured on the same three cases | Route A (dmcg `model/`) | Route B (direct) |
|---|---|---|
| code lines to lower and render (non-blank, non-comment, non-docstring) | **104** | **65** |
| of which pure conformance to the library's data model | 39 | 0 |
| attempts before the first complete render | 5 | 1 |
| undocumented gates found by failure | 4 | 0 |
| `oneOf` rule the library renders | `@model_validator(mode='before')` — the mode the design rejects (P12; a before-validator collapses a repeated JSON key) | `mode='after'`, 7 lines, hand-written |
| emitted module | 96 lines (a 44-line `_JsonSchemaRuntimeValidationBase` helper per module) | 44 lines |
| imports at run time | 37 dmcg modules; `sort_data_models` lives in `parser/base.py` (9,462 lines), which the old plan said to delete | `pydantic` only |

The four gates, each one a silent wrong answer until found: `sort_data_models` returns
`(unresolved, {path: model}, ...)` and the first element is empty on success; a field's
`constraints` must be the raw JSON-Schema dict, not a `Constraints` instance; a rule is lifted
into the model only when supplied at construction, never by assignment after; and the rule
renders nothing unless `extra_template_data["schema_runtime_validation_enabled"]` is set,
which is the parser's CLI flag leaking through. None is in a docstring.

What Route A would have given for free, priced for Route B at bundle scale: the constraint
alias table (12 keywords → `Field` kwargs, **~12 lines**, already in `route_b.py`); the
format → Python type table (`date`, `date-time`, `uri`, `uuid`, …; **~25 lines**); import
bookkeeping across modules (**~30 lines**: the node graph already carries every `$ref` as an
edge, so an import is an edge whose target is in another document); class ordering within a
module (**~15 lines**: a DFS post-order over the same edges, and `node_graph.back_edges()`
is 0 so there is no forward reference to defer); a formatter (**0 lines**: the emitter owns
its layout, which also makes P7 hold by construction rather than through a pinned
formatter). Roughly 80 lines, against conforming the whole lowering to a 14,131-line model
layer whose only public contract is "the parser calls it this way".

The lowering — deciding what each node IS — is the same size on both routes; the spike's
ratio is over the rendering half only. That is the decision: Route A adds a second
translation (our shape → dmcg's objects) on top of the one we must write anyway, and the
thing it buys back (the rules) comes in the wrong validator mode. **Route B. Remove
`datamodel-code-generator` from `pyproject.toml` in step 11**, after nothing imports it.

## 2. What stays, what is parked, what is decided now

**Kept and used from step 1:** `codegen/resolved_cache.py`, `codegen/node_graph.py`,
`codegen/harness.py` + `selfcheck.py`, `codegen/adapter_adcp.py`'s bundle loader and
portable filter. **Parked, unimported:** `node_names.py`, `module_table.py`; step 11
deletes whichever no step imported.

Nine decisions, taken here so that no step can be forced to re-decide them. Each cites the
principle that forces it.

- **D1 — definition site is a function of the document path.** `core/date-range.json`
  emits to `src/adcp/types/_schemas/core/date_range.py`. No module table: the module is
  the path with hyphens as underscores. P8 makes the schema module private, so this path is
  never public and never a contract; the public paths are generated in step 9 from the
  binding table. Churn risk: none — a private path cannot be wrong, only inconvenient.
- **D2 — what becomes a class.** An object node with `properties` → `BaseModel`; an `enum`
  node → `StrEnum`/`IntEnum`; a `oneOf`/`anyOf` node → a base (the plain name) plus one
  subclass per branch plus `<Name>Branches` alias. Nothing else is a class: scalar →
  `Annotated[str, Field(...)]`; array → `list[X]` with constraints; typed
  `additionalProperties`/`patternProperties` → `dict[str, X]` with constraints; `const` →
  `Literal`; typeless → `Any`; a `required`-only overlay, `not`, `if`/`then`/`else`,
  `dependencies`, `min`/`maxProperties`, `uniqueItems` → a **rule** on the nearest class. A
  root array → `RootModel[list[X]]` (kept from the old plan: the document is a list and
  there is no field to hang it on); a root scalar or mapping → a module-level `Annotated`
  alias. P2 one-node-one-class, and the old plan's own finding that "needing a name produces
  the wrapper, not the constraint". This is what dissolves 22 of the 30 "unnameable" nodes
  (audit F4 a, b): they are never asked for a name.
- **D3 — names.** Root: `pascal_case(title)`, the `_schema_title_to_class_name` spelling
  that keeps acronyms. Nested object or enum: parent name + `pascal_case(property)`. Union
  branch: title → discriminator `const` → sorted required set → **refuse**. A refusal
  refuses the DOCUMENT, by name and pointer, and it is counted (§5). P1, P5. Identical
  nodes (same content, two URIs) are one node — both authorities already say so (audit
  F4, `.19`); this is the only dedup, and it is by content equality, not by shape.
- **D4 — optional is absent or valid, never null (P12).** An optional property renders
  `Annotated[T | None, AfterValidator(refuse_null)] = None` through one shared alias in
  `src/adcp/types/_base.py`; `T | None` without the validator only where the schema admits
  null (`type` lists `"null"`, or the property declares no `type`). **This overrides the old
  plan's "accept an explicit null" decision**: P12 is binding and the plan is not. The cost
  P12 names — the after-validator on ~7,000 annotations disables pydantic's serialization
  fast path — is accepted. Defect D1-a (a typeless property refusing null) is fixed by the
  typeless → `Any` row of D2, not by dropping the validator.
- **D5 — rules are after-validators, hand-written once.** `src/adcp/types/_runtime.py`
  carries `RequiredGroups` (`anyOf`/`oneOf`/`not` over `required`), `ConditionalRequired`,
  `PropertyCount`, `UniqueItems`, `Dependencies`, each a dataclass plus one
  `model_validator(mode="after")` on `AdCPBaseModel` that reads a class-level tuple the
  emitter writes. The spike's `_one_of_required_groups` is the first of them. P12's mode
  correction; P3 for the 270 documents the old pipeline dropped.
- **D6 — bases are derived, not classified.** Every object class inherits `AdCPBaseModel`
  (hand-written, `_base.py`). An `allOf` of `$ref`s makes those classes the bases, so a
  request that composes `core/version-envelope.json` inherits the generated
  `VersionEnvelope`. There is no `AdcpRequest`/`AdcpResponse`/`ProtocolEnvelope` marker
  policy: that was a 1,659-site hand classification keyed on filenames, which P5 forbids.
  Anything a caller wants to `isinstance` against is a schema the document composes.
- **D7 — `extra` is derived (P3).** `additionalProperties: false` → `forbid`; `true` →
  `allow`; absent → the base's default; typed → `allow` with `__pydantic_extra__: dict[str, X]`.
- **D8 — no formatter, no patch pass (P7, P10, P11).** The emitter writes its own layout,
  documents in sorted order, and `make validate-generated` byte-compares the committed tree
  to a fresh run. A defect is fixed in the emitter or refused; nothing rewrites output.
- **D9 — the bundle directory is an argument from day 1 (P9).** `python -m codegen.emit
  --bundle <dir>`; step 11 wires the derivation from `adcp.get_adcp_spec_version()`.
  No version literal is ever written into `codegen/`.

Layout that makes the shapes parallel: `codegen/emit.py` (CLI, module writer, imports,
ordering, the refusal report) and `codegen/lower/<shape>.py`, one module per D2 row, with
`codegen/lower/__init__.py` holding the one dispatch table (node → lowering). A lane adds one
row to the table and owns one file.

## 3. The steps

Every step after 0 ends with Python emitted by `codegen.emit` and graded green by the harness
against the emitting document, in both directions. "N" is the metric in §5. Step 1 is the
whole pipeline on one document; steps 3–7 widen the lowering and share nothing but the
dispatch table.

| # | step | outcome (observable) | population; predicted ΔN | churn: what could force a re-decision, and why it cannot | principles | parallel |
|---|---|---|---|---|---|---|
| 0 | **Spike** (done) | `docs/analysis/spike/`: `route_a.py`, `route_b.py` both render; `grade.py a` and `grade.py b` print identical green verdicts; §1 table | — | — | P3, P10 (graded by the harness, not by eye) | — |
| 1 | **One leaf object document**: `core/pagination-request.json` (object, `minimum`/`maximum`, a `default`, an optional, `additionalProperties: false`, no `$ref`) | `src/adcp/types/_schemas/core/pagination_request.py` and `_base.py` exist; `from adcp.types._schemas.core.pagination_request import PaginationRequest` works; `tests/test_emit.py` runs `check_pair` on it, green both directions; `python -m codegen.emit --bundle schemas/cache/3.2 core/pagination-request.json` is the one command | the 85 leaf object documents (no `$ref`, no composition, no conditional); **N: 0 → 1**, then → up to 85 by running the same code over the leaf set and extending the format table; a leaf that refuses names its keyword | D1 fixes the path, D4 the optional, D7 the config, D8 the layout. The only later input is a new D2 row, which adds a lowering and changes nothing already emitted (P10's byte compare proves it: step 1's file is identical after every later step). | P3, P7, P10, P11, P12 | no — this is the trunk |
| 2 | **A cross-document `$ref`**: `error-details/creative-revision-content-mismatch.json` → `core/creative-revision-id.json` (a string root with `minLength`/`maxLength`) | the referencing module carries `from ..core.creative_revision_id import CreativeRevisionId` and no copy of its constraints (P2 asserted on the AST); the target emits as an `Annotated` alias (D2); both graded | 176 documents whose only `$ref` use is a property or its items; 690 carry a `$ref` somewhere; **ΔN ≈ +100** (those whose targets are leaves or aliases) | D1 fixes the import spelling (a pure function of two paths). Transitive emission is a graph walk over edges the node graph already binds at 100%. | P2, P5 | no — the import mechanism is the trunk's second half |
| 3 | **Enum root** and inline enum nodes: `enums/match-type.json`, then `core/keyword-target.json` which references it | `MatchType(StrEnum)`; `KeywordTarget.match_type: MatchType` — the reference site binds the class, which closes the 5 `enum` widening triples by construction (defect inventory, direction 2) | 214 enum roots, 535 documents with an `enum` anywhere; **ΔN ≈ +250** | D3's nested rule names an inline enum; the name is content-derived, so a later union or product step cannot rename it. Member spelling: a non-identifier value is sanitised with the unsuffixed-member check from P3. | P1, P2, P3 | **yes** — `codegen/lower/enum.py` |
| 4 | **`allOf` roots**: `$ref` conjuncts → bases (D6); an inline conjunct with `properties` → the node's own fields; a `required`-only conjunct → a rule, not a class; an enum narrowed through `allOf` → the intersection | control documents: `core/canonical-format-responsive-creative.json` (the `Optional[Any]` shadowing — 4 widening triples; a subclass never redeclares an inherited field), the §4.3 narrowing site; `allOf` of `core/version-envelope.json` inherits `ge=1, le=99` | 287 `allOf` roots, 401 documents with `allOf`; **ΔN ≈ +300** | Field merging has one rule — a child restates a field only to narrow it (P3's "same annotation or a subclass") — and the harness refuses any other merge on the spot, so there is no order-dependent "last wins" to revisit later. | P2, P3, P5 | **yes** — `codegen/lower/product.py` |
| 5 | **Union roots**: base + one class per branch + `<Name>Branches = Annotated[A \| B, AfterValidator(exactly_one)]` for `oneOf`, plain union for `anyOf`; branch names by D3; a flat root's own `properties` become the base's fields (Q5 decided: name the branch, not the merge) | controls: `core/audience-characteristic.json` (D1-d), `core/account-ref.json`, `content-standards/get-content-standards-response.json#/oneOf/0` (identity read through a `$ref`'d conjunct — D3 looks through `allOf` because the old rule's failure to was F4 e); the 8 sole-untitled-branch documents (F4 c) **refuse and are listed**, because the hatch made a name a function of its siblings | 156 union roots (90 with properties/`allOf` beside the union, 66 bare); **ΔN ≈ +130, 8 refused** until the bundle titles them | A union whose branches are not pairwise disjoint on requiredness emits branches **without a base** and a plain alias (decided; the old plan left it open). That is strictly additive later, so a base can be introduced without renaming a branch. | P1, P2, P3, P5 | **yes** — `codegen/lower/union.py` |
| 6 | **Non-object roots and mappings**: root array → `RootModel[list[X]]`; root scalar → alias; typed `additionalProperties` → `dict[str, X]` carrying `minItems`-style constraints on the value; a multi-type property applies each keyword to its own arm only | controls: `core/geo-place-support.json` (`minItems` on an `additionalProperties` value — 1 triple, `.13`), `core/attestation-reference.json` (D1-c, `minLength` on `["object","string"]`), `core/property.json` (D1-b: the inline `identifiers.items` keeps its own `additionalProperties: true` because it is its own node) | 14 scalar + 5 array + 2 mapping roots; 727 documents with `additionalProperties`; **ΔN ≈ +20 roots, and ~50 documents already emitted get their mapping constraints** | The D2 row per shape is fixed; the only thing this step chooses is the constraint spelling per container, which the harness grades keyword by keyword. | P2, P3 | **yes** — `codegen/lower/containers.py` |
| 7 | **Rules**: `not`, `if`/`then`/`else`, `dependencies`, `min`/`maxProperties`, `uniqueItems` → class-level tuples read by `_runtime.py`'s after-validator; a property declared only under `then`/`else` gets an optional field typed from that declaration (the 59 conditional-only nodes) | control: `core/canvas-constraint.json` (`maximum` inside `if`/`then` — 1 triple); `media-buy/change-term.json` keeps transcribing `x-adcp-validation` and is **not** graded by the harness (the inventory says why); `uniqueItems` needs its own instrument because `harness.steps()` does not step it — add the keyword to `steps()` in this step so the 198 documents are graded | 270 documents with a conditional or `not`, 198 with `uniqueItems`, 27 with `dependencies`; **ΔN ≈ +150** (documents refused at 4/5 for an unlowered keyword) | Every rule is data on the class plus one validator in `_runtime.py`; adding a rule kind adds a tuple, renames nothing. | P3, P11, P12 | **yes** — `codegen/lower/rules.py` + `_runtime.py` |
| 8 | **The whole population**: `python -m codegen.emit --bundle … --all` emits every portable document or refuses it by name and reason; an `mcp/`/`bundled/` projection becomes a binding-table row to its `projection_of` target and is never emitted or graded on its own (the inventory's 83 false rows) | `src/adcp/types/_schemas/**` complete; `docs/probes/emit/<run>/grade.jsonl` from the existing forked, budgeted runner over all N; `N + refused == 1,054` asserted; the binding table `document → module:Symbol, kind` written by the emitter (it knows, so it emits) | **N → ≥ 1,000**; the residue is a list of documents each with a keyword or a pointer | This step adds no rule; it loops. A refusal here is a step 3–7 gap and goes back to that lane. | P5, P7, P10 | after 3–7 |
| 9 | **Public surface from the binding table**: `adcp/types/__init__.py` and `adcp/types/<domain>/__init__.py` generated, PEP 562 lazy as today; the build refuses a root name bound to two different nodes (P8); `Warning` never takes the bare slot (P6) | `from adcp.types import PaginationRequest` and `from adcp.types.core import PaginationRequest` are the same object; a collision is a build failure naming both nodes; the 5 module collisions the table reported are measured again here — identical nodes collapse (D3), the rest refuse | all N | P8's refusal is designed to fire; its fix is a title upstream or a D3 clause, never a rename table. | P5, P6, P8 | after 8; parallel with 10 |
| 10 | **`fast_validate` / `validate_exact`** on `AdCPBaseModel`, backed by the binding table and the resolved cache; a schema refusal raises pydantic's `ValidationError` with the keyword as `type` through `PydanticCustomError` | `PaginationRequest.validate_exact({"max_results": 0})` raises with `type == "minimum"`; one test per keyword family | all N | The class → document link is emitted in step 8, so this reads a fact and derives nothing new. | P5, P10 | after 8; parallel with 9 |
| 11 | **Closeout**: P9 derivation wired; `make validate-generated` byte compare; `datamodel-code-generator` removed from `pyproject.toml` and the pin comment with it; `adapter_adcp.py`'s old-tree reading (`TREE`, `DOMAINS`, the `# filename:` header parse) deleted; parked modules deleted if unimported | `grep -r datamodel_code_generator codegen/ src/ tests/ pyproject.toml` is empty; `tox` green; the 9 narrowing rows and 12 widening triples re-run through `derive_defect_inventory.py` against the NEW tree and report 0 | — | — | P7, P9, P10, P13 | last |

**Order is by risk.** Step 1 is first because it is the one that could still invalidate the
route — if a leaf object does not round-trip through the harness, nothing after it matters.
Step 2 is second because an import is the one thing the spike did not render. Steps 3–7 are
independent shapes; their order within the table is by population, not dependency. The
previous plan put the emitter tenth; here nothing exists until it emits.

**Where a principle forced an unobvious choice.** P2 and P5 mis-shaped the previous attempt
by being applied to naming before anything emitted: "one node, one class" became "every node
needs a name" (`NEEDS_A_NAME` wider than the plan), and "refuse what you cannot derive"
became "refuse the document for a node that should never have been a class". D2 settles both
by deciding class-or-annotation BEFORE asking for a name; a refusal is then rare (8
documents) and each one is a missing title, which is the bundle's defect to fix. P12 overrides
a recorded decision of the old plan (D4). P5 removes the protocol-marker bases rather than
re-deriving them (D6).

## 4. Out of scope, and why

- **The deprecated-alias layer** (`CreateMediaBuyResponse1` and the 136 plain aliases) — owner
  decision, unchanged.
- **The canonical layer** (`canonical_creative`, §5 item 2's "flat root binds the canonical
  subclass") — `src/adcp/types/` is empty at HEAD; the rebuild emits wire-faithful classes
  and step 9 binds them. Re-layering canonical subclasses on top is additive and separate.
- **Upstream title PRs** for the 8 refused union documents — filed, not waited for; the build
  emits 1,046 without them.
- **Throughput of `fast_validate`** against ajv — unmeasured in the old plan, still unmeasured.
- **`node_names.py` / `module_table.py`** — parked; their one correct insight (rules 1–3 for
  branch names) is re-expressed as D3 in ~40 lines inside `lower/union.py`.
- **The 9 narrowing rows and 12 widening triples are NOT a separate workstream.** Each is the
  named control of one step above (D1-a → step 1; D1-b, D1-c, `minItems` → step 6; D1-d →
  step 5; `enum` ×5 → step 3; `Optional[Any]` ×4 → step 4; `maximum` in `if` → step 7;
  `$id` required → step 1's alias rule for non-identifier names). Step 11 re-runs the
  inventory against the new tree and expects 0. `MediaBuyChangeTerm` (D1-e) stays as it is.
- **`.18`'s 24 bundle edits** — withdrawn: 22 of the 30 nodes need no name under D2.

## 5. The metric

> **N = the number of portable bundle documents (of 1,054) whose types are emitted by
> `codegen.emit` and graded green by `codegen.harness` in both directions against the
> emitting document, with every document not in N listed by name and reason, and
> `N + refused == 1,054` asserted.**

A missing emitter scores N = 0 and fails. A harness pointed at a pre-cut tree scores nothing,
because the pair comes from the emitter's own binding table, not from a module header. Each
step above predicts its ΔN; the check-in number is N, read from `docs/probes/emit/<run>/`,
never from a count of closed beads. The old goal — "the harness green over the full document
population" — was satisfiable with no generator; this one is not satisfiable without one.
