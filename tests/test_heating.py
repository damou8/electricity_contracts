"""Tests of the Heating tab's command."""

from datetime import date, timedelta
from typing import Any

import pytest
from elec_tariffs import ContractKind
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import async_import_statistics
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.electricity_contracts.const import (
    CONF_HEATING_CONTENT,
    CONF_HEATING_ENERGY,
    CONF_HEATING_STATISTICS,
    CONF_INDOOR_TEMPERATURES,
    CONF_TEMPERATURE,
    CONF_WATER_ENERGY,
    CONF_WATER_STATISTIC,
    CONTENT_HEATING_WATER,
    DOMAIN,
    ENERGY_GAS,
    SECTION_HEATING,
)
from custom_components.electricity_contracts.heating import _Day, _estimated

from .conftest import (
    FIRST_HOUR,
    TEMPERATURE_ID,
    TEMPO_CONTRACT,
    TEMPO_PERIODS,
    add_statistic,
    add_temperature,
    contract_subentry,
    gas_price,
    make_entry,
)
from .test_comparison import setup_entry
from .test_websocket import command, result

# The contract of the gas home, in force.
BASE_CONTRACT = contract_subentry(
    "Base", uid="base0001", kind=ContractKind.BASE, active_from="2024-01-01"
)
HEATER_A = "sensor.heater_a"
HEATER_B = "sensor.heater_b"
GAS = "sensor.gas"
WATER = "sensor.water_heater"
INDOOR = "sensor.indoor_temperature"
# Midnight in Paris on 2 March is 23:00 UTC the day before.
MIDNIGHT = 23
DAYS = 16


async def add_energy(
    hass: HomeAssistant,
    statistic_id: str,
    kwh: list[float],
    *,
    hours: int = 1,
    days_later: int = 0,
) -> None:
    """Import the kWh of an energy sensor every `hours`, from 2 March in Paris.

    `days_later` starts it that many days after 2 March.
    """
    metadata = StatisticMetaData(
        mean_type=StatisticMeanType.NONE,
        has_sum=True,
        name=None,
        source="recorder",
        statistic_id=statistic_id,
        unit_class="energy",
        unit_of_measurement="kWh",
    )
    total = 0.0
    rows = []
    for index, value in enumerate(kwh):
        total += value
        rows.append(
            StatisticData(
                start=FIRST_HOUR
                + timedelta(days=days_later, hours=MIDNIGHT + hours * index),
                state=total,
                sum=total,
            )
        )
    async_import_statistics(hass, metadata, rows)
    await async_wait_recording_done(hass)


async def add_indoor(hass: HomeAssistant, means: list[float]) -> None:
    """Import the hourly means of an indoor thermometer, from 2 March in Paris."""
    metadata = StatisticMetaData(
        mean_type=StatisticMeanType.ARITHMETIC,
        has_sum=False,
        name="Indoor",
        source="recorder",
        statistic_id=INDOOR,
        unit_class="temperature",
        unit_of_measurement="°C",
    )
    rows = [
        StatisticData(
            start=FIRST_HOUR + timedelta(hours=hour), mean=mean, min=mean, max=mean
        )
        for hour, mean in enumerate(means, start=MIDNIGHT)
    ]
    async_import_statistics(hass, metadata, rows)
    await async_wait_recording_done(hass)


def hourly(per_day: list[float]) -> list[float]:
    """Spread each day's kWh evenly over its 24 hours."""
    return [value / 24 for value in per_day for _ in range(24)]


async def heating(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    entry: MockConfigEntry,
    start: str = "2026-03-02",
    end: str = "2026-03-17",
) -> dict[str, Any]:
    answer: dict[str, Any] = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/heating",
        entry_id=entry.entry_id,
        start=start,
        end=end,
    )
    return answer


@pytest.fixture
async def cold_days(hass: HomeAssistant) -> list[float]:
    """Import 16 days from 2 March: day n is 18 - n °C, the home uses 6 + 2n kWh."""
    house = [6.0 + 2 * day for day in range(DAYS)]
    await add_statistic(
        hass,
        hours=24 * DAYS,
        first=MIDNIGHT,
        values=[kwh * 1000 for kwh in hourly(house)],
    )
    await add_temperature(
        hass, [18.0 - day for day in range(DAYS) for _ in range(24)], first=MIDNIGHT
    )
    return house


