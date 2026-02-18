
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_

from ..models.limit import Limit
from ..models.transaction import Transaction
from ..models.category import Category

async def check_limit_thresholds(
    db: AsyncSession,
    user_id: UUID,
    category_id: UUID,
    amount_added: Decimal,
    transaction_date: date,
    language: str = "en"
) -> Optional[str]:
    """
    Check if adding 'amount_added' to 'category_id' expenses crosses any limit thresholds.
    Returns a warning message if crossed, else None.
    Thresholds: 50%, 75%, 90%, 100%.
    """
    # 1. Find active limits (both specific and global) covering this transaction date
    # We check if transaction_date falls within [period_start, period_end]
    limits_result = await db.execute(
        select(Limit).where(
            and_(
                Limit.user_id == user_id,
                # Either matching category OR global (null)
                or_(Limit.category_id == category_id, Limit.category_id == None),
                Limit.period_start <= transaction_date,
                Limit.period_end >= transaction_date
            )
        )
    )
    limits = limits_result.scalars().all()
    
    if not limits:
        return None

    warnings = []

    for limit in limits:
        if limit.amount <= 0:
            continue
            
        # Calculate total spent for this limit's criteria
        # If global limit (category_id is None), sum ALL expenses
        # If specific limit, sum only that category
        
        query = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.type == "expense",
                Transaction.transaction_date >= limit.period_start,
                Transaction.transaction_date <= limit.period_end,
            )
        )
        
        if limit.category_id:
            query = query.where(Transaction.category_id == limit.category_id)
        # else: for global limit, we count everything (no category filter)
        
        spent_result = await db.execute(query)
        spent_db = Decimal(str(spent_result.scalar() or 0))
        total_spent = spent_db # This already includes the new transaction if it was committed? 
        # Wait, check_limit is usually called AFTER adding transaction but BEFORE commit? 
        # In routers/transactions.py: db.add(new_tx), db.commit(), THEN check_limit.
        # So the new transaction is already in DB.
        
        percent = (total_spent / limit.amount) * 100
        
        thresholds = [50, 75, 90, 100]
        crossed_threshold = None
        
        # We need to know if we JUST crossed it. 
        # spent_before = total_spent - amount_added
        # percent_before = (spent_before / limit.amount) * 100
        # This logic assumes the new transaction caused the crossing.
        
        spent_before = total_spent - amount_added
        percent_before = (spent_before / limit.amount) * 100
        
        for t in thresholds:
            if percent_before < t and percent >= t:
                crossed_threshold = t
        
        if crossed_threshold:
            # Prepare message
            lang = language if language in ['ru', 'uz', 'en'] else 'en'
            
            if limit.category_id:
                cat_result = await db.execute(select(Category.name).where(Category.id == limit.category_id))
                limit_name = cat_result.scalar() or "Category"
            else:
                limit_name = {
                    'en': "All Expenses",
                    'ru': "Все расходы",
                    'uz': "Barcha xarajatlar"
                }.get(lang, "All Expenses")
            
            msgs = {
                'exceeded': {
                    'en': "⚠️ Limit exceeded! {cat}: {pct:.1f}% used.",
                    'ru': "⚠️ Лимит исчерпан! {cat}: {pct:.1f}% от бюджета.",
                    'uz': "⚠️ Limit oshib ketdi! {cat}: {pct:.1f}% ishlatildi."
                },
                'alert': {
                    'en': "⚠️ Limit alert: {cat} is at {pct:.1f}% ({th}% threshold).",
                    'ru': "⚠️ Внимание: {cat} — {pct:.1f}% (порог {th}%).",
                    'uz': "⚠️ Diqqat: {cat} — {pct:.1f}% ({th}% chegara)."
                }
            }
            
            if crossed_threshold >= 100:
                tpl = msgs['exceeded'][lang]
                warnings.append(tpl.format(cat=limit_name, pct=percent))
            else:
                tpl = msgs['alert'][lang]
                warnings.append(tpl.format(cat=limit_name, pct=percent, th=crossed_threshold))
                
    if warnings:
        return "\n".join(warnings)
    return None

