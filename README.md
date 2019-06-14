A program to read from an Enphase Envoy on the local network. Reads electricity production and consumption (if available) for the current moment, current day, the last seven days, and the lifetime of the Envoy.
Also reads production from individual inverters if supported.

Tested on the original Envoy (production data only) and the Envoy S (production and consumption data).

This reader uses a JSON endpoint on the Envoy gateway:

- Original Envoy: http://envoy/api/v1/production
- Envoy S: http://envoy/production.json
