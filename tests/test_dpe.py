"""Tests of the energy label in the style of the DPE."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Any

import pytest
from homeassistant.components.recorder.models import StatisticData, StatisticMeanType
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockUser
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.electricity_contracts.const import (
    CONF_HEATING_STATISTICS,
    CONF_TEMPERATURE,
    CONF_WEATHER,
    DOMAIN,
    FRANCE_TIME_ZONE,
    SECTION_HEATING,
)
from custom_components.electricity_contracts.dpe import (
    DEFAULTS,
    _class,
    _year_before,
    dpe_label,
    settings_store,
)
from custom_components.electricity_contracts.heating import _Day, counted_days

from .conftest import (
    FIRST_HOUR,
    TEMPERATURE_ID,
    TEMPO_CONTRACT,
    add_temperature,
    make_entry,
)
from .test_comparison import setup_entry
from .test_heating import (
    BASE_CONTRACT,
    DAYS,
    GAS_OPTIONS,
    HEATER_A,
    add_energy,
    cold_days,  # noqa: F401 - a fixture
    gas_home,  # noqa: F401 - a fixture
    hourly,
)
from .test_websocket import command, result


def answer(**changes: Any) -> dict[str, Any]:
    """Return a heating answer: electric heating and a measured water heater."""
    base: dict[str, Any] = {
        "measured": True,
        "gas": False,
        "with_water": True,
        "water_split": True,
        "water_measured": True,
        "water_gas": False,
        "totals": {"heating": 6800.0, "water": 1900.0},
        "estimated": None,
        "weather": None,
        "days": [],
    }
    return {**base, **changes}


def uses(label: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["use"]: row for row in label["uses"]}


# The settings of a home of 100 m², the defaults for the rest.
HOME = {**DEFAULTS, "surface": 100.0}


def test_electric_heating_and_measured_water() -> None:
    label = dpe_label(answer(), HOME)
    # The auxiliaries are 5 % of the three uses: 8 700 kWh are the other 95 %.
    rows = uses(label)
    assert rows["auxiliaries"]["energy"] == pytest.approx(457.9, abs=0.1)
    assert rows["water"]["source"] == "measured"
    # 9 158 kWh x 1.9 over 100 m².
    assert label["energy"] == 174
    # 6 800 x 0.079 + 1 900 x 0.065 + 458 x 0.064, over 100 m².
    assert label["climate"] == 6.9
    assert label["classes"] == {"energy": "C", "climate": "B", "label": "C"}
    assert label["missing"] is None


def test_no_living_area_no_class() -> None:
    # The uses are still counted: the card asks for the area beside them.
    label = dpe_label(answer(), {**HOME, "surface": None})
    assert label["classes"] is None
    assert label["missing"] == "surface"
    assert uses(label) == uses(dpe_label(answer(), HOME))
    # Without heating either, nothing is missing that the area would give.
    empty = dpe_label(
        answer(totals={"heating": 0.0, "water": 300.0}), {**HOME, "surface": None}
    )
    assert (empty["classes"], empty["missing"]) == (None, None)


def test_gas_heating_with_a_hot_water_share() -> None:
    # Gas heating alone, the hot water nowhere: 15 % of the three uses.
    label = dpe_label(
        answer(
            gas=True,
            with_water=False,
            water_split=False,
            totals={"heating": 11000.0, "water": 0.0},
        ),
        HOME,
    )
    rows = uses(label)
    total = 11000 / 0.8
    assert rows["water"]["energy"] == pytest.approx(total * 0.15, abs=0.1)
    assert rows["water"]["source"] == "share"
    # An electric water heater.
    assert rows["water"]["gas"] is False
    assert rows["water"]["primary"] == pytest.approx(total * 0.15 * 1.9, abs=0.1)
    # 16 225 kWhEP and 2 675 kg of CO₂ over 100 m².
    assert (label["energy"], label["climate"]) == (162, 26.8)
    assert label["classes"] == {"energy": "C", "climate": "C", "label": "C"}


def test_the_climate_can_set_the_class() -> None:
    # Gas heating with its hot water measured: C in energy, D in climate.
    label = dpe_label(
        answer(gas=True, water_gas=True, totals={"heating": 11000.0, "water": 2100.0}),
        HOME,
    )
    assert label["energy"] == 144
    assert label["climate"] == 30.2
    assert label["classes"] == {"energy": "C", "climate": "D", "label": "D"}


def test_hot_water_inside_the_heating_untold() -> None:
    # The heating statistics hold the hot water, without warm days to tell it.
    label = dpe_label(
        answer(
            water_split=False,
            water_measured=False,
            totals={"heating": 9500.0, "water": 0.0},
        ),
        HOME,
    )
    rows = uses(label)
    total = 9500 / 0.95
    assert rows["water"]["energy"] == pytest.approx(total * 0.15, abs=0.1)
    assert rows["heating"]["energy"] == pytest.approx(9500 - total * 0.15, abs=0.1)
    assert sum(row["energy"] for row in rows.values()) == pytest.approx(total, abs=0.2)


def test_estimated_heating() -> None:
    label = dpe_label(
        answer(
            measured=False,
            with_water=False,
            water_split=False,
            totals=None,
            estimated={"heating": 4000.0},
        ),
        {**HOME, "surface": 50.0, "coefficient": 2.3},
    )
    rows = uses(label)
    assert rows["heating"]["source"] == "estimated"
    assert label["energy"] == round(4000 / 0.8 * 2.3 / 50)


def test_no_heating_no_label() -> None:
    label = dpe_label(answer(totals={"heating": 0.0, "water": 300.0}), HOME)
    assert (label["classes"], label["missing"], label["uses"]) == (None, None, [])
    assert dpe_label(answer(measured=False, totals=None), HOME)["classes"] is None


WEATHER = {"base": 18.0, "slope": 2.0, "linear": 2.0, "square": 0.0, "reach": 20.0}


def test_moved_to_the_dpe_setpoint_from_thermometers() -> None:
    # 20 °C measured on the heating day, 2 °C more than the DPE's mean: 2 kWh
    # less a degree day. The warm day and the day without temperature count not.
    label = dpe_label(
        answer(
            weather=WEATHER,
            days=[
                {"temperature": 8.0, "indoor": 20.0},
                {"temperature": 20.0, "indoor": 24.0},
                {"temperature": None, "indoor": 20.0},
            ],
        ),
        HOME,
    )
    assert label["conventional"] == {
        "applied": True,
        "source": "thermometers",
        "indoor": 20.0,
        "shift": -2.0,
        "extra": -4.0,
    }
    assert uses(label)["heating"]["energy"] == 6796.0


def test_moved_to_the_dpe_setpoint_from_the_settings() -> None:
    # Without thermometers, 21 °C day and night: 3 °C more than the DPE's.
    label = dpe_label(
        answer(
            measured=False,
            with_water=False,
            water_split=False,
            totals=None,
            estimated={"heating": 16.0},
            weather=WEATHER,
            weather_days=[{"temperature": 10.0, "indoor": None}],
        ),
        {**HOME, "setpoint": 21.0, "setback": 0.0},
    )
    assert label["conventional"]["source"] == "setting"
    assert label["conventional"]["extra"] == -6.0
    assert uses(label)["heating"]["energy"] == 10.0


def test_a_colder_home_gets_more_heating() -> None:
    label = dpe_label(
        answer(weather=WEATHER, days=[{"temperature": 5.0, "indoor": None}]),
        {**HOME, "setpoint": 17.0, "setback": 0.0},
    )
    assert label["conventional"]["extra"] == 2.0


def test_no_weather_line_nothing_moves() -> None:
    label = dpe_label(
        answer(weather={"base": 18.0, "slope": None}), {**HOME, "setpoint": 22.0}
    )
    assert label["conventional"] == {"applied": False, "extra": 0.0}
    assert uses(label)["heating"]["energy"] == 6800.0


def test_an_estimate_counts_the_days_of_the_source() -> None:
    # A day with an outdoor temperature but no consumption counts not.
    first, second = date(2026, 3, 2), date(2026, 3, 3)
    assert counted_days({first: 5.0, second: 6.0}, {first: _Day()}) == {first: 5.0}


def test_class_bounds() -> None:
    bounds = (70, 110, 180, 250, 330, 420)
    assert [_class(value, bounds) for value in (0, 70, 71, 420, 421)] == [
        "A",
        "A",
        "B",
        "F",
        "G",
    ]


def test_a_year_before_29_february() -> None:
    assert _year_before(date(2028, 2, 29)) == date(2027, 2, 28)
    assert _year_before(date(2026, 11, 19)) == date(2025, 11, 19)


async def dpe(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, entry_id: str, end: str
) -> dict[str, Any]:
    label: dict[str, Any] = await result(
        hass_ws_client, hass, type=f"{DOMAIN}/dpe", entry_id=entry_id, end=end
    )
    return label


SETTINGS = {
    "surface": 80,
    "coefficient": 2.3,
    "auxiliaries": 4,
    "water": 20,
    "setpoint": 20,
    "setback": 2,
}


@pytest.mark.usefixtures("sources")
async def test_label_of_a_gas_home(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    gas_home: list[float],  # noqa: F811
) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT], options=GAS_OPTIONS))
    label = await dpe(hass, hass_ws_client, entry.entry_id, "2026-03-17")
    # The year narrowed to the 16 days of data.
    assert label["start"] == "2026-03-02"
    assert label["end"] == "2026-03-17"
    assert label["days"] == DAYS
    assert label["settings"] == label["defaults"] == DEFAULTS
    rows = uses(label)
    # The hot water estimated on the warm days, 5 kWh a day.
    assert rows["water"] == {
        "use": "water",
        "energy": 5.0 * DAYS,
        "gas": True,
        "source": "estimated",
        "primary": 5.0 * DAYS,
        "co2": round(5.0 * DAYS * 0.227, 1),
    }
    assert rows["heating"]["energy"] == pytest.approx(sum(gas_home) - 5.0 * DAYS)
    # No living area by default: no class until it's given.
    assert label["classes"] is None
    assert label["missing"] == "surface"
    assert "energy" not in label
    await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/dpe/save",
        entry_id=entry.entry_id,
        **HOME,
    )
    label = await dpe(hass, hass_ws_client, entry.entry_id, "2026-03-17")
    assert label["classes"]["label"] == "A"
    # The setpoint of the DPE by default: nothing moves.
    assert label["conventional"] == {
        "applied": True,
        "source": "setting",
        "indoor": 18.0,
        "shift": 0.0,
        "extra": 0.0,
    }

    saved = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/dpe/save",
        entry_id=entry.entry_id,
        **SETTINGS,
    )
    assert saved == {key: float(value) for key, value in SETTINGS.items()}
    label = await dpe(hass, hass_ws_client, entry.entry_id, "2026-03-17")
    assert label["settings"] == saved
    # 20 °C lowered by 2 °C at night: 19.3 °C, 1.3 °C more than the DPE's.
    conventional = label["conventional"]
    assert conventional["source"] == "setting"
    assert (conventional["indoor"], conventional["shift"]) == (19.3, -1.3)
    assert conventional["extra"] < 0
    rows = uses(label)
    assert rows["heating"]["energy"] == pytest.approx(
        sum(gas_home) - 5.0 * DAYS + conventional["extra"], abs=0.1
    )
    assert rows["auxiliaries"]["energy"] == pytest.approx(
        (rows["heating"]["energy"] + rows["water"]["energy"]) / 0.96 * 0.04, abs=0.1
    )

    # Removing the source forgets its settings.
    await hass.config_entries.async_remove(entry.entry_id)
    assert await settings_store(hass, entry.entry_id).async_load() is None


@pytest.mark.usefixtures("sources")
async def test_label_before_the_data(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    gas_home: list[float],  # noqa: F811
) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT], options=GAS_OPTIONS))
    label = await dpe(hass, hass_ws_client, entry.entry_id, "2025-12-31")
    assert label["days"] == 0
    assert label["end"] is None
    assert label["classes"] is None


@pytest.mark.usefixtures("sources")
@pytest.mark.parametrize(
    "change",
    [
        {"surface": 2},
        {"coefficient": 4},
        {"auxiliaries": 31},
        {"water": 61},
        {"setpoint": 9},
        {"setback": 11},
    ],
)
async def test_settings_are_bounded(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    gas_home: list[float],  # noqa: F811
    change: dict[str, float],
) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT], options=GAS_OPTIONS))
    response = await command(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/dpe/save",
        entry_id=entry.entry_id,
        **{**SETTINGS, **change},
    )
    assert response["error"]["code"] == "invalid_format"


@pytest.mark.usefixtures("sources")
async def test_settings_need_an_admin(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_admin_user: MockUser,
    gas_home: list[float],  # noqa: F811
) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT], options=GAS_OPTIONS))
    hass_admin_user.groups = []
    response = await command(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/dpe/save",
        entry_id=entry.entry_id,
        **SETTINGS,
    )
    assert response["error"]["code"] == "unauthorized"


@pytest.mark.usefixtures("sources")
async def test_label_of_an_unknown_entry(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    gas_home: list[float],  # noqa: F811
) -> None:
    await setup_entry(hass, make_entry([BASE_CONTRACT], options=GAS_OPTIONS))
    for message in (
        {"type": f"{DOMAIN}/dpe", "end": "2026-03-17"},
        {"type": f"{DOMAIN}/dpe/save", **SETTINGS},
    ):
        response = await command(hass_ws_client, hass, entry_id="unknown", **message)
        assert response["error"]["code"] == "not_found"


@pytest.mark.usefixtures("sources")
async def test_label_of_an_estimated_heating(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    cold_days: list[float],  # noqa: F811
) -> None:
    entry = await setup_entry(
        hass,
        make_entry([TEMPO_CONTRACT], options={CONF_TEMPERATURE: TEMPERATURE_ID}),
    )
    await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/dpe/save",
        entry_id=entry.entry_id,
        **{**SETTINGS, "setpoint": 19, "setback": 0},
    )
    label = await dpe(hass, hass_ws_client, entry.entry_id, "2026-03-17")
    # 2 kWh a degree day; 19 °C day and night is 1 °C more than the DPE's, on
    # the 15 days below 18 °C.
    rows = uses(label)
    assert rows["heating"]["source"] == "estimated"
    assert label["conventional"]["shift"] == -1.0
    assert label["conventional"]["extra"] == pytest.approx(-2 * 15, abs=0.1)
    assert rows["heating"]["energy"] == pytest.approx(
        2 * sum(range(DAYS)) - 30, abs=0.1
    )


def test_heating_estimated_before_the_measured_one() -> None:
    before: dict[str, Any] = {
        "heating": 1000.0,
        "days": 5,
        "weather": None,
        "weather_days": [],
    }
    rows = uses(dpe_label(answer(days=[{}] * 10, before=before), HOME))
    assert rows["heating"]["energy"] == 7800.0
    assert rows["heating"]["source"] == "mixed"
    # The water of the 5 days before, at the mean of the 10 measured ones.
    assert rows["water"]["energy"] == 1900.0 + 190.0 * 5


LINKY_DAYS = "linky:44444444444444"
# 13 to 28 February, French time: 0 °C to 15 °C, and 10 kWh plus 2 a degree day.
FEBRUARY = [date(2026, 2, 13) + timedelta(days=offset) for offset in range(16)]


def _hours_from_first(moment: datetime) -> int:
    """Return the hours from the tests' first hour to `moment`."""
    return int((moment.astimezone(UTC) - FIRST_HOUR) / timedelta(hours=1))


