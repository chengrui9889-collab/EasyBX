from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.batch import BatchInvoice, ReimbursementBatch
from app.models.invoice import Invoice
from app.schemas.dashboard import DashboardStatsResponse, RecentBatchItem


def get_dashboard_stats(db: Session, user_id: int) -> DashboardStatsResponse:
    today = date.today()
    first_day_of_month = today.replace(day=1)

    pending_count = (
        db.query(func.count(Invoice.id))
        .filter(
            Invoice.user_id == user_id,
            Invoice.status == "pending",
            Invoice.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )

    monthly_total = (
        db.query(func.coalesce(func.sum(Invoice.amount), 0.0))
        .filter(
            Invoice.user_id == user_id,
            Invoice.status == "confirmed",
            Invoice.deleted_at.is_(None),
            Invoice.invoice_date >= first_day_of_month,
            Invoice.invoice_date <= today,
        )
        .scalar()
        or 0.0
    )

    active_batch_count = (
        db.query(func.count(ReimbursementBatch.id))
        .filter(ReimbursementBatch.user_id == user_id)
        .scalar()
        or 0
    )

    recent_batches_query = (
        db.query(ReimbursementBatch)
        .filter(ReimbursementBatch.user_id == user_id)
        .order_by(ReimbursementBatch.created_at.desc())
        .limit(5)
        .all()
    )

    recent_batches = []
    for batch in recent_batches_query:
        invoice_count = (
            db.query(BatchInvoice)
            .filter(BatchInvoice.batch_id == batch.id)
            .count()
        )
        recent_batches.append(RecentBatchItem(
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
        ))

    return DashboardStatsResponse(
        pending_invoice_count=pending_count,
        monthly_total_amount=round(monthly_total, 2),
        active_batch_count=active_batch_count,
        recent_batches=recent_batches,
    )