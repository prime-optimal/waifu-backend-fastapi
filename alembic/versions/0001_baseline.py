"""baseline generated from src.db.models

Revision ID: 0001_baseline
Revises:
Create Date: 2025-10-28 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

# revision identifiers
revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def create_enum(name: str, values: list[str]) -> None:
    """Create a PostgreSQL enum if it does not already exist."""
    # language=PostgreSQL
    op.execute(
        f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN CREATE TYPE {name} AS ENUM ({', '.join(repr(v) for v in values)}); END IF; END $$"
    )


def drop_enum(name: str) -> None:
    """Drop a PostgreSQL enum if it exists."""
    op.execute(f"DROP TYPE IF EXISTS {name}")


def upgrade() -> None:
    create_enum("userrole", ["user", "admin"])
    create_enum("workflowstatus", ["pending", "running", "completed", "failed"])

    op.create_table(
        "users",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String, nullable=False, unique=True, index=True),
        sa.Column("role", sa.Enum("user", "admin", name="userrole"), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "workflow_runs",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Enum("pending", "running", "completed", "failed", name="workflowstatus"), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_workflow_runs_user_id", "workflow_runs", ["user_id"])

    op.create_table(
        "assets",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("workflow_run_id", PG_UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("url", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_assets_workflow_run_id", "assets", ["workflow_run_id"])


def downgrade() -> None:
    op.drop_index("ix_assets_workflow_run_id", table_name="assets")
    op.drop_table("assets")

    op.drop_index("ix_workflow_runs_user_id", table_name="workflow_runs")
    op.drop_table("workflow_runs")

    op.drop_table("users")

    drop_enum("userrole")
    drop_enum("workflowstatus")
    