async def add_linky(
    hass: HomeAssistant, daily: list[float], first_hour: datetime, hourly: list[float]
) -> None:
    """Import Wh only known by day from 13 February, then hours from `first_hour`."""
    starts = [
        datetime.combine(day, time(), FRANCE_TIME_ZONE)
        for day in FEBRUARY[: len(daily)]
    ]
    starts += [first_hour + timedelta(hours=hour) for hour in range(len(hourly))]
    values = daily + hourly
    sums = [sum(values[: index + 1]) for index in range(len(values))]
    async_add_external_statistics(
        hass,
        {
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "name": "Linky",
            "source": "linky",
            "statistic_id": LINKY_DAYS,
            "unit_class": "energy",
            "unit_of_measurement": "Wh",
        },
        [
            StatisticData(start=start.astimezone(UTC), state=value, sum=total)
            for start, value, total in zip(starts, values, sums, strict=True)
        ],
    )
    await async_wait_recording_done(hass)


@pytest.mark.usefixtures("sources")
async def test_linky_days_estimate_the_heating_before_the_window(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await hass.config.async_update(time_zone="Europe/Paris")
    await add_linky(
        hass,
        [(10 + 2 * (18 - index)) * 1000.0 for index in range(16)],
        datetime(2026, 3, 1, tzinfo=FRANCE_TIME_ZONE),
        [500.0] * 48,
    )
    # Each French day at its temperature, hour by hour.
    await add_temperature(
        hass,
        [float(index) for index in range(16) for _ in range(24)],
        first=_hours_from_first(
            datetime.combine(FEBRUARY[0], time(), FRANCE_TIME_ZONE)
        ),
    )
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT],
            statistic_id=LINKY_DAYS,
            options={CONF_TEMPERATURE: TEMPERATURE_ID},
        ),
    )
    label = await dpe(hass, hass_ws_client, entry.entry_id, "2026-03-02")
    assert (label["start"], label["end"], label["days"]) == (
        "2026-02-13",
        "2026-03-02",
        18,
    )
    # 2 kWh a degree day, on 18 + 17 + ... + 3 degree days.
    assert label["estimated"] == {
        "start": "2026-02-13",
        "end": "2026-02-28",
        "heating": 336.0,
    }
    assert label["unestimated"] is None
    rows = uses(label)
    assert rows["heating"]["source"] == "estimated"
    assert rows["heating"]["energy"] == pytest.approx(336.0, abs=0.1)

    # 19 °C day and night is 1 °C more than the DPE's: the 16 days estimated
    # move too, by 2 kWh each.
    await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/dpe/save",
        entry_id=entry.entry_id,
        **{**SETTINGS, "setpoint": 19, "setback": 0},
    )
    label = await dpe(hass, hass_ws_client, entry.entry_id, "2026-03-02")
    assert label["conventional"]["extra"] == pytest.approx(-32.0, abs=0.1)
    assert uses(label)["heating"]["energy"] == pytest.approx(304.0, abs=0.1)


