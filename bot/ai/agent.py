"""Slim AIAgent class — orchestrates tools, prompt, and handlers."""
import json
import logging
from typing import Dict, Any, List

from openai import AsyncOpenAI

from ..config import config
from ..api_client import BarakaAPIClient
from ..dialog_context import dialog_context
from ..categories_data import DEFAULT_CATEGORIES

from .tools import TOOLS
from .prompt import build_system_prompt
from .tool_handlers import execute_tool
from .editor import edit_transaction as _edit_transaction
from .editor import edit_debt as _edit_debt

logger = logging.getLogger(__name__)


class AIAgent:
    """AI Agent using OpenAI Function Calling for transaction management."""

    def __init__(self, api_client: BarakaAPIClient):
        self.api_client = api_client
        self.client = AsyncOpenAI(
            api_key=config.OPENAI_API_KEY,
            timeout=120.0,
        )
        self.model = "gpt-5.1"
        self.tools = TOOLS

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def process_message(self, user_id: int, message: str) -> dict:
        """Process user message with AI agent.

        Returns dict with:
        - response: str — AI response text
        - created_transactions: List[Dict]
        - created_debts: List[Dict]
        - settled_debts: List[Dict]
        - premium_upsells: List[Dict]
        """
        from ..user_storage import storage
        from ..i18n import t

        lang = storage.get_user_language(user_id) or "uz"

        try:
            # Add user message to context
            dialog_context.add_message(user_id, "user", message)

            # Fetch fresh categories for the system prompt
            try:
                categories = await self.api_client.get_categories()
                expense_slugs = [c["slug"] for c in categories if c.get("type") == "expense"]
                income_slugs = [c["slug"] for c in categories if c.get("type") == "income"]
            except Exception as e:
                logger.error(f"Failed to fetch categories for prompt: {e}")
                expense_slugs = [c["slug"] for c in DEFAULT_CATEGORIES if c["type"] == "expense"]
                income_slugs = [c["slug"] for c in DEFAULT_CATEGORIES if c["type"] == "income"]

            # Build messages list
            dynamic_prompt = build_system_prompt(expense_slugs, income_slugs)
            history = dialog_context.get_openai_messages(user_id)
            messages = [{"role": "system", "content": dynamic_prompt}] + history

            # First OpenAI call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
            )

            assistant_message = response.choices[0].message

            # Handle empty response
            if not assistant_message.content and not assistant_message.tool_calls:
                logger.error("AI returned empty response")
                fallback = {
                    "uz": "Tushundim! Yozdim.",
                    "ru": "Понял! Записал.",
                    "en": "Got it! Recorded.",
                }.get(lang, "Понял! Записал.")
                return {"response": fallback, "parsed_transactions": []}

            # Multi-round tool execution loop (max 3 rounds)
            tool_calls = assistant_message.tool_calls
            created_transactions: List[Dict] = []
            created_debts: List[Dict] = []
            settled_debts: List[Dict] = []
            premium_upsells: List[Dict] = []
            max_rounds = 3
            round_num = 0

            while tool_calls and round_num < max_rounds:
                round_num += 1
                tool_results = []

                for tc in tool_calls:
                    try:
                        logger.info(
                            f"AI calling tool (round {round_num}): "
                            f"{tc.function.name} with args: {tc.function.arguments}"
                        )
                        result = await execute_tool(self.api_client, user_id, tc)

                        tool_results.append({
                            "tool_call_id": tc.id,
                            "output": json.dumps(result, ensure_ascii=False),
                        })

                        # Classify results
                        if isinstance(result, dict) and result.get("success"):
                            if "transaction_id" in result:
                                created_transactions.append(result)
                            elif "debt_id" in result:
                                created_debts.append(result)
                            elif "settled_debt_id" in result:
                                settled_debts.append(result)
                        elif result.get("premium_required"):
                            premium_upsells.append(result)

                    except Exception as e:
                        logger.exception(f"Error executing tool {tc.function.name}: {e}")
                        tool_results.append({
                            "tool_call_id": tc.id,
                            "output": json.dumps({"error": str(e)}, ensure_ascii=False),
                        })

                # Append assistant + tool messages to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": assistant_message.tool_calls,
                })
                for tr in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tr["tool_call_id"],
                        "content": tr["output"],
                    })

                # Next OpenAI call (may return more tool calls)
                next_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                )
                assistant_message = next_response.choices[0].message
                tool_calls = assistant_message.tool_calls

            final_text = assistant_message.content

            # Save to context
            dialog_context.add_message(user_id, "assistant", final_text or "")

            fallback_done = {
                "uz": "Tayyor!",
                "ru": "Готово!",
                "en": "Done!",
            }.get(lang, "Готово!")

            return {
                "response": final_text or fallback_done,
                "created_transactions": created_transactions,
                "created_debts": created_debts,
                "settled_debts": settled_debts,
                "premium_upsells": premium_upsells,
            }

        except Exception as e:
            logger.exception(f"AI agent error: {e}")
            error_msg = t("common.common.error", lang)
            return {
                "response": f"❌ {error_msg}",
                "created_transactions": [],
            }

    # ------------------------------------------------------------------
    # Editors (delegate to editor module)
    # ------------------------------------------------------------------

    async def edit_transaction(self, old_data: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Smartly edit transaction based on user input."""
        return await _edit_transaction(self.client, self.api_client, self.model, old_data, user_input)

    async def edit_debt(self, old_data: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """Smartly edit debt based on user input."""
        return await _edit_debt(self.client, self.model, old_data, user_input)
