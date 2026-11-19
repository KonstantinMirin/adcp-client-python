# Solution design: the registry types, and what the SDK should do with them

> "I need a separate agent doing a solution design for it for the SDK properly: what can we
> use/reuse from type emission, what is different." — the owner

**THIS DOCUMENT CHANGES NOTHING.** No generator, no module, no test, no name. It is written to
be rejected or taken in parts; the decisions in §3, §4 and §9 are the owner's and are marked as
such. Three one-line defects found on the way are in §10 as findings and are not fixed here.

**PROVENANCE CONVENTION, because the failure mode `CLAUDE.md` opens with is an unmarked guess
that becomes a decision nobody remembers taking.** Every figure carries one of:

| | what it means |
|---|---|
| **[M]** | measured in this worktree on 2026-11-18, with the command or probe named |
| **[F]** | `FINDINGS-openapi.md` — measured by the stopped lane on a tree that existed, then reverted |
| **[A]** | read off a committed artifact (`src/adcp/types/verify.json`, `verdicts.tsv`) |
| **[B]** | given by `TASK.md` and not re-derived, per its instruction |
| **[U]** | **UNMEASURED** — a question, not a fact |

Vocabulary: a union's parts are **BRANCHES**.

---

## 1. The subject in one page

| | |
|---|---|
| `src/adcp/types/registry.py` | 2,051 lines; **155 classes** = 107 models + 47 enums + 1 root-model union **[M]** |
| written by | `scripts/generate_registry_types.py` (291 lines), wrapping `datamodel-code-generator` |
| from | `schemas/registry-openapi.yaml` — `openapi: 3.1.0`, `info.version: 1.0.0`, one server, `https://agenticadvertising.org` **[M]** |
| that document holds | 67 `components/schemas`, 90 paths, **94 operations**, 94 unique `operationId`s, 2 security schemes (`bearerAuth`, `oauth2`) **[M]** |
| emitted by `codegen/` | **no** — nothing under `codegen/` opens a `.yaml` **[F]** |
| the emission, for scale | `./check`: `emitted 1059 / refused 0; approximated 805 facts in 239 documents` **[M, run here, 1.23 s]** |

**The structural fact that makes this a design question rather than a cleanup.** Of the 28 files
of `src/adcp/types/` the emission does not write, twelve are another generator's output and
**eleven of those twelve declare zero classes — every statement in them is a re-export, a
SPELLING. `registry.py` declares 155 subjects no bundle document states** **[F]**. That is the
whole of the owner's line: *`adcp.types` may hold hand-written types the SDK needs; what it may
not hold is another generator's output.* Measured in this checkout, `registry.py` is the only
file in the package that is a second generator's **types**; `src/adcp/reporting/_preview/`,
which `pyproject.toml` excludes on the same grounds, **does not exist here** **[M]** — see
finding F3.

---

## 2. What the client actually is, measured — this is the premise for everything after it

`src/adcp/registry.py` is 3,148 lines and `RegistryClient` has **97 public methods** besides
`close` **[M, `ast` over the class body]**. Their return annotations group as:

| returns | count | examples |
|---|---|---|
| `dict[str, Any]` or `str` | **72** | `lookup_publisher`, `get_agent_monitoring_settings`, `requeue_agent_for_heartbeat`, `get_agent_badge_svg`, `run_storyboard`, `create_organization` |
| one of the 155 OpenAPI classes | **15** | `list_brands`, `validate_property`, `lookup_domain`, `get_feed`, the five community-mirror methods |
| a type from `adcp.core` (**hand-written**, 444 lines) | **10** | `lookup_brand → ResolvedBrand`, `resolve_policy → Policy`, `list_members → list[Member]` |

**Three readings follow, and each one bears on the decision.**

1. **The second generator buys typing for 15 of 97 methods.** 2,051 lines, 155 classes, a
   51-entry hand-maintained rename table and 142 `legacy_names` rows **[M]** are the price of
   fifteen annotations.
2. **The SDK already serves ten of them from HAND-WRITTEN models**, in `adcp/core.py`
   (`ResolvedBrand`, `ResolvedProperty`, `Member`, `Policy`, `PolicySummary`, `PolicyHistory`,
   `PolicyExemplars`, `PolicyRevision`) **[M]**. The precedent for hand-writing a registry
   response type is not hypothetical — it is the majority of the client's typed surface, and it
   is the same precedent the owner used to keep `Protocol`.
3. **A large share of the 72 untyped methods are registry-OPERATOR functions, not buyer
   functions**: pausing an agent's monitoring, setting a heartbeat interval, requeueing an
   agent, fetching a badge SVG, running and comparing storyboards, storing an agent's OAuth
   client credentials, creating an organization **[M, from the method list]**. That is an admin
   console's API living inside a protocol-types SDK.

**And the coverage is held 1:1 by a hand-maintained table inside a test.**
`tests/test_registry_types_drift.py::test_all_openapi_endpoints_have_client_methods` carries a
~98-row `OPERATION_TO_METHOD` map and fails if any of the 94 operations has no method **[M]**.
So the client is contractually obliged to mirror every endpoint the service adds, forever, by
hand.

---

## 3. Should the SDK ship a client for this service at all?

### The case FOR, and it is stronger than "a buyer plausibly needs it"

**The protocol bundle itself routes a buyer to this service.** Measured over
`schemas/cache/3.2`, three portable documents name a registry REST endpoint in their own text
**[M]**:

* `core/registry-feed-response.json` — *"Response from GET /api/registry/feed and the `feed`
  event body from GET /api/registry/feed/stream"*;
* `media-buy/list-creative-formats-request.json` — on the deprecated `publisher_domain` filter:
  ***"New callers use `GET /api/registry/publisher?domain=...` for publisher acceptance"***;
* `index.json`.

So the protocol, in a document the compiler emits from, tells a new caller to make an HTTP call
to this service for a question `list_creative_formats` no longer answers in band. A buyer that
cannot resolve a publisher's acceptance cannot complete the flow the bundle describes. **The
bundle also states two of the service's payloads outright** — `core/registry-event.json` and
`core/registry-feed-response.json` are the change feed, emitted today as `RegistryEvent` and
`RegistryFeedResponse` **[M]**. Part of this service is already inside the protocol's own type
system.

### The case AGAINST

Different service, different base URL, different auth (`bearerAuth` / `oauth2` against AdCP's
own agent auth), **different version axis** — `info.version: 1.0.0` against AdCP 3.2.7, with
nothing tying a bump in one to a bump in the other **[M]**. 94 operations of which most are
operator-facing. A 2,051-line generated module whose generator **no longer reproduces its own
file**: a run today writes 2,099 lines against the committed 2,051, differing at 56 lines, and
silently renames the public class `PolicyExemplarPass` to `PassItem` **[F]**. And a drift test
whose coverage clause is `schema_name in cls or cls.startswith(schema_name[:5])` — a
five-character prefix match that is close to unfailable **[M]** — so the one gate on the
generated half asserts almost nothing.

