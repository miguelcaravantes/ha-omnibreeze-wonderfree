"""Diagnostics for OmniBreeze Wonderfree."""

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_AUTH_KEY


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    """Return safe config entry diagnostics."""
    return {"entry": async_redact_data(dict(entry.data), {CONF_AUTH_KEY})}
