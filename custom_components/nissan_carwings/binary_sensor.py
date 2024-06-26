"""Binary sensor platform for nissan_carwings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from custom_components.nissan_carwings.const import DATA_BATTERY_STATUS_KEY

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
    """Set up the binary_sensor platform."""
    async_add_entities(
        [
            LeafPluggedInSensor(coordinator=entry.runtime_data.coordinator),
            LeafChargingSensor(coordinator=entry.runtime_data.coordinator),
        ]
    )


class LeafPluggedInSensor(NissanCarwingsEntity, BinarySensorEntity):
    """Plugged In Sensor class."""

    def __init__(self, coordinator: CarwingsDataUpdateCoordinator) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = BinarySensorEntityDescription(
            key="plug_status",
            name="Plug Status",
            device_class=BinarySensorDeviceClass.PLUG,
        )
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    @property
    def available(self) -> bool:
        """Sensor availability."""
        return self.coordinator.data[DATA_BATTERY_STATUS_KEY].is_connected is not None

    @property
    def is_on(self) -> bool:
        """Return true if plugged in."""
        return bool(self.coordinator.data[DATA_BATTERY_STATUS_KEY].is_connected)


class LeafChargingSensor(NissanCarwingsEntity, BinarySensorEntity):
    """Charging Sensor class."""

    def __init__(self, coordinator: CarwingsDataUpdateCoordinator) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = BinarySensorEntityDescription(
            key="charging_status",
            name="Charging",
            device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        )
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    @property
    def available(self) -> bool:
        """Sensor availability."""
        return self.coordinator.data[DATA_BATTERY_STATUS_KEY].is_charging is not None

    @property
    def is_on(self) -> bool:
        """Return true if charging."""
        return bool(self.coordinator.data[DATA_BATTERY_STATUS_KEY].is_charging)
