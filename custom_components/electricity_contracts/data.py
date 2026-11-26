"""Typed view of the configuration kept in the config entry and its subentries."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, time
from typing import Any

from elec_tariffs import (
    TRANCHES,
    ContractKind,
    ContractRules,
    GasPricePeriod,
    GasProfile,
    PricePeriod,
    TimeRange,
    Tranche,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    CONF_ACTIVE_FROM,
    CONF_ACTIVE_TO,
    CONF_END,
    CONF_FIXED_PER_YEAR,
    CONF_HEATING_CONTENT,
    CONF_HEATING_ENERGY,
    CONF_HEATING_STATISTICS,
    CONF_INDOOR_TEMPERATURES,
    CONF_KIND,
    CONF_KVA,
    CONF_OFF_PEAK,
    CONF_PERIODS,
    CONF_PRICE,
    CONF_PRICE_ENTITY,
    CONF_PRICES,
    CONF_PRICING,
    CONF_PROFILE,
    CONF_START,
    CONF_STATISTIC_ID,
    CONF_UID,
    CONF_WATER_ENERGY,
    CONF_WATER_STATISTIC,
    CONF_WEEKEND_OFF_PEAK,
    CONTENT_HEATING_WATER,
    ENERGY_ELECTRICITY,
    ENERGY_GAS,
    FRANCE_TIME_ZONE,
    NO_METER,
    PRICING_ENTITY,
    PRICING_MANUAL,
    PRICING_OFFICIAL,
    SECTION_HEATING,
    SUBENTRY_CONTRACT,
    SUBENTRY_GAS_CONTRACT,
)


def source_statistic(entry: ConfigEntry) -> str | None:
    """Return the electricity consumption statistic, None for a source without one."""
    statistic_id: str | None = entry.data.get(CONF_STATISTIC_ID)
    return statistic_id


def source_object(entry: ConfigEntry) -> str:
    """Return the object part of the IDs of the statistics the entry writes."""
    statistic_id = source_statistic(entry)
    return slugify(statistic_id) if statistic_id else NO_METER


def parse_time_range(value: str) -> TimeRange:
    """Read an off-peak range written like "22:00-06:00".

    Raise ValueError when it isn't two times on a whole or half hour.
    """
    start_text, separator, end_text = value.strip().partition("-")
    if not separator:
        msg = f"{value!r} is not a range"
        raise ValueError(msg)
    start = time.fromisoformat(start_text.strip())
    end = time.fromisoformat(end_text.strip())
    if start == end:
        msg = f"{value!r} is empty"
        raise ValueError(msg)
    return TimeRange(start=start, end=end)


def format_time_range(time_range: TimeRange) -> str:
    """Write an off-peak range like "22:00-06:00"."""
    return f"{time_range.start:%H:%M}-{time_range.end:%H:%M}"


def _optional_date(value: Any) -> date | None:
    return date.fromisoformat(value) if value else None


def period_from_data(data: Mapping[str, Any]) -> PricePeriod:
    """Read an electricity price period kept in a contract subentry."""
    return PricePeriod(
        start=date.fromisoformat(data[CONF_START]),
        end=_optional_date(data.get(CONF_END)),
        fixed_per_year=data[CONF_FIXED_PER_YEAR],
        prices={
            Tranche(tranche): price for tranche, price in data[CONF_PRICES].items()
        },
    )


def gas_period_from_data(data: Mapping[str, Any]) -> GasPricePeriod:
    """Read a gas price period kept in a gas contract subentry."""
    return GasPricePeriod(
        start=date.fromisoformat(data[CONF_START]),
        end=_optional_date(data.get(CONF_END)),
        fixed_per_year=data[CONF_FIXED_PER_YEAR],
        price=data[CONF_PRICE],
    )


@dataclass(frozen=True, kw_only=True)
class EntityPrice:
    """A price of a kWh read from a sensor, hour by hour, and a subscription."""

    entity_id: str
    fixed_per_year: float

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> EntityPrice | None:
        """Read the sensor of a contract priced by one; None for another pricing."""
        if data[CONF_PRICING] != PRICING_ENTITY:
            return None
        return cls(
            entity_id=data[CONF_PRICE_ENTITY],
            fixed_per_year=data[CONF_FIXED_PER_YEAR],
        )

    def current(self, hass: HomeAssistant) -> float | None:
        """Return the price the sensor shows now, None if it shows none."""
        state = hass.states.get(self.entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None
        try:
            return float(state.state)
        except ValueError:
            return None


@dataclass(frozen=True, kw_only=True)
class Contract:
    """An electricity contract to cost the consumption under."""

    subentry_id: str
    uid: str
    name: str
    rules: ContractRules
    pricing: str
    kva: int | None
    periods: tuple[PricePeriod, ...]
    """The prices entered by hand, oldest first."""
    entity: EntityPrice | None
    active_from: date | None
    active_to: date | None

    @property
    def kind(self) -> ContractKind:
        """How the contract splits consumption into tranches."""
        return self.rules.kind

    @property
    def official(self) -> bool:
        """Tell whether the contract follows the regulated prices."""
        return self.pricing == PRICING_OFFICIAL

    @classmethod
    def from_subentry(cls, subentry: ConfigSubentry) -> Contract:
        """Read a contract subentry."""
        data = subentry.data
        kind = ContractKind(data[CONF_KIND])
        rules = ContractRules(kind=kind)
        if kind is ContractKind.HPHC:
            rules = ContractRules(
                kind=kind,
                off_peak=tuple(parse_time_range(text) for text in data[CONF_OFF_PEAK]),
                weekend_off_peak=data[CONF_WEEKEND_OFF_PEAK],
            )
        pricing = data[CONF_PRICING]
        return cls(
            subentry_id=subentry.subentry_id,
            uid=data[CONF_UID],
            name=subentry.title,
            rules=rules,
            pricing=pricing,
            kva=data[CONF_KVA] if pricing == PRICING_OFFICIAL else None,
            periods=(
                tuple(
                    sorted(
                        (period_from_data(item) for item in data.get(CONF_PERIODS, [])),
                        key=lambda period: period.start,
                    )
                )
                if pricing == PRICING_MANUAL
                else ()
            ),
            entity=EntityPrice.from_data(data),
            active_from=_optional_date(data.get(CONF_ACTIVE_FROM)),
            active_to=_optional_date(data.get(CONF_ACTIVE_TO)),
        )


def contracts(entry: ConfigEntry) -> list[Contract]:
    """Return the electricity contracts of an entry, in the order they were added."""
    return [
        Contract.from_subentry(subentry)
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_CONTRACT
    ]


def in_force(entry_contracts: list[Contract], day: date) -> Contract | None:
    """Return the contract that was in force on `day`, if any."""
    for contract in entry_contracts:
        if (
            contract.active_from is not None
            and contract.active_from <= day
            and (contract.active_to is None or contract.active_to >= day)
        ):
            return contract
    return None


def price_periods(
    hass: HomeAssistant,
    contract: Contract,
    official: Mapping[tuple[ContractKind, int], list[PricePeriod]],
) -> list[PricePeriod]:
    """Return the price periods of a contract, oldest first.

    A contract priced by a sensor has one period from today, at the price the
    sensor shows now (none while it shows none): what is shown and projected.
    Its past hours are costed at the price of each hour instead.
    """
    if contract.official:
        assert contract.kva is not None
        return official[(contract.kind, contract.kva)]
    if contract.entity is not None:
        price = contract.entity.current(hass)
        if price is None:
            return []
        return [
            PricePeriod(
                start=dt_util.now(FRANCE_TIME_ZONE).date(),
                end=None,
                fixed_per_year=contract.entity.fixed_per_year,
                prices=dict.fromkeys(TRANCHES[contract.kind], price),
            )
        ]
    return list(contract.periods)


def periods_overlap(
    first: tuple[date, date | None], second: tuple[date, date | None]
) -> bool:
    """Tell whether two periods (last day included, None if open) share a day."""
    first_start, first_end = first
    second_start, second_end = second
    return (first_end is None or second_start <= first_end) and (
        second_end is None or first_start <= second_end
    )


@dataclass(frozen=True, kw_only=True)
class Heating:
    """What heats the home and its water, from the options."""

    statistics: tuple[str, ...]
    """Statistics summed as the heating; electric ones are part of the source."""
    gas: bool
    with_water: bool
    """The statistics hold the hot water as well."""
    water_statistic: str | None
    water_gas: bool
    indoor: tuple[str, ...]
    outdoor: str | None

    @classmethod
    def from_options(
        cls, options: Mapping[str, Any], *, outdoor: str | None
    ) -> Heating:
        """Read the heating section and the indoor thermometers; all are optional.

        `outdoor` is the outdoor temperature statistic (see `outdoor_statistic`).
        """
        section: Mapping[str, Any] = options.get(SECTION_HEATING) or {}
        return cls(
            statistics=tuple(section.get(CONF_HEATING_STATISTICS) or ()),
            gas=section.get(CONF_HEATING_ENERGY, ENERGY_ELECTRICITY) == ENERGY_GAS,
            with_water=section.get(CONF_HEATING_CONTENT) == CONTENT_HEATING_WATER,
            water_statistic=section.get(CONF_WATER_STATISTIC) or None,
            water_gas=section.get(CONF_WATER_ENERGY, ENERGY_ELECTRICITY) == ENERGY_GAS,
            indoor=tuple(options.get(CONF_INDOOR_TEMPERATURES) or ()),
            outdoor=outdoor,
        )

    @property
    def measured(self) -> bool:
        """Tell whether statistics measure the heating; without, it is estimated."""
        return bool(self.statistics)

    @property
    def shown(self) -> bool:
        """Tell whether there is anything to show about heating."""
        return self.measured or self.outdoor is not None


@dataclass(frozen=True, kw_only=True)
class GasContract:
    """A gas contract: what the gas of the heating and hot water is costed at."""

    subentry_id: str
    uid: str
    name: str
    pricing: str
    profile: GasProfile | None
    """The CRE profile of a contract at the reference price."""
    periods: tuple[GasPricePeriod, ...]
    """The prices entered by hand, oldest first."""
    entity: EntityPrice | None
    active_from: date | None
    active_to: date | None

    @classmethod
    def from_subentry(cls, subentry: ConfigSubentry) -> GasContract:
        """Read a gas contract subentry."""
        data = subentry.data
        pricing = data[CONF_PRICING]
        return cls(
            subentry_id=subentry.subentry_id,
            uid=data[CONF_UID],
            name=subentry.title,
            pricing=pricing,
            profile=(
                GasProfile(data[CONF_PROFILE]) if pricing == PRICING_OFFICIAL else None
            ),
            periods=(
                tuple(
                    sorted(
                        (
                            gas_period_from_data(item)
                            for item in data.get(CONF_PERIODS, [])
                        ),
                        key=lambda period: period.start,
                    )
                )
                if pricing == PRICING_MANUAL
                else ()
            ),
            entity=EntityPrice.from_data(data),
            active_from=_optional_date(data.get(CONF_ACTIVE_FROM)),
            active_to=_optional_date(data.get(CONF_ACTIVE_TO)),
        )

    def covers(self, day: date) -> bool:
        """Tell whether the contract was in force on `day`.

        Without a first day it was always in force: a home usually has one.
        """
        return (self.active_from is None or self.active_from <= day) and (
            self.active_to is None or day <= self.active_to
        )


def gas_contracts(entry: ConfigEntry) -> list[GasContract]:
    """Return the gas contracts of an entry, in the order they were added."""
    return [
        GasContract.from_subentry(subentry)
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_GAS_CONTRACT
    ]


def gas_in_force(entry_contracts: list[GasContract], day: date) -> GasContract | None:
    """Return the gas contract that was in force on `day`, if any."""
    return next((item for item in entry_contracts if item.covers(day)), None)
