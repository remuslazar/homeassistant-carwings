"""Sample API Client."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from typing import Any

import aiohttp
import async_timeout
import pycarwings3

from custom_components.nissan_carwings.const import (
    LOGGER,
    PYCARWINGS_MAX_RESPONSE_ATTEMPTS,
    PYCARWINGS_SLEEP,
)

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
        self._carwings3 = pycarwings3.Session(
            username, password, region, session=session, base_url=BASE_URL
        )

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
            LOGGER.error(
                "carwings3.get_status_from_update() failed: vin=%s", response.vin
            )
            raise NissanCarwingsApiUpdateTimeoutError

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        try:
            response = await self._carwings3.get_leaf()
            LOGGER.debug("carwings3.get_leaf() OK: vin=%s", response.vin)
            battery_status = await response.get_latest_battery_status()
            LOGGER.debug(
                f"carwings3.get_latest_battery_status() OK: SOC={battery_status.battery_percent:.0f}%",  # noqa: E501 , PGH003# type: ignore
            )

        except pycarwings3.CarwingsError as exception:
            msg = f"Error fetching data - {exception}"
            raise NissanCarwingsApiClientError(
                msg,
            ) from exception
        else:
            return {"battery_status": battery_status}

    async def async_set_title(self, value: str) -> Any:
        """Get data from the API."""
        return await self._api_wrapper(
            method="patch",
            url="https://jsonplaceholder.typicode.com/posts/1",
            data={"title": value},
            headers={"Content-type": "application/json; charset=UTF-8"},
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise NissanCarwingsApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise NissanCarwingsApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise NissanCarwingsApiClientError(
                msg,
            ) from exception
