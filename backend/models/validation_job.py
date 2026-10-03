from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pydantic import BaseModel, Field
from backend.database.base import Base


class ValidationJob(Base):
    __tablename__ = "validation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)  # PENDING, RUNNING, COMPLETED, FAILED
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    processed_findings: Mapped[int] = mapped_column(Integer, default=0)
    true_positives_count: Mapped[int] = mapped_column(Integer, default=0)
    false_positives_count: Mapped[int] = mapped_column(Integer, default=0)
    needs_review_count: Mapped[int] = mapped_column(Integer, default=0)
    time_saved_hours: Mapped[float] = mapped_column(Float, default=0.0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    results: Mapped[list["ValidationResult"]] = relationship("ValidationResult", back_populates="job", cascade="all, delete-orphan")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("validation_jobs.id"), index=True)
    finding_id: Mapped[int] = mapped_column(Integer, ForeignKey("findings.id"), index=True)
    
    verdict: Mapped[str] = mapped_column(String(30), index=True)  # TRUE_POSITIVE, FALSE_POSITIVE, NEEDS_MANUAL_REVIEW
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    
    # Sub-component scores (0.0 to 1.0 or 0 to 100)
    feasibility_score: Mapped[float] = mapped_column(Float, default=0.5)
    context_score: Mapped[float] = mapped_column(Float, default=0.5)
    evidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    
    exploitation_difficulty: Mapped[str] = mapped_column(String(20), default="MEDIUM")  # EASY, MEDIUM, HARD
    business_impact: Mapped[str] = mapped_column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    false_positive_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["ValidationJob"] = relationship("ValidationJob", back_populates="results")
    finding: Mapped["Finding"] = relationship("Finding", back_populates="validation_results")


# Pydantic Schemas
class ValidationOptions(BaseModel):
    environment_type: str = "Production Web/API"
    llm_provider: Optional[str] = None  # None uses system default
    min_confidence_tp: float = 75.0
    max_confidence_fp: float = 40.0


class ValidationRequest(BaseModel):
    finding_ids: list[int] = Field(default_factory=list, description="IDs of findings to validate. Empty validates all unverified.")
    options: ValidationOptions = Field(default_factory=ValidationOptions)


class ValidationResultResponse(BaseModel):
    id: int
    job_id: int
    finding_id: int
    verdict: str
    confidence_score: float
    reasoning: str
    feasibility_score: float
    context_score: float
    evidence_score: float
    exploitation_difficulty: str
    business_impact: str
    recommended_action: Optional[str] = None
    false_positive_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ValidationJobResponse(BaseModel):
    id: int
    status: str
    total_findings: int
    processed_findings: int
    true_positives_count: int
    false_positives_count: int
    needs_review_count: int
    time_saved_hours: float
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
