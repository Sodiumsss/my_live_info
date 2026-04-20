from unittest.mock import MagicMock

from live_info.db.repositories import Repository


class FakeTable:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.last = None

    def select(self, *_):
        self.last = ("select",)
        return self

    def eq(self, *_):
        return self

    def execute(self):
        return MagicMock(data=self.rows)

    def upsert(self, data, **_):
        self.last = ("upsert", data)
        return self


class FakeClient:
    def __init__(self, tables):
        self._tables = tables

    def table(self, name):
        return self._tables[name]


def test_get_subscribed_artists_dedupes():
    subs = FakeTable(
        rows=[
            {"artist_id": "a1", "artists": {"canonical_name": "Taylor Swift"}},
            {"artist_id": "a1", "artists": {"canonical_name": "Taylor Swift"}},
            {"artist_id": "a2", "artists": {"canonical_name": "Coldplay"}},
        ]
    )
    repo = Repository(FakeClient({"subscriptions": subs}))
    import asyncio

    out = asyncio.run(repo.get_subscribed_artists())
    assert sorted((a.id, a.canonical_name) for a in out) == [
        ("a1", "Taylor Swift"),
        ("a2", "Coldplay"),
    ]
