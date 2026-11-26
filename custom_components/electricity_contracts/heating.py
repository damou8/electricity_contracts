"""What heating used and cost over a window, and what a setting would cost."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from statistics import median
from typing import Any

from elec_tariffs import (
    MissingColorError,
    MissingPriceError,
    PricePeriod,
    TempoColor,
    cost_hour,
    cost_hour_at_price,
)
from homeassistant.components.recorder.statistics import (
    StatisticsRow,
    get_metadata,
    statistics_during_period,
)
from homeassistant.const import UnitOfEnergy, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.recorder import get_instance
from homeassistant.util import dt as dt_util

from .comparison import day_start, hourly_changes, narrow_window
from .const import CONF_WEATHER, FRANCE_TIME_ZONE
from .coordinator import ElectricityContractsConfigEntry
from .costing import hourly_rows
from .data import (
    Contract,
    Heating,
    contracts,
    gas_contracts,
    in_force,
    price_periods,
    source_statistic,
)
from .insights import DEGREE_DAY_BASE, daily_means, line_heating, weather_fit
from .prices import GasPricer, HourlyPrices, hourly_prices, price_entities
from .weather import outdoor_fill, outdoor_ids, outdoor_rows, outdoor_statistic

# kWh below which a day is taken as costed in full.
_UNCOSTED_TOLERANCE = 0.001
# A year back: the warm days hot water mixed with the heating is told from
# (enough of them to stand for a usual day), and the days an estimate before
# the heating statistics is fitted on.
_YEAR = timedelta(days=365)
_MIN_WARM_DAYS = 7


def _local(timestamp: float) -> datetime:
    return dt_util.utc_from_timestamp(timestamp).astimezone(FRANCE_TIME_ZONE)


@dataclass(kw_only=True)
class _Day:
    """What one day used, French time."""

    energy: float = 0.0
    cost: float = 0.0
    uncosted: float = 0.0
    """kWh with no cost: daily values, or hours whose price or color isn't known."""

    def add(self, cost: float | None, kwh: float) -> None:
        """Add the cost of `kwh`; None when they couldn't be costed."""
        if cost is None:
            self.uncosted += kwh
        else:
            self.cost += cost

    @property
    def priced(self) -> float | None:
        return self.cost if self.uncosted <= _UNCOSTED_TOLERANCE else None


@dataclass(kw_only=True)
class _Usage:
    """Days, hours of the day and tranches of one or several statistics."""

    days: dict[date, _Day] = field(default_factory=dict)
    hours: list[list[float]] = field(
        default_factory=lambda: [[0.0, 0] for _ in range(24)]
    )
    hourly_days: set[date] = field(default_factory=set)
    tranches: dict[str, list[float]] = field(default_factory=dict)

    def day(self, day: date) -> _Day:
        return self.days.setdefault(day, _Day())


class _Pricer:
    """Cost kWh at the prices of the contract in force, or of the gas contract."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ElectricityContractsConfigEntry,
        entry_contracts: list[Contract],
        hourly: HourlyPrices,
    ) -> None:
        sources = entry.runtime_data.data.sources
        self._calendar = sources.calendar
        self._contracts = entry_contracts
        self._hourly = hourly
        self._periods = {
            contract.uid: price_periods(hass, contract, sources.official_prices)
            for contract in entry_contracts
        }
        self._gas = GasPricer(hass, gas_contracts(entry), sources.gas_prices, hourly)

    def electricity(
        self, start: datetime, kwh: float
    ) -> dict[str, tuple[float, float]] | None:
        """Cost an hour of electricity; None if no price or color is known."""
        local = start.astimezone(FRANCE_TIME_ZONE)
        contract = in_force(self._contracts, local.date())
        if contract is None:
            return None
        try:
            if contract.entity is not None:
                sensor = self._hourly.get(contract.entity.entity_id)
                price = sensor.at(start) if sensor is not None else None
                if price is None:
                    return None
                cost = cost_hour_at_price(
                    local,
                    kwh,
                    contract.rules,
                    self._calendar,
                    price=price,
                    fixed_per_year=contract.entity.fixed_per_year,
                )
            else:
                cost = cost_hour(
                    local,
                    kwh,
                    contract.rules,
                    self._periods[contract.uid],
                    self._calendar,
                )
        except MissingColorError, MissingPriceError:
            return None
        return {
            tranche.value: (energy, cost.variable.get(tranche, 0.0))
            for tranche, energy in cost.energy.items()
        }

    def gas_hour(self, start: datetime, kwh: float) -> float | None:
        """Cost an hour of gas; None without a price that hour."""
        return self._gas.hour(start, kwh)

    def gas_day(self, day: date, kwh: float) -> float | None:
        """Cost gas only known for the whole day; None without a price that day."""
        return self._gas.day(day, kwh)

    def gas_fixed(self, day: date) -> float | None:
        """Return the day's share of the gas subscription."""
        return self._gas.fixed(day)

    def contract_today(self, today: date) -> tuple[Contract, PricePeriod] | None:
        """Return the contract in force today and its prices of the day."""
        contract = in_force(self._contracts, today)
        if contract is None:
            return None
        period = next(
            (item for item in self._periods[contract.uid] if item.covers(today)), None
        )
        return (contract, period) if period is not None else None

    def gas_today(self, today: date) -> float | None:
        """Return the price of a kWh of gas today."""
        return self._gas.today(today)


