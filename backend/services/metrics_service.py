from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.finding import Finding
from backend.models.validation_job import ValidationJob


class MetricsService:
    """Calculates and aggregates verification metrics, time saved, and false positive rates."""

    @staticmethod
    async def get_dashboard_metrics(db: AsyncSession) -> dict[str, Any]:
        # Count total findings
        total_q = await db.execute(select(func.count(Finding.id)))
        total_findings = total_q.scalar() or 0

        # Count by status
        tp_q = await db.execute(select(func.count(Finding.id)).where(Finding.status == "TRUE_POSITIVE"))
        true_positives = tp_q.scalar() or 0

        fp_q = await db.execute(select(func.count(Finding.id)).where(Finding.status == "FALSE_POSITIVE"))
        false_positives = fp_q.scalar() or 0

        review_q = await db.execute(select(func.count(Finding.id)).where(Finding.status == "NEEDS_MANUAL_REVIEW"))
        needs_review = review_q.scalar() or 0

        unverified_q = await db.execute(select(func.count(Finding.id)).where(Finding.status == "UNVERIFIED"))
        unverified = unverified_q.scalar() or 0

        # Severity breakdown
        crit_q = await db.execute(select(func.count(Finding.id)).where(Finding.severity == "Critical"))
        critical_count = crit_q.scalar() or 0

        high_q = await db.execute(select(func.count(Finding.id)).where(Finding.severity == "High"))
        high_count = high_q.scalar() or 0

        med_q = await db.execute(select(func.count(Finding.id)).where(Finding.severity == "Medium"))
        med_count = med_q.scalar() or 0

        low_q = await db.execute(select(func.count(Finding.id)).where(Finding.severity == "Low"))
        low_count = low_q.scalar() or 0

        validated_count = true_positives + false_positives + needs_review
        # Manual verification takes ~10 min (0.167h) per finding
        time_saved_hours = round(validated_count * (10.0 / 60.0), 1)

        fp_rate = round((false_positives / validated_count * 100.0), 1) if validated_count > 0 else 0.0
        tp_rate = round((true_positives / validated_count * 100.0), 1) if validated_count > 0 else 0.0

        return {
            "total_findings": total_findings,
            "validated_findings": validated_count,
            "unverified_findings": unverified,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "needs_review": needs_review,
            "time_saved_hours": time_saved_hours,
            "false_positive_rate": fp_rate,
            "true_positive_rate": tp_rate,
            "severity_counts": {
                "Critical": critical_count,
                "High": high_count,
                "Medium": med_count,
                "Low": low_count
            }
        }


metrics_service = MetricsService()
