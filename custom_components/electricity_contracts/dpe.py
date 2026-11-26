"""An energy label in the style of the French DPE, from what the home used.

The label counts the heating, the hot water and the auxiliaries (ventilation,
pumps) of the 12 months that end on a day, divided by the living area. The
auxiliaries are always a share of the three; the hot water is one only when it
is neither measured nor estimated.

Electric heating before the heating tab's window (before the heating statistics,
or before the first costed hour) is estimated from the Linky's days and the
outdoor temperature, so the label covers the whole year.
"""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import probatio as vol
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.const import UnitOfEnergy, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .comparison import day_start
from .const import CONF_WEATHER, DOMAIN, FRANCE_TIME_ZONE
from .coordinator import ElectricityContractsConfigEntry
from .data import Heating, source_statistic
from .heating import async_heating_between, heating_window
from .insights import line_heating, weather_fit
from .weather import outdoor_ids, outdoor_rows, outdoor_statistic

STORE_VERSION = 1

SURFACE = "surface"
COEFFICIENT = "coefficient"
AUXILIARIES = "auxiliaries"
WATER = "water"
SETPOINT = "setpoint"
SETBACK = "setback"

# The DPE heats to 19 °C, 3 °C less at night from 22:00 to 6:00 (méthode 3CL).
DPE_SETPOINT = 19.0
DPE_SETBACK = 3.0
_NIGHT_SHARE = 8 / 24

# The living area in m², the primary energy of a kWh of electricity (1.9 from
# 1 January 2026), the shares in % of the three uses, and the home's own
# setpoint and night setback in °C, used without indoor thermometers.
DEFAULTS: dict[str, float] = {
    SURFACE: 100.0,
    COEFFICIENT: 1.9,
    AUXILIARIES: 5.0,
    WATER: 15.0,
    SETPOINT: DPE_SETPOINT,
    SETBACK: DPE_SETBACK,
}
# The shares can't take all of the three uses: 30 + 60 leaves the heating 10 %.
SETTINGS_SCHEMA: dict[Any, Any] = {
    vol.Required(SURFACE): vol.All(vol.Coerce(float), vol.Range(min=5, max=2000)),
    vol.Required(COEFFICIENT): vol.All(vol.Coerce(float), vol.Range(min=1, max=3)),
    vol.Required(AUXILIARIES): vol.All(vol.Coerce(float), vol.Range(min=0, max=30)),
    vol.Required(WATER): vol.All(vol.Coerce(float), vol.Range(min=0, max=60)),
    vol.Required(SETPOINT): vol.All(vol.Coerce(float), vol.Range(min=10, max=26)),
    vol.Required(SETBACK): vol.All(vol.Coerce(float), vol.Range(min=0, max=10)),
}

# kg of CO₂ a kWh, as in the DPE (arrêté du 31 mars 2021).
_CO2_ELECTRICITY = {"heating": 0.079, "water": 0.065, "auxiliaries": 0.064}
_CO2_GAS = 0.227
# The upper bound of classes A to F; above the last, G.
ENERGY_BOUNDS = (70, 110, 180, 250, 330, 420)
CLIMATE_BOUNDS = (6, 11, 30, 50, 70, 100)
_LETTERS = "ABCDEFG"


def settings_store(hass: HomeAssistant, entry_id: str) -> Store[dict[str, float]]:
    """Return the store of an entry's label settings.

    Kept out of the options: changing them doesn't reload the entry.
    """
    return Store(hass, STORE_VERSION, f"{DOMAIN}.{entry_id}.dpe")


async def async_load_settings(hass: HomeAssistant, entry_id: str) -> dict[str, float]:
    """Return an entry's settings, the defaults for those never saved."""
    saved = await settings_store(hass, entry_id).async_load() or {}
    return {key: float(saved.get(key, value)) for key, value in DEFAULTS.items()}


async def async_save_settings(
    hass: HomeAssistant, entry_id: str, settings: dict[str, float]
) -> dict[str, float]:
    """Save an entry's settings and return them."""
    saved = {key: float(settings[key]) for key in DEFAULTS}
    await settings_store(hass, entry_id).async_save(saved)
    return saved


