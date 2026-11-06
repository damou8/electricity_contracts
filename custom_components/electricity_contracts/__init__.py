"""Cost the hourly consumption of a Linky meter under several electricity contracts."""

import logging

from homeassistant.core import HomeAssistant, callback

from .coordinator import (
    ElectricityContractsConfigEntry,
    ElectricityContractsCoordinator,
    async_delete_issues,
    cache_store,
)
from .data import contracts, manual_prices

_LOGGER = logging.getLogger(__name__)


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
    """Delete the cache and the repair issues of a removed entry."""
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
