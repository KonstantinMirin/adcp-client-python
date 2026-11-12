# The edited upstream test files: enumeration, classification, and the change the audit needs

Written for the lane that owns `survey/regenerate.py`. Nothing here is a fix — the reviewer
does not fix. Every figure is re-derived at `ours/9.6.1` = `d33ee388c` against upstream
`4ed0bce87`, both worktrees clean.

**The question this settles.** `survey/dropin/deselect.py:27` states *"UPSTREAM'S SUITE
STAYS BYTE-IDENTICAL. Nothing is edited under `tests/`."* `survey/regenerate.py:989` states
that an edit in a disposable tree *"is a fork beginning, which §8a says can only be deleted
and regenerated."* Section 2 of `verdicts/tree-diff-verification.md` found 41 edited
`test_*.py` files. The answer is **both halves are true at once, of two different trees**:

* the docstring is **false as written** about `tests/` in *this* repository — 44 files are
  edited there, by six named commits;
* the audit is **not wrong, it is blind** — `--audit`'s subject is the regenerated drop-in
  tree, whose `tests/` is taken from upstream's git revision, so these 44 files are not in
  the tree it inspects. Nothing in `survey/` compares our `tests/` to upstream's bytes.

So the edits are neither "a fork the audit called" nor "an edit the audit excused". They
are **unaudited**, in a tree no instrument ranges over, and that is the gap to close.

---

## 1. The enumeration — 44 files, six commits, no hand drift

`git ls-tree` over both revisions: 44 paths under `tests/` that exist in both and differ in
bytes. (Section 2 of the verification said 41; that figure was `test_*.py` only. The other
three are `tests/conformance/_round_trip.py` and two under `tests/type_checks/`.)

Every one of the 44 is attributable. `git log 4ed0bce87..HEAD -- <path>` returns at least
one of exactly six commits, and no file carries an unattributed change:

| commit | subject | files |
|---|---|---|
| `6c140f352` | fix(tests): the envelope's `status`, on the 97 sites the class resolves to | 23 |
| `280c6f443` | fix(tests): library types come from adcp, schema types from adcp.types | 13 |
| `f2660c76a` | fix(tests): the class each fixture names, and the fields the document requires | 6 |
| `59112a626` | test: the tests whose subject was deleted go with it, each one named | 5 |
| `d28f93607` | fix(tests): status is required, and the document says so independently | 3 |
| `24e92acc8` | fix(tests): major_versions is a list of ints, because the schema says so | 3 |

**Who made them: none of the three candidates the brief offers.** Not `regenerate.py`'s
substitution step — that writes `src/`, never `tests/`, and the PORT verdict is served at
*runtime* by the meta-path finder `survey/dropin/_dropin.py` ("PORT (kept, re-pointed by the
finder)", `regenerate.py:578`), so a port costs no byte in a test file. Not surviving hand
drift — every edit lands in a dated commit with a derivation, and four of the six name the
script that produced them (`scripts/add_required_status_to_fixtures.py`,
`scripts/relayer_client_type_imports.py`, and the generalisation of the first in
`f2660c76a`). They are deliberate, scripted, reasoned edits to this repository's copy of
upstream's suite.

---

## 2. The classification

| class | files | what it is |
|---|---|---|
| **(a) mechanical and derivable** | **10** | an import re-pointed, nothing else changed |
| **(b) a changed payload** | **29** | a document-required field added to a construction |
| **(c) other** | **5** | test functions removed with their deleted subject |

### (a) Import re-point — 10 files, legitimate by the owner's rule

`280c6f443` only, and the whole diff of each of the ten is one or two import lines:

```python
-from adcp import ADCPClient, ADCPMultiAgentClient, get_adcp_spec_version
-from adcp.types import AgentConfig, Protocol
+from adcp import ADCPClient, ADCPMultiAgentClient, AgentConfig, Protocol, get_adcp_spec_version
```

```
integration/test_a2a_context_id.py            test_adcp_version_option.py
integration/test_reference_agent_webhooks.py  test_adcp_version_wire.py
integration/test_reference_agents.py          test_beta6_reporting_version.py
test_compact_lifecycle_matrix.py              test_property_lists.py
test_schema_validation_client.py              test_update_rights_roundtrip.py
```

