"""Tests for the webhook receiver-side dedup store."""

from __future__ import annotations

import pytest

from adcp.server.idempotency import MemoryBackend, WebhookDedupStore


@pytest.fixture
def store() -> WebhookDedupStore:
    return WebhookDedupStore(MemoryBackend(), ttl_seconds=86400)


@pytest.mark.asyncio
async def test_first_seen_returns_true(store: WebhookDedupStore) -> None:
    assert await store.check_and_record("sender-1", "whk_abc") is True


@pytest.mark.asyncio
async def test_repeat_returns_false(store: WebhookDedupStore) -> None:
    await store.check_and_record("sender-1", "whk_abc")
    assert await store.check_and_record("sender-1", "whk_abc") is False


@pytest.mark.asyncio
async def test_different_senders_independent(store: WebhookDedupStore) -> None:
    """Per-sender scoping: the same key from a different sender is fresh."""
    await store.check_and_record("sender-1", "whk_abc")
    assert await store.check_and_record("sender-2", "whk_abc") is True


@pytest.mark.asyncio
async def test_different_keys_independent(store: WebhookDedupStore) -> None:
    await store.check_and_record("sender-1", "whk_a")
    assert await store.check_and_record("sender-1", "whk_b") is True


@pytest.mark.asyncio
async def test_ttl_expiry_allows_reprocess() -> None:
    """Entries past TTL reprocess as fresh — matches spec's 'retries outside
    window are reprocessed' guidance."""
    clock = [1_000_000.0]
    store = WebhookDedupStore(
        MemoryBackend(clock=lambda: clock[0]),
        ttl_seconds=86400,
        clock=lambda: clock[0],
    )

    assert await store.check_and_record("sender-1", "whk_abc") is True
    clock[0] += 86400 + 1  # Advance past TTL
    assert await store.check_and_record("sender-1", "whk_abc") is True


@pytest.mark.asyncio
async def test_rejects_empty_sender(store: WebhookDedupStore) -> None:
    with pytest.raises(ValueError):
        await store.check_and_record("", "whk_abc")


@pytest.mark.asyncio
async def test_rejects_empty_key(store: WebhookDedupStore) -> None:
    with pytest.raises(ValueError):
        await store.check_and_record("sender-1", "")


def test_ttl_spec_bounds() -> None:
    # Below minimum (<24h) should reject — spec contract from webhooks.mdx
    # "Dedup state SHOULD persist for at least 24h".
    with pytest.raises(ValueError, match="ttl_seconds"):
        WebhookDedupStore(MemoryBackend(), ttl_seconds=3600)
    # Over 7 days
    with pytest.raises(ValueError, match="ttl_seconds"):
        WebhookDedupStore(MemoryBackend(), ttl_seconds=604801)
