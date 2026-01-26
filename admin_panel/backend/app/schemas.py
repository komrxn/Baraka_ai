from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

# Auth Schemas
class AdminLogin(BaseModel):
    username: str # email
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    is_super_admin: bool

# User Schemas
class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    telegram_id: int
    name: str
    phone_number: str
    default_currency: str
    language: str
    is_premium: bool
    subscription_type: Optional[str]
    subscription_ends_at: Optional[datetime]
    created_at: datetime
    voice_usage_count: int

class UserList(BaseModel):
    items: list[UserBase]
    total: int
    page: int
    size: int

class SubscriptionUpdate(BaseModel):
    subscription_type: str # monthly, annual, trial, null
    days: Optional[int] = None # Add days from now

class SubscriptionUpdateAction(BaseModel):
    action: str # "grant", "revoke"
    plan: Optional[str] = None # "monthly", "quarterly", "annual"
    duration_days: Optional[int] = None
