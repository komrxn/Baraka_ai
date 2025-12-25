"""User data storage."""
import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


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
            # json.dump(self.users, f, indent=2)
            json.dump(self.users, f, indent=2, default=str) # Added default=str for datetime objects
    
    def _save_pending(self):
        """Save pending to file."""
        with open(self.pending_file, 'w') as f:
            json.dump(self.pending, f, indent=2)
    
    def save_user_token(self, user_id: int, token: str, username: str = ""):
        """Save user token and username."""
        # Ensure user_id is stored as a string key
        user_id_str = str(user_id)
        current_data = self.users.get(user_id_str, {})
        current_lang = current_data.get('language', 'uz')
        
        self.users[user_id_str] = {
            'token': token,
            'username': username,
            'language': current_lang
        }
        self._save_users()
        logger.info(f"Saved token for user {user_id}")
    
    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language (default: uz).
        
        For authorized users, fetches from database.
        For unauthorized users, uses local storage.
        """
        # First check local storage (fast path)
        local_lang = self.users.get(str(user_id), {}).get('language', 'uz')
        
        # If user is authorized, try to get language from API
        if self.is_user_authorized(user_id):
            try:
                import asyncio
                from .api_client import MidasAPIClient
                from .config import config
                
                token = self.get_user_token(user_id)
                if token:
                    api = MidasAPIClient(config.API_BASE_URL)
                    api.set_token(token)
                    
                    # Fetch user info from API
                    loop = asyncio.get_event_loop()
                    user_info = loop.run_until_complete(api.get_me())
                    
                    # Update local storage with fetched language
                    db_lang = user_info.get('language', 'uz')
                    if db_lang != local_lang:
                        self.set_user_language(user_id, db_lang)
                    
                    return db_lang
            except Exception as e:
                logger.warning(f"Failed to fetch language from API for user {user_id}: {e}")
                # Fallback to local storage
        
        return local_lang
    
    def set_user_language(self, user_id: int, language: str):
        """Set user's preferred language (local storage only)."""
        user_id_str = str(user_id)
        if user_id_str in self.users:
            self.users[user_id_str]['language'] = language
        else:
            # If user doesn't exist, create a minimal entry with just language
            self.users[user_id_str] = {'language': language}
        self._save_users()
    
    def clear_user_token(self, telegram_id: int):
        """Clear user token when it expires or becomes invalid."""
        user_id_str = str(telegram_id)
        if user_id_str in self.users:
            # Preserve language, just remove token (set to None or empty)
            # Or if strict about structure, we can just pop 'token' key if we handled it safely elsewhere.
            # But get_user_token expects 'token' key.
            # Let's set token to None
            self.users[user_id_str]['token'] = None
            self._save_users()
    
    def get_user_token(self, telegram_id: int) -> Optional[str]:
        """Get user auth token."""
        user_data = self.users.get(str(telegram_id))
        return user_data.get("token") if user_data else None
    
    def is_user_authorized(self, telegram_id: int) -> bool:
        """Check if user is authorized."""
        user = self.users.get(str(telegram_id))
        return user is not None and user.get('token') is not None
    
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
        self.clear_user_token(telegram_id)
        self.clear_pending_transaction(telegram_id)


# Global storage instance
storage = UserStorage()
