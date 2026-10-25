"""Apply the survey's decisions to a COPY of the plan and emit a git-format patch.

The plan itself is never touched: three rows are citing it as authority right now.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

SP = pathlib.Path(sys.argv[1])
TARGET = SP / "docs" / "plan" / "rebuild-plan.md"
text = TARGET.read_text()


def splice(anchor: str, addition: str) -> None:
    """Insert ``addition`` immediately after ``anchor``, which must occur once."""
    global text
    if text.count(anchor) != 1:
        raise SystemExit(f"anchor occurs {text.count(anchor)} times:\n{anchor[:160]}")
    text = text.replace(anchor, anchor + addition)


# --------------------------------------------------------------------------- #
# A. into D2, after the shape-union paragraph
# --------------------------------------------------------------------------- #
A_ANCHOR = """  **A union whose branches share a property set but differ in a property's SCHEMA is a shape
  union and keeps a class per branch.** 12 nodes, 85 branches: `core/registry-event.json` is 20
  branches over `entity_type`, `event_type` and a `payload` that differs at each one. D3 names
  those from the discriminator `const`, so each class is named for the value it carries rather
  than by position.
"""

A_ADD = """
  **An object's own facets beside a union AT ONE NODE compose, and the object rule applies
  first.** A node may declare `properties`, `required` or `additionalProperties` and a
  `oneOf`/`anyOf` together, and draft-07 applies both to the same instance: it satisfies the
  node's own object statement AND exactly one branch. So the base carries the node's own
  properties as fields and its `additionalProperties` reading by D8, `_ROOT_REQUIRED` records
  the node's own required set as §4 already states, and each branch subclass inherits them —
  D2's union rule applied after the node's own object rule, in that order, which is the
  ordering D7 already states for a conjunct whose content is a union.

  Measured over all 1,054 portable documents, at every schema position: **19 distinct keyword
  signatures, 88 nodes.** The two largest are `{additionalProperties, anyOf, properties,
  required, type}` at 31 nodes (`core/attestation-evaluation.json#/properties/action_binding`)
  and `{additionalProperties, anyOf, properties, type}` at 18
  (`core/canonical-forecast-point.json#/properties/viewability`); `core/registry-event.json`
  and `core/postal-country-system.json` are both in the set, at their roots. This was the
  largest single gap the signature survey found (`salesagent-j3k2l.53`), and two places in
  this build already name it from one side without deciding it: §4's `_ROOT_REQUIRED` names
  the fact the reading needs, and `applied_schema`'s KNOWN CEILING names the same shape from
  the harness side — "a row whose root asserts more than a type about the same instance needs
  this extended". One decision closes both.

  **This reading hands D3's new nested rule a collision its stated qualifier does not
  separate, and the question is D3's rather than this decision's.** Each branch subclass
  declares the node's properties, so sibling branches declare nested classes for the SAME
  property name in one module — and D3 names a nested class `pascal_case(property)`, qualified
  by *the nearest enclosing property* where two nodes of one module would collide, which is
  the same for every sibling. Measured over all 1,054 portable documents at TYPE positions
  only (a node under `not`, `if`, `then` or `else` is a rule and lowers no class, §6's third
  counting rule): **1,063 nested model nodes take a name in 303 modules, 84 names are taken by
  two or more nodes in 62 modules over 299 nodes, the enclosing property separates 9 of the
  84, and 55 of the 75 it does not separate have members differing ONLY by a combinator
  index.** The largest are 44 nodes taking `AssetsItem` in `core/format.json`, 14
  `ComponentsItem` in `formats/canonical/coordinated_placements.json`, 10 `Payload` in
  `core/registry-event.json` and 9 `Payload` in `core/wholesale-feed-event.json`. D3's own
  figure of 19 collisions in 9 modules is over the EMITTED tree, which is ~705 of the 1,054
  and excludes the shape unions, so the two numbers measure different populations and both
  are right; the direction is that the population the rule will meet is larger and is
  dominated by a shape the qualifier does not address. The minimum reading is that a collision
  between branch siblings is qualified by the BRANCH's name, which D3 already derives — but
  that is a sentence in D3 and this decision does not write it.
