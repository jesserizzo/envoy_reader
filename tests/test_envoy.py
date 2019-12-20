from envoy_reader.envoy_reader import EnvoyReader
import consts

import requests
import pytest
import asyncio
import json
from pytest_httpserver import HTTPServer

HOST = "localhost"

@pytest.mark.asyncio
@pytest.mark.parametrize("test_input_url, test_input_page, expected", [("/api/v1/production", consts.PRODUCTION_OUTPUT_P, "P"),
                                                                       ("/production.json", consts.PRODUCTION_OUTPUT_PC, "PC"),
                                                                       ("/production", consts.PRODUCTION_OUTPUT_1_P0, "P0")])
async def test_detect_model(test_input_url, test_input_page, expected):
    wp = open(test_input_page, "r").read()
    with HTTPServer(port=80) as httpserver:
        if expected != "P0":
            httpserver.expect_request(test_input_url).respond_with_json(wp)
        else:
            httpserver.expect_request(test_input_url).respond_with_data(wp)
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        await e.detect_model()
        assert e.endpoint_type == expected

@pytest.mark.asyncio
async def test_detect_model_exception():
    with HTTPServer(port=80) as httpserver:
        httpserver.expect_request("/foo").respond_with_json({"foo": "bar"})
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        with pytest.raises(RuntimeError):
            assert await e.detect_model()

@pytest.mark.asyncio
@pytest.mark.parametrize("test_input_url, test_input_page, expected", [("/info.xml", consts.INFO_OUTPUT_PC, "043616"),
                                                                       ("/info.xml", consts.INFO_OUTPUT_P, "error"),
                                                                       ("/info.xml", consts.INFO_OUTPUT_P0, "error")])
async def test_get_serial_number(test_input_url, test_input_page, expected):
    wp = open(test_input_page, "r").read()
    with HTTPServer(port=80) as httpserver:
        httpserver.expect_request(test_input_url).respond_with_data(wp)
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        if expected != "error":
            await e.get_serial_number()
            assert e.serial_number_last_six == expected
        else:
            with pytest.raises(IndexError):
                assert await e.get_serial_number()

@pytest.mark.asyncio
async def test_get_serial_number_exception_no_response():
    e = EnvoyReader(HOST)
    a = await e.get_serial_number()
    assert a == f"Unable to connect to Envoy. Check that the device is up at 'http://{HOST}'."

@pytest.mark.asyncio
@pytest.mark.parametrize("test_input_url, test_input_page, device_type", [("/api/v1/production", consts.PRODUCTION_OUTPUT_P, "P"),
                                                                          ("/production.json", consts.PRODUCTION_OUTPUT_PC, "PC"),
                                                                          ("/production", consts.PRODUCTION_OUTPUT_1_P0, "P0")])
async def test_call_api(test_input_url, test_input_page, device_type):
    wp = open(test_input_page, "r").read()
    with HTTPServer(port=80) as httpserver:
        if device_type != "P0":
            httpserver.expect_request(test_input_url).respond_with_json(wp)
        else:
            httpserver.expect_request(test_input_url).respond_with_data(wp)
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        r = await e.call_api()
        assert r == wp

def test_create_connect_errormessage():
    e = EnvoyReader(HOST)
    assert e.create_connect_errormessage() == f"Unable to connect to Envoy. Check that the device is up at 'http://{HOST}'."

@pytest.mark.parametrize("url", [("/api/v1/production"),
                                 ("/production.json"),
                                 ("/production")])
def test_create_json_errormessage(url):
    e = EnvoyReader(HOST)
    e.endpoint_url = f"http://{HOST}{url}"
    assert e.create_json_errormessage() == f"Got a response from 'http://{HOST}{url}', but metric could not be found. Maybe your model of Envoy doesn't support the requested metric."

