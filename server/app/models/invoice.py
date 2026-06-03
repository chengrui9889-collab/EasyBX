from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    invoice_no: Mapped[str] = mapped_column(String(50), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=True)
    vendor: Mapped[str] = mapped_column(String(200), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_original_name: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="processing", index=True)
    buyer_name: Mapped[str] = mapped_column(String(200), nullable=True)
    invoice_type: Mapped[str] = mapped_column(String(100), nullable=True)
    project_name: Mapped[str] = mapped_column(String(200), nullable=True)
    ocr_raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    remark: Mapped[str] = mapped_column(Text, nullable=True)
    train_no: Mapped[str] = mapped_column(String(50), nullable=True)
    departure_station: Mapped[str] = mapped_column(String(100), nullable=True)
    arrival_station: Mapped[str] = mapped_column(String(100), nullable=True)
    departure_location: Mapped[str] = mapped_column(String(200), nullable=True)
    arrival_location: Mapped[str] = mapped_column(String(200), nullable=True)
    flight_no: Mapped[str] = mapped_column(String(50), nullable=True)
    departure_city: Mapped[str] = mapped_column(String(100), nullable=True)
    arrival_city: Mapped[str] = mapped_column(String(100), nullable=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
