[![Build Main](https://github.com/jesserizzo/envoy_reader/actions/workflows/build-main.yml/badge.svg)](https://github.com/jesserizzo/envoy_reader/actions/workflows/build-main.yml)
[![Latest Release](https://img.shields.io/github/v/release/jesserizzo/envoy_reader)](https://img.shields.io/github/v/release/jesserizzo/envoy_reader)

A program to read from an Enphase Envoy on the local network. Reads electricity production and consumption (if available) for the current moment, current day, the last seven days, and the lifetime of the Envoy.
Also reads production from individual inverters if supported.

Tested on the original Envoy (production data only) and the Envoy S (production and consumption data).

This reader uses a JSON endpoint on the Envoy gateway:
- Original Envoy: http://envoy/api/v1/production    (available on software level R3.9 and later)
- Envoy S: http://envoy/production.json

For older Envoy with software before R3.9, data is collected from html at http://envoy/production
