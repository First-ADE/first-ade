"""initial

Revision ID: 1a2b3c4d5e6f
Revises: None
Create Date: 2026-05-23 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1a2b3c4d5e6f"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit_log table
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("action", sa.String(), nullable=True),
        sa.Column("details", sa.String(), nullable=True),
        sa.Column("previous_hash", sa.String(), nullable=True),
        sa.Column("hash", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create override_log table (without expiry_notified)
    op.create_table(
        "override_log",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("axiom_id", sa.String(), nullable=False),
        sa.Column("scope_type", sa.String(), nullable=False),
        sa.Column("scope_value", sa.String(), nullable=False),
        sa.Column("rationale", sa.String(), nullable=False),
        sa.Column("created_by", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_permanent", sa.Boolean(), nullable=True),
        sa.Column("permanent_justification", sa.String(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create escalation_queue table
    op.create_table(
        "escalation_queue",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=True),
        sa.Column("next_retry", sa.DateTime(), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("escalation_queue")
    op.drop_table("override_log")
    op.drop_table("audit_log")
