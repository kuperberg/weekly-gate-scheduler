"""Service registration for schedule mutations."""
from datetime import datetime
import uuid
import voluptuous as vol
from .const import DOMAIN, JERUSALEM
from .model import GateEvent

def register_services(hass):
    if hass.services.has_service(DOMAIN, "open_now_until_0400"):
        return
    def runtime(call):
        return hass.data[DOMAIN][call.data["entry_id"]]
    async def save(data, source):
        await data.store.async_save(
            data.controller.scheduler.schedule, data.controller.scheduler.manual_until
        )
        await data.controller.async_reconcile(source)
    async def open_0400(call):
        data = runtime(call); data.controller.scheduler.open_now_until_0400(datetime.now(JERUSALEM)); await save(data, "manual_0400")
    async def open_1700(call):
        data = runtime(call); data.controller.scheduler.open_now_until_1700(datetime.now(JERUSALEM)); await save(data, "manual_1700")
    async def finish(call):
        data = runtime(call); data.controller.scheduler.finish_active(datetime.now(JERUSALEM)); await save(data, "finish_active")
    async def upsert(call):
        data = runtime(call)
        data.controller.scheduler.upsert_event(GateEvent(call.data.get("event_id") or uuid.uuid4().hex, call.data["weekday"], call.data["start_time"], call.data["end_time"], call.data.get("end_next_day", False), call.data.get("enabled", True)))
        await save(data, "upsert_event")
    async def delete(call):
        data = runtime(call); data.controller.scheduler.delete_event(call.data["event_id"]); await save(data, "delete_event")
    async def enabled(call):
        data = runtime(call); data.controller.scheduler.set_event_enabled(call.data["event_id"], call.data["enabled"]); await save(data, "set_event_enabled")
    base = vol.Schema({vol.Required("entry_id"): str})
    hass.services.async_register(DOMAIN, "open_now_until_0400", open_0400, schema=base)
    hass.services.async_register(DOMAIN, "open_now_until_1700", open_1700, schema=base)
    hass.services.async_register(DOMAIN, "finish_active", finish, schema=base)
    hass.services.async_register(DOMAIN, "upsert_event", upsert, schema=vol.Schema({vol.Required("entry_id"): str, vol.Optional("event_id"): str, vol.Required("weekday"): vol.All(int, vol.Range(min=0,max=6)), vol.Required("start_time"): str, vol.Required("end_time"): str, vol.Optional("end_next_day", default=False): bool, vol.Optional("enabled", default=True): bool}))
    hass.services.async_register(DOMAIN, "delete_event", delete, schema=vol.Schema({vol.Required("entry_id"): str, vol.Required("event_id"): str}))
    hass.services.async_register(DOMAIN, "set_event_enabled", enabled, schema=vol.Schema({vol.Required("entry_id"): str, vol.Required("event_id"): str, vol.Required("enabled"): bool}))
