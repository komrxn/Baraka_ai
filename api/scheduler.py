import asyncio
import logging
from datetime import datetime
from sqlalchemy import select, and_
from .database import AsyncSessionLocal
from .models.user import User
from .services.notification import send_subscription_expired_message

logger = logging.getLogger(__name__)

async def check_expired_subscriptions():
    """Check for expired subscriptions and downgrade/notify users."""
    logger.info("⏳ Checking for expired subscriptions...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Find users who are NOT free but have expired end date
            now = datetime.now()
            stmt = select(User).where(
                and_(
                    User.subscription_type != "free",
                    User.subscription_ends_at < now
                )
            )
            result = await db.execute(stmt)
            expired_users = result.scalars().all()
            
            count = 0
            for user in expired_users:
                # Double check to be safe
                if user.subscription_ends_at and user.subscription_ends_at.replace(tzinfo=None) < now:
                    old_tier = user.subscription_type
                    user.subscription_type = "free"
                    # user.is_premium is computed, so no need to set
                    
                    # Notify user
                    try:
                        await send_subscription_expired_message(user)
                    except Exception as e:
                        logger.error(f"Failed to notify user {user.id} of expiration: {e}")
                        
                    count += 1
            
            if count > 0:
                await db.commit()
                logger.info(f"✅ Downgraded {count} expired subscriptions.")
            else:
                logger.info("✅ No expired subscriptions found.")
                
        except Exception as e:
            logger.error(f"Error checking expired subscriptions: {e}")

async def start_scheduler():
    """Start the background scheduler loop."""
    while True:
        try:
            await check_expired_subscriptions()
        except Exception as e:
            logger.error(f"Scheduler crash: {e}")
        
        # Run every 6 hours (6 * 3600 seconds)
        # For testing, user might want faster, but 6h is reasonable for prod
        await asyncio.sleep(6 * 3600)
