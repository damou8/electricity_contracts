"""What is ahead: the price over the next hours, and the bill of the season."""

from collections.abc import Mapping
from dataclasses import replace
from datetime import date, datetime, timedelta
from functools import partial
from typing import Any

from elec_tariffs import (
    TEMPO_OFF_PEAK,
    ContractKind,
    ContractRules,
    PricePeriod,
    TempoColor,
    Tranche,
    cost_hour,
    is_off_peak,
    season_bounds,
    season_of,
    tempo_day,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.recorder import get_instance
from homeassistant.util import dt as dt_util

from .comparison import (
    ActualTotals,
    covers,
    data_end,
    day_start,
    hourly_changes,
    read_changes,
)
from .const import FRANCE_TIME_ZONE
from .coordinator import ElectricityContractsConfigEntry
from .data import Contract, contracts, in_force, manual_prices, price_periods

# RTE places at most this many days of each color in a season.
RED_DAYS = 22
WHITE_DAYS = 43
# Red days fall on weekdays from November to March, white days on any day but
# Sunday. Bank holidays aren't left out.
_RED_MONTHS = (11, 12, 1, 2, 3)
_SATURDAY = 5
_SUNDAY = 6

_HOUR = timedelta(hours=1)
_HALF_HOUR = timedelta(minutes=30)
_TIMELINE = timedelta(hours=24)
# The same day of the week, a year before.
_YEAR_BEFORE = timedelta(days=364)
# Below this share of last year's hours, the rest of the season isn't projected.
_MIN_HISTORY = 0.9


def tranche_at(
    local: datetime, rules: ContractRules, calendar: Mapping[date, TempoColor]
) -> Tranche | None:
    """Return the tranche at a moment (French time), None if its color is unknown."""
    if rules.kind is ContractKind.BASE:
        return Tranche.BASE
    if rules.kind is ContractKind.HPHC:
        weekend = rules.weekend_off_peak and local.weekday() >= _SATURDAY
        if weekend or is_off_peak(local.time(), rules.off_peak):
            return Tranche.HC
        return Tranche.HP
    color = calendar.get(tempo_day(local))
    if color is None:
        return None
    part = "hc" if is_off_peak(local.time(), TEMPO_OFF_PEAK) else "hp"
    return Tranche(f"{color.value}_{part}")


def placed_days(calendar: Mapping[date, TempoColor], day: date) -> list[TempoColor]:
    """Return the colors already placed in the season of `day`."""
    first, last = season_bounds(season_of(day))
    return [color for placed, color in calendar.items() if first <= placed <= last]


async def async_outlook(
    hass: HomeAssistant, *, entry: ElectricityContractsConfigEntry
) -> dict[str, Any]:
    """Describe the price over the next 24 hours and the bill of the season."""
    now = dt_util.utcnow()
    today = now.astimezone(FRANCE_TIME_ZONE).date()
    contract = in_force(contracts(entry), today)
    if contract is None:
        return {"contract": None, "prices": [], "season": None}
    sources = entry.runtime_data.data.sources
    periods = price_periods(contract, manual_prices(entry), sources.official_prices)
    return {
        "contract": {"id": contract.uid, "name": contract.name},
        "prices": _timeline(now, contract.rules, periods, sources.calendar),
        "season": await _async_season(
            hass, entry=entry, contract=contract, periods=periods, today=today
        ),
    }


def _timeline(
    now: datetime,
    rules: ContractRules,
    periods: list[PricePeriod],
    calendar: Mapping[date, TempoColor],
) -> list[dict[str, Any]]:
    """Split the next 24 hours where the price changes, from now on.

    A tranche is None while its Tempo color isn't published, a price None when no
    price is known for the day.
    """
    moment = now.replace(minute=now.minute - now.minute % 30, second=0, microsecond=0)
    segments: list[dict[str, Any]] = []
    while moment < now + _TIMELINE:
        local = moment.astimezone(FRANCE_TIME_ZONE)
        tranche = tranche_at(local, rules, calendar)
        period = next((item for item in periods if item.covers(local.date())), None)
        price = period.prices.get(tranche) if tranche and period else None
        if (
            segments
            and segments[-1]["tranche"] == tranche
            and segments[-1]["price"] == price
        ):
            segments[-1]["end"] = moment + _HALF_HOUR
        else:
            segments.append(
                {
                    "start": max(moment, now),
                    "end": moment + _HALF_HOUR,
                    "tranche": tranche,
                    "price": price,
                }
            )
        moment += _HALF_HOUR
    return [
        {
            **segment,
            "start": segment["start"].astimezone(FRANCE_TIME_ZONE).isoformat(),
            "end": segment["end"].astimezone(FRANCE_TIME_ZONE).isoformat(),
            "tranche": segment["tranche"].value if segment["tranche"] else None,
        }
        for segment in segments
    ]


async def _async_season(
    hass: HomeAssistant,
    *,
    entry: ElectricityContractsConfigEntry,
    contract: Contract,
    periods: list[PricePeriod],
    today: date,
) -> dict[str, Any] | None:
    """Add what the season has cost so far to what the rest should cost.

    The rest of the season consumes like the same days a year before, at today's
    prices. Tempo's colors left go to the days that consumed the most.
    """
    coordinator = entry.runtime_data
    status = coordinator.data.costing
    entry_contracts = contracts(entry)
    available = data_end(status, entry_contracts)
    if status.actual is None or status.first_hour is None or available is None:
        return None
    first_day, last_day = season_bounds(season_of(today))
    season_start = day_start(first_day)
    season_end = day_start(last_day + timedelta(days=1))
    spent_start = max(season_start, status.first_hour)
    spent_end = max(min(available, season_end), spent_start)
    previous_first, previous_last = season_bounds(
        season_of(first_day - timedelta(days=1))
    )
    previous_start = day_start(previous_first)
    previous_end = day_start(previous_last + timedelta(days=1))
    actual = coordinator.costing.actual_statistics()
    energy_id = coordinator.costing.contract_statistics(
        contract.uid, contract.kind
    ).energy
    totals = [actual.variable, actual.fixed, actual.energy]

    def read() -> tuple[
        dict[str, float],
        dict[str, float] | None,
        dict[str, float] | None,
        list[tuple[float, float]],
    ]:
        spent = read_changes(hass, spent_start, spent_end, totals)
        previous = to_date = None
        if status.first_hour is not None and status.first_hour <= previous_start:
            previous = read_changes(
                hass, previous_start, previous_end, [*totals, energy_id]
            )
            to_date = read_changes(
                hass,
                previous_start,
                previous_start + (spent_end - season_start),
                totals,
            )
        history = hourly_changes(
            hass, spent_end - _YEAR_BEFORE, season_end - _YEAR_BEFORE, [energy_id]
        )[energy_id]
        return spent, previous, to_date, history

    spent, previous, to_date, history = await get_instance(hass).async_add_executor_job(
        read
    )
    projection = await hass.async_add_executor_job(
        partial(
            _project,
            contract,
            periods,
            coordinator.data.sources.calendar,
            history,
            start=spent_end,
            end=season_end,
            today=today,
        )
    )

    spent_cost = spent[actual.variable] + spent[actual.fixed]
    previous_total = None
    if (
        previous is not None
        and to_date is not None
        and covers(
            ActualTotals(
                energy=previous[actual.energy],
                variable=previous[actual.variable],
                fixed=previous[actual.fixed],
            ),
            previous[energy_id],
        )
    ):
        previous_total = {
            "total": round(previous[actual.variable] + previous[actual.fixed], 2),
            "to_date": round(to_date[actual.variable] + to_date[actual.fixed], 2),
        }
    return {
        "start": first_day.isoformat(),
        "end": last_day.isoformat(),
        "until": (spent_end - _HOUR).astimezone(FRANCE_TIME_ZONE).date().isoformat(),
        "complete": spent_start == season_start,
        "spent": {
            "cost": round(spent_cost, 2),
            "energy": round(spent[actual.energy], 3),
        },
        "projection": (
            {key: round(value, 2) for key, value in projection.items()}
            if projection is not None
            else None
        ),
        "total": (
            round(spent_cost + projection["cost"], 2)
            if projection is not None
            else None
        ),
        "previous": previous_total,
    }


def _project(  # noqa: PLR0913 - the contract, its data and the hours to project
    contract: Contract,
    periods: list[PricePeriod],
    calendar: Mapping[date, TempoColor],
    history: list[tuple[float, float]],
    *,
    start: datetime,
    end: datetime,
    today: date,
) -> dict[str, float] | None:
    """Cost the hours from `start` to `end` as they were consumed a year before.

    Return None when too few of those hours are known, or no price is known today.
    """
    period = next((item for item in periods if item.covers(today)), None)
    if period is None:
        return None
    hours: list[datetime] = []
    moment = start
    while moment < end:
        hours.append(moment.astimezone(FRANCE_TIME_ZONE))
        moment += _HOUR
    if (energy := _year_before(history, hours)) is None:
        return None
    # Today's prices for the rest of the season: the next ones aren't known.
    prices = [replace(period, start=min(period.start, today), end=None)]
    colors = dict(calendar)
    if contract.kind is ContractKind.TEMPO:
        colors.update(_place_colors(calendar, hours, energy, today))
    cost = 0.0
    for hour, kwh in zip(hours, energy, strict=True):
        cost += cost_hour(hour, kwh, contract.rules, prices, colors).total
    return {"cost": cost, "energy": sum(energy)}


def _year_before(
    history: list[tuple[float, float]], hours: list[datetime]
) -> list[float] | None:
    """Return what each hour (French time) consumed on the same day a year before.

    The few hours missing take the average of the same hour of the day; None when
    too many are missing.
    """

    def wall(moment: datetime) -> datetime:
        return moment.astimezone(FRANCE_TIME_ZONE).replace(tzinfo=None)

    before = {
        wall(dt_util.utc_from_timestamp(timestamp)) + _YEAR_BEFORE: energy
        for timestamp, energy in history
    }
    by_hour: dict[int, list[float]] = {}
    for hour in hours:
        if (value := before.get(wall(hour))) is not None:
            by_hour.setdefault(hour.hour, []).append(value)
    if sum(len(values) for values in by_hour.values()) < _MIN_HISTORY * len(hours):
        return None
    energy: list[float] = []
    for hour in hours:
        if (value := before.get(wall(hour))) is None:
            same = by_hour.get(hour.hour, [])
            value = sum(same) / len(same) if same else 0.0
        energy.append(value)
    return energy


def _place_colors(
    calendar: Mapping[date, TempoColor],
    hours: list[datetime],
    energy: list[float],
    today: date,
) -> dict[date, TempoColor]:
    """Give the red and white days left to the days that should consume the most."""
    by_day: dict[date, float] = {}
    for hour, kwh in zip(hours, energy, strict=True):
        day = tempo_day(hour)
        by_day[day] = by_day.get(day, 0.0) + kwh
    unknown = sorted(
        (day for day in by_day if day not in calendar),
        key=lambda day: by_day[day],
        reverse=True,
    )
    placed = placed_days(calendar, today)
    red_left = max(0, RED_DAYS - placed.count(TempoColor.RED))
    white_left = max(0, WHITE_DAYS - placed.count(TempoColor.WHITE))
    colors: dict[date, TempoColor] = {}
    for day in unknown:
        if red_left and day.weekday() < _SATURDAY and day.month in _RED_MONTHS:
            colors[day] = TempoColor.RED
            red_left -= 1
        elif white_left and day.weekday() != _SUNDAY:
            colors[day] = TempoColor.WHITE
            white_left -= 1
        else:
            colors[day] = TempoColor.BLUE
    return colors