"""

splice(A_ANCHOR, A_ADD)

# --------------------------------------------------------------------------- #
# B. into D5, after its opening paragraph
# --------------------------------------------------------------------------- #
B_ANCHOR = """  field-bound constraint does none of those. It also keeps `= 50` meaning a default rather than
  conflating the default with metadata.
"""

B_ADD = """
  **Each value keyword binds as the document's own fact, and the mapping is a table rather
  than two worked instances.** This decision was written with a rendering for a numeric bound
  (`ge`/`le`) and one for `{"minItems": 1}` (`min_length`), and the keyword-to-constraint
  mapping was never stated — so eleven keywords had a binding rule and no rendering. Sites are
  TYPE and rule positions together, over all 1,054 portable documents:

  | the document states | the annotation carries | sites | documents |
  |---|---|---|---|
  | `minimum` | `ge` | 1,083 | 288 |
  | `maximum` | `le` | 197 | 115 |
  | `exclusiveMinimum` | `gt` | 58 | 30 |
  | `exclusiveMaximum` | `lt` | 4 | 4 |
  | `minLength` | `min_length` | 771 | 287 |
  | `maxLength` | `max_length` | 607 | 243 |
  | `pattern` | `pattern` | 830 | 345 |
  | `minItems` | `min_length` | 1,075 | 347 |
  | `maxItems` | `max_length` | 147 | 88 |
  | `format` | selects a TYPE, never a constraint | 806 | 300 |

  `multipleOf` has **0 sites**, so it has no rendering here and the first document to carry
  one refuses by name. That is a row asserted empty while it is empty, which is D14's rule.

  **`gt` is not `ge`, and the bundle chose between them 730 times.** 672 sites state
  `minimum: 0` and 58 state `exclusiveMinimum: 0` — all 58 of them, 57 on a `number` and 1 on
  an `integer`. The two readings differ on exactly one instance, so rendering either keyword
  as the other makes 58 fields accept a zero their document refuses or 672 refuse a zero their
  document accepts. This decision already says the same thing from the other side:
  `PositiveInt` for `{integer, minimum: 1}` renders `exclusiveMinimum: 0` and is refused for
  stating a different fact about the same integers.

  **Measured, not reasoned.** At every site the keyword's own value supplies the boundary
  witness — the array one shorter than `minItems`, the value `exclusiveMinimum` and
  `exclusiveMaximum` name — and the witness goes to the document through `jsonschema` twice,
  once at the node and once at the node with the keyword deleted. A keyword CONSTRAINS where
  the witness is refused with it and accepted without, which is what rules out a sibling
  keyword having done the refusing. `exclusiveMinimum` constrains at **58 of 58** sites,
  `exclusiveMaximum` at **4 of 4**, `minItems` at **1,044 of 1,075**. The other 31 are witness
  artifacts with the cause named rather than sites where the keyword does nothing: 15 where a
  sibling `contains` refuses the same short array, 14 where the element type refuses the
  filler the witness is built from, 1 where an unresolved `$ref` at the node stops the
  validator, and `core/creative-localization.json#/properties/target_variants`, which states
  `minItems: 0` and forbids nothing at all.
"""

splice(B_ANCHOR, B_ADD)

# --------------------------------------------------------------------------- #
# C. into D6
# --------------------------------------------------------------------------- #
C_ANCHOR = """  subschema that must not match). Those six are the whole population. Everything else is an
  annotation, which pydantic enforces on the constructor without a rule. A rule narrows the
  constructor; acceptance stays with the schema (D4).
