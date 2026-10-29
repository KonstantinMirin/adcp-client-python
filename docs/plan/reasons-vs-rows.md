# Reasons versus rows: the two differences

> **SUPERSEDED on 2026-10-29. Every figure below is measured at base `02841377` and none of
> them survives to trunk `26c20abc`** — the three numbers went `885 / 169` to `959 / 95` and
> the primary/chained split `60 / 109` to `18 / 77`. The audit was re-run in both directions
> at that trunk and its result is **in the tracker, not in this file**: `bd show
> adcp-client-python-10l` carries the summary, and every row it closed, corrected or filed
> carries its own measurement. Nineteen rows closed on "the obstruction is gone"; three
> unowned mechanisms were filed (`-3bg`, `-ot0`, `-uqf`), two of which account for 48 of the
> 95 refusals.
>
> **This file is kept as the record of the first run, not as a reading of the compiler.** It
> is left unedited on purpose: a stale audit that says which base it was taken at is
> evidence, and the same document re-written in place would lose the one thing the re-run
> proved — that a stated figure goes stale and a stated reading does not.

An audit of one question — **does the set of reasons we cannot emit equal the set of rows we have
filed?** — compared in both directions. A reason with no row is work nobody has scheduled. A row
with no reason costs a lane when someone picks it up.

Everything below is measured on branch `audit/reasons-vs-rows`, worktree `/srv/ws/wt-audit`, base
`02841377`, over the 1,054 portable documents of `schemas/cache/3.2`. Where a figure disagrees
with the brief that commissioned this audit, the figure here wins and the disagreement is named.

    PYTHONPATH=.:src uv run --no-sync python -c "... bundle.portable(...)" > /tmp/portable.txt
    PYTHONPATH=.:src .venv/bin/python -m codegen --bundle schemas/cache/3.2 \
        --tree /tmp/audit-tree $(cat /tmp/portable.txt)

Rows are the 46 in `beads-snapshot.jsonl`; 23 of them are not closed.

---

## 0. The three numbers

    emitted 885 / refused 169 (deferred 120, verdict 49); accounted 934; 1054 named
    approximated 11 facts in 9 documents (WIDENED 1, UNDERDETERMINED 10; ours 11, upstream 0)

`portable` is 1,054. The brief's expected figures and the measured ones agree exactly, so there is
no finding here.

**The split of 169 into primary and chained is a finding.** Read off `Refusal.kind` rather than off
the sentence — the field `emit` records beside `resolved` — the partition is:

| | count | deferred | verdict |
| --- | --- | --- | --- |
| primary | **60** | 44 | 16 |
| chained | **109** | 76 | 33 |
| total | 169 | 120 | 49 |

The brief's splitting rule — "a chained refusal's detail says *its target X is refused* or
*resolved no target*" — is wrong on the second clause. `compiler.unresolved` mints
`Kind.VERDICT` with no `through=`, so the two "the run resolved no target" refusals are PRIMARY,
not chained. Including them gives 58 primary and 111 chained, which is the figure to discard.
The sentence test that reproduces `kind` exactly is *detail starts with* `its target `: 109
chained, 60 primary, confirmed against the field itself.

---

## 1. The reasons, grouped by cause

Seventeen mechanisms produce the 60 primary refusals. Grouping is by the mechanism the detail
describes and the code site that produces it, not by wording: `G2` and `G3` emerge from the same
line (`compiler._screen`) and are separate causes; `G7a` and `G7b` emerge from one function
(`_the_conjuncts_own_type`) at two clauses and are separate causes.

"Blocks" is derived from `bundle.edges`: the refused documents that transitively reference a
member of the group, excluding the group itself. "chained" restricts that to the 109 chained
refusals, which is the part the group alone would free. **Cascades overlap**: a document
downstream of two groups is counted in both, and the union of all cascades over the refused set is
130, which is larger than the 109 chained because a document can be downstream of a group and
carry a primary refusal of its own.

