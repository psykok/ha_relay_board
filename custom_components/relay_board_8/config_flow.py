"""Config flow for the 8-Channel Relay Board integration."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class RelayBoard8ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for the 8-Channel Relay Board."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})

            try:
                session = async_get_clientsession(self.hass)
                url = f"http://{user_input[CONF_HOST]}:{user_input[CONF_PORT]}/relay_en.cgi"
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
                    title=f"Relay Board {user_input[CONF_HOST]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
