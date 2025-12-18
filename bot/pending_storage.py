"""Pending transactions storage for confirmation flow."""
from typing import Dict, List, Any
from datetime import datetime, timedelta
import uuid


class PendingTransactionStorage:
    """Store pending transactions awaiting user confirmation."""
    
    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}
        # Format: {tx_id: {user_id, tx_data, created_at}}
    
    def add(self, user_id: int, tx_data: Dict[str, Any]) -> str:
        """Add pending transaction and return tx_id."""
        tx_id = str(uuid.uuid4())[:8]  # Short ID
        self._storage[tx_id] = {
            'user_id': user_id,
            'tx_data': tx_data,
            'created_at': datetime.now()
        }
        return tx_id
    
    def get(self, tx_id: str) -> Optional[Dict]:
        """Get pending transaction."""
        return self._storage.get(tx_id)
    
    def update(self, tx_id: str, data: Dict):
        """Update pending transaction."""
        if tx_id in self._storage:
            self._storage[tx_id] = data
    
    def remove(self, tx_id: str):
        """Remove pending transaction."""
        if tx_id in self._storage:
            del self._storage[tx_id]
    
    def cleanup_old(self, hours: int = 24):
        """Remove transactions older than N hours."""
        now = datetime.now()
        expired = [
            tx_id for tx_id, data in self._storage.items()
            if now - data['created_at'] > timedelta(hours=hours)
        ]
        for tx_id in expired:
            del self._storage[tx_id]


# Global instance
pending_storage = PendingTransactionStorage()
