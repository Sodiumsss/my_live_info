"""Build the encrypted config.js for the admin Web UI.

Reads ADMIN_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY from env. Encrypts the
service key with PBKDF2(ADMIN_KEY) + AES-GCM, then writes the resulting
``config.js`` into the Vite build output (``web/dist`` by default).

Run this AFTER ``npm run build`` so that ``web/dist`` already contains the
Vite-generated assets. The CI workflow at ``.github/workflows/pages.yml``
chains the two steps together.

Exits non-zero if any required env var is missing or the dist directory
doesn't exist — the GitHub Actions build fails visibly in that case.
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import sys
from hashlib import pbkdf2_hmac
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ITERATIONS = 600_000
SALT_BYTES = 16
IV_BYTES = 12
KEY_BYTES = 32  # AES-256

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "web" / "dist"
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


def _write_config(dist: Path, payload: dict[str, object]) -> None:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    (dist / "config.js").write_text(
        f"window.LIVE_INFO_CONFIG = {body};\n",
        encoding="utf-8",
    )


def main() -> int:
    env = _require_env()
    dist = Path(os.environ.get("WEB_DIST", str(DIST_DIR)))
    if not dist.is_dir():
        print(
            f"ERROR: dist directory {dist} does not exist. "
            "Run `npm --prefix web ci && npm --prefix web run build` first.",
            file=sys.stderr,
        )
        sys.exit(1)
    encrypted = _encrypt(env["ADMIN_KEY"], env["SUPABASE_SERVICE_KEY"])
    payload = {"supabaseUrl": env["SUPABASE_URL"], **encrypted}
    _write_config(dist, payload)
    print(f"OK: wrote {dist}/config.js")
    return 0


if __name__ == "__main__":
    sys.exit(main())
