from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(50), nullable=True)
    default_department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_reporter: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_payee: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_bank_account: Mapped[str | None] = mapped_column(String(30), nullable=True)
    default_bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
