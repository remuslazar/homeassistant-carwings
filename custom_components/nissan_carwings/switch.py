"""Switch platform for nissan_carwings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

from custom_components.nissan_carwings.const import DATA_CLIMATE_STATUS_KEY

from .entity import NissanCarwingsEntity

if TYPE_CHECKING:
    import pycarwings3.responses
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
        client = self.coordinator.config_entry.runtime_data.client
        # respect the pending state
        if client.climate_control_pending_state is not None:
            return client.climate_control_pending_state

        data: pycarwings3.responses.CarwingsLatestClimateControlStatusResponse = self.coordinator.data[
            DATA_CLIMATE_STATUS_KEY
        ]
        return data.is_hvac_running

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the switch."""
        client = self.coordinator.config_entry.runtime_data.client
        client.climate_control_pending_state = True
        await self.async_update_ha_state()
        await client.async_set_climate(switch_on=True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the switch."""
        client = self.coordinator.config_entry.runtime_data.client
        client.climate_control_pending_state = False
        await self.async_update_ha_state()
        await client.async_set_climate(switch_on=False)
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Switch availability."""
        if super().available is False:
            return False

        return self.coordinator.config_entry.runtime_data.client.climate_control_pending_state is None
