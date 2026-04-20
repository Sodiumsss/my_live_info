import httpx
import respx
import pytest

from live_info.llm.client import LLMClient, LLMError


@respx.mock
async def test_chat_returns_content():
    respx.post("https://llm.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "hello"}}]},
        )
    )
    async with LLMClient(base_url="https://llm.example.com/v1", api_key="k", model="m") as c:
        out = await c.chat([{"role": "user", "content": "hi"}])
    assert out == "hello"


@respx.mock
async def test_chat_raises_on_http_error():
    respx.post("https://llm.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(500, text="boom")
    )
    async with LLMClient(base_url="https://llm.example.com/v1", api_key="k", model="m") as c:
        with pytest.raises(LLMError):
            await c.chat([{"role": "user", "content": "hi"}])


@respx.mock
async def test_chat_sends_tools_when_enabled():
    route = respx.post("https://llm.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "x"}}]})
    )
    async with LLMClient(base_url="https://llm.example.com/v1", api_key="k", model="m") as c:
        await c.chat([{"role": "user", "content": "hi"}], enable_web_search=True)
    sent = route.calls[0].request
    body = sent.content.decode()
    assert "web_search" in body
