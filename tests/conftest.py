"""Pytest global fixtures.

Strip HTTP/SOCKS proxy env vars for the whole test session so httpx doesn't
try to route mocked requests through a real proxy.
"""

import os

_PROXY_VARS = (
    "ALL_PROXY",
    "all_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "HTTPS_PROXY",
    "https_proxy",
    "NO_PROXY",
    "no_proxy",
)

for _v in _PROXY_VARS:
    os.environ.pop(_v, None)
