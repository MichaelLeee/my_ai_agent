"""add insights

Revision ID: 0022_add_insights
Revises: 0021_add_note_links
Create Date: 2026-06-08 05:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0022_add_insights'
down_revision: Union[str, None] = '0021_add_note_links'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('insights',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('related_note_ids', postgresql.JSONB(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_insights_user_id', 'insights', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_insights_user_id')
    op.drop_table('insights')
