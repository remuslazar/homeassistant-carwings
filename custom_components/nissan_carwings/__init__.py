"""
Custom integration to integrate nissan_carwings with Home Assistant.

For more details about this integration, please refer to
https://github.com/remuslazar/homeassistant-carwings
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_PASSWORD, CONF_REGION, CONF_USERNAME, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import ServiceValidationError, HomeAssistantError
from homeassistant.loader import async_get_loaded_integration

from custom_components.nissan_carwings.const import (
    CONF_PYCARWINGS3_BASE_URL,
    DATA_CLIMATE_STATUS_KEY,
    DATA_DRIVING_ANALYSIS_KEY,
    DATA_TIMESTAMP_KEY,
    DOMAIN,
    LOGGER,
    SERVICE_UPDATE,
    SERVICE_START_CLIMATE,
    SERVICE_STOP_CLIMATE,
    SERVICE_START_CHARGING,
)

from .api import NissanCarwingsApiClient
from .coordinator import (
    CarwingsClimateDataUpdateCoordinator,
    CarwingsDataUpdateCoordinator,
    CarwingsDrivingAnalysisDataUpdateCoordinator,
)
from .data import NissanCarwingsClimatePendingState, NissanCarwingsData

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
        climate_pending_state=NissanCarwingsClimatePendingState(),
        driving_analysis_coordinator=driving_analysis_coordinator,
    )

    LOGGER.info(
        f"Starting Nissan Carwings integration for user={entry.data[CONF_USERNAME]}"
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    climate_coordinator.data = {DATA_CLIMATE_STATUS_KEY: None, DATA_TIMESTAMP_KEY: None}
    driving_analysis_coordinator.data = {
        DATA_DRIVING_ANALYSIS_KEY: None,
        DATA_TIMESTAMP_KEY: None,
    }

    # synchronize data in background to speedup the startup time for this integration
    # related entities will stick in the unavailable state until the first data is fetched
    hass.loop.create_task(climate_coordinator.async_refresh())
    hass.loop.create_task(driving_analysis_coordinator.async_refresh())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await register_services(hass, entry)

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


async def register_services(hass: HomeAssistant, entry: NissanCarwingsConfigEntry):
    """Register services for Nissan Carwings."""

    def validate_vin(service_call, current_vin, service_name):
        """Validate that the VIN in the service call matches the current VIN."""
        vin = service_call.data.get("vin")
        if vin and vin != current_vin:
            raise ServiceValidationError(
                f"VIN mismatch: service call to {service_name} for VIN={vin}, but current VIN={current_vin}"
            )
        return True

    async def async_handle_update(service_call):
        """Handle service to update leaf data from Nissan servers."""
        client = entry.runtime_data.client
        coordinator = entry.runtime_data.coordinator
        current_vin = entry.data["vin"]
        validate_vin(service_call, current_vin, "update")
        LOGGER.debug("Service call to update data for VIN=%s", current_vin)
        # request the latest data from the Nissan servers
        await client.async_update_data()
        # tell the coordinator to refresh the data
        await coordinator.async_request_refresh()

    async def start_climate_service(service_call):
        """Handle starting the climate system."""
        client = entry.runtime_data.client
        current_vin = entry.data["vin"]
        validate_vin(service_call, current_vin, "start climate")
        LOGGER.debug("Service call to start climate for VIN=%s", current_vin)
        await client.async_set_climate(switch_on=True)
        entry.runtime_data.climate_coordinator.set_climate_pending_state(True)

    async def stop_climate_service(service_call):
        """Handle stopping the climate system."""
        client = entry.runtime_data.client
        current_vin = entry.data["vin"]
        validate_vin(service_call, current_vin, "stop climate")
        LOGGER.debug("Service call to stop climate for VIN=%s", current_vin)
        await client.async_set_climate(switch_on=False)
        entry.runtime_data.climate_coordinator.set_climate_pending_state(False)

    async def start_charging(service_call):
        """Handle starting charging."""
        client = entry.runtime_data.client
        current_vin = entry.data["vin"]
        validate_vin(service_call, current_vin, "start charging")
        LOGGER.debug("Service call to start charging for VIN=%s", current_vin)
        try:
            result = await client.async_start_charging()
            if not result:
                raise HomeAssistantError("Failed to start charging")
        except Exception as exception:
            raise HomeAssistantError(f"Error starting charging: {exception}")

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE,
        async_handle_update,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_CLIMATE,
        start_climate_service,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_CLIMATE,
        stop_climate_service,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_CHARGING,
        start_charging,
    )
