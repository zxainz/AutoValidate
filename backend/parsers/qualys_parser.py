import csv
import io
import xml.etree.ElementTree as ET
from typing import Union
from backend.parsers.base import BaseParser
from backend.models.finding import FindingCreate

SEVERITY_MAP = {
    "1": "Info",
    "2": "Low",
    "3": "Medium",
    "4": "High",
    "5": "Critical",
    "info": "Info",
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "critical": "Critical",
    "urgent": "Critical"
}


class QualysParser(BaseParser):
    def parse(self, content: Union[bytes, str]) -> list[FindingCreate]:
        if isinstance(content, bytes):
            text_content = content.decode("utf-8", errors="replace")
        else:
            text_content = content

        text_stripped = text_content.strip()
        if not text_stripped:
            return []

        if text_stripped.startswith("<?xml") or "<SCAN" in text_stripped or "<GLOSSARY" in text_stripped or "<IP" in text_stripped or "<QID>" in text_stripped:
            return self._parse_xml(text_content)
        else:
            return self._parse_csv(text_content)

    def _parse_xml(self, xml_text: str) -> list[FindingCreate]:
        findings: list[FindingCreate] = []
        if not xml_text.strip():
            return findings

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            try:
                root = ET.fromstring(f"<root>{xml_text}</root>")
            except ET.ParseError:
                return []

        # Look for host IP containers
        ip_elements = root.findall(".//IP")
        if not ip_elements:
            # Also support standalone QID elements if snippet
            items = root.findall(".//CATALOG//VULN") or root.findall(".//VULN")
            if not items and root.find(".//QID") is not None:
                items = [root]
            for item in items:
                f = self._parse_item(item, host="unknown")
                if f:
                    findings.append(f)
            return findings

        for ip_elem in ip_elements:
            host_name = ip_elem.get("value") or ip_elem.findtext("IP") or "unknown"
            vuln_records = ip_elem.findall(".//VULN") or ip_elem.findall(".//VULNS/VULN")
            for record in vuln_records:
                f = self._parse_item(record, host=host_name)
                if f:
                    findings.append(f)

        return findings

    def _parse_item(self, item: ET.Element, host: str) -> FindingCreate | None:
        qid = item.findtext("QID") or item.get("number")
        title = item.findtext("Title") or item.findtext("TITLE") or f"Qualys Finding QID-{qid}"
        raw_sev = item.findtext("Severity") or item.findtext("SEVERITY") or item.get("severity", "3")
        severity = SEVERITY_MAP.get(str(raw_sev).lower(), "Medium")

        port_str = item.findtext("Port") or item.findtext("PORT") or item.get("port")
        port = int(port_str) if port_str and port_str.isdigit() else None
        protocol = item.findtext("Protocol") or item.findtext("PROTOCOL") or "tcp"

        cves = []
        cve_tags = item.findall(".//CVE") or item.findall(".//CVE_LIST/CVE")
        for c in cve_tags:
            cve_id = c.findtext("ID") or c.text
            if cve_id and cve_id.strip():
                cves.append(cve_id.strip())

        diagnosis = item.findtext("DIAGNOSIS") or item.findtext("Diagnosis") or ""
        consequence = item.findtext("CONSEQUENCE") or item.findtext("Consequence") or ""
        solution = item.findtext("SOLUTION") or item.findtext("Solution") or ""
        results = item.findtext("RESULTS") or item.findtext("Results") or item.findtext("PAYLOAD") or ""

        description = f"{diagnosis}\n\nConsequence: {consequence}".strip()

        return FindingCreate(
            scan_source="qualys",
            scanner_id=f"QID-{qid}" if qid else None,
            title=title.strip(),
            severity=severity,
            cve_list=cves,
            cvss_score=None,
            target_host=host,
            target_port=port,
            target_url=f"{protocol}://{host}:{port}" if port else f"http://{host}",
            protocol=protocol.lower(),
            vuln_type="Vulnerability Assessment",
            description=description,
            solution=solution.strip(),
            raw_evidence=results.strip(),
            raw_payload=None
        )

    def _parse_csv(self, csv_text: str) -> list[FindingCreate]:
        findings: list[FindingCreate] = []
        reader = csv.DictReader(io.StringIO(csv_text))
        for row in reader:
            qid = row.get("QID")
            title = row.get("Title") or f"Qualys QID-{qid}"
            sev_raw = str(row.get("Severity") or "3").strip().lower()
            severity = SEVERITY_MAP.get(sev_raw, "Medium")
            host = row.get("IP") or row.get("DNS") or "unknown"
            port_str = row.get("Port")
            port = int(port_str) if port_str and port_str.isdigit() else None
            protocol = (row.get("Protocol") or "tcp").lower()
            
            cve_raw = row.get("CVE ID") or row.get("CVE") or ""
            cves = [c.strip() for c in cve_raw.split(",") if c.strip()]
            
            diag = row.get("Diagnosis") or row.get("Threat") or ""
            sol = row.get("Solution") or ""
            results = row.get("Results") or ""

            findings.append(
                FindingCreate(
                    scan_source="qualys",
                    scanner_id=f"QID-{qid}" if qid else None,
                    title=title.strip(),
                    severity=severity,
                    cve_list=cves,
                    cvss_score=None,
                    target_host=host,
                    target_port=port,
                    target_url=f"{protocol}://{host}:{port}" if port else f"http://{host}",
                    protocol=protocol,
                    vuln_type="Vulnerability Assessment",
                    description=diag.strip(),
                    solution=sol.strip(),
                    raw_evidence=results.strip(),
                    raw_payload=None
                )
            )

        return findings
