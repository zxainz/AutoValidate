import csv
import io
import xml.etree.ElementTree as ET
from typing import Union
from backend.parsers.base import BaseParser
from backend.models.finding import FindingCreate

SEVERITY_MAP = {
    "0": "Info",
    "1": "Low",
    "2": "Medium",
    "3": "High",
    "4": "Critical",
    "none": "Info",
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "critical": "Critical"
}


class NessusParser(BaseParser):
    def parse(self, content: Union[bytes, str]) -> list[FindingCreate]:
        if isinstance(content, bytes):
            text_content = content.decode("utf-8", errors="replace")
        else:
            text_content = content

        text_stripped = text_content.strip()
        if not text_stripped:
            return []

        if text_stripped.startswith("<?xml") or "<NessusClientData_v2" in text_stripped or "<Report" in text_stripped:
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
                return findings

        # Walk through ReportHost elements
        for host in root.findall(".//ReportHost"):
            host_name = host.get("name", "unknown")
            
            for item in host.findall("ReportItem"):
                plugin_id = item.get("pluginID")
                plugin_name = item.get("pluginName") or (item.findtext("plugin_name") or "Unknown Nessus Finding").strip()
                port = item.get("port")
                protocol = item.get("protocol", "tcp")
                raw_severity = item.get("severity", "1")
                severity = SEVERITY_MAP.get(str(raw_severity).lower(), "Medium")
                
                # Risk factor override if present
                risk_factor = item.findtext("risk_factor")
                if risk_factor and risk_factor.lower() in SEVERITY_MAP:
                    severity = SEVERITY_MAP[risk_factor.lower()]

                # CVE list
                cves = [elem.text.strip() for elem in item.findall("cve") if elem.text]

                # CVSS score
                cvss_str = item.findtext("cvss3_base_score") or item.findtext("cvss_base_score")
                cvss_score = float(cvss_str) if cvss_str else None

                description = item.findtext("description") or ""
                solution = item.findtext("solution") or ""
                plugin_output = item.findtext("plugin_output") or ""
                synopsis = item.findtext("synopsis") or ""

                port_int = int(port) if port and port.isdigit() else None

                findings.append(
                    FindingCreate(
                        scan_source="nessus",
                        scanner_id=str(plugin_id) if plugin_id else None,
                        title=plugin_name,
                        severity=severity,
                        cve_list=cves,
                        cvss_score=cvss_score,
                        target_host=host_name,
                        target_port=port_int,
                        target_url=f"{protocol}://{host_name}:{port}" if port_int else f"http://{host_name}",
                        protocol=protocol,
                        vuln_type="Network / Host Vulnerability",
                        description=f"{synopsis}\n\n{description}".strip(),
                        solution=solution.strip(),
                        raw_evidence=plugin_output.strip(),
                        raw_payload=None
                    )
                )

        return findings

    def _parse_csv(self, csv_text: str) -> list[FindingCreate]:
        findings: list[FindingCreate] = []
        reader = csv.DictReader(io.StringIO(csv_text))
        
        for row in reader:
            # Map standard Nessus CSV columns
            title = row.get("Name") or row.get("Plugin Name") or "Unknown Nessus Finding"
            plugin_id = row.get("Plugin ID") or row.get("Plugin")
            severity_raw = (row.get("Risk") or row.get("Severity") or "Medium").strip().lower()
            severity = SEVERITY_MAP.get(severity_raw, "Medium")
            host = row.get("Host") or row.get("IP Address") or "unknown"
            port_str = row.get("Port")
            port = int(port_str) if port_str and port_str.isdigit() else None
            protocol = row.get("Protocol") or "tcp"
            cve = row.get("CVE") or ""
            cves = [c.strip() for c in cve.split(",") if c.strip()]
            cvss_str = row.get("CVSS") or row.get("CVSS v3.0 Base Score") or row.get("CVSS v2.0 Base Score")
            try:
                cvss_score = float(cvss_str) if cvss_str else None
            except ValueError:
                cvss_score = None

            description = row.get("Description") or row.get("Synopsis") or ""
            solution = row.get("Solution") or ""
            evidence = row.get("Plugin Output") or ""

            findings.append(
                FindingCreate(
                    scan_source="nessus",
                    scanner_id=str(plugin_id) if plugin_id else None,
                    title=title,
                    severity=severity,
                    cve_list=cves,
                    cvss_score=cvss_score,
                    target_host=host,
                    target_port=port,
                    target_url=f"{protocol}://{host}:{port}" if port else f"http://{host}",
                    protocol=protocol,
                    vuln_type="Network / Host Vulnerability",
                    description=description.strip(),
                    solution=solution.strip(),
                    raw_evidence=evidence.strip(),
                    raw_payload=None
                )
            )

        return findings
