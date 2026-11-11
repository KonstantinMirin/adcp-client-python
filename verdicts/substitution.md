# The substituted tree imports: `adcp-client-python-l1r3`

**Before**: 735 items collected, 738 collection errors, one cause.
**After**: **11,681 items collected**, 177 files still erroring, a different cause.

Every figure here is from a command, and the tree was rebuilt rather than patched — §8a says
a drop-in tree is disposable and is regenerated from this repository, never edited.

---

## 1. Reproduced first

`/srv/ws/dropin-now` (digest `59ae4ad1…`) was not re-measured. A tree was rebuilt from this
trunk and the bead's defect reproduced on it:

```
PYTHONPATH=.:src ./.venv/bin/python survey/regenerate.py \
    --wheel /srv/ws/scratch-words/upvenv/lib/python3.12/site-packages/adcp \
    --out /srv/ws/.adcp-scratch/l1r3
```

Collected over `tests/`: **735 of 5,596, with 366 files erroring**, every one reaching
`ModuleNotFoundError` on a module of ours the substitution had not copied.

The bead reads the count as 38 public domain modules and that is right: this repository
publishes 38 non-underscore modules at `src/adcp/types/*.py`. The built tree held 23 of them
— the ones that compose `_surface` — and none of the other 15.

---

## 2. The defect: the copy step was a SELECTION

`_copy_ours_beside` copied four named modules, then every public path whose body is
`from ._surface.<stem> import *`. Both readings are a **subset** of our type layer, so the
substituted tree was missing **14 modules of ours**:

```
_adapter  _restored  aliases  base  buyer  capabilities  error_narrowing
guards  legacy  media_buy_status_helpers  projections  registry  v32  variants
```

Twelve of those are words `strip_their_types` had *just moved out of the way*: upstream's own
module went to `types/_upstream/<word>` because the name collides with one of ours — and then
ours never arrived, so the path held nothing at all. The import dies first on
`adcp.types.base`, because our `_base.py` reads `from adcp.types.base import AdCPBaseModel`,
the restored upstream base every emitted model derives from.

**The fix is the whole directory, because any predicate over it is a selection and a
selection is what went wrong.** `codegen/emit.py` writes into `_schemas/` and `_surface/`,
both subdirectories, so every `*.py` sitting directly in `src/adcp/types/` is ours by hand or
ours by a survey, and all of it is the layer the substitution puts in place of theirs. The
two halves of the build now read the same directory: `strip_their_types` already asks
`module.stem in ours` over it.

Copied beside the emit: **4 → 51**.

---

## 3. `canonical_creative`: `strip_their_types` kept it, and it is not a stale source

The bead asks which. **Measured**: the file in the built tree is upstream's wheel bytes plus
the one declared `MACHINERY_MARKER`, which only `strip_their_types` appends. Not a stale read.

It kept it because the keep/move rule asks only `module.stem in ours` — and a module this
repository **deleted** has no name left to collide with, so it fell through to "keep as
machinery". A module withdrawn on purpose came back through the wheel.

**The rule that settles it is derived from a classification this repository already commits.**
`survey/upstream-machinery-9.6.1.tsv` carries a `verdict` per module of upstream's `types/`;
`LIVE-RESTORE` is this repository saying *their hand-written file is one we must carry*. Read
beside the live tree, the pair that can only mean a deliberate withdrawal is

> `verdict == LIVE-RESTORE` **and** no `src/adcp/types/<stem>.py` here.

On this trunk it names exactly one module, `canonical_creative`. Every other module upstream
has and we do not is `LIVE-TRANSITIVELY`, `TEST-ONLY-DELETE` or `GENERATED-STAYS-DELETED` —
the record never claimed those, so theirs is genuine machinery and keeps its bytes
(`validation`, `coercion`, `seller`, `response_dispatch`, `versioned`, …). Restore a module
and the pair stops matching; delete another `LIVE-RESTORE` one and it withdraws the same way.

### The withdrawal is not free, and the patch is now carried

Withdrawing it alone cost **128 test files**, none of them about creatives: upstream's own
kept SDK imports the module at module scope — `src/adcp/client.py` line 188 and
`src/adcp/server/responses.py` twice — so `adcp.client` stopped importing and everything
downstream of it failed at collection.

`adcp-client-python-2f52` already made that patch in this repository, and the owner accepted
it in those words: *"Means drop-in is impossible and we STILL DELETE THEM … drop-in and a
patch then."* What was missing is that the substituted tree never carried it.
`_carry_the_patch_a_withdrawal_needs` now replaces an upstream SDK module with ours when all
three hold:

1. upstream's copy **imports** a withdrawn module (by AST, so a comment naming it is not an
   import);
2. this repository has a module at the same path;
3. **ours does not import it.**

The third clause is what makes the swap a repair rather than a preference: it carries only
the modules whose patch is the removal of that very import, so the substitution cannot creep
from `types/` into upstream's SDK. Measured, it names two files —
`src/adcp/client.py` and `src/adcp/server/responses.py` — and the 128 errors go.

---

## 4. The deselect integration: two tables became one

There were two layers and the runner read one.