### RECOMMENDATION

**Yes to the client. No to the second generator. Narrow both.**

1. **Keep `RegistryClient` in the SDK**, where it is, under `adcp.registry*`. The protocol
   points at the service; shipping the pointer without the client makes every adopter write the
   same httpx wrapper, and the client already carries real work that is not type-shaped —
   bounded response reading, `Retry-After` handling, bulk chunking, error projection with size
   caps.
2. **Retire `scripts/generate_registry_types.py` rather than relocate its output.** Its output
   types fifteen methods, duplicates fourteen words the schema subject already owns (§7), and
   cannot be regenerated without a public rename. The types the client needs are hand-written —
   exactly as `adcp.core`'s ten already are — and the relocated file is carried as a frozen
   compatibility surface, not as a regenerable artifact.
3. **Type by priority, and the priority is the protocol's.** The endpoints the bundle names
   (`/api/registry/publisher`, the feed) come first. `lookup_publisher` returns
   `dict[str, Any]` today while the spec states `PublisherLookupResult` and the generator emits
   it — and **nothing imports that class except `legacy_names.py`** **[M]**. That single pair is
   the whole dead-weight problem in one line: the generator types what no one calls and leaves
   the call the protocol names untyped.
4. **Do not split a second distribution.** `adcp-registry` would double the release machinery
   (`release-please`, Trusted Publishing, the approval environment) for 3,148 lines that import
   `adcp.exceptions` and `adcp.identifiers`. Revisit only if the operator half is kept and grows.

**The reasoning that decides it.** The owner's line is not "not emitted" — `Protocol` stays. It
is "another generator's output in the emitted package". A hand-written `adcp.registry_types`
is on the right side of that line, is the shape ten of the client's typed methods already have,
and removes the generator-version hazard entirely. The 155-class module buys type coverage the
client does not use and pays for it in a public namespace it contests at fourteen words.

**What this recommendation does NOT claim.** Whether the operator half (monitoring, badges,
storyboards, organizations) should stay in the SDK at all is a product question I have no
measurement for — **[U]**. If it goes, `test_all_openapi_endpoints_have_client_methods`'s
contract goes with it, and that is the owner's call.

---

## 4. If yes: where the types live, and what the public surface is

### The module path

```
src/adcp/registry_types.py        ->  adcp.registry_types
```

Beside `adcp/registry.py`, `adcp/registry_sync.py`, `adcp/property_registry.py` — the consumer
family, not the emitted package. This is the path the stopped lane measured: `FINDINGS-openapi.md`
§7 records that one caller derives upstream's module word via `relative_to(src/adcp/types)` and
"makes another raise `ValueError`" after the move, which is only true of a path outside
`src/adcp/types/` whose stem is `registry_types` **[F]**.

**`adcp.types.registry` must RAISE, not redirect.** `CLAUDE.md`'s `Format`/`LegacyFormat` rule
applies unchanged: *a public word that changes meaning while staying importable is the worst
available outcome.* `ModuleNotFoundError` is the intended post-state and was measured as such
**[F, §8]**.

### The public surface, measured precisely

`registry.py`'s 155 class names reach consumers at three distinct namespaces, and they do not
agree with each other. All figures **[M, resolved through the real facade with
`PYTHONPATH=.:src`]**:

| namespace | resolves | to the vendored module | to a schema subject |
|---|---|---|---|
| `adcp.<Name>` | 27 of 155 | **17** | 10 |
| `adcp.types.<Name>` | **155 of 155** | 141 | **14** |
| advertised in `adcp.types.__all__` (4,251 names) | — | **148** | — |
| advertised in `_restored.__all__` (176 names) | — | **141** | — |

**Three words resolve to different objects at the two namespaces** **[M]**:

```
AuthorizedAgent    adcp -> a union alias (__module__ 'types')   adcp.types -> adcp.types.registry
DiscoveryMethod    adcp -> an alias (__module__ 'typing')       adcp.types -> adcp.types.registry
ValidationResult   adcp -> adcp.types.registry                  adcp.types -> property/validation-result.json's class
```

`ValidationResult` is the sharp one: `adcp.ValidationResult` and `adcp.types.ValidationResult`
are **different classes today**, because `adcp/__init__.py` routes the word explicitly to the
vendored module while `adcp.types._decided` screens it to the document's subject. That is a
pre-existing defect, independent of any move, and it is finding F4.

### What happens to the 27 words `TASK.md` names

Measured **[M]**: of the 27 registry class names in `adcp.__all__` (745 names), **17 resolve to
`adcp.types.registry` and 10 already resolve elsewhere** — 7 to `adcp.core`'s hand-written types
(`Policy`, `PolicySummary`, `PolicyHistory`, `PolicyRevision`, `PolicyExemplars`,
`ResolvedBrand`, `ResolvedProperty`), 1 to an emitted class (`KellerType` →
`adcp.types._schemas.brand`), and 2 to aliases that are not classes at all (`AuthorizedAgent`,
`DiscoveryMethod`). So:

* **`from adcp import AgentHealth` keeps working.** The 16-name lazy-route group in
  `adcp/__init__.py` (plus `BrandSource` through the restored flat offer) keeps its NAMES and
  changes only its KEY. Every witness held across exactly this move **[F, §8]**: 17 names in
  `adcp.__all__`, `from adcp import AgentHealth` works, 141 flat words, the six contested words
  still `adcp.core`, `adcp.types.BrandSource` still the vendored class.
* **The 10 that resolve elsewhere do not move**, because the vendored module is not where they
  come from. Nothing is owed them.

### The 141 advertised flat words are the one real break, and it is a SEPARATE decision

`adcp.types._restored.MODULES` names `registry`, and `_restored.__all__` advertises **141** of
its words flat at `adcp.types.<word>` **[M]**. Two options, and they must not be conflated:

**(a) Relocate the file, keep the flat offer.** `_restored` grows one `home()` function reading
the relocation from a single place **[F, §7]**, `MODULES` names the new home, and **zero
advertised names change**. The owner's line is satisfied by the FILE leaving the emitted
package; the WORDS stay. This is what §9's Stage 2 does.

**(b) Withdraw the 141.** This is `FINDINGS-sixwords.md`'s own open question 2 — *"whether the
142 uncontested registry words belong on the flat surface at all"* — and it is unsettled. It
withdraws 141 advertised names, which `tests/test_public_words_resolve.py` grades as an outage
when a word is advertised and does not resolve, and
`tests_emit/test_the_restored_flat_surface.py` grades for agreement between the offer and the
namespace **[M, both files exist]**.

**Recommendation: (a) now, (b) as its own staged decision with its own before/after.** A
relocation that also withdraws 141 public names is two changes graded as one, and if it reddens
nobody can say which half did it.

---

## 5. What is REUSABLE from the type emission, module by module

