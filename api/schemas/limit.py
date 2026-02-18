from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class LimitBase(BaseModel):
    """Base limit schema."""
    category_id: Optional[UUID] = None
    amount: Decimal = Field(..., gt=0, description="Limit amount")
    period_start: date = Field(..., description="Start of the period")
    period_end: date = Field(..., description="End of the period")


class LimitCreate(LimitBase):
    """Schema for creating a limit."""
    pass


class LimitUpdate(BaseModel):
    """Schema for updating a limit."""
    amount: Optional[Decimal] = Field(None, gt=0)
    period_start: Optional[date] = None
    period_end: Optional[date] = None


class LimitResponse(LimitBase):
    """Schema for limit response."""
    id: UUID
    user_id: UUID
    spent: Decimal = Field(default=Decimal("0"), description="Amount spent in this period")
    remaining: Decimal = Field(default=Decimal("0"), description="Amount remaining")
    percentage: float = Field(default=0.0, ge=0, le=100, description="Percentage spent")
    is_exceeded: bool = Field(default=False, description="Whether limit is exceeded")
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LimitSummary(BaseModel):
    """Summary of limits for a period."""
    total_limits: int = 0
    total_budget: Decimal = Decimal("0")
    total_spent: Decimal = Decimal("0")
    exceeded_count: int = 0
    limits: list[LimitResponse] = []
