"""add expiry_notified

Revision ID: 2a3b4c5d6e7f
Revises: 1a2b3c4d5e6f
Create Date: 2026-05-23 00:01:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2a3b4c5d6e7f"  # pragma: allowlist secret
down_revision: Union[str, None] = "1a2b3c4d5e6f"  # pragma: allowlist secret
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

__all__ = ["revision", "down_revision", "branch_labels", "depends_on"]


def upgrade() -> None:
    # Add expiry_notified column to override_log table
    op.add_column(
        "override_log", sa.Column("expiry_notified", sa.Boolean(), server_default=sa.text("0"), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("override_log", "expiry_notified")
