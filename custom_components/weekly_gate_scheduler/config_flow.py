"""Config flow for Weekly Gate Scheduler."""

from __future__ import annotations

from typing import Any, Iterable, Optional

import voluptuous as vol

from .const import CONF_RELAY_ENTITY_ID, DOMAIN, MODE_HOLD_OPEN, MODE_NORMAL


class RelayValidationError(ValueError):
    """A relay entity cannot be used by the scheduler."""

    def __init__(self, translation_key: str) -> None:
        super().__init__(translation_key)
        self.translation_key = translation_key


def validate_relay_entity(hass: Any, entity_id: str) -> str:
    """Validate that an entity exposes the relay modes the scheduler needs."""
    state = hass.states.get(entity_id)
    if state is None:
        raise RelayValidationError("entity_not_found")
    if not entity_id.startswith("select."):
        raise RelayValidationError("not_select")
    options = set(state.attributes.get("options", []))
    if not {MODE_NORMAL, MODE_HOLD_OPEN}.issubset(options):
        raise RelayValidationError("missing_options")
    return entity_id


def build_entry_data(entity_id: str) -> dict[str, str]:
    """Return stable config-entry data."""
    return {CONF_RELAY_ENTITY_ID: entity_id}


def is_duplicate_relay(entries: Iterable[Any], entity_id: str) -> bool:
    """Return whether another entry already controls this relay."""
    for entry in entries:
        data = entry.get("data", {}) if isinstance(entry, dict) else entry.data
        if data.get(CONF_RELAY_ENTITY_ID) == entity_id:
            return True
    return False


try:
    from homeassistant import config_entries
    from homeassistant.data_entry_flow import FlowResult
    from homeassistant.helpers import selector
except ModuleNotFoundError:  # Unit tests exercise pure validation without HA installed.
    config_entries = None
else:

    class WeeklyGateSchedulerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
        """Configure one scheduler per Palgate relay select."""

        VERSION = 1

        async def async_step_user(
            self, user_input: Optional[dict[str, Any]] = None
        ) -> FlowResult:
            """Handle the initial configuration form."""
            errors: dict[str, str] = {}
            if user_input is not None:
                entity_id = user_input[CONF_RELAY_ENTITY_ID]
                local_name = user_input.get("name", "לוח שבועי לשער")
                try:
                    validate_relay_entity(self.hass, entity_id)
                except RelayValidationError as exc:
                    errors["base"] = exc.translation_key
                else:
                    if is_duplicate_relay(self._async_current_entries(), entity_id):
                        return self.async_abort(reason="already_configured")
                    await self.async_set_unique_id(entity_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=local_name,
                        data=build_entry_data(entity_id),
                    )

            schema = vol.Schema(
                {
                    vol.Optional("name", default="לוח שבועי לשער"): str,
                    vol.Required(CONF_RELAY_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="select")
                    )
                }
            )
            return self.async_show_form(
                step_id="user", data_schema=schema, errors=errors
            )

