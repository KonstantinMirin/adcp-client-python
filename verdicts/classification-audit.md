# Classification audit — the reviewer's two defects, reproduced, and the rule repaired

`verdicts/tree-diff-verification.md` §3 returned NOT CONFIRMED on
`survey/upstream_test_character.py` in both directions. Both claims are **reproduced here
rather than taken on trust** — they are a claim under test exactly as the figures they
challenge were — and both are repaired. Branch `claude/issue-b2pm-alias-note`, cut from
`ours/9.6.1` at `790004d77`.

```bash
PYTHONPATH=.:src ./.venv/bin/python survey/upstream_test_character.py /srv/ws/wt-upbase \
    --junit /srv/ws/scratch-attribute/upstream.xml
```

---

## The movement, both directions, side by side

| | DELETE fn | PORT fn | BEHAVIOUR fn | DELETE items | PORT items | BEHAVIOUR items |
|---|---|---|---|---|---|---|
| **1.** the state the reviewer measured | 159 | 370 | 9,565 | 924 | 800 | 19,927 |
| **2.** trunk `790004d77` — the claim/message repair already landed | 147 | 371 | 9,576 | 659 | 831 | 20,161 |
| **3.** + the widened token table (this row) | **153** | 371 | 9,570 | — | — | — |
| **4.** + every-assertion DELETE (this row) | **27** | **409** | **9,658** | **120** | **924** | **20,607** |

Totals are 10,094 functions and 21,668 collected items at every step, against upstream's own
junit of 18,756 passed / 62 failed / 4 errored / 2,846 skipped. UNMAPPED is 17 items at every
step and does not move.

**The two directions move against each other, which is the check that the fix is not
one-sided:** step 3 puts **6 functions INTO** DELETE, step 4 takes **126 OUT**. Net against
trunk: 120 out, 0 in — the 6 that the widened table caught are themselves mixed functions, so
the every-assertion rule releases them again. Reported as two steps rather than one net
figure for that reason.

---

## Direction 1 — BEHAVIOUR counted as DELETE. Reproduced: 12. Already repaired on trunk.

The reviewer's count is exactly right. Re-deriving it by running the token table over the
whole `ast.Assert` (claim **and** message) and comparing against the claim alone:

**12 functions carry an implementation token only in the message**, and they are the twelve
the reviewer names, including all three they call behavioural:

| | claim | the token is in |
|---|---|---|
| `test_reporting_production_lease_order.py::test_public_stores_lease_and_configuration_writer_keep_consistent_order` | `not any(isinstance(result, BaseException) for result in results)` | `[type(result).__name__ …]`, the message |
| `…::test_lease_never_waits_for_another_account_after_acquiring_one` | same | same |
| `test_import_memory.py::test_import_peak_rss_within_budget` | `peak < IMPORT_RSS_BUDGET_MIB` | `model_rebuild`, the message |

The other nine are `__all__` and export-snapshot inventories, correctly DELETE on intent and,
as the reviewer says, correctly classified **by accident of the same defect**.

**This half was already repaired between the review and now**, at `91b2323a3`:
`_assertion_text` returns `(ast.unparse(sub.test), ast.unparse(sub))` and `classify` reads
the first. That is why trunk is 147 and not 159 — exactly these 12. I have left the repair
alone and strengthened the docstring to state the rule, since the module's own prose did not
previously say that an `assert` has two expressions and only the first is asserted.

---

## Direction 2 — DELETE counted as BEHAVIOUR. Reproduced, with the counts corrected.

Scanning only the **claims** of BEHAVIOUR functions on trunk:

| construct | reviewer | re-derived |
|---|---|---|
| `model_json_schema()` | 7 | **6** |
| `model_config` | 6 | **5** |

11, not 13. The one-each difference is the claim/message repair: it had already moved a
function out of each group by the time I measured. The reviewer's reading of the constructs
is right; only the sizes moved.

**And neither construct is uniformly an implementation assertion**, which the reviewer half
anticipated ("this group needs a judgment, not a blanket token"). Reading all eleven claims:

### `model_json_schema()` — 3 of the 6 are implementation

| claim | verdict | why |
|---|---|---|
| `set(fields) == set(TargetingOverlayInput.model_json_schema()['properties'])` | DELETE | a field INVENTORY, which is `model_fields` reached through the schema export |
| `reference.model_json_schema()['properties']['agent_url']['format'] == 'uri'` | DELETE | reads the inventory to reach one emitted key |
| `SellerListCreativesRequest.model_json_schema() == canonical` | DELETE | the WHOLE emitted schema, every key the generator wrote |
| `request.model_json_schema() == get_portable_schema(…)` | DELETE | same |
| `'creatives' not in SyncCreativesRequest.model_json_schema()['required']` | **BEHAVIOUR** | a REQUIREDNESS claim: a payload omitting `creatives` is a value the document admits |
| `'budget' in PackageRequest31.model_json_schema()['required']` | **BEHAVIOUR** | same, in the other direction |

