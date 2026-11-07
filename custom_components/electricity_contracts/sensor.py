"""Sensors of the actual cost and of the comparisons."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import EntityCategory, UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .comparison import Comparison, ContractTotals
from .const import DOMAIN, FRANCE_TIME_ZONE
from .coordinator import (
    ElectricityContractsConfigEntry,
    ElectricityContractsCoordinator,
    ElectricityContractsData,
)
from .data import Contract, comparisons, contracts

# Read-only entities of a coordinator.
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class SourceSensorDescription(SensorEntityDescription):
    """A sensor of the consumption source."""

    value_fn: Callable[[ElectricityContractsData], StateType | datetime]
    attributes_fn: Callable[[ElectricityContractsData], dict[str, Any]] | None = None


def _source_descriptions(currency: str) -> tuple[SourceSensorDescription, ...]:
    return (
        SourceSensorDescription(
            key="last_day_cost",
            translation_key="last_day_cost",
            device_class=SensorDeviceClass.MONETARY,
            native_unit_of_measurement=currency,
            suggested_display_precision=2,
            value_fn=lambda data: data.summary.last_day_cost,
            attributes_fn=lambda data: {
                "day": (
                    data.summary.last_day.isoformat() if data.summary.last_day else None
                )
            },
        ),
        SourceSensorDescription(
            key="month_average_price",
            translation_key="month_average_price",
            native_unit_of_measurement=f"{currency}/{UnitOfEnergy.KILO_WATT_HOUR}",
            suggested_display_precision=4,
            value_fn=lambda data: data.summary.month_price,
        ),
        SourceSensorDescription(
            key="current_contract",
            translation_key="current_contract",
            value_fn=lambda data: data.summary.current_contract,
        ),
        SourceSensorDescription(
            key="last_hour",
            translation_key="last_hour",
            device_class=SensorDeviceClass.TIMESTAMP,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda data: data.costing.last_source_hour,
        ),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ElectricityContractsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors of the source and of each comparison."""
    coordinator = entry.runtime_data
    currency = hass.config.currency
    source = [
        SourceSensor(coordinator, description)
        for description in _source_descriptions(currency)
    ]
    async_add_entities(source)
    unique_ids = {entity.unique_id for entity in source}
    entry_contracts = contracts(entry)
    for config in comparisons(entry):
        device = DeviceInfo(
            identifiers={(DOMAIN, config.subentry_id)},
            name=config.name,
            entry_type=DeviceEntryType.SERVICE,
        )
        entities: list[SensorEntity] = [
            BestContractSensor(coordinator, config.subentry_id, device),
            SavingSensor(coordinator, config.subentry_id, device, currency),
        ]
        for contract in config.select(entry_contracts):
            entities.append(
                ContractCostSensor(
                    coordinator, config.subentry_id, device, contract, currency
                )
            )
            entities.append(
                ContractPriceSensor(
                    coordinator, config.subentry_id, device, contract, currency
                )
            )
        async_add_entities(entities, config_subentry_id=config.subentry_id)
        unique_ids.update(entity.unique_id for entity in entities)
    _async_remove_stale_entities(hass, entry, unique_ids)


@callback
def _async_remove_stale_entities(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry, unique_ids: set[Any]
) -> None:
    """Remove the sensors of contracts no longer compared."""
    registry = er.async_get(hass)
    for item in er.async_entries_for_config_entry(registry, entry.entry_id):
        if item.domain == "sensor" and item.unique_id not in unique_ids:
            registry.async_remove(item.entity_id)


class SourceSensor(CoordinatorEntity[ElectricityContractsCoordinator], SensorEntity):
    """A sensor of the consumption source and its actual cost."""

    _attr_has_entity_name = True
    entity_description: SourceSensorDescription

    def __init__(
        self,
        coordinator: ElectricityContractsCoordinator,
        description: SourceSensorDescription,
    ) -> None:
        """Attach the sensor to the source's device."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> StateType | datetime:
        """Return the value from the latest update."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the attributes, if the sensor has any."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data)


