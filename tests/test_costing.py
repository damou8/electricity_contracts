"""Tests of turning statistic rows into hours."""

from datetime import UTC, date, datetime, timedelta

import pytest

from custom_components.electricity_contracts.const import FRANCE_TIME_ZONE
from custom_components.electricity_contracts.costing import expand_rows

HOUR = timedelta(hours=1)


def midnight(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=FRANCE_TIME_ZONE).astimezone(
        UTC
    )


def daily_rows(
    first: date, days: int, kwh: float = 24.0
) -> list[tuple[datetime, float]]:
    return [(midnight(first + timedelta(days=n)), kwh) for n in range(days)]


def hourly_rows(
    start: datetime, hours: int, kwh: float = 0.5
) -> list[tuple[datetime, float]]:
    return [(start + HOUR * n, kwh) for n in range(hours)]


def test_hourly_rows_are_kept() -> None:
    rows = hourly_rows(datetime(2026, 4, 1, tzinfo=UTC), 5)
    assert [(hour.start, hour.kwh) for hour in expand_rows(rows)] == rows


def test_daily_rows_are_spread_over_their_day() -> None:
    hours = expand_rows(daily_rows(date(2025, 4, 1), 3))
    assert len(hours) == 72
    assert hours[0].start == midnight(date(2025, 4, 1))
    assert hours[-1].start == midnight(date(2025, 4, 4)) - HOUR
    # Without hourly days to learn from, days are spread evenly.
    assert {round(hour.kwh, 9) for hour in hours} == {1.0}


def test_daily_row_on_a_23_hour_day() -> None:
    hours = expand_rows(daily_rows(date(2026, 3, 28), 3, kwh=23.0))
    spring = [
        hour
        for hour in hours
        if hour.start.astimezone(FRANCE_TIME_ZONE).date() == date(2026, 3, 29)
    ]
    assert len(spring) == 23
    assert sum(hour.kwh for hour in spring) == pytest.approx(23)


def test_switch_from_daily_to_hourly_rows() -> None:
    # Like a Linky meter whose load curve starts on 22 March 2026.
    days = daily_rows(date(2026, 3, 19), 3, kwh=12.0)
    hours_start = midnight(date(2026, 3, 22))
    rows = days + hourly_rows(hours_start, 24 * 20)
    hours = expand_rows(rows)
    assert len(hours) == 72 + 24 * 20
    assert hours[72].start == hours_start
    assert [hour.start for hour in hours] == sorted({hour.start for hour in hours})
    assert sum(hour.kwh for hour in hours) == pytest.approx(36 + 0.5 * 24 * 20)


def test_daily_rows_follow_the_hourly_days() -> None:
    hours_start = midnight(date(2026, 3, 23))
    # 20 hourly days where only the night (22:00 to 6:00) consumes.
    hourly = [
        (
            start,
            1.0
            if start.astimezone(FRANCE_TIME_ZONE).hour in (*range(6), 22, 23)
            else 0.0,
        )
        for start, _ in hourly_rows(hours_start, 24 * 20)
    ]
    rows = [(midnight(date(2026, 3, 22)), 8.0), *hourly]
    hours = expand_rows(rows)
    day = hours[:24]
    night = [
        hour
        for hour in day
        if hour.start.astimezone(FRANCE_TIME_ZONE).hour in (*range(6), 22, 23)
    ]
    assert sum(hour.kwh for hour in night) == pytest.approx(8)


def test_last_row_after_daily_rows_is_daily() -> None:
    hours = expand_rows(daily_rows(date(2025, 4, 1), 2))
    assert len(hours) == 48


def test_single_midnight_row_is_an_hour() -> None:
    rows = [(midnight(date(2025, 4, 1)), 0.5)]
    assert len(expand_rows(rows)) == 1


def test_missing_hours_share_the_next_row() -> None:
    start = datetime(2026, 10, 25, 0, tzinfo=UTC)
    rows = [(start, 0.4), (start + 2 * HOUR, 0.8)]
    hours = expand_rows(rows)
    assert [(hour.start, hour.kwh) for hour in hours] == [
        (start, 0.4),
        (start + HOUR, 0.4),
        (start + 2 * HOUR, 0.4),
    ]
