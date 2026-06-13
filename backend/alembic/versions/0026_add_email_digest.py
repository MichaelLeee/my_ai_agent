"""add email digest toggle to users

Revision ID: 0026_add_email_digest
Revises: 0025_add_api_keys
Create Date: 2026-06-11 12:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0026_add_email_digest'
down_revision: Union[str, None] = '0025_add_api_keys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column(
        'email_digest_enabled', sa.Boolean(), nullable=False,
        server_default='true'))


def downgrade() -> None:
    op.drop_column('users', 'email_digest_enabled')
