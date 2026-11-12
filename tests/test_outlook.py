"""Tests of the price ahead and of the projection of the season."""

from datetime import UTC, date, datetime, time, timedelta

import pytest
from elec_tariffs import (
    ContractKind,
    ContractRules,
    TempoColor,
    TimeRange,
    Tranche,
    cost_hour,
)
from homeassistant.config_entries import ConfigSubentryData

from custom_components.electricity_contracts.const import FRANCE_TIME_ZONE
from custom_components.electricity_contracts.data import Contract, contracts
from custom_components.electricity_contracts.outlook import (
    _history,
    _peak_shares,
    _place_colors,
    _project,
    _split_like,
    tranche_at,
)

from .conftest import BASE_CONTRACT, TEMPO_CONTRACT, TEMPO_PERIODS, make_entry

HPHC = ContractRules(
    kind=ContractKind.HPHC,
    off_peak=(TimeRange(start=time(22), end=time(6)),),
    weekend_off_peak=True,
)


def paris(year: int, month: int, day: int, hour: int = 0) -> datetime:
    return datetime(year, month, day, hour, tzinfo=FRANCE_TIME_ZONE)


def contract(subentry: ConfigSubentryData) -> Contract:
    return contracts(make_entry([subentry]))[0]


@pytest.mark.parametrize(
    ("moment", "rules", "tranche"),
    [
        (paris(2026, 11, 6, 23), HPHC, Tranche.HC),
        (paris(2026, 11, 6, 12), HPHC, Tranche.HP),
        # Saturday.
        (paris(2026, 11, 7, 12), HPHC, Tranche.HC),
        (paris(2026, 11, 6, 12), ContractRules(kind=ContractKind.BASE), Tranche.BASE),
        # The night belongs to the Tempo day that started the evening before.
        (paris(2026, 11, 7, 3), ContractRules(kind=ContractKind.TEMPO), Tranche.RED_HC),
        (paris(2026, 11, 7, 12), ContractRules(kind=ContractKind.TEMPO), None),
    ],
)
def test_tranche_at(
    moment: datetime, rules: ContractRules, tranche: Tranche | None
) -> None:
    assert tranche_at(moment, rules, {date(2026, 11, 6): TempoColor.RED}) == tranche


def test_place_colors() -> None:
    # 21 red days placed already: one left, for the weekday that consumes most.
    placed = {
        date(2026, 9, 1) + timedelta(days=day): TempoColor.RED for day in range(21)
    }
    hours = [paris(2026, 12, 4) + timedelta(hours=hour) for hour in range(24 * 3)]
    # Friday 4, Saturday 5 and Sunday 6 December; Saturday consumes most.
    energy = [1.0] * 24 + [3.0] * 24 + [2.0] * 24
    colors = _place_colors(placed, hours, energy, date(2026, 12, 1))
    # The hours before 6:00 on the 4th belong to the 3rd.
    assert colors == {
        date(2026, 12, 3): TempoColor.WHITE,
        # No red on a Saturday, white instead; the red goes to Friday.
        date(2026, 12, 5): TempoColor.WHITE,
        date(2026, 12, 4): TempoColor.RED,
        # No white on a Sunday.
        date(2026, 12, 6): TempoColor.BLUE,
    }


def history(start: datetime, values: list[float]) -> list[tuple[float, float]]:
    """Hourly rows a year (52 weeks) before `start`."""
    first = start - timedelta(days=364)
    return [
        ((first + timedelta(hours=hour)).timestamp(), value)
        for hour, value in enumerate(values)
    ]


