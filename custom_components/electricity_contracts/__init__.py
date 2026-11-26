"""Cost the hourly consumption of a Linky meter under several electricity contracts."""

import logging
import secrets
from datetime import timedelta
from types import MappingProxyType
from typing import Any

import probatio as vol
from homeassistant.config_entries import ConfigEntry, ConfigEntryState, ConfigSubentry
from homeassistant.const import ATTR_CONFIG_ENTRY_ID, Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .comparison import async_compare, comparison_response, day_start
from .const import (
    CONF_CONTRACT,
    CONF_END,
    CONF_FIXED_PER_YEAR,
    CONF_INDOOR_TEMPERATURES,
    CONF_PERIODS,
    CONF_PRICE,
    CONF_PRICES,
    CONF_PRICING,
    CONF_START,
    CONF_UID,
    DOMAIN,
    PRICING_MANUAL,
    SECTION_HEATING,
    SERVICE_COMPARE,
    SERVICE_RECOMPUTE,
    SUBENTRY_COMPARISON,
    SUBENTRY_CONTRACT,
    SUBENTRY_GAS_CONTRACT,
    SUBENTRY_GAS_PRICE,
    SUBENTRY_PRICE_PERIOD,
)
from .coordinator import (
    ElectricityContractsConfigEntry,
    ElectricityContractsCoordinator,
    async_delete_issues,
    cache_store,
)
from .data import contracts
from .dpe import settings_store
from .panel import async_register_panel, async_remove_panel, async_setup_frontend
from .statistics import async_remove_statistics
from .weather import async_remove_weather
from .websocket import async_register_commands

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS = [Platform.SENSOR]

ATTR_START = "start"
ATTR_END = "end"
ATTR_CONTRACTS = "contracts"

RECOMPUTE_SCHEMA = vol.Schema({vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string})
COMPARE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string,
        vol.Required(ATTR_START): cv.date,
        vol.Required(ATTR_END): cv.date,
        vol.Optional(ATTR_CONTRACTS): vol.All(cv.ensure_list, [cv.string]),
    }
)


