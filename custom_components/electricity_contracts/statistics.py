"""Write the costs as long-term statistics, and rewrite them when needed.

Each contract gets, per tranche, an energy (kWh) and a cost statistic, plus its
subscription and its total cost. The actual cost follows the contract in force
each day. Statistics are external (`electricity_contracts:…`), hourly, and their
sums start at the first hour of consumption.

Statistics are only appended to, hour by hour. They are cleared and written again
when what they depend on changes: a contract's settings or prices, the activity
periods, the consumption source, or the source's past values (a Linky import
started again).
"""

import hashlib
import json
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from functools import partial
from typing import Any

from elec_tariffs import (
    TRANCHES,
    ContractKind,
    DayCalendar,
    HourCost,
    PricePeriod,
    Tranche,
)
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
    get_metadata,
    statistics_during_period,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.storage import Store
from homeassistant.util import slugify
from homeassistant.util.unit_conversion import EnergyConverter

from .const import CONF_STATISTIC_ID, DOMAIN
from .costing import (
    ActualCosted,
    ContractInput,
    Costed,
    Waiting,
    cost_actual,
    cost_contract,
    hourly_rows,
)
from .data import (
    Contract,
    contracts,
    format_time_range,
    manual_prices,
    price_periods,
)

_LOGGER = logging.getLogger(__name__)

# Bump to rewrite every statistic after a change in how costs are computed.
COSTING_VERSION = 3
STATE_VERSION = 1
ACTUAL = "actual"
_HOUR = timedelta(hours=1)
_EPOCH = datetime(2000, 1, 1, tzinfo=UTC)
# How far before the last hour written to read the source again, so that a daily
# row can be told from an hourly one by the rows around it.
_LOOKBACK = timedelta(days=2)

_NAMES: Mapping[str, Mapping[str, str]] = {
    "en": {
        "energy": "{contract} energy {tranche}",
        "cost": "{contract} cost {tranche}",
        "fixed": "{contract} subscription",
        "total": "{contract} total cost",
        "energy_total": "{contract} total energy",
        "actual": "Actual cost",
        "actual_fixed": "Actual subscription",
        "actual_energy": "Actual energy",
    },
    "fr": {
        "energy": "{contract} énergie {tranche}",
        "cost": "{contract} coût {tranche}",
        "fixed": "{contract} abonnement",
        "total": "{contract} coût total",
        "energy_total": "{contract} énergie totale",
        "actual": "Coût réel",
        "actual_fixed": "Abonnement réel",
        "actual_energy": "Énergie réelle",
    },
}
_TRANCHE_NAMES: Mapping[str, Mapping[Tranche, str]] = {
    "en": {
        Tranche.BASE: "base",
        Tranche.HC: "off-peak",
        Tranche.HP: "peak",
        Tranche.BLUE_HC: "blue off-peak",
        Tranche.BLUE_HP: "blue peak",
        Tranche.WHITE_HC: "white off-peak",
        Tranche.WHITE_HP: "white peak",
        Tranche.RED_HC: "red off-peak",
        Tranche.RED_HP: "red peak",
    },
    "fr": {
        Tranche.BASE: "base",
        Tranche.HC: "HC",
        Tranche.HP: "HP",
        Tranche.BLUE_HC: "Bleu HC",
        Tranche.BLUE_HP: "Bleu HP",
        Tranche.WHITE_HC: "Blanc HC",
        Tranche.WHITE_HP: "Blanc HP",
        Tranche.RED_HC: "Rouge HC",
        Tranche.RED_HP: "Rouge HP",
    },
}


@dataclass(frozen=True, kw_only=True)
class SeriesStatus:
    """How far a contract, or the actual cost, has been costed."""

    last_hour: datetime | None
    waiting: Waiting | None


@dataclass(frozen=True, kw_only=True)
class CostingStatus:
    """Progress of every series of an entry."""

    contracts: dict[str, SeriesStatus] = field(default_factory=dict)
    actual: SeriesStatus | None = None
    last_source_hour: datetime | None = None
    first_hour: datetime | None = None
    """First hour costed: hours before it only have daily totals, or nothing."""


@dataclass(frozen=True, kw_only=True)
class ContractStatistics:
    """IDs of the statistics of a contract."""

    total: str
    fixed: str
    energy: str
    tranche_energy: dict[Tranche, str]
    tranche_cost: dict[Tranche, str]


