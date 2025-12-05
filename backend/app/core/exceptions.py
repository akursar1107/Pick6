"""Custom exception handlers"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class First6Exception(Exception):
    """Base exception for First6 application"""

    pass


class NotFoundError(First6Exception):
    """Resource not found"""

    pass


class ValidationError(First6Exception):
    """Validation error"""

    pass


class DuplicatePickError(ValidationError):
    """Duplicate pick for user and game"""

    pass


class GameLockedError(ValidationError):
    """Game is locked (kickoff time has passed)"""

    pass


class UnauthorizedError(First6Exception):
    """User not authorized for this operation"""

    pass


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )
