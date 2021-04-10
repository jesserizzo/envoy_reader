"""Module to read production and consumption values from an Enphase Envoy on the local network."""
import asyncio
import logging
import re
import time
from json.decoder import JSONDecodeError

import httpx

#
# Legacy parser is only used on ancient firmwares
#
PRODUCTION_REGEX = r"<td>Currentl.*</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(W|kW|MW)</td>"
DAY_PRODUCTION_REGEX = r"<td>Today</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>"
WEEK_PRODUCTION_REGEX = (
    r"<td>Past Week</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>"
)
LIFE_PRODUCTION_REGEX = (
    r"<td>Since Installation</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>"
)
SERIAL_REGEX = re.compile(r"Envoy\s*Serial\s*Number:\s*([0-9]+)")

ENDPOINT_URL_PRODUCTION_JSON = "http://{}/production.json"
ENDPOINT_URL_PRODUCTION_V1 = "http://{}/api/v1/production"
ENDPOINT_URL_PRODUCTION_INVERTERS = "http://{}/api/v1/production/inverters"
ENDPOINT_URL_PRODUCTION = "http://{}/production"

# pylint: disable=pointless-string-statement

ENVOY_MODEL_S = "PC"
ENVOY_MODEL_C = "P"
ENVOY_MODEL_LEGACY = "P0"

_LOGGER = logging.getLogger(__name__)


def has_production_and_consumption(json):
    """Check if json has keys for both production and consumption."""
    return "production" in json and "consumption" in json


def has_metering_setup(json):
    """Check if Active Count of Production CTs (eim) installed is greater than one."""
    return json["production"][1]["activeCount"] > 0


