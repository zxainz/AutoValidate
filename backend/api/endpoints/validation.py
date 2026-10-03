import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.dependencies import get_db
from backend.core.config import settings
from backend.models.finding import Finding
from backend.models.validation_job import ValidationJob, ValidationRequest, ValidationJobResponse, ValidationOptions
from backend.services.validation_service import validation_service
from backend.core.ai_engine import ai_engine

router = APIRouter(prefix="/validation", tags=["validation"])


@router.post("/start")
async def start_validation(
    request: ValidationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Launch asynchronous AI validation across unverified findings or specified IDs.
    """
    if request.finding_ids:
        total = len(request.finding_ids)
    else:
        # Count unverified
        res = await db.execute(select(Finding).where(Finding.status == "UNVERIFIED"))
        unverified = res.scalars().all()
        total = len(unverified)
        if total == 0:
            # If all are already verified, check total findings
            all_res = await db.execute(select(Finding))
            all_findings = all_res.scalars().all()
            total = len(all_findings)

    # Strict check: Real GLM-5.3 API key required
    api_key = (ai_engine.api_key or settings.ZAI_API_KEY).strip()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Real GLM-5.3 API key required. Offline simulation is disabled."
        )

    if total == 0:
        raise HTTPException(status_code=400, detail="No findings available to validate. Please upload a scanner file first.")

    # Create job record
    job = ValidationJob(
        status="PENDING",
        total_findings=total,
        processed_findings=0
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Launch background validation
    background_tasks.add_task(validation_service.run_validation_job, job.id, request.options)

    # Estimate time (approx 1.5 seconds per finding with parallel/batched reasoning)
    est_seconds = max(5, int(total * 1.5))

    return {
        "job_id": job.id,
        "status": "started",
        "total_findings": total,
        "estimated_time_seconds": est_seconds,
        "estimated_time_human": f"{est_seconds} seconds" if est_seconds < 60 else f"{round(est_seconds / 60, 1)} minutes"
    }


@router.get("/jobs/{job_id}", response_model=ValidationJobResponse)
async def get_job_status(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get real-time status of a validation job."""
    job = await db.get(ValidationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs", response_model=list[ValidationJobResponse])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    """List recent validation jobs."""
    res = await db.execute(select(ValidationJob).order_by(desc(ValidationJob.id)).limit(20))
    return res.scalars().all()


@router.post("/single/{finding_id}")
async def validate_single_finding(
    finding_id: int,
    environment_type: str = Query("Production Web/API"),
    db: AsyncSession = Depends(get_db)
):
    """Interactively validate a single finding on-demand using real GLM-5.3 API."""
    api_key = (ai_engine.api_key or settings.ZAI_API_KEY).strip()
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Real GLM-5.3 API key required. Offline simulation is disabled."
        )

    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    result = await ai_engine.validate_finding(
        finding,
        environment_type=environment_type
    )

    finding.status = result["verdict"]
    finding.confidence_score = result["confidence_score"]
    await db.commit()
    await db.refresh(finding)

    return {
        "finding_id": finding.id,
        "title": finding.title,
        **result
    }