def _summed(
    rows_by_id: Iterable[list[tuple[datetime, float]]],
) -> tuple[dict[datetime, float], dict[datetime, float]]:
    """Sum several statistics' rows, hour by hour and day by day.

    Return the hourly rows and the daily ones (a whole day in one row), by start.
    """
    hourly: dict[datetime, float] = {}
    daily: dict[datetime, float] = {}
    for rows in rows_by_id:
        hours = {hour.start for hour in hourly_rows(rows)}
        for start, kwh in rows:
            target = hourly if start in hours else daily
            target[start] = target.get(start, 0.0) + kwh
    return hourly, daily


def _usage(
    rows_by_id: Iterable[list[tuple[datetime, float]]],
    *,
    gas: bool,
    pricer: _Pricer,
    subscription: bool = False,
) -> _Usage:
    """Count and cost what statistics used, by day, hour of the day and tranche.

    With `subscription`, each day of gas also costs its share of the gas
    subscription: the statistics are the main use of the gas.
    """
    usage = _Usage()
    hourly, daily = _summed(rows_by_id)
    for start, kwh in sorted(hourly.items()):
        local = start.astimezone(FRANCE_TIME_ZONE)
        day = usage.day(local.date())
        day.energy += kwh
        usage.hours[local.hour][0] += kwh
        usage.hourly_days.add(local.date())
        if gas:
            day.add(pricer.gas_hour(start, kwh), kwh)
            continue
        costed = pricer.electricity(start, kwh)
        if costed is None:
            day.uncosted += kwh
            continue
        for tranche, (energy, cost) in costed.items():
            day.cost += cost
            item = usage.tranches.setdefault(tranche, [0.0, 0.0])
            item[0] += energy
            item[1] += cost
    for start, kwh in daily.items():
        local = start.astimezone(FRANCE_TIME_ZONE)
        day = usage.day(local.date())
        day.energy += kwh
        day.add(pricer.gas_day(local.date(), kwh) if gas else None, kwh)
    if gas and subscription:
        for day_of, costed_day in usage.days.items():
            if (fixed := pricer.gas_fixed(day_of)) is not None:
                costed_day.cost += fixed
    for counted in usage.hours:
        counted[1] = len(usage.hourly_days)
    return usage


def _off_peak_share(tranches: dict[str, list[float]]) -> float | None:
    energy = sum(item[0] for item in tranches.values())
    if energy <= 0:
        return None
    return (
        sum(
            item[0]
            for tranche, item in tranches.items()
            if tranche == "hc" or tranche.endswith("_hc")
        )
        / energy
    )


