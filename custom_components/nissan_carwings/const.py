"""Constants for nissan_carwings."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "nissan_carwings"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

PYCARWINGS_SLEEP = 40
PYCARWINGS_MAX_RESPONSE_ATTEMPTS = 3
