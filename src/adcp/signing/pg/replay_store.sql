-- AdCP RFC 9421 replay-dedup store.
--
-- Run this once per deployment. Tracked by the adcp-client-python
-- PgReplayStore; see src/adcp/signing/pg/replay_store.py for the
-- query shapes the Python code executes.
--
-- COLLATE "C" on the identifier columns avoids locale-dependent case
-- folding — on some locales "Key-A" and "key-a" compare equal, which
-- would let an attacker collapse distinct kids / nonces into the same
-- slot. "C" is the byte-for-byte comparison we actually want.
--
-- Run a periodic sweep (cron, every minute or so):
--     DELETE FROM adcp_replay WHERE expires_at <= now();
-- The PgReplayStore.sweep_expired() method does exactly this and can
-- be called from an admin endpoint if you prefer an in-process sweep.

CREATE TABLE IF NOT EXISTS adcp_replay (
    keyid      TEXT        COLLATE "C" NOT NULL,
    nonce      TEXT        COLLATE "C" NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (keyid, nonce)
);

-- Supports the sweep query and the at_capacity COUNT. Postgres will
-- use this for range predicates like ``expires_at > now()``, so
-- ``at_capacity`` for a busy keyid is an index-assisted scan rather
-- than a full table scan.
CREATE INDEX IF NOT EXISTS adcp_replay_expires_idx
    ON adcp_replay (expires_at);

-- A partial index on (keyid) WHERE expires_at > now() is NOT usable —
-- ``now()`` is STABLE, not IMMUTABLE, which Postgres forbids in index
-- predicates. If ``at_capacity`` for a specific keyid becomes hot in
-- profiling, the workable alternative is a composite
-- ``(keyid, expires_at)`` index; the existing PK + single-column
-- expires index already covers most patterns.
