"""add_text_usage_007

Revision ID: add_text_usage_007
Revises: add_usage_counters_006
Create Date: 2026-02-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_text_usage_007'
down_revision: Union[str, None] = 'add_usage_counters_006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add text usage counters
    op.add_column('users', sa.Column('text_usage_daily', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('text_usage_count', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    # Remove text usage counters
    op.drop_column('users', 'text_usage_count')
    op.drop_column('users', 'text_usage_daily')
