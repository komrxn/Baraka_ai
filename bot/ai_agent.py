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
                                "enum": ["food", "transport", "entertainment", "shopping", "bills", "healthcare", "education", "housing", "salary", "freelance", "investment", "gift", "other"],
                                "description": "Категория: food (еда/кафе), transport (такси/транспорт), entertainment (развлечения), shopping (покупки), bills (счета/связь), healthcare (здоровье), education (образование), housing (жильё), salary (зарплата), freelance (фриланс), investment (инвестиции), gift (подарок), other (прочее)"
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
        
        self.system_prompt = """Ты умный финансовый ассистент в Telegram боте Midas. 

ТВОИ ЗАДАЧИ:
1. Помогать пользователю записывать доходы и расходы
2. Отвечать на вопросы о финансах
3. Общаться дружелюбно на русском языке

ПРАВИЛА РАБОТЫ С ТРАНЗАКЦИЯМИ:
- Когда пользователь говорит о трате денег - вызывай create_transaction с type="expense"
- Когда говорит о доходе - вызывай create_transaction с type="income"
- Если в одном сообщении несколько транзакций - вызывай create_transaction НЕСКОЛЬКО РАЗ
- Преобразуй "30к", "30 тысяч", "30 тыщ" в 30000
- Преобразуй "5кк", "5 млн", "5 лям" в 5000000
- По умолчанию валюта - uzs (узбекский сум)

ПРИМЕРЫ:
Пользователь: "Потратил на ужин 70к и получил зарплату 300к"
Ты вызываешь:
  1. create_transaction(type="expense", amount=70000, description="ужин", category_slug="food")
  2. create_transaction(type="income", amount=300000, description="зарплата", category_slug="salary")
Отвечаешь: "✅ Записал:\n• Расход: Ужин -70,000 UZS\n• Доход: Зарплата +300,000 UZS"

Пользователь: "Сколько я потратил?"
Ты вызываешь: get_statistics()
Отвечаешь на основе данных из функции

Пользователь: "Привет!"
Ты НЕ вызываешь функции, просто отвечаешь: "Привет! Я помогу тебе вести учёт финансов. Просто напиши о своих тратах или доходах!"

КАТЕГОРИИ:
- food - еда, кафе, рестораны, кофе, обеды
- transport - такси, транспорт, проезд
- bills - счета, связь, интернет, Beeline, Click
- shopping - покупки, одежда, техника
- entertainment - развлечения, кино, игры
- salary - зарплата, оклад
- other - всё остальное

Будь кратким и дружелюбным!
Всегда отвечай на языке на котором говорит пользователь"""
    
    async def process_message(self, user_id: int, message: str) -> str:
        """Process user message with AI agent."""
        try:
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
            
            return final_text or "Понял!"
            
        except Exception as e:
            logger.exception(f"AI agent error: {e}")
            return "❌ Произошла ошибка. Попробуй ещё раз."
    
    async def _execute_tool(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function."""
        try:
            if function_name == "create_transaction":
                # Create transaction via API
                tx_data = {
                    "type": arguments["type"],
                    "amount": float(arguments["amount"]),
                    "description": arguments["description"],
                    "currency": arguments.get("currency", "uzs"),
                    "transaction_date": None  # API will use current time
                }
                
                # Add category if provided
                if arguments.get("category_slug"):
                    # Get category ID from slug
                    categories = await self.api_client.get_categories()
                    for cat in categories:
                        if cat.get("slug") == arguments["category_slug"]:
                            tx_data["category_id"] = cat["id"]
                            break
                
                result = await self.api_client.create_transaction(tx_data)
                return {
                    "success": True,
                    "transaction": result
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
