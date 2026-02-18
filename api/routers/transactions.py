from datetime import datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from ..database import get_db
from ..models.user import User
from ..models.transaction import Transaction
from ..models.category import Category
from ..schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse
)
from ..auth.jwt import get_current_user
from ..services.limits import check_limit_thresholds  # <--- Added import

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    type: Optional[str] = Query(None, pattern="^(income|expense)$"),
    category_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's transactions with filtering and pagination.
    
    - **page**: Page number (1-indexed)
    - **page_size**: Items per page (1-100)
    - **type**: Filter by income/expense
    - **category_id**: Filter by category
    - **start_date**: Filter by date range (inclusive)
    - **end_date**: Filter by date range (inclusive)
    """
    
    # Build query
    query = select(Transaction).where(Transaction.user_id == current_user.id)
    
    if type:
        query = query.where(Transaction.type == type)
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if start_date:
        query = query.where(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.where(Transaction.transaction_date <= end_date)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Pagination
    from sqlalchemy.orm import joinedload
    query = query.order_by(Transaction.transaction_date.desc())
    query = query.options(joinedload(Transaction.category)) # <--- Eager load categories
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return TransactionListResponse(
        total=total,
        items=[TransactionResponse.model_validate(tx) for tx in transactions],
        page=page,
        page_size=page_size
    )


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new transaction manually."""
    
    # Validate category belongs to user or is default
    if transaction_data.category_id:
        cat_result = await db.execute(
            select(Category).where(
                Category.id == transaction_data.category_id,
                ((Category.user_id == current_user.id) | (Category.is_default == True))
            )
        )
        if not cat_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category"
            )
    
    # Create transaction
    new_transaction = Transaction(
        user_id=current_user.id,
        **transaction_data.model_dump()
    )
    
    db.add(new_transaction)
    await db.commit()
    
    # Fetch full object with category
    from sqlalchemy.orm import joinedload
    result = await db.execute(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.id == new_transaction.id)
    )
    result = await db.execute(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.id == new_transaction.id)
    )
    new_transaction = result.scalar_one()

    # Check limits
    if new_transaction.type == "expense" and new_transaction.category_id:
        warning = await check_limit_thresholds(
            db, 
            current_user.id, 
            new_transaction.category_id, 
            new_transaction.amount, 
            new_transaction.transaction_date.date(),
            current_user.language  # <--- Added language
        )
        if warning:
            # We can't attach it to sqlalchemy model directly if it's not a column, 
            # but we can attach it to the Pydantic model response
            # Or simpler: monkey patch the object before validation, or construct response manually
            setattr(new_transaction, "limit_warning", warning)
    
    return TransactionResponse.model_validate(new_transaction)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific transaction by ID."""
    from sqlalchemy.orm import joinedload
    
    result = await db.execute(
        select(Transaction)
        .options(joinedload(Transaction.category))  # <--- Eager load
        .where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return TransactionResponse.model_validate(transaction)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    update_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a transaction."""
    
    # Find transaction
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(transaction, field, value)
    
    await db.commit()
    # Fetch again with relationship to return full data
    from sqlalchemy.orm import joinedload
    result = await db.execute(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.id == transaction_id)
    )
    result = await db.execute(
        select(Transaction)
        .options(joinedload(Transaction.category))
        .where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one()

    # Check limits (only if expense)
    if transaction.type == "expense" and transaction.category_id:
        # For update, we consider the NEW amount as the one contributing to the threshold
        # (check_limit_thresholds subtracts 'amount' from total to find 'before' state)
        warning = await check_limit_thresholds(
            db, 
            current_user.id, 
            transaction.category_id, 
            transaction.amount, 
            transaction.transaction_date.date(),
            current_user.language  # <--- Added language
        )
        if warning:
            setattr(transaction, "limit_warning", warning)
    
    return TransactionResponse.model_validate(transaction)


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_transactions(
    transaction_ids: List[UUID],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple transactions at once."""
    
    # Verify ownership and existence
    result = await db.execute(
        select(Transaction).where(
            Transaction.id.in_(transaction_ids),
            Transaction.user_id == current_user.id
        )
    )
    transactions = result.scalars().all()
    
    if not transactions:
        # Nothing to delete (or IDs invalid/not owned)
        return None
        
    for tx in transactions:
        await db.delete(tx)
        
    await db.commit()
    return None


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a transaction."""
    
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    await db.delete(transaction)
    await db.commit()
    
    return None