@pytest.mark.asyncio
@pytest.mark.parametrize("test_input_url, test_input_page, device_type, expected_power", [("/api/v1/production", consts.PRODUCTION_OUTPUT_P, "P", 141),
                                                                                          ("/production.json", consts.PRODUCTION_OUTPUT_PC, "PC", 478.707),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_1_P0, "P0", 318),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_2_P0, "P0", 1390)])
async def test_production(test_input_url, test_input_page, device_type, expected_power):
    with HTTPServer(port=80) as httpserver:
        if device_type != "P0":
            wp = open(test_input_page, "r").read()
            wp = json.loads(wp)
            httpserver.expect_request(test_input_url).respond_with_json(wp)
        else:
            wp = open(test_input_page, "r").read()
            httpserver.expect_request(test_input_url).respond_with_data(wp)
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        a = await e.production()
        assert a == int(expected_power)
        assert e.endpoint_type == device_type

@pytest.mark.asyncio
@pytest.mark.parametrize("test_input_url, test_input_page, device_type, expected_power", [("/api/v1/production", consts.PRODUCTION_OUTPUT_P, "P", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE),
                                                                                          ("/production.json", consts.PRODUCTION_OUTPUT_PC, "PC", 478.707),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_1_P0, "P0", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_2_P0, "P0", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE)])
async def test_consumption(test_input_url, test_input_page, device_type, expected_power):
    with HTTPServer(port=80) as httpserver:
        if device_type != "P0":
            wp = open(test_input_page, "r").read()
            wp = json.loads(wp)
            httpserver.expect_request(test_input_url).respond_with_json(wp)
        else:
            wp = open(test_input_page, "r").read()
            httpserver.expect_request(test_input_url).respond_with_data(wp)
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        a = await e.consumption()
        if device_type == "PC":
            assert a == int(expected_power)
        else:
            assert a == expected_power
        assert e.endpoint_type == device_type

@pytest.mark.asyncio
@pytest.mark.parametrize("test_input_url, test_input_page, device_type, expected_power", [("/api/v1/production", consts.PRODUCTION_OUTPUT_P, "P", 9803),
                                                                                          ("/production.json", consts.PRODUCTION_OUTPUT_PC, "PC", 4429.459),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_1_P0, "P0", 6740),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_2_P0, "P0", 8790)])
async def test_daily_production(test_input_url, test_input_page, device_type, expected_power):
    with HTTPServer(port=80) as httpserver:
        if device_type != "P0":
            wp = open(test_input_page, "r").read()
            wp = json.loads(wp)
            httpserver.expect_request(test_input_url).respond_with_json(wp)
        else:
            wp = open(test_input_page, "r").read()
            httpserver.expect_request(test_input_url).respond_with_data(wp)
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        a = await e.daily_production()
        assert a == int(expected_power)
        assert e.endpoint_type == device_type

@pytest.mark.asyncio
@pytest.mark.parametrize("test_input_url, test_input_page, device_type, expected_power", [("/api/v1/production", consts.PRODUCTION_OUTPUT_P, "P", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE),
                                                                                          ("/production.json", consts.PRODUCTION_OUTPUT_PC, "PC", 4598.459),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_1_P0, "P0", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_2_P0, "P0", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE)])
async def test_daily_consumption(test_input_url, test_input_page, device_type, expected_power):
    with HTTPServer(port=80) as httpserver:
        if device_type != "P0":
            wp = open(test_input_page, "r").read()
            wp = json.loads(wp)
            httpserver.expect_request(test_input_url).respond_with_json(wp)
        else:
            wp = open(test_input_page, "r").read()
            httpserver.expect_request(test_input_url).respond_with_data(wp)
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        a = await e.daily_consumption()
        if device_type == "PC":
            assert a == int(expected_power)
        else:
            assert a == expected_power
        assert e.endpoint_type == device_type

@pytest.mark.asyncio
@pytest.mark.parametrize("test_input_url, test_input_page, device_type, expected_power", [("/api/v1/production", consts.PRODUCTION_OUTPUT_P, "P", 58017),
                                                                                          ("/production.json", consts.PRODUCTION_OUTPUT_PC, "PC", 4429.459),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_1_P0, "P0", 45800),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_2_P0, "P0", 87700)])
