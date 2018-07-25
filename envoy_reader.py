import requests
import json


def call_api(ip_address):
    url = "http://{}/production.json".format(ip_address)
    try:
        response = requests.get(url, timeout=5)
    except (requests.exceptions.RequestException, ValueError):
        return "Could not update status for Enphase Envoy"

    return response.text


def production(ip_address):
    try:
        raw_json = call_api(ip_address)
        production = json.loads(raw_json)["production"][1]["wNow"]
        return production
    except:
        return raw_json


def consumption(ip_address):
    try:
        raw_json = call_api(ip_address)
        consumption = json.loads(raw_json)["consumption"][0]["wNow"]
        return consumption
    except:
        return raw_json


def daily_production(ip_address):
    try:
        raw_json = call_api(ip_address)
        daily_production = json.loads(raw_json)["production"][1]["whToday"]
        return daily_production
    except:
        return raw_json


def daily_consumption(ip_address):
    try:
        raw_json = call_api(ip_address)
        daily_consumption = json.loads(raw_json)["consumption"][0]["whToday"]
        return daily_consumption
    except:
        return raw_json


def seven_days_production(ip_address):
    try:
        raw_json = call_api(ip_address)
        seven_days_production = json.loads(raw_json)["production"][1][
            "whLastSevenDays"
        ]
        return seven_days_production
    except:
        return raw_json


def seven_days_consumption(ip_address):
    try:
        raw_json = call_api(ip_address)
        seven_days_consumption = json.loads(raw_json)["consumption"][0][
            "whLastSevenDays"
        ]
        return seven_days_consumption
    except:
        return raw_json


def lifetime_production(ip_address):
    try:
        raw_json = call_api(ip_address)
        lifetime_production = json.loads(raw_json)["production"][1][
            "whLifetime"
        ]
        return lifetime_production
    except:
        return raw_json


def lifetime_consumption(ip_address):
    try:
        raw_json = call_api(ip_address)
        lifetime_consumption = json.loads(raw_json)["consumption"][0][
            "whLifetime"
        ]
        return lifetime_consumption
    except:
        return raw_json


print(seven_days_consumption("192.168.1.6"))
