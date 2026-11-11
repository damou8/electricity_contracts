"""WebSocket commands behind the Contracts page."""

from datetime import date, datetime, timedelta
from typing import Any

import probatio as vol
from elec_tariffs import PricePeriod
from homeassistant.components.websocket_api import async_register_command
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.const import (
    ERR_INVALID_FORMAT,
    ERR_NOT_ALLOWED,
    ERR_NOT_FOUND,
)
from homeassistant.components.websocket_api.decorators import (
    async_response,
    websocket_command,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv

from .bill import Bill, async_bill
from .comparison import (
    GroupBy,
    async_compare,
    async_series,
    comparison_response,
    data_end,
    day_start,
)
from .const import DOMAIN, FRANCE_TIME_ZONE
from .coordinator import (
    ElectricityContractsConfigEntry,
    ElectricityContractsCoordinator,
)
from .data import (
    Contract,
    contracts,
    format_time_range,
    manual_prices,
    price_periods,
)
from .insights import async_insights

_HOUR = timedelta(hours=1)
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


def _contract(contract: Contract, periods: list[PricePeriod]) -> dict[str, Any]:
    """Describe a contract and the prices it has had, oldest first."""
    return {
        "id": contract.uid,
        "name": contract.name,
        "kind": contract.kind.value,
        "official": contract.official,
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


@websocket_command({vol.Required("type"): f"{DOMAIN}/entries"})
@callback
def ws_entries(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """List the consumption sources, their contracts and the days they cover."""
    result: list[dict[str, Any]] = []
    for entry in hass.config_entries.async_loaded_entries(DOMAIN):
        manual = manual_prices(entry)
        coordinator: ElectricityContractsCoordinator = entry.runtime_data
        status = coordinator.data.costing
        entry_contracts = contracts(entry)
        end = data_end(status, entry_contracts)
        result.append(
            {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "first_day": (
                    _local_day(status.first_hour) if status.first_hour else None
                ),
                "last_day": _local_day(end - _HOUR) if end else None,
                "contracts": [
                    _contract(
                        contract,
                        price_periods(
                            contract, manual, coordinator.data.sources.official_prices
                        ),
                    )
                    for contract in entry_contracts
                ],
                "actual": status.actual is not None,
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
    group_by: GroupBy = "day" if (end - start).days < _MAX_DAYS_BY_DAY else "month"
    series = await async_series(
        hass, writer=coordinator.costing, comparison=comparison, group_by=group_by
    )
    connection.send_result(
        msg["id"],
        {
            **comparison_response(comparison),
            "group_by": group_by,
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
        periods=price_periods(
            contract, manual_prices(entry), coordinator.data.sources.official_prices
        ),
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
