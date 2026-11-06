"""Tests of when the prices and Tempo colors are downloaded."""

from datetime import date, datetime, timedelta
from typing import Any

import pytest
from elec_tariffs import TempoAuthError, TempoColor, TempoFormatError
from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.electricity_contracts.const import (
    CONF_RTE_CLIENT_ID,
    CONF_RTE_CLIENT_SECRET,
    DOMAIN,
    TEMPO_TIME_ZONE,
)
from custom_components.electricity_contracts.coordinator import (
    ElectricityContractsCoordinator,
)

from .conftest import (
    BASE_CONTRACT,
    NOW,
    TEMPO_CONTRACT,
    Sources,
    add_statistic,
    color_of,
    make_entry,
    published_calendar,
)

pytestmark = pytest.mark.usefixtures("statistic")

TODAY = date(2026, 11, 7)
TOMORROW = date(2026, 11, 8)


async def setup_entry(
    hass: HomeAssistant, entry: MockConfigEntry | None = None
) -> MockConfigEntry:
    entry = entry or make_entry([TEMPO_CONTRACT])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def coordinator(entry: MockConfigEntry) -> ElectricityContractsCoordinator:
    result: ElectricityContractsCoordinator = entry.runtime_data
    return result


def calls(sources: Sources) -> list[tuple[date, date]]:
    return [call.args for call in sources.public.async_calendar.await_args_list]


def at_paris(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=TEMPO_TIME_ZONE)


async def test_first_setup_downloads_the_seasons_since_the_first_day(
    hass: HomeAssistant, sources: Sources, hass_storage: dict[str, Any]
) -> None:
    entry = await setup_entry(hass)
    # Consumption starts on 1 March 2026; it is 10:00 in Paris, before tomorrow's
    # color is published.
    assert calls(sources) == [
        (date(2026, 3, 1), date(2026, 8, 31)),
        (date(2026, 9, 1), TOMORROW),
    ]
    data = coordinator(entry).data
    assert data.first_day == date(2026, 3, 1)
    assert min(data.calendar) == date(2026, 3, 1)
    assert max(data.calendar) == TODAY
    assert data.calendar[date(2026, 3, 4)] is color_of(date(2026, 3, 4))
    stored = hass_storage[f"{DOMAIN}.{entry.entry_id}"]["data"]
    assert stored["calendar"]["2026-11-07"] == color_of(TODAY).value
    assert set(stored["season_checked"]) == {"2025-2026", "2026-2027"}


async def test_restart_uses_the_cache(hass: HomeAssistant, sources: Sources) -> None:
    entry = await setup_entry(hass)
    sources.public.async_calendar.reset_mock()
    assert await hass.config_entries.async_reload(entry.entry_id)
    assert calls(sources) == []
    assert max(coordinator(entry).data.calendar) == TODAY


async def test_tomorrow_is_asked_after_publication(
    hass: HomeAssistant, sources: Sources, freezer: FrozenDateTimeFactory
) -> None:
    entry = await setup_entry(hass)
    sources.public.async_calendar.reset_mock()
    published = at_paris(TODAY, 11) + coordinator(entry)._tomorrow_delay

    freezer.move_to(published - timedelta(minutes=1))
    await coordinator(entry).async_refresh()
    assert calls(sources) == []

    # Not published yet: asked once, then again after a while.
    freezer.move_to(published)
    await coordinator(entry).async_refresh()
    assert calls(sources) == [(TODAY, TOMORROW)]
    freezer.tick(timedelta(minutes=30))
    await coordinator(entry).async_refresh()
    assert len(calls(sources)) == 1

    sources.public.async_calendar.side_effect = published_calendar(TOMORROW)
    freezer.tick(timedelta(minutes=30))
    await coordinator(entry).async_refresh()
    assert len(calls(sources)) == 2
    assert coordinator(entry).data.calendar[TOMORROW] is color_of(TOMORROW)

    # Once known, neither tomorrow nor, after midnight, today is asked again.
    freezer.move_to(at_paris(TOMORROW, 1))
    await coordinator(entry).async_refresh()
    assert len(calls(sources)) == 2