@pytest.mark.usefixtures("sources")
async def test_electric_heaters(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, cold_days: list[float]
) -> None:
    # Half of every hour of the home is heating, three quarters of it in A.
    await add_energy(hass, HEATER_A, hourly([0.375 * kwh for kwh in cold_days]))
    await add_energy(hass, HEATER_B, hourly([0.125 * kwh for kwh in cold_days]))
    await add_indoor(hass, [19.5] * 24 * DAYS)
    entities = er.async_get(hass)
    areas = ar.async_get(hass)
    living = areas.async_create("Living room")
    entities.async_get_or_create(
        "sensor", "test", "a", suggested_object_id="heater_a", original_name="A"
    )
    entities.async_update_entity(HEATER_A, area_id=living.id)
    # B is named by its device's area.
    device_entry = MockConfigEntry(domain="test")
    device_entry.add_to_hass(hass)
    device = dr.async_get(hass).async_get_or_create(
        config_entry_id=device_entry.entry_id, identifiers={("test", "b")}
    )
    dr.async_get(hass).async_update_device(device.id, area_id=living.id)
    entities.async_get_or_create(
        "sensor",
        "test",
        "b",
        suggested_object_id="heater_b",
        original_name="B",
        device_id=device.id,
    )
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT],
            options={
                CONF_TEMPERATURE: TEMPERATURE_ID,
                SECTION_HEATING: {CONF_HEATING_STATISTICS: [HEATER_A, HEATER_B]},
                CONF_INDOOR_TEMPERATURES: [INDOOR],
            },
        ),
    )
    answer = await heating(hass, hass_ws_client, entry)

    assert answer["measured"] is True
    assert answer["gas"] is False
    assert answer["water_split"] is False
    assert answer["has_indoor"] is True
    assert len(answer["days"]) == DAYS
    first = answer["days"][0]
    assert first["temperature"] == 18.0
    assert first["indoor"] == 19.5
    assert first["heating"] == pytest.approx(3.0)
    assert first["house"] == pytest.approx(6.0)

    totals = answer["totals"]
    house = sum(cold_days)
    assert totals["heating"] == pytest.approx(house / 2)
    assert totals["house"] == pytest.approx(house)
    assert totals["share"] == pytest.approx(0.5)
    # Every hour of heating is half an hour of the home: half its cost too.
    assert totals["heating_cost"] == pytest.approx(totals["house_cost"] / 2, abs=0.02)
    assert answer["estimated"] is None

    tranches = answer["tranches"]
    assert sum(item["energy"] for item in tranches.values()) == pytest.approx(
        totals["heating"]
    )
    assert sum(item["cost"] for item in tranches.values()) == pytest.approx(
        totals["heating_cost"], abs=0.05
    )
    assert answer["statistics"] == [
        {
            "id": HEATER_A,
            "name": "A",
            "area": "Living room",
            "energy": pytest.approx(0.75 * house / 2),
        },
        {
            "id": HEATER_B,
            "name": "B",
            "area": "Living room",
            "energy": pytest.approx(0.25 * house / 2),
        },
    ]
    assert answer["profile"] == [pytest.approx(house / 2 / DAYS / 24, abs=1e-3)] * 24
    # 3 + n kWh a day at 18 - n °C.
    assert answer["weather"]["slope"] == pytest.approx(1.0)
    assert answer["weather"]["intercept"] == pytest.approx(3.0)

    simulator = answer["simulator"]
    assert simulator["indoor"] == 19.5
    assert simulator["outdoor"] == 10.5
    # Off-peak from 22:00 to 6:00: a third of evenly spread hours.
    assert simulator["off_peak_share"] == pytest.approx(1 / 3, abs=1e-3)
    assert simulator["kind"] == "tempo"
    assert simulator["prices"] == {
        tranche.value: price for tranche, price in TEMPO_PERIODS[1].prices.items()
    }
    assert simulator["gas_price"] is None


