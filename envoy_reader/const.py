"""Constants for the Enphase Envoy Reader."""
feature_none = 0
feature_production = 1
feature_consumption = 2
feature_inverters = 4
feature_all_sensors_data = 7
response_info_xml = 1
response_api_v1_production = 2
response_api_v1_inverters = 3
response_json_production = 4
response_html_production = 5
INFO_XML_URL = "http://{}/info.xml"
PRODUCTION_API_URL = "http://{}/api/v1/production"
INVERTERS_API_URL = "http://{}/api/v1/production/inverters"
PRODUCTION_JSON_URL = "http://{}/production.json"
INVENTORY_JSON_URL = "http://{}/inventory.json"
PRODUCTION_HTML_URL = "http://{}/production"
PRODUCTION_REGEX = \
    r'<td>Currentl.*</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(W|kW|MW)</td>'
DAY_PRODUCTION_REGEX = \
    r'<td>Today</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>'
WEEK_PRODUCTION_REGEX = \
    r'<td>Past Week</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>'
LIFE_PRODUCTION_REGEX = \
    r'<td>Since Installation</td>\s+<td>\s*(\d+|\d+\.\d+)\s*(Wh|kWh|MWh)</td>'

message_data_not_available = "{} data not available for your Envoy device."
