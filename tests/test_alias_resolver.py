import pytest
from unittest.mock import AsyncMock

from live_info.llm.alias_resolver import AliasResolver


class FakeRepo:
    def __init__(self, alias_map=None, artists=None):
        self.alias_map = alias_map or {}         # alias -> artist_id
        self.artists = artists or {}              # canonical_name -> artist_id
        self.recorded = []

    async def find_artist_id_by_alias(self, alias):
        return self.alias_map.get(alias)

    async def upsert_artist(self, canonical_name):
        aid = self.artists.get(canonical_name) or f"a-{canonical_name}"
        self.artists[canonical_name] = aid
        return aid

    async def upsert_alias(self, alias, artist_id, source):
        self.alias_map[alias] = artist_id
        self.recorded.append((alias, artist_id, source))


async def test_alias_hit_returns_cached():
    repo = FakeRepo(alias_map={"Taylor Swift": "a1"})
    llm = AsyncMock()
    r = AliasResolver(repo=repo, llm=llm)
    aid = await r.resolve("Taylor Swift")
    assert aid == "a1"
    llm.chat.assert_not_awaited()


async def test_alias_miss_asks_llm_and_caches():
    repo = FakeRepo()
    llm = AsyncMock()
    llm.chat.return_value = '{"canonical_name": "Taylor Swift"}'
    r = AliasResolver(repo=repo, llm=llm)
    aid = await r.resolve("霉霉")
    assert aid == "a-Taylor Swift"
    assert repo.alias_map["霉霉"] == "a-Taylor Swift"
    assert repo.recorded[-1][2] == "llm"
    # canonical 本身也应该被登记为 alias=canonical（便于下次命中）
    assert repo.alias_map["Taylor Swift"] == "a-Taylor Swift"


async def test_alias_miss_llm_returns_bad_json_returns_none():
    repo = FakeRepo()
    llm = AsyncMock()
    llm.chat.return_value = "sorry I don't know"
    r = AliasResolver(repo=repo, llm=llm)
    aid = await r.resolve("???")
    assert aid is None