@pytest.mark.usefixtures("sources")
async def test_estimated_from_the_source(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, cold_days: list[float]
) -> None:
    entry = await setup_entry(
        hass,
        make_entry([TEMPO_CONTRACT], options={CONF_TEMPERATURE: TEMPERATURE_ID}),
    )
    answer = await heating(hass, hass_ws_client, entry)

    assert answer["measured"] is False
    assert answer["totals"] is None
    # 2 kWh a degree day, over 0 + 1 + … + 15 degree days.
    estimated = answer["estimated"]
    assert estimated["heating"] == pytest.approx(2 * sum(range(DAYS)))
    assert estimated["share"] == pytest.approx(
        2 * sum(range(DAYS)) / sum(cold_days), abs=1e-4
    )
    assert estimated["heating_cost"] > 0
    assert answer["simulator"]["indoor"] is None
    assert answer["simulator"]["off_peak_share"] == pytest.approx(1 / 3, abs=1e-3)


@pytest.mark.usefixtures("statistic", "sources")
async def test_estimate_needs_a_fit(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(
        hass,
        make_entry([TEMPO_CONTRACT], options={CONF_TEMPERATURE: TEMPERATURE_ID}),
    )
    answer = await heating(hass, hass_ws_client, entry, "2026-03-01", "2026-03-02")
    # No temperature recorded: nothing to estimate from.
    assert answer["estimated"] is None
    assert answer["weather"]["slope"] is None


@pytest.fixture
async def gas_home(hass: HomeAssistant) -> list[float]:
    """Import 16 days of gas: 8 warm days at 20 °C, then 8 from 17 °C down to 10 °C.

    The hot water takes 5 kWh a day, more on 3 of the warm days; heating 4 kWh a
    degree day.
    """
    temperatures = [20.0] * 8 + [17.0 - day for day in range(8)]
    water = [5.0] * 5 + [9.0] * 3 + [5.0] * 8
    gas = [water[day] + 4 * max(0.0, 18 - temperatures[day]) for day in range(DAYS)]
    await add_statistic(hass, first=MIDNIGHT, values=[250.0] * 24 * DAYS)
    await add_temperature(
        hass, [value for value in temperatures for _ in range(24)], first=MIDNIGHT
    )
    await add_energy(hass, GAS, hourly(gas))
    return gas


GAS_OPTIONS: dict[str, Any] = {
    CONF_TEMPERATURE: TEMPERATURE_ID,
    SECTION_HEATING: {
        CONF_HEATING_STATISTICS: [GAS],
        CONF_HEATING_ENERGY: ENERGY_GAS,
        CONF_HEATING_CONTENT: CONTENT_HEATING_WATER,
    },
}


@pytest.mark.usefixtures("sources")
async def test_gas_with_hot_water(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, gas_home: list[float]
) -> None:
    entry = await setup_entry(
        hass,
        make_entry([BASE_CONTRACT, gas_price(0.1, "2026-01-01")], options=GAS_OPTIONS),
    )
    answer = await heating(hass, hass_ws_client, entry)

    assert answer["gas"] is True
    assert answer["water_split"] is True
    assert answer["water_measured"] is False
    assert answer["water_gas"] is True
    # The median of the warm days, the 3 showers aside: from 18 °C, or from
    # where the heating starts when that's higher.
    assert answer["water_per_day"] == 5.0
    assert answer["water_warm_from"] == max(18.0, answer["weather"]["base"])
    totals = answer["totals"]
    # Each day gives up to 5 kWh of hot water: all days use more.
    assert totals["water"] == pytest.approx(5.0 * DAYS)
    assert totals["heating"] == pytest.approx(sum(gas_home) - 5.0 * DAYS)
    assert totals["heating_cost"] == pytest.approx(0.1 * totals["heating"], abs=0.01)
    assert totals["water_cost"] == pytest.approx(0.5 * DAYS, abs=0.01)
    assert totals["house"] == pytest.approx(6.0 * DAYS)
    assert totals["share"] == pytest.approx(
        totals["heating"] / (sum(gas_home) + 6.0 * DAYS), abs=1e-4
    )
    assert answer["tranches"] is None
    assert answer["average_price"] == pytest.approx(0.1)
    simulator = answer["simulator"]
    assert simulator["gas_price"] == 0.1
    assert simulator["kind"] is None
    assert simulator["prices"] is None
    # The off-peak share of the source: none under a Base contract.
    assert simulator["off_peak_share"] == 0

    # Over the cold days only, the hot water is still read on the warm ones.
    cold = await heating(hass, hass_ws_client, entry, "2026-03-10", "2026-03-17")
    assert cold["water_per_day"] == 5.0
    assert cold["totals"]["water"] == pytest.approx(5.0 * 8)


@pytest.mark.usefixtures("sources")
async def test_gas_without_price_or_warm_days(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, gas_home: list[float]
) -> None:
    # A price that ends before the window: the gas is not costed.
    entry = await setup_entry(
        hass,
        make_entry(
            [BASE_CONTRACT, gas_price(0.1, "2025-01-01", "2025-12-31")],
            options=GAS_OPTIONS,
        ),
    )
    answer = await heating(hass, hass_ws_client, entry, "2026-03-10", "2026-03-17")
    totals = answer["totals"]
    assert totals["heating_cost"] is None
    assert totals["water_cost"] is None
    assert answer["average_price"] is None
    assert answer["simulator"]["gas_price"] is None
    assert [day["heating_cost"] for day in answer["days"]] == [None] * 8


@pytest.mark.usefixtures("sources")
async def test_gas_hot_water_needs_warm_days(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await add_statistic(hass, first=MIDNIGHT, values=[250.0] * 24 * 4)
    await add_temperature(hass, [5.0] * 24 * 4, first=MIDNIGHT)
    await add_energy(hass, GAS, hourly([60.0] * 4))
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT], options=GAS_OPTIONS))
    answer = await heating(hass, hass_ws_client, entry, "2026-03-02", "2026-03-05")
    # Not a warm day in the year: the hot water stays in the heating.
    assert answer["water_split"] is False
    assert answer["water_per_day"] is None
    assert answer["totals"]["heating"] == pytest.approx(240.0)
    assert answer["totals"]["water"] == 0


