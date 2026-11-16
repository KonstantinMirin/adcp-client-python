# The 98 failures about names the previous generator chose

**The measurement, from the two artifacts and not from a terminal.**

```
.venv/bin/python -m pytest tests/ -q --no-header -p no:randomly --continue-on-collection-errors
cp test-results/report.json test-results/{before,after}.json
```

| `report.json` → `summary` | before | after | delta |
| --- | --- | --- | --- |
| `failed` | 496 | **398** | **−98** |
| `passed` | 14,565 | **14,681** | **+116** |
| `error` | 5 | 5 | 0 |
| `skipped` | 2,826 | 2,825 | −1 |
| `total` | 17,893 | 17,910 | +17 |

`before.json` matches TASK.md's trunk figure exactly — failed=496, error=5,
passed=14565 — so this is the tree it says it is. The −98 is the whole population
and nothing else: **0 nodeids went from `passed` to anything else**, and **0
failing nodeids in `after.json` are new**. The one skip that went was the
`got empty parameter set` on the branch obligation, which is the opposite of a
loss. The +116 is more than 98 because the parametrisations that derived nothing
now derive something: the branch set went 0 → 26 and the file gained a test.

**Per file.**

| file | before | after | re-pointed | deleted |
| --- | --- | --- | --- | --- |
| `test_legacy_surface_names_every_branch.py` (was `…_every_arm.py`) | 55: 53 F, 1 P, 1 S | **81 P** | 53 | 0 |
| `test_domain_roots_import_in_any_order.py` | 31: 26 F, 5 P | **31 P** | 26 | 0 |
| `test_asset_aliases_stable.py` | 48: 19 F, 29 P | **39 P** | 10 | 9 |

**The other gates.**

```
./check                       emitted 1059 / refused 0 (deferred 0, verdict 0); accounted 1059   (unmoved)
.venv/bin/ruff check tests/   Found 104 errors                                    (was 105; it did not grow)
```

The ruff figure is a real before/after on the same command: the three files at
`3e09d6c70` with the renamed file absent gave 105, HEAD gives 104.

---

## TWO PREMISE CORRECTIONS, both on TASK.md's worked example

**1. `Slot` EXISTS. It is not the previous generator's invented word.** TASK.md
says *"no `Slot` exists anywhere in the tree"*. Measured, it exists twice:

```
src/adcp/types/_schemas/formats/canonical/_base.py:154   Slot = SlotsItem
src/adcp/types/legacy_names.py:2464                      from …formats.canonical._base import Slot as Slot
PYTHONPATH=.:src python -c "import adcp.types as t; print(t.Slot)"
    <class 'adcp.types._schemas.formats.canonical._base.SlotsItem'>
```

So `Slot` is on the public flat surface, bound by `legacy_names.py` under the
indexed decision *"One class per SUBJECT, not per position"*, and
`adcp.types.Slot is adcp.types.formats.CanonicalFormatBaseSlotsItem` holds.
`SlotsItem` is what §4 Names derives for the item of the `slots` array
(`formats/canonical/_base.json#/properties/slots/items`, which the class states
itself), and `Slot` is a second spelling of that one class.

**What is absent is a class on a PACKAGE ROOT.** The failing import is
`from adcp.types.domains.formats import Slot` — read off the `formats` package,
whose `__init__.py` is empty. The conclusion TASK.md draws is still the right
one, for the reason it gives (`domains` mirrors MODULE paths), but the ground is
"a package root binds no class", not "the word was invented".

**2. The 25 are not one cause.** TASK.md says the file *"fails 25 times on one
cause: `cannot import name 'Slot'`"*. Measured from `before.json`:

| failures | cause |
| --- | --- |
| 2 | `cannot import name 'Slot' from 'adcp.types._schemas.formats'` — the two reported entry points |
| 22 | `AttributeError: … has no attribute '__all__'` — 22 of the 24 mirrored roots are packages whose `__init__` declares nothing |
| 1 | `test_a_domain_root_imports_nothing_until_a_name_is_read`, on `core.AccountReference` |
| 1 | `test_a_resolved_name_…` — the same `core.AccountReference`, in-process, which is the `surface-absent:1` |

