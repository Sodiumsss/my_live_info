from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Protocol

from live_info.models import RawShow, SaleStatus

log = logging.getLogger(__name__)


class LLMLike(Protocol):
    async def chat(self, messages, *, enable_web_search: bool = False, response_format_json: bool = False) -> str: ...


_SYSTEM = (
    "你是一个演唱会信息搜索助手。用户会给你一个艺人名，"
    "请用联网搜索工具查询该艺人 2026 年及之后已官宣的演唱会，"
    "返回 JSON，格式如下，不要任何额外文字：\n"
    "{\"shows\": ["
    "{\"artist\": str, \"city\": str, \"date\": \"YYYY-MM-DD\", "
    "\"venue\": str | null, \"sources\": [str]}"
    "]}"
)

_REPAIR = "你刚才的输出不是合法 JSON。请严格按要求只返回 JSON，不要 markdown 或其他文本。"


class LLMVerifier:
    def __init__(self, llm: LLMLike):
        self.llm = llm

    async def verify(self, artist_name: str) -> list[RawShow]:
        messages = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": artist_name},
        ]
        for attempt in range(2):
            try:
                content = await self.llm.chat(
                    messages,
                    enable_web_search=True,
                    response_format_json=True,
                )
                data = json.loads(content)
                return self._parse(artist_name, data)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                log.warning("LLM verify attempt %d failed for %r: %s", attempt, artist_name, e)
                messages.append({"role": "assistant", "content": content if 'content' in dir() else ""})
                messages.append({"role": "user", "content": _REPAIR})
        return []

    @staticmethod
    def _parse(artist_name: str, data: dict) -> list[RawShow]:
        out: list[RawShow] = []
        for it in data.get("shows", []):
            try:
                d = datetime.strptime(it["date"], "%Y-%m-%d").date()
            except (KeyError, ValueError):
                continue
            out.append(
                RawShow(
                    raw_artist_name=artist_name,
                    city=it.get("city") or "",
                    show_date=d,
                    venue=it.get("venue"),
                    sale_status=SaleStatus.UNKNOWN,
                    source="llm",
                    llm_source_urls=list(it.get("sources") or []),
                )
            )
        return out
