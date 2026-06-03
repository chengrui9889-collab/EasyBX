from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.invoice import Invoice
from app.models.user import User
from app.schemas.export import PdfExportRequest, ReimbursementPreviewResponse
from app.services.pdf_service import generate_invoice_pdf
from app.services import reimbursement_service

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/invoice-pdf")
async def export_invoice_pdf(
    req: PdfExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not req.invoice_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_INVOICES", "message": "请选择要导出的发票"},
        )

    invoices = (
        db.query(Invoice)
        .filter(
            Invoice.id.in_(req.invoice_ids),
            Invoice.user_id == current_user.id,
        )
        .all()
    )

    if len(invoices) < len(req.invoice_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "INVOICE_NOT_FOUND", "message": "部分发票不存在或不属于当前用户"},
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


@router.get("/reimbursement-preview/{batch_id}", response_model=ReimbursementPreviewResponse)
async def get_reimbursement_preview(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return reimbursement_service.get_reimbursement_preview(db, current_user.id, batch_id)


@router.get("/reimbursement-pdf/{batch_id}")
async def export_reimbursement_pdf(batch_id: int):
    return {"message": "TODO"}