@pytest.mark.parametrize(
    ("first_day", "open_meteo", "estimated", "unestimated"),
    [
        # No outdoor temperature before the window: the Linky's days are left
        # out, rather than counted without heating.
        (None, False, None, ("2026-02-13", "2026-02-28")),
        # From 15 February only: the estimate starts there, on 16 + 15 + ... + 3
        # degree days.
        (
            2,
            True,
            ("2026-02-15", 2.0 * sum(range(3, 17))),
            ("2026-02-13", "2026-02-14"),
        ),
    ],
)
@pytest.mark.usefixtures("sources")
async def test_linky_days_without_temperature_are_left_out(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    *,
    first_day: int | None,
    open_meteo: bool,
    estimated: tuple[str, float] | None,
    unestimated: tuple[str, str],
) -> None:
    await hass.config.async_update(time_zone="Europe/Paris")
    await add_linky(
        hass,
        [(10 + 2 * (18 - index)) * 1000.0 for index in range(16)],
        datetime(2026, 3, 1, tzinfo=FRANCE_TIME_ZONE),
        [500.0] * 48,
    )
    if first_day is not None:
        await add_temperature(
            hass,
            [float(index) for index in range(first_day, 16) for _ in range(24)],
            first=_hours_from_first(
                datetime.combine(FEBRUARY[first_day], time(), FRANCE_TIME_ZONE)
            ),
        )
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT],
            statistic_id=LINKY_DAYS,
            options={CONF_TEMPERATURE: TEMPERATURE_ID, CONF_WEATHER: open_meteo},
        ),
    )
    label = await dpe(hass, hass_ws_client, entry.entry_id, "2026-03-02")
    assert label["unestimated"] == {
        "start": unestimated[0],
        "end": unestimated[1],
        "open_meteo": open_meteo,
    }
    if estimated is None:
        assert label["estimated"] is None
        assert (label["start"], label["days"]) == ("2026-03-01", 2)
    else:
        start, heating = estimated
        assert label["estimated"] == {
            "start": start,
            "end": "2026-02-28",
            "heating": heating,
        }
        assert (label["start"], label["days"]) == (start, 16)


