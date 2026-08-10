"""Structured error envelope: {"error": {"code", "message", "request_id"}}."""
from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Domain error that serializes to the standard error envelope."""

    def __init__(self, status_code: int, code: str, message: str, headers: dict | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers or {}
        super().__init__(message)


def error_body(code: str, message: str, request_id: str) -> dict:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.code, exc.message, request_id),
        headers=exc.headers,
    )
