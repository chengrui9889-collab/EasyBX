from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.batches import router as batches_router
from app.api.dashboard import router as dashboard_router
from app.api.exports import router as exports_router
from app.api.invoices import router as invoices_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(batches_router)
api_router.include_router(dashboard_router)
api_router.include_router(exports_router)
api_router.include_router(invoices_router)
