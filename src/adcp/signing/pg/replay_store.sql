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

-- Supports the sweep query and the at_capacity COUNT.
CREATE INDEX IF NOT EXISTS adcp_replay_expires_idx
    ON adcp_replay (expires_at);

-- Partial index for the hot per-keyid live-count query. Postgres can
-- scan just this smaller index for at_capacity() instead of the full
-- table. The WHERE clause is immutable (references now()) so the
-- index must be created with a recent-enough Postgres (12+) and the
-- query must use a matching predicate structure. Most deployments can
-- safely rely on the primary index above; enable this one if profiling
-- shows at_capacity hot on a specific keyid.
--
-- CREATE INDEX adcp_replay_keyid_live_idx
--     ON adcp_replay (keyid)
--     WHERE expires_at > now();
