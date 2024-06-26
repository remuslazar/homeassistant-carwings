"""Custom types for nissan_carwings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from custom_components.nissan_carwings.coordinator import CarwingsDrivingAnalysisDataUpdateCoordinator

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import NissanCarwingsApiClient
    from .coordinator import (
        CarwingsClimateDataUpdateCoordinator,
        CarwingsDataUpdateCoordinator,
    )


type NissanCarwingsConfigEntry = ConfigEntry[NissanCarwingsData]


@dataclass
class NissanCarwingsData:
    """Data for the Carwings integration."""

    client: NissanCarwingsApiClient
    coordinator: CarwingsDataUpdateCoordinator
    climate_coordinator: CarwingsClimateDataUpdateCoordinator
    driving_analysis_coordinator: CarwingsDrivingAnalysisDataUpdateCoordinator
    integration: Integration
