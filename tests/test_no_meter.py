"""Tests of a source without an electricity meter."""

from datetime import date
from typing import Any

import pytest
from homeassistant.components.recorder.statistics import async_list_statistic_ids
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.electricity_contracts.const import (
    CONF_HEATING_ENERGY,
    CONF_HEATING_STATISTICS,
    CONF_TEMPERATURE,
    CONF_WEATHER,
    DOMAIN,
    ENERGY_GAS,
    SECTION_HEATING,
)

from .conftest import (
    TEMPERATURE_ID,
    TEMPO_CONTRACT,
    Sources,
    add_statistic,
    make_entry,
)
from .test_comparison import setup_entry
from .test_heating import (
    BASE_CONTRACT,
    DAYS,
    GAS,
    GAS_OPTIONS,
    HEATER_A,
    HEATER_B,
    add_energy,
    gas_home,  # noqa: F401 - a fixture
    gas_price,
    heating,
    hourly,
)
from .test_websocket import result

GAS_ONLY: dict[str, Any] = {
    CONF_TEMPERATURE: TEMPERATURE_ID,
    SECTION_HEATING: {
        CONF_HEATING_STATISTICS: [GAS],
        CONF_HEATING_ENERGY: ENERGY_GAS,
    },
}


async def own_statistics(hass: HomeAssistant) -> list[str]:
    found = await async_list_statistic_ids(hass)
    return sorted(item["statistic_id"] for item in found if item["source"] == DOMAIN)


async def entries(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> list[dict[str, Any]]:
    answer: list[dict[str, Any]] = await result(
        hass_ws_client, hass, type=f"{DOMAIN}/entries"
    )
    return answer


@pytest.mark.usefixtures("sources")
async def test_prices_and_tempo_without_a_meter(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT], statistic_id=None))
    # Nothing to cost, nothing written.
    assert await own_statistics(hass) == []
    [listed] = await entries(hass, hass_ws_client)
    assert listed["meter"] is False
    assert listed["first_day"] is None
    assert listed["last_day"] is None
    assert listed["heating"] is None
    assert listed["inputs"]["meter"] is None
    assert [contract["id"] for contract in listed["contracts"]] == ["tempo001"]

    outlook = await result(
        hass_ws_client, hass, type=f"{DOMAIN}/outlook", entry_id=entry.entry_id
    )
    assert outlook["contract"]["name"] == "Tempo"
    assert outlook["prices"]
    assert outlook["season"] is None

    insights = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/insights",
        entry_id=entry.entry_id,
        start="2026-11-01",
        end="2026-11-07",
    )
    assert insights["days"] == []
    tempo = insights["tempo"]
    assert tempo["season"]["red_total"] == 22
    # No consumption to estimate tomorrow from.
    assert tempo["tomorrow_estimate"] is None

    # The price sensors work too.
    assert hass.states.async_entity_ids("sensor")


@pytest.mark.usefixtures("statistic", "sources")
async def test_a_meter_without_contract_in_force_has_no_tempo(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(hass, make_entry([]))
    insights = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/insights",
        entry_id=entry.entry_id,
        start="2026-11-01",
        end="2026-11-07",
    )
    assert insights["tempo"] is None


@pytest.mark.usefixtures("sources")
async def test_gas_heating_without_a_meter(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    gas = [10.0 + day for day in range(DAYS)]
    await add_energy(hass, GAS, hourly(gas))
    entry = await setup_entry(
        hass,
        make_entry(
            [BASE_CONTRACT, gas_price(0.1, "2026-01-01")],
            options=GAS_ONLY,
            statistic_id=None,
        ),
    )
    # The days come from the heating statistics.
    assert entry.runtime_data.data.sources.first_day == date(2026, 3, 2)
    [listed] = await entries(hass, hass_ws_client)
    assert listed["first_day"] == "2026-03-02"
    assert listed["last_day"] == "2026-03-17"
    assert listed["heating"] == {
        "measured": True,
        "gas": True,
        "with_water": False,
        "indoor": False,
    }

    answer = await heating(hass, hass_ws_client, entry, "2026-03-01", "2026-12-31")
    totals = answer["totals"]
    assert totals["heating"] == pytest.approx(sum(gas))
    assert totals["heating_cost"] == pytest.approx(0.1 * sum(gas), abs=0.01)
    assert totals["house"] == 0
    # The rest of the home is unknown.
    assert totals["share"] is None
    assert len(answer["days"]) == DAYS


@pytest.mark.usefixtures("sources")
async def test_electric_heaters_without_a_meter(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await add_energy(hass, HEATER_A, hourly([24.0] * DAYS))
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT],
            options={SECTION_HEATING: {CONF_HEATING_STATISTICS: [HEATER_A]}},
            statistic_id=None,
        ),
    )
    answer = await heating(hass, hass_ws_client, entry)
    totals = answer["totals"]
    assert totals["heating"] == pytest.approx(24.0 * DAYS)
    # Costed at the contract's prices, hour by hour.
    assert totals["heating_cost"] > 0
    assert totals["share"] is None
    assert answer["tranches"]


