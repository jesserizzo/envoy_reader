import requests
import sys
import json


class EnvoyReader():
    # P for prooduction data only (ie. Envoy model C)
    # PC for production and consumption data (ie. Envoy model S)
    endpoint_type = ""
    endpoint_url = ""

    message_consumption_not_available = "Consumption data not available for your Envoy device."

    def __init__(self, host):
        self.host = host.lower()

    def detect_model(self):
        self.endpoint_url = "http://{}/production.json".format(self.host)
        response = requests.get(self.endpoint_url, timeout=10, allow_redirects=False)
        if response.status_code == 200 and len(response.json()) == 3:
            self.endpoint_type = "PC"
            return
        else:
            self.endpoint_url = "http://{}/api/v1/production".format(self.host)
            response = requests.get(self.endpoint_url, timeout=10, allow_redirects=False)
            if response.status_code == 200:
                self.endpoint_type = "P"
                return

        self.endpoint_url = ""
        raise RuntimeError(
                "Could not connect or determine Envoy model. " +
                "Check that the device is up at 'http://" + self.host + "'.")
    
    def call_api(self):
        # detection of endpoint
        if self.endpoint_type == "":
            EnvoyReader.detect_model(self)

        response = requests.get(self.endpoint_url, timeout=10, allow_redirects=False)
        return response.json()

    def create_json_errormessage(self):
        return ("Unable to connect to Envoy. Check that the device is up at 'http://" + self.host + "'.")

    def create_connect_errormessage(self):
        return ("Got a response from '" + self.endpoint_url + "', but metric could not be found. " +
                "Maybe your model of Envoy doesn't support the requested metric.")

    def production(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            if self.endpoint_type == "PC":
                production = raw_json["production"][1]["wNow"]
            else:
                production = raw_json["wattsNow"]
            return int(production)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)

    def consumption(self):
        if self.endpoint_type == "P":
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
        try:
            raw_json = EnvoyReader.call_api(self)
            if self.endpoint_type == "PC":
                daily_production = raw_json["production"][1]["whToday"]
            else:
                daily_production = raw_json["wattHoursToday"]
            return int(daily_production)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)

    def daily_consumption(self):
        if self.endpoint_type == "P":
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
        try:
            raw_json = EnvoyReader.call_api(self)
            if self.endpoint_type == "PC":
                seven_days_production = raw_json["production"][1]["whLastSevenDays"]
            else:
                seven_days_production = raw_json["wattHoursSevenDays"]
            return int(seven_days_production)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)

    def seven_days_consumption(self):
        if self.endpoint_type == "P":
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
        try:
            raw_json = EnvoyReader.call_api(self)
            if self.endpoint_type == "PC":
                lifetime_production = raw_json["production"][1]["whLifetime"]
            else:
                lifetime_production = raw_json["wattHoursLifetime"]
            return int(lifetime_production)

        except requests.exceptions.ConnectionError:
            return EnvoyReader.create_connect_errormessage(self)
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return EnvoyReader.create_json_errormessage(self)

    def lifetime_consumption(self):
        if self.endpoint_type == "P":
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
