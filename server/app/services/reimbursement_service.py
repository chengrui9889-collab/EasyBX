from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.invoice import Invoice


def amount_to_chinese(amount: float) -> str:
    digits_cn = "零壹贰叁肆伍陆柒捌玖"
    units_int = ["", "拾", "佰", "仟"]
    units_section = ["", "万", "亿"]

    yuan = int(amount)
    jiao = int(round(amount * 10, 2)) % 10
    fen = int(round(amount * 100, 2)) % 10

    if yuan == 0 and jiao == 0 and fen == 0:
        return "零元整"

    def _convert_int(n: int) -> str:
        if n == 0:
            return "零"
        result = ""
        section_idx = 0
        lower_section_val = 0
        while n > 0:
            section = n % 10000
            n //= 10000
            if section > 0:
                section_str = _convert_section(section)
                if section_idx > 0:
                    if section < 1000 and lower_section_val < 1000:
                        result = "零" + result
                    section_str += units_section[section_idx]
                result = section_str + result
            lower_section_val = section
            section_idx += 1
        return result

    def _convert_section(n: int) -> str:
        result = ""
        unit_idx = 0
        last_is_zero = False
        while n > 0:
            digit = n % 10
            n //= 10
            if digit == 0:
                if not last_is_zero and result:
                    last_is_zero = True
                    result = "零" + result
            else:
                last_is_zero = False
                result = digits_cn[digit] + units_int[unit_idx] + result
            unit_idx += 1
        return result

    int_part = _convert_int(yuan)
    result = int_part + "元"

    if jiao == 0 and fen == 0:
        result += "整"
    else:
        if jiao > 0:
            result += digits_cn[jiao] + "角"
        if fen > 0:
            result += digits_cn[fen] + "分"
        else:
            result += "整"

    return result


def get_reimbursement_preview(db: Session, user_id: int, batch_id: int):
    batch = (
        db.query(ReimbursementBatch)
        .filter(
            ReimbursementBatch.id == batch_id,
            ReimbursementBatch.user_id == user_id,
        )
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")

    batch_invoices = (
        db.query(BatchInvoice)
        .filter(BatchInvoice.batch_id == batch_id)
        .all()
    )

    if not batch_invoices:
        raise HTTPException(status_code=400, detail="批次中没有发票数据")

    from sqlalchemy import or_

    non_substitute_rows = [
        bi
        for bi in batch_invoices
        if not bi.is_substitute or bi.substitute_for is not None
    ]

    if not non_substitute_rows:
        raise HTTPException(status_code=400, detail="批次中没有发票数据")

    groups: dict[str, float] = {}
    for bi in non_substitute_rows:
        key = None
        value = 0.0

        if bi.source_type == "manual":
            key = bi.expense_item or "其他"
            value = bi.row_amount or 0.0
        elif bi.invoice_id is not None:
            invoice = db.query(Invoice).filter(Invoice.id == bi.invoice_id).first()
            if invoice:
                key = invoice.category or "其他"
                value = invoice.amount or 0.0

        if key:
            groups[key] = round(groups.get(key, 0.0) + value, 2)

    total = round(sum(groups.values()), 2)

    from app.schemas.export import ReimbursementItem, ReimbursementPreviewResponse

    sorted_items = sorted(groups.items(), key=lambda x: x[1], reverse=True)
    items = [
        ReimbursementItem(expense_item=k, amount=v) for k, v in sorted_items
    ]

    return ReimbursementPreviewResponse(
        department=batch.department,
        report_date=batch.report_date.isoformat() if batch.report_date else None,
        reporter=batch.reporter,
        items=items,
        total_amount=total,
        total_amount_cn=amount_to_chinese(total),
    )