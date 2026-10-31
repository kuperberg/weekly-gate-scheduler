"""Persistent schedule serialization."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from .model import GateEvent, WeekSchedule


STORAGE_VERSION = 1


class StorageDataError(ValueError):
    """Stored scheduler data is invalid and was not overwritten."""


def _event_to_dict(item: GateEvent) -> dict[str, Any]:
    return {
        "id": item.id,
        "weekday": item.weekday,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "end_next_day": item.end_next_day,
        "enabled": item.enabled,
        "cancelled_at": item.cancelled_at.isoformat() if item.cancelled_at else None,
    }


def _event_from_dict(value: dict[str, Any]) -> GateEvent:
    cancelled = value.get("cancelled_at")
    return GateEvent(
        id=value["id"],
        weekday=int(value["weekday"]),
        start_time=value["start_time"],
        end_time=value["end_time"],
        end_next_day=bool(value.get("end_next_day", False)),
        enabled=bool(value.get("enabled", True)),
        cancelled_at=datetime.fromisoformat(cancelled) if cancelled else None,
    )


class ScheduleStore:
    """Persist one config entry's schedule via a Home Assistant Store backend."""

    def __init__(self, hass: Any = None, entry_id: str = "", backend: Any = None) -> None:
        self.manual_until: Optional[datetime] = None
        if backend is not None:
            self._store = backend
        else:
            from homeassistant.helpers.storage import Store

            self._store = Store(hass, STORAGE_VERSION, f"weekly_gate_scheduler.{entry_id}")

    async def async_load(self) -> Optional[WeekSchedule]:
        raw = await self._store.async_load()
        if raw is None:
            return None
        try:
            if raw.get("version") != STORAGE_VERSION:
                raise StorageDataError("unsupported storage version")
            value = raw["schedule"]
            manual = raw.get("manual_until")
            self.manual_until = datetime.fromisoformat(manual) if manual else None
            return WeekSchedule(
                date.fromisoformat(value["week_start"]),
                tuple(_event_from_dict(item) for item in value.get("events", [])),
                tuple(_event_from_dict(item) for item in value.get("carry_over", [])),
            )
        except StorageDataError:
            raise
        except Exception as exc:
            raise StorageDataError("invalid stored schedule") from exc

    async def async_save(
        self, schedule: WeekSchedule, manual_until: Optional[datetime] = None
    ) -> None:
        self.manual_until = manual_until
        await self._store.async_save(
            {
                "version": STORAGE_VERSION,
                "manual_until": manual_until.isoformat() if manual_until else None,
                "schedule": {
                    "week_start": schedule.week_start.isoformat(),
                    "events": [_event_to_dict(item) for item in schedule.events],
                    "carry_over": [_event_to_dict(item) for item in schedule.carry_over],
                },
            }
        )
