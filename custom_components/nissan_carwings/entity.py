"""CarwingsEntity class."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import CarwingsDataUpdateCoordinator


class NissanCarwingsEntity(CoordinatorEntity[CarwingsDataUpdateCoordinator]):
    """CarwingsEntity class."""

    _attr_attribution = ATTRIBUTION

    # a prefix to be prepended to the unique_id of each entity
    unique_id_prefix: str

    def __init__(self, coordinator: CarwingsDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        # see https://developers.home-assistant.io/blog/2022/07/10/entity_naming/
        self.has_entity_name = True
        vin = coordinator.config_entry.data["vin"]
        nickname = coordinator.config_entry.data["nickname"]

        self.unique_id_prefix = f"{vin}"

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

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return default attributes for Nissan leaf entities."""
        return {
            "VIN": self.coordinator.config_entry.data["vin"],
        }
