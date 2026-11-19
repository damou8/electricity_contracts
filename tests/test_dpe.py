"""Tests of the energy label in the style of the DPE."""

from datetime import date
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockUser
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.electricity_contracts.const import DOMAIN
from custom_components.electricity_contracts.dpe import (
    DEFAULTS,
    _class,
    _year_before,
    dpe_label,
    settings_store,
)

from .conftest import make_entry
from .test_comparison import setup_entry
from .test_heating import (
    BASE_CONTRACT,
    DAYS,
    GAS_OPTIONS,
    gas_home,  # noqa: F401 - a fixture
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
    }
    return {**base, **changes}


def uses(label: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["use"]: row for row in label["uses"]}


def test_electric_heating_and_measured_water() -> None:
    label = dpe_label(answer(), DEFAULTS)
    # The auxiliaries are 5 % of the three uses: 8 700 kWh are the other 95 %.
    rows = uses(label)
    assert rows["auxiliaries"]["energy"] == pytest.approx(457.9, abs=0.1)
    assert rows["water"]["source"] == "measured"
    # 9 158 kWh x 1.9 over 100 m².
    assert label["energy"] == 174
    # 6 800 x 0.079 + 1 900 x 0.065 + 458 x 0.064, over 100 m².
    assert label["climate"] == 6.9
    assert label["classes"] == {"energy": "C", "climate": "B", "label": "C"}


def test_gas_heating_with_a_hot_water_share() -> None:
    # Gas heating alone, the hot water nowhere: 15 % of the three uses.
    label = dpe_label(
        answer(
            gas=True,
            with_water=False,
            water_split=False,
            totals={"heating": 11000.0, "water": 0.0},
        ),
        DEFAULTS,
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
        DEFAULTS,
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
        DEFAULTS,
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
        {**DEFAULTS, "surface": 50.0, "coefficient": 2.3},
    )
    rows = uses(label)
    assert rows["heating"]["source"] == "estimated"
    assert label["energy"] == round(4000 / 0.8 * 2.3 / 50)


def test_no_heating_no_label() -> None:
    assert dpe_label(answer(totals={"heating": 0.0, "water": 300.0}), DEFAULTS) == {
        "classes": None,
        "uses": [],
    }
    assert dpe_label(answer(measured=False, totals=None), DEFAULTS)["classes"] is None


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


SETTINGS = {"surface": 80, "coefficient": 2.3, "auxiliaries": 4, "water": 20}


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
    assert label["classes"]["label"] == "A"

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
    assert uses(label)["auxiliaries"]["energy"] == pytest.approx(
        sum(gas_home) / 0.96 * 0.04, abs=0.1
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
    [{"surface": 2}, {"coefficient": 4}, {"auxiliaries": 31}, {"water": 61}],
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
