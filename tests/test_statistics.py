"""Tests of the cost statistics."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from elec_tariffs import (
    TRANCHES,
    ContractKind,
    ContractRules,
    TempoColor,
    Tranche,
    cost_hour,
)
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_metadata,
    statistics_during_period,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_CONFIG_ENTRY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.recorder import get_instance
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.electricity_contracts.const import (
    CONF_FIXED_PER_YEAR,
    CONF_PRICES,
    CONF_STATISTIC_ID,
    DOMAIN,
    FRANCE_TIME_ZONE,
    SERVICE_RECOMPUTE,
)
from custom_components.electricity_contracts.coordinator import (
    ElectricityContractsCoordinator,
)
from custom_components.electricity_contracts.statistics import (
    _TRANCHE_NAMES,
    StatisticsWriter,
)

from .conftest import (
    BASE_CONTRACT,
    BASE_PERIODS,
    FIRST_HOUR,
    MANUAL_CONTRACT,
    OTHER_STATISTIC_ID,
    TEMPO_CONTRACT,
    TEMPO_PERIODS,
    Sources,
    add_statistic,
    color_of,
    contract_subentry,
    make_entry,
    price_period_subentry,
    published_calendar,
)

pytestmark = pytest.mark.usefixtures("statistic", "sources")

PREFIX = "electricity_contracts:linky_00000000000000"
TEMPO = f"{PREFIX}_tempo001"
BASE = f"{PREFIX}_base0001"
OFFER = f"{PREFIX}_offer001"
ACTUAL = f"{PREFIX}_actual_cost"
HOURS = [FIRST_HOUR + timedelta(hours=hour) for hour in range(48)]
TEMPO_RULES = ContractRules(kind=ContractKind.TEMPO)


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry) -> MockConfigEntry:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await settle(hass)
    return entry


async def settle(hass: HomeAssistant) -> None:
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)


async def refresh(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    coordinator: ElectricityContractsCoordinator = entry.runtime_data
    await coordinator.async_refresh()
    await settle(hass)


async def rows(hass: HomeAssistant, *ids: str) -> dict[str, list[Any]]:
    await async_wait_recording_done(hass)
    result: dict[str, list[Any]] = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        datetime(2000, 1, 1, tzinfo=UTC),
        None,
        set(ids),
        "hour",
        None,
        {"sum", "state"},
    )
    return result


async def last_sum(hass: HomeAssistant, statistic_id: str) -> float:
    found = (await rows(hass, statistic_id))[statistic_id]
    value: float = found[-1]["sum"]
    return value


def expected_tempo(hours: list[datetime]) -> dict[str, float]:
    calendar = {
        day: color_of(day)
        for day in (date(2026, 2, 28), date(2026, 3, 1), date(2026, 3, 2))
    }
    totals = {"energy": 0.0, "variable": 0.0, "fixed": 0.0}
    by_tranche = dict.fromkeys(TRANCHES[ContractKind.TEMPO], 0.0)
    for start in hours:
        cost = cost_hour(
            start.astimezone(FRANCE_TIME_ZONE),
            0.5,
            TEMPO_RULES,
            TEMPO_PERIODS,
            calendar,
        )
        totals["energy"] += sum(cost.energy.values())
        totals["variable"] += sum(cost.variable.values())
        totals["fixed"] += cost.fixed
        for tranche, value in cost.variable.items():
            by_tranche[tranche] += value
    return totals | {f"cost_{tranche}": value for tranche, value in by_tranche.items()}


async def test_contract_statistics(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT]))
    expected = expected_tempo(HOURS)
    found = await rows(
        hass, f"{TEMPO}_cost", f"{TEMPO}_cost_fixed", f"{BASE}_energy_base"
    )
    total = found[f"{TEMPO}_cost"]
    assert [row["start"] for row in total] == [hour.timestamp() for hour in HOURS]
    assert total[-1]["sum"] == pytest.approx(expected["variable"] + expected["fixed"])
    assert found[f"{TEMPO}_cost_fixed"][-1]["sum"] == pytest.approx(expected["fixed"])
    assert found[f"{BASE}_energy_base"][-1]["sum"] == pytest.approx(24.0)
    for tranche in TRANCHES[ContractKind.TEMPO]:
        assert await last_sum(hass, f"{TEMPO}_cost_{tranche}") == pytest.approx(
            expected[f"cost_{tranche}"]
        )
    energy = [
        await last_sum(hass, f"{TEMPO}_energy_{tranche}")
        for tranche in TRANCHES[ContractKind.TEMPO]
    ]
    assert sum(energy) == pytest.approx(24.0)
    # Only Tempo is in force: the actual cost is its variable cost.
    assert await last_sum(hass, ACTUAL) == pytest.approx(expected["variable"])
    assert await last_sum(hass, f"{ACTUAL}_fixed") == pytest.approx(expected["fixed"])

    status = entry.runtime_data.data.costing
    assert status.contracts["tempo001"].last_hour == HOURS[-1]
    assert status.contracts["tempo001"].waiting is None
    assert status.actual is not None
    assert status.actual.last_hour == HOURS[-1]
    assert status.last_source_hour == HOURS[-1]


async def test_statistic_metadata(hass: HomeAssistant) -> None:
    await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    ids = {f"{TEMPO}_energy_blue_hp", f"{TEMPO}_cost_red_hp", f"{TEMPO}_cost", ACTUAL}
    metadata = await get_instance(hass).async_add_executor_job(
        lambda: get_metadata(hass, statistic_ids=ids)
    )
    energy = metadata[f"{TEMPO}_energy_blue_hp"][1]
    assert energy["name"] == "Tempo energy blue peak"
    assert energy["unit_of_measurement"] == "kWh"
    assert energy["unit_class"] == "energy"
    assert energy["source"] == DOMAIN
    assert energy["has_sum"]
    cost = metadata[f"{TEMPO}_cost_red_hp"][1]
    assert cost["name"] == "Tempo cost red peak"
    assert cost["unit_of_measurement"] == "EUR"
    assert cost["unit_class"] is None
    assert metadata[f"{TEMPO}_cost"][1]["name"] == "Tempo total cost"
    assert metadata[ACTUAL][1]["name"] == "Actual cost"


async def test_french_names(hass: HomeAssistant) -> None:
    hass.config.language = "fr"
    await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    metadata = await get_instance(hass).async_add_executor_job(
        lambda: get_metadata(
            hass, statistic_ids={f"{TEMPO}_energy_white_hc", f"{TEMPO}_cost_fixed"}
        )
    )
    assert metadata[f"{TEMPO}_energy_white_hc"][1]["name"] == "Tempo énergie Blanc HC"
    assert metadata[f"{TEMPO}_cost_fixed"][1]["name"] == "Tempo abonnement"


async def test_new_hours_are_appended(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    first = (await rows(hass, f"{BASE}_cost"))[f"{BASE}_cost"]
    await add_statistic(hass, first=48, hours=24)
    await refresh(hass, entry)
    found = await rows(hass, f"{BASE}_energy_base", f"{BASE}_cost")
    assert len(found[f"{BASE}_cost"]) == 72
    assert found[f"{BASE}_cost"][:48] == first
    assert found[f"{BASE}_energy_base"][-1]["sum"] == pytest.approx(36.0)
    # Base has no activity period: no actual cost.
    assert not (await rows(hass, ACTUAL))


async def test_waiting_for_a_tempo_color(
    hass: HomeAssistant, sources: Sources, freezer: FrozenDateTimeFactory
) -> None:
    # Colors are only known until the Tempo day of 1 March 2026.
    sources.public.async_calendar.side_effect = published_calendar(date(2026, 3, 1))
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT]))
    status = entry.runtime_data.data.costing
    # The 2 March Tempo day starts at 6:00 in Paris, 5:00 UTC.
    stop = datetime(2026, 3, 2, 4, tzinfo=UTC)
    assert status.contracts["tempo001"].last_hour == stop
    waiting = status.contracts["tempo001"].waiting
    assert waiting is not None
    assert (waiting.reason, waiting.day) == ("color", date(2026, 3, 2))
    assert status.contracts["base0001"].last_hour == HOURS[-1]
    assert status.actual is not None
    assert status.actual.last_hour == stop
    assert (await rows(hass, f"{TEMPO}_cost"))[f"{TEMPO}_cost"][-1]["start"] == (
        stop.timestamp()
    )

    sources.public.async_calendar.side_effect = published_calendar(date(2026, 11, 7))
    freezer.tick(timedelta(hours=6))
    await refresh(hass, entry)
    status = entry.runtime_data.data.costing
    assert status.contracts["tempo001"].last_hour == HOURS[-1]
    assert await last_sum(hass, ACTUAL) == pytest.approx(
        expected_tempo(HOURS)["variable"]
    )
    assert len((await rows(hass, f"{BASE}_cost"))[f"{BASE}_cost"]) == 48


async def test_actual_cost_follows_the_contracts_in_force(hass: HomeAssistant) -> None:
    base = contract_subentry(
        "Base",
        uid="base0001",
        kind=ContractKind.BASE,
        active_from="2026-02-01",
        active_to="2026-03-01",
    )
    tempo = contract_subentry(
        "Tempo", uid="tempo001", kind=ContractKind.TEMPO, active_from="2026-03-02"
    )
    await setup_entry(hass, make_entry([base, tempo]))
    # 1 March in Paris ends at 23:00 UTC.
    on_base = [hour for hour in HOURS if hour < datetime(2026, 3, 1, 23, tzinfo=UTC)]
    on_tempo = [hour for hour in HOURS if hour not in on_base]
    expected = expected_tempo(on_tempo)["variable"] + len(on_base) * 0.5 * 0.1952
    assert await last_sum(hass, ACTUAL) == pytest.approx(expected)


async def test_no_actual_cost_before_the_first_contract(hass: HomeAssistant) -> None:
    base = contract_subentry(
        "Base", uid="base0001", kind=ContractKind.BASE, active_from="2026-03-02"
    )
    await setup_entry(hass, make_entry([base]))
    found = (await rows(hass, ACTUAL))[ACTUAL]
    on_base = [hour for hour in HOURS if hour >= datetime(2026, 3, 1, 23, tzinfo=UTC)]
    assert len(found) == 48
    assert found[22]["sum"] == 0
    assert found[-1]["sum"] == pytest.approx(len(on_base) * 0.5 * 0.1952)


async def test_deleted_source_clears_everything(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    get_instance(hass).async_clear_statistics(["linky:00000000000000"])
    await settle(hass)
    await refresh(hass, entry)
    assert not await rows(hass, f"{BASE}_cost")
    assert entry.runtime_data.data.costing.contracts["base0001"].last_hour is None


async def test_removing_an_entry_without_statistics(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry())
    await hass.config_entries.async_remove(entry.entry_id)
    await settle(hass)


async def test_daily_rows_are_not_costed(hass: HomeAssistant) -> None:
    source = "linky:22222222222222"
    first_hour = datetime(2026, 3, 22, tzinfo=FRANCE_TIME_ZONE).astimezone(UTC)
    starts = [first_hour - timedelta(days=days) for days in (3, 2, 1)]
    starts += [first_hour + timedelta(hours=hour) for hour in range(24)]
    values = [12000.0] * 3 + [500.0] * 24
    sums = [sum(values[: index + 1]) for index in range(len(values))]
    async_add_external_statistics(
        hass,
        {
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "name": "Linky",
            "source": "linky",
            "statistic_id": source,
            "unit_class": "energy",
            "unit_of_measurement": "Wh",
        },
        [
            StatisticData(start=start, state=value, sum=total)
            for start, value, total in zip(starts, values, sums, strict=True)
        ],
    )
    await settle(hass)
    await setup_entry(hass, make_entry([BASE_CONTRACT], statistic_id=source))
    energy = "electricity_contracts:linky_22222222222222_base0001_energy_base"
    found = (await rows(hass, energy))[energy]
    assert found[0]["start"] == first_hour.timestamp()
    assert len(found) == 24
    assert found[-1]["sum"] == pytest.approx(12.0)


async def test_manual_price_change_rewrites_the_contract(hass: HomeAssistant) -> None:
    entry = await setup_entry(
        hass,
        make_entry([MANUAL_CONTRACT, price_period_subentry("offer001", "2026-01-01")]),
    )
    assert await last_sum(hass, f"{OFFER}_cost_base") == pytest.approx(24 * 0.19)
    period = next(
        subentry
        for subentry in entry.subentries.values()
        if subentry.subentry_type == "price_period"
    )
    hass.config_entries.async_update_subentry(
        entry,
        period,
        data={**period.data, CONF_PRICES: {"base": 0.25}, CONF_FIXED_PER_YEAR: 0.0},
    )
    await settle(hass)
    assert entry.state is ConfigEntryState.LOADED
    found = await rows(hass, f"{OFFER}_cost_base", f"{OFFER}_cost_fixed")
    assert len(found[f"{OFFER}_cost_base"]) == 48
    assert found[f"{OFFER}_cost_base"][-1]["sum"] == pytest.approx(24 * 0.25)
    assert found[f"{OFFER}_cost_fixed"][-1]["sum"] == 0


async def test_manual_contract_without_prices_waits(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([MANUAL_CONTRACT]))
    waiting = entry.runtime_data.data.costing.contracts["offer001"].waiting
    assert waiting is not None
    assert (waiting.reason, waiting.day) == ("price", date(2026, 3, 1))
    assert not await rows(hass, f"{OFFER}_cost")


async def test_removed_contract_is_cleared(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT]))
    assert await rows(hass, f"{BASE}_cost")
    base = next(
        subentry for subentry in entry.subentries.values() if subentry.title == "Base"
    )
    hass.config_entries.async_remove_subentry(entry, base.subentry_id)
    await settle(hass)
    assert not await rows(hass, f"{BASE}_cost", f"{BASE}_energy_base")
    assert await rows(hass, f"{TEMPO}_cost")


async def test_rewritten_source_rewrites_everything(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    # The Linky app imported the history again, with other values.
    await add_statistic(hass, wh=1000.0)
    await refresh(hass, entry)
    found = (await rows(hass, f"{BASE}_energy_base"))[f"{BASE}_energy_base"]
    assert len(found) == 48
    assert found[-1]["sum"] == pytest.approx(48.0)


async def test_inconsistent_series_is_rewritten(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    get_instance(hass).async_clear_statistics([f"{BASE}_cost_fixed"])
    await settle(hass)
    await refresh(hass, entry)
    found = await rows(hass, f"{BASE}_cost_fixed", f"{BASE}_energy_base")
    assert len(found[f"{BASE}_cost_fixed"]) == 48
    assert found[f"{BASE}_energy_base"][-1]["sum"] == pytest.approx(24.0)


async def test_series_without_its_last_statistic(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    get_instance(hass).async_clear_statistics([f"{BASE}_cost"])
    await settle(hass)
    await refresh(hass, entry)
    found = await rows(hass, f"{BASE}_cost", f"{BASE}_energy_base")
    assert len(found[f"{BASE}_cost"]) == 48
    assert found[f"{BASE}_energy_base"][-1]["sum"] == pytest.approx(24.0)


async def test_recompute_action(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    # Damage the last row; recomputing writes it again from the first hour.
    async_add_external_statistics(
        hass,
        {
            "mean_type": StatisticMeanType.NONE,
            "has_sum": True,
            "name": "Base total cost",
            "source": DOMAIN,
            "statistic_id": f"{BASE}_cost",
            "unit_class": None,
            "unit_of_measurement": "EUR",
        },
        [StatisticData(start=HOURS[-1], state=0.0, sum=-1.0)],
    )
    await settle(hass)
    assert await last_sum(hass, f"{BASE}_cost") == -1.0
    await hass.services.async_call(
        DOMAIN,
        SERVICE_RECOMPUTE,
        {ATTR_CONFIG_ENTRY_ID: entry.entry_id},
        blocking=True,
    )
    await settle(hass)
    assert await last_sum(hass, f"{BASE}_cost") > 0


async def test_recompute_action_errors(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    with pytest.raises(ServiceValidationError) as unknown:
        await hass.services.async_call(
            DOMAIN, SERVICE_RECOMPUTE, {ATTR_CONFIG_ENTRY_ID: "nope"}, blocking=True
        )
    assert unknown.value.translation_key == "entry_not_found"
    assert await hass.config_entries.async_unload(entry.entry_id)
    with pytest.raises(ServiceValidationError) as not_loaded:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RECOMPUTE,
            {ATTR_CONFIG_ENTRY_ID: entry.entry_id},
            blocking=True,
        )
    assert not_loaded.value.translation_key == "entry_not_loaded"


async def test_new_source_rewrites_everything(hass: HomeAssistant) -> None:
    await add_statistic(hass, OTHER_STATISTIC_ID, hours=24)
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    hass.config_entries.async_update_entry(
        entry,
        unique_id=OTHER_STATISTIC_ID,
        data={CONF_STATISTIC_ID: OTHER_STATISTIC_ID},
    )
    await settle(hass)
    assert entry.state is ConfigEntryState.LOADED
    assert not await rows(hass, f"{BASE}_cost")
    other = "electricity_contracts:linky_11111111111111_base0001_energy_base"
    assert await last_sum(hass, other) == pytest.approx(12.0)


async def test_removing_the_entry_clears_its_statistics(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    assert await rows(hass, f"{TEMPO}_cost", ACTUAL)
    await hass.config_entries.async_remove(entry.entry_id)
    await settle(hass)
    assert not await rows(hass, f"{TEMPO}_cost", ACTUAL)


async def test_without_contracts_nothing_is_written(hass: HomeAssistant) -> None:
    entry = await setup_entry(hass, make_entry())
    assert entry.runtime_data.data.costing.contracts == {}


async def test_unreadable_record_is_ignored(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
) -> None:
    entry = make_entry([BASE_CONTRACT])
    hass_storage[f"{DOMAIN}.{entry.entry_id}.statistics"] = {
        "version": 1,
        "key": f"{DOMAIN}.{entry.entry_id}.statistics",
        "data": {"series": "broken"},
    }
    await setup_entry(hass, entry)
    assert "unreadable record" in caplog.text
    assert await last_sum(hass, f"{BASE}_energy_base") == pytest.approx(24.0)


async def test_deleted_source_writes_nothing(hass: HomeAssistant) -> None:
    entry = make_entry([BASE_CONTRACT])
    entry.add_to_hass(hass)
    writer = StatisticsWriter(hass, entry)
    writer.source_id = "linky:deleted"
    await writer.async_load()
    status = await writer.async_update(
        {(ContractKind.BASE, 6): BASE_PERIODS}, {date(2026, 3, 1): TempoColor.BLUE}
    )
    assert status.contracts["base0001"].last_hour is None
    assert status.last_source_hour is None


def test_tranche_names_cover_every_tranche() -> None:
    for names in _TRANCHE_NAMES.values():
        assert set(names) == set(Tranche)
