"""Tests for the legacy HMAC-SHA256 webhook verifier.

The wire format must match :func:`adcp.webhooks.get_adcp_signed_headers_for_webhook`.
We sign with that function and verify with :func:`verify_webhook_hmac` to catch
any accidental divergence between sender and receiver.
"""

from __future__ import annotations

import json
import time

import pytest

from adcp.webhooks import (
    LegacyWebhookHmacError,
    LegacyWebhookHmacOptions,
    get_adcp_signed_headers_for_webhook,
    verify_webhook_hmac,
)


def _sign_body(
    secret: str, payload: dict, timestamp: str | None = None
) -> tuple[bytes, dict[str, str], str]:
    """Sign a payload and return (raw_body, headers, timestamp)."""
    if timestamp is None:
        timestamp = str(int(time.time()))
    headers = {"Content-Type": "application/json"}
    get_adcp_signed_headers_for_webhook(
        headers=headers, secret=secret, timestamp=timestamp, payload=payload
    )
    # The existing sender uses json.dumps(payload_dict) without sort_keys —
    # receiver MUST verify against the raw bytes the sender emitted, which
    # means we serialize once here and use the same bytes on both sides.
    raw = json.dumps(payload).encode("utf-8")
    return raw, headers, timestamp


def test_roundtrip_verifies() -> None:
    secret = "s" * 32
    ts = str(int(time.time()))
    body, headers, _ = _sign_body(secret, {"idempotency_key": "whk_1", "task_id": "t1"}, ts)

    result = verify_webhook_hmac(
        headers=headers,
        body=body,
        options=LegacyWebhookHmacOptions(
            secret=secret.encode(),
            sender_identity="test-sender",
            now=float(int(ts)),
        ),
    )
    assert result.as_sender_identity() == "test-sender"


def test_rejects_tampered_body() -> None:
    secret = "s" * 32
    ts = str(int(time.time()))
    body, headers, _ = _sign_body(secret, {"idempotency_key": "whk_1", "task_id": "t1"}, ts)

    with pytest.raises(LegacyWebhookHmacError):
        verify_webhook_hmac(
            headers=headers,
            body=body + b" ",
            options=LegacyWebhookHmacOptions(
                secret=secret.encode(),
                sender_identity="test-sender",
                now=float(int(ts)),
            ),
        )


def test_rejects_wrong_secret() -> None:
    ts = str(int(time.time()))
    body, headers, _ = _sign_body(
        "real-secret-padding-to-16-chars", {"idempotency_key": "whk_1"}, ts
    )

    with pytest.raises(LegacyWebhookHmacError):
        verify_webhook_hmac(
            headers=headers,
            body=body,
            options=LegacyWebhookHmacOptions(
                secret=b"wrong-secret-padded-long-enough",
                sender_identity="test-sender",
                now=float(int(ts)),
            ),
        )


def test_rejects_stale_timestamp() -> None:
    secret = "s" * 32
    ts = str(int(time.time()))
    body, headers, _ = _sign_body(secret, {"idempotency_key": "whk_1"}, ts)

    with pytest.raises(LegacyWebhookHmacError, match="skew"):
        verify_webhook_hmac(
            headers=headers,
            body=body,
            options=LegacyWebhookHmacOptions(
                secret=secret.encode(),
                sender_identity="test-sender",
                now=float(int(ts)) + 10_000,  # Well outside window
            ),
        )


def test_rejects_missing_signature() -> None:
    with pytest.raises(LegacyWebhookHmacError, match="missing"):
        verify_webhook_hmac(
            headers={"Content-Type": "application/json"},
            body=b'{"idempotency_key":"whk_1"}',
            options=LegacyWebhookHmacOptions(
                secret=b"s" * 32,
                sender_identity="test-sender",
                now=float(int(time.time())),
            ),
        )


def test_rejects_wrong_prefix() -> None:
    ts = str(int(time.time()))
    with pytest.raises(LegacyWebhookHmacError, match="must start with"):
        verify_webhook_hmac(
            headers={
                "Content-Type": "application/json",
                "X-AdCP-Signature": "md5=abc",
                "X-AdCP-Timestamp": ts,
            },
            body=b"{}",
            options=LegacyWebhookHmacOptions(
                secret=b"s" * 32,
                sender_identity="test-sender",
                now=float(int(ts)),
            ),
        )