def _names(
    hass: HomeAssistant, statistic_ids: Sequence[str], metadata: dict[str, Any]
) -> list[dict[str, str | None]]:
    """Name each statistic, with the area of its sensor when it has one."""
    entities = er.async_get(hass)
    areas = ar.async_get(hass)
    named: list[dict[str, str | None]] = []
    for statistic_id in statistic_ids:
        name = None
        if statistic_id in metadata:
            name = metadata[statistic_id][1]["name"]
        area = None
        if (entity := entities.async_get(statistic_id)) is not None:
            name = name or entity.name or entity.original_name
            area_id = entity.area_id
            if area_id is None and entity.device_id is not None:
                device = dr.async_get(hass).async_get(entity.device_id)
                area_id = device.area_id if device else None
            if area_id is not None and (found := areas.async_get_area(area_id)):
                area = found.name
        named.append({"id": statistic_id, "name": name or statistic_id, "area": area})
    return named


@dataclass(frozen=True, kw_only=True)
class _Read:
    """The rows a heating answer is made of."""

    energy: dict[str, list[StatisticsRow]]
    house: dict[str, list[tuple[float, float]]]
    temperatures: dict[str, list[StatisticsRow]]
    metadata: dict[str, Any]
    # Daily rows of the year before the window's end, when hot water is estimated.
    year_energy: dict[str, list[StatisticsRow]] = field(default_factory=dict)
    year_temperature: dict[str, list[StatisticsRow]] = field(default_factory=dict)
    # The hourly prices of the sensors contracts are priced by.
    prices: HourlyPrices = field(default_factory=dict)


@dataclass(kw_only=True)
class _Split:
    """The days of measured heating, its hot water taken out, and their totals."""

    days: list[dict[str, Any]] = field(default_factory=list)
    heating: float = 0.0
    heating_cost: float = 0.0
    water: float = 0.0
    water_cost: float = 0.0
    complete: bool = True


def _house(
    rows: dict[str, list[tuple[float, float]]], energy_id: str, cost_id: str
) -> tuple[dict[date, _Day], dict[datetime, float]]:
    """Return the source's consumption and variable cost by day, and its hours."""
    days: dict[date, _Day] = {}
    hours: dict[datetime, float] = {}
    for timestamp, energy in rows.get(energy_id, []):
        days.setdefault(_local(timestamp).date(), _Day()).energy += energy
        hours[datetime.fromtimestamp(timestamp, UTC)] = energy
    for timestamp, cost in rows.get(cost_id, []):
        days.setdefault(_local(timestamp).date(), _Day()).cost += cost
    return days, hours


def _water_of_day(
    day: date, item: _Day, water: _Usage | None, water_per_day: float | None
) -> tuple[float, float | None]:
    """Return the hot water of a day, measured or estimated, and its cost."""
    if water is not None:
        measured = water.days.get(day)
        return (measured.energy, measured.priced) if measured else (0.0, 0.0)
    if water_per_day is None:
        return 0.0, 0.0
    energy = min(item.energy, water_per_day)
    if item.priced is None or not item.energy:
        return energy, None
    return energy, item.priced * energy / item.energy


def _split(  # noqa: PLR0913 - the usage, its water and what each day is shown with
    usage: _Usage,
    *,
    water: _Usage | None,
    subtract: bool,
    water_per_day: float | None,
    temperatures: tuple[dict[date, float], dict[date, float]],
    house: dict[date, _Day],
    calendar: dict[date, TempoColor],
) -> _Split:
    """Take the hot water out of the heating, day by day, when it is inside."""
    outdoor, indoor = temperatures
    split = _Split()
    for day in sorted(usage.days):
        item = usage.days[day]
        water_energy, water_cost = _water_of_day(day, item, water, water_per_day)
        heat_energy = item.energy - (water_energy if subtract else 0.0)
        heat_cost: float | None = None
        if item.priced is not None and not (subtract and water_cost is None):
            heat_cost = item.priced - ((water_cost or 0.0) if subtract else 0.0)
        if heat_cost is None or water_cost is None:
            split.complete = False
        split.heating += heat_energy
        split.heating_cost += heat_cost or 0.0
        split.water += water_energy
        split.water_cost += water_cost or 0.0
        split.days.append(
            {
                "date": day.isoformat(),
                "color": calendar[day].value if day in calendar else None,
                "temperature": _round(outdoor.get(day), 1),
                "indoor": _round(indoor.get(day), 1),
                "heating": round(heat_energy, 3),
                "heating_cost": _round(heat_cost, 2),
                "water": round(water_energy, 3),
                "water_cost": _round(water_cost, 2),
                "house": round(house[day].energy, 3) if day in house else None,
            }
        )
    return split


