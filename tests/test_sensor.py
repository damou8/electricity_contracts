"""Tests of the current price and tranche sensors."""

from datetime import UTC, datetime

import pytest
from elec_tariffs import ContractKind
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.electricity_contracts.const import DOMAIN

from .conftest import BASE_CONTRACT, TEMPO_CONTRACT, contract_subentry, make_entry
from .test_comparison import setup_entry


def sensor(hass: HomeAssistant, entry: MockConfigEntry, key: str) -> State:
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_{key}"
    )
    assert entity_id is not None
    state = hass.states.get(entity_id)
    assert state is not None
    return state


async def move_to(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, moment: datetime
) -> None:
    freezer.move_to(moment)
    async_fire_time_changed(hass, moment)
    await hass.async_block_till_done(wait_background_tasks=True)


@pytest.mark.usefixtures("statistic", "sources")
async def test_tempo_price_and_tranche(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    # 7 November 2026, 10:00 in Paris: a blue day, in peak hours.
    price = sensor(hass, entry, "current_price")
    assert float(price.state) == 0.1654
    assert price.attributes["unit_of_measurement"] == "EUR/kWh"
    tranche = sensor(hass, entry, "current_tranche")
    assert tranche.state == "blue_hp"
    assert tranche.attributes["options"] == [
        "base",
        "hc",
        "hp",
        "blue_hc",
        "blue_hp",
        "white_hc",
        "white_hp",
        "red_hc",
        "red_hp",
    ]
    # Off-peak hours start at 22:00.
    await move_to(hass, freezer, datetime(2026, 11, 7, 21, tzinfo=UTC))
    assert float(sensor(hass, entry, "current_price").state) == 0.1356
    assert sensor(hass, entry, "current_tranche").state == "blue_hc"
    # The next Tempo day starts at 6:00; its color isn't published.
    await move_to(hass, freezer, datetime(2026, 11, 8, 5, tzinfo=UTC))
    assert sensor(hass, entry, "current_price").state == STATE_UNKNOWN
    assert sensor(hass, entry, "current_tranche").state == STATE_UNKNOWN


@pytest.mark.usefixtures("statistic", "sources")
async def test_base_price(hass: HomeAssistant) -> None:
    base = contract_subentry(
        "Base", uid="base0001", kind=ContractKind.BASE, active_from="2026-01-01"
    )
    entry = await setup_entry(hass, make_entry([base]))
    assert float(sensor(hass, entry, "current_price").state) == 0.2001
    assert sensor(hass, entry, "current_tranche").state == "base"


@pytest.mark.usefixtures("statistic", "sources")
async def test_no_contract_in_force(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    assert sensor(hass, entry, "current_price").state == STATE_UNKNOWN
    assert sensor(hass, entry, "current_tranche").state == STATE_UNKNOWN