@pytest.mark.usefixtures("sources")
async def test_measured_water_inside_the_heating(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, cold_days: list[float]
) -> None:
    # The heater's statistic counts the water heater, measured on its own.
    await add_energy(hass, HEATER_A, hourly([0.5 * kwh for kwh in cold_days]))
    await add_energy(hass, WATER, hourly([1.0] * DAYS))
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT],
            options={
                CONF_TEMPERATURE: TEMPERATURE_ID,
                SECTION_HEATING: {
                    CONF_HEATING_STATISTICS: [HEATER_A],
                    CONF_HEATING_CONTENT: CONTENT_HEATING_WATER,
                    CONF_WATER_STATISTIC: WATER,
                },
            },
        ),
    )
    answer = await heating(hass, hass_ws_client, entry)
    assert answer["water_measured"] is True
    assert answer["water_split"] is True
    assert answer["water_gas"] is False
    assert answer["water_per_day"] is None
    totals = answer["totals"]
    assert totals["water"] == pytest.approx(DAYS)
    assert totals["heating"] == pytest.approx(sum(cold_days) / 2 - DAYS)
    # The fit is made on the heating alone.
    assert answer["weather"]["intercept"] == pytest.approx(2.0)


@pytest.mark.usefixtures("sources")
async def test_gas_water_heater_beside_electric_heating(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, cold_days: list[float]
) -> None:
    await add_energy(hass, HEATER_A, hourly([0.5 * kwh for kwh in cold_days]))
    await add_energy(hass, WATER, hourly([4.0] * DAYS))
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT, gas_price(0.1, "2026-01-01")],
            options={
                SECTION_HEATING: {
                    CONF_HEATING_STATISTICS: [HEATER_A],
                    CONF_WATER_STATISTIC: WATER,
                    CONF_WATER_ENERGY: ENERGY_GAS,
                },
            },
        ),
    )
    answer = await heating(hass, hass_ws_client, entry)
    # Not inside the heating: nothing taken out of it.
    assert answer["water_gas"] is True
    totals = answer["totals"]
    assert totals["heating"] == pytest.approx(sum(cold_days) / 2)
    assert totals["water"] == pytest.approx(4.0 * DAYS)
    assert totals["water_cost"] == pytest.approx(0.4 * DAYS, abs=0.01)
    assert answer["has_outdoor"] is False
    assert answer["weather"] is None


