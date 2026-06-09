"""add link_type to note_links

Revision ID: 0023_add_link_type
Revises: 0022_add_insights
Create Date: 2026-06-09 01:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0023_add_link_type'
down_revision: Union[str, None] = '0022_add_insights'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('note_links',
        sa.Column('link_type', sa.String(length=20), nullable=False,
                  server_default='relates_to'))


def downgrade() -> None:
    op.drop_column('note_links', 'link_type')
