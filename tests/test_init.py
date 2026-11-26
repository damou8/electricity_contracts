"""Tests of setting up, reloading and removing a consumption source."""

from types import MappingProxyType
from typing import Any

import pytest
from homeassistant.config_entries import ConfigEntryState, ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from custom_components.electricity_contracts.const import (
    CONF_HEATING_STATISTICS,
    CONF_INDOOR_TEMPERATURES,
    CONF_PERIODS,
    CONF_RTE_CLIENT_ID,
    CONF_RTE_CLIENT_SECRET,
    DOMAIN,
    SECTION_HEATING,
    SUBENTRY_COMPARISON,
)

from .conftest import (
    MANUAL_CONTRACT,
    TEMPO_CONTRACT,
    Sources,
    comparison_subentry,
    gas_period,
    legacy_gas_price,
    legacy_price_period,
    make_entry,
    manual_period,
)


@pytest.mark.usefixtures("statistic")
async def test_setup_and_unload(hass: HomeAssistant, sources: Sources) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.LOADED
    sources.trv.async_price_periods.assert_awaited_once()
    assert sources.public.async_calendar.await_count > 0
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.usefixtures("statistic", "sources")
async def test_migration_removes_comparisons_and_sensors(hass: HomeAssistant) -> None:
    entry = make_entry([TEMPO_CONTRACT, comparison_subentry("March")], minor_version=1)
    entry.add_to_hass(hass)
    comparison_id = next(
        subentry.subentry_id
        for subentry in entry.subentries.values()
        if subentry.subentry_type == SUBENTRY_COMPARISON
    )
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    source = devices.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, entry.entry_id)}
    )
    comparison = devices.async_get_or_create(
        config_entry_id=entry.entry_id,
        config_subentry_id=comparison_id,
        identifiers={(DOMAIN, comparison_id)},
    )
    entities.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{entry.entry_id}_last_day_cost",
        config_entry=entry,
        device_id=source.id,
    )
    entities.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{comparison_id}_saving",
        config_entry=entry,
        config_subentry_id=comparison_id,
        device_id=comparison.id,
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.LOADED
    assert entry.minor_version == 3
    assert [item.subentry_type for item in entry.subentries.values()] == ["contract"]
    # Only the sensors of 0.2 are left, on a device of their own.
    assert {
        item.unique_id
        for item in er.async_entries_for_config_entry(entities, entry.entry_id)
    } == {f"{entry.entry_id}_current_price", f"{entry.entry_id}_current_tranche"}
    assert devices.async_get(comparison.id) is None
    assert [
        device.identifiers
        for device in dr.async_entries_for_config_entry(devices, entry.entry_id)
    ] == [{(DOMAIN, entry.entry_id)}]


@pytest.mark.usefixtures("statistic")
async def test_setup_without_contracts_downloads_nothing(
    hass: HomeAssistant, sources: Sources
) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.LOADED
    sources.trv.async_price_periods.assert_not_awaited()
    sources.public.async_calendar.assert_not_awaited()


