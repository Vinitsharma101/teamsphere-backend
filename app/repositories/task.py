from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskPriority, TaskStatus


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, task_id: int) -> Optional[Task]:
        return self.db.get(Task, task_id)

    def list_in_project(
        self,
        project_id: int,
        *,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Task], int]:
        conditions = [Task.project_id == project_id]
        if status is not None:
            conditions.append(Task.status == status)
        if priority is not None:
            conditions.append(Task.priority == priority)
        if assigned_to is not None:
            conditions.append(Task.assigned_to == assigned_to)

        items_stmt = (
            select(Task)
            .where(*conditions)
            .order_by(Task.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_stmt = select(func.count()).select_from(Task).where(*conditions)

        items = list(self.db.execute(items_stmt).scalars().all())
        total = int(self.db.execute(count_stmt).scalar_one())
        return items, total

    def create(self, *, data: dict, project_id: int, created_by: int) -> Task:
        task = Task(**data, project_id=project_id, created_by=created_by)
        self.db.add(task)
        self.db.flush()
        return task

    def update(self, task: Task, data: dict) -> Task:
        for field, value in data.items():
            setattr(task, field, value)
        self.db.flush()
        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)
        self.db.flush()
