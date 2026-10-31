"""Pure date-bound schedule model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
import re
from typing import Optional, Tuple

from .const import JERUSALEM


_TIME = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _parse_time(value: str) -> time:
    if not _TIME.fullmatch(value):
        raise ValueError("time must use strict HH:MM")
    hour, minute = (int(part) for part in value.split(":"))
    return time(hour, minute)


@dataclass(frozen=True)
class GateEvent:
    id: str
    weekday: int
    start_time: str
    end_time: str
    end_next_day: bool = False
    enabled: bool = True
    cancelled_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.weekday not in range(7):
            raise ValueError("weekday must be 0..6")
        _parse_time(self.start_time)
        _parse_time(self.end_time)
        if not self.end_next_day and _parse_time(self.end_time) <= _parse_time(self.start_time):
            raise ValueError("same-day event end must be after start")


@dataclass(frozen=True)
class WeekSchedule:
    week_start: date
    events: Tuple[GateEvent, ...] = field(default_factory=tuple)
    carry_over: Tuple[GateEvent, ...] = field(default_factory=tuple)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(JERUSALEM)


def week_start_for(now: datetime) -> date:
    local = _aware(now)
    days_since_sunday = (local.weekday() + 1) % 7
    return (local - timedelta(days=days_since_sunday)).date()


def event_bounds(event: GateEvent, week_start: date) -> Tuple[datetime, datetime]:
    event_date = week_start + timedelta(days=event.weekday)
    start = datetime.combine(event_date, _parse_time(event.start_time), JERUSALEM)
    end_date = event_date + timedelta(days=1 if event.end_next_day else 0)
    end = datetime.combine(end_date, _parse_time(event.end_time), JERUSALEM)
    if end <= start:
        raise ValueError("event end must be after start")
    return start, end


def active_events(schedule: WeekSchedule, now: datetime) -> list[GateEvent]:
    local = _aware(now)
    active = []
    for item in schedule.events:
        if not item.enabled or item.cancelled_at is not None:
            continue
        start, end = event_bounds(item, schedule.week_start)
        instant = local.astimezone(timezone.utc)
        if start.astimezone(timezone.utc) <= instant < end.astimezone(timezone.utc):
            active.append(item)
    previous_start = schedule.week_start - timedelta(days=7)
    for item in schedule.carry_over:
        if not item.enabled or item.cancelled_at is not None:
            continue
        start, end = event_bounds(item, previous_start)
        instant = local.astimezone(timezone.utc)
        if start.astimezone(timezone.utc) <= instant < end.astimezone(timezone.utc):
            active.append(item)
    return active


def roll_schedule(schedule: WeekSchedule, now: datetime) -> WeekSchedule:
    local = _aware(now)
    current_start = week_start_for(local)
    if schedule.week_start == current_start:
        carry = tuple(
            item
            for item in schedule.carry_over
            if event_bounds(item, current_start - timedelta(days=7))[1] > local
        )
        return WeekSchedule(current_start, schedule.events, carry)
    if schedule.week_start + timedelta(days=7) != current_start:
        return WeekSchedule(current_start)
    carry = []
    for item in schedule.events:
        if item.weekday != 6 or not item.enabled or item.cancelled_at is not None:
            continue
        start, end = event_bounds(item, schedule.week_start)
        if start <= local < end:
            carry.append(item)
    return WeekSchedule(current_start, (), tuple(carry))
