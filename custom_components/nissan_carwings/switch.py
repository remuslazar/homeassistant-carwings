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
            ClimateControlSwitch(coordinator=entry.runtime_data.coordinator),
        ]
    )


class ClimateControlSwitch(NissanCarwingsEntity, SwitchEntity):
    """nissan_carwings switch class."""

    def __init__(
        self,
        coordinator: CarwingsDataUpdateCoordinator,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator)
        self.entity_description = SwitchEntityDescription(
            key="ac_control", name="AC Control"
        )
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        data: pycarwings3.responses.CarwingsLatestClimateControlStatusResponse = (
            self.coordinator.data[DATA_CLIMATE_STATUS_KEY]
        )
        return data.is_hvac_running

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the switch."""
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the switch."""
        await self.coordinator.async_request_refresh()
