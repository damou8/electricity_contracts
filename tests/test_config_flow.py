"""Tests of the config, options and subentry flows."""

from datetime import timedelta
from typing import Any

import pytest
from elec_tariffs import TempoAuthError, TempoError
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.electricity_contracts.const import (
    CONF_ACTIVE_FROM,
    CONF_ACTIVE_TO,
    CONF_CONTRACT,
    CONF_END,
    CONF_FIXED_PER_YEAR,
    CONF_KIND,
    CONF_KVA,
    CONF_OFF_PEAK,
    CONF_PRICES,
    CONF_PRICING,
    CONF_RTE_CLIENT_ID,
    CONF_RTE_CLIENT_SECRET,
    CONF_START,
    CONF_STATISTIC_ID,
    CONF_UID,
    CONF_WEEKEND_OFF_PEAK,
    DOMAIN,
    PRICING_MANUAL,
    PRICING_OFFICIAL,
    SUBENTRY_CONTRACT,
    SUBENTRY_PRICE_PERIOD,
)

from .conftest import (
    BASE_CONTRACT,
    MANUAL_CONTRACT,
    OTHER_STATISTIC_ID,
    STATISTIC_ID,
    TEMPO_CONTRACT,
    Sources,
    add_statistic,
    make_entry,
    price_period_subentry,
)

# Source entry.


@pytest.mark.usefixtures("statistic")
async def test_user_flow(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATISTIC_ID: STATISTIC_ID}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Linky 00000000000000"
    assert result["data"] == {CONF_STATISTIC_ID: STATISTIC_ID}
    assert result["result"].unique_id == STATISTIC_ID


async def add_bad_statistics(hass: HomeAssistant) -> None:
    await add_statistic(hass, "linky:temperature", unit="°C")
    await add_statistic(hass, "linky:no_sum", has_sum=False)
    await add_statistic(hass, "linky:empty", hours=0)
    await add_statistic(hass, "linky:daily", hours=3, step=timedelta(days=1))


@pytest.mark.parametrize(
    ("statistic_id", "error"),
    [
        pytest.param("linky:missing", "statistic_not_found", id="not_found"),
        pytest.param("linky:temperature", "statistic_not_energy", id="not_energy"),
        pytest.param("linky:no_sum", "statistic_no_sum", id="no_sum"),
        pytest.param("linky:empty", "statistic_no_data", id="no_rows"),
        pytest.param("linky:daily", "statistic_daily", id="daily"),
    ],
)
@pytest.mark.usefixtures("statistic")
async def test_user_flow_refuses_statistic(
    hass: HomeAssistant, statistic_id: str, error: str
) -> None:
    await add_bad_statistics(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATISTIC_ID: statistic_id}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_STATISTIC_ID: error}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATISTIC_ID: STATISTIC_ID}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


@pytest.mark.usefixtures("statistic")
async def test_user_flow_already_configured(hass: HomeAssistant) -> None:
    make_entry().add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATISTIC_ID: STATISTIC_ID}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.usefixtures("statistic", "sources")
async def test_reconfigure_to_another_statistic(hass: HomeAssistant) -> None:
    await add_statistic(hass, OTHER_STATISTIC_ID)
    await add_statistic(hass, "linky:temperature", unit="°C")
    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATISTIC_ID: "linky:temperature"}
    )
    assert result["errors"] == {CONF_STATISTIC_ID: "statistic_not_energy"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATISTIC_ID: OTHER_STATISTIC_ID}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == OTHER_STATISTIC_ID
    assert entry.data == {CONF_STATISTIC_ID: OTHER_STATISTIC_ID}


@pytest.mark.usefixtures("statistic")
async def test_reconfigure_keeps_the_statistic(hass: HomeAssistant) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATISTIC_ID: STATISTIC_ID}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"


@pytest.mark.usefixtures("statistic")
async def test_reconfigure_to_a_configured_statistic(hass: HomeAssistant) -> None:
    await add_statistic(hass, OTHER_STATISTIC_ID)
    make_entry(statistic_id=OTHER_STATISTIC_ID).add_to_hass(hass)
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATISTIC_ID: OTHER_STATISTIC_ID}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


# Options.


async def options_flow(hass: HomeAssistant, user_input: dict[str, Any]) -> Any:
    entry = make_entry(options={CONF_RTE_CLIENT_ID: "old", CONF_RTE_CLIENT_SECRET: "x"})
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    return await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )


async def test_options_save_checked_credentials(
    hass: HomeAssistant, sources: Sources
) -> None:
    result = await options_flow(
        hass, {CONF_RTE_CLIENT_ID: " my-id ", CONF_RTE_CLIENT_SECRET: "my-secret"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_RTE_CLIENT_ID: "my-id",
        CONF_RTE_CLIENT_SECRET: "my-secret",
    }
    sources.official.async_check_credentials.assert_awaited_once()
    assert sources.official_class.call_args.args[1:] == ("my-id", "my-secret")


@pytest.mark.usefixtures("sources")
async def test_options_clear_credentials(hass: HomeAssistant) -> None:
    result = await options_flow(hass, {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {}


@pytest.mark.parametrize(
    ("user_input", "check_error", "error"),
    [
        pytest.param(
            {CONF_RTE_CLIENT_ID: "my-id"},
            None,
            "incomplete_credentials",
            id="no_secret",
        ),
        pytest.param(
            {CONF_RTE_CLIENT_ID: "my-id", CONF_RTE_CLIENT_SECRET: "bad"},
            TempoAuthError("refused"),
            "invalid_auth",
            id="refused",
        ),
        pytest.param(
            {CONF_RTE_CLIENT_ID: "my-id", CONF_RTE_CLIENT_SECRET: "secret"},
            TempoError("down"),
            "cannot_connect",
            id="down",
        ),
    ],
)
async def test_options_errors(
    hass: HomeAssistant,
    sources: Sources,
    user_input: dict[str, str],
    check_error: Exception | None,
    error: str,
) -> None:
    sources.official.async_check_credentials.side_effect = check_error
    result = await options_flow(hass, user_input)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}
    sources.official.async_check_credentials.side_effect = None
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_RTE_CLIENT_ID: "my-id", CONF_RTE_CLIENT_SECRET: "secret"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


# Contracts.


async def start_subentry_flow(
    hass: HomeAssistant, entry_id: str, subentry_type: str
) -> Any:
    return await hass.config_entries.subentries.async_init(
        (entry_id, subentry_type), context={"source": SOURCE_USER}
    )


async def add_contract(
    hass: HomeAssistant,
    entry_id: str,
    first: dict[str, Any],
    details: dict[str, Any],
) -> Any:
    result = await start_subentry_flow(hass, entry_id, SUBENTRY_CONTRACT)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], first
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "details"
    return await hass.config_entries.subentries.async_configure(
        result["flow_id"], details
    )


@pytest.mark.parametrize(
    ("first", "details", "expected"),
    [
        pytest.param(
            {CONF_NAME: " Tempo ", CONF_KIND: "tempo", CONF_PRICING: PRICING_OFFICIAL},
            {CONF_KVA: "6", CONF_ACTIVE_FROM: "2024-01-01"},
            {
                CONF_KIND: "tempo",
                CONF_PRICING: PRICING_OFFICIAL,
                CONF_KVA: 6,
                CONF_ACTIVE_FROM: "2024-01-01",
                CONF_ACTIVE_TO: None,
            },
            id="tempo",
        ),
        pytest.param(
            {CONF_NAME: "HP/HC", CONF_KIND: "hphc", CONF_PRICING: PRICING_OFFICIAL},
            {
                CONF_KVA: "9",
                CONF_OFF_PEAK: ["23:00 - 07:00", "", "12:30-14:00"],
                CONF_WEEKEND_OFF_PEAK: True,
            },
            {
                CONF_KIND: "hphc",
                CONF_PRICING: PRICING_OFFICIAL,
                CONF_KVA: 9,
                CONF_OFF_PEAK: ["23:00-07:00", "12:30-14:00"],
                CONF_WEEKEND_OFF_PEAK: True,
                CONF_ACTIVE_FROM: None,
                CONF_ACTIVE_TO: None,
            },
            id="hphc",
        ),
        pytest.param(
            {CONF_NAME: "Offer", CONF_KIND: "base", CONF_PRICING: PRICING_MANUAL},
            {CONF_ACTIVE_FROM: "2023-01-01", CONF_ACTIVE_TO: "2023-12-31"},
            {
                CONF_KIND: "base",
                CONF_PRICING: PRICING_MANUAL,
                CONF_ACTIVE_FROM: "2023-01-01",
                CONF_ACTIVE_TO: "2023-12-31",
            },
            id="manual",
        ),
    ],
)
async def test_add_contract(
    hass: HomeAssistant,
    first: dict[str, Any],
    details: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await add_contract(hass, entry.entry_id, first, details)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    (subentry,) = entry.subentries.values()
    assert subentry.title == first[CONF_NAME].strip()
    uid = subentry.data[CONF_UID]
    assert len(uid) == 8
    assert subentry.unique_id == uid
    assert dict(subentry.data) == {CONF_UID: uid, **expected}


@pytest.mark.parametrize(
    ("details", "errors"),
    [
        pytest.param(
            {CONF_KVA: "6", CONF_OFF_PEAK: ["22h-6h"], CONF_WEEKEND_OFF_PEAK: False},
            {CONF_OFF_PEAK: "invalid_off_peak"},
            id="unreadable_range",
        ),
        pytest.param(
            {
                CONF_KVA: "6",
                CONF_OFF_PEAK: ["22:15-06:00"],
                CONF_WEEKEND_OFF_PEAK: False,
            },
            {CONF_OFF_PEAK: "invalid_off_peak"},
            id="quarter_hour",
        ),
        pytest.param(
            {
                CONF_KVA: "6",
                CONF_OFF_PEAK: ["22:00-22:00"],
                CONF_WEEKEND_OFF_PEAK: False,
            },
            {CONF_OFF_PEAK: "invalid_off_peak"},
            id="empty_range",
        ),
        pytest.param(
            {CONF_KVA: "6", CONF_OFF_PEAK: [" "], CONF_WEEKEND_OFF_PEAK: False},
            {CONF_OFF_PEAK: "invalid_off_peak"},
            id="no_range",
        ),
        pytest.param(
            {
                CONF_KVA: "6",
                CONF_OFF_PEAK: ["22:00-06:00"],
                CONF_WEEKEND_OFF_PEAK: False,
                CONF_ACTIVE_TO: "2026-01-01",
            },
            {CONF_ACTIVE_FROM: "active_to_without_from"},
            id="end_without_start",
        ),
        pytest.param(
            {
                CONF_KVA: "6",
                CONF_OFF_PEAK: ["22:00-06:00"],
                CONF_WEEKEND_OFF_PEAK: False,
                CONF_ACTIVE_FROM: "2026-01-01",
                CONF_ACTIVE_TO: "2025-12-31",
            },
            {CONF_ACTIVE_TO: "end_before_start"},
            id="end_before_start",
        ),
        pytest.param(
            {
                CONF_KVA: "6",
                CONF_OFF_PEAK: ["22:00-06:00"],
                CONF_WEEKEND_OFF_PEAK: False,
                CONF_ACTIVE_FROM: "2023-06-01",
            },
            {"base": "overlapping_active_period"},
            id="overlap",
        ),
    ],
)
async def test_add_contract_errors(
    hass: HomeAssistant, details: dict[str, Any], errors: dict[str, str]
) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    result = await add_contract(
        hass,
        entry.entry_id,
        {CONF_NAME: "HP/HC", CONF_KIND: "hphc", CONF_PRICING: PRICING_OFFICIAL},
        details,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "details"
    assert result["errors"] == errors
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_KVA: "6", CONF_OFF_PEAK: ["22:00-06:00"], CONF_WEEKEND_OFF_PEAK: False},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_contract_needs_a_name(hass: HomeAssistant) -> None:
    entry = make_entry([BASE_CONTRACT])
    entry.add_to_hass(hass)
    first = {CONF_NAME: "  ", CONF_KIND: "base", CONF_PRICING: PRICING_MANUAL}
    result = await start_subentry_flow(hass, entry.entry_id, SUBENTRY_CONTRACT)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], first
    )
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_NAME: "empty_name"}
    (subentry,) = entry.subentries.values()
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_NAME: "", CONF_PRICING: PRICING_OFFICIAL}
    )
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {CONF_NAME: "empty_name"}


