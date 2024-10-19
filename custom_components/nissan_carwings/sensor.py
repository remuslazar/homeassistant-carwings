"""Sensor platform for nissan_carwings."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfLength
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.util.unit_conversion import DistanceConverter
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM
import pycarwings3
import pycarwings3.responses

from custom_components.nissan_carwings.const import (
    DATA_BATTERY_STATUS_KEY,
    DATA_CLIMATE_STATUS_KEY,
    DATA_DRIVING_ANALYSIS_KEY,
    DATA_TIMESTAMP_KEY,
)
from custom_components.nissan_carwings.coordinator import (
    CarwingsClimateDataUpdateCoordinator,
    CarwingsDrivingAnalysisDataUpdateCoordinator,
)

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
            DrivingAnalysisSensor(coordinator=entry.runtime_data.driving_analysis_coordinator),
            LastBatteryStatusUpdateSensor(coordinator=coordinator),
            HVACTimerSensor(coordinator=entry.runtime_data.climate_coordinator),
        ]
    )


class BatterySensor(NissanCarwingsEntity, SensorEntity):
    """Battery Sensor."""

    _attr_translation_key = "battery_soc"

    def __init__(self, coordinator: CarwingsDataUpdateCoordinator) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = SensorEntityDescription(
            key="battery_soc",
            name="Battery",
            device_class=SensorDeviceClass.BATTERY,
            native_unit_of_measurement=PERCENTAGE,
        )
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""

        if self.coordinator.data[DATA_BATTERY_STATUS_KEY] is None:
            return None

        # 0% SOC is not a valid value
        if self.coordinator.data[DATA_BATTERY_STATUS_KEY].battery_percent == 0:
            return None

        return round(self.coordinator.data[DATA_BATTERY_STATUS_KEY].battery_percent)

    @property
    def icon(self) -> str:
        """Battery state icon handling."""
        charging = (
            self.coordinator.data[DATA_BATTERY_STATUS_KEY].is_charging
            if self.coordinator.data[DATA_BATTERY_STATUS_KEY] is not None
            else None
        )
        return icon_for_battery_level(battery_level=self.state, charging=charging)


class RemainingRangeSensor(NissanCarwingsEntity, SensorEntity):
    """Remaining Range Sensor."""

    def __init__(self, coordinator: CarwingsDataUpdateCoordinator, *, is_ac_on: bool) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self._ac_on = is_ac_on
        self.entity_description = SensorEntityDescription(
            key="range_ac_on" if is_ac_on else "range_ac_off",
            name="Range (AC)" if is_ac_on else "Range",
            device_class=SensorDeviceClass.DISTANCE,
            native_unit_of_measurement=PERCENTAGE,
        )
        self._attr_translation_key = "range_ac_on" if is_ac_on else "range_ac_off"
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"
        self._attr_icon = "mdi:speedometer"

    @property
    def native_value(self) -> float | None:
        """Battery range in miles or kms."""
        data: pycarwings3.responses.CarwingsLatestBatteryStatusResponse | None = self.coordinator.data[
            DATA_BATTERY_STATUS_KEY
        ]

        if data is None:
            return None

        ret: float | None
        if self._ac_on:
            ret = data.cruising_range_ac_on_km
        else:
            ret = data.cruising_range_ac_off_km

        if ret is None:
            return None

        if self.hass.config.units is US_CUSTOMARY_SYSTEM:
            ret = DistanceConverter.convert(ret, UnitOfLength.KILOMETERS, UnitOfLength.MILES)

        return round(ret)

    @property
    def native_unit_of_measurement(self) -> str:
        """Battery range unit."""
        if self.hass.config.units is US_CUSTOMARY_SYSTEM:
            return UnitOfLength.MILES
        return UnitOfLength.KILOMETERS


class BatteryCapacitySensor(NissanCarwingsEntity, SensorEntity):
    """Current Battery Capacity Sensor."""

    _attr_translation_key = "battery_capacity"

    def __init__(self, coordinator: CarwingsDataUpdateCoordinator) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = SensorEntityDescription(
            key="battery_capacity",
            name="Battery Capacity",
            device_class=SensorDeviceClass.ENERGY_STORAGE,
            native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
            entity_registry_enabled_default=False,  # Sensor not enabled by default
        )
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""

        if self.coordinator.data[DATA_BATTERY_STATUS_KEY] is None:
            return None

        return float(self.coordinator.data[DATA_BATTERY_STATUS_KEY].battery_remaining_amount_wh)


class DrivingAnalysisSensor(NissanCarwingsEntity, SensorEntity):
    """Driving Analysis Sensor."""

    _attr_translation_key = "electric_mileage"

    def __init__(self, coordinator: CarwingsDrivingAnalysisDataUpdateCoordinator) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = SensorEntityDescription(
            key="driving_analysis",
            name="Electric Mileage",
            device_class=SensorDeviceClass.ENERGY_STORAGE,
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            icon="mdi:ev-station",
            suggested_display_precision=1,
        )
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    @property
    def native_value(self) -> float | None:
        """Return the native value of the sensor."""

        if self.coordinator.data[DATA_DRIVING_ANALYSIS_KEY] is None:
            return None

        da: pycarwings3.responses.CarwingsDrivingAnalysisResponse = self.coordinator.data[DATA_DRIVING_ANALYSIS_KEY]
        return float(da.electric_mileage)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return default attributes for Nissan leaf entities."""

        if self.coordinator.data[DATA_DRIVING_ANALYSIS_KEY] is None:
            return {
                "VIN": self.coordinator.config_entry.data["vin"],
            }

        # flatten the advice property
        try:
            driving_analysis: dict[str, Any] = self.coordinator.data[DATA_DRIVING_ANALYSIS_KEY].__dict__
            first_advice = driving_analysis["advice"][0]
            driving_analysis["advice_title"] = first_advice["title"]
            driving_analysis["advice_body"] = first_advice["body"]
            del driving_analysis["advice"]
        except (KeyError, IndexError):
            driving_analysis = self.coordinator.data[DATA_DRIVING_ANALYSIS_KEY].__dict__

        return {
            "VIN": self.coordinator.config_entry.data["vin"],
            **driving_analysis,
        }


