"""Storage backends for :class:`~adcp.server.idempotency.IdempotencyStore`.

A backend owns two responsibilities:

1. Retrieve a cached response by ``(principal_id, idempotency_key)``, honoring
   the seller's replay TTL.
2. Atomically commit ``(payload_hash, response)`` on a fresh key. Atomicity
   with the handler's business writes is the backend's choice — :class:`MemoryBackend`
   makes no such guarantee; :class:`PgBackend` (follow-up) will when the handler
   uses the same engine.

Backends expose async methods. The in-process :class:`MemoryBackend` is
synchronous under the hood but wrapped in ``async`` signatures so the store
can remain backend-agnostic.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CachedResponse:
    """A single cached handler response keyed by ``(principal_id, key)``.

    :param payload_hash: Canonical JSON SHA-256 of the *original* request. On
        replay we compare the new request's hash to this value; mismatch is
        ``IDEMPOTENCY_CONFLICT``.
    :param response: The response dict the handler returned. Returned verbatim
        on replay — the seller injects ``replayed: true`` at the envelope
        level before sending.
    :param expires_at_epoch: Unix timestamp (seconds) when this entry becomes
        eligible for eviction. Reads after this time return None.
    """

    payload_hash: str
    response: dict[str, Any]
    expires_at_epoch: float


class IdempotencyBackend(ABC):
    """Abstract storage backend contract.

    All methods are async. Implementations MUST be safe to call concurrently
    from multiple asyncio tasks — :class:`IdempotencyStore` does not serialize
    access on the caller's behalf.
    """

    @abstractmethod
    async def get(
        self, principal_id: str, key: str
    ) -> CachedResponse | None:
        """Return the cached entry, or None if missing or expired."""

    @abstractmethod
    async def put(
        self,
        principal_id: str,
        key: str,
        entry: CachedResponse,
    ) -> None:
        """Store ``entry`` under ``(principal_id, key)``. Overwrites any prior
        entry — the store only calls ``put`` after verifying the slot is empty
        or expired, so an overwrite in that window is a legitimate retry of
        the write itself."""

    @abstractmethod
    async def delete_expired(self, now_epoch: float | None = None) -> int:
        """Best-effort sweep of expired entries. Returns the count removed.

        Sweeping is optional — :meth:`get` MUST self-filter expired entries.
        Backends that have natural TTL primitives (Redis ``EXPIRE``, Postgres
        partial indexes) may implement this as a no-op."""


class MemoryBackend(IdempotencyBackend):
    """In-process dict-backed store.

    Suitable for tests, single-process reference implementations, and local
    development. **Not suitable for multi-process deployments** — each worker
    has its own cache, so a retry that lands on a different worker is treated
    as a fresh request.

    Thread safety: the backend uses an :class:`asyncio.Lock` to serialize
    mutations of the shared dict. Reads go through the lock too; for a pure
    in-process backend this is cheap and prevents torn reads across concurrent
    ``get``/``put`` interleaving.

    :param clock: Callable returning the current epoch seconds. Override for
        tests that need to advance time deterministically without monkeypatching
        :mod:`time`. Defaults to :func:`time.time`.
    """

    def __init__(self, *, clock: Callable[[], float] = time.time) -> None:
        self._store: dict[tuple[str, str], CachedResponse] = {}
        self._lock = asyncio.Lock()
        self._clock = clock

    async def get(
        self, principal_id: str, key: str
    ) -> CachedResponse | None:
        async with self._lock:
            entry = self._store.get((principal_id, key))
            if entry is None:
                return None
            if entry.expires_at_epoch <= self._clock():
                # Lazy expiry — drop the stale entry so the next request
                # treats the slot as fresh and races to repopulate.
                del self._store[(principal_id, key)]
                return None
            return entry

    async def put(
        self,
        principal_id: str,
        key: str,
        entry: CachedResponse,
    ) -> None:
        async with self._lock:
            self._store[(principal_id, key)] = entry

    async def delete_expired(self, now_epoch: float | None = None) -> int:
        cutoff = now_epoch if now_epoch is not None else self._clock()
        async with self._lock:
            stale = [k for k, v in self._store.items() if v.expires_at_epoch <= cutoff]
            for k in stale:
                del self._store[k]
            return len(stale)

    async def clear(self) -> None:
        """Remove all cached entries.

        Test-suite hook — handy for resetting state between fixtures when a
        single :class:`MemoryBackend` is shared across multiple tests.
        """
        async with self._lock:
            self._store.clear()

    async def _size(self) -> int:
        """Test-only: return the current entry count."""
        async with self._lock:
            return len(self._store)


class PgBackend(IdempotencyBackend):
    """PostgreSQL-backed store — **scaffold, not yet implemented**.

    .. warning::
       Calling ``PgBackend(...)`` raises ``NotImplementedError`` today. Use
       :class:`MemoryBackend` for tests, or implement your own
       :class:`IdempotencyBackend` subclass against the database of your
       choice until this implementation lands. Tracked at
       https://github.com/adcontextprotocol/adcp-client-python/issues/182.

    **Design intent.** Share a transaction with the handler's business
    writes so the cache entry commits atomically with side effects. Without
    that, a crash between ``handler success`` and ``cache commit`` causes
    the retry to re-execute the handler, duplicating side effects.

    **Schema sketch for the implementer.**

    .. code-block:: sql

        CREATE TABLE adcp_idempotency (
            principal_id TEXT       COLLATE "C" NOT NULL,
            key          TEXT       COLLATE "C" NOT NULL,
            payload_hash TEXT       NOT NULL,
            response     JSONB      NOT NULL,
            expires_at   TIMESTAMPTZ NOT NULL,
            PRIMARY KEY (principal_id, key)
        );

    Notes:

    * ``COLLATE "C"`` (or ``CITEXT`` with a deliberate case policy) — avoid
      the default locale collation on the identifier columns. On some
      locales ``Principal-A`` and ``principal-a`` compare equal, which
      would collapse distinct tenants into the same cache slot.
    * Queries MUST filter on ``principal_id`` in the ``WHERE`` clause even
      with the composite PK — row-level security (RLS) enforced via a
      policy like ``USING (principal_id = current_setting('adcp.principal_id')::text)``
      gives belt-and-suspenders protection against accidental cross-tenant
      reads in future handlers.
    * ``get`` uses ``SELECT ... WHERE expires_at > now()``.
    * ``put`` uses ``INSERT ... ON CONFLICT (principal_id, key) DO UPDATE``.
    * Accept a SQLAlchemy/asyncpg session factory so the caller can thread
      the handler's transaction through for atomic commit — the atomicity
      guarantee is the whole reason to use a SQL backend.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(
            "PgBackend is scaffolded but not yet implemented. Use MemoryBackend "
            "for tests, or implement your own IdempotencyBackend subclass "
            "against your database of choice until the PgBackend implementation "
            "lands. Tracking: "
            "https://github.com/adcontextprotocol/adcp-client-python/issues/182."
        )

    async def get(
        self, principal_id: str, key: str
    ) -> CachedResponse | None:  # pragma: no cover
        raise NotImplementedError

    async def put(
        self,
        principal_id: str,
        key: str,
        entry: CachedResponse,
    ) -> None:  # pragma: no cover
        raise NotImplementedError

    async def delete_expired(
        self, now_epoch: float | None = None
    ) -> int:  # pragma: no cover
        raise NotImplementedError
