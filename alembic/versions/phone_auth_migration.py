"""Drop old tables and recreate with phone auth schema

Revision ID: phone_auth_migration
Revises: 
Create Date: 2025-12-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'phone_auth_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop все таблицы (clean start)
    op.execute('DROP TABLE IF EXISTS transactions CASCADE')
    op.execute('DROP TABLE IF EXISTS categories CASCADE')
    op.execute('DROP TABLE IF EXISTS debts CASCADE')
    op.execute('DROP TABLE IF EXISTS limits CASCADE')
    op.execute('DROP TABLE IF EXISTS users CASCADE')
    
    # Create users table with new schema
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('default_currency', sa.String(length=3), server_default='uzs', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id'),
        sa.UniqueConstraint('phone_number')
    )
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'])
    op.create_index('ix_users_phone_number', 'users', ['phone_number'])


def downgrade() -> None:
    # Cannot downgrade - data will be lost
    pass
