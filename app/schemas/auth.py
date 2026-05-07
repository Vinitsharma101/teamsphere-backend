from pydantic import BaseModel

from app.schemas.user import UserRead


class AuthResponse(BaseModel):
    message: str
    user: UserRead
