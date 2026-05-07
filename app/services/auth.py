from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserLogin


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: UserCreate) -> User:
        if self.users.get_by_email(payload.email):
            raise ConflictError("Email already registered")

        user = self.users.create(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, payload: UserLogin) -> User:
        user = self.users.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active:
            raise AuthenticationError("Account disabled")
        return user

    @staticmethod
    def issue_tokens(user_id: int) -> tuple[str, str]:
        return create_access_token(user_id), create_refresh_token(user_id)