| | n | kind | keywords reported on | blocks | of which chained |
| --- | --- | --- | --- | --- | --- |
| **G1** restatement neither matches nor narrows | 13 | deferred | `$ref` `additionalProperties` `items` `properties` | 71 | 63 |
| **G2** a sibling of a nested union | 9 | deferred | `additionalProperties` `properties` | 42 | 34 |
| **G3** a handler claims no code for a keyword its cell lowers | 4 | deferred | `pattern` `oneOf` `anyOf` `additionalProperties` | 55 | 40 |
| **G4** a presence-only branch of a root union | 5 | deferred | `required` | 2 | 2 |
| **G5** `required` names a property no declaration declares | 3 | deferred | `required` | 28 | 24 |
| **G6** a conjunct carrying a combinator of shapes | 5 | deferred | `oneOf` `anyOf` | 28 | 23 |
| **G7a** a `$ref` conjunct whose target is not a class, beside declared fields | 3 | verdict | `allOf` | 61 | 48 |
| **G7b** two conjuncts each resolve to a non-class | 2 | verdict | `allOf` | 35 | 27 |
| **G8** a `not` beside a `$ref` conjunct that IS the type | 2 | deferred | `allOf` | 12 | 11 |
| **G9** an `allOf` of `type: array` composes no object | 3 | verdict | `type` | 2 | 2 |
| **G10** a branch with no identity to derive a name from | 2 | verdict | `title` | 7 | 6 |
| **G11** two nodes derive one class name | 1 | verdict | `title` | 0 | 0 |
| **G12** two declarations at one pointer | 1 | verdict | `$ref` | 0 | 0 |
| **G13** a local pointer reached through the conjunct arm is not a binding | 2 | verdict | `$ref` | 2 | 2 |
| **G14** the target declares no symbol at the fragment | 1 | deferred | `$ref` | 5 | 2 |
| **G15** the run resolved no target | 2 | verdict | `$ref` | 4 | 4 |
| **G16** a constrained arm of a type list beside another live arm | 1 | deferred | `minLength` | 43 | 39 |
| **G17** an `allOf` conjunct the enum row does not lower | 1 | deferred | `enum` | 2 | 1 |

The reported keyword is `_disagreeing`'s or the screen's and is not the mechanism: `_disagreeing`
returns `min()` over the differing keys, so `additionalProperties` wins alphabetically at five G1
sites that are about `properties`.

### G1 — the restatement arm (13 primary, blocks 71)

`compiler.lower_composition:2506`, reached from `_restatement` returning `None`.

    brand/verify-brand-claim-response.json          /definitions/signed_response/allOf/1/properties/payload
    brand/verify-brand-claims-response.json         /definitions/signed_response/allOf/1/properties/payload
    core/assets/daast-asset.json                    /oneOf/0/properties/macro_declarations
    core/assets/daast-tracker-asset.json            /properties/macro_declarations/items/allOf/1/properties/location
    core/assets/display-tag-asset.json              /oneOf/0/properties/macro_declarations
    core/assets/pixel-tracker-asset.json            /properties/macro_declarations/items/allOf/1/properties/location
    core/assets/url-asset.json                      /properties/macro_declarations/items/allOf/1/properties/location
    core/assets/vast-asset.json                     /oneOf/0/properties/macro_declarations
    core/assets/vast-tracker-asset.json             /properties/macro_declarations/items/allOf/1/properties/location
    core/tracker-execution-selector.json            /oneOf/1/properties/vast_versions
    governance/check-governance-response.json       /properties/runtime_attestation_evaluations/items/allOf/1/properties/action_binding
    media-buy/get-media-buys-response.json          /properties/media_buys/items/allOf/2/properties/indicators
    signals/get-signals-response.json               /properties/signals/items/properties/range

Instrumenting `_restatement` over the whole population records **21 `None` returns**, by clause and
by the keyword that fails `_at_least_as_tight`:

    11  not-at-least-as-tight    properties
     4  not-at-least-as-tight    items
     3  unresolvable-$ref-base   $ref
     2  not-at-least-as-tight    allOf
     1  not-at-least-as-tight    properties, required

**Every one is a subschema-valued keyword or an unresolvable `$ref` base. Zero are a scalar bound
or a disjoint enum.** That decides §4 item 3 below.

### G2 — a sibling of a nested union (9 primary, blocks 42)

`lower/union.py:1339 lower` → `nested` → `check_keywords` → `_screen`. A nested `oneOf`/`anyOf`
with a sibling keyword lowers to `A | B`, and `ir.TypeRef` carries a container and its members and
nothing else, so the sibling fact has no slot. Nine documents:
`account/sync-accounts-request.json`, `compliance/comply-test-controller-response.json`,
`core/canonical-forecast-point.json`, `core/forecast-point.json`, `core/format.json`,
`creative/preview-creative-response.json`, `formats/canonical/coordinated_placements.json`,
`formats/canonical/seller_rendered_stateful_display.json`, `governance/sync-plans-request.json`.

### G3 — a handler claims no code for a keyword its cell lowers (4 primary, blocks 55)

One mechanism, `compiler._screen`'s unclaimed-keyword arm with the default sentence, three
handlers:

    lower/const.py:133     core/postal-country-system.json  /anyOf/0/properties/country   pattern
    lower/union.py:1712    media-buy/get-reporting-status-response.json  /oneOf/0         oneOf
    lower/union.py:1712    media-buy/proposal-refinement.json  /oneOf/1                   anyOf
    lower/scalars.py:404   protocol/get-adcp-capabilities-response.json  …/oneOf/0        additionalProperties

Every cell involved lowers at the position; the handler does not claim the key.

### The remaining groups

* **G4** `lower/union.py:1771 _plan` — a branch declaring no property. This is `onq`'s Group B.
* **G5** `compiler.fields:1200` — `required` naming a name no `properties` declares, so it is a
  rule rather than a field. `core/product-format-declaration.json` (`format_kind`, `params`),
  `creative/validate-input-result.json` (`field`), `extensions/extension-meta.json` (`$id`).
