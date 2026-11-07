"""Tests of the comparisons, their sensors and the compare action."""

from datetime import UTC, date, datetime
from typing import Any
from unittest.mock import patch

import pytest
from elec_tariffs import ContractKind, PricePeriod, Tranche
from homeassistant.components.recorder.statistics import statistic_during_period
from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import ATTR_CONFIG_ENTRY_ID, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.recorder import get_instance
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.electricity_contracts.comparison import (
    WINDOW_CURRENT_MONTH,
    WINDOW_CURRENT_YEAR,
    WINDOW_FIXED,
    WINDOW_LAST_12_MONTHS,
    WINDOW_TEMPO_SEASON,
    async_wait_for_recorder,
    window_days,
)
from custom_components.electricity_contracts.const import (
    CONF_CONTRACTS,
    CONF_END,
    CONF_START,
    CONF_WINDOW,
    DOMAIN,
    SERVICE_COMPARE,
    SUBENTRY_COMPARISON,
)

from .conftest import (
    BASE_CONTRACT,
    MANUAL_CONTRACT,
    TEMPO_CONTRACT,
    Sources,
    comparison_subentry,
    contract_subentry,
    make_entry,
)

PREFIX = "electricity_contracts:linky_00000000000000"
FIRST_HOUR = datetime(2026, 3, 1, tzinfo=UTC)
END = datetime(2026, 3, 3, tzinfo=UTC)  # after the last of the 48 hours


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> MockConfigEntry:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)
    return entry


async def change(
    hass: HomeAssistant, statistic_id: str, start: datetime, end: datetime
) -> float:
    result = await get_instance(hass).async_add_executor_job(
        statistic_during_period, hass, start, end, statistic_id, {"change"}, None
    )
    value: float = result["change"]
    return value


def state(hass: HomeAssistant, unique_id: str) -> Any:
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id is not None, unique_id
    found = hass.states.get(entity_id)
    assert found is not None
    return found


def comparison_id(entry: MockConfigEntry) -> str:
    return str(
        next(
            subentry.subentry_id
            for subentry in entry.subentries.values()
            if subentry.subentry_type == SUBENTRY_COMPARISON
        )
    )


@pytest.mark.parametrize(
    ("window", "today", "expected"),
    [
        pytest.param(
            WINDOW_CURRENT_YEAR,
            date(2026, 11, 7),
            (date(2026, 1, 1), date(2026, 12, 31)),
            id="year",
        ),
        pytest.param(
            WINDOW_CURRENT_MONTH,
            date(2026, 2, 7),
            (date(2026, 2, 1), date(2026, 2, 28)),
            id="month",
        ),
        pytest.param(
            WINDOW_TEMPO_SEASON,
            date(2026, 3, 7),
            (date(2025, 9, 1), date(2026, 8, 31)),
            id="season",
        ),
        pytest.param(
            WINDOW_LAST_12_MONTHS,
            date(2026, 11, 7),
            (date(2025, 11, 8), date(2026, 11, 7)),
            id="12_months",
        ),
        pytest.param(
            WINDOW_LAST_12_MONTHS,
            date(2028, 2, 29),
            (date(2027, 3, 1), date(2028, 2, 29)),
            id="leap_day",
        ),
    ],
)
def test_window_days(window: str, today: date, expected: tuple[date, date]) -> None:
    assert window_days(window, today) == expected


def test_fixed_window() -> None:
    assert window_days(
        WINDOW_FIXED, date(2026, 11, 7), date(2026, 1, 1), date(2026, 1, 31)
    ) == (
        date(2026, 1, 1),
        date(2026, 1, 31),
    )


