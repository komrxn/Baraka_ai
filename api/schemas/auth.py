from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for user registration via Telegram."""
    telegram_id: int = Field(..., description="Telegram user ID")
    phone_number: str = Field(..., min_length=10, max_length=20, description="Phone number")
    name: str = Field(..., min_length=1, max_length=100, description="User name")
    language: str = Field(default="uz", description="User interface language (uz, ru, en)")


class UserLogin(BaseModel):
    """Schema for user login via phone."""
    phone_number: str = Field(..., description="Phone number")
    telegram_id: Optional[int] = Field(None, description="Optional Telegram ID for validation")


class UserResponse(BaseModel):
    """Schema for user response."""
    id: UUID
    telegram_id: int
    phone_number: str
    name: str
    default_currency: str
    language: str
    created_at: datetime
    is_premium: bool = False
    subscription_type: Optional[str] = None
    subscription_ends_at: Optional[datetime] = None
    is_trial_used: bool = False
    
    is_active: bool = False
    
    class Config:
        from_attributes = True

    @staticmethod
    def resolve_is_active(user) -> bool:
        if not user.is_premium:
            return False
        if not user.subscription_ends_at:
            return False
        # Naive check, assuming server time is acceptable or user object has been validated
        return user.subscription_ends_at.timestamp() > datetime.now().timestamp()


class TelegramRegister(BaseModel):
    """Telegram-based registration."""
    telegram_id: int
    phone_number: str
    name: str
    language: str = "uz"  # Default to Uzbek


class LoginResponse(BaseModel):
    """Login response with token."""
    access_token: str
    token_type: str = "bearer"
    username: str
    language: str = "uz"


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
