"""Dialog context manager using Redis."""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DialogContext:
    """Manages dialog context for each user."""
    
    def __init__(self):
        """Initialize in-memory storage (can be replaced with Redis)."""
        self._contexts: Dict[int, List[Dict[str, Any]]] = {}
        self.max_history = 10  # Keep last 10 messages
        self.ttl_minutes = 30  # Clear after 30 minutes of inactivity
    
    def add_message(self, user_id: int, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to user's context."""
        if user_id not in self._contexts:
            self._contexts[user_id] = []
        
        message = {
            "role": role,  # user, assistant, system
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self._contexts[user_id].append(message)
        
        # Keep only last N messages
        if len(self._contexts[user_id]) > self.max_history:
            self._contexts[user_id] = self._contexts[user_id][-self.max_history:]
        
        logger.info(f"Added message to context for user {user_id}: {role}")
    
    def get_context(self, user_id: int, last_n: int = 5) -> List[Dict[str, Any]]:
        """Get recent context for user."""
        if user_id not in self._contexts:
            return []
        
        # Clean old messages
        self._clean_old_messages(user_id)
        
        return self._contexts[user_id][-last_n:]
    
    def get_last_transaction(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get last pending or saved transaction from context."""
        context = self.get_context(user_id)
        
        for msg in reversed(context):
            msg_type = msg.get("metadata", {}).get("type")
            if msg_type in ["pending_transaction", "saved_transaction"]:
                return msg.get("metadata", {}).get("transaction")
        
        return None
    
    def clear_context(self, user_id: int):
        """Clear user's context."""
        if user_id in self._contexts:
            del self._contexts[user_id]
            logger.info(f"Cleared context for user {user_id}")
    
    def _clean_old_messages(self, user_id: int):
        """Remove messages older than TTL."""
        if user_id not in self._contexts:
            return
        
        cutoff = datetime.now() - timedelta(minutes=self.ttl_minutes)
        
        self._contexts[user_id] = [
            msg for msg in self._contexts[user_id]
            if datetime.fromisoformat(msg["timestamp"]) > cutoff
        ]
    
    def format_for_ai(self, user_id: int) -> str:
        """Format context as string for AI prompt."""
        context = self.get_context(user_id)
        
        if not context:
            return ""
        
        lines = ["История диалога:"]
        for msg in context:
            role_label = {
                "user": "Пользователь",
                "assistant": "Ассистент",
                "system": "Система"
            }.get(msg["role"], msg["role"])
            
            lines.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(lines)
    
    def get_openai_messages(self, user_id: int, last_n: int = 10) -> list:
        """Get conversation history formatted for OpenAI API."""
        context = self.get_context(user_id, last_n=last_n)
        
        messages = []
        for msg in context:
            # Only include user and assistant messages
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        return messages


# Global context manager
dialog_context = DialogContext()
