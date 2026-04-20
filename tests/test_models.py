from datetime import date, datetime, timezone
from live_info.models import Artist, Concert, RawShow, User, SaleStatus, Status


def test_concert_unique_key():
    a = Artist(id="a1", canonical_name="Taylor Swift")
    c = Concert(
        id="c1",
        artist_id=a.id,
        city="Shanghai",
        show_date=date(2026, 8, 12),
        venue="Mercedes-Benz Arena",
        status=Status.VERIFIED,
        sale_status=SaleStatus.UNKNOWN,
    )
    assert c.unique_key() == ("a1", "Shanghai", date(2026, 8, 12))


def test_raw_show_from_maoyan_minimal():
    raw = RawShow(
        raw_artist_name="霉霉",
        city="上海",
        show_date=date(2026, 8, 12),
        venue="梅奔",
        sale_status=SaleStatus.ON_SALE,
        source="maoyan",
        source_url="https://show.maoyan.com/123",
        source_id="123",
    )
    assert raw.source == "maoyan"


def test_user_has_channel():
    u = User(id="u1", name="Alice", email="a@x.com", feishu_webhook=None)
    assert u.has_email()
    assert not u.has_feishu()
