from datetime import date, datetime

import pytest

from custom_components.weekly_gate_scheduler.const import JERUSALEM
from custom_components.weekly_gate_scheduler.model import GateEvent, WeekSchedule
from custom_components.weekly_gate_scheduler.storage import ScheduleStore, StorageDataError


class Backend:
    def __init__(self, value=None):
        self.value = value

    async def async_load(self):
        return self.value

    async def async_save(self, value):
        self.value = value


@pytest.mark.asyncio
async def test_empty_first_run_and_round_trip_cancelled_event():
    backend = Backend()
    store = ScheduleStore(backend=backend)
    assert await store.async_load() is None
    cancelled = datetime(2026, 11, 1, 18, tzinfo=JERUSALEM)
    schedule = WeekSchedule(
        date(2026, 11, 1),
        (GateEvent("e", 0, "17:00", "22:00", cancelled_at=cancelled),),
    )
    await store.async_save(schedule)
    assert await store.async_load() == schedule


@pytest.mark.asyncio
async def test_corrupt_or_unknown_schema_raises_without_overwrite():
    original = {"version": 99, "schedule": {}}
    backend = Backend(original)
    with pytest.raises(StorageDataError):
        await ScheduleStore(backend=backend).async_load()
    assert backend.value is original


@pytest.mark.asyncio
async def test_malformed_data_raises_without_overwrite():
    original = {"version": 1, "schedule": {"week_start": "bad"}}
    backend = Backend(original)
    with pytest.raises(StorageDataError):
        await ScheduleStore(backend=backend).async_load()
    assert backend.value is original


@pytest.mark.asyncio
async def test_manual_deadline_round_trip():
    backend = Backend()
    store = ScheduleStore(backend=backend)
    schedule = WeekSchedule(date(2026, 11, 1))
    deadline = datetime(2026, 11, 2, 4, tzinfo=JERUSALEM)
    await store.async_save(schedule, manual_until=deadline)
    assert await store.async_load() == schedule
    assert store.manual_until == deadline
