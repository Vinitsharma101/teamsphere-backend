from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.userroute import router as user_router
from app.routes.taskroute import router as task_router
from app.routes.projectroute import router as project_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://teamsphere.vercel.app",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(task_router)
app.include_router(project_router)