@dataclass(frozen=True, kw_only=True)
class ActualStatistics:
    """IDs of the actual cost statistics."""

    variable: str
    fixed: str
    energy: str


@dataclass(frozen=True, kw_only=True)
class _Statistic:
    statistic_id: str
    name: str
    energy: bool
    value: Callable[[Any], float]


@dataclass(frozen=True, kw_only=True)
class _Series:
    """Statistics written together, hour by hour."""

    key: str
    fingerprint: str
    statistics: tuple[_Statistic, ...]

    @property
    def ids(self) -> list[str]:
        return [statistic.statistic_id for statistic in self.statistics]


@dataclass(kw_only=True)
class _State:
    """What was written, kept between restarts."""

    source_object: str | None = None
    source_start: float | None = None
    source_sum: float | None = None
    first_hour: float | None = None
    series: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_store(cls, data: dict[str, Any] | None) -> _State:
        if not data:
            return cls()
        try:
            series = {
                str(key): {
                    "fingerprint": str(value["fingerprint"]),
                    "ids": [str(item) for item in value["ids"]],
                }
                for key, value in data["series"].items()
            }
            return cls(
                source_object=data["source_object"],
                source_start=data["source_start"],
                source_sum=data["source_sum"],
                first_hour=data.get("first_hour"),
                series=series,
            )
        except KeyError, TypeError, AttributeError:
            _LOGGER.warning("Ignoring an unreadable record of the written statistics")
            return cls()

    def to_store(self) -> dict[str, Any]:
        return {
            "source_object": self.source_object,
            "source_start": self.source_start,
            "source_sum": self.source_sum,
            "first_hour": self.first_hour,
            "series": self.series,
        }

    def all_ids(self) -> list[str]:
        return [item for series in self.series.values() for item in series["ids"]]


def statistics_store(hass: HomeAssistant, entry_id: str) -> Store[dict[str, Any]]:
    """Return the store that records which statistics an entry wrote."""
    return Store(hass, STATE_VERSION, f"{DOMAIN}.{entry_id}.statistics")


def _time(timestamp: float | None) -> datetime | None:
    return datetime.fromtimestamp(timestamp, UTC) if timestamp is not None else None


