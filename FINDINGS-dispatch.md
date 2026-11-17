# The 42 reported branches: §4's `anyOf` claim holds, so the CHECK was the defect

`tests_emit/test_union_dispatch.py::test_a_payload_the_document_admits_dispatches_to_the_branch_it_was_drawn_from`
failed on 42 entries, each reading `('core/async-response-data.json', '#/anyOf/<i>',
'no UNDERDETERMINED declared', …)`. The brief's §4 claim was to be VERIFIED before being
acted on. **It holds on all three points, measured below.** The emission is correct, the
check had no clause for the case, and the clause is now written.

**And the number the brief asked for, whatever it turned out to be: of the 42, the count
that dispatch to a branch the DOCUMENT REFUSES is `0`.** So is the count that land
outside the base's own branch list. The exemption is spent entirely on the case §4
describes, and nothing was widened to "any branch".

---

## 1. The verification, point by point

### 1a. The document is `anyOf`, not `oneOf`

Read off the bundle a run actually grades (`tests_emit/fresh.BUNDLE`, the PATCHED bundle,
not `fresh.PUBLISHED`):

```
core/async-response-data.json   keys: ['$schema', 'title', 'description', 'anyOf']   anyOf: 42
```

No `oneOf` and no `allOf` anywhere in the document. Each of the 42 is a titled `$ref` to an
operation response document (`GetProductsResponse`, `GetProductsRejected`,
`GetProductsAsyncWorking`, …), and the async envelopes share `{status, task_id}` — so
`{'status': 'submitted', 'task_id': 'a'}` satisfies many branches at once and the union is
genuinely inseparable. **CONFIRMED.**

### 1b. §4 says what the `underdetermined_census` docstring quotes

Read in both documents, not just the quote:

| document | line | text |
|---|---|---|
| `docs/plan/rebuild-plan.md` | 1219–1220 | "A union matching none of the three emits a plain `A \| B` over its branches and **declares an WIDENED approximation at the union's pointer where the combinator is `oneOf`, and nothing at all where it is `anyOf`.**" |
| `docs/plan/rebuild-plan.md` | 1225 | "`A \| B` admits the union of the branches, which is what the document admits, so **nothing widens and nothing narrows** — **for `anyOf`.**" |
| `docs/plan/rebuild-plan.md` | 722 | "A union whose branches §4's dispatch cannot separate admits exactly what the document admits where the combinator is `anyOf`, and which branch an overlapping payload becomes is a property of declaration order that nothing can observe." |
| `docs/plan/architecture.md` | 1816–1820 | "Where the combinator is `oneOf` it declares a WIDENED `Approximation` … **Where it is `anyOf` it declares nothing**: the model admits exactly what the document admits, and the only loss — which branch an overlapping payload becomes — is observable by no witness and no dump." |

The two documents agree with each other and with the docstring. **CONFIRMED.**

### 1c. `lower/union.py` declares nothing for `anyOf`, at both minting sites

Both sites are guarded on the keyword, and both carry the 2026-11-16 correction in their
own comments:

| site | guard |
|---|---|
| `codegen/lower/union.py:2016` (`lower_union`, the ROOT) | `if kw == "oneOf":` … `approximate.declare(…, kind=ir.WIDENED)` |
| `codegen/lower/union.py:3103` (`nested`, below the root) | `if kw != "oneOf": return` … `approximate.declare(…, kind=ir.WIDENED)` |

Neither site can mint anything at an `anyOf`, and `ir.WIDENED` is the only kind either
passes. **CONFIRMED.**

**So the brief is right and the emission is not the defect.** Nothing in `codegen/` or
`src/adcp/` was touched.

---

## 2. What the 42 actually are

Measured over the emitted tree (`NODESET_CENSUS`, and a direct reading of the same loop):

| | |
|---|---|
| landed on a branch other than the one drawn from | **42** |
| of those, combinator is `anyOf` | **42** (0 are `oneOf`) |
| of those, base declares `UNDERDETERMINED` | **0** |
| of those, landed OUTSIDE the base's own branch list | **0** |
| of those, the document **ADMITS** the answering branch | **42** |
| **of those, the document REFUSES the answering branch** | **0** |

The brief named one document; there are two, both bare-`anyOf` roots:

