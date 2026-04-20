from datetime import date

from live_info.models import Concert, Event, EventKind, SaleStatus, Status
from live_info.notifiers.renderer import render_email, render_feishu_card


def _ev_new():
    c = Concert(
        id="c1", artist_id="a1", city="上海",
        show_date=date(2026, 8, 12), venue="梅奔",
        status=Status.VERIFIED, sale_status=SaleStatus.ANNOUNCED,
        source_url="https://show.maoyan.com/111",
    )
    return Event(kind=EventKind.NEW, concert=c, artist_name="Taylor Swift")


def _ev_change():
    c = Concert(
        id="c1", artist_id="a1", city="上海",
        show_date=date(2026, 8, 12),
        status=Status.VERIFIED, sale_status=SaleStatus.ON_SALE,
    )
    return Event(
        kind=EventKind.STATUS_CHANGE, concert=c, artist_name="Taylor Swift",
        changes={"sale_status": ("announced", "on_sale")},
    )


def test_feishu_new_contains_key_fields():
    card = render_feishu_card([_ev_new()])
    assert card["msg_type"] == "interactive"
    body = str(card)
    assert "Taylor Swift" in body
    assert "上海" in body
    assert "2026-08-12" in body
    assert "https://show.maoyan.com/111" in body


def test_feishu_change_contains_diff():
    card = render_feishu_card([_ev_change()])
    body = str(card)
    assert "announced" in body and "on_sale" in body


def test_email_returns_subject_and_html():
    subject, html = render_email([_ev_new(), _ev_change()])
    assert "演唱会" in subject
    assert "Taylor Swift" in html
    assert "<html" in html.lower()
