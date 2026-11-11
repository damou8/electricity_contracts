"""Tests of the commands behind the Contracts page, and of the page itself."""

from datetime import date, timedelta
from typing import Any

import pytest
from elec_tariffs import ContractKind, PricePeriod, TempoColor, Tranche
from homeassistant.components import frontend
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)
from pytest_homeassistant_custom_component.typing import (
    ClientSessionGenerator,
    WebSocketGenerator,
)

from custom_components.electricity_contracts.const import DOMAIN
from custom_components.electricity_contracts.panel import PANEL_URL_PATH

from .conftest import (
    BASE_CONTRACT,
    BASE_PERIODS,
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
from .test_comparison import compare, setup_entry


def prices(period: PricePeriod) -> dict[str, Any]:
    return {
        "start": period.start.isoformat(),
        "end": period.end.isoformat() if period.end else None,
        "fixed_per_year": period.fixed_per_year,
        "tranches": {tranche.value: price for tranche, price in period.prices.items()},
    }


async def command(
    hass_ws_client: WebSocketGenerator, hass: HomeAssistant, **message: Any
) -> dict[str, Any]:
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(message)
    response: dict[str, Any] = await client.receive_json()
    return response


async def result(
    hass_ws_client: WebSocketGenerator, hass: HomeAssistant, **message: Any
) -> Any:
    response = await command(hass_ws_client, hass, **message)
    assert response["success"], response
    return response["result"]


@pytest.mark.usefixtures("statistic", "sources")
async def test_entries(hass: HomeAssistant, hass_ws_client: WebSocketGenerator) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT]))
    entries = await result(hass_ws_client, hass, type=f"{DOMAIN}/entries")
    assert entries == [
        {
            "entry_id": entry.entry_id,
            "title": entry.title,
            "first_day": "2026-03-01",
            # The last of the 48 hours is midnight, French time.
            "last_day": "2026-03-03",
            "contracts": [
                {
                    "id": "tempo001",
                    "name": "Tempo",
                    "kind": "tempo",
                    "official": True,
                    "kva": 6,
                    "off_peak": [],
                    "weekend_off_peak": False,
                    "active_from": "2024-01-01",
                    "active_to": None,
                    "prices": [prices(period) for period in TEMPO_PERIODS],
                },
                {
                    "id": "base0001",
                    "name": "Base",
                    "kind": "base",
                    "official": True,
                    "kva": 6,
                    "off_peak": [],
                    "weekend_off_peak": False,
                    "active_from": None,
                    "active_to": None,
                    "prices": [prices(period) for period in BASE_PERIODS],
                },
            ],
            "actual": True,
        }
    ]


@pytest.mark.usefixtures("sources")
async def test_entries_before_any_data(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    offer = contract_subentry(
        "Offer", uid="offer001", kind=ContractKind.BASE, pricing="manual"
    )
    await setup_entry(hass, make_entry([BASE_CONTRACT, offer]))
    [entry] = await result(hass_ws_client, hass, type=f"{DOMAIN}/entries")
    # No price was entered for the offer.
    assert entry["contracts"][1]["official"] is False
    assert entry["contracts"][1]["prices"] == []
    assert entry["first_day"] is None
    assert entry["last_day"] is None
    assert entry["actual"] is False


@pytest.mark.usefixtures("statistic", "sources")
async def test_compare_by_day(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT]))
    response = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/compare",
        entry_id=entry.entry_id,
        start="2026-03-01",
        end="2026-03-31",
    )
    # The same totals as the compare action.
    action = await compare(hass, entry, "2026-03-01", "2026-03-31")
    assert {key: value for key, value in response.items() if key in action} == action
    assert response["group_by"] == "day"
    series = response["series"]
    assert [bucket["start"] for bucket in series] == [
        "2026-03-01",
        "2026-03-02",
        "2026-03-03",
    ]
    # 23, 24 and 1 hours of 0.5 kWh, French time.
    assert [bucket["energy"] for bucket in series] == [11.5, 12.0, 0.5]
    for contract in response["contracts"]:
        assert sum(
            bucket["contracts"][contract["id"]] for bucket in series
        ) == pytest.approx(contract["total_cost"], abs=0.02)
    # Tempo is in force at every hour.
    for bucket in series:
        assert bucket["actual"] == bucket["contracts"]["tempo001"]


@pytest.mark.usefixtures("sources")
async def test_compare_by_month(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await add_statistic(hass, hours=24 * 32)
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    response = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/compare",
        entry_id=entry.entry_id,
        start="2026-01-01",
        end="2026-12-31",
    )
    assert response["group_by"] == "month"
    series = response["series"]
    assert [bucket["start"] for bucket in series] == ["2026-03-01", "2026-04-01"]
    assert sum(bucket["energy"] for bucket in series) == pytest.approx(24 * 32 * 0.5)


