"""Tests of the diagnostics."""

import json

import pytest
from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.electricity_contracts.const import (
    CONF_RTE_CLIENT_ID,
    CONF_RTE_CLIENT_SECRET,
)

from .conftest import MANUAL_CONTRACT, TEMPO_CONTRACT, make_entry


@pytest.mark.usefixtures("statistic", "sources")
async def test_diagnostics_hide_personal_data(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    entry = make_entry(
        [TEMPO_CONTRACT],
        options={CONF_RTE_CLIENT_ID: "my-id", CONF_RTE_CLIENT_SECRET: "my-secret"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    result = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    text = json.dumps(result)
    for secret in ("00000000000000", "my-id", "my-secret"):
        assert secret not in text
    assert result["entry"]["title"] == REDACTED
    assert result["entry"]["data"] == {"statistic_id": REDACTED}
    assert result["entry"]["subentries"][0]["title"] == "Tempo"
    sources = result["sources"]
    assert sources["first_day"] == "2026-03-01"
    assert sources["tempo_sources"] == "rte_public+rte_official"
    assert sources["calendar"]["days"] == 253
    assert sources["calendar"]["last"] == "2026-11-07"
    assert sources["prices"]["tempo:6"]["periods"] == 2
    costing = sources["costing"]
    assert costing["contracts"]["tempo001"] == {
        "last_hour": "2026-03-02T23:00:00+00:00",
        "waiting": None,
    }
    assert costing["actual"]["last_hour"] == "2026-03-02T23:00:00+00:00"


@pytest.mark.usefixtures("statistic", "sources")
async def test_diagnostics_of_a_waiting_contract(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    entry = make_entry([MANUAL_CONTRACT])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    result = await get_diagnostics_for_config_entry(hass, hass_client, entry)
    costing = result["sources"]["costing"]
    assert costing["contracts"]["offer001"] == {
        "last_hour": None,
        "waiting": {"reason": "price", "day": "2026-03-01"},
    }
    assert costing["actual"] is None
