"""Example: A2A agent with a durable, scope-isolated SQLite-backed ``TaskStore``.

A2A's default ``InMemoryTaskStore`` is single-process and non-durable —
fine for demos but tasks vanish on restart. Production agents need a
durable store so long-running operations survive process restarts and
can be resumed by whichever worker picks up the request.

This example wires up a minimal SQLite-backed store that implements
``a2a.server.tasks.task_store.TaskStore``. SQLite is the right reference
target: it's in the stdlib, needs no infrastructure, and the SQL
pattern translates directly to Postgres / MySQL / etc. for production.

**Security model — tenant-scoped lookups.** The ``TaskStore`` ABC passes
a ``ServerCallContext`` carrying the authenticated user on every call.
**Ignoring it is a cross-tenant data leak**: any principal that learns
(or guesses) a task id owned by another tenant retrieves that tenant's
full task — including history, artifacts, and any caller-supplied PII
in ``Message.parts``. This store derives a ``scope`` column from
``context.user.user_name`` and filters every read/write by it, so a
request arriving with a different principal never sees another
tenant's task. Sellers with richer identity (a typed ``tenant_id``,
organization IDs, etc.) should override ``_scope_from_context`` to
return *their* scope key — the lookup filter then follows automatically.

**Not production-ready.** Remaining gaps for real deployments:

- Postgres/MySQL + async driver (asyncpg / aiomysql).
- Transactional atomicity with the handler's business writes —
  same-engine transaction so a crash between "handler success" and
  "task save" doesn't duplicate side effects.
- Connection pooling.
- Row-level TTL / garbage collection for completed tasks.
- Optimistic concurrency: ``INSERT OR REPLACE`` below is
  last-writer-wins. Two in-flight ``save()`` calls on the same task
  interleave with no version check; a slow ``save(working)`` landing
  after a fast ``save(completed)`` will revert the state. Production
  stores need ``WHERE updated_at < ?`` guards or a version column.
- ``Task.model_dump_json`` includes ``history`` (buyer-supplied
  messages, artifact metadata). Persisting it makes plaintext
  conversation content land on disk — protect the database file
  (encryption at rest, backup access control) and consider
  field-level redaction before writing.
- Shared-host file permissions: this example sets the SQLite file
  mode to 0o600 on first creation so a co-tenant process on the same
  machine can't read it. A migration that recreates the file inherits
  that; replace or harden it if you need stricter access rules.

Run::

    uv run python examples/a2a_db_tasks.py
    # or: python -m adcp.examples.a2a_db_tasks
"""

from __future__ import annotations

import contextlib
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from a2a.server.context import ServerCallContext
from a2a.server.tasks.task_store import TaskStore
from a2a.types import Task

from adcp.server import ADCPHandler, serve
from adcp.server.responses import capabilities_response, products_response

_ANONYMOUS_SCOPE = "__anonymous__"
"""Scope value used when a request arrives without an authenticated
principal. Unauthenticated tasks all share this scope — they can't
cross-contaminate with authenticated tasks because the scope column
is part of every WHERE clause."""


# ----------------------------------------------------------------------
# SQLite-backed TaskStore
# ----------------------------------------------------------------------


