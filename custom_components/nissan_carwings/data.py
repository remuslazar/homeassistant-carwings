"""Custom types for nissan_carwings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from datetime import datetime
from pytz import UTC

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import NissanCarwingsApiClient
    from .coordinator import (
        CarwingsClimateDataUpdateCoordinator,
        CarwingsDataUpdateCoordinator,
        CarwingsDrivingAnalysisDataUpdateCoordinator,
    )


type NissanCarwingsConfigEntry = ConfigEntry[NissanCarwingsData]


@dataclass
class NissanCarwingsData:
    """Data for the Carwings integration."""

    client: NissanCarwingsApiClient
    coordinator: CarwingsDataUpdateCoordinator
    climate_coordinator: CarwingsClimateDataUpdateCoordinator
    climate_pending_state: NissanCarwingsClimatePendingState
    driving_analysis_coordinator: CarwingsDrivingAnalysisDataUpdateCoordinator
    integration: Integration


@dataclass()
class NissanCarwingsClimatePendingState:
    """Climate Pending State."""

    # pending state for the climate control (user has switched on the climate control but the change is not yet reflected in the API)
    # None if no change is pending, True if it should be turned on, False if it should be turned off
    _pending_state: bool = False

    # pending state timestamp (when the change was requested)
    _pending_timestamp: datetime = datetime.fromtimestamp(0).replace(tzinfo=UTC)

    @property
    def pending_state(self) -> bool:
        """Get the pending state."""
        return self._pending_state

    @property
    def pending_timestamp(self) -> datetime:
        """Get the pending timestamp."""
        return self._pending_timestamp

    @pending_state.setter
    def pending_state(self, state: bool) -> None:
        """Set the pending state and update the timestamp."""
        self._pending_state = state
        self._pending_timestamp = datetime.now(UTC)
