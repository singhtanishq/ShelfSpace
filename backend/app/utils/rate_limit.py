"""Minimal in-process sliding-window rate limiter for sensitive endpoints.

Suitable for a single-process deployment; swap for a distributed limiter
(Redis-based) when scaling beyond one worker.
"""

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from app.utils.exceptions import RateLimitError

_lock = threading.Lock()
_buckets: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)


def _client_ip(request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(request, bucket: str, limit: int, window_seconds: int) -> None:
    """Raise RateLimitError when `limit` requests within `window_seconds` are exceeded."""
    key = (bucket, _client_ip(request))
    now = time.monotonic()
    with _lock:
        q = _buckets[key]
        while q and q[0] <= now - window_seconds:
            q.popleft()
        if len(q) >= limit:
            raise RateLimitError(
                "Too many attempts. Please try again shortly.",
                details={"retry_after_seconds": int(window_seconds)},
            )
        q.append(now)
