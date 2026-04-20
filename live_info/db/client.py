from __future__ import annotations

from supabase import Client, create_client


def make_client(url: str, service_key: str) -> Client:
    return create_client(url, service_key)
