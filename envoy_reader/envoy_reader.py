import requests
import sys
import json


class EnvoyReader():
    def __init__(self, host, envoy_model):
        self.host = host.lower()
        self.envoy_model = envoy_model.lower()

    def call_api(self):
        if self.envoy_model == "original":
            url = "http://{}/api/v1/production".format(self.host)
            response = requests.get(url, timeout=10)
        else:
            url = "http://{}/production.json".format(self.host)
            response = requests.get(url, timeout=10, allow_redirects=False)
            if response.status_code == 200:
                self.envoy_model = "s"
            elif response.status_code == 301:
                self.envoy_model = "original"
                url = "http://{}/api/v1/production".format(self.host)
                response = requests.get(url, timeout=10)
        return response.json()

    def production(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            if self.envoy_model == "s":
                production = raw_json["production"][1]["wNow"]
            else:
                production = raw_json["wattsNow"]
            return int(production)
        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address")

    def consumption(self):
        try:
            if self.envoy_model == "original":
                return "Unavailable"
            raw_json = EnvoyReader.call_api(self)
            if self.envoy_model == "s":
                consumption = raw_json["consumption"][0]["wNow"]
                return int(consumption)
            else:
                return "Unavailable"
        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address")

    def daily_production(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            if self.envoy_model == "s":
                daily_production = raw_json["production"][1]["whToday"]
            else:
                daily_production = raw_json["wattHoursToday"]
            return int(daily_production)
        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address")

    def daily_consumption(self):
        try:
            if self.envoy_model == "original":
                return "Unavailable"
            raw_json = EnvoyReader.call_api(self)
            if self.envoy_model == "s":
                daily_consumption = raw_json["consumption"][0]["whToday"]
                return int(daily_consumption)
            else:
                return "Unavailable"

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address")

    def seven_days_production(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            if self.envoy_model == "s":
                seven_days_production = raw_json["production"][1][
                    "whLastSevenDays"
                ]
            else:
                seven_days_production = raw_json["wattHoursSevenDays"]
            return int(seven_days_production)
        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address")

    def seven_days_consumption(self):
        try:
            if self.envoy_model == "original":
                return "Unavailable"
            raw_json = EnvoyReader.call_api(self)
            if self.envoy_model == "s":
                seven_days_consumption = raw_json["consumption"][0][
                    "whLastSevenDays"
                ]
                return int(seven_days_consumption)
            else:
                return "Unavailable"
        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address")

    def lifetime_production(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            if self.envoy_model == "s":
                lifetime_production = raw_json["production"][1][
                    "whLifetime"
                ]
            else:
                lifetime_production = raw_json["wattHoursLifetime"]
            return int(lifetime_production)
        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address")

    def lifetime_consumption(self):
        try:
            if self.envoy_model == "original":
                return "Unavailable"
            raw_json = EnvoyReader.call_api(self)
            if self.envoy_model == "s":
                lifetime_consumption = raw_json["consumption"][0][
                    "whLifetime"
                ]
                return int(lifetime_consumption)
            else:
                return "Unavailable"

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address")


if __name__ == "__main__":
    host = input("Enter the Envoy IP address, " +
                 "or press enter to search for it.")
    if host == "":
        host = "envoy"
    envoy_model = input("Enter the model of the Envoy " +
                        "('Original' or 'S'), or press enter.")
    if envoy_model == "":
        envoy_model = "unknown"

    print("production {}".format(EnvoyReader(host, envoy_model)
                                 .production()))
    print("consumption {}".format(EnvoyReader(host, envoy_model)
                                  .consumption()))
    print("daily_production {}".format(EnvoyReader(host, envoy_model)
                                       .daily_production()))
    print("daily_consumption {}".format(EnvoyReader(host, envoy_model)
                                        .daily_consumption()))
    print("seven_days_production {}".format(EnvoyReader(host, envoy_model)
                                            .seven_days_production()))
    print("seven_days_consumption {}".format(EnvoyReader(host, envoy_model)
                                             .seven_days_consumption()))
    print("lifetime_production {}".format(EnvoyReader(host, envoy_model)
                                          .lifetime_production()))
    print("lifetime_consumption {}".format(EnvoyReader(host, envoy_model)
                                           .lifetime_consumption()))
