from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.models.project_member import ProjectRole, role_at_least
from app.models.task import Task, TaskPriority, TaskStatus
from app.repositories.project_member import ProjectMemberRepository
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: Session):
        self.db = db
        self.tasks = TaskRepository(db)
        self.members = ProjectMemberRepository(db)

    def _membership(self, project_id: int, user_id: int):
        member = self.members.get(project_id, user_id)
        if not member:
            raise PermissionDeniedError("You are not a member of this project")
        return member

    def _ensure_assignee_is_member(
        self, project_id: int, assigned_to: Optional[int]
    ) -> None:
        if assigned_to is None:
            return
        if not self.members.get(project_id, assigned_to):
            raise ValidationError("Assignee must be a member of the project")

    def list_in_project(
        self,
        project_id: int,
        user_id: int,
        *,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Task], int]:
        self._membership(project_id, user_id)
        return self.tasks.list_in_project(
            project_id,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
            offset=offset,
            limit=limit,
        )

    def create(self, project_id: int, payload: TaskCreate, user_id: int) -> Task:
        member = self._membership(project_id, user_id)
        if not role_at_least(member.role, ProjectRole.MEMBER):
            raise PermissionDeniedError("Viewers cannot create tasks")
        self._ensure_assignee_is_member(project_id, payload.assigned_to)

        task = self.tasks.create(
            data=payload.model_dump(),
            project_id=project_id,
            created_by=user_id,
        )
        self.db.commit()
        self.db.refresh(task)
        return task

    def get(self, task_id: int, user_id: int) -> Task:
        task = self.tasks.get(task_id)
        if not task:
            raise NotFoundError("Task not found")
        self._membership(task.project_id, user_id)
        return task

    def update(self, task_id: int, payload: TaskUpdate, user_id: int) -> Task:
        task = self.tasks.get(task_id)
        if not task:
            raise NotFoundError("Task not found")

        member = self._membership(task.project_id, user_id)
        if not role_at_least(member.role, ProjectRole.MEMBER):
            raise PermissionDeniedError("Viewers cannot update tasks")

        data = payload.model_dump(exclude_unset=True)
        if "assigned_to" in data:
            self._ensure_assignee_is_member(task.project_id, data["assigned_to"])

        if data:
            self.tasks.update(task, data)
            self.db.commit()
            self.db.refresh(task)
        return task

    def delete(self, task_id: int, user_id: int) -> None:
        task = self.tasks.get(task_id)
        if not task:
            raise NotFoundError("Task not found")

        member = self._membership(task.project_id, user_id)
        is_admin = member.role == ProjectRole.ADMIN
        is_creator = task.created_by == user_id
        if not (is_admin or is_creator):
            raise PermissionDeniedError(
                "Only the task creator or a project admin can delete this task"
            )

        self.tasks.delete(task)
        self.db.commit()
