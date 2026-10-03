from typing import Optional
from backend.models.finding import FindingBase


class ConfidenceScorer:
    """
    Computes an objective 0-100 confidence score for vulnerability findings.
    Blends LLM feasibility scores, evidence quality metrics, CVE validation, and empirical historical rates.
    """

    def __init__(self):
        self.weights = {
            "technical_feasibility": 0.30,
            "environmental_context": 0.25,
            "evidence_quality": 0.20,
            "historical_accuracy": 0.15,
            "verification_success": 0.10,
        }

        # Empirical scanner accuracy benchmarks by category
        self.historical_accuracy_map = {
            "sql_injection": 0.85,
            "xss": 0.70,
            "rce": 0.90,
            "command_injection": 0.88,
            "file_upload": 0.65,
            "deserialization": 0.60,
            "version_banner": 0.35,
            "ssl_tls": 0.45,
            "information_disclosure": 0.50,
            "default": 0.60,
        }

    def get_historical_accuracy(self, vuln_type: Optional[str], title: Optional[str]) -> float:
        combined = f"{vuln_type or ''} {title or ''}".lower()
        if "sql" in combined:
            return self.historical_accuracy_map["sql_injection"]
        elif "cross-site" in combined or "xss" in combined:
            return self.historical_accuracy_map["xss"]
        elif "remote code" in combined or "rce" in combined:
            return self.historical_accuracy_map["rce"]
        elif "banner" in combined or "version" in combined or "detection" in combined:
            return self.historical_accuracy_map["version_banner"]
        elif "ssl" in combined or "tls" in combined or "cipher" in combined:
            return self.historical_accuracy_map["ssl_tls"]
        return self.historical_accuracy_map["default"]

    def calculate_confidence(
        self,
        feasibility_score: float,
        context_score: float,
        evidence_score: float,
        cve_list: list[str],
        vuln_type: Optional[str] = None,
        title: Optional[str] = None,
        verification_success: float = 0.5,
    ) -> float:
        """
        Calculate overall confidence score (0.0 - 100.0)
        """
        # Clamp inputs between 0.0 and 1.0
        feasibility = max(0.0, min(1.0, feasibility_score))
        context = max(0.0, min(1.0, context_score))
        evidence = max(0.0, min(1.0, evidence_score))
        historical = self.get_historical_accuracy(vuln_type, title)
        verification = max(0.0, min(1.0, verification_success))

        # Base weighted sum scaled to 0-100
        weighted_sum = (
            (feasibility * self.weights["technical_feasibility"])
            + (context * self.weights["environmental_context"])
            + (evidence * self.weights["evidence_quality"])
            + (historical * self.weights["historical_accuracy"])
            + (verification * self.weights["verification_success"])
        ) * 100.0

        # Adjust based on CVE presence
        if cve_list and len(cve_list) > 0:
            weighted_sum += 5.0  # Confirmed standardized vulnerability
        else:
            # Custom or generic unindexed issue
            weighted_sum -= 5.0

        final_score = round(max(0.0, min(100.0, weighted_sum)), 1)
        return final_score

    def determine_verdict(self, confidence_score: float, tp_threshold: float = 75.0, fp_threshold: float = 40.0) -> str:
        if confidence_score >= tp_threshold:
            return "TRUE_POSITIVE"
        elif confidence_score < fp_threshold:
            return "FALSE_POSITIVE"
        else:
            return "NEEDS_MANUAL_REVIEW"


confidence_scorer = ConfidenceScorer()