* **G6** `compiler.lower_composition:2395` — a root conjunct whose own content is a `oneOf`/`anyOf`
  of shapes. `adagents.json`, `formats/canonical/display_tag.json`, `html5.json`, `image.json`,
  `governance/check-governance-request.json`.
* **G7a** `_the_conjuncts_own_type:1781` — the target is not a class and the node declares fields
  of its own. `core/package-signal-targeting.json`, `core/product-filters.json`,
  `core/vendor-pricing-option.json`.
* **G7b** `_the_conjuncts_own_type:1769` — two conjuncts each become the node's own type and the
  node has one. `core/targeting-input.json`, `core/targeting.json`.
* **G8** `_the_conjuncts_own_type:1845` — a `not` of required groups beside a `$ref` conjunct that
  IS the type: `ForbiddenGroups` is a rule on a class and the node has none.
  `core/canonical-product.json`, `core/product.json`.
* **G9** `compiler.lower_composition:2039`. `media-buy/legacy-purchase-continuation-input.json`,
  `media-buy/refine-proposals-request.json`, `media-buy/refine-proposals-response.json`.
* **G10** `lower/names.py:412 derive`. `core/requirements/asset-requirements.json`,
  `creative/get-creative-features-response.json`.
* **G11** `lower/names.py:573 assign`. `trusted-match/provider-registration.json`, name
  `TMPProviderRegistrationTrue`.
* **G12** `compiler.Module.declare:769`. `brand.json` at `/definitions/colors`.
* **G13** `emit.resolve:1179`. `core/account-identity-change-preview.json`,
  `core/registry-event.json`.
* **G14** `emit.resolve:1261`. `core/catalog-selection.json` wants `core/catalog.json#/properties/type`,
  whose node is itself a `$ref` to `enums/catalog-type.json`.
* **G15** `compiler.unresolved:351`. `account/list-account-changes-response.json`,
  `core/package-delivery-metric-value.json`.
* **G16** `lower/containers.py:772 multi_type`. `core/attestation-reference.json` at
  `/properties/embedded_credential/properties/value`, `type: ["object","string"]` with `minLength`.
* **G17** `compiler.lower_composition:2410`. `core/creative-approval-scope.json`.

### Sixteen verdicts, none of them derived from a cell

`docs/plan/architecture.md` §3: "a refusal's kind is derived from the cell and never chosen at a
raise site." All 16 primary verdicts are minted with a literal `kind=Kind.VERDICT` at the raise
site. `kind_for` is called by `_screen` and by the restatement arm and by nothing that mints a
verdict.

Two consequences are measured:

1. **Six verdicts report a property of the COMPILER as a property of a document** — G11, G12, G13
   and G15 — plus 4 chained verdicts behind them, 10 refusals in all. `architecture.md` §2 puts a
   compiler defect in `BuildFailure`, which no layer catches, precisely so it is not counted
   against a bundle that did nothing wrong. `adcp-client-python-g31` already argues this for G15;
   it holds for the other three for the same reason.
2. **Three verdicts are minted for work already scheduled as a widening** — G7a, which
   `architecture.md` §14 step 10 adopted on 2026-10-27 and `adcp-client-python-10l.21` carries —
   plus **27 chained verdicts** behind them. That is `rebuild-plan.md` §9's first mistake: a
   verdict minted for unwritten code reports clearable work as finished. `accounted` is
   `emitted + verdicts`, so these 30 inflate the headline figure by 30.

---

## 2. The rows

Twenty-three rows are not closed. For each, the reason from §1 it clears.

| row | status | clears |
| --- | --- | --- |
| `10l` | open | epic. Container, clears nothing itself. |
| `97w` | open | **G1** (13 primary, blocks 71). |
| `10l.21` | in_progress | **G4** (5) and **G7a** (3). Also the UNDERDETERMINED declarations, which are approximations and not refusals. |
| `857` | open | **G12** (1). |
| `g31` | open | **G15** (2). |
| `10l.33` | open | NO REASON — the guard over the decision set. Legitimately not about a refusal. |
| `10l.31` | open | NO REASON — the suite's memory ceiling. Legitimately not about a refusal. |
| `10l.22` | open | NO REASON — the upstream asks. Legitimately not about a refusal. |
| `10l.28` | in_progress | NO REASON — the `#8525` extract-and-`$ref` patch. Upstream, and a rename of emitted types; no document refuses for it. |
| `10l.32` | open | NO REASON — an acceptance narrowing in emitted modules (43 positions select `HttpUrl`), not an emission blocker. Legitimate. |
| `10l.23` | open (in_progress) | NO REASON — a consumer-facing base over 26 emitted documents. Legitimate. |
| `10l.30` | open | NO REASON — a separator reader. No union refuses today; the shape is 10 UNDERDETERMINED approximations. See §3. |
| `6zg` | open | NO REASON — the one live site emits and is green by the row's own measurement. A §8 decision, not work. |
| `zyn` | open | NO REASON — `core/delivery-metrics.json` emits; this is a red pair, not a refusal. Legitimate. |
| `5a1` | open | NO REASON — `core/format-option-ref.json` emits; this is a silent widening on an emitted module. Legitimate. |
| `10l.16` | open | NO REASON — `deprecated`'s cell is `rendered=False`; a grading-honesty row. Legitimate. |
| `10l.9` Wave 1 | open | NO REASON. See §3 and §4 item 4. |
| `10l.10` Wave 2 | open | **G3** partially (`oneOf`, `anyOf` at 2 sites) and the 10 `oneOf` approximations. |
| `10l.11` Wave 3 | open | NO REASON. |
| `10l.12` Wave 4 | open | the 1 `patternProperties` approximation. No refusal. |
| `10l.13` Wave 5 | open | NO REASON. |
| `10l.14` Wave 6 | open | NO REASON. |
| `10l.15` Wave 7 | open | NO REASON as titled; the registry half is already done. One real item survives — see §3. |

