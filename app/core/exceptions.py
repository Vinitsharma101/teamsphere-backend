from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppException(Exception):
    status_code: int = 400
    detail: str = "Application error"

    def __init__(self, detail: str | None = None, status_code: int | None = None):
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.detail)


class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"


class PermissionDeniedError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Permission denied"


class AuthenticationError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Not authenticated"


class ConflictError(AppException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Conflict"


class ValidationError(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Invalid input"


def _error_response(status_code: int, detail, request: Request) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "status": status_code,
                "detail": detail,
                "path": request.url.path,
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def _app_exc(request: Request, exc: AppException):
        return _error_response(exc.status_code, exc.detail, request)

    @app.exception_handler(StarletteHTTPException)
    async def _http_exc(request: Request, exc: StarletteHTTPException):
        return _error_response(exc.status_code, exc.detail, request)

    @app.exception_handler(RequestValidationError)
    async def _validation_exc(request: Request, exc: RequestValidationError):
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY, exc.errors(), request
        )

    @app.exception_handler(IntegrityError)
    async def _integrity_exc(request: Request, exc: IntegrityError):
        logger.warning("DB integrity error: %s", exc)
        return _error_response(
            status.HTTP_409_CONFLICT, "Database integrity error", request
        )

    @app.exception_handler(SQLAlchemyError)
    async def _db_exc(request: Request, exc: SQLAlchemyError):
        logger.exception("Database error")
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Database error", request
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        logger.exception("Unhandled error")
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error", request
        )