This is the half the owner asked for by name. Each row says what is reused, **verbatim /
with one change / not at all**, and the measurement behind it.

### 5.1 `src/adcp/types/_base.py` — the base model and the artifact's vocabulary · **REUSABLE VERBATIM**

| symbol | reusable for an OpenAPI-derived class | why, measured |
|---|---|---|
| `SchemaRef(document, pointer)` | **yes, verbatim** | it is a `(document, pointer)` `NamedTuple` with no bundle assumption in it. `#/components/schemas/PolicySummary` and `#/paths/~1api~1registry~1feed/get/responses/200/content/application~1json/schema` are both valid pointers, and **RFC 6901 `~1` escaping is already implemented** at `_base.py:1444`, `codegen/bundle.escape_key`, `lower/names.py:517` and `dump_exemptions.py:600` **[M]** |
| `SchemaBound.strict_validate` | **yes, verbatim** | it is `_refuse_at(ref, payload, …)` then `model_validate`. Nothing in it is bundle-shaped |
| `_refuse_at` / `applied_schema` / `_refuse` | **yes — MEASURED, not reasoned** | see the probe below |
| `AdCPBaseModel` | **as a base, with one divergence to settle** | its `extra` default is `ignore`; `RegistryBaseModel` is `extra="allow"` **[M, `adcp/types/base.py:962`]**. §2's rule is *`extra` follows the schema and nothing else*: 81 of the 96 `additionalProperties` in the OpenAPI document are `{}` → `allow`, **0 are `false`** → nothing maps to `forbid` **[M]**. So `allow` is what the document states almost everywhere and the divergence is mostly a coincidence of agreement, not a conflict |
| `OmittedNotNull`, `Approximation`, `NARROWED`/`WIDENED` markers | **yes, verbatim** | they are declarations on the artifact, not readings of the bundle |
| `BranchDispatchMixin` / `_Dispatching` | **yes, and there is almost nothing to dispatch** | the document states **1 `oneOf`, 6 `anyOf`, 3 `allOf` in total** **[M]**. One union exists in the output already (`CommunityMirrorPublishRequest`, 5 branches) |

**THE PROBE, because this is the claim everything else rests on.** Loading
`schemas/registry-openapi.yaml`, coercing to JSON and calling the production schema half
**[M]**:

```
applied_schema(spec, "#/paths/~1api~1registry~1feed/get/responses/200/content/application~1json/schema")
  -> keys ['type','properties','required'], required ['events','cursor','has_more'],
     and it is the SAME OBJECT as the raw node
_refuse(node, {"events": [], "cursor": None, "has_more": False}, root=spec)   -> ACCEPTED
_refuse(node, {...events[0].created_at = "nope"...}, root=spec)              -> REFUSED at events.0.created_at
applied_schema(spec, "#/components/schemas/ResolvedBrand"); _refuse(.., {}, root=spec)
                                                                             -> REFUSED, 4 validation errors
```

Three things are established and one is ruled out:

* the pointer walk traverses the OAS wrapper hops (`paths`, the method, `responses`, `200`,
  `content`, the media type) **without conjoining anything wrongly** — it returns the raw node
  identically, so `applied_schema`'s `SAME_INSTANCE_FACTS` conjunction is transparent to a
  non-schema segment, which was the one thing I expected to break;
* `root=spec` resolves `$ref`s into `#/components/schemas/…` — **19 of the 67 components carry a
  `$ref`** **[M]** and `ResolvedBrand` is one of them;
* **`$ref`-with-siblings is 0** across all 2,161 schema nodes **[M]**, so the draft-07 /
  2020-12 divergence on sibling keywords — the one that would have made a draft-07 reading
  wrong — **does not arise in this document at all**;
* what it does **not** establish is the dialect. See §6.1.

### 5.2 `src/adcp/types/constraints.py` + `codegen/constraints.py` — the constraint carriers · **REUSABLE, AND THE FORMATS MAP CLEANLY**

`constraints.py` is **generated** (`# Generated by codegen.emit`); the decisions live in
`codegen/constraints.py` (727 lines) and in the generated module's own docstring. Reuse means
reusing the derivation, not the file.

Does an OpenAPI `format` map onto them? **The document's whole format vocabulary is three
values** — `date-time` ×18, `uuid` ×5, `uri` ×10 **[M]** — and the emission has an answer for
each:

| the document says | the emission's answer | applies here |
|---|---|---|
| `format: uri` + `pattern: ^https://` | `AdCPUrl` = `Annotated[WireAnyUrl, UrlConstraints(max_length=2083, allowed_schemes=["https"])]` | **yes** — 6 nodes state `pattern: ^https:\/\/` and no `format` **[M]**, which is `AdCPUrl`'s own `allowed_schemes` stated as a pattern |
| `format: uri`, no pattern | `AnyUrl` (host required), **not** `HttpUrl` — the cap is accepted, the decision is indexed | **yes**, 10 nodes |
| `format: date-time` | `WireDatetime` (keeps its wire text) | **yes**, 18 nodes |
| `format: uuid` | a `StrFormatUuid`-shaped alias | **yes**, 5 nodes — but see §6.1, the assertion is dialect-dependent |
| `minLength`/`maxLength`/`minimum`/`maximum` | `StrMaxLen100`, `IntMin0Max150`, `NonEmptyList` — §4's "constraint in words" | **yes**: 8 + 14 + 19 + 6 nodes **[M]** |
| a bare `pattern` | a constrained `str` with the pattern on the type | **yes**, 16 nodes |

**And the shape that forces a drop does NOT occur here.** The emission's two largest
`format`-related approximation classes come from a `uri` node that also asserts something a URL
type cannot carry. Measured over the OpenAPI document: **no `uri` node has a sibling `pattern`,
`minLength` or `maxLength` — zero** **[M]**. `EmailAddress` has no site either: `format: email`
does not appear.

**`SchemaInt` applies and matters**: 19 `minimum` nodes, and `SchemaIntegral`'s
`as_json_schema_integer` is the reading that `1.0` is a JSON-Schema integer.

### 5.3 The gate — `tests_emit/test_the_grade_is_green.py` · **REUSABLE IN SHAPE; THE POPULATION NEEDS A POINTER SET, AND THERE IS ONE**

The gate is 2,570 (document, pointer) pairs **[B]**; the committed artifact reads
`graded 2570, pass 2548, not_pass 22` with `accepts 2569/1/0, refuses 2563/0/7, dump 2569/0/1`
**[A, `verify.json`]**. Its three contract checks are *accepts / refuses / dump*, and absent is
not a pass.

**Can an OpenAPI-derived class be graded the same way, and against what pointer?** Yes, and the
pointer set is measured:

```
561 schema ROOTS  =  67 components/schemas  +  494 inline schemas under paths   [M]
2,161 schema NODES reached by a draft-07-style applicator walk from those roots  [M]
```

So there is a pointer to key on at every position, and the **494 inline roots are why this
matters**: only **66 of the 155 existing class names correspond to a `components/schemas` key**,
before or after the 51 renames **[M]**. The other 89 classes come from schemas inline in a
`requestBody` or a `responses` entry — they have a pointer, they have no component name, and
that is exactly the case §4's naming rules were written for.

Four things the gate needs that do not exist today, each small and each named:

1. **A record to read.** `_base._document` does `json.loads(path.read_text())` — **JSON only**
   **[M]**. The spec must ship as JSON. Measured: 346,956 bytes of YAML → **255,970 bytes of
   JSON** **[M]**. And the conversion is not free: `yaml.safe_load` produces **9 `datetime`/`date`
   objects** from unquoted `example` values, so the document **does not round-trip to JSON
   without a coercion** **[M]** — finding F5.
2. **`__adcp_schema__` on the classes.** `harness.pairs`' predicate is `SchemaBound`, and
   `_record_root` returns `None` "for a module that is not inside `PACKAGE` at all — a
   hand-written class naming a document has no tree of its own, and this package's own records
   are then the only answer" **[M, the docstring]**. **So a hand-written class may carry a
   `SchemaRef` and get `strict_validate` for free.** That is the single highest-value reuse in
   this document and it needs no new machinery.
3. **A second population.** `harness.pairs(package, path=…)` walks one package; the OpenAPI
   pairs are a second call with a second root. It returns `(found, unimportable)` and records
   rather than raises, so adding a population cannot take down the existing one.
4. **A witness source.** `codegen/verify/witness.py` constructs a witness from the node's own
   keywords (`const` → its value, `enum` → first member, `required` → its keys, a bound →
   exactly that many). Every one of those keywords is in this document. Where construction
   cannot produce a value the architecture's rule is *the document's own `examples` is the
   witness* — and this document carries `example` (singular, OAS spelling) at **149 sites** and
   `examples` (JSON Schema spelling) at **2** **[M]**. See §6.2: that is a one-row change to
   `keywords.py`, and it is the **only** vocabulary gap in the whole document.

### 5.4 The committed-tree-equals-fresh-emission gate · **NOT REUSABLE AS IT STANDS, AND THAT IS THE HOLE THAT LET THIS HAPPEN**

`tests_emit/test_emit.py::test_the_committed_tree_is_what_a_fresh_run_emits` compares two file
SETS and every byte of the files in both, plus a DERIVED `out.beside` set
(`{constraints.py, envelopes.py} | the 23 domain aggregators | the compat mirror`) **[M]**.
**An EXTRA committed file is in neither comparison** **[F, §3]** — which is why 2,051 lines sat
inside the emitted package with no check on either side of that compare holding them.

The converse gate was written, run and demonstrated by the stopped lane, as four clauses over a
`NOT_EMITTED` table: every file is emitted, is the derived public composition of an emitted
aggregator, or is NAMED in the table; the table names nothing the emission writes and nothing
that is gone; every module the emission's own text imports is in the table as foundation; and
**no "another generator's output" entry DECLARES A TYPE** (`ast.walk`, so a class under
`try:` or `if TYPE_CHECKING:` is not a way through) **[F]**. Both teeth were demonstrated:

```
clause 1: ['registry.py'] is neither emitted, nor a public composition, nor named
clause 4: registry.py is another generator's output and DECLARES 155 class(es)
```

**This is reusable immediately and independently of every other decision in this document.** It
is §9's Stage 0.

### 5.5 The naming rules (`rebuild-plan.md` §4) and the alias layer · **REUSABLE AS RULES; THE TITLE INPUT IS ABSENT**

What §4 would do to this document, measured:

* **The 51-entry hand rename table is what §4 exists to replace.** `Source` → `Source4`,
  `Revision2`, `Contact1`, `AdagentsJson1`, `CommunityMirrorPublishRequest1..5`, `Pas`,
  `FailItem` — the generator's own names are traversal-order artifacts, and §4's *a positional
  index is a declared placeholder, not a name* forbids every one of them.
  `tests_emit/test_no_positional_name_is_public.py` reads the whole symbol **[M, the file
  exists]**. **11 of the 155 committed class names still end in a digit after the renames** —
  `Status1`, `Status2`, `Status3`, `Status4`, `Source5`, `Source6`, `Property1`,
  `AuthorizedAgent2`, `StoryboardStatus1`, `Agent1`, `Code1` **[M]**.
* **The rename table is already decaying**: `CLASS_RENAMES["Pas"]` is DEAD — the generator now
  names that class `PassItem`, so a regeneration silently renames the public
  `PolicyExemplarPass` **[F, §6]**.
* **`enum: [true]` is rendered `class SuccessLiteral(Enum): boolean_True = True`** **[M]** — a
  consumer writes `SuccessLiteral.boolean_True`. §4 and the indexed decision *a required
  property the document PINS to one value may default to it* give a better answer at the same
  position.
* **The catalogue would collapse real duplication**: 123 enum nodes over **72 distinct value
  lists** **[M]**, the most repeated being `[true]` ×14, `['true']` ×5, and a nine-member
  channel list ×4. §3a's L0 entry key *is* the value list.
* **But §4's root rule has no input**: `pascal_case(title)` — and **not one schema node in the
  document carries a `title` keyword** **[M, the 22-key census in §6.2 contains no `title`]**.
  See §6.3.

The **alias layer** (`adcp.types.aliases`) is reusable in pattern — a stable semantic spelling
in front of a generator-derived name — and is in fact the pattern the 51 renames are a worse
version of: the renames rewrite the generated text, so a generator-version bump moves a public
name (F2); an alias layer binds a stable word to whatever the generator called it.

### 5.6 The approximation machinery · **REUSABLE, AND THE ANSWER TO "ARE THERE FACTS TO DROP" IS: ALMOST NONE, MEASURED**

The question `TASK.md` asks is the right one and the answer is measurable rather than arguable.
The emission's own approximations, by keyword, over the committed tree **[M, `grep` for
`Approximation(…)` across `_schemas/`, 1,183 declarations]**:

```
if 439   minLength 351   format 351   oneOf 16   additionalProperties 15
maxLength 5   required 4   maxProperties 2
```

Held against the OpenAPI document **[M]**:

| keyword | emission drops it | sites in this document | would drop here? |
|---|---|---|---|
| `if` | 439 | **0** — no `if`/`then`/`else`/`not` anywhere | no |
| `minLength` | 351 | 8 | **no** — the drop is driven by a `uri` node asserting a length, and there are 0 such nodes here |
| `format` | 351 | 33 | **no**, same reason |
| `maxLength` | 5 | 14 | no, same reason |
| `additionalProperties` | 15 | 96 — **81 are `{}`, 15 carry a value schema** | **the 15 are the candidate**: a typed-extras constraint pydantic cannot express at a node that also declares `properties` |
| `oneOf` | 16 | 1 | possible at one node |
| `required` | 4 | 242 | only in the presence-group shape, which needs the `anyOf` sites |
| `maxProperties` | 2 | 0 | no |

