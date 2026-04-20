from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock

from live_info.llm.verifier import LLMVerifier
from live_info.models import SaleStatus

FIX = Path(__file__).parent / "fixtures"


async def test_verify_parses_json():
    llm = AsyncMock()
    llm.chat.return_value = (FIX / "llm_verify.json").read_text(encoding="utf-8")
    v = LLMVerifier(llm=llm)
    shows = await v.verify("Taylor Swift")
    assert len(shows) == 2
    s = shows[0]
    assert s.raw_artist_name == "Taylor Swift"
    assert s.city == "上海"
    assert s.show_date == date(2026, 8, 12)
    assert s.source == "llm"
    assert s.sale_status == SaleStatus.UNKNOWN
    assert s.llm_source_urls == ["https://www.example.com/news/1"]


async def test_verify_retries_on_bad_json_then_gives_up():
    llm = AsyncMock()
    llm.chat.side_effect = ["not json", "still not json"]
    v = LLMVerifier(llm=llm)
    shows = await v.verify("x")
    assert shows == []
    assert llm.chat.await_count == 2


async def test_verify_recovers_on_retry():
    llm = AsyncMock()
    llm.chat.side_effect = [
        "not json",
        (FIX / "llm_verify.json").read_text(encoding="utf-8"),
    ]
    v = LLMVerifier(llm=llm)
    shows = await v.verify("x")
    assert len(shows) == 2
