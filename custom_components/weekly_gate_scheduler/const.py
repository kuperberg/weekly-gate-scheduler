"""Constants for Weekly Gate Scheduler."""

from zoneinfo import ZoneInfo


DOMAIN = "weekly_gate_scheduler"
PLATFORMS = ["sensor", "binary_sensor", "button"]
CONF_RELAY_ENTITY_ID = "relay_entity_id"
MODE_NORMAL = "normal"
MODE_HOLD_OPEN = "hold_open"
JERUSALEM = ZoneInfo("Asia/Jerusalem")

