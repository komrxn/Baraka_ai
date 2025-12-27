from datetime import datetime
from decimal import Decimal
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    """Base transaction schema."""
    type: str = Field(..., pattern="^(income|expense)$")
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="uzs", max_length=3)
    description: Optional[str] = Field(None, max_length=500)
    category_id: Optional[UUID] = None
    transaction_date: Optional[datetime] = None


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    pass


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    description: Optional[str] = Field(None, max_length=500)
    category_id: Optional[UUID] = None
    transaction_date: Optional[datetime] = None


from .category import CategoryResponse

class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    id: UUID
    user_id: UUID
    ai_parsed_data: Optional[dict[str, Any]] = None
    ai_confidence: Optional[Decimal] = None
    category: Optional[CategoryResponse] = None  # <--- Added
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list."""
    total: int
    items: list[TransactionResponse]
    page: int
    page_size: int
