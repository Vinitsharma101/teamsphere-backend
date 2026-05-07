from typing import List, Tuple

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_project_role
from app.db.session import get_db
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.project_member import ProjectTransfer
from app.services.project import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ProjectService(db).create(payload, current_user.id)


@router.get("", response_model=List[ProjectRead])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ProjectService(db).list_for_user(current_user.id)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    ctx: Tuple[Project, ProjectMember] = Depends(
        require_project_role(ProjectRole.VIEWER)
    ),
):
    project, _ = ctx
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    ctx: Tuple[Project, ProjectMember] = Depends(
        require_project_role(ProjectRole.ADMIN)
    ),
):
    project, _ = ctx
    return ProjectService(db).update(project, payload)


@router.delete("/{project_id}", response_model=MessageResponse)
def delete_project(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ctx: Tuple[Project, ProjectMember] = Depends(
        require_project_role(ProjectRole.ADMIN)
    ),
):
    project, _ = ctx
    ProjectService(db).delete(project, current_user.id)
    return MessageResponse(message="Project deleted")


@router.post("/{project_id}/transfer", response_model=ProjectRead)
def transfer_ownership(
    payload: ProjectTransfer,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ctx: Tuple[Project, ProjectMember] = Depends(
        require_project_role(ProjectRole.ADMIN)
    ),
):
    project, _ = ctx
    return ProjectService(db).transfer_ownership(
        project,
        new_owner_email=payload.new_owner_email,
        actor_user_id=current_user.id,
    )
