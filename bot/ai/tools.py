"""Tool definitions for OpenAI Function Calling."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_transaction",
            "description": "Create a new transaction (expense or income)",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Transaction amount"},
                    "currency": {
                        "type": "string",
                        "enum": ["uzs", "usd", "eur", "rub", "gbp", "cny", "kzt", "aed", "try"],
                        "description": "Currency code (uzs, usd, eur, rub, etc.)",
                    },
                    "category_slug": {
                        "type": "string",
                        "description": "Category slug (must be from available list)",
                    },
                    "description": {"type": "string", "description": "Description of the transaction"},
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format (optional)"},
                    "type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "Transaction type",
                    },
                },
                "required": ["amount", "currency", "category_slug", "type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Get current balance and limits status",
            "parameters": {"type": "object", "properties": {}},
        },
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
                        "description": "Time period for statistics",
                    }
                },
                "required": ["period"],
            },
        },
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
                    "slug": {
                        "type": "string",
                        "description": "English unique slug (e.g. 'server_costs' for 'Серверы')",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["income", "expense"],
                        "description": "Category type",
                    },
                    "icon": {"type": "string", "description": "Emoji icon for the category"},
                    "color": {"type": "string", "description": "Color in HEX format (e.g. #FF0000)"},
                },
                "required": ["name", "type", "icon"],
            },
        },
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
                    "currency": {
                        "type": "string",
                        "enum": ["uzs", "usd"],
                        "description": "Currency code",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["i_owe", "owe_me"],
                        "description": "Debt type: 'i_owe' if I borrowed, 'owe_me' if I lent",
                    },
                    "description": {"type": "string", "description": "Description (optional)"},
                    "due_date": {
                        "type": "string",
                        "description": "Due date in YYYY-MM-DD format (optional)",
                    },
                },
                "required": ["person_name", "amount", "currency", "type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "settle_debt",
            "description": (
                "Mark a debt as paid/settled. If the debt does not exist yet, "
                "first call create_debt to record it, then call settle_debt to mark it as settled."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "person_name": {
                        "type": "string",
                        "description": "Name of the person to settle debt with",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to pay (optional, if not specified tries to settle full debt)",
                    },
                },
                "required": ["person_name"],
            },
        },
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
                    "period": {
                        "type": "string",
                        "enum": ["month"],
                        "description": "Period (default: month)",
                    },
                },
                "required": ["category_slug", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_transactions",
            "description": "Delete multiple transactions by their IDs. Use this ONLY after listing transactions to find their IDs and confirming with the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of transaction IDs (UUIDs) to delete"
                    }
                },
                "required": ["transaction_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_transactions",
            "description": "Get a list of recent transactions. Use this to find IDs for deletion or to show history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of transactions to retrieve (default: 5, max: 20)"
                    }
                },
                "required": []
            }
        }
    }
]