async def test_hourly_schedule(
    hass: HomeAssistant, sources: Sources, freezer: FrozenDateTimeFactory
) -> None:
    await setup_entry(hass)
    sources.public.async_calendar.side_effect = published_calendar(TOMORROW)
    for _ in range(3):
        freezer.tick(timedelta(hours=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
    # 13:00 in Paris: tomorrow's color has been fetched by the hourly update.
    assert calls(sources)[-1] == (TODAY, TOMORROW)


async def test_missing_days_of_the_current_season(
    hass: HomeAssistant,
    sources: Sources,
    hass_storage: dict[str, Any],
    freezer: FrozenDateTimeFactory,
) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    calendar = published_calendar(date(2026, 11, 1))
    hass_storage[f"{DOMAIN}.{entry.entry_id}"] = {
        "version": 1,
        "key": f"{DOMAIN}.{entry.entry_id}",
        "data": {
            "calendar": {
                day.isoformat(): color.value
                for day, color in calendar(date(2026, 3, 1), date(2026, 11, 1)).items()
            },
            "season_checked": {
                "2025-2026": "2026-09-02T00:00:00+00:00",
                "2026-2027": "2026-11-01T08:00:00+00:00",
            },
            "tomorrow_checked": None,
            "prices": {},
            "prices_fetched": {},
            "failing_since": {},
        },
    }
    # RTE didn't publish the last days either.
    sources.public.async_calendar.side_effect = calendar
    await setup_entry(hass, entry)
    assert calls(sources) == [(date(2026, 9, 1), TOMORROW)]

    # Asked again only after a few hours.
    sources.public.async_calendar.side_effect = published_calendar(TODAY)
    season_calls = [(date(2026, 9, 1), TOMORROW)]
    freezer.tick(timedelta(hours=5))
    await coordinator(entry).async_refresh()
    assert [call for call in calls(sources) if call[0] != TODAY] == season_calls
    freezer.tick(timedelta(hours=1))
    await coordinator(entry).async_refresh()
    assert [call for call in calls(sources) if call[0] != TODAY] == season_calls * 2
    assert max(coordinator(entry).data.calendar) == TODAY


async def test_past_season_checked_after_its_end_is_not_asked_again(
    hass: HomeAssistant, sources: Sources, hass_storage: dict[str, Any]
) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    calendar = published_calendar(TODAY)(date(2026, 3, 1), TODAY)
    del calendar[date(2026, 4, 1)]
    hass_storage[f"{DOMAIN}.{entry.entry_id}"] = {
        "version": 1,
        "key": f"{DOMAIN}.{entry.entry_id}",
        "data": {
            "calendar": {day.isoformat(): c.value for day, c in calendar.items()},
            "season_checked": {"2025-2026": "2026-09-02T00:00:00+00:00"},
            "tomorrow_checked": None,
            "prices": {},
            "prices_fetched": {},
            "failing_since": {},
        },
    }
    await setup_entry(hass, entry)
    assert calls(sources) == []


async def test_unreadable_cache_is_ignored(
    hass: HomeAssistant,
    sources: Sources,
    hass_storage: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
) -> None:
    entry = make_entry([TEMPO_CONTRACT])
    hass_storage[f"{DOMAIN}.{entry.entry_id}"] = {
        "version": 1,
        "key": f"{DOMAIN}.{entry.entry_id}",
        "data": {"calendar": {"yesterday": "purple"}},
    }
    await setup_entry(hass, entry)
    assert "unreadable cache" in caplog.text
    assert len(calls(sources)) == 2


async def test_prices_are_refreshed_daily(
    hass: HomeAssistant, sources: Sources, freezer: FrozenDateTimeFactory
) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT]))
    assert sources.trv.async_price_periods.await_count == 2
    data = coordinator(entry).data
    assert set(data.official_prices) == {("tempo", 6), ("base", 6)}
    freezer.tick(timedelta(hours=23))
    await coordinator(entry).async_refresh()
    assert sources.trv.async_price_periods.await_count == 2
    freezer.tick(timedelta(hours=1))
    await coordinator(entry).async_refresh()
    assert sources.trv.async_price_periods.await_count == 4


