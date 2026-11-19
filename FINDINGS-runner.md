# The emission suite: what the hang is, and what the 493 reds are

**THE RECORD IS THE BEAD, AND THIS FILE IS ITS DETAIL.**
[`adcp-client-python-8cz3`](#) carries every figure below as notes — the tracker is `bd`, and
a measurement that lives only in a root `FINDINGS-*.md` is how 73% of the open P0 beads came
to carry a claim that is already false. Nothing new goes in a file like this one; what is
here is the long form of that bead's notes (the stacks, the per-file cause table) and it is
owed a `bd` append, not a successor document.

**Measured 2026-11-19 in `/srv/ws/wt-runner` (branch `claude/the-emission-suite-runs`) at
`6263d7b2e`, clean working tree, CPython 3.12.13.** Every figure below is reproducible from
the per-file artifacts the runner leaves in `test-results/emit/` (gitignored, regenerable).

## The verdict first

| | |
|---|---|
| the brief's leading suspect | `fresh.py`'s exclusive lock plus the child interpreter |
| the verdict on it | **REFUTED**, three independent ways (§1.2). `fresh.py` and `compiled.py` are **unchanged**: assertion, child process and lock all stand |
| what the hang is | **two unbounded tests in one file, back to back, at exactly the 25% mark** of 11,970 collected items — 20 m 33 s then > 14 min, both in `test_emit.py`, printing nothing |
| why `--timeout=1200` "never fired" | the `signal` method arms a **one-shot** `ITIMER_REAL`, and two things in this tree take it: `hypothesis`'s GC callback discards the exception it raises, and `codegen.harness.within` clears `ITIMER_REAL` in its own `finally`. Whether a run is cut is a race — **mine was cut at 1,233 s, the earlier one was not** (§1.3) |
| the fix | one bounded pytest process per file: `--timeout-method=thread` (a timer thread, which neither failure mode reaches) plus `timeout(1)` round the process. `make emit-suite` |
| the suite's real result | **493 failing nodes over 53 of 94 subjects; 0 hung; 41 subjects completely green.** Not "0 failing", and not 114 either (§2) |
| triage | **383 of the 493 are 9 causes**, none of them emission content; the other 110 are one finding each over 41 files (§2) |
| `ci-local` | **nothing wired yet.** The recommendation is a gate over the enumerated **GREEN** set, grow-only — the same ratchet from the side that is short today (§4) |

## §0 The exit-code trap, answered

`emit-suite` cannot have that bug, and it has two independent guards:

* the status line is `rc=$?` **taken straight off the command**, never off a pipeline — the
  recipe pipes nothing, and the Makefile carries that sentence as a comment beside the line
  so the next edit does not reintroduce it;
* the exit code is **not the reading anyway.** `EMIT_REPORT` grades each shard's
  `--json-report` JSON: every node whose outcome is not `passed`/`skipped`/`xfailed` is
  named, grouped by file, and written to `test-results/emit/suite/_red.txt`. A shard that
  left **no** report at all is a separate, louder failure (`KILLED`), because that is what a
  hang looks like once it is bounded.

The two readings agree at `6263d7b2e`: 53 subjects with a nonzero exit, 53 subjects with
failing nodes in their JSON.

## §1 The hang

### §1.1 The reproduction

```
pytest tests_emit -v --timeout=1200 -p no:cacheprovider      # collected 11970 items
```

`test_the_grade_is_green.py` alone is **5,140 items** — two parametrized readers over 2,570
pairs, and `make gate` runs one of them. Stopped by hand after **50 m 40 s at 2,894 of
11,970 items (26%)**. A watchdog sampled the process tree every 30 s and dumped `py-spy` for
every process in it whenever the log had not advanced for 120 s; 66 dumps were taken.

**`[ 25%]`, 20 m 33 s, one item.** `py-spy`, sampled three times eight seconds apart, moved
through `codegen/catalogue.py` throughout — a live walk, not a wait:

```
of (codegen/catalogue.py:1065) / key (1100) / reached (1022) / stating (1133)
admitted_identities (codegen/catalogue.py:1372)
admitted_identities (test_emit.py:495)        identity_of (test_emit.py:529)
pair_of (test_emit.py:603)
test_every_declared_fact_holds_a_value_at_its_innermost_graded_carrier (test_emit.py:1933)
```

The same test in its own process under `--timeout=600 --timeout-method=thread` was cut at
600 s inside the same frame (`digest.update(admitted.key(...))`, `catalogue.py:1372`), so it
is neither a suite interaction nor contention: the reader asks for the whole bundle's
identity catalogue **per pair**, through `pair_of` → `identity_of`, and reaches it OUTSIDE
the `harness.within(PAIR_BUDGET)` that bounds the graded path. Nothing bounds it.

**And run alone with no bound at all it still did not finish: 38 min, killed by hand
(2,296 s, `ADCP_RUN_UNBOUNDED=1`), still inside `admitted_identities`.** Three measurements,
three bounds, one frame — and 2,296 s is already past `emit-suite`'s own 1,800 s per-test
bound, so no run of this suite can carry it. That is what `UNBOUNDED` in
`tests_emit/conftest.py` records, and `ADCP_RUN_UNBOUNDED=1` is how the day it becomes finite
gets noticed.

**The next item, > 14 min, still `[ 26%]`.**
`test_the_output_is_a_function_of_its_inputs_and_of_nothing_else` spawns `python -m codegen`
over all 1,059 documents and waits in `subprocess.communicate`. Measured alone afterwards:
**1,012.3 s and green.** The next slowest test anywhere in the other 92 files is 17.7 s.

**`do_wait` with no child could not be reproduced.** 92 `wchan` samples over the run: 52
running, 39 in `communicate`'s `poll`, 1 `wait_woken`, **0 `do_wait`**. The second silent
test is nonetheless where a sampler would read one — `capture_output` keeps the parent in
`selectors.poll` for most of the wait and in `waitpid` at the end of it — and `wait4` with no
eligible child returns `ECHILD` rather than blocking, so the two halves of that observation
were most likely not sampled at the same instant.

### §1.2 The named suspect, refuted

1. **`fcntl.flock` occurs in exactly one file in the tree.**
   `grep -rn "flock\|lockf\|LOCK_EX" codegen/ src/ tests_emit/ scripts/ check verify` returns
   `tests_emit/fresh.py` and nothing else. There is no second lock for a child to want.
2. **The build child binds neither `fresh` nor `conftest`.** `_BUILD`'s whole import surface
   is `compiled` and `codegen.emit`; run with the parent's own `PYTHONPATH`,
   `[m for m in sys.modules if m in ("fresh", "conftest")]` is `[]`. A process that never
   imports `fresh` never calls `_materialised` and never reaches the lock.
3. **`codegen/` contains no `subprocess`, no `fork` and no lock at all**, so the only process
   the lock window can create is `_build`'s own child, and (2) covers it.

And the store was **warm**: `_materialised()` returns in 0.65 s and the tree is present, so
the serial run never entered the lock window after session start. The hang reproduced anyway.

### §1.3 The backstop is a coin flip, which is the part worth keeping

`pytest-timeout`'s default method is `signal`: one `signal.setitimer(ITIMER_REAL, timeout)`
per item. Two things in this tree take it away, both already written down here:

* **`hypothesis` swallows it.** `codegen.harness.within`'s docstring: *"a one-shot
  `signal.alarm` does not bound anything, because the signal can land in a context where
  Python DISCARDS the exception it raises … `hypothesis` installs one
  (`junkdrawer.gc_callback`). Measured: a one-shot alarm fired twice inside that callback,
  was ignored both times with "Exception ignored in", and the pair then ran 13 minutes
  against a 45 s budget with no alarm left to fire."*
* **`within` clears it.** A process has **one** `ITIMER_REAL`. `within` installs its own
  timer on entry and does `setitimer(ITIMER_REAL, 0)` in its `finally` — correct for its own
  budget, and it also cancels whatever the plugin armed for the enclosing item.

So "it never fired" and "it fired at 1,233 s" are the same mechanism seen from either side of
a race. `--timeout-method=thread` has neither failure mode: a `threading.Timer` dumps every
thread's stack and calls `os._exit(1)`. Measured on both unbounded tests — cut on time, with
the test and the line named. One cost, stated: `os._exit` skips `subprocess` cleanup, so a
cut orphans the `python -m codegen` child it was waiting on (it finishes on its own in
minutes); `timeout(1)`'s own kill goes to the process group and does not.

### §1.4 The fix, and what it costs

`make emit-suite`: one pytest process per subject, `EMIT_JOBS=6` at a time, each bounded by
`--timeout=1800 --timeout-method=thread` and by `timeout -k 10 2700`. The subject list is a
**wildcard** over `tests_emit/test_*.py`, so a file added later is run without anyone
remembering — the half `test_union_dispatch.py` did not have when `8e64bafe5` broke it — plus
`test_the_grade_is_green.py::test_this_pair_has_no_undeclared_approximation`, the 2,570 pairs
no target ran before this row. `make gate` keeps the other half and **does not move**.

| | before | after |
|---|---|---|
| invocation | `pytest tests_emit --timeout=1200` | `make emit-suite` |
| result | **did not report**: 26% of 11,970 items in 50 m 40 s, stopped by hand | **9,400 collected, 493 failed, 8,649 passed, 257 skipped, 1 xfailed, 0 hung, in 1,391 s** -- every subject reported |
| longest silence | **20 m 33 s** at `[ 25%]` | bounded per test and per file |
| a hang is attributable to | nothing — one process, one exit code | one subject, by name, in its own `.status`, with the stack in its `.log` |
| the other 93 subjects when one hangs | not run | run and reported |

The one node this suite does not run is named in `tests_emit/conftest.py`'s `UNBOUNDED` with
its measurement, marked `xfail(run=False)` so it is **reported as `XFAIL [NOTRUN]`** rather
than deselected into invisibility, and `ADCP_RUN_UNBOUNDED=1` runs it anyway — a bound nobody
can re-measure is a bound nobody can delete. It is a bound, not an allowlist: there is no
list of defects anywhere in `conftest.py`.

CPU cost, honestly: 92 files are **2,344 s of CPU** between them and `test_emit.py` is a
further 1,201 s, so one process per file pays one interpreter start, one `codegen` import and
one 76 MB unpickle per file instead of once for the suite. The two long poles are started
first because `xargs` starts subjects in the order given.

## §2 The suite's real result, and every file's cause

**493 failing nodes over 53 of 94 subjects, 0 hung, 41 subjects completely green.**
`test-results/emit/suite/_red.txt` names every one. Measured twice, independently: once by a
hand-driven per-file sweep and once by `make emit-suite` itself, and the two agree node for
node -- 9,400 collected, 493 failed, 8,649 passed, 257 skipped, 1 xfailed, 1,391 s wall at
`EMIT_JOBS=6`, of which `test_emit.py` alone is 1,390 s.

The brief's premise ("93 of 93 files pass individually, 0 failing") does not hold at this
commit, and neither does 114: the gap is `test_emit.py` (91, and no 420 s cap can reach it —
one of its tests is 1,012 s) and the grade file's approximation half (21, which no target has
ever run).