class EnvoyReader:  # pylint: disable=too-many-instance-attributes
    """Instance of EnvoyReader"""

    # P0 for older Envoy model C, s/w < R3.9 no json pages
    # P for production data only (ie. Envoy model C, s/w >= R3.9)
    # PC for production and consumption data (ie. Envoy model S)

    message_consumption_not_available = (
        "Consumption data not available for your Envoy device."
    )

    def __init__(  # pylint: disable=too-many-arguments
        self, host, username="envoy", password="", inverters=False, async_client=None
    ):
        """Init the EnvoyReader."""
        self.host = host.lower()
        self.username = username
        self.password = password
        self.get_inverters = inverters
        self.endpoint_type = None
        self.serial_number_last_six = None
        self.endpoint_production_json_results = None
        self.endpoint_production_v1_results = None
        self.endpoint_production_inverters = None
        self.endpoint_production_results = None
        self.isMeteringEnabled = False  # pylint: disable=invalid-name
        self._async_client = async_client

    @property
    def async_client(self):
        """Return the httpx client."""
        return self._async_client or httpx.AsyncClient()

    async def _update(self):
        """Update the data."""
        if self.endpoint_type == ENVOY_MODEL_S:
            await self._update_from_pc_endpoint()
        if self.endpoint_type == ENVOY_MODEL_C or (
            self.endpoint_type == ENVOY_MODEL_S and not self.isMeteringEnabled
        ):
            await self._update_from_p_endpoint()
        if self.endpoint_type == ENVOY_MODEL_LEGACY:
            await self._update_from_p0_endpoint()

    async def _update_from_pc_endpoint(self):
        """Update from PC endpoint."""
        await self._update_endpoint(
            "endpoint_production_json_results", ENDPOINT_URL_PRODUCTION_JSON
        )

    async def _update_from_p_endpoint(self):
        """Update from P endpoint."""
        await self._update_endpoint(
            "endpoint_production_v1_results", ENDPOINT_URL_PRODUCTION_V1
        )

    async def _update_from_p0_endpoint(self):
        """Update from P0 endpoint."""
        await self._update_endpoint(
            "endpoint_production_results", ENDPOINT_URL_PRODUCTION
        )

    async def _update_endpoint(self, attr, url):
        """Update a property from an endpoint."""
        formatted_url = url.format(self.host)
        response = await self._async_fetch_with_retry(
            formatted_url, allow_redirects=False
        )
        setattr(self, attr, response)
        _LOGGER.debug("Fetched from %s: %s: %s", formatted_url, response, response.text)

    async def _async_fetch_with_retry(self, url, **kwargs):
        """Retry 3 times to fetch the url if there is a transport error."""
        for attempt in range(3):
            try:
                async with self.async_client as client:
                    return await client.get(url, timeout=30, **kwargs)
            except httpx.TransportError:
                if attempt == 2:
                    raise

    async def getData(self):  # pylint: disable=invalid-name
        """Fetch data from the endpoint."""
        if not self.endpoint_type:
            await self.detect_model()
        else:
            await self._update()

        if not self.get_inverters:
            return

        inverters_url = ENDPOINT_URL_PRODUCTION_INVERTERS.format(self.host)
        inverters_auth = httpx.DigestAuth(self.username, self.password)

        response = await self._async_fetch_with_retry(
            inverters_url, auth=inverters_auth
        )
        _LOGGER.debug(
            "Fetched from %s: %s: %s",
            inverters_url,
            response,
            response.text,
        )
        if response.status_code == 401:
            response.raise_for_status()
        self.endpoint_production_inverters = response
        return

    async def detect_model(self):
        """Method to determine if the Envoy supports consumption values or only production."""
        # If a password was not given as an argument when instantiating
        # the EnvoyReader object than use the last six numbers of the serial
        # number as the password.  Otherwise use the password argument value.
        if self.password == "" and not self.serial_number_last_six:
            await self.get_serial_number()
            self.password = self.serial_number_last_six

        try:
            await self._update_from_pc_endpoint()
        except httpx.HTTPError:
            pass
        if (
            self.endpoint_production_json_results
            and self.endpoint_production_json_results.status_code == 200
            and has_production_and_consumption(
                self.endpoint_production_json_results.json()
            )
        ):
            self.isMeteringEnabled = has_metering_setup(
                self.endpoint_production_json_results.json()
            )
            if not self.isMeteringEnabled:
                await self._update_from_p_endpoint()
            self.endpoint_type = ENVOY_MODEL_S
            return

        try:
            await self._update_from_p_endpoint()
        except httpx.HTTPError:
            pass
        if (
            self.endpoint_production_v1_results
            and self.endpoint_production_v1_results.status_code == 200
        ):
            self.endpoint_type = ENVOY_MODEL_C  # Envoy-C, production only
            return

        try:
            await self._update_from_p0_endpoint()
        except httpx.HTTPError:
            pass
        if (
            self.endpoint_production_results
            and self.endpoint_production_results.status_code == 200
        ):
            self.endpoint_type = ENVOY_MODEL_LEGACY  # older Envoy-C
            return

        raise RuntimeError(
            "Could not connect or determine Envoy model. "
            + "Check that the device is up at 'http://"
            + self.host
            + "'."
        )

    async def get_serial_number(self):
        """Method to get last six digits of Envoy serial number for auth"""
        full_serial = await self.get_full_serial_number()
        if full_serial:
            self.serial_number_last_six = full_serial[-6:]

    async def get_full_serial_number(self):
        """Method to get the  Envoy serial number."""
        response = await self._async_fetch_with_retry(
            "http://{}/info.xml".format(self.host),
            allow_redirects=True,
        )
        if not response.text:
            return None
        if "<sn>" in response.text:
            return response.text.split("<sn>")[1].split("</sn>")[0]
        match = SERIAL_REGEX.search(response.text)
        if match:
            return match.group(1)

    def create_connect_errormessage(self):
        """Create error message if unable to connect to Envoy"""
        return (
            "Unable to connect to Envoy. "
            + "Check that the device is up at 'http://"
            + self.host
            + "'."
        )

    def create_json_errormessage(self):
        """Create error message if unable to parse JSON response"""
        return (
            "Got a response from '"
            + self.host
            + "', but metric could not be found. "
            + "Maybe your model of Envoy doesn't "
            + "support the requested metric."
        )

    async def production(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        if self.endpoint_type == ENVOY_MODEL_S:
            raw_json = self.endpoint_production_json_results.json()
            idx = 1 if self.isMeteringEnabled else 0
            production = raw_json["production"][idx]["wNow"]
        elif self.endpoint_type == ENVOY_MODEL_C:
            raw_json = self.endpoint_production_v1_results.json()
            production = raw_json["wattsNow"]
        elif self.endpoint_type == ENVOY_MODEL_LEGACY:
            text = self.endpoint_production_results.text
            match = re.search(PRODUCTION_REGEX, text, re.MULTILINE)
            if match:
                if match.group(2) == "kW":
                    production = float(match.group(1)) * 1000
                else:
                    if match.group(2) == "mW":
                        production = float(match.group(1)) * 1000000
                    else:
                        production = float(match.group(1))
            else:
                raise RuntimeError("No match for production, check REGEX  " + text)
        return int(production)

    async def consumption(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        """Only return data if Envoy supports Consumption"""
        if (
            self.endpoint_type == ENVOY_MODEL_C
            or self.endpoint_type == ENVOY_MODEL_LEGACY
        ):
            return self.message_consumption_not_available

        raw_json = self.endpoint_production_json_results.json()
        consumption = raw_json["consumption"][0]["wNow"]
        return int(consumption)

    async def daily_production(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        if self.endpoint_type == ENVOY_MODEL_S and self.isMeteringEnabled:
            raw_json = self.endpoint_production_json_results.json()
            daily_production = raw_json["production"][1]["whToday"]
        elif self.endpoint_type == ENVOY_MODEL_C or (
            self.endpoint_type == ENVOY_MODEL_S and not self.isMeteringEnabled
        ):
            raw_json = self.endpoint_production_v1_results.json()
            daily_production = raw_json["wattHoursToday"]
        elif self.endpoint_type == ENVOY_MODEL_LEGACY:
            text = self.endpoint_production_results.text
            match = re.search(DAY_PRODUCTION_REGEX, text, re.MULTILINE)
            if match:
                if match.group(2) == "kWh":
                    daily_production = float(match.group(1)) * 1000
                else:
                    if match.group(2) == "MWh":
                        daily_production = float(match.group(1)) * 1000000
                    else:
                        daily_production = float(match.group(1))
            else:
                raise RuntimeError(
                    "No match for Day production, " "check REGEX  " + text
                )
        return int(daily_production)

    async def daily_consumption(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        """Only return data if Envoy supports Consumption"""
        if (
            self.endpoint_type == ENVOY_MODEL_C
            or self.endpoint_type == ENVOY_MODEL_LEGACY
        ):
            return self.message_consumption_not_available

        raw_json = self.endpoint_production_json_results.json()
        daily_consumption = raw_json["consumption"][0]["whToday"]
        return int(daily_consumption)

    async def seven_days_production(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        if self.endpoint_type == ENVOY_MODEL_S and self.isMeteringEnabled:
            raw_json = self.endpoint_production_json_results.json()
            seven_days_production = raw_json["production"][1]["whLastSevenDays"]
        elif self.endpoint_type == ENVOY_MODEL_C or (
            self.endpoint_type == ENVOY_MODEL_S and not self.isMeteringEnabled
        ):
            raw_json = self.endpoint_production_v1_results.json()
            seven_days_production = raw_json["wattHoursSevenDays"]
        elif self.endpoint_type == ENVOY_MODEL_LEGACY:
            text = self.endpoint_production_results.text
            match = re.search(WEEK_PRODUCTION_REGEX, text, re.MULTILINE)
            if match:
                if match.group(2) == "kWh":
                    seven_days_production = float(match.group(1)) * 1000
                else:
                    if match.group(2) == "MWh":
                        seven_days_production = float(match.group(1)) * 1000000
                    else:
                        seven_days_production = float(match.group(1))
            else:
                raise RuntimeError(
                    "No match for 7 Day production, " "check REGEX " + text
                )
        return int(seven_days_production)

    async def seven_days_consumption(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        """Only return data if Envoy supports Consumption"""
        if (
            self.endpoint_type == ENVOY_MODEL_C
            or self.endpoint_type == ENVOY_MODEL_LEGACY
        ):
            return self.message_consumption_not_available

        raw_json = self.endpoint_production_json_results.json()
        seven_days_consumption = raw_json["consumption"][0]["whLastSevenDays"]
        return int(seven_days_consumption)

    async def lifetime_production(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        if self.endpoint_type == ENVOY_MODEL_S and self.isMeteringEnabled:
            raw_json = self.endpoint_production_json_results.json()
            lifetime_production = raw_json["production"][1]["whLifetime"]
        elif self.endpoint_type == ENVOY_MODEL_C or (
            self.endpoint_type == ENVOY_MODEL_S and not self.isMeteringEnabled
        ):
            raw_json = self.endpoint_production_v1_results.json()
            lifetime_production = raw_json["wattHoursLifetime"]
        elif self.endpoint_type == ENVOY_MODEL_LEGACY:
            text = self.endpoint_production_results.text
            match = re.search(LIFE_PRODUCTION_REGEX, text, re.MULTILINE)
            if match:
                if match.group(2) == "kWh":
                    lifetime_production = float(match.group(1)) * 1000
                else:
                    if match.group(2) == "MWh":
                        lifetime_production = float(match.group(1)) * 1000000
                    else:
                        lifetime_production = float(match.group(1))
            else:
                raise RuntimeError(
                    "No match for Lifetime production, " "check REGEX " + text
                )
        return int(lifetime_production)

    async def lifetime_consumption(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        """Only return data if Envoy supports Consumption"""
        if (
            self.endpoint_type == ENVOY_MODEL_C
            or self.endpoint_type == ENVOY_MODEL_LEGACY
        ):
            return self.message_consumption_not_available

        raw_json = self.endpoint_production_json_results.json()
        lifetime_consumption = raw_json["consumption"][0]["whLifetime"]
        return int(lifetime_consumption)

    async def inverters_production(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        """Only return data if Envoy supports retrieving Inverter data"""
        if self.endpoint_type == ENVOY_MODEL_LEGACY:
            return None

        response_dict = {}
        try:
            for item in self.endpoint_production_inverters.json():
                response_dict[item["serialNumber"]] = [
                    item["lastReportWatts"],
                    time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(item["lastReportDate"])
                    ),
                ]
        except (JSONDecodeError, KeyError, IndexError, TypeError, AttributeError):
            return None

        return response_dict

    def run_in_console(self):
        """If running this module directly, print all the values in the console."""
        print("Reading...")
        loop = asyncio.get_event_loop()
        data_results = loop.run_until_complete(
            asyncio.gather(self.getData(), return_exceptions=True)
        )

        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(
            asyncio.gather(
                self.production(),
                self.consumption(),
                self.daily_production(),
                self.daily_consumption(),
                self.seven_days_production(),
                self.seven_days_consumption(),
                self.lifetime_production(),
                self.lifetime_consumption(),
                self.inverters_production(),
                return_exceptions=True,
            )
        )

        print("production:              {}".format(results[0]))
        print("consumption:             {}".format(results[1]))
        print("daily_production:        {}".format(results[2]))
        print("daily_consumption:       {}".format(results[3]))
        print("seven_days_production:   {}".format(results[4]))
        print("seven_days_consumption:  {}".format(results[5]))
        print("lifetime_production:     {}".format(results[6]))
        print("lifetime_consumption:    {}".format(results[7]))
        if "401" in str(data_results):
            print(
                "inverters_production:    Unable to retrieve inverter data - Authentication failure"
            )
        elif results[8] is None:
            print(
                "inverters_production:    Inverter data not available for your Envoy device."
            )
        else:
            print("inverters_production:    {}".format(results[8]))


if __name__ == "__main__":
    HOST = input(
        "Enter the Envoy IP address or host name, "
        + "or press enter to use 'envoy' as default: "
    )

    USERNAME = input(
        "Enter the Username for Inverter data authentication, "
        + "or press enter to use 'envoy' as default: "
    )

    PASSWORD = input(
        "Enter the Password for Inverter data authentication, "
        + "or press enter to use the default password: "
    )

    if HOST == "":
        HOST = "envoy"

    if USERNAME == "":
        USERNAME = "envoy"

    if PASSWORD == "":
        TESTREADER = EnvoyReader(HOST, USERNAME, inverters=True)
    else:
        TESTREADER = EnvoyReader(HOST, USERNAME, PASSWORD, inverters=True)

    TESTREADER.run_in_console()