"""

C_ADD = """
  **Those six are seven. `contains` is a rule, and the closure claim above was measured
  false.** An array holding at least one item that matches a subschema spans a collection and
  has no field-level annotation in pydantic, which is this decision's own membership test, and
  it occurs at **120 sites in 46 documents**. The plan named the keyword only as a position the
  census walk descends (§6) and as a deferral count (§7.1), never as a family, while this
  decision said its six were the whole population. Seven families, and `contains` is one.

  **`propertyNames` at a RULE position is decided by neither side, and is named rather than
  decided.** D5 types a mapping's KEY from `propertyNames`, and §6's own census rule says that
  under `not`, `if`, `then` or `else` a keyword is a rule and no type is lowered from it — so a
  `propertyNames` below a conditional falls between the two. Two nodes carry it, both at
  `core/catalog-item-availability-state.json#/allOf/0/else`, in the signature
  `{not, propertyNames, required}`; it is the whole of the residue the signature survey could
  not place in a family (`salesagent-j3k2l.53`). The minimum reading is that it joins this
  list as an eighth family. Nothing forces the question until a document reaching those two
  nodes emits, and a row that decides it decides it with a document in hand.
"""

splice(C_ANCHOR, C_ADD)

# --------------------------------------------------------------------------- #
# D. into D7, after the requiredness-overlay paragraph
# --------------------------------------------------------------------------- #
D_ANCHOR = """  the pattern named above as the clearest instance, where the subclass redeclares the field
  with the base's type and no default. Four documents sit there, refused by a reader that has
  no case for a conjunct holding neither a `$ref` nor `properties`.
"""

D_ADD = """
  **The overlay is not only about requiredness: four nodes overlay a VALUE keyword on a
  referenced array.** `core/catalog-selection.json` at `/properties/ids`, `/properties/gtins`
  and `/properties/tags` each state
  `{"allOf": [{"$ref": ".../catalog.json#/properties/<x>"}], "uniqueItems": true}`, and
  `trusted-match/context-match-response.json` at
  `/properties/signals_by_provider/additionalProperties/properties/targeting_kvs` is the same
  shape with `minItems: 1`. The reading is this decision's own rule rather than a new one: the
  conjunct supplies the referenced type and the node's own keyword tightens it, so the field
  is that type carrying the extra bound — a constrained type under D5, named once and
  referenced, which is also what keeps the bound from being lost at a mapping value.

  An `allOf` of RULE-only conjuncts beside a node's own array keywords needs nothing here,
  because the conjunct rule below already covers it: three nodes are that shape, including
  `media-buy/legacy-purchase-continuation-input.json#/properties/accepted_losses`, each an
  `allOf` of `contains` conjuncts over an array that states its own `minItems` and
  `uniqueItems`.
"""

splice(D_ANCHOR, D_ADD)

# --------------------------------------------------------------------------- #
# E + F. two new decisions, after D14 and before **Layout.**
# --------------------------------------------------------------------------- #
E_ANCHOR = """  This bounds the suite permanently: nobody adds a check because something went wrong once. A
  defect either shows up in the harness's own verdict over the population, or the thing that
  prevents it is structural, or it is accepted and named in §9.
