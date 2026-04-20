from __future__ import annotations

from typing import Protocol

from live_info.models import Event, User


class Notifier(Protocol):
    async def send(self, user: User, events: list[Event]) -> bool: ...
