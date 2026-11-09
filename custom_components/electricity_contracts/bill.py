"""The bill a contract would have produced over a window."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from elec_tariffs import PricePeriod, Tranche
from homeassistant.core import HomeAssistant
from homeassistant.helpers.recorder import get_instance

from .comparison import ActualTotals, covers, day_start, narrow_window, read_changes
from .data import Contract
from .statistics import CostingStatus, StatisticsWriter


@dataclass(frozen=True, kw_only=True)
class BillLine:
    """The consumption of one tranche at one price."""

    tranche: Tranche
    energy: float
    price: float
    cost: float


@dataclass(frozen=True, kw_only=True)
class BillPeriod:
    """The part of a bill under one set of prices."""

    start: datetime
    end: datetime
    """First hour included and first hour excluded, in UTC."""
    fixed_per_year: float
    subscription: float
    lines: list[BillLine]


@dataclass(frozen=True, kw_only=True)
class Bill:
    """What a contract would have cost, line by line."""

    contract: Contract
    start: datetime
    end: datetime
    """First hour included and first hour excluded, in UTC."""
    periods: list[BillPeriod]
    actual: ActualTotals | None
    """What the contracts in force cost over the same hours, None unless one was in
    force at every hour."""

    @property
    def energy(self) -> float:
        """Energy billed, in kWh."""
        return sum(line.energy for period in self.periods for line in period.lines)

    @property
    def consumption(self) -> float:
        """Cost of the kWh."""
        return sum(line.cost for period in self.periods for line in period.lines)

    @property
    def subscription(self) -> float:
        """Cost of the subscription."""
        return sum(period.subscription for period in self.periods)

    @property
    def total(self) -> float:
        """What the bill comes to."""
        return self.consumption + self.subscription

    @property
    def difference(self) -> float | None:
        """How much more than the contracts in force it costs, None if unknown."""
        if self.actual is None:
            return None
        # From the totals to the cent, so the figures shown add up.
        return round(round(self.total, 2) - round(self.actual.total, 2), 2) + 0.0


async def async_bill(  # noqa: PLR0913 - the contract, its prices, the window, where to read
    hass: HomeAssistant,
    *,
    writer: StatisticsWriter,
    status: CostingStatus,
    contract: Contract,
    periods: list[PricePeriod],
    start: datetime,
    end: datetime,
) -> Bill:
    """Read what `contract` would have billed between `start` and `end` (UTC).

    The window is narrowed to the hours the contract and the actual cost have been
    costed for, then split where the prices change.
    """
    start, end = narrow_window(status, [contract], start, end)
    ids = writer.contract_statistics(contract.uid, contract.kind)
    windows: list[tuple[PricePeriod, datetime, datetime]] = []
    for period in periods:
        period_start = max(start, day_start(period.start))
        period_end = (
            min(end, day_start(period.end + timedelta(days=1))) if period.end else end
        )
        if period_end > period_start:
            windows.append((period, period_start, period_end))
    period_ids = [ids.fixed, *ids.tranche_energy.values(), *ids.tranche_cost.values()]
    actual_ids = (
        writer.actual_statistics()
        if status.actual is not None and end > start
        else None
    )

    def read() -> tuple[list[dict[str, float]], dict[str, float] | None]:
        changes = [
            read_changes(hass, window_start, window_end, period_ids)
            for _, window_start, window_end in windows
        ]
        actual = (
            read_changes(
                hass,
                start,
                end,
                [actual_ids.variable, actual_ids.fixed, actual_ids.energy],
            )
            if actual_ids is not None
            else None
        )
        return changes, actual

    changes, actual_changes = await get_instance(hass).async_add_executor_job(read)
    bill_periods = [
        BillPeriod(
            start=window_start,
            end=window_end,
            fixed_per_year=period.fixed_per_year,
            subscription=values[ids.fixed],
            lines=[
                BillLine(
                    tranche=tranche,
                    energy=values[ids.tranche_energy[tranche]],
                    price=period.prices[tranche],
                    cost=values[ids.tranche_cost[tranche]],
                )
                for tranche in ids.tranche_energy
            ],
        )
        for (period, window_start, window_end), values in zip(
            windows, changes, strict=True
        )
    ]
    actual = (
        ActualTotals(
            energy=actual_changes[actual_ids.energy],
            variable=actual_changes[actual_ids.variable],
            fixed=actual_changes[actual_ids.fixed],
        )
        if actual_ids is not None and actual_changes is not None
        else None
    )
    energy = sum(line.energy for period in bill_periods for line in period.lines)
    return Bill(
        contract=contract,
        start=start,
        end=end,
        periods=bill_periods,
        actual=actual if covers(actual, energy) else None,
    )
