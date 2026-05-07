from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.limiter import limiter
from app.core.security import (
    REFRESH_COOKIE_NAME,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    set_auth_cookies,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit(settings.RATE_LIMIT_SIGNUP)
def signup(
    request: Request,
    payload: UserCreate,
    response: Response,
    db: Session = Depends(get_db),
):
    user = AuthService(db).register(payload)
    access, refresh = AuthService.issue_tokens(user.id)
    set_auth_cookies(response, access, refresh)
    return AuthResponse(message="User registered", user=UserRead.model_validate(user))


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate and set auth cookies",
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(
    request: Request,
    payload: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    user = AuthService(db).authenticate(payload)
    access, refresh = AuthService.issue_tokens(user.id)
    set_auth_cookies(response, access, refresh)
    return AuthResponse(message="Login successful", user=UserRead.model_validate(user))


@router.post(
    "/refresh",
    response_model=MessageResponse,
    summary="Rotate access + refresh tokens using the refresh cookie",
)
@limiter.limit(settings.RATE_LIMIT_REFRESH)
def refresh_tokens(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
):
    if not refresh_token:
        raise AuthenticationError("Missing refresh token")
    user_id = decode_token(refresh_token, expected_type="refresh")
    set_auth_cookies(response, create_access_token(user_id), create_refresh_token(user_id))
    return MessageResponse(message="Tokens refreshed")


@router.post("/logout", response_model=MessageResponse, summary="Clear auth cookies")
def logout(response: Response):
    clear_auth_cookies(response)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserRead, summary="Current authenticated user")
def me(current_user: User = Depends(get_current_user)):
    return current_user
