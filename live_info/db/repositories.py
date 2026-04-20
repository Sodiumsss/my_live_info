from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from supabase import Client

from live_info.models import (
    Artist,
    Concert,
    SaleStatus,
    Status,
    User,
)


class Repository:
    def __init__(self, client: Client):
        self.c = client

    # ---------- subscriptions / users ----------
    async def get_subscribed_artists(self) -> list[Artist]:
        res = (
            self.c.table("subscriptions")
            .select("artist_id, artists(canonical_name)")
            .execute()
        )
        seen: dict[str, Artist] = {}
        for row in res.data or []:
            aid = row["artist_id"]
            if aid in seen:
                continue
            name = (row.get("artists") or {}).get("canonical_name")
            if not name:
                continue
            seen[aid] = Artist(id=aid, canonical_name=name)
        return list(seen.values())

    async def get_users(self) -> list[User]:
        res = self.c.table("users").select("*").execute()
        return [User(**row) for row in res.data or []]

    async def get_subscriber_user_ids(self, artist_id: str) -> list[str]:
        res = (
            self.c.table("subscriptions")
            .select("user_id")
            .eq("artist_id", artist_id)
            .execute()
        )
        return [row["user_id"] for row in res.data or []]

    # ---------- artists / aliases ----------
    async def find_artist_id_by_alias(self, alias: str) -> str | None:
        res = self.c.table("artist_aliases").select("artist_id").eq("alias", alias).execute()
        rows = res.data or []
        return rows[0]["artist_id"] if rows else None

    async def upsert_artist(self, canonical_name: str) -> str:
        res = (
            self.c.table("artists")
            .upsert({"canonical_name": canonical_name}, on_conflict="canonical_name")
            .execute()
        )
        rows = res.data or []
        if rows:
            return rows[0]["id"]
        res = self.c.table("artists").select("id").eq("canonical_name", canonical_name).execute()
        return (res.data or [{}])[0]["id"]

    async def upsert_alias(self, alias: str, artist_id: str, source: str) -> None:
        self.c.table("artist_aliases").upsert(
            {"alias": alias, "artist_id": artist_id, "source": source},
            on_conflict="alias",
        ).execute()

    # ---------- concerts ----------
    async def get_concerts_for_artist(self, artist_id: str) -> list[Concert]:
        res = self.c.table("concerts").select("*").eq("artist_id", artist_id).execute()
        return [_row_to_concert(r) for r in res.data or []]

    async def upsert_concert(self, c: Concert) -> Concert:
        payload = {
            "artist_id": c.artist_id,
            "city": c.city,
            "show_date": c.show_date.isoformat(),
            "venue": c.venue,
            "status": c.status.value,
            "sale_status": c.sale_status.value,
            "sale_open_at": c.sale_open_at.isoformat() if c.sale_open_at else None,
            "source_url": c.source_url,
            "source_performance_id": c.source_performance_id,
            "llm_sources": c.llm_sources,
            "last_seen_at": datetime.now(timezone.utc).isoformat(),
        }
        res = (
            self.c.table("concerts")
            .upsert(payload, on_conflict="artist_id,city,show_date")
            .execute()
        )
        return _row_to_concert((res.data or [{}])[0])

    async def insert_snapshot(self, c: Concert) -> None:
        self.c.table("concert_snapshots").insert(
            {
                "concert_id": c.id,
                "status": c.status.value,
                "sale_status": c.sale_status.value,
                "sale_open_at": c.sale_open_at.isoformat() if c.sale_open_at else None,
            }
        ).execute()


def _row_to_concert(r: dict[str, Any]) -> Concert:
    return Concert(
        id=r["id"],
        artist_id=r["artist_id"],
        city=r["city"],
        show_date=date.fromisoformat(r["show_date"]),
        venue=r.get("venue"),
        status=Status(r["status"]),
        sale_status=SaleStatus(r["sale_status"]),
        sale_open_at=_parse_dt(r.get("sale_open_at")),
        source_url=r.get("source_url"),
        source_performance_id=r.get("source_performance_id"),
        llm_sources=r.get("llm_sources"),
        first_seen_at=_parse_dt(r.get("first_seen_at")),
        last_seen_at=_parse_dt(r.get("last_seen_at")),
    )


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
