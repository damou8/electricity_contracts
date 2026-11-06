"""Tests of the typed view of the configuration."""

from datetime import date, time
from types import MappingProxyType

import pytest
from elec_tariffs import ContractKind, TimeRange
from homeassistant.config_entries import ConfigSubentry

from custom_components.electricity_contracts.data import (
    Contract,
    parse_time_range,
    periods_overlap,
)

from .conftest import contract_subentry


@pytest.mark.parametrize("text", ["22:00", "22:00-22:00", "22h-6h", "22:15-06:00"])
def test_unreadable_time_ranges(text: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - each case raises a different message
        parse_time_range(text)


def test_time_range() -> None:
    assert parse_time_range(" 12:30 - 14:00 ") == TimeRange(
        start=time(12, 30), end=time(14)
    )


def test_hphc_contract() -> None:
    data = contract_subentry(
        "HP/HC",
        uid="hphc0001",
        kind=ContractKind.HPHC,
        off_peak=["23:00-07:00"],
        active_from="2025-01-01",
        active_to="2025-12-31",
    )
    contract = Contract.from_subentry(
        ConfigSubentry(
            data=MappingProxyType(dict(data["data"])),
            subentry_type=data["subentry_type"],
            title=data["title"],
            unique_id=data["unique_id"],
        )
    )
    assert contract.kind is ContractKind.HPHC
    assert contract.rules.off_peak == (TimeRange(start=time(23), end=time(7)),)
    assert contract.kva == 6
    assert contract.official
    assert (contract.active_from, contract.active_to) == (
        date(2025, 1, 1),
        date(2025, 12, 31),
    )


@pytest.mark.parametrize(
    ("first", "second", "overlap"),
    [
        ((date(2025, 1, 1), date(2025, 12, 31)), (date(2026, 1, 1), None), False),
        ((date(2025, 1, 1), date(2025, 12, 31)), (date(2025, 12, 31), None), True),
        ((date(2025, 1, 1), None), (date(2020, 1, 1), date(2024, 12, 31)), False),
        ((date(2025, 1, 1), None), (date(2030, 1, 1), None), True),
    ],
)
def test_periods_overlap(
    first: tuple[date, date | None], second: tuple[date, date | None], overlap: bool
) -> None:
    assert periods_overlap(first, second) is overlap
    assert periods_overlap(second, first) is overlap