**So the honest answer is: yes, an OpenAPI projection has facts to drop, and this one has very
few** — a handful of typed-extras sites and at most one combinator. The machinery is reused
whole (it is how a drop gets DECLARED rather than being silent) and it would have almost nothing
to declare. **That is a strong argument for the projection route being cheap if it is taken at
all**, and it is also why the current generated module is so much weaker than it looks: it drops
facts with no declaration anywhere, which is what §5.7 is about.

### 5.7 What the vendored module gives up by not being in any of this

Measured on the one subject both halves state — `core/registry-event.json` versus the
hand-patched `FeedEvent` **[F, §5, re-verified here against the documents]**:

| property | the document's class | the OpenAPI copy |
|---|---|---|
| `created_at` | `WireDatetime` | `str` |
| `entity_type` | `EntityType`, 4 members | `str` |
| `event_type` | `RegistryEventEventType`, 20 members | `str` |

On `{"event_id": "not-a-uuid", "event_type": "nope.invented", …}`: `RegistryEvent` **refuses**,
`FeedEvent` **accepts** **[F]**. No `strict_validate`, no `__adcp_schema__`, no rule tuple, no
approximation declaration, no pair in the 2,570 — the vendored module is outside every
instrument the emission has.

---

## 6. What is GENUINELY DIFFERENT, and therefore cannot be reused

### 6.1 The DIALECT, and it is the one difference that costs something today

OpenAPI 3.1 schema objects are JSON Schema **2020-12**; the bundle is **draft-07**. The document
declares no dialect: it has no `jsonSchemaDialect`, and its only two `$schema` occurrences are
**property names inside the adagents document shapes, not draft declarations** **[M]**. So:

```
harness.validator_for(spec) -> Draft7Validator          [M]
harness.validator_for(node) -> Draft7Validator          [M]
"uuid" in Draft7Validator.FORMAT_CHECKER.checkers        -> False   [M]
"uuid" in Draft202012Validator.FORMAT_CHECKER.checkers   -> True    [M]
```

And the consequence, probed on the real document **[M]**:

```
_refuse(feed_node, {"events": [], "cursor": "not-a-uuid", "has_more": False}, root=spec)
  -> ACCEPTED                     # format: uuid is silently not asserted
```

**Reading this OpenAPI 3.1 document under the emission's draft-07 default silently drops the
`format: uuid` assertion at its 5 sites.** `validator_for` reads the document's own `$schema`
and defaults to draft-07 — correct for the bundle, wrong for OAS 3.1, and silent either way.
Any grading of an OpenAPI pair must select `Draft202012Validator` explicitly or inject a
`$schema`, and that choice belongs in one place beside `validator_for`.

**What is NOT a difference, measured, and this is the good news.** The other dialect divergences
that would matter do not occur:

| the divergence | sites in this document |
|---|---|
| `$ref` with siblings (ignored in draft-07, applied in 2020-12) | **0** of 2,161 nodes **[M]** |
| `nullable` (OAS 3.0 only) | 0 — the document uses `type: [x, "null"]`, **112 nodes**, which draft-07 also admits **[M]** |
| `exclusiveMinimum`/`exclusiveMaximum` as booleans (draft-04) | 0 — 1 numeric site **[M]** |
| `prefixItems`, `unevaluatedProperties`, `$defs`, `const`, `dependentSchemas`, `contains` | **0 each** **[M]** |
| `discriminator` (an OAS keyword, not JSON Schema) | **0** **[M]** |

### 6.2 The keyword vocabulary is a draft-07 subset plus ONE key

This is the measurement I would most want the owner to see. Over all **2,161 schema nodes**
reached from the 561 roots, the document uses **22 distinct keys, and 21 of them already have a
row in `codegen/keywords.py`** **[M]**:

```
rowed    type 1754  description 337  $ref 275  properties 268  required 242  items 216
         enum 123  additionalProperties 96  format 33  minimum 19  pattern 16
         maxLength 14  minLength 8  maxItems 7  minItems 7  maximum 6  anyOf 6
         allOf 3  default 2  exclusiveMinimum 1  oneOf 1
UNROWED  example 149
```

**One key. 149 sites.** `example` is OAS's singular spelling of JSON Schema's `examples`, it
states nothing about an instance, and under the admission rule *a key with no row is admitted
and marks the node for the TOP widening* — so without a row it would widen 149 nodes to `Any`
and declare 149 approximations for a keyword that drops nothing. Its correct cell is the one
`$comment`, `title` and `errorMessage` already have: `Effect.NOTHING`, `widens_to=None`,
because "there is nothing to drop and a widening would be a decision about a non-decision".

**So the semantics half of this document is not a different language. It is the same language
minus the hard keywords, plus a synonym.**

### 6.3 Endpoints and operations: the §-rules that genuinely do not apply

| rule | why it does not reach an OpenAPI document |
|---|---|
| **§1 "a document compiles to a module at its own path"** | there is no document-per-type. `bundle.portable` is `rglob("*.json")` over a directory tree, minus `mcp/` and the registry index files **[M]**. **One file, 561 schema roots** is the opposite source shape. Either the source layer learns a second shape, or the file is exploded into a synthetic document tree first (§8) |
| **§1 "every portable document contributes a symbol"** | has no referent: there is one document |
| **§4 Root naming — `pascal_case(title)`** | **not one schema node carries a `title`** **[M]**. The derivation has zero input. What the document DOES give is better: 67 component keys and **94 unique `operationId`s**, which OAS requires to be unique — so the naming authority exists and is a different one |
| **§3a L2C's titled-evidence rule** ("the bundle must title every stating position with one and the same word", a group titled nowhere is withheld) | would withhold **every** group in this document, for want of a title that is nowhere. The rule is right and must not be loosened; it simply has no evidence to read here, so the catalogue's untitled-group path is the only one available |
| **§8 the record / `bundle.record`'s inlining of a remote `$ref`** | all 275 `$ref`s are LOCAL (`#/components/schemas/…`); there is no cross-document reference to inline and no closure to compute. `Kind.CHAINED` has no instance |
| **the `$schema`-per-document reading, and the patched-bundle condition keyed on it** | one document, no per-document dialect |
| **`requestBody` / `responses` / `parameters` / `security`** | **no analogue in the emission at all.** 28 `requestBody`s, 94 `responses`, 72 `parameters` **[M]**. The emission has no concept of an operation, a status code, a media type or a query parameter. These are not types the compiler declines to emit — they are a layer above the type system. **72 of 94 operations' response bodies are untyped by the client anyway** (§2), so what this layer would buy is a typed call surface, which is a client-generator question and not a type-emission one |
| **the version axis** | `info.version: 1.0.0` against AdCP 3.2.7. `tests_emit/test_a_bundle_states_which_upstream_it_is.py` exists for the bundle; the OpenAPI document states a version that nothing in the SDK pins, compares or bumps **[M]** |

