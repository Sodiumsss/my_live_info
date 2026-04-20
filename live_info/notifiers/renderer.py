from __future__ import annotations

from jinja2 import Environment, select_autoescape

from live_info.models import Event, EventKind


_STATUS_ZH = {
    "verified": "已验证",
    "unverified": "未验证",
    "announced": "未开票",
    "on_sale": "已开票",
    "sold_out": "已售罄",
    "unknown": "未知",
}


def _zh(v: str) -> str:
    return _STATUS_ZH.get(v, v)


def render_feishu_card(events: list[Event]) -> dict:
    elements: list[dict] = []
    for e in events:
        c = e.concert
        if e.kind == EventKind.NEW:
            tag = "🆕 新演唱会"
            lines = [
                f"**{e.artist_name}** · {c.city} · {c.show_date.isoformat()}",
                f"场馆：{c.venue or '待定'}",
                f"状态：{_zh(c.status.value)} · 售票：{_zh(c.sale_status.value)}",
            ]
            if c.source_url:
                lines.append(f"[查看详情]({c.source_url})")
        else:
            tag = "🔄 状态变化"
            lines = [f"**{e.artist_name}** · {c.city} · {c.show_date.isoformat()}"]
            for field, (a, b) in e.changes.items():
                lines.append(f"{field}: {a} → {b}")

        elements.append({"tag": "div", "text": {
            "tag": "lark_md",
            "content": f"**{tag}**\n" + "\n".join(lines),
        }})
        elements.append({"tag": "hr"})

    return {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": "演唱会信息更新"}},
            "elements": elements,
        },
    }


_EMAIL_TMPL = Environment(autoescape=select_autoescape(["html"])).from_string("""\
<html><body style="font-family:sans-serif;">
<h2>演唱会信息更新</h2>
{% for e in events %}
  <div style="border:1px solid #eee;padding:12px;margin:8px 0;">
    <strong>
      {% if e.kind.value == 'new' %}🆕 新演唱会{% else %}🔄 状态变化{% endif %}
    </strong><br>
    {{ e.artist_name }} · {{ e.concert.city }} · {{ e.concert.show_date.isoformat() }}<br>
    {% if e.kind.value == 'new' %}
      场馆：{{ e.concert.venue or '待定' }}<br>
      状态：{{ zh(e.concert.status.value) }} · 售票：{{ zh(e.concert.sale_status.value) }}<br>
      {% if e.concert.source_url %}
        <a href="{{ e.concert.source_url }}">查看详情</a>
      {% endif %}
    {% else %}
      {% for field, pair in e.changes.items() %}
        {{ field }}: {{ zh(pair[0]|string) }} → {{ zh(pair[1]|string) }}<br>
      {% endfor %}
    {% endif %}
  </div>
{% endfor %}
</body></html>""")


def render_email(events: list[Event]) -> tuple[str, str]:
    subject = f"[演唱会] {len(events)} 条更新"
    html = _EMAIL_TMPL.render(events=events, zh=_zh)
    return subject, html
