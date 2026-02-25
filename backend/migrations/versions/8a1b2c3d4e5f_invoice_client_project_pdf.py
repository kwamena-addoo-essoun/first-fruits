"""invoice_client_project_pdf

Revision ID: 8a1b2c3d4e5f
Revises: 5c59f2b3a9f3
Create Date: 2026-02-24 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "8a1b2c3d4e5f"
down_revision: Union[str, None] = "5c59f2b3a9f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.add_column(sa.Column("client_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("project_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("client_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("project_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))
        batch_op.create_foreign_key("fk_invoices_client_id", "clients", ["client_id"], ["id"])
        batch_op.create_foreign_key("fk_invoices_project_id", "projects", ["project_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_constraint("fk_invoices_project_id", type_="foreignkey")
        batch_op.drop_constraint("fk_invoices_client_id", type_="foreignkey")
        batch_op.drop_column("notes")
        batch_op.drop_column("project_name")
        batch_op.drop_column("client_name")
        batch_op.drop_column("project_id")
        batch_op.drop_column("client_id")
