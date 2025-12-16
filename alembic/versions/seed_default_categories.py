"""Seed default categories

Revision ID: seed_categories_001
Revises: add_telegram_fields
Create Date: 2025-12-16 18:15:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid


# revision identifiers, used by Alembic.
revision = 'seed_categories_001'
down_revision = 'add_telegram_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add default categories for all users."""
    
    # Comprehensive category list with icons and colors
    categories = [
        # РАСХОДЫ (expense)
        {'name': 'Питание', 'slug': 'food', 'type': 'expense', 'icon': '🍔', 'color': '#FF6B6B'},
        {'name': 'Транспорт', 'slug': 'transport', 'type': 'expense', 'icon': '🚗', 'color': '#4ECDC4'},
        {'name': 'Развлечения', 'slug': 'entertainment', 'type': 'expense', 'icon': '🎮', 'color': '#FFE66D'},
        {'name': 'Покупки', 'slug': 'shopping', 'type': 'expense', 'icon': '🛍', 'color': '#A8E6CF'},
        {'name': 'Услуги', 'slug': 'services', 'type': 'expense', 'icon': '💼', 'color': '#95E1D3'},
        {'name': 'Здоровье', 'slug': 'health', 'type': 'expense', 'icon': '🏥', 'color': '#F38181'},
        {'name': 'Образование', 'slug': 'education', 'type': 'expense', 'icon': '📚', 'color': '#AA96DA'},
        {'name': 'Жильё', 'slug': 'housing', 'type': 'expense', 'icon': '🏠', 'color': '#FCBAD3'},
        {'name': 'Косметика', 'slug': 'beauty', 'type': 'expense', 'icon': '💄', 'color': '#FFB6C1'},
        {'name': 'Подарки', 'slug': 'gifts', 'type': 'expense', 'icon': '🎁', 'color': '#FF69B4'},
        {'name': 'Спорт', 'slug': 'sports', 'type': 'expense', 'icon': '⚽', 'color': '#90EE90'},
        {'name': 'Путешествия', 'slug': 'travel', 'type': 'expense', 'icon': '✈️', 'color': '#87CEEB'},
        {'name': 'Рестораны', 'slug': 'restaurants', 'type': 'expense', 'icon': '🍽', 'color': '#FFA07A'},
        {'name': 'Кафе', 'slug': 'cafe', 'type': 'expense', 'icon': '☕', 'color': '#D2691E'},
        {'name': 'Одежда', 'slug': 'clothes', 'type': 'expense', 'icon': '👕', 'color': '#DDA0DD'},
        {'name': 'Техника', 'slug': 'electronics', 'type': 'expense', 'icon': '📱', 'color': '#708090'},
        {'name': 'Связь', 'slug': 'communication', 'type': 'expense', 'icon': '📞', 'color': '#4682B4'},
        {'name': 'Такси', 'slug': 'taxi', 'type': 'expense', 'icon': '🚕', 'color': '#FFD700'},
        {'name': 'Хобби', 'slug': 'hobby', 'type': 'expense', 'icon': '🎨', 'color': '#FF8C00'},
        {'name': 'Питомцы', 'slug': 'pets', 'type': 'expense', 'icon': '🐶', 'color': '#CD853F'},
        
        # ДОХОДЫ (income)
        {'name': 'Зарплата', 'slug': 'salary', 'type': 'income', 'icon': '💰', 'color': '#28A745'},
        {'name': 'Подработка', 'slug': 'freelance', 'type': 'income', 'icon': '💵', 'color': '#20C997'},
        {'name': 'Подарок', 'slug': 'gift_income', 'type': 'income', 'icon': '🎁', 'color': '#17A2B8'},
        {'name': 'Инвестиции', 'slug': 'investments', 'type': 'income', 'icon': '📈', 'color': '#6610F2'},
        {'name': 'Бизнес', 'slug': 'business', 'type': 'income', 'icon': '💼', 'color': '#007BFF'},
        
        # ДОЛГИ (debt)
        {'name': 'Займ', 'slug': 'loan', 'type': 'debt', 'icon': '💳', 'color': '#DC3545'},
        {'name': 'Долг', 'slug': 'debt', 'type': 'debt', 'icon': '📋', 'color': '#FD7E14'},
    ]
    
    # Insert categories
    connection = op.get_bind()
    for cat in categories:
        # Check if category exists
        result = connection.execute(
            sa.text("SELECT COUNT(*) FROM categories WHERE slug = :slug AND user_id IS NULL"),
            {'slug': cat['slug']}
        )
        count = result.scalar()
        
        if count == 0:
            connection.execute(
                sa.text("""
                    INSERT INTO categories (id, name, slug, type, icon, color, is_default, user_id, created_at)
                    VALUES (:id, :name, :slug, :type, :icon, :color, true, NULL, NOW())
                """),
                {
                    'id': str(uuid.uuid4()),
                    'name': cat['name'],
                    'slug': cat['slug'],
                    'type': cat['type'],
                    'icon': cat['icon'],
                    'color': cat['color']
                }
            )


def downgrade() -> None:
    """Remove default categories."""
    op.execute("DELETE FROM categories WHERE is_default = true")
