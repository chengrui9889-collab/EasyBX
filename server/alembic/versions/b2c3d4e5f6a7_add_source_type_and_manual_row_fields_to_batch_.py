"""add_source_type_and_manual_row_fields_to_batch_invoices

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('batch_invoices') as batch_op:
        batch_op.alter_column('invoice_id', existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column('source_type', sa.String(length=20), nullable=False, server_default='invoice'))
        batch_op.add_column(sa.Column('row_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('row_amount', sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('batch_invoices') as batch_op:
        batch_op.drop_column('row_amount')
        batch_op.drop_column('row_date')
        batch_op.drop_column('source_type')
        batch_op.alter_column('invoice_id', existing_type=sa.Integer(), nullable=False)