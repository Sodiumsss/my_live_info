from datetime import date
from unittest.mock import MagicMock, patch

import httpx
import respx

from live_info.models import Concert, Event, EventKind, SaleStatus, Status, User
from live_info.notifiers.email import EmailNotifier, SMTPConfig
from live_info.notifiers.feishu import FeishuNotifier


def _ev():
    c = Concert(id="c1", artist_id="a1", city="上海",
                show_date=date(2026, 8, 12),
                status=Status.VERIFIED, sale_status=SaleStatus.ON_SALE)
    return Event(kind=EventKind.NEW, concert=c, artist_name="Taylor Swift")


@respx.mock
async def test_feishu_posts_to_webhook():
    route = respx.post("https://open.feishu.cn/hook/abc").mock(
        return_value=httpx.Response(200, json={"code": 0})
    )
    user = User(id="u1", name="Alice", feishu_webhook="https://open.feishu.cn/hook/abc")
    async with FeishuNotifier() as n:
        ok = await n.send(user, [_ev()])
    assert ok
    assert route.called


@respx.mock
async def test_feishu_returns_false_on_http_error():
    respx.post("https://open.feishu.cn/hook/abc").mock(return_value=httpx.Response(500))
    user = User(id="u1", name="Alice", feishu_webhook="https://open.feishu.cn/hook/abc")
    async with FeishuNotifier() as n:
        ok = await n.send(user, [_ev()])
    assert ok is False


def test_email_calls_smtp_send():
    cfg = SMTPConfig(host="smtp.x", port=587, user="u", password="p", sender="bot@x")
    user = User(id="u1", name="Alice", email="a@x.com")
    with patch("live_info.notifiers.email.smtplib.SMTP") as SMTP:
        smtp = MagicMock()
        SMTP.return_value.__enter__.return_value = smtp
        n = EmailNotifier(cfg)
        ok = n.send(user, [_ev()])
    assert ok
    assert smtp.send_message.called
