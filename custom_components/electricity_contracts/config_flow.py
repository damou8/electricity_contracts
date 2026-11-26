"""Config flow for Electricity Contracts."""

import logging
import secrets
from collections.abc import Callable, Coroutine
from datetime import date, timedelta
from typing import Any, override

import probatio as vol
from elec_tariffs import (
    TRANCHES,
    ContractKind,
    GasProfile,
    RteOfficialTempoClient,
    TempoAuthError,
    TempoError,
)
from homeassistant.components.recorder.models import StatisticMeanType
from homeassistant.components.recorder.statistics import (
    async_list_statistic_ids,
    get_last_statistics,
    get_metadata,
)
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import (
    SOURCE_USER,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_NAME, UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.selector import (
    BooleanSelector,
    DateSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    StatisticSelector,
    StatisticSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.util import dt as dt_util
from homeassistant.util.unit_conversion import EnergyConverter, TemperatureConverter

from .const import (
    CONF_ACTIVE_FROM,
    CONF_ACTIVE_TO,
    CONF_END,
    CONF_FIXED_PER_YEAR,
    CONF_HEATING_CONTENT,
    CONF_HEATING_ENERGY,
    CONF_HEATING_STATISTICS,
    CONF_INDOOR_TEMPERATURES,
    CONF_KIND,
    CONF_KVA,
    CONF_OFF_PEAK,
    CONF_PERIODS,
    CONF_PRICE,
    CONF_PRICE_ENTITY,
    CONF_PRICES,
    CONF_PRICING,
    CONF_PROFILE,
    CONF_RTE_CLIENT_ID,
    CONF_RTE_CLIENT_SECRET,
    CONF_START,
    CONF_STATISTIC_ID,
    CONF_TEMPERATURE,
    CONF_UID,
    CONF_WATER_ENERGY,
    CONF_WATER_STATISTIC,
    CONF_WEATHER,
    CONF_WEEKEND_OFF_PEAK,
    CONTENT_HEATING,
    CONTENT_HEATING_WATER,
    DEFAULT_KVA,
    DOMAIN,
    ENERGY_ELECTRICITY,
    ENERGY_GAS,
    NO_METER,
    NO_METER_TITLES,
    OFF_PEAK_OTHER,
    OFF_PEAK_PRESETS,
    OFFERED_KVA,
    PRICING_ENTITY,
    PRICING_MANUAL,
    PRICING_OFFICIAL,
    SECTION_ACTIVE,
    SECTION_HEATING,
    SECTION_WATER,
    SUBENTRY_CONTRACT,
    SUBENTRY_GAS_CONTRACT,
)
from .data import (
    contracts,
    format_time_range,
    gas_contracts,
    parse_time_range,
    periods_overlap,
)

_LOGGER = logging.getLogger(__name__)

# Rows at least 23 hours apart (a day, or a day when the clocks change).
_DAILY_SECONDS = 23 * 3600

# Left empty, the source has no meter: prices, Tempo and heating only.
STATISTIC_SCHEMA = vol.Schema({vol.Optional(CONF_STATISTIC_ID): StatisticSelector()})

ENERGY_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[ENERGY_ELECTRICITY, ENERGY_GAS],
        translation_key="energy",
        mode=SelectSelectorMode.LIST,
    )
)
TEMPERATURE_SELECTOR = EntitySelector(
    EntitySelectorConfig(
        domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.TEMPERATURE
    )
)
# The statistics of a sensor go by its entity ID.
OUTDOOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_TEMPERATURE): TEMPERATURE_SELECTOR,
        vol.Optional(CONF_WEATHER, default=False): BooleanSelector(),
    }
)
INDOOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_INDOOR_TEMPERATURES): EntitySelector(
            EntitySelectorConfig(
                domain=SENSOR_DOMAIN,
                device_class=SensorDeviceClass.TEMPERATURE,
                multiple=True,
            )
        ),
    }
)
HEATING_SCHEMA = vol.Schema(
    {
        vol.Required(SECTION_HEATING): section(
            vol.Schema(
                {
                    vol.Optional(CONF_HEATING_STATISTICS): StatisticSelector(
                        StatisticSelectorConfig(multiple=True)
                    ),
                    vol.Optional(
                        CONF_HEATING_ENERGY, default=ENERGY_ELECTRICITY
                    ): ENERGY_SELECTOR,
                    vol.Optional(
                        CONF_HEATING_CONTENT, default=CONTENT_HEATING
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[CONTENT_HEATING, CONTENT_HEATING_WATER],
                            translation_key=CONF_HEATING_CONTENT,
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            {"collapsed": False},
        ),
        vol.Required(SECTION_WATER): section(
            vol.Schema(
                {
                    vol.Optional(CONF_WATER_STATISTIC): StatisticSelector(),
                    vol.Optional(
                        CONF_WATER_ENERGY, default=ENERGY_ELECTRICITY
                    ): ENERGY_SELECTOR,
                }
            ),
            {"collapsed": False},
        ),
    }
)
RTE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_RTE_CLIENT_ID): TextSelector(),
        vol.Optional(CONF_RTE_CLIENT_SECRET): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
    }
)
_HEATING_KEYS = (CONF_HEATING_STATISTICS, CONF_HEATING_ENERGY, CONF_HEATING_CONTENT)
_WATER_KEYS = (CONF_WATER_STATISTIC, CONF_WATER_ENERGY)

