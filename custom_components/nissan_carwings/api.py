"""Sample API Client."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from pycarwings3.responses import (
    CarwingsLatestClimateControlStatusResponse,
    CarwingsLatestBatteryStatusResponse,
    CarwingsDrivingAnalysisResponse,
)
from pycarwings3 import Session, CarwingsError

from .const import (
    LOGGER,
    PYCARWINGS_MAX_RESPONSE_ATTEMPTS,
    PYCARWINGS_SLEEP,
)

if TYPE_CHECKING:
    import aiohttp


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

    is_update_in_progress = False
    update_semaphore = asyncio.Semaphore(1)

    def __init__(
        self,
        username: str,
        password: str,
        region: str,
        session: aiohttp.ClientSession,
        base_url: str | None,
    ) -> None:
        """Sample API Client."""
        self._username = username
        self._password = password
        self._region = region
        self._session = session

        if base_url:
            # use the custom base_url the user has provided via
            self._carwings3 = Session(
                username,
                password,
                region,
                session=session,
                base_url=base_url,
            )
        else:
            self._carwings3 = Session(username, password, region, session=session)

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

        except CarwingsError as exception:
            msg = f"Error fetching information - {exception}"
            if str(exception) == "INVALID PARAMS":
                LOGGER.error("Login failed: username=%s, region=%s", self._username, self._region)
                raise NissanCarwingsApiClientAuthenticationError(
                    msg,
                ) from exception

            # default
            raise NissanCarwingsApiClientError(
                msg,
            ) from exception

        else:
            return {"vin": response.vin, "nickname": response.nickname}

    async def async_update_data(self):
        """Update data from the API."""

        # prevent concurrent updates
        if self.update_semaphore.locked():
            LOGGER.warning("async_update_data(): previous update is currently in progress, waiting for it to finish.")
            return_after_release = True
        else:
            return_after_release = False

        async with self.update_semaphore:
            if return_after_release:
                return
            self.is_update_in_progress = True

            try:
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
                    LOGGER.warn(
                        f"carwings3.request_update() => Timeout after {PYCARWINGS_MAX_RESPONSE_ATTEMPTS} attempts x {PYCARWINGS_SLEEP}s; vin={response.vin}"
                    )
                    raise NissanCarwingsApiUpdateTimeoutError
            except NissanCarwingsApiUpdateTimeoutError:
                raise
            except Exception as exception:
                raise NissanCarwingsApiClientError from exception

            finally:
                self.is_update_in_progress = False

    async def async_get_data(self) -> CarwingsLatestBatteryStatusResponse | None:
        """Get data from the API."""
        try:
            response = await self._carwings3.get_leaf()
            LOGGER.debug("carwings3.get_leaf() OK: vin=%s", response.vin)
            battery_status: CarwingsLatestBatteryStatusResponse | None = await response.get_latest_battery_status()
            if battery_status:
                LOGGER.debug(
                    f"carwings3.get_latest_battery_status() OK: SOC={battery_status.battery_percent:.0f}%, timestamp={battery_status.timestamp}"  # noqa: E501
                )

        except Exception as exception:
            msg = f"Error fetching battery status - {exception.__class__.__name__}: {exception}"
            LOGGER.error(msg)
            raise NissanCarwingsApiClientError(
                msg,
            ) from exception
        else:
            return battery_status

    async def async_get_climate_data(self) -> CarwingsLatestClimateControlStatusResponse | None:
        """Get data from the API."""
        try:
            response = await self._carwings3.get_leaf()
            LOGGER.debug("carwings3.get_leaf() OK: vin=%s", response.vin)
            climate_status: CarwingsLatestClimateControlStatusResponse | None = await response.get_latest_hvac_status()
            if climate_status:
                LOGGER.debug(
                    f"carwings3.get_latest_hvac_status() OK: running={climate_status.is_hvac_running}, remaining_time={climate_status.ac_duration}, start/stop timestamp: {climate_status.ac_start_stop_date_and_time}"  # noqa: E501
                )

        except Exception as exception:
            msg = f"Error fetching climate data - {exception.__class__.__name__}: {exception}"
            LOGGER.error(msg)
            raise NissanCarwingsApiClientError(
                msg,
            ) from exception
        else:
            return climate_status

    async def async_set_climate(self, *, switch_on: bool = True) -> Any:
        """Set climate control."""

        try:
            response = await self._carwings3.get_leaf()
            LOGGER.debug("carwings3.get_leaf() OK: vin=%s", response.vin)

            result_key = await response.start_climate_control() if switch_on else await response.stop_climate_control()
            LOGGER.debug(f"carwings3.{'start' if switch_on else 'stop'}_climate_control() OK: resultKey={result_key}")
        except CarwingsError as exception:
            LOGGER.error("Error setting climate control - %s", exception)

    async def async_get_driving_analysis_data(self) -> CarwingsDrivingAnalysisResponse | None:
        """Get data from the API."""
        try:
            response = await self._carwings3.get_leaf()
            LOGGER.debug("carwings3.get_leaf() OK: vin=%s", response.vin)
            driving_analysis: CarwingsDrivingAnalysisResponse | None = await response.get_driving_analysis()
            if driving_analysis:
                LOGGER.debug(
                    f"carwings3.get_drive_analysis() OK; target_date={driving_analysis.target_date}, mileage={driving_analysis.electric_mileage}"
                )

        except Exception as exception:
            msg = f"Error fetching driving analysis data - {exception.__class__.__name__}: {exception}"
            LOGGER.error(msg)
            raise NissanCarwingsApiClientError(
                msg,
            ) from exception
        else:
            return driving_analysis

    async def async_start_charging(self) -> bool:
        """Start charging."""
        response = await self._carwings3.get_leaf()
        result = await response.start_charging()
        LOGGER.debug("carwings3.start_charging(): result=%s", result)
        return result
