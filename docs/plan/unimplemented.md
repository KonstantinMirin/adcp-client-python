# What the two plan documents state, and what is in the artifact

`docs/plan/rebuild-plan.md` and `docs/plan/architecture.md` state several hundred goals between
them. This document walks both, plus `docs/plan/execution-plan.md`, and partitions every one on a
single axis:

**OBSERVABLE IN THE ARTIFACT** — a consumer who has only `src/adcp` and the bundle can tell
whether it holds. These are correctness goals, and each gets a derived status: *achieved*,
*achieved by a recorded exception*, or *NOT ACHIEVED*, with the derivation beside it.

**INTERNAL ONLY** — no consumer can tell. "`compiler.py` is dissolved", "the lowering seam has one
inhabitant", "no keyword set literal lives outside `keywords.py`" are of this kind. They get one
line saying so and **no verdict**, deliberately: there are unboundedly many wrong internal shapes,
so enumerating a few proves nothing, gating them encodes the shape of the code as a test, and the
gate then blocks the refactor it was meant to encourage while establishing no correctness. An
internal goal is a maintainability preference and is done when it pays for itself.

The axis is not a softening. Every *correctness* claim either document makes is in Part A with a
number against it.

---

## How every figure in Part A was derived

**The subject is the tree a fresh run emits, not the committed one**, which is
`architecture.md` §5's own rule of 2026-10-29 ("the tree is an ARTIFACT and not a phase"). The
committed tree disagrees with a fresh run at 74 of 1,054 modules (item **A-1**), so a census over
`src/` would have graded a mixture of two compilers.

```
cd /srv/ws/wt-ratchet
PYTHONPATH=.:src .venv/bin/python -c "import pathlib;from codegen import bundle;\
print('\n'.join(sorted(bundle.portable(pathlib.Path('schemas/cache/3.2')))))" > /tmp/portable.txt
PYTHONPATH=.:src .venv/bin/python -m codegen --bundle schemas/cache/3.2 \
    --tree /tmp/fresh-tree --package /tmp/fresh-pkg $(cat /tmp/portable.txt | tr '\n' ' ')
```

That run's own report, and the baseline this document's row did not move:

```
emitted 1054 / refused 0 (); accounted 1054; 1054 named
approximated 120 facts in 53 documents (WIDENED 81, UNDERDETERMINED 39; ours 120, upstream 0)
./check  ->  emitted 1054 / refused 0 (deferred 0, verdict 0); accounted 1054
             kind: verdict 0, deferred 0, chained 0  ->  primary 0, chained 0
             approximated 120 facts in 53 documents
```

Fresh tree: 1,084 `.py` files — 1,053 document modules plus `brand/__init__.py` (one namespace,
item **A-9**) plus 30 package markers — carrying **3,449 module-level classes**. Every figure
below is an AST walk over those files, or a `bundle.record` lookup, and is reproducible from the
command above. Where a figure needs the grader rather than the artifact's text, it says so and
names the gate instead of asserting a number this row did not re-run.

---

## Part A — observable in the artifact

### A.1 NOT ACHIEVED, in the order a consumer meets them

