"""Cost the hourly consumption of a Linky meter under several electricity contracts."""

import logging

import probatio as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_CONFIG_ENTRY_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, SERVICE_RECOMPUTE
from .coordinator import (
    ElectricityContractsConfigEntry,
    ElectricityContractsCoordinator,
    async_delete_issues,
    cache_store,
)
from .data import contracts, manual_prices
from .statistics import async_remove_statistics

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

RECOMPUTE_SCHEMA = vol.Schema({vol.Required(ATTR_CONFIG_ENTRY_ID): cv.string})


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the actions."""

    async def async_recompute(call: ServiceCall) -> None:
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
        coordinator: ElectricityContractsCoordinator = entry.runtime_data
        await coordinator.async_recompute()

    hass.services.async_register(
        DOMAIN, SERVICE_RECOMPUTE, async_recompute, schema=RECOMPUTE_SCHEMA
    )
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> bool:
    """Set up a consumption source from a config entry."""
    _async_remove_orphan_price_periods(hass, entry)
    coordinator = ElectricityContractsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    # A coordinator only refreshes on schedule while something listens to it.
    entry.async_on_unload(coordinator.async_add_listener(_async_no_op))
    # Contracts, price periods and options change through subentry and options
    # flows; reloading applies them.
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> bool:
    """Unload a config entry."""
    return True


async def async_remove_entry(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> None:
    """Delete the statistics, the cache and the repair issues of a removed entry."""
    await async_remove_statistics(hass, entry.entry_id)
    await cache_store(hass, entry.entry_id).async_remove()
    async_delete_issues(hass, entry.entry_id)


@callback
def _async_no_op() -> None:
    """Keep the coordinator's schedule running."""


async def _async_reload(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> None:
    hass.config_entries.async_schedule_reload(entry.entry_id)


@callback
def _async_remove_orphan_price_periods(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> None:
    """Remove the price periods of contracts that were deleted."""
    known = {contract.uid for contract in contracts(entry)}
    for prices in manual_prices(entry):
        if prices.contract_uid not in known:
            _LOGGER.debug(
                "Removing price period %s of a deleted contract", prices.subentry_id
            )
            hass.config_entries.async_remove_subentry(entry, prices.subentry_id)
