"""The price of electricity right now, and its tranche, for automations."""

from datetime import datetime
from typing import override

from elec_tariffs import Tranche
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, FRANCE_TIME_ZONE
from .coordinator import (
    ElectricityContractsConfigEntry,
    ElectricityContractsCoordinator,
)
from .data import contracts, in_force, manual_prices, price_periods
from .outlook import tranche_at

# The coordinator does the updates.
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ElectricityContractsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors of the contract in force."""
    async_add_entities([CurrentPriceSensor(entry), CurrentTrancheSensor(entry)])


class ContractNowSensor(
    CoordinatorEntity[ElectricityContractsCoordinator], SensorEntity
):
    """What the contract in force says about this moment.

    Tranches change on the hour or the half hour, French time: the state is
    written again then, and when the prices or the Tempo colors change.
    """

    _attr_has_entity_name = True

    def __init__(self, entry: ElectricityContractsConfigEntry, key: str) -> None:
        """Belong to the entry's device."""
        super().__init__(entry.runtime_data)
        self._entry = entry
        self._attr_translation_key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            translation_key="contracts",
        )

    @override
    async def async_added_to_hass(self) -> None:
        """Follow the half hours."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_half_hour, minute=(0, 30), second=0
            )
        )

    @callback
    def _async_half_hour(self, now: datetime) -> None:
        del now
        self.async_write_ha_state()

    def _now(self) -> tuple[Tranche | None, float | None]:
        """Return the tranche and its price; None while unknown."""
        local = dt_util.now(FRANCE_TIME_ZONE)
        contract = in_force(contracts(self._entry), local.date())
        if contract is None:
            return None, None
        sources = self.coordinator.data.sources
        tranche = tranche_at(local, contract.rules, sources.calendar)
        if tranche is None:
            return None, None
        periods = price_periods(
            contract, manual_prices(self._entry), sources.official_prices
        )
        period = next((item for item in periods if item.covers(local.date())), None)
        return tranche, period.prices.get(tranche) if period else None


class CurrentPriceSensor(ContractNowSensor):
    """The price of a kWh right now, subscription excluded."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 4

    def __init__(self, entry: ElectricityContractsConfigEntry) -> None:
        """Price in the server's currency, like the Energy dashboard expects."""
        super().__init__(entry, "current_price")
        self._attr_native_unit_of_measurement = (
            f"{entry.runtime_data.hass.config.currency}/{UnitOfEnergy.KILO_WATT_HOUR}"
        )

    @property
    @override
    def native_value(self) -> float | None:
        """Return the price of the tranche in force."""
        return self._now()[1]


class CurrentTrancheSensor(ContractNowSensor):
    """The tranche in force: base, peak or off-peak, and the Tempo color."""

    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, entry: ElectricityContractsConfigEntry) -> None:
        """Name the tranche."""
        super().__init__(entry, "current_tranche")
        self._attr_options = [tranche.value for tranche in Tranche]

    @property
    @override
    def native_value(self) -> str | None:
        """Return the tranche in force."""
        tranche = self._now()[0]
        return tranche.value if tranche else None
