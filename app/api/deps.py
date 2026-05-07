from typing import Tuple

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, NotFoundError, PermissionDeniedError
from app.core.security import ACCESS_COOKIE_NAME, decode_token
from app.db.session import get_db
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole, role_at_least
from app.models.user import User
from app.repositories.project import ProjectRepository
from app.repositories.project_member import ProjectMemberRepository
from app.repositories.user import UserRepository


def get_current_user(
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(default=None, alias=ACCESS_COOKIE_NAME),
) -> User:
    if not access_token:
        raise AuthenticationError("Not authenticated")

    user_id = decode_token(access_token, expected_type="access")
    user = UserRepository(db).get(user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


def require_project_role(min_role: ProjectRole):
    def _dep(
        project_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Tuple[Project, ProjectMember]:
        project = ProjectRepository(db).get(project_id)
        if not project:
            raise NotFoundError("Project not found")

        membership = ProjectMemberRepository(db).get(project_id, current_user.id)
        if not membership:
            raise PermissionDeniedError("You are not a member of this project")
        if not role_at_least(membership.role, min_role):
            raise PermissionDeniedError(
                f"Requires '{min_role.value}' role or higher"
            )
        return project, membership

    return _dep
