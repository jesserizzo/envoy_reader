import requests
import sys
import json
import re

PRODUCTION_REGEX = r'<td>Currentl.*</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(W|kW|MW)</td>'
DAY_PRODUCTION_REGEX = r'<td>Today</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>'
WEEK_PRODUCTION_REGEX = r'<td>Past Week</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>'
LIFE_PRODUCTION_REGEX = r'<td>Since Installation</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>'

class EnvoyReader():
    # P0 for older Envoy model C, firmware before R3.9.xx, without local api json pages
    # P for production data only (ie. Envoy model C, firmware R3.9.xx and later)
    # PC for production and consumption data (ie. Envoy model S)
    endpoint_type = ""
    endpoint_url = ""

    message_consumption_not_available = "Consumption data not available for your Envoy device."

    def __init__(self, host):
        self.host = host.lower()

    def detect_model(self):
        self.endpoint_url = "http://{}/production.json".format(self.host)
        response = requests.get(self.endpoint_url, timeout=30, allow_redirects=False)
        if response.status_code == 200 and len(response.json()) == 3:
            self.endpoint_type = "PC"       # Envoy-S, Production and Consumption monitoring
            return
        else:
            self.endpoint_url = "http://{}/api/v1/production".format(self.host)
            response = requests.get(self.endpoint_url, timeout=30, allow_redirects=False)
            if response.status_code == 200:
                self.endpoint_type = "P"       # newer Envoy-C, production only
                return
            else:
                self.endpoint_url = "http://{}/production".format(self.host)
                response = requests.get(self.endpoint_url, timeout=30, allow_redirects=False)
                if response.status_code == 200:
                    self.endpoint_type = "P0"       # older firmware Envoy-C, production only
                    return

        self.endpoint_url = ""
        raise RuntimeError(
                "Could not connect or determine Envoy model. " +
                "Check that the device is up at 'http://" + self.host + "'.")

    def call_api(self):
        # detection of endpoint if not already known
        if self.endpoint_type == "":
            EnvoyReader.detect_model(self)

        response = requests.get(self.endpoint_url, timeout=30, allow_redirects=False)
        if self.endpoint_type == "P" or self.endpoint_type == "PC":
            return response.json()         # these little Envoys have .json
        if self.endpoint_type == "P0":
            return response.text           # these little Envoys have none...

    def create_connect_errormessage(self):
        return ("Unable to connect to Envoy. Check that the device is up at 'http://" + self.host + "'.")

    def create_json_errormessage(self):
        return ("Got a response from '" + self.endpoint_url + "', but metric could not be found. " +
                "Maybe your model of Envoy doesn't support the requested metric.")

    def production(self):
        if self.endpoint_type == "":
            EnvoyReader.detect_model(self)

        try:
            if self.endpoint_type == "PC":
                raw_json = EnvoyReader.call_api(self)
                production = raw_json["production"][1]["wNow"]
            else:
                if self.endpoint_type == "P":
                    raw_json = EnvoyReader.call_api(self)
                    production = raw_json["wattsNow"]
                else:
                    if self.endpoint_type == "P0":
                        text = EnvoyReader.call_api(self)
                        match = re.search(PRODUCTION_REGEX, text, re.MULTILINE)
                        if match:
                            if match.group(2) == "kW":
                                production = float(match.group(1))*1000
                            else:
                                if match.group(2) == "mW":
                                    production = float(match.group(1))*1000000
                                else:
                                    production = float(match.group(1))
                        else:
                            raise RuntimeError("No match for production, check REGEX  " +  text)
            return int(production)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)

    def consumption(self):
        if self.endpoint_type == "P" or self.endpoint_type == "P0":
            return self.message_consumption_not_available

        try:
            raw_json = EnvoyReader.call_api(self)
            consumption = raw_json["consumption"][0]["wNow"]
            return int(consumption)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)

    def daily_production(self):
        if self.endpoint_type == "":
            EnvoyReader.detect_model(self)

        try:
            if self.endpoint_type == "PC":
                raw_json = EnvoyReader.call_api(self)
                daily_production = raw_json["production"][1]["whToday"]
            else:
                if self.endpoint_type == "P":
                    raw_json = EnvoyReader.call_api(self)
                    daily_production = raw_json["wattHoursToday"]
                else:
                    if self.endpoint_type == "P0":
                        text = EnvoyReader.call_api(self)
                        match = re.search(DAY_PRODUCTION_REGEX, text, re.MULTILINE)
                        if match:
                            if match.group(2) == "kWh":
                                daily_production = float(match.group(1))*1000
                            else:
                                if match.group(2) == "MWh":
                                    daily_production = float(match.group(1))*1000000
                                else:
                                    daily_production = float(match.group(1))
                        else:
                            raise RuntimeError("No match for Day production, check REGEX  " +  text)
            return int(daily_production)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)

    def daily_consumption(self):
        if self.endpoint_type == "P" or self.endpoint_type == "P0":
            return self.message_consumption_not_available

        try:
            raw_json = EnvoyReader.call_api(self)
            daily_consumption = raw_json["consumption"][0]["whToday"]
            return int(daily_consumption)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)

    def seven_days_production(self):
        if self.endpoint_type == "":
            EnvoyReader.detect_model(self)

        try:
            if self.endpoint_type == "PC":
                raw_json = EnvoyReader.call_api(self)
                seven_days_production = raw_json["production"][1]["whLastSevenDays"]
            else:
                if self.endpoint_type == "P":
                    raw_json = EnvoyReader.call_api(self)
                    seven_days_production = raw_json["wattHoursSevenDays"]
                else:
                    if self.endpoint_type == "P0":
                        text = EnvoyReader.call_api(self)
                        match = re.search(WEEK_PRODUCTION_REGEX, text, re.MULTILINE)
                        if match:
                            if match.group(2) == "kWh":
                                seven_days_production = float(match.group(1))*1000
                            else:
                                if match.group(2) == "MWh":
                                    seven_days_production = float(match.group(1))*1000000
                                else:
                                    seven_days_production = float(match.group(1))
                        else:
                            raise RuntimeError("No match for 7 Day production, check REGEX " +  text)
            return int(seven_days_production)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)

    def seven_days_consumption(self):
        if self.endpoint_type == "P" or self.endpoint_type == "P0":
            return self.message_consumption_not_available

        try:
            raw_json = EnvoyReader.call_api(self)
            seven_days_consumption = raw_json["consumption"][0]["whLastSevenDays"]
            return int(seven_days_consumption)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)

    def lifetime_production(self):
        if self.endpoint_type == "":
            EnvoyReader.detect_model(self)

        try:
            if self.endpoint_type == "PC":
                raw_json = EnvoyReader.call_api(self)
                lifetime_production = raw_json["production"][1]["whLifetime"]
            else:
                if self.endpoint_type == "P":
                    raw_json = EnvoyReader.call_api(self)
                    lifetime_production = raw_json["wattHoursLifetime"]
                else:
                    if self.endpoint_type == "P0":
                        text = EnvoyReader.call_api(self)
                        match = re.search(LIFE_PRODUCTION_REGEX, text, re.MULTILINE)
                        if match:
                            if match.group(2) == "kWh":
                                lifetime_production = float(match.group(1))*1000
                            else:
                                if match.group(2) == "MWh":
                                    lifetime_production = float(match.group(1))*1000000
                                else:
                                    lifetime_production = float(match.group(1))
                        else:
                            raise RuntimeError("No match for Lifetime production, check REGEX " +  text)
            return int(lifetime_production)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)

    def lifetime_consumption(self):
        if self.endpoint_type == "P" or self.endpoint_type == "P0":
            return self.message_consumption_not_available

        try:
            raw_json = EnvoyReader.call_api(self)
            lifetime_consumption = raw_json["consumption"][0]["whLifetime"]
            return int(lifetime_consumption)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)


if __name__ == "__main__":
    host = input("Enter the Envoy IP address or host name, " +
                 "or press enter to use 'envoy' as default: ")
    if host == "":
        host = "envoy"

    testreader = EnvoyReader(host)
    print("production:              {}".format(testreader.production()))
    print("consumption:             {}".format(testreader.consumption()))
    print("daily_production:        {}".format(testreader.daily_production()))
    print("daily_consumption:       {}".format(testreader.daily_consumption()))
    print("seven_days_production:   {}".format(testreader.seven_days_production()))
    print("seven_days_consumption:  {}".format(testreader.seven_days_consumption()))
    print("lifetime_production:     {}".format(testreader.lifetime_production()))
    print("lifetime_consumption:    {}".format(testreader.lifetime_consumption()))
