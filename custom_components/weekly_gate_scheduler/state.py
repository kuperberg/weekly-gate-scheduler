"""Mutable scheduler state and manual action rules."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from typing import Optional

from .const import JERUSALEM, MODE_HOLD_OPEN, MODE_NORMAL
from .model import GateEvent, WeekSchedule, active_events, event_bounds


class SchedulerState:
    def __init__(self, schedule: WeekSchedule) -> None:
        self.schedule = schedule
        self.manual_until: Optional[datetime] = None

    @staticmethod
    def _local(now: datetime) -> datetime:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("datetime must be timezone-aware")
        return now.astimezone(JERUSALEM)

    def open_now_until_0400(self, now: datetime) -> datetime:
        local = self._local(now)
        tomorrow = local.date() + timedelta(days=1)
        self.manual_until = datetime.combine(
            tomorrow, datetime.min.time().replace(hour=4), JERUSALEM
        )
        return self.manual_until

    def open_now_until_1700(self, now: datetime) -> datetime:
        local = self._local(now)
        target_date = local.date() if local.hour < 17 else local.date() + timedelta(days=1)
        self.manual_until = datetime.combine(
            target_date, datetime.min.time().replace(hour=17), JERUSALEM
        )
        return self.manual_until

    def desired_mode(self, now: datetime) -> str:
        local = self._local(now)
        manual = self.manual_until is not None and local < self.manual_until
        return MODE_HOLD_OPEN if manual or active_events(self.schedule, local) else MODE_NORMAL

    def active_until(self, now: datetime) -> Optional[datetime]:
        local = self._local(now)
        values = []
        if self.manual_until is not None and local < self.manual_until:
            values.append(self.manual_until)
        for item in active_events(self.schedule, local):
            base = self.schedule.week_start
            if item in self.schedule.carry_over:
                base -= timedelta(days=7)
            values.append(event_bounds(item, base)[1])
        return max(values) if values else None

    def finish_active(self, now: datetime) -> None:
        local = self._local(now)
        active_ids = {item.id for item in active_events(self.schedule, local)}
        self.manual_until = None
        events = tuple(
            replace(item, cancelled_at=local) if item.id in active_ids else item
            for item in self.schedule.events
        )
        carry = tuple(
            replace(item, cancelled_at=local) if item.id in active_ids else item
            for item in self.schedule.carry_over
        )
        self.schedule = WeekSchedule(self.schedule.week_start, events, carry)

    def reactivate_event(self, event_id: str) -> None:
        events = tuple(
            replace(item, cancelled_at=None) if item.id == event_id else item
            for item in self.schedule.events
        )
        carry = tuple(
            replace(item, cancelled_at=None) if item.id == event_id else item
            for item in self.schedule.carry_over
        )
        self.schedule = WeekSchedule(self.schedule.week_start, events, carry)

    def upsert_event(self, event: GateEvent) -> None:
        found = False
        values = []
        for item in self.schedule.events:
            if item.id == event.id:
                values.append(replace(event, cancelled_at=item.cancelled_at))
                found = True
            else:
                values.append(item)
        if not found:
            values.append(event)
        self.schedule = WeekSchedule(
            self.schedule.week_start, tuple(values), self.schedule.carry_over
        )

    def delete_event(self, event_id: str) -> None:
        values = tuple(item for item in self.schedule.events if item.id != event_id)
        if len(values) == len(self.schedule.events):
            raise KeyError(event_id)
        self.schedule = WeekSchedule(
            self.schedule.week_start, values, self.schedule.carry_over
        )

    def set_event_enabled(self, event_id: str, enabled: bool) -> None:
        found = False
        values = []
        for item in self.schedule.events:
            if item.id == event_id:
                values.append(replace(item, enabled=enabled, cancelled_at=None if enabled else item.cancelled_at))
                found = True
            else:
                values.append(item)
        if not found:
            raise KeyError(event_id)
        self.schedule = WeekSchedule(
            self.schedule.week_start, tuple(values), self.schedule.carry_over
        )

    def public_events(self) -> list[dict]:
        return [
            {
                "id": item.id,
                "weekday": item.weekday,
                "start_time": item.start_time,
                "end_time": item.end_time,
                "end_next_day": item.end_next_day,
                "enabled": item.enabled,
                "cancelled": item.cancelled_at is not None,
            }
            for item in self.schedule.events
        ]
