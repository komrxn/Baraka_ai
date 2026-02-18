"""make category_id nullable

Revision ID: 008
Revises: 007
Create Date: 2026-02-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'make_category_id_nullable_008'
down_revision = 'add_text_usage_007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop the existing unique constraint
    op.drop_constraint('uq_user_category_period', 'limits', type_='unique')
    
    # 2. Make category_id nullable
    op.alter_column('limits', 'category_id',
               existing_type=postgresql.UUID(),
               nullable=True)
               
    # 3. Create a unique index that allows NULL category_id (handling global limits)
    # We want unique (user_id, category_id, period_start)
    # In Postgres, unique constraints allow multiple NULLs, so multiple global limits for same date could exist
    # To prevent that, we can use a partial index for global limits
    
    # Index for normal limits
    op.create_index('ix_limits_user_category_period', 'limits', 
                    ['user_id', 'category_id', 'period_start'], 
                    unique=True, 
                    postgresql_where=sa.text('category_id IS NOT NULL'))
                    
    # Index for global limits
    op.create_index('ix_limits_user_global_period', 'limits', 
                    ['user_id', 'period_start'], 
                    unique=True, 
                    postgresql_where=sa.text('category_id IS NULL'))


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_limits_user_global_period', table_name='limits')
    op.drop_index('ix_limits_user_category_period', table_name='limits')
    
    # Revert category_id to not null (WARNING: will fail if nulls exist)
    # We assume usage of this down migration implies checking data first or it's dev env
    op.execute("DELETE FROM limits WHERE category_id IS NULL")
    op.alter_column('limits', 'category_id',
               existing_type=postgresql.UUID(),
               nullable=False)
               
    # Restore constraint
    op.create_unique_constraint('uq_user_category_period', 'limits', ['user_id', 'category_id', 'period_start'])
