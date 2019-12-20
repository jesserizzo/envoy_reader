import os

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
INPUT_PATH = os.path.join(BASE_PATH, 'inputs')
PRODUCTION_OUTPUT_PC = os.path.join(INPUT_PATH, 'production.json')
PRODUCTION_OUTPUT_P = os.path.join(INPUT_PATH, 'api_v1_production.json')
PRODUCTION_OUTPUT_1_P0 = os.path.join(INPUT_PATH, 'production_W.html')
PRODUCTION_OUTPUT_2_P0 = os.path.join(INPUT_PATH, 'production_kW.html')
INFO_OUTPUT_PC = os.path.join(INPUT_PATH, 'info.xml')
INFO_OUTPUT_P = os.path.join(INPUT_PATH, 'info_p.html')
INFO_OUTPUT_P0 = os.path.join(INPUT_PATH, 'info_p0.html')

MESSAGE_CONSUMPTION_NOT_AVAILABLE = ("Consumption data not available for your Envoy device.")