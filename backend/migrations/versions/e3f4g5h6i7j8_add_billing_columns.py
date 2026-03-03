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
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("plan", sa.String(), nullable=False, server_default="free")
        )
        batch_op.add_column(
            sa.Column("stripe_customer_id", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("stripe_subscription_id", sa.String(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("stripe_subscription_id")
        batch_op.drop_column("stripe_customer_id")
        batch_op.drop_column("plan")
