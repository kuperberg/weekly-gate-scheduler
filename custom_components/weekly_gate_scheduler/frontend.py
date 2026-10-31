"""Serve and register the bundled Lovelace card."""

from __future__ import annotations

from pathlib import Path
import re


BASE_URL = "/weekly_gate_scheduler/weekly-gate-scheduler-card.js"


def resource_url(version: str) -> str:
    if not re.fullmatch(r"[0-9A-Za-z._-]+", version):
        raise ValueError("unsafe integration version")
    return f"{BASE_URL}?v={version}"


async def async_register_frontend(hass, version: str) -> None:
    from homeassistant.components import persistent_notification
    from homeassistant.components.http import StaticPathConfig

    card = Path(__file__).parent / "www" / "weekly-gate-scheduler-card.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(BASE_URL, str(card), cache_headers=False)]
    )
    url = resource_url(version)
    persistent_notification.async_create(
        hass,
        "יש להוסיף פעם אחת משאב JavaScript מסוג Module ב־Lovelace:\n\n" + url,
        title="לוח שבועי לשער — השלמת התקנה",
        notification_id="weekly_gate_scheduler_resource",
    )
