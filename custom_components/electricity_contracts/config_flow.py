"""Config flow for Electricity Contracts."""

import logging
import secrets
from datetime import date
from typing import Any, override

import probatio as vol
from elec_tariffs import (
    TRANCHES,
    ContractKind,
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
from homeassistant.const import CONF_NAME
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
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.util.unit_conversion import EnergyConverter, TemperatureConverter

from .const import (
    CONF_ACTIVE_FROM,
    CONF_ACTIVE_TO,
    CONF_CONTRACT,
    CONF_END,
    CONF_FIXED_PER_YEAR,
    CONF_KIND,
    CONF_KVA,
    CONF_OFF_PEAK,
    CONF_PRICES,
    CONF_PRICING,
    CONF_RTE_CLIENT_ID,
    CONF_RTE_CLIENT_SECRET,
    CONF_START,
    CONF_STATISTIC_ID,
    CONF_TEMPERATURE,
    CONF_UID,
    CONF_WEEKEND_OFF_PEAK,
    DEFAULT_KVA,
    DOMAIN,
    OFF_PEAK_OTHER,
    OFF_PEAK_PRESETS,
    OFFERED_KVA,
    PRICING_MANUAL,
    PRICING_OFFICIAL,
    SECTION_ACTIVE,
    SECTION_RTE,
    SUBENTRY_CONTRACT,
    SUBENTRY_PRICE_PERIOD,
)
from .data import (
    Contract,
    contracts,
    format_time_range,
    manual_prices,
    parse_time_range,
    periods_overlap,
)

_LOGGER = logging.getLogger(__name__)

# Rows at least 23 hours apart (a day, or a day when the clocks change).
_DAILY_SECONDS = 23 * 3600

STATISTIC_SCHEMA = vol.Schema({vol.Required(CONF_STATISTIC_ID): StatisticSelector()})

OPTIONS_SCHEMA = vol.Schema(
    {
        # The statistics of a sensor go by its entity ID.
        vol.Optional(CONF_TEMPERATURE): EntitySelector(
            EntitySelectorConfig(
                domain=SENSOR_DOMAIN, device_class=SensorDeviceClass.TEMPERATURE
            )
        ),
        vol.Required(SECTION_RTE): section(
            vol.Schema(
                {
                    vol.Optional(CONF_RTE_CLIENT_ID): TextSelector(),
                    vol.Optional(CONF_RTE_CLIENT_SECRET): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                }
            ),
            {"collapsed": True},
        ),
    }
)

KIND_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[kind.value for kind in ContractKind],
        translation_key=CONF_KIND,
        mode=SelectSelectorMode.LIST,
    )
)
PRICING_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[PRICING_OFFICIAL, PRICING_MANUAL],
        translation_key=CONF_PRICING,
        mode=SelectSelectorMode.LIST,
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
_CONTRACT_KEYS = (
    CONF_UID,
    CONF_KIND,
    CONF_PRICING,
    CONF_KVA,
    CONF_OFF_PEAK,
    CONF_WEEKEND_OFF_PEAK,
    CONF_ACTIVE_FROM,
    CONF_ACTIVE_TO,
)


class InvalidStatisticError(Exception):
    """The chosen statistic can't be used as a consumption source."""

    def __init__(self, reason: str) -> None:
        """Keep the translation key of the reason."""
        super().__init__(reason)
        self.reason = reason


