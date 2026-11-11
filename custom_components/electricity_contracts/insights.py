"""What the consumption in force looked like over a window: days, hours, Tempo."""

from datetime import date, datetime, timedelta
from typing import Any

from elec_tariffs import ContractKind, TempoColor, Tranche, season_bounds, season_of
from homeassistant.core import HomeAssistant
from homeassistant.helpers.recorder import get_instance
from homeassistant.util import dt as dt_util

from .comparison import day_start, hourly_changes, narrow_window, read_changes
from .const import FRANCE_TIME_ZONE
from .coordinator import ElectricityContractsConfigEntry
from .data import Contract, contracts, manual_prices, price_periods

# RTE places at most this many days of each color in a season.
RED_DAYS = 22
WHITE_DAYS = 43
# Tempo's peak hours, also used to tell day from night for the other contracts.
_PEAK_HOURS = range(6, 22)
_ESTIMATE_WEEKS = 8


def _local(timestamp: float) -> datetime:
    return dt_util.utc_from_timestamp(timestamp).astimezone(FRANCE_TIME_ZONE)


def _tempo_in_force(entry_contracts: list[Contract], day: date) -> Contract | None:
    for contract in entry_contracts:
        if (
            contract.kind is ContractKind.TEMPO
            and contract.active_from is not None
            and contract.active_from <= day
            and (contract.active_to is None or contract.active_to >= day)
        ):
            return contract
    return None


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
        return {"days": [], "profile": [], "previous": None, "tempo": None}
    entry_contracts = contracts(entry)
    start, end = narrow_window(status, entry_contracts, start, end)
    ids = coordinator.costing.actual_statistics()
    costs = [ids.variable, ids.fixed]
    today = dt_util.now(FRANCE_TIME_ZONE).date()
    tempo = _tempo_in_force(entry_contracts, today)
    previous_start = start - (end - start)
    has_previous = (
        end > start
        and status.first_hour is not None
        and previous_start >= status.first_hour
    )

    def read() -> tuple[
        dict[str, list[tuple[float, float]]],
        dict[str, float] | None,
        list[tuple[float, float]],
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
        return hours, previous, recent

    hours, previous, recent = await get_instance(hass).async_add_executor_job(read)
    calendar = coordinator.data.sources.calendar

    days: dict[date, dict[str, float]] = {}
    profile = [[0.0, 0] for _ in range(24)]
    for timestamp, energy in hours.get(ids.energy, []):
        local = _local(timestamp)
        day = days.setdefault(local.date(), {"energy": 0.0, "peak": 0.0, "cost": 0.0})
        day["energy"] += energy
        if local.hour in _PEAK_HOURS:
            day["peak"] += energy
        profile[local.hour][0] += energy
        profile[local.hour][1] += 1
    for statistic_id in costs:
        for timestamp, cost in hours.get(statistic_id, []):
            if (costed := days.get(_local(timestamp).date())) is not None:
                costed["cost"] += cost

    return {
        "days": [
            {
                "date": day.isoformat(),
                "color": calendar[day].value if day in calendar else None,
                "energy": round(values["energy"], 3),
                "peak_energy": round(values["peak"], 3),
                "cost": round(values["cost"], 2),
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
    placed = [
        placed_color for day, placed_color in calendar.items() if first <= day <= last
    ]
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
