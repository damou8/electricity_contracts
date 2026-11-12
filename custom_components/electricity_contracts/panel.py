"""The Contracts page in the sidebar."""

import hashlib
from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http.server import StaticPathConfig
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

PANEL_URL_PATH = "electricity-contracts"
PANEL_ELEMENT = "electricity-contracts-panel"
PANEL_ICON = "mdi:scale-balance"
_TITLES = {"en": "Contracts", "fr": "Contrats"}

_FRONTEND = Path(__file__).parent / "frontend"
_STATIC_URL = f"/{DOMAIN}_frontend"


def _module_version() -> str:
    """Change the module URL whenever the page changes, so browsers reload it."""
    return hashlib.sha256((_FRONTEND / "panel.js").read_bytes()).hexdigest()[:12]


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve the page's module; static paths can't be removed, so do it once."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(_STATIC_URL, str(_FRONTEND), cache_headers=False)]
    )


async def async_register_panel(hass: HomeAssistant) -> None:
    """Add the page to the sidebar, unless another source already did."""
    if frontend.async_panel_exists(hass, PANEL_URL_PATH):
        return
    version = await hass.async_add_executor_job(_module_version)
    # Another source may have added it meanwhile.
    if frontend.async_panel_exists(hass, PANEL_URL_PATH):
        return
    language = hass.config.language.split("-")[0]
    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=_TITLES.get(language, _TITLES["en"]),
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL_PATH,
        config={
            "_panel_custom": {
                "name": PANEL_ELEMENT,
                "module_url": f"{_STATIC_URL}/panel.js?v={version}",
                "embed_iframe": False,
                "trust_external": False,
            }
        },
        require_admin=False,
    )


@callback
def async_remove_panel(hass: HomeAssistant) -> None:
    """Take the page out of the sidebar."""
    frontend.async_remove_panel(hass, PANEL_URL_PATH, warn_if_unknown=False)
