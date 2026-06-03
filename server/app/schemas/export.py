from typing import Literal

from pydantic import BaseModel


class PdfExportRequest(BaseModel):
    invoice_ids: list[int]
    layouts: dict[str, Literal["portrait", "landscape"]] = {}


class BatchPdfExportRequest(BaseModel):
    layouts: dict[str, Literal["portrait", "landscape"]] = {}


class ReimbursementItem(BaseModel):
    expense_item: str
    amount: float


class ReimbursementPreviewResponse(BaseModel):
    department: str
    report_date: str | None = None
    reporter: str
    items: list[ReimbursementItem]
    total_amount: float
    total_amount_cn: str