One reading underneath all 26, and it is the one TASK.md names: a domain root was
taken to BIND the tree's classes. Only `adagents` and `brand` declare anything
(1 and 50 names) because they are single-document MODULES at the top of the tree.

---

## THE LEDGER — 98 failures, one decision each

### `test_domain_roots_import_in_any_order.py` — 26 re-pointed, 0 deleted

The subject is real: #1784 is an import-ORDER defect and a fresh interpreter is
the only thing that grades it. What was graded against the previous surface was
the ROOT's contents.

* **2** entry points now import `SlotsItem` from the module that declares it,
  `adcp.types.domains.formats.canonical._base` — the mirror path, kept, because
  the mirror resolves module paths and that is what the reported defect was
  about. Verified in `python -I`: imports first, in any order.
* **22 + 2** root parameters assert the root **IS** the module it mirrors
  (`adcp.types.domains.<d> is adcp.types._schemas.<d>`, and the `sys.modules`
  entry too) and walk whatever `__all__` that module declares. Identity is the
  mirror's own load-bearing claim — its docstring states that a second execution
  under the mirror name would mint a second class per node with a false
  `isinstance` — so it is what a fresh-interpreter test should hold.
* **#1784 restated as `sys.modules`**, which is what the defect actually was:
  importing `adcp.types.domains.core` leaves **0** modules under it; importing
  `…core.account_ref` brings in **12** (its own `$ref` closure) and
  **not** `core/format.json`. Both measured.
* The resolution test states identity of module and of class, and **no**
  `sys.modules` assertion: the mirror name is registered when the import system
  is ASKED for it, and a process already holding `_schemas.core` reaches
  `account_ref` as an attribute of the package the root IS. That was found by
  running it — the first draft asserted the entry and raised `KeyError`.

### `test_legacy_surface_names_every_branch.py` — 53 re-pointed, 0 deleted

* **51** `Legacy*` classes failed one line: `_CANONICAL_ROOT = "adcp.types.domains"`.
  Classes are declared at `adcp.types._schemas.<domain>.<document>`; the mirror
  is a second NAME for those modules and never where a class says it was
  declared. Both halves of #1398's round trip (the prefix AND asking that module
  for its own attribute back) are kept, against the declaring root.
* **1** `test_the_derived_sets_are_not_empty`, red at `assert 0 > 12`. The branch
  set came from `rglob("*_response.py")` over the mirror package, which holds
  `__init__.py` alone. It now walks `_schemas`: **92** response modules, **12**
  on the `Legacy*` surface, **26 branches**, **0** of them unnameable.
* **1** `test_the_format_reference_is_reachable_under_a_public_name`, which
  pinned the public list to exactly `["LegacyFormatId",
  "LegacyFormatReferenceStructuredObject"]` and now reads
  `["FormatId", "FormatReferenceStructuredObject", "LegacyFormatId",
  "LegacyFormatReferenceStructuredObject"]`. The two additions are the document's
  own words — `core/format-id.json` is titled "Format Reference (Structured
  Object)" — so the list is asserted by **membership**: a name a document states
  is not a drift to pin out, and #1398 needs the `Legacy*` spellings to reach the
  compiled class, which they do.

**A branch is no longer a `typing.get_args` member, because the emission is not a
`Union[...]`.** A response union is a BASE plus one SUBCLASS per `oneOf` entry
(rebuild-plan §4), so `get_args` returned nothing and `(union,)` made every tool
a single-branch response. Branches are now the subclasses the declaring module
itself declares, and a second test asserts each carries the `#/oneOf/<i>` pointer
of the entry it compiles — without that, the set is "whatever the module
subclasses", a name pattern wearing a class graph.

**And the root is taken from its pointer, not from `<Tool>Response`.** A root
takes the document's TITLE, so `creative/list-creative-formats-response.json`
roots at `ListCreativeFormatsResponseCreativeAgent` and a `getattr(module,
f"{tool}Response")` lookup **skipped that document while reporting a full set**.
Reading `__adcp_schema__.pointer == "#"` (asserted unique per module) covers
12 of 12 and took the branch count 25 → 26. This was caught by counting the
skips rather than trusting the total, and it is the reason the file has one more
test than the ledger above implies.

### `test_asset_aliases_stable.py` — 10 re-pointed, 9 deleted

