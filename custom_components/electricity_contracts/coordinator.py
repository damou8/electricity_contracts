"""Keep the regulated prices and the Tempo calendar up to date."""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from elec_tariffs import (
    ContractKind,
    FallbackTempoSource,
    PricePeriod,
    RteOfficialTempoClient,
    RtePublicTempoClient,
    TempoAuthError,
    TempoCalendarSource,
    TempoColor,
    TempoError,
    Tranche,
    TrvClient,
    TrvError,
    season_bounds,
    season_of,
)
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .comparison import async_wait_for_recorder
from .const import (
    CONF_RTE_CLIENT_ID,
    CONF_RTE_CLIENT_SECRET,
    CONF_STATISTIC_ID,
    DOMAIN,
    FRANCE_TIME_ZONE,
    PRICES_MAX_AGE_HOURS,
    SEASON_RETRY_HOURS,
    SOURCE_ISSUE_AFTER_HOURS,
    STORAGE_VERSION,
    TOMORROW_JITTER_MINUTES,
    TOMORROW_PUBLISHED,
    TOMORROW_RETRY_MINUTES,
)
from .data import Contract, contracts, manual_prices
from .statistics import (
    CostingStatus,
    RecorderNotStartedError,
    SeriesStatus,
    StatisticsWriter,
)

_LOGGER = logging.getLogger(__name__)

SOURCE_TEMPO = "tempo"
SOURCE_PRICES = "prices"

type ElectricityContractsConfigEntry = ConfigEntry[ElectricityContractsCoordinator]
type PricesKey = tuple[ContractKind, int]


@dataclass(frozen=True, kw_only=True)
class SourcesData:
    """What the contracts need to be costed."""

    first_day: date
    calendar: dict[date, TempoColor]
    official_prices: dict[PricesKey, list[PricePeriod]]


@dataclass(frozen=True, kw_only=True)
class ElectricityContractsData:
    """The sources and how far the statistics were written."""

    sources: SourcesData
    costing: CostingStatus


def _prices_key(kind: ContractKind, kva: int) -> str:
    return f"{kind.value}:{kva}"


def _period_to_store(period: PricePeriod) -> dict[str, Any]:
    return {
        "start": period.start.isoformat(),
        "end": period.end.isoformat() if period.end else None,
        "fixed_per_year": period.fixed_per_year,
        "prices": {tranche.value: price for tranche, price in period.prices.items()},
    }


def _period_from_store(data: dict[str, Any]) -> PricePeriod:
    return PricePeriod(
        start=date.fromisoformat(data["start"]),
        end=date.fromisoformat(data["end"]) if data["end"] else None,
        fixed_per_year=float(data["fixed_per_year"]),
        prices={Tranche(key): float(value) for key, value in data["prices"].items()},
    )


def _time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


@dataclass(kw_only=True)
class _Cache:
    """What was downloaded, kept between restarts."""

    calendar: dict[date, TempoColor] = field(default_factory=dict)
    season_checked: dict[str, datetime] = field(default_factory=dict)
    tomorrow_checked: datetime | None = None
    prices: dict[str, list[PricePeriod]] = field(default_factory=dict)
    prices_fetched: dict[str, datetime] = field(default_factory=dict)
    failing_since: dict[str, datetime] = field(default_factory=dict)

    @classmethod
    def from_store(cls, data: dict[str, Any] | None) -> _Cache:
        """Read the stored cache; start afresh if it can't be read."""
        if data is None:
            return cls()
        try:
            return cls(
                calendar={
                    date.fromisoformat(day): TempoColor(color)
                    for day, color in data["calendar"].items()
                },
                season_checked={
                    season: datetime.fromisoformat(when)
                    for season, when in data["season_checked"].items()
                },
                tomorrow_checked=_time(data["tomorrow_checked"]),
                prices={
                    key: [_period_from_store(period) for period in periods]
                    for key, periods in data["prices"].items()
                },
                prices_fetched={
                    key: datetime.fromisoformat(when)
                    for key, when in data["prices_fetched"].items()
                },
                failing_since={
                    source: datetime.fromisoformat(when)
                    for source, when in data["failing_since"].items()
                },
            )
        except KeyError, TypeError, ValueError, AttributeError:
            _LOGGER.warning("Ignoring an unreadable cache of prices and Tempo colors")
            return cls()

    def to_store(self) -> dict[str, Any]:
        """Return the cache in a JSON-friendly form."""
        return {
            "calendar": {
                day.isoformat(): color.value
                for day, color in sorted(self.calendar.items())
            },
            "season_checked": {
                season: when.isoformat() for season, when in self.season_checked.items()
            },
            "tomorrow_checked": (
                self.tomorrow_checked.isoformat() if self.tomorrow_checked else None
            ),
            "prices": {
                key: [_period_to_store(period) for period in periods]
                for key, periods in self.prices.items()
            },
            "prices_fetched": {
                key: when.isoformat() for key, when in self.prices_fetched.items()
            },
            "failing_since": {
                source: when.isoformat() for source, when in self.failing_since.items()
            },
        }