@pytest.mark.usefixtures("statistic", "sources")
async def test_comparison_sensors(hass: HomeAssistant) -> None:
    entry = await setup_entry(
        hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT, comparison_subentry("March")])
    )
    subentry_id = comparison_id(entry)
    tempo_total = await change(hass, f"{PREFIX}_tempo001_cost", FIRST_HOUR, END)
    base_total = await change(hass, f"{PREFIX}_base0001_cost", FIRST_HOUR, END)
    actual = await change(
        hass, f"{PREFIX}_actual_cost", FIRST_HOUR, END
    ) + await change(hass, f"{PREFIX}_actual_cost_fixed", FIRST_HOUR, END)

    tempo_cost = state(hass, f"{subentry_id}_tempo001_cost")
    assert float(tempo_cost.state) == pytest.approx(tempo_total)
    assert tempo_cost.attributes["unit_of_measurement"] == "EUR"
    assert tempo_cost.attributes["energy"] == pytest.approx(24.0)
    assert tempo_cost.attributes["from"] == "2026-03-01T01:00:00+01:00"
    assert tempo_cost.attributes["to"] == "2026-03-03T01:00:00+01:00"
    assert tempo_cost.name == "March Tempo cost"
    base_price = state(hass, f"{subentry_id}_base0001_price")
    assert float(base_price.state) == pytest.approx(base_total / 24)
    assert base_price.attributes["unit_of_measurement"] == "EUR/kWh"
    best = "Tempo" if tempo_total < base_total else "Base"
    assert state(hass, f"{subentry_id}_best_contract").state == best
    saving = state(hass, f"{subentry_id}_saving")
    assert float(saving.state) == pytest.approx(
        actual - min(tempo_total, base_total), abs=0.005
    )
    # Tempo is in force: when it is also the best, the saving is exactly 0.
    if best == "Tempo":
        assert saving.state == "0.0"

    device = er.async_get(hass).async_get(tempo_cost.entity_id)
    assert device is not None
    assert device.config_subentry_id == subentry_id


@pytest.mark.usefixtures("statistic", "sources")
async def test_saving_on_the_contract_in_force(hass: HomeAssistant) -> None:
    base = contract_subentry(
        "Base", uid="base0001", kind=ContractKind.BASE, active_from="2024-01-01"
    )
    tempo = contract_subentry("Tempo", uid="tempo001", kind=ContractKind.TEMPO)
    entry = await setup_entry(
        hass, make_entry([base, tempo, comparison_subentry("March")])
    )
    subentry_id = comparison_id(entry)
    base_total = await change(hass, f"{PREFIX}_base0001_cost", FIRST_HOUR, END)
    tempo_total = await change(hass, f"{PREFIX}_tempo001_cost", FIRST_HOUR, END)
    assert tempo_total < base_total
    assert state(hass, f"{subentry_id}_best_contract").state == "Tempo"
    saving = float(state(hass, f"{subentry_id}_saving").state)
    assert saving == pytest.approx(base_total - tempo_total, abs=0.005)
    assert saving > 0


@pytest.mark.usefixtures("statistic", "sources")
async def test_no_saving_without_a_contract_in_force_at_every_hour(
    hass: HomeAssistant,
) -> None:
    # Base is in force from 2 March: 1 March costs nothing in the actual totals.
    base = contract_subentry(
        "Base", uid="base0001", kind=ContractKind.BASE, active_from="2026-03-02"
    )
    tempo = contract_subentry("Tempo", uid="tempo001", kind=ContractKind.TEMPO)
    entry = await setup_entry(
        hass, make_entry([base, tempo, comparison_subentry("March")])
    )
    subentry_id = comparison_id(entry)
    assert state(hass, f"{subentry_id}_best_contract").state != "unknown"
    assert state(hass, f"{subentry_id}_saving").state == "unknown"
    second_day: Any = await hass.services.async_call(
        DOMAIN,
        SERVICE_COMPARE,
        {
            ATTR_CONFIG_ENTRY_ID: entry.entry_id,
            "start": "2026-03-02",
            "end": "2026-03-02",
        },
        blocking=True,
        return_response=True,
    )
    assert second_day["saving"] is not None


