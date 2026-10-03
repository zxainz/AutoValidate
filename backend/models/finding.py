import json
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel, Field
from backend.database.base import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scan_source: Mapped[str] = mapped_column(String(50), index=True)  # nessus, qualys, burp, generic
    scanner_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)  # e.g. pluginID, QID
    title: Mapped[str] = mapped_column(String(300), index=True)
    severity: Mapped[str] = mapped_column(String(20), default="Medium", index=True)  # Critical, High, Medium, Low, Info
    cve_list_json: Mapped[str] = mapped_column(Text, default="[]")  # JSON string of CVEs
    cvss_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_host: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    target_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(20), default="tcp")
    vuln_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Validation status: 'UNVERIFIED', 'TRUE_POSITIVE', 'FALSE_POSITIVE', 'NEEDS_MANUAL_REVIEW'
    status: Mapped[str] = mapped_column(String(30), default="UNVERIFIED", index=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to latest validation result
    validation_results: Mapped[list["ValidationResult"]] = relationship("ValidationResult", back_populates="finding", cascade="all, delete-orphan")

    @property
    def cves(self) -> list[str]:
        try:
            return json.loads(self.cve_list_json)
        except Exception:
            return []

    @cves.setter
    def cves(self, val: list[str]):
        self.cve_list_json = json.dumps(val or [])


# Pydantic Schemas
class FindingBase(BaseModel):
    scan_source: str
    scanner_id: Optional[str] = None
    title: str
    severity: str = "Medium"
    cve_list: list[str] = Field(default_factory=list)
    cvss_score: Optional[float] = None
    target_host: Optional[str] = None
    target_port: Optional[int] = None
    target_url: Optional[str] = None
    protocol: Optional[str] = "tcp"
    vuln_type: Optional[str] = None
    description: Optional[str] = None
    solution: Optional[str] = None
    raw_evidence: Optional[str] = None
    raw_payload: Optional[str] = None


class FindingCreate(FindingBase):
    pass


class FindingResponse(FindingBase):
    id: int
    status: str
    confidence_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    latest_result: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}
