"""What the consumption in force looked like over a window: days, hours, Tempo."""

import math
from datetime import date, datetime, timedelta
from typing import Any

from elec_tariffs import ContractKind, TempoColor, Tranche, season_bounds, season_of
from homeassistant.components.recorder.statistics import (
    StatisticsRow,
    statistics_during_period,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.recorder import get_instance
from homeassistant.util import dt as dt_util

from .comparison import (
    data_end,
    day_start,
    hourly_changes,
    linky_days,
    narrow_window,
    read_changes,
)
from .const import FRANCE_TIME_ZONE
from .coordinator import ElectricityContractsConfigEntry
from .data import (
    Contract,
    contracts,
    in_force,
    manual_prices,
    price_periods,
    source_statistic,
)
from .outlook import RED_DAYS, WHITE_DAYS, placed_days
from .weather import outdoor_ids, outdoor_rows, outdoor_statistic

# Tempo's peak hours, also used to tell day from night for the other contracts.
_PEAK_HOURS = range(6, 22)
_ESTIMATE_WEEKS = 8
# What keeps running: the lowest hour between 3:00 and 5:00 of the quiet nights.
_BASELOAD_HOURS = (3, 4)
_QUIET_NIGHTS = 0.1
_YEAR = timedelta(days=365)
_YEAR_HOURS = 8760
# Heating degree days count the degrees below a base, from each day's mean. The
# base is where the heating starts: fitted on the days, from 10 to 20 °C, and
# 18 °C when the days can't tell (all cold, or all warm).
DEGREE_DAY_BASE = 18.0
_BASES = tuple(base / 2 for base in range(20, 41))
_MIN_FIT_DAYS = 14
_SINGULAR = 1e-9
# Below this mean square (kWh²), fits are exact: rounding must not rank them.
_FLOOR = 1e-12


def _local(timestamp: float) -> datetime:
    return dt_util.utc_from_timestamp(timestamp).astimezone(FRANCE_TIME_ZONE)


async def async_insights(
    hass: HomeAssistant,
    *,
    entry: ElectricityContractsConfigEntry,
    start: datetime,
    end: datetime,
) -> dict[str, Any]:
    """Describe the actual consumption between `start` and `end` (UTC).

    The window is narrowed like a comparison, so the figures agree.
    """
    coordinator = entry.runtime_data
    status = coordinator.data.costing
    entry_contracts = contracts(entry)
    today = dt_util.now(FRANCE_TIME_ZONE).date()
    contract = in_force(entry_contracts, today)
    tempo = contract if contract and contract.kind is ContractKind.TEMPO else None
    calendar = coordinator.data.sources.calendar
    if status.actual is None:
        return {
            "days": [],
            "daily": [],
            "profile": [],
            "previous": None,
            # Nothing costed yet, or no meter: the colors left still help.
            "tempo": (
                _tempo(entry, tempo, calendar, [], today) if tempo is not None else None
            ),
            "baseload": None,
            "weather": None,
        }
    # The days the Linky only gave in total are read over the whole window.
    window_start, window_end = start, end
    start, end = narrow_window(status, entry_contracts, start, end)
    source_id = source_statistic(entry)
    ids = coordinator.costing.actual_statistics()
    costs = [ids.variable, ids.fixed]
    temperature_id = outdoor_statistic(entry)
    previous_start = start - (end - start)
    has_previous = (
        end > start
        and status.first_hour is not None
        and previous_start >= status.first_hour
    )
    year_end = data_end(status, entry_contracts) or end
    year_start = max(year_end - _YEAR, status.first_hour or year_end)

    def read() -> tuple[
        dict[str, list[tuple[float, float]]],
        dict[str, float] | None,
        list[tuple[float, float]],
        dict[str, list[tuple[float, float]]],
        list[StatisticsRow],
        dict[date, float],
    ]:
        hours = (
            hourly_changes(hass, start, end, [*costs, ids.energy])
            if end > start
            else {}
        )
        previous = (
            read_changes(hass, previous_start, start, [*costs, ids.energy])
            if has_previous
            else None
        )
        recent = (
            hourly_changes(
                hass,
                day_start(today - timedelta(weeks=_ESTIMATE_WEEKS)),
                day_start(today),
                [ids.energy],
            )[ids.energy]
            if tempo is not None
            else []
        )
        year = hourly_changes(hass, year_start, year_end, [ids.variable, ids.energy])
        linky = (
            linky_days(hass, source_id, window_start, window_end) if source_id else {}
        )
        temperatures = (
            outdoor_rows(
                entry,
                statistics_during_period(
                    hass,
                    window_start,
                    window_end,
                    set(outdoor_ids(entry)),
                    "hour",
                    {"temperature": UnitOfTemperature.CELSIUS},
                    {"mean"},
                ),
            )
            if temperature_id and (end > start or linky)
            else []
        )
        return hours, previous, recent, year, temperatures, linky

    hours, previous, recent, year, temperatures, linky = await get_instance(
        hass
    ).async_add_executor_job(read)

    days: dict[date, dict[str, float]] = {}
    profile = [[0.0, 0] for _ in range(24)]
    nights: dict[date, float] = {}
    for timestamp, energy in hours.get(ids.energy, []):
        local = _local(timestamp)
        day = days.setdefault(local.date(), {"energy": 0.0, "peak": 0.0, "cost": 0.0})
        day["energy"] += energy
        if local.hour in _PEAK_HOURS:
            day["peak"] += energy
        if local.hour in _BASELOAD_HOURS:
            nights[local.date()] = min(nights.get(local.date(), energy), energy)
        profile[local.hour][0] += energy
        profile[local.hour][1] += 1
    for statistic_id in costs:
        for timestamp, cost in hours.get(statistic_id, []):
            if (costed := days.get(_local(timestamp).date())) is not None:
                costed["cost"] += cost
    temperature = daily_means(temperatures)

    return {
        "days": [
            {
                "date": day.isoformat(),
                "color": calendar[day].value if day in calendar else None,
                "energy": round(values["energy"], 3),
                "peak_energy": round(values["peak"], 3),
                "cost": round(values["cost"], 2),
                "temperature": (
                    round(temperature[day], 1) if day in temperature else None
                ),
            }
            for day, values in sorted(days.items())
        ],
        # Days only known in total: no hours, so no cost nor peak hours.
        "daily": [
            {
                "date": day.isoformat(),
                "color": calendar[day].value if day in calendar else None,
                "energy": round(energy, 3),
                "temperature": (
                    round(temperature[day], 1) if day in temperature else None
                ),
            }
            for day, energy in sorted(linky.items())
        ],
        "profile": [
            round(total / count, 4) if count else None for total, count in profile
        ],
        "previous": (
            {
                "start": previous_start.astimezone(FRANCE_TIME_ZONE).isoformat(),
                "energy": round(previous[ids.energy], 3),
                "cost": round(previous[ids.variable] + previous[ids.fixed], 2),
            }
            if previous is not None
            else None
        ),
        "tempo": (
            _tempo(entry, tempo, calendar, recent, today) if tempo is not None else None
        ),
        "baseload": _baseload(
            nights,
            hours=len(hours.get(ids.energy, [])),
            energy=sum(values["energy"] for values in days.values()),
            year=year,
            cost_id=ids.variable,
            energy_id=ids.energy,
        ),
        "weather": (
            weather_fit(days, temperature) if temperature_id is not None else None
        ),
    }


def daily_means(rows: list[StatisticsRow]) -> dict[date, float]:
    """Average the hourly means of each day, French time."""
    by_day: dict[date, list[float]] = {}
    for row in rows:
        if (mean := row.get("mean")) is not None:
            by_day.setdefault(_local(row["start"]).date(), []).append(mean)
    return {day: sum(values) / len(values) for day, values in by_day.items()}


def _baseload(  # noqa: PLR0913 - the nights, the window and the year
    nights: dict[date, float],
    *,
    hours: int,
    energy: float,
    year: dict[str, list[tuple[float, float]]],
    cost_id: str,
    energy_id: str,
) -> dict[str, Any] | None:
    """Describe what keeps running all the time, and what it costs over a year.

    The quietest nights tell it, as heating or cooling keeps others busy. A
    constant load pays the average price of the hours, which comes from the last
    12 months.
    """
    if not nights:
        return None
    # The 10th percentile of the nights; an hour's kWh is its average power in kW.
    quiet = sorted(nights.values())
    power = quiet[int(_QUIET_NIGHTS * (len(quiet) - 1))]
    energy_by_hour = dict(year.get(energy_id, []))
    prices = [
        cost / energy_by_hour[hour]
        for hour, cost in year.get(cost_id, [])
        if energy_by_hour.get(hour, 0) > 0
    ]
    annual_energy = power * _YEAR_HOURS
    return {
        "power": round(power * 1000),
        "nights": [
            {"date": day.isoformat(), "power": round(value * 1000)}
            for day, value in sorted(nights.items())
        ],
        "share": (round(min(1.0, power * hours / energy), 4) if energy > 0 else None),
        "annual_energy": round(annual_energy),
        "annual_cost": (
            round(annual_energy * sum(prices) / len(prices), 2) if prices else None
        ),
    }


def weather_fit(
    days: dict[date, dict[str, float]], temperature: dict[date, float]
) -> dict[str, Any]:
    """Split the consumption between the cold and the rest.

    Each day's consumption is fitted on its heating degree days: an intercept,
    what a day consumes without heating, and the heating, which grows with the
    degrees under the base, on a curve (`linear` + `square`) when the days show
    one and it keeps rising, else on a straight line. Past the coldest day seen
    (`reach`), it goes on straight. `slope` is what a degree colder costs on
    average over these days. The base is the one, every half degree from 10 to
    20 °C, that fits the days best: a fixed 18 °C counted the
    rest of the home's consumption that grows in winter as heating; measured
    homes start heating around 16 °C. `line_heating` gives the heating of a day
    from the fit.
    """
    pairs = [
        (temperature[day], values["energy"])
        for day, values in days.items()
        if day in temperature
    ]
    energy = sum(value for _, value in pairs)
    base, fitted, found = (
        _best_base(pairs)
        if len(pairs) >= _MIN_FIT_DAYS
        else (DEGREE_DAY_BASE, None, False)
    )
    degree_days = sum(max(0.0, base - outdoor) for outdoor, _ in pairs)
    curve: dict[str, float] = {}
    slope = intercept = share = None
    if fitted is not None:
        intercept, linear, square, reach = fitted
        curve = {"linear": linear, "square": square, "reach": reach}
        heating = sum(
            line_heating(curve, max(0.0, base - outdoor)) for outdoor, _ in pairs
        )
        slope = heating / degree_days if degree_days > 0 else linear
        if slope > 0 and energy > 0:
            share = min(1.0, heating / energy)
    return {
        "base": base,
        "base_fitted": found,
        "days": len(pairs),
        "degree_days": round(degree_days, 1),
        "mean_temperature": (
            round(
                sum(temperature[day] for day in days if day in temperature)
                / len(pairs),
                1,
            )
            if pairs
            else None
        ),
        "slope": round(slope, 3) if slope is not None else None,
        "intercept": round(intercept, 2) if intercept is not None else None,
        "linear": round(curve["linear"], 4) if curve else None,
        "square": round(curve["square"], 6) if curve else None,
        "reach": round(curve["reach"], 2) if curve else None,
        "heating_share": round(share, 4) if share is not None else None,
    }


def line_heating(weather: dict[str, Any], degrees: float) -> float:
    """Return the heating of a day `degrees` under the base, from a weather fit.

    On the curve up to the coldest day seen, then straight on at its slope there.
    """
    if degrees <= 0:
        return 0.0
    linear, square, reach = weather["linear"], weather["square"], weather["reach"]
    if degrees <= reach:
        return float(linear * degrees + square * degrees**2)
    end = linear * reach + square * reach**2
    return float(end + (linear + 2 * square * reach) * (degrees - reach))


def _solve(matrix: list[list[float]], vector: list[float]) -> list[float] | None:
    """Solve a small linear system by elimination; None when it's singular.

    A pivot is too small against the largest value of its column at the start.
    """
    size = len(vector)
    rows = [[*row, value] for row, value in zip(matrix, vector, strict=True)]
    scales = [max(abs(row[column]) for row in matrix) or 1.0 for column in range(size)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(rows[row][column]))
        if abs(rows[pivot][column]) < _SINGULAR * scales[column]:
            return None
        rows[column], rows[pivot] = rows[pivot], rows[column]
        for row in range(size):
            if row != column:
                factor = rows[row][column] / rows[column][column]
                rows[row] = [
                    a - factor * b for a, b in zip(rows[row], rows[column], strict=True)
                ]
    return [rows[index][size] / rows[index][index] for index in range(size)]


def _least_squares(
    points: list[tuple[float, float]], terms: int
) -> tuple[list[float], float] | None:
    """Fit y = a + b x (+ c x²): the coefficients and the sum of squares.

    x is scaled to 0..1 for the solve, so the squares stay close in size.
    """
    scale = max((abs(x) for x, _ in points), default=0.0) or 1.0
    scaled = [(x / scale, y) for x, y in points]
    powers = range(terms + 1)
    matrix = [[sum(u ** (i + j) for u, _ in scaled) for j in powers] for i in powers]
    vector = [sum(y * u**i for u, y in scaled) for i in powers]
    solved = _solve(matrix, vector)
    if solved is None:
        return None
    coefficients = [c / scale**i for i, c in enumerate(solved)]
    squares = sum(
        (y - sum(c * u**i for i, c in enumerate(solved))) ** 2 for u, y in scaled
    )
    return coefficients, squares


def _degrees(
    pairs: list[tuple[float, float]], base: float
) -> list[tuple[float, float]]:
    return [(max(0.0, base - outdoor), value) for outdoor, value in pairs]


def _fit(
    pairs: list[tuple[float, float]], base: float
) -> tuple[tuple[float, float, float, float], float, int] | None:
    """Fit the energy on the degree days under `base`.

    Returns (intercept, linear, square, reach), the sum of squares and the
    number of coefficients, None when no line fits (no day under the base). The
    curve is kept when the line rises, there are enough heating days, the curve
    keeps rising up to the coldest of them, and it fits clearly better than the
    line, its extra coefficient paid for.
    """
    points = _degrees(pairs, base)
    reach = max(x for x, _ in points)
    line = _least_squares(points, 1)
    if line is None:
        return None
    (intercept, linear), squares = line
    best = (intercept, linear, 0.0, reach), squares, 2
    if linear > 0 and sum(1 for x, _ in points if x > 0) >= _MIN_FIT_DAYS:
        curve = _least_squares(points, 2)
        if curve is not None:
            (intercept, linear, square), squares = curve
            if (
                linear >= 0
                and linear + 2 * square * reach > 0
                and _score(squares, len(points), 3) < _score(best[1], len(points), 2)
            ):
                best = (intercept, linear, square, reach), squares, 3
    return best


def _score(squares: float, count: int, terms: int) -> float:
    """Bayesian information criterion: the curve's extra coefficient has a cost."""
    return count * math.log(max(squares / count, _FLOOR)) + terms * math.log(count)


def _best_base(
    pairs: list[tuple[float, float]],
) -> tuple[float, tuple[float, float, float, float] | None, bool]:
    """Return the base where the heating starts, its fit, and whether days told it.

    Each base is scored with its own fit, and a curve's extra coefficient is
    paid for, so a base doesn't win only because a curve became possible there.
    Without days between 10 and 20 °C, every base fits alike and 18 °C stays.
    It also stays when no base gives heating that rises with the cold (its
    line is returned as it is), or when no other base fits clearly better.
    """
    low, high = _BASES[0], _BASES[-1]
    default = _fit(pairs, DEGREE_DAY_BASE)
    if not any(low < outdoor < high for outdoor, _ in pairs):
        return DEGREE_DAY_BASE, default[0] if default else None, False
    best: tuple[float, tuple[float, float, float, float], float] | None = None
    for base in (DEGREE_DAY_BASE, *_BASES):
        fitted = default if base == DEGREE_DAY_BASE else _fit(pairs, base)
        if fitted is None or fitted[0][1] <= 0:
            continue
        score = _score(fitted[1], len(pairs), fitted[2])
        # Clearly better only: bases that fit alike, up to rounding, keep 18 °C.
        if best is None or score < best[2] - 1e-6:
            best = base, fitted[0], score
    if best is None:
        return DEGREE_DAY_BASE, default[0] if default else None, False
    return best[0], best[1], True


def _tempo(
    entry: ElectricityContractsConfigEntry,
    contract: Contract,
    calendar: dict[date, TempoColor],
    recent: list[tuple[float, float]],
    today: date,
) -> dict[str, Any]:
    """Describe today, tomorrow and what is left of the Tempo season."""
    tomorrow = today + timedelta(days=1)
    color = calendar.get(tomorrow)

    # What the same day of the week consumed lately, in and out of peak hours.
    same_days: dict[date, list[float]] = {}
    for timestamp, energy in recent:
        local = _local(timestamp)
        if local.weekday() == tomorrow.weekday():
            split = same_days.setdefault(local.date(), [0.0, 0.0])
            split[0 if local.hour in _PEAK_HOURS else 1] += energy
    estimate: dict[str, Any] | None = None
    if same_days:
        peak = sum(split[0] for split in same_days.values()) / len(same_days)
        off_peak = sum(split[1] for split in same_days.values()) / len(same_days)
        periods = price_periods(
            contract,
            manual_prices(entry),
            entry.runtime_data.data.sources.official_prices,
        )
        period = next((item for item in periods if item.covers(tomorrow)), None)
        # What the day would cost in each color, until its color is published.
        costs = (
            {
                item.value: round(
                    peak * period.prices[Tranche(f"{item.value}_hp")]
                    + off_peak * period.prices[Tranche(f"{item.value}_hc")]
                    + period.fixed_per_year / 365,
                    2,
                )
                for item in TempoColor
            }
            if period is not None
            else None
        )
        estimate = {
            "energy": round(peak + off_peak, 3),
            "cost": costs[color.value] if costs and color is not None else None,
            "costs": costs,
        }

    first, last = season_bounds(season_of(today))
    placed = placed_days(calendar, today)
    return {
        "today": calendar[today].value if today in calendar else None,
        "tomorrow": color.value if color is not None else None,
        "tomorrow_estimate": estimate,
        "season": {
            "start": first.isoformat(),
            "end": last.isoformat(),
            "red_total": RED_DAYS,
            "red_left": max(0, RED_DAYS - placed.count(TempoColor.RED)),
            "white_total": WHITE_DAYS,
            "white_left": max(0, WHITE_DAYS - placed.count(TempoColor.WHITE)),
        },
    }
