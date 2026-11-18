"""Outdoor temperature from Open-Meteo, for homes without an outdoor thermometer.

With the option on and no outdoor sensor chosen, the hourly temperature at the
home's location, rounded to 0.1° (about 10 km), is written as a statistic of the
entry from the day before the first day of consumption. The tabs read it like the
statistics of a sensor. The last days are asked again at each update, since
Open-Meteo revises them once its reanalysis catches up.
"""

from datetime import UTC, date, datetime, timedelta
from typing import Any, Final

from elec_tariffs import OpenMeteoClient
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.storage import Store
from homeassistant.util.unit_conversion import TemperatureConverter

from .const import CONF_TEMPERATURE, CONF_WEATHER, DOMAIN
from .data import source_object
from .statistics import async_clear_statistics

STORE_VERSION: Final = 1
REVISED_DAYS: Final = 7
_NAMES: Final = {
    "en": "Outdoor temperature (Open-Meteo)",
    "fr": "Température extérieure (Open-Meteo)",
}


def weather_statistic_id(entry: ConfigEntry) -> str:
    """Return the ID of the entry's Open-Meteo temperature statistic."""
    return f"{DOMAIN}:{source_object(entry)}_outdoor_temperature"


def uses_weather(entry: ConfigEntry) -> bool:
    """Tell whether the outdoor temperature comes from Open-Meteo."""
    options = entry.options
    return bool(options.get(CONF_WEATHER)) and not options.get(CONF_TEMPERATURE)


def outdoor_statistic(entry: ConfigEntry) -> str | None:
    """Return the statistic of the outdoor temperature, None without one."""
    if sensor := entry.options.get(CONF_TEMPERATURE):
        return str(sensor)
    return weather_statistic_id(entry) if uses_weather(entry) else None


def outdoor_source(entry: ConfigEntry) -> str | None:
    """Say where the outdoor temperature comes from: a sensor or Open-Meteo."""
    if entry.options.get(CONF_TEMPERATURE):
        return "sensor"
    return "open_meteo" if uses_weather(entry) else None


def weather_store(hass: HomeAssistant, entry_id: str) -> Store[dict[str, Any]]:
    """Return the store of the location the temperature was written for."""
    return Store(hass, STORE_VERSION, f"{DOMAIN}.{entry_id}.weather")


class WeatherWriter:
    """Write the Open-Meteo temperature of one entry as a statistic."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: OpenMeteoClient
    ) -> None:
        """Prepare the statistic of an entry."""
        self.hass = hass
        self.entry = entry
        self.client = client
        self.statistic_id = weather_statistic_id(entry)
        self._store = weather_store(hass, entry.entry_id)
        self._written: dict[str, Any] = {}

    @property
    def enabled(self) -> bool:
        """Tell whether the entry takes its outdoor temperature from Open-Meteo."""
        return uses_weather(self.entry)

    @property
    def coordinates(self) -> list[float]:
        """Return the home's location, rounded to 0.1°."""
        return [
            round(self.hass.config.latitude, 1),
            round(self.hass.config.longitude, 1),
        ]

    async def async_load(self) -> None:
        """Load the statistic, location and first day written for."""
        self._written = await self._store.async_load() or {}

    async def async_update(self, first_day: date, now: datetime) -> None:
        """Ask Open-Meteo for the hours missing or revised, and write them.

        Clear the statistic when the option was turned off or the home moved.
        Raise WeatherError when Open-Meteo fails, and RecorderNotStartedError
        when the statistic must be cleared before Home Assistant has started.
        """
        coordinates = self.coordinates
        written_id = self._written.get("statistic_id")
        if (
            not self.enabled
            or self._written.get("coordinates") != coordinates
            or written_id != self.statistic_id
        ):
            if self._written or self.enabled:
                # Hours of another place, of the source's former statistic (its
                # ID follows the source), or of an earlier installation.
                stale = {self.statistic_id, written_id or self.statistic_id}
                await async_clear_statistics(self.hass, sorted(stale))
            if self._written:
                self._written = {}
                await self._store.async_remove()
            if not self.enabled:
                return
            last = None
        else:
            last = await self._async_last_hour()
        first = first_day - timedelta(days=1)
        written_from = self._written.get("first_day")
        start = (
            first
            # Older data arrived since: the days before are missing.
            if last is None or (written_from and first.isoformat() < written_from)
            else last.date() - timedelta(days=REVISED_DAYS)
        )
        utc_now = now.astimezone(UTC)
        temperatures = await self.client.async_hourly_temperatures(
            coordinates[0], coordinates[1], start, utc_now.date()
        )
        current_hour = utc_now.replace(minute=0, second=0, microsecond=0)
        rows = [
            StatisticData(start=moment, mean=value, min=value, max=value)
            for moment, value in sorted(temperatures.items())
            if moment < current_hour
        ]
        if rows:
            async_add_external_statistics(self.hass, self._metadata(), rows)
        written = {
            "statistic_id": self.statistic_id,
            "coordinates": coordinates,
            "first_day": min(start.isoformat(), written_from or start.isoformat()),
        }
        if self._written != written:
            self._written = written
            await self._store.async_save(self._written)

    async def _async_last_hour(self) -> datetime | None:
        last = await get_instance(self.hass).async_add_executor_job(
            lambda: get_last_statistics(
                self.hass, 1, self.statistic_id, convert_units=False, types={"mean"}
            )
        )
        rows = last.get(self.statistic_id)
        return datetime.fromtimestamp(rows[0]["start"], UTC) if rows else None

    def _metadata(self) -> StatisticMetaData:
        language = self.hass.config.language.split("-")[0]
        return StatisticMetaData(
            mean_type=StatisticMeanType.ARITHMETIC,
            has_sum=False,
            name=_NAMES.get(language, _NAMES["en"]),
            source=DOMAIN,
            statistic_id=self.statistic_id,
            unit_class=TemperatureConverter.UNIT_CLASS,
            unit_of_measurement=UnitOfTemperature.CELSIUS,
        )


async def async_remove_weather(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clear the Open-Meteo temperature of a removed entry and forget it."""
    store = weather_store(hass, entry.entry_id)
    if (written := await store.async_load()) is not None:
        current = weather_statistic_id(entry)
        stale = {current, written.get("statistic_id") or current}
        get_instance(hass).async_clear_statistics(sorted(stale))
    await store.async_remove()
