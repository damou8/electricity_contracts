"""Tests of the outdoor temperature from Open-Meteo."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from elec_tariffs import WeatherError
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.recorder.statistics import (
    get_metadata,
    statistics_during_period,
)
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.recorder import get_instance
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.electricity_contracts.const import (
    CONF_STATISTIC_ID,
    CONF_TEMPERATURE,
    CONF_WEATHER,
    DOMAIN,
)
from custom_components.electricity_contracts.data import Heating
from custom_components.electricity_contracts.weather import (
    outdoor_fill,
    outdoor_source,
    outdoor_statistic,
)

from .conftest import (
    FIRST_HOUR,
    NOW,
    OTHER_STATISTIC_ID,
    TEMPERATURE_ID,
    TEMPO_CONTRACT,
    Sources,
    add_statistic,
    add_temperature,
    make_entry,
)
from .test_comparison import setup_entry
from .test_websocket import result

WEATHER_ID = f"{DOMAIN}:linky_00000000000000_outdoor_temperature"
# The test home, rounded to 0.1°.
COORDINATES = (32.9, -117.2)


def weather_entry(**options: Any) -> MockConfigEntry:
    return make_entry([TEMPO_CONTRACT], options={CONF_WEATHER: True, **options})


async def hours(
    hass: HomeAssistant, statistic_id: str = WEATHER_ID
) -> dict[datetime, float | None]:
    await async_wait_recording_done(hass)
    rows = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        datetime(2026, 1, 1, tzinfo=UTC),
        None,
        {statistic_id},
        "hour",
        None,
        {"mean"},
    )
    return {
        datetime.fromtimestamp(row["start"], UTC): row["mean"]
        for row in rows.get(statistic_id, [])
    }


def asked(sources: Sources) -> list[tuple[Any, ...]]:
    return [
        call.args for call in sources.weather.async_hourly_temperatures.await_args_list
    ]


@pytest.mark.usefixtures("statistic")
async def test_the_temperature_is_written_as_a_statistic(
    hass: HomeAssistant, sources: Sources
) -> None:
    entry = await setup_entry(hass, weather_entry())
    # From the day before the first day of consumption, at the rounded location.
    assert asked(sources) == [(*COORDINATES, date(2026, 2, 28), date(2026, 11, 7))]
    written = await hours(hass)
    assert min(written) == NOW - timedelta(days=3)
    # The current hour isn't over: it waits.
    assert max(written) == NOW - timedelta(hours=1)
    assert set(written.values()) == {10.0}
    metadata = await get_instance(hass).async_add_executor_job(
        lambda: get_metadata(hass, statistic_ids={WEATHER_ID})
    )
    assert metadata[WEATHER_ID][1]["unit_of_measurement"] == "°C"
    assert metadata[WEATHER_ID][1]["name"] == "Outdoor temperature (Open-Meteo)"
    assert outdoor_statistic(entry) == WEATHER_ID
    assert outdoor_source(entry) == "open_meteo"
    heating = Heating.from_options(entry.options, outdoor=outdoor_statistic(entry))
    assert heating.shown


@pytest.mark.usefixtures("statistic")
async def test_the_last_days_are_asked_again(
    hass: HomeAssistant, sources: Sources, freezer: FrozenDateTimeFactory
) -> None:
    entry = await setup_entry(hass, weather_entry())
    freezer.tick(timedelta(hours=1))
    await entry.runtime_data.async_refresh()
    # A week before the last hour written, revised since.
    assert asked(sources)[-1] == (*COORDINATES, date(2026, 10, 31), date(2026, 11, 7))
    assert max(await hours(hass)) == NOW


@pytest.mark.usefixtures("statistic")
async def test_older_data_asks_the_days_before(
    hass: HomeAssistant, sources: Sources
) -> None:
    entry = await setup_entry(hass, weather_entry())
    coordinator = entry.runtime_data
    # Older consumption imported, found again at the next setup.
    coordinator._first_day = date(2026, 1, 1)
    await coordinator.async_refresh()
    assert asked(sources)[-1] == (*COORDINATES, date(2025, 12, 31), date(2026, 11, 7))
    await coordinator.async_refresh()
    assert asked(sources)[-1][2] == date(2026, 10, 31)


@pytest.mark.usefixtures("statistic")
async def test_a_sensor_comes_first(hass: HomeAssistant, sources: Sources) -> None:
    entry = await setup_entry(
        hass, make_entry(options={CONF_TEMPERATURE: TEMPERATURE_ID})
    )
    assert asked(sources) == []
    assert outdoor_statistic(entry) == TEMPERATURE_ID
    assert outdoor_fill(entry) is None
    assert outdoor_source(entry) == "sensor"


# 6 November 2026 at midnight, French time: the sensor's first hour.
SENSOR_START = datetime(2026, 11, 5, 23, tzinfo=UTC)


async def test_open_meteo_gives_the_days_before_the_sensor(
    hass: HomeAssistant,
    sources: Sources,
    hass_ws_client: WebSocketGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    # Consumption from 4 November, French time, to now.
    first_hour = datetime(2026, 11, 3, 23, tzinfo=UTC)
    await add_statistic(
        hass,
        hours=int((NOW - first_hour) / timedelta(hours=1)),
        first=int((first_hour - FIRST_HOUR) / timedelta(hours=1)),
    )
    await add_temperature(
        hass,
        [5.0] * int((NOW - SENSOR_START) / timedelta(hours=1)),
        first=int((SENSOR_START - FIRST_HOUR) / timedelta(hours=1)),
    )
    entry = await setup_entry(hass, weather_entry(**{CONF_TEMPERATURE: TEMPERATURE_ID}))
    assert outdoor_statistic(entry) == TEMPERATURE_ID
    assert outdoor_fill(entry) == WEATHER_ID
    # Up to the sensor's first day only.
    assert asked(sources) == [(*COORDINATES, date(2026, 11, 3), date(2026, 11, 5))]
    written = await hours(hass)
    assert max(written) == SENSOR_START - timedelta(hours=1)
    [listed] = await result(hass_ws_client, hass, type=f"{DOMAIN}/entries")
    assert listed["outdoor"] == "sensor"
    assert listed["outdoor_fill_until"] == "2026-11-06"

    # The days before the sensor read Open-Meteo, the others the sensor.
    insights = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/insights",
        entry_id=entry.entry_id,
        start="2026-11-04",
        end="2026-11-06",
    )
    assert [(day["date"], day["temperature"]) for day in insights["days"]] == [
        ("2026-11-04", 10.0),
        ("2026-11-05", 10.0),
        ("2026-11-06", 5.0),
    ]

    heating = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/heating",
        entry_id=entry.entry_id,
        start="2026-11-04",
        end="2026-11-06",
    )
    # Its weather line reads the three days: (10 + 10 + 5) / 3.
    assert heating["weather"]["days"] == 3
    assert heating["weather"]["mean_temperature"] == 8.3

    # Within a week, the last days are asked again, still up to the sensor.
    freezer.tick(timedelta(hours=1))
    await entry.runtime_data.async_refresh()
    assert asked(sources)[-1] == (*COORDINATES, date(2026, 10, 29), date(2026, 11, 5))
    assert max(await hours(hass)) == SENSOR_START - timedelta(hours=1)


async def test_days_long_before_now_are_not_asked_again(
    hass: HomeAssistant, sources: Sources, freezer: FrozenDateTimeFactory
) -> None:
    await add_statistic(hass)
    # The sensor starts on 20 October, French time.
    sensor_start = datetime(2026, 10, 19, 22, tzinfo=UTC)
    await add_temperature(
        hass,
        [5.0] * int((NOW - sensor_start) / timedelta(hours=1)),
        first=int((sensor_start - FIRST_HOUR) / timedelta(hours=1)),
    )

    async def every_hour(
        latitude: float, longitude: float, start: date, end: date
    ) -> dict[datetime, float]:
        del latitude, longitude
        first = datetime(start.year, start.month, start.day, tzinfo=UTC)
        last = datetime(end.year, end.month, end.day, 23, tzinfo=UTC)
        count = int((last - first) / timedelta(hours=1)) + 1
        return {first + timedelta(hours=hour): 10.0 for hour in range(count)}

    sources.weather.async_hourly_temperatures.side_effect = every_hour
    entry = await setup_entry(hass, weather_entry(**{CONF_TEMPERATURE: TEMPERATURE_ID}))
    assert asked(sources) == [(*COORDINATES, date(2026, 2, 28), date(2026, 10, 19))]
    assert max(await hours(hass)) == sensor_start - timedelta(hours=1)
    # Every hour before the sensor is written, and too old to be revised.
    freezer.tick(timedelta(hours=1))
    await entry.runtime_data.async_refresh()
    assert len(asked(sources)) == 1


@pytest.mark.usefixtures("statistic", "sources")
async def test_a_sensor_older_than_the_consumption_needs_no_fill(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await add_temperature(hass, [5.0] * 24)
    await setup_entry(hass, weather_entry(**{CONF_TEMPERATURE: TEMPERATURE_ID}))
    [listed] = await result(hass_ws_client, hass, type=f"{DOMAIN}/entries")
    assert listed["outdoor_fill_until"] is None


async def test_without_any_outdoor_temperature(hass: HomeAssistant) -> None:
    entry = make_entry()
    assert outdoor_statistic(entry) is None
    assert outdoor_source(entry) is None


@pytest.mark.usefixtures("statistic", "sources")
async def test_turning_it_off_clears_the_statistic(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = await setup_entry(hass, weather_entry())
    store = f"{DOMAIN}.{entry.entry_id}.weather"
    assert hass_storage[store]["data"] == {
        "statistic_id": WEATHER_ID,
        "coordinates": list(COORDINATES),
        "first_day": "2026-02-28",
        # No sensor: up to now.
        "until": None,
    }
    hass.config_entries.async_update_entry(entry, options={})
    await hass.async_block_till_done()
    assert await hours(hass) == {}
    assert store not in hass_storage


@pytest.mark.usefixtures("statistic")
async def test_a_new_location_writes_everything_again(
    hass: HomeAssistant, sources: Sources
) -> None:
    entry = await setup_entry(hass, weather_entry())

    async def last_day(
        latitude: float, longitude: float, start: date, end: date
    ) -> dict[datetime, float]:
        del latitude, longitude, start, end
        return {NOW - timedelta(hours=hour): 5.0 for hour in range(1, 25)}

    sources.weather.async_hourly_temperatures.side_effect = last_day
    hass.config.latitude = 45.04
    await entry.runtime_data.async_refresh()
    assert asked(sources)[-1] == (45.0, -117.2, date(2026, 2, 28), date(2026, 11, 7))
    # The hours of the old location are gone.
    written = await hours(hass)
    assert min(written) == NOW - timedelta(hours=24)
    assert set(written.values()) == {5.0}


@pytest.mark.usefixtures("statistic", "sources")
async def test_another_meter_clears_the_former_statistic(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = await setup_entry(hass, weather_entry())
    assert await hours(hass)
    await add_statistic(hass, OTHER_STATISTIC_ID)
    # Reconfigured after a meter change: the statistic's ID follows the source.
    hass.config_entries.async_update_entry(
        entry,
        unique_id=OTHER_STATISTIC_ID,
        data={CONF_STATISTIC_ID: OTHER_STATISTIC_ID},
    )
    await hass.async_block_till_done(wait_background_tasks=True)
    assert await hours(hass) == {}
    other = f"{DOMAIN}:linky_11111111111111_outdoor_temperature"
    assert (
        hass_storage[f"{DOMAIN}.{entry.entry_id}.weather"]["data"]["statistic_id"]
        == other
    )
    assert await hours(hass, other)


@pytest.mark.usefixtures("statistic", "sources")
async def test_removing_after_a_meter_change_clears_both(
    hass: HomeAssistant,
) -> None:
    entry = await setup_entry(hass, weather_entry())
    await hass.config_entries.async_unload(entry.entry_id)
    # Reconfigured, then removed before an update wrote the new statistic.
    hass.config_entries.async_update_entry(
        entry,
        unique_id=OTHER_STATISTIC_ID,
        data={CONF_STATISTIC_ID: OTHER_STATISTIC_ID},
    )
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert await hours(hass) == {}


@pytest.mark.usefixtures("statistic")
async def test_open_meteo_down_for_two_days(
    hass: HomeAssistant, sources: Sources, freezer: FrozenDateTimeFactory
) -> None:
    sources.weather.async_hourly_temperatures.side_effect = WeatherError("down")
    entry = await setup_entry(hass, weather_entry())
    coordinator = entry.runtime_data
    # The costs don't wait for the weather.
    assert coordinator.last_update_success
    assert coordinator.data.costing.actual is not None
    assert coordinator.last_errors == {"weather": "down"}
    issue_id = f"weather_unavailable_{entry.entry_id}"
    registry = ir.async_get(hass)
    assert registry.async_get_issue(DOMAIN, issue_id) is None

    freezer.tick(timedelta(hours=48))
    await coordinator.async_refresh()
    assert registry.async_get_issue(DOMAIN, issue_id) is not None

    sources.weather.async_hourly_temperatures.side_effect = Sources._temperatures
    await coordinator.async_refresh()
    assert registry.async_get_issue(DOMAIN, issue_id) is None
    assert coordinator.last_errors == {}


@pytest.mark.usefixtures("statistic")
async def test_cleared_once_home_assistant_has_started(
    hass: HomeAssistant, sources: Sources
) -> None:
    hass.set_state(CoreState.starting)
    entry = await setup_entry(hass, make_entry(options={CONF_WEATHER: True}))
    assert asked(sources) == []
    hass.set_state(CoreState.running)
    await entry.runtime_data.async_refresh()
    assert len(asked(sources)) == 1


@pytest.mark.usefixtures("statistic", "sources")
async def test_removing_the_entry_clears_the_statistic(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    entry = await setup_entry(hass, weather_entry())
    assert await hours(hass)
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert await hours(hass) == {}
    assert f"{DOMAIN}.{entry.entry_id}.weather" not in hass_storage


@pytest.mark.usefixtures("statistic", "sources")
async def test_removing_an_entry_without_weather(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.usefixtures("statistic", "sources")
async def test_the_panel_knows_the_source(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await setup_entry(hass, weather_entry())
    [entry] = await result(hass_ws_client, hass, type=f"{DOMAIN}/entries")
    assert entry["outdoor"] == "open_meteo"
    assert entry["heating"] is not None
