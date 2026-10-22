# `definitions` and `$defs` as declarations in their own module — the prediction

`salesagent-j3k2l.20`. Committed before any line of the change exists, so the grading
below is against a record and not against a recollection.

Branch `sdk/j3k2l20-defs-declarations`, worktree `/Users/konst/projects/acp-j3k2l20`,
off `emit/from-scratch` at **`63dc1bb68c181d5bbc233a44f42dcecb0f9efab7`** with a clean
tree. Every number here is predicted against that sha, measured on
`schemas/cache/3.2` with `bundled/` and `mcp/` excluded (1,054 portable documents).

Three sibling lanes are in flight off the same sha (`.24` a branch-type bug, `.16`
`const`, `.21` root type lists). Nothing below is measured on their trees.

## The baseline at `63dc1bb68`

`emit.emit` over all 1,054 portable documents, in process:

| fact | value |
|---|---|
| portable documents | 1,054 |
| emitted | **401** |
| refused | **653** |
| refusals on `definitions` | **35** |
| refusals on `$defs` | **5** |
| … all 40 at pointer `/`, on "this step lowers no such keyword (a later D2 row does)" | 40 of 40 |
| graded pairs in the committed tree | 462 (450 `pass`, 12 `no_constraint_to_step`) |
| `added` / `missing` / `differs` | 0 / 0 / 0 |