async def async_validate_statistic(hass: HomeAssistant, statistic_id: str) -> str:
    """Check that a statistic is an energy total with data; return its name.

    Raise InvalidStatisticError otherwise.
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
    if len(rows) == 2 and rows[0]["start"] - rows[1]["start"] >= _DAILY_SECONDS:  # noqa: PLR2004
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
    MINOR_VERSION = 2

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the hourly energy statistic to cost."""
        errors: dict[str, str] = {}
        candidates = await async_energy_statistics(
            self.hass, configured=set(self._async_current_ids())
        )
        if not candidates:
            return self.async_abort(reason="no_statistic")
        if user_input is not None:
            statistic_id = user_input[CONF_STATISTIC_ID]
            await self.async_set_unique_id(statistic_id)
            self._abort_if_unique_id_configured()
            try:
                title = await async_validate_statistic(self.hass, statistic_id)
            except InvalidStatisticError as err:
                errors[CONF_STATISTIC_ID] = err.reason
            else:
                return self.async_create_entry(
                    title=title, data={CONF_STATISTIC_ID: statistic_id}
                )
        # The frontend can't show a required statistic selector without a value.
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STATISTIC_SCHEMA, user_input or {CONF_STATISTIC_ID: candidates[0]}
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Use another statistic, for example after a meter change."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            statistic_id = user_input[CONF_STATISTIC_ID]
            if statistic_id != entry.unique_id:
                await self.async_set_unique_id(statistic_id)
                self._abort_if_unique_id_configured()
            try:
                await async_validate_statistic(self.hass, statistic_id)
            except InvalidStatisticError as err:
                errors[CONF_STATISTIC_ID] = err.reason
            else:
                # The update listener reloads the entry.
                return self.async_update_and_abort(
                    entry,
                    unique_id=statistic_id,
                    data={CONF_STATISTIC_ID: statistic_id},
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
            SUBENTRY_PRICE_PERIOD: PricePeriodSubentryFlow,
        }


class ElectricityContractsOptionsFlow(OptionsFlow):
    """Set the outdoor temperature and the RTE credentials, both optional."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Check the temperature and the credentials before saving them."""
        errors: dict[str, str] = {}
        if user_input is not None:
            options: dict[str, str] = {}
            if temperature := user_input.get(CONF_TEMPERATURE):
                try:
                    await async_validate_temperature(self.hass, temperature)
                except InvalidStatisticError as err:
                    errors[CONF_TEMPERATURE] = err.reason
                options[CONF_TEMPERATURE] = temperature
            rte = user_input.get(SECTION_RTE, {})
            client_id = rte.get(CONF_RTE_CLIENT_ID, "").strip()
            client_secret = rte.get(CONF_RTE_CLIENT_SECRET, "").strip()
            if (client_id or client_secret) and not errors:
                if error := await self._check_credentials(client_id, client_secret):
                    errors["base"] = error
                options[CONF_RTE_CLIENT_ID] = client_id
                options[CONF_RTE_CLIENT_SECRET] = client_secret
            if not errors:
                return self.async_create_entry(data=options)
        current = self.config_entry.options
        suggested: dict[str, Any] = {
            SECTION_RTE: {
                key: current[key]
                for key in (CONF_RTE_CLIENT_ID, CONF_RTE_CLIENT_SECRET)
                if current.get(key)
            }
        }
        if current.get(CONF_TEMPERATURE):
            suggested[CONF_TEMPERATURE] = current[CONF_TEMPERATURE]
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, user_input or suggested
            ),
            errors=errors,
        )

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