def _year_before(day: date) -> date:
    """Return the day a year before, 28 February for 29 February."""
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, day=28)


def _class(value: float, bounds: tuple[int, ...]) -> str:
    below = [
        letter
        for letter, bound in zip(_LETTERS, bounds, strict=False)
        if value <= bound
    ]
    return below[0] if below else _LETTERS[-1]


def _mean_temperature(setpoint: float, setback: float) -> float:
    """Return the mean indoor temperature of a setpoint lowered at night."""
    return setpoint - setback * _NIGHT_SHARE


def _fitted(weather: dict[str, Any] | None) -> bool:
    return bool(weather and weather["slope"] and weather["slope"] > 0)


def _conventional(answer: dict[str, Any], settings: dict[str, float]) -> dict[str, Any]:
    """Say how much more heating the DPE's setpoint takes than the home's.

    The weather fit gives the heating of a day from its degrees under the base:
    moving the home's mean indoor temperature to the DPE's moves its base by as
    much, on each day of the year. The home's temperature is what its
    thermometers measured on the heating days, else its setpoint setting.
    Without a fit, nothing moves.
    The days estimated before the window move with their own line.
    """
    parts: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    if _fitted(answer["weather"]):
        days = answer["days"] if answer["measured"] else answer["weather_days"]
        parts.append((answer["weather"], days))
    if (before := answer.get("before")) and _fitted(before["weather"]):
        parts.append((before["weather"], before["weather_days"]))
    if not parts:
        return {"applied": False, "extra": 0.0}
    counted = [
        (weather, [day for day in days if day["temperature"] is not None])
        for weather, days in parts
    ]
    measured = [
        day["indoor"]
        for weather, days in counted
        for day in days
        if day["indoor"] is not None and day["temperature"] < weather["base"]
    ]
    if measured:
        indoor, source = sum(measured) / len(measured), "thermometers"
    else:
        indoor = _mean_temperature(settings[SETPOINT], settings[SETBACK])
        source = "setting"
    shift = _mean_temperature(DPE_SETPOINT, DPE_SETBACK) - indoor
    extra = sum(
        line_heating(weather, weather["base"] + shift - day["temperature"])
        - line_heating(weather, weather["base"] - day["temperature"])
        for weather, days in counted
        for day in days
    )
    return {
        "applied": True,
        "source": source,
        "indoor": round(indoor, 1),
        "shift": round(shift, 1),
        "extra": extra,
    }


def _uses(
    answer: dict[str, Any], settings: dict[str, float], extra: float
) -> list[dict[str, Any]]:
    """Return the kWh of the heating, the hot water and the auxiliaries.

    Each with its energy (gas or not) and where it comes from: measured,
    estimated (by the Heating tab) or share (a setting). `extra` is what the
    DPE's setpoint adds to the heating. Empty without heating.
    """
    auxiliaries = settings[AUXILIARIES] / 100
    water_share = settings[WATER] / 100
    gas = bool(answer["gas"])
    if answer["measured"]:
        heat = answer["totals"]["heating"] if answer["totals"] else 0.0
        heat_source = "measured"
    else:
        estimated = answer["estimated"]
        heat = estimated["heating"] if estimated else 0.0
        heat_source = "estimated"
    # The heating estimated from the Linky before the window holds no hot water.
    before = answer.get("before")
    earlier = before["heating"] if before else 0.0
    if before:
        heat_source = "mixed" if heat_source == "measured" else "estimated"
    if heat + earlier <= 0:
        return []
    if answer["water_split"]:
        water = answer["totals"]["water"]
        if before and (days := len(answer["days"])):
            # The water of the days before, at the window's daily mean.
            water += water / days * before["days"]
        water_gas = bool(answer["water_gas"])
        water_source = "measured" if answer["water_measured"] else "estimated"
        heat = max(0.0, heat + earlier + extra)
        total = (heat + water) / (1 - auxiliaries)
    elif answer["measured"] and answer["with_water"]:
        # The hot water is in the heating statistics, but can't be told apart;
        # before them, its share comes on top of the Linky's estimate.
        inside = heat / (1 - auxiliaries) * water_share
        water = inside + earlier / (1 - auxiliaries - water_share) * water_share
        heat = max(0.0, heat - inside + earlier + extra)
        total = (heat + water) / (1 - auxiliaries)
        water_gas, water_source = gas, "share"
    else:
        # The hot water is elsewhere, unmeasured: an electric water heater.
        heat = max(0.0, heat + earlier + extra)
        total = heat / (1 - auxiliaries - water_share)
        water = total * water_share
        water_gas, water_source = False, "share"
    return [
        {"use": "heating", "energy": heat, "gas": gas, "source": heat_source},
        {"use": "water", "energy": water, "gas": water_gas, "source": water_source},
        {
            "use": "auxiliaries",
            "energy": total * auxiliaries,
            "gas": False,
            "source": "share",
        },
    ]


