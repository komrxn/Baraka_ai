from enum import Enum
from dataclasses import dataclass

class SubscriptionTier(str, Enum):
    PLUS = "plus"
    PRO = "pro"
    PREMIUM = "premium"

@dataclass(frozen=True)
class Plan:
    id: str
    tier: SubscriptionTier
    months: int
    price_uzs: int
    name_ru: str
    name_uz: str

class PricingService:
    # Centralized Pricing Configuration
    # Prices in UZS
    PLANS = {
        "plus_1": Plan("plus_1", SubscriptionTier.PLUS, 1, 34999, "Plus (1 мес)", "Plus (1 oy)"),
        "plus_3": Plan("plus_3", SubscriptionTier.PLUS, 3, 94999, "Plus (3 мес)", "Plus (3 oy)"),
        
        "pro_1": Plan("pro_1", SubscriptionTier.PRO, 1, 49999, "Pro (1 мес)", "Pro (1 oy)"),
        "pro_3": Plan("pro_3", SubscriptionTier.PRO, 3, 119999, "Pro (3 мес)", "Pro (3 oy)"),
        
        "premium_1": Plan("premium_1", SubscriptionTier.PREMIUM, 1, 89999, "Premium (1 мес)", "Premium (1 oy)"),
        "premium_3": Plan("premium_3", SubscriptionTier.PREMIUM, 3, 229999, "Premium (3 мес)", "Premium (3 oy)"),
    }

    @classmethod
    def get_plan(cls, plan_id: str) -> Plan:
        return cls.PLANS.get(plan_id)

    @classmethod
    def get_tier_by_amount(cls, amount_uzs: float) -> tuple[SubscriptionTier, int]:
        """
        Deduce Tier and Duration based on paid amount.
        Returns (Tier, Duration_Months).
        Includes a small epsilon for float comparison safety.
        """
        epsilon = 100.0 # 100 UZS tolerance? Or even smaller.
        
        # Sort plans by price descending to match highest tier first
        sorted_plans = sorted(cls.PLANS.values(), key=lambda p: p.price_uzs, reverse=True)
        
        for plan in sorted_plans:
            if abs(amount_uzs - plan.price_uzs) < epsilon:
                return plan.tier, plan.months
        
        # Fallback or None?
        return None, None
