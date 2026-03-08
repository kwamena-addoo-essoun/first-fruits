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
    op.add_column('invoices', sa.Column('client_id', sa.Integer(), nullable=True))
    op.add_column('invoices', sa.Column('project_id', sa.Integer(), nullable=True))
    op.add_column('invoices', sa.Column('client_name', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('project_name', sa.String(), nullable=True))
    op.add_column('invoices', sa.Column('notes', sa.Text(), nullable=True))
    op.create_foreign_key('fk_invoices_client_id', 'invoices', 'clients', ['client_id'], ['id'])
    op.create_foreign_key('fk_invoices_project_id', 'invoices', 'projects', ['project_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_invoices_project_id', 'invoices', type_='foreignkey')
    op.drop_constraint('fk_invoices_client_id', 'invoices', type_='foreignkey')
    op.drop_column('invoices', 'notes')
    op.drop_column('invoices', 'project_name')
    op.drop_column('invoices', 'client_name')
    op.drop_column('invoices', 'project_id')
    op.drop_column('invoices', 'client_id')
