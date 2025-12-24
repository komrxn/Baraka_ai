"""AI Agent with OpenAI integration and tool support."""
import json
import logging
from typing import Dict, Any, List
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageToolCall as ToolCall

from .config import config
from .api_client import MidasAPIClient
from .dialog_context import dialog_context

logger = logging.getLogger(__name__)


class AIAgent:
    """AI Agent using OpenAI Function Calling for transaction management."""
    
    def __init__(self, api_client: MidasAPIClient):
        self.api_client = api_client
        self.client = AsyncOpenAI(
            api_key=config.OPENAI_API_KEY,
            timeout=60.0  # 60 секунд таймаут
        )
        self.model = "gpt-5.1"  
        
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_transaction",
                    "description": "Создать транзакцию дохода или расхода. Вызывай эту функцию когда пользователь говорит о трате денег или получении дохода.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["income", "expense"],
                                "description": "Тип: income (доход) или expense (расход)"
                            },
                            "amount": {
                                "type": "number",
                                "description": "Сумма в числовом формате. Если написано '30к' или '30 тысяч', преобразуй в 30000"
                            },
                            "currency": {
                                "type": "string",
                                "enum": ["uzs", "usd", "eur", "rub"],
                                "default": "uzs",
                                "description": "Валюта: uzs, usd, eur, rub"
                            },
                            "description": {
                                "type": "string",
                                "description": "Краткое описание транзакции"
                            },
                            "category_slug": {
                                "type": "string",
                                "enum": ["food", "transport", "taxi", "housing", "entertainment", "health", "education", "clothing", "communication", "gifts", "sports", "beauty", "travel", "cafes", "groceries", "utilities", "other_expense", "salary", "freelance", "investments", "gift_income", "other_income"],
                                "description": "Категория: food (еда), transport (транспорт), taxi (такси - ТОЛЬКО для такси!), housing (жильё), entertainment (развлечения), health (здоровье), education (образование), clothing (одежда), communication (связь), gifts (подарки), sports (спорт), beauty (красота), travel (путешествия), cafes (кафе), groceries (продукты), utilities (коммуналка), other_expense (другое расход), salary (зарплата), freelance (фриланс), investments (инвестиции), gift_income (подарок), other_income (другое доход)"
                            }
                        },
                        "required": ["type", "amount", "description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_balance",
                    "description": "Получить текущий баланс, доходы и расходы за период",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "period": {
                                "type": "string",
                                "enum": ["day", "week", "month", "year"],
                                "default": "month",
                                "description": "Период: day, week, month, year"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_statistics",
                    "description": "Получить статистику по категориям расходов",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "period": {
                                "type": "string",
                                "enum": ["day", "week", "month", "year"],
                                "default": "month"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_category",
                    "description": "Create a new category. Only use IF user explicitly asks to create/add a category.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Category name (e.g. 'Crypto', 'Flowers')"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["expense", "income"],
                                "default": "expense"
                            },
                            "icon": {
                                "type": "string",
                                "description": "Emoji icon for category (e.g. 🪙, 💐)"
                            }
                        },
                        "required": ["name", "type"]
                    }
                }
            }
            {
                "type": "function",
                "function": {
                    "name": "create_debt",
                    "description": "Создать запись о долге. Используй когда пользователь говорит 'Я дал в долг', 'Мне должны', 'Занял у...'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["i_owe", "owe_me"],
                                "description": "Тип долга: i_owe (Я должен), owe_me (Мне должны)"
                            },
                            "person_name": {
                                "type": "string",
                                "description": "Имя человека (кому дал или у кого взял)"
                            },
                            "amount": {
                                "type": "number",
                                "description": "Сумма долга"
                            },
                            "currency": {
                                "type": "string",
                                "enum": ["uzs", "usd"],
                                "default": "uzs"
                            },
                             "description": {
                                "type": "string",
                                "description": "Описание (на что, когда вернуть и т.д.)"
                            },
                            "due_date": {
                                "type": "string",
                                "description": "Дата возврата в формате YYYY-MM-DD (если указана). Если 'завтра', 'через неделю' - преобразуй в дату."
                            }
                        },
                        "required": ["type", "person_name", "amount"]
                    }
                }
            }
        ]
        
        self.system_prompt = """You are Midas AI, a smart finance assistant.

CORE OBJECTIVE:
Record transactions and debts, and help manage finances.

AVAILABLE CATEGORIES (use slug):
EXPENSES: food, groceries, cafes, transport, taxi, housing, utilities, entertainment, health, education, clothing, communication, gifts, sports, beauty, travel, other_expense
INCOME: salary, freelance, investments, gift_income, other_income

CATEGORY MAPPING RULES (IMPORTANT):
- "shopping" / "xarid" / "покупки" → clothing (одежда, обувь)
- "market" / "bozor" / "магазин продуктов" → groceries (продукты питания)
- "restaurant" / "restoran" → cafes
- "fuel" / "benzin" / "газ" → transport
- "internet" / "phone bill" → communication
- "rent" / "ijara" / "аренда" → housing
- "gym" / "fitnes" → sports
- "medicine" / "dori" / "лекарства" → health
- "книги" / "kitoblar" / "course" → education

MAP intelligently based on context. If unsure, use 'other_expense'.

RULES:
1. **Transactions:**
   - If user says "Spent 50k on food" → CALL `create_transaction`.
   - If user says "Income 200$" → CALL `create_transaction` (type=income).

2. **Debts (NEW):**
   - If user says "I lent 50k to Ali" / "Daler qarz oldi 50k" / "Дал в долг Али 50к" → CALL `create_debt` (type="owe_me").
   - If user says "I borrowed 100$ from John" / "Men Alidan 100$ qarz oldim" / "Взял в долг у Джона 100$" → CALL `create_debt` (type="i_owe").
   - Extract `person_name` carefully.

3. **Context/Memory:**
   - REMEMBER previous messages. DO NOT lose the amount.

4. **Voice/Typos:**
   - AGGRESSIVELY GUESS intent. Fix typos.

5. **General:**
   - Be CONCISE. Detect and use USER'S language.

EXAMPLES:
User: "Lunch 50k"
Action: create_transaction(amount=50000, type="expense", category_slug="food", description="Lunch")

User: "Dalerga 500k qarz berdim" (I lent 500k to Daler)
Action: create_debt(type="owe_me", person_name="Daler", amount=500000, description="Qarz berdim")

User: "Azizdan 100$ oldim" (I borrowed 100$ from Aziz)
Action: create_debt(type="i_owe", person_name="Aziz", amount=100, currency="usd", description="Qarz oldim")
"""
    
    async def process_message(self, user_id: int, message: str) -> dict:
        """Process user message with AI agent.
        
        Returns dict with:
        - response: str - AI response text
        - parsed_transactions: List[Dict] - transactions awaiting confirmation
        """
        try:
            # Track parsed transactions
            parsed_transactions = []
            
            # Add user message to context
            dialog_context.add_message(user_id, "user", message)
            
            # Initialize created_transactions list
            created_transactions = []
            
            # Get conversation history
            history = dialog_context.get_openai_messages(user_id)
            
            # Add system prompt
            messages = [{"role": "system", "content": self.system_prompt}] + history
            
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
                return {
                    "response": "Понял! Записал.",
                    "parsed_transactions": []
                }
            
            tool_calls = assistant_message.tool_calls
            
            # If AI wants to call tools
            if tool_calls:
                # Execute all tool calls
                tool_results = []
                created_transactions = [] # Initialize list to collect created transactions
                
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
                        
                        # Collect successfully created transactions or categories
                        if tool_result.get("success"):
                            if "transaction_id" in tool_result:
                                created_transactions.append(tool_result)
                            # You can handle category success here if needed, 
                            # but usually the AI explains it in the final response.
                            
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
            
            # Save assistant response to context
            dialog_context.add_message(user_id, "assistant", final_text or "")
            
            return {
                "response": final_text or "Готово!",
                "created_transactions": created_transactions
            }
            
        except Exception as e:
            logger.exception(f"AI agent error: {e}")
            return {
                "response": "❌ Произошла ошибка. Попробуй ещё раз.",
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
                return {
                    "success": True, 
                    "transaction_id": result["id"], 
                    "amount": amount, 
                    "currency": currency,
                    "type": transaction_type,
                    "description": description,
                    "category": resolved_category_slug or category_slug or "other_expense"  # ← slug for i18n!
                }

            elif function_name == "create_category":
                name = args.get("name")
                type_ = args.get("type", "expense")
                icon = args.get("icon", "🏷")
                
                logger.info(f"Creating category: {name} ({type_})")
                result = await self.api_client.create_category(name, type_, icon)
                # Return minimal info - AI will handle user-facing message
                return {"success": True, "category_id": result["id"], "name": name, "created": True}
            
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
                
            elif function_name == "get_statistics":
                period = args.get("period", "month")
                result = await self.api_client.get_category_breakdown(period)
                return result

            return {"success": False, "error": "Unknown function"}
                    
        except Exception as e:
            logger.exception(f"Tool execution error: {e}")
            return {"error": str(e)}