def cache_store(hass: HomeAssistant, entry_id: str) -> Store[dict[str, Any]]:
    """Return the store that keeps the downloads of an entry."""
    return Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}")


class ElectricityContractsCoordinator(DataUpdateCoordinator[ElectricityContractsData]):
    """Keep the sources of one consumption source and write its cost statistics."""

    config_entry: ElectricityContractsConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: ElectricityContractsConfigEntry
    ) -> None:
        """Set up the clients of the price and calendar sources."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(hours=1),
        )
        session = async_get_clientsession(hass)
        self.statistic_id: str = config_entry.data[CONF_STATISTIC_ID]
        self.trv = TrvClient(session)
        sources: list[TempoCalendarSource] = [RtePublicTempoClient(session)]
        options = config_entry.options
        self.has_credentials = CONF_RTE_CLIENT_ID in options
        if self.has_credentials:
            sources.append(
                RteOfficialTempoClient(
                    session,
                    options[CONF_RTE_CLIENT_ID],
                    options[CONF_RTE_CLIENT_SECRET],
                )
            )
        self.tempo = FallbackTempoSource(sources)
        # Spread the requests of every installation over a few minutes.
        digest = hashlib.sha256(config_entry.entry_id.encode()).digest()
        self._tomorrow_delay = timedelta(
            minutes=int.from_bytes(digest[:4]) % TOMORROW_JITTER_MINUTES
        )
        self._store = cache_store(hass, config_entry.entry_id)
        self._cache = _Cache()
        self._first_day: date | None = None
        self.last_errors: dict[str, str] = {}
        self.costing = StatisticsWriter(hass, config_entry)

    async def _async_setup(self) -> None:
        """Load the cache and find the first day of consumption."""
        self._cache = _Cache.from_store(await self._store.async_load())
        self._first_day = await self._async_first_day()
        await self.costing.async_load()

    async def _async_first_day(self) -> date:
        """Return the day of the first hour of consumption, or today if none."""
        recorder = get_instance(self.hass)
        months = await recorder.async_add_executor_job(
            statistics_during_period,
            self.hass,
            datetime(2000, 1, 1, tzinfo=UTC),
            None,
            {self.statistic_id},
            "month",
            None,
            {"sum"},
        )
        if not months.get(self.statistic_id):
            return dt_util.now(FRANCE_TIME_ZONE).date()
        # Months follow the server's time zone: look for the first hour in the
        # first month only.
        month_start = datetime.fromtimestamp(months[self.statistic_id][0]["start"], UTC)
        hours = await recorder.async_add_executor_job(
            statistics_during_period,
            self.hass,
            month_start,
            month_start + timedelta(days=32),
            {self.statistic_id},
            "hour",
            None,
            {"sum"},
        )
        first = datetime.fromtimestamp(
            hours[self.statistic_id][0]["start"], FRANCE_TIME_ZONE
        )
        return first.date()

    async def _async_update_data(self) -> ElectricityContractsData:
        """Fetch what is missing, then cost the hours not costed yet."""
        assert self._first_day is not None
        now = dt_util.utcnow()
        entry_contracts = contracts(self.config_entry)
        needed_prices = sorted(
            {
                (contract.kind, contract.kva)
                for contract in entry_contracts
                if contract.official and contract.kva is not None
            }
        )
        needs_tempo = any(
            contract.kind is ContractKind.TEMPO for contract in entry_contracts
        )
        changed = False
        if needed_prices:
            changed |= await self._async_refresh_prices(needed_prices, now)
        if needs_tempo:
            # Hours before 6:00 on the first day belong to the day before's color.
            changed |= await self._async_refresh_tempo(
                self._first_day - timedelta(days=1), now
            )
        if changed:
            await self._store.async_save(self._cache.to_store())
        self._update_issues(
            now, needs_tempo=needs_tempo, needs_prices=bool(needed_prices)
        )

        missing = [
            _prices_key(kind, kva)
            for kind, kva in needed_prices
            if not self._cache.prices.get(_prices_key(kind, kva))
        ]
        if needs_tempo and not self._cache.calendar:
            missing.append(SOURCE_TEMPO)
        if missing:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="sources_unavailable",
                translation_placeholders={"missing": ", ".join(missing)},
            )
        sources = SourcesData(
            first_day=self._first_day,
            calendar=dict(self._cache.calendar),
            official_prices={
                (kind, kva): self._cache.prices[_prices_key(kind, kva)]
                for kind, kva in needed_prices
            },
        )
        # Where each series stopped is read back from the statistics, and so
        # are the totals: both need the imports queued before to be written.
        # A first import takes minutes, and a reload meanwhile would queue it
        # again.
        await self._async_wait_for_recorder()
        try:
            costing = await self.costing.async_update(
                sources.official_prices, sources.calendar
            )
        except RecorderNotStartedError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="recorder_starting"
            ) from err
        await self._async_wait_for_recorder()
        self._update_price_issues(costing, contracts(self.config_entry))
        return ElectricityContractsData(sources=sources, costing=costing)

    async def _async_wait_for_recorder(self) -> None:
        if not await async_wait_for_recorder(self.hass):
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="recorder_busy"
            )

    def _update_price_issues(
        self, costing: CostingStatus, entry_contracts: list[Contract]
    ) -> None:
        """Raise an issue for each contract waiting for a price, clear the others.

        A contract priced by hand that has no price yet is still being set up:
        the Contracts page shows it waiting, with a link to add them.
        """
        prefix = f"missing_price_{self.config_entry.entry_id}_"
        priced = {prices.contract_uid for prices in manual_prices(self.config_entry)}
        wanted: dict[str, tuple[Contract, date]] = {}
        for contract in entry_contracts:
            status = costing.contracts.get(contract.uid)
            if (
                status
                and status.waiting
                and status.waiting.reason == "price"
                and (contract.official or contract.uid in priced)
            ):
                wanted[f"{prefix}{contract.uid}"] = (contract, status.waiting.day)
        registry = ir.async_get(self.hass)
        for domain, issue_id in list(registry.issues):
            if (
                domain == DOMAIN
                and issue_id.startswith(prefix)
                and issue_id not in wanted
            ):
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)
        for issue_id, (contract, day) in wanted.items():
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=(
                    "missing_price_official" if contract.official else "missing_price"
                ),
                translation_placeholders={
                    "contract": contract.name,
                    "day": day.isoformat(),
                    "kva": str(contract.kva or ""),
                },
            )

    async def async_recompute(self) -> None:
        """Clear and write every statistic again."""
        self.costing.request_recompute()
        await self.async_refresh()

    async def _async_refresh_prices(
        self, needed: list[PricesKey], now: datetime
    ) -> bool:
        changed = False
        max_age = timedelta(hours=PRICES_MAX_AGE_HOURS)
        for kind, kva in needed:
            key = _prices_key(kind, kva)
            fetched = self._cache.prices_fetched.get(key)
            if fetched and now - fetched < max_age:
                continue
            try:
                periods = await self.trv.async_price_periods(kind, kva)
            except TrvError as err:
                changed |= self._record_failure(SOURCE_PRICES, err, now)
                continue
            self._cache.prices[key] = periods
            self._cache.prices_fetched[key] = now
            self._record_success(SOURCE_PRICES)
            changed = True
        return changed

    async def _async_refresh_tempo(self, first_day: date, now: datetime) -> bool:
        today = now.astimezone(FRANCE_TIME_ZONE).date()
        tomorrow = today + timedelta(days=1)
        changed = False
        try:
            for season in self._seasons(first_day, today):
                start, end = season_bounds(season)
                start = max(start, first_day)
                if not self._season_needs_fetch(season, start, min(end, today), now):
                    continue
                colors = await self.tempo.async_calendar(start, min(end, tomorrow))
                self._cache.calendar.update(colors)
                self._cache.season_checked[season] = now
                changed = True
            if self._tomorrow_needs_fetch(tomorrow, now):
                colors = await self.tempo.async_calendar(today, tomorrow)
                self._cache.calendar.update(colors)
                self._cache.tomorrow_checked = now
                changed = True
        except TempoError as err:
            changed |= self._record_failure(SOURCE_TEMPO, err, now)
        else:
            changed |= self._record_success(SOURCE_TEMPO)
        return changed

    @staticmethod
    def _seasons(first_day: date, today: date) -> list[str]:
        first = int(season_of(first_day)[:4])
        last = int(season_of(today)[:4])
        return [f"{year}-{year + 1}" for year in range(first, last + 1)]

    def _season_needs_fetch(
        self, season: str, start: date, end: date, now: datetime
    ) -> bool:
        day = start
        while day <= end:
            if day not in self._cache.calendar:
                break
            day += timedelta(days=1)
        else:
            return False
        checked = self._cache.season_checked.get(season)
        return checked is None or now - checked >= timedelta(hours=SEASON_RETRY_HOURS)

    def _tomorrow_needs_fetch(self, tomorrow: date, now: datetime) -> bool:
        if tomorrow in self._cache.calendar:
            return False
        local = now.astimezone(FRANCE_TIME_ZONE)
        published = (
            datetime.combine(local.date(), TOMORROW_PUBLISHED, FRANCE_TIME_ZONE)
            + self._tomorrow_delay
        )
        if local < published:
            return False
        checked = self._cache.tomorrow_checked
        return checked is None or now - checked >= timedelta(
            minutes=TOMORROW_RETRY_MINUTES
        )

    def _record_failure(self, source: str, err: Exception, now: datetime) -> bool:
        if source not in self.last_errors:
            _LOGGER.warning("Could not update the %s source: %s", source, err)
        self.last_errors[source] = str(err)
        if source == SOURCE_TEMPO:
            self._update_credentials_issue()
        if source in self._cache.failing_since:
            return False
        self._cache.failing_since[source] = now
        return True

    def _record_success(self, source: str) -> bool:
        if self.last_errors.pop(source, None) is not None:
            _LOGGER.info("The %s source works again", source)
        if source == SOURCE_TEMPO:
            self._update_credentials_issue()
        return self._cache.failing_since.pop(source, None) is not None

    def _update_credentials_issue(self) -> None:
        issue_id = f"rte_credentials_refused_{self.config_entry.entry_id}"
        refused = isinstance(self.tempo.last_errors.get("rte_official"), TempoAuthError)
        if refused:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key="rte_credentials_refused",
                translation_placeholders={"title": self.config_entry.title},
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, issue_id)

    def _update_issues(
        self, now: datetime, *, needs_tempo: bool, needs_prices: bool
    ) -> None:
        threshold = timedelta(hours=SOURCE_ISSUE_AFTER_HOURS)
        for source, needed, translation_key in (
            (
                SOURCE_TEMPO,
                needs_tempo,
                "tempo_unavailable_official"
                if self.has_credentials
                else "tempo_unavailable",
            ),
            (SOURCE_PRICES, needs_prices, "prices_unavailable"),
        ):
            issue_id = f"{source}_unavailable_{self.config_entry.entry_id}"
            since = self._cache.failing_since.get(source)
            if needed and since is not None and now - since >= threshold:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    issue_id,
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key=translation_key,
                    translation_placeholders={
                        "title": self.config_entry.title,
                        "since": dt_util.as_local(since).strftime("%Y-%m-%d %H:%M"),
                        "error": self.last_errors.get(source, ""),
                    },
                )
            else:
                ir.async_delete_issue(self.hass, DOMAIN, issue_id)

    def diagnostics(self) -> dict[str, Any]:
        """Summarise the sources without personal data."""
        colors = list(self._cache.calendar.values())
        return {
            "first_day": self._first_day.isoformat() if self._first_day else None,
            "tempo_sources": self.tempo.name,
            "tempo_last_source": self.tempo.last_source,
            "calendar": {
                "days": len(colors),
                "first": min(self._cache.calendar).isoformat() if colors else None,
                "last": max(self._cache.calendar).isoformat() if colors else None,
                **{color.value: colors.count(color) for color in TempoColor},
            },
            "season_checked": {
                season: when.isoformat()
                for season, when in self._cache.season_checked.items()
            },
            "prices": {
                key: {
                    "fetched": self._cache.prices_fetched[key].isoformat()
                    if key in self._cache.prices_fetched
                    else None,
                    "periods": len(periods),
                    "latest": _period_to_store(periods[-1]) if periods else None,
                }
                for key, periods in self._cache.prices.items()
            },
            "failing_since": {
                source: when.isoformat()
                for source, when in self._cache.failing_since.items()
            },
            "last_errors": self.last_errors,
            "costing": _costing_diagnostics(self.data.costing),
        }


def _series_diagnostics(status: SeriesStatus | None) -> dict[str, Any] | None:
    if status is None:
        return None
    return {
        "last_hour": status.last_hour.isoformat() if status.last_hour else None,
        "waiting": (
            {"reason": status.waiting.reason, "day": status.waiting.day.isoformat()}
            if status.waiting
            else None
        ),
    }


def _costing_diagnostics(status: CostingStatus) -> dict[str, Any]:
    return {
        "last_source_hour": (
            status.last_source_hour.isoformat() if status.last_source_hour else None
        ),
        "contracts": {
            uid: _series_diagnostics(item) for uid, item in status.contracts.items()
        },
        "actual": _series_diagnostics(status.actual),
    }


@callback
def async_delete_issues(hass: HomeAssistant, entry_id: str) -> None:
    """Delete the repair issues of an entry."""
    for prefix in (
        "rte_credentials_refused",
        f"{SOURCE_TEMPO}_unavailable",
        f"{SOURCE_PRICES}_unavailable",
    ):
        ir.async_delete_issue(hass, DOMAIN, f"{prefix}_{entry_id}")
    prefix = f"missing_price_{entry_id}_"
    for domain, issue_id in list(ir.async_get(hass).issues):
        if domain == DOMAIN and issue_id.startswith(prefix):
            ir.async_delete_issue(hass, DOMAIN, issue_id)