class SqliteTaskStore(TaskStore):
    """Durable A2A ``TaskStore`` backed by a single SQLite file.

    Tasks are serialised as JSON and scoped by an authenticated
    principal derived from ``ServerCallContext.user.user_name``. Every
    read and delete filters on that scope so a request for a task the
    current principal doesn't own returns ``None`` (not the task).

    SQLite connections are opened per-operation (not pool; not
    long-lived) because sqlite3 connections are not safe to share
    across threads. Fine for this reference impl; swap in an async
    pool (asyncpg, aiomysql) for multi-node production.
    """

    def __init__(self, db_path: str | Path = "a2a_tasks.db") -> None:
        self._db_path = str(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        path = Path(self._db_path)
        first_create = not path.exists()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS a2a_tasks (
                    scope      TEXT NOT NULL,
                    task_id    TEXT NOT NULL,
                    task_json  TEXT NOT NULL,
                    updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
                    PRIMARY KEY (scope, task_id)
                )
                """
            )
        # Only tighten permissions on first creation, so operators who
        # manage permissions via umask / ACLs externally aren't
        # clobbered on every process start.
        if first_create:
            with contextlib.suppress(OSError):
                os.chmod(self._db_path, 0o600)

    def _scope_from_context(self, context: ServerCallContext | None) -> str:
        """Derive the per-principal scope key from the request context.

        Defaults to ``user.user_name`` when an authenticated user is
        present, falling back to ``_ANONYMOUS_SCOPE`` for unauthenticated
        requests. Override for richer identity — e.g. return
        ``f"{tenant_id}:{principal_id}"`` when you carry an explicit
        tenant in ``context.state``. The scope is used as a partition
        key on every read/write; anything you don't include here
        *cannot* be enforced by the store.
        """
        user = getattr(context, "user", None) if context is not None else None
        if user is None:
            return _ANONYMOUS_SCOPE
        user_name = getattr(user, "user_name", None)
        is_authenticated = getattr(user, "is_authenticated", False)
        if is_authenticated and isinstance(user_name, str) and user_name:
            return user_name
        return _ANONYMOUS_SCOPE

    @asynccontextmanager
    async def _conn(self):
        # SQLite connections aren't safe across threads. Open a fresh
        # connection per operation and commit-on-success / rollback-on-error
        # so a port to psycopg / aiomysql doesn't silently leak partial
        # writes — SQLite auto-rolls-back on close, but most other drivers
        # don't.
        conn = sqlite3.connect(self._db_path)
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()
        finally:
            conn.close()

    async def save(self, task: Task, context: ServerCallContext | None = None) -> None:
        scope = self._scope_from_context(context)
        task_json = task.model_dump_json(exclude_none=True)
        async with self._conn() as conn:
            # NOTE: ``INSERT OR REPLACE`` is last-writer-wins. Production
            # stores should guard with a version column or
            # ``WHERE updated_at < ?`` to prevent concurrent updates
            # silently reverting task state (e.g. 'completed' → 'working').
            conn.execute(
                "INSERT OR REPLACE INTO a2a_tasks "
                "(scope, task_id, task_json, updated_at) "
                "VALUES (?, ?, ?, strftime('%s','now'))",
                (scope, task.id, task_json),
            )

    async def get(self, task_id: str, context: ServerCallContext | None = None) -> Task | None:
        scope = self._scope_from_context(context)
        async with self._conn() as conn:
            row = conn.execute(
                "SELECT task_json FROM a2a_tasks WHERE scope = ? AND task_id = ?",
                (scope, task_id),
            ).fetchone()
        if row is None:
            return None
        payload: dict[str, Any] = json.loads(row[0])
        return Task.model_validate(payload)

    async def delete(self, task_id: str, context: ServerCallContext | None = None) -> None:
        scope = self._scope_from_context(context)
        async with self._conn() as conn:
            conn.execute(
                "DELETE FROM a2a_tasks WHERE scope = ? AND task_id = ?",
                (scope, task_id),
            )


# ----------------------------------------------------------------------
# Minimal handler so the example runs end-to-end
# ----------------------------------------------------------------------


class DemoAgent(ADCPHandler):
    async def get_adcp_capabilities(self, params: Any, context: Any = None) -> dict[str, Any]:
        return capabilities_response(["media_buy"])

    async def get_products(self, params: Any, context: Any = None) -> dict[str, Any]:
        return products_response([{"product_id": "demo_display", "name": "Demo display placement"}])


# ----------------------------------------------------------------------
# Wiring — pass the store through ``serve()``.
# ----------------------------------------------------------------------


def main() -> None:
    store = SqliteTaskStore(db_path="a2a_tasks.db")
    serve(
        DemoAgent(),
        name="a2a-db-tasks-demo",
        transport="a2a",
        task_store=store,
    )


if __name__ == "__main__":
    main()