@pytest.mark.usefixtures("statistic")
async def test_setup_retries_when_sources_are_down(
    hass: HomeAssistant, sources: Sources
) -> None:
    sources.fail_prices()
    sources.fail_public()
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.usefixtures("statistic")
async def test_official_source_used_with_credentials(
    hass: HomeAssistant, sources: Sources
) -> None:
    sources.fail_public()
    entry = make_entry(
        [TEMPO_CONTRACT],
        options={CONF_RTE_CLIENT_ID: "my-id", CONF_RTE_CLIENT_SECRET: "my-secret"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.LOADED
    assert sources.official_class.call_args.args[1:] == ("my-id", "my-secret")
    assert sources.official.async_calendar.await_count > 0
    assert entry.runtime_data.tempo.last_source == "rte_official"


@pytest.mark.usefixtures("statistic", "sources")
async def test_migration_moves_price_periods_into_their_contract(
    hass: HomeAssistant,
) -> None:
    entry = make_entry(
        [
            TEMPO_CONTRACT,
            MANUAL_CONTRACT,
            legacy_price_period("offer001", "2026-08-01"),
            legacy_price_period("offer001", "2026-01-01", "2026-07-31"),
            legacy_price_period("gone0001", "2026-02-01"),
        ],
        minor_version=2,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.minor_version == 3
    assert [item.subentry_type for item in entry.subentries.values()] == [
        "contract",
        "contract",
    ]
    offer = next(
        item for item in entry.subentries.values() if item.data["uid"] == "offer001"
    )
    assert offer.data[CONF_PERIODS] == [
        manual_period("2026-01-01", "2026-07-31"),
        manual_period("2026-08-01"),
    ]
    tempo = next(
        item for item in entry.subentries.values() if item.data["uid"] == "tempo001"
    )
    assert CONF_PERIODS not in tempo.data


@pytest.mark.usefixtures("statistic", "sources")
async def test_migration_moves_gas_prices_into_a_gas_contract(
    hass: HomeAssistant,
) -> None:
    hass.config.language = "fr"
    entry = make_entry(
        [
            TEMPO_CONTRACT,
            legacy_gas_price(0.12, "2026-08-01"),
            legacy_gas_price(0.1, "2025-08-01", "2026-07-31"),
        ],
        options={
            SECTION_HEATING: {
                CONF_HEATING_STATISTICS: ["sensor.gas"],
                CONF_INDOOR_TEMPERATURES: ["sensor.living_room"],
            },
            CONF_RTE_CLIENT_ID: "my-id",
            CONF_RTE_CLIENT_SECRET: "my-secret",
        },
        minor_version=2,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    gas = next(
        item
        for item in entry.subentries.values()
        if item.subentry_type == "gas_contract"
    )
    assert gas.title == "Gaz · mes prix"
    assert gas.unique_id == gas.data["uid"]
    assert gas.data["pricing"] == "manual"
    assert gas.data[CONF_PERIODS] == [
        gas_period(0.1, "2025-08-01", "2026-07-31"),
        gas_period(0.12, "2026-08-01"),
    ]
    assert len(entry.subentries) == 2
    # The indoor thermometers have a page of their own.
    assert entry.options == {
        SECTION_HEATING: {CONF_HEATING_STATISTICS: ["sensor.gas"]},
        CONF_INDOOR_TEMPERATURES: ["sensor.living_room"],
        CONF_RTE_CLIENT_ID: "my-id",
        CONF_RTE_CLIENT_SECRET: "my-secret",
    }


@pytest.mark.usefixtures("statistic", "sources")
async def test_migration_without_heating_left(hass: HomeAssistant) -> None:
    entry = make_entry(
        [TEMPO_CONTRACT],
        options={SECTION_HEATING: {CONF_INDOOR_TEMPERATURES: ["sensor.living_room"]}},
        minor_version=2,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.options == {CONF_INDOOR_TEMPERATURES: ["sensor.living_room"]}


@pytest.mark.usefixtures("statistic")
async def test_changes_reload_the_entry(hass: HomeAssistant, sources: Sources) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    sources.trv.async_price_periods.assert_not_awaited()
    hass.config_entries.async_add_subentry(
        entry,
        ConfigSubentry(
            data=MappingProxyType(dict(TEMPO_CONTRACT["data"])),
            subentry_type=TEMPO_CONTRACT["subentry_type"],
            title=TEMPO_CONTRACT["title"],
            unique_id=TEMPO_CONTRACT["unique_id"],
        ),
    )
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    sources.trv.async_price_periods.assert_awaited_once()


@pytest.mark.usefixtures("statistic")
async def test_remove_entry_deletes_cache_and_issues(
    hass: HomeAssistant, hass_storage: dict[str, Any], sources: Sources
) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    key = f"{DOMAIN}.{entry.entry_id}"
    assert key in hass_storage
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"tempo_unavailable_{entry.entry_id}",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="tempo_unavailable",
    )
    assert sources.public.async_calendar.await_count > 0
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert key not in hass_storage
    assert not ir.async_get(hass).issues
