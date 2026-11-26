"""Tests of contracts priced by a sensor, and of the gas contracts."""

from datetime import date, timedelta
from typing import Any

import pytest
from elec_tariffs import ContractKind, GasProfile, PrvgError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.electricity_contracts.comparison import compared_window
from custom_components.electricity_contracts.const import (
    CONF_HEATING_ENERGY,
    CONF_HEATING_STATISTICS,
    CONF_TEMPERATURE,
    CONF_WATER_ENERGY,
    CONF_WATER_STATISTIC,
    DOMAIN,
    ENERGY_GAS,
    PRICING_ENTITY,
    PRICING_OFFICIAL,
    SECTION_HEATING,
)
from custom_components.electricity_contracts.costing import SensorPrices
from custom_components.electricity_contracts.data import contracts

from .conftest import (
    FIRST_HOUR,
    GAS_PERIODS,
    PRICE_ID,
    TEMPERATURE_ID,
    Sources,
    add_price,
    add_statistic,
    contract_subentry,
    gas_contract_subentry,
    gas_period,
    make_entry,
)
from .test_heating import (
    BASE_CONTRACT,
    DAYS,
    GAS,
    HEATER_A,
    MIDNIGHT,
    WATER,
    add_energy,
    gas_home,  # noqa: F401 - a fixture
    heating,
    hourly,
)
from .test_sensor import sensor
from .test_statistics import PREFIX, last_sum, setup_entry
from .test_websocket import result

DYNAMIC = contract_subentry(
    "Dynamic",
    uid="dyn00001",
    kind=ContractKind.BASE,
    pricing=PRICING_ENTITY,
    price_entity=PRICE_ID,
    # 1 € an hour.
    fixed_per_year=365 * 24.0,
    active_from="2026-01-01",
)
DYN = f"{PREFIX}_dyn00001"
# Gas heating alone, without hot water.
GAS_ONLY: dict[str, Any] = {
    CONF_TEMPERATURE: TEMPERATURE_ID,
    SECTION_HEATING: {CONF_HEATING_STATISTICS: [GAS], CONF_HEATING_ENERGY: ENERGY_GAS},
}


@pytest.mark.usefixtures("statistic", "sources")
async def test_each_hour_at_the_price_of_the_sensor(hass: HomeAssistant) -> None:
    # The 48 hours of 0.5 kWh: the first day at 0.1 €, the second at 0.3 €.
    await add_price(hass, [0.1] * 24 + [0.3] * 24)
    entry = await setup_entry(hass, make_entry([DYNAMIC]))
    assert await last_sum(hass, f"{DYN}_cost_base") == pytest.approx(4.8)
    assert await last_sum(hass, f"{DYN}_cost_fixed") == pytest.approx(48.0)
    assert await last_sum(hass, f"{PREFIX}_actual_cost") == pytest.approx(4.8)
    assert entry.runtime_data.data.costing.contracts["dyn00001"].waiting is None


@pytest.mark.usefixtures("statistic", "sources")
async def test_hours_without_a_price_wait(hass: HomeAssistant) -> None:
    await add_price(hass, [0.1] * 24)
    entry = await setup_entry(hass, make_entry([DYNAMIC]))
    status = entry.runtime_data.data.costing.contracts["dyn00001"]
    assert status.last_hour == FIRST_HOUR + timedelta(hours=23)
    assert status.waiting is not None
    assert status.waiting.reason == "price"
    # 2 March, 1:00 in Paris.
    assert status.waiting.day == date(2026, 3, 2)
    # The sensor's next statistics bring the price: no repair issue.
    assert not [
        issue_id
        for domain, issue_id in ir.async_get(hass).issues
        if domain == DOMAIN and issue_id.startswith("missing_price")
    ]


