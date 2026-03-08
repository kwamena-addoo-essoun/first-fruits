"""add billing columns to users

Revision ID: e3f4g5h6i7j8
Revises: d2e3f4g5h6i7
Create Date: 2026-03-02 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "e3f4g5h6i7j8"
down_revision: Union[str, None] = "a391cceedd00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # These columns are already created in the initial_schema migration (5c59f2b3a9f3).
    # This migration is a no-op to preserve the revision history.
    pass


def downgrade() -> None:
    pass
