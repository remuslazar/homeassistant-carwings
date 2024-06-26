"""Sensor platform for nissan_carwings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfLength
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.util.unit_conversion import DistanceConverter
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM

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
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            BatterySensor(coordinator=coordinator),
            RemainingRangeSensor(coordinator=coordinator, is_ac_on=True),
            RemainingRangeSensor(coordinator=coordinator, is_ac_on=False),
            BatteryCapacitySensor(coordinator=coordinator),
        ]
    )


class BatterySensor(NissanCarwingsEntity, SensorEntity):
    """Battery Sensor."""

    def __init__(self, coordinator: CarwingsDataUpdateCoordinator) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = SensorEntityDescription(
            key="battery_soc",
            name="Battery SOC",
            device_class=SensorDeviceClass.BATTERY,
            native_unit_of_measurement=PERCENTAGE,
        )
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return round(self.coordinator.data[DATA_BATTERY_STATUS_KEY].battery_percent)

    @property
    def icon(self) -> str:
        """Battery state icon handling."""
        charging = self.coordinator.data[DATA_BATTERY_STATUS_KEY].is_charging
        return icon_for_battery_level(battery_level=self.state, charging=charging)

    @property
    def available(self) -> bool:
        """Sensor availability."""
        return (
            self.coordinator.data[DATA_BATTERY_STATUS_KEY].battery_percent is not None
        )


class RemainingRangeSensor(NissanCarwingsEntity, SensorEntity):
    """Remaining Range Sensor."""

    def __init__(
        self, coordinator: CarwingsDataUpdateCoordinator, *, is_ac_on: bool
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self._ac_on = is_ac_on
        self.entity_description = SensorEntityDescription(
            key="range_ac_on" if is_ac_on else "range_ac_off",
            name="Remaining Range (AC)" if is_ac_on else "Remaining Range",
            device_class=SensorDeviceClass.DISTANCE,
            native_unit_of_measurement=PERCENTAGE,
        )
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"
        self._attr_icon = "mdi:speedometer"

    @property
    def native_value(self) -> float | None:
        """Battery range in miles or kms."""
        ret: float | None
        if self._ac_on:
            ret = self.coordinator.data[DATA_BATTERY_STATUS_KEY].cruising_range_ac_on_km
        else:
            ret = self.coordinator.data[
                DATA_BATTERY_STATUS_KEY
            ].cruising_range_ac_off_km

        if ret is None:
            return None

        if self.hass.config.units is US_CUSTOMARY_SYSTEM:
            ret = DistanceConverter.convert(
                ret, UnitOfLength.KILOMETERS, UnitOfLength.MILES
            )

        return round(ret)

    @property
    def native_unit_of_measurement(self) -> str:
        """Battery range unit."""
        if self.hass.config.units is US_CUSTOMARY_SYSTEM:
            return UnitOfLength.MILES
        return UnitOfLength.KILOMETERS


class BatteryCapacitySensor(NissanCarwingsEntity, SensorEntity):
    """Current Battery Capacity Sensor."""

    def __init__(self, coordinator: CarwingsDataUpdateCoordinator) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = SensorEntityDescription(
            key="battery_capacity",
            name="Battery Capacity",
            device_class=SensorDeviceClass.ENERGY_STORAGE,
            native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        )
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    @property
    def available(self) -> bool:
        """Sensor availability."""
        return (
            self.coordinator.data[DATA_BATTERY_STATUS_KEY].battery_remaining_amount_wh
            is not None
        )

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""
        return float(
            self.coordinator.data[DATA_BATTERY_STATUS_KEY].battery_remaining_amount_wh
        )