### §2.1 The nine causes — 383 of the 493

| nodes | files | cause | what clears it |
|---|---|---|---|
| **156** | 2 | **no `<version>.provenance.json` beside the bundle.** 34 bundle directories are committed and **not one** record exists, including `3.2`'s — the bundle every verdict in this repository rests on | §3: scope the obligation, do not invent 31 records |
| **69** | 14 | **a synthetic bundle a reader writes into `tmp_path` carries no `manifest.json`**, which `codegen/bundle.py:2449` requires (*"no task registry names which documents are requests and which are responses"*). Landed with `4cb78fd2c`; the fixtures predate it | one shared writer that writes a minimal manifest, and 14 call sites. Each writer is private to its file today (`test_fragment_ref.write_bundle` is imported by one other file) |
| **53** | 1 | **`OmittedNotNull` on a property whose document ADMITS an explicit null.** 53 of the 54 in one test, one direction. The decision index settles it: the marker is for *"a property outside `required` whose type does NOT admit `null`"*, and e.g. `aao/agent-publishers.json` `manager_domain` is `"type": ["string","null"]` and not required. The class refuses a null its document admits — an undeclared **narrowing** | one lowering fix in `codegen/`; the 53 are its sites |
| **35** | 2 | **a path named in prose does not resolve or cannot be checked** — `src/adcp/client.py` names `adcp.idempotency.replay_ttl_seconds`; 12 more spell a placeholder (`adcp.types.registry.<word>`) that no import can check | mechanical text fixes |
| **17** | 7 | **a stale symbol: the reader names what the tree no longer has** — `codegen.harness.Fixtures`, `check_accepts(examples=…)`, `test_emit.FORMAT_STRATEGIES`, `codegen.constraints._digest`, `adcp.types.compat.__adcp_provisional__` | rename to the live symbol |
| **12** | 5 | **`schemas/cache/3.3` is absent.** It is `fresh.SECOND`; `FINDINGS-flake.md` already recorded the absence | fetch the bundle, or scope as §3 |
| **9** | 1 | **`core/creative-representation.json#/allOf/0`'s branches emit nothing** — and `core/creative-representation.json#/allOf/0 CreativeRepresentationFormatId` is **already one of `make gate`'s own 7**, so this is one defect counted in two targets | the gate's existing 7 |
| **6** | 1 | **the type-checker gate's own invocation is broken in this tree** — `KeyError: 'files'`, `usage: mypy [-h]…` | fix the invocation |
| **26** | 6 | **an approximation or a narrowing the run does not declare.** 15 are the grade file's approximation half: 8 `admits=fail:model_refused_admitted` (class narrower than its document, on `anyOf` and `url_parsing`), 7 `widening=fail:unproved_widening` | declarations, per `CLAUDE.md`'s rule that the defect is the missing `WIDENED`/`NARROWED`/`UNDERDETERMINED` |

