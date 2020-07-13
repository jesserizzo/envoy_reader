import asyncio
import json
import time
from datetime import datetime, timedelta

import re
import httpx
import h11
import logging

from .const import (feature_none, feature_production, feature_consumption, feature_inverters, feature_all_sensors_data, response_api_v1_production, response_api_v1_inverters, response_json_production, response_html_production, INFO_XML_URL, PRODUCTION_API_URL, INVERTERS_API_URL, PRODUCTION_JSON_URL, PRODUCTION_HTML_URL, PRODUCTION_REGEX, DAY_PRODUCTION_REGEX, WEEK_PRODUCTION_REGEX, LIFE_PRODUCTION_REGEX, message_data_not_available)

"""Module to read production and consumption values from an Enphase Envoy on
 the local network"""

_LOGGER = logging.getLogger(__name__)


class EnvoyReader():
    """Instance of EnvoyReader"""
    # PRODUCTION_HTML_URL for older Envoy model C, s/w < R3.9 no json pages
    # P for production data only (ie. Envoy model C, s/w >= R3.9)
    # PC for production and consumption data (ie. Envoy model S)

    def __init__(self, host, username="envoy", password=""):
        self.host = host.lower()
        self.username = username
        self._password = password
        self._serial_number = ''
        self.sensors = {}
        self._features = {}
        self.required_sensors = feature_all_sensors_data
        self.clent_session = None
        self.cached_response = {}
        self._lock = asyncio.Lock()
        self._last_state_update = None
        self._sensors_update_interval = timedelta(seconds=15)

    @property
    def support_features(self):
        all_features = feature_none
        for features in self._features.values():
            all_features |= features
        return all_features

    @property
    def serial_number(self):
        return self._serial_number

    @property
    def password(self):
        if self._password == '' and self._serial_number != '':
            return self.serial_number[-6:]
        else:
            return self._password

    @property
    def update_interval(self):
        return self._sensors_update_interval.total_seconds()

    @update_interval.setter
    def update_interval(self, interval):
        self._sensors_update_interval = timedelta(seconds=interval)

    def hasProductionAndConsumption(self, json):
        """Check if json has keys for both production and consumption"""
        return "production" in json and "consumption" in json

    async def getEnvoyResponse(self, endpoint_url_template, json_format=True, auth=None):
        try:
            if self.clent_session is None:
                self.clent_session = httpx.AsyncClient()
            endpoint_url = endpoint_url_template.format(self.host)
            if auth is None:
                response = await self.clent_session.get(endpoint_url)
            else:
                response = await self.clent_session.get(endpoint_url, auth=auth)
            if response.status_code == 200:
                if json_format is True:
                    return response.status_code, response.json()
                else:
                    return response.status_code, response.text
            else:
                return response.status_code, None
        except httpx.HTTPError:
            _LOGGER.warning(self.create_connect_errormessage())
            return 599, self.create_connect_errormessage()
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return 422, self.create_json_errormessage(endpoint_url_template.format(self.host))
        except h11.RemoteProtocolError:
            await response.close()
            return 501, None

    def getValueFromJson(raw_json, key, object=None, index=None):
        try:
            if object is not None and index is not None:
                value = raw_json[object][index][key]
            else:
                value = raw_json[key]
            return int(value)
        except IndexError:
            pass
        return None

    async def getJsonProduction(self):
        raw_json = None
        if response_json_production in self.cached_response:
            raw_json = self.cached_response[response_json_production]
        else:
            status_code, raw_json = await self.getEnvoyResponse(PRODUCTION_JSON_URL)
            if status_code == 200:
                self.cached_response[response_json_production] = raw_json
        return raw_json

    async def getProductionFromProductionJson(self):
        raw_json = await self.getJsonProduction()
        if raw_json:
            production = (EnvoyReader.getValueFromJson(raw_json, "wNow", "production", 0)
                          or EnvoyReader.getValueFromJson(raw_json, "wNow", "production", 1)
                          or 0)
            daily = (EnvoyReader.getValueFromJson(raw_json, "whToday", "production", 1)
                     or 0)
            seven_days = (EnvoyReader.getValueFromJson(raw_json, "whLastSevenDays", "production", 1)
                          or 0)
            lifetime = (EnvoyReader.getValueFromJson(raw_json, "whLifetime", "production", 0)
                        or EnvoyReader.getValueFromJson(raw_json, "whLifetime", "production", 1)
                        or 0)
            return production, daily, seven_days, lifetime

    async def getConsumptionFromProductionJson(self):
        raw_json = await self.getJsonProduction()
        if raw_json:
            consumption = EnvoyReader.getValueFromJson(raw_json, "wNow", "consumption", 0) or 0
            daily = EnvoyReader.getValueFromJson(raw_json, "whToday", "consumption", 0) or 0
            seven_days = EnvoyReader.getValueFromJson(raw_json, "whLastSevenDays", "consumption", 0) or 0
            lifetime = EnvoyReader.getValueFromJson(raw_json, "whLifetime", "consumption", 0) or 0
            return consumption, daily, seven_days, lifetime

    async def getAPIv1Production(self):
        if response_api_v1_production in self.cached_response:
            raw_json = self.cached_response[response_api_v1_production]
        else:
            status_code, raw_json = await self.getEnvoyResponse(PRODUCTION_API_URL)
            if status_code == 200:
                self.cached_response[response_api_v1_production] = raw_json
        return raw_json

    async def getProductionFromProductionAPI(self):
        raw_json = await self.getAPIv1Production()
        if raw_json:
            production = EnvoyReader.getValueFromJson(raw_json, "wattsNow") or 0
            daily = EnvoyReader.getValueFromJson(raw_json, "wattHoursToday") or 0
            seven_days = EnvoyReader.getValueFromJson(raw_json, "wattHoursSevenDays") or 0
            lifetime = EnvoyReader.getValueFromJson(raw_json, "wattHoursLifetime") or 0
            return production, daily, seven_days, lifetime

    async def getHtmlProduction(self):
        if response_html_production in self.cached_response:
            raw_text = self.cached_response[response_html_production]
        else:
            status_code, raw_text = await self.getEnvoyResponse(PRODUCTION_HTML_URL, json_format=False)
            if status_code == 200:
                self.cached_response[response_html_production] = raw_text
        return raw_text

    async def getProductionFromProductionHTML(self):
        raw_text = await self.getHtmlProduction()
        if raw_text:
            production = EnvoyReader.getProductionFromHtml(raw_text)
            daily = EnvoyReader.getDailyProductionFromHtml(raw_text)
            seven_days = EnvoyReader.getSevenDaysProductionFromHtml(raw_text)
            lifetime = EnvoyReader.getLifetimeProductionFromHtml(raw_text)
            return production, daily, seven_days, lifetime

    async def getAPIv1Inverters(self):
        await self.get_serial_number()
        if response_api_v1_inverters in self.cached_response:
            raw_json = self.cached_response[response_api_v1_inverters]
        else:
            auth = httpx.DigestAuth(self.username, self.password)
            status_code, raw_json = await self.getEnvoyResponse(INVERTERS_API_URL, auth=auth)
            if status_code == 200:
                self.cached_response[response_api_v1_inverters] = raw_json
            else:
                raw_json = None
        return raw_json

    async def getInvertersFromProductionAPI(self):
        raw_json = await self.getAPIv1Inverters()
        if raw_json:
            response_dict = {}
            for item in raw_json:
                response_dict[item["serialNumber"]] = [item["lastReportWatts"], time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item["lastReportDate"]))]
            return response_dict

    async def detect_model(self):
        """Method to determine if the Envoy supports consumption values or
         only production"""

        self._features.clear()

        try:
            productions = await self.getProductionFromProductionJson()
            if productions[1] > 0 or productions[2] > 0:
                self._features[response_json_production] |= feature_production
            consumptions = await self.getConsumptionFromProductionJson()
            if consumptions[1] > 0 or consumptions[2] > 0:
                self._features[response_json_production] |= feature_consumption
            if response_json_production in self._features:
                _LOGGER.debug("response_json_production features: {}".format(self._features[response_json_production]))
        except TypeError:
            pass

        try:
            productions = await self.getProductionFromProductionAPI()
            if productions[1] > 0 or productions[2] > 0:
                self._features[response_api_v1_production] = feature_production
            _LOGGER.debug("response_api_v1_production features: {}".format(self._features[response_api_v1_production]))
        except TypeError:
            pass

        if not self._features and await self.getHtmlProduction():
            self._features[response_html_production] = feature_production
            _LOGGER.debug("response_html_production features: {}".format(self._features[response_html_production]))

        if await self.getAPIv1Inverters():
            self._features[response_api_v1_inverters] = feature_inverters
            _LOGGER.debug("response_api_v1_inverters features: {}".format(self._features[response_api_v1_inverters]))

        _LOGGER.debug("support_features: {}".format(self.support_features))
        if self.support_features == feature_none:
            raise RuntimeError(
                "Could not connect or determine Envoy model. " +
                "Check that the device is up at 'http://" + self.host + "'.")

    def set_mode(self, mode):
        if mode == "PC" or mode == "EnvoyS":
            self._features[response_json_production] = feature_production | feature_consumption
            self._features[response_api_v1_production] = feature_production
            self._features[response_api_v1_inverters] = feature_inverters
        elif mode == "P" or mode == "EnvoyC":
            self._features[response_api_v1_production] = feature_production
            self._features[response_api_v1_inverters] = feature_inverters
        elif mode == "P0" or mode == "EnvoyO":
            self._features[response_html_production] = feature_production
        elif mode == "IQEnvoy":
            self._features[response_json_production] = feature_consumption
            self._features[response_api_v1_production] = feature_production
            self._features[response_api_v1_inverters] = feature_inverters
        _LOGGER.debug("support_features: {}".format(self.support_features))

    async def get_serial_number(self):
        """Method to get last six digits of Envoy serial number for auth"""
        if self._serial_number != '' or self._password != '':
            return
        try:
            status, raw_text = await self.getEnvoyResponse(INFO_XML_URL, json_format=False)
            if status == 200 and len(raw_text) > 0:
                sn = raw_text.split("<sn>")[1].split("</sn>")[0]
                if len(sn) >= 6:
                    self._serial_number = sn
            _LOGGER.debug("serial number: {}".format(self._serial_number))
        except TypeError:
            pass

    async def update_sensors_value(self, names, values):
        if isinstance(names, tuple) and isinstance(values, tuple):
            minlen = min(len(names), len(values))
            for index in range(minlen):
                self.sensors[names[index]] = values[index]

    def is_features_supported(self, response, features):
        return (response in self._features
                and (self._features[response] & features) == features)

    async def update_required_sensors(self):
        valid_sensors = self.required_sensors & self.support_features
        _LOGGER.debug("valid sensors: {}".format(valid_sensors))

        consumption_sensors = valid_sensors & feature_consumption
        production_sensors = valid_sensors & feature_production
        inverters_sensors = valid_sensors & feature_inverters
        if consumption_sensors:
            sensors = 'consumption', 'daily_consumption', 'seven_days_consumption', 'lifetime_consumption'
            values = await self.getConsumptionFromProductionJson()
            await self.update_sensors_value(sensors, values)
            if self.is_features_supported(response_json_production, production_sensors):
                sensors = 'production', 'daily_production', 'seven_days_production', 'lifetime_production'
                values = await self.getProductionFromProductionJson()
                await self.update_sensors_value(sensors, values)
                production_sensors = feature_none
        if production_sensors:
            # read from api_v1 first, as it is faster
            sensors = 'production', 'daily_production', 'seven_days_production', 'lifetime_production'
            if self.is_features_supported(response_api_v1_production, production_sensors):
                values = await self.getProductionFromProductionAPI()
                await self.update_sensors_value(sensors, values)
            elif self.is_features_supported(response_json_production, production_sensors):
                values = await self.getProductionFromProductionJson()
                await self.update_sensors_value(sensors, values)
            elif self.is_features_supported(response_html_production, production_sensors):
                values = await self.getProductionFromProductionHTML()
                await self.update_sensors_value(sensors, values)
        if inverters_sensors:
            values = await self.getInvertersFromProductionAPI()
            self.sensors['inverters_production'] = values

        self.cached_response.clear()

    def checkUpdateInterval(self):
        call_dt = datetime.utcnow()
        if self._last_state_update is None or \
           call_dt >= self._sensors_update_interval + self._last_state_update:
            self._last_state_update = datetime.utcnow()
            return True
        return False

    async def call_api(self):
        """Method to call the Envoy API"""
        # detection of endpoint if not already known
        async with self._lock:
            if not self._features:
                await self.detect_model()
            if self.checkUpdateInterval():
                await self.update_required_sensors()

    def create_connect_errormessage(self):
        """Create error message if unable to connect to Envoy"""
        return ("Unable to connect to Envoy. " +
                "Check that the device is up at 'http://"
                + self.host + "'.")

    def create_json_errormessage(self, endpoint_url):
        """Create error message if unable to parse JSON response"""
        return ("Got a response from '" + endpoint_url +
                "', but metric could not be found. " +
                "Maybe your model of Envoy doesn't " +
                "support the requested metric.")

    async def production(self):
        await self.call_api()
        if 'production' in self.sensors:
            return self.sensors['production']
        else:
            return 0

    async def consumption(self):
        await self.call_api()
        if not (self.support_features & feature_consumption):
            return message_data_not_available.format('Consumption')
        elif 'consumption' in self.sensors:
            return self.sensors['consumption']
        else:
            return 0

    async def daily_production(self):
        await self.call_api()
        if 'daily_production' in self.sensors:
            return self.sensors['daily_production']
        else:
            return 0

    async def daily_consumption(self):
        await self.call_api()
        if not (self.support_features & feature_consumption):
            return message_data_not_available.format('Consumption')
        elif 'daily_consumption' in self.sensors:
            return self.sensors['daily_consumption']
        else:
            return 0

    async def seven_days_production(self):
        await self.call_api()
        if 'seven_days_production' in self.sensors:
            return self.sensors['seven_days_production']
        else:
            return 0

    async def seven_days_consumption(self):
        await self.call_api()
        if not (self.support_features & feature_consumption):
            return message_data_not_available.format('Consumption')
        elif 'seven_days_consumption' in self.sensors:
            return self.sensors['seven_days_consumption']
        else:
            return 0

    async def lifetime_production(self):
        await self.call_api()
        if 'lifetime_production' in self.sensors:
            return self.sensors['lifetime_production']
        else:
            return 0

    async def lifetime_consumption(self):
        await self.call_api()
        if not (self.support_features & feature_consumption):
            return message_data_not_available.format('Consumption')
        elif 'lifetime_consumption' in self.sensors:
            return self.sensors['lifetime_consumption']
        else:
            return 0

    async def inverters_production(self):
        await self.call_api()
        if not (self.support_features & feature_inverters):
            return message_data_not_available.format('Inverters production')
        elif 'inverters_production' in self.sensors:
            return self.sensors['inverters_production']
        else:
            return 0

    async def getProductionFromHtml(self, raw_text):
        """Call API and parse production values from response"""
        try:
            match = re.search(
                PRODUCTION_REGEX, raw_text, re.MULTILINE)
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
                    + raw_text)
            return int(production)
        except AttributeError:
            _LOGGER.debug("unknown error on getProductionFromHtml")
            pass

    async def getDailyProductionFromHtml(self, raw_text):
        """Call API and parse todays production values from response"""
        try:
            match = re.search(
                DAY_PRODUCTION_REGEX, raw_text, re.MULTILINE)
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
                    raw_text)
            return int(daily_production)
        except AttributeError:
            _LOGGER.debug("unknown error on getDailyProductionFromHtml")
            pass

    async def getSevenDaysProductionFromHtml(self, raw_text):
        """Call API and parse the past seven days production values from the
         response"""
        try:
            match = re.search(
                WEEK_PRODUCTION_REGEX, raw_text, re.MULTILINE)
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
                                   "check REGEX " + raw_text)
            return int(seven_days_production)
        except AttributeError:
            _LOGGER.debug("unknown error on getSevenDaysProductionFromHtml")
            pass

    async def getLifetimeProductionFromHtml(self, raw_text):
        """Call API and parse the lifetime of production from response"""
        try:
            match = re.search(
                LIFE_PRODUCTION_REGEX, raw_text, re.MULTILINE)
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
                    "check REGEX " + raw_text)
            return int(lifetime_production)
        except AttributeError:
            _LOGGER.debug("unknown error on getLifetimeProductionFromHtml")
            pass

    async def update(self):
        """
        Single entry point for Home Assistant
        """
        data = {}

        tasks = [
            self.production(),
            self.consumption(),
            self.daily_production(),
            self.daily_consumption(),
            self.seven_days_production(),
            self.seven_days_consumption(),
            self.lifetime_production(),
            self.lifetime_consumption(),
            self.inverters_production()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for key, result in zip(tasks, results):
            key = key.__name__
            data[key] = result

        return data

    def run_in_console(self):
        """If running this module directly, print all the values in the
         console."""
        print("Reading...")
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
            self.inverters_production()))
        print("production:              {}".format(results[0]))
        print("consumption:             {}".format(results[1]))
        print("daily_production:        {}".format(results[2]))
        print("daily_consumption:       {}".format(results[3]))
        print("seven_days_production:   {}".format(results[4]))
        print("seven_days_consumption:  {}".format(results[5]))
        print("lifetime_production:     {}".format(results[6]))
        print("lifetime_consumption:    {}".format(results[7]))
        print("inverters_production:    {}".format(results[8]))
