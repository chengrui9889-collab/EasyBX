from datetime import date, datetime

from pydantic import BaseModel, Field


class InvoiceResponse(BaseModel):
    id: int
    user_id: int
    invoice_no: str | None
    amount: float | None
    invoice_date: date | None
    category: str | None
    vendor: str | None
    file_path: str
    file_original_name: str | None
    status: str
    buyer_name: str | None
    invoice_type: str | None
    project_name: str | None
    ocr_raw_data: dict | None
    remark: str | None
    train_no: str | None
    departure_station: str | None
    arrival_station: str | None
    departure_location: str | None
    arrival_location: str | None
    flight_no: str | None
    departure_city: str | None
    arrival_city: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpdateInvoiceRequest(BaseModel):
    invoice_no: str | None = Field(default=None, max_length=50)
    amount: float | None = None
    invoice_date: date | None = None
    category: str | None = Field(default=None, max_length=50)
    vendor: str | None = Field(default=None, max_length=200)
    remark: str | None = Field(default=None, max_length=500)
    buyer_name: str | None = Field(default=None, max_length=200)
    invoice_type: str | None = Field(default=None, max_length=100)
    project_name: str | None = Field(default=None, max_length=200)
    train_no: str | None = Field(default=None, max_length=50)
    departure_station: str | None = Field(default=None, max_length=100)
    arrival_station: str | None = Field(default=None, max_length=100)
    departure_location: str | None = Field(default=None, max_length=200)
    arrival_location: str | None = Field(default=None, max_length=200)
    flight_no: str | None = Field(default=None, max_length=50)
    departure_city: str | None = Field(default=None, max_length=100)
    arrival_city: str | None = Field(default=None, max_length=100)


class UploadFileResult(BaseModel):
    filename: str
    success: bool
    invoice_id: int | None = None
    error: str | None = None


class UploadResponse(BaseModel):
    results: list[UploadFileResult]
    skipped_count: int = 0


class InvoiceListResponse(BaseModel):
    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DeleteResponse(BaseModel):
    deleted: bool
    type: str
    restorable_until: datetime | None = None
