"""Switch platform for the 8-Channel Relay Board."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NUM_RELAYS
from .coordinator import RelayBoard8Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities from a config entry."""
    coordinator: RelayBoard8Coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        RelayBoard8Switch(coordinator, relay_id)
        for relay_id in range(1, NUM_RELAYS + 1)
    ]
    async_add_entities(entities)


class RelayBoard8Switch(CoordinatorEntity[RelayBoard8Coordinator], SwitchEntity):
    """A switch entity representing one relay on the board."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RelayBoard8Coordinator,
        relay_id: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._relay_id = relay_id
        self._attr_unique_id = f"{coordinator.host}_relay_{relay_id}"
        self._attr_translation_key = f"relay_{relay_id}"
        self._attr_name = f"Relay {relay_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=f"Relay Board ({coordinator.host})",
            model="8-Channel Relay Board",
        )

    @property
    def is_on(self) -> bool:
        """Return True if the relay is on."""
        return self.coordinator.data.get(self._relay_id, False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the relay on."""
        await self.coordinator.async_turn_relay(self._relay_id, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the relay off."""
        await self.coordinator.async_turn_relay(self._relay_id, False)


