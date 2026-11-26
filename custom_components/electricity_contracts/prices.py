"""Prices read from a sensor, and what a kWh of gas costs on a day."""

from collections.abc import Iterable, Mapping
from datetime import UTC, date, datetime, timedelta

from elec_tariffs import GasPricePeriod, GasProfile, fixed_cost_per_day
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.core import HomeAssistant

from .const import FRANCE_TIME_ZONE
from .costing import SensorPrices
from .data import Contract, GasContract, gas_in_force

# Prices are read from a week before the hours to cost: an hour missing just
# after the start still has the price before it.
_LOOKBACK = timedelta(days=7)


type HourlyPrices = dict[str, SensorPrices]
"""The prices of each sensor, by entity ID."""


def price_entities(
    entry_contracts: Iterable[Contract | GasContract],
) -> set[str]:
    """Return the sensors the contracts read their prices from."""
    return {
        contract.entity.entity_id
        for contract in entry_contracts
        if contract.entity is not None
    }


def first_statistic_hour(hass: HomeAssistant, statistic_id: str) -> datetime | None:
    """Return the start (UTC) of a statistic's first hour; None without one.

    Runs in the recorder's executor.
    """
    months = statistics_during_period(
        hass,
        datetime(2000, 1, 1, tzinfo=UTC),
        None,
        {statistic_id},
        "month",
        None,
        {"mean", "sum"},
    )
    if not months.get(statistic_id):
        return None
    # Months follow the server's time zone: look for the first hour in the
    # first month only.
    month_start = datetime.fromtimestamp(months[statistic_id][0]["start"], UTC)
    hours = statistics_during_period(
        hass,
        month_start,
        month_start + timedelta(days=32),
        {statistic_id},
        "hour",
        None,
        {"mean", "sum"},
    )
    return datetime.fromtimestamp(hours[statistic_id][0]["start"], UTC)


def hourly_prices(
    hass: HomeAssistant, entity_ids: set[str], start: datetime, end: datetime | None
) -> HourlyPrices:
    """Read the hourly mean of each price sensor, for the hours from `start` (UTC).

    Runs in the recorder's executor. A sensor's statistics are in its own unit,
    a price of a kWh: the flow refuses another one.
    """
    if not entity_ids:
        return {}
    rows = statistics_during_period(
        hass, start - _LOOKBACK, end, entity_ids, "hour", None, {"mean"}
    )
    return {
        entity_id: SensorPrices(
            {
                datetime.fromtimestamp(row["start"], UTC): mean
                for row in rows.get(entity_id, [])
                if (mean := row.get("mean")) is not None
            },
            first_statistic_hour(hass, entity_id),
        )
        for entity_id in entity_ids
    }


class GasPricer:
    """Cost the gas used under the gas contract in force each day."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_contracts: list[GasContract],
        official: Mapping[GasProfile, list[GasPricePeriod]],
        hourly: HourlyPrices,
    ) -> None:
        """Keep the contracts, the reference prices and the sensors' prices."""
        self._hass = hass
        self._contracts = entry_contracts
        self._official = official
        self._hourly = hourly

    def _periods(self, contract: GasContract) -> list[GasPricePeriod]:
        if contract.profile is not None:
            return self._official.get(contract.profile, [])
        return list(contract.periods)

    def _period(self, contract: GasContract, day: date) -> GasPricePeriod | None:
        return next(
            (item for item in self._periods(contract) if item.covers(day)), None
        )

    def hour(self, start: datetime, kwh: float) -> float | None:
        """Cost the gas of the hour starting at `start`; None without its price."""
        day = start.astimezone(FRANCE_TIME_ZONE).date()
        contract = gas_in_force(self._contracts, day)
        if contract is None:
            return None
        if contract.entity is not None:
            price = self._sensor(contract.entity.entity_id).at(start)
            return kwh * price if price is not None else None
        period = self._period(contract, day)
        return kwh * period.price if period is not None else None

    def _sensor(self, entity_id: str) -> SensorPrices:
        return self._hourly.get(entity_id) or SensorPrices({}, None)

    def day(self, day: date, kwh: float) -> float | None:
        """Cost gas only known for a whole day; None without the day's price.

        A sensor's price is the mean of its hours that day.
        """
        contract = gas_in_force(self._contracts, day)
        if contract is None:
            return None
        if contract.entity is not None:
            prices = self._day_prices(contract.entity.entity_id, day)
            return kwh * sum(prices) / len(prices) if prices else None
        period = self._period(contract, day)
        return kwh * period.price if period is not None else None

    def _day_prices(self, entity_id: str, day: date) -> list[float]:
        sensor = self._sensor(entity_id)
        hour = datetime.combine(day, datetime.min.time(), FRANCE_TIME_ZONE)
        end = datetime.combine(
            day + timedelta(days=1), datetime.min.time(), FRANCE_TIME_ZONE
        ).astimezone(UTC)
        prices: list[float] = []
        # 23 to 25 hours, with the changes of time.
        hour = hour.astimezone(UTC)
        while hour < end:
            if (price := sensor.at(hour)) is not None:
                prices.append(price)
            hour += timedelta(hours=1)
        return prices

    def fixed(self, day: date) -> float | None:
        """Return the day's share of the subscription; None without a contract."""
        contract = gas_in_force(self._contracts, day)
        if contract is None:
            return None
        if contract.entity is not None:
            return fixed_cost_per_day(contract.entity.fixed_per_year, day)
        period = self._period(contract, day)
        return (
            fixed_cost_per_day(period.fixed_per_year, day)
            if period is not None
            else None
        )

    def today(self, today: date) -> float | None:
        """Return the price of a kWh of gas today."""
        contract = gas_in_force(self._contracts, today)
        if contract is None:
            return None
        if contract.entity is not None:
            return contract.entity.current(self._hass)
        period = self._period(contract, today)
        return period.price if period is not None else None
