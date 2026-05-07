from typing import Tuple

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_project_role
from app.db.session import get_db
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.common import MessageResponse, Page, PageParams
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task import TaskService


def page_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PageParams:
    return PageParams(page=page, page_size=page_size)


project_tasks_router = APIRouter(
    prefix="/projects/{project_id}/tasks", tags=["Tasks"]
)


@project_tasks_router.post(
    "", response_model=TaskRead, status_code=status.HTTP_201_CREATED
)
def create_task(
    project_id: int,
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: Tuple[Project, ProjectMember] = Depends(
        require_project_role(ProjectRole.MEMBER)
    ),
):
    return TaskService(db).create(project_id, payload, current_user.id)


@project_tasks_router.get("", response_model=Page[TaskRead])
def list_project_tasks(
    project_id: int,
    pagination: PageParams = Depends(page_params),
    status_filter: TaskStatus | None = Query(None, alias="status"),
    priority: TaskPriority | None = Query(None),
    assigned_to: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: Tuple[Project, ProjectMember] = Depends(
        require_project_role(ProjectRole.VIEWER)
    ),
):
    items, total = TaskService(db).list_in_project(
        project_id,
        current_user.id,
        status=status_filter,
        priority=priority,
        assigned_to=assigned_to,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return Page.build(
        [TaskRead.model_validate(t) for t in items], total, pagination
    )


task_router = APIRouter(prefix="/tasks", tags=["Tasks"])


@task_router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TaskService(db).get(task_id, current_user.id)


@task_router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TaskService(db).update(task_id, payload, current_user.id)


@task_router.delete("/{task_id}", response_model=MessageResponse)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    TaskService(db).delete(task_id, current_user.id)
    return MessageResponse(message="Task deleted")