---

## 3. The two differences

### 3a. Reasons with no row — thirteen, filed

Each was filed under epic `adcp-client-python-10l` with the cascade figure and a derived acceptance
criterion. The criterion in every case is the same shape: the primary refusal clears, the named
cascade clears or reports its own next obstruction by name, and `APPROXIMATED` moves only where the
row declares a widening.

| filed | reason | primary | blocks | P |
| --- | --- | --- | --- | --- |
| `10l.34` | G2 — a sibling of a nested `oneOf`/`anyOf` has no slot on `ir.TypeRef` | 9 | 42 | 1 |
| `10l.35` | G3 — a handler claims no code for a keyword its cell lowers, at three handlers | 4 | 55 | 1 |
| `10l.36` | G5 — `required` names a property no declaration declares | 3 | 28 | 1 |
| `10l.37` | G6 — a root conjunct carrying a combinator of shapes | 5 | 28 | 1 |
| `10l.38` | G7b — two conjuncts each resolve to a non-class | 2 | 35 | 1 |
| `10l.39` | G8 — a `not` of required groups beside a `$ref` conjunct that IS the type | 2 | 12 | 1 |
| `10l.40` | G9 — an `allOf` at a node whose `type` is `array` | 3 | 2 | 1 |
| `10l.41` | G10 — a branch with no title, no `const` and no `required` | 2 | 7 | 1 |
| `10l.42` | G11 — two nodes of one module derive one class name | 1 | 0 | 2 |
| `10l.43` | G13 — a local pointer reached through the conjunct arm is not a binding | 2 | 2 | 1 |
| `10l.44` | G14 — the target declares no symbol at the fragment, and the node is itself a `$ref` | 1 | 5 | 1 |
| `10l.45` | G16 — a constrained arm of a type list beside another live arm | 1 | 43 | 1 |
| `10l.46` | G17 — an `allOf` conjunct the `enum` row does not lower | 1 | 2 | 2 |

`10l.37` is filed with a `blocks` dependency on `adcp-client-python-10l.30`, which measures three
of its five documents. No other filed row takes a dependency: the overlaps are stated in each
row's text so a reader sees them without the graph deciding an order the measurement does not
support.

