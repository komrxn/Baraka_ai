"""AI-powered editors for transactions and debts."""
import json
import logging
from typing import Dict, Any

from openai import AsyncOpenAI

from ..api_client import BarakaAPIClient

logger = logging.getLogger(__name__)


async def edit_transaction(
    client: AsyncOpenAI,
    api_client: BarakaAPIClient,
    model: str,
    old_data: Dict[str, Any],
    user_input: str,
) -> Dict[str, Any]:
    """Smartly edit transaction based on user input.

    Uses AI to determine which fields to update, resolves category slugs
    to IDs, and returns the update dict.
    """
    try:
        # Get available category slugs to guide AI
        categories = await api_client.get_categories()

        tx_type = old_data.get("type", "expense")
        valid_slugs = [c["slug"] for c in categories if c.get("type") == tx_type]
        slugs_str = ", ".join(valid_slugs)

        prompt = f"""You are smart transaction editor.
            
CURRENT TRANSACTION JSON:
{json.dumps(old_data, ensure_ascii=False)}

VALID CATEGORY SLUGS for '{tx_type}':
{slugs_str}

CATEGORY MAPPING RULES (IMPORTANT):
- "food" / "ovqat" / "еда" / "продукты" -> groceries (if cooking ingredients) OR cafes
- "yandex" / "taxi" -> taxi
- "click" / "payme" -> utilities (often)
- "netflix" / "spotify" / "apple" -> subscriptions
- "zara" / "nike" -> clothing or shoes
- "shop" / "bozor" -> groceries or home_other
- "u cell" / "beeline" -> internet or communication
- "benzin" / "zapravka" -> fuel
- "metro" / "bus" -> public_transport
- "apteka" / "dori" -> medicine
- "kurs" / "o'qish" -> courses or education

USER INPUT: "{user_input}"

TASK:
Update fields based on user input.
- If user attempts to change amount (e.g. "40k", "50000"), update 'amount'.
- If user attempts to change category/description (e.g. "taxi", "lunch", "на еду"), update 'description' AND 'category_slug'.
- IMPORTANT: 'category_slug' MUST be one of the VALID CATEGORY SLUGS provided above. Pick the closest match.
- If user says something unrelated, try to interpret it as description update.
- Return ONLY valid JSON with updated fields.

EXAMPLE 1:
Old: {{ "amount": 30000, "description": "Taxi" }}
Input: "40k"
Output: {{ "amount": 40000 }}

EXAMPLE 2:
Old: {{ "amount": 30000, "description": "Taxi" }}
Input: "Metro"
Output: {{ "description": "Metro", "category_slug": "public_transport" }}

EXAMPLE 3:
Old: {{ "amount": 30000, "description": "Taxi" }}
Input: "На еду 50к"
Output: {{ "amount": 50000, "description": "На еду", "category_slug": "groceries" }}

Return JSON:"""

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        result_json = response.choices[0].message.content
        updates = json.loads(result_json)

        # Resolve category slug to ID if changed
        if "category_slug" in updates:
            _resolve_edit_category(updates, categories, old_data)

        return updates
    except Exception as e:
        logger.error(f"AI edit transaction error: {e}")
        return {"description": user_input}


async def edit_debt(
    client: AsyncOpenAI,
    model: str,
    old_data: Dict[str, Any],
    user_input: str,
) -> Dict[str, Any]:
    """Smartly edit debt based on user input.

    Uses AI to determine which fields to update and returns the update dict.
    """
    try:
        prompt = f"""You are smart debt editor.

CURRENT DEBT JSON:
{json.dumps(old_data, ensure_ascii=False)}

USER INPUT: "{user_input}"

TASK:
Update fields: amount, person_name, description, type (owe_me/i_owe).
- CRITICAL: Detect semantics of WHO OWES WHOM.
  - "I owe..." / "Я должен..." / "Men qarzdorman..." -> type: "i_owe"
  - "Owes me..." / "Мне должны..." / "Menga qarz..." -> type: "owe_me"
- If the phrase implies a complete change of context (e.g. "Actually I owe Kama"), update 'type' and 'person_name' accordingly.
- Detect amount changes (K/k/ming/mln support).
- Detect person name changes.

EXAMPLE 1:
Old: {{ "amount": 100000, "person_name": "Ali", "type": "owe_me" }}
Input: "200k"
Output: {{ "amount": 200000 }}

EXAMPLE 2 (Complete context switch):
Old: {{ "amount": 100000, "person_name": "Ali", "type": "owe_me" }}
Input: "Я должна Каме 150к"
Output: {{ "amount": 150000, "type": "i_owe", "person_name": "Кама", "description": "Я должна Каме" }}

EXAMPLE 3 (Just type switch):
Old: {{ "amount": 50000, "person_name": "Vali", "type": "owe_me" }}
Input: "Не, это я ему должен"
Output: {{ "type": "i_owe" }}

Return JSON:"""

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        result_json = response.choices[0].message.content
        updates = json.loads(result_json)
        return updates
    except Exception as e:
        logger.error(f"AI edit debt error: {e}")
        return {"description": user_input}


def _resolve_edit_category(
    updates: Dict[str, Any],
    categories: list,
    old_data: Dict[str, Any],
) -> None:
    """Resolve category_slug in updates dict to category_id (in-place)."""
    category_slug = updates["category_slug"]
    try:
        category_id = None
        target_slug = category_slug.lower().strip()

        # 1. Try exact slug match
        for cat in categories:
            if cat.get("slug") == target_slug:
                category_id = cat.get("id")
                logger.info(f"Resolved slug '{target_slug}' to id {category_id} (exact match)")
                break

        # 2. Try name match
        if not category_id:
            for cat in categories:
                if cat.get("name", "").lower() == target_slug:
                    category_id = cat.get("id")
                    logger.info(f"Resolved slug '{target_slug}' to id {category_id} (name match)")
                    break

        # 3. Fallback
        if not category_id:
            logger.warning(
                f"Could not resolve slug '{target_slug}' in {len(categories)} categories. "
                f"Available slugs snippet: {[c['slug'] for c in categories[:5]]}..."
            )
            fallback_slug = f"other_{old_data.get('type', 'expense')}"
            for cat in categories:
                if cat.get("slug") == fallback_slug:
                    category_id = cat.get("id")
                    logger.info(f"Falling back to '{fallback_slug}' id {category_id}")
                    break

        if category_id:
            updates["category_id"] = category_id
            del updates["category_slug"]
        else:
            logger.warning(
                f"Could not resolve category id for slug: {category_slug} (even fallback failed)"
            )

    except Exception as e:
        logger.error(f"Error resolving category in edit: {e}")
