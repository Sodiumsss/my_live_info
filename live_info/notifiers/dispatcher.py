from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from live_info.models import Event, EventKind, User


class FeishuLike(Protocol):
    async def send(self, user: User, events: list[Event]) -> bool: ...


class EmailLike(Protocol):
    def send(self, user: User, events: list[Event]) -> bool: ...


async def dispatch(
    events: list[Event],
    users_by_id: dict[str, User],
    subscribers_by_artist: dict[str, list[str]],
    *,
    feishu: FeishuLike | None,
    email: EmailLike | None,
) -> dict[str, dict]:
    per_user: dict[str, list[Event]] = defaultdict(list)
    for e in events:
        for uid in subscribers_by_artist.get(e.concert.artist_id, []):
            user = users_by_id.get(uid)
            if not user:
                continue
            if e.kind == EventKind.STATUS_CHANGE and not user.notify_on_status_change:
                continue
            per_user[uid].append(e)

    result: dict[str, dict] = {}
    for uid, evs in per_user.items():
        user = users_by_id[uid]
        entry: dict = {"events": len(evs)}
        if feishu and user.has_feishu():
            entry["feishu"] = await feishu.send(user, evs)
        if email and user.has_email():
            entry["email"] = email.send(user, evs)
        result[uid] = entry
    return result