@pytest.mark.usefixtures("statistic", "sources")
async def test_compared_from_the_first_price(hass: HomeAssistant) -> None:
    # A sensor newer than the meter: prices from the second day only.
    await add_price(hass, [0.3] * 24, first=24)
    entry = await setup_entry(hass, make_entry([DYNAMIC]))
    second_day = FIRST_HOUR + timedelta(hours=24)
    status = entry.runtime_data.data.costing
    series = status.contracts["dyn00001"]
    assert series.first_hour == second_day
    assert series.last_hour == FIRST_HOUR + timedelta(hours=47)
    assert series.waiting is None
    assert await last_sum(hass, f"{DYN}_cost_base") == pytest.approx(3.6)
    # Its first day isn't known: nothing is counted for it.
    assert await last_sum(hass, f"{PREFIX}_actual_cost") == pytest.approx(3.6)
    assert status.actual is not None
    assert status.actual.waiting is None
    # Comparisons start with its first price.
    window = compared_window(
        status, contracts(entry), FIRST_HOUR, FIRST_HOUR + timedelta(hours=48)
    )
    assert window == (second_day, FIRST_HOUR + timedelta(hours=48))

    # Kept across restarts.
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    status = entry.runtime_data.data.costing
    assert status.contracts["dyn00001"].first_hour == second_day


@pytest.mark.usefixtures("statistic", "sources")
async def test_a_missing_hour_takes_the_price_before(hass: HomeAssistant) -> None:
    # Home Assistant was off at 10:00 and 11:00: the sensor has no price then.
    await add_price(hass, [0.1] * 10)
    await add_price(hass, [0.3] * 36, first=12)
    entry = await setup_entry(hass, make_entry([DYNAMIC]))
    status = entry.runtime_data.data.costing.contracts["dyn00001"]
    assert status.waiting is None
    assert status.last_hour == FIRST_HOUR + timedelta(hours=47)
    # 0.5 kWh an hour: 12 hours at 0.1 €, 36 at 0.3 €.
    assert await last_sum(hass, f"{DYN}_cost_base") == pytest.approx(6.0)


@pytest.mark.usefixtures("statistic", "sources")
async def test_a_sensor_without_prices_waits(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([DYNAMIC]))
    status = entry.runtime_data.data.costing.contracts["dyn00001"]
    assert status.last_hour is None
    assert status.first_hour is None
    assert status.waiting is not None
    assert status.waiting.reason == "price"


def test_sensor_prices() -> None:
    hour = timedelta(hours=1)
    prices = SensorPrices(
        {FIRST_HOUR + 2 * hour: 0.2, FIRST_HOUR + 5 * hour: 0.5}, FIRST_HOUR
    )
    assert prices.before_first(FIRST_HOUR - hour)
    assert prices.at(FIRST_HOUR - hour) is None
    # Read from too late to have the price before: the one after.
    assert prices.at(FIRST_HOUR) == 0.2
    assert prices.at(FIRST_HOUR + 4 * hour) == 0.2
    assert prices.at(FIRST_HOUR + 5 * hour) == 0.5
    # After the last price: not known yet.
    assert prices.at(FIRST_HOUR + 6 * hour) is None
    # Without a first hour, the first price is the first one read.
    assert SensorPrices({FIRST_HOUR: 0.1}, None).first == FIRST_HOUR
    assert SensorPrices({}, None).at(FIRST_HOUR) is None


@pytest.mark.usefixtures("statistic", "sources")
async def test_the_price_shown_is_the_sensors(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await add_price(hass, [0.2] * 48)
    hass.states.async_set(PRICE_ID, "0.25")
    entry = await setup_entry(hass, make_entry([DYNAMIC]))
    assert float(sensor(hass, entry, "current_price").state) == 0.25
    [listed] = await result(hass_ws_client, hass, type=f"{DOMAIN}/entries")
    [contract] = listed["contracts"]
    assert contract["pricing"] == PRICING_ENTITY
    assert [period["tranches"] for period in contract["prices"]] == [{"base": 0.25}]
    # The bill gives the mean price of each tranche.
    bill = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/bill",
        entry_id=entry.entry_id,
        contract_id="dyn00001",
        start="2026-03-01",
        end="2026-03-02",
    )
    [period] = bill["periods"]
    [line] = period["lines"]
    assert line["price"] == pytest.approx(0.2)
    assert period["fixed_per_year"] == 365 * 24.0

    hass.states.async_set(PRICE_ID, "unavailable")
    [listed] = await result(hass_ws_client, hass, type=f"{DOMAIN}/entries")
    assert listed["contracts"][0]["prices"] == []
    hass.states.async_set(PRICE_ID, "n/a")
    [listed] = await result(hass_ws_client, hass, type=f"{DOMAIN}/entries")
    assert listed["contracts"][0]["prices"] == []


