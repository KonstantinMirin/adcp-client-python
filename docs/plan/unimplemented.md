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

**Every row carries RELOCATION or DECISION**, including the achieved ones, because that column is
what says whether a row can be handed to a lane. A *relocation* is delegable and verified
mechanically against a gate that exists or is named here; a *decision* needs the owner, and the
sentence it needs is in Part C.

---

## How every figure here was derived, and what it supersedes

**The subject is the tree a fresh run emits** — `architecture.md` §5's rule of 2026-10-29 ("the
tree is an ARTIFACT and not a phase"). That is now also the subject of *grading*: the grading row
landed, so a census and the suite range over the same population, and the 2026-10-29 reading of
this document (taken while they did not) is superseded wherever the two disagree. **Nine of its
figures are refuted below and each refutation is named in place.**

```
cd /srv/ws/wt-replan
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

Fresh tree: **1,084 `.py` files** — 1,053 document modules plus `brand/__init__.py` (one namespace,
item **A-1**) plus 30 package markers — carrying **3,449 module-level classes**, beside **1,054
`.json` records** at the documents' own hyphenated paths. Every figure below is an AST walk over
those files, a `bundle.record` lookup, `tools/parity/census.py` over the same tree, or a named
cheap gate. **No figure here needed the full suite**, which is 6–7 hours cold; where a figure needs
the grader the gate is named and the row says whether this walk ran it.

Two populations the rest of this document uses: `tests/test_emit.graded()` yields **2,793 pairs**
(class-or-alias against the schema it names), and `pytest tests/ --collect-only` collects **3,495
items**.

---

## Part A — observable in the artifact

### A.1 NOT ACHIEVED, in the order a consumer meets them

| # | the goal, and where it is stated | derived status | size | RELOCATION or DECISION | the gate |
| --- | --- | --- | --- | --- | --- |
| **A-2** | `rebuild-plan.md` §1: "re-exported from `adcp.types.<domain>`, where the domain is derived from the document's own path" | **NOT ACHIEVED.** 0 domain modules exist. `src/adcp/types/` holds `_base`, `_runtime`, `constraints`, `envelopes`, `_schemas/`. **22** domains are present as Python packages under `_schemas/` (`a2ui`, `aao`, `account`, `brand`, `collection`, `compliance`, `content_standards`, `core`, `creative`, `enums`, `error_details`, `extensions`, `formats`, `governance`, `media_buy`, `pricing_options`, `property`, `protocol`, `registries`, `signals`, `sponsored_intelligence`, `trusted_match`), so every consumer import today is the private `adcp.types._schemas.<path>` | 22 modules over 1,054 documents | **BOTH** — the domain is derived from the path (relocation); *what each module exports* is undecided (A-3) | NONE. A named one: every class the tree declares resolves at exactly one `adcp.types.<domain>.<Name>` |
| **A-3** | `rebuild-plan.md` §1: "There is **one import path per class**, and never a second way to reach the same class. … The one path is the domain surface's" — the export half | **NOT ACHIEVED, and it is the decision A-2 is blocked on.** `__all__` is `emit.exported`, derived and correct for the question it answers ("the names another module can ask for"). It is not a consumer surface. **486 of 1,084 modules declare 2,283 of the tree's 3,449 classes that their own `__all__` omits.** Of those 2,283, **611 are union branches** — a class whose base list names a class declared in the same module — and **613 branch classes exist, so 611 of 613 are unreachable publicly**. `core/requirements/asset_requirements.py` declares 13 classes and writes `__all__ = ["AssetRequirements"]` | 2,283 classes in 486 modules; 611 of 613 branches | **DECISION.** Neither document states what the domain surface exports. Re-exporting `__all__` leaves 2,283 classes unreachable; re-exporting every declaration contradicts nothing but has never been said | NONE until the sentence exists. `tools/parity/census.py --tree` prints the row (`unexported`) |
| **A-4** | `rebuild-plan.md` §1: "one import path per class" — the collision half | **NOT ACHIEVED.** 4 modules bind **56** names to two classes each: `adagents.py` (16), `core/async_response_data.py` (19), `core/package_format_snapshot.py` (16), `core/vendor_pricing_option.py` (5). Each module *imports* the name and then declares a subclass under it, so after the module body the name means the subclass and a consumer importing it from the two modules gets two classes with different `__adcp_schema__` pointers. Python does not object: the base is evaluated before the name is bound | 4 modules, 56 names. `lower/names.py`'s `occupied` does not treat an imported symbol as occupied | RELOCATION | EXISTS **and is RED, naming all 56**: `tests/test_names_collision.py::test_no_module_of_the_tree_declares_a_name_it_imports` (3.2 s). Bead `adcp-client-python-10l.111` (it reports 5 names; the tree is 56) |
| **A-6** | `rebuild-plan.md` §4 Names (2026-10-29, bead `.93`): "A boolean pin contributes no segment, because `true` names nothing" | **ACHIEVED** (`3be.11`, 2026-10-30). Verified on a fresh emit: **0 of 3,449 class names end in a boolean-pin segment**, against 8 before. §4's figure said three branches; the measurement is four of each shape — four keep the identifying pin and drop the boolean, four are all-boolean so rung 2 answers nothing and the branch falls to rung 3. It subsumes the collision case as §4 says, and 0 branches of the bundle collide on a non-boolean pin. Was: **NOT ACHIEVED.** `core/package_signal_targeting.py` declares `PackageSignalTargetingBinaryTrue` and `core/signal_targeting_expression.py` declares `SignalTargetingExpressionBinaryTrue`; the rule gives `…Binary` | 1 rule; 2 class names, 3 branches pinning something identifying beside a `true` | RELOCATION | NONE for this clause. `tests/test_names_collision.py::test_rung_two_reads_every_pin_the_branch_states_in_the_documents_key_order` is green and does not reach it |
| **A-7** | `rebuild-plan.md` §4 Names (2026-10-28): "The `definitions` entry dropped its `<Root>` prefix … the module carries the document" | **ACHIEVED** (`3be.11`, 2026-10-30). `names.Entry` is a chain of TWO, `(root, key)`, so the dropped prefix is the entry's ANCESTOR segment and §4's collision rule can still spend it. 150 of 153 entry positions over 44 documents lost the prefix; the 3 that keep it are the 3 real collisions. Over 40 chars **174 → 128**, median 18 → 17, verified on a fresh emit. Was: **NOT ACHIEVED.** `core/verification_token_claims.py` declares `AgenticAdvertisingOrgVerificationTokenClaimsVerificationTokenGradingProfile` — 75 characters, the document's own worked example of the old rule. Tree-wide: **479 of 3,449** names exceed 30 characters, **174** exceed 40, **101** carry three or more ancestor segments; the longest is 85 (`AdCPAgentsAuthorizationCommunityFormatRegistryAuthorizedAgentsItemPublisherProperties`). Median name is 18 characters | 1 naming rung, 174 names | **BOTH** — whether a branch carries the root's prefix is Part C item 2 (decision); the `definitions`-entry rung itself is a relocation once that is answered | `tests/test_names_collision.py::test_the_long_name_is_the_exception_and_not_the_rule` exists and is green, so it does not reach this |
| **A-8** | **BLOCKED on `adcp-client-python-sys`** — implemented, measured and REVERTED, because the second declaration SUBSTITUTED the first: a site is `(document, pointer, keyword)` in three places, so which kind survives is path-dependent. `rebuild-plan.md` §4 (2026-10-29): "For `oneOf` it is false, and an inseparable `oneOf` owes TWO declarations" — the dropped exclusivity is a WIDENED fact declared **beside** the UNDERDETERMINED one | **NOT ACHIEVED.** All **18** `oneOf` facts the fresh tree declares carry `kind='UNDERDETERMINED'` alone; 0 carry both kinds. `core/evaluator_spec.py` — the document's own measured case — writes exactly one `Approximation` at `core/evaluator-spec.json#/oneOf` | 18 sites over 16 documents, 1 handler arm | RELOCATION | NONE. A named one: every inseparable `oneOf` pointer carries both kinds; its mirror is `tests/test_the_declared_backlog.py` |
| **A-9** | `architecture.md` §2 (2026-10-29): "The approximation takes the `SchemaRef` spelling, because that is the one the reader of a declaration uses" | **NOT ACHIEVED, unmoved.** Of 178 `Approximation(...)` instances in the fresh tree, **38 have a pointer a strict segment-walk of their own document of record cannot reach** — the `patternProperties` family under `creative_manifest`, and `adagents.json#/oneOf/1/anyOf`. At the level the report counts, **25 of the 120 distinct facts**. Against the RAW document rather than the record, 85 of 178 | 38 of 178 instances = 25 of 120 facts | RELOCATION, and it is the mechanism A-14 is blocked on | `tests/test_the_declared_backlog.py::test_the_underdetermined_equality_holds_in_both_directions` is RED on this cause (A-14) |
| **A-10** | `rebuild-plan.md` §6 and §7: `errorMessage` and the registry data keys move into §6's projection | **HALF ACHIEVED, and the remaining half is one cell.** The 19 registry data keys are `Effect.NOTHING` in `keywords.py` and project into §6's generated grid; §7's grid no longer carries them. **`errorMessage` is the only `Effect.REFUSE` row left in the table**, so §7's generated region still lists it where the section's title is "the set is empty", and §6's grid has no row for it. §7's own prose still says "the grid above … still carries both rows" | 1 cell and `pytest tests/test_keywords.py --write-grids` | RELOCATION, and **flipping that one cell is also the whole of §14 step 8's `Effect.REFUSE` residue** | EXISTS: `tests/test_keywords.py` holds the grid equality in both directions (green, because the cell and the grid agree *with each other* on the stale answer) |
| **A-11** | `architecture.md` §14, after the waves: "these keywords' OURS approximations reach 0" | **NOT ACHIEVED — this is the open work, not a defect.** ours 120, upstream 0. By attribution, counted in FACTS: `§5 objects/patternProperties` **80** facts in 28 documents (all WIDENED), `§5 combinators/anyOf` **21** in 18 (all UNDERDETERMINED), `§5 combinators/oneOf` **18** in 16 (all UNDERDETERMINED), `§5 strings/maxLength` **1** in 1 (WIDENED). WIDENED 81, UNDERDETERMINED 39, never summed. **One keyword family is two thirds of the backlog** | 120 facts in 53 documents | DECISION per keyword family, then RELOCATION | EXISTS: the report's own figure, printed by `./check` |
| **A-12** | `rebuild-plan.md` §8: a model is never tighter than its document and never silently wider — the three defect directions pinned at zero through `COMPARISON_FACTS` | **NOT ACHIEVED. `COMPARISON_FACTS` holds 0 entries and the live reading is 155 red pairs over 75 documents, carrying 1,086 red facts: missing 718, differs 43, added 325, over_declared 0.** 105 of the 155 are red on `missing` alone and 8 on `added` alone. Worst documents: `media-buy/proposal-refinement.json` 10 pairs, `adagents.json` 8, `media-buy/refine-proposals-response.json` 8, `media-buy/create-media-buy-request.json` 7 | 155 of 2,789 comparable pairs; 1,086 facts | **BOTH** — `over_declared 0` is met and stays a pin (relocation); the 1,086 facts are not one cause and the owner has to say which of §8's rows each direction belongs to before they can be split into lanes (decision) | EXISTS **and is RED**: `tests/test_emit.py::test_every_class_passes_all_three_checks` and `::test_the_harness_result_is_counted_over_the_whole_population`, which asserts `live == COMPARISON_FACTS`'s own arithmetic. Reproducible in ~4 minutes *without* the accepts draw: `harness.compare_schema` over `graded()` |
| **A-13** | `rebuild-plan.md` §8 / `architecture.md` §9: the declared backlog is the set the walk mints, read off the run and not off a docstring | **NOT ACHIEVED as a gate.** `DECLARED_WIDENINGS` is pinned at **117** sites and a fresh run mints **120**: the three new ones are `media-buy/proposal-refinement.json#/oneOf/1/anyOf`, `media-buy/refine-proposals-request.json#/properties/refinements/items/oneOf/1/anyOf` and `media-buy/request-proposals-request.json#/anyOf`, all `anyOf`. Nothing is pinned-and-no-longer-declared | 3 sites | RELOCATION — re-pin from the run, with the three named | EXISTS **and is RED**: `tests/test_the_declared_backlog.py::test_the_declared_backlog_is_the_set_this_compiler_mints` (110 s for the file) |
| **A-14** | `rebuild-plan.md` §8: "The set of unions declaring one equals the set the derivation cannot separate, in both directions" | **NOT ACHIEVED in the stale direction, and it has grown.** The silent direction is exact — **89** inseparable-and-undeclared sites, equal to `UNDERDETERMINED_UNIONS` in both directions. The stale direction reads **5**, not 3: `adagents.json#/oneOf/1/anyOf`, `core/async-response-data.json#/anyOf`, `core/mcp-webhook-payload.json#/properties/result/anyOf`, `media-buy/proposal-refinement.json#/oneOf/1/anyOf`, `media-buy/refine-proposals-request.json#/properties/refinements/items/oneOf/1/anyOf`. Two of the five are A-13's new sites, so the two rows have one cause | 5 sites | **DECISION**, and the sentence is Part C item 1 — the cause is A-9: one union, two spellings, counted twice. An equality is an obligation and not a ratchet, so it stays at `[]` and reddens | EXISTS **and is RED**: `tests/test_the_declared_backlog.py::test_the_underdetermined_equality_holds_in_both_directions` |
| **A-15** | `architecture.md` §9 / `rebuild-plan.md` §8: every class the tree carries is graded against the document it names | **NOT ACHIEVED for 4 pairs.** `harness.pair_of` raises `KeyError: '0'` at `#/anyOf/1/properties/account/allOf/0/anyOf/{0,1}` in `media-buy/buy-products-request.json` and `media-buy/request-proposals-request.json`: `_intersection` composes a restatement as `{**child, "allOf": [base]}`, so pointers below carry an `allOf` index the document does not have. 2,789 of 2,793 pairs can be paired | 4 pairs, 2 documents, 1 function | RELOCATION | NONE that passes today — the four raise inside the fixture rather than failing a check. A named one: `pair_of` succeeds for all 2,793. Bead `adcp-client-python-10l.108` |
| **A-16** | `architecture.md` §2: a shipped docstring's dotted cross-references resolve | **ACHIEVED** (fixed on trunk at `1b2e5e39`; three references, not one — the field was named in `nodes.py` twice more). Was: **NOT ACHIEVED, 1 reference.** `codegen/lower/union.py` writes `nodes.Union.siblings` and the symbol is gone — the raw-carrier row renamed it. Internal prose, but the gate is real and red | 1 reference | RELOCATION | EXISTS **and is RED**: `tests/test_prose_resolves.py::test_every_dotted_cross_reference_in_the_prose_resolves[codegen/lower/union.py]` (4 s) |

