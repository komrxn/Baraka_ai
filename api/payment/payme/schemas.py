from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

# Base JSON-RPC
class JsonRpcRequest(BaseModel):
    method: str
    params: Dict[str, Any]
    id: Union[int, str, None] = None

class PaymeError(BaseModel):
    code: int
    message: str 
    data: Optional[str] = None

class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[PaymeError] = None
    id: Union[int, str, None] = None

# Params models for specific methods

class CheckPerformTransactionParams(BaseModel):
    amount: int
    account: Dict[str, Any]

class CreateTransactionParams(BaseModel):
    id: str # paycom_transaction_id
    time: int
    amount: int
    account: Dict[str, Any]

class PerformTransactionParams(BaseModel):
    id: str

class CancelTransactionParams(BaseModel):
    id: str
    reason: int

class CheckTransactionParams(BaseModel):
    id: str

class GetStatementParams(BaseModel):
    from_: int = Field(alias="from")
    to: int
