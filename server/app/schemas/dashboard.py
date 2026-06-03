from datetime import date, datetime

from pydantic import BaseModel


class RecentBatchItem(BaseModel):
    id: int
    department: str
    period_start: date | None = None
    period_end: date | None = None
    report_date: date | None = None
    reporter: str
    total_amount: float
    status: str
    invoice_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardStatsResponse(BaseModel):
    pending_invoice_count: int
    monthly_total_amount: float
    active_batch_count: int
    recent_batches: list[RecentBatchItem]