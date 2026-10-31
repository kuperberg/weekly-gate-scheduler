"""Return-to-normal button."""
from datetime import datetime
from homeassistant.components.button import ButtonEntity
from .const import DOMAIN, JERUSALEM

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([GateNormalButton(entry, hass.data[DOMAIN][entry.entry_id])])

class GateNormalButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "סיום פתיחה — חזרה למצב אפליקציה"
    _attr_icon = "mdi:gate"
    def __init__(self, entry, runtime):
        self.runtime = runtime
        self._attr_unique_id = f"{entry.entry_id}_normal"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title}
    async def async_press(self):
        self.runtime.controller.scheduler.finish_active(datetime.now(JERUSALEM))
        await self.runtime.store.async_save(
            self.runtime.controller.scheduler.schedule,
            self.runtime.controller.scheduler.manual_until,
        )
        await self.runtime.controller.async_reconcile("normal_button")
