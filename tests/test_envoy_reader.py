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


def _load_json_fixture(version_and_featureSet, name) -> dict:
    with open(_fixtures_dir() / version_and_featureSet / name, "r") as read_in:
        return json.load(read_in)


@pytest.mark.asyncio
@respx.mock
async def test_with_4_2_27_firmware_with_ProdEIMDisabled_ConsEIMDisabled():
    """Verify with 4.2.27 firmware with Production and Consumption Metering disabled."""
    version = "4.2.27"
    featureSet = ["ProdEIM_Disabled", "ConsEIM_Disabled"]
    version_and_featureSet = version + "_" + featureSet[0] + "_" + featureSet[1]
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production.json").mock(
        return_value=Response(
            200, json=_load_json_fixture(version_and_featureSet, "production.json")
        )
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version_and_featureSet, "api_v1_production")
        )
    )

    reader = EnvoyReader("127.0.0.1", inverters=False)
    await reader.getData()

    assert await reader.consumption() == 5811.099
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
async def test_with_4_2_33_firmware_with_ProdEIMDisabled_ConsEIMDisabled():
    """Verify with 4.2.33 firmware with Production Metering Enabled and Consumption Metering disabled."""
    version = "4.2.33"
    featureSet = ["ProdEIM_Enabled", "ConsEIM_Disabled"]
    version_and_featureSet = version + "_" + featureSet[0] + "_" + featureSet[1]
    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production.json").mock(
        return_value=Response(
            200, json=_load_json_fixture(version_and_featureSet, "production.json")
        )
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version_and_featureSet, "api_v1_production")
        )
    )

    reader = EnvoyReader("127.0.0.1", inverters=False)
    await reader.getData()

    assert await reader.consumption() == 0
    assert await reader.production() == -1.123
    assert await reader.daily_consumption() == 0
    assert await reader.daily_production() == 39.573
    assert await reader.seven_days_consumption() == 0
    assert await reader.seven_days_production() == 350.573
    assert await reader.lifetime_consumption() == 0
    assert await reader.lifetime_production() == 53494.573
    assert await reader.inverters_production() is None


@pytest.mark.asyncio
@respx.mock
async def test_with_5_0_49_firmware_with_no_metering_data():
    """Verify with 5.0.49 firmware with no Metering Data."""
    version = "5.0.49"
    featureSet = ["ProdEIM_NA", "ConsEIM_NA"]
    version_and_featureSet = version + "_" + featureSet[0] + "_" + featureSet[1]

    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production.json").mock(
        return_value=Response(
            200, json=_load_json_fixture(version_and_featureSet, "production.json")
        )
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version_and_featureSet, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200,
            json=_load_json_fixture(
                version_and_featureSet, "api_v1_production_inverters"
            ),
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
async def test_with_5_0_55_firmware_with_ProdEIMEnabled_ConsEIMDisabled():
    """Verify with 5.0.55 firmware with Production and Consumption Enabled."""
    version = "5.0.55"
    featureSet = ["ProdEIM_Enabled", "ConsEIM_Enabled"]
    version_and_featureSet = version + "_" + featureSet[0] + "_" + featureSet[1]

    respx.get("/info.xml").mock(return_value=Response(200, text=""))
    respx.get("/production.json").mock(
        return_value=Response(
            200, json=_load_json_fixture(version_and_featureSet, "production.json")
        )
    )
    respx.get("/api/v1/production").mock(
        return_value=Response(
            200, json=_load_json_fixture(version_and_featureSet, "api_v1_production")
        )
    )
    respx.get("/api/v1/production/inverters").mock(
        return_value=Response(
            200,
            json=_load_json_fixture(
                version_and_featureSet, "api_v1_production_inverters"
            ),
        )
    )
    reader = EnvoyReader("127.0.0.1", inverters=True)
    await reader.getData()

    assert await reader.consumption() == 1154.178
    assert await reader.production() == 4151.795
    assert await reader.daily_consumption() == 21717.074
    assert await reader.daily_production() == 41401.742
    assert await reader.seven_days_consumption() == 426886.074
    assert await reader.seven_days_production() == 278982.742
    assert await reader.lifetime_consumption() == 13960032.074
    assert await reader.lifetime_production() == 4079704.742
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
