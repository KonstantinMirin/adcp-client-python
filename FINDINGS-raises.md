# Findings — the 36 `DID NOT RAISE` cases, grounded one at a time

The population is the artifact's, not a guess: `test-results/before.json`, written by the
full suite before any edit here, holds **36** failed entries whose `longrepr` carries
`Failed: DID NOT RAISE`. They fall in eight files:

| file | cases | ground |
| --- | --- | --- |
| `tests/test_reporting_webhook_operation_id.py` | 13 | A — a key no pinned bundle states |
| `tests/test_manifest_response_readback.py` | 12 | B — the previous emission's class graph |
| `tests/test_reporting_capability_models.py` | 3 | C — a DECLARED widening, and an inverse nothing states |
| `tests/test_scalar_roots.py` | 3 | E — D2 makes a scalar root an alias, which has no constructor |
| `tests/test_beta3_url_constraints.py` | 2 | D — a DECLARED widening, graded on the schema half |
| `tests/test_lazy_rebuild.py` | 1 | A — the patcher that supplied the field is not declared here |
| `tests/test_trusted_match_validation.py` | 1 | F — the rule is PROSE in a `description` |
| `tests/test_validation_parity.py` | 1 | F — the rule is in the `x-` namespace the draft ignores |

Each ground was re-measured here before anything was touched; two of the task's three
statements of ground C needed correcting, and both corrections are recorded below.

---

## Ground A — `operation_id` is stated by no pinned-bundle node (13 cases)

`core/reporting-webhook.json`, measured across every bundle in `schemas/cache`:

    properties:           authentication, reporting_frequency, requested_metrics, token, url
    required:             url, authentication, reporting_frequency
    additionalProperties: TRUE
    operation_id stated in 3.1? No.  in 3.2? No.  In 3.2.0-beta.6 ONLY, and REQUIRED there.

`ReportingWebhook.model_fields` is exactly those five, so the class is faithful and the key
arrives as an EXTRA that the document's own `additionalProperties: true` admits
unconstrained. The refusals these tests wanted belonged to the field
`adcp.types._forward_compat` patched in; that module is not declared in this emission.

