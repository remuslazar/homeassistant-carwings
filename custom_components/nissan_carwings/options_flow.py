"""Config flow to configure Nissan Carwings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

from custom_components.nissan_carwings.const import (
    DEFAULT_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL_CHARGING,
    DEFAULT_UPDATE_INTERVAL,
    OPTIONS_POLL_INTERVAL,
    OPTIONS_POLL_INTERVAL_CHARGING,
    OPTIONS_UPDATE_INTERVAL,
)

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        OPTIONS_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(OPTIONS_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                    ): cv.positive_int,
                    vol.Required(
                        OPTIONS_POLL_INTERVAL,
                        default=self.config_entry.options.get(OPTIONS_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
                    ): cv.positive_int,
                    vol.Required(
                        OPTIONS_POLL_INTERVAL_CHARGING,
                        default=self.config_entry.options.get(
                            OPTIONS_POLL_INTERVAL_CHARGING, DEFAULT_POLL_INTERVAL_CHARGING
                        ),
                    ): cv.positive_int,
                }
            ),
        )