KIND_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[kind.value for kind in ContractKind],
        translation_key=CONF_KIND,
        mode=SelectSelectorMode.LIST,
    )
)
PRICING_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[PRICING_OFFICIAL, PRICING_MANUAL, PRICING_ENTITY],
        translation_key=CONF_PRICING,
        mode=SelectSelectorMode.LIST,
    )
)
GAS_PRICING_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[PRICING_OFFICIAL, PRICING_MANUAL, PRICING_ENTITY],
        translation_key="gas_pricing",
        mode=SelectSelectorMode.LIST,
    )
)
PROFILE_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[GasProfile.HEATING.value, GasProfile.COOKING_WATER.value],
        translation_key=CONF_PROFILE,
        mode=SelectSelectorMode.LIST,
    )
)
PRICE_SELECTOR = NumberSelector(
    NumberSelectorConfig(
        min=0,
        max=10,
        step="any",
        unit_of_measurement="€/kWh",
        mode=NumberSelectorMode.BOX,
    )
)
FIXED_SELECTOR = NumberSelector(
    NumberSelectorConfig(
        min=0,
        max=10000,
        step=0.01,
        unit_of_measurement="€",
        mode=NumberSelectorMode.BOX,
    )
)
# Every power a regulated offer has; the kind of contract narrows it on saving.
KVA_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[
            SelectOptionDict(value=str(kva), label=f"{kva} kVA")
            for kva in sorted(
                {kva for powers in OFFERED_KVA.values() for kva in powers}
            )
        ],
        mode=SelectSelectorMode.DROPDOWN,
    )
)
OFF_PEAK_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[*OFF_PEAK_PRESETS, OFF_PEAK_OTHER],
        translation_key=CONF_OFF_PEAK,
        mode=SelectSelectorMode.DROPDOWN,
    )
)

# The name a new contract is given, in the server's language; users change it.
_KIND_NAMES: dict[str, dict[ContractKind, str]] = {
    "en": {
        ContractKind.BASE: "Base",
        ContractKind.HPHC: "Off-peak",
        ContractKind.TEMPO: "Tempo",
    },
    "fr": {
        ContractKind.BASE: "Base",
        ContractKind.HPHC: "Heures creuses",
        ContractKind.TEMPO: "Tempo",
    },
}
_MY_PRICES = {"en": "my prices", "fr": "mes prix"}
_SENSOR_PRICE = {"en": "sensor price", "fr": "prix d'un capteur"}
_GAS = {"en": "Gas", "fr": "Gaz"}
_PROFILE_NAMES: dict[str, dict[GasProfile, str]] = {
    "en": {
        GasProfile.HEATING: "reference price, heating",
        GasProfile.COOKING_WATER: "reference price, cooking and hot water",
    },
    "fr": {
        GasProfile.HEATING: "prix repère chauffage",
        GasProfile.COOKING_WATER: "prix repère cuisson et eau chaude",
    },
}
# The labels of a contract's menu, which lists its price periods: Home Assistant
# shows a menu's labels as given, in the server's language.
_MENU: dict[str, dict[str, str]] = {
    "en": {
        "contract": "The contract: name, prices, off-peak hours and dates",
        "gas_contract": "The contract: name, prices and dates",
        "since": "Prices since {start}",
        "between": "Prices from {start} to {end}",
        "add_period": "Add a price period",
        "remove_period": "Remove a price period",
    },
    "fr": {
        "contract": "Le contrat : nom, prix, heures creuses et dates",
        "gas_contract": "Le contrat : nom, prix et dates",
        "since": "Prix depuis le {start}",
        "between": "Prix du {start} au {end}",
        "add_period": "Ajouter une période de prix",
        "remove_period": "Supprimer une période de prix",
    },
}
_MONTHS = {
    "en": [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ],
    "fr": [
        "janvier",
        "février",
        "mars",
        "avril",
        "mai",
        "juin",
        "juillet",
        "août",
        "septembre",
        "octobre",
        "novembre",
        "décembre",
    ],
}
_PERIOD_STEP = "period_"
# The field of the period to remove.
_REMOVED = "period"


def _language(hass: HomeAssistant) -> str:
    language = hass.config.language.split("-")[0]
    return language if language in _MENU else "en"


def day_label(day: date, language: str) -> str:
    """Write a day in words, like "1er août 2026" or "1 August 2026"."""
    months = _MONTHS.get(language, _MONTHS["en"])
    number = "1er" if language == "fr" and day.day == 1 else str(day.day)
    return f"{number} {months[day.month - 1]} {day.year}"


def period_label(period: dict[str, Any], language: str) -> str:
    """Name a price period by its days."""
    texts = _MENU.get(language, _MENU["en"])
    start = day_label(date.fromisoformat(period[CONF_START]), language)
    if not period.get(CONF_END):
        return texts["since"].format(start=start)
    end = day_label(date.fromisoformat(period[CONF_END]), language)
    return texts["between"].format(start=start, end=end)


class InvalidStatisticError(Exception):
    """The chosen statistic can't be used as a consumption source."""

    def __init__(self, reason: str) -> None:
        """Keep the translation key of the reason."""
        super().__init__(reason)
        self.reason = reason


async def async_validate_statistic(
    hass: HomeAssistant, statistic_id: str, *, daily: bool = False
) -> str:
    """Check that a statistic is an energy total with data; return its name.

    Only daily values are refused unless `daily` is true. Raise
    InvalidStatisticError otherwise.
    """
    recorder = get_instance(hass)
    metadata = await recorder.async_add_executor_job(
        lambda: get_metadata(hass, statistic_ids={statistic_id})
    )
    if statistic_id not in metadata:
        raise InvalidStatisticError(reason="statistic_not_found")
    _, meta = metadata[statistic_id]
    if meta["unit_of_measurement"] not in EnergyConverter.VALID_UNITS:
        raise InvalidStatisticError(reason="statistic_not_energy")
    if not meta["has_sum"]:
        raise InvalidStatisticError(reason="statistic_no_sum")
    last = await recorder.async_add_executor_job(
        lambda: get_last_statistics(
            hass, 2, statistic_id, convert_units=False, types={"sum"}
        )
    )
    rows = last.get(statistic_id)
    if not rows:
        raise InvalidStatisticError(reason="statistic_no_data")
    if (
        not daily
        and len(rows) == 2  # noqa: PLR2004
        and rows[0]["start"] - rows[1]["start"] >= _DAILY_SECONDS
    ):
        # Only daily values: they can't be split between off-peak and peak hours.
        raise InvalidStatisticError(reason="statistic_daily")
    return meta["name"] or statistic_id


