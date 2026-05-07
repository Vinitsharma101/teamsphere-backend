from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import TimestampedRead


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class UserRead(TimestampedRead):
    id: int
    name: str
    email: EmailStr
    is_active: bool