def dpe_label(answer: dict[str, Any], settings: dict[str, float]) -> dict[str, Any]:
    """Return the label of a heating answer: its classes and what each use counts.

    `classes` is None when there is no heating to count. `conventional` tells
    how the heating was moved to the DPE's setpoint.
    """
    conventional = _conventional(answer, settings)
    rows = []
    for item in _uses(answer, settings, conventional["extra"]):
        energy = item["energy"]
        primary = energy * (1.0 if item["gas"] else settings[COEFFICIENT])
        co2 = energy * (_CO2_GAS if item["gas"] else _CO2_ELECTRICITY[item["use"]])
        rows.append(
            {
                **item,
                "energy": round(energy, 1),
                "primary": round(primary, 1),
                "co2": round(co2, 1),
            }
        )
    conventional["extra"] = round(conventional["extra"], 1)
    if not rows:
        return {"classes": None, "uses": [], "conventional": conventional}
    surface = settings[SURFACE]
    energy = round(sum(row["primary"] for row in rows) / surface)
    climate = round(sum(row["co2"] for row in rows) / surface, 1)
    energy_class = _class(energy, ENERGY_BOUNDS)
    climate_class = _class(climate, CLIMATE_BOUNDS)
    return {
        "classes": {
            "energy": energy_class,
            "climate": climate_class,
            # The worse of the two.
            "label": max(energy_class, climate_class),
        },
        "energy": energy,
        "climate": climate,
        "uses": rows,
        "conventional": conventional,
    }


def _local_day(moment: datetime) -> date:
    return moment.astimezone(FRANCE_TIME_ZONE).date()


def _day_of(timestamp: float) -> date:
    """Return the day a daily row of the recorder stands for, in its time zone."""
    return dt_util.as_local(datetime.fromtimestamp(timestamp, UTC)).date()


