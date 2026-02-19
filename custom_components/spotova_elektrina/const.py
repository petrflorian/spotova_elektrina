# custom_components/spotova_elektrina/const.py
"""Constants for the Spotová Elektřina integration."""
from homeassistant.const import Platform

DOMAIN = "spotova_elektrina"
DEFAULT_NAME = "Spotová Elektřina"
API_ENDPOINT_QH = "https://spotovaelektrina.cz/api/v1/price/get-prices-json-qh"
API_ENDPOINT_HOURLY = "https://spotovaelektrina.cz/api/v1/price/get-prices-json"

PLATFORMS = [Platform.SENSOR]
