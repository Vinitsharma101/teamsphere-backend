from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
)
from app.models.project import Project
from app.models.project_member import ProjectRole
from app.repositories.project import ProjectRepository
from app.repositories.project_member import ProjectMemberRepository
from app.repositories.user import UserRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.projects = ProjectRepository(db)
        self.members = ProjectMemberRepository(db)
        self.users = UserRepository(db)

    def create(self, payload: ProjectCreate, user_id: int) -> Project:
        project = self.projects.create(
            data=payload.model_dump(), created_by=user_id
        )
        self.members.add(project_id=project.id, user_id=user_id, role=ProjectRole.ADMIN)
        self.db.commit()
        self.db.refresh(project)
        return project

    def list_for_user(self, user_id: int) -> List[Project]:
        ids = self.members.list_project_ids_for_user(user_id)
        if not ids:
            return []
        return self.projects.list_by_ids(ids)

    def update(self, project: Project, payload: ProjectUpdate) -> Project:
        data = payload.model_dump(exclude_unset=True)
        if data:
            self.projects.update(project, data)
            self.db.commit()
            self.db.refresh(project)
        return project

    def delete(self, project: Project, actor_user_id: int) -> None:
        if project.created_by != actor_user_id:
            raise PermissionDeniedError("Only the project owner can delete this project")
        self.projects.delete(project)
        self.db.commit()

    def transfer_ownership(
        self, project: Project, *, new_owner_email: str, actor_user_id: int
    ) -> Project:
        if project.created_by != actor_user_id:
            raise PermissionDeniedError("Only the current owner can transfer ownership")

        new_owner = self.users.get_by_email(new_owner_email)
        if not new_owner:
            raise NotFoundError("Target user not found")
        if new_owner.id == actor_user_id:
            raise ConflictError("You already own this project")

        new_owner_member = self.members.get(project.id, new_owner.id)
        if not new_owner_member:
            self.members.add(
                project_id=project.id, user_id=new_owner.id, role=ProjectRole.ADMIN
            )
        elif new_owner_member.role != ProjectRole.ADMIN:
            self.members.update_role(new_owner_member, ProjectRole.ADMIN)

        project.created_by = new_owner.id
        self.db.commit()
        self.db.refresh(project)
        return project