@pytest.mark.usefixtures("sources")
async def test_electric_heating_at_the_price_of_the_sensor(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await add_statistic(hass, first=MIDNIGHT, values=[250.0] * 48)
    await add_energy(hass, HEATER_A, [1.0] * 48)
    await add_price(hass, [0.2] * 48, first=MIDNIGHT)
    entry = await setup_entry(
        hass,
        make_entry(
            [DYNAMIC], options={SECTION_HEATING: {CONF_HEATING_STATISTICS: [HEATER_A]}}
        ),
    )
    answer = await heating(hass, hass_ws_client, entry, "2026-03-02", "2026-03-03")
    assert answer["totals"]["heating"] == pytest.approx(48.0)
    assert answer["totals"]["heating_cost"] == pytest.approx(9.6)
    assert answer["tranches"] == {"base": {"energy": 48.0, "cost": 9.6}}


@pytest.mark.usefixtures("sources")
async def test_electric_heating_stops_where_the_sensor_does(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await add_statistic(hass, first=MIDNIGHT, values=[250.0] * 48)
    await add_energy(hass, HEATER_A, [1.0] * 48)
    # The last hour has no price: like a comparison, the heating stops before it.
    await add_price(hass, [0.2] * 47, first=MIDNIGHT)
    entry = await setup_entry(
        hass,
        make_entry(
            [DYNAMIC], options={SECTION_HEATING: {CONF_HEATING_STATISTICS: [HEATER_A]}}
        ),
    )
    answer = await heating(hass, hass_ws_client, entry, "2026-03-02", "2026-03-04")
    assert answer["totals"]["heating"] == pytest.approx(47.0)
    assert answer["totals"]["heating_cost"] == pytest.approx(9.4)


async def test_gas_at_the_reference_price(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    sources: Sources,
    gas_home: list[float],  # noqa: F811 - the fixture
) -> None:
    contract = gas_contract_subentry(
        "Gas", pricing=PRICING_OFFICIAL, profile=GasProfile.HEATING
    )
    entry = await setup_entry(
        hass, make_entry([BASE_CONTRACT, contract], options=GAS_ONLY)
    )
    sources.prvg.async_price_periods.assert_awaited_once_with(GasProfile.HEATING)
    assert entry.runtime_data.data.sources.gas_prices == {
        GasProfile.HEATING: GAS_PERIODS[GasProfile.HEATING]
    }
    answer = await heating(hass, hass_ws_client, entry)
    # 0.1 € a kWh in March, and 365 € a year: 1 € a day.
    totals = answer["totals"]
    assert totals["heating"] == pytest.approx(sum(gas_home))
    assert totals["heating_cost"] == pytest.approx(0.1 * sum(gas_home) + DAYS, abs=0.01)
    assert answer["days"][0]["heating_cost"] == pytest.approx(0.1 * gas_home[0] + 1.0)
    assert answer["simulator"]["gas_price"] == 0.1


async def test_gas_reference_price_kept_and_its_failures(
    hass: HomeAssistant, sources: Sources
) -> None:
    contract = gas_contract_subentry(
        "Gas", pricing=PRICING_OFFICIAL, profile=GasProfile.COOKING_WATER
    )
    entry = make_entry([contract], options=GAS_ONLY)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    # Downloaded once a day: the reload reads the prices back from the cache.
    sources.prvg.async_price_periods.assert_awaited_once_with(GasProfile.COOKING_WATER)
    coordinator = entry.runtime_data
    assert (
        coordinator.data.sources.gas_prices[GasProfile.COOKING_WATER]
        == (GAS_PERIODS[GasProfile.COOKING_WATER])
    )
    assert coordinator.diagnostics()["gas_prices"]["cooking_water"]["periods"] == 1

    # A failure keeps the prices and doesn't stop the update.
    sources.prvg.async_price_periods.side_effect = PrvgError("down")
    coordinator._cache.gas_fetched.clear()
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.last_errors["gas_prices"] == "down"
    assert coordinator.data.sources.gas_prices[GasProfile.COOKING_WATER]


async def test_gas_reference_price_never_downloaded(
    hass: HomeAssistant, sources: Sources
) -> None:
    sources.prvg.async_price_periods.side_effect = PrvgError("down")
    contract = gas_contract_subentry(
        "Gas", pricing=PRICING_OFFICIAL, profile=GasProfile.HEATING
    )
    entry = make_entry([contract], options=GAS_ONLY)
    entry.add_to_hass(hass)
    # The gas only prices the heating: the rest works without it.
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.data.sources.gas_prices == {GasProfile.HEATING: []}


@pytest.mark.usefixtures("sources")
async def test_gas_at_the_price_of_a_sensor(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    gas_home: list[float],  # noqa: F811 - the fixture
) -> None:
    await add_price(hass, [0.2] * 24 * DAYS, first=MIDNIGHT)
    hass.states.async_set(PRICE_ID, "0.21")
    contract = gas_contract_subentry(
        "Gas", pricing=PRICING_ENTITY, price_entity=PRICE_ID, fixed_per_year=0.0
    )
    entry = await setup_entry(
        hass, make_entry([BASE_CONTRACT, contract], options=GAS_ONLY)
    )
    answer = await heating(hass, hass_ws_client, entry)
    assert answer["totals"]["heating_cost"] == pytest.approx(
        0.2 * sum(gas_home), abs=0.01
    )
    assert answer["simulator"]["gas_price"] == 0.21


@pytest.mark.usefixtures("sources")
async def test_gas_days_at_the_mean_price_of_a_sensor(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await add_statistic(hass, first=MIDNIGHT, values=[250.0] * 48)
    # Days only known in total.
    await add_energy(hass, GAS, [30.0, 40.0], hours=24)
    # 0.1 € the first 12 hours, 0.3 € the next 12: 0.2 € on average.
    await add_price(hass, ([0.1] * 12 + [0.3] * 12) * 2, first=MIDNIGHT)
    contract = gas_contract_subentry(
        "Gas", pricing=PRICING_ENTITY, price_entity=PRICE_ID, fixed_per_year=365.0
    )
    entry = await setup_entry(
        hass, make_entry([BASE_CONTRACT, contract], options=GAS_ONLY)
    )
    answer = await heating(hass, hass_ws_client, entry, "2026-03-02", "2026-03-03")
    assert [day["heating_cost"] for day in answer["days"]] == [
        pytest.approx(30 * 0.2 + 1.0),
        pytest.approx(40 * 0.2 + 1.0),
    ]


@pytest.mark.usefixtures("sources", "gas_home")
async def test_gas_without_a_contract_in_force(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    contract = gas_contract_subentry(
        "Gas",
        pricing=PRICING_OFFICIAL,
        active_from="2026-04-01",
    )
    entry = await setup_entry(
        hass, make_entry([BASE_CONTRACT, contract], options=GAS_ONLY)
    )
    answer = await heating(hass, hass_ws_client, entry)
    assert answer["totals"]["heating_cost"] is None
    # Today, it is in force.
    assert answer["simulator"]["gas_price"] == 0.1


@pytest.mark.usefixtures("sources")
async def test_one_gas_subscription_for_heating_and_hot_water(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await add_statistic(hass, first=MIDNIGHT, values=[250.0] * 24 * DAYS)
    await add_energy(hass, GAS, hourly([20.0] * DAYS))
    await add_energy(hass, WATER, hourly([5.0] * DAYS))
    # 0.1 € a kWh, and 365 € a year: 1 € a day.
    contract = gas_contract_subentry(
        "Gas", periods=[gas_period(0.1, "2026-01-01", fixed=365.0)]
    )
    entry = await setup_entry(
        hass,
        make_entry(
            [BASE_CONTRACT, contract],
            options={
                SECTION_HEATING: {
                    CONF_HEATING_STATISTICS: [GAS],
                    CONF_HEATING_ENERGY: ENERGY_GAS,
                    CONF_WATER_STATISTIC: WATER,
                    CONF_WATER_ENERGY: ENERGY_GAS,
                },
            },
        ),
    )
    totals = (await heating(hass, hass_ws_client, entry))["totals"]
    # The subscription goes with the heating, once.
    assert totals["heating_cost"] == pytest.approx(0.1 * 20.0 * DAYS + DAYS, abs=0.01)
    assert totals["water_cost"] == pytest.approx(0.1 * 5.0 * DAYS, abs=0.01)