async def test_contract_before_another_one(hass: HomeAssistant) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    result = await add_contract(
        hass,
        entry.entry_id,
        {CONF_NAME: "Old", CONF_KIND: "base", CONF_PRICING: PRICING_OFFICIAL},
        {CONF_KVA: "6", CONF_ACTIVE_FROM: "2020-01-01", CONF_ACTIVE_TO: "2023-12-31"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_reconfigure_contract(hass: HomeAssistant) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    (subentry,) = entry.subentries.values()
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_NAME: "My Tempo", CONF_PRICING: PRICING_MANUAL}
    )
    assert result["step_id"] == "details"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_ACTIVE_FROM: "2024-01-01", CONF_ACTIVE_TO: "2026-10-31"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    subentry = entry.subentries[subentry.subentry_id]
    assert subentry.title == "My Tempo"
    assert dict(subentry.data) == {
        CONF_UID: "tempo001",
        CONF_KIND: "tempo",
        CONF_PRICING: PRICING_MANUAL,
        CONF_ACTIVE_FROM: "2024-01-01",
        CONF_ACTIVE_TO: "2026-10-31",
    }


async def test_reconfigure_contract_suggests_current_values(
    hass: HomeAssistant,
) -> None:
    entry = make_entry([BASE_CONTRACT])
    entry.add_to_hass(hass)
    (subentry,) = entry.subentries.values()
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_NAME: "Base", CONF_PRICING: PRICING_OFFICIAL}
    )
    assert result["data_schema"] is not None
    schema = result["data_schema"].schema
    kva = next(key for key in schema if key == CONF_KVA)
    assert kva.description == {"suggested_value": "6"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_KVA: "9"}
    )
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[subentry.subentry_id].data[CONF_KVA] == 9


