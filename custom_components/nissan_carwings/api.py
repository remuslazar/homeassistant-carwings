"""Sample API Client."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import pycarwings3
import pycarwings3.responses

from custom_components.nissan_carwings.const import (
    DATA_BATTERY_STATUS_KEY,
    DATA_CLIMATE_STATUS_KEY,
    DATA_DRIVING_ANALYSIS_KEY,
    DATA_TIMESTAMP_KEY,
    LOGGER,
    PYCARWINGS_MAX_RESPONSE_ATTEMPTS,
    PYCARWINGS_SLEEP,
)

if TYPE_CHECKING:
    import aiohttp

# TODO: make this configurable for development
BASE_URL = "https://carwings-simulator.herokuapp.com/api/"


class NissanCarwingsApiClientError(Exception):
    """Exception to indicate a general API error."""


class NissanCarwingsApiClientCommunicationError(
    NissanCarwingsApiClientError,
):
    """Exception to indicate a communication error."""


class NissanCarwingsApiClientAuthenticationError(
    NissanCarwingsApiClientError,
):
    """Exception to indicate an authentication error."""


class NissanCarwingsApiUpdateTimeoutError(Exception):
    """Exception to indicate when an update was not successful."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise NissanCarwingsApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class NissanCarwingsApiClient:
    """Nissan Carwings API Client."""

    # pending state for the climate control:
    # None if no change is pending, True if it should be turned on
    # False if it should be turned off
    climate_control_pending_state = None

    is_update_in_progress = False

    def __init__(
        self,
        username: str,
        password: str,
        region: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Sample API Client."""
        self._username = username
        self._password = password
        self._region = region
        self._session = session
        self._carwings3 = pycarwings3.Session(username, password, region, session=session, base_url=BASE_URL)

    async def async_test_credentials(self) -> dict[str, str]:
        """
        Test the credentials.

        This method tests the credentials by attempting to connect and login
        If there is an error, it raises a NissanCarwingsApiClientError
        """
        try:
            response = await self._carwings3.connect()
            LOGGER.info(
                "Connect/Login successful: nickname=%s, VIN=%s",
                response.nickname,
                response.vin,
            )

        except pycarwings3.CarwingsError as exception:
            msg = f"Error fetching information - {exception}"
            raise NissanCarwingsApiClientError(
                msg,
            ) from exception

        else:
            return {"vin": response.vin, "nickname": response.nickname}

    async def async_update_data(self) -> Any:
        """Update data from the API."""
        self.is_update_in_progress = True
        response = await self._carwings3.get_leaf()
        LOGGER.debug("carwings3.get_leaf() OK: vin=%s", response.vin)
        result_key = await response.request_update()
        LOGGER.debug("carwings3.request_update() OK: resultKey=%s", result_key)
        for attempt in range(PYCARWINGS_MAX_RESPONSE_ATTEMPTS):
            status = await response.get_status_from_update(result_key)
            LOGGER.debug(
                "Waiting %s seconds for battery update (%s) (%s)",
                PYCARWINGS_SLEEP,
                response.vin,
                attempt,
            )
            await asyncio.sleep(PYCARWINGS_SLEEP)

            if status is not None:
                LOGGER.debug(
                    "carwings3.get_status_from_update() OK: timestamp=%s",
                    status.timestamp,
                )
                break
        else:
            LOGGER.error("carwings3.get_status_from_update() failed: vin=%s", response.vin)
            raise NissanCarwingsApiUpdateTimeoutError

        # finally
        self.is_update_in_progress = False

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        try:
            response = await self._carwings3.get_leaf()
            LOGGER.debug("carwings3.get_leaf() OK: vin=%s", response.vin)
            battery_status: (
                pycarwings3.responses.CarwingsLatestBatteryStatusResponse | None
            ) = await response.get_latest_battery_status()
            if battery_status:
                LOGGER.debug(
                    f"carwings3.get_latest_battery_status() OK: SOC={battery_status.battery_percent:.0f}%"  # noqa: E501
                )

        except pycarwings3.CarwingsError as exception:
            msg = f"Error fetching data - {exception}"
            raise NissanCarwingsApiClientError(
                msg,
            ) from exception
        else:
            return {
                DATA_BATTERY_STATUS_KEY: battery_status,
                DATA_TIMESTAMP_KEY: battery_status.timestamp if battery_status else None,
            }

    async def async_get_climate_data(self) -> Any:
        """Get data from the API."""
        try:
            response = await self._carwings3.get_leaf()
            LOGGER.debug("carwings3.get_leaf() OK: vin=%s", response.vin)
            climate_status: (
                pycarwings3.responses.CarwingsLatestClimateControlStatusResponse | None
            ) = await response.get_latest_hvac_status()
            if climate_status:
                LOGGER.debug(
                    f"carwings3.get_latest_hvac_status() OK: running={climate_status.is_hvac_running}"  # noqa: E501
                )

        except pycarwings3.CarwingsError as exception:
            msg = f"Error fetching data - {exception}"
            raise NissanCarwingsApiClientError(
                msg,
            ) from exception
        else:
            return {
                DATA_CLIMATE_STATUS_KEY: climate_status,
                DATA_TIMESTAMP_KEY: climate_status.timestamp if climate_status else None,
            }

    async def async_set_climate(self, *, switch_on: bool = True) -> Any:
        """Set climate control."""
        self.climate_control_pending_state = switch_on

        response = await self._carwings3.get_leaf()
        LOGGER.debug("carwings3.get_leaf() OK: vin=%s", response.vin)

        result_key = await response.start_climate_control() if switch_on else await response.stop_climate_control()
        LOGGER.debug("carwings3.start/stop_climate_control() OK: resultKey=%s", result_key)
        for attempt in range(PYCARWINGS_MAX_RESPONSE_ATTEMPTS):
            status = (
                await response.get_start_climate_control_result(result_key)
                if switch_on
                else await response.get_stop_climate_control_result(result_key)
            )
            LOGGER.debug(
                "Waiting %s seconds for climate status update (%s) (%s)",
                PYCARWINGS_SLEEP,
                response.vin,
                attempt,
            )
            await asyncio.sleep(PYCARWINGS_SLEEP)

            if status is not None:
                LOGGER.debug(
                    "carwings3.get_climate_status_from_update() OK: timestamp=%s",
                    status.timestamp,
                )
                break
        else:
            LOGGER.error("carwings3.get_status_from_update() failed: vin=%s", response.vin)
            raise NissanCarwingsApiUpdateTimeoutError

        self.climate_control_pending_state = None

    async def async_get_driving_analysis_data(self) -> Any:
        """Get data from the API."""
        try:
            response = await self._carwings3.get_leaf()
            LOGGER.debug("carwings3.get_leaf() OK: vin=%s", response.vin)
            driving_analysis: (
                pycarwings3.responses.CarwingsDrivingAnalysisResponse | None
            ) = await response.get_driving_analysis()
            if driving_analysis:
                LOGGER.debug(f"carwings3.get_drive_analysis() OK: {driving_analysis}")

        except pycarwings3.CarwingsError as exception:
            msg = f"Error fetching data - {exception}"
            raise NissanCarwingsApiClientError(
                msg,
            ) from exception
        else:
            return {
                DATA_DRIVING_ANALYSIS_KEY: driving_analysis,
                DATA_TIMESTAMP_KEY: None,
            }
