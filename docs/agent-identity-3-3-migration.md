# Experimental AdCP 3.3 agent identity

This SDK supports an opt-in preview of issue [#1500](https://github.com/adcontextprotocol/adcp-client-python/issues/1500). The Web Bot Auth wire profile and identity schemas are pinned to the draft commits recorded in `tests/conformance/vectors/wba-profile/README.md` and `src/adcp/signing/_identity_schemas/UPSTREAM.json`. They may change before the protocol release. The stable wire pin and `COMPATIBLE_ADCP_VERSIONS` do not advertise 3.3 yet.

The behavior below follows the final spec decisions (adcontextprotocol/adcp#8162, #8168, #8169, #8170) and matches the Go (`adcp-go`) and TypeScript (`@adcp/sdk/identity-3.3`) SDKs, except where [Differences from the other SDKs](#differences-from-the-other-sdks) says otherwise.

## Buyer signing and publishing

Give each agent its own HTTPS origin. Generate a key using the existing keygen helpers, then derive its WBA public JWK and thumbprint:

```python
from adcp.signing import (
    SigningConfig, load_private_key_pem, public_directory_key, sign_key_directory,
)

private_key = load_private_key_pem(private_pem)
public_jwk = public_directory_key(private_key)
signing = SigningConfig(
    private_key=private_key,
    key_id=public_jwk["kid"],
    agent_origin="https://buyer.agency.com",
)
# Pass signing=signing to ADCPClient or install_signing_event_hook.
```

`agent_origin` explicitly selects Web Bot Auth, sets and covers the structured `Signature-Agent` member, uses `tag="web-bot-auth"`, and uses standard Base64 signatures regardless of the legacy wire encoding. The signer derives the algorithm from the public key, generates a 64-byte random nonce (unpadded base64url, which Cloudflare's `web-bot-auth` verifier requires), and binds every nonempty body with its digest. `@target-uri` covers the URI the request is sent to, unchanged: percent-encoding such as `/a%7Eb/mcp/` is signed as sent (RFC 9421 §2.2.2). The canonical origin is used only for the `Signature-Agent` identity. A request that already carries signature fields is refused rather than stripped; the signer never drops another party's signature.

Automatic signing also requires `web-bot-auth` in the seller's `request_signing.profiles`; omission advertises legacy support only. An unsupported configured profile raises before sending and never silently downgrades. Keep header emission opt-in until all counterparties tolerate the additional covered component.

Ed25519 and P-256 keys work everywhere. `sign_wba_request`, `public_directory_key` and `sign_key_directory` also accept RSA keys of 2048 to 8192 bits, which sign with `rsa-pss-sha512` as in the draft's Appendix E vectors.

Serve the key directory at `/.well-known/http-message-signatures-directory` on that origin. Signing it is RECOMMENDED (WBA Appendix B.1):

```python
response = sign_key_directory(
    agent_origin="https://buyer.agency.com",
    private_keys=[private_key],
)
# Serve response.body as the exact response bytes, with response.headers.
```

The helper signs once per key, covering `"@authority";req` and `content-digest`. It backdates `created` by five minutes, because verifiers allow little clock skew on directory signatures, and the signatures still expire `expires_in_seconds` from now. Recreate and republish the response before its signatures expire. Publish new keys before using them; verifiers cache directories for up to five minutes. A publisher must not expose private key material in the directory.

Serve a signed revocation list at `/.well-known/governance-revocations.json` on the same origin (`adcp-gov-revocation+jws`, signed by a directory key), even when no key is revoked. **Without one, sellers treat your origin as identity-established and won't bind it for spend.** While they can't read it, or it is stale past grace, your spend-committing calls get `SERVICE_UNAVAILABLE`; other calls proceed.

List the origin in `https://{your registrable domain}/.well-known/trust.json` with `adcp:buying`. `validate_trust_record(document, operator_domain=...)` validates it before you publish.

## Seller verification

```python
from adcp.server import RequestSignatureVerification, serve
from adcp.signing import (
    DiscoveredSignerKeys, OriginBindings, OriginRevocationChecker, TrustRecordEvaluator,
)

keys = DiscoveredSignerKeys()
bindings = OriginBindings()  # One-process example; production supplies a durable resolver.
records = TrustRecordEvaluator(polling_interval_seconds=60)
verification = RequestSignatureVerification(
    signer_keys=keys,
    enable_web_bot_auth=True,
    origin_bindings=bindings,
    trust_records=records,
    wba_revocation_checker=OriginRevocationChecker(keys),
    required_for=frozenset({"sync_accounts", "create_media_buy"}),
    # Supply a shared replay_store for multiple processes/replicas.
)
serve(handler, request_signature_verification=verification)
```

A presented `Signature-Agent` or `web-bot-auth` tag selects WBA exclusively, including when verification is in shadow mode. A seller that has not enabled Web Bot Auth answers such a request 403 without `Accept-Signature`; it never falls back to the RFC 9421 profile. `signer_keys` must resolve by origin (its `__call__` accepts `signer_origin=`), which `DiscoveredSignerKeys` does; construction raises `TypeError` otherwise.

### Layers

Verification and authorization are separate layers, as in the other SDKs.

- **Verification** (`verify_wba_request`) needs only the key directory and a replay store. It reads no revocation list and no trust record, and grants no authority, so it can also run in front of the server. `revocation_checker` is optional there; when given, the revocation check runs after verification.
- **Authorization** runs after it: revocation (`check_wba_revocation`), then the binding, re-evaluated against the operator's trust record, then grants.

### Errors are split by layer

- **The signature path** answers only with Web Bot Auth statuses and headers, never 503 (DR-0023): 400 when a signature field does not parse, 403 with `Accept-Signature` for a missing or failed signature or an unresolvable key directory, 403 without `Accept-Signature` for a revoked key, and 429 for replay-store or discovery capacity. Any body is the one generic authentication error, the same for every cause: `{"errors":[{"code":"AUTH_INVALID","message":"Request authentication failed","recovery":"correctable"}]}`. The specific reason is logged, never sent.
- **Authorization outcomes** after verification use the standard AdCP error envelope (the MCP and A2A error bindings for skills; otherwise JSON with HTTP 403 or 503 and `Retry-After`) with existing codes:
  - an operation outside what an unbound caller may do gets what an anonymous caller would get;
  - an operation in `required_for` from an unbound or delisted origin, or a failed binding, gets `PERMISSION_DENIED` with no `details`;
  - a missing grant gets `PERMISSION_DENIED` with `{"scope": "agent", "reason": "grant_absent"}`;
  - a trust-record or revocation-list outage on a spend-committing call gets the retryable `SERVICE_UNAVAILABLE`.
- **Infrastructure outages** (the replay store or revocation store failing) are application-layer `SERVICE_UNAVAILABLE`, never a signature outcome.

A correctly signed request with a valid key never gets 403 with `Accept-Signature`. Clients act on the status and `Accept-Signature`, not the generic body: sign again on 403 with `Accept-Signature`, stop using the key on 403 without it, back off on 429 or 503.

Duplicate structured-field parameters, dictionary labels, and `Signature-Agent` labels (for example `created=1;created=2`) are malformed. Verification rejects them before key discovery or replay admission: WBA returns HTTP 400, and the RFC 9421 profile returns `request_signature_header_malformed`. Parameters on different covered components remain independent, and quoted delimiters do not create extra members or parameters.

### Interop

- Nonces must encode exactly 64 bytes, as unpadded base64url or padded standard base64 (Cloudflare's rule).
- `@target-uri` is the target URI as received, built from the request line (`raw_path` and query string), so percent-encoding is preserved. `@authority` is that URI's authority, lowercased with any default port removed (RFC 9421 §2.2.3).
- RSA keys verify with `rsa-pss-sha512` (2048 to 8192 bits, odd exponent).
- `tests/conformance/vectors/wba-interop/` vendors adcp-client's Cloudflare interop fixtures with provenance; the SDK verifies both the Cloudflare-signed and the adcp-client-signed requests and directories.

### Key directories

`DiscoveredSignerKeys` resolves `(covered origin, thumbprint)`. It never calls capabilities or reads brand.json or trust.json.

- A plain, unsigned JWK Set is accepted by default (`application/http-message-signatures-directory+json`, `application/jwk-set+json` or `application/json`). Keys are found by their RFC 7638 thumbprint; a `kid` is optional and does not affect lookup. Keys the profile cannot use are skipped; private key material fails the directory. `DiscoveredSignerKeys(require_signed_directories=True)` refuses unsigned directories.
- When a directory carries signatures, every one must verify, cover exactly `"@authority";req` and `"content-digest"`, and fall inside its window (60 seconds of skew on `created`, none on `expires`). The digest covers the exact bytes served, a UTF-8 BOM included. Only keys with a verified signature are usable; an unsigned key beside them is ignored.
- **Discovery failures** (WBA §6.10) cover a directory that does not resolve: a network or TLS error, a timeout, any status other than 200 (404, 410, 429 and 5xx included), or an invalid directory. A discovery failure never evicts a cached directory: its keys keep verifying for up to `max_stale_seconds` (24 hours by default) after the last successful fetch, never past the directory signatures' expiry. A key missing from such a stale copy is a discovery failure too. Failures are retried after a 60-second cooldown.
- With no usable cached copy, the request is unverified, and what happens is local policy: `RequestSignatureVerification(wba_discovery_failure=...)`. The default `"reject"` answers 403 with `Accept-Signature`. `"anonymous"` serves the request exactly as an unsigned one, except operations in `required_for` or `protocol_methods_required_for`.
- A directory that resolves without the key is evidence that the key was removed: a signature failure.
- Successful directories are an LRU cache of `max_origins` (256) origins; eviction only forces a refetch. Concurrent discoveries are bounded globally and per operator (`max_origins_per_operator`, 8). A refusal by these local limits is load shedding: 429, and a cached copy keeps verifying for one more five-minute period only.

The operator quota groups use a registrable domain, except that every tenant of a PSL PRIVATE hosting suffix (such as `*.vercel.app` or `*.github.io`) counts under the provider's registrable domain (`adcp.signing.etld.quota_key`). Authority itself still treats each tenant as its own operator.

To continue accepting configured RFC 9421 buyers on the same endpoint, pass their existing `StaticSignerKeys` or `JwksUriSignerKeys` as `DiscoveredSignerKeys(legacy_resolver=...)`. Only messages selected for the legacy profile use this resolver. A failed WBA discovery never falls back to it.

### Revocation

Framework WBA verification installs `OriginRevocationChecker` by default. It reads each origin's signed list and reports, through `status(origin, keyid)`:

- **`"revoked"`:** refused with 403 and no `Accept-Signature`. A stale list still revokes everything it revoked, and revocations are never withdrawn.
- **`"current"`:** a list within `next_update` plus grace (four polling intervals) does not revoke the key.
- **`"no_list"`:** the origin answers 404/410 and no list was ever verified. The identity is established but cannot be bound: `TrustRecordEvaluator.bind` refuses it, and the binding gate treats a bound origin with no list as identity-established.
- **`"stale"`:** the list cannot be read or verified, is past grace (a stale first list included), or exceeds the checker's limits. Spend-committing calls get `SERVICE_UNAVAILABLE` from the binding and grant gates; other calls proceed. A later 404 after a verified list is a failure to read it, never a reset.
- **`"unavailable"`:** for custom checkers backed by a store that cannot be read: every bound call gets `SERVICE_UNAVAILABLE`.

The result is recorded in `VerifiedSigner.revocation` and in `context.metadata["adcp.auth_info"].extra["wba_revocation"]`. A custom `wba_revocation_checker` can implement `status()`, or be a legacy async callable `(origin, keyid) -> bool` whose failure counts as `"stale"`. Concurrent checks for one origin share one fetch. Both checker variants keep `keyCompromise` and the earliest `invalidity_date`; an undated compromise stays undated. `RevocationDetails.exposes(received_at)` uses seller receipt time to assess compromise exposure.

Revoked key facts have non-evicting limits: `max_facts_per_origin=2048`, `max_facts_per_operator=8192` (per quota group) and `max_history_facts=65536`. Overflow refuses the offending origin (it stays `"stale"`) without forgetting another origin's revocations. **Public deployments must persist revocation history durably**, so revocations hold across restarts and replicas.

## Identity-established callers and binding

A verified origin with no binding is identity-established. It gets what an anonymous caller gets:

- Operations in `unbound_for` (default `get_adcp_capabilities` and `get_principal`) run with the verified identity attached. `get_principal` is always allowed, and on MCP so are the session methods (`initialize`, `notifications/initialized`, `ping`, `tools/list`).
- Any other operation is served exactly as an anonymous request, with no verified signer, so your application answers it as it answers anonymous callers (for example, bearer authentication still applies). An operation in `required_for` or `protocol_methods_required_for` is refused with `PERMISSION_DENIED`.
- Include `sync_principal` in `unbound_for` only when the application implements an explicit open onboarding policy that checks trust, requirements and billing before approval. `get_principal` implementations should return the preview's `unconfigured` result when no durable principal exists. Discovering a key never creates or upserts an account.

To approve a binding, evaluate the operator's record explicitly:

```python
await records.bind(verified_signer, principal_id="principal_123", bindings=bindings)
```

The signer must carry a current revocation state (`verified_signer.revocation == "current"`; the framework's verification sets it), and the record must currently list exactly one agent at the verified origin with `adcp:buying`. Migrating an existing RFC 9421 principal requires `existing_rfc9421_principal=True, migration_approved=True` and a seller-side approval decision. The same origin cannot be rebound to another principal. Once bound, legacy signatures for that origin are rejected (no downgrade). Persist bindings and the origin's commercial identity in the seller's registry; the registry still governs suspension, billing and account access.

The framework preserves the verified origin as caller identity and exposes the binding's principal ID in `context.metadata["adcp.auth_info"].extra["principal_id"]`. The verified signer is read per request from the request scope, so a stateful MCP session never attributes one request's signer to another.

### Delisting and trust-record outages

A stored binding records seller approval, not permanent operator membership. The binding gate re-evaluates the operator's agent entry through `trust_records` on every request; its cache is bounded by the polling interval. `binding_role` defaults to `adcp:buying`.

- **Delisted** (the last record read does not list the origin with the role, or the operator never published a record): the origin falls back to identity-established, exactly as at first contact, with no exception: task polling and cancelling included. The binding is kept, so the origin still cannot downgrade to RFC 9421, and `bind` refuses to bind it again while it is unlisted. Operators retire an agent by publishing an empty `agents[]`.
- **Unreachable or unreadable** (a transport error, any status other than 200 including a 404/410 after the operator published a record, an invalid record, or a local capacity refusal): a discovery failure, not a delisting and not a removal. An outage never restores access.
  - The last record read stays authoritative. If it did not list the origin, the origin stays delisted whatever made the refresh fail.
  - If it did, spend-committing calls fail with `SERVICE_UNAVAILABLE`. Other calls continue under the binding while that record is within `TrustRecordEvaluator(outage_continuation_seconds=...)` past its freshness. That bound is seller policy (default four polling intervals; `0` disables continuation). After it, they also get `SERVICE_UNAVAILABLE` until a fetch succeeds.
  - With no record in the authority history, outages are `SERVICE_UNAVAILABLE`.
- A 404/410 from an operator that has never published a record means no record: the origin is not listed. `TrustRecordEvaluator.check_listing` implements these rules.

`RequestSignatureVerification.spend_classifier(operation, params)` lets a seller classify spending using its own state. The default treats new purchases, acquisitions, `activate_signal`, resumes, financial changes, and unknown operations as spend-committing; name changes, pauses, and cancellations can continue under a cached binding. The decision also governs the account grant gate.

Framework `serve` dispatch projects authorization failures through the existing MCP and A2A error bindings before handler side effects. Standalone `SignedRequestVerificationMiddleware` answers them itself with the AdCP envelope by default. Set `defer_authorization_errors=True` only when the integration applies the verified context with `apply_verified_signer` and calls `check_wba_authorization` from `adcp.server.signed_requests` before its handler. The built-in A2A handler checks the owner-scoped task store before cancelling or subscribing to an active task; a custom `request_handler` must enforce equivalent ownership checks.

## Trust records

`TrustRecordEvaluator` derives `https://{eTLD+1}/.well-known/trust.json` using the SDK's pinned ICANN and PRIVATE PSL snapshot. It follows one `authoritative_location` pointer while preserving the original owner, follows no HTTP redirects, caps bytes at 2 MiB, rejects ambiguous JSON, and caches no longer than the configured polling interval (default 60 seconds). Negative results are cached for 60 seconds.

- **Host budgets.** Fetches to an operator's own hosts are limited per `(operator, host)` (`max_fetches_per_host`, 4). `authoritative_location` hops to hosts outside the operator's registrable domain share a separate global per-host budget (`max_foreign_fetches_per_host`, 16), so a hop never spends the target operator's own budget and many operators cannot multiply fetches to one host. Host cool-downs are scoped to `(operator, host)` and never follow content errors. A budget refusal is a retryable outage that is never cached as a failure.
- **Authority history** (which operators have served a 200, and the last record read from each) is security state. It is never evicted. The in-memory default admits at most `max_history_records` (256) operators and `max_history_records_per_operator` (64) per quota group (PSL PRIVATE tenants count under their provider). A new operator over quota is refused as unavailable before fetching, and no other operator's history is lost. Losing this history (a restart, another replica) turns a later 404 into absence, re-enabling brand.json fallback, or turns a delisting into an outage. **Public deployments must persist authority history durably.**

`validate_trust_record(document, operator_domain=...)` validates authoring output, rejects keys in agent entries, checks ownership, and enforces one agent per origin. The record's host is its owner; a hosted document cannot name another owner inside its content.

## Demand grants

`TrustGrantEvaluator.check(...)` follows L2 §Grants in trust.json:

- **One record authorizes: the house's.** Pass `resolve_house=` (an async `brand_domain -> house_domain | None`) that returns the house named by the brand's verified brand.json (a house redirect, or a `house_domain` the house's `brand_refs[]` reciprocates). Without it, or when it returns `None`, the brand's own domain is the house. A resolver failure is `SERVICE_UNAVAILABLE`. Grants in any other record are never consulted.
- **Domains compare as registrable domains** under the pinned PSL snapshot. Authority is implicit when `account.operator`, the brand's domain and the signer's operator share one.
- **Otherwise a chain must reach the signer's operator with `account.operator` on it:** the house grants the signer's operator, which is `account.operator`; the brand is `account.operator` (a self-operated brand) and its house grants the signer's operator; or the house grants `account.operator`, whose own record grants the signer's operator. There is no third link.
- **Every link must cover** the scope, `profiles.adcp.brands`, the countries and the agent narrowing (a narrowed link that does not list the signer's canonical origin ends the chain), and the check time must fall inside every link's `valid_from`/`valid_until`, so the effective window is the latest `valid_from` to the earliest `valid_until`.
- `exclusive_grants` makes `grants[]` exhaustive for the scopes it names, disabling `seller_authorization` for them.
- **No downgrade.** A 200 from the house's trust.json makes it the only source of grants: `legacy_authorization` (brand.json `authorized_operators`) runs only while the house has never published one.
- **Fetch failures.** A grantor or intermediary record that can't be read, including a 404/410 after it was read, is never absence and never `grant_absent`. A claim marked non-spend (`allow_stale_on_outage=True`) is evaluated on the last records read within the outage-continuation bound; anything else gets `SERVICE_UNAVAILABLE`. An intermediary that has never published a record provides no second link.

For `DecisioningPlatform`, wire a gate and an active buyer-agent registry:

```python
from adcp.decisioning.trust_grants import TrustGrantClaim, TrustGrantGate
from adcp.signing import TrustGrantEvaluator

# Extract existing-account brand/operator/countries from seller-owned state.
gate = TrustGrantGate(
    evaluator=TrustGrantEvaluator(records, resolve_house=resolve_verified_house),
    extract_claim=lambda account, agent: TrustGrantClaim(
        brand_domain=account.metadata["brand_domain"],
        account_operator=account.metadata["operator"],
        brand_id=account.metadata.get("brand_id"),
        countries=tuple(account.metadata.get("countries", ())),
    ),
)
# adcp.decisioning.serve(..., buyer_agent_registry=registry, trust_grant_gate=gate,
#                         request_signature_verification=verification)
```

- The gate checks every natural-key `sync_accounts` declaration before any upsert. A row that names an existing `account_id` is checked against that account's seller-owned claim, and its brand/operator fields are checked too; an `account_id` that does not resolve is denied.
- Existing accounts and account-scoped calls use the seller's extractor, including a fresh check before spending. An extractor that raises, or a claim without a brand or operator, fails closed with `PERMISSION_DENIED`.
- `TrustGrantClaim.scope` defaults to `adcp:media_buying` for buying, `list_products` and account provisioning. For other domains, configure `extract_operation_claim(account, buyer_agent, operation)` to select an explicit scope.
- A missing grant raises `PERMISSION_DENIED` with `{"scope": "agent", "reason": "grant_absent"}` after commercial identity is established. A signer its own operator does not list gets `PERMISSION_DENIED` without details; an outage requiring fresh authority gets the retryable `SERVICE_UNAVAILABLE`. A stale revocation list fails spend closed at the gate too. Provisioning always requires fresh authority. The gate changes no account status.
- The gate keeps no claim history of its own: the evaluator's last record read is authoritative, so a withdrawn grant stays withdrawn through a later outage.

When configured, this gate replaces the older `brand_authorization_gate` for account-scoped dispatch. Put any permitted brand.json fallback in `TrustGrantEvaluator(legacy_authorization=...)`. Legacy RFC 9421 and bearer buyers can use it without an operator trust record while the house has never published trust.json. Supply equivalent checks in custom `ADCPHandler` implementations before account side effects.

Typed client results preserve `adcp_error`, including its code, recovery guidance, and details.

## Preview types and rollout

Use the preview `RequestSigning` model (`adcp.types.experimental_identity`) to advertise `profiles=["adcp/request-signing/v1", "web-bot-auth"]` on a server accepting both. The preview reader models preserve unknown onboarding requirement kinds so applications can fall back to the posture's message and URL; unknown kinds cannot be satisfied automatically. Authoring validation still enforces the pinned draft schema.

The schemas follow #8170 and #8168: the buyer posture lives only in trust.json, at `profiles.adcp.onboarding` on the record and on an agent entry; one mode enum (`open`, `application`, `invite_only`) serves sellers and buyers; the `agent_identity` requirement kind and `documentation_url` are gone; `aao_verified` uses `verified_specialisms`; `relationship.status` uses `pending_approval`.

Import experimental models from `adcp.types.experimental_identity`: `AgentOnboarding`, its modes/tiers/requirements, `BuyerOnboardingPosture`, `TrustRecord`, `GetPrincipalResponse`, `PrincipalRelationship`, `PrincipalRelationshipStatus`, `PrincipalChangedWebhook`, and `GrantAbsentDetails`. Generate the private models offline with `python scripts/generate_identity_preview.py`; validate behavioral constraints with the trust helpers.

For preview `principal.changed` reasons, pass `experimental_agent_identity=True` to `WebhookSender.prepare_principal_changed` or `send_principal_changed`, and again to `send_prepared` or `resend` when publishing persisted events.

Use `ADCPClient(..., experimental_agent_identity=True)` or the equivalent multi-agent option to preserve and parse these fields on capabilities, principal reads and completed-task callbacks. WBA signing opts into these response models automatically.

`PrincipalService(relationship_resolver=...)` accepts an async seller-owned lookup keyed by the authenticated `PrincipalIdentity`. `relationship` is a 3.3 field: `PrincipalService.get_principal(..., context=tool_context)` consults the resolver and emits it only when `context.resolved_adcp_version` is 3.3 or later. Reading a pending application can therefore return `unconfigured` with a relationship without creating a durable principal or authorizing an account.

Onboarding posture is advisory. Sellers still implement requirements, applications and billing policy. Evaluate the verified origin's trust record and required role with `records.check_listing(...)` when applying an `open` policy, before provisioning access.

RFC 9421 configuration emits a `DeprecationWarning` and continues to work through 3.x. `async_resolve_agent`, `verify_from_agent_url`, BrandJsonJwksResolver and governance/rights/document JWS verification retain their existing chain until AdCP 3.4. Roll back opt-in signing only for origins that have not been bound; rolling a bound origin back to RFC 9421 requires explicit seller migration.

## Differences from the other SDKs

- **Nonce acceptance.** The verifier accepts exactly 64-byte nonces, as Go does. The TypeScript verifier keeps a 16-byte floor.
- **Signed directories with an unsigned key.** Only keys with a verified signature are usable (draft directory-05). Go accepts every key in a signed directory; TypeScript refuses the directory.
- **Discovery capacity.** A local discovery-limit refusal is a 429, as in TypeScript. Go treats it as a discovery failure.
- **Directory created skew.** Directory signatures tolerate 60 seconds of `created` skew, as in TypeScript; Go allows none. All SDKs backdate `created` when publishing.
- **Replay status.** A replayed nonce is 403, as in Go and the #7894 vectors; capacity is 429.
- **Spend classification.** `update_media_buy` and `control_media_buy` are classified by their parameters; Go treats every `update_media_buy` as spend.
- **Grant-gate claim history.** The gate no longer keeps its own approval/denial history (and its `max_denials` / `max_claims_per_operator` options are gone): the evaluator's last record read is the single source, as in Go. A seller-authorization hook must therefore order its own concurrent decisions.

## Not covered yet

- The final 3.3 schema bundle and the P7 trust-record and grant-chain conformance vectors are upstream release dependencies; re-pin and rerun conformance when they land.
- Durable stores are application-owned: bindings, revocation history, authority history and replay state are in memory by default. Public deployments need all four.
