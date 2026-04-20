"""One-call webhook receiver: verify signature, dedupe, parse.

Packages the three things every AdCP webhook receiver has to do so callers
don't re-read the five-point normative checklist in ``webhooks.mdx``:

1. Verify the RFC 9421 signature (or fall back to HMAC-SHA256 when the buyer
   explicitly opts in for 3.x migration).
2. Dedupe on ``(authenticated_sender_identity, idempotency_key)`` with a 24h+
   TTL. Duplicates are a no-op, not an error.
3. Parse the body into the right typed payload so the caller gets a
   ``McpWebhookPayload`` / ``RevocationNotification`` / etc. back.

Usage::

    from adcp.webhooks import (
        WebhookReceiver,
        WebhookReceiverConfig,
        WebhookVerifyOptions,
    )
    from adcp.server.idempotency import MemoryBackend, WebhookDedupStore

    receiver = WebhookReceiver(
        config=WebhookReceiverConfig(
            verify_options=WebhookVerifyOptions(
                jwks_resolver=my_jwks_resolver,
                replay_store=my_replay_store,
            ),
            dedup=WebhookDedupStore(MemoryBackend(), ttl_seconds=86400),
        ),
    )

    @app.post("/webhooks/adcp")
    async def hook(request):
        outcome = await receiver.receive(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            body=await request.body(),
        )
        if outcome.rejected:
            return Response(status_code=401, headers=outcome.response_headers)
        # MUST return 2xx on duplicates — the sender interprets non-2xx as
        # delivery failure and retries.
        if outcome.duplicate:
            return Response(status_code=200)
        await process(outcome.payload)
        return Response(status_code=200)
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, cast, runtime_checkable

from pydantic import ValidationError

from adcp.server.idempotency.webhook_dedup import WebhookDedupStore
from adcp.signing.errors import SignatureVerificationError
from adcp.signing.webhook_hmac import (
    LegacyWebhookHmacError,
    LegacyWebhookHmacOptions,
    verify_webhook_hmac,
)
from adcp.signing.webhook_verifier import (
    WebhookVerifyOptions,
    verify_webhook_signature,
)
from adcp.types.generated_poc.brand.revocation_notification import RevocationNotification
from adcp.types.generated_poc.collection.collection_list_changed_webhook import (
    CollectionListChangedWebhook,
)
from adcp.types.generated_poc.content_standards.artifact_webhook_payload import (
    ArtifactWebhookPayload,
)
from adcp.types.generated_poc.core.mcp_webhook_payload import McpWebhookPayload
from adcp.types.generated_poc.property.property_list_changed_webhook import (
    PropertyListChangedWebhook,
)

logger = logging.getLogger(__name__)

WebhookKind = Literal[
    "mcp",
    "revocation_notification",
    "collection_list_changed",
    "property_list_changed",
    "artifact",
]

WebhookPayload = (
    McpWebhookPayload
    | RevocationNotification
    | CollectionListChangedWebhook
    | PropertyListChangedWebhook
    | ArtifactWebhookPayload
)

RejectionReason = Literal[
    "signature_missing",
    "signature_invalid",
    "signature_legacy_failed",
    "content_type_invalid",
    "body_invalid_json",
    "payload_invalid",
    "idempotency_key_missing",
    "idempotency_key_invalid",
]

# Spec: ^[A-Za-z0-9_.:-]{16,255}$ per security.mdx §Idempotency. Enforce at the
# receiver so a non-conformant sender can't churn dedup storage with
# unreasonable key lengths or exotic charsets.
_IDEMPOTENCY_KEY_RE = re.compile(r"^[A-Za-z0-9_.:-]{16,255}$")

_ACCEPTED_CONTENT_TYPES = ("application/json",)


@dataclass(frozen=True)
class LegacyHmacFallback:
    """Opt-in policy for accepting HMAC-SHA256 senders during 3.x migration.

    The default behavior of the receiver is to reject any request that fails
    9421 verification. Pass an instance of this class to ``WebhookReceiverConfig``
    to accept HMAC-signed webhooks as a fallback.

    :param options_for: callback that returns a populated
        :class:`LegacyWebhookHmacOptions` given the incoming request headers.
        Your implementation resolves the sender (from Bearer, hostname, or
        legacy shared-secret tag) and returns the secret + sender_identity
        tuple the verifier needs. Return ``None`` to decline the fallback
        for this request (rejection follows the 9421-only failure path).
    :param only_when_9421_absent: when ``True`` (default), HMAC fallback only
        fires when no 9421 headers are present at all. When a request carries
        9421 headers that FAIL verification, it still rejects — preventing a
        downgrade attack where a MITM strips the 9421 signature and replaces
        it with a forged HMAC one it knows the secret for. When ``False``,
        HMAC is tried on any 9421 failure; only set this for testing or known
        homogenous sender cohorts.
    """

    options_for: Callable[[Mapping[str, str]], LegacyWebhookHmacOptions | None]
    only_when_9421_absent: bool = True

    @classmethod
    def from_shared_secret(
        cls,
        *,
        secret: bytes,
        sender_identity: str,
        only_when_9421_absent: bool = True,
        window_seconds: int = 300,
    ) -> LegacyHmacFallback:
        """Convenience constructor for the "one secret, one sender" case.

        Covers the common 3.x migration setup where the receiver has exactly
        one publisher on the legacy scheme and binds them to a known
        ``sender_identity`` (typically a buyer-defined string). For multi-
        sender or header-derived-identity setups, construct with an
        ``options_for`` callback directly.
        """
        import time as _time

        def _options_for(_headers: Mapping[str, str]) -> LegacyWebhookHmacOptions:
            return LegacyWebhookHmacOptions(
                secret=secret,
                sender_identity=sender_identity,
                now=_time.time(),
                window_seconds=window_seconds,
            )

        return cls(
            options_for=_options_for,
            only_when_9421_absent=only_when_9421_absent,
        )


@dataclass(frozen=True)
class WebhookReceiverConfig:
    """Configuration bundle.

    :param verify_options: verifier configuration (JWKS, replay store, etc.).
        A single instance is reused for every request — the verifier stamps
        ``now`` itself via ``verify_options.clock()``, so there's no need to
        refresh a time field per request.
    :param dedup: webhook-dedup store.
    :param legacy_hmac: optional HMAC-SHA256 fallback for 3.x migration.
    :param kind: which webhook payload type to parse into. Default ``"mcp"``
        (the task-status webhook that dominates most integrations); pass
        explicitly for list-change / artifact / revocation receivers.
    """

    verify_options: WebhookVerifyOptions
    dedup: WebhookDedupStore
    legacy_hmac: LegacyHmacFallback | None = None
    kind: WebhookKind = "mcp"


@dataclass(frozen=True)
class WebhookOutcome:
    """Result of a single ``receive`` call.

    Exactly one of ``rejected`` or ``payload`` is set. ``duplicate=True`` is
    compatible with a non-None ``payload`` — the payload parsed fine, the
    signature verified fine, it's just a retry the caller should 200 away.
    """

    rejected: bool = False
    rejection_reason: RejectionReason | None = None
    response_headers: Mapping[str, str] = field(default_factory=dict)
    # Populated on successful verify (even when rejected downstream of crypto)
    sender_identity: str | None = None
    # Populated on successful verify + parse
    payload: WebhookPayload | None = None
    duplicate: bool = False
    idempotency_key: str | None = None


@runtime_checkable
class VerifiedSignerLike(Protocol):
    """Anything with ``as_sender_identity() -> str``.

    Both :class:`VerifiedWebhookSender` (9421) and :class:`VerifiedLegacyWebhookSender`
    (HMAC) implement this shape, so the receiver treats both verification
    paths identically downstream.
    """

    def as_sender_identity(self) -> str: ...


class WebhookReceiver:
    """Stateless webhook entry point, one instance per receiver configuration.

    Instance state (``config``) is read-only after construction. Per-request
    state lives in the :class:`WebhookOutcome` returned from :meth:`receive`.
    """

    def __init__(self, config: WebhookReceiverConfig) -> None:
        self._config = config

    async def receive(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
    ) -> WebhookOutcome:
        """Verify, dedupe, parse. Returns a :class:`WebhookOutcome`.

        Never raises for sender-caused cryptographic or protocol failures —
        returns an outcome with ``rejected=True`` and populated
        ``response_headers`` so the caller can convert to an HTTP response
        without try/except around every call. Operational failures inside
        the dedup backend or verify-options factory MAY still raise; wrap
        the call if you need to 5xx cleanly on internal errors.
        """
        if not _content_type_is_json(headers):
            return _reject("content_type_invalid", sender_identity=None)

        signer, rejection = await self._verify(method=method, url=url, headers=headers, body=body)
        if rejection is not None:
            return rejection
        assert signer is not None  # verification succeeded

        sender_id = signer.as_sender_identity()

        try:
            payload_dict = json.loads(body)
        except json.JSONDecodeError:
            return _reject("body_invalid_json", sender_identity=sender_id)
        if not isinstance(payload_dict, dict):
            return _reject("body_invalid_json", sender_identity=sender_id)

        idempotency_key = payload_dict.get("idempotency_key")
        if not isinstance(idempotency_key, str) or not idempotency_key:
            # Spec 3.0-rc: idempotency_key is REQUIRED on every webhook payload.
            return _reject("idempotency_key_missing", sender_identity=sender_id)
        if not _IDEMPOTENCY_KEY_RE.match(idempotency_key):
            # Non-conformant format — charset or length out of bounds.
            return _reject("idempotency_key_invalid", sender_identity=sender_id)

        parsed = self._parse(payload_dict)
        if parsed is None:
            return _reject("payload_invalid", sender_identity=sender_id)

        is_first_seen = await self._config.dedup.check_and_record(
            sender_id=sender_id, idempotency_key=idempotency_key
        )

        return WebhookOutcome(
            sender_identity=sender_id,
            payload=parsed,
            duplicate=not is_first_seen,
            idempotency_key=idempotency_key,
        )

    async def _verify(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
    ) -> tuple[VerifiedSignerLike | None, WebhookOutcome | None]:
        """Returns (signer, None) on success or (None, rejection_outcome)."""
        has_9421 = _has_9421_headers(headers)

        if has_9421:
            try:
                signer = verify_webhook_signature(
                    method=method,
                    url=url,
                    headers=headers,
                    body=body,
                    options=self._config.verify_options,
                )
                return signer, None
            except SignatureVerificationError as exc:
                # Downgrade defense: when 9421 IS present but fails, do NOT
                # consult HMAC fallback by default. A MITM that stripped a
                # valid 9421 signature and replaced it with a forged HMAC one
                # is exactly what the downgrade guard exists for.
                fallback = self._config.legacy_hmac
                allow_hmac = fallback is not None and not fallback.only_when_9421_absent
                if not allow_hmac:
                    return None, WebhookOutcome(
                        rejected=True,
                        rejection_reason="signature_invalid",
                        response_headers=_www_authenticate_header(exc.code),
                    )
                logger.warning(
                    "9421 webhook verify failed (%s); trying HMAC legacy because "
                    "legacy_hmac.only_when_9421_absent=False is set",
                    exc.code,
                )

        fallback = self._config.legacy_hmac
        if fallback is None:
            # No 9421 headers AND no HMAC fallback configured → spec says 9421
            # is baseline-required in 3.0, so this is non-conformant.
            return None, WebhookOutcome(
                rejected=True,
                rejection_reason="signature_missing",
                response_headers=_www_authenticate_header("webhook_signature_required"),
            )

        hmac_options = fallback.options_for(headers)
        if hmac_options is None:
            return None, WebhookOutcome(
                rejected=True,
                rejection_reason="signature_missing",
                response_headers=_www_authenticate_header("webhook_signature_required"),
            )
        try:
            legacy_signer = verify_webhook_hmac(headers=headers, body=body, options=hmac_options)
            return legacy_signer, None
        except LegacyWebhookHmacError:
            return None, WebhookOutcome(
                rejected=True,
                rejection_reason="signature_legacy_failed",
                response_headers=_www_authenticate_header("webhook_signature_invalid"),
            )

    def _parse(self, payload_dict: dict[str, Any]) -> WebhookPayload | None:
        model = _MODEL_BY_KIND[self._config.kind]
        try:
            return cast(WebhookPayload, model.model_validate(payload_dict))
        except ValidationError as exc:
            # Operators need the field-level reason to diagnose sender bugs.
            # The receiver still returns payload_invalid downstream; this is
            # just observability.
            logger.warning(
                "webhook payload failed %s validation: %s",
                self._config.kind,
                exc.errors(include_url=False),
            )
            return None


def _has_9421_headers(headers: Mapping[str, str]) -> bool:
    """True only when BOTH 9421 headers are present.

    Requiring both prevents a malformed single-header attempt from blocking
    HMAC fallback: if a sender emits only ``Signature-Input`` (without
    ``Signature``) and the receiver has legacy HMAC configured, we want the
    HMAC path to run, not the 9421 header-malformed rejection.
    """
    lowered = {str(k).lower() for k in headers.keys()}
    return "signature-input" in lowered and "signature" in lowered


def _content_type_is_json(headers: Mapping[str, str]) -> bool:
    """Require application/json (the 9421 profile signs content-type, but the
    receiver still must reject obvious mismatches before parsing)."""
    for k, v in headers.items():
        if str(k).lower() == "content-type":
            ct = str(v).split(";", 1)[0].strip().lower()
            return ct in _ACCEPTED_CONTENT_TYPES
    return False


# Known webhook_signature_* codes — used to validate WWW-Authenticate values.
# Anything else (e.g. a future code, or an attacker-influenced string) gets
# replaced with WEBHOOK_SIGNATURE_INVALID so we never emit untrusted data in
# a response header.
_VALID_WWW_AUTHENTICATE_CODES = frozenset(
    {
        "webhook_signature_required",
        "webhook_signature_invalid",
        "webhook_signature_header_malformed",
        "webhook_signature_params_incomplete",
        "webhook_signature_tag_invalid",
        "webhook_signature_alg_not_allowed",
        "webhook_signature_window_invalid",
        "webhook_signature_components_incomplete",
        "webhook_signature_components_unexpected",
        "webhook_signature_key_unknown",
        "webhook_signature_key_purpose_invalid",
        "webhook_signature_digest_mismatch",
        "webhook_signature_replayed",
        "webhook_signature_key_revoked",
        "webhook_signature_revocation_stale",
        "webhook_signature_jwks_unavailable",
        "webhook_signature_jwks_untrusted",
        "webhook_signature_rate_abuse",
    }
)


def _www_authenticate_header(code: str) -> dict[str, str]:
    """401-response header per spec — realm intentionally omitted.

    Code is whitelisted against known webhook_signature_* values so a
    future contributor passing an unchecked string can't inject CR/LF into
    a response header.
    """
    safe_code = code if code in _VALID_WWW_AUTHENTICATE_CODES else "webhook_signature_invalid"
    return {"WWW-Authenticate": f'Signature error="{safe_code}"'}


def _reject(reason: RejectionReason, *, sender_identity: str | None) -> WebhookOutcome:
    return WebhookOutcome(
        rejected=True,
        rejection_reason=reason,
        sender_identity=sender_identity,
        response_headers={},  # 400/422 — non-auth failure, no WWW-Authenticate
    )


_MODEL_BY_KIND: dict[WebhookKind, type[Any]] = {
    "mcp": McpWebhookPayload,
    "revocation_notification": RevocationNotification,
    "collection_list_changed": CollectionListChangedWebhook,
    "property_list_changed": PropertyListChangedWebhook,
    "artifact": ArtifactWebhookPayload,
}


__all__ = [
    "LegacyHmacFallback",
    "VerifiedSignerLike",
    "WebhookKind",
    "WebhookOutcome",
    "WebhookPayload",
    "WebhookReceiver",
    "WebhookReceiverConfig",
]
