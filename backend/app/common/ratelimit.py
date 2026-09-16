"""Minimal in-process rate limiting for abuse-prone endpoints.

The Architecture doc lists rate limiting as an API-layer responsibility; this is
the smallest thing that discharges it for the endpoints that actually need it.

Scope: counters live in this process's memory, which is correct for the current
single-instance deployment. Running more than one instance divides the effective
limit by the instance count — move this to Redis at the same time as the
WebSocket backplane (see the Stage 3 notes in the deployment roadmap).
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        hits = self._hits[key]
        while hits and hits[0] < cutoff:
            hits.popleft()
        if len(hits) >= self.max_requests:
            return False
        hits.append(now)
        return True


def _client_key(request: Request) -> str:
    # Behind Render/Cloudflare the socket peer is the proxy, so prefer the
    # forwarded client address when present.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(limiter: SlidingWindowLimiter, name: str):
    """Build a FastAPI dependency enforcing `limiter` per client address."""

    async def _dependency(request: Request) -> None:
        if not limiter.allow(f"{name}:{_client_key(request)}"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="too many requests, try again shortly",
            )

    return _dependency
