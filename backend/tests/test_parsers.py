import pytest
from pathlib import Path
from backend.parsers.nessus_parser import NessusParser
from backend.parsers.burp_parser import BurpParser
from backend.parsers.qualys_parser import QualysParser
from backend.parsers.generic_parser import GenericParser
from backend.parsers import detect_and_get_parser

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "sample_scans"


def test_nessus_xml_parser():
    sample_file = SAMPLES_DIR / "nessus_sample.xml"
    content = sample_file.read_bytes()
    parser = NessusParser()
    findings = parser.parse(content)

    assert len(findings) == 3
    # Check Finding 1: OpenSSL
    f1 = findings[0]
    assert "OpenSSL" in f1.title
    assert f1.severity == "High"
    assert "CVE-2021-3450" in f1.cve_list
    assert f1.target_host == "192.168.10.50"
    assert f1.target_port == 443

    # Check Finding 2: Log4j
    f2 = findings[1]
    assert "Log4j" in f2.title
    assert f2.severity == "Critical"
    assert "CVE-2021-44228" in f2.cve_list


def test_burp_json_parser():
    sample_file = SAMPLES_DIR / "burp_sample.json"
    content = sample_file.read_text(encoding="utf-8")
    parser = BurpParser()
    findings = parser.parse(content)

    assert len(findings) == 3
    sqli = findings[0]
    assert "SQL Injection" in sqli.title
    assert sqli.severity == "High"
    assert "500 Internal Server Error" in sqli.raw_evidence

    xss = findings[2]
    assert "Cross-Site Scripting" in xss.title
    assert "targetapp.com" in xss.target_host


def test_qualys_xml_parser():
    sample_file = SAMPLES_DIR / "qualys_sample.xml"
    content = sample_file.read_text(encoding="utf-8")
    parser = QualysParser()
    findings = parser.parse(content)

    assert len(findings) == 1
    f = findings[0]
    assert f.scanner_id == "QID-38341"
    assert "CVE-2021-3450" in f.cve_list
    assert f.target_host == "10.0.1.15"


def test_generic_json_parser():
    sample_file = SAMPLES_DIR / "generic_sample.json"
    content = sample_file.read_text(encoding="utf-8")
    parser = GenericParser()
    findings = parser.parse(content)

    assert len(findings) == 2
    assert findings[0].title == "Cross-Site Scripting (Stored)"
    assert findings[0].severity == "High"
    assert "CVE-2023-1234" in findings[0].cve_list


def test_auto_detect_parser():
    nessus_parser = detect_and_get_parser("my_scan.nessus", "<NessusClientData_v2>")
    assert isinstance(nessus_parser, NessusParser)

    burp_parser = detect_and_get_parser("report.json", '{"issues": []}')
    assert isinstance(burp_parser, BurpParser)

    qualys_parser = detect_and_get_parser("qualys.xml", "<SCAN value='test'><QID>123</QID></SCAN>")
    assert isinstance(qualys_parser, QualysParser)


def test_empty_inputs_across_all_parsers():
    for parser_cls in [NessusParser, BurpParser, QualysParser, GenericParser]:
        p = parser_cls()
        assert p.parse("") == []
        assert p.parse(b"") == []
        assert p.parse("   \n\t  ") == []


def test_malformed_inputs_handling():
    # Broken XML
    assert NessusParser().parse("<broken><xml>") == []
    assert QualysParser().parse("<not><valid<xml>") == []

    # Broken JSON
    assert BurpParser().parse("{broken json") == []
    assert GenericParser().parse("{not valid: json}") == []

    # Empty structure
    assert GenericParser().parse("{}") == []
    assert GenericParser().parse("[]") == []
    assert BurpParser().parse('{"issues": []}') == []


def test_special_characters_and_unicode_handling():
    sample = {
        "findings": [
            {
                "title": "SQLi with Unicode: \u00e9\u00e0\u4e2d\u6587 \ud83d\udd12",
                "severity": "High",
                "evidence": "SELECT * FROM users WHERE pass = 'admin'\u0000; -- test",
                "target": "https://test.local/\u00e9"
            }
        ]
    }
    import json
    parsed = GenericParser().parse(json.dumps(sample))
    assert len(parsed) == 1
    assert "\u00e9" in parsed[0].title