The premise that moved is a **module path**, which is the one thing the owner's rule permits
an edit for. The commit's own argument is stronger than "it fails otherwise": upstream's own
`tests/test_public_api.py::test_client_types_are_exported` — unedited — already asserts
`adcp.AgentConfig` and `adcp.Protocol` on the top-level package, so the rewrite moves these
imports *toward* upstream's stated contract. It is also keyed on what fails to resolve rather
than on the word, which is what stops `TaskStatus` (resolvable in both, to different classes)
being swapped under a passing test.

**Verdict: legitimate.** This is the class that needs a declared marker so an audit stops
reading it as a fork (§3 below). One caveat for the owning lane: in the drop-in tree the
finder already serves these spellings, so the edit is needed *only* in our own `tests/`. Two
mechanisms now do the same job in two trees, and only one of them is declared.

### (b) A changed payload — 29 files, and this is the finding

`6c140f352` + `d28f93607` + `f2660c76a` + `24e92acc8`. **109 added lines supply a value to a
construction.** The dominant form, repeated across 23 files with an identical three-line
comment:

```python
     provisional = CreateMediaBuySuccessResponse(
+        status="completed",
         media_buy_id="mb_1",
```
`tests/test_create_media_buy_response_types.py::test_confirmed_at_accepts_null_and_stays_required`

```python
             async def handle_si_get_offering(self, request, context=None):
-                return SiGetOfferingResponse()
+                return SiGetOfferingResponse(status="completed", available=...)
```
`tests/test_server_framework.py::TestSponsoredIntelligenceHandler.create_concrete_handler`

and from `f2660c76a`'s ADD remedy, values that are not `status` at all — `verdict="approved"`,
`outcome_state="accepted"`, and `const` values for `authority`, `media_type`,
`schema_version`, `asset_type` (12 constructions across 4 files).

The 29: `conformance/signing/test_autosign_e2e.py`, `…/test_autosign_hook.py`,
`test_account_lifecycle.py`, `test_beta3_url_constraints.py`, `test_capabilities.py`,
`test_client.py`, `test_create_media_buy_response_types.py`,
`test_decisioning_async_discovery.py`, `test_decisioning_brand_authz_dispatch.py`,
`test_decisioning_buyer_agent_dispatch.py`, `test_decisioning_handler.py`,
`test_decisioning_refine.py`, `test_delivery_manifest_readback.py`,
`test_discriminated_unions.py`, `test_feed_mirror.py`, `test_get_products_projection.py`,
`test_implementation_config.py`, `test_media_buy_context_echo.py`,
`test_mixed_legacy_projection_regression.py`, `test_preview_html.py`, `test_public_api.py`,
`test_rootmodel_proxy.py`, `test_server_dx.py`, `test_server_framework.py`,
`test_simple_api.py`, `test_type_coercion.py`, `test_typed_handler_params.py`,
`type_checks/handler_three_branch_return.py`, `type_checks/response_envelope_fields.py`.

**Why it is a finding, stated against the rule rather than against the intent.** The rule is
that a behavioural test may be edited only where its *premise* is wrong — a class name or a
module path — and that its payload and its expectation may not be edited to make it pass. A
field added to a construction is a **payload**. It is not a name and it is not a path. Every
one of these edits is therefore outside the permission, however well-grounded the reason is.

And the reasons *are* well-grounded — this is not sloppiness and should not be reported as
such. `core/protocol-envelope.json` does carry `required: ["status"]`; every response
document does compose it through `allOf`; `d28f93607` established that against the raw
documents with `jsonschema` and a registry over `schemas/cache/3.2` rather than against our
own IR, which is the right instrument; `6c140f352` resolved each callee through its file's
own lexical bindings and *dropped* 215 of 321 name-matched sites rather than editing them,
including 60 where adding `status` "would have been nonsense". The derivation is careful.

