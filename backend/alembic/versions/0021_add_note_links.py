"""add note links

Revision ID: 0021_add_note_links
Revises: 0020_add_notes
Create Date: 2026-06-08 04:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0021_add_note_links'
down_revision: Union[str, None] = '0020_add_notes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('note_links',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('source_note_id', sa.UUID(), nullable=False),
        sa.Column('target_note_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['source_note_id'], ['notes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_note_id'], ['notes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_note_id', 'target_note_id', name='uq_note_link_source_target'),
    )
    op.create_index('ix_note_links_source_note_id', 'note_links', ['source_note_id'])
    op.create_index('ix_note_links_target_note_id', 'note_links', ['target_note_id'])


def downgrade() -> None:
    op.drop_index('ix_note_links_target_note_id')
    op.drop_index('ix_note_links_source_note_id')
    op.drop_table('note_links')
