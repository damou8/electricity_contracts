"""WebSocket commands behind the Contracts page."""

from datetime import date, datetime, timedelta
from typing import Any

import probatio as vol
from elec_tariffs import PricePeriod
from homeassistant.components.recorder.statistics import get_last_statistics
from homeassistant.components.websocket_api import async_register_command
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.const import (
    ERR_INVALID_FORMAT,
    ERR_NOT_ALLOWED,
    ERR_NOT_FOUND,
)
from homeassistant.components.websocket_api.decorators import (
    async_response,
    require_admin,
    websocket_command,
)
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.recorder import get_instance

from .bill import Bill, async_bill
from .comparison import (
    GroupBy,
    async_compare,
    async_series,
    comparison_response,
    data_end,
    day_start,
    linky_days,
)
from .const import CONF_TEMPERATURE, DOMAIN, FRANCE_TIME_ZONE
from .coordinator import (
    ElectricityContractsConfigEntry,
    ElectricityContractsCoordinator,
)
from .data import (
    Contract,
    Heating,
    contracts,
    format_time_range,
    price_periods,
    source_statistic,
)
from .dpe import SETTINGS_SCHEMA, async_dpe, async_save_settings
from .heating import async_heating
from .insights import async_insights
from .outlook import async_outlook
from .statistics import SeriesStatus
from .weather import outdoor_fill, outdoor_source, outdoor_statistic

_HOUR = timedelta(hours=1)
# Rows at least 23 hours apart (a day, or a day when the clocks change).
_DAILY_SECONDS = 23 * 3600
# Longer windows are split into months.
_MAX_DAYS_BY_DAY = 62

ATTR_ENTRY_ID = "entry_id"
ATTR_CONTRACT_ID = "contract_id"
ATTR_START = "start"
ATTR_END = "end"


@callback
def async_register_commands(hass: HomeAssistant) -> None:
    """Register the commands of the Contracts page."""
    async_register_command(hass, ws_entries)
    async_register_command(hass, ws_compare)
    async_register_command(hass, ws_bill)
    async_register_command(hass, ws_insights)
    async_register_command(hass, ws_heating)
    async_register_command(hass, ws_outlook)
    async_register_command(hass, ws_dpe)
    async_register_command(hass, ws_dpe_save)


def _local_day(moment: datetime) -> str:
    return moment.astimezone(FRANCE_TIME_ZONE).date().isoformat()


