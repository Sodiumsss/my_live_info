import json
from datetime import date
from pathlib import Path

import httpx
import pytest
import respx

from live_info.crawlers.maoyan import MaoyanCrawler, map_ticket_status
from live_info.models import SaleStatus

FIX = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def test_map_ticket_status():
    assert map_ticket_status(0) == SaleStatus.ANNOUNCED
    assert map_ticket_status(1) == SaleStatus.ON_SALE
    assert map_ticket_status(2) == SaleStatus.SOLD_OUT
    assert map_ticket_status(999) == SaleStatus.UNKNOWN
    assert map_ticket_status(None) == SaleStatus.UNKNOWN


@respx.mock
async def test_search_returns_shows():
    respx.get(url__startswith="https://m.dianping.com/myshow/ajax/performances/").mock(
        return_value=httpx.Response(200, json=load("maoyan_search.json"))
    )
    async with MaoyanCrawler() as c:
        shows = await c.search("Taylor Swift")

    assert len(shows) == 2
    s0 = shows[0]
    assert s0.raw_artist_name == "Taylor Swift"
    assert s0.city == "上海"
    assert s0.show_date == date(2026, 8, 12)
    assert s0.venue == "梅赛德斯奔驰文化中心"
    assert s0.sale_status == SaleStatus.ON_SALE
    assert s0.source == "maoyan"
    assert s0.source_id == "111"
    assert s0.source_url.startswith("https://show.maoyan.com/")


@respx.mock
async def test_search_handles_date_range():
    respx.get(url__startswith="https://m.dianping.com/myshow/ajax/performances/").mock(
        return_value=httpx.Response(200, json=load("maoyan_search.json"))
    )
    async with MaoyanCrawler() as c:
        shows = await c.search("Taylor Swift")
    # 日期范围 "2026.08.20 - 2026.08.21" → 取起始日
    assert shows[1].show_date == date(2026, 8, 20)


@respx.mock
async def test_search_retries_on_5xx():
    route = respx.get(url__startswith="https://m.dianping.com/myshow/ajax/performances/").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json=load("maoyan_search.json")),
        ]
    )
    async with MaoyanCrawler(max_retries=1) as c:
        shows = await c.search("x")
    assert route.call_count == 2
    assert len(shows) == 2


@respx.mock
async def test_search_returns_empty_on_repeated_failure():
    respx.get(url__startswith="https://m.dianping.com/myshow/ajax/performances/").mock(
        return_value=httpx.Response(500)
    )
    async with MaoyanCrawler(max_retries=2) as c:
        shows = await c.search("x")
    assert shows == []
