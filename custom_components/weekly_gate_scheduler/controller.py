"""Desired-state reconciliation for the configured relay select."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional

from .const import JERUSALEM
from .state import SchedulerState


class GateController:
    def __init__(
        self,
        scheduler: SchedulerState,
        adapter: Any,
        now_fn: Callable[[], datetime] = lambda: datetime.now(JERUSALEM),
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.scheduler = scheduler
        self.adapter = adapter
        self.now_fn = now_fn
        self.sleep = sleep
        self.status = "normal"
        self.last_error: Optional[str] = None
        self.last_check: Optional[datetime] = None
        self.last_source: Optional[str] = None
        self.attempts = 0
        self._lock = asyncio.Lock()
        self._listeners: list[Callable[[], None]] = []

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener) if listener in self._listeners else None

    def _notify(self) -> None:
        for listener in tuple(self._listeners):
            listener()

    async def async_reconcile(self, source: str) -> bool:
        async with self._lock:
            desired = self.scheduler.desired_mode(self.now_fn())
            self.last_check = self.now_fn()
            self.last_source = source
            self.last_error = None
            if self.adapter.current_mode() == desired:
                self.status = desired
                self.attempts = 0
                self._notify()
                return True
            self.status = "working"
            self._notify()
            for attempt, delay in enumerate((0, 5, 15, 30), start=1):
                if delay:
                    await self.sleep(delay)
                desired = self.scheduler.desired_mode(self.now_fn())
                self.attempts = attempt
                try:
                    await self.adapter.set_mode(desired)
                    if self.adapter.current_mode() != desired:
                        raise RuntimeError("relay state did not confirm requested mode")
                except Exception as exc:
                    self.last_error = str(exc)
                    continue
                self.status = desired
                self.last_error = None
                self._notify()
                return True
            self.status = "fault"
            self._notify()
            return False

    @property
    def snapshot(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "desired_mode": self.scheduler.desired_mode(self.now_fn()),
            "observed_mode": self.adapter.current_mode(),
            "active_until": self.scheduler.active_until(self.now_fn()).isoformat()
            if self.scheduler.active_until(self.now_fn())
            else None,
            "manual_until": self.scheduler.manual_until.isoformat()
            if self.scheduler.manual_until
            else None,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_source": self.last_source,
            "last_error": self.last_error,
            "attempts": self.attempts,
        }
