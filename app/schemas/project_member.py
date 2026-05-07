from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.project_member import ProjectRole
from app.schemas.common import ORMModel
from app.schemas.user import UserRead


class ProjectMemberCreate(BaseModel):
    email: EmailStr
    role: ProjectRole = ProjectRole.MEMBER


class ProjectMemberUpdate(BaseModel):
    role: ProjectRole


class ProjectMemberRead(ORMModel):
    id: int
    project_id: int
    user_id: int
    role: ProjectRole
    joined_at: datetime
    user: UserRead


class ProjectTransfer(BaseModel):
    new_owner_email: EmailStr
