from datetime import date, datetime

import pytest

from custom_components.weekly_gate_scheduler.const import JERUSALEM
from custom_components.weekly_gate_scheduler.model import (
    GateEvent,
    WeekSchedule,
    active_events,
    event_bounds,
    roll_schedule,
    week_start_for,
)


def dt(y, m, d, h=0, minute=0):
    return datetime(y, m, d, h, minute, tzinfo=JERUSALEM)


def event(**changes):
    values = dict(id="e1", weekday=0, start_time="17:00", end_time="22:00")
    values.update(changes)
    return GateEvent(**values)


def test_same_day_and_next_day_bounds():
    sunday = date(2026, 11, 1)
    assert event_bounds(event(), sunday) == (dt(2026, 11, 1, 17), dt(2026, 11, 1, 22))
    overnight = event(end_time="04:00", end_next_day=True)
    assert event_bounds(overnight, sunday) == (
        dt(2026, 11, 1, 17),
        dt(2026, 11, 2, 4),
    )


def test_active_events_filters_disabled_cancelled_and_supports_overlap():
    schedule = WeekSchedule(
        date(2026, 11, 1),
        (
            event(id="a", start_time="17:00", end_time="22:00"),
            event(id="b", start_time="18:00", end_time="23:00"),
            event(id="c", enabled=False),
            event(id="d", cancelled_at=dt(2026, 11, 1, 18)),
        ),
    )
    assert [item.id for item in active_events(schedule, dt(2026, 11, 1, 19))] == ["a", "b"]


def test_week_starts_on_sunday_and_rejects_naive_datetimes():
    assert week_start_for(dt(2026, 11, 4)) == date(2026, 11, 1)
    with pytest.raises(ValueError, match="timezone-aware"):
        week_start_for(datetime(2026, 11, 4))


def test_rollover_keeps_only_active_saturday_carry_over():
    old = WeekSchedule(
        date(2026, 10, 25),
        (
            event(id="fri", weekday=5, end_next_day=False),
            event(
                id="sat",
                weekday=6,
                start_time="22:00",
                end_time="04:00",
                end_next_day=True,
            ),
        ),
    )
    rolled = roll_schedule(old, dt(2026, 11, 1, 2))
    assert rolled.week_start == date(2026, 11, 1)
    assert rolled.events == ()
    assert [item.id for item in rolled.carry_over] == ["sat"]
    assert roll_schedule(old, dt(2026, 11, 1, 5)).carry_over == ()


def test_israel_dst_bounds_keep_local_wall_clock_values():
    schedule_start = date(2026, 3, 22)
    bounds = event_bounds(
        event(weekday=5, start_time="01:00", end_time="05:00"), schedule_start
    )
    assert (bounds[0].hour, bounds[1].hour) == (1, 5)
    assert bounds[0].tzinfo == JERUSALEM and bounds[1].tzinfo == JERUSALEM


@pytest.mark.parametrize(
    "kwargs",
    [
        {"weekday": 7},
        {"start_time": "7:00"},
        {"end_time": "24:00"},
        {"start_time": "17:00", "end_time": "17:00"},
        {"start_time": "17:00", "end_time": "04:00", "end_next_day": False},
    ],
)
def test_event_validation(kwargs):
    with pytest.raises(ValueError):
        event(**kwargs)


def test_dst_fallback_event_does_not_reopen_after_chronological_end():
    item = event(start_time="00:00", end_time="01:30")
    schedule = WeekSchedule(date(2026, 10, 25), (item,))
    second_0110 = datetime.fromisoformat("2026-10-25T01:10:00+02:00")
    assert active_events(schedule, second_0110) == []