**Re-pointed (10).**

* **9** `<Type>Content` names asserted `cls.__module__ ==
  "adcp.types.domains.core.assets.<x>"`. The mirror hands the import system the
  private module ALREADY BUILT and deliberately does not stamp the mirror's spec
  onto it, so `__module__` reports `adcp.types._schemas.core.assets.<x>` —
  by design, and the design is written down. Graded there, and additionally on
  the document the class states itself: `__adcp_schema__` is
  `core/assets/<type>-asset.json#`, which is the obligation the public word
  carries and is stronger than any module string.
* **1** `FormatCategory`. No document in the pinned bundle states it, so no
  module compiles to `enums/format_category` and **no module path can carry the
  note**. The guided `ImportError` is served at the NAME by `adcp._REMOVED_IN_V4`
  — same regex, same `MIGRATION_v3_to_v4.md#formatcategory--removed` anchor —
  which is where `from adcp import FormatCategory` arrives.

**Deleted (9).** `test_legacy_asset_names_not_on_public_surface` demanded that
nine words be ABSENT from `adcp.types`. Every one is a word this tree states:

| name | what it is here |
| --- | --- |
| `AudioAsset`, `ImageAsset`, `TextAsset`, `VideoAsset`, `WebhookAsset` | the compiler's own class name, `pascal_case(title)` of `core/assets/<type>-asset.json` (§4 Names) |
| `CssAsset`, `HtmlAsset`, `JavascriptAsset`, `UrlAsset` | second names for `CSSAsset`, `HTMLAsset`, `JavaScriptAsset`, `URLAsset`, under the indexed decision *"One class per SUBJECT, not per position"* |

The assertion was the previous surface's 4.0 curation ("renamed to
`<Type>Content`"), and a tree that names classes from documents cannot honour it
without suppressing a word its own document gives. Removed, not adapted, per the
standing instruction. What the `<Type>Content` half owes is kept above and is now
graded against the document.

**Prose, in a fourth commit.** The file's docstring described `AssetsNN` classes
that `datamodel-code-generator` renumbers, repaired by editing a numbered import
in `aliases.py`. None of that is this tree: the branches of `core/format.json`'s
`assets` union are named from the document, `legacy_names.py` binds upstream's
words — numbered spellings included — to them, and renumbering cannot happen
because no name is a position. The 27 assertions that already passed grade the
failure that survives all of that: a public word landing on the wrong branch,
where `isinstance` and every payload go quietly wrong. The docstring and both
failure messages now say that and name the module that binds the word.

---

## WHAT I DID NOT TOUCH, AND TWO THINGS FOR THE OWNER

Nothing under `codegen/`, `src/` or `tests_emit/` was edited, and `./check` is
unmoved at 1059/0. No ground pointed at a compiler defect or a missing alias.

**1. Two files outside the write scope name the renamed file.** Both are prose,
neither affects a test:

* `tests/test_delivery_manifest_readback.py:159` — a docstring citing
  `tests/test_legacy_surface_names_every_arm.py` as where the `Legacy*`
  obligation lives;
* `survey/dropin/upstream-tests-about-their-generator.txt:73` — the drop-in
  roster, which lists the old filename.

`FINDINGS-del2.md` and `survey/bead-sweep.json` also carry the old path, as the
record of a measurement taken when that was the name; those read correctly as
history and I would leave them.

**2. AN OPEN QUESTION THIS LANE PINS AN ANSWER TO, so it should be said out
loud.** `survey/name-decisions-9.6.1.json` records a finding that upstream's
domain root *"carries the names that domain declares exactly once"*, i.e. the
DOMAIN SURFACE `adcp.types.<domain>`, while our mirror's root resolves to the
empty private package `_schemas.<domain>` — and it says binding
`domains.DOMAINS` and resolving the roots *"belong in one change to
`codegen/mirror/`"*. That change was not made, and
`test_each_domain_root_imports_first_and_is_the_module_it_mirrors` now asserts
the current answer: the root IS the private module. If the owner decides the
mirror's roots should instead carry the domain's names, that assertion is the
line that has to move, and the name-walk beside it would start grading 24 roots
rather than 2. I did not make that decision here; the mirror's own docstring
states identity as load-bearing, so pinning it is the conservative reading.
