from __future__ import annotations

from typing import Any

import httpx


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def __aenter__(self) -> "LLMClient":
        return self

    async def __aexit__(self, *exc) -> None:
        await self._client.aclose()

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        enable_web_search: bool = False,
        response_format_json: bool = False,
    ) -> str:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        if enable_web_search:
            body["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the public web for up-to-date information.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query string.",
                                },
                            },
                            "required": ["query"],
                        },
                    },
                }
            ]
            body["tool_choice"] = "auto"
        if response_format_json:
            body["response_format"] = {"type": "json_object"}

        r = await self._client.post(f"{self.base_url}/chat/completions", json=body)
        if r.status_code >= 400:
            raise LLMError(f"LLM {r.status_code}: {r.text[:500]}")
        try:
            data = r.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            raise LLMError(f"bad LLM response: {e}") from e
