"""Button platform for nissan_carwings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.exceptions import HomeAssistantError

from custom_components.nissan_carwings.const import LOGGER

from .entity import NissanCarwingsEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import CarwingsDataUpdateCoordinator
    from .data import NissanCarwingsConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: NissanCarwingsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    async_add_entities(
        [
            UpdateButton(coordinator=entry.runtime_data.coordinator),
            StartChargingButton(coordinator=entry.runtime_data.coordinator),
        ]
    )


class UpdateButton(NissanCarwingsEntity, ButtonEntity):
    """nissan_carwings switch class."""

    _attr_translation_key = "request_update"

    def __init__(
        self,
        coordinator: CarwingsDataUpdateCoordinator,
    ) -> None:
        """Initialize the button class."""
        super().__init__(coordinator)
        self.entity_description = ButtonEntityDescription(key="request_update", name="Request Update")
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    async def async_press(self) -> None:
        """Handle the button press."""
        client = self.coordinator.config_entry.runtime_data.client
        if not client.is_update_in_progress:
            client.is_update_in_progress = True
            self.async_write_ha_state()
            try:
                await client.async_update_data()
            except Exception as exception:
                LOGGER.error("Error performing update via update button: %s", exception)
            await self.coordinator.async_request_refresh()
        else:
            LOGGER.warning(
                "Update was triggered via async_press() but there is already an update in progress."  # noqa: E501
            )

    @property
    def available(self) -> bool:
        """Button availability."""
        return not self.coordinator.config_entry.runtime_data.client.is_update_in_progress


class StartChargingButton(NissanCarwingsEntity, ButtonEntity):
    _attr_translation_key = "start_charging"

    def __init__(
        self,
        coordinator: CarwingsDataUpdateCoordinator,
    ) -> None:
        """Initialize the button class."""
        super().__init__(coordinator)
        self.entity_description = ButtonEntityDescription(key="start_charging", name="Start Charging")
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    async def async_press(self) -> None:
        """Handle the button press."""
        client = self.coordinator.config_entry.runtime_data.client
        try:
            result = await client.async_start_charging()
            if not result:
                raise HomeAssistantError("Failed to start charging")
        except Exception as exception:
            raise HomeAssistantError(f"Error starting charging: {exception}")
