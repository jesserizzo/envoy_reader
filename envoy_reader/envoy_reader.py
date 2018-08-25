import requests
import sys
import json

envoy_model = "S"
def call_api(ip_address):
    url = "http://{}/production.json".format(ip_address)
    response = requests.get(url, timeout=5, allow_redirects=False)
    if response.status_code == 301:
        global envoy_model
        envoy_model = "Original"
        url = "http://{}/api/v1/production".format(ip_address)
        response = requests.get(url, timeout=5)
        return response.json()

    return response.json()


def production(ip_address):
    try:
        raw_json = call_api(ip_address)
        if envoy_model == "S":
            production = raw_json["production"][1]["wNow"]
        else:
            production = raw_json["wattsNow"]
        return int(production)
    except requests.exceptions.ConnectionError:
        return "Unable to connect to Envoy. Check the IP address"
    except (json.decoder.JSONDecodeError, KeyError):
        return ("Got a response, but it doesn't look right. " +
                "Check the IP address")


def consumption(ip_address):
    try:
        raw_json = call_api(ip_address)
        if envoy_model == "S":
            consumption = raw_json["consumption"][0]["wNow"]
            return int(consumption)
        else:
            return "Unavailable"
    except requests.exceptions.ConnectionError:
        return "Unable to connect to Envoy. Check the IP address"
    except (json.decoder.JSONDecodeError, KeyError):
        return ("Got a response, but it doesn't look right. " +
                "Check the IP address")


def daily_production(ip_address):
    try:
        raw_json = call_api(ip_address)
        if envoy_model == "S":
            daily_production = raw_json["production"][1]["whToday"]
        else:
            daily_production = raw_json["wattHoursToday"]
        return int(daily_production)
    except requests.exceptions.ConnectionError:
        return "Unable to connect to Envoy. Check the IP address"
    except (json.decoder.JSONDecodeError, KeyError):
        return ("Got a response, but it doesn't look right. " +
                "Check the IP address")


def daily_consumption(ip_address):
    try:
        raw_json = call_api(ip_address)
        if envoy_model == "S":
            daily_consumption = raw_json["consumption"][0]["whToday"]
            return int(daily_consumption)
        else:
            return "Unavailable"

    except requests.exceptions.ConnectionError:
        return "Unable to connect to Envoy. Check the IP address"
    except (json.decoder.JSONDecodeError, KeyError):
        return ("Got a response, but it doesn't look right. " +
                "Check the IP address")


def seven_days_production(ip_address):
    try:
        raw_json = call_api(ip_address)
        if envoy_model == "S":
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


def seven_days_consumption(ip_address):
    try:
        raw_json = call_api(ip_address)
        if envoy_model == "S":
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


def lifetime_production(ip_address):
    try:
        raw_json = call_api(ip_address)
        if envoy_model == "S":
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


def lifetime_consumption(ip_address):
    try:
        raw_json = call_api(ip_address)
        if envoy_model == "S":
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
    host = "envoy"
    print("production {}".format(production(host)))
    print("consumption {}".format(consumption(host)))
    print("daily_production {}".format(daily_production(host)))
    print("daily_consumption {}".format(daily_consumption(host)))
    print("seven_days_production {}".format(seven_days_production(host)))
    print("seven_days_consumption {}".format(seven_days_consumption(host)))
    print("lifetime_production {}".format(lifetime_production(host)))
    print("lifetime_consumption {}".format(lifetime_consumption(host)))
