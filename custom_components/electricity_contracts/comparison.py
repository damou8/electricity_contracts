"""Compare contracts over a window, from the cost statistics."""

import asyncio
import calendar
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Final

from elec_tariffs import Tranche, season_bounds, season_of
from homeassistant.components.recorder.statistics import statistic_during_period
from homeassistant.core import HomeAssistant
from homeassistant.helpers.recorder import get_instance

from .const import FRANCE_TIME_ZONE
from .data import Contract
from .statistics import CostingStatus, StatisticsWriter

_LOGGER = logging.getLogger(__name__)

WINDOW_FIXED: Final = "fixed"
WINDOW_LAST_12_MONTHS: Final = "last_12_months"
WINDOW_CURRENT_YEAR: Final = "current_year"
WINDOW_CURRENT_MONTH: Final = "current_month"
WINDOW_TEMPO_SEASON: Final = "tempo_season"
WINDOWS: Final = (
    WINDOW_LAST_12_MONTHS,
    WINDOW_CURRENT_YEAR,
    WINDOW_CURRENT_MONTH,
    WINDOW_TEMPO_SEASON,
    WINDOW_FIXED,
)

_HOUR = timedelta(hours=1)
_RECORDER_TIMEOUT = 60


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
        """What the best contract would have saved on the contracts in force."""
        best = self.best
        if best is None or self.actual is None or not self.actual.energy:
            return None
        # To the cent: equal totals must give 0, not a rounding error.
        return round(self.actual.total - best.total, 2) + 0.0


def day_start(day: date) -> datetime:
    """Return local midnight of a day, in UTC."""
    return datetime.combine(day, time(), FRANCE_TIME_ZONE).astimezone(UTC)


def window_days(
    window: str, today: date, start: date | None = None, end: date | None = None
) -> tuple[date, date]:
    """Return the first and last day of a window (both included)."""
    if window == WINDOW_FIXED:
        assert start is not None
        assert end is not None
        return start, end
    if window == WINDOW_CURRENT_YEAR:
        return date(today.year, 1, 1), date(today.year, 12, 31)
    if window == WINDOW_CURRENT_MONTH:
        last = calendar.monthrange(today.year, today.month)[1]
        return today.replace(day=1), today.replace(day=last)
    if window == WINDOW_TEMPO_SEASON:
        return season_bounds(season_of(today))
    # The last 12 months, today included.
    try:
        year_ago = today.replace(year=today.year - 1)
    except ValueError:  # 29 February
        year_ago = today.replace(year=today.year - 1, day=28)
    return year_ago + timedelta(days=1), today


async def async_wait_for_recorder(hass: HomeAssistant) -> None:
    """Wait until the recorder has written what was queued, at most a minute.

    Statistics are imported by the recorder's thread; reading them right after
    queuing an import would miss the new rows.
    """
    recorder = get_instance(hass)
    try:
        async with asyncio.timeout(_RECORDER_TIMEOUT):
            while future := recorder.async_get_commit_future():
                await future
    except TimeoutError:
        _LOGGER.debug("The recorder is still busy; totals may lag behind")


def _changes(
    hass: HomeAssistant, start: datetime, end: datetime, ids: list[str]
) -> dict[str, float]:
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
    available = data_end(status, contracts)
    if status.first_hour is not None:
        start = max(start, status.first_hour)
    end = min(end, available) if available is not None else start
    end = max(end, start)

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
        await get_instance(hass).async_add_executor_job(_changes, hass, start, end, ids)
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


def comparison_response(comparison: Comparison) -> dict[str, Any]:
    """Return a comparison as the response of the compare action."""

    def contract(item: ContractTotals) -> dict[str, Any]:
        return {
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
