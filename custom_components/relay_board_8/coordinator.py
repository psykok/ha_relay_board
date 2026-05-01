"""DataUpdateCoordinator for the 8-Channel Relay Board."""

from __future__ import annotations

import asyncio

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER, NUM_RELAYS


class RelayBoard8Coordinator(DataUpdateCoordinator[dict[int, bool]]):
    """Coordinator that polls the relay board and parses relay states."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=None,
        )
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data[CONF_PORT]
        self.username: str = entry.data[CONF_USERNAME]
        self.password: str = entry.data[CONF_PASSWORD]
        self._base_url = f"http://{self.host}:{self.port}/relay_en.cgi"
        self._auth = aiohttp.BasicAuth(self.username, self.password)
        self._request_lock = asyncio.Lock()

    def _parse_relay_states(self, html: str) -> dict[int, bool]:
        """Parse HTML response to extract relay on/off states."""
        states: dict[int, bool] = {}
        for i in range(1, NUM_RELAYS + 1):
            try:
                after_relay = html.split(f"relay{i}")[1]
                delimiter = f"relay{i + 1}" if i < NUM_RELAYS else "All"
                section = after_relay.split(delimiter)[0]
                states[i] = "lighton" in section
            except (IndexError, ValueError):
                states[i] = False
        return states

    async def _make_request(
        self, method: str, data: str | None = None
    ) -> str:
        """Make an HTTP request with a fresh connection."""
        connector = aiohttp.TCPConnector(force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            if method == "GET":
                async with session.get(
                    self._base_url, auth=self._auth
                ) as response:
                    response.raise_for_status()
                    return await response.text()
            else:
                async with session.post(
                    self._base_url,
                    data=data,
                    auth=self._auth,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    response.raise_for_status()
                    return await response.text()

    async def _async_update_data(self) -> dict[int, bool]:
        """Fetch relay states from the device."""
        async with self._request_lock:
            try:
                html = await self._make_request("GET")
                return self._parse_relay_states(html)
            except aiohttp.ClientError as err:
                raise UpdateFailed(f"Error communicating with device: {err}") from err

    async def async_turn_relay(self, relay_id: int, turn_on: bool) -> None:
        """Turn a relay on or off."""
        async with self._request_lock:
            if turn_on:
                data = f"saida{relay_id}on=on"
            else:
                data = f"saida{relay_id}off=off"

            try:
                html = await self._make_request("POST", data)
                self.async_set_updated_data(self._parse_relay_states(html))
            except aiohttp.ClientError as err:
                LOGGER.error("Error switching relay %d: %s", relay_id, err)
