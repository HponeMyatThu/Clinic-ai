"""In-memory rate limiter middleware."""

from __future__ import annotations

import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.schemas.common import ErrorDetail, ErrorResponse, generate_request_id


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter by client IP address."""

    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        # Skip health check endpoints
        if request.url.path.startswith("/api/v1/health") or request.url.path == "/":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old timestamps
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]

        if len(self.requests[client_ip]) >= self.max_requests:
            req_id = getattr(request.state, "request_id", generate_request_id())
            return JSONResponse(
                status_code=429,
                content=ErrorResponse(
                    request_id=req_id,
                    error=ErrorDetail(
                        code="RATE_LIMIT_EXCEEDED",
                        message="Too many requests. Please slow down.",
                    ),
                ).model_dump(),
            )

        self.requests[client_ip].append(now)
        return await call_next(request)

