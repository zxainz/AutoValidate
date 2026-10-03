from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Integer, Float, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel
from backend.database.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), default="Pentest Validation Report")
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    true_positives: Mapped[int] = mapped_column(Integer, default=0)
    false_positives: Mapped[int] = mapped_column(Integer, default=0)
    needs_review: Mapped[int] = mapped_column(Integer, default=0)
    time_saved_hours: Mapped[float] = mapped_column(Float, default=0.0)
    html_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    csv_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    json_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ReportResponse(BaseModel):
    id: int
    title: str
    total_findings: int
    true_positives: int
    false_positives: int
    needs_review: int
    time_saved_hours: float
    created_at: datetime
    formats_available: list[str] = []

    model_config = {"from_attributes": True}
