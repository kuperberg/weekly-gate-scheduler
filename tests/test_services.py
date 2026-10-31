from datetime import date

import pytest

from custom_components.weekly_gate_scheduler.model import GateEvent, WeekSchedule
from custom_components.weekly_gate_scheduler.state import SchedulerState


def test_event_crud_is_stable_and_preserves_explicit_id():
    state = SchedulerState(WeekSchedule(date(2026, 11, 1)))
    item = GateEvent("abc", 2, "13:00", "22:00")
    state.upsert_event(item)
    assert state.schedule.events == (item,)
    changed = GateEvent("abc", 2, "14:00", "22:00")
    state.upsert_event(changed)
    assert state.schedule.events == (changed,)
    state.delete_event("abc")
    assert state.schedule.events == ()


def test_enable_cycle_reactivates_cancelled_event():
    item = GateEvent("abc", 0, "17:00", "22:00", cancelled_at=None)
    state = SchedulerState(WeekSchedule(date(2026, 11, 1), (item,)))
    state.set_event_enabled("abc", False)
    assert not state.schedule.events[0].enabled
    state.set_event_enabled("abc", True)
    assert state.schedule.events[0].enabled
    assert state.schedule.events[0].cancelled_at is None


def test_missing_event_mutations_raise_clear_error():
    state = SchedulerState(WeekSchedule(date(2026, 11, 1)))
    with pytest.raises(KeyError, match="missing"):
        state.delete_event("missing")
