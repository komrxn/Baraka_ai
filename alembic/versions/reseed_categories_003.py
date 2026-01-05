"""Reseed default categories after table reset

Revision ID: reseed_categories_003
Revises: subscription_click_002
Create Date: 2026-01-05 16:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = 'reseed_categories_003'
down_revision = 'subscription_click_002'
branch_labels = None
depends_on = None

DEFAULT_CATEGORIES = [
    # EXPENSES
    {'name': 'Аренда/Ипотека', 'slug': 'rent', 'type': 'expense', 'icon': '🏠', 'color': '#FF6B6B'},
    {'name': 'Коммуналка', 'slug': 'utilities', 'type': 'expense', 'icon': '💡', 'color': '#4ECDC4'},
    {'name': 'Интернет', 'slug': 'internet', 'type': 'expense', 'icon': '🌐', 'color': '#45B7D1'},
    {'name': 'Продукты (осн.)', 'slug': 'groceries', 'type': 'expense', 'icon': '🛒', 'color': '#96CEB4'},
    {'name': 'Кафе и рестораны', 'slug': 'cafes', 'type': 'expense', 'icon': '🍽️', 'color': '#FFAD60'},
    {'name': 'Доставка', 'slug': 'delivery', 'type': 'expense', 'icon': '🛵', 'color': '#D9534F'},
    {'name': 'Такси', 'slug': 'taxi', 'type': 'expense', 'icon': '🚕', 'color': '#FFEEAD'},
    {'name': 'Бензин', 'slug': 'fuel', 'type': 'expense', 'icon': '⛽', 'color': '#707070'},
    {'name': 'Транспорт', 'slug': 'public_transport', 'type': 'expense', 'icon': '🚌', 'color': '#5BC0DE'},
    {'name': 'Парковка', 'slug': 'parking', 'type': 'expense', 'icon': '🅿️', 'color': '#999999'},
    {'name': 'Лекарства', 'slug': 'medicine', 'type': 'expense', 'icon': '💊', 'color': '#FF9999'},
    {'name': 'Врачи', 'slug': 'doctors', 'type': 'expense', 'icon': '👨‍⚕️', 'color': '#FF6F69'},
    {'name': 'Продукты (вкусн.)', 'slug': 'groceries_optional', 'type': 'expense', 'icon': '🍫', 'color': '#FFCC5C'},
    {'name': 'Стоматология', 'slug': 'dentistry', 'type': 'expense', 'icon': '🦷', 'color': '#E0E0E0'},
    {'name': 'Одежда', 'slug': 'clothing', 'type': 'expense', 'icon': '👔', 'color': '#A8D8EA'},
    {'name': 'Обувь', 'slug': 'shoes', 'type': 'expense', 'icon': '👟', 'color': '#AA96DA'},
    {'name': 'Аксессуары', 'slug': 'accessories', 'type': 'expense', 'icon': '👓', 'color': '#FCBAD3'},
    {'name': 'Быт. химия', 'slug': 'household_chemicals', 'type': 'expense', 'icon': '🧼', 'color': '#95E1D3'},
    {'name': 'Гигиена', 'slug': 'hygiene', 'type': 'expense', 'icon': '🧴', 'color': '#F38181'},
    {'name': 'Косметика', 'slug': 'cosmetics', 'type': 'expense', 'icon': '💄', 'color': '#FFB7B2'},
    {'name': 'Для дома', 'slug': 'home_other', 'type': 'expense', 'icon': '🛋️', 'color': '#FCE38A'},
    {'name': 'Развлечения', 'slug': 'entertainment', 'type': 'expense', 'icon': '🎮', 'color': '#F06292'},
    {'name': 'Подписки', 'slug': 'subscriptions', 'type': 'expense', 'icon': '📺', 'color': '#BA68C8'},
    {'name': 'Хобби', 'slug': 'hobbies', 'type': 'expense', 'icon': '🎨', 'color': '#FFFF99'},
    {'name': 'Спортзал', 'slug': 'gym', 'type': 'expense', 'icon': '💪', 'color': '#4D96FF'},
    {'name': 'Курсы', 'slug': 'courses', 'type': 'expense', 'icon': '🎓', 'color': '#6495ED'},
    {'name': 'Книги', 'slug': 'books', 'type': 'expense', 'icon': '📚', 'color': '#8B4513'},
    {'name': 'Обучение', 'slug': 'education', 'type': 'expense', 'icon': '🏫', 'color': '#FFD700'},
    {'name': 'Гаджеты', 'slug': 'gadgets', 'type': 'expense', 'icon': '📱', 'color': '#333333'},
    {'name': 'Софт', 'slug': 'software', 'type': 'expense', 'icon': '💻', 'color': '#000080'},
    {'name': 'Оборудование', 'slug': 'equipment', 'type': 'expense', 'icon': '🛠️', 'color': '#808080'},
    {'name': 'Подарки', 'slug': 'gifts_expense', 'type': 'expense', 'icon': '🎁', 'color': '#FF69B4'},
    {'name': 'Семья', 'slug': 'family', 'type': 'expense', 'icon': '👨‍👩‍👧‍👦', 'color': '#FFB6C1'},
    {'name': 'Путешествия', 'slug': 'travel', 'type': 'expense', 'icon': '✈️', 'color': '#87CEEB'},
    {'name': 'Кредиты', 'slug': 'loans', 'type': 'expense', 'icon': '💳', 'color': '#CD5C5C'},
    {'name': 'Долги', 'slug': 'debts_payment', 'type': 'expense', 'icon': '🤝', 'color': '#A52A2A'},
    {'name': 'Сбережения', 'slug': 'savings', 'type': 'expense', 'icon': '💰', 'color': '#32CD32'},
    {'name': 'Инвестиции', 'slug': 'investments_expense', 'type': 'expense', 'icon': '📉', 'color': '#FF4500'},
    {'name': 'Штрафы', 'slug': 'fines', 'type': 'expense', 'icon': '👮', 'color': '#000000'},
    {'name': 'Другое', 'slug': 'other_expense', 'type': 'expense', 'icon': '📦', 'color': '#BDC3C7'},

    # INCOME
    {'name': 'Зарплата', 'slug': 'salary', 'type': 'income', 'icon': '💵', 'color': '#2ECC71'},
    {'name': 'Фриланс/Проект', 'slug': 'freelance', 'type': 'income', 'icon': '💻', 'color': '#3498DB'},
    {'name': 'Инвестиции', 'slug': 'investments_income', 'type': 'income', 'icon': '📈', 'color': '#9B59B6'},
    {'name': 'Подарок', 'slug': 'gift_income', 'type': 'income', 'icon': '🎁', 'color': '#E91E63'},
    {'name': 'Другое', 'slug': 'other_income', 'type': 'income', 'icon': '💸', 'color': '#1ABC9C'}
]

def upgrade() -> None:
    connection = op.get_bind()
    
    # Use raw SQL for safety and speed
    for cat in DEFAULT_CATEGORIES:
        # Check if exists
        result = connection.execute(
            sa.text("SELECT count(*) FROM categories WHERE slug = :slug AND user_id IS NULL"),
            {"slug": cat['slug']}
        )
        count = result.scalar()
        
        if count == 0:
            connection.execute(
                sa.text("""
                    INSERT INTO categories (id, name, slug, type, icon, color, is_default, created_at, updated_at)
                    VALUES (:id, :name, :slug, :type, :icon, :color, true, now(), now())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "name": cat["name"],
                    "slug": cat["slug"],
                    "type": cat["type"],
                    "icon": cat["icon"],
                    "color": cat["color"]
                }
            )

def downgrade() -> None:
    pass # No need to delete valid categories on downgrade unless strictly required
