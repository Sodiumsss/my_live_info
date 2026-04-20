from __future__ import annotations

import asyncio
import logging
import re
from datetime import date
from typing import Any, Optional
from urllib.parse import quote

import httpx

from live_info.models import RawShow, SaleStatus

log = logging.getLogger(__name__)

SEARCH_URL = (
    "https://m.dianping.com/myshow/ajax/performances/"
    "1;st=0;k={kw};p=1;s={size};tft=0?cityId={city}"
)
DETAIL_URL = "https://m.dianping.com/myshow/ajax/performance/{pid};poi=false"
SHOW_URL_PREFIX = "https://show.maoyan.com/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://show.maoyan.com/",
}

_TICKET_STATUS_MAP = {
    0: SaleStatus.ANNOUNCED,
    1: SaleStatus.ON_SALE,
    2: SaleStatus.SOLD_OUT,
}


def map_ticket_status(code: Any) -> SaleStatus:
    if code is None:
        return SaleStatus.UNKNOWN
    try:
        return _TICKET_STATUS_MAP.get(int(code), SaleStatus.UNKNOWN)
    except (TypeError, ValueError):
        return SaleStatus.UNKNOWN


_DATE_RE = re.compile(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})")


def parse_show_date(raw: str | None) -> date | None:
    if not raw:
        return None
    m = _DATE_RE.search(raw)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


class MaoyanCrawler:
    def __init__(self, max_retries: int = 2, timeout: float = 15.0):
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(headers=HEADERS, timeout=timeout)

    async def __aenter__(self) -> "MaoyanCrawler":
        return self

    async def __aexit__(self, *exc) -> None:
        await self._client.aclose()

    async def _get_json(self, url: str) -> Optional[dict]:
        attempt = 0
        while True:
            try:
                r = await self._client.get(url)
                r.raise_for_status()
                return r.json()
            except (httpx.HTTPError, ValueError) as e:
                if attempt >= self.max_retries:
                    log.warning("maoyan GET failed after %d retries: %s (%s)", attempt, url, e)
                    return None
                await asyncio.sleep(2 ** attempt)
                attempt += 1

    async def search(self, artist_name: str, city_id: int = 0, page_size: int = 20) -> list[RawShow]:
        url = SEARCH_URL.format(kw=quote(artist_name), size=page_size, city=city_id)
        payload = await self._get_json(url)
        if not payload:
            return []
        items = ((payload.get("data") or {}).get("list")) or []
        shows: list[RawShow] = []
        for it in items:
            sd = parse_show_date(it.get("showTimeRange"))
            if not sd:
                continue
            shows.append(
                RawShow(
                    raw_artist_name=artist_name,
                    city=it.get("cityName") or "",
                    show_date=sd,
                    venue=it.get("shopName"),
                    sale_status=map_ticket_status(it.get("ticketStatus")),
                    source="maoyan",
                    source_url=f"{SHOW_URL_PREFIX}{it.get('performanceId')}",
                    source_id=str(it.get("performanceId")) if it.get("performanceId") else None,
                )
            )
        return shows