def counted_days(
    outdoor: dict[date, float], house: dict[date, _Day]
) -> dict[date, float]:
    """Return the outdoor means of the days an estimate counts: those of the source."""
    return {day: temperature for day, temperature in outdoor.items() if day in house}


def _estimated(
    weather: dict[str, Any], outdoor: dict[date, float], house: dict[date, _Day]
) -> dict[str, Any]:
    """Estimate the heating in the source's consumption from its fit."""
    energy = sum(
        line_heating(weather, weather["base"] - temperature)
        for temperature in counted_days(outdoor, house).values()
    )
    house_energy = sum(item.energy for item in house.values())
    house_cost = sum(item.cost for item in house.values())
    price = house_cost / house_energy if house_energy > 0 else None
    return {
        "heating": round(energy, 3),
        "heating_cost": _round(energy * price, 2) if price is not None else None,
        "share": (
            round(min(1.0, energy / house_energy), 4) if house_energy > 0 else None
        ),
    }


def _tranches_of(
    hours: dict[datetime, float], pricer: _Pricer
) -> dict[str, list[float]]:
    """Count the kWh and cost of each tranche of the contract in force."""
    tranches: dict[str, list[float]] = {}
    for hour, kwh in hours.items():
        if (costed := pricer.electricity(hour, kwh)) is not None:
            for tranche, (energy, cost) in costed.items():
                item = tranches.setdefault(tranche, [0.0, 0.0])
                item[0] += energy
                item[1] += cost
    return tranches


