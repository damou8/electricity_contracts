"""Cost hours of consumption under each contract, and the actual cost.

Pure functions, without Home Assistant: they run in the executor.
"""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Literal

from elec_tariffs import (
    ContractRules,
    DayCalendar,
    DayShape,
    HourCost,
    MissingColorError,
    MissingPriceError,
    PricePeriod,
    cost_hour,
)

from .const import FRANCE_TIME_ZONE


@dataclass(frozen=True, kw_only=True)
class Hour:
    """Consumption of the hour starting at `start` (UTC)."""

    start: datetime
    kwh: float


_HOUR = timedelta(hours=1)


def _next_midnight(start: datetime) -> datetime:
    day = start.astimezone(FRANCE_TIME_ZONE).date() + timedelta(days=1)
    return datetime.combine(day, time(), FRANCE_TIME_ZONE).astimezone(UTC)


def _is_midnight(start: datetime) -> bool:
    local = start.astimezone(FRANCE_TIME_ZONE)
    return local.hour == 0 and local.minute == 0


def _daily_rows(rows: Sequence[tuple[datetime, float]]) -> list[bool]:
    """Tell which rows hold a whole day, as Linky meters without a load curve do.

    Such a row starts at local midnight and the next one at the next midnight. The
    last row is a daily one if it follows another daily one.
    """
    daily: list[bool] = []
    for index, (start, _) in enumerate(rows):
        if not _is_midnight(start):
            daily.append(False)
        elif index + 1 < len(rows):
            daily.append(rows[index + 1][0] == _next_midnight(start))
        else:
            daily.append(
                index > 0 and daily[-1] and _next_midnight(rows[index - 1][0]) == start
            )
    return daily


def _day_shape(
    rows: Sequence[tuple[datetime, float]], daily: Sequence[bool]
) -> DayShape:
    """Learn how days split between hours from the days whose hours are known."""
    days: dict[date, dict[int, float]] = defaultdict(dict)
    for (start, kwh), is_daily in zip(rows, daily, strict=True):
        if not is_daily:
            local = start.astimezone(FRANCE_TIME_ZONE)
            days[local.date()][local.hour] = kwh
    return DayShape.learn(
        {
            day: [values[hour] for hour in range(24)]
            for day, values in days.items()
            if len(values) == 24  # noqa: PLR2004 - hours in a day
        }
    )


def expand_rows(rows: Sequence[tuple[datetime, float]]) -> list[Hour]:
    """Turn statistic rows (start in UTC, kWh since the row before) into hours.

    A daily row is spread over its day with a shape learned from the days whose
    hours are known. A row after missing hours is spread evenly over them.
    """
    daily = _daily_rows(rows)
    shape = _day_shape(rows, daily) if any(daily) else DayShape.flat()
    hours: list[Hour] = []
    covered_until: datetime | None = None
    for (start, kwh), is_daily in zip(rows, daily, strict=True):
        if is_daily:
            end = _next_midnight(start)
            starts = [start + _HOUR * index for index in range((end - start) // _HOUR)]
            values = shape.spread(
                [item.astimezone(FRANCE_TIME_ZONE) for item in starts], kwh
            )
            hours.extend(
                Hour(start=item, kwh=value)
                for item, value in zip(starts, values, strict=True)
            )
            covered_until = end
            continue
        first = start
        if covered_until is not None and covered_until < start:
            first = covered_until
        count = (start - first) // _HOUR + 1
        hours.extend(
            Hour(start=first + _HOUR * index, kwh=kwh / count) for index in range(count)
        )
        covered_until = start + _HOUR
    return hours


@dataclass(frozen=True, kw_only=True)
class Waiting:
    """Why costing stopped: a Tempo color or a price not known yet."""

    reason: Literal["color", "price"]
    day: date


@dataclass(frozen=True, kw_only=True)
class ContractInput:
    """What costing a contract needs."""

    uid: str
    rules: ContractRules
    periods: Sequence[PricePeriod]
    active_from: date | None
    active_to: date | None

    def active_on(self, day: date) -> bool:
        """Tell whether the contract was in force on `day`."""
        return (
            self.active_from is not None
            and self.active_from <= day
            and (self.active_to is None or day <= self.active_to)
        )


@dataclass(frozen=True, kw_only=True)
class Costed:
    """Costs of consecutive hours, up to the first one that couldn't be costed."""

    costs: dict[datetime, HourCost] = field(default_factory=dict)
    waiting: Waiting | None = None


@dataclass(frozen=True, kw_only=True)
class ActualCost:
    """Variable and fixed cost of an hour under the contract in force."""

    variable: float
    fixed: float


@dataclass(frozen=True, kw_only=True)
class ActualCosted:
    """Actual costs of consecutive hours, up to the first one not known yet."""

    costs: dict[datetime, ActualCost] = field(default_factory=dict)
    waiting: Waiting | None = None


def cost_contract(
    contract: ContractInput, hours: Sequence[Hour], calendar: DayCalendar
) -> Costed:
    """Cost `hours` (in order) under a contract until data is missing."""
    costs: dict[datetime, HourCost] = {}
    for hour in hours:
        local = hour.start.astimezone(FRANCE_TIME_ZONE)
        try:
            costs[hour.start] = cost_hour(
                local, hour.kwh, contract.rules, contract.periods, calendar
            )
        except MissingColorError as err:
            return Costed(costs=costs, waiting=Waiting(reason="color", day=err.day))
        except MissingPriceError as err:
            return Costed(costs=costs, waiting=Waiting(reason="price", day=err.day))
    return Costed(costs=costs)


def cost_actual(
    contracts: Sequence[ContractInput],
    costed: Mapping[str, Costed],
    hours: Sequence[Hour],
) -> ActualCosted:
    """Cost each hour under the contract in force that day, nothing if none was."""
    costs: dict[datetime, ActualCost] = {}
    for hour in hours:
        day = hour.start.astimezone(FRANCE_TIME_ZONE).date()
        active = next(
            (contract for contract in contracts if contract.active_on(day)), None
        )
        if active is None:
            costs[hour.start] = ActualCost(variable=0.0, fixed=0.0)
            continue
        result = costed[active.uid]
        cost = result.costs.get(hour.start)
        if cost is None:
            return ActualCosted(costs=costs, waiting=result.waiting)
        costs[hour.start] = ActualCost(
            variable=sum(cost.variable.values()), fixed=cost.fixed
        )
    return ActualCosted(costs=costs)
