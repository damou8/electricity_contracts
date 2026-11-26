"""Tests of the config, options and subentry flows."""

from datetime import timedelta
from typing import Any

import pytest
from elec_tariffs import ContractKind, GasProfile, TempoAuthError, TempoError
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.config_entries import (
    SOURCE_USER,
    ConfigSubentryData,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, section

from custom_components.electricity_contracts.config_flow import (
    async_energy_statistics,
)
from custom_components.electricity_contracts.const import (
    CONF_ACTIVE_FROM,
    CONF_ACTIVE_TO,
    CONF_END,
    CONF_FIXED_PER_YEAR,
    CONF_HEATING_CONTENT,
    CONF_HEATING_ENERGY,
    CONF_HEATING_STATISTICS,
    CONF_INDOOR_TEMPERATURES,
    CONF_KIND,
    CONF_KVA,
    CONF_OFF_PEAK,
    CONF_PERIODS,
    CONF_PRICE,
    CONF_PRICE_ENTITY,
    CONF_PRICES,
    CONF_PRICING,
    CONF_PROFILE,
    CONF_RTE_CLIENT_ID,
    CONF_RTE_CLIENT_SECRET,
    CONF_START,
    CONF_STATISTIC_ID,
    CONF_TEMPERATURE,
    CONF_UID,
    CONF_WATER_ENERGY,
    CONF_WATER_STATISTIC,
    CONF_WEATHER,
    CONF_WEEKEND_OFF_PEAK,
    CONTENT_HEATING,
    CONTENT_HEATING_WATER,
    DOMAIN,
    ENERGY_ELECTRICITY,
    ENERGY_GAS,
    NO_METER,
    OFF_PEAK_OTHER,
    PRICING_ENTITY,
    PRICING_MANUAL,
    PRICING_OFFICIAL,
    SECTION_ACTIVE,
    SECTION_HEATING,
    SECTION_WATER,
    SUBENTRY_CONTRACT,
    SUBENTRY_GAS_CONTRACT,
)

from .conftest import (
    BASE_CONTRACT,
    OTHER_STATISTIC_ID,
    PRICE_ID,
    STATISTIC_ID,
    TEMPERATURE_ID,
    TEMPO_CONTRACT,
    Sources,
    add_price,
    add_statistic,
    add_temperature,
    contract_subentry,
    gas_contract_subentry,
    gas_period,
    make_entry,
    manual_contract,
    manual_period,
)
from .test_heating import GAS, HEATER_A, INDOOR, WATER, add_energy, add_indoor

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
    schema = result["data_schema"]
    assert schema is not None
    (field,) = schema.schema
    assert field.description == {"suggested_value": OTHER_STATISTIC_ID}


@pytest.mark.usefixtures("statistic")
async def test_user_flow_suggests_only_a_new_linky(hass: HomeAssistant) -> None:
    # Gas, say, and a Linky already set up: no meter is the likelier answer.
    await add_statistic(hass, "meter:energy")
    make_entry().add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    schema = result["data_schema"]
    assert schema is not None
    (field,) = schema.schema
    assert field.description is None


async def test_user_flow_without_meter(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    # No statistic to suggest: the field starts empty.
    schema = result["data_schema"]
    assert schema is not None
    (field,) = schema.schema
    assert field.description is None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "No meter"
    assert result["data"] == {}
    assert result["result"].unique_id == NO_METER

    # Only one source without a meter.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_flow_without_meter_in_french(hass: HomeAssistant) -> None:
    hass.config.language = "fr"
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["title"] == "Sans compteur"


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
    # The title named the former meter.
    assert entry.title == "Linky 11111111111111"


@pytest.mark.usefixtures("statistic")
async def test_reconfigure_without_meter_and_back(hass: HomeAssistant) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == NO_METER
    assert entry.data == {}
    assert entry.title == "No meter"

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATISTIC_ID: STATISTIC_ID}
    )
    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == STATISTIC_ID
    assert entry.data == {CONF_STATISTIC_ID: STATISTIC_ID}
    assert entry.title == "Linky 00000000000000"


@pytest.mark.usefixtures("statistic")
async def test_reconfigure_keeps_a_title_of_your_own(hass: HomeAssistant) -> None:
    await add_statistic(hass, OTHER_STATISTIC_ID)
    entry = make_entry()
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(entry, title="Home")
    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATISTIC_ID: OTHER_STATISTIC_ID}
    )
    assert result["reason"] == "reconfigure_successful"
    assert entry.title == "Home"


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