class _Answer:
    """Build the answer of the heating command from what was read."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ElectricityContractsConfigEntry,
        read: _Read,
        house_ids: tuple[str, str] | None,
        heating: Heating,
    ) -> None:
        self._hass = hass
        self.heating = heating
        self.pricer = _Pricer(hass, entry, contracts(entry), read.prices)
        self.meter = source_statistic(entry) is not None
        self.calendar = entry.runtime_data.data.sources.calendar
        self.read = read
        self.entry = entry
        heating = self.heating
        # The sensor, and Open-Meteo before it.
        self.outdoor = (
            daily_means(outdoor_rows(entry, read.temperatures))
            if heating.outdoor
            else {}
        )
        indoor_rows = [
            row for item in heating.indoor for row in read.temperatures.get(item, [])
        ]
        self.indoor = daily_means(indoor_rows)
        values = [mean for row in indoor_rows if (mean := row.get("mean")) is not None]
        self.indoor_mean = sum(values) / len(values) if values else None
        self.house, self.house_hours = (
            _house(read.house, *house_ids) if house_ids else ({}, {})
        )

    def _water_per_day(self, warm_from: float) -> float | None:
        """Return what a warm day of the last year used, None without enough of them.

        A day is warm from `warm_from` outside. Read on the year rather than the
        window: a winter month has no day without heating.
        """
        outdoor = self.heating.outdoor
        if outdoor is None:
            return None
        temperatures = {
            _day_of(row["start"]): mean
            for row in outdoor_rows(self.entry, self.read.year_temperature)
            if (mean := row.get("mean")) is not None
        }
        energy: dict[date, float] = {}
        for statistic_id in self.heating.statistics:
            for row in self.read.year_energy.get(statistic_id, []):
                day = _day_of(row["start"])
                energy[day] = energy.get(day, 0.0) + (row.get("change") or 0.0)
        warm = [
            value
            for day, value in energy.items()
            if temperatures.get(day, -273.0) >= warm_from
        ]
        return median(warm) if len(warm) >= _MIN_WARM_DAYS else None

    def _rows(self, statistic_id: str) -> list[tuple[datetime, float]]:
        return [
            (datetime.fromtimestamp(row["start"], UTC), row.get("change") or 0.0)
            for row in self.read.energy.get(statistic_id, [])
        ]

    def build(self, today: date) -> dict[str, Any]:
        """Return the answer."""
        heating = self.heating
        house_energy = sum(item.energy for item in self.house.values())
        house_cost = sum(item.cost for item in self.house.values())
        if not heating.measured:
            fit_days = {
                day: {"energy": item.energy} for day, item in self.house.items()
            }
            weather = weather_fit(fit_days, self.outdoor) if heating.outdoor else None
            average = house_cost / house_energy if house_energy > 0 else None
            return self._answer(
                weather=weather,
                estimated=(
                    _estimated(weather, self.outdoor, self.house)
                    if weather is not None and _fitted(weather)
                    else None
                ),
                off_peak=_off_peak_share(_tranches_of(self.house_hours, self.pricer)),
                average=average,
                today=today,
            )

        # The gas subscription goes with the heating when it is gas, else with
        # the hot water.
        usage = _usage(
            [self._rows(item) for item in heating.statistics],
            gas=heating.gas,
            pricer=self.pricer,
            subscription=heating.gas,
        )
        water = (
            _usage(
                [self._rows(heating.water_statistic)],
                gas=heating.water_gas,
                pricer=self.pricer,
                subscription=heating.water_gas and not heating.gas,
            )
            if heating.water_statistic
            else None
        )
        # Water measured inside the heating statistics is taken out of them.
        inside = (
            water is not None
            and heating.with_water
            and heating.water_gas == heating.gas
        )
        fit_days = {
            day: {
                "energy": item.energy
                - (
                    water.days[day].energy
                    if inside and water and day in water.days
                    else 0.0
                )
            }
            for day, item in usage.days.items()
        }
        weather = weather_fit(fit_days, self.outdoor) if heating.outdoor else None
        # Hot water inside the heating statistics and not measured: what a day
        # without heating uses.
        # No heating from 18 °C, or from the fitted base when it is higher.
        warm_from = max(DEGREE_DAY_BASE, weather["base"] if weather else 0.0)
        water_per_day = (
            self._water_per_day(warm_from)
            if heating.with_water and water is None
            else None
        )
        split = _split(
            usage,
            water=water,
            subtract=inside or water_per_day is not None,
            water_per_day=water_per_day,
            temperatures=(self.outdoor, self.indoor),
            house=self.house,
            calendar=self.calendar,
        )
        # The water heater's own energy, or the heating's when inside it.
        water_gas = heating.water_gas if heating.water_statistic else heating.gas
        # Electric heating is a share of the source's electricity; gas heating, of
        # all the energy of the home, gas hot water included.
        # Without a meter, the rest of the home is unknown: no share.
        everything = (
            house_energy
            + (
                split.heating + (split.water if water_gas else 0.0)
                if heating.gas
                else 0.0
            )
            if self.meter
            else 0.0
        )
        average = (
            split.heating_cost / split.heating
            if split.complete and split.heating > 0
            else None
        )
        answer = self._answer(
            weather=weather,
            estimated=None,
            off_peak=_off_peak_share(
                _tranches_of(self.house_hours, self.pricer)
                if heating.gas
                else usage.tranches
            ),
            average=average,
            today=today,
        )
        answer.update(
            {
                "water_measured": water is not None,
                "water_split": water is not None or water_per_day is not None,
                "water_per_day": _round(water_per_day, 2),
                "water_warm_from": warm_from if water_per_day is not None else None,
                # The hot water is gas, outside the electricity bill.
                "water_gas": water_gas,
                "days": split.days,
                "statistics": [
                    {
                        **named,
                        "energy": round(
                            sum(kwh for _, kwh in self._rows(str(named["id"]))), 3
                        ),
                    }
                    for named in _names(
                        self._hass, heating.statistics, self.read.metadata
                    )
                ],
                "totals": {
                    "heating": round(split.heating, 3),
                    "heating_cost": (
                        round(split.heating_cost, 2) if split.complete else None
                    ),
                    "water": round(split.water, 3),
                    "water_cost": round(split.water_cost, 2)
                    if split.complete
                    else None,
                    "house": round(house_energy, 3),
                    "house_cost": round(house_cost, 2),
                    "share": (
                        round(split.heating / everything, 4) if everything > 0 else None
                    ),
                },
                "tranches": (
                    None
                    if heating.gas
                    else {
                        tranche: {
                            "energy": round(item[0], 3),
                            "cost": round(item[1], 2),
                        }
                        for tranche, item in usage.tranches.items()
                    }
                ),
                "profile": (
                    [
                        round(total / count, 4) if count else None
                        for total, count in usage.hours
                    ]
                    if usage.hourly_days
                    else None
                ),
            }
        )
        return answer

    def _answer(
        self,
        *,
        weather: dict[str, Any] | None,
        estimated: dict[str, Any] | None,
        off_peak: float | None,
        average: float | None,
        today: date,
    ) -> dict[str, Any]:
        heating = self.heating
        outdoor = list(self.outdoor.values())
        contract = None if heating.gas else self.pricer.contract_today(today)
        return {
            "measured": heating.measured,
            "gas": heating.gas,
            "with_water": heating.with_water or heating.water_statistic is not None,
            "water_measured": False,
            "water_split": False,
            "water_per_day": None,
            "water_warm_from": None,
            "has_outdoor": heating.outdoor is not None,
            "has_indoor": bool(heating.indoor),
            "days": [],
            "statistics": [],
            "totals": None,
            "estimated": estimated,
            "tranches": None,
            "profile": None,
            "weather": weather,
            "average_price": _round(average, 4),
            "simulator": {
                "indoor": _round(self.indoor_mean, 1),
                "outdoor": _round(sum(outdoor) / len(outdoor), 1) if outdoor else None,
                "off_peak_share": _round(off_peak, 4),
                "kind": contract[0].kind.value if contract else None,
                "prices": (
                    {
                        tranche.value: price
                        for tranche, price in contract[1].prices.items()
                    }
                    if contract
                    else None
                ),
                "gas_price": self.pricer.gas_today(today) if heating.gas else None,
            },
        }


def _fitted(weather: dict[str, Any] | None) -> bool:
    return weather is not None and weather["slope"] is not None and weather["slope"] > 0


def heating_window(
    entry: ElectricityContractsConfigEntry, start: datetime, end: datetime
) -> tuple[datetime, datetime]:
    """Narrow a window to the hours heating can be read on.

    With a meter, like a comparison, so the figures agree with the other tabs;
    without one, to where the heating statistics are.
    """
    coordinator = entry.runtime_data
    if coordinator.statistic_id:
        return narrow_window(coordinator.data.costing, contracts(entry), start, end)
    start = max(start, day_start(coordinator.data.sources.first_day))
    heating_end = coordinator.data.heating_end
    return start, max(start, min(end, heating_end)) if heating_end else start


async def async_heating(
    hass: HomeAssistant,
    *,
    entry: ElectricityContractsConfigEntry,
    start: datetime,
    end: datetime,
) -> dict[str, Any]:
    """Describe what heating used and cost between `start` and `end` (UTC).

    The window is narrowed by `heating_window` first, and to the heating
    statistics when they start later. Electric heating before them, back to the
    Linky's first day, is estimated from its days and the weather: in kWh, in
    `estimated_days` and `before`, apart from the measured `days`. A window
    wholly before them has no measured day. `unestimated` gives the days before
    that have no outdoor temperature.
    """
    first, last = heating_window(entry, start, end)
    stop = max(first, last)
    heaters = await async_heaters_start(entry)
    coordinator = entry.runtime_data
    electric = (
        coordinator.statistic_id is not None
        and not Heating.from_options(entry.options, outdoor=None).gas
    )
    main = min(max(first, heaters), stop) if heaters is not None else first
    answer = await async_heating_between(hass, entry=entry, start=main, end=stop)
    answer.update({"estimated_days": [], "before": None, "unestimated": None})
    if heaters is None or not electric:
        return answer
    # Only before the heating statistics: the days they measured stay theirs,
    # even those the window was narrowed from.
    before, answer["unestimated"] = await async_before_heaters(
        hass, entry, start, min(heaters, main), heaters=heaters
    )
    if before is not None:
        answer["estimated_days"] = before["estimated_days"]
        answer["before"] = {
            key: before[key] for key in ("start", "end", "days", "missing")
        } | {"heating": round(before["heating"], 1)}
    return answer


async def async_heaters_start(
    entry: ElectricityContractsConfigEntry,
) -> datetime | None:
    """Return the first day of the heating statistics, None without any."""
    if not Heating.from_options(entry.options, outdoor=None).measured:
        return None
    day = await entry.runtime_data.async_heating_first_day()
    return day_start(day) if day else None


async def async_before_heaters(
    hass: HomeAssistant,
    entry: ElectricityContractsConfigEntry,
    start: datetime,
    end: datetime,
    *,
    heaters: datetime | None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Estimate the electric heating from `start` to `end` from the Linky's days.

    From the Linky's first day at the earliest. The fit runs over up to a year
    before the first day of the heating statistics (`heaters`), else before
    `end`: a day gets the same estimate whatever the window. Returns the
    estimate, with the `missing` days it couldn't count (no outdoor temperature
    or no Linky day), and the days before its first one that have no outdoor
    temperature (`unestimated`), each None when empty.
    """
    linky = day_start(entry.runtime_data.data.sources.first_day)
    begin = max(start, linky)
    if begin >= end:
        return None, None
    fit_end = heaters or end
    before = await async_linky_heating(
        hass, entry, begin, end, fit=(max(linky, fit_end - _YEAR), fit_end)
    )
    estimated_from = end
    if before is not None:
        estimated_from = day_start(date.fromisoformat(before["start"]))
        span = (local_day(end) - date.fromisoformat(before["start"])).days
        before["missing"] = span - before["days"]
    unestimated = (
        {
            "start": local_day(begin).isoformat(),
            "end": (local_day(estimated_from) - timedelta(days=1)).isoformat(),
            "open_meteo": bool(entry.options.get(CONF_WEATHER)),
        }
        if begin < estimated_from
        else None
    )
    return before, unestimated


