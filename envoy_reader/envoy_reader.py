import asyncio
import json
import time

import re
import httpcore
import httpx

"""Module to read production and consumption values from an Enphase Envoy on
 the local network"""

PRODUCTION_REGEX = \
    r'<td>Currentl.*</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(W|kW|MW)</td>'
DAY_PRODUCTION_REGEX = \
    r'<td>Today</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>'
WEEK_PRODUCTION_REGEX = \
    r'<td>Past Week</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>'
LIFE_PRODUCTION_REGEX = \
    r'<td>Since Installation</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>'

ENDPOINT_URL_PRODUCTION_JSON = "http://{}/production.json"
ENDPOINT_URL_PRODUCTION_V1 = "http://{}/api/v1/production"
ENDPOINT_URL_PRODUCTION_INVERTERS = "http://{}/api/v1/production/inverters"
ENDPOINT_URL_PRODUCTION = "http://{}/production"

class EnvoyReader():
    """Instance of EnvoyReader"""
    # P0 for older Envoy model C, s/w < R3.9 no json pages
    # P for production data only (ie. Envoy model C, s/w >= R3.9)
    # PC for production and consumption data (ie. Envoy model S)

    message_consumption_not_available = ("Consumption data not available for "
                                         "your Envoy device.")

    def __init__(self, host, username="envoy", password="", inverters=False):
        self.host = host.lower()
        self.username = username
        self.password = password
        self.get_inverters = inverters
        self.endpoint_type = ""
        self.serial_number_last_six = ""
        self.endpoint_production_json_results = ""
        self.endpoint_production_v1_results = ""
        self.endpoint_production_inverters = ""
        self.endpoint_production_results = ""
        self.isMeteringEnabled = False

    def hasProductionAndConsumption(self, json):
        """Check if json has keys for both production and consumption"""
        return "production" in json and "consumption" in json

    def hasMeteringSetup(self, json):
        """Check if Active Count of Production CTs (eim) installed is greater than one"""
        if json["production"][1]["activeCount"] > 0:
            return True
        else:
            return False

    async def getData(self):
        try:
            async with httpx.AsyncClient() as client:
                self.endpoint_production_json_results = await client.get(
                    ENDPOINT_URL_PRODUCTION_JSON.format(self.host), timeout=30, allow_redirects=False)
                self.endpoint_production_v1_results = await client.get(
                    ENDPOINT_URL_PRODUCTION_V1.format(self.host), timeout=30, allow_redirects=False)
                self.endpoint_production_results = await client.get(
                    ENDPOINT_URL_PRODUCTION.format(self.host), timeout=30, allow_redirects=False)
        except httpx.HTTPError:
            pass
        
        await self.detect_model()
        
        if(self.get_inverters):
            """If a password was not given as an argument when instantiating
            the EnvoyReader object than use the last six numbers of the serial
            number as the password.  Otherwise use the password argument value."""
            if self.password == "":
                if self.serial_number_last_six == "":
                    try:
                        await self.get_serial_number()
                    except httpx.HTTPError:
                        raise
                    self.password = self.serial_number_last_six
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(ENDPOINT_URL_PRODUCTION_INVERTERS.format(self.host),
                        timeout=30, auth=httpx.DigestAuth(self.username, self.password))
                if response is not None and response.status_code != 401:                                    
                    self.endpoint_production_inverters = response
                else:
                    response.raise_for_status()
            except (httpx.RemoteProtocolError):
                raise
            except (httpcore.RemoteProtocolError, httpx.RemoteProtocolError):
                await response.close()
            except httpx.HTTPError:
                response.raise_for_status()

    async def detect_model(self):
        """Method to determine if the Envoy supports consumption values or
         only production"""

        if self.endpoint_production_json_results.status_code == 200 and self.hasProductionAndConsumption(self.endpoint_production_json_results.json()):
            self.isMeteringEnabled = self.hasMeteringSetup(self.endpoint_production_json_results.json())
            self.endpoint_type = "PC"
            return
        else:
            if self.endpoint_production_v1_results.status_code == 200:
                self.endpoint_type = "P"       # Envoy-C, production only
                return
            else:
                endpoint_url = ENDPOINT_URL_PRODUCTION.format(self.host)
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        endpoint_url, timeout=30, allow_redirects=False)
                if response.status_code == 200:
                    self.endpoint_type = "P0"       # older Envoy-C
                    return

        raise RuntimeError(
            "Could not connect or determine Envoy model. " +
            "Check that the device is up at 'http://" + self.host + "'.")

    async def get_serial_number(self):
        """Method to get last six digits of Envoy serial number for auth"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://{}/info.xml".format(self.host),
                    timeout=30, allow_redirects=False)
            if len(response.text) > 0:
                sn = response.text.split("<sn>")[1].split("</sn>")[0][-6:]
                self.serial_number_last_six = sn
        except httpx.ConnectionError:
            raise

    def create_connect_errormessage(self):
        """Create error message if unable to connect to Envoy"""
        return ("Unable to connect to Envoy. " +
                "Check that the device is up at 'http://"
                + self.host + "'.")

    def create_json_errormessage(self):
        """Create error message if unable to parse JSON response"""
        return ("Got a response from '" + self.host +
                "', but metric could not be found. " +
                "Maybe your model of Envoy doesn't " +
                "support the requested metric.")

    async def production(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        try:
            if self.endpoint_type == "PC":
                raw_json = self.endpoint_production_json_results.json()
                if self.isMeteringEnabled:
                    production = raw_json["production"][1]["wNow"]
                else:
                    production = raw_json["production"][0]["wNow"]
            else:
                if self.endpoint_type == "P":
                    raw_json = self.endpoint_production_v1_results.json()
                    production = raw_json["wattsNow"]
                else:
                    if self.endpoint_type == "P0":
                        text = self.endpoint_production_results.text
                        match = re.search(
                            PRODUCTION_REGEX, text, re.MULTILINE)
                        if match:
                            if match.group(2) == "kW":
                                production = float(match.group(1))*1000
                            else:
                                if match.group(2) == "mW":
                                    production = float(
                                        match.group(1))*1000000
                                else:
                                    production = float(match.group(1))
                        else:
                            raise RuntimeError(
                                "No match for production, check REGEX  "
                                + text)
            return int(production)

        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            raise

    async def consumption(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        """Only return data if Envoy supports Consumption"""
        if self.endpoint_type == "P" or self.endpoint_type == "P0":
            return self.message_consumption_not_available

        try:
            raw_json = self.endpoint_production_json_results.json()
            consumption = raw_json["consumption"][0]["wNow"]
            return int(consumption)

        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            raise

    async def daily_production(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        try:
            if self.endpoint_type == "PC" and self.isMeteringEnabled:
                raw_json = self.endpoint_production_json_results.json()
                daily_production = raw_json["production"][1]["whToday"]
            elif self.endpoint_type == "PC" and not self.isMeteringEnabled:
                raw_json = self.endpoint_production_v1_results.json()
                daily_production = raw_json["wattHoursToday"]
            else:
                if self.endpoint_type == "P":
                    raw_json = self.endpoint_production_v1_results.json()
                    daily_production = raw_json["wattHoursToday"]
                else:
                    if self.endpoint_type == "P0":
                        text = self.endpoint_production_results.text
                        match = re.search(
                            DAY_PRODUCTION_REGEX, text, re.MULTILINE)
                        if match:
                            if match.group(2) == "kWh":
                                daily_production = float(
                                    match.group(1))*1000
                            else:
                                if match.group(2) == "MWh":
                                    daily_production = float(
                                        match.group(1))*1000000
                                else:
                                    daily_production = float(
                                        match.group(1))
                        else:
                            raise RuntimeError(
                                "No match for Day production, "
                                "check REGEX  " +
                                text)
            return int(daily_production)

        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            raise

    async def daily_consumption(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        """Only return data if Envoy supports Consumption"""
        if self.endpoint_type == "P" or self.endpoint_type == "P0":
            return self.message_consumption_not_available

        try:
            raw_json = self.endpoint_production_json_results.json()
            daily_consumption = raw_json["consumption"][0]["whToday"]
            return int(daily_consumption)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            raise

    async def seven_days_production(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        try:
            if self.endpoint_type == "PC" and self.isMeteringEnabled:
                raw_json = self.endpoint_production_json_results.json()
                seven_days_production = raw_json["production"][1]["whLastSevenDays"]
            elif self.endpoint_type == "PC" and not self.isMeteringEnabled:
                raw_json = self.endpoint_production_v1_results.json()
                seven_days_production = raw_json["wattHoursSevenDays"]
            else:
                if self.endpoint_type == "P":
                    raw_json = self.endpoint_production_v1_results.json()
                    seven_days_production = raw_json["wattHoursSevenDays"]
                else:
                    if self.endpoint_type == "P0":
                        text = self.endpoint_production_results.text
                        match = re.search(
                            WEEK_PRODUCTION_REGEX, text, re.MULTILINE)
                        if match:
                            if match.group(2) == "kWh":
                                seven_days_production = float(
                                    match.group(1))*1000
                            else:
                                if match.group(2) == "MWh":
                                    seven_days_production = float(
                                        match.group(1))*1000000
                                else:
                                    seven_days_production = float(
                                        match.group(1))
                        else:
                            raise RuntimeError("No match for 7 Day production, "
                                               "check REGEX " + text)
            return int(seven_days_production)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            raise

    async def seven_days_consumption(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        """Only return data if Envoy supports Consumption"""
        if self.endpoint_type == "P" or self.endpoint_type == "P0":
            return self.message_consumption_not_available

        try:
            raw_json = self.endpoint_production_json_results.json()
            seven_days_consumption = raw_json["consumption"][0]["whLastSevenDays"]
            return int(seven_days_consumption)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            raise

    async def lifetime_production(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        try:
            if self.endpoint_type == "PC" and self.isMeteringEnabled:
                raw_json = self.endpoint_production_json_results.json()
                lifetime_production = raw_json["production"][1]["whLifetime"]
            elif self.endpoint_type == "PC" and not self.isMeteringEnabled:
                raw_json = self.endpoint_production_v1_results.json()
                lifetime_production = raw_json["wattHoursLifetime"]
            else:
                if self.endpoint_type == "P":
                    raw_json = self.endpoint_production_v1_results.json()
                    lifetime_production = raw_json["wattHoursLifetime"]
                else:
                    if self.endpoint_type == "P0":
                        text = self.endpoint_production_results.text
                        match = re.search(
                            LIFE_PRODUCTION_REGEX, text, re.MULTILINE)
                        if match:
                            if match.group(2) == "kWh":
                                lifetime_production = float(
                                    match.group(1))*1000
                            else:
                                if match.group(2) == "MWh":
                                    lifetime_production = float(
                                        match.group(1))*1000000
                                else:
                                    lifetime_production = float(
                                        match.group(1))
                        else:
                            raise RuntimeError(
                                "No match for Lifetime production, "
                                "check REGEX " + text)
            return int(lifetime_production)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            raise

    async def lifetime_consumption(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        """Only return data if Envoy supports Consumption"""
        if self.endpoint_type == "P" or self.endpoint_type == "P0":
            return self.message_consumption_not_available

        try:
            raw_json = self.endpoint_production_json_results.json()
            lifetime_consumption = raw_json["consumption"][0]["whLifetime"]
            return int(lifetime_consumption)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            raise

    async def inverters_production(self):
        """Running getData() beforehand will set self.enpoint_type and self.isDataRetrieved"""
        """so that this method will only read data from stored variables"""

        """Only return data if Envoy supports retrieving Inverter data"""
        if self.endpoint_type == "P0":
            return "Inverter data not available for your Envoy device."

        response_dict = {}
        try:
            for item in self.endpoint_production_inverters.json():
                response_dict[item["serialNumber"]] = [item["lastReportWatts"], time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item["lastReportDate"]))]
        except (json.decoder.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError):
            return None

        return response_dict

    def run_in_console(self):
        """If running this module directly, print all the values in the
         console."""
        print("Reading...")
        loop = asyncio.get_event_loop()
        dataResults = loop.run_until_complete(asyncio.gather(
            self.getData(), return_exceptions=True
        ))

        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(asyncio.gather(
            self.production(),
            self.consumption(),
            self.daily_production(),
            self.daily_consumption(),
            self.seven_days_production(),
            self.seven_days_consumption(),
            self.lifetime_production(),
            self.lifetime_consumption(),
            self.inverters_production(), return_exceptions=True))

        print("production:              {}".format(results[0]))
        print("consumption:             {}".format(results[1]))
        print("daily_production:        {}".format(results[2]))
        print("daily_consumption:       {}".format(results[3]))
        print("seven_days_production:   {}".format(results[4]))
        print("seven_days_consumption:  {}".format(results[5]))
        print("lifetime_production:     {}".format(results[6]))
        print("lifetime_consumption:    {}".format(results[7]))
        if "401" in str(dataResults):
            print("inverters_production:    Unable to retrieve inverter data - Authentication failure")
        else:
            print("inverters_production:    {}".format(results[8]))


if __name__ == "__main__":
    HOST = input("Enter the Envoy IP address or host name, " +
                 "or press enter to use 'envoy' as default: ")

    USERNAME = input("Enter the Username for Inverter data authentication, " +
                     "or press enter to use 'envoy' as default: ")

    PASSWORD = input("Enter the Password for Inverter data authentication, " +
                     "or press enter to use the default password: ")

    if HOST == "":
        HOST = "envoy"

    if USERNAME == "":
        USERNAME = "envoy"

    if PASSWORD == "":
        TESTREADER = EnvoyReader(HOST, USERNAME, inverters=True)
    else:
        TESTREADER = EnvoyReader(HOST, USERNAME, PASSWORD, inverters=True)

    TESTREADER.run_in_console()