@pytest.mark.usefixtures("statistic", "sources")
async def test_heating_unknown_entry(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    response = await command(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/heating",
        entry_id="nope",
        start="2026-03-01",
        end="2026-03-02",
    )
    assert response["success"] is False


@pytest.mark.usefixtures("statistic", "sources")
async def test_heating_before_the_data(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT],
            options={SECTION_HEATING: {CONF_HEATING_STATISTICS: [HEATER_A]}},
        ),
    )
    answer = await heating(hass, hass_ws_client, entry, "2025-01-01", "2025-01-31")
    assert answer["days"] == []
    assert answer["totals"]["heating"] == 0
    assert answer["totals"]["share"] is None
    assert answer["profile"] is None
    assert answer["statistics"] == [
        {"id": HEATER_A, "name": HEATER_A, "area": None, "energy": 0}
    ]


@pytest.mark.usefixtures("statistic", "sources")
async def test_entries_tell_the_heating(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    # Gazpar: one row a day; the outdoor sensor, one an hour.
    await add_energy(hass, GAS, [30.0] * 3, hours=24)
    await add_temperature(hass, [10.0] * 3)
    await setup_entry(hass, make_entry([TEMPO_CONTRACT], options=GAS_OPTIONS))
    [entry] = await result(hass_ws_client, hass, type=f"{DOMAIN}/entries")
    assert entry["heating"] == {
        "measured": True,
        "gas": True,
        "with_water": True,
        "indoor": False,
    }
    assert entry["inputs"] == {
        "meter": "linky",
        "meter_step": "hour",
        "heating": [GAS],
        "water": None,
        "outdoor": TEMPERATURE_ID,
        "indoor": [],
        "steps": {GAS: "day", TEMPERATURE_ID: "hour"},
    }


@pytest.mark.usefixtures("sources")
async def test_gas_read_once_a_day(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    # A meter read once a day, written at midnight: only kWh by day.
    await add_statistic(hass, first=MIDNIGHT, values=[250.0] * 24 * 4)
    await add_energy(hass, GAS, [30.0, 40.0, 50.0, 60.0], hours=24)
    entry = await setup_entry(
        hass,
        make_entry(
            [BASE_CONTRACT, gas_price(0.1, "2026-03-03")],
            options={
                SECTION_HEATING: {
                    CONF_HEATING_STATISTICS: [GAS],
                    CONF_HEATING_ENERGY: ENERGY_GAS,
                    CONF_HEATING_CONTENT: CONTENT_HEATING_WATER,
                },
            },
        ),
    )
    answer = await heating(hass, hass_ws_client, entry, "2026-03-02", "2026-03-05")
    assert [day["heating"] for day in answer["days"]] == [30.0, 40.0, 50.0, 60.0]
    # The first day is before the price.
    assert [day["heating_cost"] for day in answer["days"]] == [None, 4.0, 5.0, 6.0]
    assert answer["totals"]["heating_cost"] is None
    # No hours, no typical day.
    assert answer["profile"] is None
    # No outdoor temperature: the hot water can't be told apart.
    assert answer["water_split"] is False


@pytest.mark.usefixtures("statistic", "sources")
async def test_heating_window_must_be_in_order(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT], options=GAS_OPTIONS))
    response = await command(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/heating",
        entry_id=entry.entry_id,
        start="2026-03-02",
        end="2026-03-01",
    )
    assert response["success"] is False


