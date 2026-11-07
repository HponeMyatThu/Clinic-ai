"""Global error handling middleware.

Enforces Section 4 of docx:
Return machine-readable error code and request_id; never include PHI in error details.
"""

from __future__ import annotations

import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorDetail, ErrorResponse, generate_request_id

logger = logging.getLogger("gcms.errors")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        req_id = getattr(request.state, "request_id", generate_request_id())
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                request_id=req_id,
                error=ErrorDetail(
                    code=f"HTTP_{exc.status_code}",
                    message=str(exc.detail),
                ),
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = getattr(request.state, "request_id", generate_request_id())
        first_err = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(loc) for loc in first_err.get("loc", []))
        msg = first_err.get("msg", "Invalid request parameter")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                request_id=req_id,
                error=ErrorDetail(
                    code="VALIDATION_ERROR",
                    message=msg,
                    field=field or None,
                ),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        req_id = getattr(request.state, "request_id", generate_request_id())
        logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                request_id=req_id,
                error=ErrorDetail(
                    code="INTERNAL_SERVER_ERROR",
                    message="An unexpected server error occurred. Please contact system support.",
                ),
            ).model_dump(),
        )

