import pytest
from live_info.config import Config


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "svc")
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example.com/v1")
    monkeypatch.setenv("LLM_API_KEY", "key")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "u")
    monkeypatch.setenv("SMTP_PASS", "p")
    monkeypatch.setenv("SMTP_FROM", "bot@x.com")
    monkeypatch.setenv("DRY_RUN", "true")

    cfg = Config.from_env()
    assert cfg.supabase_url == "https://x.supabase.co"
    assert cfg.llm_model == "gpt-4o-mini"
    assert cfg.dry_run is True
    assert cfg.smtp_port == 587


def test_config_missing_required(monkeypatch):
    for k in ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "LLM_BASE_URL", "LLM_API_KEY"]:
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(ValueError, match="Missing required env"):
        Config.from_env()
