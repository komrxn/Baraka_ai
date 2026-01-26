import asyncio
import os
import sys

# In the container, PYTHONPATH=/app, and the code is in /app/app
# so 'import app.models' works.

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.admin import AdminUser
from app.core.security import get_password_hash

# Env vars should be loaded by the container environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/midas_db")

async def reset_password():
    print(f"Connecting to DB: {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(AdminUser).where(AdminUser.email == "admin@baraka.ai"))
        admin = result.scalar_one_or_none()

        if admin:
            print(f"Found admin: {admin.email}")
            new_password = "admin"
            print(f"Resetting password to: '{new_password}'")
            admin.hashed_password = get_password_hash(new_password)
            session.add(admin)
            await session.commit()
            print("Password reset successfully!")
        else:
            print("Admin user not found! Creating one...")
            new_password = "admin"
            new_admin = AdminUser(
                email="admin@baraka.ai",
                hashed_password=get_password_hash(new_password),
                is_super_admin=True
            )
            session.add(new_admin)
            await session.commit()
            print(f"Created new admin with password: '{new_password}'")

if __name__ == "__main__":
    try:
        asyncio.run(reset_password())
    except Exception as e:
        print(f"Error: {e}")
