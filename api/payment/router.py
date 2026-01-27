from fastapi import APIRouter
from .click.router import router as click_router
from .payme.router import router as payme_router

router = APIRouter(prefix="/payment", tags=["Payment"])

router.include_router(click_router)
router.include_router(payme_router)
