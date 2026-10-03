import pytest
from backend.core.scoring import confidence_scorer
from backend.core.evidence_validator import evidence_validator


def test_confidence_scorer_true_positive():
    # Strong feasibility and evidence
    score = confidence_scorer.calculate_confidence(
        feasibility_score=0.95,
        context_score=0.90,
        evidence_score=0.95,
        cve_list=["CVE-2021-44228"],
        vuln_type="rce",
        title="Apache Log4j RCE",
        verification_success=1.0
    )
    assert score >= 75.0
    verdict = confidence_scorer.determine_verdict(score)
    assert verdict == "TRUE_POSITIVE"


def test_confidence_scorer_false_positive():
    # Low feasibility, backported, no verified evidence
    score = confidence_scorer.calculate_confidence(
        feasibility_score=0.15,
        context_score=0.20,
        evidence_score=0.20,
        cve_list=[],
        vuln_type="version_banner",
        title="OpenSSL Version Detection",
        verification_success=0.1
    )
    assert score < 40.0
    verdict = confidence_scorer.determine_verdict(score)
    assert verdict == "FALSE_POSITIVE"


def test_evidence_validator_backport():
    res = evidence_validator.analyze_evidence(
        title="OpenSSL 1.1.1 Detection",
        description="Outdated version",
        raw_evidence="Remote banner: OpenSSL/1.1.1n-0+deb11u5 (Debian-11+deb11u5)"
    )
    assert res["is_backported"] is True
    assert res["preliminary_evidence_score"] <= 0.3


def test_evidence_validator_waf_block():
    res = evidence_validator.analyze_evidence(
        title="Directory Traversal",
        description="Path traversal attempted",
        raw_evidence="HTTP/1.1 403 Forbidden\nServer: Cloudflare\nAccess Denied"
    )
    assert res["has_waf_block"] is True
