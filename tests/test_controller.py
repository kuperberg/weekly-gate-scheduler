from datetime import date, datetime

import pytest

from custom_components.weekly_gate_scheduler.const import JERUSALEM
from custom_components.weekly_gate_scheduler.controller import GateController
from custom_components.weekly_gate_scheduler.model import GateEvent, WeekSchedule
from custom_components.weekly_gate_scheduler.state import SchedulerState


NOW = datetime(2026, 11, 1, 18, tzinfo=JERUSALEM)


class Adapter:
    def __init__(self, mode="normal", failures=0, available=True):
        self.mode, self.failures, self.available = mode, failures, available
        self.calls = []

    def current_mode(self):
        return self.mode if self.available else None

    async def set_mode(self, mode):
        self.calls.append(mode)
        if self.failures:
            self.failures -= 1
            raise RuntimeError("cloud unavailable")
        self.mode = mode


def active_state():
    item = GateEvent("e", 0, "17:00", "22:00")
    return SchedulerState(WeekSchedule(date(2026, 11, 1), (item,)))


@pytest.mark.asyncio
async def test_noop_when_correct_and_sets_configured_mode_when_wrong():
    adapter = Adapter("hold_open")
    controller = GateController(active_state(), adapter, now_fn=lambda: NOW)
    assert await controller.async_reconcile("test")
    assert adapter.calls == []
    adapter.mode = "normal"
    assert await controller.async_reconcile("test")
    assert adapter.calls == ["hold_open"]


@pytest.mark.asyncio
async def test_retries_three_times_after_initial_failure_and_recovers():
    adapter = Adapter(failures=3)
    delays = []

    async def sleep(value):
        delays.append(value)

    controller = GateController(active_state(), adapter, now_fn=lambda: NOW, sleep=sleep)
    assert await controller.async_reconcile("test")
    assert adapter.calls == ["hold_open"] * 4
    assert delays == [5, 15, 30]
    assert controller.status == "hold_open"


@pytest.mark.asyncio
async def test_fault_after_all_attempts_and_later_recovery():
    adapter = Adapter(failures=4)
    controller = GateController(active_state(), adapter, now_fn=lambda: NOW, sleep=lambda _: _done())
    assert not await controller.async_reconcile("watchdog")
    assert controller.status == "fault"
    assert "cloud unavailable" in controller.last_error
    assert await controller.async_reconcile("watchdog")
    assert controller.status == "hold_open"


async def _done():
    return None


@pytest.mark.asyncio
async def test_retry_recomputes_desired_mode_after_finish():
    adapter = Adapter(failures=1)
    state = active_state()
    async def sleep(_):
        state.finish_active(NOW)
    controller = GateController(state, adapter, now_fn=lambda: NOW, sleep=sleep)
    assert await controller.async_reconcile("open")
    assert adapter.calls == ["hold_open", "normal"]
    assert adapter.mode == "normal"