def local_day(moment: datetime) -> date:
    """Return the day of a moment in France."""
    return moment.astimezone(FRANCE_TIME_ZONE).date()


async def async_linky_heating(
    hass: HomeAssistant,
    entry: ElectricityContractsConfigEntry,
    start: datetime,
    end: datetime,
    *,
    fit: tuple[datetime, datetime] | None = None,
) -> dict[str, Any] | None:
    """Estimate the electric heating from `start` to `end` from the Linky's days.

    Each day's consumption is fitted on its heating degree days, like the weather
    fit, over `fit` (first and first left out; else from `start` to `end`): the
    heating of each day comes from its degree days. Only the days with an
    outdoor temperature count, so the estimate starts at the first of them.
    Without a fit, None: those days are left out rather than counted without
    heating.
    """
    source_id = source_statistic(entry)
    assert source_id is not None
    heating = Heating.from_options(entry.options, outdoor=outdoor_statistic(entry))
    fit_start, fit_end = fit or (start, end)
    since, until = min(start, fit_start), max(end, fit_end)

    def read() -> tuple[dict[date, float], dict[date, float], dict[date, float]]:
        energy = {
            _day_of(row["start"]): row.get("change") or 0.0
            for row in statistics_during_period(
                hass,
                since,
                until,
                {source_id},
                "day",
                {"energy": UnitOfEnergy.KILO_WATT_HOUR},
                {"change"},
            ).get(source_id, [])
        }
        temperatures = statistics_during_period(
            hass,
            since,
            until,
            {*outdoor_ids(entry), *heating.indoor},
            "day",
            {"temperature": UnitOfTemperature.CELSIUS},
            {"mean"},
        )
        indoor: dict[date, list[float]] = {}
        for statistic_id in heating.indoor:
            for row in temperatures.get(statistic_id, []):
                if (mean := row.get("mean")) is not None:
                    indoor.setdefault(_day_of(row["start"]), []).append(mean)
        return (
            energy,
            {
                _day_of(row["start"]): mean
                for row in outdoor_rows(entry, temperatures)
                if (mean := row.get("mean")) is not None
            },
            {day: sum(values) / len(values) for day, values in indoor.items()},
        )

    energy, outdoor, indoor = await get_instance(hass).async_add_executor_job(read)
    # A daily read also returns the day that starts at its end.
    first_day, end_day = local_day(start), local_day(end)
    fit_first, fit_last = local_day(fit_start), local_day(fit_end)
    weather = weather_fit(
        {
            day: {"energy": kwh}
            for day, kwh in energy.items()
            if fit_first <= day < fit_last
        },
        outdoor,
    )
    if not _fitted(weather):
        return None
    counted = {
        day: outdoor[day]
        for day in sorted(energy)
        if first_day <= day < end_day and day in outdoor
    }
    if not counted:
        return None
    days = {
        day: line_heating(weather, weather["base"] - value)
        for day, value in counted.items()
    }
    return {
        "start": min(counted).isoformat(),
        "end": (end_day - timedelta(days=1)).isoformat(),
        "days": len(counted),
        "heating": sum(days.values()),
        "weather": weather,
        "weather_days": [
            {"temperature": value, "indoor": indoor.get(day)}
            for day, value in counted.items()
        ],
        "estimated_days": [
            {
                "date": day.isoformat(),
                "temperature": _round(counted[day], 1),
                "heating": round(kwh, 3),
            }
            for day, kwh in days.items()
        ],
    }


