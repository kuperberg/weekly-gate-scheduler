from datetime import date, datetime

from custom_components.weekly_gate_scheduler.const import JERUSALEM
from custom_components.weekly_gate_scheduler.model import GateEvent, WeekSchedule
from custom_components.weekly_gate_scheduler.state import SchedulerState


def dt(h, minute=0, day=1):
    return datetime(2026, 11, day, h, minute, tzinfo=JERUSALEM)


def test_manual_deadlines_use_next_calendar_day_rules():
    state = SchedulerState(WeekSchedule(date(2026, 11, 1)))
    state.open_now_until_0400(dt(10))
    assert state.manual_until == dt(4, day=2)
    state.open_now_until_1700(dt(10))
    assert state.manual_until == dt(17)
    state.open_now_until_1700(dt(17))
    assert state.manual_until == dt(17, day=2)


def test_finish_active_cancels_active_but_not_future_events():
    active = GateEvent("active", 0, "17:00", "22:00")
    future = GateEvent("future", 1, "17:00", "22:00")
    state = SchedulerState(WeekSchedule(date(2026, 11, 1), (active, future)))
    state.open_now_until_0400(dt(18))
    state.finish_active(dt(19))
    assert state.manual_until is None
    items = {item.id: item for item in state.schedule.events}
    assert items["active"].cancelled_at == dt(19)
    assert items["future"].cancelled_at is None


def test_desired_mode_stays_open_while_any_source_is_active():
    weekly = GateEvent("weekly", 0, "17:00", "23:00")
    state = SchedulerState(WeekSchedule(date(2026, 11, 1), (weekly,)))
    state.open_now_until_1700(dt(16))
    assert state.desired_mode(dt(16, 30)) == "hold_open"
    assert state.desired_mode(dt(18)) == "hold_open"
    assert state.desired_mode(dt(23)) == "normal"


def test_reactivation_is_explicit():
    cancelled = GateEvent("e", 0, "17:00", "22:00", cancelled_at=dt(18))
    state = SchedulerState(WeekSchedule(date(2026, 11, 1), (cancelled,)))
    state.reactivate_event("e")
    assert state.schedule.events[0].cancelled_at is None
