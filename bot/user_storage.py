"""User data storage."""
import json
import os
from typing import Optional, Dict, Any
from pathlib import Path


class UserStorage:
    """Store user auth tokens and pending transactions."""
    
    def __init__(self, storage_dir: str = "bot/data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.users_file = self.storage_dir / "users.json"
        self.pending_file = self.storage_dir / "pending.json"
        self._load()
    
    def _load(self):
        """Load data from files."""
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = {}
        
        if self.pending_file.exists():
            with open(self.pending_file, 'r') as f:
                self.pending = json.load(f)
        else:
            self.pending = {}
    
    def _save_users(self):
        """Save users to file."""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
            json.dump(self.users, f, indent=2, default=str) # Added default=str for datetime objects
    
    def _save_pending(self):
        """Save pending to file."""
        with open(self.pending_file, 'w') as f:
            json.dump(self.pending, f, indent=2)
    
    def save_user_token(self, user_id: int, token: str):
        """Save user authentication token."""
        self.users[str(user_id)] = {
            "token": token,
            "timestamp": datetime.now()
        }
        self._save_users() # Changed from _save_to_file() to _save_users() for consistency
        logger.info(f"Saved token for user {user_id}")
    
    def clear_user_token(self, telegram_id: int):
        """Clear user token when it expires or becomes invalid."""
        if str(telegram_id) in self.users:
            # Username is no longer stored, so this line is removed/adjusted
            self.users.pop(str(telegram_id))
            self._save_users()
            # If a logger is available, you might log this event
            # logger.info(f"Cleared expired token for user {telegram_id} ({username})")
        else:
            # If a logger is available, you might log this event
            # logger.warning(f"Attempted to clear token for non-existent user {telegram_id}")
            pass # No action needed if user not found
    
    def get_user_token(self, telegram_id: int) -> Optional[str]:
        """Get user auth token."""
        user_data = self.users.get(str(telegram_id))
        return user_data["token"] if user_data else None
    
    def is_user_authorized(self, telegram_id: int) -> bool:
        """Check if user is authorized."""
        return str(telegram_id) in self.users
    
    def save_pending_transaction(self, telegram_id: int, transaction_data: Dict[str, Any]):
        """Save pending transaction for confirmation."""
        self.pending[str(telegram_id)] = transaction_data
        self._save_pending()
    
    def get_pending_transaction(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get pending transaction."""
        return self.pending.get(str(telegram_id))
    
    def clear_pending_transaction(self, telegram_id: int):
        """Clear pending transaction."""
        if str(telegram_id) in self.pending:
            del self.pending[str(telegram_id)]
            self._save_pending()
    
    def logout_user(self, telegram_id: int):
        """Logout user."""
        if str(telegram_id) in self.users:
            del self.users[str(telegram_id)]

            self._save_users()
        self.clear_pending_transaction(telegram_id)


# Global storage instance
storage = UserStorage()
