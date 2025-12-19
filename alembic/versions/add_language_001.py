"""add_user_language_field

Revision ID: add_language_001
Revises: seed_default_categories
Create Date: 2025-12-19 17:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_language_001'
down_revision = 'seed_default_categories'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add language column with default 'uz'
    op.add_column('users', sa.Column('language', sa.String(length=2), server_default='uz', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'language')