The defect is categorical, not evidential: **the mechanism for "upstream's fixture omits a
field the document requires" already exists and is not an edit.** It is the deselect list —
`survey/dropin/deselected-9.6.1.tsv`, whose `collapsed-disjunction` and `invented-value`
kinds are exactly this shape, and whose own docstring says a test that depends on upstream's
generator's laxness "cannot pass against any implementation that honours the document" and
so leaves the denominator with its reason recorded. These 109 sites took the other road:
they repair the fixture in place so the test stays in the denominator and passes. That is a
larger claim about our artifact than the deselect list makes, and it is made in a tree the
audit does not read.

Two further consequences the owning lane should weigh:

1. **The figure moves.** A test that passes because we edited its fixture is counted in
   "18,819 passed" beside tests that pass untouched. The junit cannot tell them apart, and
   neither can `upstream_test_character.py`, whose PORT bucket (800 items) is about *route*,
   not about whether the file was edited.
2. **The direction is safe, which is the one piece of good news.** Measured over all 44
   files: **0 assertions added, 0 assertions changed.** The 13 removed assertion lines are
   all inside functions removed by `59112a626`, except one in `test_native_ci.py` that names
   a deleted file. So no expectation was weakened; only inputs were completed. That is the
   difference between this and the failure mode the rule exists to prevent, and it is worth
   stating in whatever disposition the owner chooses.

### (c) Other — 5 files, function removals

`59112a626` only: `conformance/_round_trip.py` (drops an `adcp.types._eager` import and its
comment, a support module with no tests), `test_account_reference_request_fields.py` (−2
functions), `test_lazy_rebuild.py` (−1), `test_literal_discriminator_defaults.py` (−4),
`test_native_ci.py` (−1 assertion naming the deleted `tests/test_versioned_bases.py`). All
five are named in that commit's REWRITE/REPOINT sections with the subject each depended on,
and `verdicts/tree-diff-verification.md` §2 confirmed those reasons hold. Not edits-to-pass;
deletions of dead-subject statements inside surviving files. **Legitimate, already declared
— in a commit message rather than in data, which §3 addresses.**

---

## 3. What the audit needs, exactly

### 3.1 The reason it reports nothing today

`regenerate.py:983 audit(tree, rev, ours)` classifies the files of a **drop-in tree**. That
tree's `tests/` comes from upstream's git revision — `verify_revision` exists precisely to
license taking the suite from git by proving the revision's `src/adcp/**` is the wheel's
("0 disagreements means the revision's `tests/` is the wheel's own suite"). Our `tests/` is
never copied in. Measured, `--audit dropin/9.6 --rev 4ed0bce87 --ours HEAD`:

```
upstream verbatim 37,408 | ours verbatim 1,028 | UPSTREAM EDITED 17
OURS EDITED 1,187 | AUTHORED THERE 7,354
```

and of those 17 UPSTREAM EDITED exactly **one** is under `tests/`
(`tests/fixtures/public_api_snapshot.json`). None of the 44 appears, because none of them is
in that tree. **The audit is honest about its subject; its subject is the wrong tree for
this question.**

### 3.2 A latent ordering defect that becomes live the moment the subject changes

`audit()`'s branch order is:

```python
if theirs_path in theirs and theirs[theirs_path] == blob:   -> upstream verbatim
elif path in mine and mine[path] == blob:                   -> ours verbatim      # <-- 2nd
... marker branches ...
elif theirs_path in theirs:                                 -> UPSTREAM EDITED    # <-- 6th
```

For any path upstream owns whose bytes we have edited, branch 2 matches — the file *is* ours
verbatim, because ours is the edited copy — and the UPSTREAM EDITED branch is never reached.
So an audit pointed at any tree built from our `tests/` would classify all 44 as **"ours
verbatim"**: the most reassuring label in `PROVENANCE`, on exactly the files that are a fork
beginning. This is a reading of four lines, not a run; today it is masked only by the fact
that no such tree is built.

**Change 1 (correctness, independent of everything else).** Test upstream provenance first.
If `theirs_path in theirs`, the only honest outcomes are `upstream verbatim`, `upstream plus
the machinery marker`, a *declared* edit (change 3), or `UPSTREAM EDITED`. `ours verbatim`
must be reachable only for paths upstream does not carry.

