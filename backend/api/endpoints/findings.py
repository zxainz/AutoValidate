import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy import select, delete, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.dependencies import get_db
from backend.models.finding import Finding, FindingResponse, FindingCreate
from backend.models.validation_job import ValidationResult
from backend.parsers import PARSER_MAP, detect_and_get_parser

router = APIRouter(prefix="/findings", tags=["findings"])


@router.post("/upload")
async def upload_scanner_file(
    file: UploadFile = File(...),
    scanner_type: str = Form("auto"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and parse scanner output files (Nessus, Qualys, Burp Suite, Generic JSON).
    Supports automatic format detection.
    """
    try:
        content_bytes = await file.read()
        sample_str = content_bytes[:4000].decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {str(e)}")

    # Select parser
    if scanner_type == "auto" or not scanner_type:
        parser = detect_and_get_parser(file.filename or "", sample_str)
    elif scanner_type in PARSER_MAP:
        parser = PARSER_MAP[scanner_type]()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported scanner type: {scanner_type}")

    try:
        parsed_items: list[FindingCreate] = parser.parse(content_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Parser error while processing file: {str(e)}")

    if not parsed_items:
        return {
            "filename": file.filename or "unknown",
            "scanner_detected": parser.__class__.__name__.replace("Parser", "").lower(),
            "total_imported": 0,
            "sample_findings": [],
            "message": "No security findings could be identified in the uploaded file."
        }

    # Save findings into DB
    created_findings = []
    for item in parsed_items:
        db_finding = Finding(
            scan_source=item.scan_source,
            scanner_id=item.scanner_id,
            title=item.title,
            severity=item.severity,
            cve_list_json=json.dumps(item.cve_list),
            cvss_score=item.cvss_score,
            target_host=item.target_host,
            target_port=item.target_port,
            target_url=item.target_url,
            protocol=item.protocol or "tcp",
            vuln_type=item.vuln_type,
            description=item.description,
            solution=item.solution,
            raw_evidence=item.raw_evidence,
            raw_payload=item.raw_payload,
            status="UNVERIFIED",
            confidence_score=None
        )
        db.add(db_finding)
        created_findings.append(db_finding)

    await db.commit()
    for f in created_findings:
        await db.refresh(f)

    return {
        "filename": file.filename,
        "scanner_detected": parser.__class__.__name__.replace("Parser", "").lower(),
        "total_imported": len(created_findings),
        "sample_findings": [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity,
                "target": f.target_url or f.target_host
            }
            for f in created_findings[:5]
        ]
    }


@router.get("")
async def list_findings(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    scan_source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List findings with filtering, search, and pagination."""
    stmt = select(Finding).options(selectinload(Finding.validation_results)).order_by(desc(Finding.id))

    if status:
        stmt = stmt.where(Finding.status == status.upper())
    if severity:
        stmt = stmt.where(Finding.severity == severity.capitalize())
    if scan_source:
        stmt = stmt.where(Finding.scan_source == scan_source.lower())
    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            (Finding.title.ilike(search_filter))
            | (Finding.description.ilike(search_filter))
            | (Finding.target_host.ilike(search_filter))
        )

    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    findings = res.scalars().all()

    output = []
    for f in findings:
        latest = f.validation_results[-1] if f.validation_results else None
        output.append({
            "id": f.id,
            "scan_source": f.scan_source,
            "scanner_id": f.scanner_id,
            "title": f.title,
            "severity": f.severity,
            "cve_list": f.cves,
            "cvss_score": f.cvss_score,
            "target_host": f.target_host,
            "target_port": f.target_port,
            "target_url": f.target_url,
            "protocol": f.protocol,
            "vuln_type": f.vuln_type,
            "description": f.description,
            "solution": f.solution,
            "raw_evidence": f.raw_evidence,
            "status": f.status,
            "confidence_score": f.confidence_score,
            "created_at": f.created_at,
            "latest_result": {
                "verdict": latest.verdict,
                "confidence_score": latest.confidence_score,
                "reasoning": latest.reasoning,
                "feasibility_score": latest.feasibility_score,
                "context_score": latest.context_score,
                "evidence_score": latest.evidence_score,
                "exploitation_difficulty": latest.exploitation_difficulty,
                "business_impact": latest.business_impact,
                "recommended_action": latest.recommended_action,
                "false_positive_reason": latest.false_positive_reason,
            } if latest else None
        })

    return output


@router.get("/{finding_id}")
async def get_finding(finding_id: int, db: AsyncSession = Depends(get_db)):
    """Get finding details including full evidence, solution, and validation reasoning."""
    stmt = select(Finding).options(selectinload(Finding.validation_results)).where(Finding.id == finding_id)
    res = await db.execute(stmt)
    f = res.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")

    latest = f.validation_results[-1] if f.validation_results else None
    return {
        "id": f.id,
        "scan_source": f.scan_source,
        "scanner_id": f.scanner_id,
        "title": f.title,
        "severity": f.severity,
        "cve_list": f.cves,
        "cvss_score": f.cvss_score,
        "target_host": f.target_host,
        "target_port": f.target_port,
        "target_url": f.target_url,
        "protocol": f.protocol,
        "vuln_type": f.vuln_type,
        "description": f.description,
        "solution": f.solution,
        "raw_evidence": f.raw_evidence,
        "raw_payload": f.raw_payload,
        "status": f.status,
        "confidence_score": f.confidence_score,
        "created_at": f.created_at,
        "validation_history": [
            {
                "id": vr.id,
                "job_id": vr.job_id,
                "verdict": vr.verdict,
                "confidence_score": vr.confidence_score,
                "reasoning": vr.reasoning,
                "feasibility_score": vr.feasibility_score,
                "context_score": vr.context_score,
                "evidence_score": vr.evidence_score,
                "exploitation_difficulty": vr.exploitation_difficulty,
                "business_impact": vr.business_impact,
                "recommended_action": vr.recommended_action,
                "false_positive_reason": vr.false_positive_reason,
                "created_at": vr.created_at
            }
            for vr in f.validation_results
        ]
    }


@router.delete("")
async def clear_all_findings(db: AsyncSession = Depends(get_db)):
    """Clear all findings from the database to start a fresh assessment."""
    await db.execute(delete(ValidationResult))
    await db.execute(delete(Finding))
    await db.commit()
    return {"message": "All findings cleared successfully."}


@router.delete("/{finding_id}")
async def delete_finding(finding_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a single finding."""
    f = await db.get(Finding, finding_id)
    if not f:
        raise HTTPException(status_code=404, detail="Finding not found")
    await db.delete(f)
    await db.commit()
    return {"message": f"Finding {finding_id} deleted."}