# Price periods.


async def add_price_period(
    hass: HomeAssistant, entry_id: str, period: dict[str, Any], prices: dict[str, Any]
) -> Any:
    result = await start_subentry_flow(hass, entry_id, SUBENTRY_PRICE_PERIOD)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], period
    )
    if result["type"] is not FlowResultType.FORM or result["step_id"] != "prices":
        return result
    return await hass.config_entries.subentries.async_configure(
        result["flow_id"], prices
    )


async def test_price_period_needs_a_manual_contract(hass: HomeAssistant) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    result = await start_subentry_flow(hass, entry.entry_id, SUBENTRY_PRICE_PERIOD)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_manual_contracts"


async def test_add_price_period(hass: HomeAssistant) -> None:
    entry = make_entry([TEMPO_CONTRACT, MANUAL_CONTRACT])
    entry.add_to_hass(hass)
    result = await add_price_period(
        hass,
        entry.entry_id,
        {CONF_CONTRACT: "offer001", CONF_START: "2026-02-01", CONF_FIXED_PER_YEAR: 150},
        {"base": 0.19},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Offer · 2026-02-01 → …"
    assert result["data"] == {
        CONF_CONTRACT: "offer001",
        CONF_START: "2026-02-01",
        CONF_END: None,
        CONF_FIXED_PER_YEAR: 150.0,
        CONF_PRICES: {"base": 0.19},
    }


@pytest.mark.parametrize(
    ("period", "errors"),
    [
        pytest.param(
            {CONF_START: "2026-02-01", CONF_END: "2026-01-31"},
            {CONF_END: "end_before_start"},
            id="end_before_start",
        ),
        pytest.param(
            {CONF_START: "2025-12-01", CONF_END: "2026-02-01"},
            {"base": "overlapping_price_period"},
            id="overlap",
        ),
    ],
)
async def test_add_price_period_errors(
    hass: HomeAssistant, period: dict[str, str], errors: dict[str, str]
) -> None:
    entry = make_entry(
        [MANUAL_CONTRACT, price_period_subentry("offer001", "2026-02-01")]
    )
    entry.add_to_hass(hass)
    result = await add_price_period(
        hass,
        entry.entry_id,
        {CONF_CONTRACT: "offer001", CONF_FIXED_PER_YEAR: 150, **period},
        {},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == errors
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_CONTRACT: "offer001",
            CONF_START: "2025-01-01",
            CONF_END: "2026-01-31",
            CONF_FIXED_PER_YEAR: 140,
        },
    )
    assert result["step_id"] == "prices"


async def test_reconfigure_price_period(hass: HomeAssistant) -> None:
    entry = make_entry(
        [
            MANUAL_CONTRACT,
            price_period_subentry("offer001", "2025-01-01", "2026-01-31"),
            price_period_subentry("offer001", "2026-02-01"),
        ]
    )
    entry.add_to_hass(hass)
    subentry = next(
        subentry
        for subentry in entry.subentries.values()
        if subentry.data.get(CONF_START) == "2026-02-01"
    )
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["description_placeholders"] == {"contract": "Offer"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_START: "2026-01-01", CONF_FIXED_PER_YEAR: 150}
    )
    assert result["errors"] == {"base": "overlapping_price_period"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_START: "2026-02-01", CONF_END: "2026-12-31", CONF_FIXED_PER_YEAR: 160},
    )
    assert result["step_id"] == "prices"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"base": 0.2}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    updated = entry.subentries[subentry.subentry_id]
    assert updated.title == "Offer · 2026-02-01 → 2026-12-31"
    assert updated.data[CONF_PRICES] == {"base": 0.2}
    assert updated.data[CONF_FIXED_PER_YEAR] == 160.0


async def test_reconfigure_price_period_of_a_deleted_contract(
    hass: HomeAssistant,
) -> None:
    entry = make_entry([price_period_subentry("gone0001", "2026-02-01")])
    entry.add_to_hass(hass)
    (subentry,) = entry.subentries.values()
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_PRICE_PERIOD),
        context={"source": SOURCE_RECONFIGURE, "subentry_id": subentry.subentry_id},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "contract_not_found"
