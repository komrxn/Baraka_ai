"""add_usage_counters_006

Revision ID: add_usage_counters_006
Revises: make_id_null_005
Create Date: 2026-01-06 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_usage_counters_006'
down_revision: Union[str, None] = 'make_id_null_005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add usage counters
    op.add_column('users', sa.Column('voice_usage_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('photo_usage_count', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    # Remove usage counters
    op.drop_column('users', 'photo_usage_count')
    op.drop_column('users', 'voice_usage_count')
