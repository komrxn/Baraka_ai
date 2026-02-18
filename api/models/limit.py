from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import uuid4
from sqlalchemy import Numeric, DateTime, Date, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class Limit(Base):
    """Budget limit model for tracking spending limits per category."""
    
    __tablename__ = "limits"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    category_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    
    # Limit details
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="limits")
    category: Mapped["Category"] = relationship("Category")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'category_id', 'period_start', name='uq_user_category_period'),
    )
    
    def __repr__(self) -> str:
        return f"<Limit(id={self.id}, category_id={self.category_id}, amount={self.amount})>"