async def test_seven_days_production(test_input_url, test_input_page, device_type, expected_power):
    with HTTPServer(port=80) as httpserver:
        if device_type != "P0":
            wp = open(test_input_page, "r").read()
            wp = json.loads(wp)
            httpserver.expect_request(test_input_url).respond_with_json(wp)
        else:
            wp = open(test_input_page, "r").read()
            httpserver.expect_request(test_input_url).respond_with_data(wp)
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        a = await e.seven_days_production()
        assert a == int(expected_power)
        assert e.endpoint_type == device_type

@pytest.mark.asyncio
@pytest.mark.parametrize("test_input_url, test_input_page, device_type, expected_power", [("/api/v1/production", consts.PRODUCTION_OUTPUT_P, "P", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE),
                                                                                          ("/production.json", consts.PRODUCTION_OUTPUT_PC, "PC", 4598.459),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_1_P0, "P0", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_2_P0, "P0", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE)])
async def test_seven_days_consumption(test_input_url, test_input_page, device_type, expected_power):
    with HTTPServer(port=80) as httpserver:
        if device_type != "P0":
            wp = open(test_input_page, "r").read()
            wp = json.loads(wp)
            httpserver.expect_request(test_input_url).respond_with_json(wp)
        else:
            wp = open(test_input_page, "r").read()
            httpserver.expect_request(test_input_url).respond_with_data(wp)
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        a = await e.seven_days_consumption()
        if device_type == "PC":
            assert a == int(expected_power)
        else:
            assert a == expected_power
        assert e.endpoint_type == device_type

@pytest.mark.asyncio
@pytest.mark.parametrize("test_input_url, test_input_page, device_type, expected_power", [("/api/v1/production", consts.PRODUCTION_OUTPUT_P, "P", 13131422),
                                                                                          ("/production.json", consts.PRODUCTION_OUTPUT_PC, "PC", 4598.459),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_1_P0, "P0", 46800000),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_2_P0, "P0", 23400000)])
async def test_lifetime_production(test_input_url, test_input_page, device_type, expected_power):
    with HTTPServer(port=80) as httpserver:
        if device_type != "P0":
            wp = open(test_input_page, "r").read()
            wp = json.loads(wp)
            httpserver.expect_request(test_input_url).respond_with_json(wp)
        else:
            wp = open(test_input_page, "r").read()
            httpserver.expect_request(test_input_url).respond_with_data(wp)
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        a = await e.lifetime_production()
        assert a == int(expected_power)
        assert e.endpoint_type == device_type

@pytest.mark.asyncio
@pytest.mark.parametrize("test_input_url, test_input_page, device_type, expected_power", [("/api/v1/production", consts.PRODUCTION_OUTPUT_P, "P", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE),
                                                                                          ("/production.json", consts.PRODUCTION_OUTPUT_PC, "PC", 4598.459),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_1_P0, "P0", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE),
                                                                                          ("/production", consts.PRODUCTION_OUTPUT_2_P0, "P0", consts.MESSAGE_CONSUMPTION_NOT_AVAILABLE)])
async def test_lifetime_consumption(test_input_url, test_input_page, device_type, expected_power):
    with HTTPServer(port=80) as httpserver:
        if device_type != "P0":
            wp = open(test_input_page, "r").read()
            wp = json.loads(wp)
            httpserver.expect_request(test_input_url).respond_with_json(wp)
        else:
            wp = open(test_input_page, "r").read()
            httpserver.expect_request(test_input_url).respond_with_data(wp)
        assert httpserver.is_running()
        e = EnvoyReader(HOST)
        a = await e.lifetime_consumption()
        if device_type == "PC":
            assert a == int(expected_power)
        else:
            assert a == expected_power
        assert e.endpoint_type == device_type