"""

E_ADD = """- **D15 — an annotation is admitted BY NAME, and the names are measured.** A keyword that
  constrains no instance contributes nothing to the emitted class, and the drop is reported.
  D7 says this already for a keyword draft-07 does not define INSIDE A CONJUNCT; the keywords
  below sit at arbitrary positions, so this decision states the rule where the conjunct rule
  cannot reach. Three populations carry the property and each is admitted on its own
  measurement, over all 1,054 portable documents — **18,203 nodes declaring something at a
  schema position, 97 distinct keywords**:

  - **Draft-07's own annotation keywords**, which the draft defines and which assert nothing
    about an instance: `$schema` (1,054 sites), `$comment` (48), `title` (1,460),
    `description` (9,591), `examples` (166), `default` (342), `deprecated` (179 sites in 95
    documents), `readOnly` (4), `writeOnly` (1), and `$id`/`example` at none.
    `description` and `default` are RENDERED, by §6's description-authority rule and by D4;
    the other nine have nowhere to go and are never a reason to refuse.
  - **The bundle's own `x-` namespace**: **30 names over 1,090 sites**, the largest being
    `x-entity` (515 sites in 260 documents), `x-adcp-validation` (179 in 135) and `x-status`
    (170).
  - **`notes` (2) and `enumMetadata` (4)**, the two names draft-07 does not define that
    annotate a document for a reader.

  **Every one was measured and none was assumed.** For all **63 non-vocabulary keywords** this
  decision touches, at every site, the keyword's own value AT THAT SITE was taken as a
  one-keyword schema and asked to judge a thirteen-instance corpus: **0 refusals over 184,418
  validations.** None of them can refuse any instance, whatever its value, and the mechanism
  is that `jsonschema`'s draft-07 vocabulary has 32 keywords and not one of these is among
  them. A keyword the validator cannot consult cannot narrow the document, so dropping it
  cannot make the model wider than the schema it names.

  **Membership is by name and never by prefix.** A prefix rule admits every future `x-`
  keyword unexamined, including one that constrains, and this plan excludes that twice on its
  own ground: D5 takes the https arm as "the 47 patterns that are EXACTLY `^https://`, as a
  literal set and not as a rule about regexes", because a literal set can be audited where a
  predicate cannot, and §6 says a derived rule admitting a widening is invisible and
  permanent. So the 30 names are enumerated, a thirty-first refuses by name, and that refusal
  is the designed outcome rather than a failure.

  **A registry document's own INSTANCE DATA at a schema root is not an annotation.** Nineteen
  names over 25 sites — `version` (4), `lastUpdated` (3), `last_updated`, `mappings`,
  `vocabulary`, `governance`, `extensions`, `_generated`, `_generatedAt`, `adcp_version`,
  `architecture`, `asset_types`, `baseUrl`, `prerelease`, `protocol_layers`,
  `published_version`, `stability`, `usage_notes`, `versioning` — are the payload of five
  registry, vocabulary and index documents carried beside their schema. They refuse nothing
  either, measured in the same run, but admitting them would call a registry's `mappings`
  payload an annotation and grow the set by a data field name per registry. They stay refused.

  **`title` constrains nothing and is NOT an annotation, because D2 reads another keyword
  through it.** It refuses nothing — it is one of the 63 above — and it decides what a node
  becomes anyway: D2 says a value set no name reaches is a `Literal` and a NAMED enum node is
  a `StrEnum`, so the presence of a title is the input that selects between two renderings.
  Measured: **226 enum nodes carry a title and 843 do not**, and the projection
  `{enum, type}` alone holds 226 titled and 679 untitled nodes — 905 nodes that a rule
  projecting `title` out would merge into one signature with two different answers.

  **The test that draws is the one to apply to the whole set: a keyword is an annotation for
  this purpose only where projecting it does not change the answer.** `title` fails it because
  it selects another keyword's reading, and the nineteen payload keys above fail it because
  their decision IS the refusal that projecting them would hide. Everything else in the three
  populations passes, and the figures each reading produces are in `salesagent-j3k2l.53`'s
  report rather than here, because a signature count is an instrument's output and not a fact
  about the bundle.

  **What this decision cannot buy, and the direction in which it does not fail.**
  `x-adcp-validation` carries instance obligations at **179 sites in 135 documents**, and no
  draft-07 keyword expresses any of them. Dropping them cannot make the model wider than its
  DOCUMENT, because the document does not enforce them either — the keyword is one of the 63
  measured above. The gap is between the document and the written spec, so it is upstream.

  **Its content was measured, because "enforce the machine-readable part and report the rest"
  is the obvious second reading and the measurement does not support it.** Classifying every
  value by what it IS rather than by the key holding it: **164 bespoke keys holding an English
  sentence, 137 `verifier_constraints` entries holding one, 74 `spec` values naming a docs
  path, 60 holding a single token, 47 an object of names, 10 a boolean, 9 a list of sentences,
  7 a list of names.** Reading by key name misleads twice over: `ordered_bounds` sounds
  structured and both its values are the sentence "minimum MUST be less than or equal to
  maximum", while `unique_config_generation`, `immutable_generation`, `secret_rejection`,
  `account_isolation` and ten more bespoke keys hold sentences too. **Exactly 16 entries
  across 14 documents are machine-readable**: six `unique_item_properties`
  (`["representation_id"]`, `["kind"]`, `["format_option_id"]`, `["creative_id"]`,
  `["capability_id"]`), two `member_of`, and one each of `map_keys_subset_of_array`,
  `resolver_response_binding`, `disjoint_place_fields`, `allowed_slot_asset_types`,
  `required_when`, `schema_required_when`, and two description-only objects.

  **Enforcing those 16 is refused on this plan's own ground rather than on effort.** Each
  states something draft-07 cannot — uniqueness BY A KEY is not expressible at all — so the
  document accepts every instance they forbid. Measured with a control, on
  `core/forecast-point-dimensions.json`, whose root states
  `unique_item_properties: ["kind"]`: a one-item list is ACCEPTED (so the witness conforms)
  and `[{"kind": "device_type", "device_type": "ctv"},
  {"kind": "device_type", "device_type": "mobile"}]` is ACCEPTED too, while the keyword
  forbids it — the two items differ, so the node's own `uniqueItems: true` is satisfied, and
  they share `kind`. **That document assigns the job itself, and not to a type SDK**: its own
  text reads "JSON Schema draft-07 cannot express unique-by-property for this array shape, so
  conformance tooling should reject repeated `kind` values." A D6 rule enforcing one therefore
  makes the class refuse a
  payload `strict_validate`'s schema half accepts: `check_accepts` draws from the document and
  reports `model_refused_valid`, while the schema comparison sees nothing at all, a rule
  having no rendering in `model_json_schema()`. That is the model-narrower-than-its-document
  direction, which §6 names as the only one that makes a correct SDK refuse valid traffic.
  D6's "a rule narrows the constructor; acceptance stays with the schema" holds for its seven
  families because every one of them is a keyword the DOCUMENT states, so rule and schema
  agree; these sixteen would be the first rules where they disagree.

  So there is ONE decision and not two: the whole keyword contributes nothing, the drop is
  reported, and the 16 machine-readable entries are reported as a named subset so the bundle
  has a list to work from. **No SDK enforces it today** — measured across the TypeScript
  client (3 hits, all generated doc comments carrying the schema's own prose), Python v9 (4
  files) and this tree (0 `.py` hits, 58 packaged `.json` copies) — so the decision changes no
  behaviour and records why.

  **The sharpest instance is an open vocabulary written in the namespace the validator
  ignores.** `enums/advertiser-industry.json` states an `enum`, `x-extensible: true` and
  `x-pattern: "^[a-z][a-z0-9_]+(\\\\.[a-z][a-z0-9_]+)?$"` at its root — the known members
  beside anything matching the pattern, which is exactly the construct D2 decides for
  `core/geo-place-system.json` and `core/geo-place-type.json` where the bundle spelled it as
  an `anyOf`. Spelled this way the document's accepted set is the CLOSED enum, because
  `jsonschema` enforces `enum` and ignores the other two, so a closed `StrEnum` is faithful to
  the document and the document is narrower than its author's own statement. `x-extensible` is
  at 2 sites and `x-pattern` at 1.

  **`x-canonicalization` was the other candidate to constrain and it is already covered.** All
  16 sites read `"set"`, and all 16 carry `uniqueItems: true` and a `minItems` beside it — so
  the duplicate half IS the document's own `uniqueItems` (D6) and the order half is not an
  acceptance statement at all, both orders being accepted. It adds nothing at any of its
  sites. `x-adcp-open-payload` measures the same way: 3 of its 4 sites sit beside
  `additionalProperties: true`, which D8 already reads as `allow` with retention, and the
  fourth is a typeless node that D2 reads as `Any`.

  **Three things this decision leaves UNDECIDED, each with what would decide it.**

  - **Whether `deprecated` RENDERS.** 179 sites in 95 documents, 178 `true` and 1 `false`, 16
    of them at a root. pydantic renders it from `Field(deprecated=True)` and the emitted tree
    declares it nowhere, so the schema comparison's `missing` is 0 only because no graded
    document carries one yet; the first that does reports it. Admitting the name here settles
    that it constrains nothing and settles nothing about the rendering. What decides it is a
    graded pair: the first document carrying a `deprecated` that emits, which makes both
    answers measurable against the comparison instead of arguable.
  - **Whether any `x-` fact belongs ON the class** as a `ClassVar` — `x-status`,
    `x-mutates-state`, `x-entity`, `x-operation-family`. This decision says they contribute
    nothing to what the class accepts or states about itself, which is the honest reading of
    the measurement, and carrying them is a different question about what the SDK offers
    BEYOND types. What would decide it is a consumer that needs one, and nothing in this plan
    asks for it; until then a `ClassVar` would be a fact no check grades.
  - **Whether the bundle should state `x-adcp-validation`'s obligations in a form a validator
    can read.** Upstream, not here. What decides it is the bundle, and the 16
    machine-readable entries above are the list to start from.

  **One of these is a fact the SDK renders under another name, and it is dropped today.** The
  enum row reads `enumDescriptions` (137 sites in 135 documents) into member docstrings;
  `enums/signal-value-type.json` carries **`x-enum-descriptions` and no `enumDescriptions`**,
  so that one document's three members emit with no documentation. Admitting the name here is
  what drops it; carrying it is a one-line change in the enum row, and this decision records
  which it is rather than leaving the drop unnamed.
