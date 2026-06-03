from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReimbursementBatch(Base):
    __tablename__ = "reimbursement_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=True)
    reporter: Mapped[str] = mapped_column(String(50), nullable=False)
    reviewer: Mapped[str] = mapped_column(String(50), nullable=True)
    payee: Mapped[str] = mapped_column(String(50), nullable=True)
    bank_account: Mapped[str] = mapped_column(String(30), nullable=True)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=True)
    report_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class BatchInvoice(Base):
    __tablename__ = "batch_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    invoice_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), default="invoice")
    row_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    row_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    expense_item: Mapped[str] = mapped_column(String(50), nullable=True)
    remark: Mapped[str] = mapped_column(String(500), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, default=1.0)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    advance_amount: Mapped[float] = mapped_column(Float, default=0.0)
    is_substitute: Mapped[bool] = mapped_column(default=False)
    substitute_for: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
