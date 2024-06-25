"""Adds config flow for Carwings."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_PASSWORD, CONF_REGION, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from custom_components.nissan_carwings.options_flow import OptionsFlowHandler

from .api import (
    NissanCarwingsApiClient,
    NissanCarwingsApiClientAuthenticationError,
    NissanCarwingsApiClientCommunicationError,
    NissanCarwingsApiClientError,
    TestCredentialsResponse,
)
from .const import DOMAIN, LOGGER


class CarwingsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Carwings."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                res = await self._test_credentials(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    region=user_input[CONF_REGION],
                )
            except NissanCarwingsApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except NissanCarwingsApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except NissanCarwingsApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"{res.nickname}(VIN={res.vin})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                    vol.Required(
                        CONF_REGION, description="Region"
                    ): selector.SelectSelector(
                        {
                            "options": [
                                {"value": "NE", "label": "NE (Europe)"},
                                {"value": "NNA", "label": "NNA (USA)"},
                                {"value": "NCI", "label": "NCI (Canada)"},
                                {"value": "NMA", "label": "NMA (Australia)"},
                                {"value": "NML", "label": "NML (Japan)"},
                            ]
                        }
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(
        self, username: str, password: str, region: str
    ) -> TestCredentialsResponse:
        """Validate credentials."""
        client = NissanCarwingsApiClient(
            username=username,
            password=password,
            region=region,
            session=async_create_clientsession(self.hass),
        )
        return await client.async_test_credentials()

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)
