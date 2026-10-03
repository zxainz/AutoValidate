import json
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport, Response
from backend.main import app
from backend.database.base import Base
from backend.database.session import engine
from backend.core.ai_engine import ai_engine


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.mark.asyncio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["app"] == "AutoValidate Pro"


@pytest.mark.asyncio
async def test_ai_status_endpoint_missing_key():
    ai_engine.api_key = ""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ai/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is False
        assert data["status"] == "missing_key"


@pytest.mark.asyncio
async def test_strict_api_rejection_without_key():
    ai_engine.api_key = ""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/validation/start", json={"finding_ids": []})
        assert resp.status_code == 400
        assert "Real GLM-5.3 API key required" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_and_metrics_flow_with_live_client_pipeline():
    from pathlib import Path
    sample_path = Path(__file__).resolve().parent.parent / "sample_scans" / "nessus_sample.xml"
    content = sample_path.read_bytes()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Clear existing
        await client.delete("/api/findings")

        # Upload Nessus sample
        files = {"file": ("nessus_sample.xml", content, "application/xml")}
        data = {"scanner_type": "nessus"}
        upload_resp = await client.post("/api/findings/upload", files=files, data=data)
        assert upload_resp.status_code == 200
        res = upload_resp.json()
        assert res["total_imported"] == 3

        # Check metrics
        metrics_resp = await client.get("/api/metrics")
        assert metrics_resp.status_code == 200
        m = metrics_resp.json()
        assert m["total_findings"] == 3
        assert m["unverified_findings"] == 3

        # List findings
        findings_resp = await client.get("/api/findings")
        assert findings_resp.status_code == 200
        findings = findings_resp.json()
        assert len(findings) == 3

        # Configure mock API key
        ai_engine.api_key = "test-live-key"

        # Simulate real GLM-5.3 response payload for Finding 1 (False Positive)
        mock_glm_fp = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "verdict": "FALSE_POSITIVE",
                        "confidence_score": 15,
                        "feasibility_score": 0.1,
                        "context_score": 0.2,
                        "evidence_score": 0.15,
                        "reasoning": "Debian security backport renders this unexploitable.",
                        "exploitation_difficulty": "HARD",
                        "business_impact": "LOW",
                        "recommended_action": "Mark as false positive.",
                        "false_positive_reason": "OS distribution backported patch."
                    })
                }
            }]
        }

        # Simulate real GLM-5.3 response payload for Finding 2 (True Positive)
        mock_glm_tp = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "verdict": "TRUE_POSITIVE",
                        "confidence_score": 95,
                        "feasibility_score": 0.95,
                        "context_score": 0.9,
                        "evidence_score": 0.95,
                        "reasoning": "Log4j RCE confirmed with interactive command execution proof.",
                        "exploitation_difficulty": "EASY",
                        "business_impact": "CRITICAL",
                        "recommended_action": "Patch log4j immediately.",
                        "false_positive_reason": None
                    })
                }
            }]
        }

        openssl_f = next(f for f in findings if "OpenSSL" in f["title"])
        log4j_f = next(f for f in findings if "Log4j" in f["title"])

        with patch.object(ai_engine, "_call_llm", new_callable=AsyncMock) as mock_llm:
            # 1. Validate OpenSSL (False Positive)
            mock_llm.return_value = {
                "verdict": "FALSE_POSITIVE",
                "confidence_score": 15.0,
                "feasibility_score": 0.1,
                "context_score": 0.2,
                "evidence_score": 0.15,
                "reasoning": "Debian security backport renders this unexploitable.",
                "exploitation_difficulty": "HARD",
                "business_impact": "LOW",
                "recommended_action": "Mark as false positive.",
                "false_positive_reason": "OS distribution backported patch."
            }

            val_resp = await client.post(f"/api/validation/single/{openssl_f['id']}")
            assert val_resp.status_code == 200
            val_data = val_resp.json()
            assert val_data["verdict"] == "FALSE_POSITIVE"

            # 2. Validate Log4j (True Positive)
            mock_llm.return_value = {
                "verdict": "TRUE_POSITIVE",
                "confidence_score": 95.0,
                "feasibility_score": 0.95,
                "context_score": 0.9,
                "evidence_score": 0.95,
                "reasoning": "Log4j RCE confirmed with interactive command execution proof.",
                "exploitation_difficulty": "EASY",
                "business_impact": "CRITICAL",
                "recommended_action": "Patch log4j immediately.",
                "false_positive_reason": None
            }

            val_resp2 = await client.post(f"/api/validation/single/{log4j_f['id']}")
            assert val_resp2.status_code == 200
            val_data2 = val_resp2.json()
            assert val_data2["verdict"] == "TRUE_POSITIVE"
            assert val_data2["confidence_score"] >= 75.0

        # Generate report
        rep_resp = await client.post("/api/reports/generate?title=Test%20Engagement%20Report")
        assert rep_resp.status_code == 200
        rep_data = rep_resp.json()
        assert rep_data["id"] is not None

        # Export HTML report
        export_html = await client.get(f"/api/reports/{rep_data['id']}/export?format=html")
        assert export_html.status_code == 200
        assert "Verified True Positives" in export_html.text

        # Export CSV report
        export_csv = await client.get(f"/api/reports/{rep_data['id']}/export?format=csv")
        assert export_csv.status_code == 200
        assert "Finding ID,Title,Severity" in export_csv.text

        # Export PDF report
        export_pdf = await client.get(f"/api/reports/{rep_data['id']}/export?format=pdf")
        assert export_pdf.status_code == 200
