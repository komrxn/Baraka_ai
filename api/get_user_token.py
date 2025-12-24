import asyncio
import sys
import os

# Ensure we can import from api package
sys.path.append(os.getcwd())

from api.database import async_session_maker
from api.models.user import User
from api.auth.jwt import create_access_token
from sqlalchemy import select

async def main(telegram_id):
    async with async_session_maker() as db:
        try:
            tid = int(telegram_id)
        except ValueError:
            print("Error: telegram_id must be an integer")
            return

        result = await db.execute(select(User).where(User.telegram_id == tid))
        user = result.scalar_one_or_none()
        
        if user:
            # Generate token similarly to login endpoint
            token = create_access_token(
                data={"sub": str(user.id), "telegram_id": user.telegram_id}
            )
            print(f"\nUser found: {user.name}")
            print(f"Phone: {user.phone_number}")
            print("-" * 50)
            print(f"ACCESS TOKEN:\n{token}")
            print("-" * 50)
        else:
            print(f"\n❌ User with telegram_id {telegram_id} not found in database.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 api/get_user_token.py <telegram_id>")
        sys.exit(1)
    
    asyncio.run(main(sys.argv[1]))
