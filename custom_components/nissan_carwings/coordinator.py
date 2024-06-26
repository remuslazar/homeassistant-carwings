"""DataUpdateCoordinator for nissan_carwings."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    NissanCarwingsApiClientAuthenticationError,
    NissanCarwingsApiClientError,
    NissanCarwingsApiUpdateTimeoutError,
)
from .const import DOMAIN, LOGGER, OPTIONS_UPDATE_INTERVAL

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import NissanCarwingsConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class CarwingsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: NissanCarwingsConfigEntry
    request_update = False

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: NissanCarwingsConfigEntry,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=config_entry.options.get(OPTIONS_UPDATE_INTERVAL, 300)
            ),
        )
        self.config_entry = config_entry
        LOGGER.debug(
            "CarwingsDataUpdateCoordinator initialized with update interval %s",
            self.update_interval,
        )

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            # request an update if the user has requested it (and wait for it to complete)  # noqa: E501
            if self.request_update:
                self.request_update = False
                await self.config_entry.runtime_data.client.async_update_data()

            return await self.config_entry.runtime_data.client.async_get_data()
        except NissanCarwingsApiUpdateTimeoutError as exception:
            raise UpdateFailed(exception) from exception
        except NissanCarwingsApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except NissanCarwingsApiClientError as exception:
            raise UpdateFailed(exception) from exception
