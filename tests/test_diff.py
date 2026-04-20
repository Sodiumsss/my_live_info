from datetime import date

from live_info.diff import diff_events, merge_raw_shows
from live_info.models import (
    Concert,
    EventKind,
    RawShow,
    SaleStatus,
    Status,
)


def _raw_maoyan(city, d, **kw):
    return RawShow(
        raw_artist_name="Taylor Swift",
        city=city,
        show_date=d,
        source="maoyan",
        **kw,
    )


def _raw_llm(city, d, **kw):
    return RawShow(
        raw_artist_name="Taylor Swift",
        city=city,
        show_date=d,
        source="llm",
        **kw,
    )


def test_merge_verified_when_both_sources():
    my = [_raw_maoyan("上海", date(2026, 8, 12), venue="梅奔",
                      sale_status=SaleStatus.ON_SALE,
                      source_url="https://show.maoyan.com/111",
                      source_id="111")]
    ll = [_raw_llm("上海", date(2026, 8, 12), llm_source_urls=["https://x/1"])]

    out = merge_raw_shows("a1", my, ll)
    assert len(out) == 1
    c = out[0]
    assert c.status == Status.VERIFIED
    assert c.sale_status == SaleStatus.ON_SALE
    assert c.source_url == "https://show.maoyan.com/111"
    assert c.source_performance_id == "111"
    assert c.llm_sources == ["https://x/1"]


def test_merge_only_maoyan_is_unverified():
    my = [_raw_maoyan("北京", date(2026, 8, 20), sale_status=SaleStatus.ANNOUNCED)]
    out = merge_raw_shows("a1", my, [])
    assert out[0].status == Status.UNVERIFIED
    assert out[0].sale_status == SaleStatus.ANNOUNCED


def test_merge_only_llm_is_unverified_unknown_sale():
    ll = [_raw_llm("成都", date(2026, 9, 1))]
    out = merge_raw_shows("a1", [], ll)
    assert out[0].status == Status.UNVERIFIED
    assert out[0].sale_status == SaleStatus.UNKNOWN


def test_diff_new_event():
    new = [Concert(id="", artist_id="a1", city="上海",
                   show_date=date(2026, 8, 12),
                   status=Status.VERIFIED, sale_status=SaleStatus.ON_SALE)]
    events = diff_events(old=[], new=new)
    assert len(events) == 1
    assert events[0].kind == EventKind.NEW


def test_diff_status_change_event():
    old = [Concert(id="c1", artist_id="a1", city="上海",
                   show_date=date(2026, 8, 12),
                   status=Status.UNVERIFIED, sale_status=SaleStatus.ANNOUNCED)]
    new = [Concert(id="c1", artist_id="a1", city="上海",
                   show_date=date(2026, 8, 12),
                   status=Status.VERIFIED, sale_status=SaleStatus.ON_SALE)]
    events = diff_events(old, new)
    assert len(events) == 1
    e = events[0]
    assert e.kind == EventKind.STATUS_CHANGE
    assert e.changes["status"] == ("unverified", "verified")
    assert e.changes["sale_status"] == ("announced", "on_sale")


def test_diff_unchanged_emits_nothing():
    c = Concert(id="c1", artist_id="a1", city="上海",
                show_date=date(2026, 8, 12),
                status=Status.VERIFIED, sale_status=SaleStatus.ON_SALE)
    assert diff_events([c], [c]) == []
