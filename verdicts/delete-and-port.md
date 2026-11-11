# DELETE and PORT: removing the tests that grade the old generation

**What this records.** The owner's instruction was: remove the tests that grade the old
generation, keep and re-point the ones whose route is a spelling of upstream's
implementation, and keep the rest as the target. This is what was measured, what was built,
what ran, and the two things that did not.

Every figure here is from a command in this repository. Where a figure could not be
produced, this says so and names what blocked it rather than substituting a nearby one.

---

## 1. The classification reproduces, with one correction

Re-run, not trusted:

```
PYTHONPATH=.:src ./.venv/bin/python survey/upstream_test_character.py /srv/ws/wt-upbase \
    --junit /srv/ws/scratch-attribute/upstream.xml
```

The brief's figures reproduce **exactly** on the first run, before any change of mine:

| | brief | reproduced |
|---|---|---|
| DELETE | 159 functions / 924 collected | 159 / 924 |
| PORT | 370 / 800 | 370 / 800 |
| BEHAVIOUR | 9565 / 19927 | 9565 / 19927 |
| UNMAPPED | 17 collected | 17 |
| TOTAL | 10094 / 21668 | 10094 / 21668 |

One figure does not: the brief says **18,819 passed** on upstream's own tree; this junit
says **18,756**, with 62 failed, 4 errored and 2,846 skipped. 18,756 + 62 + 4 = 18,822,
which is the non-skipped total. The 63-item difference is between two runs and not between
two readings; everything below is stated over the junit named above so it is one run
throughout.

### The correction: a token in an assert's MESSAGE is not an assertion

`survey/upstream_test_character.py`'s own docstring says "THE TOKENS ARE READ INSIDE
ASSERTIONS ONLY, which is what keeps the rule honest" — and the code read
`ast.unparse(node)` over the whole `ast.Assert`, which is the claim **and the failure
message**. An `assert` carries two expressions and only the first is asserted; the second
runs when the first is false and exists to say why.

Measured: **14 test functions** carry an implementation token only in a message. The
clearest pair is `tests/conformance/reporting/test_reporting_production_lease_order.py`,
twice:

```python
assert not any(isinstance(result, BaseException) for result in results), \
    [type(result).__name__ for result in results]
```

The claim is "no task in this gather raised" — behaviour. The `__name__` that deleted it is
in the diagnostic. The same reading took `assert paths` (a public path exists), `assert not
missing`, `assert not drift`, `assert field is not None` (a `deprecated` property reached the
field), `assert alias_cls is expected`, `assert peak < IMPORT_RSS_BUDGET_MIB` and
`assert direct or through_legacy`.

`_assertion_text` now returns `(claim, whole statement)` and the token table is read over
`Assert.test`. The `assertion` column still quotes the whole statement, so a reader sees
what a reader would look at. **12 test functions move**, all out of DELETE:

| was | now | count |
|---|---|---|
| DELETE | BEHAVIOUR | 11 |
| DELETE | PORT | 1 |

After the correction:

| | before | after |
|---|---|---|
| DELETE | 159 / 924 | **147 / 659** |
| PORT | 370 / 800 | **371 / 831** |
| BEHAVIOUR | 9565 / 19927 | **9576 / 20161** |

**And the correction is corroborated by the junit.** Before it, 6 DELETE items failed on
upstream's own tree. After it, the DELETE set is **659 collected, 658 passed, 1 skipped, 0
failed, 0 errored**. Removing it therefore removes **no failure** — it takes only passing
items out of the denominator, which is the direction that makes the remaining figure harder
to earn rather than easier. A DELETE set that carried failures would be a way of hiding
them; this one cannot be.

---

## 2. The removal: derived, in the build, and a deselection

`survey/regenerate.py` gains step **5b**, after the 104 whole files step 5 already removes:

```
== 5b. the DELETE set deselected, derived
   test functions deselected: 32
   files they are spread over: 25
   test functions retained: 8133
   PORT (kept, re-pointed by the finder): 167
   BEHAVIOUR (kept, must pass): 7966
```

**32, not 147, and the arithmetic says why.** Step 5 deletes 104 test files whose *subject*
is their generator; those files hold 1,929 of the 10,094 functions, and most of the DELETE
set is among them. Over the population that is left, the DELETE set is 32 functions in 25
files. 8,133 retained + 32 deselected = 8,165 functions in the retained files; 10,094 −
8,165 = 1,929 in the 104. The 147 is the figure over upstream's whole tree and the 32 is the
incremental one; both are true and they are over different denominators.

