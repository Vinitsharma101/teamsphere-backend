from typing import List, Tuple

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_project_role
from app.db.session import get_db
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project_member import (
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberUpdate,
)
from app.services.project_member import ProjectMemberService

router = APIRouter(prefix="/projects/{project_id}/members", tags=["Project Members"])


@router.get("", response_model=List[ProjectMemberRead])
def list_members(
    project_id: int,
    db: Session = Depends(get_db),
    _: Tuple[Project, ProjectMember] = Depends(
        require_project_role(ProjectRole.VIEWER)
    ),
):
    return ProjectMemberService(db).list(project_id)


@router.post(
    "", response_model=ProjectMemberRead, status_code=status.HTTP_201_CREATED
)
def add_member(
    project_id: int,
    payload: ProjectMemberCreate,
    db: Session = Depends(get_db),
    _: Tuple[Project, ProjectMember] = Depends(
        require_project_role(ProjectRole.ADMIN)
    ),
):
    return ProjectMemberService(db).add(
        project_id, email=payload.email, role=payload.role
    )


@router.patch("/{user_id}", response_model=ProjectMemberRead)
def update_member_role(
    project_id: int,
    user_id: int,
    payload: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: Tuple[Project, ProjectMember] = Depends(
        require_project_role(ProjectRole.ADMIN)
    ),
):
    return ProjectMemberService(db).update_role(
        project_id, user_id, payload.role, current_user.id
    )


@router.delete("/{user_id}", response_model=MessageResponse)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    _: Tuple[Project, ProjectMember] = Depends(
        require_project_role(ProjectRole.ADMIN)
    ),
):
    ProjectMemberService(db).remove(project_id, user_id)
    return MessageResponse(message="Member removed")


leave_router = APIRouter(prefix="/projects/{project_id}", tags=["Project Members"])


@leave_router.post("/leave", response_model=MessageResponse)
def leave_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: Tuple[Project, ProjectMember] = Depends(
        require_project_role(ProjectRole.VIEWER)
    ),
):
    ProjectMemberService(db).leave(project_id, current_user.id)
    return MessageResponse(message="Left the project")
