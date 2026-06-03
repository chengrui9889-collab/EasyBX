from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.invoice import Invoice
from app.schemas.invoice import (
    DeleteResponse,
    InvoiceListResponse,
    InvoiceResponse,
    UpdateInvoiceRequest,
    UploadFileResult,
    UploadResponse,
)
from app.utils.file_utils import generate_storage_path, is_allowed_file

MAX_FILES = 20
VALID_PAGE_SIZES = {20, 50, 100, 200}


def upload_batch(
    db: Session,
    user_id: int,
    files: list,
    upload_dir: Path,
    task_manager=None,
) -> UploadResponse:
    skipped_count = 0
    results: list[UploadFileResult] = []

    if len(files) > MAX_FILES:
        skipped_count = len(files) - MAX_FILES
        files = files[:MAX_FILES]

    for file in files:
        filename = file.filename

        if not is_allowed_file(filename):
            results.append(
                UploadFileResult(
                    filename=filename,
                    success=False,
                    error="不支持的文件格式",
                )
            )
            continue

        content = file.file.read()

        if len(content) > settings.max_upload_size_bytes:
            results.append(
                UploadFileResult(
                    filename=filename,
                    success=False,
                    error=f"文件大小超过 {settings.max_upload_size_mb}MB 限制",
                )
            )
            continue

        storage_path = generate_storage_path(upload_dir, user_id, filename)
        Path(storage_path).parent.mkdir(parents=True, exist_ok=True)
        with open(storage_path, "wb") as f:
            f.write(content)

        invoice = Invoice(
            user_id=user_id,
            file_path=storage_path,
            file_original_name=filename,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        if task_manager is not None:
            task_manager.submit_task(invoice.id, storage_path, None)

        results.append(
            UploadFileResult(
                filename=filename,
                success=True,
                invoice_id=invoice.id,
            )
        )

    cleanup_expired(db, upload_dir)
    return UploadResponse(results=results, skipped_count=skipped_count)


def list_invoices(
    db: Session,
    user_id: int,
    state: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> InvoiceListResponse:
    if page_size not in VALID_PAGE_SIZES:
        page_size = 20

    query = db.query(Invoice).filter(
        Invoice.user_id == user_id,
        Invoice.deleted_at.is_(None),
    )

    if state:
        query = query.filter(Invoice.status == state)
    else:
        query = query.filter(Invoice.status != "archived")

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)

    items = (
        query
        .order_by(Invoice.invoice_date.desc().nullslast(), Invoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return InvoiceListResponse(
        items=[InvoiceResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def get_invoice(db: Session, user_id: int, invoice_id: int) -> Invoice:
    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.id == invoice_id,
            Invoice.user_id == user_id,
            Invoice.deleted_at.is_(None),
        )
        .first()
    )
    return invoice


UPDATABLE_STATES = {"pending", "failed", "confirmed"}


def _find_invoice(db: Session, user_id: int, invoice_id: int) -> Invoice:
    invoice = get_invoice(db, user_id, invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="发票不存在",
        )
    return invoice


def update_invoice(
    db: Session,
    user_id: int,
    invoice_id: int,
    data: UpdateInvoiceRequest,
) -> Invoice:
    invoice = _find_invoice(db, user_id, invoice_id)

    if invoice.status not in UPDATABLE_STATES:
        if invoice.status == "processing":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OCR 进行中，无法编辑",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已入库不可编辑",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(invoice, field, value)

    db.commit()
    db.refresh(invoice)
    return invoice


def confirm_invoice(
    db: Session,
    user_id: int,
    invoice_id: int,
) -> Invoice:
    invoice = _find_invoice(db, user_id, invoice_id)

    if invoice.status not in UPDATABLE_STATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前状态不允许确认入库",
        )

    if invoice.invoice_date is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="请填写发票日期",
        )

    if invoice.amount is None or invoice.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="金额必须大于 0",
        )

    invoice.status = "confirmed"
    invoice.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(invoice)
    return invoice


def delete_invoice_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()


HARD_DELETE_STATES = {"processing", "pending", "failed"}
RESTORE_DAYS = 30


def _find_invoice_any(db: Session, user_id: int, invoice_id: int) -> Invoice | None:
    return (
        db.query(Invoice)
        .filter(
            Invoice.id == invoice_id,
            Invoice.user_id == user_id,
        )
        .first()
    )


def delete_invoice(
    db: Session,
    user_id: int,
    invoice_id: int,
    upload_dir: Path,
) -> DeleteResponse:
    invoice = _find_invoice_any(db, user_id, invoice_id)
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="发票不存在",
        )

    if invoice.status in HARD_DELETE_STATES:
        delete_invoice_file(invoice.file_path)
        db.delete(invoice)
        db.commit()
        return DeleteResponse(deleted=True, type="hard")

    invoice.deleted_at = datetime.now(UTC)
    db.commit()
    return DeleteResponse(
        deleted=True,
        type="soft",
        restorable_until=invoice.deleted_at + timedelta(days=RESTORE_DAYS),
    )


def restore_invoice(
    db: Session,
    user_id: int,
    invoice_id: int,
) -> Invoice:
    invoice = _find_invoice_any(db, user_id, invoice_id)

    if invoice is None or invoice.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到可恢复的发票",
        )

    if invoice.deleted_at.replace(tzinfo=UTC) < datetime.now(UTC) - timedelta(days=RESTORE_DAYS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已超过 30 天恢复期限，无法恢复",
        )

    invoice.deleted_at = None
    invoice.status = "confirmed"
    invoice.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(invoice)
    return invoice


def list_trash(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> InvoiceListResponse:
    cutoff = datetime.now(UTC) - timedelta(days=RESTORE_DAYS)

    query = db.query(Invoice).filter(
        Invoice.user_id == user_id,
        Invoice.deleted_at.isnot(None),
        Invoice.deleted_at > cutoff,
    )

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)

    items = (
        query
        .order_by(Invoice.deleted_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return InvoiceListResponse(
        items=[InvoiceResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def cleanup_expired(db: Session, upload_dir: Path) -> None:
    cutoff = datetime.now(UTC) - timedelta(days=RESTORE_DAYS)

    expired = (
        db.query(Invoice)
        .filter(
            Invoice.deleted_at.isnot(None),
            Invoice.deleted_at <= cutoff,
        )
        .all()
    )

    for invoice in expired:
        delete_invoice_file(invoice.file_path)
        db.delete(invoice)

    if expired:
        db.commit()


def restore_archived_invoice(
    db: Session,
    user_id: int,
    invoice_id: int,
) -> Invoice:
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.user_id == user_id,
    ).first()

    if invoice is None:
        raise HTTPException(status_code=404, detail="发票不存在")

    if invoice.status != "archived":
        raise HTTPException(status_code=400, detail="只有已归档状态的发票才能恢复")

    invoice.status = "confirmed"
    db.commit()
    db.refresh(invoice)
    return invoice
