"""Tests of the config, options and subentry flows."""

from datetime import timedelta
from typing import Any

import pytest
from elec_tariffs import ContractKind, TempoAuthError, TempoError
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, section

from custom_components.electricity_contracts.config_flow import (
    async_energy_statistics,
)
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
    CONF_TEMPERATURE,
    CONF_UID,
    CONF_WEEKEND_OFF_PEAK,
    DOMAIN,
    OFF_PEAK_OTHER,
    PRICING_MANUAL,
    PRICING_OFFICIAL,
    SECTION_ACTIVE,
    SECTION_RTE,
    SUBENTRY_CONTRACT,
    SUBENTRY_PRICE_PERIOD,
)

from .conftest import (
    BASE_CONTRACT,
    MANUAL_CONTRACT,
    OTHER_STATISTIC_ID,
    STATISTIC_ID,
    TEMPERATURE_ID,
    TEMPO_CONTRACT,
    Sources,
    add_statistic,
    add_temperature,
    contract_subentry,
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


@pytest.mark.usefixtures("statistic")
async def test_user_flow_suggests_a_linky_statistic(hass: HomeAssistant) -> None:
    await add_statistic(hass, "meter:energy")
    await add_statistic(hass, OTHER_STATISTIC_ID)
    await add_statistic(hass, "linky:temperature", unit="°C")
    await add_statistic(hass, f"{DOMAIN}:linky_00000000000000_actual_energy")
    make_entry().add_to_hass(hass)
    assert await async_energy_statistics(hass, configured={STATISTIC_ID}) == [
        OTHER_STATISTIC_ID,
        "meter:energy",
        STATISTIC_ID,
    ]
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    # The frontend can't show a required statistic selector without a value.
    schema = result["data_schema"]
    assert schema is not None
    (field,) = schema.schema
    assert field.description == {"suggested_value": OTHER_STATISTIC_ID}


async def test_user_flow_without_statistic(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_statistic"


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


def credentials(client_id: str | None = None, secret: str | None = None) -> Any:
    """Fill the RTE section of the options."""
    values = {CONF_RTE_CLIENT_ID: client_id, CONF_RTE_CLIENT_SECRET: secret}
    return {SECTION_RTE: {key: value for key, value in values.items() if value}}


def suggested(result: Any) -> dict[str, Any]:
    """Return the suggested values of a form, sections included."""
    values: dict[str, Any] = {}
    for key, value in result["data_schema"].schema.items():
        if isinstance(value, section):
            values[key.schema] = {
                inner.schema: inner.description["suggested_value"]
                for inner in value.schema.schema
                if inner.description
            }
        elif key.description:
            values[key.schema] = key.description["suggested_value"]
    return values


async def test_options_suggest_the_current_values(hass: HomeAssistant) -> None:
    entry = make_entry(
        options={
            CONF_TEMPERATURE: TEMPERATURE_ID,
            CONF_RTE_CLIENT_ID: "my-id",
            CONF_RTE_CLIENT_SECRET: "my-secret",
        }
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert suggested(result) == {
        CONF_TEMPERATURE: TEMPERATURE_ID,
        SECTION_RTE: {CONF_RTE_CLIENT_ID: "my-id", CONF_RTE_CLIENT_SECRET: "my-secret"},
    }


async def test_options_save_checked_credentials(
    hass: HomeAssistant, sources: Sources
) -> None:
    result = await options_flow(hass, credentials(" my-id ", "my-secret"))
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_RTE_CLIENT_ID: "my-id",
        CONF_RTE_CLIENT_SECRET: "my-secret",
    }
    sources.official.async_check_credentials.assert_awaited_once()
    assert sources.official_class.call_args.args[1:] == ("my-id", "my-secret")


@pytest.mark.usefixtures("sources")
async def test_options_clear_credentials(hass: HomeAssistant) -> None:
    result = await options_flow(hass, credentials())
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {}


@pytest.mark.parametrize(
    ("user_input", "check_error", "error"),
    [
        pytest.param(
            credentials("my-id"), None, "incomplete_credentials", id="no_secret"
        ),
        pytest.param(
            credentials("my-id", "bad"),
            TempoAuthError("refused"),
            "invalid_auth",
            id="refused",
        ),
        pytest.param(
            credentials("my-id", "secret"),
            TempoError("down"),
            "cannot_connect",
            id="down",
        ),
    ],
)
async def test_options_errors(
    hass: HomeAssistant,
    sources: Sources,
    user_input: dict[str, Any],
    check_error: Exception | None,
    error: str,
) -> None:
    sources.official.async_check_credentials.side_effect = check_error
    result = await options_flow(hass, user_input)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}
    sources.official.async_check_credentials.side_effect = None
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], credentials("my-id", "secret")
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_options_save_the_temperature(hass: HomeAssistant) -> None:
    await add_temperature(hass, [10.0, 11.0])
    result = await options_flow(
        hass, {CONF_TEMPERATURE: TEMPERATURE_ID, **credentials()}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    # Credentials left empty are removed.
    assert result["data"] == {CONF_TEMPERATURE: TEMPERATURE_ID}


@pytest.mark.parametrize(
    ("unit", "mean_type", "error"),
    [
        pytest.param(
            "kWh", StatisticMeanType.ARITHMETIC, "statistic_not_temperature", id="unit"
        ),
        pytest.param("°C", StatisticMeanType.CIRCULAR, "statistic_no_mean", id="mean"),
        pytest.param(None, None, "statistic_not_found", id="missing"),
    ],
)
async def test_options_temperature_errors(
    hass: HomeAssistant,
    sources: Sources,
    unit: str | None,
    mean_type: StatisticMeanType | None,
    error: str,
) -> None:
    if unit is not None and mean_type is not None:
        await add_temperature(hass, [10.0], unit=unit, mean_type=mean_type)
    result = await options_flow(
        hass,
        {CONF_TEMPERATURE: TEMPERATURE_ID, **credentials("my-id", "secret")},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_TEMPERATURE: error}
    # The credentials wait for a valid temperature.
    sources.official.async_check_credentials.assert_not_awaited()


# Contracts.


async def start_subentry_flow(
    hass: HomeAssistant, entry_id: str, subentry_type: str
) -> Any:
    return await hass.config_entries.subentries.async_init(
        (entry_id, subentry_type), context={"source": SOURCE_USER}
    )


def details(
    name: str = "My contract",
    active_from: str | None = None,
    active_to: str | None = None,
    off_peak: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fill the second step of a contract; `off_peak` holds the HP/HC fields."""
    period = {CONF_ACTIVE_FROM: active_from, CONF_ACTIVE_TO: active_to}
    return {
        CONF_NAME: name,
        **(off_peak or {}),
        SECTION_ACTIVE: {key: value for key, value in period.items() if value},
    }


async def add_contract(
    hass: HomeAssistant,
    entry_id: str,
    first: dict[str, Any],
    second: dict[str, Any],
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
        result["flow_id"], second
    )


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        pytest.param(
            {CONF_KIND: "tempo", CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "6"},
            details(" Tempo ", active_from="2024-01-01"),
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
            {CONF_KIND: "hphc", CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "9"},
            details(
                "HP/HC", off_peak={CONF_OFF_PEAK: "23_07", CONF_WEEKEND_OFF_PEAK: True}
            ),
            {
                CONF_KIND: "hphc",
                CONF_PRICING: PRICING_OFFICIAL,
                CONF_KVA: 9,
                CONF_OFF_PEAK: ["23:00-07:00"],
                CONF_WEEKEND_OFF_PEAK: True,
                CONF_ACTIVE_FROM: None,
                CONF_ACTIVE_TO: None,
            },
            id="hphc",
        ),
        pytest.param(
            # A manual contract keeps no power.
            {CONF_KIND: "base", CONF_PRICING: PRICING_MANUAL, CONF_KVA: "6"},
            details("Offer", "2023-01-01", "2023-12-31"),
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
    second: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await add_contract(hass, entry.entry_id, first, second)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    # The message after it: where the prices go, or where the contract shows.
    manual = expected[CONF_PRICING] == PRICING_MANUAL
    assert result["description"] == ("add_prices" if manual else None)
    (subentry,) = entry.subentries.values()
    assert subentry.title == second[CONF_NAME].strip()
    uid = subentry.data[CONF_UID]
    assert len(uid) == 8
    assert subentry.unique_id == uid
    assert dict(subentry.data) == {CONF_UID: uid, **expected}


@pytest.mark.parametrize(
    ("language", "first", "name"),
    [
        pytest.param(
            "fr",
            {CONF_KIND: "hphc", CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "9"},
            "Heures creuses 9 kVA",
            id="official",
        ),
        pytest.param(
            "en",
            {CONF_KIND: "tempo", CONF_PRICING: PRICING_MANUAL, CONF_KVA: "6"},
            "Tempo · my prices",
            id="manual",
        ),
        pytest.param(
            "de",
            {CONF_KIND: "base", CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "6"},
            # Base 6 kVA is taken.
            "Base 6 kVA 2",
            id="taken",
        ),
    ],
)
async def test_contract_name_is_suggested(
    hass: HomeAssistant, language: str, first: dict[str, Any], name: str
) -> None:
    await hass.config.async_update(language=language)
    entry = make_entry(
        [contract_subentry("base 6 kva", uid="base0001", kind=ContractKind.BASE)]
    )
    entry.add_to_hass(hass)
    result = await start_subentry_flow(hass, entry.entry_id, SUBENTRY_CONTRACT)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], first
    )
    assert result["step_id"] == "details"
    assert suggested(result)[CONF_NAME] == name


async def test_contract_power_must_be_offered(hass: HomeAssistant) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await start_subentry_flow(hass, entry.entry_id, SUBENTRY_CONTRACT)
    # Tempo has no 3 kVA offer.
    tempo = {CONF_KIND: "tempo", CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "3"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], tempo
    )
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_KVA: "kva_not_offered"}
    # Prices set by hand don't depend on it.
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**tempo, CONF_PRICING: PRICING_MANUAL}
    )
    assert result["step_id"] == "details"


async def test_add_contract_with_other_off_peak_hours(hass: HomeAssistant) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await add_contract(
        hass,
        entry.entry_id,
        {CONF_KIND: "hphc", CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "6"},
        details(off_peak={CONF_OFF_PEAK: OFF_PEAK_OTHER, CONF_WEEKEND_OFF_PEAK: False}),
    )
    assert result["step_id"] == "off_peak"
    assert suggested(result) == {CONF_OFF_PEAK: [""]}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_OFF_PEAK: ["01:00 - 07:00", "", "12:30-14:30"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    (subentry,) = entry.subentries.values()
    assert subentry.data[CONF_OFF_PEAK] == ["01:00-07:00", "12:30-14:30"]


@pytest.mark.parametrize(
    "ranges",
    [
        pytest.param(["22h-6h"], id="unreadable_range"),
        pytest.param(["22:15-06:00"], id="quarter_hour"),
        pytest.param(["22:00-22:00"], id="empty_range"),
        pytest.param([" "], id="no_range"),
    ],
)
async def test_other_off_peak_hours_errors(
    hass: HomeAssistant, ranges: list[str]
) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await add_contract(
        hass,
        entry.entry_id,
        {CONF_KIND: "hphc", CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "6"},
        details(off_peak={CONF_OFF_PEAK: OFF_PEAK_OTHER, CONF_WEEKEND_OFF_PEAK: False}),
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_OFF_PEAK: ranges}
    )
    assert result["step_id"] == "off_peak"
    assert result["errors"] == {CONF_OFF_PEAK: "invalid_off_peak"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_OFF_PEAK: ["22:00-06:00"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


@pytest.mark.parametrize(
    ("second", "errors"),
    [
        pytest.param(
            details(active_to="2026-01-01"),
            {SECTION_ACTIVE: "active_to_without_from"},
            id="end_without_start",
        ),
        pytest.param(
            details(active_from="2026-01-01", active_to="2025-12-31"),
            {SECTION_ACTIVE: "end_before_start"},
            id="end_before_start",
        ),
        pytest.param(
            details(active_from="2023-06-01"),
            {SECTION_ACTIVE: "overlapping_active_period"},
            id="overlap",
        ),
        pytest.param(details(" "), {CONF_NAME: "empty_name"}, id="no_name"),
        pytest.param(details("tempo"), {CONF_NAME: "duplicate_name"}, id="taken_name"),
    ],
)
async def test_add_contract_errors(
    hass: HomeAssistant, second: dict[str, Any], errors: dict[str, str]
) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    result = await add_contract(
        hass,
        entry.entry_id,
        {CONF_KIND: "base", CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "6"},
        second,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "details"
    assert result["errors"] == errors
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], details()
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_contract_before_another_one(hass: HomeAssistant) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    result = await add_contract(
        hass,
        entry.entry_id,
        {CONF_KIND: "base", CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "6"},
        details("Old", "2020-01-01", "2023-12-31"),
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_reconfigure_contract(hass: HomeAssistant) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    (subentry,) = entry.subentries.values()
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert suggested(result) == {CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "6"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PRICING: PRICING_MANUAL, CONF_KVA: "6"}
    )
    assert result["step_id"] == "details"
    assert suggested(result) == {
        CONF_NAME: "Tempo",
        SECTION_ACTIVE: {CONF_ACTIVE_FROM: "2024-01-01"},
    }
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], details("My Tempo", "2024-01-01", "2026-10-31")
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


async def test_reconfigure_contract_power(hass: HomeAssistant) -> None:
    entry = make_entry([BASE_CONTRACT])
    entry.add_to_hass(hass)
    (subentry,) = entry.subentries.values()
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "36"}
    )
    # Base stops at 15 kVA.
    assert result["errors"] == {CONF_KVA: "kva_not_offered"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "9"}
    )
    # A contract keeps its own name.
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], details("Base")
    )
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[subentry.subentry_id].data[CONF_KVA] == 9


@pytest.mark.parametrize(
    ("off_peak", "preset", "typed"),
    [
        pytest.param(["22:30-06:30"], "2230_0630", [""], id="preset"),
        pytest.param(
            ["02:00-07:00", "13:00-16:00"],
            OFF_PEAK_OTHER,
            ["02:00-07:00", "13:00-16:00"],
            id="other",
        ),
    ],
)
async def test_reconfigure_off_peak_hours(
    hass: HomeAssistant, off_peak: list[str], preset: str, typed: list[str]
) -> None:
    hphc = contract_subentry(
        "HP/HC", uid="hphc0001", kind=ContractKind.HPHC, off_peak=off_peak
    )
    entry = make_entry([hphc])
    entry.add_to_hass(hass)
    (subentry,) = entry.subentries.values()
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "6"}
    )
    assert suggested(result)[CONF_OFF_PEAK] == preset
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        details(
            "HP/HC",
            off_peak={CONF_OFF_PEAK: OFF_PEAK_OTHER, CONF_WEEKEND_OFF_PEAK: False},
        ),
    )
    assert suggested(result) == {CONF_OFF_PEAK: typed}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_OFF_PEAK: ["23:00-07:00"]}
    )
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[subentry.subentry_id].data[CONF_OFF_PEAK] == ["23:00-07:00"]


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
