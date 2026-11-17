# `make gate` refused to run on the first run under a cold compile key

**Measured 2026-11-17 in `/srv/ws/wt-flake` (branch `claude/the-gate-runs-every-time`).**

## The verdict first

| | | |
|---|---|---|
| what fired | `tests_emit/fresh.py:322` `_bound()`'s `assert not already` | pytest exit **3** (`INTERNALERROR`), `make: *** Error 3`, **no test collected, none run** |
| when | the first run under a compile key nothing has compiled yet | and on no other run, which is why it read as a flake |
| who imported the committed tree | `codegen.constraints.narrowed_by_url_type`, **inside the compile** | `from adcp.types import constraints` → `adcp.types.__getattr__` → `adcp.types.compat` → the 23 domain aggregators → `adcp.types._schemas` |
| the fix | the compile runs in a CHILD PROCESS (`tests_emit/fresh.py`, `_BUILD` / `_build`) | the assertion is untouched and still protects the same invariant |

**The assertion was right every time it fired.** The process really had bound
`src/adcp/types/_schemas` and really could not have been made to grade a fresh tree. What
was wrong was that the grading process was also the process that ran the BUILD.

## The importer, named

The audit hook (`sys.addaudithook`, raising on the first `import` event for
`adcp.types._schemas`) gives the chain verbatim:

```
tests_emit/fresh.py:342            PACKAGE = _bound()
tests_emit/fresh.py:293              types = _materialised()
tests_emit/fresh.py:254                compiled(BUNDLE, population())
tests_emit/compiled.py:318             out = emit.emit(Path(bundle), list(population))
codegen/emit.py:2817  …  codegen/lower/scalars.py:381
codegen/constraints.py:294             from adcp.types import constraints as emitted
src/adcp/types/__init__.py:154         compat = _alias_module()
src/adcp/types/__init__.py:339         importlib.import_module("adcp.types.compat")
src/adcp/types/compat.py:34            from adcp.types.a2ui import A2UIBoundValue as A2UiBoundValue
src/adcp/types/a2ui.py:11              from ._surface.a2ui import *
src/adcp/types/_surface/a2ui.py:21     from .._schemas.a2ui.bound_value import A2UIBoundValue
```

Three facts make it, and all three are load-bearing:

1. **The compiler READS the emitted constraints module.**
   `narrowed_by_url_type` asks the committed `adcp.types.constraints` what a URL type
   narrows (`TypeAdapter(chosen).json_schema()`). That is a legitimate read — the
   compiler is a consumer of that module — and it is not a defect to remove.
2. **`from adcp.types import constraints` does not go straight to the submodule.**
   The import system asks the package for the attribute first, `adcp.types.__getattr__`
   answers a name it has no submodule bound for by reaching the compat layer, and the
   compat layer is the one path in the package that pulls the whole generated graph.
   One `getattr` on a lazy facade is the whole distance between "read one module" and
   "bind 1,051".
3. **It happened three lines before the assertion that forbids it**, at `fresh.py`'s own
   module scope — so no ordering inside `tests_emit/conftest.py` could ever have helped.
   The leads in the task (a plugin, a conftest above `tests_emit/`, a stale `.pyc`,
   plugin autoload) are all ruled out by the stack: the importer is `fresh.py` itself.

## Why it looked intermittent, and why a retry always passed

`_materialised()` only calls the compiler when the key MISSES. On a hit it stats a
directory and returns — nothing imports anything, and the run is clean. So:

* the key is `tests_emit/compiled.py`'s `digest`: every `.py` under `codegen/`, plus
  `src/adcp/types/_base.py`, `src/adcp/types/_runtime.py`, `codegen/published.json`,
  plus the bundle path and the population;
* the store is **shared across worktrees** (`/srv/ws/.adcp-cache`), so *any* lane
  touching the compiler moves the key for *every* lane;
* the first run under the new key compiles → imports the committed tree → refuses, and
  in refusing still leaves the compiled pickle and the written tree behind;
* every run after it hits that entry → never compiles → passes.

That is exactly "it passes on retry every time", exactly "observed on trunk and in a
worktree that predated today's changes", and exactly why it is invisible to a lane that
edits only tests: `tests_emit/fresh.py` is **not** in the key.

A warm `make gate` loop cannot reproduce it. The condition is a cold key, which is what
the reproduction below creates with `ADCP_CACHE` rather than by editing `codegen/`
(out of scope for this row, and an edit would change the compile it is measuring).

## Reproduction counts

`ADCP_CACHE=<empty dir> make gate`, one unused cache root per run, deleted after:

