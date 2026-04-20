"""Example: A2A agent with a durable, SQLite-backed ``TaskStore``.

A2A's default ``InMemoryTaskStore`` is single-process and non-durable —
fine for demos but tasks vanish on restart. Production agents need a
durable store so long-running operations survive process restarts and
can be resumed by whichever worker picks up the request.

This example wires up a minimal SQLite-backed store that implements
``a2a.server.tasks.task_store.TaskStore``. SQLite is the right reference
target: it's in the stdlib, needs no infrastructure, and the SQL
pattern translates directly to Postgres / MySQL / etc. for production.

**Not production-ready.** For real use you want:

- Postgres/MySQL + async driver (asyncpg / aiomysql).
- The idempotency transaction pattern: `put(task)` in the same
  transaction as the handler's business writes, so a crash between
  "handler success" and "cache commit" doesn't duplicate side effects.
- Connection pooling.
- Row-level TTL / garbage collection for completed tasks.

Run::

    uv run python examples/a2a_db_tasks.py
    # or: python -m adcp.examples.a2a_db_tasks
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from a2a.server.context import ServerCallContext
from a2a.server.tasks.task_store import TaskStore
from a2a.types import Task

from adcp.server import ADCPHandler, serve
from adcp.server.responses import capabilities_response, products_response

# ----------------------------------------------------------------------
# SQLite-backed TaskStore
# ----------------------------------------------------------------------


class SqliteTaskStore(TaskStore):
    """Durable A2A ``TaskStore`` backed by a single SQLite file.

    Tasks are serialised as JSON. Reads and writes go through sqlite3
    directly (synchronous under the hood, wrapped in ``async def`` to
    match the ``TaskStore`` ABC) — single-file SQLite is fast enough
    for demo/single-node workloads and avoids an async driver
    dependency. Swap for asyncpg / aiomysql for multi-node production.
    """

    def __init__(self, db_path: str | Path = "a2a_tasks.db") -> None:
        self._db_path = str(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS a2a_tasks (
                    task_id TEXT PRIMARY KEY,
                    task_json TEXT NOT NULL,
                    updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
                )
                """
            )

    @asynccontextmanager
    async def _conn(self):
        # SQLite connections are not safe to share across threads; open
        # a fresh one per operation. Fine for this reference impl.
        conn = sqlite3.connect(self._db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    async def save(self, task: Task, context: ServerCallContext | None = None) -> None:
        task_json = task.model_dump_json(exclude_none=True)
        async with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO a2a_tasks (task_id, task_json, updated_at) "
                "VALUES (?, ?, strftime('%s','now'))",
                (task.id, task_json),
            )

    async def get(self, task_id: str, context: ServerCallContext | None = None) -> Task | None:
        async with self._conn() as conn:
            row = conn.execute(
                "SELECT task_json FROM a2a_tasks WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        if row is None:
            return None
        payload: dict[str, Any] = json.loads(row[0])
        return Task.model_validate(payload)

    async def delete(self, task_id: str, context: ServerCallContext | None = None) -> None:
        async with self._conn() as conn:
            conn.execute("DELETE FROM a2a_tasks WHERE task_id = ?", (task_id,))


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
