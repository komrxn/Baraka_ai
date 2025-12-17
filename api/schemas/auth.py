from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for user registration via Telegram."""
    telegram_id: int = Field(..., description="Telegram user ID")
    phone_number: str = Field(..., min_length=10, max_length=20, description="Phone number")
    name: str = Field(..., min_length=1, max_length=100, description="User name")


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
    created_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
