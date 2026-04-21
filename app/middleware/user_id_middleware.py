from __future__ import annotations

import logging

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

_PROTECTED_PREFIX = "/api/users/"


class UserIdMiddleware(BaseHTTPMiddleware):
    """Extract x-user-id header from requests and attach to request state.

    For all endpoints under /api/users/*, the header is required. If missing,
    returns 401. For health/docs/other endpoints the header is optional.
    """

    async def dispatch(self, request: Request, call_next):
        user_id = request.headers.get("x-user-id")

        if user_id:
            request.state.user_id = user_id
            logger.info(
                "[AUDIT] user=%s %s %s", user_id, request.method, request.url.path
            )
        elif request.url.path.startswith(_PROTECTED_PREFIX):
            return JSONResponse(
                {"detail": "Unauthorized: x-user-id header required"},
                status_code=401,
            )

        return await call_next(request)
