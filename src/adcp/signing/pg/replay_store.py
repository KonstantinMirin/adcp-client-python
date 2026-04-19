"""PostgreSQL-backed :class:`~adcp.signing.ReplayStore` implementation.

Gives multi-instance AdCP verifiers a shared nonce-seen store so a
replay accepted on worker A can't land again on worker B within the
signature's validity window.

The caller supplies a :class:`psycopg_pool.ConnectionPool`. We don't
open, own, or close the pool — integrators typically already have one
for their main database and sharing it is cleaner than a second pool.

Schema
------

See :file:`adcp/signing/pg/replay_store.sql`. Run it once per
deployment, then instantiate::

    from psycopg_pool import ConnectionPool
    from adcp.signing.pg import PgReplayStore

    pool = ConnectionPool("postgresql://...", min_size=4, max_size=20)
    replay = PgReplayStore(pool=pool)

Sweep
-----

:meth:`seen` self-filters via ``expires_at > now()``, so lookups never
return stale entries. Rows accumulate, though — schedule a periodic
sweep (pg cron, app cron, whatever) running::

    DELETE FROM adcp_replay WHERE expires_at <= now();

Or call :meth:`sweep_expired` from an admin endpoint if you prefer an
in-process sweep.

Failure mode
------------

Transport or connection errors propagate as-is (psycopg's
``OperationalError``, etc.). The verifier treats any exception from
the replay store as a verification failure — this matches the
fail-closed posture the spec requires: a broken replay store MUST
reject requests, never silently pass.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psycopg_pool import ConnectionPool

try:
    import psycopg  # noqa: F401
    import psycopg_pool  # noqa: F401

    PG_AVAILABLE = True
except ImportError:
    PG_AVAILABLE = False


logger = logging.getLogger(__name__)

DEFAULT_TABLE_NAME = "adcp_replay"

_INSTALL_HINT = (
    "PgReplayStore requires psycopg3 and psycopg-pool. Install the 'pg' "
    "extra: `pip install 'adcp[pg]'`."
)


class PgReplayStore:
    """PostgreSQL-backed replay store implementing :class:`ReplayStore`.

    Parameters
    ----------
    pool:
        A :class:`psycopg_pool.ConnectionPool` owned by the caller. Each
        operation acquires a short-lived connection, runs a single
        statement, and returns the connection. No long-lived
        transactions, no cross-operation state.
    per_keyid_cap:
        Maximum number of live (non-expired) nonces per ``keyid``.
        Mirrors :class:`InMemoryReplayStore`; spec-recommended 1M.
        When :meth:`at_capacity` reports True, the verifier rejects
        with ``request_signature_rate_abuse`` rather than silently
        evicting older entries (which would create a replay window
        under attack).
    table_name:
        Override the default ``adcp_replay`` table if two tenants share
        a database and need separate replay stores. Must be a
        byte-equal-clean identifier — we don't quote it into the SQL
        dynamically for obvious injection reasons; the constructor
        validates shape.

    Concurrency
    -----------

    Safe to share across threads and processes. Postgres provides the
    cross-instance locking we need via PK conflict resolution on
    ``INSERT ... ON CONFLICT``.
    """

    def __init__(
        self,
        *,
        pool: ConnectionPool,
        per_keyid_cap: int = 1_000_000,
        table_name: str = DEFAULT_TABLE_NAME,
    ) -> None:
        if not PG_AVAILABLE:
            raise ImportError(_INSTALL_HINT)
        if not _is_safe_identifier(table_name):
            raise ValueError(f"table_name must be [a-z_][a-z0-9_]*, got {table_name!r}")
        self._pool = pool
        self._per_keyid_cap = per_keyid_cap
        self._table = table_name

        # Pre-format queries with the validated table name so the hot
        # path doesn't f-string per call.
        self._sql_seen = (
            f"SELECT 1 FROM {self._table} "  # noqa: S608 — table name is whitelisted
            f"WHERE keyid = %s AND nonce = %s AND expires_at > now()"
        )
        self._sql_remember = (
            f"INSERT INTO {self._table} (keyid, nonce, expires_at) "  # noqa: S608
            f"VALUES (%s, %s, now() + make_interval(secs => %s)) "
            f"ON CONFLICT (keyid, nonce) DO UPDATE "
            f"SET expires_at = EXCLUDED.expires_at"
        )
        self._sql_at_capacity = (
            f"SELECT COUNT(*) >= %s FROM {self._table} "  # noqa: S608
            f"WHERE keyid = %s AND expires_at > now()"
        )
        self._sql_sweep = f"DELETE FROM {self._table} WHERE expires_at <= now()"  # noqa: S608

    # -- ReplayStore Protocol -----------------------------------------

    def seen(self, keyid: str, nonce: str) -> bool:
        """Return True iff ``(keyid, nonce)`` has a live entry."""
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(self._sql_seen, (keyid, nonce))
            return cur.fetchone() is not None

    def remember(self, keyid: str, nonce: str, ttl_seconds: float) -> None:
        """Record ``(keyid, nonce)`` with a TTL.

        ``ON CONFLICT ... DO UPDATE`` refreshes the expiry on a
        legitimate retry of the same nonce in-window — matches
        :class:`InMemoryReplayStore` behavior.
        """
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(self._sql_remember, (keyid, nonce, ttl_seconds))

    def at_capacity(self, keyid: str) -> bool:
        """Return True iff the live row count for ``keyid`` meets the cap.

        Implementation note: ``COUNT(*) >= cap`` with the partial index
        on ``(keyid) WHERE expires_at > now()`` is the fast path.
        Without the partial index, this is a PK+predicate scan — still
        O(live rows for keyid) but an index-only scan. For the
        spec-recommended 1M cap, the expensive case is exactly when a
        signer is misbehaving, so paying for accuracy is the right
        trade.
        """
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(self._sql_at_capacity, (self._per_keyid_cap, keyid))
            row = cur.fetchone()
            return bool(row[0]) if row is not None else False

    # -- admin / cron ------------------------------------------------

    def sweep_expired(self) -> int:
        """Delete all rows whose ``expires_at`` is in the past.

        Returns the number of rows removed. Safe to call concurrently
        with :meth:`seen` / :meth:`remember`.

        Call from a cron or admin endpoint. :meth:`seen` self-filters
        so expired rows never cause false positives, but they do
        accumulate and grow the table.
        """
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(self._sql_sweep)
            return cur.rowcount or 0

    def live_count(self, keyid: str) -> int:
        """Return the number of live (non-expired) rows for ``keyid``.

        Mostly useful for tests, monitoring, and admin tooling. Not on
        the :class:`ReplayStore` Protocol — hit-path code should call
        :meth:`at_capacity` which short-circuits at the cap without
        materializing the count.
        """
        sql = (
            f"SELECT COUNT(*) FROM {self._table} "  # noqa: S608
            f"WHERE keyid = %s AND expires_at > now()"
        )
        with self._pool.connection() as conn, conn.cursor() as cur:
            cur.execute(sql, (keyid,))
            row = cur.fetchone()
            return int(row[0]) if row is not None else 0


def _is_safe_identifier(name: str) -> bool:
    """Allow only lowercase ASCII identifiers for the table-name kwarg.

    We format this value into SQL statically (once at construction),
    so the injection surface is already tiny — but the validation here
    keeps the contract obvious to future maintainers. Matches what
    Postgres considers a "simple" identifier (no quoting required).
    """
    if not name:
        return False
    if not (name[0].isalpha() or name[0] == "_"):
        return False
    for ch in name:
        if not (ch.islower() or ch.isdigit() or ch == "_"):
            return False
    return len(name) <= 63  # Postgres NAMEDATALEN default


__all__ = ["PG_AVAILABLE", "DEFAULT_TABLE_NAME", "PgReplayStore"]