### A.2 Achieved, with the derivation

| the goal | derivation | RELOCATION or DECISION |
| --- | --- | --- |
| **`architecture.md` §5 (2026-10-29): the committed tree's population is `bundle.portable`, because the tree is an artifact** — **this was item A-1 and is now CLOSED** | **0 differences.** A fresh emission and `src/adcp/types/_schemas` agree byte for byte across all 1,084 `.py` files *and* all 1,054 `.json` records. The 2026-10-29 reading was 74 modules (39 absent, 35 differing); the regeneration landed and the goal holds | NONE — closed. Held by `tests/test_emit.py::test_the_committed_tree_is_what_a_fresh_run_emits` and `tests/test_fragment_ref.py::test_the_committed_tree_is_the_fresh_emission_of_the_derived_population` |
| **`rebuild-plan.md` §4 Names (2026-10-29): "A bare `$ref` branch is named for its TARGET, and the index is the rung after that"** — **this was item A-5 and is now CLOSED** | **0 bare-`$ref` branches take an index.** Only **5** `…Branch<N>` classes survive, over 5 documents: `adagents.py`'s `…CommunityFormatRegistryBranch0`, `content_standards/get_content_standards_response.py`'s `…Branch0`, `core/postal_area.py`'s `…Branch9`, `core/postal_country_system.py`'s `…Branch9`, `media_buy/buy_products_request.py`'s `…Branch1`. Read in the bundle, **none of the five is a bare `$ref`**: each branch states `properties`/`required`/`type` of its own and no earlier rung identifies it, which is §4's own "a branch with no derivable identity takes its index". The identity rung landed | RELOCATION — re-state the §4 measurement (Part C item 3); the rule needs no change |
| §1: "A set of Pydantic classes, one per schema node that needs one" | 1,054 of 1,054 portable documents emit; 3,449 module-level classes; `refused 0` | NONE — closed |
| §1: "Every portable document of the bundle contributes a symbol" | 30 of 1,084 modules declare no `__all__` and **all 30 declare 0 classes** — they are the package markers. 0 modules have an empty `__all__`; 0 have none where one is owed | NONE — closed |
| §1: "Generated modules are private" | the tree is `adcp/types/_schemas/`, a leading-underscore package | NONE — closed |
| §1: "a document compiles to a module at its own path" | every one of the 1,054 documents resolves to `emit.module_file(document, bundle.package_roots)` in the fresh tree; no module is unclaimed | NONE — closed |
| §1: "A second name bound to a class by identity … `X is Y` holds" | **60** module-level `X = Y` bindings in 32 modules — the carve-out, not A-4's collision (A-4 is a *subclass* under an imported name) | NONE — closed |
| `architecture.md` §10 (2026-10-29): a document whose path is also a directory's is that package's root | `brand.json` is the one such pair; `brand/__init__.py` carries the classes and declares an `__all__`, and `brand.py` does not exist. The rejected alternative — an unimportable `brand.py` beside a 0-byte package — is absent | NONE — closed |
| `architecture.md` §8: `AdCPRootModel` joins `AdCPBaseModel`, both taking `strict_validate` and `__adcp_schema__` from one mixin | `src/adcp/types/_base.py`: `class AdCPBaseModel(SchemaBound)` and `class AdCPRootModel(SchemaBound, RootModel[Any])`; 11 tree classes sit on them | NONE — closed |
| §2: "Constraints bind to the type, not the field"; "Every constrained scalar is named"; an alias names a constraint and never a concept | `adcp/types/constraints.py`, each name derived from the constraint alone; the two names that are decisions rather than derivations — `AdCPUrl` and the re-exported `HttpUrl` — carry their measurement (47 of the bundle's 300 `uri` positions restrict the scheme; `AdCPUrl` everywhere was tried and withdrawn at 228 of 300) in the module docstring | NONE — closed |
| §2 / `architecture.md` §7: an approximation is a DECLARATION written into the emitted module | 178 `Approximation(...)` instances → **120** distinct `(document, pointer, keyword)` facts in **53** documents, as `__adcp_approximations__` class attributes. Not in `json_schema_extra`, which §7 forbids | NONE — closed |
| §2: two kinds, never summed; ours and upstream, never summed | WIDENED 81 / UNDERDETERMINED 39 (reported separately); ours 120 / upstream 0; the report prints three figures over three denominators and adds none | NONE — closed |
| §2: a narrowing taken on purpose is admitted by an enumerated registry and by nothing else | one entry, `harness.URL_IMPLIED`, graded by `tests/test_decision_set.py` with both sides derived | NONE — closed |
| **`architecture.md` §9: the committed tree's declarations are the run's** | **0 and 0.** The committed tree carries 120 sites in 53 documents and a fresh run mints 120 in 53; `carried - minted` and `minted - carried` are both empty. The last reading was 58 carried-not-minted and 45 minted-not-carried | RELOCATION — `tests/test_the_declared_backlog.py::test_the_committed_trees_declarations_are_the_runs` is green with its two `ratchet` ceilings at 58 and 45 against a live 0 and 0; lower both to 0 so the gate guards again |
| §4 Names: root is `pascal_case(title)`, else the file stem | median class name 18 characters; **7** of 3,449 names end in a digit — A-5's 5 indexed branches plus `ComponentsItemFormatKindParamsHtml5` and `V2`, each of which is the document's own word | NONE — closed |
| §4 Names (2026-10-29): rung 2 reads **every** pin in the document's key order | `core/postal_country_system.py` declares `…FRCodePostal`, `…AUPostcode`, `…BRCep`, `…INPin`, `…ZAPostalCode` for the five two-pin branches and keeps `…US`, `…GB`, `…CA`, `…Plz` for the four single-pin ones | NONE — closed |
| §4 Names (2026-10-29): a rung that collides has not identified the branch, so **both** fall | `trusted_match/provider_registration.py` declares `TMPProviderRegistrationContextMatch` and `…IdentityMatch` off rung 3's `required` set, not rung 2's shared `true` | NONE — closed |
| §4 Names (2026-10-29): a branch colliding with its own root — the root keeps the name | `core/postal_area.py` declares the root as `PostalArea`; the branch moved. The hand-minted verdict that wrote off this document and the 31 chained behind it is gone: `refused 0` | NONE — closed |
| §4 Names (2026-10-28): where N positions collide, **all N** lengthen, so the name is order-independent | `tests/test_names_collision.py::test_all_n_colliders_lengthen_and_a_name_is_not_a_function_of_the_order` and `::test_inserting_a_branch_after_an_indexed_one_moves_no_existing_name`, both green; 15 of the file's 16 tests pass (A-4 is the one that does not) | NONE — closed |
| §4: a union root is a base plus one class per branch; a `$ref` branch is a class with two bases; the four mixin mechanics; a value serialises as what it is | `tests/test_emit.py::test_a_union_root_emits_a_base_plus_one_subclass_per_branch`, `::test_a_payload_resolves_to_its_branch_on_all_four_paths`, `::test_a_consumers_subclass_of_a_union_base_keeps_its_own_schema`, `::test_a_union_base_instance_and_a_branch_each_serialise_as_what_they_are` | NONE — closed |
| §4: which branch a payload is, derived from bundle data and never from a hand-written map | no per-document map exists; the inseparable residue is declared, 39 UNDERDETERMINED facts | NONE — closed |
| §1 / §3: the bundle directory is an argument and nothing reads a hard-coded path | `python -m codegen` requires `--bundle`; no version literal in the package | NONE — closed |
| §3 / §5: the grids of §5, §6 and §7 are generated between markers | `<!-- generated from codegen/keywords.py -->` … `<!-- end generated -->` regions present in `rebuild-plan.md`; `tests/test_keywords.py` holds the equality both ways and `--write-grids` writes it. The whole file is green | NONE — closed, except A-10's cell |
| `architecture.md` §2 (2026-10-29): a base list naming one class twice RAISES, at `ir.ClassDecl` | `tests/test_the_tree_imports.py::test_a_base_list_naming_one_class_twice_raises` green | RELOCATION — its companion `::test_no_document_of_the_bundle_reaches_the_duplicate_base_guard` needs a non-vacuous spelling; `tests/nodeset.py`'s refusal to let an empty population pass is the helper working as designed |
| `architecture.md` §2 (2026-10-29): a check may not be downstream of its own precondition | the import obligation moved out of `test_emit.py` and off the committed population: `tests/test_the_tree_imports.py::test_every_module_a_fresh_run_emits_imports_and_every_class_of_it_is_defined`. `graded()` reports `UNIMPORTABLE` empty over the fresh tree | NONE — closed |
| `architecture.md` §9 (2026-10-29): the accepts corpus is keyed on the DOCUMENT and never on our rendering of it | `harness.corpus_key` takes `identity` from the caller; `test_emit.identity_of` supplies `bundle.source_identities[document]` beside the pointer, and `tests/test_accepts_corpus.py` perturbs each half. 2,793 pairs give 2,793 distinct keys | RELOCATION — the store is mid-refill, which is A.3 |

### A.3 Observable but not re-derived in this row

`rebuild-plan.md` §8's accepts, refuses and round-trip checks range over 2,793 pairs and need the
grader. This row did not run them and asserts no value for them. The gates are
`tests/test_emit.py::test_every_class_passes_all_three_checks`,
`::test_the_schema_comparison_sees_a_fact_the_model_adds_as_well`,
`tests/test_every_check_names_its_set.py` (green) and `tests/test_the_declared_backlog.py`
(A-13, A-14). The comparison half of that same population *was* re-derived, as A-12, because
`harness.compare_schema` needs no draw.

**The held accepts corpus is mid-refill and the figure is a moving reading, not a defect.** The
corpus key moved to the document's own bytes, so every pre-move entry is orphaned: at this
reading `/srv/ws/.adcp-cache/accepts-corpus` holds **3,305 entries of which 2,252 are addressed by
no live pair**, and **1,740 of the 2,793 pairs hold no entry** (1,053 do). A cold pass is what
fills it. **RELOCATION, owned elsewhere** — `/tmp` is a 63 GB tmpfs and its exhaustion killed two
earlier full-suite attempts; the scratch move is another lane's row.

**`pyproject.toml`'s suite figures are stale in both directions and the file is not this row's.**
Its wall-clock table reports 3,322 s (55:22) at `-n 10 --dist=loadgroup` **over a population of
2,162 items**; collection today is **3,495**, 62% more, and a cold run is 6–7 hours. Its memory
paragraph claims a 10.35 GB peak. **RELOCATION** — re-read both beside the population they are
over; the memory figure has a live correction from another lane (73.4 GB) and that lane owns it.
`tests/test_type_checker.py` is RED with mypy errors in `compiler.py` / `emit.py`, so §2's "the
type checker proves the match total" is unproven — noted, not touched here. **RELOCATION.**

Also observable and not re-derived: the patched bundle's admissibility condition
(`rebuild-plan.md` §1, 2026-10-27), measured there at 22,337 record differences over 429 documents
with zero differences a validator can act on. **RELOCATION.**

---

## Part B — internal only, no verdict

Each of these is stated in `architecture.md` as a structural property of `codegen/`. **No consumer
of `src/adcp` can observe any of them**, and none is a correctness claim. They are recorded here
with today's READING so that nobody files them as defects, gates them, or carries a stale number
forward — **the figures in this part moved since 2026-10-29 and none of the movement is a verdict.**

- §1's five-layer pipeline sketch, and which module holds which stage.
- §2's paradigm: total functions over immutable values, immutable node representations, composition
  by explicit combinators, effects at the two ends only.
- §2 / §14 step 10: the lowering seam collapsing to `Lowering` alone, `Refusal` narrowing to its one
  producer in `bundle.record`, `Kind.DEFERRED` retiring. **Reading: there is no `class Lowering`
  anywhere in `codegen/`; `lower/decide.py:39` returns `Decided | Refusal`; `Refusal(...)` is
  called at 94 sites by AST, 49 of them in `compiler.py`; `Kind.DEFERRED` has 10 AST references
  across 5 modules.** (The figures 85, 93 and 141 all appear in committed prose; 94 is what the
  AST says today, and the 141 is a pre-`refused == 0` reading — Part C item 4.)
- §3: `keywords.py` as the one table with exactly four readers, and nothing else in `codegen/`
  naming a keyword in a set literal. **Reading, with its definition stated because the definition
  is most of the answer: counting every `set`/`frozenset` literal all of whose members are strings
  `keywords.py` also writes gives 55 sites outside it — 20 in `compiler.py`, 9 in `lower/union.py`,
  8 in `harness.py`, 6 in `schema/parse.py`, 5 in `lower/rules.py`, the rest singletons. Most are
  one-member membership tests (`{"$ref"}`), which the row that pointed eleven sites at the table
  deliberately did not touch. The 23 carried in earlier prose is a different predicate, and neither
  number is a goal.**
- §4: `parse` as the one reader of a raw mapping; the twelve node kinds as frozen dataclasses; a
  handler reading node fields and never a mapping. **Reading: `nodes.RAW_CARRIERS` declares the
  carriers and `tests/test_import_rule.py` holds the set equal to a name-blind detector in both
  directions — green.**
- §5: the one dispatch, chosen against a `(position, kind)` product table and a polymorphic
  hierarchy. **Reading: `lower/decide.py:56` is one `match` with 12 node-kind arms plus a `case _`
  carrying `assert_never`, and it is the only such construct in `codegen/`.**
- §6: who walks, who carries the position, how a child's `Lowering` composes.
- §7: the IR being complete — "nothing before `render.py` holds a string of Python" — and naming
  being a pass over the finished module rather than a thread through the walk.
- §8: the one-way Pydantic boundary, and `render.py` being the only importer of it under
  `codegen/`. **Reading: `render.py` holds all 11 `pydantic` / `datamodel_code_generator` imports
  in the MODEL layer and `tests/test_import_rule.py`'s `MODEL_LAYER_EXCEPTIONS` is `{}`.
  `harness.py` imports `pydantic` as the VERIFIER, which is the rule's own carve-out and not an
  exception to it.**
- §9: `verify/` as a package with a closed import set that never names the walk.
- §11: the layer table, the arrow graph, the import graph being acyclic, and the "nothing repeats /
  one owner" table in full. **Reading: over module-level imports inside `codegen/` there is now
  exactly ONE cycle, `compiler → lower.names → compiler`. Counting deferred (function-level)
  imports there are 13, every one of them through `compiler`. The walk→run edge is gone and
  `tests/test_import_rule.py` closes the population's imports transitively.**
- §12: `compiler.py` and `emit.py` dissolving into `schema/`, `lower/`, `ir.py`, `render.py`,
  `emit.py` and `__main__.py`; `harness.py` and `dump_exemptions.py` becoming `verify/`.
  **Reading, and NO VERDICT: `compiler.py` is 6,309 lines and 14 modules import it at module
  level. 6,271 and 6,279 both appear in committed prose and in beads; neither is current, and the
  line count is not a correctness goal — it must not be gated by a test asserting code shape.**
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

1. **`rebuild-plan.md` §8 — which spelling of a pointer a declaration is counted at.** This is the
   single sentence that unblocks the most: it is A-9's rule, A-14's cause, and two of A-13's three
   new sites. `architecture.md` §2 says "an approximation's pointer is the `SchemaRef` spelling",
   and the artifact writes the declaration at the node the *walk* reached, where the class is
   stamped one `allOf` conjunct away. `adagents.json#/oneOf/1/anyOf` is declared and separable
   while `adagents.json#/oneOf/1/allOf/0/anyOf` is inseparable and declared by nothing — one union,
   two spellings, counted twice, five times over. §8 needs to say which spelling the equality
   ranges over.

2. **`rebuild-plan.md` §1 — what the domain surface EXPORTS.** The section says a module is
   "re-exported from `adcp.types.<domain>`" and never says which of its names. `__all__` answers a
   different question (A-3), and the difference is 2,283 classes in 486 modules — **611 of the
   tree's 613 union branches among them**. Without this sentence A-2 cannot be built, only guessed.

3. **`rebuild-plan.md` §4 Names — whether a branch name carries the root's prefix.** The worked
   example writes `FRCodePostal`, `AUPostcode`, `BRCep`, `INPin`, `ZAPostalCode`, `US`, `GB`, `CA`,
   `Plz`; the artifact writes `PostalCountrySystemFRCodePostal` and so on. The nested rule's own
   reason — "the module path already carries the document" — argues for the short form, and D5's
   one-importable-symbol rule argues the root prefix is not free. This is A-7's decision half: 174
   names over 40 characters, and the prefix is in most of them. Either the example gains the prefix
   or the rule says the branch is not prefixed.

4. **`rebuild-plan.md` §4 Names — the measured figure for indexed branches, which the rule has now
   outrun.** "Measured: 19 classes over 6 documents take the index today, and every one of them is
   a bare `$ref` whose target names itself." A fresh run gives **5 classes over 5 documents, and
   none of them is a bare `$ref` branch** — each states `properties`/`required`/`type` of its own
   and no earlier rung identifies it. The rule is not merely unaffected; **it is satisfied**, and
   the sentence reads as a defect report for work that landed. An intermediate reading of 18 over 7
   with 13 bare `$ref`s is also superseded.

5. **Three stated figures are pre-`refused == 0` and read as present tense.** Each was true when
   written and is now a figure over an empty set:
   - `architecture.md` §11: "`lower/` still names `Refusal` at 141 sites." (94 by AST today, and
     the count is internal either way.)
   - `architecture.md` §14 step 8: "of the **141 primary refusals** exactly 1 sits on an
     `Effect.REFUSE` cell."
   - `rebuild-plan.md` §8: "Measured over the **102 primary refusal sites**: 43 are `properties` and
     `items` segments only, 46 sit inside a combinator, and 13 have no instance location at all."

   Primary refusals are 0. Each sentence is load-bearing *as history* — it records why a step was
   ordered the way it was — so the repair is a tense and a date, not a deletion. **And step 8's
   stated obstacle is gone twice over: `errorMessage` is the only `Effect.REFUSE` row left in
   `keywords.py`, so retiring the effect is A-10's one cell.**

6. **`rebuild-plan.md` §7's prose contradicts its own generated grid.** The section says "the grid
   above is generated and still carries both rows; the cells move when §6's do", and §6's have
   moved: the registry data keys are `Effect.NOTHING` and project into §6. One row remains. The
   sentence needs to say so, or say nothing and let the grid speak.

---

## Part D — docstrings promising an end state that has not arrived

**This part is EMPTY, and that is the finding.** All five rows the 2026-10-29 walk recorded have
been corrected, including the two that ship to consumers, and `tests/test_prose_resolves.py` now
grades shipped prose — every import path a shipped docstring names must resolve, no shipped
docstring may state a placeholder path, and the clauses are held against their own population.

| where | what it claimed | what it says now |
| --- | --- | --- |
| `src/adcp/types/constraints.py` (SHIPPED) | types are reachable at `adcp.types.<domain>.<Name>` | "through that document's own module, at its path under `adcp.types._schemas` — which is PRIVATE, and is the only path there is today" |
| `src/adcp/types/__init__.py` (SHIPPED) | the surface is "generated from the binding table in step 9" | names step 9 as *the faithful rows*, says the surface has NOT arrived, and gives the `pkgutil.iter_modules` reading a consumer can re-derive it from |
| `codegen/schema/__init__.py` | `parse.py` "has **NO READER yet**" | `parse.py` is the one parser and its reader is named |
| `codegen/lower/__init__.py` | step 5 still needs `decide` moved in and `schema/parse.py` written | "`codegen/lower/decide.py` is the exhaustive `match` over the node kinds", and records that the sentence a step-5 lane would read first was the stalest in the package |
| `codegen/compiler.py` | "**§14 steps 5 and 7 dissolve this module.**" | "§12 would dissolve this module, and NO ROW OWNS THAT … what is left in this file is a residue, and it is INTERNAL", pointing at Part B for why it gets no verdict |

**RELOCATION, and it is one line**: A-16 is the single dangling cross-reference the new gate
catches — `codegen/lower/union.py`'s `nodes.Union.siblings`, renamed by the raw-carrier row.

---

## A note on the instrument this document replaced

This row was first scoped to make the internal figures a ratchet — `compiler.py`'s line count, its
importer count, `Refusal(` mint sites, keyword set literals, module-level import cycles — each with
today's value as a ceiling, in `./check --architecture`. **That was withdrawn before any code was
written** (`adcp-client-python-10l.114`), because it encodes the shape of the code as a test: there
are unboundedly many wrong internal shapes, so pinning a handful proves nothing; the pins block the
refactoring they were meant to drive; and none of them establishes any correctness a consumer can
observe.

Part B's re-reading is the argument's own evidence. Every one of those five figures moved since
2026-10-29 — 6,271 → 6,309 lines, 12 → 14 importers, 85 and 93 → 94 mint sites, 23 → 55 set
literals under a stated predicate, 3 → 1 module-level cycle — and **not one of the movements is a
verdict a consumer could act on**, while four of the five would have reddened a ratchet for work
that improved the code. The replacement is this document's axis: an internal goal is a preference
and gets no verdict, and the figures that *are* gated are the ones in Part A, every one of which a
consumer of `src/adcp` can check.

**The other half of that lesson is that a figure rots in either direction.** Nine readings in Part
A were refuted today and five of the nine had gone *green* without anything noticing: the committed
tree matched, the bare-`$ref` rule was satisfied, the artifact-versus-run gap closed to 0 and 0,
the registry keys moved into §6, and all five Part D docstrings were fixed. A stale defect report
costs a lane the same day a stale pin does. **State the READING, with the command that produced
it.**