@pytest.mark.usefixtures("statistic", "sources")
async def test_source_sensors(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    # The last full day in Paris is 2 March: from 1 March 23:00 to 2 March 23:00 UTC.
    start, end = (
        datetime(2026, 3, 1, 23, tzinfo=UTC),
        datetime(2026, 3, 2, 23, tzinfo=UTC),
    )
    day_cost = await change(hass, f"{PREFIX}_actual_cost", start, end) + await change(
        hass, f"{PREFIX}_actual_cost_fixed", start, end
    )
    last_day = state(hass, f"{entry.entry_id}_last_day_cost")
    assert float(last_day.state) == pytest.approx(day_cost)
    assert last_day.attributes["day"] == "2026-03-02"
    month_cost = await change(
        hass, f"{PREFIX}_actual_cost", FIRST_HOUR, end
    ) + await change(hass, f"{PREFIX}_actual_cost_fixed", FIRST_HOUR, end)
    month_energy = await change(hass, f"{PREFIX}_actual_energy", FIRST_HOUR, end)
    price = state(hass, f"{entry.entry_id}_month_average_price")
    assert float(price.state) == pytest.approx(month_cost / month_energy)
    assert state(hass, f"{entry.entry_id}_current_contract").state == "Tempo"
    assert (
        state(hass, f"{entry.entry_id}_last_hour").state == "2026-03-02T23:00:00+00:00"
    )


@pytest.mark.usefixtures("statistic", "sources")
async def test_source_sensors_without_contract_in_force(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    assert state(hass, f"{entry.entry_id}_last_day_cost").state == "unknown"
    assert state(hass, f"{entry.entry_id}_month_average_price").state == "unknown"
    assert state(hass, f"{entry.entry_id}_current_contract").state == "unknown"


@pytest.mark.usefixtures("statistic", "sources")
async def test_current_contract_after_it_ended(hass: HomeAssistant) -> None:
    ended = contract_subentry(
        "Tempo",
        uid="tempo001",
        kind=ContractKind.TEMPO,
        active_from="2024-01-01",
        active_to="2026-10-31",
    )
    entry = await setup_entry(hass, make_entry([ended]))
    assert state(hass, f"{entry.entry_id}_current_contract").state == "unknown"
    assert state(hass, f"{entry.entry_id}_last_day_cost").state != "unknown"


@pytest.mark.usefixtures("statistic", "sources")
async def test_window_without_data(hass: HomeAssistant) -> None:
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT, comparison_subentry("Season", WINDOW_TEMPO_SEASON)]
        ),
    )
    subentry_id = comparison_id(entry)
    cost = state(hass, f"{subentry_id}_tempo001_cost")
    assert float(cost.state) == 0
    # The season starts after the data: the window is empty, not reversed.
    assert cost.attributes["from"] == cost.attributes["to"]
    assert cost.attributes["from"] == "2026-09-01T00:00:00+02:00"
    assert state(hass, f"{subentry_id}_tempo001_price").state == "unknown"
    assert state(hass, f"{subentry_id}_best_contract").state == "unknown"
    assert state(hass, f"{subentry_id}_saving").state == "unknown"


@pytest.mark.usefixtures("statistic", "sources")
async def test_selected_contracts_and_stale_sensors(hass: HomeAssistant) -> None:
    entry = await setup_entry(
        hass,
        make_entry(
            [
                TEMPO_CONTRACT,
                BASE_CONTRACT,
                comparison_subentry("Year", WINDOW_LAST_12_MONTHS),
            ]
        ),
    )
    subentry_id = comparison_id(entry)
    registry = er.async_get(hass)
    assert registry.async_get_entity_id(
        "sensor", DOMAIN, f"{subentry_id}_base0001_cost"
    )
    subentry = entry.subentries[subentry_id]
    hass.config_entries.async_update_subentry(
        entry, subentry, data={**subentry.data, CONF_CONTRACTS: ["tempo001"]}
    )
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert not registry.async_get_entity_id(
        "sensor", DOMAIN, f"{subentry_id}_base0001_cost"
    )
    assert state(hass, f"{subentry_id}_tempo001_cost").state != "unknown"