### 6.4 And one difference that is a FACT about the two documents, not about the formats

`core/registry-feed-response.json` and the OpenAPI feed response describe the same wire payload
and **disagree** **[M]**:

| | the core document | the OpenAPI document |
|---|---|---|
| `required` | `events, cursor, has_more, freshness` | `events, cursor, has_more` |
| `freshness` | **required**, and `Freshness.retention_days` required inside it | **absent entirely** |
| `cursor` | `format: uuid` | `format: uuid` |
| `event_type` | 20-member enum | `string` with an `example` |
| `entity_type` | 5-member enum | `string` with an `example` |

The emitted class is `RegistryFeedResponse` with `freshness: Annotated[Freshness, …]` —
**not optional** **[M]**. This is the before/after §7 needs.

---

## 7. The duplicates and the dead weight

### 7.1 `FeedEvent` vs `RegistryEvent` — do NOT repoint it yet, and here is the measured why

What `FeedEvent` is: **not the OpenAPI spec's output at all.** It is literal Python appended by
`fix_spec_reality_gaps` in the generator, under the comment *"the registry feed endpoint now
declares its response inline, so datamodel-code-generator no longer emits the named models"*
**[F, §5; the code is at `scripts/generate_registry_types.py:162-176`]**. So a hand-written patch
inside a generator duplicates, more weakly, a type the emission already produces from a
document.

**Before/after, for `FeedEvent`:**

| | today (`FeedEvent`) | repointed (`RegistryEvent`) |
|---|---|---|
| `event_type` | `str` — any value | `RegistryEventEventType`, 20 members, a `StrEnum` |
| `fnmatch(event.event_type, pattern)` in `registry_sync.py:126` | works | **still works** — the emitted enums subclass `str` **[M, `_str_enum`]** |
| a 21st event type the service adds | accepted, dispatched, ignored by handlers | **refused**, and `poll_once` raises until the bundle is bumped |
| `created_at` | `str` | `WireDatetime` |
| `strict_validate`, `__adcp_schema__`, a graded pair | none | all three |

**Before/after, for `FeedPage` — and this one is a blocker:**

`FeedPage` is `{events, cursor, has_more}`; `RegistryFeedResponse` additionally **requires
`freshness`**. `get_feed` does `self._parse(FeedPage, resp.json(), "Feed poll")` →
`model_validate` **[M, `registry.py:3148`]**. So repointing `FeedPage` to the emitted class
**refuses every feed response that omits `freshness`** — and the service's own OpenAPI document
says it omits it.

**Which of the two documents describes the live service is [U] — I cannot call the API from
here.** That is precisely the question that must be answered before the repoint, and it is a
one-request measurement for whoever can make it.

**Recommendation.** Repoint in two steps, not one:

1. **`FeedEvent` → `RegistryEvent`, gated by a differential test, not by a hope.** The test:
   for every event type the service can emit today, the emitted enum has a member. Where it does
   not, the finding is an upstream ask against `core/registry-event.json`, not a reason to keep
   the weaker class. The forward-compatibility cost is real and is the owner's to accept: a
   strict feed consumer breaks on a new event type where a `str` one shrugs.
2. **`FeedPage` stays until `freshness` is settled.** Either the service sends it and the
   OpenAPI document is wrong, or it does not and `core/registry-feed-response.json` is wrong.
   One of the two is an upstream report; neither is a repoint.

### 7.2 The fourteen words a schema subject already owns

**[M]** — all 155 names resolve at `adcp.types.<Name>`, and 14 resolve to something that is not
the vendored module:

| word | the subject that owns it | its home |
|---|---|---|
| `Policy`, `PolicySummary`, `PolicyHistory`, `PolicyRevision`, `PolicyExemplars`, `ResolvedBrand`, `ResolvedProperty` | the SDK's own hand-written types | `adcp.core` |
| `Accreditation` | `protocol/get-adcp-capabilities-response.json#/…/accreditations/items` | emitted |
| `ValidationResult` | `property/validation-result.json#` | emitted |
| `PublisherPropertySelector` | `core/publisher-property-selector.json#` | emitted |
| `KellerType` | `brand.json` | emitted |
| `DelegationType` | `adagents.json` | emitted |
| `PolicyCategory` | `enums/policy-category.json` | emitted |
| `PolicyEnforcement` | `enums/policy-enforcement.json` (class `PolicyEnforcementLevel`) | emitted |