@pytest.mark.usefixtures("sources")
async def test_hot_water_needs_seven_warm_days(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    # 6 warm days are not enough to tell what a day without heating uses.
    temperatures = [20.0] * 6 + [10.0] * 4
    await add_statistic(hass, first=MIDNIGHT, values=[250.0] * 24 * 10)
    await add_temperature(
        hass, [value for value in temperatures for _ in range(24)], first=MIDNIGHT
    )
    await add_energy(hass, GAS, hourly([5.0] * 6 + [40.0] * 4))
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT], options=GAS_OPTIONS))
    answer = await heating(hass, hass_ws_client, entry, "2026-03-02", "2026-03-11")
    assert answer["water_split"] is False
    assert answer["totals"]["heating"] == pytest.approx(190.0)


@pytest.mark.usefixtures("sources")
async def test_gas_heating_with_an_electric_water_heater(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, gas_home: list[float]
) -> None:
    # The water heater is electric: part of the source, not of the gas.
    await add_energy(hass, WATER, hourly([2.0] * DAYS))
    entry = await setup_entry(
        hass,
        make_entry(
            [BASE_CONTRACT, gas_price(0.1, "2026-01-01")],
            options={
                CONF_TEMPERATURE: TEMPERATURE_ID,
                SECTION_HEATING: {
                    CONF_HEATING_STATISTICS: [GAS],
                    CONF_HEATING_ENERGY: ENERGY_GAS,
                    CONF_WATER_STATISTIC: WATER,
                },
            },
        ),
    )
    answer = await heating(hass, hass_ws_client, entry)
    assert answer["water_gas"] is False
    totals = answer["totals"]
    assert totals["heating"] == pytest.approx(sum(gas_home))
    assert totals["water"] == pytest.approx(2.0 * DAYS)
    # The electric hot water is in the source already: not counted twice.
    assert totals["share"] == pytest.approx(
        sum(gas_home) / (sum(gas_home) + 6.0 * DAYS), abs=1e-4
    )


@pytest.mark.usefixtures("sources")
async def test_water_of_another_energy_stays_in_the_heating(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, gas_home: list[float]
) -> None:
    # Options the form refuses: the gas holds hot water, the water heater is
    # electric. Nothing electric is taken out of the gas.
    await add_energy(hass, WATER, hourly([2.0] * DAYS))
    entry = await setup_entry(
        hass,
        make_entry(
            [BASE_CONTRACT],
            options={
                **GAS_OPTIONS,
                SECTION_HEATING: {
                    **GAS_OPTIONS[SECTION_HEATING],
                    CONF_WATER_STATISTIC: WATER,
                },
            },
        ),
    )
    answer = await heating(hass, hass_ws_client, entry)
    assert answer["totals"]["heating"] == pytest.approx(sum(gas_home))
    assert answer["water_per_day"] is None


@pytest.mark.usefixtures("sources")
async def test_off_peak_share_of_hphc(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, cold_days: list[float]
) -> None:
    await add_energy(hass, HEATER_A, hourly([0.5 * kwh for kwh in cold_days]))
    hphc = contract_subentry(
        "HP/HC", uid="hphc0001", kind=ContractKind.HPHC, active_from="2024-01-01"
    )
    entry = await setup_entry(
        hass,
        make_entry(
            [hphc],
            options={SECTION_HEATING: {CONF_HEATING_STATISTICS: [HEATER_A]}},
        ),
    )
    answer = await heating(hass, hass_ws_client, entry)
    # Off-peak from 22:00 to 6:00: a third of evenly spread hours.
    assert answer["simulator"]["off_peak_share"] == pytest.approx(1 / 3, abs=1e-3)
    assert answer["simulator"]["kind"] == "hphc"
    assert set(answer["tranches"]) == {"hc", "hp"}


