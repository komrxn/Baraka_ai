"""API client for Baraka Ai backend."""
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


class BarakaAPIClient:
    """Client for interacting with Baraka Ai API."""
    
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
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def get_transaction(self, tx_id: str) -> Dict[str, Any]:
        """Get single transaction by ID."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/transactions/{tx_id}",
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
    async def create_category(self, name: str, type: str, icon: str = "🏷", slug: Optional[str] = None) -> Dict[str, Any]:
        """Create a new category."""
        final_slug = slug if slug else name.lower().replace(" ", "_")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/categories",
                json={"name": name, "type": type, "icon": icon, "slug": final_slug},
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
    async def get_debt(self, debt_id: str) -> Dict[str, Any]:
        """Get single debt by ID."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/debts/{debt_id}",
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

    @handle_auth_errors
    async def get_subscription_status(self, telegram_id: Optional[int] = None) -> Dict[str, Any]:
        """Get subscription status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/subscriptions/status",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def activate_trial(self) -> Dict[str, Any]:
        """Activate free trial."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/subscriptions/trial",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def generate_payment_link(self, plan_id: str = "monthly") -> Dict[str, Any]:
        """Generate payment link."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/subscriptions/pay",
                json={"plan_id": plan_id},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def set_limit(self, category_slug: str, amount: float, period: str = "month") -> Dict[str, Any]:
        """Set limit for a category (Create or Update)."""
        import datetime
        from dateutil.relativedelta import relativedelta
        
        # 1. Resolve category
        categories = await self.get_categories()
        category_id = None
        target_slug = category_slug.lower().strip()
        
        for cat in categories:
            if cat.get("slug") == target_slug:
                category_id = cat.get("id")
                break
        
        if not category_id:
            # Try name match
            for cat in categories:
                if cat.get("name", "").lower() == target_slug:
                    category_id = cat.get("id")
                    break
        
        if not category_id:
             # Try fallback "other_expense"
             for cat in categories:
                if cat.get("slug") == "other_expense":
                    category_id = cat.get("id")
                    break
                    
        if not category_id:
            logger.error(f"Category '{category_slug}' not found. Available slugs: {[c.get('slug') for c in categories[:5]]}...")
            raise ValueError(f"Category '{category_slug}' not found.")
            
        logger.info(f"Resolved category '{category_slug}' to ID {category_id}")

        # 2. Determine period dates
        today = datetime.date.today()
        start_date = datetime.date(today.year, today.month, 1)
        end_date = start_date + relativedelta(months=1) - relativedelta(days=1)
        
        # 3. Check existing limit
        # We need to fetch limits and check if one exists for this category/period
        # The list_limits endpoint filters by period if provided, or we can just fetch all and filter in python
        # Let's fetch current month limits
        current_limits_summary = await self.get_balance(period="month") # This returns analytics... not specific limits list.
        # Use GET /limits endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/limits",
                params={"period_start": start_date.isoformat(), "period_end": end_date.isoformat()},
                headers=self.headers
            )
            response.raise_for_status()
            limits = response.json()
            
        existing_limit = next((l for l in limits if l["category_id"] == category_id), None)
        
        async with httpx.AsyncClient() as client:
            if existing_limit:
                # UPDATE
                response = await client.put(
                    f"{self.base_url}/limits/{existing_limit['id']}",
                    json={"amount": amount},
                    headers=self.headers
                )
            else:
                # CREATE
                response = await client.post(
                    f"{self.base_url}/limits",
                    json={
                        "category_id": category_id,
                        "amount": amount,
                        "period_start": start_date.isoformat(),
                        "period_end": end_date.isoformat()
                    },
                    headers=self.headers
                )
            response.raise_for_status()
            return response.json()

    @handle_auth_errors
    async def increment_usage(self, usage_type: str) -> Dict[str, Any]:
        """Increment usage counter (voice or photo)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/usage",
                params={"type": usage_type},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
