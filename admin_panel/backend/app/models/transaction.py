from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4
from sqlalchemy import String, Numeric, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from ..database import Base

class Transaction(Base):
    """Transaction model for details (Admin Read-Only)."""
    
    __tablename__ = "transactions"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    category_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), 
        # ForeignKey("categories.id", ondelete="SET NULL"),  # Category model might not exist in admin yet
        nullable=True,
        index=True
    )
    
    # Transaction details
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # income, expense
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="uzs")
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # AI parsing metadata
    ai_parsed_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ai_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    
    # Timestamps
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Relationships (Commented out to avoid clutter/errors in Admin if not needed yet)
    # user: Mapped["User"] = relationship("User", back_populates="transactions")
    # category: Mapped[Optional["Category"]] = relationship("Category", back_populates="transactions")
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, type={self.type}, amount={self.amount} {self.currency})>"