@pytest.mark.usefixtures("sources")
async def test_heating_before_the_heaters_is_estimated(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, cold_days: list[float]
) -> None:
    await hass.config.async_update(time_zone="Europe/Paris")
    # The heater only from 16 March, the 15th of the 16 cold days.
    await add_energy(hass, HEATER_A, hourly([2.0 * 14, 2.0 * 15]), days_later=14)
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT],
            options={
                CONF_TEMPERATURE: TEMPERATURE_ID,
                SECTION_HEATING: {CONF_HEATING_STATISTICS: [HEATER_A]},
            },
        ),
    )
    answer = await heating(hass, hass_ws_client, entry)
    # Measured from the heater's first day.
    assert [day["date"] for day in answer["days"]] == ["2026-03-16", "2026-03-17"]
    assert answer["totals"]["heating"] == pytest.approx(2.0 * (14 + 15))
    # The 14 days before it from the Linky: 2 kWh a degree day, n degree days on
    # day n, in kWh only.
    assert answer["before"] == {
        "start": "2026-03-02",
        "end": "2026-03-15",
        "days": 14,
        "missing": 0,
        "heating": 2.0 * sum(range(14)),
    }
    assert answer["heaters_from"] is None
    assert answer["estimated_days"][3] == {
        "date": "2026-03-05",
        "temperature": 15.0,
        "heating": pytest.approx(6.0),
    }
    assert len(answer["estimated_days"]) == 14
    assert answer["unestimated"] is None
    # From 10 March, 6 days estimated: too few to fit, the year before the
    # heater fits them.
    answer = await heating(hass, hass_ws_client, entry, start="2026-03-10")
    assert answer["before"]["heating"] == pytest.approx(2.0 * sum(range(8, 14)))
    # Wholly before the heater: estimated like a home without heating
    # statistics, from the consumption and the weather.
    answer = await heating(hass, hass_ws_client, entry, end="2026-03-15")
    assert answer["measured"] is False
    assert answer["heaters_from"] == "2026-03-16"
    assert answer["days"] == []
    assert answer["estimated"]["heating"] == pytest.approx(2.0 * sum(range(14)))


@pytest.mark.usefixtures("sources")
async def test_heating_before_the_heaters_needs_a_temperature(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await hass.config.async_update(time_zone="Europe/Paris")
    house = [6.0 + 2 * day for day in range(DAYS)]
    await add_statistic(
        hass,
        hours=24 * DAYS,
        first=MIDNIGHT,
        values=[kwh * 1000 for kwh in hourly(house)],
    )
    # The outdoor sensor and the heater from 16 March only.
    await add_temperature(hass, [4.0] * 48, first=MIDNIGHT + 24 * 14)
    await add_energy(hass, HEATER_A, hourly([28.0, 30.0]), days_later=14)
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT],
            options={
                CONF_TEMPERATURE: TEMPERATURE_ID,
                SECTION_HEATING: {CONF_HEATING_STATISTICS: [HEATER_A]},
            },
        ),
    )
    answer = await heating(hass, hass_ws_client, entry)
    assert (answer["before"], answer["estimated_days"]) == (None, [])
    assert answer["unestimated"] == {
        "start": "2026-03-02",
        "end": "2026-03-15",
        "open_meteo": False,
    }


@pytest.mark.usefixtures("sources")
async def test_gas_heating_isnt_estimated_before_its_meter(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, gas_home: list[float]
) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT], options=GAS_OPTIONS))
    answer = await heating(hass, hass_ws_client, entry)
    assert (answer["before"], answer["estimated_days"], answer["unestimated"]) == (
        None,
        [],
        None,
    )


def test_estimate_shares_only_the_days_with_a_temperature() -> None:
    weather = {"base": 18.0, "linear": 2.0, "square": 0.0, "reach": 30.0}
    house = {
        date(2026, 1, 1): _Day(energy=30.0, cost=6.0),
        date(2026, 1, 2): _Day(energy=10.0, cost=1.0),
    }
    # Only 1 January has an outdoor temperature: 10 degrees under the base.
    estimated = _estimated(weather, {date(2026, 1, 1): 8.0}, house)
    assert estimated["heating"] == pytest.approx(20.0)
    assert estimated["share"] == pytest.approx(20 / 30, abs=1e-4)
    assert estimated["heating_cost"] == pytest.approx(4.0)
