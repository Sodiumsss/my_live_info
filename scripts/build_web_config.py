"""Build script for the admin Web UI deployed to GitHub Pages.

Reads ADMIN_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY from env. Encrypts the
service key with PBKDF2(ADMIN_KEY) + AES-GCM, then writes web/dist/ with
the static assets + a generated config.js that holds only the ciphertext.

If any required env var is missing, exits 1 so the GitHub Actions build
fails visibly.
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import shutil
import sys
from hashlib import pbkdf2_hmac
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ITERATIONS = 600_000
SALT_BYTES = 16
IV_BYTES = 12
KEY_BYTES = 32  # AES-256

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_SRC = REPO_ROOT / "web"
STATIC_FILES = ("index.html", "app.js", "styles.css")
REQUIRED_ENV = ("ADMIN_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY")


def _require_env() -> dict[str, str]:
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(
            "ERROR: required environment variables not set: " + ", ".join(missing),
            file=sys.stderr,
        )
        print(
            "Set them as GitHub repository secrets (Settings → Secrets and "
            "variables → Actions → New repository secret).",
            file=sys.stderr,
        )
        sys.exit(1)
    return {k: os.environ[k] for k in REQUIRED_ENV}


def _encrypt(admin_key: str, service_key: str) -> dict[str, object]:
    salt = secrets.token_bytes(SALT_BYTES)
    iv = secrets.token_bytes(IV_BYTES)
    key = pbkdf2_hmac("sha256", admin_key.encode("utf-8"), salt, ITERATIONS, KEY_BYTES)
    ciphertext = AESGCM(key).encrypt(iv, service_key.encode("utf-8"), None)
    return {
        "salt": base64.b64encode(salt).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        "iterations": ITERATIONS,
    }


def _copy_static(dist: Path) -> None:
    dist.mkdir(parents=True, exist_ok=True)
    for name in STATIC_FILES:
        src = WEB_SRC / name
        if not src.exists():
            print(f"ERROR: missing static asset {src}", file=sys.stderr)
            sys.exit(1)
        shutil.copy2(src, dist / name)


def _write_config(dist: Path, payload: dict[str, object]) -> None:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    (dist / "config.js").write_text(
        f"window.LIVE_INFO_CONFIG = {body};\n",
        encoding="utf-8",
    )


def main() -> int:
    env = _require_env()
    dist = Path(os.environ.get("WEB_DIST", str(WEB_SRC / "dist")))
    _copy_static(dist)
    encrypted = _encrypt(env["ADMIN_KEY"], env["SUPABASE_SERVICE_KEY"])
    payload = {"supabaseUrl": env["SUPABASE_URL"], **encrypted}
    _write_config(dist, payload)
    print(f"OK: wrote {dist}/config.js and static assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
