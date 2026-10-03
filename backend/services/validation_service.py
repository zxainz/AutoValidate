import asyncio
import logging
from datetime import datetime
from typing import Callable, Optional, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.finding import Finding
from backend.models.validation_job import ValidationJob, ValidationResult, ValidationOptions
from backend.core.ai_engine import ai_engine
from backend.core.scoring import confidence_scorer
from backend.database.session import async_session_maker

logger = logging.getLogger("autovalidate.validation_service")


class ValidationService:
    """Orchestrates asynchronous batch validation jobs and communicates progress."""

    def __init__(self):
        self.subscribers: list[Callable[[dict[str, Any]], Any]] = []

    def register_subscriber(self, callback: Callable[[dict[str, Any]], Any]):
        self.subscribers.append(callback)

    def unregister_subscriber(self, callback: Callable[[dict[str, Any]], Any]):
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    async def broadcast_progress(self, event_data: dict[str, Any]):
        for sub in list(self.subscribers):
            try:
                res = sub(event_data)
                if asyncio.iscoroutine(res):
                    await res
            except Exception as e:
                logger.error(f"Error broadcasting to subscriber: {e}")

    async def run_validation_job(self, job_id: int, options: ValidationOptions):
        """Background task runner for validation jobs."""
        async with async_session_maker() as db:
            job = await db.get(ValidationJob, job_id)
            if not job:
                logger.error(f"Job {job_id} not found.")
                return

            job.status = "RUNNING"
            await db.commit()
            await db.refresh(job)

            # Query findings to process
            stmt = select(Finding)
            if job.total_findings > 0:
                # If specific findings were queued
                res = await db.execute(stmt.where(Finding.status == "UNVERIFIED"))
                findings_to_process = list(res.scalars().all())
            else:
                res = await db.execute(stmt)
                findings_to_process = list(res.scalars().all())

            job.total_findings = len(findings_to_process)
            await db.commit()

            # Strict check: Live API key must be configured
            api_key = (ai_engine.api_key or settings.ZAI_API_KEY).strip()
            if not api_key:
                job.status = "FAILED"
                job.error_message = "Real GLM-5.3 API key required. Offline simulation is disabled."
                await db.commit()
                await self.broadcast_progress({
                    "type": "error",
                    "job_id": job.id,
                    "error": job.error_message
                })
                return

            processed = 0
            tp_count = 0
            fp_count = 0
            review_count = 0

            for finding in findings_to_process:
                try:
                    result_dict = await ai_engine.validate_finding(
                        finding,
                        environment_type=options.environment_type
                    )

                    # Create ValidationResult record
                    val_res = ValidationResult(
                        job_id=job.id,
                        finding_id=finding.id,
                        verdict=result_dict["verdict"],
                        confidence_score=result_dict["confidence_score"],
                        reasoning=result_dict["reasoning"],
                        feasibility_score=result_dict["feasibility_score"],
                        context_score=result_dict["context_score"],
                        evidence_score=result_dict["evidence_score"],
                        exploitation_difficulty=result_dict["exploitation_difficulty"],
                        business_impact=result_dict["business_impact"],
                        recommended_action=result_dict["recommended_action"],
                        false_positive_reason=result_dict["false_positive_reason"],
                    )
                    db.add(val_res)

                    # Update finding status
                    finding.status = result_dict["verdict"]
                    finding.confidence_score = result_dict["confidence_score"]
                    finding.updated_at = datetime.utcnow()

                    processed += 1
                    if result_dict["verdict"] == "TRUE_POSITIVE":
                        tp_count += 1
                    elif result_dict["verdict"] == "FALSE_POSITIVE":
                        fp_count += 1
                    else:
                        review_count += 1

                    job.processed_findings = processed
                    job.true_positives_count = tp_count
                    job.false_positives_count = fp_count
                    job.needs_review_count = review_count
                    job.time_saved_hours = round(processed * (10.0 / 60.0), 1)

                    await db.commit()

                    # Notify subscribers / WebSockets
                    await self.broadcast_progress({
                        "type": "progress",
                        "job_id": job.id,
                        "finding_id": finding.id,
                        "title": finding.title,
                        "verdict": result_dict["verdict"],
                        "confidence_score": result_dict["confidence_score"],
                        "processed": processed,
                        "total": job.total_findings,
                        "percent": round((processed / job.total_findings) * 100, 1) if job.total_findings > 0 else 100
                    })

                    # Small cooperative yield
                    await asyncio.sleep(0.05)

                except Exception as e:
                    err_msg = getattr(e, 'detail', str(e))
                    logger.error(f"Error validating finding {finding.id} via GLM-5.3 API: {err_msg}")
                    job.status = "FAILED"
                    job.error_message = f"GLM-5.3 API Error: {err_msg}"
                    await db.commit()
                    await self.broadcast_progress({
                        "type": "error",
                        "job_id": job.id,
                        "error": job.error_message
                    })
                    return

            job.status = "COMPLETED"
            job.completed_at = datetime.utcnow()
            await db.commit()

            await self.broadcast_progress({
                "type": "completed",
                "job_id": job.id,
                "total": job.total_findings,
                "true_positives": tp_count,
                "false_positives": fp_count,
                "needs_review": review_count,
                "time_saved_hours": job.time_saved_hours
            })


validation_service = ValidationService()
