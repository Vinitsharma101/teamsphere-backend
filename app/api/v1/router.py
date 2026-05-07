from fastapi import APIRouter

from app.api.v1 import auth, project_members, projects, tasks

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router)
api_v1_router.include_router(projects.router)
api_v1_router.include_router(project_members.router)
api_v1_router.include_router(project_members.leave_router)
api_v1_router.include_router(tasks.project_tasks_router)
api_v1_router.include_router(tasks.task_router)
