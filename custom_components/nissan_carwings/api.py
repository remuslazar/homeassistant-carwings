"""Sample API Client."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Any

import aiohttp
import async_timeout
import pycarwings3

from custom_components.nissan_carwings.const import LOGGER

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


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise NissanCarwingsApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


@dataclass
class TestCredentialsResponse:
    """Response from the test_credentials method."""

    vin: str
    nickname: str


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

    async def async_test_credentials(self) -> TestCredentialsResponse:
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
            return TestCredentialsResponse(vin=response.vin, nickname=response.nickname)

        except pycarwings3.CarwingsError as exception:
            msg = f"Error fetching information - {exception}"
            raise NissanCarwingsApiClientError(
                msg,
            ) from exception

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        return await self._api_wrapper(
            method="get",
            url="https://jsonplaceholder.typicode.com/posts/1",
        )

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
