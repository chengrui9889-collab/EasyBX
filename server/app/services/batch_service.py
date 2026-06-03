from datetime import date

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.invoice import Invoice
from app.models.substitute import SubstituteRelation
from app.models.user import User
from app.schemas.batch import (
    AddInvoicesRequest,
    AvailableInvoiceItem,
    AvailableInvoiceListResponse,
    BatchDetailResponse,
    BatchListItem,
    BatchListResponse,
    BatchResponse,
    CreateBatchRequest,
    LedgerRowResponse,
    ManualRowCreateRequest,
    ManualRowDeleteResponse,
    ManualRowResponse,
    ManualRowUpdateRequest,
    UpdateBatchInvoiceRequest,
    UpdateBatchRequest,
)


def create_batch(db: Session, user_id: int, data: CreateBatchRequest) -> BatchResponse:
    user = db.query(User).filter(User.id == user_id).first()

    department = data.department if data.department is not None else (user.default_department if user else None)
    reporter = data.reporter if data.reporter is not None else (user.default_reporter if user else None)
    payee = data.payee if data.payee is not None else (user.default_payee if user else None)
    bank_account = data.bank_account if data.bank_account is not None else (user.default_bank_account if user else None)
    bank_name = data.bank_name if data.bank_name is not None else (user.default_bank_name if user else None)
    report_date = data.report_date if data.report_date is not None else date.today()

    batch = ReimbursementBatch(
        user_id=user_id,
        department=department or "",
        period_start=data.period_start,
        period_end=data.period_end,
        report_date=report_date,
        reporter=reporter or "",
        reviewer=data.reviewer,
        payee=payee,
        bank_account=bank_account,
        bank_name=bank_name,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return BatchResponse.model_validate(batch)


def list_batches(db: Session, user_id: int, status: str | None = None) -> BatchListResponse:
    query = (
        db.query(ReimbursementBatch)
        .filter(ReimbursementBatch.user_id == user_id)
    )

    if status:
        query = query.filter(ReimbursementBatch.status == status)

    batches = query.order_by(ReimbursementBatch.created_at.desc()).all()

    items = []
    for batch in batches:
        invoice_count = (
            db.query(BatchInvoice)
            .filter(
                BatchInvoice.batch_id == batch.id,
                or_(
                    BatchInvoice.source_type != "invoice",
                    BatchInvoice.is_substitute == False,
                    BatchInvoice.substitute_for.isnot(None),
                ),
            )
            .count()
        )
        item = BatchListItem(
            id=batch.id,
            department=batch.department,
            period_start=batch.period_start,
            period_end=batch.period_end,
            report_date=batch.report_date,
            reporter=batch.reporter,
            total_amount=batch.total_amount,
            status=batch.status,
            invoice_count=invoice_count,
            created_at=batch.created_at,
            updated_at=batch.updated_at,
        )
        items.append(item)

    return BatchListResponse(items=items, total=len(items))


def _auto_remark(invoice: Invoice) -> str:
    if invoice.remark:
        return invoice.remark
    if invoice.departure_station and invoice.arrival_station:
        return f"{invoice.departure_station}→{invoice.arrival_station}"
    if invoice.departure_location and invoice.arrival_location:
        return f"{invoice.departure_location}→{invoice.arrival_location}"
    if invoice.departure_city and invoice.arrival_city:
        return f"{invoice.departure_city}→{invoice.arrival_city}"
    return ""


def list_available_invoices(
    db: Session,
    user_id: int,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> AvailableInvoiceListResponse:
    used_ids = (
        db.query(BatchInvoice.invoice_id)
        .filter(
            BatchInvoice.invoice_id.isnot(None),
            or_(
                BatchInvoice.source_type != "invoice",
                BatchInvoice.is_substitute == False,
                BatchInvoice.substitute_for.isnot(None),
            ),
        )
        .subquery()
    )

    query = db.query(Invoice).filter(
        Invoice.user_id == user_id,
        Invoice.status == "confirmed",
        Invoice.id.notin_(used_ids),
    )

    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            (Invoice.invoice_no.ilike(kw))
            | (Invoice.vendor.ilike(kw))
            | (Invoice.category.ilike(kw))
        )

    total = query.count()
    offset = (page - 1) * page_size
    invoices = query.order_by(Invoice.created_at.desc()).offset(offset).limit(page_size).all()

    items = [AvailableInvoiceItem.model_validate(inv) for inv in invoices]
    return AvailableInvoiceListResponse(items=items, total=total, page=page, page_size=page_size)


def add_invoices(
    db: Session,
    user_id: int,
    batch_id: int,
    data: AddInvoicesRequest,
) -> list[dict]:
    batch = _get_and_validate_batch(db, batch_id, user_id)
    _ensure_draft(batch, "添加发票")

    try:
        results = []
        for invoice_id in data.invoice_ids:
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise HTTPException(status_code=400, detail=f"发票 {invoice_id} 不存在")

            if invoice.status != "confirmed":
                raise HTTPException(status_code=400, detail=f"发票 {invoice_id} 状态不是已确认")

            existing = db.query(BatchInvoice).filter(
                BatchInvoice.invoice_id == invoice_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"发票 {invoice_id} 已在其他批次中")

            amount = invoice.amount if invoice.amount else 0.0
            bi = BatchInvoice(
                batch_id=batch_id,
                invoice_id=invoice_id,
                quantity=1.0,
                unit_price=amount,
                advance_amount=amount,
                remark=_auto_remark(invoice),
            )
            db.add(bi)
            db.flush()

            batch.total_amount += amount

            results.append({
                "id": bi.id,
                "batch_id": bi.batch_id,
                "invoice_id": bi.invoice_id,
                "quantity": bi.quantity,
                "unit_price": bi.unit_price,
                "advance_amount": bi.advance_amount,
                "remark": bi.remark,
            })

        db.commit()
        return results
    except HTTPException:
        db.rollback()
        raise


def remove_invoice(db: Session, user_id: int, batch_id: int, invoice_id: int) -> bool:
    batch = _get_and_validate_batch(db, batch_id, user_id)
    _ensure_draft(batch, "移除发票")

    bi = db.query(BatchInvoice).filter(
        BatchInvoice.batch_id == batch_id,
        BatchInvoice.invoice_id == invoice_id,
    ).first()
    if not bi:
        raise HTTPException(status_code=404, detail="发票不在该批次中")

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    amount = invoice.amount if invoice and invoice.amount else 0.0

    db.delete(bi)
    batch.total_amount -= amount
    db.commit()

    return True


def get_batch_detail(db: Session, user_id: int, batch_id: int) -> BatchDetailResponse:
    batch = db.query(ReimbursementBatch).filter(
        ReimbursementBatch.id == batch_id,
        ReimbursementBatch.user_id == user_id,
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    batch_invoices = db.query(BatchInvoice).filter(
        BatchInvoice.batch_id == batch_id,
        or_(
            BatchInvoice.source_type != "invoice",
            BatchInvoice.is_substitute == False,
            BatchInvoice.substitute_for.isnot(None),
        )
    ).all()

    ledger_rows = []
    for bi in batch_invoices:
        invoice = db.query(Invoice).filter(Invoice.id == bi.invoice_id).first()
        if bi.source_type == "manual":
            ledger_rows.append(LedgerRowResponse(
                id=bi.id,
                invoice_id=None,
                invoice_date=bi.row_date,
                category=None,
                amount=bi.row_amount,
                quantity=bi.quantity,
                unit_price=bi.unit_price,
                advance_amount=bi.advance_amount,
                remark=bi.remark,
                expense_item=bi.expense_item,
                invoice_no=None,
                vendor=None,
                is_substitute=bi.is_substitute,
                substitute_for=bi.substitute_for,
                source_type=bi.source_type,
                row_date=bi.row_date,
                row_amount=bi.row_amount,
            ))
        else:
            ledger_rows.append(LedgerRowResponse(
                id=bi.id,
                invoice_id=bi.invoice_id,
                invoice_date=invoice.invoice_date if invoice else None,
                category=invoice.category if invoice else None,
                invoice_type=invoice.invoice_type if invoice else None,
                amount=invoice.amount if invoice else None,
                quantity=bi.quantity,
                unit_price=bi.unit_price,
                advance_amount=bi.advance_amount,
                remark=bi.remark,
                expense_item=bi.expense_item,
                invoice_no=invoice.invoice_no if invoice else None,
                vendor=invoice.vendor if invoice else None,
                is_substitute=bi.is_substitute,
                substitute_for=bi.substitute_for,
                source_type=bi.source_type,
                row_date=bi.row_date,
                row_amount=bi.row_amount,
            ))

    detail = BatchDetailResponse.model_validate(batch)
    detail.ledger_rows = ledger_rows
    return detail


def update_batch_invoice(
    db: Session,
    user_id: int,
    batch_id: int,
    invoice_id: int,
    data: UpdateBatchInvoiceRequest,
) -> dict:
    batch = _get_and_validate_batch(db, batch_id, user_id)
    _ensure_draft(batch, "编辑台账")

    bi = db.query(BatchInvoice).filter(
        BatchInvoice.batch_id == batch_id,
        BatchInvoice.invoice_id == invoice_id,
    ).first()
    if not bi:
        raise HTTPException(status_code=404, detail="发票不在该批次中")

    if data.quantity is not None:
        if data.quantity < 1:
            raise HTTPException(status_code=400, detail="数量不能小于1")
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        amount = invoice.amount if invoice and invoice.amount else 0.0
        bi.quantity = data.quantity
        bi.unit_price = round(amount / data.quantity, 2)

    if data.advance_amount is not None:
        bi.advance_amount = data.advance_amount

    if data.remark is not None:
        bi.remark = data.remark

    db.commit()
    db.refresh(bi)

    return {
        "id": bi.id,
        "batch_id": bi.batch_id,
        "invoice_id": bi.invoice_id,
        "quantity": bi.quantity,
        "unit_price": bi.unit_price,
        "advance_amount": bi.advance_amount,
        "remark": bi.remark,
        "expense_item": bi.expense_item,
        "is_substitute": bi.is_substitute,
        "substitute_for": bi.substitute_for,
    }


def _ensure_draft(batch: ReimbursementBatch, action: str) -> None:
    if batch.status != "draft":
        raise HTTPException(status_code=400, detail=f"只有草稿状态的批次才能{action}")


def complete_batch(db: Session, user_id: int, batch_id: int) -> BatchResponse:
    batch = _get_and_validate_batch(db, batch_id, user_id)
    _ensure_draft(batch, "完成")
    batch.status = "completed"
    db.commit()
    db.refresh(batch)
    return BatchResponse.model_validate(batch)


def archive_batch(db: Session, user_id: int, batch_id: int) -> dict:
    batch = _get_and_validate_batch(db, batch_id, user_id)

    if batch.status == "archived":
        raise HTTPException(status_code=400, detail="该批次已归档")

    if batch.status != "completed":
        raise HTTPException(status_code=400, detail="只有已完成状态的批次才能归档")

    linked_invoices = (
        db.query(BatchInvoice)
        .filter(BatchInvoice.batch_id == batch_id, BatchInvoice.invoice_id.isnot(None))
        .all()
    )

    if not linked_invoices:
        raise HTTPException(status_code=400, detail="该批次无发票")

    invoice_ids = [bi.invoice_id for bi in linked_invoices]
    db.query(Invoice).filter(Invoice.id.in_(invoice_ids)).update(
        {"status": "archived"}, synchronize_session=False
    )

    batch.status = "archived"
    db.commit()
    db.refresh(batch)

    return {
        "archived": True,
        "archived_invoice_count": len(invoice_ids),
        "batch_status": batch.status,
    }


def unarchive_batch(db: Session, user_id: int, batch_id: int) -> dict:
    batch = _get_and_validate_batch(db, batch_id, user_id)

    if batch.status != "archived":
        raise HTTPException(status_code=400, detail="只有已归档状态的批次才能撤销归档")

    linked_invoices = (
        db.query(BatchInvoice)
        .filter(BatchInvoice.batch_id == batch_id, BatchInvoice.invoice_id.isnot(None))
        .all()
    )

    invoice_ids = [bi.invoice_id for bi in linked_invoices]
    if invoice_ids:
        db.query(Invoice).filter(Invoice.id.in_(invoice_ids)).update(
            {"status": "confirmed"}, synchronize_session=False
        )

    batch.status = "completed"
    db.commit()
    db.refresh(batch)

    return {
        "unarchived": True,
        "batch_status": batch.status,
        "restored_invoice_count": len(invoice_ids),
    }


def update_batch(db: Session, user_id: int, batch_id: int, data: UpdateBatchRequest) -> BatchResponse:
    batch = _get_and_validate_batch(db, batch_id, user_id)
    _ensure_draft(batch, "修改")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(batch, key, value)

    db.commit()
    db.refresh(batch)
    return BatchResponse.model_validate(batch)


def delete_batch(db: Session, user_id: int, batch_id: int) -> dict:
    batch = db.query(ReimbursementBatch).filter(
        ReimbursementBatch.id == batch_id,
        ReimbursementBatch.user_id == user_id,
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    count = db.query(BatchInvoice).filter(BatchInvoice.batch_id == batch_id).count()

    db.query(SubstituteRelation).filter(SubstituteRelation.batch_id == batch_id).delete()
    db.query(BatchInvoice).filter(BatchInvoice.batch_id == batch_id).delete()
    db.delete(batch)
    db.commit()

    return {"deleted": True, "released_invoice_count": count}


def _get_and_validate_batch(db: Session, batch_id: int, user_id: int) -> ReimbursementBatch:
    batch = db.query(ReimbursementBatch).filter(
        ReimbursementBatch.id == batch_id,
        ReimbursementBatch.user_id == user_id,
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    return batch


def add_manual_row(
    db: Session,
    user_id: int,
    batch_id: int,
    data: ManualRowCreateRequest,
) -> ManualRowResponse:
    _get_and_validate_batch(db, batch_id, user_id)

    row_date_value = data.row_date if data.row_date is not None else date.today()
    unit_price = round(data.row_amount / data.quantity, 2)
    advance = data.advance_amount if data.advance_amount is not None else data.row_amount

    bi = BatchInvoice(
        batch_id=batch_id,
        invoice_id=None,
        source_type="manual",
        row_date=row_date_value,
        row_amount=data.row_amount,
        expense_item=data.expense_item,
        quantity=data.quantity,
        unit_price=unit_price,
        advance_amount=advance,
        remark=data.remark or "",
    )
    db.add(bi)
    db.commit()
    db.refresh(bi)

    return ManualRowResponse.model_validate(bi)


def update_manual_row(
    db: Session,
    user_id: int,
    batch_id: int,
    row_id: int,
    data: ManualRowUpdateRequest,
) -> ManualRowResponse:
    _get_and_validate_batch(db, batch_id, user_id)

    bi = db.query(BatchInvoice).filter(
        BatchInvoice.id == row_id,
        BatchInvoice.batch_id == batch_id,
    ).first()
    if not bi:
        raise HTTPException(status_code=404, detail="台账行不存在")
    if bi.source_type != "manual":
        raise HTTPException(status_code=400, detail="只能编辑手动添加的台账行")

    if data.row_amount is not None:
        bi.row_amount = data.row_amount
        qty = data.quantity if data.quantity is not None else bi.quantity
        bi.unit_price = round(data.row_amount / qty, 2)

    if data.quantity is not None:
        bi.quantity = data.quantity
        amt = data.row_amount if data.row_amount is not None else (bi.row_amount or 0)
        bi.unit_price = round(amt / data.quantity, 2)

    if data.advance_amount is not None:
        bi.advance_amount = data.advance_amount

    if data.remark is not None:
        bi.remark = data.remark

    if data.row_date is not None:
        bi.row_date = data.row_date

    if data.expense_item is not None:
        bi.expense_item = data.expense_item

    db.commit()
    db.refresh(bi)

    return ManualRowResponse.model_validate(bi)


def delete_manual_row(
    db: Session,
    user_id: int,
    batch_id: int,
    row_id: int,
) -> ManualRowDeleteResponse:
    _get_and_validate_batch(db, batch_id, user_id)

    bi = db.query(BatchInvoice).filter(
        BatchInvoice.id == row_id,
        BatchInvoice.batch_id == batch_id,
    ).first()
    if not bi:
        raise HTTPException(status_code=404, detail="台账行不存在")
    if bi.source_type != "manual":
        raise HTTPException(status_code=400, detail="只能删除手动添加的台账行")

    db.delete(bi)
    db.commit()

    return ManualRowDeleteResponse(deleted=True, released_substitute_count=0)