from datetime import date, datetime

from pydantic import BaseModel, Field


class CreateBatchRequest(BaseModel):
    department: str | None = Field(default=None, max_length=100)
    period_start: date | None = None
    period_end: date | None = None
    report_date: date | None = None
    reporter: str | None = Field(default=None, max_length=50)
    reviewer: str | None = Field(default=None, max_length=50)
    payee: str | None = Field(default=None, max_length=50)
    bank_account: str | None = Field(default=None, max_length=30)
    bank_name: str | None = Field(default=None, max_length=100)


class UpdateBatchRequest(BaseModel):
    department: str | None = Field(default=None, max_length=100)
    period_start: date | None = None
    period_end: date | None = None
    report_date: date | None = None
    reporter: str | None = Field(default=None, max_length=50)
    reviewer: str | None = Field(default=None, max_length=50)
    payee: str | None = Field(default=None, max_length=50)
    bank_account: str | None = Field(default=None, max_length=30)
    bank_name: str | None = Field(default=None, max_length=100)


class AddInvoicesRequest(BaseModel):
    invoice_ids: list[int] = Field(..., max_length=50)


class BatchInvoiceResponse(BaseModel):
    id: int
    invoice_id: int | None
    source_type: str = "invoice"
    row_date: date | None = None
    row_amount: float | None = None
    expense_item: str | None
    remark: str | None
    quantity: float
    unit_price: float
    advance_amount: float
    is_substitute: bool
    substitute_for: str | None

    model_config = {"from_attributes": True}


class BatchResponse(BaseModel):
    id: int
    department: str
    period_start: date | None
    period_end: date | None
    report_date: date | None
    reporter: str
    reviewer: str | None
    payee: str | None
    bank_account: str | None
    bank_name: str | None
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BatchDetailResponse(BatchResponse):
    ledger_rows: list["LedgerRowResponse"] = []


class BatchListItem(BaseModel):
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
    updated_at: datetime

    model_config = {"from_attributes": True}


class BatchListResponse(BaseModel):
    items: list[BatchListItem]
    total: int


class LedgerRowResponse(BaseModel):
    id: int
    invoice_id: int | None = None
    source_type: str = "invoice"
    row_date: date | None = None
    row_amount: float | None = None
    invoice_date: date | None = None
    category: str | None = None
    invoice_type: str | None = None
    amount: float | None = None
    quantity: float
    unit_price: float
    advance_amount: float
    remark: str | None = None
    expense_item: str | None = None
    invoice_no: str | None = None
    vendor: str | None = None
    is_substitute: bool
    substitute_for: str | None = None

    model_config = {"from_attributes": True}


class AvailableInvoiceItem(BaseModel):
    id: int
    invoice_no: str | None
    amount: float | None
    invoice_date: date | None
    category: str | None
    vendor: str | None
    file_path: str
    file_original_name: str | None

    model_config = {"from_attributes": True}


class AvailableInvoiceListResponse(BaseModel):
    items: list[AvailableInvoiceItem]
    total: int
    page: int
    page_size: int


class UpdateBatchInvoiceRequest(BaseModel):
    quantity: float | None = None
    advance_amount: float | None = None
    remark: str | None = Field(default=None, max_length=500)


class BatchInvoiceRequest(BaseModel):
    invoice_id: int
    expense_item: str | None = Field(default=None, max_length=50)
    remark: str | None = Field(default=None, max_length=500)
    is_substitute: bool = False
    substitute_for: str | None = Field(default=None, max_length=500)


class DeleteBatchResponse(BaseModel):
    deleted: bool
    released_invoice_count: int


class ManualRowCreateRequest(BaseModel):
    row_date: date | None = None
    expense_item: str = Field(..., max_length=50)
    row_amount: float = Field(..., gt=0)
    quantity: float = 1.0
    advance_amount: float | None = None
    remark: str | None = None


class ManualRowResponse(BaseModel):
    id: int
    batch_id: int
    source_type: str = "manual"
    row_date: date | None = None
    expense_item: str | None = None
    row_amount: float | None = None
    quantity: float
    unit_price: float
    advance_amount: float
    remark: str | None = None
    is_substitute: bool = False
    substitute_for: str | None = None

    model_config = {"from_attributes": True}


class ManualRowUpdateRequest(BaseModel):
    row_date: date | None = None
    expense_item: str | None = Field(default=None, max_length=50)
    row_amount: float | None = None
    quantity: float | None = None
    advance_amount: float | None = None
    remark: str | None = None


class ManualRowDeleteResponse(BaseModel):
    deleted: bool
    released_substitute_count: int = 0


class SubstituteInvoiceItem(BaseModel):
    id: int
    invoice_no: str
    amount: float
    invoice_date: date | None = None
    category: str | None = None
    vendor: str | None = None
    file_path: str | None = None
    file_original_name: str | None = None
    used_as_substitute: float = 0.0
    remaining_amount: float = 0.0

    model_config = {"from_attributes": True}


class SubstituteInvoiceListResponse(BaseModel):
    items: list["SubstituteInvoiceItem"]
    total: int
    page: int = 1
    page_size: int = 50


class SubstituteCreateRequest(BaseModel):
    mode: str = Field(
        ...,
        pattern=r"^(one_to_one|one_to_many|many_to_one)$",
    )
    substitute_invoice_ids: list[int] = Field(..., min_length=1, max_length=20)
    target_row_ids: list[int] = Field(..., min_length=1, max_length=10)


class SubstituteRelationResponse(BaseModel):
    id: int
    batch_id: int
    substitute_invoice_id: int
    target_row_id: int
    mode: str
    created_at: datetime | None = None
    substitute_invoice: "SubstituteInvoiceItem | None" = None
    target_row: "ManualRowResponse | None" = None

    model_config = {"from_attributes": True}


class SubstituteRelationListResponse(BaseModel):
    relations: list["SubstituteRelationResponse"]


class SubstituteCreatedResponse(BaseModel):
    relations: list["SubstituteRelationResponse"]
    updated_target_rows: list["ManualRowResponse"]