def test_project_tempo() -> None:
    tempo = contract(TEMPO_CONTRACT)
    start = paris(2026, 12, 1).astimezone(UTC)
    end = start + timedelta(days=2)
    # The hour missing takes the average of the same hour on the other days.
    rows = history(start, [0.5] * 48)
    del rows[24 + 5]
    known = {date(2026, 11, 30): TempoColor.BLUE}
    projection = _project(
        tempo,
        TEMPO_PERIODS,
        known,
        _history(rows, []),
        {},
        start=start,
        end=end,
        today=date(2026, 11, 30),
    )
    # No red day placed yet: Tuesday 1 and Wednesday 2 December are red.
    colors = {
        **known,
        date(2026, 12, 1): TempoColor.RED,
        date(2026, 12, 2): TempoColor.RED,
    }
    expected = sum(
        cost_hour(
            (start + timedelta(hours=hour)).astimezone(FRANCE_TIME_ZONE),
            0.5,
            tempo.rules,
            TEMPO_PERIODS,
            colors,
        ).total
        for hour in range(48)
    )
    assert projection == {"energy": 24.0, "cost": pytest.approx(expected)}


def test_project_needs_history_and_prices() -> None:
    base = contract(BASE_CONTRACT)
    start = paris(2026, 12, 1).astimezone(UTC)
    end = start + timedelta(days=1)
    rows = _history(history(start, [0.5] * 20), [])
    assert (
        _project(
            base,
            TEMPO_PERIODS,
            {},
            rows,
            {},
            start=start,
            end=end,
            today=date(2026, 11, 30),
        )
        is None
    )
    assert (
        _project(base, [], {}, rows, {}, start=start, end=end, today=date(2026, 11, 30))
        is None
    )
    assert _project(
        base, TEMPO_PERIODS, {}, rows, {}, start=end, end=end, today=date(2026, 11, 30)
    ) == {
        "cost": 0.0,
        "energy": 0.0,
    }


def test_history_spreads_the_days_known_in_total() -> None:
    # 1 December was only known in total, the hours after it one by one.
    day = paris(2026, 12, 1).astimezone(UTC)
    rows = [
        (day.timestamp(), 24.0),
        ((day + timedelta(days=1)).timestamp(), 2.0),
        ((day + timedelta(days=1, hours=1)).timestamp(), 3.0),
    ]
    hours = {
        moment.replace(tzinfo=FRANCE_TIME_ZONE): value
        for moment, value in _history(rows, []).items()
    }
    # Without hours to learn a typical day from, every hour gets as much.
    assert [hours[paris(2026, 12, 1, hour)] for hour in range(24)] == [1.0] * 24
    assert hours[paris(2026, 12, 2, 0)] == 2.0
    assert hours[paris(2026, 12, 2, 1)] == 3.0
    assert len(hours) == 26


def test_peak_shares() -> None:
    shares = _peak_shares(
        {
            Tranche.BLUE_HC: 3.0,
            Tranche.BLUE_HP: 1.0,
            Tranche.RED_HC: 4.0,
            Tranche.RED_HP: 0.0,
        }
    )
    # White days consumed nothing: they take the share of all the days.
    assert shares == {
        TempoColor.BLUE: 0.25,
        TempoColor.WHITE: 1 / 8,
        TempoColor.RED: 0.0,
    }
    assert _peak_shares({}) == {}


def test_split_like_the_color() -> None:
    # A red day from 6:00 to 6:00, 1 kWh an hour: 16 in peak hours, 8 off-peak.
    hours = [paris(2026, 12, 1, 6) + timedelta(hours=hour) for hour in range(24)]
    colors = {date(2026, 12, 1): TempoColor.RED}
    energy = _split_like(hours, [1.0] * 24, colors, {TempoColor.RED: 0.25})
    assert sum(energy) == pytest.approx(24.0)
    # 22:00 to 6:00 are off-peak.
    assert sum(energy[16:]) == pytest.approx(18.0)
    assert _split_like(hours, [1.0] * 24, colors, {}) == [1.0] * 24
    # A day of unknown color, or cut, stays as it is.
    assert _split_like(hours, [1.0] * 24, {}, {TempoColor.RED: 0.25}) == [1.0] * 24
    assert (
        _split_like(hours[:20], [1.0] * 20, colors, {TempoColor.RED: 0.25})
        == [1.0] * 20
    )
