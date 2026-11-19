"""An energy label in the style of the French DPE, from what the home used.

The label counts the heating, the hot water and the auxiliaries (ventilation,
pumps) of the 12 months that end on a day, divided by the living area. The
auxiliaries are always a share of the three; the hot water is one only when it
is neither measured nor estimated.
"""

from datetime import date, datetime, timedelta
from typing import Any

import probatio as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .comparison import day_start
from .const import DOMAIN, FRANCE_TIME_ZONE
from .coordinator import ElectricityContractsConfigEntry
from .heating import async_heating, heating_window

STORE_VERSION = 1

SURFACE = "surface"
COEFFICIENT = "coefficient"
AUXILIARIES = "auxiliaries"
WATER = "water"

# The living area in m², the primary energy of a kWh of electricity (1.9 from
# 1 January 2026), and the shares in % of the three uses.
DEFAULTS: dict[str, float] = {
    SURFACE: 100.0,
    COEFFICIENT: 1.9,
    AUXILIARIES: 5.0,
    WATER: 15.0,
}
# The shares can't take all of the three uses: 30 + 60 leaves the heating 10 %.
SETTINGS_SCHEMA: dict[Any, Any] = {
    vol.Required(SURFACE): vol.All(vol.Coerce(float), vol.Range(min=5, max=2000)),
    vol.Required(COEFFICIENT): vol.All(vol.Coerce(float), vol.Range(min=1, max=3)),
    vol.Required(AUXILIARIES): vol.All(vol.Coerce(float), vol.Range(min=0, max=30)),
    vol.Required(WATER): vol.All(vol.Coerce(float), vol.Range(min=0, max=60)),
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


def _uses(answer: dict[str, Any], settings: dict[str, float]) -> list[dict[str, Any]]:
    """Return the kWh of the heating, the hot water and the auxiliaries.

    Each with its energy (gas or not) and where it comes from: measured,
    estimated (by the Heating tab) or share (a setting). Empty without heating.
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
    if heat <= 0:
        return []
    if answer["water_split"]:
        water = answer["totals"]["water"]
        water_gas = bool(answer["water_gas"])
        water_source = "measured" if answer["water_measured"] else "estimated"
        total = (heat + water) / (1 - auxiliaries)
    elif answer["measured"] and answer["with_water"]:
        # The hot water is in the heating statistics, but can't be told apart.
        total = heat / (1 - auxiliaries)
        water = total * water_share
        heat -= water
        water_gas, water_source = gas, "share"
    else:
        # The hot water is elsewhere, unmeasured: an electric water heater.
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

    `classes` is None when there is no heating to count.
    """
    rows = []
    for item in _uses(answer, settings):
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
    if not rows:
        return {"classes": None, "uses": []}
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
    }


def _local_day(moment: datetime) -> date:
    return moment.astimezone(FRANCE_TIME_ZONE).date()


async def async_dpe(
    hass: HomeAssistant, *, entry: ElectricityContractsConfigEntry, end: date
) -> dict[str, Any]:
    """Return the label of the 12 months that end on `end`, included.

    `start` and `end` are the days the label counts: the year, narrowed to the
    data. `days` tells a year that isn't whole.
    """
    start = day_start(_year_before(end) + timedelta(days=1))
    stop = day_start(end + timedelta(days=1))
    first, last = heating_window(entry, start, stop)
    settings = await async_load_settings(hass, entry.entry_id)
    answer = await async_heating(hass, entry=entry, start=start, end=stop)
    days = (_local_day(last) - _local_day(first)).days if last > first else 0
    return {
        "settings": settings,
        "defaults": DEFAULTS,
        "start": _local_day(first).isoformat(),
        "end": (_local_day(last) - timedelta(days=1)).isoformat() if days else None,
        "days": days,
        **dpe_label(answer, settings),
    }
