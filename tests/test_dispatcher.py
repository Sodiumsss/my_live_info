from datetime import date
from unittest.mock import AsyncMock, MagicMock

from live_info.models import Concert, Event, EventKind, SaleStatus, Status, User
from live_info.notifiers.dispatcher import dispatch


def _ev(artist_id, kind=EventKind.NEW, artist_name="T"):
    c = Concert(id="c", artist_id=artist_id, city="上海",
                show_date=date(2026, 8, 12),
                status=Status.VERIFIED, sale_status=SaleStatus.ON_SALE)
    return Event(kind=kind, concert=c, artist_name=artist_name)


async def test_dispatch_only_sends_to_subscribers():
    users = {
        "u1": User(id="u1", name="A", feishu_webhook="https://h/1"),
        "u2": User(id="u2", name="B", email="b@x"),
    }
    subscribers = {"a1": ["u1"]}
    events = [_ev("a1")]

    feishu = AsyncMock()
    feishu.send.return_value = True
    email = MagicMock()
    email.send.return_value = False  # u2 shouldn't be targeted at all

    result = await dispatch(events, users, subscribers, feishu=feishu, email=email)
    assert result["u1"]["feishu"] is True
    assert "u2" not in result
    feishu.send.assert_awaited_once()
    email.send.assert_not_called()


async def test_dispatch_filters_status_change_when_user_opts_out():
    users = {"u1": User(id="u1", name="A", feishu_webhook="https://h/1",
                        notify_on_status_change=False)}
    subscribers = {"a1": ["u1"]}
    events = [_ev("a1", kind=EventKind.STATUS_CHANGE)]

    feishu = AsyncMock()
    email = MagicMock()
    result = await dispatch(events, users, subscribers, feishu=feishu, email=email)
    assert result == {}
    feishu.send.assert_not_awaited()


async def test_dispatch_sends_both_channels_when_configured():
    users = {"u1": User(id="u1", name="A",
                        email="a@x", feishu_webhook="https://h/1")}
    subscribers = {"a1": ["u1"]}
    events = [_ev("a1")]

    feishu = AsyncMock(); feishu.send.return_value = True
    email = MagicMock(); email.send.return_value = True
    result = await dispatch(events, users, subscribers, feishu=feishu, email=email)
    assert result["u1"] == {"feishu": True, "email": True, "events": 1}