class ContractSubentryFlow(ConfigSubentryFlow):
    """Add or change a contract: what it is, then its name and its days."""

    def __init__(self) -> None:
        """Start with an empty contract."""
        self._title = ""
        self._data: dict[str, Any] = {}

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

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Change where the prices come from, or the power."""
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}
        if user_input is not None:
            self._title = subentry.title
            self._data = dict(subentry.data)
            kind = ContractKind(subentry.data[CONF_KIND])
            if self._read_pricing(user_input, kind, errors):
                return await self.async_step_details()
        schema = vol.Schema(
            {
                vol.Required(CONF_PRICING): PRICING_SELECTOR,
                vol.Required(CONF_KVA): KVA_SELECTOR,
            }
        )
        suggested = user_input or {
            CONF_PRICING: subentry.data[CONF_PRICING],
            CONF_KVA: str(subentry.data.get(CONF_KVA, DEFAULT_KVA)),
        }
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
            errors=errors,
            description_placeholders={"name": subentry.title},
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
        kind = ContractKind(self._data[CONF_KIND])
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
                return self._async_save()
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
                return self._async_save()
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

    @staticmethod
    def _details_schema(kind: ContractKind) -> vol.Schema:
        fields: dict[vol.Marker, Any] = {
            # pylint: disable-next=home-assistant-config-flow-name-field
            vol.Required(CONF_NAME): str,
        }
        if kind is ContractKind.HPHC:
            fields[vol.Required(CONF_OFF_PEAK)] = OFF_PEAK_SELECTOR
            fields[vol.Required(CONF_WEEKEND_OFF_PEAK, default=False)] = (
                BooleanSelector()
            )
        fields[vol.Required(SECTION_ACTIVE)] = section(
            vol.Schema(
                {
                    vol.Optional(CONF_ACTIVE_FROM): DateSelector(),
                    vol.Optional(CONF_ACTIVE_TO): DateSelector(),
                }
            ),
            {"collapsed": False},
        )
        return vol.Schema(fields)

    def _suggested_details(self, kind: ContractKind) -> dict[str, Any]:
        """Suggest the current values, or a name and the usual off-peak hours."""
        suggested: dict[str, Any] = {
            CONF_NAME: self._title or self._default_name(kind),
            SECTION_ACTIVE: {
                key: self._data[key]
                for key in (CONF_ACTIVE_FROM, CONF_ACTIVE_TO)
                if self._data.get(key)
            },
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

    def _default_name(self, kind: ContractKind) -> str:
        """Name a new contract after its kind and power, unlike the others."""
        language = self.hass.config.language.split("-")[0]
        names = _KIND_NAMES.get(language, _KIND_NAMES["en"])
        if CONF_KVA in self._data:
            name = f"{names[kind]} {self._data[CONF_KVA]} kVA"
        else:
            name = f"{names[kind]} · {_MY_PRICES.get(language, _MY_PRICES['en'])}"
        taken = {contract.name.casefold() for contract in contracts(self._get_entry())}
        candidate = name
        number = 1
        while candidate.casefold() in taken:
            number += 1
            candidate = f"{name} {number}"
        return candidate

    def _name_error(self) -> str | None:
        """Return why the name can't be used: the compare action selects by name."""
        if not self._title:
            return "empty_name"
        name = self._title.casefold()
        if any(
            contract.name.casefold() == name and contract.uid != self._data[CONF_UID]
            for contract in contracts(self._get_entry())
        ):
            return "duplicate_name"
        return None

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
        elif active_from and self._overlaps_another_contract(active_from, active_to):
            errors[SECTION_ACTIVE] = "overlapping_active_period"
        return {
            CONF_ACTIVE_FROM: active_from.isoformat() if active_from else None,
            CONF_ACTIVE_TO: active_to.isoformat() if active_to else None,
        }

    def _overlaps_another_contract(
        self, active_from: date, active_to: date | None
    ) -> bool:
        return any(
            periods_overlap(
                (active_from, active_to), (contract.active_from, contract.active_to)
            )
            for contract in contracts(self._get_entry())
            if contract.uid != self._data[CONF_UID] and contract.active_from
        )

    def _async_save(self) -> SubentryFlowResult:
        data = {key: self._data[key] for key in _CONTRACT_KEYS if key in self._data}
        if self.source == SOURCE_USER:
            # A contract priced by hand waits for its prices: say where they go.
            return self.async_create_entry(
                title=self._title,
                data=data,
                unique_id=data[CONF_UID],
                description=(
                    "add_prices" if data[CONF_PRICING] == PRICING_MANUAL else None
                ),
            )
        return self.async_update_and_abort(
            self._get_entry(),
            self._get_reconfigure_subentry(),
            title=self._title,
            data=data,
        )

    def _new_uid(self) -> str:
        used = {contract.uid for contract in contracts(self._get_entry())}
        while (uid := secrets.token_hex(4)) in used:
            continue  # pragma: no cover - a collision among 4 billion values
        return uid


