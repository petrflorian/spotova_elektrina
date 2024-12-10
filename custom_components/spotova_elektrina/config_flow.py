"""Config flow for Spotová Elektřina integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)

class SpotovaElektrinaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Spotová Elektřina."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title=DEFAULT_NAME,
                data={},
            )

        return self.async_show_form(step_id="user")