**It is derived, never written.** `survey/upstream_test_character.py --delete-tsv` is the
only source of the list, and step 5b calls `classify()` against the tree it has just laid —
not against a recorded list — so the table deselects over the files that are *there*. That
is the discipline `population()` already follows.

**It deselects rather than excises, and §8a decides that.** `regenerate.py --audit`
classifies every file of a drop-in tree as `upstream verbatim`, `ours verbatim`, one of the
two plus a declared marker, or an EDIT — "an edit in a disposable tree is a fork beginning".
Cutting 147 functions out of 65 of upstream's files would make all 65 `UPSTREAM EDITED`, and
the audit that makes the tree checkable would report a fork of 65 files. Deselection takes
them out of the **denominator**, which is the whole of what was wanted, and leaves every
retained file byte-identical to upstream's.

`survey/dropin/deselect.py` is the plugin, copied into the tree beside the derived
`deselect.tsv` and loaded with `-p deselect`. It keys on `(path, function)`, so every
parametrisation of a deselected function goes together. Demonstrated on the built tree:

```
deselect: 3 items over 2 test functions, by survey/upstream_test_character.py's DELETE verdict
88 passed, 46 skipped, 3 deselected in 8.61s
```

A row whose **file this command collected** and whose test it did not fails the run; a row
naming a file this chunk was not given is out of scope and says nothing. Reading it the other
way made the first chunk refuse the whole table — the suite is run in four chunks and each
command sees a quarter of the paths.

### The reasons, as the table states them

147 functions over 65 files:

| count | reason |
|---|---|
| 40 | asserts pydantic's field table — their generator's representation |
| 38 | asserts an export inventory, not behaviour |
| 17 | asserts against their generated module LAYOUT |
| 12 | asserts pydantic's private machinery |
| 12 | asserts a generated class's own name rather than a value |
| 11 | asserts WHERE a type lives, which reading 6 makes ours to choose |
| 6 | asserts the ANNOTATION OBJECT their generator emitted |
| 5 | asserts a generated signature rather than a value |
| 3 | asserts on the import system's state rather than on a response |
| 2 | asserts the annotation objects their generator emitted |
| 1 | asserts against their eager generated re-export module |

Each row of `deselect.tsv` carries its reason **and the assertion that decided it**, so the
check is "open the test, read the assert, does the quoted text say what the reason says" and
not "trust the classifier".

---

## 3. PORT: the re-pointing is the finder, and no file of theirs is edited

A PORT test is behavioural and reaches its subject through `adcp.types.domains.**`,
`adcp.types._generated`, `adcp.types.aliases` or another spelling of upstream's
implementation. **The re-pointing is not an edit to their file** — for the same §8a reason
the removal is a deselection — it is `adcp.types._dropin`'s finder, which serves upstream's
own module paths out of our emitted tree. On upstream's own junit the PORT set is 831
collected items and 801 of them pass, so the route is already carried.

**No PORT test was found to need its ASSERTION changed**, which is the thing the brief said
to report rather than do quietly. The whole PORT residue on that junit is **24 items of one
parametrised function**:

`tests/test_domain_roots_import_in_any_order.py::test_each_domain_root_imports_first_and_binds_its_names`,
parametrised over `sorted(adcp.types.domains.DOMAINS)`. Its claim is that importing a domain
root first in a fresh interpreter binds every name in its `__all__` — behaviour, and its
assertion needs no change. Those 24 fail **on upstream's own tree in this junit**, so they
are not evidence about our artifact in either direction.

In our drop-in tree that same file does not collect at all: `AttributeError: module
'adcp.types.domains' has no attribute 'DOMAINS'`. That is a finding for whoever owns
`survey/dropin/_dropin.py` — the finder serves the domain modules and not the package
attribute the parametrisation reads — and it is recorded here rather than worked around.

---

## 4. The three figures

Over the one real run available, `/srv/ws/scratch-attribute/upstream.xml`, which is
upstream's suite on upstream's own tree:

