from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fastapi import HTTPException

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.invoice import Invoice
from app.models.substitute import SubstituteRelation
from app.schemas.batch import (
    ManualRowResponse,
    SubstituteCreatedResponse,
    SubstituteCreateRequest,
    SubstituteInvoiceItem,
    SubstituteInvoiceListResponse,
    SubstituteRelationListResponse,
    SubstituteRelationResponse,
)


def list_substitute_invoices(
    db: Session,
    user_id: int,
    batch_id: int,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> SubstituteInvoiceListResponse:
    batch = db.query(ReimbursementBatch).filter(
        ReimbursementBatch.id == batch_id,
        ReimbursementBatch.user_id == user_id,
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    used_invoice_ids_subq = (
        select(BatchInvoice.invoice_id)
        .where(
            BatchInvoice.invoice_id.isnot(None),
            BatchInvoice.source_type == "invoice",
        )
        .subquery()
    )

    base_q = db.query(Invoice).filter(
        Invoice.user_id == user_id,
        Invoice.status == "confirmed",
        Invoice.id.notin_(used_invoice_ids_subq),
    )

    if keyword:
        like = f"%{keyword}%"
        base_q = base_q.filter(
            (Invoice.invoice_no.like(like)) | (Invoice.vendor.like(like))
        )

    total = base_q.count()

    invoices = (
        base_q
        .order_by(Invoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    used_subq = (
        db.query(
            SubstituteRelation.substitute_invoice_id,
            func.coalesce(func.sum(BatchInvoice.row_amount), 0.0).label("used"),
        )
        .join(BatchInvoice, SubstituteRelation.target_row_id == BatchInvoice.id)
        .group_by(SubstituteRelation.substitute_invoice_id)
        .subquery()
    )

    invoice_ids = [inv.id for inv in invoices]
    usage_map: dict[int, float] = {}
    if invoice_ids:
        usage_rows = (
            db.query(
                used_subq.c.substitute_invoice_id, used_subq.c.used
            )
            .filter(used_subq.c.substitute_invoice_id.in_(invoice_ids))
            .all()
        )
        usage_map = {row.substitute_invoice_id: float(row.used) for row in usage_rows}

    items = []
    for inv in invoices:
        used = usage_map.get(inv.id, 0.0)
        items.append(
            SubstituteInvoiceItem(
                id=inv.id,
                invoice_no=inv.invoice_no or "",
                amount=inv.amount or 0.0,
                invoice_date=inv.invoice_date,
                category=inv.category,
                vendor=inv.vendor,
                file_path=inv.file_path,
                file_original_name=inv.file_original_name,
                used_as_substitute=used,
                remaining_amount=(inv.amount or 0.0) - used,
            )
        )

    return SubstituteInvoiceListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


def create_substitution(
    db: Session,
    user_id: int,
    batch_id: int,
    data: SubstituteCreateRequest,
) -> SubstituteCreatedResponse:
    batch = db.query(ReimbursementBatch).filter(
        ReimbursementBatch.id == batch_id,
        ReimbursementBatch.user_id == user_id,
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    mode = data.mode
    sub_ids = data.substitute_invoice_ids
    tgt_ids = data.target_row_ids

    if mode == "one_to_one":
        if len(sub_ids) != 1 or len(tgt_ids) != 1:
            raise HTTPException(status_code=400, detail="一对一模式需要恰好一张替票发票和一个目标行")
    elif mode == "one_to_many":
        if len(sub_ids) != 1 or len(tgt_ids) < 1:
            raise HTTPException(status_code=400, detail="一对多模式需要一张替票发票和至少一个目标行")
    elif mode == "many_to_one":
        if len(sub_ids) < 1 or len(tgt_ids) != 1:
            raise HTTPException(status_code=400, detail="多对一模式需要至少一张替票发票和一个目标行")

    target_rows = db.query(BatchInvoice).filter(
        BatchInvoice.id.in_(tgt_ids),
        BatchInvoice.batch_id == batch_id,
    ).all()
    if len(target_rows) != len(tgt_ids):
        raise HTTPException(status_code=400, detail="部分目标行不属于当前批次")

    target_total = 0.0
    for tr in target_rows:
        if tr.source_type == "manual":
            target_total += tr.row_amount or 0.0
        else:
            inv = db.query(Invoice).filter(Invoice.id == tr.invoice_id).first()
            target_total += (inv.amount or 0.0) if inv else 0.0

    occupied_subq = (
        select(BatchInvoice.invoice_id)
        .where(
            BatchInvoice.invoice_id.isnot(None),
            BatchInvoice.source_type == "invoice",
            BatchInvoice.is_substitute == False,
        )
        .subquery()
    )

    sub_invoices = db.query(Invoice).filter(
        Invoice.id.in_(sub_ids),
        Invoice.user_id == user_id,
        Invoice.status == "confirmed",
        Invoice.id.notin_(occupied_subq),
    ).all()

    if len(sub_invoices) != len(sub_ids):
        raise HTTPException(status_code=400, detail="部分替票发票不存在、未入库或已被占用")

    sub_used_map: dict[int, float] = {}
    used_rows = (
        db.query(
            SubstituteRelation.substitute_invoice_id,
            func.coalesce(func.sum(BatchInvoice.row_amount), 0.0).label("used"),
        )
        .join(BatchInvoice, SubstituteRelation.target_row_id == BatchInvoice.id)
        .filter(SubstituteRelation.substitute_invoice_id.in_(sub_ids))
        .group_by(SubstituteRelation.substitute_invoice_id)
        .all()
    )
    sub_used_map = {row.substitute_invoice_id: float(row.used) for row in used_rows}

    sub_available = 0.0
    for inv in sub_invoices:
        used = sub_used_map.get(inv.id, 0.0)
        sub_available += (inv.amount or 0.0) - used

    if sub_available < target_total:
        raise HTTPException(status_code=400, detail="替票发票金额不足，无法替换目标费用行")

    created_relations = []
    updated_rows = []

    existing_placeholder_ids = {
        row.invoice_id
        for row in db.query(BatchInvoice).filter(
            BatchInvoice.batch_id == batch_id,
            BatchInvoice.is_substitute == True,
            BatchInvoice.source_type == "invoice",
        ).all()
    }

    for sub_inv in sub_invoices:
        if sub_inv.id not in existing_placeholder_ids:
            placeholder = BatchInvoice(
                batch_id=batch_id,
                invoice_id=sub_inv.id,
                source_type="invoice",
                is_substitute=True,
            )
            db.add(placeholder)
            existing_placeholder_ids.add(sub_inv.id)

    for sub_inv in sub_invoices:
        for tr in target_rows:
            rel = SubstituteRelation(
                batch_id=batch_id,
                substitute_invoice_id=sub_inv.id,
                target_row_id=tr.id,
                mode=mode,
            )
            db.add(rel)
            created_relations.append(rel)

    for tr in target_rows:
        sub_nos = []
        for sub_inv in sub_invoices:
            sub_nos.append(sub_inv.invoice_no or str(sub_inv.id))

        tr.is_substitute = True
        sub_label = "替票" + ("、替票".join(sub_nos))
        tr.substitute_for = sub_label

        existing_remark = (tr.remark or "").strip()
        if sub_label not in existing_remark:
            tr.remark = (existing_remark + "（" + sub_label + "）").strip()

    db.commit()

    for rel in created_relations:
        db.refresh(rel)
    for tr in target_rows:
        db.refresh(tr)

    relation_responses = []
    for rel in created_relations:
        rel_sub_inv = next(si for si in sub_invoices if si.id == rel.substitute_invoice_id)
        rel_tr = next(tr for tr in target_rows if tr.id == rel.target_row_id)

        def _build_invoice_item(inv, used_map, sub_available_map):
            u = used_map.get(inv.id, 0.0)
            return SubstituteInvoiceItem(
                id=inv.id,
                invoice_no=inv.invoice_no or "",
                amount=inv.amount or 0.0,
                invoice_date=inv.invoice_date,
                category=inv.category,
                vendor=inv.vendor,
                file_path=inv.file_path,
                file_original_name=inv.file_original_name,
                used_as_substitute=u,
                remaining_amount=(inv.amount or 0.0) - u,
            )

        relation_responses.append(
            SubstituteRelationResponse(
                id=rel.id,
                batch_id=rel.batch_id,
                substitute_invoice_id=rel.substitute_invoice_id,
                target_row_id=rel.target_row_id,
                mode=rel.mode,
                substitute_invoice=_build_invoice_item(rel_sub_inv, sub_used_map, {}),
                target_row=ManualRowResponse.model_validate(rel_tr),
            )
        )

    row_responses = [ManualRowResponse.model_validate(tr) for tr in target_rows]

    return SubstituteCreatedResponse(
        relations=relation_responses,
        updated_target_rows=row_responses,
    )


def list_substitutions(
    db: Session,
    user_id: int,
    batch_id: int,
) -> SubstituteRelationListResponse:
    batch = db.query(ReimbursementBatch).filter(
        ReimbursementBatch.id == batch_id,
        ReimbursementBatch.user_id == user_id,
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    relations = (
        db.query(SubstituteRelation)
        .filter(SubstituteRelation.batch_id == batch_id)
        .all()
    )

    invoice_ids = {r.substitute_invoice_id for r in relations}
    invoices = db.query(Invoice).filter(Invoice.id.in_(invoice_ids)).all() if invoice_ids else []
    invoice_map = {inv.id: inv for inv in invoices}

    target_ids = {r.target_row_id for r in relations}
    target_rows = db.query(BatchInvoice).filter(BatchInvoice.id.in_(target_ids)).all() if target_ids else []
    target_map = {tr.id: tr for tr in target_rows}

    def _build_inv_item(inv):
        return SubstituteInvoiceItem(
            id=inv.id,
            invoice_no=inv.invoice_no or "",
            amount=inv.amount or 0.0,
            invoice_date=inv.invoice_date,
            category=inv.category,
            vendor=inv.vendor,
            file_path=inv.file_path,
            file_original_name=inv.file_original_name,
            used_as_substitute=0.0,
            remaining_amount=inv.amount or 0.0,
        )

    result = []
    for rel in relations:
        result.append(
            SubstituteRelationResponse(
                id=rel.id,
                batch_id=rel.batch_id,
                substitute_invoice_id=rel.substitute_invoice_id,
                target_row_id=rel.target_row_id,
                mode=rel.mode,
                created_at=rel.created_at,
                substitute_invoice=_build_inv_item(invoice_map[rel.substitute_invoice_id]) if rel.substitute_invoice_id in invoice_map else None,
                target_row=ManualRowResponse.model_validate(target_map[rel.target_row_id]) if rel.target_row_id in target_map else None,
            )
        )

    return SubstituteRelationListResponse(relations=result)


def remove_substitution(
    db: Session,
    user_id: int,
    batch_id: int,
    sub_id: int,
) -> dict:
    batch = db.query(ReimbursementBatch).filter(
        ReimbursementBatch.id == batch_id,
        ReimbursementBatch.user_id == user_id,
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    rel = db.query(SubstituteRelation).filter(
        SubstituteRelation.id == sub_id,
        SubstituteRelation.batch_id == batch_id,
    ).first()
    if not rel:
        raise HTTPException(status_code=404, detail="替票关联不存在")

    target_row = db.query(BatchInvoice).filter(BatchInvoice.id == rel.target_row_id).first()

    remaining_relations = (
        db.query(SubstituteRelation)
        .filter(
            SubstituteRelation.batch_id == batch_id,
            SubstituteRelation.target_row_id == rel.target_row_id,
            SubstituteRelation.id != sub_id,
        )
        .all()
    )

    if not remaining_relations:
        if target_row:
            target_row.is_substitute = False
            target_row.substitute_for = None
            current_remark = target_row.remark or ""
            import re
            current_remark = re.sub(r"（替票[^）]*）", "", current_remark).strip()
            target_row.remark = current_remark

    db.delete(rel)
    db.flush()

    other_for_same_invoice = (
        db.query(SubstituteRelation)
        .filter(
            SubstituteRelation.batch_id == batch_id,
            SubstituteRelation.substitute_invoice_id == rel.substitute_invoice_id,
        )
        .first()
    )

    if not other_for_same_invoice:
        placeholder = db.query(BatchInvoice).filter(
            BatchInvoice.batch_id == batch_id,
            BatchInvoice.invoice_id == rel.substitute_invoice_id,
            BatchInvoice.is_substitute == True,
        ).first()
        if placeholder:
            db.delete(placeholder)

    db.commit()

    return {"removed": True}