from typing import List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, project_id: int) -> Optional[Project]:
        return self.db.get(Project, project_id)

    def list_by_ids(self, ids: Sequence[int]) -> List[Project]:
        if not ids:
            return []
        stmt = (
            select(Project)
            .where(Project.id.in_(ids))
            .order_by(Project.created_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def create(self, *, data: dict, created_by: int) -> Project:
        project = Project(**data, created_by=created_by)
        self.db.add(project)
        self.db.flush()
        return project

    def update(self, project: Project, data: dict) -> Project:
        for field, value in data.items():
            setattr(project, field, value)
        self.db.flush()
        return project

    def delete(self, project: Project) -> None:
        self.db.delete(project)
        self.db.flush()
