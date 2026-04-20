from __future__ import annotations

import json
import logging
from typing import Protocol

log = logging.getLogger(__name__)


class AliasRepo(Protocol):
    async def find_artist_id_by_alias(self, alias: str) -> str | None: ...
    async def upsert_artist(self, canonical_name: str) -> str: ...
    async def upsert_alias(self, alias: str, artist_id: str, source: str) -> None: ...


class LLMLike(Protocol):
    async def chat(self, messages, *, enable_web_search: bool = False, response_format_json: bool = False) -> str: ...


_SYSTEM_PROMPT = (
    "你是一个艺人别名规范化助手。用户会给你一个中文/英文/昵称/绰号，"
    "请返回 JSON：{\"canonical_name\": \"<艺人的官方英文名（若无则中文本名）>\"}。"
    "如果你无法判断是哪个真实存在的艺人，返回 {\"canonical_name\": null}。"
    "只返回 JSON，不要任何额外文字。"
)


class AliasResolver:
    def __init__(self, repo: AliasRepo, llm: LLMLike):
        self.repo = repo
        self.llm = llm

    async def resolve(self, raw_name: str) -> str | None:
        raw_name = raw_name.strip()
        if not raw_name:
            return None

        hit = await self.repo.find_artist_id_by_alias(raw_name)
        if hit:
            return hit

        try:
            content = await self.llm.chat(
                [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": raw_name},
                ],
                response_format_json=True,
            )
            data = json.loads(content)
            canonical = data.get("canonical_name")
        except (json.JSONDecodeError, Exception) as e:
            log.warning("alias LLM failed for %r: %s", raw_name, e)
            return None

        if not canonical:
            return None

        artist_id = await self.repo.upsert_artist(canonical)
        await self.repo.upsert_alias(raw_name, artist_id, source="llm")
        if canonical != raw_name:
            await self.repo.upsert_alias(canonical, artist_id, source="llm")
        return artist_id
