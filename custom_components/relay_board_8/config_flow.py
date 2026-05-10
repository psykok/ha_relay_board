"""Config flow for the 8-Channel Relay Board integration."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_PROTOCOL,
    DEFAULT_REST_PORT,
    DEFAULT_TCP_PORT,
    DOMAIN,
    PROTOCOL_REST,
    PROTOCOL_TCP,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PROTOCOL, default=PROTOCOL_TCP): vol.In(
            {PROTOCOL_TCP: "TCP", PROTOCOL_REST: "REST (HTTP)"}
        ),
    }
)

STEP_TCP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PORT, default=DEFAULT_TCP_PORT): int,
    }
)

STEP_REST_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PORT, default=DEFAULT_REST_PORT): int,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class RelayBoard8ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the 8-Channel Relay Board."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_input: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: host and protocol selection."""
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
            self._user_input = user_input

            if user_input[CONF_PROTOCOL] == PROTOCOL_TCP:
                return await self.async_step_tcp()
            return await self.async_step_rest()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
        )

    async def async_step_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle TCP configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = self._user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), timeout=5
                )
                writer.write(b"R1\r\n")
                await writer.drain()
                data = await asyncio.wait_for(reader.read(256), timeout=5)
                writer.close()
                await writer.wait_closed()
                response = data.decode().strip()
                if "Relay" not in response:
                    errors["base"] = "cannot_connect"
            except (OSError, asyncio.TimeoutError):
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"Relay Board {self._user_input[CONF_HOST]}",
                    data={
                        CONF_HOST: self._user_input[CONF_HOST],
                        CONF_PROTOCOL: PROTOCOL_TCP,
                        CONF_PORT: port,
                    },
                )

        return self.async_show_form(
            step_id="tcp",
            data_schema=STEP_TCP_SCHEMA,
            errors=errors,
        )

    async def async_step_rest(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle REST configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = self._user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            try:
                session = async_get_clientsession(self.hass)
                url = f"http://{host}:{port}/relay_en.cgi"
                auth = aiohttp.BasicAuth(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
                async with session.get(url, auth=auth) as response:
                    if response.status == 401:
                        errors["base"] = "invalid_auth"
                    elif response.status != 200:
                        errors["base"] = "cannot_connect"
                    else:
                        html = await response.text()
                        if "Switch Control" not in html:
                            errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=f"Relay Board {self._user_input[CONF_HOST]}",
                    data={
                        CONF_HOST: self._user_input[CONF_HOST],
                        CONF_PROTOCOL: PROTOCOL_REST,
                        CONF_PORT: port,
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="rest",
            data_schema=STEP_REST_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration."""
        if user_input is not None:
            self._user_input = {
                CONF_HOST: self._get_reconfigure_entry().data[CONF_HOST],
                **user_input,
            }
            if user_input[CONF_PROTOCOL] == PROTOCOL_TCP:
                return await self.async_step_reconfigure_tcp()
            return await self.async_step_reconfigure_rest()

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PROTOCOL,
                        default=self._get_reconfigure_entry().data.get(
                            CONF_PROTOCOL, PROTOCOL_REST
                        ),
                    ): vol.In(
                        {PROTOCOL_TCP: "TCP", PROTOCOL_REST: "REST (HTTP)"}
                    ),
                }
            ),
        )

    async def async_step_reconfigure_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle TCP reconfiguration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = self._user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port), timeout=5
                )
                writer.write(b"R1\r\n")
                await writer.drain()
                data = await asyncio.wait_for(reader.read(256), timeout=5)
                writer.close()
                await writer.wait_closed()
                response = data.decode().strip()
                if "Relay" not in response:
                    errors["base"] = "cannot_connect"
            except (OSError, asyncio.TimeoutError):
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data={
                        CONF_HOST: host,
                        CONF_PROTOCOL: PROTOCOL_TCP,
                        CONF_PORT: port,
                    },
                )

        return self.async_show_form(
            step_id="reconfigure_tcp",
            data_schema=STEP_TCP_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure_rest(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle REST reconfiguration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = self._user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            try:
                session = async_get_clientsession(self.hass)
                url = f"http://{host}:{port}/relay_en.cgi"
                auth = aiohttp.BasicAuth(
                    user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
                async with session.get(url, auth=auth) as response:
                    if response.status == 401:
                        errors["base"] = "invalid_auth"
                    elif response.status != 200:
                        errors["base"] = "cannot_connect"
                    else:
                        html = await response.text()
                        if "Switch Control" not in html:
                            errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data={
                        CONF_HOST: host,
                        CONF_PROTOCOL: PROTOCOL_REST,
                        CONF_PORT: port,
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reconfigure_rest",
            data_schema=STEP_REST_SCHEMA,
            errors=errors,
        )
