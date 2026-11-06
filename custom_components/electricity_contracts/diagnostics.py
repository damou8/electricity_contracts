"""Diagnostics for Electricity Contracts."""

from typing import Any

from homeassistant.components.diagnostics import REDACTED, async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_RTE_CLIENT_ID, CONF_RTE_CLIENT_SECRET, CONF_STATISTIC_ID
from .coordinator import ElectricityContractsConfigEntry

# The statistic ID and the entry title usually contain the meter's PRM number.
TO_REDACT = {CONF_STATISTIC_ID, CONF_RTE_CLIENT_ID, CONF_RTE_CLIENT_SECRET}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ElectricityContractsConfigEntry
) -> dict[str, Any]:
    """Return the configuration and the state of the sources."""
    return {
        "entry": {
            "title": REDACTED,
            "version": f"{entry.version}.{entry.minor_version}",
            "data": async_redact_data(entry.data, TO_REDACT),
            "options": async_redact_data(entry.options, TO_REDACT),
            "subentries": [
                {
                    "subentry_type": subentry.subentry_type,
                    "title": subentry.title,
                    "data": dict(subentry.data),
                }
                for subentry in entry.subentries.values()
            ],
        },
        "sources": entry.runtime_data.diagnostics(),
    }