@pytest.mark.usefixtures("statistic", "sources")
async def test_actual_left_out_where_no_contract_was_in_force(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    base = contract_subentry(
        "Base", uid="base0001", kind=ContractKind.BASE, active_from="2026-03-02"
    )
    entry = await setup_entry(hass, make_entry([base]))
    response = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/compare",
        entry_id=entry.entry_id,
        start="2026-03-01",
        end="2026-03-02",
    )
    first, second = response["series"]
    assert first["actual"] is None
    assert second["actual"] == second["contracts"]["base0001"]


@pytest.mark.usefixtures("sources")
async def test_compare_before_any_data(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    response = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/compare",
        entry_id=entry.entry_id,
        start="2026-03-01",
        end="2026-03-02",
    )
    assert response["series"] == []


@pytest.mark.usefixtures("statistic", "sources")
async def test_bill_of_the_contract_in_force(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT]))
    bill = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/bill",
        entry_id=entry.entry_id,
        contract_id="tempo001",
        start="2026-03-01",
        end="2026-03-02",
    )
    action = await compare(hass, entry, "2026-03-01", "2026-03-02")
    tempo = action["contracts"][0]
    assert bill["contract"] == {"id": "tempo001", "name": "Tempo", "kind": "tempo"}
    assert (bill["start"], bill["end"]) == (action["start"], action["end"])
    [period] = bill["periods"]
    assert period["fixed_per_year"] == TEMPO_PERIODS[0].fixed_per_year
    assert {line["tranche"]: line["price"] for line in period["lines"]} == {
        tranche.value: price for tranche, price in TEMPO_PERIODS[0].prices.items()
    }
    for line in period["lines"]:
        assert line["cost"] == pytest.approx(line["energy"] * line["price"], abs=0.01)
    assert bill["energy"] == pytest.approx(tempo["energy"])
    assert bill["subscription"] == pytest.approx(tempo["fixed_cost"], abs=0.01)
    assert bill["total"] == pytest.approx(tempo["total_cost"], abs=0.01)
    assert bill["actual"] == pytest.approx(bill["total"], abs=0.01)
    assert str(bill["difference"]) == "0.0"


@pytest.mark.usefixtures("statistic", "sources")
async def test_bill_of_another_contract(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT]))
    bill = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/bill",
        entry_id=entry.entry_id,
        contract_id="base0001",
        start="2026-03-01",
        end="2026-03-02",
    )
    action = await compare(hass, entry, "2026-03-01", "2026-03-02")
    assert bill["actual"] == action["actual"]["total_cost"]
    assert bill["difference"] == pytest.approx(
        action["contracts"][1]["total_cost"] - action["actual"]["total_cost"],
        abs=0.01,
    )


@pytest.mark.usefixtures("statistic", "sources")
async def test_bill_split_where_prices_change(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    offer = contract_subentry(
        "Offer", uid="offer001", kind=ContractKind.BASE, pricing="manual"
    )
    entry = await setup_entry(
        hass,
        make_entry(
            [
                offer,
                price_period_subentry("offer001", "2026-01-01", "2026-03-01"),
                price_period_subentry("offer001", "2026-03-02"),
            ]
        ),
    )
    bill = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/bill",
        entry_id=entry.entry_id,
        contract_id="offer001",
        start="2026-01-01",
        end="2026-03-31",
    )
    assert [(period["start"], period["end"]) for period in bill["periods"]] == [
        ("2026-03-01T01:00:00+01:00", "2026-03-02T00:00:00+01:00"),
        ("2026-03-02T00:00:00+01:00", "2026-03-03T01:00:00+01:00"),
    ]
    assert [period["lines"][0]["energy"] for period in bill["periods"]] == [11.5, 12.5]
    # No contract is in force: nothing to compare the bill with.
    assert bill["actual"] is None
    assert bill["difference"] is None


@pytest.mark.usefixtures("statistic", "sources")
@pytest.mark.parametrize(
    ("message", "code"),
    [
        ({"entry_id": "unknown"}, "not_found"),
        ({"start": "2026-03-02", "end": "2026-03-01"}, "invalid_format"),
        ({"contract_id": "unknown"}, "not_found"),
    ],
)
async def test_bill_errors(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    message: dict[str, str],
    code: str,
) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    response = await command(
        hass_ws_client,
        hass,
        **{
            "type": f"{DOMAIN}/bill",
            "entry_id": entry.entry_id,
            "contract_id": "tempo001",
            "start": "2026-03-01",
            "end": "2026-03-02",
            **message,
        },
    )
    assert not response["success"]
    assert response["error"]["code"] == code


