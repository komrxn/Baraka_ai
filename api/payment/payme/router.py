from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from .services import PaymeService
from .schemas import JsonRpcRequest, JsonRpcResponse, PaymeError
from .exceptions import PaymeException
from .utils import verify_payme_auth

router = APIRouter(prefix="/payme", tags=["Payme"])

@router.post("")
async def payme_rpc_endpoint(
    request: JsonRpcRequest, 
    raw_request: Request,
    db: AsyncSession = Depends(get_db),
    authorized: bool = Depends(verify_payme_auth)
):
    """
    Single entry point for Payme JSON-RPC.
    """
    service = PaymeService(db)
    response_id = request.id
    
    try:
        method = request.method
        params = request.params
        res = None

        if method == "CheckPerformTransaction":
            res = await service.check_perform_transaction(params)
        elif method == "CreateTransaction":
            res = await service.create_transaction(params)
        elif method == "PerformTransaction":
            res = await service.perform_transaction(params)
        elif method == "CancelTransaction":
            res = await service.cancel_transaction(params)
        elif method == "CheckTransaction":
            res = await service.check_transaction(params)
        elif method == "GetStatement":
            res = await service.get_statement(params)
        elif method == "ChangePassword":
             # Optional Method, often not used or just returns success if logic not needed
             res = {"success": True}
        else:
            return {
                "jsonrpc": "2.0",
                "id": response_id,
                "error": {
                    "code": -32504,
                    "message": "Method not found"
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": response_id,
            "result": res
        }
        
    except PaymeException as pe:
        # Expected Logic Error
        error_data = {
            "code": pe.code,
            "message": pe.message
        }
        if pe.data is not None:
            error_data["data"] = pe.data

        return {
            "jsonrpc": "2.0",
            "id": response_id,
            "error": error_data
        }
    except Exception as e:
        # Unexpected System Error
        import traceback
        traceback.print_exc()
        return {
            "jsonrpc": "2.0",
            "id": response_id,
            "error": {
                "code": -32400,
                "message": {"ru": "System Error", "uz": "Tizim xatosi", "en": "System Error"},
                "data": str(e)
            }
        }
