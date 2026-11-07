"""Fixtures for the Electricity Contracts tests."""

from collections.abc import Callable, Generator
from datetime import UTC, date, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from elec_tariffs import (
    ContractKind,
    PricePeriod,
    TempoColor,
    TempoError,
    Tranche,
    TrvError,
)
from freezegun.api import FrozenDateTimeFactory
from homeassistant.components.recorder.core import Recorder
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_wait_recording_done,
)

from custom_components.electricity_contracts.const import (
    CONF_ACTIVE_FROM,
    CONF_ACTIVE_TO,
    CONF_CONTRACT,
    CONF_CONTRACTS,
    CONF_END,
    CONF_FIXED_PER_YEAR,
    CONF_KIND,
    CONF_KVA,
    CONF_OFF_PEAK,
    CONF_PRICES,
    CONF_PRICING,
    CONF_START,
    CONF_STATISTIC_ID,
    CONF_UID,
    CONF_WEEKEND_OFF_PEAK,
    CONF_WINDOW,
    DOMAIN,
    PRICING_MANUAL,
    PRICING_OFFICIAL,
    SUBENTRY_COMPARISON,
    SUBENTRY_CONTRACT,
    SUBENTRY_PRICE_PERIOD,
)

STATISTIC_ID = "linky:00000000000000"
OTHER_STATISTIC_ID = "linky:11111111111111"
FIRST_HOUR = datetime(2026, 3, 1, tzinfo=UTC)
NOW = datetime(2026, 11, 7, 9, tzinfo=UTC)  # 10:00 in Paris

TEMPO_PERIODS = [
    PricePeriod(
        start=date(2026, 2, 1),
        end=date(2026, 7, 31),
        fixed_per_year=187.41,
        prices={
            Tranche.BLUE_HC: 0.1325,
            Tranche.BLUE_HP: 0.1612,
            Tranche.WHITE_HC: 0.1499,
            Tranche.WHITE_HP: 0.1871,
            Tranche.RED_HC: 0.1575,
            Tranche.RED_HP: 0.706,
        },
    ),
    PricePeriod(
        start=date(2026, 8, 1),
        end=None,
        fixed_per_year=189.98,
        prices={
            Tranche.BLUE_HC: 0.1356,
            Tranche.BLUE_HP: 0.1654,
            Tranche.WHITE_HC: 0.1536,
            Tranche.WHITE_HP: 0.1921,
            Tranche.RED_HC: 0.1615,
            Tranche.RED_HP: 0.7295,
        },
    ),
]
BASE_PERIODS = [
    PricePeriod(
        start=date(2026, 2, 1),
        end=date(2026, 7, 31),
        fixed_per_year=188.5,
        prices={Tranche.BASE: 0.1952},
    ),
    PricePeriod(
        start=date(2026, 8, 1),
        end=None,
        fixed_per_year=190.81,
        prices={Tranche.BASE: 0.2001},
    ),
]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    recorder_mock: Recorder,
    enable_custom_integrations: None,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Run every test with the recorder and the integration, at a fixed time."""
    freezer.move_to(NOW)


def color_of(day: date) -> TempoColor:
    """Return a made-up but stable color for a day."""
    if day.month in (12, 1) and day.weekday() < 5 and day.day % 3 == 0:
        return TempoColor.RED
    if day.month in (11, 2, 3) and day.weekday() < 6 and day.day % 4 == 0:
        return TempoColor.WHITE
    return TempoColor.BLUE


def published_calendar(
    last_day: date,
) -> Callable[[date, date], dict[date, TempoColor]]:
    """Answer like RTE when `last_day` is the last color published."""

    def answer(start: date, end: date) -> dict[date, TempoColor]:
        days: dict[date, TempoColor] = {}
        day = start
        while day <= min(end, last_day):
            days[day] = color_of(day)
            day += timedelta(days=1)
        return days

    return answer


async def add_statistic(
    hass: HomeAssistant,
    statistic_id: str = STATISTIC_ID,
    *,
    hours: int = 48,
    unit: str = "Wh",
    has_sum: bool = True,
    first: int = 0,
    wh: float = 500.0,
    step: timedelta = timedelta(hours=1),
) -> None:
    """Import an hourly statistic like the Linky app does."""
    source = statistic_id.split(":", 1)[0]
    metadata = StatisticMetaData(
        mean_type=StatisticMeanType.NONE,
        has_sum=has_sum,
        name=f"Linky {statistic_id.split(':', 1)[1]}",
        source=source,
        statistic_id=statistic_id,
        unit_class="energy" if unit == "Wh" else None,
        unit_of_measurement=unit,
    )
    rows = [
        StatisticData(
            start=FIRST_HOUR + step * hour,
            state=wh,
            sum=wh * (hour + 1),
        )
        for hour in range(first, first + hours)
    ]
    async_add_external_statistics(hass, metadata, rows)
    await async_wait_recording_done(hass)


@pytest.fixture
async def statistic(hass: HomeAssistant) -> str:
    """Import the Linky statistic of the tests."""
    await add_statistic(hass)
    return STATISTIC_ID


def contract_subentry(
    title: str,
    *,
    uid: str,
    kind: ContractKind,
    pricing: str = PRICING_OFFICIAL,
    kva: int = 6,
    active_from: str | None = None,
    active_to: str | None = None,
    off_peak: list[str] | None = None,
) -> ConfigSubentryData:
    """Build the subentry of a contract."""
    data: dict[str, Any] = {
        CONF_UID: uid,
        CONF_KIND: kind.value,
        CONF_PRICING: pricing,
        CONF_ACTIVE_FROM: active_from,
        CONF_ACTIVE_TO: active_to,
    }
    if pricing == PRICING_OFFICIAL:
        data[CONF_KVA] = kva
    if kind is ContractKind.HPHC:
        data[CONF_OFF_PEAK] = off_peak or ["22:00-06:00"]
        data[CONF_WEEKEND_OFF_PEAK] = False
    return ConfigSubentryData(
        data=data, subentry_type=SUBENTRY_CONTRACT, title=title, unique_id=uid
    )


def price_period_subentry(
    contract_uid: str, start: str, end: str | None = None
) -> ConfigSubentryData:
    """Build the subentry of a price period of a Base contract."""
    return ConfigSubentryData(
        data={
            CONF_CONTRACT: contract_uid,
            CONF_START: start,
            CONF_END: end,
            CONF_FIXED_PER_YEAR: 150.0,
            CONF_PRICES: {"base": 0.19},
        },
        subentry_type=SUBENTRY_PRICE_PERIOD,
        title=f"Offer · {start} → {end or '…'}",
        unique_id=None,
    )


def comparison_subentry(
    title: str,
    window: str = "fixed",
    *,
    start: str | None = "2026-03-01",
    end: str | None = "2026-03-31",
    contracts: list[str] | None = None,
) -> ConfigSubentryData:
    """Build the subentry of a comparison."""
    return ConfigSubentryData(
        data={
            CONF_WINDOW: window,
            CONF_START: start if window == "fixed" else None,
            CONF_END: end if window == "fixed" else None,
            CONF_CONTRACTS: contracts or [],
        },
        subentry_type=SUBENTRY_COMPARISON,
        title=title,
        unique_id=None,
    )


TEMPO_CONTRACT = contract_subentry(
    "Tempo", uid="tempo001", kind=ContractKind.TEMPO, active_from="2024-01-01"
)
BASE_CONTRACT = contract_subentry("Base", uid="base0001", kind=ContractKind.BASE)
MANUAL_CONTRACT = contract_subentry(
    "Offer", uid="offer001", kind=ContractKind.BASE, pricing=PRICING_MANUAL
)


def make_entry(
    subentries: list[ConfigSubentryData] | None = None,
    options: dict[str, Any] | None = None,
    statistic_id: str = STATISTIC_ID,
) -> MockConfigEntry:
    """Build the config entry of a consumption source."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Linky 00000000000000",
        unique_id=statistic_id,
        data={CONF_STATISTIC_ID: statistic_id},
        options=options or {},
        subentries_data=subentries or [],
    )


