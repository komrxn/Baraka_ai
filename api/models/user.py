from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import String, DateTime, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class User(Base):
    """User model with Telegram-native authentication."""
    
    __tablename__ = "users"
    
    # Primary fields
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # User preferences
    default_currency: Mapped[str] = mapped_column(String(3), default="uzs", nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    language: Mapped[str] = mapped_column(String(2), default="uz", server_default="uz", nullable=False)
    
    # Subscription
    subscription_type: Mapped[str] = mapped_column(String(20), default="free", server_default="free", nullable=False) # free, plus, pro, premium (or trial -> pro with short duration)
    subscription_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_trial_used: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)
    
    # Limits & Usage Tracking
    last_daily_reset: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    voice_usage_daily: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    image_usage_daily: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    text_usage_daily: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    
    # Recoil (3-day limit)
    last_3day_reset: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    request_count_3day: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    
    # Legacy counters (keep for history or migrate later)
    voice_usage_count: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    photo_usage_count: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    text_usage_count: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    
    # Relationships
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    categories: Mapped[list["Category"]] = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    debts: Mapped[list["Debt"]] = relationship("Debt", back_populates="user", cascade="all, delete-orphan")
    limits: Mapped[list["Limit"]] = relationship("Limit", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def subscription_tier(self) -> str:
        """Helper to normalize subscription tier."""
        if self.subscription_type in ("trial", "plus", "pro", "premium"):
             return self.subscription_type
        return "free"

    @property
    def is_premium(self) -> bool:
        """Alias for is_premium_active for schema compatibility."""
        return self.is_premium_active

    @property
    def is_premium_active(self) -> bool:
        """Check if premium/paid subscription is active."""
        if self.subscription_type == "free":
            return False
            
        if self.subscription_ends_at and self.subscription_ends_at.replace(tzinfo=None) < datetime.now():
            return False
            
        return True

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, tier={self.subscription_type})>"
