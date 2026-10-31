"""Scheduler status sensor."""
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([GateStatusSensor(entry, hass.data[DOMAIN][entry.entry_id].controller)])

class GateStatusSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "מצב לוח השער"
    _attr_icon = "mdi:gate"
    def __init__(self, entry, controller):
        self.controller = controller
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title}
    @property
    def native_value(self): return self.controller.status
    @property
    def extra_state_attributes(self): return {**self.controller.snapshot, "events": self.controller.scheduler.public_events(), "week_start": self.controller.scheduler.schedule.week_start.isoformat()}
    async def async_added_to_hass(self): self.async_on_remove(self.controller.add_listener(self.async_write_ha_state))
