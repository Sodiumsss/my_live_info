from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Status(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"


class SaleStatus(StrEnum):
    ANNOUNCED = "announced"
    ON_SALE = "on_sale"
    SOLD_OUT = "sold_out"
    UNKNOWN = "unknown"


class Artist(BaseModel):
    id: str
    canonical_name: str


class RawShow(BaseModel):
    """两路 crawler/verifier 的原始产出。艺人名尚未归一化。"""

    raw_artist_name: str
    city: str
    show_date: date
    venue: Optional[str] = None
    sale_status: SaleStatus = SaleStatus.UNKNOWN
    sale_open_at: Optional[datetime] = None
    source: Literal["maoyan", "llm"]
    source_url: Optional[str] = None
    source_id: Optional[str] = None
    llm_source_urls: list[str] = Field(default_factory=list)


class Concert(BaseModel):
    model_config = ConfigDict(use_enum_values=False)

    id: str
    artist_id: str
    city: str
    show_date: date
    venue: Optional[str] = None
    status: Status
    sale_status: SaleStatus
    sale_open_at: Optional[datetime] = None
    source_url: Optional[str] = None
    source_performance_id: Optional[str] = None
    llm_sources: Optional[list[str]] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None

    def unique_key(self) -> tuple[str, str, date]:
        return (self.artist_id, self.city, self.show_date)


class User(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    feishu_webhook: Optional[str] = None
    notify_on_status_change: bool = True

    def has_email(self) -> bool:
        return bool(self.email)

    def has_feishu(self) -> bool:
        return bool(self.feishu_webhook)


class EventKind(StrEnum):
    NEW = "new"
    STATUS_CHANGE = "status_change"


class Event(BaseModel):
    kind: EventKind
    concert: Concert
    artist_name: str                   # canonical
    changes: dict[str, tuple] = Field(default_factory=dict)
    # 形如 {"sale_status": ("announced", "on_sale")}