| denominator | collected | skipped | ran | passed | failed | errored |
|---|---|---|---|---|---|---|
| **BEHAVIOUR** | 20,161 | 2,822 | 17,339 | **17,297** | 38 | 4 |
| **BEHAVIOUR + PORT** | 20,992 | 2,828 | 18,164 | **18,098** | 62 | 4 |
| **everything, incl. DELETE** | 21,668 | 2,846 | 18,822 | **18,756** | 62 | 4 |

The brief's "17,116 is the real target" is this table's first row: on this junit the
BEHAVIOUR denominator is **17,339 run** and **17,297 passed**. The difference between
17,116 and 17,339 is the same 63-item run-to-run difference as the total, plus the 11
functions the message-token correction moved back into BEHAVIOUR.

**What these figures are NOT.** They are upstream's suite against upstream's own types. They
state the denominator the removal produces; they do not state how our artifact scores
against it, because that run could not be produced today.

---

## 5. What did not run, and exactly why

The build completes and the tree is written (digest in `REGENERATED.json`), but a freshly
built drop-in tree does not collect. Measured on the first build: **366 of 577 behavioural
files error at collection**. Two causes were in `survey/regenerate.py` and are fixed here;
the third is not mine to touch.

**Fixed — the graft was stale against the `_surface` split.** `OURS_BESIDE_THE_EMIT` names
four modules. Since `codegen/emit.py`'s `SURFACE` split the public domain path from the
aggregator, `adcp/types/<domain>.py` is a hand-written one-line composition over
`adcp/types/_surface/<domain>.py` and the compiler does not write it — so the graft landed a
tree with no `adcp.types.core`, no `adcp.types.a2ui`. `compat.py`'s first statement is
`from adcp.types.a2ui import ...`, so the alias module raised at import, through
`adcp.types.__getattr__` → `_alias_module` → `compat`, and took 366 files with it (287 on
`a2ui`, 69 on `base`, the rest on `registry`, `legacy`, `core`, `capabilities`,
`error_narrowing`). `_copy_ours_beside` now also copies every module of ours whose body
contains `from ._surface.<its own stem> import *` — read off the file, so a 24th domain
arrives by a run reporting it. 27 files now land beside the emit instead of 4.

**Fixed — one package-root module of ours with no upstream counterpart.** Our
`adcp/types/core.py` re-exports the SDK's own client types with `from ..core import ...`,
because the ruling that keeps `adcp.types` schema-derived moved `TaskResult`, `AgentConfig`,
`Protocol` and `TaskStatus` to `adcp.core`. Upstream has no `adcp/core.py` at all.
`_copy_the_package_root_modules_they_lack` copies ours where theirs has **no module at that
path**; a name they do carry is left alone and stays their bytes. Measured on this trunk the
rule finds exactly one module.

**NOT fixed, and outside this lane's write scope — the finder does not serve
`adcp.types.base`.** With both graft gaps closed, the next import still fails:

```
src/adcp/types/_base.py:139  from adcp.types.base import AdCPBaseModel as _UpstreamBaseModel
ModuleNotFoundError: No module named 'adcp.types.base'
```

`src/adcp/types/_upstream/base.py` is in the tree and carries
`__adcp_upstream_machinery__`, and `_kept_machinery()` finds it — but under its `_upstream`
path. Mapping `adcp.types.base` onto `adcp.types._upstream.base` is a decision inside
`survey/dropin/_dropin.py`, which this lane may not edit. Until that lands, the drop-in
cannot be run and the three figures above cannot be restated against our types.

That is the one deliverable of the brief that is not here. It is not a classification
problem and not a removal problem: the removal mechanism is built, derived and demonstrated
working on the tree that exists.

---

## 6. For the verifying lane

- The DELETE list is at `<tree>/deselect.tsv`, written by step 5b. Column 3 is the reason,
  column 4 is the assertion that decided it. Regenerate it standalone with
  `survey/upstream_test_character.py <root> --delete-tsv <path>`.
- The 12 functions the message-token correction moved are listed in §1 by their claim; each
  one's `assert` has an implementation token in its message and a behavioural claim.
- `DELETE` contributes 0 failures and 0 errors on upstream's own junit. If a future DELETE
  row is found to carry a failure, that row is wrong — the set is meant to be inert.
- No file under `/srv/ws/wt-upbase` was touched; `git status` there is clean.
- Nothing under `src/` or `codegen/` was touched.
