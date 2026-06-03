from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SubstituteRelation(Base):
    __tablename__ = "substitute_relations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    substitute_invoice_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target_row_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("batch_invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())