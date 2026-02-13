from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Integer, BigInteger, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base

class ClickTransaction(Base):
    """
    Model to track Click.uz payment transactions.
    """
    __tablename__ = "click_transactions"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Click parameters
    click_trans_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    service_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    click_paydoc_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # Internal parameters
    merchant_trans_id: Mapped[str] = mapped_column(String, index=True, nullable=False) # Our Order ID
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="input", nullable=False) 
    # input, waiting, preauth, confirmed, rejected, refunded, error
    
    action: Mapped[int] = mapped_column(Integer, nullable=False) # 0=Prepare, 1=Complete
    
    sign_time: Mapped[str] = mapped_column(String, nullable=False)
    error: Mapped[int] = mapped_column(Integer, default=0)
    error_note: Mapped[str] = mapped_column(String, default="Success")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="click_transactions")