async def options_page(
    hass: HomeAssistant,
    page: str,
    user_input: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> Any:
    """Open one page of the options from their menu, and fill it."""
    entry = make_entry(options=options if options is not None else OTHER_OPTIONS)
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["outdoor", "indoor", "heating", "rte"]
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": page}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == page
    return await hass.config_entries.options.async_configure(
        result["flow_id"], user_input
    )


# What the other pages set: each page keeps them.
OTHER_OPTIONS: dict[str, Any] = {CONF_INDOOR_TEMPERATURES: ["sensor.living_room"]}


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


async def open_page(hass: HomeAssistant, options: dict[str, Any], page: str) -> Any:
    entry = make_entry(options=options)
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    return await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": page}
    )


@pytest.mark.parametrize(
    ("page", "expected"),
    [
        pytest.param(
            "outdoor",
            {CONF_TEMPERATURE: TEMPERATURE_ID, CONF_WEATHER: True},
            id="outdoor",
        ),
        pytest.param("indoor", {CONF_INDOOR_TEMPERATURES: [INDOOR]}, id="indoor"),
        pytest.param(
            "heating",
            {
                SECTION_HEATING: {
                    CONF_HEATING_STATISTICS: [HEATER_A],
                    CONF_HEATING_ENERGY: ENERGY_GAS,
                },
                SECTION_WATER: {CONF_WATER_STATISTIC: WATER},
            },
            id="heating",
        ),
        pytest.param(
            "rte",
            {CONF_RTE_CLIENT_ID: "my-id", CONF_RTE_CLIENT_SECRET: "my-secret"},
            id="rte",
        ),
    ],
)
async def test_options_suggest_the_current_values(
    hass: HomeAssistant, page: str, expected: dict[str, Any]
) -> None:
    options = {
        CONF_TEMPERATURE: TEMPERATURE_ID,
        CONF_WEATHER: True,
        CONF_INDOOR_TEMPERATURES: [INDOOR],
        SECTION_HEATING: {
            CONF_HEATING_STATISTICS: [HEATER_A],
            CONF_HEATING_ENERGY: ENERGY_GAS,
            CONF_WATER_STATISTIC: WATER,
        },
        CONF_RTE_CLIENT_ID: "my-id",
        CONF_RTE_CLIENT_SECRET: "my-secret",
    }
    result = await open_page(hass, options, page)
    assert suggested(result) == expected


async def test_options_suggest_nothing_when_empty(hass: HomeAssistant) -> None:
    result = await open_page(hass, {}, "heating")
    assert suggested(result) == {SECTION_HEATING: {}, SECTION_WATER: {}}


async def test_options_save_checked_credentials(
    hass: HomeAssistant, sources: Sources
) -> None:
    result = await options_page(
        hass,
        "rte",
        {CONF_RTE_CLIENT_ID: " my-id ", CONF_RTE_CLIENT_SECRET: "my-secret"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        **OTHER_OPTIONS,
        CONF_RTE_CLIENT_ID: "my-id",
        CONF_RTE_CLIENT_SECRET: "my-secret",
    }
    sources.official.async_check_credentials.assert_awaited_once()
    assert sources.official_class.call_args.args[1:] == ("my-id", "my-secret")


@pytest.mark.usefixtures("sources")
async def test_options_clear_credentials(hass: HomeAssistant) -> None:
    result = await options_page(
        hass,
        "rte",
        {},
        options={CONF_RTE_CLIENT_ID: "old", CONF_RTE_CLIENT_SECRET: "x"},
    )
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
    user_input: dict[str, Any],
    check_error: Exception | None,
    error: str,
) -> None:
    sources.official.async_check_credentials.side_effect = check_error
    result = await options_page(hass, "rte", user_input)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}
    sources.official.async_check_credentials.side_effect = None
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_RTE_CLIENT_ID: "my-id", CONF_RTE_CLIENT_SECRET: "s"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_options_save_the_temperature(hass: HomeAssistant) -> None:
    await add_temperature(hass, [10.0, 11.0])
    result = await options_page(
        hass,
        "outdoor",
        {CONF_TEMPERATURE: TEMPERATURE_ID},
        options={**OTHER_OPTIONS, CONF_WEATHER: True},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    # Open-Meteo, left off, is removed.
    assert result["data"] == {**OTHER_OPTIONS, CONF_TEMPERATURE: TEMPERATURE_ID}


async def test_options_save_open_meteo(hass: HomeAssistant) -> None:
    result = await options_page(hass, "outdoor", {CONF_WEATHER: True})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {**OTHER_OPTIONS, CONF_WEATHER: True}


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
    unit: str | None,
    mean_type: StatisticMeanType | None,
    error: str,
) -> None:
    if unit is not None and mean_type is not None:
        await add_temperature(hass, [10.0], unit=unit, mean_type=mean_type)
    result = await options_page(hass, "outdoor", {CONF_TEMPERATURE: TEMPERATURE_ID})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_TEMPERATURE: error}