| test | cases | disposition |
| --- | --- | --- |
| `test_reporting_operation_id_rejects_invalid_supplied_values` | 6 | **replaced** by `test_reporting_webhook_admits_any_operation_id_value`: each of the six values is admitted, kept verbatim through the dump, and accepted by `strict_validate` — the document's own answer, at both halves. |
| `test_nested_registration_validation_rejects_bad_reporting_id` | 5 | **replaced** by `test_nested_registration_carries_the_unconstrained_extra_through`: no node of the five request documents states the key under `reporting_webhook`, so the value rides through the parent, its dump, and the pinned request schema (Draft7 reports no error). |
| `test_tampered_stored_operation_id_fails_validation` | 1 | **removed.** It asked `WebhookSender.prepare_media_buy_delivery` to refuse a malformed stored value. There is no field to constrain, and the SDK promise behind it is for the owner (below). |
| `test_beta6_versioned_request_schema_preserves_reporting_operation_id` | 1 | **rewritten.** Its premise — a historical versioned type — is false: measured, `adcp.types.v32.AcceptProposalRequest` **is** `adcp.types.media_buy.AcceptProposalRequest` (that module's own words: *"AN ALIAS IS A NAME AND NEVER A SECOND TYPE"*). The beta.6 contract is real and is now graded where it lives — `get_named_validator("core/reporting-webhook.json", version="3.2.0-beta.6")` reports `'operation_id' is a required property`, and the pinned validator reports nothing for the same registration with or without the key. |

The same ground decides the one case in `tests/test_lazy_rebuild.py`:
`test_forward_compat_patches_apply_on_first_use` had `adcp.types._forward_compat`'s patched
field as its entire subject — an empty `operation_id` refused once the model is built, and
the field present in the parent's lazily built `$defs`. The module is named in two
docstrings under `src/adcp/types/` and declared nowhere, so there is no patch whose
first-use application could be observed. **Removed**, with a comment in its place recording
what it asked.

## Ground B — a readback node IS the input model's branch (12 cases)

`test_manifest_readback_cannot_bypass_input_validation` asserted
`not isinstance(manifest, input_model)` and a `model_type` refusal when the instance is
handed back. Measured:

    readback class : CanonicalFormatManifest
    mro            : CanonicalFormatManifest -> CreativeManifest -> BranchDispatchMixin -> …
    isinstance(manifest, CreativeManifest) -> True
    CreativeManifest.model_validate(manifest) is manifest -> True

`CLAUDE.md` records the decision: `core/creative-manifest.json#` emits `CreativeManifest` as
the base with `NamedFormatManifest` / `CanonicalFormatManifest` as its branches, and
**"`isinstance` holds against the parent."** The test contradicted a recorded decision; the
premise was true under the FLAT emission, where a readback node was an unrelated class.

**Rewritten** as `test_manifest_readback_is_the_input_model_s_own_branch`, which keeps the
dump half the task asked be kept and grades the instance half as the emission states it:
the instance is accepted, is not copied, and keeps its branch class and kind; the dump
validates back into the same branch with the same kind. The `input_model` parametrization is
gone and replaced by the assertion that found it unnecessary — `CreativeManifest is
InputManifest`, one object under the flat name and the domain path — so all **24** cases of
that function (the 12 in the population and the 12 `dump` cases that failed on the same
`assert not isinstance`) now pass.

## Ground C — one declared widening, and one implication nothing states (3 cases)

**Two corrections to the task's statement of this ground, both measured.**

1. The task says `allOf` 3–7 "test `properties`/`const`/`contains` in the `if`, which the
   rule vocabulary cannot express". `allOf/2` does exactly that — `if: {properties:
   {reliable_reporting_version: {const: "1.0"}}, required: [...]}` — and IS lowered, as
   `ConditionalRequired(when=Match(key='reliable_reporting_version', allowed=('1.0',)), …)`.
   And `allOf/7`'s `if` is `required`-only. What is declared at 3–7 is not decided by the
   `if` at all: §5's `then` row puts a conditional's `properties` on the schema half and not
   on the model, so each of those five has a `then` the model cannot carry. `allOf/3`, `/4`
   and `/7` ALSO contribute a lowered `ConditionalRequired` from the `then`'s `required`,
   which is why one of the four parametrized cases was already green.
2. The three red cases are **not one ground**. Only one of them is the declared widening.

| case | ground | disposition |
| --- | --- | --- |
| `[False-readiness_notification-managed_delivery]` | **DECLARED widening.** `#/allOf/7`'s `then` pins `managed_delivery: {const: true}`; the class records `Approximation(pointer='#/allOf/7', keyword='if', kind='WIDENED', rung='KEYWORD')`. Reporting it as a defect is reporting a decision already taken. | kept, moved to the half that holds it: `strict_validate` refuses with `True was expected`. |
| `[None-receipt_task-reconciled_billing]`, `[False-…]` | **No node states the inverse.** Measured over bundle 3.2, nothing keys an `if` on `receipt_task`. The stated direction is `#/allOf/4` — `reconciled_billing: true` → `required: [receipt_task]` — and `receipt_task`'s own description says *"Required when reconciled_billing is true"*. | **removed**, replaced by `test_receipt_task_alone_is_admitted_because_no_node_states_the_inverse`: both halves admit it. |

The fourth case, `[None-readiness_notification-managed_delivery]`, was not in the population
(it raised, and failed on the message). `#/allOf/7`'s `required` half IS lowered —
`ConditionalRequired(when=Match(key='readiness_notification', present=True),
require=('managed_delivery',))` — so it is kept, standalone and nested, under the message
this emission reports: `managed_delivery required when readiness_notification`.

**Adjacent, same ground, repaired in the same commit (2 cases, NOT in the 36):**
`test_reconciled_is_cumulative_even_without_a_receipt_task` expected
`"reconciled_billing requires managed_delivery"`, an implication no node of bundle 3.2
states in that direction, and was failing on the message of the refusal that IS stated. It
is now `test_reconciled_billing_requires_a_receipt_task` and asserts `#/allOf/4`.

## Ground D — the image size mutex, graded on the schema half (2 cases)

`tests/test_beta3_url_constraints.py::test_image_package_dimensions_must_cooccur`.
`media-buy/package-request.json#/allOf/2`:

    {"if": {"properties": {"format_kind": {"const": "image"}},
            "required": ["format_kind", "params"]},
     "then": {"properties": {"params": {"dependencies": {"width": ["height"],
                                                         "height": ["width"]}}}}}

