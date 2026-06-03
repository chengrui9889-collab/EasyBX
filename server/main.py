from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.services.ocr_service import OcrTaskManager

app = FastAPI(
    title="EasyBX API",
    description="智能发票管理与报销整理助手",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

upload_dir = settings.upload_dir
if not upload_dir.exists():
    upload_dir.mkdir(parents=True, exist_ok=True)

ocr_task_manager = OcrTaskManager(max_workers=settings.ocr_max_workers) if settings.ocr_enabled else None
if ocr_task_manager is not None:
    app.state.ocr_task_manager = ocr_task_manager


@app.on_event("startup")
async def startup():
    pass


@app.on_event("shutdown")
async def shutdown():
    if ocr_task_manager is not None:
        ocr_task_manager.shutdown(wait=False)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "EasyBX"}