@callback
def _async_loaded_entry(hass: HomeAssistant, call: ServiceCall) -> ConfigEntry:
    """Return the loaded entry an action targets, or raise."""
    entry = hass.config_entries.async_get_entry(call.data[ATTR_CONFIG_ENTRY_ID])
    if entry is None or entry.domain != DOMAIN:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="entry_not_found"
        )
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_not_loaded",
            translation_placeholders={"title": entry.title},
        )
    return entry


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the actions and the Contracts page's commands."""

    async def async_recompute(call: ServiceCall) -> None:
        coordinator: ElectricityContractsCoordinator = _async_loaded_entry(
            hass, call
        ).runtime_data
        await coordinator.async_recompute()

    async def async_compare_contracts(call: ServiceCall) -> ServiceResponse:
        entry = _async_loaded_entry(hass, call)
        coordinator: ElectricityContractsCoordinator = entry.runtime_data
        start, end = call.data[ATTR_START], call.data[ATTR_END]
        if end < start:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="end_before_start"
            )
        selected = contracts(entry)
        if names := list(dict.fromkeys(call.data.get(ATTR_CONTRACTS, []))):
            known = {contract.name: contract for contract in selected}
            if unknown := [name for name in names if name not in known]:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="unknown_contracts",
                    translation_placeholders={"names": ", ".join(unknown)},
                )
            selected = [known[name] for name in names]
        comparison = await async_compare(
            hass,
            writer=coordinator.costing,
            status=coordinator.data.costing,
            contracts=selected,
            start=day_start(start),
            end=day_start(end + timedelta(days=1)),
            details=True,
        )
        return comparison_response(comparison)

    hass.services.async_register(
        DOMAIN, SERVICE_RECOMPUTE, async_recompute, schema=RECOMPUTE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_COMPARE,
        async_compare_contracts,
        schema=COMPARE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    async_register_commands(hass)
    await async_setup_frontend(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> bool:
    """Set up a consumption source from a config entry."""
    # Before the first refresh, which takes minutes when a contract was added:
    # the page tells it is preparing the figures meanwhile.
    await async_register_panel(hass)
    # Contracts and options change through subentry and options flows;
    # reloading applies them. Listened to before the first refresh: a contract
    # added meanwhile reloads the entry once its setup is done.
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    coordinator = ElectricityContractsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    # A coordinator only refreshes on schedule while something listens to it.
    entry.async_on_unload(coordinator.async_add_listener(_async_no_op))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> bool:
    """Unload a config entry, and the Contracts page with the last enabled one.

    A reload keeps the page: every change of contract reloads the entry.
    """
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    if entry.disabled_by:
        _async_remove_panel_if_unused(hass, entry)
    return True


async def async_migrate_entry(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> bool:
    """Bring an entry written by an older version up to date.

    Home Assistant refuses newer versions itself, before calling this.
    """
    if entry.minor_version < 2:  # noqa: PLR2004
        _async_remove_comparisons(hass, entry)
        hass.config_entries.async_update_entry(entry, minor_version=2)
    if entry.minor_version < 3:  # noqa: PLR2004
        _async_move_prices_into_contracts(hass, entry)
        _async_move_indoor_temperatures(hass, entry)
        hass.config_entries.async_update_entry(entry, minor_version=3)
    return True


async def async_remove_entry(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> None:
    """Delete the statistics, the cache and the repair issues of a removed entry."""
    _async_remove_panel_if_unused(hass, entry)
    await async_remove_statistics(hass, entry.entry_id)
    await async_remove_weather(hass, entry)
    await cache_store(hass, entry.entry_id).async_remove()
    await settings_store(hass, entry.entry_id).async_remove()
    async_delete_issues(hass, entry.entry_id)


@callback
def _async_remove_panel_if_unused(
    hass: HomeAssistant, leaving: ElectricityContractsConfigEntry
) -> None:
    """Remove the Contracts page when no other enabled entry is left."""
    if not [
        other
        for other in hass.config_entries.async_entries(
            DOMAIN, include_ignore=False, include_disabled=False
        )
        if other.entry_id != leaving.entry_id
    ]:
        async_remove_panel(hass)


@callback
def _async_no_op() -> None:
    """Keep the coordinator's schedule running."""


async def _async_reload(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> None:
    hass.config_entries.async_schedule_reload(entry.entry_id)


@callback
def _async_remove_comparisons(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> None:
    """Remove the comparisons and sensors of 0.1, replaced by the Contracts page."""
    for subentry in list(entry.subentries.values()):
        if subentry.subentry_type == SUBENTRY_COMPARISON:
            hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)
    entities = er.async_get(hass)
    for item in er.async_entries_for_config_entry(entities, entry.entry_id):
        entities.async_remove(item.entity_id)
    devices = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(devices, entry.entry_id):
        devices.async_update_device(device.id, remove_config_entry_id=entry.entry_id)


# The name of the gas contract the gas prices of 0.6 move into.
_MY_GAS_PRICES = {"en": "Gas · my prices", "fr": "Gaz · mes prix"}


@callback
def _async_move_prices_into_contracts(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> None:
    """Move the price periods into their contract, and the gas prices into one.

    Until 0.6, each price period and each gas price was a subentry of its own.
    The periods of a deleted contract are dropped; the gas prices become one gas
    contract priced by hand, always in force, with no subscription.
    """
    periods: dict[str, list[dict[str, Any]]] = {}
    gas: list[dict[str, Any]] = []
    for subentry in list(entry.subentries.values()):
        data = subentry.data
        if subentry.subentry_type == SUBENTRY_PRICE_PERIOD:
            periods.setdefault(data[CONF_CONTRACT], []).append(
                {
                    CONF_START: data[CONF_START],
                    CONF_END: data.get(CONF_END),
                    CONF_FIXED_PER_YEAR: data[CONF_FIXED_PER_YEAR],
                    CONF_PRICES: dict(data[CONF_PRICES]),
                }
            )
        elif subentry.subentry_type == SUBENTRY_GAS_PRICE:
            gas.append(
                {
                    CONF_START: data[CONF_START],
                    CONF_END: data.get(CONF_END),
                    CONF_FIXED_PER_YEAR: 0.0,
                    CONF_PRICE: data[CONF_PRICE],
                }
            )
        else:
            continue
        hass.config_entries.async_remove_subentry(entry, subentry.subentry_id)
    for subentry in list(entry.subentries.values()):
        if (
            subentry.subentry_type == SUBENTRY_CONTRACT
            and subentry.data[CONF_PRICING] == PRICING_MANUAL
        ):
            moved = periods.get(subentry.data[CONF_UID], [])
            hass.config_entries.async_update_subentry(
                entry,
                subentry,
                data={
                    **subentry.data,
                    CONF_PERIODS: sorted(moved, key=lambda item: item[CONF_START]),
                },
            )
    if gas:
        used = {subentry.data.get(CONF_UID) for subentry in entry.subentries.values()}
        while (uid := secrets.token_hex(4)) in used:
            continue  # pragma: no cover - a collision among 4 billion values
        language = hass.config.language.split("-")[0]
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType(
                    {
                        CONF_UID: uid,
                        CONF_PRICING: PRICING_MANUAL,
                        CONF_PERIODS: sorted(gas, key=lambda item: item[CONF_START]),
                    }
                ),
                subentry_type=SUBENTRY_GAS_CONTRACT,
                title=_MY_GAS_PRICES.get(language, _MY_GAS_PRICES["en"]),
                unique_id=uid,
            ),
        )


@callback
def _async_move_indoor_temperatures(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> None:
    """Move the indoor thermometers out of the heating options: a page of their own."""
    heating = dict(entry.options.get(SECTION_HEATING) or {})
    indoor = heating.pop(CONF_INDOOR_TEMPERATURES, None)
    if indoor is None:
        return
    options = {**entry.options, CONF_INDOOR_TEMPERATURES: indoor}
    if heating:
        options[SECTION_HEATING] = heating
    else:
        options.pop(SECTION_HEATING, None)
    hass.config_entries.async_update_entry(entry, options=options)