Same §5 `then` row as ground C, same declaration — `#/allOf/2 if WIDENED KEYWORD` — and the
document types `params` as `{"type": "object", "additionalProperties": true}`, which is why
the field is `dict[str, Any] | None` and never reaches the canonical image parameters here.
**Kept**, moved to `PackageRequest.strict_validate`, which refuses with the document's own
keyword (`params` / `dependencies`), asserted by `(loc, type)` like the rest of that file.

## Ground E — a scalar root is an alias, and an alias has no constructor (3 cases)

rebuild-plan §4, *What becomes what*: **a scalar at a root → "a module-level annotated
alias, not a class"**, and *"A root scalar is an alias, so it has no class to carry
`strict_validate`; its module binds the same validation as a module-level function over the
same schema reference."* Measured, `adcp.PropertyTag` is
`Annotated[str, FieldInfo(pattern='^[a-z0-9_]+$'), …]`, so `PropertyTag("Invalid-Tag")` is
`str("Invalid-Tag")` and `PropertyTag()` is `""`.

`test_construction_enforces_the_string_pattern`, `test_construction_rejects_a_wrong_scalar_type`
and `test_missing_value_raises_type_error` graded the `str` subclass
`post_generate_fixes.rewrite_scalar_rootmodels` used to emit. **Replaced** by one test over
the two sites the alias does have: inside a model field (`string_pattern_mismatch`,
`string_type`) and through `adcp.types._schemas.core.property_tag.strict_validate`
(`pattern`, `type`).

## Ground F — a rule no keyword of the document states (2 cases)

| test | what states the rule | disposition |
| --- | --- | --- |
| `test_provider_registration_rejects_non_https_endpoint` | `trusted-match/provider-registration.json#/properties/endpoint` is `{"type": "string", "format": "uri"}`. *"MUST be HTTPS in production"* is in the same node's `description`, beside the reserved-range and IP-pinning rules no keyword can state either. A description constrains no instance. | **rewritten** to assert what the document says: both halves admit `http://`, and the obligation is the operator's, enforced where the connection is made. |
| `test_high_risk_behavioral_extension_has_targeted_runtime_validator` | `media-buy/change-term.json` states no `allOf` and no conditional; the action/constraint compatibility table is under `x-adcp-validation.verifier_constraints`. rebuild-plan §6 decides it by name: *"`x-adcp-validation` constrains in intent and not in the document, so a model enforcing it would be narrower than its document (upstream: `adcontextprotocol/adcp#8472`)"*. | **rewritten**: the document assertion is kept and strengthened (`pause` is absent from the `budget` row), and the payload is asserted admitted by the model and by `strict_validate`. |

---

## What the suite did, read off the two artifacts

`test-results/before.json` and `test-results/after.json` are the same command
(`pytest tests/ -q --no-header -p no:randomly --continue-on-collection-errors`) run before
and after these commits, copied aside because every pytest run overwrites `report.json`.

| | before | after |
| --- | --- | --- |
| `summary.failed` | **547** | **496** |
| `summary.passed` | 14531 | 14565 |
| `summary.error` | 5 | 5 |
| entries whose `longrepr` says `DID NOT RAISE` | **36** | **0** |
| collected | 17920 | 17903 |

**51 failures went, none appeared** — the before-failing set minus the after-failing set is
51 nodeids and the reverse difference is empty.

| no longer failing | file | = population + adjacent |
| --- | --- | --- |
| 24 | `tests/test_manifest_response_readback.py` | 12 + 12 `dump` cases of the same function |
| 13 | `tests/test_reporting_webhook_operation_id.py` | 13 + 0 |
| 6 | `tests/test_reporting_capability_models.py` | 3 + 1 message case + 2 adjacent |
| 3 | `tests/test_scalar_roots.py` | 3 + 0 |
| 2 | `tests/test_beta3_url_constraints.py` | 2 + 0 |
| 1 | `tests/test_lazy_rebuild.py` | 1 + 0 |
| 1 | `tests/test_trusted_match_validation.py` | 1 + 0 |
| 1 | `tests/test_validation_parity.py` | 1 + 0 |

