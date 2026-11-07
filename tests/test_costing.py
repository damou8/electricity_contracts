"""Tests of keeping the statistic rows that hold one hour."""

from datetime import UTC, date, datetime, timedelta

from custom_components.electricity_contracts.const import FRANCE_TIME_ZONE
from custom_components.electricity_contracts.costing import hourly_rows

HOUR = timedelta(hours=1)


def midnight(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=FRANCE_TIME_ZONE).astimezone(
        UTC
    )


def daily(first: date, days: int) -> list[tuple[datetime, float]]:
    return [(midnight(first + timedelta(days=n)), 24.0) for n in range(days)]


def hourly(start: datetime, hours: int) -> list[tuple[datetime, float]]:
    return [(start + HOUR * n, 0.5) for n in range(hours)]


def kept(rows: list[tuple[datetime, float]]) -> list[tuple[datetime, float]]:
    return [(hour.start, hour.kwh) for hour in hourly_rows(rows)]


def test_hourly_rows_are_kept() -> None:
    rows = hourly(datetime(2026, 4, 1, tzinfo=UTC), 5)
    assert kept(rows) == rows


def test_daily_rows_are_not_costed() -> None:
    assert kept(daily(date(2025, 4, 1), 3)) == []
    # Across the spring change the day has 23 hours.
    assert kept(daily(date(2026, 3, 28), 3)) == []


def test_switch_from_daily_to_hourly_rows() -> None:
    # Like a Linky meter whose load curve starts on 22 March 2026.
    hours = hourly(midnight(date(2026, 3, 22)), 30)
    assert kept(daily(date(2026, 3, 19), 3) + hours) == hours


def test_single_midnight_row_is_an_hour() -> None:
    rows = [(midnight(date(2025, 4, 1)), 0.5)]
    assert kept(rows) == rows


def test_missing_hours_are_not_estimated() -> None:
    start = datetime(2026, 10, 25, tzinfo=UTC)
    rows = [(start, 0.4), (start + 2 * HOUR, 0.8)]
    assert kept(rows) == rows
