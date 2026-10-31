"""Scheduler fault sensor."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([GateFaultSensor(entry, hass.data[DOMAIN][entry.entry_id].controller)])

class GateFaultSensor(BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_name = "תקלה בלוח השער"
    _attr_device_class = "problem"
    def __init__(self, entry, controller):
        self.controller = controller
        self._attr_unique_id = f"{entry.entry_id}_fault"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title}
    @property
    def is_on(self): return self.controller.status == "fault"
    async def async_added_to_hass(self): self.async_on_remove(self.controller.add_listener(self.async_write_ha_state))
