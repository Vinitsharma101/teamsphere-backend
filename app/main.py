from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.limiter import limiter
from app.core.logging import get_logger, setup_logging
from app.db.session import get_db
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

logger = get_logger(__name__)


OPENAPI_TAGS = [
    {"name": "Auth", "description": "Signup, login, token refresh, current user."},
    {"name": "Projects", "description": "Project CRUD and ownership transfer."},
    {
        "name": "Project Members",
        "description": "Manage project membership and roles (admin/member/viewer).",
    },
    {"name": "Tasks", "description": "Project-scoped task CRUD with filters and pagination."},
    {"name": "Health", "description": "Service health checks."},
]


def _rate_limit_handler(request, exc: RateLimitExceeded):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "status": 429,
                "detail": f"Rate limit exceeded: {exc.detail}",
                "path": request.url.path,
            }
        },
    )


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description=(
            "TeamSphere — project management backend. "
            "Cookie-based JWT authentication, RBAC (admin/member/viewer), "
            "project-scoped tasks with filtering and pagination."
        ),
        debug=settings.DEBUG,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_tags=OPENAPI_TAGS,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if settings.SECURITY_HEADERS_ENABLED:
        app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SlowAPIMiddleware)

    register_exception_handlers(app)

    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["Health"], summary="Liveness + DB check")
    def health(db: Session = Depends(get_db)):
        db_ok = True
        try:
            db.execute(text("SELECT 1"))
        except Exception:
            logger.exception("Health check DB error")
            db_ok = False
        return {
            "status": "ok" if db_ok else "degraded",
            "env": settings.APP_ENV,
            "database": "ok" if db_ok else "error",
        }

    @app.get("/", include_in_schema=False)
    def root():
        return {
            "service": settings.APP_NAME,
            "version": "1.0.0",
            "docs": "/docs" if not settings.is_production else None,
        }

    return app


app = create_app()
