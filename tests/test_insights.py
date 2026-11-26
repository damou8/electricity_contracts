"""Tests of the weather line: where the heating starts and what a degree costs."""

from datetime import date, timedelta
from typing import Any

import pytest

from custom_components.electricity_contracts.insights import weather_fit

FIRST = date(2026, 1, 1)


def fit(temperatures: list[float], energy: list[float]) -> dict[str, Any]:
    days = [FIRST + timedelta(days=index) for index in range(len(temperatures))]
    return weather_fit(
        {day: {"energy": kwh} for day, kwh in zip(days, energy, strict=True)},
        dict(zip(days, temperatures, strict=True)),
    )


def test_the_base_is_where_the_heating_starts() -> None:
    # 5 kWh a day, and 2 more a degree under 12.5 °C, from 2 to 24 °C.
    temperatures = [2.0 + index for index in range(23)]
    weather = fit(temperatures, [5.0 + 2.0 * max(0.0, 12.5 - t) for t in temperatures])
    assert weather["base"] == 12.5
    assert weather["slope"] == pytest.approx(2.0)
    assert weather["intercept"] == pytest.approx(5.0)
    assert weather["degree_days"] == pytest.approx(sum(range(11)) + 5.5)


def test_cold_days_alone_keep_18_degrees() -> None:
    # Every day is under every base: they all fit alike.
    temperatures = [float(index % 8) for index in range(20)]
    weather = fit(temperatures, [4.0 + 3.0 * (18.0 - t) for t in temperatures])
    assert weather["base"] == 18.0
    assert weather["slope"] == pytest.approx(3.0)
    assert weather["intercept"] == pytest.approx(4.0)


def test_no_heating_keeps_18_degrees() -> None:
    # More used on warm days (cooling): no base gives heating.
    temperatures = [5.0 + index for index in range(20)]
    weather = fit(temperatures, [10.0 + 0.5 * t for t in temperatures])
    assert weather["base"] == 18.0
    assert weather["heating_share"] is None


def test_heating_under_cooling() -> None:
    # Heating under 10 °C, and air conditioning above 14 °C: at 18 °C the line
    # falls, at 10 °C the heating shows.
    temperatures = [float(index) for index in range(31)]
    energy = [
        10.0 + 2.0 * max(0.0, 10.0 - t) + 2.0 * max(0.0, t - 14.0) for t in temperatures
    ]
    weather = fit(temperatures, energy)
    assert weather["base"] == 10.0
    assert weather["slope"] > 0


def test_too_few_days_for_a_line() -> None:
    temperatures = [float(index) for index in range(13)]
    weather = fit(temperatures, [20.0 - t for t in temperatures])
    assert (weather["base"], weather["slope"], weather["days"]) == (18.0, None, 13)
