"""Tool execution handlers for AI agent function calls."""
import json
import logging
from typing import Dict, Any

from openai.types.chat import ChatCompletionMessageToolCall as ToolCall

from ..api_client import BarakaAPIClient

logger = logging.getLogger(__name__)


async def execute_tool(
    api_client: BarakaAPIClient,
    user_id: int,
    tool_call: ToolCall,
) -> Dict[str, Any]:
    """Execute an AI function call and return the result."""
    try:
        function_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        logger.info(f"Executing tool: {function_name}")

        if function_name == "create_transaction":
            return await _handle_create_transaction(api_client, user_id, args)
        elif function_name == "set_limit":
            return await _handle_set_limit(api_client, args)
        elif function_name == "create_category":
            return await _handle_create_category(api_client, args)
        elif function_name == "get_balance":
            return await _handle_get_balance(api_client, args)
        elif function_name == "create_debt":
            return await _handle_create_debt(api_client, args)
        elif function_name == "settle_debt":
            return await _handle_settle_debt(api_client, args)
        elif function_name == "get_statistics":
            return await _handle_get_statistics(api_client, args)

        elif function_name == "delete_transactions":
            transaction_ids = args.get("transaction_ids", [])
            if not transaction_ids:
                return {"success": False, "error": "No transaction IDs provided"}
            
            try:
                await api_client.bulk_delete_transactions(transaction_ids)
                return {
                    "success": True, 
                    "message": f"Successfully deleted {len(transaction_ids)} transactions.",
                    "deleted_count": len(transaction_ids)
                }
            except Exception as e:
                return {"success": False, "error": str(e)}

        else:
            return {"error": f"Unknown tool: {function_name}"}

    except Exception as e:
        logger.exception(f"Tool execution error: {e}")
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Individual tool handlers
# ---------------------------------------------------------------------------