### 3.3 The audit our `tests/` does not have

**Change 2.** Give `audit()` a second subject: this repository's own `tests/`, compared to
upstream's revision. Nothing else in `survey/` makes that comparison, and without it
`deselect.py:27`'s sentence has no instrument behind it — which is how 44 files were edited
across six commits without a single figure moving. The existing function already does the
work; it needs `tree="HEAD"` to be a supported subject with change 1 applied, and the
`tests/` subtree is the population to report over.

Expected output on today's tree, if both changes land: `upstream verbatim` 606 (+ non-`.py`
paths), **`UPSTREAM EDITED` 44**, with the 44 named.

### 3.4 The declared marker for the class that deserves one

**Change 3.** `(a)` is legitimate and must stop reading as a fork; `(c)` is legitimate and is
declared only in a commit message. Both want the shape this repository already uses for
declared data — `survey/dropin/upstream-tests-about-their-generator.txt`, which
`regenerate.py` refuses to build against if a declared path is not a file of upstream's.

Proposed: `survey/dropin/upstream-tests-edited-here.tsv`, one row per edited path:

```
path                                   class            commit      reason
tests/test_adcp_version_option.py      import-repoint   280c6f443   AgentConfig/Protocol are library types; upstream's own test_public_api asserts them on `adcp`
tests/test_lazy_rebuild.py             function-removal 59112a626   the removal hook is deleted; 1 function removed, 8 remain
```

with two gates, both the same shape `drop_their_generator_tests` already enforces:

* every path listed must be a file of upstream's revision, else the build stops;
* every path the `tests/` audit calls `UPSTREAM EDITED` must be listed, else the build stops.

The second gate is what makes the declaration honest: a new edit cannot be added without a
row, and a row cannot outlive its file. The audit then reports `declared edit (import-repoint)`
and `declared edit (function-removal)` instead of `UPSTREAM EDITED`, and the count it is
allowed to carry is the declared one.

**`(b)` must not get a marker.** A declared-payload class would turn the rule into an
allowlist, and `docs/plan/final-state.md`'s reading on allowlists is the one this repository
applies everywhere else. The owner's rule leaves two dispositions for these 29 files, and
both are mechanisms that already exist:

* **deselect** — extend `deselected-9.6.1.tsv` to the 109 sites. The classification already
  has the kinds (`collapsed-disjunction`, `invented-value`) and the documents; the cost is
  that the affected tests leave the behavioural denominator, which is the honest accounting
  of a test that cannot pass against a conforming implementation.
* **port** — move the fixture repair into the drop-in build, where `_dropin.py` and the
  deselect plugin already live, so the retained file stays byte-identical and the repair is
  regenerable rather than committed. This is the route that keeps the tests in the
  denominator without forking the file.

Reverting without choosing one of the two puts ~109 sites back to red; the measured cost of
each route is the owner's call and is not a reviewer's to make.

### 3.5 The sentence

**Change 4.** `survey/dropin/deselect.py:27` must be scoped to the mechanism it describes —
the deselect list writes nothing under `tests/`, which is true — or deleted. As written it
is a statement about the tree, and the tree contradicts it by 44 files.

---

## Summary for the owning lane

| # | change | where | why |
|---|---|---|---|
| 1 | test upstream provenance before `ours verbatim` | `audit()` branch order | today any edited upstream file reads as "ours verbatim" |
| 2 | make this repository's `tests/` an audited subject | `audit()` / a new mode | nothing compares our `tests/` to upstream's bytes |
| 3 | declare `(a)` and `(c)` in `survey/dropin/upstream-tests-edited-here.tsv`, gated both ways | new declared data | 15 legitimate edits should not read as a fork, and should not rest in a commit message |
| 4 | scope or delete the byte-identical sentence | `deselect.py:27` | it is false about the tree |
| — | `(b)`: 29 files, 109 sites — **no marker**; deselect or port | owner's call | a payload edit is outside the rule, however well derived |
