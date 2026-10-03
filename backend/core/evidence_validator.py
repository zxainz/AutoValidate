import re
from typing import Any

class EvidenceValidator:
    """
    Statically analyzes raw scanner evidence for typical false-positive indicators,
    such as OS backported security patches, generic 404/500 misinterpretations,
    and missing exploit execution proofs.
    """

    BACKPORT_PATTERNS = [
        re.compile(r"Debian-[\w+~.-]+", re.IGNORECASE),
        re.compile(r"Ubuntu-[\w+~.-]+", re.IGNORECASE),
        re.compile(r"\.el[6-9][\w_.]*", re.IGNORECASE),
        re.compile(r"\.amzn[1-2][\w_.]*", re.IGNORECASE),
    ]

    BANNER_ONLY_KEYWORDS = [
        "banner", "remote version", "version detection", "server banner",
        "service detection", "installed version", "reportitem"
    ]

    def analyze_evidence(self, title: str, description: str, raw_evidence: str | None) -> dict[str, Any]:
        evidence_text = (raw_evidence or "").strip()
        desc_text = (description or "").strip()
        combined = f"{title} {desc_text} {evidence_text}".lower()

        is_backported = False
        backport_match = None
        for pattern in self.BACKPORT_PATTERNS:
            match = pattern.search(evidence_text)
            if match:
                is_backported = True
                backport_match = match.group(0)
                break

        # Check if the scanner only detected a banner
        is_banner_only = any(kw in combined for kw in self.BANNER_ONLY_KEYWORDS) and (
            "payload" not in combined and "execution" not in combined and "http request:" not in combined
        )

        # Check for web error reflection / WAF block
        has_waf_block = "403 forbidden" in combined or "cloudflare" in combined or "access denied" in combined
        has_custom_404 = "404 not found" in combined

        # Check for strong execution proof
        has_execution_proof = (
            "uid=" in evidence_text or "root:" in evidence_text or
            "syntax error" in evidence_text or "sql" in evidence_text and "error" in evidence_text or
            "<script>alert" in evidence_text or "system32" in evidence_text.lower()
        )

        base_evidence_score = 0.5
        if has_execution_proof:
            base_evidence_score = 0.95
        elif is_backported:
            base_evidence_score = 0.20
        elif is_banner_only:
            base_evidence_score = 0.30
        elif has_waf_block:
            base_evidence_score = 0.35

        return {
            "is_backported": is_backported,
            "backport_package": backport_match,
            "is_banner_only": is_banner_only,
            "has_waf_block": has_waf_block,
            "has_custom_404": has_custom_404,
            "has_execution_proof": has_execution_proof,
            "preliminary_evidence_score": base_evidence_score,
        }

evidence_validator = EvidenceValidator()
