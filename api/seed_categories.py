import asyncio
import os
import sys
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.database import get_db, async_session_maker
from api.models.category import Category
from bot.categories_data import DEFAULT_CATEGORIES

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def seed_categories():
    print("Seeding categories...")
    async with async_session_maker() as session:
        for cat_data in DEFAULT_CATEGORIES:
            slug = cat_data['slug']
            # Find category by slug (system default)
            stmt = select(Category).where(Category.slug == slug)
            result = await session.execute(stmt)
            category = result.scalar_one_or_none()
            
            if category:
                print(f"Updating {slug}...")
                category.icon = cat_data['icon']
                category.color = cat_data['color']
                category.type = cat_data['type']
                # Don't overwrite name if it might be customized? 
                # Actually user wants to reset defaults.
                category.name = cat_data['name'] 
                category.is_default = True
            else:
                print(f"Creating {slug}...")
                new_cat = Category(
                    id=uuid4(),
                    name=cat_data['name'],
                    slug=slug,
                    type=cat_data['type'],
                    icon=cat_data['icon'],
                    color=cat_data['color'],
                    is_default=True,
                    user_id=None # Default category
                )
                session.add(new_cat)
        
        await session.commit()
        print("Categories seeded successfully.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_categories())