@pytest.mark.usefixtures("statistic", "sources")
async def test_compare_action(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT]))
    response: Any = await hass.services.async_call(
        DOMAIN,
        SERVICE_COMPARE,
        {
            ATTR_CONFIG_ENTRY_ID: entry.entry_id,
            "start": "2026-03-01",
            "end": "2026-03-02",
        },
        blocking=True,
        return_response=True,
    )
    assert response is not None
    assert response["start"] == "2026-03-01T01:00:00+01:00"
    assert response["end"] == "2026-03-03T00:00:00+01:00"
    tempo = response["contracts"][0]
    assert tempo["name"] == "Tempo"
    assert tempo["kind"] == "tempo"
    assert sum(item["energy"] for item in tempo["tranches"].values()) == pytest.approx(
        23.5
    )
    assert set(tempo["tranches"]) == {
        tranche.value for tranche in Tranche if "_" in tranche
    }
    assert tempo["total_cost"] == pytest.approx(
        tempo["variable_cost"] + tempo["fixed_cost"], abs=0.01
    )
    assert response["best"] in {"Tempo", "Base"}
    assert response["actual"]["energy"] == pytest.approx(23.5)
    assert response["saving"] is not None

    only_base: Any = await hass.services.async_call(
        DOMAIN,
        SERVICE_COMPARE,
        {
            ATTR_CONFIG_ENTRY_ID: entry.entry_id,
            "start": "2026-03-01",
            "end": "2026-03-01",
            "contracts": ["Base", "Base"],
        },
        blocking=True,
        return_response=True,
    )
    assert only_base is not None
    assert [item["name"] for item in only_base["contracts"]] == ["Base"]
    assert only_base["contracts"][0]["tranches"]["base"]["energy"] == pytest.approx(
        11.5
    )


@pytest.mark.usefixtures("statistic", "sources")
async def test_compare_without_costs(hass: HomeAssistant) -> None:
    # The manual contract has no price, so it was never costed; Base isn't in force.
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT, MANUAL_CONTRACT]))
    response: Any = await hass.services.async_call(
        DOMAIN,
        SERVICE_COMPARE,
        {
            ATTR_CONFIG_ENTRY_ID: entry.entry_id,
            "start": "2026-03-01",
            "end": "2026-03-02",
        },
        blocking=True,
        return_response=True,
    )
    assert response["start"] == response["end"]
    assert [item["total_cost"] for item in response["contracts"]] == [0, 0]
    assert response["best"] is None
    assert response["actual"] is None
    assert response["saving"] is None


@pytest.mark.usefixtures("sources")
async def test_compare_before_any_data(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry())
    response: Any = await hass.services.async_call(
        DOMAIN,
        SERVICE_COMPARE,
        {
            ATTR_CONFIG_ENTRY_ID: entry.entry_id,
            "start": "2026-03-01",
            "end": "2026-03-02",
        },
        blocking=True,
        return_response=True,
    )
    assert response["contracts"] == []
    assert response["start"] == "2026-03-01T00:00:00+01:00"


@pytest.mark.parametrize(
    ("data", "key"),
    [
        pytest.param(
            {"start": "2026-03-02", "end": "2026-03-01"}, "end_before_start", id="dates"
        ),
        pytest.param(
            {"start": "2026-03-01", "end": "2026-03-02", "contracts": ["Nope"]},
            "unknown_contracts",
            id="contracts",
        ),
    ],
)
@pytest.mark.usefixtures("statistic", "sources")
async def test_compare_action_errors(
    hass: HomeAssistant, data: dict[str, Any], key: str
) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    with pytest.raises(ServiceValidationError) as caught:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_COMPARE,
            {ATTR_CONFIG_ENTRY_ID: entry.entry_id, **data},
            blocking=True,
            return_response=True,
        )
    assert caught.value.translation_key == key


@pytest.mark.usefixtures("statistic", "sources")
async def test_missing_manual_price_repair(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([MANUAL_CONTRACT]))
    issue_id = f"missing_price_{entry.entry_id}_offer001"
    issue = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.translation_key == "missing_price"
    assert issue.translation_placeholders == {
        "contract": "Offer",
        "day": "2026-03-01",
        "kva": "",
    }
    contract = next(iter(entry.subentries.values()))
    hass.config_entries.async_remove_subentry(entry, contract.subentry_id)
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None


@pytest.mark.usefixtures("statistic", "sources")
async def test_ignored_repair_stays_ignored(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([MANUAL_CONTRACT]))
    issue_id = f"missing_price_{entry.entry_id}_offer001"
    ir.async_ignore_issue(hass, DOMAIN, issue_id, ignore=True)
    await entry.runtime_data.async_refresh()
    await async_wait_recording_done(hass)
    issue = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.dismissed_version is not None


