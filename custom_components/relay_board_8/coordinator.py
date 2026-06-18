"""DataUpdateCoordinator for the 8-Channel Relay Board."""

from __future__ import annotations

import asyncio

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_PROTOCOL, DOMAIN, LOGGER, NUM_RELAYS, PROTOCOL_TCP


class RelayBoard8Coordinator(DataUpdateCoordinator[dict[int, bool]]):
    """Coordinator that manages communication with the relay board."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data[CONF_PORT]
        self.protocol: str = entry.data[CONF_PROTOCOL]
        self.username: str = entry.data.get(CONF_USERNAME, "")
        self.password: str = entry.data.get(CONF_PASSWORD, "")
        self._request_lock = asyncio.Lock()

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=None,
        )

        if self.protocol != PROTOCOL_TCP:
            self._base_url = f"http://{self.host}:{self.port}/relay_en.cgi"
            self._auth = aiohttp.BasicAuth(self.username, self.password)

    # --- TCP transport ---

    async def _tcp_command(self, cmd: str) -> str:
        """Send a TCP command and return the response."""
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout=5
        )
        try:
            writer.write(f"{cmd}\r\n".encode())
            await writer.drain()
            data = await asyncio.wait_for(reader.read(256), timeout=5)
            return data.decode().strip()
        finally:
            writer.close()
            await writer.wait_closed()

    # --- REST transport ---

    async def _rest_request(
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

    def _parse_rest_states(self, html: str) -> dict[int, bool]:
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

    # --- Coordinator interface ---

    async def async_turn_relay(self, relay_id: int, turn_on: bool) -> None:
        """Turn a relay on or off."""
        async with self._request_lock:
            try:
                if self.protocol == PROTOCOL_TCP:
                    await self._tcp_turn_relay(relay_id, turn_on)
                else:
                    await self._rest_turn_relay(relay_id, turn_on)
            except (aiohttp.ClientError, OSError, asyncio.TimeoutError) as err:
                LOGGER.error("Error switching relay %d: %s", relay_id, err)

    async def _tcp_turn_relay(self, relay_id: int, turn_on: bool) -> None:
        """Turn relay via TCP and update state from response."""
        if relay_id == 9:
            for i in range(1, NUM_RELAYS + 1):
                cmd = f"L{i}" if turn_on else f"D{i}"
                await self._tcp_command(cmd)
            states = {i: turn_on for i in range(1, NUM_RELAYS + 1)}
        else:
            cmd = f"L{relay_id}" if turn_on else f"D{relay_id}"
            response = await self._tcp_command(cmd)
            states = dict(self.data) if self.data else {}
            states[relay_id] = "Relayon" in response

        self.async_set_updated_data(states)

    async def _rest_turn_relay(self, relay_id: int, turn_on: bool) -> None:
        """Turn relay via REST and update state from response."""
        if turn_on:
            data = f"saida{relay_id}on=on"
        else:
            data = f"saida{relay_id}off=off"

        html = await self._rest_request("POST", data)
        self.async_set_updated_data(self._parse_rest_states(html))
