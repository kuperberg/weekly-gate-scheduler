"""Weekly Gate Scheduler integration."""

from __future__ import annotations

from datetime import datetime, timedelta
from .const import CONF_RELAY_ENTITY_ID, DOMAIN, JERUSALEM, PLATFORMS
from .controller import GateController
from .model import WeekSchedule, roll_schedule, week_start_for
from .runtime import HARelayAdapter, RuntimeData
from .frontend import async_register_frontend
from .services import register_services
from .state import SchedulerState
from .storage import ScheduleStore


async def async_setup_entry(hass, entry) -> bool:
    from homeassistant.exceptions import ConfigEntryNotReady
    from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
    relay = entry.data[CONF_RELAY_ENTITY_ID]
    relay_state = hass.states.get(relay)
    if relay_state is None or not {"normal", "hold_open"}.issubset(set(relay_state.attributes.get("options", []))):
        raise ConfigEntryNotReady("Relay-mode select is not ready")
    store = ScheduleStore(hass, entry.entry_id)
    now = datetime.now(JERUSALEM)
    schedule = await store.async_load() or WeekSchedule(week_start_for(now))
    scheduler = SchedulerState(roll_schedule(schedule, now))
    scheduler.manual_until = store.manual_until
    controller = GateController(scheduler, HARelayAdapter(hass, relay))
    runtime = RuntimeData(controller, store, [])
    domain_data = hass.data.setdefault(DOMAIN, {})
    domain_data[entry.entry_id] = runtime
    register_services(hass)
    if not domain_data.get("_frontend_registered"):
        await async_register_frontend(hass, "0.1.3")
        domain_data["_frontend_registered"] = True
    async def reconcile(_=None):
        scheduler.schedule = roll_schedule(scheduler.schedule, datetime.now(JERUSALEM))
        await store.async_save(scheduler.schedule, scheduler.manual_until)
        await controller.async_reconcile("watchdog")
    runtime.remove_callbacks.append(async_track_time_change(hass, reconcile, second=0))
    runtime.remove_callbacks.append(async_track_state_change_event(hass, [relay], reconcile))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_create_background_task(hass, reconcile(), "weekly-gate-scheduler-startup")
    return True


async def async_unload_entry(hass, entry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        runtime = hass.data[DOMAIN].pop(entry.entry_id)
        for remove in runtime.remove_callbacks:
            remove()
    return unloaded

