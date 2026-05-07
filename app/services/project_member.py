from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.models.project_member import ProjectMember, ProjectRole
from app.repositories.project import ProjectRepository
from app.repositories.project_member import ProjectMemberRepository
from app.repositories.user import UserRepository


class ProjectMemberService:
    def __init__(self, db: Session):
        self.db = db
        self.members = ProjectMemberRepository(db)
        self.users = UserRepository(db)
        self.projects = ProjectRepository(db)

    def list(self, project_id: int) -> List[ProjectMember]:
        return self.members.list_for_project(project_id)

    def add(self, project_id: int, *, email: str, role: ProjectRole) -> ProjectMember:
        user = self.users.get_by_email(email)
        if not user:
            raise NotFoundError("User not found")
        if self.members.get(project_id, user.id):
            raise ConflictError("User is already a member of this project")

        member = self.members.add(project_id=project_id, user_id=user.id, role=role)
        self.db.commit()
        self.db.refresh(member)
        return member

    def update_role(
        self,
        project_id: int,
        target_user_id: int,
        new_role: ProjectRole,
        actor_user_id: int,
    ) -> ProjectMember:
        member = self.members.get(project_id, target_user_id)
        if not member:
            raise NotFoundError("Member not found")

        project = self.projects.get(project_id)
        if not project:
            raise NotFoundError("Project not found")

        if target_user_id == project.created_by and new_role != ProjectRole.ADMIN:
            raise PermissionDeniedError(
                "Cannot demote the project owner. Transfer ownership first."
            )

        if (
            member.role == ProjectRole.ADMIN
            and new_role != ProjectRole.ADMIN
            and self.members.count_admins(project_id) <= 1
        ):
            raise ConflictError("Cannot demote the last remaining admin")

        self.members.update_role(member, new_role)
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove(self, project_id: int, target_user_id: int) -> None:
        project = self.projects.get(project_id)
        if not project:
            raise NotFoundError("Project not found")

        if target_user_id == project.created_by:
            raise PermissionDeniedError(
                "Cannot remove the project owner. Transfer ownership first."
            )

        member = self.members.get(project_id, target_user_id)
        if not member:
            raise NotFoundError("Member not found")

        self.members.remove(member)
        self.db.commit()

    def leave(self, project_id: int, user_id: int) -> None:
        project = self.projects.get(project_id)
        if not project:
            raise NotFoundError("Project not found")

        if user_id == project.created_by:
            raise PermissionDeniedError(
                "Owner cannot leave. Transfer ownership or delete the project."
            )

        member = self.members.get(project_id, user_id)
        if not member:
            raise NotFoundError("You are not a member of this project")

        self.members.remove(member)
        self.db.commit()
