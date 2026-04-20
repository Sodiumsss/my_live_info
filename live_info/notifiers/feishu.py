from __future__ import annotations

import logging

import httpx

from live_info.models import Event, User
from live_info.notifiers.renderer import render_feishu_card

log = logging.getLogger(__name__)


class FeishuNotifier:
    def __init__(self, timeout: float = 10.0):
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "FeishuNotifier":
        return self

    async def __aexit__(self, *exc) -> None:
        await self._client.aclose()

    async def send(self, user: User, events: list[Event]) -> bool:
        if not user.feishu_webhook or not events:
            return False
        try:
            r = await self._client.post(user.feishu_webhook, json=render_feishu_card(events))
            if r.status_code >= 400:
                log.warning("feishu %s -> %s %s", user.name, r.status_code, r.text[:200])
                return False
            return True
        except httpx.HTTPError as e:
            log.warning("feishu %s error: %s", user.name, e)
            return False