class Sources:
    """The library clients the integration uses, replaced by mocks."""

    def __init__(self) -> None:
        """Answer with the test prices and colors published up to today."""
        self.trv = MagicMock()
        self.trv.async_price_periods = AsyncMock(side_effect=self._prices)
        self.public = MagicMock()
        self.public.name = "rte_public"
        self.public.async_calendar = AsyncMock(
            side_effect=published_calendar(date(2026, 11, 7))
        )
        self.official = MagicMock()
        self.official.name = "rte_official"
        self.official.async_calendar = AsyncMock(
            side_effect=published_calendar(date(2026, 11, 7))
        )
        self.official.async_check_credentials = AsyncMock()
        self.official_class = MagicMock(return_value=self.official)

    @staticmethod
    async def _prices(kind: ContractKind, kva: int) -> list[PricePeriod]:
        del kva
        return {ContractKind.TEMPO: TEMPO_PERIODS, ContractKind.BASE: BASE_PERIODS}[
            kind
        ]

    def fail_prices(self) -> None:
        """Make data.gouv.fr unreachable."""
        self.trv.async_price_periods.side_effect = TrvError("down")

    def fail_public(self, error: TempoError | None = None) -> None:
        """Make the public Tempo calendar fail."""
        self.public.async_calendar.side_effect = error or TempoError("down")


@pytest.fixture
def sources() -> Generator[Sources]:
    """Replace the library clients where the integration imports them."""
    mocks = Sources()
    module = "custom_components.electricity_contracts"
    with (
        patch(f"{module}.coordinator.TrvClient", return_value=mocks.trv),
        patch(f"{module}.coordinator.RtePublicTempoClient", return_value=mocks.public),
        patch(f"{module}.coordinator.RteOfficialTempoClient", mocks.official_class),
        patch(f"{module}.config_flow.RteOfficialTempoClient", mocks.official_class),
    ):
        yield mocks