So the tokens are `model_json_schema()['properties']` (and the double-quoted spelling) and
`model_json_schema() ==`, never bare `model_json_schema`. **`['required']` is deliberately
not matched**: the owner's rule says a value the document admits or refuses is behaviour, and
requiredness is exactly that.

### `model_config` — 2 of the 5 are implementation

| claim | verdict | why |
|---|---|---|
| `"model_config = ConfigDict(extra='allow')" in updated` | DELETE | a fragment of PYTHON SOURCE asserted against a string — the text of a generated module, which the table already deletes through `inspect.getsource`, written without the call |
| `"model_config = ConfigDict(\n        extra='allow',\n    )" in updated` | DELETE | same |
| `AdCPBaseModel.model_config.get('extra') == 'ignore'` | **BEHAVIOUR** | reads the config VALUE, and ours carries that config too, so the test can pass — the burden is on declining |
| `model.model_config['extra'] == 'allow'` | **BEHAVIOUR** | same |
| `AdCPBaseModel.model_config['extra'] == _EXTRA_POLICY` | **BEHAVIOUR** | same |

So the token is `model_config = ConfigDict` — the **source spelling**, which cannot appear in
a claim except as generated text — and never `.model_config[` or `.model_config.get(`.

This corrects the reviewer on their own evidence in a way that matters: the repo note they
cite (`59112a626`, "dropping its 5 generator-text tests leaves 16 green and 1 red") is about
`test_extra_policy.py`, and only **2** of that file's assertions are generator text by this
reading. The other three read a config value our own base model also carries.

---

## The third defect, which the reviewer raised and I have acted on

> *"because of the `break`, 133 of the 159 DELETE functions carry more than one assertion
> (629 assertions in total), and the verdict comes from whichever one is hit first … it is
> not the reading the docstring describes."*

Reproduced on trunk: **120 of the 147 DELETE functions have at least one claim with no
implementation token**, and 27 have none. The most extreme is a 21-assertion function decided
by `assert 'SalesPlatform' in dx.__all__`.

**The owner's rule decides it and the direction is not optional**: *"a test is DELETE only
where there is NO behaviour behind the assertion at all … where you cannot tell, it is
BEHAVIOUR and it must pass — the burden is on declining a test, never on keeping one."* A
function asserting an export inventory AND a wire envelope has behaviour behind it. So DELETE
now requires **every** claim to carry an implementation token, and the first matching one is
quoted as the reason.

**26 of the 120 released functions assert on a payload** — `model_validate`, `model_dump`,
`pytest.raises` — which is the "hiding a real failure" direction the reviewer named, now
closed. The clearest is
`test_reporting_capability_models.py::test_core_attributes_schema_and_json_round_trip_do_not_synthesize_promises`:
**1 of its 12 claims** carries a token (`type(None) in get_args(field.annotation)`) and the
other eleven are round-trips and envelope reads. It was out of the denominator on that one
claim.

### What this costs, named rather than hidden

Of the 120 released, **38 assert `module.X is X`** and **21 assert a NAME's membership in a
collection**. Those are export-surface claims the token table does not cover, so they are now
kept and some of them will not pass.

**I did not tokenise `module.X is X`, and the reason is this package's own design.** Reading
10 makes it the defining property of an alias — *"an alias is a NAME and never a second type,
so `isinstance` holds across every spelling of one subject"* — and `docs/migration-from-upstream.md`
§12 asserts exactly that property of every one of our 1,077 alias rows. A token that deleted the
construct would decline a test our own surface is built to satisfy. Where such a test fails it
fails because we do not ship the module it imports, which is §1's machinery and a different
subject with a different remedy.

That residue is the honest cost of putting the burden on declining, and it is 59 functions
with a named construct rather than an unquantified caveat.

---

## What did not change, and why

**No allowlist.** The rule decides every one of the 10,094 functions; nothing names a test by
hand. The three tokens added are constructs, each with the reason it is an implementation
assertion, and each refusing the neighbouring spelling that is behaviour (`['required']`,
`.model_config[`).

**`model_fields_set` stays excluded** by name, inherited rather than re-decided: it mirrors a
WIRE fact — whether the key was present on the payload.

**PORT is untouched as a rule** and moves only because functions released from DELETE land in
it when their route is upstream's layout: 371 → 409, +38.

---

## The two numbers to carry forward

Against upstream's own junit (18,756 passed of 21,668 collected):

* **DELETE is 27 functions / 120 collected items**, down from 147 / 659. That is the set that
  leaves the denominator, and every row of it now has no behaviour behind any of its claims.
* **The graded denominator is 21,548 items** (21,668 − 120), up from 21,009 under the old
  rule. **We are asking to be graded on 539 more items than before**, which is the direction
  this repair should move a number that was being flattered.
