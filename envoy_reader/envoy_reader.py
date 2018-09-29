import requests
import sys
import json


class EnvoyReader():
    # C for Envoy model C - S for Envoy model S
    model = ""
    url = ""

    def __init__(self, host):
        self.host = host.lower()

    def detect_model(self):
        self.url = "http://{}/production.json".format(self.host)
        response = requests.get(self.url, timeout=10, allow_redirects=False)
        if response.status_code == 200 and len(response.json()) == 3:
            self.model = "S"
        else:
            self.url = "http://{}/api/v1/production".format(self.host)
            response = requests.get(self.url, timeout=10, allow_redirects=False)
            if response.status_code == 200:
                self.model = "C"
    
    def call_api(self):
        # detection 
        if self.model == "":
            EnvoyReader.detect_model(self)

        if self.model == "S" or self.model == "C":
            return EnvoyReader.call_api_get(self)
        else:
            raise RuntimeError("Could not connect or determine Envoy model. Check the IP address '" + self.host + "'.")

    def call_api_get(self):
        response = requests.get(self.url, timeout=10, allow_redirects=False)
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
            return "Unable to connect to Envoy. Check the IP address '" + self.host + "'."
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address '" + self.host + "'.")

    def consumption(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            try:
                consumption = raw_json["consumption"][0]["wNow"]
            except (IndexError, KeyError):
                return "Unavailable"
            return int(consumption)

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address '" + self.host + "'."
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address '" + self.host + "',  or maybe your model of Envoy " +
                    "doesn't support this.")

    def daily_production(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            try:
                daily_production = raw_json["production"][1]["whToday"]
            except (KeyError, IndexError):
                daily_production = raw_json["wattHoursToday"]
            return int(daily_production)

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address '" + self.host + "'."
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address '" + self.host + "',  or maybe your model of Envoy " +
                    "doesn't support this.")

    def daily_consumption(self):
        try:
            raw_json = EnvoyReader.call_api(self)
            try:
                daily_consumption = raw_json["consumption"][0]["whToday"]
            except (KeyError, IndexError):
                return "Unavailable"
            return int(daily_consumption)

        except requests.exceptions.ConnectionError:
            return "Unable to connect to Envoy. Check the IP address '" + self.host + "'."
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address '" + self.host + "',  or maybe your model of Envoy " +
                    "doesn't support this.")

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
            return "Unable to connect to Envoy. Check the IP address '" + self.host + "'."
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address '" + self.host + "',  or maybe your model of Envoy " +
                    "doesn't support this.")

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
            return "Unable to connect to Envoy. Check the IP address '" + self.host + "'."
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address '" + self.host + "',  or maybe your model of Envoy " +
                    "doesn't support this.")

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
            return "Unable to connect to Envoy. Check the IP address '" + self.host + "'."
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address '" + self.host + "'.")

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
            return "Unable to connect to Envoy. Check the IP address '" + self.host + "'."
        except (json.decoder.JSONDecodeError, KeyError, IndexError):
            return ("Got a response, but it doesn't look right. " +
                    "Check the IP address '" + self.host + "',  or maybe your model of Envoy " +
                    "doesn't support this.")


if __name__ == "__main__":
    host = input("Enter the Envoy IP address or host name, " +
                 "or press enter to use 'envoy' as default: ")
    if host == "":
        host = "envoy"

    testreader = EnvoyReader(host)
    print("production {}".format(testreader.production()))
    print("consumption {}".format(testreader.consumption()))
    print("daily_production {}".format(testreader.daily_production()))
    print("daily_consumption {}".format(testreader.daily_consumption()))
    print("seven_days_production {}".format(testreader
                                            .seven_days_production()))
    print("seven_days_consumption {}".format(testreader
                                             .seven_days_consumption()))
    print("lifetime_production {}".format(testreader
                                          .lifetime_production()))
    print("lifetime_consumption {}".format(testreader
                                           .lifetime_consumption()))
