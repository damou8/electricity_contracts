"""Cost hours of consumption under each contract, and the actual cost.

Pure functions, without Home Assistant: they run in the executor.
"""

from bisect import bisect_left
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Literal

from elec_tariffs import (
    ContractRules,
    DayCalendar,
    HourCost,
    MissingColorError,
    MissingPriceError,
    PricePeriod,
    cost_hour,
    cost_hour_at_price,
)

from .const import FRANCE_TIME_ZONE


@dataclass(frozen=True, kw_only=True)
class Hour:
    """Consumption of the hour starting at `start` (UTC)."""

    start: datetime
    kwh: float


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


def hourly_rows(rows: Sequence[tuple[datetime, float]]) -> list[Hour]:
    """Keep the rows (start in UTC, kWh) that hold one hour.

    Daily rows aren't costed: how their consumption splits between off-peak and
    peak hours isn't known.
    """
    return [
        Hour(start=start, kwh=kwh)
        for (start, kwh), is_daily in zip(rows, _daily_rows(rows), strict=True)
        if not is_daily
    ]


def daily_totals(rows: Sequence[tuple[datetime, float]]) -> dict[date, float]:
    """Return the kWh of the rows (start in UTC, kWh) that hold a whole day.

    Keyed by the day, French time: what the Linky gave for the days without a
    load curve.
    """
    return {
        start.astimezone(FRANCE_TIME_ZONE).date(): kwh
        for (start, kwh), is_daily in zip(rows, _daily_rows(rows), strict=True)
        if is_daily
    }


@dataclass(frozen=True, kw_only=True)
class Waiting:
    """Why costing stopped: a Tempo color or a price not known yet."""

    reason: Literal["color", "price"]
    day: date


def in_force(day: date, active_from: date | None, active_to: date | None) -> bool:
    """Tell whether a contract in force from `active_from` to `active_to` was on `day`.

    Without `active_from`, the contract is only compared.
    """
    return (
        active_from is not None
        and active_from <= day
        and (active_to is None or day <= active_to)
    )


class SensorPrices:
    """The hourly prices of a sensor, from its first one.

    An hour before the sensor's first price isn't priced. An hour missing
    between two prices, while Home Assistant was off or the sensor unavailable,
    takes the price before it. An hour after the last price waits for it.
    """

    def __init__(
        self, prices: Mapping[datetime, float], first: datetime | None
    ) -> None:
        """Keep the prices by UTC start, and the start of the sensor's first one."""
        self._prices = dict(prices)
        self._hours = sorted(self._prices)
        self.first = first if first is not None or not self._hours else self._hours[0]

    def before_first(self, hour: datetime) -> bool:
        """Tell whether `hour` comes before the sensor's first price."""
        return self.first is not None and hour < self.first

    def at(self, hour: datetime) -> float | None:
        """Return the price of the hour starting at `hour`; None if it has none."""
        hour = hour.astimezone(UTC)
        if (price := self._prices.get(hour)) is not None:
            return price
        if not self._hours or self.before_first(hour) or hour > self._hours[-1]:
            return None
        index = bisect_left(self._hours, hour)
        # Without the price before, read too far back: the one after.
        return self._prices[self._hours[index - 1 if index else 0]]


@dataclass(frozen=True, kw_only=True)
class ContractInput:
    """What costing a contract needs."""

    uid: str
    rules: ContractRules
    periods: Sequence[PricePeriod]
    active_from: date | None
    active_to: date | None
    sensor_prices: SensorPrices | None = None
    """For a contract priced by a sensor: the price of each hour."""
    fixed_per_year: float = 0.0
    """For a contract priced by a sensor: its subscription."""

    def active_on(self, day: date) -> bool:
        """Tell whether the contract was in force on `day`."""
        return in_force(day, self.active_from, self.active_to)


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
    energy: float


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
        sensor = contract.sensor_prices
        price: float | None = None
        if sensor is not None:
            # Compared from the sensor's first price only.
            if sensor.before_first(hour.start):
                continue
            if (price := sensor.at(hour.start)) is None:
                return Costed(
                    costs=costs, waiting=Waiting(reason="price", day=local.date())
                )
        try:
            if price is None:
                costs[hour.start] = cost_hour(
                    local, hour.kwh, contract.rules, contract.periods, calendar
                )
            else:
                costs[hour.start] = cost_hour_at_price(
                    local,
                    hour.kwh,
                    contract.rules,
                    calendar,
                    price=price,
                    fixed_per_year=contract.fixed_per_year,
                )
        except MissingColorError as err:
            return Costed(costs=costs, waiting=Waiting(reason="color", day=err.day))
        except MissingPriceError as err:
            return Costed(costs=costs, waiting=Waiting(reason="price", day=err.day))
    return Costed(costs=costs)


def _before_sensor(contract: ContractInput, hour: Hour) -> bool:
    """Tell whether `hour` comes before the first price of a contract's sensor."""
    return contract.sensor_prices is not None and contract.sensor_prices.before_first(
        hour.start
    )


def cost_actual(
    contracts: Sequence[ContractInput],
    costed: Mapping[str, Costed],
    hours: Sequence[Hour],
) -> ActualCosted:
    """Cost each hour under the contract in force that day.

    Nothing when none was, or before the first price of its sensor.
    """
    costs: dict[datetime, ActualCost] = {}
    for hour in hours:
        day = hour.start.astimezone(FRANCE_TIME_ZONE).date()
        active = next(
            (contract for contract in contracts if contract.active_on(day)), None
        )
        if active is None or _before_sensor(active, hour):
            # No contract in force, or one priced by a sensor that had no
            # price yet: nothing is known of what the hour cost.
            costs[hour.start] = ActualCost(variable=0.0, fixed=0.0, energy=0.0)
            continue
        result = costed[active.uid]
        cost = result.costs.get(hour.start)
        if cost is None:
            return ActualCosted(costs=costs, waiting=result.waiting)
        costs[hour.start] = ActualCost(
            variable=sum(cost.variable.values()),
            fixed=cost.fixed,
            energy=sum(cost.energy.values()),
        )
    return ActualCosted(costs=costs)
