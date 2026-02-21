import asyncio
import logging
from sqlalchemy import select, and_

from api.database import AsyncSessionLocal
from api.models.user import User
from api.services.notification import send_premium_upsell_message

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def notify_all_unused_trials():
    """
    Finds all users who are currently on 'free' plan and HAVE NOT used their trial.
    Sends them the 'premium upsell / registration welcome' notification.
    """
    logger.info("🚀 Starting broadcast for unused trials...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Select users who are on 'free' and have is_trial_used = False
            stmt = select(User).where(
                and_(
                    User.subscription_type == "free",
                    User.is_trial_used == False
                )
            )
            result = await db.execute(stmt)
            unused_users = result.scalars().all()
            
            total_users = len(unused_users)
            logger.info(f"📊 Found {total_users} users with unused trials.")
            
            success_count = 0
            fail_count = 0
            
            for user in unused_users:
                try:
                    await send_premium_upsell_message(user)
                    success_count += 1
                    logger.info(f"✅ Sent upsell notification to User ID: {user.id} | Telegram: {user.telegram_id}")
                    # Throttle slightly to respect Telegram limits
                    await asyncio.sleep(0.05)
                except Exception as e:
                    fail_count += 1
                    logger.error(f"❌ Failed to notify User ID: {user.id}: {e}")
            
            logger.info(f"🎉 Broadcast finished! Sent: {success_count}, Failed: {fail_count}")
            
        except Exception as e:
            logger.exception(f"Critical error during broadcast: {e}")

if __name__ == "__main__":
    # Run the async broadcast
    asyncio.run(notify_all_unused_trials())
