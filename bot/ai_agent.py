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
        self.model = "gpt-5-nano"  
        
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
        ]
        
        self.system_prompt = """You are Midas AI, a smart finance assistant.

CORE OBJECTIVE:
Record transactions and help manage finances.

RULES:
1. **Transactions:**
   - If user gives Amount + (Category OR Description) -> CALL `create_transaction` IMMEDIATELY.
   - If info is missing (e.g. "Spent 50k"), ASK briefly: "What for?" (in user's language).
   - If unsure about category, use best guess or 'other'.
   - "Taxi" -> category="taxi" (NOT transport).

2. **Categories:**
   - Create category ONLY if user says "Create/Add category X".
   - CALL `create_category` tool.
   - If user uses a new category in a transaction (e.g. "Lunch 50k crypto"), check if "crypto" exists. If not, ask: "Create category 'crypto'?" OR map to 'entertainment'/'other'.

3. **General:**
   - Be CONCISE. No long explanations.
   - Detect and use USER'S language.

EXAMPLES:
User: "Lunch 50k"
Action: create_transaction(amount=50000, type="expense", category_slug="food", description="Lunch")

User: "50k"
Response: "Nima uchun bu xarajat? 📝" (Uzbek) / "На что потрачено? 📝" (Russian)

User: "Create category Bitcoin 🪙"
Action: create_category(name="Bitcoin", type="expense", icon="🪙")

User: "Add income Salary 500$"
Action: create_transaction(amount=500, type="income", category_slug="salary", currency="usd")
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
                
                # Add category_id if slug provided
                if category_slug:
                    try:
                       tx_data["category_id"] = category_slug
                    except:
                        pass
                
                logger.info(f"Creating transaction: {tx_data}")
                result = await self.api_client.create_transaction(tx_data)
                return {"success": True, "transaction_id": result["id"], "amount": amount, "currency": currency}

            elif function_name == "create_category":
                name = args.get("name")
                type_ = args.get("type", "expense")
                icon = args.get("icon", "🏷")
                
                logger.info(f"Creating category: {name} ({type_})")
                result = await self.api_client.create_category(name, type_, icon)
                return {"success": True, "category_id": result["id"], "name": name}
            
            elif function_name == "get_balance":
                period = args.get("period", "month")
                result = await self.api_client.get_balance(period)
                return result
                
            elif function_name == "get_statistics":
                period = args.get("period", "month")
                result = await self.api_client.get_category_breakdown(period)
                return result

            return {"success": False, "error": "Unknown function"}
                    
        except Exception as e:
            logger.exception(f"Tool execution error: {e}")
            return {"error": str(e)}
