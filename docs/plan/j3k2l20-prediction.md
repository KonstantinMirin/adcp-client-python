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

Filled in after the measurement, against the table above.
