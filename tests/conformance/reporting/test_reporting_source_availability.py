"""Declared source readiness through the actual production progress stores."""

from datetime import timedelta
from functools import partial

import pytest

from ._production_support import Source, production_harness
from .test_reporting_production_lock_order import source_turn


@pytest.mark.parametrize("backend", ["memory", "postgres"])
async def test_scheduled_source_wait_preserves_pending_production_work(backend, tmp_path):
    async with production_harness(
        backend,
        tmp_path / "destination.sqlite",
        count=1,
        periods=1,
        source_publication=True,
        source_factory=partial(Source, expected_availability_lag="PT30M"),
    ) as h:
        source = h.production.offerings[0].producer._source
        await h.production.activate(account_id=h.item.config.account_id)
        h.source_clock.advance(timedelta(seconds=30))
        first = await source_turn(h.production)
        assert not source.requests
        assert not first.revisions_committed
        assert not first.slices_failed

        h.source_clock.advance(timedelta(minutes=29, seconds=29))
        waiting = await source_turn(h.production)
        assert not source.requests
        assert not waiting.revisions_committed
        assert not waiting.slices_failed

        h.source_clock.advance(timedelta(seconds=1))
        ready = await source_turn(h.production)
        assert len(source.requests) == 1
        assert len(ready.revisions_committed) == 1
        assert not ready.slices_failed
        assert source.requests[0].period.end == h.item.obligation.period.end
        stored = await h.store.get_obligation(
            account_id=h.item.config.account_id,
            reporting_obligation_id=h.item.obligation.reporting_obligation_id,
        )
        assert stored.period.expected_at == h.item.obligation.period.expected_at
