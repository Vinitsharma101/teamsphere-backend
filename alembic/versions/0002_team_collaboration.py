"""team collaboration: project_members, task project/assignee/priority

Revision ID: 0002_team_collab
Revises: 0001_initial
Create Date: 2026-05-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_team_collab"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="member",
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])

    op.execute(
        """
        INSERT INTO project_members (project_id, user_id, role)
        SELECT id, created_by, 'admin' FROM projects
        """
    )

    op.add_column(
        "tasks",
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "assigned_to",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            server_default="medium",
        ),
    )

    op.alter_column("tasks", "user_id", new_column_name="created_by")
    op.create_index("ix_tasks_project_id", "tasks", ["project_id"])
    op.create_index("ix_tasks_assigned_to", "tasks", ["assigned_to"])
    op.create_index("ix_tasks_created_by", "tasks", ["created_by"])
    try:
        op.drop_index("ix_tasks_user_id", table_name="tasks")
    except Exception:
        pass

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id, created_by FROM tasks WHERE project_id IS NULL")).all()
    for task_id, owner_id in rows:
        existing = bind.execute(
            sa.text(
                "SELECT id FROM projects WHERE created_by = :uid AND name = '__inbox__' LIMIT 1"
            ),
            {"uid": owner_id},
        ).first()
        if existing:
            inbox_id = existing[0]
        else:
            inbox_id = bind.execute(
                sa.text(
                    """
                    INSERT INTO projects (name, status, created_by)
                    VALUES ('__inbox__', 'active', :uid) RETURNING id
                    """
                ),
                {"uid": owner_id},
            ).scalar()
            bind.execute(
                sa.text(
                    """
                    INSERT INTO project_members (project_id, user_id, role)
                    VALUES (:pid, :uid, 'admin')
                    """
                ),
                {"pid": inbox_id, "uid": owner_id},
            )
        bind.execute(
            sa.text("UPDATE tasks SET project_id = :pid WHERE id = :tid"),
            {"pid": inbox_id, "tid": task_id},
        )

    op.alter_column("tasks", "project_id", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_tasks_created_by", table_name="tasks")
    op.drop_index("ix_tasks_assigned_to", table_name="tasks")
    op.drop_index("ix_tasks_project_id", table_name="tasks")
    op.alter_column("tasks", "created_by", new_column_name="user_id")
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"])
    op.drop_column("tasks", "priority")
    op.drop_column("tasks", "assigned_to")
    op.drop_column("tasks", "project_id")

    op.drop_index("ix_project_members_user_id", table_name="project_members")
    op.drop_index("ix_project_members_project_id", table_name="project_members")
    op.drop_table("project_members")