@pytest.mark.usefixtures("sources")
async def test_heating_statistics_without_data(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(
        hass,
        make_entry([BASE_CONTRACT], options=GAS_OPTIONS, statistic_id=None),
    )
    assert entry.runtime_data.data.heating_end is None
    [listed] = await entries(hass, hass_ws_client)
    assert listed["first_day"] is None
    assert listed["last_day"] is None
    answer = await heating(hass, hass_ws_client, entry)
    assert answer["days"] == []


@pytest.mark.usefixtures("sources")
async def test_no_estimate_without_a_meter(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    # An outdoor temperature alone estimates the heating from the meter.
    await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT],
            options={CONF_TEMPERATURE: TEMPERATURE_ID},
            statistic_id=None,
        ),
    )
    [listed] = await entries(hass, hass_ws_client)
    assert listed["heating"] is None


@pytest.mark.usefixtures("sources")
async def test_open_meteo_without_a_meter(
    hass: HomeAssistant, sources: Sources
) -> None:
    await add_energy(hass, GAS, hourly([10.0] * DAYS))
    await setup_entry(
        hass,
        make_entry(
            [BASE_CONTRACT],
            options={**GAS_ONLY, CONF_TEMPERATURE: None, CONF_WEATHER: True},
            statistic_id=None,
        ),
    )
    call = sources.weather.async_hourly_temperatures.await_args
    assert call is not None
    # From the day before the first day of the heating statistics.
    assert call.args[2] == date(2026, 3, 1)
    assert await own_statistics(hass) == [f"{DOMAIN}:no_meter_outdoor_temperature"]


@pytest.mark.usefixtures("sources")
async def test_removing_the_meter_clears_the_costs(hass: HomeAssistant) -> None:
    await add_statistic(hass)
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    assert await own_statistics(hass)
    flow = await entry.start_reconfigure_flow(hass)
    flow = await hass.config_entries.flow.async_configure(flow["flow_id"], {})
    assert flow["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)
    assert entry.runtime_data.statistic_id is None
    assert await own_statistics(hass) == []


@pytest.mark.usefixtures("sources", "gas_home")
async def test_the_heating_window_ends_with_its_statistics(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(
        hass,
        make_entry(
            [BASE_CONTRACT, gas_price(0.1, "2026-01-01")],
            options=GAS_OPTIONS,
            statistic_id=None,
        ),
    )
    # Asked until the end of next year: the warm days of the hot water are still
    # read on the year before the last hour of gas.
    answer = await heating(hass, hass_ws_client, entry, "2026-03-01", "2027-12-31")
    assert answer["water_per_day"] == 5.0
    assert answer["totals"]["water"] == pytest.approx(5.0 * DAYS)


@pytest.mark.usefixtures("sources")
async def test_the_first_day_of_any_heating_statistic(
    hass: HomeAssistant,
) -> None:
    await add_energy(hass, HEATER_A, hourly([24.0] * 4), days_later=5)
    await add_energy(hass, HEATER_B, hourly([24.0] * DAYS))
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT],
            options={SECTION_HEATING: {CONF_HEATING_STATISTICS: [HEATER_A, HEATER_B]}},
            statistic_id=None,
        ),
    )
    assert entry.runtime_data.data.sources.first_day == date(2026, 3, 2)
