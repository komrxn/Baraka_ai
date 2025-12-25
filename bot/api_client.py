"""API client for Midas backend."""
import httpx
from typing import Optional, Dict, Any
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class UnauthorizedError(Exception):
    """Raised when API returns 401 Unauthorized (token expired/invalid)."""
    pass


def handle_auth_errors(func):
    """Decorator to handle 401 Unauthorized errors."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning(f"401 Unauthorized in {func.__name__}: Token expired or invalid")
                raise UnauthorizedError("Token expired or invalid")
            raise
    return wrapper


class MidasAPIClient:
    """Client for interacting with Midas API."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.token: Optional[str] = None
        
    def set_token(self, token: str):
        """Set authentication token."""
        self.token = token
        
    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers with auth."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def register(self, telegram_id: int, phone: str, name: str, language: str = "uz") -> Dict[str, Any]:
        """Register a new user."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/register",
                json={
                    "telegram_id": telegram_id,
                    "phone_number": phone,
                    "name": name,
                    "language": language
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def login(self, phone_number: str) -> Dict[str, Any]:
        """Login user via phone."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/login",
                json={"phone_number": phone_number}
            )
            response.raise_for_status()
            return response.json()
    
    @handle_auth_errors
    async def get_me(self) -> Dict[str, Any]:
        """Get current user info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/auth/me",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def parse_text(self, text: str, auto_create: bool = False) -> Dict[str, Any]:
        """Parse transaction from text using AI."""
        async with httpx.AsyncClient(timeout=60.0) as client:  # ← 60 секунд для AI
            response = await client.post(
                f"{self.base_url}/ai/parse-transaction",
                headers={"Authorization": self.headers["Authorization"]} if self.token else {},
                data={  # ← Form data, не JSON!
                    "text": text,
                    "auto_create": str(auto_create).lower()
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def parse_voice(self, audio_bytes: bytes, auto_create: bool = False) -> Dict[str, Any]:
        """Parse transaction from voice using AI."""
        async with httpx.AsyncClient(timeout=60.0) as client:  # ← 60 секунд для AI
            response = await client.post(
                f"{self.base_url}/ai/parse-transaction",
                headers={"Authorization": self.headers["Authorization"]} if self.token else {},
                data={"auto_create": str(auto_create).lower()},
                files={"voice": ("audio.ogg", audio_bytes, "audio/ogg")}
            )
            response.raise_for_status()
            return response.json()
    
    async def parse_image(self, image_bytes: bytes, auto_create: bool = False) -> Dict[str, Any]:
        """Parse transaction from receipt image using AI."""
        async with httpx.AsyncClient(timeout=60.0) as client:  # ← 60 секунд для AI
            response = await client.post(
                f"{self.base_url}/ai/parse-transaction",
                headers={"Authorization": self.headers["Authorization"]} if self.token else {},
                data={"auto_create": str(auto_create).lower()},
                files={"image": ("receipt.jpg", image_bytes, "image/jpeg")}
            )
            response.raise_for_status()
            return response.json()
    
    @handle_auth_errors
    async def create_transaction(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new transaction."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/transactions",
                json=tx_data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    @handle_auth_errors
    async def update_transaction(self, tx_id: str, **updates) -> Dict[str, Any]:
        """Update transaction via PATCH."""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/transactions/{tx_id}",
                json=updates,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    @handle_auth_errors
    async def delete_transaction(self, tx_id: str) -> None:
        """Delete transaction."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/transactions/{tx_id}",
                headers=self.headers
            )
            response.raise_for_status()
    
    @handle_auth_errors
    async def get_balance(self, period: str = "month") -> Dict[str, Any]:
        """Get balance."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/analytics/balance",
                params={"period": period},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    @handle_auth_errors
    async def get_categories(self) -> list:
        """Get all categories."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/categories",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    @handle_auth_errors
    async def get_category_breakdown(self, period: str = "month") -> Dict[str, Any]:
        """Get category breakdown statistics."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/analytics/categories",
                params={"period": period, "transaction_type": "expense"},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def get_transactions(self, limit: int = 5) -> list:
        """Get recent transactions."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/transactions",
                params={"limit": limit, "skip": 0},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def create_category(self, name: str, type: str, icon: str = "🏷") -> Dict[str, Any]:
        """Create a new category."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/categories",
                json={"name": name, "type": type, "icon": icon, "slug": name.lower().replace(" ", "_")},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def create_debt(self, debt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new debt record."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/debts",
                json=debt_data,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def get_debts(self, status: str = "open") -> list:
        """Get list of debts."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/debts",
                params={"status": status},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def mark_debt_as_paid(self, debt_id: str) -> Dict[str, Any]:
        """Mark debt as paid."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/debts/{debt_id}/mark-paid",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def update_debt(self, debt_id: str, **updates) -> Dict[str, Any]:
        """Update debt via PUT."""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/debts/{debt_id}",
                json=updates,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def delete_debt(self, debt_id: str) -> None:
        """Delete debt."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/debts/{debt_id}",
                headers=self.headers
            )
            response.raise_for_status()

    @handle_auth_errors
    async def update_user_language(self, language: str) -> Dict[str, Any]:
        """Update user's language preference."""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/auth/me/language",
                params={"language": language},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