The next six refusal keywords, for scale: `$ref` 228 (219 of them a chain — "its
target … is refused"), `const` 75, `allOf` 66, `if` 66, `uniqueItems` 48, `type` 35.

### The population, characterised

| fact | value |
|---|---|
| documents declaring `definitions`/`$defs` at the ROOT | 45 |
| … refused ON that keyword (**the 40**) | 40 |
| … refused on something else already (`allOf` 3, `type` 2) | 5 |
| documents carrying the keyword at ANY schema position | 46 |
| … so sections at a non-root position | **1** (`brand/get-brand-identity-response.json#/oneOf/0/properties/fonts`) |
| documents declaring BOTH `definitions` and `$defs` | 0 |
| entries across the 40 | **157** |
| … named by a LOCAL `#/…` reference in their own document | **146** |
| … named only by an ABSOLUTE fragment reference from elsewhere | 0 |
| … named by **nothing** | **11** |
| local `$ref` sites in the whole bundle | 405 |
| … whose pointer is `/definitions/<k>` or `/$defs/<k>` | 402 |
| … pointing into the one nested section | 3 |
| … naming the document ROOT, or a node that is not an entry | 0 |
| distinct entry keys in the bundle | 163, of which `class_name` cannot spell **0** |
| forward references among entries (referrer declared before its target) | **20**, in 4 documents |
| documents with a reference CYCLE among their entries | **0** |
| documents reaching one of the 40 through a `$ref` closure | 94, all 94 refused today, 31 of them as a chain |

## The form: this is the WALK, not a dispatch row — and the measurement says so

The bead says "THIS IS ONE DISPATCH ROW". **Measured, it cannot be one**, and the
figure is the refutation: of the 40 documents, `composes_at_the_root` claims **16**,
`is_object_root` claims **15** and `union_root` claims **9**. A `definitions` section
is not a root KIND — it sits beside whatever kind the root already is, and a root is
exactly one kind, which is the property `emit.ROWS` is a partition by.

A row claiming all 40 would therefore have to lower three root kinds itself, and it
could not delegate to the table instead: a lowering imports `codegen.compiler` and
`codegen.refusal` and nothing else under `codegen` (D13, graded by
`tests/test_import_rule.py`), so it cannot reach `emit.ROWS`. Adding the keyword to
`bundle.declares_its_own_root_kind` does not rescue the row either: that function is
read by `is_object_root`, `is_scalar_root` and `is_container_root` and by no other
selector, so `composes_at_the_root` and `union_root` would keep claiming 25 of the 40
and `emit.lower_document` would raise `AmbiguousRoot` on every one of them.

So **no row and no selector is added, and `ROWS` is unchanged.** What a `$ref` names is
a NODE, and the emitter already has the one mechanism for that: `bundle.named_nodes`
asks for a symbol, `emit.decide_type` gives the node one, and `Module.declared` maps
pointer → symbol so a reference finds it. All three exist for the ABSOLUTE fragment
reference; a local reference is the same question with an empty document half, which
is what `bundle.split_ref` already hands back and what this change branches on.

Four edits, each named with what it is for:

1. **`bundle.named_nodes`** also records a LOCAL reference's pointer against the
   REFERRING document. It skips one today (`if not head or not pointer: continue`).
   This keeps it a function of the bundle: a document's own references are part of
   the bundle, not of the run's document set.
2. **`compiler.DEFINITION_SECTIONS`**, admitted by `check_keywords` beside
   `ANNOTATIONS`. One place for all 13 screens, because the section asserts nothing
   about an instance in any draft the bundle declares — what it HOLDS is reached by
   reference, and the reference is what declares it.
3. **`compiler.local_symbol`**, the sibling of `name_the_node`: the symbol for a node
   of THIS document that a local reference names, declared on first ask through
   `mod.decide` and memoised in `Module.declared`. On demand rather than eagerly,
   which is what makes the 20 forward references a non-event — the same memo-plus-
   inflight shape `emit.emit`'s cross-document `lower` already uses, so a cycle
   refuses by name instead of recurring.
4. **`emit.decide_type`'s `$ref` arm** branches on the empty document half and calls
   (3); `lower_document` carries the named nodes' subschemas on the `Module`, keyed by
   the pointer `bundle.nodes` yields, so there is no second pointer navigator and no
   second escaping rule. The local-reference refusal moves OUT of `emit.emit`'s
   `bind`, which is the cross-document binder and never sees one again.

The name is D3's nested rule with the document root as the parent: root symbol +
`class_name(the entry's own key)`. Measured spellable for all 163 of the bundle's
entry keys; a key that derives no identifier refuses, and two entries deriving one
name is `Module.declare`'s existing build failure.

Every declared node names **its own** pointer in `__adcp_schema__` — `declare_object`
already writes `schema_ref(mod.document, pointer)` and nothing here changes it. Checked
that the pointer lands: `bundle.resolved` KEEPS the section and every entry in it
(probed on `core/placement-presentation.json`, `aao/agent-publishers.json`,
`content-standards/artifact.json`), so `schema_at(SchemaRef(doc, "#/definitions/x"))`
resolves in the written package and `graded()` picks the class up by its own
`__adcp_schema__`.

## The deliberate decision: an entry nothing references is SKIPPED

**Decided: skipped. 11 of the 157 entries (7.0%), all 11 in one document,
`a2ui/si-catalog.json`.**

Why:

- `definitions` and `$defs` have **no validation effect**. An entry nothing references
  cannot change what the document accepts or what it refuses, so skipping it cannot
  make a model wider than its schema — which is the one defect a refusal exists to
  prevent (P3). The emitted class would be narrower or wider than nothing at all.
- Declaring it emits a class that no field names, nothing imports, `__all__` does not
  export and no reference resolves to. Its only observable effect is the wrong one: a
  keyword inside a DEAD section would refuse the whole document. `a2ui/si-catalog.json`
  is exactly that case — 11 dead entries against a root declaring 2 properties, whose
  24 `$ref`s all sit inside the dead section, so declaring them would also drag
  `a2ui/bound-value.json`'s whole closure into a module no instance reaches.
- "Every node gets a name" is not a rule this emitter holds anywhere. It does not name
  a node under `not`, an `examples` payload, or a `propertyNames` schema. The rule it
  does hold is "every node a reference NAMES gets a symbol", and `bundle.named_nodes`
  is that rule — this change widens it to local references and stops there.
- Skipping is also what makes the lazy declaration in (3) correct rather than a
  convenience: the entries that are declared are exactly the ones something asked for.

The decision is REVERSIBLE in one place — an eager pass over the section in
`lower_document` — and the cost of reversing it is the 20 forward references needing a
topological order, which the lazy form does not.

## Predictions

Graded in the same file after the measurement. Point estimates, with a range where I
do not expect to be close.

| # | prediction | value |
|---|---|---|
| P1 | of the 40, documents that no longer refuse on `definitions`/`$defs` | **40 of 40** |
| P2 | of the 40, documents that EMIT | **16** (range 10–24) |
| P3 | of the 40, documents still refused, on a non-deferral keyword | **24** (range 16–30) |
| P4 | the 6 that state a keyword outside EVERY handled set still refuse | **6 of 6** — `contains` ×5, `patternProperties` ×1 |
| P5 | documents unblocked by the `$ref` CHAIN (not themselves of the 40) | **7** (range 2–14) |
| P6 | N (emitted over 1,054) | **424** (range 415–445) |
| P7 | refused over 1,054 | **630** (range 609–639) |
| P8 | emitted + refused | **1,054**, exactly |
| P9 | graded pairs in the regenerated tree | **557** (range 520–610) |
| P10 | `added` facts | **0** |
| P11 | `missing` facts | **0** |
| P12 | `differs` facts | **0** |
| P13 | `a2ui/si-catalog.json` emits, with **0** classes from its `definitions` | yes |
| P14 | `brand/get-brand-identity-response.json`'s nested section resolves through the same path | yes |
| P15 | documents whose refusal keyword becomes `definitions`/`$defs` anywhere in the bundle | **0** |
| P16 | `emit.ROWS` length | **6**, unchanged |

**Why P2's range is wide.** The sharp instrument is not available without the change:
34 of the 40 state no keyword outside the UNION of every handled set, but that union is
not the screen — `check_keywords` is applied per POSITION, and `const`, `if`/`then`/
`else`, `not`, `uniqueItems` and a nested `allOf` are each handled at exactly one
position and refuse at every other. Those five are the five largest non-`$ref` blockers
in the base census (75 / 66 / 66 / 48 / 23 of 653). So 34 is a ceiling that the
position screen will cut into, and I do not know by how much. 16 is the midpoint of a
guess, named as one.

**What would make me wrong in the dangerous direction.** A non-zero `added`, `missing`
or `differs` (P10–P12). Those three are the only checks that grade the generated code,
and a definitions entry declared as a class is graded against a pointer no pair has
ever named before, so this change is the first thing to put that path under load.

## The grading

Measured on branch `sdk/j3k2l20-defs-declarations`, `emit.emit` over all 1,054 portable
documents, against a re-measurement of `63dc1bb68` in a pristine worktree
(`/Users/konst/projects/acp-j3k2l20-base`) in the same process-per-tree instrument
(`snap.py`, which inserts the tree it is told to measure at `sys.path[0]` and asserts
`codegen.emit.__file__` came from it).

| # | predicted | measured | verdict |
|---|---|---|---|
| P1 | 40 of 40 off the section keyword | **40 of 40** | right |
| P2 | 16 emit (10–24) | **0** | **WRONG, and outside the range** |
| P3 | 24 still refused (16–30) | **40** | **WRONG, and outside the range** |
| P4 | the 6 with a keyword outside every handled set still refuse, on `contains`/`patternProperties` | all 6 refuse; **0 of them on either keyword** | outcome right, mechanism wrong |
| P5 | 7 unblocked by the `$ref` chain (2–14) | **0** | **WRONG** |
| P6 | N = 424 (415–445) | **401**, unchanged | **WRONG, and outside the range** |
| P7 | refused = 630 (609–639) | **653**, unchanged | **WRONG, and outside the range** |
| P8 | emitted + refused = 1,054 | **1,054** | right |
| P9 | 557 graded pairs (520–610) | **462**, unchanged | **WRONG, and outside the range** |
| P10 | `added` = 0 | **0** | right |
| P11 | `missing` = 0 | **0** | right |
| P12 | `differs` = 0 | **0** | right |
| P13 | `a2ui/si-catalog.json` emits, 0 classes from its section | does **not** emit — `const` at `/properties/catalogId`; 0 classes from its section | half wrong |
| P14 | the nested section resolves through the same path | `brand/get-brand-identity-response.json` still refuses on `allOf` at `/`, so the real bundle never reaches it; its pointer IS in `named_nodes` and the path is graded on a constructed bundle | not demonstrated on the bundle |
| P15 | 0 refusals on a section keyword | **0** | right |
| P16 | `ROWS` length 6 | **6** | right |

**Five of sixteen are wrong and four of those are outside their stated range, all in one
direction: nothing emits.** The one prediction that mattered — that this step moves N —
was wrong, and the reason is a single thing the 34-of-40 instrument could not see.

### Why P2 was wrong, and what the right instrument would have been

The predictor unioned EVERY row's handled set and asked which documents state a keyword
outside the union. That admits a keyword handled at exactly one position everywhere, and
the five largest non-`$ref` blockers are all of that kind. The prediction said so and
then used 34 as a ceiling anyway, with a midpoint guess inside it. The position screen
did not cut into that ceiling by a fraction: it cut all of it.

The keywords the 40 land on, measured:

| keyword | documents | owner |
|---|---|---|
| `if` | 10 | D6's rule at an `allOf` conjunct — step 4/7's boundary |
| `const` | 7 | D2's `Literal` row — `salesagent-j3k2l.16`, in flight |
| `$ref` | 4 | a chain, or a bare-`$ref` union branch |
| `anyOf` | 3 | step 5's row at a nested position |
| `properties` | 3 | a root conjunct beside a union (step 5's own refusal) |
| `type` | 2 | real: a declared `null` beside another type, and `properties` with no `type` |
| `discriminator` | 2 | step 5's row at a nested position |
| `allOf` | 2 | step 4's row at a nested position |
| `else` | 2 | D6, as `if` |
| `not` | 2 | D6 |
| `minProperties` | 1 | D6 |
| `uniqueItems` | 1 | D6 |
| `maxProperties` | 1 | D6 |

Not one of the 40 is held by a keyword with no scheduled row, which is the exit
condition; and not one is held ONLY by the section, which is why N does not move. **This
step cannot raise N on its own**, and the sharp instrument for that was available before
the change: for each of the 40, walk the document the way the rows walk it and take the
first keyword each position's own screen refuses. I substituted a cheap union for it and
reported a range I had no instrument for.

`salesagent-j3k2l.16` (`const`) alone would clear 7 of the 40 once both land, and D6 at a
conjunct position would clear 14 more.

### What the change did move, none of it predicted

- **The refusal attribution, for all 40.** `(keyword, pointer)` moved for exactly 40
  documents and for 0 outside them, with no document emitted-to-refused in either
  direction. The keyword census moves by −35 `definitions`, −5 `$defs` and +40
  distributed across 13 keywords.
- **7 documents now refuse at a pointer INSIDE a section**, where 0 could before — every
  pointer under `definitions` was unreachable. That is the descent made observable, and
  it is what `test_the_bundles_own_sections_are_walked_and_the_closure_follows` grades.
- **The closure reaches further where a root refusal moved into the properties.**
  `governance/policy-entry.json` stopped at `$defs` at `/` before any of its 8 property
  references was read; it now refuses at `/properties/acceptance_profile`, so the three
  enum documents its earlier properties name are emitted. Over step 1, 2 and 4's own
  587-document population that is **214 → 217**, and the with/without-row delta for
  `composes_at_the_root` is **31 → 34** (both referrers of `policy-entry` in that
  population are selected by that row and by no other, so removing it removes the only
  path). Over the whole 1,054 it is +0, because there all three are named directly.
- **One document outside the 40 changed its refusal DETAIL and nothing else**:
  `core/registry-feed-response.json`, whose chain quotes `core/registry-event.json`'s new
  message. `(keyword, pointer)` is unchanged.
- **The committed tree is byte-identical.** `test_the_committed_tree_is_what_a_fresh_run_emits`
  passes untouched, so no module was regenerated and the 462 graded pairs, 450 `pass`,
  4,658 compared facts and 0/0/0 added-missing-differs are all unchanged. Which also
  means **no declared section entry reaches the committed tree**, so the positive path —
  the class, its own pointer, the symbol the property names, the entry nothing references
  — is graded on constructed bundles in `tests/test_fragment_ref.py` and nowhere else.
  That is the same arrangement `salesagent-j3k2l.14` records for the absolute half and
  for the same reason: the population is gated behind other steps.
- **4 of the bundle's 405 local reference sites name an entry that is ITSELF a `$ref`**
  (`brand.json#/definitions/logo_slot`, `core/registry-event.json#/$defs/badgeRole`, each
  named twice). That arm was found while writing `local_reference` and it decided the
  signature: the function returns the `Decided` rather than reading `Module.declared`
  back, because such an entry decides to a symbol the module IMPORTED and nothing
  declared it at that pointer. Reading the memo back would have been a `KeyError` on 2
  real documents.

### What was dropped from the design as unreachable

An identifier check on the derived name. `class_name` returns alphanumerics only and
`emit.lower_document` refuses a title deriving no identifier before any row runs, so an
identifier root concatenated with it is always an identifier. What can go wrong is a
COLLISION, which `Module.declare` already fails the build for — graded on `a_b` against
`a.b`, which both derive `CollideAB`.

### The checks, each probed by making it fail

| check | removed | observed |
|---|---|---|
| `Module.resolving` (the cycle guard) | branch disabled | `RecursionError: maximum recursion depth exceeded`, both the two-hop and the self-reference case |
| `local_reference`'s "names no node" | branch disabled | `TypeError: argument of type 'NoneType' is not a container`, one frame out in `_decide` |
| `DEFINITION_SECTIONS` in `check_keywords` | removed from the screen | 3 tests red, including the whole-population "0 refusals on a section" |
| `named_nodes`' local arm | `continue` restored | the constructed bundle refuses with `#/definitions/slot names no node of this document` |
