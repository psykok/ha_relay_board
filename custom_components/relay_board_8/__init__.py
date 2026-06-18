"""The 8-Channel Relay Board integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_PROTOCOL, DOMAIN, NUM_RELAYS, PROTOCOL_REST
from .coordinator import RelayBoard8Coordinator

PLATFORMS = ["switch", "button"]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to new format."""
    if entry.version == 1:
        new_data = {**entry.data, CONF_PROTOCOL: PROTOCOL_REST}
        hass.config_entries.async_update_entry(entry, data=new_data, version=2)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Relay Board from a config entry."""
    coordinator = RelayBoard8Coordinator(hass, entry)
    coordinator.async_set_updated_data(
        {i: False for i in range(1, NUM_RELAYS + 1)}
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
