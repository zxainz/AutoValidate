import json
import logging
from typing import Any, Optional
import httpx
from fastapi import HTTPException
from backend.core.config import settings
from backend.core.prompt_templates import SYSTEM_PROMPT, VALIDATION_PROMPT_TEMPLATE
from backend.core.scoring import confidence_scorer
from backend.core.evidence_validator import evidence_validator
from backend.models.finding import Finding

logger = logging.getLogger("autovalidate.ai_engine")


class AIEngine:
    """
    Validation engine powered STRICTLY by the real live GLM-5.3 API via Z.ai.
    Offline simulation, mock results, and heuristic fallbacks are strictly disabled.
    """

    def __init__(self):
        self.api_key = settings.ZAI_API_KEY
        self.base_url = settings.ZAI_BASE_URL
        self.model_name = settings.MODEL_NAME

    async def test_connection(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Sends a minimal ping request to the live GLM-5.3 API to verify credentials and connectivity.
        """
        key = (api_key if api_key is not None else self.api_key or settings.ZAI_API_KEY).strip()
        if not key:
            return {
                "connected": False,
                "status": "missing_key",
                "message": "ZAI_API_KEY is not configured. Real API key required."
            }

        url = (base_url or self.base_url or settings.ZAI_BASE_URL).rstrip("/")
        endpoint = f"{url}/chat/completions" if not url.endswith("/chat/completions") else url
        model = (model_name or self.model_name or settings.MODEL_NAME).strip()

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "ping"}
            ],
            "max_tokens": 5,
            "temperature": 0.0
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
                if resp.status_code == 200:
                    return {
                        "connected": True,
                        "status": "connected",
                        "model": model,
                        "message": f"Successfully connected to live {model} API"
                    }
                else:
                    return {
                        "connected": False,
                        "status": "auth_error",
                        "http_status": resp.status_code,
                        "message": f"API returned status {resp.status_code}: {resp.text[:200]}"
                    }
        except httpx.ConnectError as e:
            return {
                "connected": False,
                "status": "connect_error",
                "message": f"Failed to connect to API endpoint: {str(e)}"
            }
        except httpx.TimeoutException:
            return {
                "connected": False,
                "status": "timeout",
                "message": "Connection to GLM-5.3 API timed out"
            }
        except Exception as e:
            return {
                "connected": False,
                "status": "error",
                "message": f"API connection check error: {str(e)}"
            }

    async def validate_finding(
        self,
        finding: Finding,
        environment_type: str = "Production Web/API",
    ) -> dict[str, Any]:
        """
        Validates a single finding exclusively using the real GLM-5.3 API.
        Raises HTTP 400 if API key is missing or HTTP 503 if API fails.
        Zero mock/simulated fallbacks allowed.
        """
        api_key = (self.api_key or settings.ZAI_API_KEY).strip()
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="Real GLM-5.3 API key required. Offline simulation is disabled."
            )

        # Call real live API
        return await self._call_llm(finding, environment_type, api_key)

    async def _call_llm(self, finding: Finding, environment_type: str, api_key: str) -> dict[str, Any]:
        base_url = (self.base_url or settings.ZAI_BASE_URL).rstrip("/")
        endpoint = f"{base_url}/chat/completions" if not base_url.endswith("/chat/completions") else base_url

        # Build prompt
        user_content = VALIDATION_PROMPT_TEMPLATE.format(
            target=finding.target_url or finding.target_host or "unknown",
            target_port=finding.target_port or "N/A",
            protocol=finding.protocol or "tcp",
            scan_source=finding.scan_source,
            scanner_id=finding.scanner_id or "N/A",
            environment_type=environment_type,
            title=finding.title,
            severity=finding.severity,
            cve_list=", ".join(finding.cves) if finding.cves else "None",
            cvss_score=finding.cvss_score if finding.cvss_score is not None else "N/A",
            vuln_type=finding.vuln_type or "General Security Finding",
            description=finding.description or "No description provided.",
            raw_evidence=finding.raw_evidence or "No raw evidence available.",
            solution=finding.solution or "No solution specified."
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name or settings.MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            "temperature": settings.TEMPERATURE,
            "max_tokens": settings.MAX_TOKENS,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                res_data = response.json()
        except httpx.HTTPStatusError as e:
            status = 401 if e.response.status_code in [401, 403] else 503
            err_msg = f"GLM-5.3 API Error ({e.response.status_code}): {e.response.text}"
            logger.error(err_msg)
            raise HTTPException(status_code=status, detail=err_msg)
        except Exception as e:
            err_msg = f"Failed to communicate with GLM-5.3 API: {str(e)}. Real API connection required."
            logger.error(err_msg)
            raise HTTPException(status_code=503, detail=err_msg)

        try:
            message_content = res_data["choices"][0]["message"]["content"]
            
            # Clean possible markdown wrap
            cleaned = message_content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            parsed = json.loads(cleaned.strip())
        except Exception as e:
            logger.error(f"Failed to parse GLM-5.3 JSON response: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"Invalid JSON returned from GLM-5.3 API: {str(e)}"
            )

        # Calculate final confidence via calibrated scorer
        feasibility = float(parsed.get("feasibility_score", 0.5))
        context = float(parsed.get("context_score", 0.5))
        evidence = float(parsed.get("evidence_score", 0.5))

        calc_conf = confidence_scorer.calculate_confidence(
            feasibility_score=feasibility,
            context_score=context,
            evidence_score=evidence,
            cve_list=finding.cves,
            vuln_type=finding.vuln_type,
            title=finding.title
        )

        final_conf = parsed.get("confidence_score")
        if final_conf is None or abs(float(final_conf) - calc_conf) > 20:
            final_conf = calc_conf
        else:
            final_conf = float(final_conf)

        verdict = confidence_scorer.determine_verdict(final_conf)

        return {
            "verdict": verdict,
            "confidence_score": final_conf,
            "feasibility_score": feasibility,
            "context_score": context,
            "evidence_score": evidence,
            "reasoning": parsed.get("reasoning", "Live GLM-5.3 API validation completed."),
            "exploitation_difficulty": parsed.get("exploitation_difficulty", "MEDIUM"),
            "business_impact": parsed.get("business_impact", "MEDIUM"),
            "recommended_action": parsed.get("recommended_action", "Review target patch status."),
            "false_positive_reason": parsed.get("false_positive_reason")
        }


ai_engine = AIEngine()
