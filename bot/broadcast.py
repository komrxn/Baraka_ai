"""Broadcast notifications service for sending updates to all users."""
import logging
import asyncio
from typing import Optional
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


# Path to pending announcement file
ANNOUNCEMENT_FILE = Path(__file__).parent / "data" / "pending_announcement.json"


def create_announcement(
    version: str,
    texts: dict,
    features: list = None
):
    """
    Create a pending announcement that will be sent on next bot startup.
    
    Args:
        version: Version string (e.g., "1.5.0")
        texts: Dict with language codes as keys and announcement texts as values
               {"ru": "...", "uz": "...", "en": "..."}
        features: Optional list of feature names for logging
    """
    announcement = {
        "version": version,
        "created_at": datetime.now().isoformat(),
        "texts": texts,
        "features": features or [],
        "sent": False
    }
    
    # Ensure data directory exists
    ANNOUNCEMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ANNOUNCEMENT_FILE, "w", encoding="utf-8") as f:
        json.dump(announcement, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ Created announcement v{version} with features: {features}")


def get_pending_announcement() -> Optional[dict]:
    """Get pending announcement if exists and not yet sent."""
    if not ANNOUNCEMENT_FILE.exists():
        return None
    
    try:
        with open(ANNOUNCEMENT_FILE, "r", encoding="utf-8") as f:
            announcement = json.load(f)
        
        if not announcement.get("sent", False):
            return announcement
    except Exception as e:
        logger.error(f"Error reading announcement: {e}")
    
    return None


def mark_announcement_sent():
    """Mark current announcement as sent."""
    if not ANNOUNCEMENT_FILE.exists():
        return
    
    try:
        with open(ANNOUNCEMENT_FILE, "r", encoding="utf-8") as f:
            announcement = json.load(f)
        
        announcement["sent"] = True
        announcement["sent_at"] = datetime.now().isoformat()
        
        with open(ANNOUNCEMENT_FILE, "w", encoding="utf-8") as f:
            json.dump(announcement, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ Marked announcement as sent")
    except Exception as e:
        logger.error(f"Error marking announcement sent: {e}")


async def broadcast_announcement(bot, user_storage):
    """
    Send pending announcement to all users.
    
    Args:
        bot: Telegram Bot instance
        user_storage: Storage instance with user tokens/languages
    """
    announcement = get_pending_announcement()
    if not announcement:
        logger.info("No pending announcements")
        return
    
    texts = announcement.get("texts", {})
    version = announcement.get("version", "")
    
    if not texts:
        logger.warning("Announcement has no texts")
        return
    
    logger.info(f"📢 Broadcasting announcement v{version} to all users...")
    
    # Get all user IDs from storage
    users = user_storage.get_all_users()
    
    sent_count = 0
    failed_count = 0
    
    for user_id, user_data in users.items():
        try:
            lang = user_data.get("language", "uz")
            text = texts.get(lang) or texts.get("uz") or texts.get("ru") or list(texts.values())[0]
            
            await bot.send_message(
                chat_id=int(user_id),
                text=text,
                parse_mode="Markdown"
            )
            sent_count += 1
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.05)
            
        except Exception as e:
            logger.debug(f"Failed to send to {user_id}: {e}")
            failed_count += 1
    
    logger.info(f"📢 Broadcast complete: {sent_count} sent, {failed_count} failed")
    
    # Mark as sent
    mark_announcement_sent()
