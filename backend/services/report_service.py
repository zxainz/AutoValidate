import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from backend.core.config import settings
from backend.models.finding import Finding
from backend.models.report import Report


class ReportService:
    """Multi-format validation report generator (HTML, CSV, JSON, PDF)."""

    @staticmethod
    def generate_csv(findings: list[Finding]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Finding ID", "Title", "Severity", "Scanner", "Scanner ID", "Target Host",
            "Target Port", "Target URL", "CVEs", "CVSS", "Verdict", "Confidence Score",
            "Reasoning", "Remediation", "False Positive Reason"
        ])

        for f in findings:
            latest = f.validation_results[-1] if f.validation_results else None
            writer.writerow([
                f.id,
                f.title,
                f.severity,
                f.scan_source,
                f.scanner_id or "",
                f.target_host or "",
                f.target_port or "",
                f.target_url or "",
                ", ".join(f.cves),
                f.cvss_score or "",
                latest.verdict if latest else f.status,
                f"{latest.confidence_score}%" if latest else (f"{f.confidence_score}%" if f.confidence_score else ""),
                latest.reasoning if latest else "",
                (latest.recommended_action if latest else None) or f.solution or "",
                latest.false_positive_reason if latest else ""
            ])

        return output.getvalue()

    @staticmethod
    def generate_json(report: Report, findings: list[Finding]) -> str:
        data = {
            "report_id": report.id,
            "title": report.title,
            "generated_at": report.created_at.isoformat(),
            "summary": {
                "total_findings": report.total_findings,
                "true_positives": report.true_positives,
                "false_positives": report.false_positives,
                "needs_review": report.needs_review,
                "time_saved_hours": report.time_saved_hours,
                "false_positive_elimination_rate": (
                    f"{round((report.false_positives / report.total_findings * 100), 1)}%"
                    if report.total_findings > 0 else "0%"
                )
            },
            "findings": [
                {
                    "id": f.id,
                    "title": f.title,
                    "severity": f.severity,
                    "scanner": f.scan_source,
                    "scanner_id": f.scanner_id,
                    "target_host": f.target_host,
                    "target_port": f.target_port,
                    "target_url": f.target_url,
                    "cves": f.cves,
                    "cvss_score": f.cvss_score,
                    "verdict": f.validation_results[-1].verdict if f.validation_results else f.status,
                    "confidence_score": f.validation_results[-1].confidence_score if f.validation_results else f.confidence_score,
                    "reasoning": f.validation_results[-1].reasoning if f.validation_results else "",
                    "recommended_action": f.validation_results[-1].recommended_action if f.validation_results else f.solution,
                    "false_positive_reason": f.validation_results[-1].false_positive_reason if f.validation_results else None,
                }
                for f in findings
            ]
        }
        return json.dumps(data, indent=2)

    @staticmethod
    def generate_html(report: Report, findings: list[Finding]) -> str:
        verified_tps = [f for f in findings if (f.validation_results and f.validation_results[-1].verdict == "TRUE_POSITIVE") or f.status == "TRUE_POSITIVE"]
        filtered_fps = [f for f in findings if (f.validation_results and f.validation_results[-1].verdict == "FALSE_POSITIVE") or f.status == "FALSE_POSITIVE"]
        reviews = [f for f in findings if (f.validation_results and f.validation_results[-1].verdict == "NEEDS_MANUAL_REVIEW") or f.status == "NEEDS_MANUAL_REVIEW"]

        fp_rate = round((report.false_positives / report.total_findings * 100), 1) if report.total_findings > 0 else 0

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{report.title} - AutoValidate Pro</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px; }}
    .container {{ max-width: 1000px; margin: 0 auto; background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); }}
    .header {{ border-bottom: 2px solid #334155; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }}
    .title {{ font-size: 28px; font-weight: 700; color: #38bdf8; margin: 0; }}
    .meta {{ font-size: 13px; color: #94a3b8; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
    .kpi-card {{ background: #0f172a; border: 1px solid #334155; padding: 20px; border-radius: 8px; text-align: center; }}
    .kpi-val {{ font-size: 32px; font-weight: 800; }}
    .kpi-label {{ font-size: 13px; color: #94a3b8; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; text-transform: uppercase; }}
    .badge-critical {{ background: #ef444422; color: #f87171; border: 1px solid #ef4444; }}
    .badge-high {{ background: #f9731622; color: #fb923c; border: 1px solid #f97316; }}
    .badge-medium {{ background: #f59e0b22; color: #fbbf24; border: 1px solid #f59e0b; }}
    .badge-low {{ background: #3b82f622; color: #60a5fa; border: 1px solid #3b82f6; }}
    .badge-tp {{ background: #10b98122; color: #34d399; border: 1px solid #10b981; }}
    .badge-fp {{ background: #ef444422; color: #f87171; border: 1px solid #ef4444; }}
    .badge-rev {{ background: #f59e0b22; color: #fbbf24; border: 1px solid #f59e0b; }}
    h2 {{ font-size: 20px; border-left: 4px solid #38bdf8; padding-left: 12px; margin-top: 40px; margin-bottom: 20px; }}
    .finding-card {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
    .finding-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }}
    .finding-title {{ font-size: 17px; font-weight: 600; color: #f1f5f9; }}
    .reasoning-box {{ background: #1e293b; border-left: 3px solid #10b981; padding: 12px 16px; border-radius: 4px; font-size: 14px; line-height: 1.5; color: #cbd5e1; margin: 12px 0; }}
    .fp-box {{ background: #1e293b; border-left: 3px solid #ef4444; padding: 12px 16px; border-radius: 4px; font-size: 14px; line-height: 1.5; color: #cbd5e1; margin: 12px 0; }}
    .recommendation {{ background: #1e293b; border-left: 3px solid #38bdf8; padding: 12px 16px; border-radius: 4px; font-size: 14px; color: #cbd5e1; }}
    .evidence-block {{ font-family: monospace; background: #090d16; padding: 10px; border-radius: 4px; font-size: 12px; color: #94a3b8; overflow-x: auto; max-height: 150px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1 class="title">{report.title}</h1>
        <div class="meta">Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')} | AutoValidate Pro v1.0</div>
      </div>
      <div>
        <span class="badge badge-tp">AI Validated</span>
      </div>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-val" style="color: #38bdf8;">{report.total_findings}</div>
        <div class="kpi-label">Total Ingested</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val" style="color: #34d399;">{report.true_positives}</div>
        <div class="kpi-label">True Positives</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val" style="color: #f87171;">{report.false_positives}</div>
        <div class="kpi-label">Filtered False Positives ({fp_rate}%)</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-val" style="color: #a78bfa;">{report.time_saved_hours}h</div>
        <div class="kpi-label">Triage Time Saved</div>
      </div>
    </div>

    <h2>Verified True Positives (Deliver to Client)</h2>
"""
        if not verified_tps:
            html += "<p style='color: #94a3b8;'>No confirmed true positives found.</p>"
        else:
            for f in verified_tps:
                res = f.validation_results[-1] if f.validation_results else None
                conf = res.confidence_score if res else (f.confidence_score or 0)
                reason = res.reasoning if res else "Verified finding."
                rec = (res.recommended_action if res else None) or f.solution or "Apply standard remediation."
                sev_class = f"badge-{f.severity.lower()}" if f.severity.lower() in ["critical", "high", "medium", "low"] else "badge-medium"
                
                html += f"""
    <div class="finding-card">
      <div class="finding-header">
        <div>
          <span class="badge {sev_class}">{f.severity}</span>
          <span class="finding-title" style="margin-left: 8px;">{f.title}</span>
          <div class="meta" style="margin-top: 4px;">Target: {f.target_url or f.target_host} | Source: {f.scan_source.upper()} ({f.scanner_id or 'N/A'}) | CVE: {', '.join(f.cves) or 'None'}</div>
        </div>
        <span class="badge badge-tp">{conf}% Confidence</span>
      </div>
      <div class="reasoning-box"><strong>Validation Assessment:</strong> {reason}</div>
      <div class="recommendation"><strong>Remediation:</strong> {rec}</div>
    </div>
"""

        html += f"""
    <h2>Eliminated False Positives (Excluded from Client Report)</h2>
"""
        if not filtered_fps:
            html += "<p style='color: #94a3b8;'>No false positives detected.</p>"
        else:
            for f in filtered_fps:
                res = f.validation_results[-1] if f.validation_results else None
                fp_reason = (res.false_positive_reason if res else None) or "Flagged as non-exploitable by AI reasoning."
                sev_class = f"badge-{f.severity.lower()}" if f.severity.lower() in ["critical", "high", "medium", "low"] else "badge-medium"

                html += f"""
    <div class="finding-card" style="border-color: #450a0a;">
      <div class="finding-header">
        <div>
          <span class="badge {sev_class}">{f.severity}</span>
          <span class="finding-title" style="margin-left: 8px; text-decoration: line-through; color: #94a3b8;">{f.title}</span>
          <div class="meta" style="margin-top: 4px;">Target: {f.target_url or f.target_host} | Source: {f.scan_source.upper()}</div>
        </div>
        <span class="badge badge-fp">False Positive</span>
      </div>
      <div class="fp-box"><strong>Elimination Justification:</strong> {fp_reason}</div>
    </div>
"""

        html += """
  </div>
</body>
</html>
"""
        return html

    @staticmethod
    def generate_pdf(report: Report, findings: list[Finding]) -> bytes:
        """Generates a professional PDF document using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0284c7'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=15
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=14,
            spaceAfter=8
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        callout_style = ParagraphStyle(
            'Callout',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#0f766e'),
            backColor=colors.HexColor('#f0fdfa'),
            borderColor=colors.HexColor('#14b8a6'),
            borderWidth=1,
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=6
        )

        elements = []
        elements.append(Paragraph(report.title, title_style))
        elements.append(Paragraph(
            f"Generated: {report.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')} | AutoValidate Pro AI Engine",
            subtitle_style
        ))

        # KPI Summary Table
        kpi_data = [
            ["Total Findings Ingested", "True Positives", "False Positives Eliminated", "Triage Time Saved"],
            [str(report.total_findings), str(report.true_positives), str(report.false_positives), f"{report.time_saved_hours} hrs"]
        ]
        kpi_table = Table(kpi_data, colWidths=[130, 130, 140, 140])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#15803d')),
            ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#b91c1c')),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 15))

        # True Positives Section
        elements.append(Paragraph("Verified True Positives (Validated Findings)", h2_style))
        tps = [f for f in findings if (f.validation_results and f.validation_results[-1].verdict == "TRUE_POSITIVE") or f.status == "TRUE_POSITIVE"]
        if not tps:
            elements.append(Paragraph("No verified true positives recorded.", body_style))
        else:
            for f in tps:
                res = f.validation_results[-1] if f.validation_results else None
                conf = res.confidence_score if res else (f.confidence_score or 0)
                reason = res.reasoning if res else "Verified finding."
                rec = (res.recommended_action if res else None) or f.solution or "Verify and apply security updates."

                card_content = [
                    Paragraph(f"<b>[{f.severity}] {f.title}</b> — Confidence: {conf}%", body_style),
                    Paragraph(f"Target: {f.target_url or f.target_host}:{f.target_port or ''} | Scanner: {f.scan_source.upper()} | CVE: {', '.join(f.cves) or 'None'}", subtitle_style),
                    Paragraph(f"<b>Validation Reasoning:</b> {reason}", callout_style),
                    Paragraph(f"<b>Remediation:</b> {rec}", body_style),
                    Spacer(1, 8)
                ]
                elements.append(KeepTogether(card_content))

        elements.append(Spacer(1, 10))
        # False Positives Section
        elements.append(Paragraph("Filtered False Positives (Eliminated from Report)", h2_style))
        fps = [f for f in findings if (f.validation_results and f.validation_results[-1].verdict == "FALSE_POSITIVE") or f.status == "FALSE_POSITIVE"]
        if not fps:
            elements.append(Paragraph("No false positives detected.", body_style))
        else:
            for f in fps:
                res = f.validation_results[-1] if f.validation_results else None
                fp_reason = (res.false_positive_reason if res else None) or "Flagged as non-exploitable by AI analysis."
                card_content = [
                    Paragraph(f"<b>[{f.severity}] {f.title}</b> — <font color='#b91c1c'>FALSE POSITIVE</font>", body_style),
                    Paragraph(f"Target: {f.target_url or f.target_host} | Source: {f.scan_source.upper()}", subtitle_style),
                    Paragraph(f"<b>Reason for Elimination:</b> {fp_reason}", body_style),
                    Spacer(1, 6)
                ]
                elements.append(KeepTogether(card_content))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


report_service = ReportService()
