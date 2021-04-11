#!/usr/bin/env python
"""Tests for envoy_reader.py."""
# -*- coding: utf-8 -*-
import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from envoy_reader.envoy_reader import EnvoyReader


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


def _load_json_fixture(version, name) -> dict:
    with open(_fixtures_dir() / version / name, "r") as read_in:
        return json.load(read_in)


@pytest.mark.asyncio
@respx.mock
async def test_with_4_2_27_firmware():
    """Verify with 4.2.27 firmware."""
    version = "4.2.27"
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production.json").mock(
        return_value=Response(200, json=_load_json_fixture(version, "production.json"))
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )

    reader = EnvoyReader("127.0.0.1", inverters=False)
    await reader.getData()

    assert await reader.consumption() == 5811
    assert await reader.production() == 5891
    assert await reader.daily_consumption() == 0
    assert await reader.daily_production() == 17920
    assert await reader.seven_days_consumption() == 0
    assert await reader.seven_days_production() == 276614
    assert await reader.lifetime_consumption() == 0
    assert await reader.lifetime_production() == 10279087
    assert await reader.inverters_production() is None


@pytest.mark.asyncio
@respx.mock
async def test_with_5_0_49_firmware():
    """Verify with 5.0.49 firmware."""
    version = "5.0.49"

    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production.json").mock(
        return_value=Response(200, json=_load_json_fixture(version, "production.json"))
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    reader = EnvoyReader("127.0.0.1", inverters=True)
    await reader.getData()

    assert (
        await reader.consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.production() == 4859
    assert (
        await reader.daily_consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.daily_production() == 5046
    assert (
        await reader.seven_days_consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.seven_days_production() == 445686
    assert (
        await reader.lifetime_consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.lifetime_production() == 88742152
    assert isinstance(await reader.inverters_production(), dict)


@pytest.mark.asyncio
@respx.mock
async def test_with_3_9_36_firmware():
    """Verify with 3.9.36 firmware."""
    version = "3.9.36"

    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production.json").mock(return_value=Response(404))
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    reader = EnvoyReader("127.0.0.1", inverters=True)
    await reader.getData()

    assert (
        await reader.consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.production() == 1271
    assert (
        await reader.daily_consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.daily_production() == 1460
    assert (
        await reader.seven_days_consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.seven_days_production() == 130349
    assert (
        await reader.lifetime_consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.lifetime_production() == 6012540
    assert isinstance(await reader.inverters_production(), dict)


@pytest.mark.asyncio
@respx.mock
async def test_with_3_17_3_firmware():
    """Verify with 3.17.3 firmware."""
    version = "3.17.3"

    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production.json").mock(return_value=Response(404))
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200, json=_load_json_fixture(version, "api_v1_production_inverters")
        )
    )
    reader = EnvoyReader("127.0.0.1", inverters=True)
    await reader.getData()

    assert (
        await reader.consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.production() == 5463
    assert (
        await reader.daily_consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.daily_production() == 5481
    assert (
        await reader.seven_days_consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.seven_days_production() == 389581
    assert (
        await reader.lifetime_consumption()
        == "Consumption data not available for your Envoy device."
    )
    assert await reader.lifetime_production() == 93706280
    assert isinstance(await reader.inverters_production(), dict)
