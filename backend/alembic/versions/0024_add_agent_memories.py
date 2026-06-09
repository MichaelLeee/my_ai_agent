"""add agent memories

Revision ID: 0024_add_agent_memories
Revises: 0023_add_link_type
Create Date: 2026-06-09 17:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0024_add_agent_memories'
down_revision: Union[str, None] = '0023_add_link_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('agent_memories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('source', sa.String(100), nullable=False, server_default='conversation'),
        sa.Column('importance', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'key', name='uq_agent_memory_user_key'),
    )
    op.create_index('ix_agent_memories_user_id', 'agent_memories', ['user_id'])
    # pgvector embedding column via raw SQL (no pgvector.sqlalchemy package)
    op.execute(
        "ALTER TABLE agent_memories ADD COLUMN embedding vector(1024)"
    )


def downgrade() -> None:
    op.drop_index('ix_agent_memories_user_id')
    op.drop_table('agent_memories')
