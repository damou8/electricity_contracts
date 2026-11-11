"""What the consumption in force looked like over a window: days, hours, Tempo."""

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
    narrow_window,
    read_changes,
)
from .const import CONF_TEMPERATURE, FRANCE_TIME_ZONE
from .coordinator import ElectricityContractsConfigEntry
from .data import Contract, contracts, in_force, manual_prices, price_periods
from .outlook import RED_DAYS, WHITE_DAYS, placed_days

# Tempo's peak hours, also used to tell day from night for the other contracts.
_PEAK_HOURS = range(6, 22)
_ESTIMATE_WEEKS = 8
# What keeps running: the lowest hour between 3:00 and 5:00 of the quiet nights.
_BASELOAD_HOURS = (3, 4)
_QUIET_NIGHTS = 0.1
_YEAR = timedelta(days=365)
_YEAR_HOURS = 8760
# Heating degree days count the degrees below 18 °C of each day's mean.
DEGREE_DAY_BASE = 18.0
_MIN_FIT_DAYS = 14


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
    if status.actual is None:
        return {
            "days": [],
            "profile": [],
            "previous": None,
            "tempo": None,
            "baseload": None,
            "weather": None,
        }
    entry_contracts = contracts(entry)
    start, end = narrow_window(status, entry_contracts, start, end)
    ids = coordinator.costing.actual_statistics()
    costs = [ids.variable, ids.fixed]
    today = dt_util.now(FRANCE_TIME_ZONE).date()
    contract = in_force(entry_contracts, today)
    tempo = contract if contract and contract.kind is ContractKind.TEMPO else None
    temperature_id: str | None = entry.options.get(CONF_TEMPERATURE)
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
        temperatures = (
            statistics_during_period(
                hass,
                start,
                end,
                {temperature_id},
                "hour",
                {"temperature": UnitOfTemperature.CELSIUS},
                {"mean"},
            ).get(temperature_id, [])
            if temperature_id and end > start
            else []
        )
        return hours, previous, recent, year, temperatures

    hours, previous, recent, year, temperatures = await get_instance(
        hass
    ).async_add_executor_job(read)
    calendar = coordinator.data.sources.calendar

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
    temperature = _daily_means(temperatures)

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
            _weather(days, temperature) if temperature_id is not None else None
        ),
    }


def _daily_means(rows: list[StatisticsRow]) -> dict[date, float]:
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


def _weather(
    days: dict[date, dict[str, float]], temperature: dict[date, float]
) -> dict[str, Any]:
    """Split the consumption between the cold and the rest.

    Each day's consumption is fitted as a straight line of its heating degree days:
    the slope is what a degree colder costs, the intercept what a day consumes
    without heating.
    """
    points = [
        (max(0.0, DEGREE_DAY_BASE - temperature[day]), values["energy"])
        for day, values in days.items()
        if day in temperature
    ]
    degree_days = sum(point[0] for point in points)
    energy = sum(point[1] for point in points)
    slope = intercept = share = None
    if len(points) >= _MIN_FIT_DAYS:
        mean_x = degree_days / len(points)
        mean_y = energy / len(points)
        variance = sum((x - mean_x) ** 2 for x, _ in points)
        if variance > 0:
            slope = sum((x - mean_x) * (y - mean_y) for x, y in points) / variance
            intercept = mean_y - slope * mean_x
            if slope > 0 and energy > 0:
                share = min(1.0, slope * degree_days / energy)
    return {
        "base": DEGREE_DAY_BASE,
        "days": len(points),
        "degree_days": round(degree_days, 1),
        "mean_temperature": (
            round(
                sum(temperature[day] for day in days if day in temperature)
                / len(points),
                1,
            )
            if points
            else None
        ),
        "slope": round(slope, 3) if slope is not None else None,
        "intercept": round(intercept, 2) if intercept is not None else None,
        "heating_share": round(share, 4) if share is not None else None,
    }


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
        estimate = {
            "energy": round(peak + off_peak, 3),
            "cost": (
                round(
                    peak * period.prices[Tranche(f"{color.value}_hp")]
                    + off_peak * period.prices[Tranche(f"{color.value}_hc")]
                    + period.fixed_per_year / 365,
                    2,
                )
                if color is not None and period is not None
                else None
            ),
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
