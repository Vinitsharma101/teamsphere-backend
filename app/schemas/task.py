from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.task import TaskPriority, TaskStatus
from app.schemas.common import TimestampedRead


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=10_000)
    due_date: Optional[date] = None
    category: Optional[str] = Field(None, max_length=60)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=10_000)
    due_date: Optional[date] = None
    category: Optional[str] = Field(None, max_length=60)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None


class TaskRead(TimestampedRead):
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[date]
    category: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    project_id: int
    created_by: int
    assigned_to: Optional[int]


class TaskFilters(BaseModel):
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None
