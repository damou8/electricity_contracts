"""Typed view of the configuration kept in the config entry and its subentries."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, time
from typing import Any

from elec_tariffs import (
    ContractKind,
    ContractRules,
    PricePeriod,
    TimeRange,
    Tranche,
)
from homeassistant.config_entries import ConfigEntry, ConfigSubentry

from .const import (
    CONF_ACTIVE_FROM,
    CONF_ACTIVE_TO,
    CONF_CONTRACT,
    CONF_END,
    CONF_FIXED_PER_YEAR,
    CONF_KIND,
    CONF_KVA,
    CONF_OFF_PEAK,
    CONF_PRICES,
    CONF_PRICING,
    CONF_START,
    CONF_UID,
    CONF_WEEKEND_OFF_PEAK,
    PRICING_OFFICIAL,
    SUBENTRY_CONTRACT,
    SUBENTRY_PRICE_PERIOD,
)


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


@dataclass(frozen=True, kw_only=True)
class Contract:
    """A contract to cost the consumption under."""

    subentry_id: str
    uid: str
    name: str
    rules: ContractRules
    official: bool
    kva: int | None
    active_from: date | None
    active_to: date | None

    @property
    def kind(self) -> ContractKind:
        """How the contract splits consumption into tranches."""
        return self.rules.kind

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
        official = data[CONF_PRICING] == PRICING_OFFICIAL
        return cls(
            subentry_id=subentry.subentry_id,
            uid=data[CONF_UID],
            name=subentry.title,
            rules=rules,
            official=official,
            kva=data[CONF_KVA] if official else None,
            active_from=_optional_date(data.get(CONF_ACTIVE_FROM)),
            active_to=_optional_date(data.get(CONF_ACTIVE_TO)),
        )


@dataclass(frozen=True, kw_only=True)
class ManualPrices:
    """Prices entered by hand for a contract, from one day to another."""

    subentry_id: str
    contract_uid: str
    period: PricePeriod

    @classmethod
    def from_subentry(cls, subentry: ConfigSubentry) -> ManualPrices:
        """Read a price period subentry."""
        data = subentry.data
        return cls(
            subentry_id=subentry.subentry_id,
            contract_uid=data[CONF_CONTRACT],
            period=PricePeriod(
                start=date.fromisoformat(data[CONF_START]),
                end=_optional_date(data.get(CONF_END)),
                fixed_per_year=data[CONF_FIXED_PER_YEAR],
                prices={
                    Tranche(tranche): price
                    for tranche, price in data[CONF_PRICES].items()
                },
            ),
        )


def contracts(entry: ConfigEntry) -> list[Contract]:
    """Return the contracts of an entry, in the order they were added."""
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


def manual_prices(entry: ConfigEntry) -> list[ManualPrices]:
    """Return the price periods entered by hand, in the order they were added."""
    return [
        ManualPrices.from_subentry(subentry)
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_PRICE_PERIOD
    ]


def price_periods(
    contract: Contract,
    manual: list[ManualPrices],
    official: Mapping[tuple[ContractKind, int], list[PricePeriod]],
) -> list[PricePeriod]:
    """Return the price periods of a contract, oldest first."""
    if contract.official:
        assert contract.kva is not None
        return official[(contract.kind, contract.kva)]
    return sorted(
        (item.period for item in manual if item.contract_uid == contract.uid),
        key=lambda period: period.start,
    )


def periods_overlap(
    first: tuple[date, date | None], second: tuple[date, date | None]
) -> bool:
    """Tell whether two periods (last day included, None if open) share a day."""
    first_start, first_end = first
    second_start, second_end = second
    return (first_end is None or second_start <= first_end) and (
        second_end is None or first_start <= second_end
    )
