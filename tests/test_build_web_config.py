"""Tests for scripts/build_web_config.py (admin Web UI build step)."""
from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "build_web_config.py"


def _run(env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _base_env(tmp_path: Path, **overrides) -> dict[str, str]:
    env = {
        "PATH": "/usr/bin:/bin:/usr/local/bin",
        "HOME": str(tmp_path),
        "ADMIN_KEY": "correct-horse-battery-staple-42",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SERVICE_KEY": "sbp_secret_service_role_token_xyz",
        "WEB_DIST": str(tmp_path / "dist"),
    }
    env.update(overrides)
    return env


@pytest.mark.parametrize("missing", ["ADMIN_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY"])
def test_exits_when_required_env_missing(tmp_path, missing):
    env = _base_env(tmp_path)
    env.pop(missing)
    result = _run(env, REPO_ROOT)
    assert result.returncode == 1, result.stdout + result.stderr
    assert missing in (result.stdout + result.stderr)


def test_produces_config_and_static_files(tmp_path):
    env = _base_env(tmp_path)
    result = _run(env, REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr

    dist = Path(env["WEB_DIST"])
    assert (dist / "index.html").exists()
    assert (dist / "app.js").exists()
    assert (dist / "styles.css").exists()

    config_js = (dist / "config.js").read_text(encoding="utf-8")
    m = re.search(r"window\.LIVE_INFO_CONFIG\s*=\s*(\{.*?\});?\s*$", config_js, re.S)
    assert m, f"config.js shape unexpected:\n{config_js}"
    payload = json.loads(m.group(1))

    for key in ("supabaseUrl", "salt", "iv", "ciphertext", "iterations"):
        assert key in payload, f"missing {key} in {payload}"
    assert payload["supabaseUrl"] == env["SUPABASE_URL"]
    assert payload["iterations"] >= 100_000
    assert env["SUPABASE_SERVICE_KEY"] not in config_js, "service key leaked in plaintext!"


def test_roundtrip_encrypt_decrypt(tmp_path):
    env = _base_env(tmp_path)
    result = _run(env, REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr

    config_js = (Path(env["WEB_DIST"]) / "config.js").read_text(encoding="utf-8")
    payload = json.loads(re.search(r"=\s*(\{.*?\});?\s*$", config_js, re.S).group(1))

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from hashlib import pbkdf2_hmac

    salt = base64.b64decode(payload["salt"])
    iv = base64.b64decode(payload["iv"])
    ciphertext = base64.b64decode(payload["ciphertext"])
    key = pbkdf2_hmac("sha256", env["ADMIN_KEY"].encode(), salt, payload["iterations"], 32)
    plaintext = AESGCM(key).decrypt(iv, ciphertext, None).decode("utf-8")

    assert plaintext == env["SUPABASE_SERVICE_KEY"]


def test_wrong_password_fails_decrypt(tmp_path):
    env = _base_env(tmp_path)
    result = _run(env, REPO_ROOT)
    assert result.returncode == 0

    config_js = (Path(env["WEB_DIST"]) / "config.js").read_text(encoding="utf-8")
    payload = json.loads(re.search(r"=\s*(\{.*?\});?\s*$", config_js, re.S).group(1))

    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from hashlib import pbkdf2_hmac

    salt = base64.b64decode(payload["salt"])
    iv = base64.b64decode(payload["iv"])
    ciphertext = base64.b64decode(payload["ciphertext"])
    wrong_key = pbkdf2_hmac("sha256", b"wrong-password", salt, payload["iterations"], 32)
    with pytest.raises(InvalidTag):
        AESGCM(wrong_key).decrypt(iv, ciphertext, None)
