"""timelog_nullable_end_time_hours

Revision ID: 9b2c3d4e5f6a
Revises: 8a1b2c3d4e5f
Create Date: 2026-02-24 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "9b2c3d4e5f6a"
down_revision: Union[str, None] = "8a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('timelogs', 'end_time', existing_type=sa.DateTime(), nullable=True)
    op.alter_column('timelogs', 'hours', existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    op.alter_column('timelogs', 'hours', existing_type=sa.Float(), nullable=False)
    op.alter_column('timelogs', 'end_time', existing_type=sa.DateTime(), nullable=False)
