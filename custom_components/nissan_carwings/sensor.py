"""Sensor platform for nissan_carwings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.icon import icon_for_battery_level

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
    """Set up the sensor platform."""
    async_add_entities(
        [
            BatterySensor(coordinator=entry.runtime_data.coordinator),
        ]
    )


class BatterySensor(NissanCarwingsEntity, SensorEntity):
    """Battery Sensor."""

    def __init__(self, coordinator: CarwingsDataUpdateCoordinator) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = SensorEntityDescription(
            key="nissan_carwings_sensor",
            name="Integration Sensor",
            device_class=SensorDeviceClass.BATTERY,
            native_unit_of_measurement=PERCENTAGE,
        )

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return round(self.coordinator.data["battery_status"].battery_percent)

    @property
    def icon(self) -> str:
        """Battery state icon handling."""
        charging = self.coordinator.data["battery_status"].charging_status
        return icon_for_battery_level(battery_level=self.state, charging=charging)
