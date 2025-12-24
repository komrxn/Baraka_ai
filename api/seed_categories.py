import asyncio
import os
import sys
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.database import get_db, AsyncSessionLocal
from api.models.category import Category
from bot.categories_data import DEFAULT_CATEGORIES

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from sqlalchemy import select, func, delete
from api.models.transaction import Transaction

async def seed_categories():
    print("Seeding categories...")
    async with AsyncSessionLocal() as session:
        # 1. Update/Create new defaults
        for cat_data in DEFAULT_CATEGORIES:
            slug = cat_data['slug']
            stmt = select(Category).where(Category.slug == slug)
            result = await session.execute(stmt)
            category = result.scalar_one_or_none()
            
            if category:
                # print(f"Updating {slug}...") # Less noise
                category.icon = cat_data['icon']
                category.color = cat_data['color']
                category.type = cat_data['type']
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
                    user_id=None
                )
                session.add(new_cat)
        
        await session.commit()
        
        # 2. Cleanup old defaults (that are NOT in the new list)
        print("Cleaning up deprecated default categories...")
        target_slugs = {c['slug'] for c in DEFAULT_CATEGORIES}
        
        # Fetch all categories marked as default
        stmt = select(Category).where(Category.is_default == True)
        result = await session.execute(stmt)
        existing_defaults = result.scalars().all()
        
        deleted_count = 0
        skipped_count = 0
        
        for cat in existing_defaults:
            if cat.slug not in target_slugs:
                # Check for transactions
                trans_count_stmt = select(func.count(Transaction.id)).where(Transaction.category_id == cat.id)
                trans_result = await session.execute(trans_count_stmt)
                count = trans_result.scalar()
                
                if count > 0:
                    print(f"⚠️  Skipping deprecated '{cat.name}' ({cat.slug}): has {count} transactions. Marked as non-default.")
                    cat.is_default = False # Mark as user category so it doesn't look like a system default anymore? Or just leave it. 
                    # Better to unmark as default so it doesn't confuse future seed runs, effectively making it "custom/legacy"
                    cat.is_default = False
                    skipped_count += 1
                else:
                    print(f"🗑️  Deleting unused deprecated '{cat.name}' ({cat.slug})")
                    await session.delete(cat)
                    deleted_count += 1
        
        await session.commit()
        print(f"Seeding complete. Created/Updated: {len(DEFAULT_CATEGORIES)}. Deleted: {deleted_count}. Skipped (in use): {skipped_count}.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_categories())
