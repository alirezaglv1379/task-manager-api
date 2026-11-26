"""Add refresh sessions and persistent login rate-limit counters.

Revision ID: 0002_auth_rate_limits
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_auth_rate_limits"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("family_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("replaced_by_token_hash", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"], unique=False)
    op.create_index(
        "ix_refresh_sessions_family_id", "refresh_sessions", ["family_id"], unique=False
    )
    op.create_index(
        "ix_refresh_sessions_expires_at", "refresh_sessions", ["expires_at"], unique=False
    )

    op.create_table(
        "login_rate_limits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("window_start", sa.Integer(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=False), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scope", "key_hash", "window_start", name="uq_login_rate_window"),
    )
    op.create_index(
        "ix_login_rate_limits_expires_at", "login_rate_limits", ["expires_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_login_rate_limits_expires_at", table_name="login_rate_limits")
    op.drop_table("login_rate_limits")
    op.drop_index("ix_refresh_sessions_expires_at", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_family_id", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_user_id", table_name="refresh_sessions")
    op.drop_table("refresh_sessions")
