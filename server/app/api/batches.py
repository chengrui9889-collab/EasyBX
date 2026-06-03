from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.user import User
from app.models.invoice import Invoice
from app.schemas.batch import (
    AddInvoicesRequest,
    AvailableInvoiceListResponse,
    BatchDetailResponse,
    BatchListResponse,
    BatchResponse,
    CreateBatchRequest,
    ManualRowCreateRequest,
    ManualRowDeleteResponse,
    ManualRowResponse,
    ManualRowUpdateRequest,
    SubstituteCreatedResponse,
    SubstituteCreateRequest,
    SubstituteInvoiceListResponse,
    SubstituteRelationListResponse,
    UpdateBatchInvoiceRequest,
    UpdateBatchRequest,
)
from app.services.batch_service import (
    add_invoices,
    add_manual_row,
    archive_batch,
    complete_batch,
    create_batch,
    delete_batch,
    delete_manual_row,
    get_batch_detail,
    list_available_invoices,
    list_batches,
    remove_invoice,
    unarchive_batch,
    update_batch,
    update_batch_invoice,
    update_manual_row,
)
from app.services.substitute_service import (
    create_substitution,
    list_substitute_invoices,
    list_substitutions,
    remove_substitution,
)
from app.services.excel_service import export_batch_excel
from app.schemas.export import BatchPdfExportRequest
from app.services.pdf_service import generate_invoice_pdf

router = APIRouter(prefix="/batches", tags=["batches"])


@router.get("/available-invoices", response_model=AvailableInvoiceListResponse)
async def api_list_available_invoices(
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_available_invoices(db, current_user.id, keyword=keyword, page=page, page_size=page_size)


@router.get("/", response_model=BatchListResponse)
async def api_list_batches(
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_batches(db, current_user.id, status=status)


@router.post("/", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def api_create_batch(
    data: CreateBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_batch(db, current_user.id, data)


@router.get("/{batch_id}/export-excel")
async def api_export_batch_excel(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_bytes = export_batch_excel(db, current_user.id, batch_id)
    batch = db.query(ReimbursementBatch).filter(ReimbursementBatch.id == batch_id).first()
    dept = batch.department if batch else "unknown"
    ps = batch.period_start.isoformat() if batch and batch.period_start else ""
    pe = batch.period_end.isoformat() if batch and batch.period_end else ""
    filename = f"{dept}_{ps}_{pe}_台账.xlsx"
    encoded_filename = quote(filename)
    return StreamingResponse(
        BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )


@router.post("/{batch_id}/export-invoice-pdf")
async def api_export_batch_invoice_pdf(
    batch_id: int,
    req: BatchPdfExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    batch = (
        db.query(ReimbursementBatch)
        .filter(
            ReimbursementBatch.id == batch_id,
            ReimbursementBatch.user_id == current_user.id,
        )
        .first()
    )
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BATCH_NOT_FOUND", "message": "批次不存在"},
        )

    batch_invoices = (
        db.query(BatchInvoice)
        .filter(
            BatchInvoice.batch_id == batch_id,
            BatchInvoice.invoice_id.isnot(None),
        )
        .all()
    )

    if not batch_invoices:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_BATCH", "message": "批次中没有发票可导出"},
        )

    invoice_ids = [bi.invoice_id for bi in batch_invoices if bi.invoice_id is not None]
    invoices = (
        db.query(Invoice)
        .filter(
            Invoice.id.in_(invoice_ids),
            Invoice.user_id == current_user.id,
        )
        .all()
    )

    pdf_bytes = generate_invoice_pdf(
        db, invoices, req.layouts, settings.upload_dir
    )

    filename = quote("发票合并.pdf")
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
        },
    )


@router.get("/{batch_id}", response_model=BatchDetailResponse)
async def api_get_batch_detail(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_batch_detail(db, current_user.id, batch_id)


@router.put("/{batch_id}", response_model=BatchResponse)
async def api_update_batch(
    batch_id: int,
    data: UpdateBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_batch(db, current_user.id, batch_id, data)


@router.put("/{batch_id}/complete", response_model=BatchResponse)
async def api_complete_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return complete_batch(db, current_user.id, batch_id)


@router.post("/{batch_id}/archive")
async def api_archive_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return archive_batch(db, current_user.id, batch_id)


@router.post("/{batch_id}/unarchive")
async def api_unarchive_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return unarchive_batch(db, current_user.id, batch_id)


@router.delete("/{batch_id}")
async def api_delete_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_batch(db, current_user.id, batch_id)


@router.post("/{batch_id}/invoices")
async def api_add_invoices(
    batch_id: int,
    data: AddInvoicesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_invoices(db, current_user.id, batch_id, data)


@router.put("/{batch_id}/invoices/{invoice_id}")
async def api_update_batch_invoice(
    batch_id: int,
    invoice_id: int,
    data: UpdateBatchInvoiceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_batch_invoice(db, current_user.id, batch_id, invoice_id, data)


@router.delete("/{batch_id}/invoices/{invoice_id}")
async def api_remove_invoice(
    batch_id: int,
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    remove_invoice(db, current_user.id, batch_id, invoice_id)
    return {"removed": True}


@router.post("/{batch_id}/manual-rows", response_model=ManualRowResponse, status_code=status.HTTP_201_CREATED)
async def api_add_manual_row(
    batch_id: int,
    data: ManualRowCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_manual_row(db, current_user.id, batch_id, data)


@router.put("/{batch_id}/manual-rows/{row_id}", response_model=ManualRowResponse)
async def api_update_manual_row(
    batch_id: int,
    row_id: int,
    data: ManualRowUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_manual_row(db, current_user.id, batch_id, row_id, data)


@router.delete("/{batch_id}/manual-rows/{row_id}", response_model=ManualRowDeleteResponse)
async def api_delete_manual_row(
    batch_id: int,
    row_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_manual_row(db, current_user.id, batch_id, row_id)


@router.get("/{batch_id}/available-substitute-invoices", response_model=SubstituteInvoiceListResponse)
async def api_list_substitute_invoices(
    batch_id: int,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_substitute_invoices(db, current_user.id, batch_id, keyword, page, page_size)


@router.post("/{batch_id}/substitutions", response_model=SubstituteCreatedResponse, status_code=status.HTTP_201_CREATED)
async def api_create_substitution(
    batch_id: int,
    data: SubstituteCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_substitution(db, current_user.id, batch_id, data)


@router.get("/{batch_id}/substitutions", response_model=SubstituteRelationListResponse)
async def api_list_substitutions(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_substitutions(db, current_user.id, batch_id)


@router.delete("/{batch_id}/substitutions/{sub_id}")
async def api_remove_substitution(
    batch_id: int,
    sub_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return remove_substitution(db, current_user.id, batch_id, sub_id)