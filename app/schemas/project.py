from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedRead


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=10_000)
    due_date: Optional[date] = None
    status: str = Field("active", max_length=40)


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=10_000)
    due_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=40)


class ProjectRead(TimestampedRead):
    id: int
    name: str
    description: Optional[str]
    due_date: Optional[date]
    status: str
    created_by: int
