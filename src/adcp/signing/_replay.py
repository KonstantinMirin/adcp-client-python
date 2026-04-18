"""Replay dedup store for the AdCP request-signing profile.

Stores `(keyid, nonce)` pairs that have already been accepted, with a TTL that
mirrors the signature's `expires` parameter plus skew. A per-keyid cap prevents
unbounded growth — when the cap is hit, new signatures for that keyid are
rejected with `request_signature_rate_abuse` rather than silently evicting
older entries (which would create a replay window under attack).

Thread-safe within a process; not shared across processes — see issue #187 for
a Redis adapter for multi-instance verifiers.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Protocol


class ReplayStore(Protocol):
    """Minimum interface a replay backend must expose."""

    def seen(self, keyid: str, nonce: str) -> bool: ...

    def remember(self, keyid: str, nonce: str, ttl_seconds: float) -> None: ...

    def at_capacity(self, keyid: str) -> bool: ...


# Cap on the number of expired entries swept per mutating call. Bounded so that
# a single `remember` / `seen` stays O(1) amortized on a well-behaved workload;
# natural inserts and lookups sweep incrementally.
_SWEEP_BATCH = 16


class InMemoryReplayStore:
    """Process-local replay store. Uses a monotonic clock for TTL bookkeeping so
    wall-clock jumps (NTP adjustments, VM suspend/resume) don't race eviction.
    """

    def __init__(
        self,
        *,
        per_keyid_cap: int = 1_000_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._per_keyid_cap = per_keyid_cap
        self._clock = clock
        self._entries: dict[tuple[str, str], float] = {}
        self._counts: dict[str, int] = {}
        self._cap_hit: set[str] = set()
        self._lock = threading.RLock()

    def seen(self, keyid: str, nonce: str) -> bool:
        with self._lock:
            self._expire_one(keyid, nonce)
            return (keyid, nonce) in self._entries

    def remember(self, keyid: str, nonce: str, ttl_seconds: float) -> None:
        with self._lock:
            self._sweep_for_keyid(keyid)
            key = (keyid, nonce)
            if key not in self._entries:
                self._counts[keyid] = self._counts.get(keyid, 0) + 1
            self._entries[key] = self._clock() + ttl_seconds

    def at_capacity(self, keyid: str) -> bool:
        with self._lock:
            if keyid in self._cap_hit:
                return True
            return self._counts.get(keyid, 0) >= self._per_keyid_cap

    def mark_cap_hit(self, keyid: str) -> None:
        """Test-harness hook — simulate the cap being reached for this keyid."""
        with self._lock:
            self._cap_hit.add(keyid)

    def _expire_one(self, keyid: str, nonce: str) -> None:
        key = (keyid, nonce)
        expiry = self._entries.get(key)
        if expiry is not None and expiry < self._clock():
            del self._entries[key]
            self._counts[keyid] = self._counts.get(keyid, 1) - 1
            if self._counts[keyid] <= 0:
                self._counts.pop(keyid, None)

    def _sweep_for_keyid(self, keyid: str) -> None:
        now = self._clock()
        removed = 0
        # Scan only entries for this keyid to bound per-call work under load.
        for key, expiry in list(self._entries.items()):
            if key[0] != keyid:
                continue
            if expiry < now:
                del self._entries[key]
                self._counts[keyid] = self._counts.get(keyid, 1) - 1
                if self._counts[keyid] <= 0:
                    self._counts.pop(keyid, None)
                removed += 1
                if removed >= _SWEEP_BATCH:
                    return
