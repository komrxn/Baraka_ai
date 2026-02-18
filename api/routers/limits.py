from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from dateutil.relativedelta import relativedelta

from ..database import get_db
from ..models.limit import Limit
from ..models.transaction import Transaction
from ..models.category import Category
from ..models.user import User
from ..schemas.limit import LimitCreate, LimitUpdate, LimitResponse, LimitSummary
from ..auth.jwt import get_current_user

router = APIRouter(prefix="/limits", tags=["limits"])


async def calculate_spent(
    db: AsyncSession,
    user_id: UUID,
    category_id: UUID,
    period_start: date,
    period_end: date
) -> Decimal:
    """Calculate spent amount for a category in a period."""
    query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        and_(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end
        )
    )
    
    if category_id:
        query = query.where(Transaction.category_id == category_id)
        
    result = await db.execute(query)
    return Decimal(str(result.scalar() or 0))


def enrich_limit_with_spending(limit: Limit, spent: Decimal, category_name: Optional[str] = None) -> LimitResponse:
    """Enrich limit with spending data."""
    remaining = limit.amount - spent
    percentage = float((spent / limit.amount * 100) if limit.amount > 0 else 0)
    
    return LimitResponse(
        id=limit.id,
        user_id=limit.user_id,
        category_id=limit.category_id,
        amount=limit.amount,
        period_start=limit.period_start,
        period_end=limit.period_end,
        spent=spent,
        remaining=remaining,
        percentage=min(percentage, 100.0),
        is_exceeded=spent > limit.amount,
        category_name=category_name,
        created_at=limit.created_at,
        updated_at=limit.updated_at
    )


@router.post("", response_model=LimitResponse, status_code=201)
async def create_limit(
    limit_data: LimitCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new budget limit."""
    # Check if limit already exists for this category/global and period
    query = select(Limit).where(
        and_(
            Limit.user_id == current_user.id,
            Limit.period_start == limit_data.period_start,
            # Handling nullable category_id comparison
            Limit.category_id == limit_data.category_id if limit_data.category_id else Limit.category_id.is_(None)
        )
    )
    
    existing = await db.execute(query)
    
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Limit already exists for this category (or global) and period"
        )
    
    # Get category name if specific category
    category_name = "All Expenses"
    if limit_data.category_id:
        category_result = await db.execute(
            select(Category).where(Category.id == limit_data.category_id)
        )
        category = category_result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        category_name = category.name
    
    limit = Limit(
        user_id=current_user.id,
        **limit_data.model_dump()
    )
    
    db.add(limit)
    await db.commit()
    await db.refresh(limit)
    
    # Calculate spent
    spent = await calculate_spent(
        db, current_user.id, limit.category_id,
        limit.period_start, limit.period_end
    )
    
    return enrich_limit_with_spending(limit, spent, category_name)


@router.get("", response_model=list[LimitResponse])
async def list_limits(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all limits for current user with spending data."""
    query = select(Limit).where(Limit.user_id == current_user.id)
    
    if period_start:
        query = query.where(Limit.period_start >= period_start)
    if period_end:
        query = query.where(Limit.period_end <= period_end)
    
    query = query.order_by(Limit.period_start.desc())
    
    result = await db.execute(query)
    limits = result.scalars().all()
    
    # Enrich with spending data
    enriched_limits = []
    for limit in limits:
        spent = await calculate_spent(
            db, current_user.id, limit.category_id,
            limit.period_start, limit.period_end
        )
        
        # Get category name
        cat_result = await db.execute(
            select(Category.name).where(Category.id == limit.category_id)
        )
        category_name = cat_result.scalar()
        
        enriched_limits.append(enrich_limit_with_spending(limit, spent, category_name))
    
    return enriched_limits


@router.get("/current", response_model=LimitSummary)
async def get_current_month_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all limits for the current month with summary."""
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    end_of_month = start_of_month + relativedelta(months=1) - relativedelta(days=1)
    
    query = select(Limit).where(
        and_(
            Limit.user_id == current_user.id,
           Limit.period_start == start_of_month
        )
    )
    
    result = await db.execute(query)
    limits = result.scalars().all()
    
    # Enrich with spending data
    enriched_limits = []
    total_budget = Decimal("0")
    total_spent = Decimal("0")
    exceeded_count = 0
    
    for limit in limits:
        spent = await calculate_spent(
            db, current_user.id, limit.category_id,
            limit.period_start, limit.period_end
        )
        
        # Get category name
        cat_result = await db.execute(
            select(Category.name).where(Category.id == limit.category_id)
        )
        category_name = cat_result.scalar()
        
        enriched = enrich_limit_with_spending(limit, spent, category_name)
        enriched_limits.append(enriched)
        
        total_budget += limit.amount
        total_spent += spent
        if enriched.is_exceeded:
            exceeded_count += 1
    
    return LimitSummary(
        total_limits=len(limits),
        total_budget=total_budget,
        total_spent=total_spent,
        exceeded_count=exceeded_count,
        limits=enriched_limits
    )


@router.get("/{limit_id}", response_model=LimitResponse)
async def get_limit(
    limit_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific limit by ID."""
    result = await db.execute(
        select(Limit).where(
            and_(
                Limit.id == limit_id,
                Limit.user_id == current_user.id
            )
        )
    )
    limit = result.scalar_one_or_none()
    
    if not limit:
        raise HTTPException(status_code=404, detail="Limit not found")
    
    # Calculate spent
    spent = await calculate_spent(
        db, current_user.id, limit.category_id,
        limit.period_start, limit.period_end
    )
    
    # Get category name
    cat_result = await db.execute(
        select(Category.name).where(Category.id == limit.category_id)
    )
    category_name = cat_result.scalar()
    
    return enrich_limit_with_spending(limit, spent, category_name)


@router.put("/{limit_id}", response_model=LimitResponse)
async def update_limit(
    limit_id: UUID,
    limit_data: LimitUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a limit."""
    result = await db.execute(
        select(Limit).where(
            and_(
                Limit.id == limit_id,
                Limit.user_id == current_user.id
            )
        )
    )
    limit = result.scalar_one_or_none()
    
    if not limit:
        raise HTTPException(status_code=404, detail="Limit not found")
    
    # Update fields
    update_data = limit_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(limit, field, value)
    
    await db.commit()
    await db.refresh(limit)
    
    # Calculate spent
    spent = await calculate_spent(
        db, current_user.id, limit.category_id,
        limit.period_start, limit.period_end
    )
    
    # Get category name
    cat_result = await db.execute(
        select(Category.name).where(Category.id == limit.category_id)
    )
    category_name = cat_result.scalar()
    
    return enrich_limit_with_spending(limit, spent, category_name)


@router.delete("/{limit_id}", status_code=204)
async def delete_limit(
    limit_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a limit."""
    result = await db.execute(
        select(Limit).where(
            and_(
                Limit.id == limit_id,
                Limit.user_id == current_user.id
            )
        )
    )
    limit = result.scalar_one_or_none()
    
    if not limit:
        raise HTTPException(status_code=404, detail="Limit not found")
    
    await db.delete(limit)
    await db.commit()
    
    return None