| | runs | `INTERNALERROR` | make | what the gate reported |
|---|---|---|---|---|
| **before the fix** | 3 | **3 of 3**, each on run 1 | `Error 3` | nothing collected, nothing run |
| **after the fix** | 3 | **0 of 3** | `Error 1` | `7 failed, 2596 passed` |

Warm-key `make gate` on the default store, for the control: 2 runs before the fix and 1
after, 0 `INTERNALERROR` in all three (`7 failed, 2596 passed` each). That is the loop
the task proposed, and it is why the key and not the clock had to be the thing varied.

The machinery around the change is unmoved: `test_the_compile_store.py`,
`test_the_restored_machinery.py` and `test_the_tree_imports.py` report **3 failed, 31
passed** both with the fix and with `fresh.py` stashed back to trunk's — the same three,
none of them this row's (`SECOND`'s bundle `schemas/cache/3.3` is absent from this
checkout, and `test_the_compile_store.py`'s own child names `PYTHONPATH` without
`tests_emit`, so it raises `ModuleNotFoundError: No module named 'compiled'`).

**Trunk's gate result is confirmed: `7 failed, 2596 passed` of 2,603.** The owner's
prediction was right, and it is the same seven on a cold key as on a warm one:

```
core/asset-group-vocabulary.json#                        AdCPAssetGroupVocabularyRegistry
core/creative-representation.json#/allOf/0               CreativeRepresentationFormatId
core/format-shape-vocabulary.json#                       AdCPFormatShapeVocabularyRegistry
core/targeting-unknown-age-eligibility-constraint.json#  TargetingUnknownAgeEligibilityConstraint
core/targeting-verified-age-basis-constraint.json#       TargetingVerifiedAgeBasisConstraint
creative/asset-types/index.json#                         AdCPAssetTypeRegistry
extensions/index.json#                                   AdCPExtensionRegistry
```

## The fix

`tests_emit/fresh.py` only. `_materialised()` no longer calls `compiled()` and
`emit.write()` in-process; it runs them in a child interpreter (`_BUILD`, launched by
`_build`) and renames the staging directory the child wrote, exactly as before.

* **No retry, no re-exec, no `sys.modules` purge, no `--forked` flag.** The assertion
  stays, unweakened, and still fails a process that has bound the committed tree.
* **Nothing is derived twice.** The child is handed the bundle path, the staging path and
  the population; the key it computes is therefore the parent's key, and the pickle it
  leaves behind is the entry `./check` and every later in-process caller read already.
* **`PYTHONPATH` is named** (`.`, `src`, `tests_emit`, then whatever the caller had), for
  the reason `./check` states in its own preamble: the shared `.venv` carries an editable
  `.pth` naming ONE worktree, so an unnamed child would compile against a sibling
  checkout's committed `constraints` module. `cwd=REPO`, because `codegen.patch` reads
  `patches/8525` relative.
* **A compile that raises is still recorded** under `<key>.failed` for `FAILED_SECONDS`,
  now with the CHILD's traceback — which names the document that raised, where an
  in-parent traceback named `_materialised`. One narrowing: the record is written only
  for a nonzero exit, so a run the operator interrupts no longer poisons the key for two
  hours with a failure the compiler did not produce.
* **Cost: one interpreter start, on the path that was already paying a ~30 s compile.**
  A warm run does not spawn anything. Measured end to end, the gate is unchanged: the
  three cold post-fix runs took 468.6 s, 533.3 s and 557.4 s against a warm pre-fix run's
  464.0 s — and the spread is another session's `make gate` sharing the box for the last
  two, not the child process.

## Two things found on the way, neither fixed here

1. **`tests_emit/compiled.py`'s key does not cover an input the compile reads.**
   `_PACKAGE_INPUTS` names `_base.py` and `_runtime.py`; `narrowed_by_url_type` also
   reads the committed `src/adcp/types/constraints.py`, whose bounds reach the emitted
   result. A hand-edit to that module is therefore served a stale compile. It is
   deliberate that the key cannot simply glob `src/adcp/` — that module is also the
   compile's own OUTPUT, so the entry would never be hit again — so this needs a
   decision, not a line. Out of this row's write scope (`tests_emit/compiled.py`).
2. **`codegen.patch.for_build` resolves `patches/8525` relative to the working
   directory**, so the derivation fails with `FileNotFoundError: patches/8525/manifest.json`
   when a reader imports `fresh` from anywhere but the checkout root. The child process
   here passes `cwd=REPO` and is safe; a caller that is not is not. Out of scope
   (`codegen/`).