def issue(
    hass: HomeAssistant, name: str, entry: MockConfigEntry
) -> ir.IssueEntry | None:
    return ir.async_get(hass).async_get_issue(DOMAIN, f"{name}_{entry.entry_id}")


async def test_prices_down_for_two_days(
    hass: HomeAssistant, sources: Sources, freezer: FrozenDateTimeFactory
) -> None:
    entry = await setup_entry(hass)
    sources.fail_prices()
    freezer.tick(timedelta(hours=24))
    await coordinator(entry).async_refresh()
    # The prices already known are kept.
    assert coordinator(entry).last_update_success
    assert coordinator(entry).last_errors == {"prices": "down"}
    assert issue(hass, "prices_unavailable", entry) is None

    freezer.tick(timedelta(hours=48))
    await coordinator(entry).async_refresh()
    found = issue(hass, "prices_unavailable", entry)
    assert found is not None
    assert found.translation_placeholders is not None
    assert found.translation_placeholders["error"] == "down"

    sources.trv.async_price_periods.side_effect = Sources._prices
    freezer.tick(timedelta(hours=1))
    await coordinator(entry).async_refresh()
    assert issue(hass, "prices_unavailable", entry) is None
    assert coordinator(entry).last_errors == {}


async def test_tempo_down_for_two_days(
    hass: HomeAssistant, sources: Sources, freezer: FrozenDateTimeFactory
) -> None:
    entry = await setup_entry(hass)
    sources.fail_public(TempoFormatError("changed"))
    freezer.tick(timedelta(days=2))
    await coordinator(entry).async_refresh()
    freezer.tick(timedelta(hours=1))
    await coordinator(entry).async_refresh()
    assert coordinator(entry).last_update_success
    assert issue(hass, "tempo_unavailable", entry) is None
    freezer.tick(timedelta(days=2))
    await coordinator(entry).async_refresh()
    found = issue(hass, "tempo_unavailable", entry)
    assert found is not None
    assert found.translation_key == "tempo_unavailable"
    assert found.severity is ir.IssueSeverity.WARNING


async def test_refused_credentials(
    hass: HomeAssistant, sources: Sources, freezer: FrozenDateTimeFactory
) -> None:
    entry = await setup_entry(
        hass,
        make_entry(
            [TEMPO_CONTRACT],
            options={CONF_RTE_CLIENT_ID: "my-id", CONF_RTE_CLIENT_SECRET: "old"},
        ),
    )
    assert issue(hass, "rte_credentials_refused", entry) is None
    sources.fail_public()
    sources.official.async_calendar.side_effect = TempoAuthError("refused")
    freezer.tick(timedelta(days=1))
    await coordinator(entry).async_refresh()
    refused = issue(hass, "rte_credentials_refused", entry)
    assert refused is not None
    assert refused.severity is ir.IssueSeverity.ERROR

    freezer.tick(timedelta(days=2))
    await coordinator(entry).async_refresh()
    found = issue(hass, "tempo_unavailable", entry)
    assert found is not None
    assert found.translation_key == "tempo_unavailable_official"

    sources.official.async_calendar.side_effect = published_calendar(date(2026, 11, 11))
    freezer.tick(timedelta(hours=1))
    await coordinator(entry).async_refresh()
    assert issue(hass, "rte_credentials_refused", entry) is None
    assert issue(hass, "tempo_unavailable", entry) is None
    assert coordinator(entry).data.calendar[date(2026, 11, 10)] is TempoColor(
        color_of(date(2026, 11, 10))
    )


async def test_statistic_without_rows(hass: HomeAssistant, sources: Sources) -> None:
    await add_statistic(hass, "linky:empty", hours=0)
    entry = await setup_entry(
        hass, make_entry([TEMPO_CONTRACT], statistic_id="linky:empty")
    )
    assert entry.state is ConfigEntryState.LOADED
    assert coordinator(entry).data.first_day == TODAY
    assert calls(sources) == [(TODAY, TOMORROW)]


async def test_now_is_frozen() -> None:
    assert datetime.now(tz=NOW.tzinfo) == NOW