async def _handle_create_transaction(
    api_client: BarakaAPIClient,
    user_id: int,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle create_transaction tool call."""
    transaction_type = args.get("type", "expense")
    amount = float(args.get("amount", 0))
    description = args.get("description", "")
    currency = args.get("currency", "uzs").lower()
    category_slug = args.get("category_slug") or args.get("category")

    # Multi-currency conversion for Pro/Premium users
    original_amount = amount
    original_currency = currency
    converted = False

    if currency != "uzs":
        from ..user_storage import storage

        try:
            sub_status = await api_client.get_subscription_status(user_id)
            sub_tier = sub_status.get("subscription_type", "free")

            # free_trial counts as premium, plus/pro/premium can convert
            if sub_tier in ("plus", "pro", "premium", "free_trial"):
                import httpx

                try:
                    CBU_API_URL = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(CBU_API_URL)
                        response.raise_for_status()
                        rates_data = response.json()

                        # Find the rate
                        rate_info = None
                        for r in rates_data:
                            if r.get("Ccy", "").upper() == currency.upper():
                                rate_info = r
                                break

                        if rate_info:
                            rate = float(rate_info.get("Rate", 0))
                            nominal = int(rate_info.get("Nominal", 1))
                            amount = amount * (rate / nominal)
                            currency = "uzs"
                            converted = True
                            logger.info(
                                f"Converted {original_amount} {original_currency.upper()} "
                                f"→ {amount:.0f} UZS"
                            )
                except Exception as e:
                    logger.error(f"Currency conversion failed: {e}")
            else:
                # Free user trying multi-currency — return premium_required flag
                logger.info(
                    f"Free user {user_id} tried to use {currency.upper()}, showing upsell"
                )
                return {
                    "success": False,
                    "premium_required": True,
                    "feature": "multi_currency",
                    "original_amount": original_amount,
                    "original_currency": original_currency.upper(),
                }
        except Exception as e:
            logger.error(f"Could not check subscription for currency conversion: {e}")

    # Prepare transaction data
    tx_data: Dict[str, Any] = {
        "type": transaction_type,
        "amount": amount,
        "description": description,
        "currency": currency,
    }

    # Resolve category_id from slug
    resolved_category_slug = _resolve_category(
        await api_client.get_categories(),
        category_slug,
        transaction_type,
        tx_data,
    )

    logger.info(f"Creating transaction: {tx_data}")
    result = await api_client.create_transaction(tx_data)

    # Check for limit warning from API
    limit_warning = result.get("limit_warning")

    return {
        "success": True,
        "transaction_id": result["id"],
        "amount": amount,
        "currency": currency,
        "original_amount": original_amount if converted else None,
        "original_currency": original_currency.upper() if converted else None,
        "converted": converted,
        "type": transaction_type,
        "description": description,
        "category": resolved_category_slug or category_slug or "other_expense",
        "warning": limit_warning,
    }


async def _handle_set_limit(
    api_client: BarakaAPIClient,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle set_limit tool call."""
    category_slug = args.get("category_slug")
    amount = float(args.get("amount", 0))
    period = args.get("period", "month")

    logger.info(f"Setting limit: {category_slug} {amount}")
    try:
        result = await api_client.set_limit(category_slug, amount, period)
        logger.info(f"Set limit success: {result}")
        return {
            "success": True,
            "limit_id": result["id"],
            "category": category_slug,
            "amount": amount,
            "remaining": result["remaining"],
        }
    except Exception as e:
        logger.error(f"Set limit failed: {e}")
        return {"success": False, "error": str(e)}


async def _handle_create_category(
    api_client: BarakaAPIClient,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle create_category tool call."""
    name = args.get("name")
    slug = args.get("slug")
    type_ = args.get("type", "expense")
    icon = args.get("icon", "🏷")

    logger.info(f"Creating category: {name} ({type_}) slug={slug}")
    try:
        result = await api_client.create_category(name, type_, icon, slug=slug)
        return {"success": True, "category_id": result["id"], "name": name, "created": True}
    except Exception as e:
        # If 400 Bad Request, likely category already exists.
        if "400" in str(e):
            logger.warning(f"Category creation failed (likely exists): {e}")
            return {
                "success": True,
                "name": name,
                "created": False,
                "note": "Category already exists",
            }
        raise


async def _handle_get_balance(
    api_client: BarakaAPIClient,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle get_balance tool call."""
    period = args.get("period", "month")
    return await api_client.get_balance(period)


async def _handle_create_debt(
    api_client: BarakaAPIClient,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle create_debt tool call."""
    debt_data = {
        "type": args.get("type"),
        "person_name": args.get("person_name"),
        "amount": float(args.get("amount", 0)),
        "currency": args.get("currency", "uzs"),
        "description": args.get("description"),
        "due_date": args.get("due_date"),
    }
    logger.info(f"Creating debt: {debt_data}")
    result = await api_client.create_debt(debt_data)
    return {
        "success": True,
        "debt_id": result["id"],
        "person": debt_data["person_name"],
        "amount": debt_data["amount"],
        "type": debt_data["type"],
    }


async def _handle_settle_debt(
    api_client: BarakaAPIClient,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle settle_debt tool call."""
    person_name = args.get("person_name", "").lower()
    amount_filter = float(args.get("amount", 0)) if args.get("amount") else None

    # Fetch all open debts
    debts = await api_client.get_debts(status="open")

    # Filter by name (fuzzy match)
    matched_debts = [d for d in debts if person_name in d.get("person_name", "").lower()]

    if not matched_debts:
        return {"success": False, "error": f"Debt for '{person_name}' not found."}

    target_debt = None

    # If exact amount specified
    if amount_filter:
        amount_matches = [
            d for d in matched_debts if float(d.get("amount", 0)) == amount_filter
        ]
        if amount_matches:
            target_debt = amount_matches[0]

    # If only one match by name
    if not target_debt and len(matched_debts) == 1:
        target_debt = matched_debts[0]

    if target_debt:
        result = await api_client.mark_debt_as_paid(target_debt["id"])
        return {
            "success": True,
            "settled_debt_id": result["id"],
            "person": result["person_name"],
            "amount": result["amount"],
            "currency": result["currency"],
            "type": result["type"],
        }
    else:
        return {
            "success": False,
            "error": "Found multiple debts. Please specify amount.",
            "candidates": [f"{d['person_name']} - {d['amount']}" for d in matched_debts],
        }


async def _handle_get_statistics(
    api_client: BarakaAPIClient,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    """Handle get_statistics tool call."""
    period = args.get("period", "month")
    return await api_client.get_category_breakdown(period)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_category(
    categories: list,
    category_slug: str | None,
    transaction_type: str,
    tx_data: Dict[str, Any],
) -> str | None:
    """Resolve category slug to ID and mutate tx_data with category_id.
    
    Returns the resolved slug or None.
    """
    if not category_slug:
        return None

    resolved_slug = None
    try:
        category_id = None
        target_slug = category_slug.lower().strip()

        # 1. Try exact slug match
        for cat in categories:
            if cat.get("slug") == target_slug:
                category_id = cat.get("id")
                resolved_slug = cat.get("slug")
                break

        # 2. Try name match (case-insensitive)
        if not category_id:
            for cat in categories:
                if cat.get("name", "").lower() == target_slug:
                    category_id = cat.get("id")
                    resolved_slug = cat.get("slug")
                    break

        # 3. Fallback to 'other_expense' / 'other_income'
        if not category_id:
            fallback_slug = f"other_{transaction_type}"
            for cat in categories:
                if cat.get("slug") == fallback_slug:
                    category_id = cat.get("id")
                    resolved_slug = cat.get("slug")
                    break

        # 4. Last resort: 'other' (legacy)
        if not category_id:
            for cat in categories:
                if cat.get("slug") == "other":
                    category_id = cat.get("id")
                    resolved_slug = cat.get("slug")
                    break

        if category_id:
            tx_data["category_id"] = category_id
        else:
            logger.warning(f"Category not found for slug: {category_slug}")

    except Exception as e:
        logger.error(f"Error resolving category: {e}")

    return resolved_slug
