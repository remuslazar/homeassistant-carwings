"""CarwingsEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import CarwingsDataUpdateCoordinator


class NissanCarwingsEntity(CoordinatorEntity[CarwingsDataUpdateCoordinator]):
    """CarwingsEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: CarwingsDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        # see https://developers.home-assistant.io/blog/2022/07/10/entity_naming/
        self.has_entity_name = True
        self._attr_unique_id = coordinator.config_entry.entry_id
        vin = coordinator.config_entry.data["vin"]
        nickname = coordinator.config_entry.data["nickname"]
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
            serial_number=vin,
            name=nickname,
        )