**Three corrections to the triage in the brief, all from reading the messages rather than the
file names:**

* `test_fragment_ref` — **19 of its 20 are the `manifest.json` cause**, not the
  field-annotation key set. Exactly **one** node is `('adcp_major_version', ['deprecated', 'description'])`.
* `test_emit_product` — **13 of its 16 are the same `manifest.json` cause.** The
  reference-closure document list is **one** node, and the other two are `('contains', '$ref')`
  and `({'type': 'string'}, 'type')`. So "not obviously mechanical" is right about one node,
  not sixteen.
* `test_refuses_check` — **9 of its 10 are `AttributeError: codegen.harness has no attribute
  'Fixtures'`**, a stale symbol. Only **one** is the `RefusesResult` row shape the localise
  lane owns. That one is still theirs; the nine are not.

### §2.2 Every file, assigned

Cause numbers are §2.1's rows in order (1 provenance, 2 manifest, 3 OmittedNotNull, 4 prose,
5 stale symbol, 6 creative-representation, 7 type-checker invocation, 8 bundle 3.3,
9 undeclared approximation); `own` is a finding of its own, with its message.

| file | nodes | causes |
|---|---|---|
| `test_a_bundle_states_which_upstream_it_is.py` | 158 | 155×1, 1×8, 2×own (`['README.md']`, `['manifest.json.orig']` — the bundle holds two non-JSON files) |
| `test_emit.py` | 91 | 53×3, 5×2, 4×9, 3×5, 26×own (class/branch/alias emission findings, one each) |
| `test_prose_resolves.py` | 45 | 33×4, 12×own (a `:role:` cross-reference resolving to nothing — same family, different reader) |
| `test_the_grade_is_green.py` | 21 | 15×9, 6×own (one bookkeeping failure each) |
| `test_fragment_ref.py` | 20 | 19×2, 1×own (`('adcp_major_version', ['deprecated','description'])`) |
| `test_emit_product.py` | 16 | 13×2, 3×own (the reference closure, `('contains','$ref')`, `({'type':'string'},'type')`) |
| `test_refuses_check.py` | 10 | 9×5, 1×own (the `RefusesResult` rows — the localise lane's) |
| `test_a_branch_the_document_empties.py` | 9 | 9×6 |
| `test_cells.py` | 9 | 9×2 |
| `test_dump_exemptions.py` | 8 | 3×9, 1×5, 4×own (two exempt pointers emitting one class twice) |
| `test_the_second_bundle.py` | 7 | 7×8 |
| `test_a_property_that_admits_nothing.py` | 6 | 6×2 |
| `test_type_checker.py` | 6 | 6×7 |
| `test_applied_schema.py` | 4 | 2×2, 2×own (local-reference sites 772 below a floor of 774; one pointer reached twice) |
| `test_approximation.py` | 4 | 1×5, 3×own (a refusal message and an `additionalProperties` pointer) |
| `test_enum.py` | 4 | 1×9, 3×own (`Format`/`LegacyFormat` export set, a root enum identity, `motion_level`) |
| `test_required_with_no_declaration.py` | 4 | 3×2, 1×own (`core/format.json`'s `$defs` required sets) |
| `test_the_verdicts_are_green.py` | 4 | 2×9, 2×own (`verify.json` stale against the graded inputs; the admits check never put to 17 pairs) |
| `test_union_disjointness.py` | 4 | 2×2, 2×own (an empty derivation set — vacuous assertions) |
| `test_a_patched_bundle_says_it_is_patched.py` | 3 | 1×1, 1×8, 1×own (the published bundle's own record is the grounding) |
| `test_a_record_states_one_id.py` | 3 | 2×8, 1×2 |
| `test_decision_set.py` | 3 | 2×2, 1×own (two cited upstream issues nobody has looked up) |
| `test_import_rule.py` | 3 | 3×own (`constraints.py` imports `pydantic` past §8's layer; `overrides.py` raises `OverrideRefused`; the walk's model-layer reads) |
| `test_readme_executes.py` | 3 | 2×4, 1×own (python fence 0 exits 1) |
| `test_ref_branch_union.py` | 3 | 3×2 |
| `test_the_kept_machinery_imports.py` | 3 | 3×own (`adcp.types` does not carry `CreditLimit`; one of 100 importers cannot import) |
| `test_conj_rule_beside_a_type.py` | 2 | 2×own (one site claimed by two shapes of the partition) |
| `test_inner_facts.py` | 2 | 2×2 |
| `test_keywords.py` | 2 | 2×own (the committed grids are stale — `--write-grids`; a keyword collection outside the table) |
| `test_nested_union_sibling.py` | 2 | 1×2, 1×own (3 composing nested-union sites unmeasured) |
| `test_one_node_is_one_declaration.py` | 2 | 2×own (`adagents.json#/oneOf/1/…/allOf/0` declares two classes) |
| `test_the_bundle_a_module_reads.py` | 2 | 2×own (a module reaches a bundle `fresh.py` does not declare; an entry forcing nothing) |
| `test_the_compile_store.py` | 2 | 1×8, 1×own |
| `test_the_domain_surface.py` | 2 | 2×own (two declarations of one domain want one name; the untitled-inner-node rule) |
| `test_the_invented_default_set.py` | 2 | 2×own (a default for a field the conjunction requires; the adapter refuses a resolving name) |
| `test_the_name_override_table.py` | 2 | 2×own (`adcp.types.core.Format` and `CreativesItem` are no longer exported) |
| `test_the_resolving_spellings.py` | 2 | 1×5, 1×own (the derivation produces rows §12 does not carry) |
| `test_the_restored_flat_surface.py` | 2 | 2×own (four legacy-asset helpers absent) |
| `test_the_surface_exports_something.py` | 2 | 2×own (`adcp.types.guards` exports nothing) |
| `test_the_wheel_is_the_artifact.py` | 2 | 2×own (`_compliance/3.2.0-rc.4/` files in the wheel; a name the alias layer does not decide) |
| `test_union_dispatch.py` | 2 | 2×own (**the localise lane's two**: `DID NOT RAISE ValidationError`, and a refusal that stopped naming what it refused) |
| `test_an_asserting_override_may_only_narrow.py` | 1 | 1×2 |
| `test_catalogue.py` | 1 | 1×own (`['EmailAddress']` carries a digest or an index) |
| `test_every_check_names_its_set.py` | 1 | 1×own (two checks pin a census beyond the ratchet) |
| `test_every_upstream_name_resolves_or_is_noted.py` | 1 | 1×own (61 of upstream's 1,197 published names resolve nowhere and are not noted) |
| `test_immaterial_presence.py` | 1 | 1×5 |
| `test_scratch_is_on_disk.py` | 1 | 1×own (`.adcp-scratch`) |
| `test_the_adapter_writer_owns_its_paths.py` | 1 | 1×own (the table records restored paths the bytes do not) |
| `test_the_alias_layer_is_names.py` | 1 | 1×5 |
| `test_the_declared_backlog.py` | 1 | 1×9 |
| `test_the_hierarchy_is_preserved.py` | 1 | 1×own (branch classes with no dispatching base at the union's pointer) |
| `test_the_restored_machinery.py` | 1 | 1×own (the flat surface hands back `adcp.core`'s own objects) |
| `test_the_run_writes_its_verdicts.py` | 1 | 1×own (one verdict row's spelling) |

## §3 The provenance obligation: scope it, do not write 31 records

**The shape I recommend, and the argument.** `test_a_bundle_states_which_upstream_it_is.py`
ranges over **every** directory under `schemas/cache/` and asks each for a
`<version>.provenance.json`: 5 readers × 31 recordless snapshots = 155 of the suite's 493
reds, the largest number in it and the least meaningful.

**Writing the 31 records is the wrong fix, and not because it is work.** The record's own
content is the argument: it names *a commit and the commands that made the bundle* (plus a
digest and a document count). For a snapshot of `3.1.0-rc.4` sitting in the cache, the digest
and the count are derivable and **the commit and the commands are not** — nobody knows them
now. A record written anyway is an invented provenance claim, which makes the gate green by
fabricating the one fact it exists to check. `codegen/patch.py`'s rule about an exclusion that
excludes nothing is the same rule one layer out: a record that grounds nothing is worse than
an absent one, because it reads as grounding.

**Scope it to the bundles a run reads, and the suite already declares that set.**
`tests_emit/fresh.py` names exactly three — `PUBLISHED` (3.2), `BUNDLE` (its patched
derivation) and `SECOND` (3.3) — and
`test_the_bundle_a_module_reads.py::test_every_bundle_a_test_module_reads_is_one_tests_fresh_declares`
already makes that the one place a bundle set is declared. A snapshot nothing compiles grounds
no verdict, so the obligation over it is vacuous; the obligation over the three is not.

**And scoping does not make the finding go away — it makes it land.** There is no record for
`3.2` either. So the honest reading of these 155 is **one red, not 155**: *the bundle every
verdict in this repository rests on has no provenance record*, which is both actionable (3.2
is the bundle the repo downloads and patches today, so its commit and commands are knowable)
and currently drowned 155 to 1 by snapshots that predate the rule.

Concretely, and all of it inside `tests_emit/test_*.py`, which is not this row's to write:

1. `provenance.bundles()` returns the DECLARED set (`fresh.PUBLISHED`, `fresh.BUNDLE`,
   `fresh.SECOND`) instead of globbing `schemas/cache/*`; 155 reds become ≤ 15.
2. The recordless snapshots keep the one obligation that needs no invented fact — *the
   directory holds nothing but JSON documents* — which is already a separate reader in that
   file and already green.
3. The record for 3.2 gets written, from the fetch that produced it. That is the red worth
   having.

If the owner prefers the 31 records anyway, the thing that makes them honest is a field that
says the provenance is **unknown** rather than a commit nobody verified — at which point the
reader has to accept that value, and the obligation has been scoped after all, in a less
readable place.

## §4 What `ci-local` should run — and why the list should be the GREEN one

**Nothing is wired into `ci-local` in this row.** `make emit-suite` exists, is bounded, and
reports; `ci-local` is unchanged.

**An enumerated list of 493 reds is a second backlog, and so is a list of 199.** Clearing the
five mechanical causes (2, 4, 5, 7, and scoping 1 and 8) removes **294 nodes without touching
one emission decision** — and leaves **199 over ~45 files**: 53 `OmittedNotNull`, 26
undeclared approximations, 9 `creative-representation`, and 110 individual findings. That is
not a short list either, and freezing it as an allowlist would park the suite's real content
behind a file nobody reads.

**So invert the ratchet.** `ci-local` should carry **the enumerated set of subjects that pass
completely, and that list may only GROW**:

* **41 of the 94 subjects are green today** — `make emit-suite` names them, and after the
  mechanical work it is ~50.
* A gate over that set contains **no defect allowlist at all**. It says *these files pass and
  may not regress*, which is exactly what `8e64bafe5` needed and did not have:
  `test_union_dispatch.py` was green at `27192ec6d`, and a green-set gate would have caught
  the merge that took it to 2 failed.
* A new red in a listed subject fails `ci-local`. A red in an unlisted one is in the backlog
  this document carries, by cause, with its count — and a subject joins the list the day it
  goes green, which is the only direction that cannot rot.
* The **subject** list of `emit-suite` stays a wildcard, so a file added later is still run
  and reported; what is enumerated is which subjects are *graded as a gate*.

Staged, that is: (1) this row — the bounded, attributing runner, nothing in `ci-local`;
(2) one change per mechanical cause, no allowlist anywhere; (3) `ci-local` gains
`emit-suite --green-set`, enumerated and grow-only; (4) the 199 stay in this document, by
cause, until they are fixed or declared.

## §5 What I did not do

* **`fresh.py` and `compiled.py`: untouched.** The deadlock is not there.
  `FINDINGS-flake.md`'s two open findings (the compile key omitting
  `src/adcp/types/constraints.py`; `codegen.patch.for_build` resolving `patches/8525`
  relative to the working directory) are both still open and neither is reachable from this
  hang.
* **No CI workflow job.** Any enumerated set — green or red — is measured on **one**
  interpreter here, and CI runs 3.10–3.13. The measurement is owed per version first.
* **No `tests_emit/test_*.py` and no `codegen/` edits**, so every fix §2 and §3 name is a
  recommendation and not a change. The two in `test_union_dispatch.py` and the one
  `RefusesResult` row in `test_refuses_check.py` are the localise lane's.
* **The two slow tests are not fixed.** `test_the_output_is_a_function_of_its_inputs_and_of_nothing_else`
  is 1,012 s and green — expensive but correct. The identity reader is the one node the suite
  does not run, and the fix is in `codegen/catalogue.py` or `test_emit.py`:
  `admitted_identities` is asked for the whole bundle **per pair** where the graded path asks
  for it once, under a budget.