def _loaded_entry(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> ElectricityContractsConfigEntry | None:
    """Return the loaded entry a command targets, or send an error."""
    entry = hass.config_entries.async_get_entry(msg[ATTR_ENTRY_ID])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Consumption source not found")
        return None
    if entry.state is not ConfigEntryState.LOADED:
        connection.send_error(
            msg["id"], ERR_NOT_ALLOWED, "Consumption source not loaded"
        )
        return None
    return entry


def _window(
    connection: ActiveConnection, msg: dict[str, Any]
) -> tuple[date, date] | None:
    """Return the first and last day asked for, or send an error."""
    start: date = msg[ATTR_START]
    end: date = msg[ATTR_END]
    if end < start:
        connection.send_error(
            msg["id"], ERR_INVALID_FORMAT, "The end is before the start"
        )
        return None
    return start, end


def _contract(
    contract: Contract, periods: list[PricePeriod], series: SeriesStatus | None
) -> dict[str, Any]:
    """Describe a contract, the prices it has had, oldest first, and its costing.

    `costed` is false while no hour could be costed: the contract isn't compared,
    and `waiting` says for what, from which day.
    """
    waiting = series.waiting if series else None
    return {
        "id": contract.uid,
        "name": contract.name,
        "kind": contract.kind.value,
        "official": contract.official,
        "pricing": contract.pricing,
        "costed": series is not None and series.last_hour is not None,
        "waiting": (
            {"reason": waiting.reason, "day": waiting.day.isoformat()}
            if waiting
            else None
        ),
        "kva": contract.kva,
        "off_peak": [format_time_range(item) for item in contract.rules.off_peak],
        "weekend_off_peak": contract.rules.weekend_off_peak,
        "active_from": (
            contract.active_from.isoformat() if contract.active_from else None
        ),
        "active_to": contract.active_to.isoformat() if contract.active_to else None,
        "prices": [
            {
                "start": period.start.isoformat(),
                "end": period.end.isoformat() if period.end else None,
                "fixed_per_year": period.fixed_per_year,
                "tranches": {
                    tranche.value: price for tranche, price in period.prices.items()
                },
            }
            for period in periods
        ],
    }


def _inputs(
    entry: ConfigEntry, heating: Heating, steps: dict[str, str]
) -> dict[str, Any]:
    """Return the statistics the entry reads, for the panel to name them.

    The consumption is only told as Linky or not: its ID holds the meter number.
    `steps` says whether each statistic is "hour"ly or "day"ly, by ID.
    """
    source = source_statistic(entry)
    ids = _read_ids(entry, heating)
    return {
        "meter": None if source is None else source.split(":", 1)[0],
        "meter_step": steps.get(source) if source else None,
        "heating": list(heating.statistics),
        "water": heating.water_statistic,
        "outdoor": entry.options.get(CONF_TEMPERATURE) or None,
        "indoor": list(heating.indoor),
        "steps": {
            statistic_id: steps[statistic_id]
            for statistic_id in ids
            if statistic_id in steps
        },
    }


def _read_ids(entry: ConfigEntry, heating: Heating) -> list[str]:
    """Return the statistics other than the meter that the entry reads."""
    outdoor = entry.options.get(CONF_TEMPERATURE)
    water = [heating.water_statistic] if heating.water_statistic else []
    return [
        *heating.statistics,
        *water,
        *([outdoor] if outdoor else []),
        *heating.indoor,
    ]


def _steps(hass: HomeAssistant, ids: set[str]) -> dict[str, str]:
    """Tell, from its last two rows, whether each statistic is hourly or daily."""
    steps: dict[str, str] = {}
    for statistic_id in ids:
        rows = get_last_statistics(
            hass, 2, statistic_id, convert_units=False, types={"sum", "mean"}
        ).get(statistic_id, [])
        if len(rows) == 2:  # noqa: PLR2004 - the last two rows
            gap = rows[0]["start"] - rows[1]["start"]
            steps[statistic_id] = "day" if gap >= _DAILY_SECONDS else "hour"
    return steps


@websocket_command({vol.Required("type"): f"{DOMAIN}/entries"})
@async_response
async def ws_entries(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """List the consumption sources, their contracts and the days they cover."""
    ids: set[str] = set()
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        heating = Heating.from_options(entry.options, outdoor=None)
        ids.update(_read_ids(entry, heating))
        if source := source_statistic(entry):
            ids.add(source)
    steps = await get_instance(hass).async_add_executor_job(_steps, hass, ids)
    result: list[dict[str, Any]] = []
    # Read again: an entry may have been unloaded meanwhile.
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        coordinator: ElectricityContractsCoordinator = entry.runtime_data
        status = coordinator.data.costing
        entry_contracts = contracts(entry)
        meter = coordinator.statistic_id is not None
        heating = Heating.from_options(entry.options, outdoor=outdoor_statistic(entry))
        if meter:
            first = status.first_hour
            end = data_end(status, entry_contracts)
        else:
            # Without a meter, the days are those of the heating statistics.
            end = coordinator.data.heating_end
            first = day_start(coordinator.data.sources.first_day) if end else None
        result.append(
            {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "meter": meter,
                "first_day": _local_day(first) if first else None,
                # With the days the Linky only gave in total, which have no cost.
                "energy_first_day": (
                    coordinator.data.sources.first_day.isoformat()
                    if meter and end
                    else None
                ),
                "last_day": _local_day(end - _HOUR) if end else None,
                "contracts": [
                    _contract(
                        contract,
                        price_periods(
                            hass, contract, coordinator.data.sources.official_prices
                        ),
                        status.contracts.get(contract.uid),
                    )
                    for contract in entry_contracts
                ],
                "actual": status.actual is not None,
                "outdoor": outdoor_source(entry),
                # The sensor's first day, when Open-Meteo gives days of consumption
                # before it.
                "outdoor_fill_until": (
                    until.isoformat()
                    if outdoor_fill(entry)
                    and (until := coordinator.weather.until)
                    and until > coordinator.data.sources.first_day
                    else None
                ),
                # What the cards' notes list as "your data".
                "inputs": _inputs(entry, heating, steps),
                # Without a meter, the heating can't be estimated: only measured.
                "heating": _heating(heating) if meter or heating.measured else None,
            }
        )
    connection.send_result(msg["id"], result)


@websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/compare",
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Required(ATTR_START): cv.date,
        vol.Required(ATTR_END): cv.date,
    }
)
@async_response
async def ws_compare(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Compare every contract from one day to another, both included.

    The series is split by day up to two months, by month beyond.
    """
    if (entry := _loaded_entry(hass, connection, msg)) is None or (
        window := _window(connection, msg)
    ) is None:
        return
    start, end = window
    coordinator: ElectricityContractsCoordinator = entry.runtime_data
    comparison = await async_compare(
        hass,
        writer=coordinator.costing,
        status=coordinator.data.costing,
        contracts=contracts(entry),
        start=day_start(start),
        end=day_start(end + timedelta(days=1)),
        details=True,
    )
    source_id = source_statistic(entry)
    days = (
        await get_instance(hass).async_add_executor_job(
            linky_days,
            hass,
            source_id,
            day_start(start),
            day_start(end + timedelta(days=1)),
        )
        if source_id
        else {}
    )
    group_by: GroupBy = "day" if (end - start).days < _MAX_DAYS_BY_DAY else "month"
    series = await async_series(
        hass,
        writer=coordinator.costing,
        comparison=comparison,
        group_by=group_by,
        days=days,
    )
    connection.send_result(
        msg["id"],
        {
            **comparison_response(comparison),
            "group_by": group_by,
            # The days the Linky only gave in total: kWh without a cost.
            "daily": (
                {
                    "first": min(days).isoformat(),
                    "last": max(days).isoformat(),
                    "days": len(days),
                    "energy": round(sum(days.values()), 3),
                }
                if days
                else None
            ),
            "series": [
                {
                    "start": bucket.start.isoformat(),
                    "energy": round(bucket.energy, 3),
                    "contracts": {
                        uid: round(cost, 2) for uid, cost in bucket.contracts.items()
                    },
                    "actual": (
                        round(bucket.actual, 2) if bucket.actual is not None else None
                    ),
                    "daily": bucket.daily,
                }
                for bucket in series
            ],
        },
    )


@websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/bill",
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Required(ATTR_CONTRACT_ID): cv.string,
        vol.Required(ATTR_START): cv.date,
        vol.Required(ATTR_END): cv.date,
    }
)
@async_response
async def ws_bill(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the bill a contract would have produced, both days included."""
    if (entry := _loaded_entry(hass, connection, msg)) is None or (
        window := _window(connection, msg)
    ) is None:
        return
    known = {contract.uid: contract for contract in contracts(entry)}
    if (contract := known.get(msg[ATTR_CONTRACT_ID])) is None:
        connection.send_error(msg["id"], ERR_NOT_FOUND, "Unknown contract")
        return
    start, end = window
    coordinator: ElectricityContractsCoordinator = entry.runtime_data
    bill = await async_bill(
        hass,
        writer=coordinator.costing,
        status=coordinator.data.costing,
        contract=contract,
        periods=price_periods(hass, contract, coordinator.data.sources.official_prices),
        start=day_start(start),
        end=day_start(end + timedelta(days=1)),
    )
    connection.send_result(msg["id"], bill_response(bill))


@websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/insights",
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Required(ATTR_START): cv.date,
        vol.Required(ATTR_END): cv.date,
    }
)
@async_response
async def ws_insights(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Describe the actual consumption from one day to another, both included."""
    if (entry := _loaded_entry(hass, connection, msg)) is None or (
        window := _window(connection, msg)
    ) is None:
        return
    start, end = window
    connection.send_result(
        msg["id"],
        await async_insights(
            hass,
            entry=entry,
            start=day_start(start),
            end=day_start(end + timedelta(days=1)),
        ),
    )


@websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/heating",
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Required(ATTR_START): cv.date,
        vol.Required(ATTR_END): cv.date,
    }
)
@async_response
async def ws_heating(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Describe what heating used and cost from one day to another, both included."""
    if (entry := _loaded_entry(hass, connection, msg)) is None or (
        window := _window(connection, msg)
    ) is None:
        return
    start, end = window
    connection.send_result(
        msg["id"],
        await async_heating(
            hass,
            entry=entry,
            start=day_start(start),
            end=day_start(end + timedelta(days=1)),
        ),
    )


@websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/dpe",
        vol.Required(ATTR_ENTRY_ID): cv.string,
        vol.Required(ATTR_END): cv.date,
    }
)
@async_response
async def ws_dpe(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the energy label of the 12 months that end on a day."""
    if (entry := _loaded_entry(hass, connection, msg)) is None:
        return
    connection.send_result(
        msg["id"], await async_dpe(hass, entry=entry, end=msg[ATTR_END])
    )


@websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/dpe/save",
        vol.Required(ATTR_ENTRY_ID): cv.string,
        **SETTINGS_SCHEMA,
    }
)
@require_admin
@async_response
async def ws_dpe_save(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Save the settings of an entry's energy label."""
    if (entry := _loaded_entry(hass, connection, msg)) is None:
        return
    connection.send_result(
        msg["id"], await async_save_settings(hass, entry.entry_id, msg)
    )


def _heating(heating: Heating) -> dict[str, Any] | None:
    """Say what the Heating tab can show, None when it has nothing to show."""
    if not heating.shown:
        return None
    return {
        "measured": heating.measured,
        "gas": heating.gas,
        "with_water": heating.with_water or heating.water_statistic is not None,
        "indoor": bool(heating.indoor),
    }


@websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/outlook",
        vol.Required(ATTR_ENTRY_ID): cv.string,
    }
)
@async_response
async def ws_outlook(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Return the price over the next 24 hours and the bill of the season."""
    if (entry := _loaded_entry(hass, connection, msg)) is None:
        return
    connection.send_result(msg["id"], await async_outlook(hass, entry=entry))


def bill_response(bill: Bill) -> dict[str, Any]:
    """Return a bill as the result of the bill command."""
    actual = bill.actual
    return {
        "contract": {
            "id": bill.contract.uid,
            "name": bill.contract.name,
            "kind": bill.contract.kind.value,
        },
        "start": bill.start.astimezone(FRANCE_TIME_ZONE).isoformat(),
        "end": bill.end.astimezone(FRANCE_TIME_ZONE).isoformat(),
        "periods": [
            {
                "start": period.start.astimezone(FRANCE_TIME_ZONE).isoformat(),
                "end": period.end.astimezone(FRANCE_TIME_ZONE).isoformat(),
                "fixed_per_year": period.fixed_per_year,
                "subscription": round(period.subscription, 2),
                "lines": [
                    {
                        "tranche": line.tranche.value,
                        "energy": round(line.energy, 3),
                        "price": line.price,
                        "cost": round(line.cost, 2),
                    }
                    for line in period.lines
                ],
            }
            for period in bill.periods
        ],
        "energy": round(bill.energy, 3),
        "consumption": round(bill.consumption, 2),
        "subscription": round(bill.subscription, 2),
        "total": round(bill.total, 2),
        "actual": round(actual.total, 2) if actual is not None else None,
        "difference": bill.difference,
    }