- **D16 — `discriminator` constrains no instance and is not a naming input either.** 81 sites
  in 73 documents, 28 distinct values, 51 of them at a document root; the value is always
  `{"propertyName": "<key>"}`. It is OpenAPI's keyword and not draft-07's, so `jsonschema` has
  no validator for it: measured at every site over the same thirteen-instance corpus, **0
  refusals over 1,053 validations**. And D3's second rung reads a branch's name from the
  BRANCH'S OWN `const`, never from this keyword, so the naming rule does not consult it: at
  **75 of the 81 sites every branch `const`- or `enum`-tags the property the keyword names**,
  which makes the keyword a restatement of what the branches already say. At the other 6 the
  tag sits behind a `$ref` and D3's first rung — the branch's own title — answers instead;
  `core/assets/asset-union.json` with 21 `$ref` branches and `core/pricing-option.json` with
  10 are the two largest, and `core/requirements/catalog-field-binding.json` is the one node
  where some branches tag it inline and some do not.

  So it contributes nothing to the emitted class and the drop is reported. **The emitter reads
  it two ways today and this decision settles which.** `codegen/lower/union.py` calls it an
  annotation in draft-07 and reads it as D3's naming property; `codegen/compiler.py`'s
  `BUNDLE_ANNOTATIONS` note says it "COULD CONSTRAIN AN INSTANCE" and keeps refusing on it.
  The measurement says it cannot, and it is the refusing reading that can cost a document —
  the population it can reach is the 73 documents that carry the keyword, 51 of them at a
  root.
