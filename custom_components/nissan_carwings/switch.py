"""Switch platform for nissan_carwings."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from .entity import NissanCarwingsEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import CarwingsClimateDataUpdateCoordinator
    from .data import NissanCarwingsConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: NissanCarwingsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    async_add_entities(
        [
            ClimateControlSwitch(coordinator=entry.runtime_data.climate_coordinator),
        ]
    )


class ClimateControlSwitch(NissanCarwingsEntity, SwitchEntity):
    """nissan_carwings switch class."""

    _attr_translation_key = "ac_control"
    coordinator: CarwingsClimateDataUpdateCoordinator

    def __init__(
        self,
        coordinator: CarwingsClimateDataUpdateCoordinator,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator)
        self.entity_description = SwitchEntityDescription(key="ac_control", name="AC Control")
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.is_hvac_running

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the switch."""
        client = self.coordinator.config_entry.runtime_data.client
        await client.async_set_climate(switch_on=True)
        self.coordinator.set_climate_pending_state(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the switch."""
        client = self.coordinator.config_entry.runtime_data.client
        await client.async_set_climate(switch_on=False)
        self.coordinator.set_climate_pending_state(False)
        self.async_write_ha_state()
