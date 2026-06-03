"""create_substitute_relations_table

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'substitute_relations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('substitute_invoice_id', sa.Integer(), nullable=False),
        sa.Column('target_row_id', sa.Integer(), nullable=False),
        sa.Column('mode', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['target_row_id'], ['batch_invoices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_substitute_relations_batch_id', 'substitute_relations', ['batch_id'])
    op.create_index('ix_substitute_relations_substitute_invoice_id', 'substitute_relations', ['substitute_invoice_id'])
    op.create_index('ix_substitute_relations_target_row_id', 'substitute_relations', ['target_row_id'])


def downgrade() -> None:
    op.drop_table('substitute_relations')