| # | the goal, and where it is stated | derived status | size | RELOCATION or DECISION | the gate |
| --- | --- | --- | --- | --- | --- |
| **A-1** | `architecture.md` §5 (2026-10-29): the committed tree's population is `bundle.portable`, because the tree is an artifact | **NOT ACHIEVED.** 39 of 1,054 portable documents have no module in `src/`; 35 of the 1,015 shared modules differ byte for byte. 74 modules in all | 74 files | RELOCATION — regenerate and commit | EXISTS: `tests/test_emit.py::test_the_committed_tree_is_what_a_fresh_run_emits`, `tests/test_fragment_ref.py::test_the_committed_tree_is_the_fresh_emission_of_the_derived_population` |
| **A-2** | `rebuild-plan.md` §1: "re-exported from `adcp.types.<domain>`, where the domain is derived from the document's own path" | **NOT ACHIEVED.** 0 domain modules exist. `src/adcp/types/` holds `_base`, `_runtime`, `constraints`, `envelopes`, `_schemas/`. 22 domains are present under `_schemas/`, so every consumer import today is the private `adcp.types._schemas.<path>` | 22 modules over 1,054 documents | **BOTH** — the domain is derived from the path (relocation); *what each module exports* is undecided (A-3) | NONE. A named one: every class the tree declares resolves at exactly one `adcp.types.<domain>.<Name>` |
| **A-3** | `rebuild-plan.md` §1: "There is **one import path per class**, and never a second way to reach the same class. … The one path is the domain surface's" — the export half | **NOT ACHIEVED, and it is the decision A-2 is blocked on.** `__all__` is `emit.exported`, derived and correct for the question it answers ("the names another module can ask for": the root, every `$ref`-named pointer, a composed base's field types). It is not a consumer surface. **486 of 1,084 modules declare 2,283 of the tree's 3,449 classes that their own `__all__` omits** — `core/requirements/asset_requirements.py` names `AssetRequirements` and none of its twelve branches | 2,283 classes in 486 modules | **DECISION.** Neither document states what the domain surface exports. Re-exporting `__all__` leaves 2,283 classes unreachable publicly; re-exporting every declaration contradicts nothing but has never been said | NONE until the sentence exists |
| **A-4** | `rebuild-plan.md` §1: "one import path per class" — the collision half | **NOT ACHIEVED.** 4 modules bind 56 names to two classes each: `adagents.py` (16), `core/async_response_data.py` (19), `core/package_format_snapshot.py` (16), `core/vendor_pricing_option.py` (5). Each module *imports* the name and then declares a subclass under it, so after the module body the name means the subclass and a consumer importing it from the two modules gets two classes with different `__adcp_schema__` pointers. Python does not object: the base is evaluated before the name is bound | 4 modules, 56 names. `lower/names.py`'s `occupied` does not treat an imported symbol as occupied | RELOCATION | EXISTS **and is RED**: `tests/test_names_collision.py::test_no_module_of_the_tree_declares_a_name_it_imports`. Bead `adcp-client-python-10l.111` (it reports 5 names, over the committed tree; a fresh run is 56) |
| **A-5** | `rebuild-plan.md` §4 Names (2026-10-29): "A bare `$ref` branch is named for its TARGET, and the index is the rung after that" | **NOT ACHIEVED.** 18 classes named `…Branch<N>` over 7 documents on a fresh run. **15 of the 18 carry the target's own class name in their own base list**, so the name the rule asks for is already in the module: the twelve `AssetRequirementsBranch0..11` sit on `ImageAssetRequirements`, `VideoAssetRequirements`, …, `WebhookAssetRequirements`, plus `GetContentStandardsResponseBranch0`, `GetCreativeFeaturesResponseBranch0`, `PostalAreaBranch9`. The other 3 are not bare-`$ref` branches | 18 classes, 7 documents, 1 rule in `lower/names.py` | RELOCATION, with the rename census §4 itself asks for before it lands | NONE. A named one: no `…Branch<N>` survives where the branch's base list names a target class |
| **A-6** | `rebuild-plan.md` §4 Names (2026-10-29, bead `.93`): "A boolean pin contributes no segment, because `true` names nothing" | **NOT ACHIEVED.** `core/package_signal_targeting.py` declares `PackageSignalTargetingBinaryTrue`; the rule gives `PackageSignalTargetingBinary` | 1 rule; 3 branches pin something identifying beside a `true` | RELOCATION | NONE for this clause. `tests/test_names_collision.py::test_rung_two_reads_every_pin_the_branch_states_in_the_documents_key_order` is green and does not reach it |
| **A-7** | `rebuild-plan.md` §4 Names (2026-10-28): "The `definitions` entry dropped its `<Root>` prefix … the module carries the document" | **NOT ACHIEVED.** `core/verification_token_claims.py` declares `AgenticAdvertisingOrgVerificationTokenClaimsVerificationTokenGradingProfile` — 75 characters, the document's own worked example of the old rule. Tree-wide: 479 of 3,449 class names exceed 30 characters, the longest 85 (`AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPublisherProperties`) | 1 naming rung | RELOCATION | `tests/test_names_collision.py::test_the_long_name_is_the_exception_and_not_the_rule` exists and is green, so it does not reach this |
| **A-8** | `rebuild-plan.md` §4 (2026-10-29): "For `oneOf` it is false, and an inseparable `oneOf` owes TWO declarations" — the dropped exclusivity is a WIDENED fact declared **beside** the UNDERDETERMINED one | **NOT ACHIEVED.** All 18 `oneOf` facts the fresh tree declares carry `kind='UNDERDETERMINED'` alone. `core/evaluator-spec.json#/oneOf` — the document's own measured case — writes exactly one `Approximation` | 18 sites over 16 documents, 1 handler arm | RELOCATION | NONE. A named one: every inseparable `oneOf` pointer carries both kinds; its mirror is `tests/test_the_declared_backlog.py` |
| **A-9** | `architecture.md` §2 (2026-10-29): "The approximation takes the `SchemaRef` spelling, because that is the one the reader of a declaration uses" | **PARTIALLY ACHIEVED.** Of 178 `Approximation(...)` instances in the fresh tree, **38 have a pointer a strict segment-walk of their own document of record cannot reach** — the `patternProperties` family under `creative_manifest`, and `adagents.json#/oneOf/1/anyOf`. The decision measured 144 of 235 with a resolver that followed `$ref` and merged `allOf`, so this strict figure is an upper bound and the artifact-census row should re-measure the same way | 38 of 178 instances | RELOCATION | `tests/test_the_declared_backlog.py::test_the_committed_trees_declarations_are_the_runs` is the nearest; the two-direction equality of `rebuild-plan.md` §8 is the real one |
| **A-10** | `rebuild-plan.md` §6 and §7: `errorMessage` and the registry data keys move into §6's projection | **NOT ACHIEVED, and both documents say so of themselves** ("The grid below is generated and does not yet carry their rows"; "The grid above is generated and still carries both rows"). §7's generated region still lists `errorMessage` where the section's title is "the set is empty" | 2 cells and `pytest tests/test_keywords.py --write-grids` | RELOCATION | EXISTS: `tests/test_keywords.py` holds the grid equality in both directions; it is green because the cells and the grids agree *with each other* on the stale answer |
| **A-11** | `architecture.md` §14, after the waves: "these keywords' OURS approximations reach 0" | **NOT ACHIEVED — this is the open work, not a defect.** ours 120, upstream 0. By attribution: `§5 objects/patternProperties` 122 instances, `§5 combinators/anyOf` 29, `§5 combinators/oneOf` 24, `§5 strings/maxLength` 3 | 120 facts in 53 documents | DECISION per keyword family, then RELOCATION | EXISTS: the report's own figure, printed by `./check` |

### A.2 Achieved, with the derivation

| the goal | derivation |
| --- | --- |
| `rebuild-plan.md` §1: "A set of Pydantic classes, one per schema node that needs one" | 1,054 of 1,054 portable documents emit; 3,449 module-level classes; `refused 0` |
| §1: "Every portable document of the bundle contributes a symbol" | 0 of 1,084 modules has an empty `__all__`; 0 has none where one is owed |
| §1: "Generated modules are private" | the tree is `adcp/types/_schemas/`, a leading-underscore package |
| §1: "a document compiles to a module at its own path" | every one of the 1,054 documents resolves to `emit.module_file(document, bundle.package_roots)` in the fresh tree, no module is unclaimed |
| §1: "A second name bound to a class by identity … `X is Y` holds" | 60 module-level `X = Y` bindings in 32 modules — the carve-out, not A-4's collision (A-4 is a *subclass* under an imported name) |
| `architecture.md` §10 (2026-10-29): a document whose path is also a directory's is that package's root | `brand.json` is the one such pair; `brand/__init__.py` carries 1,599 lines and `brand.py` does not exist. The rejected alternative — an unimportable `brand.py` beside a 0-byte package — is absent |
| `architecture.md` §8: `AdCPRootModel` joins `AdCPBaseModel`, both taking `strict_validate` and `__adcp_schema__` from one mixin | `src/adcp/types/_base.py`: `class AdCPBaseModel(SchemaBound)` and `class AdCPRootModel(SchemaBound, RootModel[Any])` |
| §2: "Constraints bind to the type, not the field"; "Every constrained scalar is named"; an alias names a constraint and never a concept | `adcp/types/constraints.py`, 212 generated declarations, each named from the constraint alone; the two names that are decisions rather than derivations — `AdCPUrl` and the re-exported `HttpUrl` — carry their measurement (47 of the bundle's 300 `uri` positions restrict the scheme; `AdCPUrl` everywhere was tried and withdrawn at 228 of 300) in the module docstring |
| §2 / `architecture.md` §7: an approximation is a DECLARATION written into the emitted module | 178 `Approximation(...)` instances → 120 distinct `(document, pointer, keyword)` facts in 53 documents, as `__adcp_approximations__` class attributes. Not in `json_schema_extra`, which §7 forbids |
| §2: two kinds, never summed; ours and upstream, never summed | WIDENED 81 / UNDERDETERMINED 39 (sum 120, reported separately); ours 120 / upstream 0; the report prints three figures over three denominators and adds none |
| §2: a narrowing taken on purpose is admitted by an enumerated registry and by nothing else | one entry, `harness.URL_IMPLIED`, graded by `tests/test_decision_set.py` with both sides derived |
| §4 Names: root is `pascal_case(title)`, else the file stem | median class name 17 characters; 18 of 3,449 names end in a digit (A-5's indexed branches and their nested enums) |
| §4 Names (2026-10-29): rung 2 reads **every** pin in the document's key order | `core/postal_country_system.py` declares `…FRCodePostal`, `…AUPostcode`, `…BRCep`, `…INPin`, `…ZAPostalCode` for the five two-pin branches and keeps `…US`, `…GB`, `…CA`, `…Plz` for the four single-pin ones |
| §4 Names (2026-10-29): a rung that collides has not identified the branch, so **both** fall | `trusted_match/provider_registration.py` declares `TMPProviderRegistrationContextMatch` and `…IdentityMatch` off rung 3's `required` set, not rung 2's shared `true` |
| §4 Names (2026-10-29): a branch colliding with its own root — the root keeps the name | `core/postal_area.py` declares the root as `PostalArea`; the branch moved. The hand-minted verdict that wrote off this document and the 31 chained behind it is gone: `refused 0` |
| §4 Names (2026-10-28): where N positions collide, **all N** lengthen, so the name is order-independent | `tests/test_names_collision.py::test_all_n_colliders_lengthen_and_a_name_is_not_a_function_of_the_order` and `::test_inserting_a_branch_after_an_indexed_one_moves_no_existing_name`, both green |
| §4: a union root is a base plus one class per branch; a `$ref` branch is a class with two bases; the four mixin mechanics; a value serialises as what it is | `tests/test_emit.py::test_a_union_root_emits_a_base_plus_one_subclass_per_branch`, `::test_a_payload_resolves_to_its_branch_on_all_four_paths`, `::test_a_consumers_subclass_of_a_union_base_keeps_its_own_schema`, `::test_a_union_base_instance_and_a_branch_each_serialise_as_what_they_are` |
| §4: which branch a payload is, derived from bundle data and never from a hand-written map | no per-document map exists; the inseparable residue is declared, 39 UNDERDETERMINED facts |
| §1 / §3: the bundle directory is an argument and nothing reads a hard-coded path | `python -m codegen` requires `--bundle`; no version literal in the package |
| §3 / §5: the grids of §5, §6 and §7 are generated between markers | `<!-- generated from codegen/keywords.py -->` … `<!-- end generated -->` regions present in `rebuild-plan.md`; `tests/test_keywords.py` holds the equality both ways and `--write-grids` writes it |
| `architecture.md` §2 (2026-10-29): a base list naming one class twice RAISES, at `ir.ClassDecl` | `tests/test_the_tree_imports.py::test_a_base_list_naming_one_class_twice_raises` green. Its companion `::test_no_document_of_the_bundle_reaches_the_duplicate_base_guard` **fails**, and the failure is `tests/nodeset.py`'s refusal to let an empty population pass vacuously — not a document reaching the guard. That is the helper working as designed; the test needs a non-vacuous spelling |
| `architecture.md` §2 (2026-10-29): a check may not be downstream of its own precondition | the import obligation moved out of `test_emit.py` and off the committed population: `tests/test_the_tree_imports.py::test_every_module_a_fresh_run_emits_imports_and_every_class_of_it_is_defined`, green |

### A.3 Observable but not re-derived in this row

`rebuild-plan.md` §8's three checks and the four defect counts pinned at zero — *missing*,
*differs*, *added*, *over-declared* — range over 1,054 pairs and need the grader, not an AST walk.
This row did not run them and does not assert their values. The gates are
`tests/test_emit.py::test_every_class_passes_all_three_checks`,
`::test_the_schema_comparison_sees_a_fact_the_model_adds_as_well`,
`tests/test_every_check_names_its_set.py` (the compared-set equality) and
`tests/test_the_declared_backlog.py` (the declared-set equality). **The full suite does not
complete today** (`adcp-client-python-10l.96`) and `tests/test_type_checker.py` is RED with 6
mypy errors in `compiler.py` / `emit.py` — noted, not touched here.

Also observable and not re-derived: the patched bundle's admissibility condition
(`rebuild-plan.md` §1, 2026-10-27), measured there at 22,337 record differences over 429 documents
with zero differences a validator can act on.

---

## Part B — internal only, no verdict

Each of these is stated in `architecture.md` as a structural property of `codegen/`. **No consumer
of `src/adcp` can observe any of them**, and none is a correctness claim. They are recorded here
so that nobody files them as defects or gates them.

- §1's five-layer pipeline sketch, and which module holds which stage.
- §2's paradigm: total functions over immutable values, immutable node representations, composition
  by explicit combinators, effects at the two ends only.
- §2 / §14 step 10: the lowering seam collapsing to `Lowering` alone, `Refusal` narrowing to its one
  producer in `bundle.record`, `Kind.DEFERRED` retiring. (`lower/decide.py` returns
  `Decided | Refusal` today.)
- §3: `keywords.py` as the one table with exactly four readers, and nothing else in `codegen/`
  naming a keyword in a set literal.
- §4: `parse` as the one reader of a raw mapping; the twelve node kinds as frozen dataclasses; a
  handler reading node fields and never a mapping.
- §5: the one dispatch, chosen against a `(position, kind)` product table and a polymorphic
  hierarchy.
- §6: who walks, who carries the position, how a child's `Lowering` composes.
- §7: the IR being complete — "nothing before `render.py` holds a string of Python" — and naming
  being a pass over the finished module rather than a thread through the walk.
- §8: the one-way Pydantic boundary, and `render.py` being the only importer of it under
  `codegen/`.
- §9: `verify/` as a package with a closed import set that never names the walk.
- §11: the layer table, the arrow graph, the import graph being acyclic, and the "nothing repeats /
  one owner" table in full.
- §12: `compiler.py` and `emit.py` dissolving into `schema/`, `lower/`, `ir.py`, `render.py`,
  `emit.py` and `__main__.py`; `harness.py` and `dump_exemptions.py` becoming `verify/`.
- §14 steps 1, 2, 4, 5, 6 and 7 in their entirety — every one is a relocation of code between
  modules with a byte-identical tree as its own stated check.
- `execution-plan.md` Phase 1's eight rows, which are those steps under other numbers.

**The *bytes* mark is why this half stayed half-built, and it is worth recording once.** A gate
that passes when nothing happens proves a relocation broke nothing and cannot prove the relocation
occurred. That diagnosis is correct and it is *not* an argument for ratcheting the internal
figures: see the note at the end of this document.

---

## Part C — sentences the two documents need

A lane may not edit `rebuild-plan.md` or `architecture.md`. These are the sentences this walk found
that need the owner, each with what the artifact says instead.

1. **`rebuild-plan.md` §1 — what the domain surface EXPORTS.** The section says a module is
   "re-exported from `adcp.types.<domain>`" and never says which of its names. `__all__` answers a
   different question (A-3), and the difference is 2,283 classes in 486 modules. Without this
   sentence A-2 cannot be built, only guessed.

2. **`rebuild-plan.md` §4 Names — whether a branch name carries the root's prefix.** The worked
   example writes `FRCodePostal`, `AUPostcode`, `BRCep`, `INPin`, `ZAPostalCode`, `US`, `GB`, `CA`,
   `Plz`; the artifact writes `PostalCountrySystemFRCodePostal` and so on. The nested rule's own
   reason — "the module path already carries the document" — argues for the short form, and D5's
   one-importable-symbol rule argues the root prefix is not free. Either the example gains the
   prefix or the rule says the branch is not prefixed.

3. **`rebuild-plan.md` §4 Names — the measured figure for indexed branches.** "Measured: 19 classes
   over 6 documents take the index today, and every one of them is a bare `$ref` whose target names
   itself." A fresh run over the portable population gives **18 classes over 7 documents, and 3 of
   the 18 are not bare-`$ref` branches** (`adagents.json`'s, `core/postal_country_system.json`'s
   complement branch, `media-buy/buy_products_request.json`'s). The rule is unaffected; the sentence
   over-claims its population.

4. **Three stated figures are pre-`refused == 0` and read as present tense.** Each was true when
   written and is now a figure over an empty set:
   - `architecture.md` §11: "`lower/` still names `Refusal` at 141 sites."
   - `architecture.md` §14 step 8: "of the **141 primary refusals** exactly 1 sits on an
     `Effect.REFUSE` cell."
   - `rebuild-plan.md` §8: "Measured over the **102 primary refusal sites**: 43 are `properties` and
     `items` segments only, 46 sit inside a combinator, and 13 have no instance location at all."

   Primary refusals are 0. Each sentence is load-bearing *as history* — it records why a step was
   ordered the way it was — so the repair is a tense and a date, not a deletion.

---

## Part D — docstrings promising an end state that has not arrived

These are in the code, where the next lane reads them first. Two of the five ship to consumers.

| where | what it claims | what is true |
| --- | --- | --- |
| **`src/adcp/types/constraints.py`** (SHIPPED) | "Every other type this SDK emits is reachable at `adcp.types.<domain>.<Name>`, where the domain is the schema document's own path." | No domain module exists (A-2). The sentence is a false claim about the artifact, in the artifact, read by the consumer it is addressed to |
| **`src/adcp/types/__init__.py`** (SHIPPED) | "The public surface … is generated from the binding table in step 9. Until then this is the package marker" | §14 step 9 is "the faithful rows" and owns no binding table. Step 9 has landed; the surface has not. The docstring points a reader at a step that will never produce it |
| **`codegen/schema/__init__.py`** | "It has **NO READER yet**: `parse.py` is the other half of §14 step 5 and is not written, so `emit._decide` is still the per-node dispatch and still reads a mapping." | `codegen/schema/parse.py` is 1,458 lines and is the reader; `codegen/lower/decide.py` is the exhaustive `match` and `emit._decide` is not the dispatch. Actively misleading about which half of step 5 is missing |
| **`codegen/lower/__init__.py`** | "`codegen/emit.py` holds the run and the ONE per-node dispatch"; "What remains of step 5 is moving `decide` itself in here, as the exhaustive `match` … which needs `schema/parse.py`." | `codegen/lower/decide.py` *is* that match, and `schema/parse.py` exists. The one sentence a lane picking up step 5 would read is the stalest |
| **`codegen/compiler.py`** | "**§14 steps 5 and 7 dissolve this module.**" | 6,271 lines, not dissolved. This one is **internal only** by the axis above, so the repair is to restate it as a maintainability note with no step number attached rather than as a plan a lane is behind on |

---

## A note on the instrument this document replaced

This row was first scoped to make the internal figures a ratchet — `compiler.py`'s line count, its
importer count, `Refusal(` mint sites, keyword set literals, module-level import cycles — each with
today's value as a ceiling, in `./check --architecture`. **That was withdrawn before any code was
written** (`adcp-client-python-10l.114`), because it encodes the shape of the code as a test: there
are unboundedly many wrong internal shapes, so pinning a handful proves nothing; the pins block the
refactoring they were meant to drive; and none of them establishes any correctness a consumer can
observe.

The baselines were measured before the stop and are on that bead, as a one-off reading and
explicitly not as a gate. The replacement is this document's axis: an internal goal is a preference
and gets no verdict, and the figures that *are* gated are the ones in Part A, every one of which a
consumer of `src/adcp` can check.