Three of these have a guard whose own premise has expired and whose comment says so: G11 and G12
("Measured 0 times over the whole population, so this refuses rather than ordering them" — now 1
each), and G14 ("0 are reachable and the step whose population reaches one decides whether the
chain is followed" — one is now reachable). None of the three rows asks for the guard to be
removed; each asks for the decision the guard deferred.

### 3b. Rows with no reason — eleven proposals

**Nothing below is closed, superseded or reprioritised here.** Each is a proposal with its
evidence.

1. **`10l.9` Wave 1, `10l.11` Wave 3, `10l.13` Wave 5, `10l.14` Wave 6 — ALREADY DONE as titled.**
   Every keyword of those four waves has a non-`REFUSE` cell at every position, no primary refusal
   is reported on any of them, and no approximation names one. Measured per keyword over the
   bundle: `uniqueItems` 485 sites / 198 documents, `maxItems` 147/88, `else` 58/44, `minItems`
   1075/347, and so on, with **0 approximated facts** at every one. Under the exit condition
   `architecture.md` §14 itself prescribes for a wave after step 10 — "these keywords' OURS
   approximations reach 0" — all four are already at their exit condition. Recommend: close, or
   restate each as the specific residue it still owns, if any.

2. **`10l.15` Wave 7 — half done, and the surviving half is not what the title says.** The registry
   data keys are already `Effect.NOTHING` at every position (`keywords.py`, the `_REGISTRY_KEYS`
   loop) and **0 registry documents refuse** — `registries/v1-canonical-mapping.json` is the only
   one in the portable set and it emits. What survives is one line: `errorMessage` is still
   `Effect.REFUSE` at every position, so `keywords.grid_of("errorMessage")` answers `refused` and
   `rebuild-plan.md` §7 — whose heading reads "the set is empty" — still generates a row for it.
   §7 says this in its own words: "the cells move when §6's do." Recommend: retitle to the cell
   flip, which is one edit.

3. **`10l.12` Wave 4 — one fact, and it is `patternProperties`.** Of the 11 approximations, exactly
   1 is WIDENED and it is `core/creative-assets.json#` on `patternProperties`, rung CONTAINER.
   `dependencies` (32 sites) and `exclusiveMinimum` (58 sites) approximate nothing and refuse
   nothing. Recommend: restate as the `patternProperties` rule family §5(b) names ("a rule family
   for keys matching this pattern take this type, which no row has written"), and drop the other
   two keywords from the title.

4. **`10l.10` Wave 2 — the live content has already been spun out.** Its notes are entirely about
   the `format`/URL narrowing and say so: "This clears the `format` item only… The separate, real
   narrowing the scalar lane found is row `.32`." Of its nine keywords, `oneOf` and `anyOf` carry
   G3's two union sites and the 10 UNDERDETERMINED approximations — and `10l.30` claims those.
   Recommend: reconcile with `.30` and `.32` rather than running as a nine-keyword wave.

5. **`10l.30` and `10l.21`'s third shape are in direct contradiction over one population.**
   `10l.21` has LANDED 10 UNDERDETERMINED declarations on `oneOf` (8 content-standards documents,
   `core/evaluator-spec.json`, `registries/v1-canonical-mapping.json`), each attributed
   `rebuild-plan.md §5 combinators/oneOf`. `10l.30` states "EVERY union in the bundle separates, so
   no union need be refused or widened for an undecidable branch." If `.30` is right, all 10 are
   withdrawn and `APPROXIMATED` falls from 11 to 1. `.30`'s own scope note excludes "the 112 unions
   with a `$ref` branch", and none of the 9 approximating documents is named in `.30`'s evidence,
   so the overlap is unproven in both directions. Recommend: measure the 9 against `.30`'s four
   separators before either row lands more. Two rows must not hold opposite answers about one set.

6. **`6zg` — a decision row whose own measurement says do nothing.** Its population is one site,
   `core/canonical-media-buy-action.json#`, which "emits today, green" and which collapsing
   "reddens". What it actually asks for is a §8 pairing sentence. Recommend: it is a request against
   `rebuild-plan.md` §8, not a work row; see request 4 below.

7. **`10l.28` and `10l.22`'s ask 4 are the same upstream work.** `.22`'s fourth ask is "naming the
   constraints, where 85 of 160 aliases are a regex digest"; `.28` is the patch that names six of
   them and opens the PR. Recommend: `.22` records ask 4 as delegated to `.28`.

8. **`10l.22`'s figures are stale by an order of magnitude.** Re-measured now: ask 1 cites "134
   refusals, 75 sites" for a plain keyword beside a `oneOf` — the ROOT-sibling case produces **0**
   refusals today and the surviving NESTED case (G2) is 9 primary. `core/format-option-ref.json`,
   whose root `additionalProperties: true` the ask says "unblocks 14 documents", **emits**. Ask 3's
   "one pointer in url-asset.json blocks 13" is now 48. Ask 2's `adagents.json` is G6 and blocks 0.
   Recommend: re-measure before sending anything upstream.

9. **`zyn` and `5a1` and `10l.16` are grading-honesty rows, not emission rows.** Each is about a
   document that EMITS: `core/delivery-metrics.json`, `core/format-option-ref.json`, and every
   document stating `deprecated`. They are legitimate and correctly filed; they should not be
   counted against `refused` and should not be sequenced behind any wave.

10. **`10l.32` is the first row that will trip `10l.33`'s guard.** `.32` proposes changing
    `codegen/constraints.py`'s `url_type`, which is `.33`'s named unguarded decision ("a FUNCTION,
    so no registry guards it at all"). `.32` is **not a hazard**: it quotes the recorded rationale
    correctly, it does not propose "`AdCPUrl` everywhere", and it names what the obvious
    alternative would dissolve (`dump_exemptions.EXEMPT`'s six ORIGIN_ONLY positions). Recommend:
    sequence `.33` first, so `.32` lands against a pin rather than against a docstring.

11. **No other open row's text would lead a reader to reverse a recorded decision.** Scanning all
    23 non-closed rows for `url_type`, `URL_IMPLIED`, `FORMAT_SHAPES`, `_TIGHTER_BOUND`,
    `_ALIEN_VALUES`, `dump_exemptions.EXEMPT`, `PIN`, `ir._SECTION_7_APPROXIMATION`,
    `keywords._REFUSED` and `lower/union.ROOT_CONJUNCTS`: `10l.33` (the guard itself), `10l.32`
    (above), `10l.28`, `10l.21`, `10l.10` and `97w` mention one, and every mention either quotes
    the rationale or states the registry as a constraint on the row.

---

## 4. The four specific items

### Item 1 — `97w` and `10l.21` are NOT the same work, and the tracker already says so

**Refuted as stated, corrected as follows.** The dependency graph records
`adcp-client-python-97w blocks adcp-client-python-10l.21`. They are ordered, not duplicated. `97w`
owns §5's `properties` row — "two object declarations compose as an `allOf` of the two at that
property" — and `.21` owns the widened rows of §14 step 10.

**What IS true is that `.21`'s scope contains an item with an empty population.** `.21`'s first
scope line is "an uncomputable intersection", which is §5(b)'s *An `allOf` restatement that
neither matches nor narrows*, rung KEYWORD. Measured: of the 21 `_restatement` `None` returns over
the bundle, **18 fail on a subschema-valued keyword (`properties` 12, `items` 4, `allOf` 2) and 3
on an unresolvable `$ref` base. Zero fail on a scalar bound or a disjoint enum.** §5(b)'s row
therefore has no site in bundle 3.2 and `97w`'s row has all 13. `.21`'s own fourth instalment
reaches the same conclusion from the other side and offers it as option 2 — "Take these 13 off
§5(b) and give them to §5's `properties` row at CONJ" — and leaves the choice to the owner. The
measurement makes the choice: there is nothing else at that arm.

Recommend: strike "an uncomputable intersection" from `.21`'s scope and let `97w` carry G1 whole.
`97w`'s own population figure is stale — it says four documents measured at §14 step 9; it is 13
now, blocking 71.

**Other pairs with a coinciding population: one.** `10l.30` against `10l.21`'s third shape, which
is proposal 5 above and is worse than a duplicate — the two rows give opposite answers about the
same 10 declarations. No other pair of open rows shares a population.

### Item 2 — the two counts, settled

Both figures are correct over different populations, and the error is in pairing one numerator with
the other's denominator.

    primary refusals                                                  60
    primary refusals at the restatement arm                           13
    chained refusals whose quoted text contains the restatement
      sentence                                                        21
    13 + 21                                                           34
    refusals mentioning the restatement sentence, of 169              34

**"13 primary restatements plus 21 chained quoting them" is right.** `adcp-client-python-10l.21`'s
fourth instalment states exactly this: "13 refuse at the restatement arm itself and 21 chain to one
that does," and names all 13.

**"34 of 60 primary refusals are the restatement arm" is wrong**, and the mechanism that produced it
is in `emit`: a chained refusal's detail is built as `f"its target {wanted} is refused: {r}"`, which
embeds `str(target_refusal)` — so the target's whole sentence appears once in its own line and once
in every line that quotes it. A grep over details counts 34; the field `Refusal.kind` counts 13
primary. The denominator 60 came from the correct partition and the numerator 34 from the grep, and
the two were combined. The sentence that is safe to state is: **13 of 60 primary refusals are the
restatement arm, and 34 of 169 refusals mention it.**

This is the fifth instance of the defect `refusal.Kind`'s docstring records four of: the kind, or
the population, decided by reading English. The field exists to make that unnecessary and was not
consulted.

### Item 3 — the restatement detail misroutes, and it is the only detail that does

**Confirmed.** `compiler.py:2509-2517` emits one sentence for every `_restatement` `None` return:

> …`docs/plan/rebuild-plan.md` section 5(b) decides this row at rung KEYWORD — the field takes the
> base's declaration and the restatement's extra facts are dropped — and the facts it drops are
> nested ones the base states a WIDER value for, which section 8's approximated outcome has no
> direction for…

Thirty lines away, in the same function, `_restatement`'s `$ref` clause (`compiler.py:3240-3246`)
says the opposite about the same arm:

> It reports through the shared "neither matches nor narrows" arm and takes that arm's kind… what
> the document needs is §5's `properties` row… which is decided and unimplemented, and which the
> same arm refuses the subschema-valued restatements of `core/assets/*-asset.json` for.

The measurement in item 1 settles which is right: **all 21 sites are the `properties` row's and
none is §5(b)'s.** A reader of the refusal is sent to step 10 and to a row needing a rung and a §8
direction; the work is at step 9 and needs a recursion in `_at_least_as_tight` plus a per-key merge
in `_intersection`. That is how a row gets filed in the wrong step.

**Every other primary detail that cites a plan section was checked against what the code does.**
Nine citing shapes cover 47 of the 60 primary refusals, and the other eight are faithful:

| detail cites | sites | code does |
| --- | --- | --- |
| §5(b) rung KEYWORD + §8 approximated | 13 | **MISMATCH**: §5's `properties` row at CONJ/PROP. |
| §5's `$ref` row at CONJ (not a class) | 3 | faithful — `_the_conjuncts_own_type`, and §14 step 10 adopted it verbatim. |
| §5's `$ref` row at CONJ + §2's intersection | 2 | faithful — the node has one type and the intersection is over declarations. |
| §5's `$ref` row at CONJ + §5's `not` row + §2's rule placement | 2 | faithful — `ForbiddenGroups` is a class rule and the node is a `TypeRef`. |
| §5 CONJ one class per branch + §4's derived dispatch | 5 | faithful — `lower/union.discriminator` derives, never reads the declaration. |
| D2 / D6 / step 7's row (presence-only branch) | 5 | faithful — `_plan`'s presence arm. |
| step 7's rule, not a field (`required`) | 3 | faithful — `compiler.fields`. |
| D3 refuses rather than naming it after its siblings | 2 | faithful — `lower/names.derive`. |
| D5's alias module + the comparison's anyOf fold | 1 | faithful — `lower/containers.multi_type`. |

**Three stale measurements in refusal-adjacent comments**, none of which misroutes but each of
which will if it is read as current: `_restatement`'s docstring says "3 of the 1,054 portable
documents are refused by this predicate" (it is 13); `Module.declare`'s guard says "Measured 0
times over the whole population" (it is 1, `brand.json`); `lower/names.assign`'s guard says the
same (it is 1, `trusted-match/provider-registration.json`).

### Item 4 — the wave chain is seven serial steps on a void ordering

**Confirmed, and the plan says so in its own words.** `architecture.md` §14, after step 10:

> the wave ORDER has to be re-measured, not carried over: the waves were ordered by how many
> documents each keyword set *completes*, and after step 10 every document is complete, so the
> ordering quantity no longer exists. The new quantity is how many *approximated facts* a wave's
> keywords close.

`docs/plan/execution-plan.md` still carries the old table ("ordered by coverage, least-varied
schemas first… `if` beside them completes 185") and the tracker still carries the chain as six
`blocks` edges: `.9 → .10 → .11 → .12 → .13 → .14 → .15`.

**Measured under the quantity the plan prescribes** — approximated facts a wave's keywords close,
over the 1,054 portable documents at this tip:

| wave | keywords | approximated facts | primary refusals |
| --- | --- | --- | --- |
| 1 | `type enum pattern $ref allOf anyOf additionalProperties minLength` | 0 | 0 on these as the mechanism |
| 2 | `properties required const format maximum minimum maxLength oneOf discriminator enumMetadata` | **10** (all `oneOf`, all UNDERDETERMINED) | 2 (G3's union sites) |
| 3 | `items minItems uniqueItems not contains if then propertyNames minProperties maxProperties` | 0 | 0 |
| 4 | `dependencies exclusiveMinimum patternProperties` | **1** (`patternProperties`, WIDENED) | 0 |
| 5 | `exclusiveMaximum maxItems` | 0 | 0 |
| 6 | `else` | 0 | 0 |
| 7 | `errorMessage` | 0 | 0 |

**Two waves carry work and five carry none.** The two that do are independent of each other: the
`oneOf` separability question touches `lower/union.py` and `harness.inseparable_unions`; the
`patternProperties` rule family touches `lower/containers.py` and `_runtime.py`. They share no file
and no cell.

**The genuine edges among the keyword cells, named and grounded:**

* **`else` needs `if`.** `lower/rules._conditional` reads `if` first and returns when it is absent;
  `then` and `else` are then handled in one loop as `ConditionalRequired` and `NegatedConditional`.
  `then` and `else` are independent of each other. The edge is `if → {then, else}`, not
  `then → else`, so the plan's wave 3 → wave 6 ordering states one real edge and one invented one.
* **`discriminator` needs `oneOf`/`anyOf`.** `lower/union.py`'s header: "DISPATCH IS DERIVED FROM
  THE BRANCHES, NEVER DECLARED"; `discriminator.propertyName` is read at `union.py:348` only as a
  hint that the derivation then confirms. So `discriminator` has no cell of its own — it is
  `NOTHING` at every position — and it is not a wave item at all; it is a reader of the union
  lowering.
* **`patternProperties` interacts with `additionalProperties`.** The `additionalProperties` cell
  says "Beside `patternProperties` → refused, two value schemas" and the `patternProperties` cell
  says "Beside a non-`false` `additionalProperties` → refused". Both must change together, and
  `lower/containers._key` already owns the key rule for both spellings. This is a single edit
  across one function, not two waves.
* **No edge joins `maxItems`/`exclusiveMaximum`/`exclusiveMinimum`/`maxProperties`/`minProperties`
  to anything.** Each is a bound read by `rules_at` or by the scalar row independently.

**Proposed partial order.** Three units, two of which are concurrent and one of which is a cleanup:

    A. oneOf separability      (wave 2's oneOf)  -- owned by 10l.30, in conflict with 10l.21
    B. patternProperties rule  (wave 4)          -- unowned; §5(b) states the rung
    C. errorMessage cell flip  (wave 7)          -- one line in keywords.py

A and B are concurrent: disjoint files, disjoint cells, disjoint approximations. C is concurrent
with both and depends on nothing. Waves 1, 3, 5 and 6 have no unit. The six `blocks` edges in the
tracker express an order that no measurement supports and that costs six serial lanes.

---

## 5. Numbered requests against the two plan documents

These are requests, not edits. Neither `rebuild-plan.md` nor `architecture.md` was touched.

1. **`rebuild-plan.md` §5's generated grid contradicts §5(b) about `patternProperties`.** Lines 672
   and 673 say "Beside `patternProperties` → refused, two value schemas" and "Beside a non-`false`
   `additionalProperties` → refused". Line 745 of the same document decided on 2026-10-27 that this
   is a declared widening at rung CONTAINER, and the compiler already implements it — the one
   WIDENED approximation in the run is `core/creative-assets.json#` on `patternProperties`, whose
   document states exactly `patternProperties` beside `additionalProperties: true`. The grid is
   generated from `keywords.py`, whose cell prose is the stale half. **Without this, a reader of
   §5 files a row to make the shape refuse**, which is the misroute of item 3 in a second place.

2. **`rebuild-plan.md` §5(b)'s *An `allOf` restatement that neither matches nor narrows* row has an
   empty population and should say which shapes are not its own.** Measured: all 21 sites are
   subschema-valued or an unresolvable `$ref` base, which §5's `properties` row decides. Without a
   sentence dividing the two, the refusal detail keeps citing §5(b) and the work keeps being filed
   at step 10. **What breaks without it:** `97w` and `10l.21` keep converging on one population,
   which has already cost one duplicate filing.

3. **`architecture.md` §3's "a refusal's kind is derived from the cell and never chosen at a raise
   site" is not held, and the document should say what a refusal with no cell does.** All 16
   primary verdicts are hand-written. Six of them (G11, G12, G13, G15) report a compiler property
   as a document's, which §2 assigns to `BuildFailure`; three (G7a) are minted for work step 10
   schedules, which §9 names as the first mistake. **What breaks without it:** `accounted`
   (`emitted + verdicts`, 934 today) overstates by 30, and the next lane repeats the measurement.

4. ~~**`rebuild-plan.md` §8 needs a pairing rule for a CONJUNCT…**~~ **WITHDRAWN by the
   orchestrator, 2026-10-27: two thirds of this request are already in the file this audit read.**

   The request claimed §8 "states a pairing rule for a union BRANCH … and none for a conjunct or
   for a type LIST". Measured against the audit's own base blob
   `bff3554f0e729d4a71ec873ab50549f28e7bf57f`, which is byte-identical to trunk's, §8 carries
   **three** pairing rules:

   | line | rule |
   | --- | --- |
   | 1190 | a branch class of a root union, read under the root's siblings |
   | 1196 | the dual, for a node whose `type` is a LIST, read at its own type word (2026-10-26) |
   | 1216 | the third, for a node at a CONJUNCT of an `allOf`, read as the composition (2026-10-27) |

   So the conjunct half is written and `97w` is not waiting on a sentence — `10l.21`'s fifth
   instalment is implementing against rule three right now. `zyn`'s type-list half is rule two.
   The audit read a stale recollection of §8 rather than §8.

   **What survives.** `6zg` is a different shape from either: a class that IS the union of its
   branches, rather than a branch OF one, and no rule covers it. The row says so in its own title
   — "the §8 pairing sentence it needs". That one sentence is still owed, and it is the
   orchestrator's to write.

   Recorded rather than deleted, because the audit's job was to catch exactly this class of drift
   and it produced an instance of it. A report that re-derives every figure and then cites a
   document from memory has one leg measured and one leg not.

5. **`architecture.md` §14's note that the wave order is void should be carried into
   `docs/plan/execution-plan.md`, whose table still states the void order as fact.** That file is
   not one of the two authorities and can be edited directly; it is listed here because the two
   documents currently disagree in public. **What breaks without it:** a lane reading the execution
   plan takes seven serial waves; §14 says the quantity that ordered them no longer exists.

---

## Appendix: how each figure was produced

* `emitted / refused / deferred / verdict`, the approximations, the refusal lines:
  `python -m codegen --bundle schemas/cache/3.2 --tree /tmp/audit-tree $(cat /tmp/portable.txt)`,
  with `PYTHONPATH=.:src` and `.venv/bin/python`.
* primary versus chained: `Refusal.kind` read off `Emitted.refusals`, by re-running `emit.emit`
  in process. The sentence test `detail.startswith("its target ")` reproduces it exactly.
* the production site of every refusal: `Refusal.__init__` wrapped to capture a stack summary
  filtered to `codegen/`, keyed by `(keyword, pointer, detail)`.
* the `_restatement` clause census: `compiler._restatement` wrapped to re-derive, on a `None`
  return, whether the `"$ref" in b` clause fired and which shared keywords fail
  `_at_least_as_tight`.
* cascades: `bundle.edges(Path("schemas/cache/3.2"))`, reversed into a referrer map, transitively
  closed from each group's documents and intersected with the refused set.
* keyword usage: a recursive scan of every portable document counting key occurrences and
  documents, beside `keywords.cell(keyword, position).effect` at all nine positions.