| document | combinator | of the 42 |
|---|---|---|
| `core/async-response-data.json` | 42-branch `anyOf` | 31 |
| `core/requirements/asset-requirements.json` | 12-branch `anyOf` | 11 |

Both are the same shape and the same reason, so the clause covers both without being
written for either.

Surrounding census, for the record: 149 bases declaring 605 branch models over 550
distinct branch positions — 539 naming exactly one branch class, 11 carrying several; 472
of the 539 admitted by the document at its root, 67 refused; of the 472, **430 reach the
branch they were drawn from, 42 land elsewhere the document also admits, 0 are refused by
the base.** Of the 149 bases, **131 are `oneOf` and 18 `anyOf`** — and no `oneOf` base
lands elsewhere at all.

That last figure is worth stating plainly: **the stricter `oneOf` clause is not merely
preserved, it is the one nothing currently needs.** Loosening it would have bought nothing
and cost the whole check.

---

## 3. The clause

`tests_emit/test_union_dispatch.py` only. One helper and one condition.

```python
def _owes_no_declaration(base: type) -> bool:
    return base._branch_combinator() == "anyOf"
```

```python
-            if not _underdetermined(base):
+            if not (_underdetermined(base) or _owes_no_declaration(base)):
                 wrong[where] = (…, "no UNDERDETERMINED declared", …)
```

The three conditions AFTER it are untouched, and they are where the value is:

1. the answering class must be inside the base's own `_branch_models`, transitively —
   otherwise `wrong`;
2. the **document** must admit the payload at the answering branch's own pointer —
   otherwise `wrong`, with the document's own refusal sentence in the entry;
3. only then is it `elsewhere_the_document_also_admits`.

So the question asked at an inseparable `anyOf` is *does the branch it dispatched to also
admit the payload*, which is the one question such a union can be asked, and **not** *any
branch at all*. A dispatch to a branch the document refuses stays red whatever the
combinator says.

**`oneOf` is untouched.** "Exactly one" refuses the instance that matches two branches and
`A | B` admits it, so an inseparable `oneOf` does drop a fact, does owe a declaration, and
keeps both original exits — dispatch exactly, or declare `UNDERDETERMINED`.

The combinator is read off `_branch_combinator()`, which the emitter writes onto the base,
for the same reason `_underdetermined` reads `__adcp_approximations__`: it is the TREE's
own statement of which combinator it lowered, visible to a consumer, and not this file's
second reading of the bundle.

Stale census figures in the test's docstring were corrected to the current reading while
the paragraph was being amended (151→149 bases, 609→605 branch models, 552→550 positions,
13→11 multi-class positions). No count is asserted — `tests_emit/test_every_check_names_its_set.py`
forbids pinning a census as an equality, and none was added.

---

## 4. Measurements

### `make gate` — unchanged

| | failed | passed | total |
|---|---|---|---|
| `before.json` | 7 | 2563 | 2570 |
| `after.json` | 7 | 2563 | 2570 |

**Delta: none.** The gate collects only
`tests_emit/test_the_grade_is_green.py::test_this_pair_meets_the_contract`, which this
change does not reach. It ran first time, both times — the session-start abort is fixed.

### `./check` — unchanged

```
emitted 1059 / refused 0 (deferred 0, verdict 0); accounted 1059
approximated 805 facts in 239 documents
```

Exactly the expected figures. No `codegen/` file was touched, so this is a confirmation and
not a result.

### `tests_emit/test_union_dispatch.py` — green

All **15** tests in the module pass, including the one that reported the 42. No test was
deleted and no row was removed.

---

## 5. One thing noted and NOT acted on

`_underdetermined` reads `kind == "UNDERDETERMINED"` off the base's approximations. Since
the 2026-11-16 correction, `lower/union.py` mints `ir.WIDENED` for `oneOf` and nothing for
`anyOf` — so **no base in the tree declares `UNDERDETERMINED` at all**, and that exit is
currently unreachable. It costs nothing today (no `oneOf` base lands elsewhere), but the
`oneOf` exit named in the brief is, as written, "dispatch exactly" alone.

The brief is explicit that the `oneOf` clause is the stricter case and must not be
loosened or otherwise altered, so it was left exactly as it stands. Flagging it as a
question for the owner, not filing it as a defect: whether that exit should now read
`WIDENED` is §4's call and a different lane's.
