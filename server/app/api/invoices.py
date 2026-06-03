from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, status
from fastapi import UploadFile as FastAPIUploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.invoice import (
    DeleteResponse,
    InvoiceListResponse,
    InvoiceResponse,
    UpdateInvoiceRequest,
    UploadResponse,
)
from app.services.invoice_service import (
    confirm_invoice,
    delete_invoice,
    get_invoice,
    list_invoices,
    list_trash,
    restore_archived_invoice,
    restore_invoice,
    update_invoice,
    upload_batch,
)

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/", response_model=InvoiceListResponse)
async def api_list_invoices(
    state: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if page_size not in (20, 50, 100, 200):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="page_size 必须为 20、50、100 或 200",
        )
    return list_invoices(db, current_user.id, state=state, page=page, page_size=page_size)


@router.post("/", response_model=UploadResponse)
async def upload_invoice(
    request: Request,
    files: list[FastAPIUploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task_manager = getattr(request.app.state, "ocr_task_manager", None)
    return upload_batch(db, current_user.id, files, settings.upload_dir, task_manager=task_manager)


@router.get("/trash", response_model=InvoiceListResponse)
async def api_list_trash(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_trash(db, current_user.id, page=page, page_size=page_size)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def api_get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoice = get_invoice(db, current_user.id, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="发票不存在")
    return InvoiceResponse.model_validate(invoice)


@router.get("/{invoice_id}/file")
async def api_get_invoice_file(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoice = get_invoice(db, current_user.id, invoice_id)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="发票不存在")
    return FileResponse(invoice.file_path)


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def api_update_invoice(
    invoice_id: int,
    data: UpdateInvoiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoice = update_invoice(db, current_user.id, invoice_id, data)
    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/confirm", response_model=InvoiceResponse)
async def api_confirm_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoice = confirm_invoice(db, current_user.id, invoice_id)
    return InvoiceResponse.model_validate(invoice)


@router.delete("/{invoice_id}", response_model=DeleteResponse)
async def api_delete_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_invoice(db, current_user.id, invoice_id, settings.upload_dir)


@router.post("/{invoice_id}/restore", response_model=InvoiceResponse)
async def api_restore_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoice = restore_invoice(db, current_user.id, invoice_id)
    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/restore-from-archive", response_model=InvoiceResponse)
async def api_restore_from_archive(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invoice = restore_archived_invoice(db, current_user.id, invoice_id)
    return InvoiceResponse.model_validate(invoice)