async def async_heating_between(
    hass: HomeAssistant,
    *,
    entry: ElectricityContractsConfigEntry,
    start: datetime,
    end: datetime,
    weather_days: bool = False,
) -> dict[str, Any]:
    """Describe what heating used and cost over a window `heating_window` narrowed.

    Without heating statistics, the heating is estimated from the source's
    consumption and the outdoor temperature. `weather_days` adds, to an
    estimate, the outdoor and indoor means of the days it counts.
    """
    heating = Heating.from_options(entry.options, outdoor=outdoor_statistic(entry))
    coordinator = entry.runtime_data
    status = coordinator.data.costing
    actual = coordinator.costing.actual_statistics() if status.actual else None
    house_ids = (actual.energy, actual.variable) if actual is not None else None
    measured = [*heating.statistics]
    if heating.water_statistic:
        measured.append(heating.water_statistic)
    temperatures = [
        item
        for item in (heating.outdoor, outdoor_fill(entry), *heating.indoor)
        if item is not None
    ]
    # Hot water mixed with the heating is told apart on the warm days of a year.
    outdoor = heating.outdoor
    year = heating.measured and heating.with_water and not heating.water_statistic
    price_ids = price_entities([*contracts(entry), *gas_contracts(entry)])

    def read() -> _Read:
        if end <= start:
            return _Read(energy={}, house={}, temperatures={}, metadata={})
        return _Read(
            energy=(
                statistics_during_period(
                    hass,
                    start,
                    end,
                    set(measured),
                    "hour",
                    {"energy": UnitOfEnergy.KILO_WATT_HOUR},
                    {"change"},
                )
                if measured
                else {}
            ),
            house=hourly_changes(hass, start, end, list(house_ids))
            if house_ids
            else {},
            temperatures=(
                statistics_during_period(
                    hass,
                    start,
                    end,
                    set(temperatures),
                    "hour",
                    {"temperature": UnitOfTemperature.CELSIUS},
                    {"mean"},
                )
                if temperatures
                else {}
            ),
            metadata=(
                get_metadata(hass, statistic_ids=set(heating.statistics))
                if heating.statistics
                else {}
            ),
            prices=hourly_prices(hass, price_ids, start, end),
            **(read_year() if year and outdoor else {}),
        )

    def read_year() -> dict[str, Any]:
        since = end - _YEAR
        return {
            "year_energy": statistics_during_period(
                hass,
                since,
                end,
                set(heating.statistics),
                "day",
                {"energy": UnitOfEnergy.KILO_WATT_HOUR},
                {"change"},
            ),
            "year_temperature": statistics_during_period(
                hass,
                since,
                end,
                set(outdoor_ids(entry)),
                "day",
                {"temperature": UnitOfTemperature.CELSIUS},
                {"mean"},
            ),
        }

    rows = await get_instance(hass).async_add_executor_job(read)
    built = _Answer(hass, entry, rows, house_ids, heating)
    answer = built.build(dt_util.now(FRANCE_TIME_ZONE).date())
    if weather_days and not answer["measured"]:
        answer["weather_days"] = [
            {"temperature": temperature, "indoor": built.indoor.get(day)}
            for day, temperature in counted_days(built.outdoor, built.house).items()
        ]
    return answer


def _day_of(timestamp: float) -> date:
    """Return the day a daily row of the recorder stands for, in its time zone."""
    return dt_util.as_local(datetime.fromtimestamp(timestamp, UTC)).date()


def _round(value: float | None, digits: int) -> float | None:
    return round(value, digits) if value is not None else None
