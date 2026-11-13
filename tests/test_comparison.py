"""Tests of the compare action, the price repairs and the recorder waits."""

from datetime import UTC, date, datetime
from typing import Any
from unittest.mock import patch

import pytest
from elec_tariffs import ContractKind, PricePeriod, Tranche
from homeassistant.components.recorder.statistics import (
    async_list_statistic_ids,
    statistic_during_period,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_CONFIG_ENTRY_ID
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.recorder import get_instance
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.electricity_contracts.comparison import async_wait_for_recorder
from custom_components.electricity_contracts.const import (
    DOMAIN,
    SERVICE_COMPARE,
)

from .conftest import (
    BASE_CONTRACT,
    MANUAL_CONTRACT,
    TEMPO_CONTRACT,
    Sources,
    busy_recorder,
    contract_subentry,
    make_entry,
    price_period_subentry,
)

PREFIX = "electricity_contracts:linky_00000000000000"
FIRST_HOUR = datetime(2026, 3, 1, tzinfo=UTC)
END = datetime(2026, 3, 3, tzinfo=UTC)  # after the last of the 48 hours
# Prices of the offer from the second day: the first one has none.
LATE_PRICES = price_period_subentry("offer001", "2026-03-02")


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


async def compare(
    hass: HomeAssistant, entry: MockConfigEntry, start: str, end: str, **data: Any
) -> Any:
    return await hass.services.async_call(
        DOMAIN,
        SERVICE_COMPARE,
        {ATTR_CONFIG_ENTRY_ID: entry.entry_id, "start": start, "end": end, **data},
        blocking=True,
        return_response=True,
    )


@pytest.mark.usefixtures("statistic", "sources")
async def test_saving_on_the_contract_in_force(hass: HomeAssistant) -> None:
    base = contract_subentry(
        "Base", uid="base0001", kind=ContractKind.BASE, active_from="2024-01-01"
    )
    tempo = contract_subentry("Tempo", uid="tempo001", kind=ContractKind.TEMPO)
    entry = await setup_entry(hass, make_entry([base, tempo]))
    base_total = await change(hass, f"{PREFIX}_base0001_cost", FIRST_HOUR, END)
    tempo_total = await change(hass, f"{PREFIX}_tempo001_cost", FIRST_HOUR, END)
    assert tempo_total < base_total
    # Up to 3 March: narrowed to the last hour of data, the same 48 hours.
    response = await compare(hass, entry, "2026-03-01", "2026-03-03")
    assert response["best"] == "Tempo"
    assert response["saving"] == pytest.approx(base_total - tempo_total, abs=0.005)
    assert response["saving"] > 0


@pytest.mark.usefixtures("statistic", "sources")
async def test_saving_on_the_best_contract_is_zero(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT]))
    response = await compare(hass, entry, "2026-03-01", "2026-03-02")
    # Tempo is in force and the cheapest: equal totals give 0, not a rounding error.
    assert response["best"] == "Tempo"
    assert str(response["saving"]) == "0.0"


@pytest.mark.usefixtures("statistic", "sources")
async def test_no_saving_without_a_contract_in_force_at_every_hour(
    hass: HomeAssistant,
) -> None:
    # Base is in force from 2 March: 1 March costs nothing in the actual totals.
    base = contract_subentry(
        "Base", uid="base0001", kind=ContractKind.BASE, active_from="2026-03-02"
    )
    tempo = contract_subentry("Tempo", uid="tempo001", kind=ContractKind.TEMPO)
    entry = await setup_entry(hass, make_entry([base, tempo]))
    both_days = await compare(hass, entry, "2026-03-01", "2026-03-02")
    assert both_days["best"] is not None
    assert both_days["saving"] is None
    second_day = await compare(hass, entry, "2026-03-02", "2026-03-02")
    assert second_day["saving"] is not None


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
async def test_compare_leaves_out_contracts_without_costs(
    hass: HomeAssistant,
) -> None:
    # The manual contract has no price, so it was never costed: Base is compared
    # alone, over the hours it has, instead of over none. Base isn't in force.
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
    assert response["start"] == "2026-03-01T01:00:00+01:00"
    assert response["end"] == "2026-03-03T00:00:00+01:00"
    (base,) = response["contracts"]
    assert base["name"] == "Base"
    assert base["energy"] == 23.5
    assert response["best"] == "Base"
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
    entry = await setup_entry(hass, make_entry([MANUAL_CONTRACT, LATE_PRICES]))
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
async def test_no_repair_before_the_first_manual_price(hass: HomeAssistant) -> None:
    # Still being set up: the Contracts page shows it waiting for its prices.
    entry = await setup_entry(hass, make_entry([MANUAL_CONTRACT]))
    status = entry.runtime_data.data.costing.contracts["offer001"]
    assert status.waiting is not None
    assert status.waiting.reason == "price"
    assert not ir.async_get(hass).issues


@pytest.mark.usefixtures("statistic", "sources")
async def test_ignored_repair_stays_ignored(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([MANUAL_CONTRACT, LATE_PRICES]))
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


async def test_waiting_for_a_busy_recorder(hass: HomeAssistant) -> None:
    recorder = get_instance(hass)
    with patch.object(recorder, "async_get_commit_future", return_value=None):
        assert await async_wait_for_recorder(hass)
    with patch.object(
        recorder, "async_get_commit_future", return_value=busy_recorder(hass)
    ):
        assert not await async_wait_for_recorder(hass)


async def test_no_wait_while_home_assistant_starts(hass: HomeAssistant) -> None:
    # The recorder only commits once started: waiting would hold the startup up.
    hass.set_state(CoreState.starting)
    with patch.object(
        get_instance(hass), "async_get_commit_future", return_value=busy_recorder(hass)
    ):
        assert await async_wait_for_recorder(hass)


@pytest.mark.usefixtures("statistic", "sources")
async def test_no_clearing_while_home_assistant_starts(hass: HomeAssistant) -> None:
    # The recorder would only clear once started: the update fails instead of
    # holding the startup up, and the next one writes everything again.
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    coordinator = entry.runtime_data
    hass.set_state(CoreState.starting)
    await coordinator.async_recompute()
    assert not coordinator.last_update_success
    assert coordinator.last_exception is not None
    assert coordinator.last_exception.translation_key == "recorder_starting"

    hass.set_state(CoreState.running)
    await coordinator.async_refresh()
    await async_wait_recording_done(hass)
    assert coordinator.last_update_success
    response = await compare(hass, entry, "2026-03-01", "2026-03-03")
    assert response["contracts"][0]["energy"] > 0


@pytest.mark.parametrize(
    ("idle_waits", "written"),
    [
        # Nothing is queued while earlier imports may still be pending.
        pytest.param(0, False, id="before_costing"),
        # The totals aren't read before the new rows are written.
        pytest.param(1, True, id="after_costing"),
    ],
)
@pytest.mark.usefixtures("statistic", "sources")
async def test_setup_retries_while_the_recorder_is_busy(
    hass: HomeAssistant, idle_waits: int, written: bool
) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    futures = iter([None] * idle_waits)
    busy = busy_recorder(hass)
    with patch.object(
        get_instance(hass),
        "async_get_commit_future",
        side_effect=lambda: next(futures, busy),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
    await async_wait_recording_done(hass)
    ids = await async_list_statistic_ids(hass)
    assert any(item["source"] == DOMAIN for item in ids) is written
