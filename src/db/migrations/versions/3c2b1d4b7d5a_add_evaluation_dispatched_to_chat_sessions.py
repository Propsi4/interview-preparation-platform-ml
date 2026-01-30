"""add_evaluated_to_chat_sessions

Revision ID: 3c2b1d4b7d5a
Revises: 8afac31e6144
Create Date: 2026-01-27 19:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3c2b1d4b7d5a"
down_revision: Union[str, Sequence[str], None] = "8afac31e6144"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "chat_sessions",
        sa.Column(
            "evaluated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("chat_sessions", "evaluated")
