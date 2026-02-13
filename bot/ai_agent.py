"""AI Agent with OpenAI integration and tool support."""
import json
import logging
import datetime
from typing import Dict, Any, List
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageToolCall as ToolCall

from .config import config
from .api_client import BarakaAPIClient
from .dialog_context import dialog_context
from .categories_data import DEFAULT_CATEGORIES  # <--- Imported category data

logger = logging.getLogger(__name__)


class AIAgent:
    """AI Agent using OpenAI Function Calling for transaction management."""
    
    def __init__(self, api_client: BarakaAPIClient):
        self.api_client = api_client
        self.client = AsyncOpenAI(
            api_key=config.OPENAI_API_KEY,
            timeout=120.0  # Increased timeout to 120s
        )
        self.model = "gpt-5.1"  
        
        self.tools = [
            # ... tools (unchanged) ...
            {
                "type": "function",
                "function": {
                    "name": "create_transaction",
                    "description": "Create a new transaction (expense or income)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number", "description": "Transaction amount"},
                            "currency": {"type": "string", "enum": ["uzs", "usd", "eur", "rub", "gbp", "cny", "kzt", "aed", "try"], "description": "Currency code (uzs, usd, eur, rub, etc.)"},
                            "category_slug": {"type": "string", "description": "Category slug (must be from available list)"},
                            "description": {"type": "string", "description": "Description of the transaction"},
                            "date": {"type": "string", "description": "Date in YYYY-MM-DD format (optional)"},
                            "type": {"type": "string", "enum": ["income", "expense"], "description": "Transaction type"}
                        },
                        "required": ["amount", "currency", "category_slug", "type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_balance",
                    "description": "Get current balance and limits status",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_statistics",
                    "description": "Get expense statistics for a period",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "period": {
                                "type": "string",
                                "enum": ["today", "week", "month", "year"],
                                "description": "Time period for statistics"
                            }
                        },
                        "required": ["period"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_category",
                    "description": "Create a new category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Category name (in user's language)"},
                            "slug": {"type": "string", "description": "English unique slug (e.g. 'server_costs' for 'Серверы')"},
                            "type": {"type": "string", "enum": ["income", "expense"], "description": "Category type"},
                            "icon": {"type": "string", "description": "Emoji icon for the category"},
                            "color": {"type": "string", "description": "Color in HEX format (e.g. #FF0000)"}
                        },
                        "required": ["name", "type", "icon"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_debt",
                    "description": "Record a new debt (someone owes me or I owe someone)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "person_name": {"type": "string", "description": "Name of the person"},
                            "amount": {"type": "number", "description": "Debt amount"},
                            "currency": {"type": "string", "enum": ["uzs", "usd"], "description": "Currency code"},
                            "type": {"type": "string", "enum": ["i_owe", "owe_me"], "description": "Debt type: 'i_owe' if I borrowed, 'owe_me' if I lent"},
                            "description": {"type": "string", "description": "Description (optional)"},
                            "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format (optional)"}
                        },
                        "required": ["person_name", "amount", "currency", "type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "settle_debt",
                    "description": "Mark a debt as paid/settled",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "person_name": {"type": "string", "description": "Name of the person to settle debt with"},
                            "amount": {"type": "number", "description": "Amount to pay (optional, if not specified tries to settle full debt)"}
                        },
                        "required": ["person_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_limit",
                    "description": "Set a monthly budget limit for a category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category_slug": {"type": "string", "description": "Category slug"},
                            "amount": {"type": "number", "description": "Limit amount"},
                            "period": {"type": "string", "enum": ["month"], "description": "Period (default: month)"}
                        },
                        "required": ["category_slug", "amount"]
                    }
                }
            }
        ]


    
    async def process_message(self, user_id: int, message: str) -> dict:
        """Process user message with AI agent.
        
        Returns dict with:
        - response: str - AI response text
        - parsed_transactions: List[Dict] - transactions awaiting confirmation
        """
        from .user_storage import storage
        from .i18n import t
        lang = storage.get_user_language(user_id) or 'uz'
        
        try:
            # Track parsed transactions
            parsed_transactions = []
            
            # Add user message to context
            dialog_context.add_message(user_id, "user", message)
            
            # Initialize created_transactions list
            created_transactions = []
            
            # Get fresh categories from API to update system prompt
            try:
                categories = await self.api_client.get_categories()
                expense_slugs = [c['slug'] for c in categories if c.get('type') == 'expense']
                income_slugs = [c['slug'] for c in categories if c.get('type') == 'income']
            except Exception as e:
                logger.error(f"Failed to fetch categories for prompt: {e}")
                # Fallback to defaults
                from .categories_data import DEFAULT_CATEGORIES
                expense_slugs = [c['slug'] for c in DEFAULT_CATEGORIES if c['type'] == 'expense']
                income_slugs = [c['slug'] for c in DEFAULT_CATEGORIES if c['type'] == 'income']

            # Helper to format slugs
            def format_slugs(slugs):
                lines = []
                for i in range(0, len(slugs), 10):
                    lines.append(", ".join(slugs[i:i+10]))
                return "\n".join(lines)

            # Dynamic system prompt with FRESH categories
            dynamic_prompt = f"""You are Midas - an intelligent, friendly, and CONCISE financial assistant.
            
CAPABILITIES:
1. Register transactions
2. Show balance/limits
3. Show statistics
4. Create new categories
5. Manage debts
6. Set budgets/limits (e.g. "Limit food 200k")

CURRENT DATE: {datetime.datetime.now().strftime('%Y-%m-%d')}

AVAILABLE CATEGORIES (use slug):
EXPENSES: 
{format_slugs(expense_slugs)}

INCOME: 
{format_slugs(income_slugs)}

CATEGORY MAPPING RULES:
- "food" / "ovqat" / "еда" -> groceries (if cooking ingredients) OR cafes
- "taxi" -> taxi
- "click" / "payme" -> utilities
- "netflix" / "spotify" -> subscriptions
- "zara" / "nike" -> clothing or shoes
- "shop" / "bozor" -> groceries or home_other
- "metro" / "bus" -> public_transport
- "pharmacy" / "apteka" -> medicine
- "course" / "o'qish" -> courses

RULES:
1. **BE EXTREMELY CONCISE.**
   - Do NOT explain your thought process.
   - Do NOT say "I will now add a transaction...". Just CALL THE TOOL.
   - Do NOT mention technical terms like "slug", "json", or "tool".
   - After the tool executes, confirm briefly: "✅ Saved" or "Done".

2. **Actions first, talk later.**
   - If user input is a transaction (e.g., "Taxi 50k"), call `create_transaction` IMMEDIATELY.
   - Do not ask purely polite questions if the intent is clear.

3. **Debts:**
   - "I lent 50k to Ali" -> `create_debt(type="owe_me")`
   - "I borrowed 100k from John" -> `create_debt(type="i_owe")`
   - "Ali returned" -> `settle_debt`

4. **Limits:**
   - "Set limit for Food 300k" -> `set_limit(category_slug="groceries", amount=300000)`
   - "Limit 50$" (if context implies category) -> `set_limit`
   - If user asks to update limit, just call `set_limit` again (it overwrites).

5. **Voice/Typos:**
   - Aggressively guess intent from voice text.
   - "Food 50000" -> Category: groceries/cafes.

6. **CURRENCY RECOGNITION (CRITICAL):**
   - "dollar" / "долларов" / "dollarga" / "$" -> currency: "usd"
   - "рубль" / "рублей" / "rubl" / "₽" -> currency: "rub"
   - "евро" / "euro" / "€" -> currency: "eur"
   - "тенге" / "tenge" -> currency: "kzt"
   - "сум" / "so'm" / "sum" -> currency: "uzs"
   - Default to "uzs" ONLY if no currency mentioned.
   - IMPORTANT: Listen for currency keywords in ANY language (russian, uzbek, english).

7. **Language:**
   - Reply in the USER'S language (detected from input or context).

EXAMPLES:
User: "Lunch 50k"
Action: create_transaction(amount=50000, type="expense", category_slug="cafes", description="Lunch")

User: "50k"
Response: "What for? 📝" (Translated)

User: "Add income Salary 500$"
Action: create_transaction(amount=500, type="income", category_slug="salary", currency="usd")

User: "Dalerga 500k qarz berdim"
Action: create_debt(type="owe_me", person_name="Daler", amount=500000)

User: "Correction balance 745653"
Action: get_balance() -> calculate diff -> create_transaction(category="other_expense"/"other_income")
"""
            
            # Get conversation history
            history = dialog_context.get_openai_messages(user_id)
            
            # Add system prompt
            messages = [{"role": "system", "content": dynamic_prompt}] + history
            
            # Call OpenAI with function calling
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            assistant_message = response.choices[0].message
            
            # Check for empty response
            if not assistant_message.content and not assistant_message.tool_calls:
                logger.error("AI returned empty response")
                fallback_response = {
                    'uz': "Tushundim! Yozdim.",
                    'ru': "Понял! Записал.",
                    'en': "Got it! Recorded."
                }.get(lang, "Понял! Записал.")
                return {
                    "response": fallback_response,
                    "parsed_transactions": []
                }
            
            tool_calls = assistant_message.tool_calls
            
            # If AI wants to call tools
            if tool_calls:
                # Execute all tool calls
                tool_results = []
                created_transactions = [] # Initialize list to collect created transactions
                created_debts = [] # Initialize list to collect created debts
                settled_debts = [] # Initialize list to collect settled debts
                premium_upsells = [] # Track premium feature upsells
                
                for tool_call in tool_calls:
                    try:
                        logger.info(f"AI calling tool: {tool_call.function.name} with args: {tool_call.function.arguments}")
                        tool_result = await self._execute_tool(user_id, tool_call)
                        
                        # Format output for context
                        output_str = json.dumps(tool_result, ensure_ascii=False)
                        
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "output": output_str
                        })
                        
                        # Collect successfully created transactions, debts or categories
                        if tool_result.get("success"):
                            if "transaction_id" in tool_result:
                                created_transactions.append(tool_result)
                            elif "debt_id" in tool_result:
                                created_debts.append(tool_result)
                            elif "settled_debt_id" in tool_result:
                                settled_debts.append(tool_result)
                        elif tool_result.get("premium_required"):
                            # Track premium upsell triggers
                            premium_upsells.append(tool_result)

                            
                    except Exception as e:
                        logger.exception(f"Error executing tool {tool_call.function.name}: {e}")
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"error": str(e)}, ensure_ascii=False)
                        })
                
                # Add assistant message with tool calls to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "", # Content can be null if only tool calls
                    "tool_calls": assistant_message.tool_calls
                })
                
                # Add tool results
                for tool_result in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_result["tool_call_id"],
                        "content": tool_result["output"]
                    })
                
                # Get final response from AI
                final_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                
                final_text = final_response.choices[0].message.content
            else:
                # No tools called, just conversation
                final_text = assistant_message.content
                created_debts = []
                settled_debts = []
            
            # Save assistant response to context
            dialog_context.add_message(user_id, "assistant", final_text or "")
            
            fallback_done = {
                'uz': "Tayyor!",
                'ru': "Готово!",
                'en': "Done!"
            }.get(lang, "Готово!")
            
            return {
                "response": final_text or fallback_done,
                "created_transactions": created_transactions,
                "created_debts": created_debts,
                "settled_debts": settled_debts,
                "premium_upsells": premium_upsells if 'premium_upsells' in dir() else []
            }
            
        except Exception as e:
            logger.exception(f"AI agent error: {e}")
            error_msg = t('common.common.error', lang)
            return {
                "response": f"❌ {error_msg}",
                "created_transactions": []
            }
    
    async def _execute_tool(self, user_id: int, tool_call: ToolCall) -> Dict[str, Any]:
        """Execute AI function call."""
        try:
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            logger.info(f"Executing tool: {function_name}")
            
            if function_name == "create_transaction":
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
                    # Check subscription tier
                    from .user_storage import storage
                    try:
                        sub_status = await self.api_client.get_subscription_status(user_id)
                        sub_tier = sub_status.get("subscription_type", "free")
                        
                        # free_trial counts as premium, plus/pro/premium can convert
                        if sub_tier in ("plus", "pro", "premium", "free_trial"):
                            # Import conversion function
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
                                        # Convert: amount * (rate / nominal)
                                        amount = amount * (rate / nominal)
                                        currency = "uzs"
                                        converted = True
                                        logger.info(f"Converted {original_amount} {original_currency.upper()} → {amount:.0f} UZS")
                            except Exception as e:
                                logger.error(f"Currency conversion failed: {e}")
                        else:
                            # Free user trying multi-currency - return premium_required flag
                            logger.info(f"Free user {user_id} tried to use {currency.upper()}, showing upsell")
                            return {
                                "success": False,
                                "premium_required": True,
                                "feature": "multi_currency",
                                "original_amount": original_amount,
                                "original_currency": original_currency.upper()
                            }
                    except Exception as e:
                        logger.error(f"Could not check subscription for currency conversion: {e}")

                
                # Prepare transaction data
                tx_data = {
                    "type": transaction_type,
                    "amount": amount,
                    "description": description,
                    "currency": currency,
                }
                
                # Resolve category_id from slug
                resolved_category_slug = None
                if category_slug:
                    try:
                        categories = await self.api_client.get_categories()
                        category_id = None
                        
                        # Normalize slug
                        target_slug = category_slug.lower().strip()
                        
                        # 1. Try exact slug match
                        for cat in categories:
                            if cat.get("slug") == target_slug:
                                category_id = cat.get("id")
                                resolved_category_slug = cat.get("slug")  # ← Return slug, not name!
                                break
                        
                        # 2. Try name match (case-insensitive)
                        if not category_id:
                            for cat in categories:
                                if cat.get("name", "").lower() == target_slug:
                                    category_id = cat.get("id")
                                    resolved_category_slug = cat.get("slug")  # ← Return slug!
                                    break
                                    
                        # 3. Fallback to 'other_expense' / 'other_income' if not found
                        if not category_id:
                            fallback_slug = f"other_{transaction_type}"
                            for cat in categories:
                                if cat.get("slug") == fallback_slug:
                                    category_id = cat.get("id")
                                    resolved_category_slug = cat.get("slug")
                                    break
                        
                        # 4. Last resort: 'other' (legacy)
                        if not category_id:
                             for cat in categories:
                                if cat.get("slug") == "other":
                                    category_id = cat.get("id")
                                    resolved_category_slug = cat.get("slug")
                                    break

                        if category_id:
                            tx_data["category_id"] = category_id
                        else:
                            logger.warning(f"Category not found for slug: {category_slug}")
                            
                    except Exception as e:
                        logger.error(f"Error resolving category: {e}")
                
                logger.info(f"Creating transaction: {tx_data}")
                result = await self.api_client.create_transaction(tx_data)
                
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
                    "category": resolved_category_slug or category_slug or "other_expense",  # ← slug for i18n!
                    "warning": limit_warning  # Pass warning to AI to display
                }


            elif function_name == "set_limit":
                category_slug = args.get("category_slug")
                amount = float(args.get("amount", 0))
                period = args.get("period", "month")
                
                logger.info(f"Setting limit: {category_slug} {amount}")
                try:
                    result = await self.api_client.set_limit(category_slug, amount, period)
                    logger.info(f"Set limit success: {result}")
                    return {
                        "success": True, 
                        "limit_id": result["id"], 
                        "category": category_slug, 
                        "amount": amount,
                        "remaining": result["remaining"]
                    }
                except Exception as e:
                    logger.error(f"Set limit failed: {e}")
                    return {"success": False, "error": str(e)}

            elif function_name == "create_category":
                name = args.get("name")
                slug = args.get("slug")  # AI generated English slug
                type_ = args.get("type", "expense")
                icon = args.get("icon", "🏷")
                
                logger.info(f"Creating category: {name} ({type_}) slug={slug}")
                try:
                    # Pass the explicit slug if available
                    result = await self.api_client.create_category(name, type_, icon, slug=slug)
                    return {"success": True, "category_id": result["id"], "name": name, "created": True}
                except Exception as e:
                    # If 400 Bad Request, likely category already exists.
                    # We return success so AI continues flow.
                    if "400" in str(e):
                        logger.warning(f"Category creation failed (likely exists): {e}")
                        return {"success": True, "name": name, "created": False, "note": "Category already exists"}
                    raise e
            
            elif function_name == "get_balance":
                period = args.get("period", "month")
                result = await self.api_client.get_balance(period)
                return result
                
            elif function_name == "create_debt":
                debt_data = {
                    "type": args.get("type"),
                    "person_name": args.get("person_name"),
                    "amount": float(args.get("amount", 0)),
                    "currency": args.get("currency", "uzs"),
                    "description": args.get("description"),
                    "due_date": args.get("due_date")  # Format YYYY-MM-DD or None
                }
                logger.info(f"Creating debt: {debt_data}")
                result = await self.api_client.create_debt(debt_data)
                return {
                    "success": True, 
                    "debt_id": result["id"], 
                    "person": debt_data["person_name"], 
                    "amount": debt_data["amount"],
                    "type": debt_data["type"]
                }
                
            elif function_name == "settle_debt":
                person_name = args.get("person_name", "").lower()
                amount_filter = float(args.get("amount", 0)) if args.get("amount") else None
                
                # Fetch all open debts
                debts = await self.api_client.get_debts(status="open")
                
                # Filter by name (fuzzy match)
                matched_debts = [d for d in debts if person_name in d.get("person_name", "").lower()]
                
                if not matched_debts:
                     return {"success": False, "error": f"Debt for '{person_name}' not found."}
                
                target_debt = None
                
                # If exact amount specified
                if amount_filter:
                    amount_matches = [d for d in matched_debts if float(d.get("amount", 0)) == amount_filter]
                    if amount_matches:
                        target_debt = amount_matches[0] # Take first valid
                
                # If only one match by name
                if not target_debt and len(matched_debts) == 1:
                    target_debt = matched_debts[0]
                    
                if target_debt:
                    result = await self.api_client.mark_debt_as_paid(target_debt["id"])
                    return {
                        "success": True, 
                        "settled_debt_id": result["id"],
                        "person": result["person_name"],
                        "amount": result["amount"],
                        "currency": result["currency"],
                        "type": result["type"]
                    }
                else:
                    return {
                        "success": False, 
                        "error": "Found multiple debts. Please specify amount.",
                        "candidates": [f"{d['person_name']} - {d['amount']}" for d in matched_debts]
                    }

            elif function_name == "get_statistics":
                period = args.get("period", "month")
                result = await self.api_client.get_category_breakdown(period)
                return result

            return {"success": False, "error": "Unknown function"}
                    
        except Exception as e:
            logger.exception(f"Tool execution error: {e}")
            return {"error": str(e)}

    async def edit_transaction(self, old_data: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Smartly edit transaction based on user input."""
        try:
            # Get available category slugs to guide AI
            categories = await self.api_client.get_categories()
            
            # Filter by type if possible, or just provide all
            tx_type = old_data.get('type', 'expense')
            valid_slugs = [c['slug'] for c in categories if c.get('type') == tx_type]
            
            # Formatted list
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

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result_json = response.choices[0].message.content
            updates = json.loads(result_json)
            
            # Resolve category slug to ID if changed
            if "category_slug" in updates:
                category_slug = updates["category_slug"]
                try:
                    category_id = None
                    target_slug = category_slug.lower().strip()
                    
                    # 1. Try exact slug match
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
                        logger.warning(f"Could not resolve slug '{target_slug}' in {len(categories)} categories. Available slugs snippet: {[c['slug'] for c in categories[:5]]}...")
                        fallback_slug = f"other_{old_data.get('type', 'expense')}"
                        for cat in categories:
                            if cat.get("slug") == fallback_slug:
                                category_id = cat.get("id")
                                logger.info(f"Falling back to '{fallback_slug}' id {category_id}")
                                break
                    
                    if category_id:
                        updates["category_id"] = category_id
                        # Remove slug so we don't send it to API which might not expect it
                        if "category_slug" in updates:
                            del updates["category_slug"]
                    else:
                        logger.warning(f"Could not resolve category id for slug: {category_slug} (even fallback failed)")
                        
                except Exception as e:
                    logger.error(f"Error resolving category in edit: {e}")

            return updates
        except Exception as e:
            logger.error(f"AI edit transaction error: {e}")
            # Fallback to description update
            return {"description": user_input}

    async def edit_debt(self, old_data: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Smartly edit debt based on user input."""
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

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result_json = response.choices[0].message.content
            updates = json.loads(result_json)
            return updates
        except Exception as e:
            logger.error(f"AI edit debt error: {e}")
            return {"description": user_input}
