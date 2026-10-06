"""Stored account-context failures remain local to their configuration."""

from __future__ import annotations

import asyncio
import operator
from dataclasses import replace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from adcp.reporting.fixtures import redacted_capabilities
from adcp.reporting.service import (
    ReliableReportingConfigurationError,
    ReliableReportingService,
    ReliableReportingServiceError,
)
from adcp.reporting.testing import ScriptedReportingAdapter
from tests.test_reliable_reporting_service import NOW, _account_context, _configuration


def _service(resolver: Any) -> ReliableReportingService:
    service = ReliableReportingService.memory(account_context=resolver, clock=lambda: NOW)
    service.sources.register("gam", ScriptedReportingAdapter(redacted_capabilities(), []))
    return service


@pytest.mark.parametrize("async_resolver", [False, True])
async def test_restart_binds_healthy_accounts_and_retries_a_failed_resolver(
    async_resolver: bool, caplog: Any
) -> None:
    configs = tuple(_configuration(account_id=account) for account in ("a", "b", "c"))
    failure = RuntimeError("account credentials: private-test-token")
    unavailable = True
    attempts: list[str] = []

    def resolve(configuration: Any) -> Any:
        attempts.append(configuration.account_id)
        if configuration.account_id == "b" and unavailable:
            raise failure
        return _account_context(configuration)

    async def resolve_async(configuration: Any) -> Any:
        await asyncio.sleep(0)
        return resolve(configuration)

    service = _service(resolve_async if async_resolver else resolve)
    for configuration in configs:
        await service.store.put_configuration(configuration)
    try:
        await service.start()
        assert attempts == ["a", "b", "c"]
        assert "private-test-token" not in caplog.text
        assert service.initialization_errors == {configs[1].generation_key: failure}
        with pytest.raises(TypeError):
            operator.setitem(service.initialization_errors, configs[0].generation_key, failure)

        first = await service.run_worker(now=NOW)
        assert set(first.configurations) == {configs[0].generation_key, configs[2].generation_key}
        assert first.configuration_errors == {configs[1].generation_key: failure}

        unavailable = False
        recovered = await service.run_worker(now=NOW)
        assert set(recovered.configurations) == {
            configuration.generation_key for configuration in configs
        }
        assert not recovered.configuration_errors
        assert not service.initialization_errors
        assert attempts == ["a", "b", "c", "b", "b"]
        assert await service.store.list_all_configurations() == configs
    finally:
        await service.close()


async def test_permanent_resolver_error_is_observable_without_retry_and_can_be_reconfigured() -> (
    None
):
    configuration = _configuration()
    failure = ReliableReportingConfigurationError("account has no execution currency")
    unavailable = True
    attempts = 0

    def resolve(config: Any) -> Any:
        nonlocal attempts
        attempts += 1
        if unavailable:
            raise failure
        return _account_context(config)

    service = _service(resolve)
    await service.store.put_configuration(configuration)
    try:
        await service.start()
        for _ in range(2):
            turn = await service.run_worker(now=NOW)
            assert turn.configuration_errors == {configuration.generation_key: failure}
        assert attempts == 1

        unavailable = False
        await service.configure(configuration)
        assert not service.initialization_errors
        assert not (await service.run_worker(now=NOW)).configuration_errors
        assert attempts == 2
    finally:
        await service.close()


async def test_retry_that_becomes_permanent_stops_retrying() -> None:
    configuration = _configuration()
    permanent = ReliableReportingConfigurationError("account was removed")
    attempts = 0

    def resolve(config: Any) -> Any:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary lookup failure")
        raise permanent

    service = _service(resolve)
    await service.store.put_configuration(configuration)
    try:
        await service.start()
        for _ in range(2):
            turn = await service.run_worker(now=NOW)
            assert turn.configuration_errors == {configuration.generation_key: permanent}
        assert attempts == 2
    finally:
        await service.close()


async def test_schema_failure_still_prevents_startup(monkeypatch: Any) -> None:
    service = _service(_account_context)
    failure = RuntimeError("schema unavailable")
    monkeypatch.setattr(service.store, "create_schema", AsyncMock(side_effect=failure))
    try:
        with pytest.raises(ReliableReportingServiceError, match="startup"):
            await service.start()
    finally:
        await service.close()


async def test_static_adapter_error_still_prevents_startup() -> None:
    service = _service(lambda config: replace(_account_context(config), adapter="unknown"))
    await service.store.put_configuration(_configuration())
    try:
        with pytest.raises(ReliableReportingConfigurationError, match="unregistered"):
            await service.start()
    finally:
        await service.close()


async def test_resolver_cancellation_still_fails_startup() -> None:
    async def resolve(configuration: Any) -> Any:
        raise asyncio.CancelledError()

    service = _service(resolve)
    await service.store.put_configuration(_configuration())
    try:
        with pytest.raises(ReliableReportingServiceError, match="startup"):
            await service.start()
    finally:
        await service.close()


async def test_new_configuration_admission_still_raises_resolver_failures() -> None:
    failure = RuntimeError("account lookup unavailable")

    def resolve(configuration: Any) -> Any:
        raise failure

    service = _service(resolve)
    try:
        with pytest.raises(RuntimeError, match="account lookup unavailable"):
            await service.configure(_configuration())
    finally:
        await service.close()
