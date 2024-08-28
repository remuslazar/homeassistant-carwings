"""
Custom integration to integrate nissan_carwings with Home Assistant.

For more details about this integration, please refer to
https://github.com/remuslazar/homeassistant-carwings
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD, CONF_REGION, CONF_USERNAME, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv
from homeassistant.exceptions import ServiceValidationError
import voluptuous as vol

from homeassistant.loader import async_get_loaded_integration

from custom_components.nissan_carwings.const import (
    CONF_PYCARWINGS3_BASE_URL,
    DATA_CLIMATE_STATUS_KEY,
    DATA_DRIVING_ANALYSIS_KEY,
    DATA_TIMESTAMP_KEY,
    DOMAIN,
    LOGGER,
    SERVICE_UPDATE,
)

from .api import NissanCarwingsApiClient
from .coordinator import (
    CarwingsClimateDataUpdateCoordinator,
    CarwingsDataUpdateCoordinator,
    CarwingsDrivingAnalysisDataUpdateCoordinator,
)
from .data import NissanCarwingsData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import NissanCarwingsConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
]


class NissanCarwingsError(Exception):
    """Exception to indicate a general error related to this integration."""


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: NissanCarwingsConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = CarwingsDataUpdateCoordinator(
        hass=hass,
        config_entry=entry,
    )
    climate_coordinator = CarwingsClimateDataUpdateCoordinator(
        hass=hass,
        config_entry=entry,
    )
    driving_analysis_coordinator = CarwingsDrivingAnalysisDataUpdateCoordinator(
        hass=hass,
        config_entry=entry,
    )
    entry.runtime_data = NissanCarwingsData(
        client=NissanCarwingsApiClient(
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
            region=entry.data[CONF_REGION],
            session=async_get_clientsession(hass),
            base_url=entry.data.get(CONF_PYCARWINGS3_BASE_URL),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
        climate_coordinator=climate_coordinator,
        driving_analysis_coordinator=driving_analysis_coordinator,
    )

    LOGGER.info(f"Starting Nissan Carwings integration for user={entry.data[CONF_USERNAME]}")

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    climate_coordinator.data = {DATA_CLIMATE_STATUS_KEY: None, DATA_TIMESTAMP_KEY: None}
    driving_analysis_coordinator.data = {DATA_DRIVING_ANALYSIS_KEY: None, DATA_TIMESTAMP_KEY: None}

    # synchronize data in background to speedup the startup time for this integration
    # related entities will stick in the unavailable state until the first data is fetched
    hass.loop.create_task(climate_coordinator.async_refresh())
    hass.loop.create_task(driving_analysis_coordinator.async_refresh())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    async def async_handle_update(service_call) -> None:
        """Handle service to update leaf data from Nissan servers."""
        vin = service_call.data["vin"]

        LOGGER.debug("Service call to update data for VIN=%s", vin)

        client = coordinator.config_entry.runtime_data.client
        current_vin = coordinator.config_entry.data["vin"]
        if vin != current_vin:
            raise ServiceValidationError(
                f"VIN mismatch: service call to update data for VIN={vin}, but current VIN={current_vin}"
            )

        # request the latest data from the Nissan servers
        await client.async_update_data()
        # tell the coordinator to refresh the data
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE, async_handle_update, schema=vol.Schema({vol.Required("vin"): cv.string})
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: NissanCarwingsConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: NissanCarwingsConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