async def async_validate_temperature(hass: HomeAssistant, statistic_id: str) -> None:
    """Check that a statistic is a temperature with a mean.

    Raise InvalidStatisticError otherwise.
    """
    metadata = await get_instance(hass).async_add_executor_job(
        lambda: get_metadata(hass, statistic_ids={statistic_id})
    )
    if statistic_id not in metadata:
        raise InvalidStatisticError(reason="statistic_not_found")
    _, meta = metadata[statistic_id]
    if meta["unit_of_measurement"] not in TemperatureConverter.VALID_UNITS:
        raise InvalidStatisticError(reason="statistic_not_temperature")
    if meta["mean_type"] != StatisticMeanType.ARITHMETIC:
        raise InvalidStatisticError(reason="statistic_no_mean")


_PRICE_UNITS = {
    f"{currency}/{UnitOfEnergy.KILO_WATT_HOUR}" for currency in ("€", "EUR")
}


async def async_validate_price_entity(hass: HomeAssistant, entity_id: str) -> None:
    """Check that a sensor gives a price of a kWh, with an hourly mean.

    Raise InvalidStatisticError otherwise.
    """
    metadata = await get_instance(hass).async_add_executor_job(
        lambda: get_metadata(hass, statistic_ids={entity_id})
    )
    if entity_id not in metadata:
        raise InvalidStatisticError(reason="price_entity_not_found")
    _, meta = metadata[entity_id]
    # The costs are in euros: a price in cents would make them 100 times too high.
    if meta["unit_of_measurement"] not in _PRICE_UNITS:
        raise InvalidStatisticError(reason="price_entity_not_per_kwh")
    if meta["mean_type"] != StatisticMeanType.ARITHMETIC:
        raise InvalidStatisticError(reason="price_entity_no_mean")


async def async_energy_statistics(
    hass: HomeAssistant, *, configured: set[str | None]
) -> list[str]:
    """Return the energy totals that could be costed, the most likely first.

    Linky statistics come first, then the others; those already configured come
    last. The integration's own statistics are left out.
    """
    found = await async_list_statistic_ids(hass, statistic_type="sum")
    ids = [
        item["statistic_id"]
        for item in found
        if item["source"] != DOMAIN
        and item["statistics_unit_of_measurement"] in EnergyConverter.VALID_UNITS
    ]
    return sorted(
        ids,
        key=lambda statistic_id: (
            statistic_id in configured,
            not statistic_id.startswith("linky:"),
            statistic_id,
        ),
    )


class ElectricityContractsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a consumption source."""

    VERSION = 1
    # 2: comparisons moved from subentries to the Contracts page.
    # 3: price periods and gas prices moved into their contracts; the indoor
    # thermometers out of the heating options.
    MINOR_VERSION = 3

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the hourly energy statistic to cost, or none."""
        errors: dict[str, str] = {}
        if user_input is not None:
            statistic_id = user_input.get(CONF_STATISTIC_ID)
            await self.async_set_unique_id(statistic_id or NO_METER)
            self._abort_if_unique_id_configured()
            if not statistic_id:
                return self.async_create_entry(title=self._no_meter_title(), data={})
            try:
                title = await async_validate_statistic(self.hass, statistic_id)
            except InvalidStatisticError as err:
                errors[CONF_STATISTIC_ID] = err.reason
            else:
                return self.async_create_entry(
                    title=title, data={CONF_STATISTIC_ID: statistic_id}
                )
        configured = set(self._async_current_ids())
        candidates = await async_energy_statistics(self.hass, configured=configured)
        # Only a Linky meter not set up yet is suggested: anything else is more
        # likely gas, or no meter at all.
        suggested = (
            {CONF_STATISTIC_ID: candidates[0]}
            if candidates
            and candidates[0].startswith("linky:")
            and candidates[0] not in configured
            else {}
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STATISTIC_SCHEMA, user_input or suggested
            ),
            errors=errors,
        )

    def _no_meter_title(self) -> str:
        language = self.hass.config.language.split("-")[0]
        return NO_METER_TITLES.get(language, NO_METER_TITLES["en"])

    async def _async_title_is_ours(self, entry: ConfigEntry) -> bool:
        """Tell whether an entry's title is the one the integration gave it.

        That is the name of its statistic, or the title of an entry without a
        meter. A title that holds the statistic's meter number counts too.
        """
        title = entry.title
        statistic_id = entry.data.get(CONF_STATISTIC_ID)
        if not statistic_id:
            return title in NO_METER_TITLES.values()
        if statistic_id.split(":", 1)[-1] in title:
            return True
        metadata = await get_instance(self.hass).async_add_executor_job(
            lambda: get_metadata(self.hass, statistic_ids={statistic_id})
        )
        name = metadata[statistic_id][1]["name"] if statistic_id in metadata else None
        return title == (name or statistic_id)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Use another statistic, for example after a meter change, or none."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            statistic_id = user_input.get(CONF_STATISTIC_ID)
            unique_id = statistic_id or NO_METER
            if unique_id != entry.unique_id:
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
            try:
                title = (
                    await async_validate_statistic(self.hass, statistic_id)
                    if statistic_id
                    else self._no_meter_title()
                )
            except InvalidStatisticError as err:
                errors[CONF_STATISTIC_ID] = err.reason
            else:
                # A title the integration gave follows the source: the former
                # one named the meter, with its PRM. One of your own stays.
                moved = unique_id != entry.unique_id
                if not moved or not await self._async_title_is_ours(entry):
                    title = entry.title
                # The update listener reloads the entry.
                return self.async_update_and_abort(
                    entry,
                    unique_id=unique_id,
                    title=title,
                    data={CONF_STATISTIC_ID: statistic_id} if statistic_id else {},
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STATISTIC_SCHEMA, user_input or entry.data
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return ElectricityContractsOptionsFlow()

    @classmethod
    @callback
    @override
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return the kinds of items users add under a source."""
        return {
            SUBENTRY_CONTRACT: ContractSubentryFlow,
            SUBENTRY_GAS_CONTRACT: GasContractSubentryFlow,
        }


class ElectricityContractsOptionsFlow(OptionsFlow):
    """Set the temperatures, the heating and the RTE credentials, one page each.

    All are optional. Each page keeps the options of the others.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose what to set."""
        del user_input
        return self.async_show_menu(
            step_id="init", menu_options=["outdoor", "indoor", "heating", "rte"]
        )

    def _save(
        self, changes: dict[str, Any], removed: tuple[str, ...]
    ) -> ConfigFlowResult:
        options = {
            key: value
            for key, value in self.config_entry.options.items()
            if key not in removed
        }
        options.update(changes)
        return self.async_create_entry(data=options)

    async def async_step_outdoor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the outdoor thermometer, and Open-Meteo."""
        errors: dict[str, str] = {}
        if user_input is not None:
            changes: dict[str, Any] = {}
            if temperature := user_input.get(CONF_TEMPERATURE):
                try:
                    await async_validate_temperature(self.hass, temperature)
                except InvalidStatisticError as err:
                    errors[CONF_TEMPERATURE] = err.reason
                changes[CONF_TEMPERATURE] = temperature
            if user_input.get(CONF_WEATHER):
                changes[CONF_WEATHER] = True
            if not errors:
                return self._save(changes, (CONF_TEMPERATURE, CONF_WEATHER))
        current = self.config_entry.options
        return self.async_show_form(
            step_id="outdoor",
            data_schema=self.add_suggested_values_to_schema(
                OUTDOOR_SCHEMA,
                user_input
                or {
                    key: current[key]
                    for key in (CONF_TEMPERATURE, CONF_WEATHER)
                    if current.get(key)
                },
            ),
            errors=errors,
        )

    async def async_step_indoor(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the indoor thermometers."""
        errors: dict[str, str] = {}
        if user_input is not None:
            indoor: list[str] = list(user_input.get(CONF_INDOOR_TEMPERATURES) or [])
            for entity_id in indoor:
                try:
                    await async_validate_temperature(self.hass, entity_id)
                except InvalidStatisticError as err:
                    errors[CONF_INDOOR_TEMPERATURES] = f"indoor_{err.reason}"
                    break
            if not errors:
                return self._save(
                    {CONF_INDOOR_TEMPERATURES: indoor} if indoor else {},
                    (CONF_INDOOR_TEMPERATURES,),
                )
        current = self.config_entry.options.get(CONF_INDOOR_TEMPERATURES)
        return self.async_show_form(
            step_id="indoor",
            data_schema=self.add_suggested_values_to_schema(
                INDOOR_SCHEMA,
                user_input or ({CONF_INDOOR_TEMPERATURES: current} if current else {}),
            ),
            errors=errors,
        )

    async def async_step_heating(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the statistics of the heating and of the hot water."""
        errors: dict[str, str] = {}
        if user_input is not None:
            heating = await self._validate_heating(
                {
                    **user_input.get(SECTION_HEATING, {}),
                    **user_input.get(SECTION_WATER, {}),
                },
                errors,
            )
            if not errors:
                return self._save(
                    {SECTION_HEATING: heating} if heating else {}, (SECTION_HEATING,)
                )
        current = self.config_entry.options.get(SECTION_HEATING) or {}
        suggested = {
            SECTION_HEATING: {
                key: current[key] for key in _HEATING_KEYS if key in current
            },
            SECTION_WATER: {key: current[key] for key in _WATER_KEYS if key in current},
        }
        return self.async_show_form(
            step_id="heating",
            data_schema=self.add_suggested_values_to_schema(
                HEATING_SCHEMA, user_input or suggested
            ),
            errors=errors,
        )

    async def async_step_rte(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Enter the credentials of RTE's official API, or clear them."""
        errors: dict[str, str] = {}
        keys = (CONF_RTE_CLIENT_ID, CONF_RTE_CLIENT_SECRET)
        if user_input is not None:
            client_id = user_input.get(CONF_RTE_CLIENT_ID, "").strip()
            client_secret = user_input.get(CONF_RTE_CLIENT_SECRET, "").strip()
            if not client_id and not client_secret:
                return self._save({}, keys)
            if error := await self._check_credentials(client_id, client_secret):
                errors["base"] = error
            else:
                return self._save(
                    {
                        CONF_RTE_CLIENT_ID: client_id,
                        CONF_RTE_CLIENT_SECRET: client_secret,
                    },
                    keys,
                )
        current = self.config_entry.options
        return self.async_show_form(
            step_id="rte",
            data_schema=self.add_suggested_values_to_schema(
                RTE_SCHEMA,
                user_input or {key: current[key] for key in keys if current.get(key)},
            ),
            errors=errors,
        )

    async def _validate_heating(
        self, heating: dict[str, Any], errors: dict[str, str]
    ) -> dict[str, Any]:
        """Check the heating page; return what to keep of it.

        Its statistics may hold daily values: those days are only counted in kWh.
        Errors go to the whole form: the frontend doesn't show those of a field
        inside a section.
        """
        statistics = list(dict.fromkeys(heating.get(CONF_HEATING_STATISTICS) or []))
        water: str | None = heating.get(CONF_WATER_STATISTIC) or None
        energy = heating.get(CONF_HEATING_ENERGY, ENERGY_ELECTRICITY)
        content = heating.get(CONF_HEATING_CONTENT, CONTENT_HEATING)
        water_energy = heating.get(CONF_WATER_ENERGY, ENERGY_ELECTRICITY)
        if error := await self._energy_error(statistics):
            errors["base"] = f"heating_{error}"
        if water and water in statistics:
            errors["base"] = "water_in_heating"
        elif water and (error := await self._energy_error([water])):
            errors["base"] = f"water_{error}"
        elif (
            water
            and statistics
            and content == CONTENT_HEATING_WATER
            and water_energy != energy
        ):
            # The heating statistics would hold hot water of another energy.
            errors["base"] = "water_other_energy"
        kept: dict[str, Any] = {}
        if statistics:
            kept[CONF_HEATING_STATISTICS] = statistics
            kept[CONF_HEATING_ENERGY] = energy
            kept[CONF_HEATING_CONTENT] = content
        if water:
            kept[CONF_WATER_STATISTIC] = water
            kept[CONF_WATER_ENERGY] = water_energy
        return kept

    async def _energy_error(self, statistic_ids: list[str]) -> str | None:
        """Return why one of the statistics can't be used, None if all can."""
        for statistic_id in statistic_ids:
            if statistic_id == self.config_entry.data.get(CONF_STATISTIC_ID):
                return "is_source"
            try:
                await async_validate_statistic(self.hass, statistic_id, daily=True)
            except InvalidStatisticError as err:
                return err.reason
        return None

    async def _check_credentials(
        self, client_id: str, client_secret: str
    ) -> str | None:
        """Return why RTE refuses the credentials, None if it accepts them."""
        if not client_id or not client_secret:
            return "incomplete_credentials"
        client = RteOfficialTempoClient(
            async_get_clientsession(self.hass), client_id, client_secret
        )
        try:
            await client.async_check_credentials()
        except TempoAuthError:
            return "invalid_auth"
        except TempoError:
            return "cannot_connect"
        return None


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


type _Step = Callable[[dict[str, Any] | None], Coroutine[Any, Any, SubentryFlowResult]]


class _PricedSubentryFlow(ConfigSubentryFlow):
    """What electricity and gas contracts share: a name, dates and prices.

    Adding one asks what it is, then its name and its days, then its first
    prices when they are entered by hand, or its sensor. Its pencil opens a menu
    when its prices are entered by hand: the contract itself, each price
    period, and adding or removing one.
    """

    _SUBENTRY_TYPE: str
    _KEYS: tuple[str, ...]

    def __init__(self) -> None:
        """Start with an empty contract."""
        self._title = ""
        self._data: dict[str, Any] = {}
        self._index: int | None = None

    def _others(self) -> list[tuple[str, str, date | None, date | None]]:
        """Return the uid, name and dates of the other contracts of this kind."""
        raise NotImplementedError

    def _default_name(self) -> str:
        raise NotImplementedError

    async def async_step_contract(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Change what the contract is: where its prices come from."""
        raise NotImplementedError

    def _price_fields(self) -> dict[vol.Marker, Any]:
        """Return the fields of the prices of a kWh of a period."""
        raise NotImplementedError

    def _read_prices(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Return the prices of a kWh of a period, as kept in the subentry."""
        raise NotImplementedError

    def _suggested_prices(self, period: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @property
    def _menu_contract(self) -> str:
        return "contract"

    @property
    def _periods(self) -> list[dict[str, Any]]:
        periods: list[dict[str, Any]] = self._data.setdefault(CONF_PERIODS, [])
        return periods

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Open the menu of a contract priced by hand, else the contract itself."""
        del user_input
        subentry = self._get_reconfigure_subentry()
        self._title = subentry.title
        self._data = {
            **subentry.data,
            CONF_PERIODS: [dict(item) for item in subentry.data.get(CONF_PERIODS, [])],
        }
        if self._data[CONF_PRICING] != PRICING_MANUAL:
            return await self.async_step_contract()
        language = _language(self.hass)
        texts = _MENU[language]
        options = {"contract": texts[self._menu_contract]}
        ordered = sorted(
            range(len(self._periods)), key=lambda i: self._periods[i][CONF_START]
        )
        for index in ordered:
            options[f"{_PERIOD_STEP}{index}"] = period_label(
                self._periods[index], language
            )
        options["add_period"] = texts["add_period"]
        if len(self._periods) > 1:
            options["remove_period"] = texts["remove_period"]
        return self.async_show_menu(
            step_id="reconfigure",
            menu_options=options,
            description_placeholders={"name": self._title},
        )

    def __getattr__(self, name: str) -> _Step:
        """Open price period n from the menu: its step is "period_n"."""
        prefix = f"async_step_{_PERIOD_STEP}"
        if name.startswith(prefix) and name[len(prefix) :].isdigit():
            index = int(name[len(prefix) :])

            # The menu only offers the periods there are.
            async def step(
                user_input: dict[str, Any] | None = None,
            ) -> SubentryFlowResult:
                del user_input
                self._index = index
                return await self.async_step_period()

            return step
        raise AttributeError(name)

    async def async_step_add_period(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add prices that start on a given day."""
        del user_input
        self._index = None
        return await self.async_step_period()

    async def async_step_remove_period(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Remove one price period."""
        language = _language(self.hass)
        if user_input is not None:
            del self._periods[int(user_input[_REMOVED])]
            return self._async_save()
        return self.async_show_form(
            step_id="remove_period",
            data_schema=vol.Schema(
                {
                    vol.Required(_REMOVED): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(
                                    value=str(index),
                                    label=period_label(period, language),
                                )
                                for index, period in sorted(
                                    enumerate(self._periods),
                                    key=lambda item: item[1][CONF_START],
                                )
                            ],
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
            description_placeholders={"name": self._title},
        )

    async def async_step_first_period(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Enter the first prices of a new contract.

        Its own step, so that its text can tell how to add prices later.
        """
        return await self._async_period_form("first_period", user_input)

    async def async_step_period(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Enter the days and the prices of a period, from the menu."""
        return await self._async_period_form("period", user_input)

    async def _async_period_form(
        self, step_id: str, user_input: dict[str, Any] | None
    ) -> SubentryFlowResult:
        """Enter the days and the prices of a period."""
        errors: dict[str, str] = {}
        if user_input is not None:
            start = date.fromisoformat(user_input[CONF_START])
            end = _date(user_input.get(CONF_END))
            closed = self._closed_before(start) if self._index is None else None
            if end and end < start:
                errors[CONF_END] = "end_before_start"
            elif any(
                periods_overlap(
                    (start, end),
                    (
                        date.fromisoformat(other[CONF_START]),
                        _date(other.get(CONF_END)),
                    ),
                )
                for index, other in enumerate(self._periods)
                if index not in (self._index, closed)
            ):
                errors["base"] = "overlapping_price_period"
            else:
                if closed is not None:
                    # The prices in force until now end the day before.
                    self._periods[closed][CONF_END] = (
                        start - timedelta(days=1)
                    ).isoformat()
                period = {
                    CONF_START: start.isoformat(),
                    CONF_END: end.isoformat() if end else None,
                    CONF_FIXED_PER_YEAR: float(user_input[CONF_FIXED_PER_YEAR]),
                    **self._read_prices(user_input),
                }
                if self._index is None:
                    self._periods.append(period)
                else:
                    self._periods[self._index] = period
                return self._async_save()
        schema = vol.Schema(
            {
                vol.Required(CONF_START): DateSelector(),
                vol.Optional(CONF_END): DateSelector(),
                vol.Required(CONF_FIXED_PER_YEAR): FIXED_SELECTOR,
                **self._price_fields(),
            }
        )
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or self._suggested_period()
            ),
            errors=errors,
            description_placeholders={"name": self._title},
        )

    def _closed_before(self, start: date) -> int | None:
        """Return the open period that new prices from `start` would end."""
        return next(
            (
                index
                for index, period in enumerate(self._periods)
                if not period.get(CONF_END)
                and date.fromisoformat(period[CONF_START]) < start
            ),
            None,
        )

    def _suggested_period(self) -> dict[str, Any]:
        if self._index is not None:
            period = self._periods[self._index]
            return {
                key: period[key]
                for key in (CONF_START, CONF_END, CONF_FIXED_PER_YEAR)
                if period.get(key) is not None
            } | self._suggested_prices(period)
        if not self._periods:
            # The first prices: from the first day of the contract.
            first = self._data.get(CONF_ACTIVE_FROM)
            return {CONF_START: first} if first else {}
        last = max(self._periods, key=lambda period: period[CONF_START])
        if last.get(CONF_END):
            following = date.fromisoformat(last[CONF_END]) + timedelta(days=1)
            return {CONF_START: following.isoformat()}
        # New prices end the open ones the day before: they start today at
        # the earliest, and never on the day the open ones start.
        following = date.fromisoformat(last[CONF_START]) + timedelta(days=1)
        return {CONF_START: max(dt_util.now().date(), following).isoformat()}

    async def async_step_price_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Choose the sensor of the price of a kWh, and enter the subscription."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await async_validate_price_entity(
                    self.hass, user_input[CONF_PRICE_ENTITY]
                )
            except InvalidStatisticError as err:
                errors[CONF_PRICE_ENTITY] = err.reason
            else:
                self._data[CONF_PRICE_ENTITY] = user_input[CONF_PRICE_ENTITY]
                self._data[CONF_FIXED_PER_YEAR] = float(user_input[CONF_FIXED_PER_YEAR])
                return self._async_save()
        schema = vol.Schema(
            {
                vol.Required(CONF_PRICE_ENTITY): EntitySelector(
                    EntitySelectorConfig(domain=SENSOR_DOMAIN)
                ),
                vol.Required(CONF_FIXED_PER_YEAR): FIXED_SELECTOR,
            }
        )
        return self.async_show_form(
            step_id="price_entity",
            data_schema=self.add_suggested_values_to_schema(
                schema,
                user_input
                or {
                    key: self._data[key]
                    for key in (CONF_PRICE_ENTITY, CONF_FIXED_PER_YEAR)
                    if key in self._data
                },
            ),
            errors=errors,
            description_placeholders={"name": self._title},
        )

    async def _async_after_details(self) -> SubentryFlowResult:
        """Ask for the first prices, or the sensor, before saving."""
        pricing = self._data[CONF_PRICING]
        if pricing == PRICING_MANUAL and not self._periods:
            self._index = None
            return await self.async_step_first_period()
        if pricing == PRICING_ENTITY:
            return await self.async_step_price_entity()
        return self._async_save()

    def _name_error(self) -> str | None:
        """Return why the name can't be used: the compare action selects by name."""
        if not self._title:
            return "empty_name"
        name = self._title.casefold()
        if any(
            other_name.casefold() == name and uid != self._data[CONF_UID]
            for uid, other_name, _, _ in self._others()
        ):
            return "duplicate_name"
        return None

    def _unique_name(self, name: str) -> str:
        taken = {other_name.casefold() for _, other_name, _, _ in self._others()}
        candidate = name
        number = 1
        while candidate.casefold() in taken:
            number += 1
            candidate = f"{name} {number}"
        return candidate

    def _active_period(
        self, values: dict[str, Any], errors: dict[str, str]
    ) -> dict[str, str | None]:
        """Read and check the days the contract was in force."""
        active_from = _date(values.get(CONF_ACTIVE_FROM))
        active_to = _date(values.get(CONF_ACTIVE_TO))
        if active_to and not active_from:
            errors[SECTION_ACTIVE] = "active_to_without_from"
        elif active_from and active_to and active_to < active_from:
            errors[SECTION_ACTIVE] = "end_before_start"
        elif self._overlaps_another_contract(active_from, active_to):
            errors[SECTION_ACTIVE] = "overlapping_active_period"
        return {
            CONF_ACTIVE_FROM: active_from.isoformat() if active_from else None,
            CONF_ACTIVE_TO: active_to.isoformat() if active_to else None,
        }

    def _overlaps_another_contract(
        self, active_from: date | None, active_to: date | None
    ) -> bool:
        if active_from is None:
            return False
        return any(
            periods_overlap((active_from, active_to), (other_from, other_to))
            for uid, _, other_from, other_to in self._others()
            if uid != self._data[CONF_UID] and other_from
        )

    @staticmethod
    def _active_section() -> section:
        return section(
            vol.Schema(
                {
                    vol.Optional(CONF_ACTIVE_FROM): DateSelector(),
                    vol.Optional(CONF_ACTIVE_TO): DateSelector(),
                }
            ),
            {"collapsed": False},
        )

    def _suggested_active(self) -> dict[str, Any]:
        return {
            key: self._data[key]
            for key in (CONF_ACTIVE_FROM, CONF_ACTIVE_TO)
            if self._data.get(key)
        }

    def _async_save(self) -> SubentryFlowResult:
        data = {key: self._data[key] for key in self._KEYS if key in self._data}
        pricing = data[CONF_PRICING]
        if pricing != PRICING_MANUAL:
            data.pop(CONF_PERIODS, None)
        else:
            data[CONF_PERIODS] = sorted(
                data.get(CONF_PERIODS, []), key=lambda period: period[CONF_START]
            )
        if pricing != PRICING_ENTITY:
            data.pop(CONF_PRICE_ENTITY, None)
            data.pop(CONF_FIXED_PER_YEAR, None)
        if self.source == SOURCE_USER:
            return self.async_create_entry(
                title=self._title, data=data, unique_id=data[CONF_UID]
            )
        return self.async_update_and_abort(
            self._get_entry(),
            self._get_reconfigure_subentry(),
            title=self._title,
            data=data,
        )

    def _new_uid(self) -> str:
        used = {uid for uid, _, _, _ in self._others()}
        while (uid := secrets.token_hex(4)) in used:
            continue  # pragma: no cover - a collision among 4 billion values
        return uid


class ContractSubentryFlow(_PricedSubentryFlow):
    """Add or change an electricity contract."""

    _SUBENTRY_TYPE = SUBENTRY_CONTRACT
    _KEYS = (
        CONF_UID,
        CONF_KIND,
        CONF_PRICING,
        CONF_KVA,
        CONF_OFF_PEAK,
        CONF_WEEKEND_OFF_PEAK,
        CONF_ACTIVE_FROM,
        CONF_ACTIVE_TO,
        CONF_PERIODS,
        CONF_PRICE_ENTITY,
        CONF_FIXED_PER_YEAR,
    )

    def _others(self) -> list[tuple[str, str, date | None, date | None]]:
        return [
            (contract.uid, contract.name, contract.active_from, contract.active_to)
            for contract in contracts(self._get_entry())
        ]

    @property
    def _kind(self) -> ContractKind:
        return ContractKind(self._data[CONF_KIND])

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Choose the kind of contract, where its prices come from and its power."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._data = {CONF_UID: self._new_uid()}
            if self._read_pricing(
                user_input, ContractKind(user_input[CONF_KIND]), errors
            ):
                return await self.async_step_details()
        schema = vol.Schema(
            {
                vol.Required(CONF_KIND): KIND_SELECTOR,
                vol.Required(CONF_PRICING, default=PRICING_OFFICIAL): PRICING_SELECTOR,
                vol.Required(CONF_KVA, default=str(DEFAULT_KVA)): KVA_SELECTOR,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    async def async_step_contract(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Change where the prices come from, or the power."""
        errors: dict[str, str] = {}
        if user_input is not None and self._read_pricing(
            user_input, self._kind, errors
        ):
            return await self.async_step_details()
        schema = vol.Schema(
            {
                vol.Required(CONF_PRICING): PRICING_SELECTOR,
                vol.Required(CONF_KVA): KVA_SELECTOR,
            }
        )
        suggested = user_input or {
            CONF_PRICING: self._data[CONF_PRICING],
            CONF_KVA: str(self._data.get(CONF_KVA, DEFAULT_KVA)),
        }
        return self.async_show_form(
            step_id="contract",
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
            errors=errors,
            description_placeholders={"name": self._title},
        )

    def _read_pricing(
        self, user_input: dict[str, Any], kind: ContractKind, errors: dict[str, str]
    ) -> bool:
        """Keep the kind, the pricing and the power regulated prices need."""
        official = user_input[CONF_PRICING] == PRICING_OFFICIAL
        kva = int(user_input[CONF_KVA])
        if official and kva not in OFFERED_KVA[kind]:
            errors[CONF_KVA] = "kva_not_offered"
            return False
        self._data[CONF_KIND] = kind.value
        self._data[CONF_PRICING] = user_input[CONF_PRICING]
        if official:
            self._data[CONF_KVA] = kva
        else:
            self._data.pop(CONF_KVA, None)
        return True

    async def async_step_details(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Name the contract; set its off-peak hours and when it was in force."""
        kind = self._kind
        errors: dict[str, str] = {}
        if user_input is not None:
            self._title = user_input[CONF_NAME].strip()
            if error := self._name_error():
                errors[CONF_NAME] = error
            period = self._active_period(user_input[SECTION_ACTIVE], errors)
            if not errors:
                self._data.update(period)
                if kind is ContractKind.HPHC:
                    self._data[CONF_WEEKEND_OFF_PEAK] = user_input[
                        CONF_WEEKEND_OFF_PEAK
                    ]
                    if user_input[CONF_OFF_PEAK] == OFF_PEAK_OTHER:
                        return await self.async_step_off_peak()
                    self._data[CONF_OFF_PEAK] = OFF_PEAK_PRESETS[
                        user_input[CONF_OFF_PEAK]
                    ]
                return await self._async_after_details()
        return self.async_show_form(
            step_id="details",
            data_schema=self.add_suggested_values_to_schema(
                self._details_schema(kind), user_input or self._suggested_details(kind)
            ),
            errors=errors,
        )

    async def async_step_off_peak(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Type in off-peak hours the list doesn't have."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                ranges = [
                    parse_time_range(text)
                    for text in user_input[CONF_OFF_PEAK]
                    if text.strip()
                ]
            except ValueError:
                ranges = []
            if ranges:
                self._data[CONF_OFF_PEAK] = [format_time_range(item) for item in ranges]
                return await self._async_after_details()
            errors[CONF_OFF_PEAK] = "invalid_off_peak"
        current = self._data.get(CONF_OFF_PEAK)
        typed = (
            current if current and current not in OFF_PEAK_PRESETS.values() else [""]
        )
        return self.async_show_form(
            step_id="off_peak",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_OFF_PEAK): TextSelector(
                            TextSelectorConfig(multiple=True)
                        )
                    }
                ),
                user_input or {CONF_OFF_PEAK: typed},
            ),
            errors=errors,
        )

    def _details_schema(self, kind: ContractKind) -> vol.Schema:
        fields: dict[vol.Marker, Any] = {
            # pylint: disable-next=home-assistant-config-flow-name-field
            vol.Required(CONF_NAME): str,
        }
        if kind is ContractKind.HPHC:
            fields[vol.Required(CONF_OFF_PEAK)] = OFF_PEAK_SELECTOR
            fields[vol.Required(CONF_WEEKEND_OFF_PEAK, default=False)] = (
                BooleanSelector()
            )
        fields[vol.Required(SECTION_ACTIVE)] = self._active_section()
        return vol.Schema(fields)

    def _suggested_details(self, kind: ContractKind) -> dict[str, Any]:
        """Suggest the current values, or a name and the usual off-peak hours."""
        suggested: dict[str, Any] = {
            CONF_NAME: self._title or self._default_name(),
            SECTION_ACTIVE: self._suggested_active(),
        }
        if kind is ContractKind.HPHC:
            ranges = self._data.get(CONF_OFF_PEAK, OFF_PEAK_PRESETS["22_06"])
            suggested[CONF_OFF_PEAK] = next(
                (key for key, preset in OFF_PEAK_PRESETS.items() if preset == ranges),
                OFF_PEAK_OTHER,
            )
            suggested[CONF_WEEKEND_OFF_PEAK] = self._data.get(
                CONF_WEEKEND_OFF_PEAK, False
            )
        return suggested

    def _default_name(self) -> str:
        """Name a new contract after its kind and power, unlike the others."""
        language = self.hass.config.language.split("-")[0]
        names = _KIND_NAMES.get(language, _KIND_NAMES["en"])
        kind = names[self._kind]
        if CONF_KVA in self._data:
            return self._unique_name(f"{kind} {self._data[CONF_KVA]} kVA")
        how = (
            _SENSOR_PRICE if self._data[CONF_PRICING] == PRICING_ENTITY else _MY_PRICES
        )
        return self._unique_name(f"{kind} · {how.get(language, how['en'])}")

    def _price_fields(self) -> dict[vol.Marker, Any]:
        return {
            vol.Required(tranche.value): PRICE_SELECTOR
            for tranche in TRANCHES[self._kind]
        }

    def _read_prices(self, user_input: dict[str, Any]) -> dict[str, Any]:
        return {
            CONF_PRICES: {
                tranche.value: float(user_input[tranche.value])
                for tranche in TRANCHES[self._kind]
            }
        }

    def _suggested_prices(self, period: dict[str, Any]) -> dict[str, Any]:
        return dict(period.get(CONF_PRICES, {}))


class GasContractSubentryFlow(_PricedSubentryFlow):
    """Add or change a gas contract: it gives the gas of the heating in euros."""

    _SUBENTRY_TYPE = SUBENTRY_GAS_CONTRACT
    _KEYS = (
        CONF_UID,
        CONF_PRICING,
        CONF_PROFILE,
        CONF_ACTIVE_FROM,
        CONF_ACTIVE_TO,
        CONF_PERIODS,
        CONF_PRICE_ENTITY,
        CONF_FIXED_PER_YEAR,
    )

    @property
    @override
    def _menu_contract(self) -> str:
        return "gas_contract"

    def _others(self) -> list[tuple[str, str, date | None, date | None]]:
        # A gas contract without a first day is always in force.
        return [
            (
                contract.uid,
                contract.name,
                contract.active_from or date.min,
                contract.active_to,
            )
            for contract in gas_contracts(self._get_entry())
        ]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Choose where the prices come from."""
        self._data = {CONF_UID: self._new_uid()}
        return await self.async_step_contract(user_input, step_id="user")

    async def async_step_contract(
        self, user_input: dict[str, Any] | None = None, *, step_id: str = "contract"
    ) -> SubentryFlowResult:
        """Choose where the prices come from, and the profile of the reference price."""
        if user_input is not None:
            self._data[CONF_PRICING] = user_input[CONF_PRICING]
            if user_input[CONF_PRICING] == PRICING_OFFICIAL:
                self._data[CONF_PROFILE] = user_input[CONF_PROFILE]
            else:
                self._data.pop(CONF_PROFILE, None)
            return await self.async_step_details()
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PRICING, default=PRICING_OFFICIAL
                ): GAS_PRICING_SELECTOR,
                vol.Required(
                    CONF_PROFILE, default=GasProfile.HEATING.value
                ): PROFILE_SELECTOR,
            }
        )
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(
                schema,
                {
                    key: self._data[key]
                    for key in (CONF_PRICING, CONF_PROFILE)
                    if key in self._data
                },
            ),
            description_placeholders={"name": self._title},
        )

    async def async_step_details(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Name the contract and set when it was in force."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._title = user_input[CONF_NAME].strip()
            if error := self._name_error():
                errors[CONF_NAME] = error
            period = self._active_period(user_input[SECTION_ACTIVE], errors)
            if not errors:
                self._data.update(period)
                return await self._async_after_details()
        schema = vol.Schema(
            {
                # pylint: disable-next=home-assistant-config-flow-name-field
                vol.Required(CONF_NAME): str,
                vol.Required(SECTION_ACTIVE): self._active_section(),
            }
        )
        return self.async_show_form(
            step_id="details",
            data_schema=self.add_suggested_values_to_schema(
                schema,
                user_input
                or {
                    CONF_NAME: self._title or self._default_name(),
                    SECTION_ACTIVE: self._suggested_active(),
                },
            ),
            errors=errors,
        )

    @override
    def _overlaps_another_contract(
        self, active_from: date | None, active_to: date | None
    ) -> bool:
        # Without a first day, the contract is in force since always.
        return super()._overlaps_another_contract(active_from or date.min, active_to)

    def _default_name(self) -> str:
        language = self.hass.config.language.split("-")[0]
        gas = _GAS.get(language, _GAS["en"])
        pricing = self._data[CONF_PRICING]
        if pricing == PRICING_OFFICIAL:
            names = _PROFILE_NAMES.get(language, _PROFILE_NAMES["en"])
            how = names[GasProfile(self._data[CONF_PROFILE])]
        else:
            texts = _SENSOR_PRICE if pricing == PRICING_ENTITY else _MY_PRICES
            how = texts.get(language, texts["en"])
        return self._unique_name(f"{gas} · {how}")

    def _price_fields(self) -> dict[vol.Marker, Any]:
        return {vol.Required(CONF_PRICE): PRICE_SELECTOR}

    def _read_prices(self, user_input: dict[str, Any]) -> dict[str, Any]:
        return {CONF_PRICE: float(user_input[CONF_PRICE])}

    def _suggested_prices(self, period: dict[str, Any]) -> dict[str, Any]:
        return {CONF_PRICE: period[CONF_PRICE]}