The 17 fewer collected cases are the removals and the dropped parametrizations: the
manifest function's `input_model` axis (−12, one object under two names), three scalar-root
constructor tests replaced by one (−2), and one test each from the webhook, lazy-rebuild and
capability files (−3).

`./check` is unmoved at **emitted 1059 / refused 0 (deferred 0, verdict 0)**, and
`ruff check tests/` is unmoved at **105**. Nothing outside `tests/` and this file was
touched.

## Needs the owner

**`src/adcp/webhooks.py` reads a field the emission does not declare.** `src/` is out of this
worktree's write scope, and this is not a fixture problem.

    src/adcp/webhooks.py:378   if not webhook.operation_id:
    measured                   AttributeError: 'ReportingWebhook' object has no attribute 'operation_id'

`ReportingWebhook` carries `extra='allow'`, so a registration that HAS the key answers
through `model_extra` and the attribute resolves; a registration WITHOUT it raises
`AttributeError` where the function means to raise `ReportingWebhookOperationIdMissingError`.
That is the suppress-and-flag contract for scheduled `media_buy_delivery` sends, and it is
the exact path a legacy registration takes. Two tests report it today
(`test_typed_registration_without_operation_id_is_refused`,
`test_scheduled_sends_skip_and_flag_registrations_without_operation_id`) and they are left
red, because forcing them green would mean either editing `src/` or asserting an
`AttributeError` as though it were the design.

The same function's docstring promises `pydantic.ValidationError` for *"a stored
`operation_id` outside the 1–255 `[A-Za-z0-9_.:-]` form"*. Nothing can raise that now; the
removed `test_tampered_stored_operation_id_fails_validation` was grading that promise.

**The question behind both** is one the owner decides, not this lane: `operation_id` on
`reporting_webhook` is an SDK extension (adcp#7895 / #1547) that no pinned-bundle node
states. Either the SDK keeps carrying it — which needs a stated home, since a generated
class may not mint it — or `webhooks.py` reads it off `model_extra` and the extension
retires. The honest failure the task names,
`assert 'operation_id' in ReportingWebhook.model_fields`, is left standing as the marker for
that decision.

## Adjacent, measured, NOT touched

Red for grounds outside this lane, recorded so they are not re-derived:

* `tests/test_reporting_webhook_operation_id.py` — 11 remaining, all the same field-absence
  cluster: `model_fields` assertions, `webhook.operation_id` attribute reads, and the two
  sender tests above.
* `tests/test_manifest_response_readback.py` — 11 remaining: the async-union and
  completed-task parses, the nested envelope constraints, and the listed-creative fixture.
  None is a refusal question.
* `tests/test_reporting_capability_models.py` — 6 remaining, two grounds. Four
  (`test_core_attributes_…`) assert `{"type": "null"} in schema["properties"][name]["anyOf"]`;
  measured, the field renders `{"const": "reporting.delivery_ready", "type": "string",
  "default": null}`, which is the `None`-is-absence decision rendering an optional `const`,
  not a nullable union. Two (`test_each_explicit_supported_literal_…`) use a fixture the
  document contradicts: it sets `managed_delivery: true` without
  `resource_retention_days` / `authorization_revocation_seconds`, which `#/allOf/3` requires
  and the class DOES carry as a rule.
* `tests/test_scalar_roots.py` — 8 remaining: the rest of the file still asks the alias for
  `isinstance`, `__slots__`, `plain_scalar`, a deprecated `root` keyword and a `ViewThreshold`
  symbol this surface does not bind. One repair, wider than this lane.
* `tests/test_lazy_rebuild.py` — 4 remaining, all the patcher architecture (`_forward_compat`
  in the probe's model list, `_ergonomic` first-use, the `RootModel` parametrization import).
* `tests/test_trusted_match_validation.py` — 3 remaining: one expects
  `"countries is required"` where the lowered rule reports `required when
  identity_match=True` under an `anyOf` branch, and two fixtures omit `status` and `type`,
  which the envelope requires (requiredness is a conjunction).
* `tests/test_validation_parity.py` — 1 remaining: a parity fixture
  (`get_signals.wholesale_forbids_selector`) the model now refuses where the fixture says it
  accepts.
