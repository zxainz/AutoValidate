from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.dependencies import get_db
from backend.models.finding import Finding
from backend.models.report import Report, ReportResponse
from backend.services.report_service import report_service
from backend.services.metrics_service import metrics_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=ReportResponse)
async def generate_report_snapshot(
    title: str = Query("Pentest Validation Report"),
    db: AsyncSession = Depends(get_db)
):
    """Generate a point-in-time report snapshot summarizing current validated findings."""
    metrics = await metrics_service.get_dashboard_metrics(db)

    report = Report(
        title=title,
        total_findings=metrics["total_findings"],
        true_positives=metrics["true_positives"],
        false_positives=metrics["false_positives"],
        needs_review=metrics["needs_review"],
        time_saved_hours=metrics["time_saved_hours"]
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportResponse(
        id=report.id,
        title=report.title,
        total_findings=report.total_findings,
        true_positives=report.true_positives,
        false_positives=report.false_positives,
        needs_review=report.needs_review,
        time_saved_hours=report.time_saved_hours,
        created_at=report.created_at,
        formats_available=["html", "pdf", "csv", "json"]
    )


@router.get("", response_model=list[ReportResponse])
async def list_reports(db: AsyncSession = Depends(get_db)):
    """List historical generated reports."""
    res = await db.execute(select(Report).order_by(desc(Report.id)).limit(20))
    reports = res.scalars().all()
    return [
        ReportResponse(
            id=r.id,
            title=r.title,
            total_findings=r.total_findings,
            true_positives=r.true_positives,
            false_positives=r.false_positives,
            needs_review=r.needs_review,
            time_saved_hours=r.time_saved_hours,
            created_at=r.created_at,
            formats_available=["html", "pdf", "csv", "json"]
        )
        for r in reports
    ]


@router.get("/{report_id}/export")
async def export_report(
    report_id: int,
    format: str = Query("html", pattern="^(html|pdf|csv|json)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Export validation report in client-ready format: html, pdf, csv, or json.
    """
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Fetch findings associated with the report
    res = await db.execute(select(Finding).options(selectinload(Finding.validation_results)))
    findings = list(res.scalars().all())

    filename_base = f"autovalidate_report_{report.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    if format == "csv":
        content = report_service.generate_csv(findings)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.csv"'}
        )
    elif format == "json":
        content = report_service.generate_json(report, findings)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.json"'}
        )
    elif format == "html":
        content = report_service.generate_html(report, findings)
        return Response(
            content=content,
            media_type="text/html",
            headers={"Content-Disposition": f'inline; filename="{filename_base}.html"'}
        )
    elif format == "pdf":
        pdf_bytes = report_service.generate_pdf(report, findings)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename_base}.pdf"'}
        )

    raise HTTPException(status_code=400, detail="Invalid format specified")
