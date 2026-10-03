import base64
import json
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from typing import Union
from backend.parsers.base import BaseParser
from backend.models.finding import FindingCreate

SEVERITY_MAP = {
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "information": "Info",
    "info": "Info",
    "critical": "Critical"
}


class BurpParser(BaseParser):
    def parse(self, content: Union[bytes, str]) -> list[FindingCreate]:
        if isinstance(content, bytes):
            text_content = content.decode("utf-8", errors="replace")
        else:
            text_content = content

        text_stripped = text_content.strip()
        if not text_stripped:
            return []

        if text_stripped.startswith("{") or text_stripped.startswith("["):
            return self._parse_json(text_content)
        elif text_stripped.startswith("<") or "<issues" in text_stripped or "<issue" in text_stripped:
            return self._parse_xml(text_content)
        else:
            # Fallback to json attempt
            try:
                return self._parse_json(text_content)
            except Exception:
                return self._parse_xml(text_content)

    def _parse_json(self, json_text: str) -> list[FindingCreate]:
        try:
            data = json.loads(json_text)
        except Exception:
            return []
        raw_issues = []
        if isinstance(data, dict):
            raw_issues = data.get("issues", [])
            if not raw_issues and "findings" in data:
                raw_issues = data.get("findings", [])
            if not raw_issues and "name" in data:
                raw_issues = [data]
        elif isinstance(data, list):
            raw_issues = data

        findings: list[FindingCreate] = []
        for idx, item in enumerate(raw_issues):
            title = item.get("name") or item.get("issue_name") or item.get("title") or "Unknown Burp Finding"
            sev_raw = (item.get("severity") or "Medium").lower()
            severity = SEVERITY_MAP.get(sev_raw, "Medium")
            confidence = item.get("confidence", "Firm")

            url = item.get("url") or ""
            host = item.get("host") or ""
            port = None
            protocol = "https"

            if url:
                parsed = urlparse(url)
                if not host:
                    host = parsed.hostname or ""
                port = parsed.port
                protocol = parsed.scheme or "https"
            
            if not port and item.get("port"):
                try:
                    port = int(item.get("port"))
                except ValueError:
                    port = None

            type_id = item.get("type_index") or item.get("type") or str(idx + 1)
            description = (item.get("issueBackground") or item.get("description") or "").strip()
            remediation = (item.get("remediationBackground") or item.get("remediationDetail") or item.get("solution") or "").strip()
            detail = (item.get("issueDetail") or item.get("detail") or "").strip()

            full_desc = f"{description}\n\nTechnical Detail:\n{detail}".strip() if detail else description
            
            # Extract evidence / request / response
            evidence_parts = []
            if detail:
                evidence_parts.append(detail)
            
            req_resp = item.get("requestresponse") or []
            if isinstance(req_resp, list) and req_resp:
                rr = req_resp[0]
                if isinstance(rr, dict):
                    req = rr.get("request") or ""
                    resp = rr.get("response") or ""
                    if req:
                        evidence_parts.append(f"HTTP Request:\n{req}")
                    if resp:
                        evidence_parts.append(f"HTTP Response:\n{resp}")

            raw_evidence = "\n\n---\n\n".join(evidence_parts) if evidence_parts else None

            findings.append(
                FindingCreate(
                    scan_source="burp",
                    scanner_id=f"burp-{type_id}",
                    title=title,
                    severity=severity,
                    cve_list=[],
                    cvss_score=None,
                    target_host=host,
                    target_port=port or (443 if protocol == "https" else 80),
                    target_url=url if url else (f"{protocol}://{host}:{port}" if port else f"{protocol}://{host}"),
                    protocol=protocol,
                    vuln_type="Web Application Vulnerability",
                    description=full_desc,
                    solution=remediation,
                    raw_evidence=raw_evidence,
                    raw_payload=None
                )
            )

        return findings

    def _parse_xml(self, xml_text: str) -> list[FindingCreate]:
        findings: list[FindingCreate] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            root = ET.fromstring(f"<root>{xml_text}</root>")

        issue_elements = root.findall(".//issue")
        for idx, issue in enumerate(issue_elements):
            name = issue.findtext("name") or "Burp Finding"
            raw_sev = (issue.findtext("severity") or "Medium").lower()
            severity = SEVERITY_MAP.get(raw_sev, "Medium")
            
            host_elem = issue.find("host")
            host_ip = host_elem.get("ip") if host_elem is not None else None
            host_val = host_elem.text if host_elem is not None else "unknown"
            
            path = issue.findtext("path") or ""
            location = issue.findtext("location") or path
            type_id = issue.findtext("type") or str(idx + 1)
            
            # Reconstruct URL
            target_url = f"{host_val}{location}" if host_val and host_val.startswith("http") else f"http://{host_val}{location}"
            parsed = urlparse(target_url)
            host = parsed.hostname or host_ip or host_val
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            protocol = parsed.scheme or "http"

            desc_bg = issue.findtext("issueBackground") or ""
            detail = issue.findtext("issueDetail") or ""
            remediation = issue.findtext("remediationBackground") or ""

            full_desc = f"{desc_bg}\n\nTechnical Details:\n{detail}".strip()

            evidence_parts = []
            if detail:
                evidence_parts.append(detail)

            # Request / Response
            for rr in issue.findall(".//requestresponse"):
                req_el = rr.find("request")
                resp_el = rr.find("response")
                
                if req_el is not None and req_el.text:
                    content = req_el.text
                    if req_el.get("base64") == "true":
                        try:
                            content = base64.b64decode(content).decode("utf-8", errors="replace")
                        except Exception:
                            pass
                    evidence_parts.append(f"HTTP Request:\n{content}")

                if resp_el is not None and resp_el.text:
                    content = resp_el.text
                    if resp_el.get("base64") == "true":
                        try:
                            content = base64.b64decode(content).decode("utf-8", errors="replace")
                        except Exception:
                            pass
                    evidence_parts.append(f"HTTP Response:\n{content}")

            raw_evidence = "\n\n---\n\n".join(evidence_parts) if evidence_parts else None

            findings.append(
                FindingCreate(
                    scan_source="burp",
                    scanner_id=f"burp-{type_id}",
                    title=name.strip(),
                    severity=severity,
                    cve_list=[],
                    cvss_score=None,
                    target_host=host,
                    target_port=port,
                    target_url=target_url,
                    protocol=protocol,
                    vuln_type="Web Application Vulnerability",
                    description=full_desc,
                    solution=remediation.strip(),
                    raw_evidence=raw_evidence,
                    raw_payload=None
                )
            )

        return findings
