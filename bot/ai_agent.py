"""AI Agent with OpenAI Function Calling."""
import json
import logging
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI

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
            }
        ]
        
        self.system_prompt = """You are Midas AI, a smart finance assistant.

TASKS:
1. Help track income/expenses
2. Detect user language (Russian/Uzbek/English)
3. Respond in SAME language
4. Be CONCISE - bullet points only

TRANSACTION RULES:
- Spending → create_transaction type="expense"
- Earning → create_transaction type="income"
- Multiple in one message → call MULTIPLE times
- Convert: "30k"/"30k"/"30 ming" → 30000
- Convert: "5kk"/"5 млн"/"5 million" → 5000000
- Default currency: uzs

EXAMPLE:
User: "Spent 70k dinner, got 300k salary"
Calls:
  1. create_transaction(type="expense", amount=70000, description="dinner", category_slug="food")
  2. create_transaction(type="income", amount=300000, description="salary", category_slug="salary")
Response: "✅ Recorded:\n• Expense: Dinner -70K UZS\n• Income: Salary +300K UZS"

CATEGORIES (with RU/UZ keywords):
Expenses:
- food (ovqat, еда) - general food
- groceries (mahsulotlar, продукты) - shopping
- cafes (kafe, кафе, restoran) - cafes/restaurants
- taxi (taksi, такси, yandex, uzum) - ONLY taxi
- transport (transport, транспорт) - metro/bus (NOT taxi!)
- housing (uy, жильё) - rent
- utilities (kommunal, коммуналка, suv, elektr) - utilities
- communication (aloqa, связь, internet) - phone/internet
- clothing (kiyim, одежда) - clothes
- health (salomatlik, здоровье) - medicine/doctor
- beauty (goʻzallik, красота) - salon
- education (taʻlim, образование) - courses
- sports (sport, спорт) - gym
- entertainment (oʻyin-kulgi, развлечения) - entertainment
- travel (sayohat, путешествия) - travel
- gifts (sovgʻa, подарки) - gifts
- other_expense (boshqa, другое) - other

Income:
- salary (ish haqi, зарплата, oylik) - salary
- freelance (frilanс, фриланс) - freelance
- investments (investitsiya, инвестиции) - investments
- gift_income (sovgʻa, подарок) - gift
- other_income (boshqa daromad, другое) - other

IMPORTANT: "taksi"/"такси" → use "taxi" NOT "transport"!

Be brief. Match user's language!"""
    
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
            tool_calls = assistant_message.tool_calls
            
            # If AI wants to call tools
            if tool_calls:
                # Execute all tool calls
                tool_results = []
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"AI calling tool: {function_name} with args: {function_args}")
                    
                    # Execute the function
                    result = await self._execute_tool(function_name, function_args)
                    
                    # Collect parsed transactions
                    if result.get("pending_confirmation") and result.get("parsed_transaction"):
                        parsed_transactions.append(result["parsed_transaction"])
                    
                    tool_results.append({
                        "tool_call_id": tool_call.id,
                        "output": json.dumps(result, ensure_ascii=False)
                    })
                
                # Add assistant message with tool calls to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in tool_calls
                    ]
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
                "response": final_text or "Понял!",
                "parsed_transactions": parsed_transactions
            }
            
        except Exception as e:
            logger.exception(f"AI agent error: {e}")
            return {
                "response": "❌ Произошла ошибка. Попробуй ещё раз.",
                "parsed_transactions": []
            }
    
    async def _execute_tool(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function."""
        try:
            if function_name == "create_transaction":
                # PARSE ONLY - return data for confirmation, don't create yet
                tx_data = {
                    "type": arguments["type"],
                    "amount": float(arguments["amount"]),
                    "description": arguments["description"],
                    "currency": arguments.get("currency", "uzs"),
                    "category_slug": arguments.get("category_slug"),
                }
                
                return {
                    "success": True,
                    "pending_confirmation": True,
                    "parsed_transaction": tx_data
                }
            
            elif function_name == "get_balance":
                period = arguments.get("period", "month")
                balance = await self.api_client.get_balance(period=period)
                return balance
            
            elif function_name == "get_statistics":
                period = arguments.get("period", "month")
                balance = await self.api_client.get_balance(period=period)
                breakdown = await self.api_client.get_category_breakdown(period=period)
                return {
                    "balance": balance,
                    "breakdown": breakdown
                }
            
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            logger.exception(f"Tool execution error: {e}")
            return {"error": str(e)}