@pytest.mark.usefixtures("statistic", "sources")
async def test_compare_needs_a_loaded_entry(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    await hass.config_entries.async_unload(entry.entry_id)
    response = await command(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/compare",
        entry_id=entry.entry_id,
        start="2026-03-01",
        end="2026-03-02",
    )
    assert response["error"]["code"] == "not_allowed"


@pytest.mark.usefixtures("statistic", "sources")
async def test_panel_follows_the_entries(hass: HomeAssistant) -> None:
    await add_statistic(hass, OTHER_STATISTIC_ID)
    first = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    second = await setup_entry(
        hass, make_entry([TEMPO_CONTRACT], statistic_id=OTHER_STATISTIC_ID)
    )
    assert frontend.async_panel_exists(hass, PANEL_URL_PATH)

    await hass.config_entries.async_unload(first.entry_id)
    assert frontend.async_panel_exists(hass, PANEL_URL_PATH)
    await hass.config_entries.async_unload(second.entry_id)
    assert not frontend.async_panel_exists(hass, PANEL_URL_PATH)

    await hass.config_entries.async_setup(first.entry_id)
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)
    assert frontend.async_panel_exists(hass, PANEL_URL_PATH)


@pytest.mark.usefixtures("statistic", "sources")
async def test_panel_module(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    hass.config.language = "fr"
    await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    panel = hass.data[frontend.DATA_PANELS][PANEL_URL_PATH]
    assert panel.sidebar_title == "Contrats"
    assert panel.config is not None
    custom = panel.config["_panel_custom"]
    assert custom["name"] == "electricity-contracts-panel"

    client = await hass_client()
    response = await client.get(custom["module_url"])
    assert response.status == 200
    assert "electricity-contracts-panel" in await response.text()


@pytest.mark.usefixtures("sources")
async def test_insights(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    await add_statistic(hass, hours=72)
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT, BASE_CONTRACT]))
    insights = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/insights",
        entry_id=entry.entry_id,
        start="2026-03-02",
        end="2026-03-02",
    )
    [day] = insights["days"]
    action = await compare(hass, entry, "2026-03-02", "2026-03-02")
    assert day == {
        "date": "2026-03-02",
        "color": color_of(date(2026, 3, 2)).value,
        "energy": 12.0,
        # 16 hours from 6:00 to 22:00.
        "peak_energy": 8.0,
        "cost": action["actual"]["total_cost"],
    }
    assert insights["profile"] == [0.5] * 24
    # The day before isn't whole: the data starts at 1:00.
    assert insights["previous"] is None
    tempo = insights["tempo"]
    assert tempo["today"] == color_of(date(2026, 11, 7)).value
    # Not published yet, and nothing consumed lately to estimate from.
    assert tempo["tomorrow"] is None
    assert tempo["tomorrow_estimate"] is None
    season = tempo["season"]
    assert (season["start"], season["end"]) == ("2026-09-01", "2027-08-31")
    placed = [
        color_of(date(2026, 9, 1) + timedelta(days=offset)) for offset in range(68)
    ]
    assert season["red_left"] == 22 - placed.count(TempoColor.RED)
    assert season["white_left"] == 43 - placed.count(TempoColor.WHITE)
    assert season["white_left"] < 43

    third = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/insights",
        entry_id=entry.entry_id,
        start="2026-03-03",
        end="2026-03-03",
    )
    assert third["previous"] == {
        "start": "2026-03-02T00:00:00+01:00",
        "energy": 12.0,
        "cost": day["cost"],
    }


async def test_insights_estimate_tomorrow(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, sources: Sources
) -> None:
    # Tomorrow, Sunday 8 November, is published; the Sunday before was consumed.
    sources.public.async_calendar.side_effect = published_calendar(date(2026, 11, 8))
    await add_statistic(hass, hours=24 * 4, first=24 * 244)
    entry = await setup_entry(hass, make_entry([TEMPO_CONTRACT]))
    insights = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/insights",
        entry_id=entry.entry_id,
        start="2026-11-01",
        end="2026-11-07",
    )
    tempo = insights["tempo"]
    assert tempo["tomorrow"] == "blue"
    estimate = tempo["tomorrow_estimate"]
    assert estimate["energy"] == 12.0
    prices = TEMPO_PERIODS[1].prices
    assert estimate["cost"] == pytest.approx(
        8 * prices[Tranche.BLUE_HP] + 4 * prices[Tranche.BLUE_HC] + 189.98 / 365,
        abs=0.01,
    )


@pytest.mark.usefixtures("statistic", "sources")
async def test_insights_without_a_contract_in_force(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await setup_entry(hass, make_entry([BASE_CONTRACT]))
    insights = await result(
        hass_ws_client,
        hass,
        type=f"{DOMAIN}/insights",
        entry_id=entry.entry_id,
        start="2026-03-01",
        end="2026-03-02",
    )
    assert insights == {"days": [], "profile": [], "previous": None, "tempo": None}
