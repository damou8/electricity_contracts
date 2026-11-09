"""Compare contracts over a window, from the cost statistics."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Literal

from elec_tariffs import Tranche
from homeassistant.components.recorder.statistics import (
    statistic_during_period,
    statistics_during_period,
)
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers.recorder import get_instance
from homeassistant.util import dt as dt_util

from .const import FRANCE_TIME_ZONE
from .data import Contract
from .statistics import CostingStatus, StatisticsWriter

_HOUR = timedelta(hours=1)
_RECORDER_TIMEOUT = 60
# kWh: the same hours summed through different statistics.
_ENERGY_TOLERANCE = 0.001


@dataclass(frozen=True, kw_only=True)
class ContractTotals:
    """What a contract cost over a window."""

    contract: Contract
    energy: float
    variable: float
    fixed: float
    tranches: dict[Tranche, tuple[float, float]] | None
    """kWh and cost of each tranche, when asked for."""

    @property
    def total(self) -> float:
        """Variable and fixed cost."""
        return self.variable + self.fixed

    @property
    def average_price(self) -> float | None:
        """Total cost per kWh, None without consumption."""
        return self.total / self.energy if self.energy else None


@dataclass(frozen=True, kw_only=True)
class ActualTotals:
    """What the contracts in force cost over a window."""

    energy: float
    variable: float
    fixed: float

    @property
    def total(self) -> float:
        """Variable and fixed cost."""
        return self.variable + self.fixed

    @property
    def average_price(self) -> float | None:
        """Total cost per kWh, None without consumption."""
        return self.total / self.energy if self.energy else None


@dataclass(frozen=True, kw_only=True)
class Comparison:
    """Contracts compared over the same hours."""

    start: datetime
    end: datetime
    """First hour included and first hour excluded, in UTC."""
    contracts: list[ContractTotals]
    actual: ActualTotals | None

    @property
    def best(self) -> ContractTotals | None:
        """The cheapest contract, None if nothing was consumed."""
        candidates = [item for item in self.contracts if item.energy]
        return min(candidates, key=lambda item: item.total) if candidates else None

    @property
    def saving(self) -> float | None:
        """What the best contract would have saved on the contracts in force.

        None unless a contract was in force at every hour: hours without one cost
        nothing in the actual totals.
        """
        best = self.best
        if best is None or not covers(self.actual, best.energy):
            return None
        assert self.actual is not None
        # From the totals to the cent, so the figures shown add up and equal totals
        # give 0, not a rounding error.
        return round(round(self.actual.total, 2) - round(best.total, 2), 2) + 0.0


def covers(actual: ActualTotals | None, energy: float) -> bool:
    """Tell whether a contract was in force at every hour that consumed `energy`."""
    return actual is not None and abs(actual.energy - energy) <= _ENERGY_TOLERANCE


def day_start(day: date) -> datetime:
    """Return local midnight of a day, in UTC."""
    return datetime.combine(day, time(), FRANCE_TIME_ZONE).astimezone(UTC)


async def async_wait_for_recorder(hass: HomeAssistant) -> bool:
    """Wait until the recorder has written what was queued, at most a minute.

    Statistics are imported by the recorder's thread; reading them right after
    queuing an import would miss the new rows. The recorder runs its queue in
    order, so one commit after the imports is enough: waiting until nothing is
    pending would never end while events keep coming.

    The recorder only commits once Home Assistant has started: waiting during
    startup would hold it up for nothing, as nothing is queued yet from before.

    Return False if the recorder is still busy.
    """
    if hass.state is not CoreState.running:
        return True
    if (future := get_instance(hass).async_get_commit_future()) is None:
        return True
    try:
        async with asyncio.timeout(_RECORDER_TIMEOUT):
            await future
    except TimeoutError:
        return False
    return True


def read_changes(
    hass: HomeAssistant, start: datetime, end: datetime, ids: list[str]
) -> dict[str, float]:
    """Read how much each statistic grew between `start` and `end` (UTC).

    Run it in the recorder's executor.
    """
    changes: dict[str, float] = {}
    for statistic_id in ids:
        result = statistic_during_period(
            hass, start, end, statistic_id, {"change"}, None
        )
        changes[statistic_id] = result.get("change") or 0.0
    return changes


def data_end(status: CostingStatus, contracts: Sequence[Contract]) -> datetime | None:
    """Return the end of the hours every contract (and the actual cost) covers."""
    lasts = [
        series.last_hour if (series := status.contracts.get(contract.uid)) else None
        for contract in contracts
    ]
    if status.actual is not None:
        lasts.append(status.actual.last_hour)
    if not lasts or None in lasts:
        return None
    return min(last for last in lasts if last is not None) + _HOUR


def narrow_window(
    status: CostingStatus,
    contracts: Sequence[Contract],
    start: datetime,
    end: datetime,
) -> tuple[datetime, datetime]:
    """Narrow a window to the hours every contract has been costed for."""
    available = data_end(status, contracts)
    if status.first_hour is not None:
        start = max(start, status.first_hour)
    end = min(end, available) if available is not None else start
    return start, max(end, start)


async def async_compare(  # noqa: PLR0913 - the window, the contracts and where to read
    hass: HomeAssistant,
    *,
    writer: StatisticsWriter,
    status: CostingStatus,
    contracts: Sequence[Contract],
    start: datetime,
    end: datetime,
    details: bool = False,
) -> Comparison:
    """Read what each contract cost between `start` and `end` (UTC).

    The window is narrowed to the hours every contract has been costed for, so
    the contracts are compared over the same consumption.
    """
    start, end = narrow_window(status, contracts, start, end)
    ids: list[str] = []
    contract_ids = {
        contract.uid: writer.contract_statistics(contract.uid, contract.kind)
        for contract in contracts
    }
    for item in contract_ids.values():
        ids.extend((item.total, item.fixed, item.energy))
        if details:
            ids.extend(item.tranche_energy.values())
            ids.extend(item.tranche_cost.values())
    actual_ids = writer.actual_statistics() if status.actual is not None else None
    if actual_ids is not None:
        ids.extend((actual_ids.variable, actual_ids.fixed, actual_ids.energy))
    changes = (
        await get_instance(hass).async_add_executor_job(
            read_changes, hass, start, end, ids
        )
        if end > start
        else dict.fromkeys(ids, 0.0)
    )

    totals: list[ContractTotals] = []
    for contract in contracts:
        item = contract_ids[contract.uid]
        total = changes[item.total]
        fixed = changes[item.fixed]
        totals.append(
            ContractTotals(
                contract=contract,
                energy=changes[item.energy],
                variable=total - fixed,
                fixed=fixed,
                tranches=(
                    {
                        tranche: (
                            changes[item.tranche_energy[tranche]],
                            changes[item.tranche_cost[tranche]],
                        )
                        for tranche in item.tranche_energy
                    }
                    if details
                    else None
                ),
            )
        )
    actual = (
        ActualTotals(
            energy=changes[actual_ids.energy],
            variable=changes[actual_ids.variable],
            fixed=changes[actual_ids.fixed],
        )
        if actual_ids is not None
        else None
    )
    return Comparison(start=start, end=end, contracts=totals, actual=actual)


type GroupBy = Literal["day", "month"]


@dataclass(frozen=True, kw_only=True)
class Bucket:
    """What the contracts cost over a day or a month."""

    start: date
    energy: float
    contracts: dict[str, float]
    """Total cost of each contract, by uid."""
    actual: float | None
    """Total cost of the contracts in force, None unless one was in force at every
    hour."""


def _bucket(day: date, group_by: GroupBy) -> date:
    return day.replace(day=1) if group_by == "month" else day


def _hourly_changes(
    hass: HomeAssistant, start: datetime, end: datetime, ids: list[str]
) -> dict[str, list[tuple[float, float]]]:
    rows = statistics_during_period(
        hass, start, end, set(ids), "hour", None, {"change"}
    )
    return {
        statistic_id: [
            (row["start"], row.get("change") or 0.0)
            for row in rows.get(statistic_id, [])
        ]
        for statistic_id in ids
    }


async def async_series(
    hass: HomeAssistant,
    *,
    writer: StatisticsWriter,
    comparison: Comparison,
    group_by: GroupBy,
) -> list[Bucket]:
    """Split a comparison into days or months, French time, with none missing."""
    contracts = [item.contract for item in comparison.contracts]
    if not contracts or comparison.end <= comparison.start:
        return []
    totals = {
        contract.uid: writer.contract_statistics(contract.uid, contract.kind).total
        for contract in contracts
    }
    # Every contract costs the same consumption.
    energy_id = writer.contract_statistics(contracts[0].uid, contracts[0].kind).energy
    ids = [*totals.values(), energy_id]
    actual_ids = writer.actual_statistics() if comparison.actual is not None else None
    if actual_ids is not None:
        ids.extend((actual_ids.variable, actual_ids.fixed, actual_ids.energy))
    hourly = await get_instance(hass).async_add_executor_job(
        _hourly_changes, hass, comparison.start, comparison.end, ids
    )

    first = comparison.start.astimezone(FRANCE_TIME_ZONE).date()
    last = (comparison.end - _HOUR).astimezone(FRANCE_TIME_ZONE).date()
    sums: dict[date, dict[str, float]] = {}
    for offset in range((last - first).days + 1):
        sums.setdefault(
            _bucket(first + timedelta(days=offset), group_by), dict.fromkeys(ids, 0.0)
        )
    for statistic_id, rows in hourly.items():
        for hour, change in rows:
            day = dt_util.utc_from_timestamp(hour).astimezone(FRANCE_TIME_ZONE).date()
            sums[_bucket(day, group_by)][statistic_id] += change

    buckets: list[Bucket] = []
    for bucket_start, values in sums.items():
        actual = (
            ActualTotals(
                energy=values[actual_ids.energy],
                variable=values[actual_ids.variable],
                fixed=values[actual_ids.fixed],
            )
            if actual_ids is not None
            else None
        )
        buckets.append(
            Bucket(
                start=bucket_start,
                energy=values[energy_id],
                contracts={uid: values[total] for uid, total in totals.items()},
                actual=(
                    actual.total
                    if actual is not None and covers(actual, values[energy_id])
                    else None
                ),
            )
        )
    return buckets


def comparison_response(comparison: Comparison) -> dict[str, Any]:
    """Return a comparison as the response of the compare action."""

    def contract(item: ContractTotals) -> dict[str, Any]:
        return {
            "id": item.contract.uid,
            "name": item.contract.name,
            "kind": item.contract.kind.value,
            "energy": round(item.energy, 3),
            "variable_cost": round(item.variable, 2),
            "fixed_cost": round(item.fixed, 2),
            "total_cost": round(item.total, 2),
            "average_price": _round(item.average_price, 4),
            "tranches": {
                tranche.value: {"energy": round(energy, 3), "cost": round(cost, 2)}
                for tranche, (energy, cost) in (item.tranches or {}).items()
            },
        }

    best = comparison.best
    actual = comparison.actual
    return {
        "start": comparison.start.astimezone(FRANCE_TIME_ZONE).isoformat(),
        "end": comparison.end.astimezone(FRANCE_TIME_ZONE).isoformat(),
        "contracts": [contract(item) for item in comparison.contracts],
        "best": best.contract.name if best else None,
        "actual": (
            {
                "energy": round(actual.energy, 3),
                "variable_cost": round(actual.variable, 2),
                "fixed_cost": round(actual.fixed, 2),
                "total_cost": round(actual.total, 2),
                "average_price": _round(actual.average_price, 4),
            }
            if actual is not None
            else None
        ),
        "saving": _round(comparison.saving, 2),
    }


def _round(value: float | None, digits: int) -> float | None:
    return round(value, digits) if value is not None else None