**This is a decided decision, and the precedent generalises.** The owner's ruling of 2026-11-18,
in `FINDINGS-sixwords.md`: *"As for the six words, it has to be schema. OpenAPI-derived thing
should not be even considered for the class emission as far as I understand."* The rule stated
there — **where two subjects answer to one word, the schema subject owns the short flat name and
the OpenAPI-derived one is reachable only at its own module path** — is implemented as
`adcp.types._decided`, a screen said at every layer rather than an ordering **[M, `src/adcp/types/__init__.py:368`]**.
Two words remain open and are not mine to close: `Metric` (its rival is an alias layer's word,
not a domain path's — `FINDINGS-sixwords.md` open question 1) and `AuthorizedAgent`
(`FINDINGS-rootnames.md`).

**The seven `adcp.core` words deserve one note.** They are hand-written, not emitted — so the
duplication is *hand-written SDK type vs generated OpenAPI type*, and the hand-written one won.
That is the same verdict §3 recommends for the rest.

### 7.3 ~130 classes held up by `legacy_names.py` alone — can the generator emit less?

Measured **[M / F]**:

```
155 classes
138 named in some import
 22 have a REAL importer
116 held by legacy_names.py ALONE
 17 named in no import at all
142 `from adcp.types.registry import …` statements in legacy_names.py
148 of the 155 names advertised in adcp.types.__all__
141 of them offered flat by _restored.__all__
```

`PublisherLookupResult` is the emblem: the spec states it, the generator emits it, **only
`legacy_names.py` imports it**, and the client method for that very endpoint returns
`dict[str, Any]` **[M]**.

**Can the generator emit less? Yes — three ways, in increasing order of what breaks.**

| option | mechanism | what breaks |
|---|---|---|
| **A. Emit all 155, stop ADVERTISING them** | drop the vendored module from `_restored.MODULES`, keep the explicit 16-name route in `adcp/__init__.py` | 141 advertised flat words withdraw. `tests/test_public_words_resolve.py` and `tests_emit/test_the_restored_flat_surface.py` are the gates. **Nothing's import of a class breaks** — `adcp.registry_types.<Name>` still resolves |
| **B. Emit only the reachable set** (`datamodel-code-generator --openapi-scopes`, or a filtered spec) | the 22 with a real importer, plus their field types' transitive closure | `legacy_names.py`'s 142 rows must shrink in step, and that file is GENERATED by `survey/emit_legacy_names.py` from `survey/name-table-9.6.1.json` — a table keyed on where a class was declared when a run with upstream's 9.6.1 wheel took it, **and the wheel is not in this repository, so the table cannot be re-derived** **[F, §7]**. So the relocation and any shrink must live in the generator that reads it |
| **C. Hand-write the needed types, delete the generator** (§3's recommendation) | ~22 classes, written once, each carrying a `SchemaRef` where a bundle document states the subject | the 133 unused names stop existing. This is the only option that also removes the regeneration hazard (F2) |

**Recommendation: C, reached through A.** A is behaviour-neutral at the import level and can
land alone; C is then a shrink of a file nothing but a name census reads. B is the worst of
both — it keeps the generator, keeps the hazard, and forces the un-re-derivable name table to
move.

**The 17 named in no import at all cost nothing to delete and are the honest first measurement
of whether anyone notices** — `tests/fixtures/public_api_snapshot.json` is the repo's only gate
on a public name quietly changing which object it resolves to, and **it cannot currently be
refreshed at all**: its test is already one of the baseline failures and its regeneration script
crashes on trunk with `AttributeError: module 'adcp.types._schemas.a2ui' has no attribute
'__all__'` **[F, §7]**. That is finding F6 and it is a prerequisite for grading any name change,
not a side issue.

---

## 8. The option this design does NOT recommend, stated so it can be chosen

If the owner wants typed coverage of all 94 operations **and** wants it inside the one compiler,
there is a clean route, and §5 and §6 are the measurement that it is cheap:

**Project the OpenAPI document into a synthetic draft-07 bundle, then run the one compiler over
it.** A pre-pass writes one JSON document per schema root (67 named by their component key, 494
named by `operationId` + response code), rewrites `#/components/schemas/X` into a document
reference, injects `$schema: draft-07` or selects 2020-12 explicitly, and adds the one `example`
row to `keywords.py`. Everything downstream is then reused **verbatim**: `bundle`, `catalogue`,
`keywords`, `lower/*`, `render`, `emit`, `harness`, the 2,570-pair gate, the byte compare, the
approximation machinery, `strict_validate`.

**The precedent for admitting a derived input already exists and carries its own condition.**
`rebuild-plan.md` §1, *A patched bundle is a legitimate input, and the test is the RECORD*: a
patch is admissible exactly when no patched document's record differs from the published one at
a key that decides acceptance, and `bundle.is_an_annotation(keyword, position)` is the predicate.
A projection is a stronger claim than a patch, so it takes the same instrument in differential
form: **at every one of the 561 roots, the projected document and the OpenAPI node must agree
about every constructed witness.** That is runnable with exactly the probe in §5.1.

**Why it is not the recommendation.** The owner has said twice that this lane is not open —
*"we still do not process openapi for now"* and *"OpenAPI-derived thing should not be even
considered for the class emission"*. And the value is low where it matters: the projection types
94 operations of which the client leaves 72 untyped today, while §3's recommendation types the
endpoints the protocol itself names. The route is written down here because it is cheap **if the
goal changes**, and because knowing it is cheap is itself a reason not to build anything
bespoke in the meantime.

---

## 9. The staged plan, with the figure that must not move at each stage

**The baseline, with provenance.** Quote these and nothing else:

```
make gate    7 failed / 2563 passed of 2570                        [B]
./check      emitted 1059 / refused 0; approximated 805 facts in 239 documents   [M, run here]
verify.json  graded 2570, pass 2548, not_pass 22                   [A]
make test    81 failed / 16118 passed / 2823 skipped / 0 errors     [F, this worktree; TASK.md says "in the 80s and falling"]
ruff src/    305 findings      make typecheck  4118 errors in 693 files   [F]
adcp.__all__ 745 names, 27 of them registry's, 17 resolving to the vendored module   [M]
adcp.types.__all__ 4,251 names, 148 of them registry's; _restored.__all__ 176, 141 registry's   [M]
registry tests  169 + 87 + 26 + 24 + 2 = 308 test functions over 5 files, all passing on trunk   [M / F]
```

`make typecheck-all` and `make validate-generated` **cannot complete either way** —
`scripts/check_type_ignore_contract.py` and `scripts/generate_versioned_stubs.py` do not exist
in this checkout **[F]**. Do not put either on a stage gate.

---

### Stage 0 — close the hole. Lands alone, needs no decision.

Land the four-clause `NOT_EMITTED` gate of §5.4, with `registry.py` named in the table as a
known exception. Nothing moves; the next extra file is a named failure instead of 2,051 silent
lines.

* **New figure:** one named test; 0 files of `src/adcp/types/` unaccounted for.
* **MUST NOT MOVE:** `./check` = `1059 / 0 / 805 in 239`. `make gate` = 7/2563 of 2570.
  `make test` = 81.

### Stage 1 — make "regenerate" mean something, or stop saying it.

Two one-line defects (F1, F2) plus a version pin. Then `make regenerate-registry` is a no-op you
can put on a gate; today it crashes after writing, and its output renames a public class.

* **Gate:** `make regenerate-registry && git diff --exit-code src/adcp/types/registry.py`.
* **MUST NOT MOVE:** the 17 names `adcp.__all__` resolves from the module, and
  `adcp.AgentHealth.__module__`. `make test` = 81.
* **Declared to move:** the committed file's byte count, once, when the pinned generator's
  `extra="allow"` lines are accepted. **If the owner takes §3's recommendation, skip this stage
  entirely** — the generator is retired, not repaired.

### Stage 2 — the relocation. `adcp.types.registry` → `adcp.registry_types`.

22 files, measured by doing it **[F, §7]**: the brief's 7, plus `legacy_names.py` +
`survey/emit_legacy_names.py` (142 imports, regenerated: 142 in / 142 out), `_restored.py` (one
`home()` function, reading the one place the path is stated), `survey/upstream_machinery.py`
(where path identity silently stands in for byte identity — the bytes do not change and the
answer flips to "not restored", reddening a green test), `aliases.py` (one path token in prose),
`pyproject.toml` (**three** references: ruff `extend-exclude`, the black regex
`/(tasks|_generated|registry)\.py$` which a new name does not match, and the mypy override), and
8 tests. **And no sentence in `src/` may name `adcp.types.registry` afterwards** —
`tests_emit/test_prose_resolves.py` imports every `adcp`-rooted path any shipped docstring
spells; naming the FILE path is the workable form **[F]**.

* **MUST NOT MOVE** (every one of these was measured to hold across exactly this move **[F, §8]**):
  `make test` 81/16118/2823/0 **and the 81 failure NAMES, diffed line for line**;
  `make gate` 7/2563; `./check` identical; 141 words offered flat at `adcp.types.<word>`;
  17 names in `adcp.__all__`; `from adcp import AgentHealth` works; `adcp.types.BrandSource` is
  the vendored class; the six contested words still `adcp.core`.
* **Declared to move:** `adcp.types.registry` becomes `ModuleNotFoundError`. Intended.
* **Known stale and not fixable in the stage:** `tests/fixtures/public_api_snapshot.json`
  carries 18 `adcp.types.registry` values, its test is already a baseline failure, and its
  regeneration script crashes (F6).

### Stage 3 — the duplicate subjects, one at a time.

`FeedEvent` → `RegistryEvent` behind the differential event-type test (§7.1). `FeedPage` **does
not move** until `freshness` is settled against the live service.

* **Gate:** the differential test names every event type the emitted enum lacks.
* **MUST NOT MOVE:** `tests/test_registry_sync.py` 24 and `tests/test_property_registry.py` 26
  test functions stay green; `make test` = 81.
* **Declared to move:** the feed now refuses an unknown `event_type`. The owner accepts the
  forward-compatibility cost or the stage does not land.

### Stage 4 — withdraw the advertisement (option A of §7.3).

The vendored module leaves `_restored.MODULES`; the explicit 16-name route stays.

* **MUST NOT MOVE:** `adcp.__all__` = 745 and its 17 resolving registry names; every name
  `adcp.registry_types.<Name>` resolves; `make gate` 7/2563; `./check` identical.
* **Declared to move, and it must be declared BEFORE the run, not discovered after:**
  `_restored.__all__` 176 → ~35; `adcp.types.__all__` 4,251 → ~4,110; 141 flat words withdraw.
  `tests/test_public_words_resolve.py` and `tests_emit/test_the_restored_flat_surface.py` are the
  two gates that will speak.

### Stage 5 — hand-write the ~22 and delete the generator (option C).

Each hand-written class that corresponds to a bundle document carries a `SchemaRef` and gets
`strict_validate` for free (§5.3 item 2). `scripts/generate_registry_types.py`, its 51-entry
rename table, `make regenerate-registry`, the ruff/black/mypy exclusions and
`tests/test_registry_types_drift.py`'s prefix-match clause all go.

* **MUST NOT MOVE:** the 17 advertised names; 308 registry test functions green;
  `make test` = 81; `make gate` 7/2563; `./check` identical.
* **Declared to move:** 133 class names cease to exist; `src/adcp/types/registry.py` and
  `scripts/generate_registry_types.py` are deleted; `legacy_names.py` loses ~142 rows via its
  own generator.

### Stage 6 — only if §8 is chosen. Not recommended.

The projection, gated by the differential record check. Nothing before Stage 5 depends on it.

---

## 10. Findings found on the way, not fixed here

* **F1 — `make regenerate-registry` crashes after writing its output.**
  `format_output` invokes a bare `"ruff"`, which is not on `PATH` (ruff lives in `.venv`), and
  `check=False` does not cover a missing executable, so it raises `FileNotFoundError` **after**
  `OUTPUT_PATH.write_text` **[F, §6; the code is `scripts/generate_registry_types.py:237-248`]**.
  One line: `[sys.executable, "-m", "ruff", …]`, the way `run_codegen` already reaches
  `datamodel_code_generator`.
* **F2 — a regeneration today silently renames a public class.** `CLASS_RENAMES["Pas"]` is dead;
  the generator now names that class `PassItem`, so `PolicyExemplarPass` disappears from the
  public surface on the next run **[F, §6]**. The file is 2,051 lines committed against 2,099
  regenerated, differing at 56 lines.
* **F3 — two `pyproject.toml` entries name a path this checkout does not carry.**
  `src/adcp/reporting/_preview/` does not exist, yet ruff `extend-exclude` lists
  `src/adcp/reporting/_preview/_generated_models/` and `package-data` lists
  `reporting/_preview/schemas/**/*.json`; `scripts/vendor_reporting_status_preview.py`, which
  the comment names, is absent **[M]**. Harmless today, and it means the registry module is the
  **only** second-generator type output in this checkout — which is worth knowing when quoting
  precedent.
* **F4 — `adcp.ValidationResult` and `adcp.types.ValidationResult` are different classes.**
  `adcp/__init__.py` routes the word explicitly to the vendored module while
  `adcp.types._decided` screens it to `property/validation-result.json`'s class **[M]**.
  Pre-existing, independent of any move, and the same shape as the collision
  `FINDINGS-sixwords.md` closed one level down.
* **F5 — `schemas/registry-openapi.yaml` does not round-trip to JSON.** `yaml.safe_load`
  produces 9 `datetime`/`date` objects from unquoted `example` values (e.g.
  `PolicySummary.effective_date.example: 2025-05-25`), so `json.dumps` raises without a
  coercion **[M]**. Only matters if the spec is ever shipped as a record, but it would bite the
  first person who tries.
* **F6 — the public-API snapshot cannot be refreshed.**
  `scripts/regenerate_public_api_snapshot.py` crashes on trunk with `AttributeError: module
  'adcp.types._schemas.a2ui' has no attribute '__all__'`, and its test is already a baseline
  failure **[F, §7]**. It is the repo's only gate on a public name quietly changing which object
  it resolves to, so it is a prerequisite for Stages 2, 4 and 5 — a lane of its own.
* **F7 — the drift test's coverage clause is close to unfailable.**
  `test_all_component_schemas_have_types` accepts a match on `schema_name in cls or
  cls.startswith(schema_name[:5])` — a five-character prefix **[M]**. The one gate standing over
  the generated half asserts very little.

---

## 11. What I could not measure

Stated plainly, because an unmarked guess in a design document becomes a decision nobody
remembers taking.

1. **Whether the live service sends `freshness` on `GET /api/registry/feed`** — the core
   document requires it and the OpenAPI document omits it. One HTTP request answers it; I cannot
   make one from here. **This blocks the `FeedPage` repoint and nothing else.**
2. **Whether the service's event-type vocabulary is exactly the 20 members
   `core/registry-event.json` states.** Needed before Stage 3.
3. **Whether 805 approximated facts in 239 documents (`./check`) and the 1,183
   `Approximation(…)` declarations I counted in the committed tree are two readings of one
   number or a real divergence.** I used each only for its own claim and did not reconcile them.
4. **The relationship between `make gate`'s 7/2563 and `verify.json`'s 22 not-pass.** The
   artifact's six checks include the three bookkeeping ones, which the contract gate
   deliberately does not grade; the arithmetic is consistent with that but I did not run either
   command (`TASK.md` forbids it, at 8 and 24 minutes).
5. **Whether the operator half of `RegistryClient` has real adopters.** §3's narrowing
   recommendation would withdraw or demote it, and I have no usage data.
6. **The wheel-size and import-time cost of any option.** `tests/test_import_memory.py` budgets
   peak RSS per entry module; none of the stages above was measured against it.
7. **Whether `codegen/catalogue.py`'s untitled-group path would in fact name the 494 inline
   roots acceptably.** §6.3 establishes that L2C's titled-evidence rule has no input here; what
   the untitled path would actually produce is unmeasured, and it is the one real risk in §8.