"""

splice(E_ANCHOR, E_ADD)

TARGET.write_text(text)
BASE = __import__("os").environ.get("BASE", "HEAD")
base_copy = TARGET.with_suffix(".base.md")
base_copy.write_text(subprocess.run(
    ["git", "show", f"{BASE}:docs/plan/rebuild-plan.md"],
    cwd="/Users/konst/projects/acp-j3k2l53", capture_output=True, text=True, check=True).stdout)
out = subprocess.run(
    ["git", "diff", "--no-index", "--src-prefix=a/", "--dst-prefix=b/",
     str(base_copy), str(TARGET)],
    cwd="/Users/konst/projects/acp-j3k2l53", capture_output=True, text=True,
)
patch = out.stdout.replace(str(TARGET), "docs/plan/rebuild-plan.md")
patch = patch.replace(str(base_copy), "docs/plan/rebuild-plan.md")
patch = patch.replace("bdocs/plan/", "b/docs/plan/")
patch = patch.replace("adocs/plan/", "a/docs/plan/")
patch = patch.replace("rebuild-plan.base.md", "rebuild-plan.md")
pathlib.Path("/Users/konst/projects/acp-j3k2l53/survey-decisions.patch").write_text(patch)
print(f"patch written, {len(patch.splitlines())} lines")
