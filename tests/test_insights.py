"""Tests of the weather line: where the heating starts and what a degree costs."""

from datetime import date, timedelta
from typing import Any

import pytest

from custom_components.electricity_contracts.insights import line_heating, weather_fit

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


def heated(
    base: float, temperatures: list[float], linear: float, square: float
) -> list[float]:
    """5 kWh a day, and the heating of the degrees under `base` on a curve."""
    return [
        5.0 + linear * max(0.0, base - t) + square * max(0.0, base - t) ** 2
        for t in temperatures
    ]


@pytest.mark.parametrize(
    ("linear", "square"),
    [
        # Less a degree in the cold: heaters at full power.
        (3.0, -0.05),
        # More a degree in the cold: a heat pump losing its efficiency.
        (1.0, 0.05),
    ],
)
def test_the_heating_can_curve(linear: float, square: float) -> None:
    temperatures = [-5.0 + index for index in range(30)]
    weather = fit(temperatures, heated(15.0, temperatures, linear, square))
    assert weather["base"] == 15.0
    assert (weather["linear"], weather["square"]) == (
        pytest.approx(linear),
        pytest.approx(square),
    )
    assert weather["reach"] == 20.0
    # On average over the days, per degree under the base.
    degrees = [max(0.0, 15.0 - t) for t in temperatures]
    heating = sum(linear * x + square * x**2 for x in degrees)
    assert weather["slope"] == pytest.approx(heating / sum(degrees), abs=1e-3)


def test_the_heating_keeps_rising_with_the_cold() -> None:
    # The curve would use less on the coldest days than on milder ones: at 20
    # degrees under the base, 3 - 2 * 0.1 * 20 is under 0.
    temperatures = [-5.0 + index for index in range(30)]
    weather = fit(temperatures, heated(15.0, temperatures, 3.0, -0.1))
    # Whatever base fits best, its heating keeps rising up to the coldest day.
    assert weather["linear"] >= 0
    assert weather["linear"] + 2 * weather["square"] * weather["reach"] > 0


def test_few_heating_days_make_a_line() -> None:
    # 13 days under every base, the rest over all of them.
    temperatures = [2.0 + index for index in range(13)] + [
        20.0 + index for index in range(17)
    ]
    weather = fit(temperatures, heated(15.0, temperatures, 1.0, 0.1))
    assert weather["square"] == 0.0


def test_past_the_coldest_day_the_curve_goes_on_straight() -> None:
    weather = {"linear": 2.0, "square": 0.1, "reach": 10.0}
    assert line_heating(weather, -1.0) == 0.0
    assert line_heating(weather, 5.0) == pytest.approx(12.5)
    assert line_heating(weather, 10.0) == pytest.approx(30.0)
    # 4 kWh a degree at the coldest day seen, on 2 more degrees.
    assert line_heating(weather, 12.0) == pytest.approx(38.0)
