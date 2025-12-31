
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from ..models.limit import Limit
from ..models.transaction import Transaction
from ..models.category import Category

async def check_limit_thresholds(
    db: AsyncSession,
    user_id: UUID,
    category_id: UUID,
    amount_added: Decimal,
    transaction_date: date
) -> Optional[str]:
    """
    Check if adding 'amount_added' to 'category_id' expenses crosses any limit thresholds.
    Returns a warning message if crossed, else None.
    Thresholds: 50%, 75%, 90%, 100%.
    """
    # 1. Find active limit for this category and month
    # Assuming monthly limits aligned with calendar month for now
    start_of_month = date(transaction_date.year, transaction_date.month, 1)
    
    limit_result = await db.execute(
        select(Limit).where(
            and_(
                Limit.user_id == user_id,
                Limit.category_id == category_id,
                Limit.period_start == start_of_month
            )
        )
    )
    limit = limit_result.scalar_one_or_none()
    
    if not limit or limit.amount <= 0:
        return None
        
    spent_result = await db.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(
                Transaction.user_id == user_id,
                Transaction.category_id == category_id,
                Transaction.type == "expense",
                Transaction.transaction_date >= limit.period_start,
                Transaction.transaction_date <= limit.period_end,
            )
        )
    )
    spent_db = Decimal(str(spent_result.scalar() or 0))
    total_spent = spent_db
    
    spent_before = total_spent - amount_added
    
    percent_before = (spent_before / limit.amount) * 100
    percent_after = (total_spent / limit.amount) * 100
    
    thresholds = [50, 75, 90, 100]
    crossed_threshold = None
    
    for t in thresholds:
        if percent_before < t and percent_after >= t:
            crossed_threshold = t
            
    if not crossed_threshold:
        return None
        
    cat_result = await db.execute(select(Category.name).where(Category.id == category_id))
    category_name = cat_result.scalar() or "Category"
    
    # Localization
    lang = language if language in ['ru', 'uz', 'en'] else 'en'
    
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
        return tpl.format(cat=category_name, pct=percent_after)
    else:
        tpl = msgs['alert'][lang]
        return tpl.format(cat=category_name, pct=percent_after, th=crossed_threshold)