| layer | classifier | was written to | was read by a built tree |
|---|---|---|---|
| `delete-set` | `survey/upstream_test_character.py` — the ASSERTION is about upstream's representation | `deselect.tsv` | yes |
| `invented-default` | `survey/dropin/deselect.py` — the test leans on a default that makes a required field optional | `deselected-9.6.1.tsv` | **no** |

So the invented-default classification declined nothing, and every figure from such a tree
counted tests it had already judged uncountable.

`deselect_the_declined` now writes **one** `deselect.tsv` with a `layer` column, and a row's
`reason` is its own layer's sentence — the character classifier's quoted assertion, or the
model, field, document and pointer that refutes the default. `deselect_plugin.py` reads that
one table and reports per layer. The eleven evidence columns stay in `deselected-9.6.1.tsv`;
`committed_rows()` is the projection the runner needs.

Measured on the built tree: **63 test functions declined — 32 `delete-set`, 31
`invented-default`** — 86 collected items, and `DELETE` items surviving collection is **0**.

One defect found by running it: the invented-default table keys on a node id that may carry a
class segment (`file.py::Class::test`), and the plugin keys on the last `::` segment. The
projection now takes the last segment too, which the plugin's own staleness gate caught
rather than letting the row silently decline nothing.

---

## 5. THE FIGURE, three ways, with its denominator

Upstream's baseline, **reproduced today** on their own tree
(`/srv/ws/wt-upbase`, `-n 8`, same flags):

```
21,668 collected   18,819 passed   2,848 skipped   1 failed
```

The substituted tree, same command, `-p deselect`:

| denominator | collected | **passed** | failed | errored | skipped |
|---|---|---|---|---|---|
| **BEHAVIOUR** | 11,281 | **8,459** | 1,026 | 13 | 1,783 |
| **BEHAVIOUR + PORT** | 11,487 | **8,597** | 1,094 | 13 | 1,783 |
| **everything collected** | 11,681 | **8,597** | 1,094 | 190 | 1,800 |

**The denominator is the finding.** 21,668 − 11,681 = **9,987 items that never reached the
junit**, because 177 of upstream's files still error at collection. A pass-rate over 11,681
is not comparable to one over 21,668 and is not offered as one.

---

## 6. What still blocks the remaining 9,987, named exactly

**102 of the 177 erroring files are one unbounded recursion, and it has one name.** Traced by
spying on `adcp.types.__getattr__` while importing `adcp.types.aliases`:

```
cycle: GetContentStandardsResponse1 -> GetContentStandardsResponse1 -> ...
  _dropin.py:442 __getattr__  ->  types/__init__.py:216 __getattr__
  ->  _dropin.py:257 __getattr__  ->  _dropin.py:181 __getattr__
  ->  _dropin.py:145 _from_flat  ->  (back to 442)
```

`src/adcp/types/aliases.py` carries `from adcp.types import GetContentStandardsResponse1 as
GetContentStandardsResponse1` — the flat-surface re-point landed at `f6607f1c1`, because the
positional-name ruling withheld that declaration's domain word and the flat word was the
public home left. In **this** repository the facade resolves it through `_flat` and it is
fine. In the **substituted** tree `_dropin`'s finder routes the flat word back through
`adcp.types.__getattr__`, which reaches `aliases` again, and the two `__getattr__`s call each
other without a re-entrancy guard.

Both files are outside this lane's write scope: `src/adcp/types/aliases.py` is generated by
`survey/adapter_surface.py`, and the cycle's other half is `survey/dropin/_dropin.py`. The
repair is one of two, and the measurement does not decide between them:

* give `_dropin`'s flat resolution a re-entrancy guard, so a word it is already resolving is
  not asked of the facade again; or
* have `survey/adapter_surface.py` write the declaration's own module path rather than the
  flat word, and accept the withheld-name problem that the flat re-point was solving.

The other 75 erroring files are 7 on `ImportError` from
`_schemas/protocol/get_adcp_capabilities_response.py` and `_schemas/core/registry_event.py`,
1 on an `AttributeError`, and the remainder downstream of the same recursion.

`tests/test_domain_roots_import_in_any_order.py` still does not collect:
`AttributeError: module 'adcp.types.domains' has no attribute 'DOMAINS'` — the finder serves
the domain modules and not the package attribute that file's parametrisation reads. Same
owner, same file.

---

## 7. Gates

```
./check            emitted 1059 / refused 0, primary 0 / chained 0,
                   approximated 383 facts in 148 documents
oom_kill           75 before and after every run
wt-upbase          git status clean -- not one byte touched
upstream's tests   deselected, never excised; every retained file byte-identical
```

No allowlist, no ratchet, no floor, no budget. Four sets are derived here and none is
written: the copy step is the whole of `src/adcp/types/*.py`; the withdrawal is
`LIVE-RESTORE` ∧ absent-here; the patch set is the modules the withdrawal breaks whose
replacement does not import it; the deselect table is the two classifiers' own output.

Write scope: `survey/regenerate.py`, `survey/dropin/deselect_plugin.py`,
`survey/dropin/deselect.py`, `verdicts/substitution.md`. `deselected-9.6.1.tsv` was not
modified — its eleven columns were already correct and only the projection of them changed.
Nothing in `src/`, nothing in `codegen/`.
