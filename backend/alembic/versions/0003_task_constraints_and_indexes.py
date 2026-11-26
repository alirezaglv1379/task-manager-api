"""Normalize legacy task status and add task query indexes.

Revision ID: 0003_task_indexes
Revises: 0002_auth_rate_limits
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_task_indexes"
down_revision = "0002_auth_rate_limits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE tasks SET is_completed = 0 WHERE is_completed IS NULL"))
    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.alter_column(
            "title", existing_type=sa.String(), type_=sa.String(length=200), nullable=False
        )
        batch_op.alter_column(
            "description", existing_type=sa.String(), type_=sa.String(length=2000), nullable=True
        )
        batch_op.alter_column(
            "is_completed", existing_type=sa.Boolean(), nullable=False
        )
    op.create_index("ix_tasks_owner_id", "tasks", ["owner_id"], unique=False)
    op.create_index("ix_tasks_owner_created", "tasks", ["owner_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tasks_owner_created", table_name="tasks")
    op.drop_index("ix_tasks_owner_id", table_name="tasks")
    with op.batch_alter_table("tasks", recreate="always") as batch_op:
        batch_op.alter_column(
            "title", existing_type=sa.String(length=200), type_=sa.String(), nullable=False
        )
        batch_op.alter_column(
            "description", existing_type=sa.String(length=2000), type_=sa.String(), nullable=True
        )
        batch_op.alter_column(
            "is_completed", existing_type=sa.Boolean(), nullable=True
        )
