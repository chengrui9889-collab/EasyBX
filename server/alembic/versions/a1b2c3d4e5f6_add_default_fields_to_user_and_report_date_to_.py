"""add_default_fields_to_user_and_report_date_to_batch_and_ledger_fields_to_batch_invoice

Revision ID: a1b2c3d4e5f6
Revises: 841bfb32250c
Create Date: 2026-05-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '841bfb32250c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('default_department', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('default_reporter', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('default_payee', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('default_bank_account', sa.String(length=30), nullable=True))
    op.add_column('users', sa.Column('default_bank_name', sa.String(length=100), nullable=True))

    op.add_column('reimbursement_batches', sa.Column('report_date', sa.Date(), nullable=True))

    op.add_column('batch_invoices', sa.Column('quantity', sa.Float(), nullable=False, server_default='1.0'))
    op.add_column('batch_invoices', sa.Column('unit_price', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('batch_invoices', sa.Column('advance_amount', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    op.drop_column('batch_invoices', 'advance_amount')
    op.drop_column('batch_invoices', 'unit_price')
    op.drop_column('batch_invoices', 'quantity')

    op.drop_column('reimbursement_batches', 'report_date')

    op.drop_column('users', 'default_bank_name')
    op.drop_column('users', 'default_bank_account')
    op.drop_column('users', 'default_payee')
    op.drop_column('users', 'default_reporter')
    op.drop_column('users', 'default_department')