def _fingerprint(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _periods_value(periods: list[PricePeriod]) -> list[Any]:
    return [
        [
            period.start,
            period.end,
            period.fixed_per_year,
            sorted((str(tranche), price) for tranche, price in period.prices.items()),
        ]
        for period in periods
    ]


class StatisticsWriter:
    """Cost the consumption of one entry and keep its statistics up to date."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Prepare the statistics of an entry."""
        self.hass = hass
        self.entry = entry
        self.source_id: str = entry.data[CONF_STATISTIC_ID]
        self.prefix = f"{DOMAIN}:{slugify(self.source_id)}"
        self._store = statistics_store(hass, entry.entry_id)
        self._state = _State()
        self._recompute_all = False
        language = hass.config.language.split("-")[0]
        self._names = _NAMES.get(language, _NAMES["en"])
        self._tranche_names = _TRANCHE_NAMES.get(language, _TRANCHE_NAMES["en"])
        self._currency = hass.config.currency

    async def async_load(self) -> None:
        """Load what was written before."""
        self._state = _State.from_store(await self._store.async_load())

    def contract_statistics(self, uid: str, kind: ContractKind) -> ContractStatistics:
        """Return the statistic IDs of a contract."""
        base = f"{self.prefix}_{uid}"
        return ContractStatistics(
            total=f"{base}_cost",
            fixed=f"{base}_cost_fixed",
            energy=f"{base}_energy",
            tranche_energy={t: f"{base}_energy_{t}" for t in TRANCHES[kind]},
            tranche_cost={t: f"{base}_cost_{t}" for t in TRANCHES[kind]},
        )

    def actual_statistics(self) -> ActualStatistics:
        """Return the statistic IDs of the actual cost."""
        return ActualStatistics(
            variable=f"{self.prefix}_actual_cost",
            fixed=f"{self.prefix}_actual_cost_fixed",
            energy=f"{self.prefix}_actual_energy",
        )

    def request_recompute(self) -> None:
        """Clear and write every statistic again at the next update."""
        self._recompute_all = True

    async def async_update(
        self,
        official_prices: Mapping[tuple[ContractKind, int], list[PricePeriod]],
        calendar: DayCalendar,
    ) -> CostingStatus:
        """Cost the hours not costed yet; rewrite what is out of date first."""
        inputs, series = self._wanted(official_prices)
        await self._async_clear_outdated(series)
        if not series:
            self._state.source_object = self.prefix
            await self._store.async_save(self._state.to_store())
            return CostingStatus()

        resume: dict[str, tuple[datetime | None, dict[str, float]]] = {}
        for key, item in series.items():
            resume[key] = await self._async_resume_point(item)
        starts = [start for start, _ in resume.values()]
        fetch_from = (
            None if not starts or None in starts else min(s for s in starts if s)
        )
        source_rows, last_row = await self._async_source_rows(fetch_from)

        contract_inputs = [inputs[key] for key in inputs]
        costed, actual = await self.hass.async_add_executor_job(
            partial(
                _cost_all,
                contract_inputs,
                source_rows,
                dict(calendar),
                ACTUAL in series,
            )
        )

        status: dict[str, SeriesStatus] = {}
        for key, item in series.items():
            last_start, sums = resume[key]
            costs = actual if key == ACTUAL else costed[key]
            assert costs is not None
            written = self._write(item, costs, last_start, sums)
            if last_start is None and written is not None and costs.costs:
                first = min(costs.costs).timestamp()
                if self._state.first_hour is None or first < self._state.first_hour:
                    self._state.first_hour = first
            status[key] = SeriesStatus(
                last_hour=written or last_start, waiting=costs.waiting
            )
            self._state.series[key] = {"fingerprint": item.fingerprint, "ids": item.ids}

        self._state.source_object = self.prefix
        if last_row is not None:
            self._state.source_start, self._state.source_sum = last_row
        await self._store.async_save(self._state.to_store())
        return CostingStatus(
            contracts={key: value for key, value in status.items() if key != ACTUAL},
            actual=status.get(ACTUAL),
            last_source_hour=_time(self._state.source_start),
            first_hour=_time(self._state.first_hour),
        )

    def _wanted(
        self, official_prices: Mapping[tuple[ContractKind, int], list[PricePeriod]]
    ) -> tuple[dict[str, ContractInput], dict[str, _Series]]:
        entry_contracts = contracts(self.entry)
        manual = manual_prices(self.entry)
        inputs: dict[str, ContractInput] = {}
        series: dict[str, _Series] = {}
        fingerprints: dict[str, str] = {}
        for contract in entry_contracts:
            periods = price_periods(contract, manual, official_prices)
            inputs[contract.uid] = ContractInput(
                uid=contract.uid,
                rules=contract.rules,
                periods=periods,
                active_from=contract.active_from,
                active_to=contract.active_to,
            )
            fingerprints[contract.uid] = self._contract_fingerprint(contract, periods)
            series[contract.uid] = self._contract_series(
                contract, fingerprints[contract.uid]
            )
        active = [contract for contract in entry_contracts if contract.active_from]
        if active:
            fingerprint = _fingerprint(
                {
                    "version": COSTING_VERSION,
                    "names": self._names["actual"],
                    "currency": self._currency,
                    "contracts": [
                        [c.uid, c.active_from, c.active_to, fingerprints[c.uid]]
                        for c in active
                    ],
                }
            )
            ids = self.actual_statistics()
            series[ACTUAL] = _Series(
                key=ACTUAL,
                fingerprint=fingerprint,
                statistics=(
                    _Statistic(
                        statistic_id=ids.variable,
                        name=self._names["actual"],
                        energy=False,
                        value=lambda cost: cost.variable,
                    ),
                    _Statistic(
                        statistic_id=ids.fixed,
                        name=self._names["actual_fixed"],
                        energy=False,
                        value=lambda cost: cost.fixed,
                    ),
                    _Statistic(
                        statistic_id=ids.energy,
                        name=self._names["actual_energy"],
                        energy=True,
                        value=lambda cost: cost.energy,
                    ),
                ),
            )
        return inputs, series

    def _contract_fingerprint(
        self, contract: Contract, periods: list[PricePeriod]
    ) -> str:
        return _fingerprint(
            {
                "version": COSTING_VERSION,
                "name": contract.name,
                "names": self._names["energy"],
                "currency": self._currency,
                "kind": contract.kind,
                "off_peak": [format_time_range(r) for r in contract.rules.off_peak],
                "weekend": contract.rules.weekend_off_peak,
                "periods": _periods_value(periods),
            }
        )

    def _contract_series(self, contract: Contract, fingerprint: str) -> _Series:
        ids = self.contract_statistics(contract.uid, contract.kind)
        name = contract.name
        statistics: list[_Statistic] = []
        for tranche in TRANCHES[contract.kind]:
            tranche_name = self._tranche_names[tranche]
            statistics.append(
                _Statistic(
                    statistic_id=ids.tranche_energy[tranche],
                    name=self._names["energy"].format(
                        contract=name, tranche=tranche_name
                    ),
                    energy=True,
                    value=partial(_tranche_value, "energy", tranche),
                )
            )
            statistics.append(
                _Statistic(
                    statistic_id=ids.tranche_cost[tranche],
                    name=self._names["cost"].format(
                        contract=name, tranche=tranche_name
                    ),
                    energy=False,
                    value=partial(_tranche_value, "variable", tranche),
                )
            )
        statistics.extend(
            (
                _Statistic(
                    statistic_id=ids.energy,
                    name=self._names["energy_total"].format(contract=name),
                    energy=True,
                    value=lambda cost: sum(cost.energy.values()),
                ),
                _Statistic(
                    statistic_id=ids.fixed,
                    name=self._names["fixed"].format(contract=name),
                    energy=False,
                    value=lambda cost: cost.fixed,
                ),
                # Last: where the series stopped is read from it.
                _Statistic(
                    statistic_id=ids.total,
                    name=self._names["total"].format(contract=name),
                    energy=False,
                    value=lambda cost: cost.total,
                ),
            )
        )
        return _Series(
            key=contract.uid, fingerprint=fingerprint, statistics=tuple(statistics)
        )

    async def _async_clear_outdated(self, series: Mapping[str, _Series]) -> None:
        state = self._state
        to_clear: list[str] = []
        if (
            self._recompute_all
            or state.source_object != self.prefix
            or await self._async_source_rewritten()
        ):
            if state.series:
                _LOGGER.info("Writing every statistic of %s again", self.entry.title)
            to_clear.extend(state.all_ids())
            state.series = {}
            state.source_start = state.source_sum = state.first_hour = None
            self._recompute_all = False
        for key in list(state.series):
            wanted = series.get(key)
            if wanted is None or wanted.fingerprint != state.series[key]["fingerprint"]:
                to_clear.extend(state.series.pop(key)["ids"])
        for key, item in series.items():
            if key not in state.series:
                # Statistics left by an earlier installation would mix with new ones.
                to_clear.extend(item.ids)
        await self._async_clear(sorted(set(to_clear)))

    async def _async_source_rewritten(self) -> bool:
        """Tell whether the source changed at the last hour costed before."""
        state = self._state
        if state.source_start is None or state.source_sum is None:
            return False
        start = datetime.fromtimestamp(state.source_start, UTC)
        rows = await get_instance(self.hass).async_add_executor_job(
            statistics_during_period,
            self.hass,
            start,
            start + _HOUR,
            {self.source_id},
            "hour",
            None,
            {"sum"},
        )
        series = rows.get(self.source_id)
        current = series[0].get("sum") if series else None
        if current is None:
            return True
        return abs(current - state.source_sum) > 1e-6 * max(1.0, abs(state.source_sum))

    async def _async_clear(self, ids: list[str]) -> None:
        if not ids:
            return
        done = self.hass.loop.create_future()

        def _set_done() -> None:
            if not done.done():
                done.set_result(None)

        def _on_done() -> None:
            # Called from the recorder's thread.
            self.hass.loop.call_soon_threadsafe(_set_done)

        get_instance(self.hass).async_clear_statistics(ids, on_done=_on_done)
        await done

    async def _async_resume_point(
        self, series: _Series
    ) -> tuple[datetime | None, dict[str, float]]:
        """Return the last hour written and the sums of the series there."""
        if series.key not in self._state.series:
            return None, {}
        recorder = get_instance(self.hass)
        main = series.statistics[-1].statistic_id
        last = await recorder.async_add_executor_job(
            lambda: get_last_statistics(
                self.hass, 1, main, convert_units=False, types={"sum"}
            )
        )
        if not last.get(main):
            return None, {}
        start = datetime.fromtimestamp(last[main][0]["start"], UTC)
        rows = await recorder.async_add_executor_job(
            statistics_during_period,
            self.hass,
            start,
            start + _HOUR,
            set(series.ids),
            "hour",
            None,
            {"sum"},
        )
        sums: dict[str, float] = {}
        for statistic_id in series.ids:
            found = rows.get(statistic_id)
            if found and (value := found[0].get("sum")) is not None:
                sums[statistic_id] = value
        if len(sums) != len(series.ids):
            _LOGGER.warning("Writing the statistics of %s again", series.key)
            await self._async_clear(series.ids)
            return None, {}
        return start, sums

    async def _async_source_rows(
        self, after: datetime | None
    ) -> tuple[list[tuple[datetime, float]], tuple[float, float] | None]:
        """Return the source rows (start, kWh) and the last row (start, sum).

        Rows start a while before `after` (from the first row if None), so that
        daily rows can be recognised.
        """
        recorder = get_instance(self.hass)
        metadata = await recorder.async_add_executor_job(
            lambda: get_metadata(self.hass, statistic_ids={self.source_id})
        )
        if self.source_id not in metadata:
            return [], None
        unit = metadata[self.source_id][1]["unit_of_measurement"]
        convert = EnergyConverter.converter_factory(unit, UnitOfEnergy.KILO_WATT_HOUR)
        start = after - _LOOKBACK if after else _EPOCH
        rows = await recorder.async_add_executor_job(
            statistics_during_period,
            self.hass,
            start,
            None,
            {self.source_id},
            "hour",
            None,
            {"change", "sum"},
        )
        series = rows.get(self.source_id, [])
        values = [
            (datetime.fromtimestamp(row["start"], UTC), convert(change))
            for row in series
            if (change := row.get("change")) is not None
        ]
        last_row: tuple[float, float] | None = None
        if series and (last_sum := series[-1].get("sum")) is not None:
            last_row = (series[-1]["start"], last_sum)
        return values, last_row

    def _write(
        self,
        series: _Series,
        costs: Costed | ActualCosted,
        last_start: datetime | None,
        sums: dict[str, float],
    ) -> datetime | None:
        """Add the rows after `last_start`; return the last hour written."""
        totals = {
            item.statistic_id: sums.get(item.statistic_id, 0.0)
            for item in series.statistics
        }
        rows: dict[str, list[StatisticData]] = {
            item.statistic_id: [] for item in series.statistics
        }
        written: datetime | None = None
        for start, cost in costs.costs.items():
            if last_start is not None and start <= last_start:
                continue
            for item in series.statistics:
                value = item.value(cost)
                totals[item.statistic_id] += value
                rows[item.statistic_id].append(
                    StatisticData(
                        start=start, state=value, sum=totals[item.statistic_id]
                    )
                )
            written = start
        if written is None:
            return None
        for item in series.statistics:
            async_add_external_statistics(
                self.hass, self._metadata(item), rows[item.statistic_id]
            )
        return written

    def _metadata(self, statistic: _Statistic) -> StatisticMetaData:
        return StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=statistic.name,
            source=DOMAIN,
            statistic_id=statistic.statistic_id,
            unit_class=EnergyConverter.UNIT_CLASS if statistic.energy else None,
            unit_of_measurement=(
                UnitOfEnergy.KILO_WATT_HOUR if statistic.energy else self._currency
            ),
        )


def _tranche_value(table: str, tranche: Tranche, cost: HourCost) -> float:
    values: dict[Tranche, float] = getattr(cost, table)
    return values.get(tranche, 0.0)


def _cost_all(
    inputs: list[ContractInput],
    rows: list[tuple[datetime, float]],
    calendar: DayCalendar,
    with_actual: bool,  # noqa: FBT001 - called through partial
) -> tuple[dict[str, Costed], ActualCosted | None]:
    hours = hourly_rows(rows)
    costed = {item.uid: cost_contract(item, hours, calendar) for item in inputs}
    actual = cost_actual(inputs, costed, hours) if with_actual else None
    return costed, actual


async def async_remove_statistics(hass: HomeAssistant, entry_id: str) -> None:
    """Clear the statistics an entry wrote and forget them."""
    store = statistics_store(hass, entry_id)
    state = _State.from_store(await store.async_load())
    if ids := state.all_ids():
        get_instance(hass).async_clear_statistics(ids)
    await store.async_remove()
