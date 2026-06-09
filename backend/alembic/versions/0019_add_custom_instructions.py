"""add custom instructions

Revision ID: 0019_custom_instructions
Revises: 0018_user_slash_commands
Create Date: 2026-06-07 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0019_custom_instructions'
down_revision: Union[str, None] = '0018_user_slash_commands'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('custom_instructions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_custom_instructions_user_id', 'custom_instructions', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_custom_instructions_user_id')
    op.drop_table('custom_instructions')