def test_hot_water_inside_the_heating_before_it_is_measured() -> None:
    before: dict[str, Any] = {
        "heating": 1000.0,
        "days": 5,
        "weather": None,
        "weather_days": [],
    }
    rows = uses(
        dpe_label(
            answer(water_split=False, totals={"heating": 6800.0}, before=before),
            HOME,
        )
    )
    # 15 % of the three uses is water: carved out of the measured heating, on top
    # of the Linky's estimate, which holds none.
    inside = 6800.0 / 0.95 * 0.15
    on_top = 1000.0 / 0.8 * 0.15
    assert rows["water"]["energy"] == pytest.approx(inside + on_top, abs=0.1)
    assert rows["heating"]["energy"] == pytest.approx(6800.0 - inside + 1000.0, abs=0.1)


@pytest.mark.usefixtures("sources")
async def test_heaters_starting_later_leave_the_linky_days_before(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    cold_days: list[float],  # noqa: F811
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
    label = await dpe(hass, hass_ws_client, entry.entry_id, "2026-03-17")
    assert (label["start"], label["days"]) == ("2026-03-02", DAYS)
    # The 14 days before it from the Linky: 2 kWh a degree day, n degree days
    # on day n.
    assert label["estimated"] == {
        "start": "2026-03-02",
        "end": "2026-03-15",
        "heating": 2.0 * sum(range(14)),
    }
    rows = uses(label)
    assert rows["heating"]["source"] == "mixed"
    assert rows["heating"]["energy"] == pytest.approx(2.0 * sum(range(16)), abs=0.1)


@pytest.mark.usefixtures("sources")
async def test_gas_heating_isnt_estimated_from_the_linky(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    gas_home: list[float],  # noqa: F811
) -> None:
    await add_linky(
        hass,
        [10000.0] * 16,
        datetime(2026, 3, 2, tzinfo=FRANCE_TIME_ZONE),
        [250.0] * 24 * DAYS,
    )
    entry = await setup_entry(
        hass,
        make_entry([BASE_CONTRACT], statistic_id=LINKY_DAYS, options=GAS_OPTIONS),
    )
    label = await dpe(hass, hass_ws_client, entry.entry_id, "2026-03-17")
    assert label["estimated"] is None
    assert label["start"] == "2026-03-02"
