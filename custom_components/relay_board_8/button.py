"""Button platform for the 8-Channel Relay Board."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RelayBoard8Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities from a config entry."""
    coordinator: RelayBoard8Coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        RelayBoard8AllButton(coordinator, turn_on=True),
        RelayBoard8AllButton(coordinator, turn_on=False),
    ])


class RelayBoard8AllButton(CoordinatorEntity[RelayBoard8Coordinator], ButtonEntity):
    """A button entity to turn all relays on or off."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: RelayBoard8Coordinator, turn_on: bool
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._turn_on = turn_on
        action = "on" if turn_on else "off"
        self._attr_unique_id = f"{coordinator.host}_all_relays_{action}"
        self._attr_name = f"All Relays {action.capitalize()}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=f"Relay Board ({coordinator.host})",
            model="8-Channel Relay Board",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_turn_relay(9, self._turn_on)
