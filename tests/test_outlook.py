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
    _place_colors,
    _project,
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
        rows,
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
    rows = history(start, [0.5] * 20)
    assert (
        _project(
            base,
            TEMPO_PERIODS,
            {},
            rows,
            start=start,
            end=end,
            today=date(2026, 11, 30),
        )
        is None
    )
    assert (
        _project(base, [], {}, rows, start=start, end=end, today=date(2026, 11, 30))
        is None
    )
    assert _project(
        base, TEMPO_PERIODS, {}, rows, start=end, end=end, today=date(2026, 11, 30)
    ) == {
        "cost": 0.0,
        "energy": 0.0,
    }
