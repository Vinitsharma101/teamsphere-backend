from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.project_member import ProjectMember, ProjectRole


class ProjectMemberRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, project_id: int, user_id: int) -> Optional[ProjectMember]:
        stmt = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_project(self, project_id: int) -> List[ProjectMember]:
        stmt = (
            select(ProjectMember)
            .where(ProjectMember.project_id == project_id)
            .options(selectinload(ProjectMember.user))
            .order_by(ProjectMember.joined_at.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_project_ids_for_user(self, user_id: int) -> List[int]:
        stmt = select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
        return list(self.db.execute(stmt).scalars().all())

    def count_admins(self, project_id: int) -> int:
        stmt = select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.role == ProjectRole.ADMIN,
        )
        return len(list(self.db.execute(stmt).scalars().all()))

    def add(self, *, project_id: int, user_id: int, role: ProjectRole) -> ProjectMember:
        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
        self.db.add(member)
        self.db.flush()
        return member

    def update_role(self, member: ProjectMember, role: ProjectRole) -> ProjectMember:
        member.role = role
        self.db.flush()
        return member

    def remove(self, member: ProjectMember) -> None:
        self.db.delete(member)
        self.db.flush()