class ComparisonSensor(
    CoordinatorEntity[ElectricityContractsCoordinator], SensorEntity
):
    """A sensor of one comparison."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ElectricityContractsCoordinator,
        subentry_id: str,
        device: DeviceInfo,
        key: str,
    ) -> None:
        """Attach the sensor to the comparison's device."""
        super().__init__(coordinator)
        self._subentry_id = subentry_id
        self._attr_unique_id = f"{subentry_id}_{key}"
        self._attr_device_info = device

    @property
    def comparison(self) -> Comparison:
        """Return the latest totals of the comparison."""
        return self.coordinator.data.comparisons[self._subentry_id]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the hours compared."""
        comparison = self.comparison
        return {
            "from": comparison.start.astimezone(FRANCE_TIME_ZONE).isoformat(),
            "to": comparison.end.astimezone(FRANCE_TIME_ZONE).isoformat(),
        }


class BestContractSensor(ComparisonSensor):
    """The cheapest contract over the window."""

    _attr_translation_key = "best_contract"

    def __init__(
        self,
        coordinator: ElectricityContractsCoordinator,
        subentry_id: str,
        device: DeviceInfo,
    ) -> None:
        """Set up the sensor."""
        super().__init__(coordinator, subentry_id, device, "best_contract")

    @property
    def native_value(self) -> str | None:
        """Return the name of the cheapest contract."""
        best = self.comparison.best
        return best.contract.name if best else None


class SavingSensor(ComparisonSensor):
    """What the cheapest contract would have saved on the contracts in force."""

    _attr_translation_key = "saving"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: ElectricityContractsCoordinator,
        subentry_id: str,
        device: DeviceInfo,
        currency: str,
    ) -> None:
        """Set up the sensor."""
        super().__init__(coordinator, subentry_id, device, "saving")
        self._attr_native_unit_of_measurement = currency

    @property
    def native_value(self) -> float | None:
        """Return the saving, None without a contract in force."""
        return self.comparison.saving


class ContractSensor(ComparisonSensor):
    """A sensor of one contract in a comparison."""

    def __init__(
        self,
        coordinator: ElectricityContractsCoordinator,
        subentry_id: str,
        device: DeviceInfo,
        contract: Contract,
        key: str,
    ) -> None:
        """Set up the sensor of a contract."""
        super().__init__(coordinator, subentry_id, device, f"{contract.uid}_{key}")
        self._uid = contract.uid
        self._attr_translation_placeholders = {"contract": contract.name}

    @property
    def totals(self) -> ContractTotals:
        """Return the totals of the contract."""
        return next(
            item for item in self.comparison.contracts if item.contract.uid == self._uid
        )


class ContractCostSensor(ContractSensor):
    """What a contract cost over the window."""

    _attr_translation_key = "contract_cost"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        coordinator: ElectricityContractsCoordinator,
        subentry_id: str,
        device: DeviceInfo,
        contract: Contract,
        currency: str,
    ) -> None:
        """Set up the sensor."""
        super().__init__(coordinator, subentry_id, device, contract, "cost")
        self._attr_native_unit_of_measurement = currency

    @property
    def native_value(self) -> float | None:
        """Return the total cost."""
        return self.totals.total

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the hours compared and the split of the cost."""
        totals = self.totals
        return {
            **super().extra_state_attributes,
            "energy": round(totals.energy, 3),
            "variable_cost": round(totals.variable, 2),
            "fixed_cost": round(totals.fixed, 2),
        }


class ContractPriceSensor(ContractSensor):
    """What a contract cost per kWh over the window."""

    _attr_translation_key = "contract_price"
    _attr_suggested_display_precision = 4

    def __init__(
        self,
        coordinator: ElectricityContractsCoordinator,
        subentry_id: str,
        device: DeviceInfo,
        contract: Contract,
        currency: str,
    ) -> None:
        """Set up the sensor."""
        super().__init__(coordinator, subentry_id, device, contract, "price")
        self._attr_native_unit_of_measurement = (
            f"{currency}/{UnitOfEnergy.KILO_WATT_HOUR}"
        )

    @property
    def native_value(self) -> float | None:
        """Return the average price."""
        return self.totals.average_price
