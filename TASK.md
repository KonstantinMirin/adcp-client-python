# Task: 87 failures across 32 files -- the long tail

## Measure first, keep the artifact

    .venv/bin/python -m pytest tests/ -q --no-header -p no:randomly --continue-on-collection-errors
    cp test-results/report.json test-results/before.json

`addopts` rewrites `test-results/report.json` on EVERY pytest run, so copy it or lose it.
Trunk when written: **failed=398, error=5, passed=14681, total=17910**. Yours must match --
if not, say so and STOP. The run takes ~17 min and several agents share the box, so it may
take longer: run it in the BACKGROUND and poll. Do NOT put a short timeout on it.

At the end: full suite again, `cp test-results/report.json test-results/after.json`, and
report the delta **from those two files**, per file. Not from terminal output.

## The ground

A long tail: 32 files, led by `test_migrate_v3_to_v4.py` (14), then 6s and 4s and a
lot of 1s and 2s. There is no single ground -- expect to classify each file on its own.

The causes already proven in this codebase, in rough order of how often they have turned
up, so check these before inventing an explanation:

1. a name the PREVIOUS generator bound and this emission does not (delete or re-point);
2. a fixture short a key required one `allOf` up (add the key -- the model is right);
3. a test asserting against a DECLARED approximation (a decision, not a defect);
4. a test asserting the old FLAT class graph, where §4 now emits a base plus one child per
   branch and `isinstance` holds against the parent;
5. a genuine SDK behaviour path -- which is the one worth finding, and the one to STOP and
   report rather than fix.

`test_import_memory.py` and `test_public_api.py` are each 1 failure and are INSTRUMENTS,
not rot -- read what they grade before touching them. `test_public_api.py`'s failure is a
known snapshot drift the owner has not yet decided to re-take: leave it reporting, do not
regenerate the snapshot.

## The rule, which is NOT "delete everything"

Earlier agents removed 149 failures between them by **rewriting**: where a contract was
real they re-pointed the test at what the document actually says, and deleted only where
the subject was the PREVIOUS generator's surface, which has no node behind it. Do the same.
Per test, exactly one of:

1. **RE-POINT** -- the subject is real. Grade the name the document gives, or the stable
   spelling `src/adcp/types/aliases.py` binds, or the domain path
   `adcp.types.<domain>`, which is a supported import.
2. **DELETE** -- its only subject is the previous generator's surface, or a fixture the
   document contradicts.

Read `docs/plan/rebuild-plan.md` §4 "Names" and `CLAUDE.md` before deciding. **A public
word that changes meaning while staying importable is the worst available outcome.**

## Two rules that have each cost this project dearly

**READ THE DECISION INDEX BEFORE CALLING ANYTHING A DEFECT.** `CLAUDE.md` opens with it:
1,239 of 1,907 reported "defects" were decisions already taken. If a test fails against
something `__adcp_approximations__` or `__adcp_refused__` DECLARES, that is a DECISION.
Grep the class first.

**REQUIREDNESS IS A CONJUNCTION.** A property's requiredness is its own node's AND every
ancestor's that applies to the same instance -- `status` looks optional on a task response
and is required by `core/protocol-envelope.json` one `allOf` up. Never read one `oneOf`
branch in isolation. Ask through `adcp.types._base._refuse_at`, which resolves the
conjunction and gives the same answer `strict_validate` gives.

**If a ground points at a real COMPILER defect -- a field genuinely required by no
ancestor, a name that should be bound and is not -- STOP and write it in your reply.** Do
not patch around it in a test. That is the only way a real defect surfaces instead of being
papered over, and so far five clusters have been grounded and every one was the emitted
type being faithful and the test being wrong.

## Write scope -- these files ONLY (plus FINDINGS-rest.md)

- tests/test_migrate_v3_to_v4.py   (14)
- tests/test_discovery_payload_size.py   (6)
- tests/test_legacy_only_creative_surfaces.py   (6)
- tests/test_registry.py   (6)
- tests/test_targeting_overlay_compat.py   (6)
- tests/test_decisioning_negotiation.py   (4)
- tests/test_rc3_media_buy_runtime.py   (4)
- tests/test_response_size_limit.py   (4)
- tests/test_targeting_overlay_errors.py   (4)
- tests/test_no_explicit_null.py   (3)
- tests/test_tools_list_output_schema.py   (3)
- tests/test_canonical_formats_public_api.py   (2)
- tests/test_decisioning_idempotency_conflict.py   (2)
- tests/test_feed_version.py   (2)
- tests/test_publisher_selector_xor_autoenforce.py   (2)
- tests/test_update_rights_roundtrip.py   (2)
- tests/test_wire_types.py   (2)
- tests/test_acceptance.py   (1)
- tests/test_client.py   (1)
- tests/test_control_request_intent.py   (1)
- tests/test_decisioning_specialisms.py   (1)
- tests/test_decisioning_wire_dispatch.py   (1)
- tests/test_format_reference_wire_url.py   (1)
- tests/test_idempotency_handoff.py   (1)
- tests/test_import_memory.py   (1)
- tests/test_looks_like_v3.py   (1)
- tests/test_mcp_schema_drift.py   (1)
- tests/test_notification_outbox_artifacts.py   (1)
- tests/test_public_api.py   (1)
- tests/test_purchase_continuation.py   (1)
- tests/test_response_str.py   (1)
- tests/test_validation_parity.py   (1)

Several other agents are working in `tests/` right now, each with its own disjoint file
list. Touch NOTHING outside the list above. Do NOT touch `codegen/`, `src/` or
`tests_emit/`.

## Vocabulary

A union's parts are **BRANCHES**; "arm" is banned in anything you write. The `arm` in the
EMITTED tree and in the schemas is the DOCUMENT's own property name
(`"properties": {"arm": {...}}`) and is NEVER renamed.

## Gates

    ./check                                 # must stay: emitted 1059 / refused 0
    .venv/bin/ruff check tests/ | tail -2   # must not grow
    full suite before/after, as above

`./check` must not move at all -- you are not touching the compiler.

Commit in small commits, one ground per commit. **Never write tool attribution in a commit
message** -- no `Co-Authored-By`, no `Generated with`, in any form.