class PricePeriodSubentryFlow(ConfigSubentryFlow):
    """Add or change the prices of a contract priced by hand."""

    def __init__(self) -> None:
        """Start without a contract."""
        self._contract: Contract | None = None
        self._period: dict[str, Any] = {}

    def _manual_contracts(self) -> dict[str, Contract]:
        return {
            contract.uid: contract
            for contract in contracts(self._get_entry())
            if not contract.official
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Choose the contract and the days the prices apply to."""
        manual = self._manual_contracts()
        if not manual:
            return self.async_abort(reason="no_manual_contracts")
        errors: dict[str, str] = {}
        if user_input is not None:
            self._contract = manual[user_input[CONF_CONTRACT]]
            if self._validate_period(user_input, errors, exclude=None):
                return await self.async_step_prices()
        schema = vol.Schema(
            {
                vol.Required(CONF_CONTRACT): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=uid, label=contract.name)
                            for uid, contract in manual.items()
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                **self._period_fields(),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Change the days or the prices of a period."""
        subentry = self._get_reconfigure_subentry()
        self._contract = self._manual_contracts().get(subentry.data[CONF_CONTRACT])
        if self._contract is None:
            return self.async_abort(reason="contract_not_found")
        errors: dict[str, str] = {}
        if user_input is not None and self._validate_period(
            user_input, errors, exclude=subentry.subentry_id
        ):
            return await self.async_step_prices()
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(self._period_fields()), user_input or subentry.data
            ),
            errors=errors,
            description_placeholders={"contract": self._contract.name},
        )

    async def async_step_prices(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Enter the price of each tranche."""
        assert self._contract is not None
        tranches = TRANCHES[self._contract.kind]
        if user_input is not None:
            start = self._period[CONF_START]
            end = self._period.get(CONF_END)
            data = {
                CONF_CONTRACT: self._contract.uid,
                CONF_START: start,
                CONF_END: end,
                CONF_FIXED_PER_YEAR: float(self._period[CONF_FIXED_PER_YEAR]),
                CONF_PRICES: {
                    tranche.value: float(user_input[tranche]) for tranche in tranches
                },
            }
            title = f"{self._contract.name} · {start} → {end or '…'}"
            if self.source == SOURCE_USER:
                return self.async_create_entry(title=title, data=data)
            subentry = self._get_reconfigure_subentry()
            return self.async_update_and_abort(
                self._get_entry(), subentry, title=title, data=data
            )
        price = NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=10,
                step="any",
                unit_of_measurement="€/kWh",
                mode=NumberSelectorMode.BOX,
            )
        )
        schema = vol.Schema(
            {vol.Required(tranche.value): price for tranche in tranches}
        )
        suggested: dict[str, Any] = {}
        if self.source != SOURCE_USER:
            suggested = dict(self._get_reconfigure_subentry().data[CONF_PRICES])
        return self.async_show_form(
            step_id="prices",
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
            description_placeholders={"contract": self._contract.name},
        )

    @staticmethod
    def _period_fields() -> dict[vol.Marker, Any]:
        return {
            vol.Required(CONF_START): DateSelector(),
            vol.Optional(CONF_END): DateSelector(),
            vol.Required(CONF_FIXED_PER_YEAR): NumberSelector(
                NumberSelectorConfig(
                    min=0,
                    max=10000,
                    step=0.01,
                    unit_of_measurement="€",
                    mode=NumberSelectorMode.BOX,
                )
            ),
        }

    def _validate_period(
        self, user_input: dict[str, Any], errors: dict[str, str], *, exclude: str | None
    ) -> bool:
        assert self._contract is not None
        start = date.fromisoformat(user_input[CONF_START])
        end = _date(user_input.get(CONF_END))
        if end and end < start:
            errors[CONF_END] = "end_before_start"
        elif any(
            periods_overlap((start, end), (other.period.start, other.period.end))
            for other in manual_prices(self._get_entry())
            if other.contract_uid == self._contract.uid and other.subentry_id != exclude
        ):
            errors["base"] = "overlapping_price_period"
        if errors:
            return False
        self._period = {
            CONF_START: start.isoformat(),
            CONF_END: end.isoformat() if end else None,
            CONF_FIXED_PER_YEAR: user_input[CONF_FIXED_PER_YEAR],
        }
        return True
