from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str | None = None, required: bool = False) -> str | None:
    v = os.getenv(name, default)
    if required and not v:
        raise ValueError(f"Missing required env: {name}")
    return v


@dataclass(frozen=True)
class Config:
    supabase_url: str
    supabase_service_key: str

    llm_base_url: str
    llm_api_key: str
    llm_model: str

    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_pass: str | None
    smtp_from: str | None

    dry_run: bool

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            supabase_url=_env("SUPABASE_URL", required=True),
            supabase_service_key=_env("SUPABASE_SERVICE_KEY", required=True),
            llm_base_url=_env("LLM_BASE_URL", required=True),
            llm_api_key=_env("LLM_API_KEY", required=True),
            llm_model=_env("LLM_MODEL", default="gpt-4o-mini"),
            smtp_host=_env("SMTP_HOST"),
            smtp_port=int(_env("SMTP_PORT", default="587")),
            smtp_user=_env("SMTP_USER"),
            smtp_pass=_env("SMTP_PASS"),
            smtp_from=_env("SMTP_FROM"),
            dry_run=_env("DRY_RUN", default="false").lower() in ("1", "true", "yes"),
        )
