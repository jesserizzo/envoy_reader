import requests
import sys
import json


class EnvoyReader():
    def __init__(self, host):
        self.host = host.lower()

    def call_api(self):
        url = "http://{}/production.json".format(self.host)
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and len(response.json()) == 3:
            return response.json()
        else:
            url = "http://{}/api/v1/production".format(self.host)
            response = requests.get(url, timeout=10, allow_redirects=False)
            return response.json()

    def production(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            try:
                production = raw_json["production"][1]["wNow"]
            except (IndexError, KeyError):
                production = raw_json["wattsNow"]
            return int(production)

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address")

    def consumption(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            try:
                consumption = raw_json["consumption"][0]["wNow"]
            except (IndexError, KeyError):
                return "Unavailable"
            return int(consumption)

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address, or maybe your model of Envoy " +
                    "doesn't support this")

    def daily_production(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            try:
                daily_production = raw_json["production"][1]["whToday"]
            except (KeyError, IndexError):
                daily_production = raw_json["wattHoursToday"]
            return int(daily_production)

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address, or maybe your model of Envoy " +
                    "doesn't support this")

    def daily_consumption(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            try:
                daily_consumption = raw_json["consumption"][0]["whToday"]
            except (KeyError, IndexError):
                return "Unavailable"
            return int(daily_consumption)

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address, or maybe your model of Envoy " +
                    "doesn't support this")

    def seven_days_production(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            try:
                seven_days_production = raw_json["production"][1][
                    "whLastSevenDays"
                ]
            except (KeyError, IndexError):
                seven_days_production = raw_json["wattHoursSevenDays"]
            return int(seven_days_production)

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address, or maybe your model of Envoy " +
                    "doesn't support this")

    def seven_days_consumption(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            try:
                seven_days_consumption = raw_json["consumption"][0][
                    "whLastSevenDays"
                ]
            except (KeyError, IndexError):
                return "Unavailable"
            return int(seven_days_consumption)

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address, or maybe your model of Envoy " +
                    "doesn't support this")

    def lifetime_production(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            try:
                lifetime_production = raw_json["production"][1][
                    "whLifetime"
                ]
            except (KeyError, IndexError):
                lifetime_production = raw_json["wattHoursLifetime"]
            return int(lifetime_production)

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address")

    def lifetime_consumption(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            try:
                lifetime_consumption = raw_json["consumption"][0][
                    "whLifetime"
                ]
            except (KeyError, IndexError):
                return "Unavailable"
            return int(lifetime_consumption)

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address"
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address, or maybe your model of Envoy " +
                    "doesn't support this")


if __name__ == "__main__":
    host = input("Enter the Envoy IP address, " +
                 "or press enter to search for it.")
    if host == "":
        host = "envoy"

    print("production {}".format(EnvoyReader(host).production()))
    print("consumption {}".format(EnvoyReader(host).consumption()))
    print("daily_production {}".format(EnvoyReader(host).daily_production()))
    print("daily_consumption {}".format(EnvoyReader(host).daily_consumption()))
    print("seven_days_production {}".format(EnvoyReader(host)
                                            .seven_days_production()))
    print("seven_days_consumption {}".format(EnvoyReader(host)
                                             .seven_days_consumption()))
    print("lifetime_production {}".format(EnvoyReader(host)
                                          .lifetime_production()))
    print("lifetime_consumption {}".format(EnvoyReader(host)
                                           .lifetime_consumption()))
