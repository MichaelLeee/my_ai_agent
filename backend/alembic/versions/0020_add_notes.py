"""add notes table

Revision ID: 0020_add_notes
Revises: 0019_custom_instructions
Create Date: 2026-06-08 03:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0020_add_notes'
down_revision: Union[str, None] = '0019_custom_instructions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('notes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tags', postgresql.JSONB(), nullable=True),
        sa.Column('document_id', sa.String(length=100), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notes_user_id', 'notes', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_notes_user_id')
    op.drop_table('notes')