async def test_options_save_the_indoor_thermometers(hass: HomeAssistant) -> None:
    await add_indoor(hass, [19.0, 19.5])
    result = await options_page(
        hass, "indoor", {CONF_INDOOR_TEMPERATURES: [INDOOR]}, options={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_INDOOR_TEMPERATURES: [INDOOR]}


async def test_options_clear_the_indoor_thermometers(hass: HomeAssistant) -> None:
    result = await options_page(hass, "indoor", {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {}


async def test_options_indoor_errors(hass: HomeAssistant) -> None:
    await add_indoor(hass, [19.0])
    await add_energy(hass, HEATER_A, [1.0])
    result = await options_page(
        hass, "indoor", {CONF_INDOOR_TEMPERATURES: [INDOOR, HEATER_A]}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {
        CONF_INDOOR_TEMPERATURES: "indoor_statistic_not_temperature"
    }


def heating_page(
    heating: dict[str, Any] | None = None, water: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Fill the heating page: the frontend always sends both sections."""
    return {SECTION_HEATING: heating or {}, SECTION_WATER: water or {}}


async def test_options_save_the_heating(hass: HomeAssistant) -> None:
    for statistic_id in (HEATER_A, WATER):
        await add_energy(hass, statistic_id, [1.0, 1.0])
    result = await options_page(
        hass,
        "heating",
        heating_page(
            # Twice the same: kept once.
            {
                CONF_HEATING_STATISTICS: [HEATER_A, HEATER_A],
                CONF_HEATING_CONTENT: CONTENT_HEATING,
            },
            {CONF_WATER_STATISTIC: WATER, CONF_WATER_ENERGY: ENERGY_GAS},
        ),
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        **OTHER_OPTIONS,
        SECTION_HEATING: {
            CONF_HEATING_STATISTICS: [HEATER_A],
            CONF_HEATING_ENERGY: ENERGY_ELECTRICITY,
            CONF_HEATING_CONTENT: CONTENT_HEATING,
            CONF_WATER_STATISTIC: WATER,
            CONF_WATER_ENERGY: ENERGY_GAS,
        },
    }


async def test_options_save_only_the_heating_set(hass: HomeAssistant) -> None:
    await add_energy(hass, GAS, [3.0])
    result = await options_page(
        hass,
        "heating",
        heating_page({CONF_HEATING_STATISTICS: [GAS], CONF_HEATING_ENERGY: ENERGY_GAS}),
    )
    assert result["data"] == {
        **OTHER_OPTIONS,
        SECTION_HEATING: {
            CONF_HEATING_STATISTICS: [GAS],
            CONF_HEATING_ENERGY: ENERGY_GAS,
            CONF_HEATING_CONTENT: CONTENT_HEATING,
        },
    }


async def test_options_clear_the_heating(hass: HomeAssistant) -> None:
    result = await options_page(
        hass,
        "heating",
        heating_page(),
        options={SECTION_HEATING: {CONF_HEATING_STATISTICS: [GAS]}},
    )
    assert result["data"] == {}


@pytest.mark.parametrize(
    ("heating", "water", "errors"),
    [
        pytest.param(
            {CONF_HEATING_STATISTICS: [HEATER_A, STATISTIC_ID]},
            {},
            {"base": "heating_is_source"},
            id="source",
        ),
        pytest.param(
            {CONF_HEATING_STATISTICS: ["sensor.missing"]},
            {},
            {"base": "heating_statistic_not_found"},
            id="missing",
        ),
        pytest.param(
            {CONF_HEATING_STATISTICS: [HEATER_A]},
            {CONF_WATER_STATISTIC: HEATER_A},
            {"base": "water_in_heating"},
            id="water_in_heating",
        ),
        pytest.param(
            {},
            {CONF_WATER_STATISTIC: "sensor.missing"},
            {"base": "water_statistic_not_found"},
            id="water_missing",
        ),
        pytest.param(
            {},
            {CONF_WATER_STATISTIC: STATISTIC_ID},
            {"base": "water_is_source"},
            id="water_source",
        ),
        pytest.param(
            {
                CONF_HEATING_STATISTICS: [HEATER_A],
                CONF_HEATING_ENERGY: ENERGY_GAS,
                CONF_HEATING_CONTENT: CONTENT_HEATING_WATER,
            },
            {CONF_WATER_STATISTIC: WATER},
            {"base": "water_other_energy"},
            id="water_other_energy",
        ),
    ],
)
async def test_options_heating_errors(
    hass: HomeAssistant,
    heating: dict[str, Any],
    water: dict[str, Any],
    errors: dict[str, str],
) -> None:
    await add_energy(hass, HEATER_A, [1.0])
    await add_energy(hass, WATER, [1.0])
    result = await options_page(hass, "heating", heating_page(heating, water))
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == errors


# Electricity contracts.


async def start_subentry_flow(
    hass: HomeAssistant, entry_id: str, subentry_type: str
) -> Any:
    return await hass.config_entries.subentries.async_init(
        (entry_id, subentry_type), context={"source": SOURCE_USER}
    )


async def configure(hass: HomeAssistant, result: Any, user_input: Any) -> Any:
    return await hass.config_entries.subentries.async_configure(
        result["flow_id"], user_input
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
    result = await configure(hass, result, first)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "details"
    return await configure(hass, result, second)


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
    (subentry,) = entry.subentries.values()
    assert subentry.title == second[CONF_NAME].strip()
    uid = subentry.data[CONF_UID]
    assert len(uid) == 8
    assert subentry.unique_id == uid
    assert dict(subentry.data) == {CONF_UID: uid, **expected}


async def test_add_contract_with_its_prices(hass: HomeAssistant) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await add_contract(
        hass,
        entry.entry_id,
        # A manual contract keeps no power.
        {CONF_KIND: "hphc", CONF_PRICING: PRICING_MANUAL, CONF_KVA: "6"},
        details(
            "Offer",
            "2025-01-01",
            off_peak={CONF_OFF_PEAK: "22_06", CONF_WEEKEND_OFF_PEAK: False},
        ),
    )
    assert result["step_id"] == "first_period"
    # The first prices start with the contract.
    assert suggested(result) == {CONF_START: "2025-01-01"}
    assert set(result["data_schema"].schema) == {
        CONF_START,
        CONF_END,
        CONF_FIXED_PER_YEAR,
        "hc",
        "hp",
    }
    result = await configure(
        hass,
        result,
        {CONF_START: "2025-01-01", CONF_FIXED_PER_YEAR: 151.2, "hc": 0.16, "hp": 0.21},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    (subentry,) = entry.subentries.values()
    assert subentry.data[CONF_PRICING] == PRICING_MANUAL
    assert CONF_KVA not in subentry.data
    assert subentry.data[CONF_PERIODS] == [
        {
            CONF_START: "2025-01-01",
            CONF_END: None,
            CONF_FIXED_PER_YEAR: 151.2,
            CONF_PRICES: {"hc": 0.16, "hp": 0.21},
        }
    ]


async def test_add_contract_priced_by_a_sensor(hass: HomeAssistant) -> None:
    await add_price(hass, [0.2])
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await add_contract(
        hass,
        entry.entry_id,
        {CONF_KIND: "base", CONF_PRICING: PRICING_ENTITY, CONF_KVA: "6"},
        details("Dynamic"),
    )
    assert result["step_id"] == "price_entity"
    result = await configure(
        hass, result, {CONF_PRICE_ENTITY: PRICE_ID, CONF_FIXED_PER_YEAR: 120}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    (subentry,) = entry.subentries.values()
    assert subentry.data[CONF_PRICE_ENTITY] == PRICE_ID
    assert subentry.data[CONF_FIXED_PER_YEAR] == 120.0
    assert CONF_PERIODS not in subentry.data


@pytest.mark.parametrize(
    ("unit", "mean_type", "error"),
    [
        pytest.param(
            "€", StatisticMeanType.ARITHMETIC, "price_entity_not_per_kwh", id="unit"
        ),
        # Cents would make every cost 100 times too high.
        pytest.param(
            "c€/kWh",
            StatisticMeanType.ARITHMETIC,
            "price_entity_not_per_kwh",
            id="cents",
        ),
        pytest.param(
            "€/kWh", StatisticMeanType.CIRCULAR, "price_entity_no_mean", id="mean"
        ),
        pytest.param(None, None, "price_entity_not_found", id="missing"),
    ],
)
async def test_price_entity_errors(
    hass: HomeAssistant,
    unit: str | None,
    mean_type: StatisticMeanType | None,
    error: str,
) -> None:
    if unit is not None and mean_type is not None:
        await add_price(hass, [0.2], unit=unit, mean_type=mean_type)
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await add_contract(
        hass,
        entry.entry_id,
        {CONF_KIND: "base", CONF_PRICING: PRICING_ENTITY, CONF_KVA: "6"},
        details("Dynamic"),
    )
    result = await configure(
        hass, result, {CONF_PRICE_ENTITY: PRICE_ID, CONF_FIXED_PER_YEAR: 0}
    )
    assert result["step_id"] == "price_entity"
    assert result["errors"] == {CONF_PRICE_ENTITY: error}


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
            "fr",
            {CONF_KIND: "base", CONF_PRICING: PRICING_ENTITY, CONF_KVA: "6"},
            "Base · prix d'un capteur",
            id="entity",
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
    result = await configure(hass, result, first)
    assert result["step_id"] == "details"
    assert suggested(result)[CONF_NAME] == name


async def test_contract_power_must_be_offered(hass: HomeAssistant) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await start_subentry_flow(hass, entry.entry_id, SUBENTRY_CONTRACT)
    # Tempo has no 3 kVA offer.
    tempo = {CONF_KIND: "tempo", CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "3"}
    result = await configure(hass, result, tempo)
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_KVA: "kva_not_offered"}
    # Prices set by hand don't depend on it.
    result = await configure(hass, result, {**tempo, CONF_PRICING: PRICING_MANUAL})
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
    result = await configure(
        hass, result, {CONF_OFF_PEAK: ["01:00 - 07:00", "", "12:30-14:30"]}
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
    result = await configure(hass, result, {CONF_OFF_PEAK: ranges})
    assert result["step_id"] == "off_peak"
    assert result["errors"] == {CONF_OFF_PEAK: "invalid_off_peak"}
    result = await configure(hass, result, {CONF_OFF_PEAK: ["22:00-06:00"]})
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
    # A gas contract neither takes a name nor days from electricity contracts.
    entry = make_entry([TEMPO_CONTRACT, gas_contract_subentry("My contract")])
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
    result = await configure(hass, result, details())
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


async def test_reconfigure_contract_to_my_prices(hass: HomeAssistant) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    (subentry,) = entry.subentries.values()
    # A contract at regulated prices has no menu: its pencil opens it.
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "contract"
    assert suggested(result) == {CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "6"}
    result = await configure(
        hass, result, {CONF_PRICING: PRICING_MANUAL, CONF_KVA: "6"}
    )
    assert result["step_id"] == "details"
    assert suggested(result) == {
        CONF_NAME: "Tempo",
        SECTION_ACTIVE: {CONF_ACTIVE_FROM: "2024-01-01"},
    }
    result = await configure(
        hass, result, details("My Tempo", "2024-01-01", "2026-10-31")
    )
    # Without prices yet, it asks for them.
    assert result["step_id"] == "first_period"
    prices = dict.fromkeys(
        ["blue_hc", "blue_hp", "white_hc", "white_hp", "red_hc", "red_hp"], 0.2
    )
    result = await configure(
        hass, result, {CONF_START: "2024-01-01", CONF_FIXED_PER_YEAR: 180, **prices}
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
        CONF_PERIODS: [
            {
                CONF_START: "2024-01-01",
                CONF_END: None,
                CONF_FIXED_PER_YEAR: 180.0,
                CONF_PRICES: prices,
            }
        ],
    }


async def test_reconfigure_contract_power(hass: HomeAssistant) -> None:
    entry = make_entry([BASE_CONTRACT])
    entry.add_to_hass(hass)
    (subentry,) = entry.subentries.values()
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    result = await configure(
        hass, result, {CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "36"}
    )
    # Base stops at 15 kVA.
    assert result["errors"] == {CONF_KVA: "kva_not_offered"}
    result = await configure(
        hass, result, {CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "9"}
    )
    # A contract keeps its own name.
    result = await configure(hass, result, details("Base"))
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
    result = await configure(
        hass, result, {CONF_PRICING: PRICING_OFFICIAL, CONF_KVA: "6"}
    )
    assert suggested(result)[CONF_OFF_PEAK] == preset
    result = await configure(
        hass,
        result,
        details(
            "HP/HC",
            off_peak={CONF_OFF_PEAK: OFF_PEAK_OTHER, CONF_WEEKEND_OFF_PEAK: False},
        ),
    )
    assert suggested(result) == {CONF_OFF_PEAK: typed}
    result = await configure(hass, result, {CONF_OFF_PEAK: ["23:00-07:00"]})
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[subentry.subentry_id].data[CONF_OFF_PEAK] == ["23:00-07:00"]


async def test_reconfigure_the_sensor(hass: HomeAssistant) -> None:
    await add_price(hass, [0.2])
    dynamic = contract_subentry(
        "Dynamic",
        uid="dyn00001",
        kind=ContractKind.BASE,
        pricing=PRICING_ENTITY,
        price_entity="sensor.old_price",
        fixed_per_year=100.0,
    )
    entry = make_entry([dynamic])
    entry.add_to_hass(hass)
    (subentry,) = entry.subentries.values()
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    assert result["step_id"] == "contract"
    result = await configure(
        hass, result, {CONF_PRICING: PRICING_ENTITY, CONF_KVA: "6"}
    )
    result = await configure(hass, result, details("Dynamic"))
    assert result["step_id"] == "price_entity"
    assert suggested(result) == {
        CONF_PRICE_ENTITY: "sensor.old_price",
        CONF_FIXED_PER_YEAR: 100.0,
    }
    result = await configure(
        hass, result, {CONF_PRICE_ENTITY: PRICE_ID, CONF_FIXED_PER_YEAR: 110}
    )
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[subentry.subentry_id].data[CONF_PRICE_ENTITY] == PRICE_ID


# The menu of a contract priced by hand.

TWO_PERIODS = manual_contract(
    manual_period("2025-01-01", "2026-07-31"), manual_period("2026-08-01", base=0.2)
)


async def open_menu(
    hass: HomeAssistant, subentries: list[ConfigSubentryData] | None = None
) -> tuple[Any, Any]:
    entry = make_entry(subentries or [TWO_PERIODS])
    entry.add_to_hass(hass)
    subentry = next(iter(entry.subentries.values()))
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    return entry, result


@pytest.mark.parametrize(
    ("language", "labels"),
    [
        pytest.param(
            "fr",
            {
                "contract": "Le contrat : nom, prix, heures creuses et dates",
                "period_0": "Prix du 1er janvier 2025 au 31 juillet 2026",
                "period_1": "Prix depuis le 1er août 2026",
                "add_period": "Ajouter une période de prix",
                "remove_period": "Supprimer une période de prix",
            },
            id="fr",
        ),
        pytest.param(
            "de",
            {
                "contract": "The contract: name, prices, off-peak hours and dates",
                "period_0": "Prices from 1 January 2025 to 31 July 2026",
                "period_1": "Prices since 1 August 2026",
                "add_period": "Add a price period",
                "remove_period": "Remove a price period",
            },
            id="other",
        ),
    ],
)
async def test_menu_lists_the_price_periods(
    hass: HomeAssistant, language: str, labels: dict[str, str]
) -> None:
    await hass.config.async_update(language=language)
    _, result = await open_menu(hass)
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "reconfigure"
    assert result["menu_options"] == labels
    assert result["description_placeholders"] == {"name": "Offer"}


async def test_menu_of_one_period_removes_none(hass: HomeAssistant) -> None:
    _, result = await open_menu(hass, [manual_contract(manual_period("2026-01-01"))])
    assert list(result["menu_options"]) == ["contract", "period_0", "add_period"]


async def test_change_a_price_period(hass: HomeAssistant) -> None:
    entry, result = await open_menu(hass)
    result = await configure(hass, result, {"next_step_id": "period_1"})
    assert result["step_id"] == "period"
    assert suggested(result) == {
        CONF_START: "2026-08-01",
        CONF_FIXED_PER_YEAR: 150.0,
        "base": 0.2,
    }
    result = await configure(
        hass,
        result,
        {CONF_START: "2026-07-01", CONF_FIXED_PER_YEAR: 150} | {"base": 0.21},
    )
    assert result["errors"] == {"base": "overlapping_price_period"}
    result = await configure(
        hass,
        result,
        {CONF_START: "2026-08-01", CONF_END: "2026-12-31", CONF_FIXED_PER_YEAR: 160}
        | {"base": 0.21},
    )
    assert result["reason"] == "reconfigure_successful"
    (subentry,) = entry.subentries.values()
    assert subentry.data[CONF_PERIODS] == [
        manual_period("2025-01-01", "2026-07-31"),
        manual_period("2026-08-01", "2026-12-31", base=0.21, fixed=160.0),
    ]


async def test_add_a_price_period_ends_the_open_one(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to("2027-01-20 12:00:00+01:00")
    entry, result = await open_menu(hass)
    result = await configure(hass, result, {"next_step_id": "add_period"})
    assert result["step_id"] == "period"
    # New prices start today at the earliest.
    assert suggested(result) == {CONF_START: "2027-01-20"}
    result = await configure(
        hass, result, {CONF_START: "2027-02-01", CONF_FIXED_PER_YEAR: 155, "base": 0.22}
    )
    assert result["reason"] == "reconfigure_successful"
    (subentry,) = entry.subentries.values()
    assert subentry.data[CONF_PERIODS] == [
        manual_period("2025-01-01", "2026-07-31"),
        manual_period("2026-08-01", "2027-01-31", base=0.2),
        manual_period("2027-02-01", base=0.22, fixed=155.0),
    ]


async def test_add_a_price_period_the_day_the_open_one_starts(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    freezer.move_to("2026-08-01 12:00:00+02:00")
    _, result = await open_menu(hass)
    result = await configure(hass, result, {"next_step_id": "add_period"})
    # Today would overlap the open prices, which start today.
    assert suggested(result) == {CONF_START: "2026-08-02"}


async def test_add_a_price_period_after_the_last_one(hass: HomeAssistant) -> None:
    _, result = await open_menu(
        hass, [manual_contract(manual_period("2025-01-01", "2025-12-31"))]
    )
    result = await configure(hass, result, {"next_step_id": "add_period"})
    # The day after the last prices.
    assert suggested(result) == {CONF_START: "2026-01-01"}


@pytest.mark.parametrize(
    ("period", "errors"),
    [
        pytest.param(
            {CONF_START: "2026-02-01", CONF_END: "2026-01-31"},
            {CONF_END: "end_before_start"},
            id="end_before_start",
        ),
        pytest.param(
            {CONF_START: "2024-12-01", CONF_END: "2025-02-01"},
            {"base": "overlapping_price_period"},
            id="overlap",
        ),
    ],
)
async def test_add_price_period_errors(
    hass: HomeAssistant, period: dict[str, str], errors: dict[str, str]
) -> None:
    _, result = await open_menu(hass)
    result = await configure(hass, result, {"next_step_id": "add_period"})
    result = await configure(
        hass, result, {CONF_FIXED_PER_YEAR: 150, "base": 0.19, **period}
    )
    assert result["step_id"] == "period"
    assert result["errors"] == errors
    result = await configure(
        hass,
        result,
        {CONF_START: "2024-01-01", CONF_END: "2024-12-31"}
        | {CONF_FIXED_PER_YEAR: 140, "base": 0.18},
    )
    assert result["reason"] == "reconfigure_successful"


async def test_remove_a_price_period(hass: HomeAssistant) -> None:
    entry, result = await open_menu(hass)
    result = await configure(hass, result, {"next_step_id": "remove_period"})
    assert result["step_id"] == "remove_period"
    result = await configure(hass, result, {"period": "0"})
    assert result["reason"] == "reconfigure_successful"
    (subentry,) = entry.subentries.values()
    assert subentry.data[CONF_PERIODS] == [manual_period("2026-08-01", base=0.2)]


async def test_menu_opens_the_contract(hass: HomeAssistant) -> None:
    entry, result = await open_menu(hass)
    result = await configure(hass, result, {"next_step_id": "contract"})
    assert result["step_id"] == "contract"
    result = await configure(
        hass, result, {CONF_PRICING: PRICING_MANUAL, CONF_KVA: "6"}
    )
    result = await configure(hass, result, details("Offer 2"))
    # Its prices are kept.
    assert result["reason"] == "reconfigure_successful"
    (subentry,) = entry.subentries.values()
    assert subentry.title == "Offer 2"
    assert len(subentry.data[CONF_PERIODS]) == 2


async def test_only_period_steps_are_made_up(hass: HomeAssistant) -> None:
    _, result = await open_menu(hass)
    flow: Any = hass.config_entries.subentries._progress[result["flow_id"]]
    assert hasattr(flow, "async_step_period_1")
    assert not hasattr(flow, "async_step_period_x")
    assert not hasattr(flow, "async_step_other")


# Gas contracts.


async def add_gas_contract(
    hass: HomeAssistant, entry_id: str, first: dict[str, Any], second: dict[str, Any]
) -> Any:
    result = await start_subentry_flow(hass, entry_id, SUBENTRY_GAS_CONTRACT)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    result = await configure(hass, result, first)
    assert result["step_id"] == "details"
    return await configure(hass, result, second)


@pytest.mark.parametrize(
    ("language", "profile", "name"),
    [
        pytest.param("fr", "heating", "Gaz · prix repère chauffage", id="heating"),
        pytest.param(
            "en",
            "cooking_water",
            "Gas · reference price, cooking and hot water",
            id="cooking",
        ),
    ],
)
async def test_add_gas_contract_at_the_reference_price(
    hass: HomeAssistant, language: str, profile: str, name: str
) -> None:
    await hass.config.async_update(language=language)
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await start_subentry_flow(hass, entry.entry_id, SUBENTRY_GAS_CONTRACT)
    result = await configure(
        hass, result, {CONF_PRICING: PRICING_OFFICIAL, CONF_PROFILE: profile}
    )
    assert suggested(result) == {CONF_NAME: name, SECTION_ACTIVE: {}}
    result = await configure(hass, result, {CONF_NAME: name, SECTION_ACTIVE: {}})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    (subentry,) = entry.subentries.values()
    assert subentry.subentry_type == SUBENTRY_GAS_CONTRACT
    assert subentry.title == name
    assert dict(subentry.data) == {
        CONF_UID: subentry.unique_id,
        CONF_PRICING: PRICING_OFFICIAL,
        CONF_PROFILE: profile,
        CONF_ACTIVE_FROM: None,
        CONF_ACTIVE_TO: None,
    }


async def test_add_gas_contract_with_my_prices(hass: HomeAssistant) -> None:
    await hass.config.async_update(language="fr")
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await start_subentry_flow(hass, entry.entry_id, SUBENTRY_GAS_CONTRACT)
    # The profile only counts with the reference price.
    result = await configure(
        hass, result, {CONF_PRICING: PRICING_MANUAL, CONF_PROFILE: "heating"}
    )
    assert suggested(result)[CONF_NAME] == "Gaz · mes prix"
    result = await configure(hass, result, details("Gaz", "2026-08-01"))
    assert result["step_id"] == "first_period"
    assert set(result["data_schema"].schema) == {
        CONF_START,
        CONF_END,
        CONF_FIXED_PER_YEAR,
        CONF_PRICE,
    }
    assert suggested(result) == {CONF_START: "2026-08-01"}
    result = await configure(
        hass,
        result,
        {CONF_START: "2026-08-01", CONF_FIXED_PER_YEAR: 281.4, CONF_PRICE: 0.105},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    (subentry,) = entry.subentries.values()
    assert CONF_PROFILE not in subentry.data
    assert subentry.data[CONF_PERIODS] == [
        {
            CONF_START: "2026-08-01",
            CONF_END: None,
            CONF_FIXED_PER_YEAR: 281.4,
            CONF_PRICE: 0.105,
        }
    ]


async def test_add_gas_contract_priced_by_a_sensor(hass: HomeAssistant) -> None:
    await add_price(hass, [0.1])
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await add_gas_contract(
        hass,
        entry.entry_id,
        {CONF_PRICING: PRICING_ENTITY, CONF_PROFILE: "heating"},
        details("Gas"),
    )
    assert result["step_id"] == "price_entity"
    result = await configure(
        hass, result, {CONF_PRICE_ENTITY: PRICE_ID, CONF_FIXED_PER_YEAR: 250}
    )
    (subentry,) = entry.subentries.values()
    assert subentry.data[CONF_PRICE_ENTITY] == PRICE_ID
    assert subentry.data[CONF_FIXED_PER_YEAR] == 250.0


@pytest.mark.parametrize(
    ("second", "errors"),
    [
        # The first gas contract is in force since always.
        pytest.param(
            details("Gas 2"), {SECTION_ACTIVE: "overlapping_active_period"}, id="always"
        ),
        pytest.param(
            details("Gas", "2026-08-01"), {CONF_NAME: "duplicate_name"}, id="taken_name"
        ),
    ],
)
async def test_add_gas_contract_errors(
    hass: HomeAssistant, second: dict[str, Any], errors: dict[str, str]
) -> None:
    entry = make_entry([gas_contract_subentry("Gas", active_to="2026-07-31")])
    entry.add_to_hass(hass)
    result = await add_gas_contract(
        hass,
        entry.entry_id,
        {CONF_PRICING: PRICING_OFFICIAL, CONF_PROFILE: "heating"},
        second,
    )
    assert result["step_id"] == "details"
    assert result["errors"] == errors
    result = await configure(hass, result, details("New gas", "2026-08-01"))
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_reconfigure_gas_contract(hass: HomeAssistant) -> None:
    entry = make_entry(
        [
            gas_contract_subentry(
                "Gas", pricing=PRICING_OFFICIAL, profile=GasProfile.HEATING
            )
        ]
    )
    entry.add_to_hass(hass)
    (subentry,) = entry.subentries.values()
    result = await entry.start_subentry_reconfigure_flow(hass, subentry.subentry_id)
    assert result["step_id"] == "contract"
    assert suggested(result) == {
        CONF_PRICING: PRICING_OFFICIAL,
        CONF_PROFILE: "heating",
    }
    result = await configure(
        hass, result, {CONF_PRICING: PRICING_OFFICIAL, CONF_PROFILE: "cooking_water"}
    )
    # Its own days don't overlap another contract.
    result = await configure(hass, result, details("Gas"))
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[subentry.subentry_id].data[CONF_PROFILE] == "cooking_water"


async def test_gas_contract_menu(hass: HomeAssistant) -> None:
    gas = gas_contract_subentry("Gas", periods=[gas_period(0.1, "2026-01-01")])
    entry, result = await open_menu(hass, [gas])
    assert result["menu_options"]["contract"] == "The contract: name, prices and dates"
    result = await configure(hass, result, {"next_step_id": "period_0"})
    assert suggested(result) == {
        CONF_START: "2026-01-01",
        CONF_FIXED_PER_YEAR: 0.0,
        CONF_PRICE: 0.1,
    }
    result = await configure(
        hass,
        result,
        {CONF_START: "2026-01-01", CONF_FIXED_PER_YEAR: 200, CONF_PRICE: 0.11},
    )
    assert result["reason"] == "reconfigure_successful"
    (subentry,) = entry.subentries.values()
    assert subentry.data[CONF_PERIODS] == [gas_period(0.11, "2026-01-01", fixed=200.0)]
