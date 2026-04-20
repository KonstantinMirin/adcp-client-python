"""Webhook receiver-side dedup store.

Reuses :class:`IdempotencyBackend` (same Memory / Pg backends as the
request-side store) but has different semantics, per the adcp webhook
receiver requirements:

* No payload-hash equivalence check. The spec explicitly says receivers do
  NOT verify payload equivalence across key reuse — first copy wins, any
  later copy with the same key is silently deduped. Sender bugs that reuse
  a key with a changed payload are a sender problem.
* No ``IDEMPOTENCY_CONFLICT`` raise path. A duplicate is a no-op, not an
  error — receivers MUST return 2xx on a duplicate so the at-least-once
  sender's retry back-off doesn't fire.
* 24h default TTL (the spec minimum). Webhook senders SHOULD NOT retry
  beyond that window; entries arriving later are reprocessed as fresh
  events.

Dedup scope MUST be ``(authenticated_sender_identity, idempotency_key)``.
"Authenticated sender" means the 9421 verified ``keyid`` (or HMAC
credential), never a payload field — passing a payload-derived string in
here is an accident the receiver API should make awkward. The
:class:`adcp.signing.webhook_verifier.VerifiedWebhookSender.as_sender_identity`
helper gives you the right value.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from adcp.server.idempotency.backends import CachedResponse, IdempotencyBackend

logger = logging.getLogger(__name__)

# Spec bound: 24h minimum. Upper bound matches the request-side store (7 days) —
# webhooks have no reason to cache longer.
_MIN_TTL_SECONDS = 86400
_MAX_TTL_SECONDS = 604800

# Sentinel stored in the backend's payload_hash slot. We don't hash a payload
# for webhook dedup, but the shared backend contract requires the field.
_SENTINEL_HASH = "webhook-dedup"


class WebhookDedupStore:
    """Dedup ``(sender_id, idempotency_key)`` pairs to suppress retried webhooks.

    :param backend: any :class:`IdempotencyBackend`. Same MemoryBackend or
        PgBackend type used by :class:`IdempotencyStore` is fine — the
        ``namespace`` parameter prefixes all sender IDs so request-side and
        webhook-side scopes can't alias even when sharing one backend instance.
    :param ttl_seconds: replay window. Must be within ``[86400, 604800]`` per
        the spec minimum. Defaults to 86400 (24h).
    :param namespace: prefix applied to every ``sender_id`` before it hits
        the backend. Defaults to ``"webhook"``, which is safe when the same
        backend is shared with :class:`IdempotencyStore` (request-side keys
        are scoped by a principal_id that isn't wrapped in this namespace,
        so collisions are impossible). Override only if you run multiple
        webhook scopes against one backend (e.g., separate dedup spaces for
        task webhooks vs list-change webhooks).
    """

    def __init__(
        self,
        backend: IdempotencyBackend,
        ttl_seconds: int = _MIN_TTL_SECONDS,
        *,
        namespace: str = "webhook",
        clock: Callable[[], float] = time.time,
    ) -> None:
        if not _MIN_TTL_SECONDS <= ttl_seconds <= _MAX_TTL_SECONDS:
            raise ValueError(
                f"ttl_seconds must be in [{_MIN_TTL_SECONDS}, {_MAX_TTL_SECONDS}] "
                f"per webhook spec minimum, got {ttl_seconds}"
            )
        if not namespace:
            raise ValueError("namespace must be a non-empty string")
        self.backend = backend
        self.ttl_seconds = ttl_seconds
        self.namespace = namespace
        self._clock = clock

    async def check_and_record(self, sender_id: str, idempotency_key: str) -> bool:
        """Atomically check for first-seen and record if new.

        Returns ``True`` when the pair is first-seen (event should be
        processed), ``False`` on duplicate (caller MUST still return 2xx to
        the sender — the event was delivered successfully, it's just a retry).

        Race note: the check-then-put pattern is not atomic across concurrent
        callers unless the backend provides its own atomicity. MemoryBackend
        serializes individual ``get`` and ``put`` under an ``asyncio.Lock`` but
        does NOT bracket them together — two concurrent retries of the same
        event CAN both observe "first-seen" and both process the event. That's
        a tolerable failure mode: the ultimate guarantee is "at most once per
        replay window in the common case"; a concurrent retry arriving in the
        same few milliseconds is rare and, if it happens, produces the same
        "duplicated side effect" outcome the at-least-once contract already
        warns callers to tolerate. PgBackend implementations SHOULD use
        ``INSERT ... ON CONFLICT DO NOTHING`` returning ``rowcount`` for
        lock-free atomicity.
        """
        if not sender_id:
            raise ValueError("sender_id must be a non-empty string")
        if not idempotency_key:
            raise ValueError("idempotency_key must be a non-empty string")

        scoped_sender = f"{self.namespace}:{sender_id}"
        existing = await self.backend.get(scoped_sender, idempotency_key)
        if existing is not None:
            logger.debug(
                "webhook dedup: duplicate sender=%s key_prefix=%s",
                sender_id,
                idempotency_key[:8],
            )
            return False

        entry = CachedResponse(
            payload_hash=_SENTINEL_HASH,
            response={},
            expires_at_epoch=self._clock() + self.ttl_seconds,
        )
        try:
            await self.backend.put(scoped_sender, idempotency_key, entry)
        except Exception:
            # Same fail-open reasoning as the request-side store: log and
            # process. Swallowing the put failure means this event MIGHT
            # reprocess on retry, not that we drop it. Better than raising,
            # which would look like handler failure to the sender.
            logger.warning(
                "webhook dedup put failed for sender=%s key_prefix=%s — "
                "event processed but next retry will reprocess",
                sender_id,
                idempotency_key[:8],
                exc_info=True,
            )
        return True


__all__ = ["WebhookDedupStore"]
