"""DataUpdateCoordinator for nissan_carwings."""

from __future__ import annotations

from datetime import timedelta
from datetime import datetime
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo
from pytz import UTC

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pycarwings3.responses import CarwingsLatestClimateControlStatusResponse

from .api import (
    NissanCarwingsApiClientAuthenticationError,
    NissanCarwingsApiClientError,
    NissanCarwingsApiUpdateTimeoutError,
)
from .const import (
    DATA_BATTERY_STATUS_KEY,
    DATA_CLIMATE_STATUS_KEY,
    DATA_DRIVING_ANALYSIS_KEY,
    DATA_TIMESTAMP_KEY,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL_CHARGING,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    LOGGER,
    OPTIONS_POLL_INTERVAL,
    OPTIONS_POLL_INTERVAL_CHARGING,
    OPTIONS_UPDATE_INTERVAL,
    POLL_INTERVAL_WHEN_FAILED,
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

    # we will store the timestamp of the last failed attempt to update the data
    last_failed_attempt_timestamp: datetime | None = None

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            # check if we need to perform a poll
            interval = timedelta(
                seconds=self.config_entry.options.get(OPTIONS_POLL_INTERVAL_CHARGING, DEFAULT_POLL_INTERVAL_CHARGING)
                if self.is_charging
                else self.config_entry.options.get(OPTIONS_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
            )

            interval_when_failed = timedelta(seconds=POLL_INTERVAL_WHEN_FAILED)
            if (
                self.latest_update_timestamp is not None
                and interval.seconds > 0
                and (
                    self.last_failed_attempt_timestamp is None
                    and datetime.now(UTC) - self.latest_update_timestamp > interval
                    or self.last_failed_attempt_timestamp is not None
                    and datetime.now(UTC) - self.last_failed_attempt_timestamp > interval_when_failed
                )
            ):
                local_timestamp = self.latest_update_timestamp.astimezone(tz=ZoneInfo(self.hass.config.time_zone))
                LOGGER.info(
                    f"Polling for new battery_status data; old_timestamp={local_timestamp}, interval={interval} (is_charging={self.is_charging})"
                )
                await self.config_entry.runtime_data.client.async_update_data()
                self.last_failed_attempt_timestamp = None

            battery_status = await self.config_entry.runtime_data.client.async_get_data()

            return {
                DATA_BATTERY_STATUS_KEY: battery_status,
                DATA_TIMESTAMP_KEY: battery_status.timestamp if battery_status else None,
            }

        except NissanCarwingsApiUpdateTimeoutError as exception:
            self.last_failed_attempt_timestamp = datetime.now(UTC)
            raise UpdateFailed(exception) from exception
        except NissanCarwingsApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except NissanCarwingsApiClientError as exception:
            raise UpdateFailed(exception) from exception

    @property
    def is_charging(self) -> bool:
        """Return the current state of the battery charging."""
        if self.data is None:
            return False
        battery_status = self.data.get(DATA_BATTERY_STATUS_KEY)
        return battery_status.is_charging if battery_status is not None else False

    @property
    def latest_update_timestamp(self) -> datetime | None:
        """Return the timestamp of the latest update."""
        if self.data is None:
            return None
        return self.data.get(DATA_TIMESTAMP_KEY)


class CarwingsClimateDataUpdateCoordinator(CarwingsBaseDataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            climate_status = await self.config_entry.runtime_data.client.async_get_climate_data()
            if climate_status:
                # check if the pending state is still in effect
                if not self.is_climate_pending_state_active:
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

    def set_climate_pending_state(self, pending_state: bool) -> None:
        """Set the climate pending state."""
        self.config_entry.runtime_data.climate_pending_state.pending_state = pending_state
        self.update_interval = timedelta(seconds=UPDATE_INTERVAL_WHILE_AWAITING_UPDATE)

        # hack to reset the current update schedule (else the modified update_interval will not be applied)
        if self.data is not None:
            self.async_set_updated_data(self.data)

    @property
    def is_hvac_running(self) -> bool:
        """Return the current state of the climate control."""

        climate_status: CarwingsLatestClimateControlStatusResponse | None = self.data.get(DATA_CLIMATE_STATUS_KEY)
        climate_pending_state = self.config_entry.runtime_data.climate_pending_state

        is_hvac_running = (
            climate_pending_state.pending_state
            if self.is_climate_pending_state_active
            else climate_status.is_hvac_running
            if climate_status is not None
            else False
        )

        # check if the maximum running time has been reached or exceeded
        if (
            is_hvac_running
            and climate_status is not None
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
            driving_analysis = await self.config_entry.runtime_data.client.async_get_driving_analysis_data()
            return {
                DATA_DRIVING_ANALYSIS_KEY: driving_analysis,
                DATA_TIMESTAMP_KEY: None,  # unfortunately there is no timestamp info in the response
            }

        except NissanCarwingsApiUpdateTimeoutError as exception:
            raise UpdateFailed(exception) from exception
        except NissanCarwingsApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except NissanCarwingsApiClientError as exception:
            raise UpdateFailed(exception) from exception
