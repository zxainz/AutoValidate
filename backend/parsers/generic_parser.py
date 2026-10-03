import json
from typing import Union, Any
from urllib.parse import urlparse
from backend.parsers.base import BaseParser
from backend.models.finding import FindingCreate

SEVERITY_MAP = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "info": "Info",
    "information": "Info",
    "informational": "Info"
}


class GenericParser(BaseParser):
    def parse(self, content: Union[bytes, str]) -> list[FindingCreate]:
        if isinstance(content, bytes):
            text_content = content.decode("utf-8", errors="replace")
        else:
            text_content = content

        stripped = text_content.strip()
        if not stripped:
            return []

        try:
            data = json.loads(stripped)
        except Exception:
            return []

        items = []

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # check common container keys
            for key in ["findings", "vulnerabilities", "issues", "results", "alerts", "data"]:
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break
            if not items:
                # single object?
                items = [data]

        findings: list[FindingCreate] = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict) or not item:
                continue

            title = (
                item.get("title")
                or item.get("name")
                or item.get("vulnerability")
                or item.get("alert")
            )

            # Skip empty objects that lack any vulnerability indicators
            if not title and not item.get("description") and not item.get("cve") and not item.get("evidence"):
                continue

            title = title or f"Vulnerability #{idx + 1}"

            raw_sev = str(item.get("severity") or item.get("risk") or item.get("level") or "Medium").lower()
            severity = SEVERITY_MAP.get(raw_sev, "Medium")

            cves = []
            raw_cve = item.get("cve") or item.get("cves") or item.get("cve_list") or []
            if isinstance(raw_cve, list):
                cves = [str(c).strip() for c in raw_cve if str(c).strip() and str(c).upper() != "N/A"]
            elif isinstance(raw_cve, str) and raw_cve.strip() and raw_cve.upper() != "N/A":
                cves = [c.strip() for c in raw_cve.split(",") if c.strip()]

            cvss = None
            raw_cvss = item.get("cvss") or item.get("cvss_score") or item.get("score")
            if raw_cvss is not None:
                try:
                    cvss = float(raw_cvss)
                except ValueError:
                    pass

            target = str(item.get("target") or item.get("url") or item.get("host") or "unknown")
            host = target
            port = None
            protocol = "http"

            if target.startswith("http://") or target.startswith("https://"):
                p = urlparse(target)
                host = p.hostname or target
                port = p.port
                protocol = p.scheme
            elif ":" in target:
                parts = target.split(":")
                host = parts[0]
                if parts[1].isdigit():
                    port = int(parts[1])

            desc = item.get("description") or item.get("details") or item.get("synopsis") or ""
            sol = item.get("solution") or item.get("remediation") or item.get("recommendation") or ""
            evid = item.get("evidence") or item.get("proof") or item.get("output") or item.get("raw_evidence") or ""

            findings.append(
                FindingCreate(
                    scan_source="generic",
                    scanner_id=str(item.get("id") or item.get("identifier") or f"GEN-{idx+1}"),
                    title=str(title).strip(),
                    severity=severity,
                    cve_list=cves,
                    cvss_score=cvss,
                    target_host=host,
                    target_port=port,
                    target_url=target if target.startswith("http") else f"{protocol}://{host}" + (f":{port}" if port else ""),
                    protocol=protocol,
                    vuln_type=item.get("vuln_type") or item.get("type") or "Generic Vulnerability",
                    description=str(desc).strip(),
                    solution=str(sol).strip(),
                    raw_evidence=str(evid).strip() if evid else None,
                    raw_payload=str(item.get("payload") or "") or None
                )
            )

        return findings
