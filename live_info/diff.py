from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from live_info.models import Concert, Event, EventKind, RawShow, SaleStatus, Status


def merge_raw_shows(
    artist_id: str,
    maoyan: Iterable[RawShow],
    llm: Iterable[RawShow],
) -> list[Concert]:
    my_map: dict[tuple[str, date], RawShow] = {(r.city, r.show_date): r for r in maoyan}
    ll_map: dict[tuple[str, date], RawShow] = {(r.city, r.show_date): r for r in llm}

    keys = set(my_map) | set(ll_map)
    out: list[Concert] = []
    for key in keys:
        m = my_map.get(key)
        l = ll_map.get(key)
        status = Status.VERIFIED if (m and l) else Status.UNVERIFIED
        sale = m.sale_status if m else SaleStatus.UNKNOWN
        out.append(
            Concert(
                id="",  # 由 DB 分配
                artist_id=artist_id,
                city=key[0],
                show_date=key[1],
                venue=(m.venue if m else None) or (l.venue if l else None),
                status=status,
                sale_status=sale,
                sale_open_at=m.sale_open_at if m else None,
                source_url=m.source_url if m else None,
                source_performance_id=m.source_id if m else None,
                llm_sources=l.llm_source_urls if l else None,
            )
        )
    return out


_WATCHED = ("status", "sale_status", "sale_open_at")


def diff_events(old: list[Concert], new: list[Concert]) -> list[Event]:
    old_map = {c.unique_key(): c for c in old}
    events: list[Event] = []

    for nc in new:
        key = nc.unique_key()
        oc = old_map.get(key)
        if oc is None:
            events.append(
                Event(kind=EventKind.NEW, concert=nc, artist_name="", changes={})
            )
            continue
        changes: dict[str, tuple] = {}
        for field in _WATCHED:
            a = getattr(oc, field)
            b = getattr(nc, field)
            if a != b:
                changes[field] = (
                    a.value if hasattr(a, "value") else a,
                    b.value if hasattr(b, "value") else b,
                )
        if changes:
            events.append(
                Event(kind=EventKind.STATUS_CHANGE, concert=nc, artist_name="", changes=changes)
            )
    return events