@pytest.mark.usefixtures("statistic")
async def test_missing_regulated_price_repair(
    hass: HomeAssistant, sources: Sources
) -> None:
    late = [
        PricePeriod(
            start=date(2026, 3, 2),
            end=None,
            fixed_per_year=1,
            prices={Tranche.BASE: 0.2},
        )
    ]
    sources.trv.async_price_periods.side_effect = None
    sources.trv.async_price_periods.return_value = late
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    issue = ir.async_get(hass).async_get_issue(
        DOMAIN, f"missing_price_{entry.entry_id}_base0001"
    )
    assert issue is not None
    assert issue.translation_key == "missing_price_official"
    assert issue.translation_placeholders is not None
    assert issue.translation_placeholders["kva"] == "6"
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert not ir.async_get(hass).issues


async def test_waiting_for_a_busy_recorder(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("DEBUG")
    busy = hass.loop.create_future()
    # Time is frozen in tests: let the wait end as the timeout would.
    busy.set_exception(TimeoutError())
    with patch.object(get_instance(hass), "async_get_commit_future", return_value=busy):
        await async_wait_for_recorder(hass)
    assert "still busy" in caplog.text


async def start_flow(hass: HomeAssistant, entry: MockConfigEntry) -> Any:
    return await hass.config_entries.subentries.async_init(
        (entry.entry_id, SUBENTRY_COMPARISON), context={"source": SOURCE_USER}
    )


async def test_comparison_flow(hass: HomeAssistant) -> None:
    entry = make_entry([TEMPO_CONTRACT, BASE_CONTRACT])
    entry.add_to_hass(hass)
    result = await start_flow(hass, entry)
    assert result["step_id"] == "user"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_NAME: " ", CONF_WINDOW: WINDOW_LAST_12_MONTHS}
    )
    assert result["errors"] == {CONF_NAME: "empty_name"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Year",
            CONF_WINDOW: WINDOW_LAST_12_MONTHS,
            CONF_CONTRACTS: ["tempo001"],
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_WINDOW: WINDOW_LAST_12_MONTHS,
        CONF_CONTRACTS: ["tempo001"],
        CONF_START: None,
        CONF_END: None,
    }


async def test_fixed_comparison_flow(hass: HomeAssistant) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    result = await start_flow(hass, entry)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_NAME: "Bill", CONF_WINDOW: WINDOW_FIXED}
    )
    assert result["step_id"] == "dates"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_START: "2026-08-27", CONF_END: "2025-08-26"}
    )
    assert result["errors"] == {CONF_END: "end_before_start"}
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_START: "2025-08-27", CONF_END: "2026-08-26"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_WINDOW: WINDOW_FIXED,
        CONF_CONTRACTS: [],
        CONF_START: "2025-08-27",
        CONF_END: "2026-08-26",
    }


async def test_reconfigure_comparison(hass: HomeAssistant) -> None:
    entry = make_entry([TEMPO_CONTRACT, comparison_subentry("Bill")])
    entry.add_to_hass(hass)
    subentry_id = comparison_id(entry)
    result = await entry.start_subentry_reconfigure_flow(hass, subentry_id)
    assert result["step_id"] == "reconfigure"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_NAME: "Bill", CONF_WINDOW: WINDOW_FIXED}
    )
    assert result["step_id"] == "dates"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_START: "2026-03-01", CONF_END: "2026-04-30"}
    )
    assert result["reason"] == "reconfigure_successful"
    assert entry.subentries[subentry_id].data[CONF_END] == "2026-04-30"
    result = await entry.start_subentry_reconfigure_flow(hass, subentry_id)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_NAME: "Month", CONF_WINDOW: WINDOW_CURRENT_MONTH}
    )
    assert result["reason"] == "reconfigure_successful"
    subentry = entry.subentries[subentry_id]
    assert subentry.title == "Month"
    assert subentry.data[CONF_START] is None


async def test_comparison_needs_contracts(hass: HomeAssistant) -> None:
    entry = make_entry()
    entry.add_to_hass(hass)
    result = await start_flow(hass, entry)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_contracts"