async def _async_linky_heating(
    hass: HomeAssistant,
    entry: ElectricityContractsConfigEntry,
    start: datetime,
    end: datetime,
) -> dict[str, Any] | None:
    """Estimate the electric heating from `start` to `end` from the Linky's days.

    Each day's consumption is fitted on its heating degree days, like the weather
    fit: the heating of each day comes from its degree days. Only the days with an
    outdoor temperature count, so the estimate starts at the first of them.
    Without a line, None: those days are left out rather than counted without
    heating.
    """
    source_id = source_statistic(entry)
    assert source_id is not None
    heating = Heating.from_options(entry.options, outdoor=outdoor_statistic(entry))

    def read() -> tuple[dict[date, float], dict[date, float], dict[date, float]]:
        energy = {
            _day_of(row["start"]): row.get("change") or 0.0
            for row in statistics_during_period(
                hass,
                start,
                end,
                {source_id},
                "day",
                {"energy": UnitOfEnergy.KILO_WATT_HOUR},
                {"change"},
            ).get(source_id, [])
        }
        temperatures = statistics_during_period(
            hass,
            start,
            end,
            {*outdoor_ids(entry), *heating.indoor},
            "day",
            {"temperature": UnitOfTemperature.CELSIUS},
            {"mean"},
        )
        indoor: dict[date, list[float]] = {}
        for statistic_id in heating.indoor:
            for row in temperatures.get(statistic_id, []):
                if (mean := row.get("mean")) is not None:
                    indoor.setdefault(_day_of(row["start"]), []).append(mean)
        return (
            energy,
            {
                _day_of(row["start"]): mean
                for row in outdoor_rows(entry, temperatures)
                if (mean := row.get("mean")) is not None
            },
            {day: sum(values) / len(values) for day, values in indoor.items()},
        )

    energy, outdoor, indoor = await get_instance(hass).async_add_executor_job(read)
    # A daily read also returns the day that starts at `end`.
    first_day, end_day = _local_day(start), _local_day(end)
    energy = {day: kwh for day, kwh in energy.items() if first_day <= day < end_day}
    weather = weather_fit(
        {day: {"energy": kwh} for day, kwh in energy.items()}, outdoor
    )
    if not _fitted(weather):
        return None
    counted = {day: outdoor[day] for day in sorted(energy) if day in outdoor}
    heat = sum(
        line_heating(weather, weather["base"] - value) for value in counted.values()
    )
    return {
        "start": min(counted).isoformat(),
        "end": (_local_day(end) - timedelta(days=1)).isoformat(),
        "days": len(counted),
        "heating": heat,
        "weather": weather,
        "weather_days": [
            {"temperature": value, "indoor": indoor.get(day)}
            for day, value in counted.items()
        ],
    }


async def _async_main_start(
    entry: ElectricityContractsConfigEntry, first: datetime
) -> datetime:
    """Return where the heating tab's answer starts.

    Its window, or the heating statistics' first day when they start later.
    """
    if not Heating.from_options(entry.options, outdoor=None).measured:
        return first
    day = await entry.runtime_data.async_heating_first_day()
    return max(first, day_start(day)) if day else first


async def async_dpe(
    hass: HomeAssistant, *, entry: ElectricityContractsConfigEntry, end: date
) -> dict[str, Any]:
    """Return the label of the 12 months that end on `end`, included.

    `start` and `end` are the days the label counts: the year, narrowed to the
    data. `days` tells a year that isn't whole. `estimated` gives the days whose
    electric heating comes from the Linky and the weather, before the heating
    tab's window. `unestimated` gives the Linky's days before that the label
    leaves out, for want of an outdoor temperature, and whether Open-Meteo is on.
    """
    start = day_start(_year_before(end) + timedelta(days=1))
    stop = day_start(end + timedelta(days=1))
    first, last = heating_window(entry, start, stop)
    first = min(await _async_main_start(entry, first), max(first, last))
    settings = await async_load_settings(hass, entry.entry_id)
    answer = await async_heating_between(
        hass, entry=entry, start=first, end=max(first, last), weather_days=True
    )
    # Before the window, the Linky's days, when the heating is electric.
    coordinator = entry.runtime_data
    begin = first
    unestimated = None
    if coordinator.statistic_id and not answer["gas"]:
        linky = max(start, day_start(coordinator.data.sources.first_day))
        if linky < first and (
            before := await _async_linky_heating(hass, entry, linky, first)
        ):
            answer["before"] = before
            begin = day_start(date.fromisoformat(before["start"]))
        if linky < begin:
            unestimated = {
                "start": _local_day(linky).isoformat(),
                "end": (_local_day(begin) - timedelta(days=1)).isoformat(),
                "open_meteo": bool(entry.options.get(CONF_WEATHER)),
            }
    end_at = max(first, last)
    days = (_local_day(end_at) - _local_day(begin)).days if end_at > begin else 0
    before = answer.get("before")
    return {
        "settings": settings,
        "defaults": DEFAULTS,
        "start": _local_day(begin).isoformat(),
        "end": (_local_day(end_at) - timedelta(days=1)).isoformat() if days else None,
        "days": days,
        "estimated": (
            {
                "start": before["start"],
                "end": before["end"],
                "heating": round(before["heating"], 1),
            }
            if before
            else None
        ),
        "unestimated": unestimated,
        **dpe_label(answer, settings),
    }
