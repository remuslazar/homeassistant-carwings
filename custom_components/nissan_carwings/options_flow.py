"""Config flow to configure Nissan Carwings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries

if TYPE_CHECKING:
    from homeassistant.data_entry_flow import FlowResult


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "option1",
                        default=self.config_entry.options.get("option1"),  # type: ignore  # noqa: PGH003
                    ): bool
                }
            ),
        )
