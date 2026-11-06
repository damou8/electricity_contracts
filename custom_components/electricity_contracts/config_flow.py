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
from homeassistant.components.recorder.statistics import (
    get_last_statistics,
    get_metadata,
)
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
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.recorder import get_instance
from homeassistant.helpers.selector import (
    BooleanSelector,
    DateSelector,
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
from homeassistant.util.unit_conversion import EnergyConverter

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
    CONF_UID,
    CONF_WEEKEND_OFF_PEAK,
    DEFAULT_OFF_PEAK,
    DOMAIN,
    OFFERED_KVA,
    PRICING_MANUAL,
    PRICING_OFFICIAL,
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

STATISTIC_SCHEMA = vol.Schema({vol.Required(CONF_STATISTIC_ID): StatisticSelector()})

CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_RTE_CLIENT_ID): TextSelector(),
        vol.Optional(CONF_RTE_CLIENT_SECRET): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
    }
)

PRICING_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[PRICING_OFFICIAL, PRICING_MANUAL],
        translation_key=CONF_PRICING,
        mode=SelectSelectorMode.LIST,
    )
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
            hass, 1, statistic_id, convert_units=False, types={"sum"}
        )
    )
    if not last.get(statistic_id):
        raise InvalidStatisticError(reason="statistic_no_data")
    return meta["name"] or statistic_id


class ElectricityContractsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a consumption source."""

    VERSION = 1
    MINOR_VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose the hourly energy statistic to cost."""
        errors: dict[str, str] = {}
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
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STATISTIC_SCHEMA, user_input
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
    """Set the optional RTE credentials used when the public source fails."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Check the credentials before saving them."""
        errors: dict[str, str] = {}
        if user_input is not None:
            client_id = user_input.get(CONF_RTE_CLIENT_ID, "").strip()
            client_secret = user_input.get(CONF_RTE_CLIENT_SECRET, "").strip()
            if not client_id and not client_secret:
                return self.async_create_entry(data={})
            if not client_id or not client_secret:
                errors["base"] = "incomplete_credentials"
            else:
                client = RteOfficialTempoClient(
                    async_get_clientsession(self.hass), client_id, client_secret
                )
                try:
                    await client.async_check_credentials()
                except TempoAuthError:
                    errors["base"] = "invalid_auth"
                except TempoError:
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        data={
                            CONF_RTE_CLIENT_ID: client_id,
                            CONF_RTE_CLIENT_SECRET: client_secret,
                        }
                    )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                CREDENTIALS_SCHEMA, user_input or self.config_entry.options
            ),
            errors=errors,
        )


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


class ContractSubentryFlow(ConfigSubentryFlow):
    """Add or change a contract."""

    def __init__(self) -> None:
        """Start with an empty contract."""
        self._title = ""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Name the contract and choose its kind and where its prices come from."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._title = user_input[CONF_NAME].strip()
            if self._title:
                self._data = {
                    CONF_UID: self._new_uid(),
                    CONF_KIND: user_input[CONF_KIND],
                    CONF_PRICING: user_input[CONF_PRICING],
                }
                return await self.async_step_details()
            errors[CONF_NAME] = "empty_name"
        schema = vol.Schema(
            {
                # pylint: disable-next=home-assistant-config-flow-name-field
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_KIND): SelectSelector(
                    SelectSelectorConfig(
                        options=[kind.value for kind in ContractKind],
                        translation_key=CONF_KIND,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
                vol.Required(CONF_PRICING, default=PRICING_OFFICIAL): PRICING_SELECTOR,
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
        """Rename the contract or change where its prices come from."""
        subentry = self._get_reconfigure_subentry()
        errors: dict[str, str] = {}
        if user_input is not None:
            self._title = user_input[CONF_NAME].strip()
            if self._title:
                self._data = {**subentry.data, CONF_PRICING: user_input[CONF_PRICING]}
                return await self.async_step_details()
            errors[CONF_NAME] = "empty_name"
        schema = vol.Schema(
            {
                # pylint: disable-next=home-assistant-config-flow-name-field
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_PRICING): PRICING_SELECTOR,
            }
        )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or {CONF_NAME: subentry.title, **subentry.data}
            ),
            errors=errors,
        )

    async def async_step_details(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Set the power, off-peak hours and when the contract was in force."""
        kind = ContractKind(self._data[CONF_KIND])
        official = self._data[CONF_PRICING] == PRICING_OFFICIAL
        errors: dict[str, str] = {}
        if user_input is not None:
            data = self._details_data(
                user_input, kind=kind, official=official, errors=errors
            )
            if not errors:
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
        suggested = user_input
        if suggested is None:
            suggested = {CONF_OFF_PEAK: DEFAULT_OFF_PEAK, **self._data}
            if CONF_KVA in suggested:
                suggested[CONF_KVA] = str(suggested[CONF_KVA])
        return self.async_show_form(
            step_id="details",
            data_schema=self.add_suggested_values_to_schema(
                self._details_schema(kind, official=official), suggested
            ),
            errors=errors,
        )

    @staticmethod
    def _details_schema(kind: ContractKind, *, official: bool) -> vol.Schema:
        fields: dict[vol.Marker, Any] = {}
        if official:
            fields[vol.Required(CONF_KVA)] = SelectSelector(
                SelectSelectorConfig(
                    options=[str(kva) for kva in OFFERED_KVA[kind]],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        if kind is ContractKind.HPHC:
            fields[vol.Required(CONF_OFF_PEAK)] = TextSelector(
                TextSelectorConfig(multiple=True)
            )
            fields[vol.Required(CONF_WEEKEND_OFF_PEAK, default=False)] = (
                BooleanSelector()
            )
        fields[vol.Optional(CONF_ACTIVE_FROM)] = DateSelector()
        fields[vol.Optional(CONF_ACTIVE_TO)] = DateSelector()
        return vol.Schema(fields)

    def _details_data(
        self,
        user_input: dict[str, Any],
        *,
        kind: ContractKind,
        official: bool,
        errors: dict[str, str],
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            CONF_UID: self._data[CONF_UID],
            CONF_KIND: kind.value,
            CONF_PRICING: self._data[CONF_PRICING],
        }
        if official:
            data[CONF_KVA] = int(user_input[CONF_KVA])
        if kind is ContractKind.HPHC:
            try:
                ranges = [
                    parse_time_range(text)
                    for text in user_input[CONF_OFF_PEAK]
                    if text.strip()
                ]
            except ValueError:
                ranges = []
            if not ranges:
                errors[CONF_OFF_PEAK] = "invalid_off_peak"
            data[CONF_OFF_PEAK] = [format_time_range(item) for item in ranges]
            data[CONF_WEEKEND_OFF_PEAK] = user_input[CONF_WEEKEND_OFF_PEAK]
        active_from = _date(user_input.get(CONF_ACTIVE_FROM))
        active_to = _date(user_input.get(CONF_ACTIVE_TO))
        data[CONF_ACTIVE_FROM] = active_from.isoformat() if active_from else None
        data[CONF_ACTIVE_TO] = active_to.isoformat() if active_to else None
        if active_to and not active_from:
            errors[CONF_ACTIVE_FROM] = "active_to_without_from"
        elif active_from and active_to and active_to < active_from:
            errors[CONF_ACTIVE_TO] = "end_before_start"
        elif active_from and self._overlaps_another_contract(active_from, active_to):
            errors["base"] = "overlapping_active_period"
        return data

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