class LastBatteryStatusUpdateSensor(NissanCarwingsEntity, SensorEntity):
    """Last Successful Battery Status Update Sensor."""

    _attr_translation_key = "last_battery_status_update"
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator: CarwingsDataUpdateCoordinator) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = SensorEntityDescription(
            key="last_update",
            name="Last Update",
            device_class=SensorDeviceClass.TIMESTAMP,
            icon="mdi:update",
        )
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    @property
    def native_value(self) -> datetime | None:
        """Return the native value of the sensor."""
        if self.coordinator.data is None:
            return None

        return self.coordinator.data.get(DATA_TIMESTAMP_KEY)


class HVACTimerSensor(NissanCarwingsEntity, SensorEntity):
    """Remaining HVAC Duration Sensor."""

    _attr_translation_key = "hvac_timer"
    coordinator: CarwingsClimateDataUpdateCoordinator

    def __init__(self, coordinator: CarwingsClimateDataUpdateCoordinator) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = SensorEntityDescription(
            key="hvac_timer",
            name="AC Timer",
            device_class=SensorDeviceClass.TIMESTAMP,
            icon="mdi:timer-outline",
        )
        self._attr_unique_id = f"{self.unique_id_prefix}_{self.entity_description.key}"

    @property
    def available(self) -> bool:
        """Sensor availability."""
        if super().available is False:
            return False
        if DATA_CLIMATE_STATUS_KEY not in self.coordinator.data:
            return False

        climate: pycarwings3.responses.CarwingsLatestClimateControlStatusResponse = self.coordinator.data[
            DATA_CLIMATE_STATUS_KEY
        ]

        return (
            climate is not None
            and self.coordinator.is_hvac_running
            and not self.coordinator.is_climate_pending_state_active
            and climate.ac_duration is not None
        )

    @property
    def native_value(self) -> datetime | None:
        """Return the native value of the sensor."""

        if self.coordinator.data[DATA_CLIMATE_STATUS_KEY] is None:
            return None

        if DATA_CLIMATE_STATUS_KEY not in self.coordinator.data:
            return None
        climate: pycarwings3.responses.CarwingsLatestClimateControlStatusResponse = self.coordinator.data[
            DATA_CLIMATE_STATUS_KEY
        ]
        if climate.ac_start_stop_date_and_time is None or climate.ac_duration is None:
            return None
        return climate.ac_start_stop_date_and_time + climate.ac_duration
