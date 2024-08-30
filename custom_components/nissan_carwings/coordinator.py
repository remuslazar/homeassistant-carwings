"""DataUpdateCoordinator for nissan_carwings."""

from __future__ import annotations

from datetime import timedelta
from datetime import datetime
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo
from pytz import UTC

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import pycarwings3
import pycarwings3.responses
from pycarwings3.responses import CarwingsLatestClimateControlStatusResponse

from .api import (
    NissanCarwingsApiClientAuthenticationError,
    NissanCarwingsApiClientError,
    NissanCarwingsApiUpdateTimeoutError,
)
from .const import (
    DATA_BATTERY_STATUS_KEY,
    DATA_CLIMATE_STATUS_KEY,
    DATA_TIMESTAMP_KEY,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL_CHARGING,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    LOGGER,
    OPTIONS_POLL_INTERVAL,
    OPTIONS_POLL_INTERVAL_CHARGING,
    OPTIONS_UPDATE_INTERVAL,
    UPDATE_INTERVAL_WHILE_AWAITING_UPDATE,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import NissanCarwingsConfigEntry


class CarwingsBaseDataUpdateCoordinator(DataUpdateCoordinator):
    """Base class to manage fetching data from the API."""

    config_entry: NissanCarwingsConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: NissanCarwingsConfigEntry,
        always_update: bool = True,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=config_entry.options.get(OPTIONS_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            ),
            always_update=always_update,
        )
        self.config_entry = config_entry

        LOGGER.debug(
            f"{self.__class__} initialized with update interval %s",
            self.update_interval,
        )


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class CarwingsDataUpdateCoordinator(CarwingsBaseDataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    # timestamp of the last successful poll
    battery_status_timestamp: datetime | None = None
    is_charging: bool = False

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            # check if we need to perform a poll
            interval = timedelta(
                seconds=self.config_entry.options.get(OPTIONS_POLL_INTERVAL_CHARGING, DEFAULT_POLL_INTERVAL_CHARGING)
                if self.is_charging
                else self.config_entry.options.get(OPTIONS_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
            )
            if (
                self.battery_status_timestamp is not None
                and interval.seconds > 0
                and (datetime.now(UTC) - self.battery_status_timestamp) > interval
            ):
                local_timestamp = self.battery_status_timestamp.astimezone(tz=ZoneInfo(self.hass.config.time_zone))
                LOGGER.info(
                    f"Polling for new battery_status data; old_timestamp={local_timestamp}, interval={interval} (is_charging={self.is_charging})"
                )
                await self.config_entry.runtime_data.client.async_update_data()

            data = await self.config_entry.runtime_data.client.async_get_data()
            battery_status: pycarwings3.responses.CarwingsLatestBatteryStatusResponse | None = data.get(
                DATA_BATTERY_STATUS_KEY
            )

            if battery_status:
                self.is_charging = battery_status.is_charging
                self.battery_status_timestamp = battery_status.timestamp

            return data

        except NissanCarwingsApiUpdateTimeoutError as exception:
            # in this case we want to retry the update right away but wait for the next scheduled update
            self.battery_status_timestamp = None
            raise UpdateFailed(exception) from exception
        except NissanCarwingsApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except NissanCarwingsApiClientError as exception:
            raise UpdateFailed(exception) from exception


class CarwingsClimateDataUpdateCoordinator(CarwingsBaseDataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            climate_status = await self.config_entry.runtime_data.client.async_get_climate_data()
            if climate_status:
                # check if the pending state is still in effect
                if self.is_climate_pending_state_active:
                    # pending state is still in effect, we will poll more frequently
                    self.update_interval = timedelta(seconds=UPDATE_INTERVAL_WHILE_AWAITING_UPDATE)
                else:
                    # pending state is no longer in effect, we will return to the normal update interval
                    self.update_interval = timedelta(
                        seconds=self.config_entry.options.get(OPTIONS_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
                    )

            return {
                DATA_CLIMATE_STATUS_KEY: climate_status,
                DATA_TIMESTAMP_KEY: climate_status.timestamp if climate_status else None,
            }
        except NissanCarwingsApiUpdateTimeoutError as exception:
            raise UpdateFailed(exception) from exception
        except NissanCarwingsApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except NissanCarwingsApiClientError as exception:
            raise UpdateFailed(exception) from exception

    @property
    def is_hvac_running(self) -> bool:
        """Return the current state of the climate control."""
        climate_status: CarwingsLatestClimateControlStatusResponse | None = self.data.get(DATA_CLIMATE_STATUS_KEY)
        if climate_status is None:
            return False

        climate_pending_state = self.config_entry.runtime_data.climate_pending_state

        is_hvac_running = (
            climate_pending_state.pending_state
            if self.is_climate_pending_state_active
            else climate_status.is_hvac_running
        )

        # check if the maximum running time has been reached or exceeded
        if (
            is_hvac_running
            and climate_status.ac_start_stop_date_and_time is not None
            and climate_status.ac_duration is not None
        ):
            if datetime.now(UTC) > climate_status.ac_start_stop_date_and_time + climate_status.ac_duration:
                is_hvac_running = False

        return is_hvac_running

    @property
    def is_climate_pending_state_active(self) -> bool:
        """Is the climate status in a pending state? This means, that the state has been requested but not yet confirmed by the car."""
        climate_pending_state = self.config_entry.runtime_data.climate_pending_state
        climate_status: CarwingsLatestClimateControlStatusResponse = self.data[DATA_CLIMATE_STATUS_KEY]

        return (
            climate_status is not None
            and climate_status.ac_start_stop_date_and_time is not None
            and climate_pending_state.pending_timestamp > climate_status.ac_start_stop_date_and_time
        )


class CarwingsDrivingAnalysisDataUpdateCoordinator(CarwingsBaseDataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: NissanCarwingsConfigEntry,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            always_update=False,
        )

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            return await self.config_entry.runtime_data.client.async_get_driving_analysis_data()
        except NissanCarwingsApiUpdateTimeoutError as exception:
            raise UpdateFailed(exception) from exception
        except NissanCarwingsApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except NissanCarwingsApiClientError as exception:
            raise UpdateFailed(exception) from exception
