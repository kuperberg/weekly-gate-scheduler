"""Home Assistant relay adapter and runtime container."""
from dataclasses import dataclass
from typing import Any

class HARelayAdapter:
    def __init__(self, hass: Any, entity_id: str) -> None:
        self.hass, self.entity_id = hass, entity_id
    def current_mode(self):
        state = self.hass.states.get(self.entity_id)
        return state.state if state and state.state not in ("unknown", "unavailable") else None
    async def set_mode(self, mode: str) -> None:
        await self.hass.services.async_call("select", "select_option", {"entity_id": self.entity_id, "option": mode}, blocking=True)

@dataclass
class RuntimeData:
    controller: Any
    store: Any
    remove_callbacks: list
