"""
Phase 5 Verification Suite: Tender Specification Audit Engine (Mode B).
Validates automated detection of deprecated standards, statutory QCO exemptions,
omitted Clause 2 testing standards, foreign standard discrimination under PPP-MII,
and tender corrigendum formulation across authentic GeM/CPWD/NHAI tenders.
"""

from pathlib import Path
import pytest
from backend.app.services.auditor import TenderAuditor, get_tender_auditor

TENDERS_DIR = Path(__file__).resolve().parent.parent / "data" / "gem_tender_samples"


@pytest.fixture(scope="module")
def auditor() -> TenderAuditor:
    """Fixture providing initialized TenderAuditor."""
    return get_tender_auditor()


class TestTenderAuditorComplianceTraps:
    """Tests real-world tender compliance trap detection against harvested test fixtures."""

    def test_cpwd_structural_steel_trap(self, auditor: TenderAuditor):
        file_path = TENDERS_DIR / "cpwd_structural_steel_trap_spec.txt"
        assert file_path.exists(), f"Sample tender missing: {file_path}"
        raw_text = file_path.read_text(encoding="utf-8")

        report = auditor.audit_tender(
            raw_text=raw_text,
            tender_id="GEM/2026/B/543210",
            tender_title="CPWD Workshop Structural Steel",
            department="CPWD"
        )

        # Assertions
        assert report["qco_compliant"] is False, "Must detect failure of mandatory QCO"
        assert report["compliance_score"] < 60, f"Score {report['compliance_score']} should be < 60"
        assert report["status_color"] == "red"

        # Check detected superseded standards
        dep_standards = [d["standard_cited"] for d in report["deprecated_standards"]]
        assert any("2062" in s for s in dep_standards) or any("432" in s for s in dep_standards)

        # Check findings
        issue_types = [f["issue_type"] for f in report["findings"]]
        assert "ILLEGAL_QCO_EXEMPTION" in issue_types or "MISSING_QCO_MANDATE" in issue_types
        assert "SUPERSEDED_STANDARD" in issue_types

        # Check corrigendum generated
        assert "CORRIGENDUM / AMENDMENT" in report["corrigendum_notice"]
        assert "GEM/2026/B/543210" in report["corrigendum_notice"]

    def test_nhai_compliant_rebar_spec(self, auditor: TenderAuditor):
        file_path = TENDERS_DIR / "nhai_bridge_rebar_spec.txt"
        assert file_path.exists(), f"Sample tender missing: {file_path}"
        raw_text = file_path.read_text(encoding="utf-8")

        report = auditor.audit_tender(
            raw_text=raw_text,
            tender_id="GEM/2026/B/890123",
            tender_title="NHAI Flyover Foundation Rebars",
            department="NHAI"
        )

        assert report["qco_compliant"] is True
        assert report["compliance_score"] >= 85, f"Expected high compliance score, got {report['compliance_score']}"
        assert report["status_color"] == "green"
        assert len(report["deprecated_standards"]) == 0

    def test_meity_it_laptops_crs_spec(self, auditor: TenderAuditor):
        file_path = TENDERS_DIR / "meity_it_hardware_laptops.txt"
        assert file_path.exists(), f"Sample tender missing: {file_path}"
        raw_text = file_path.read_text(encoding="utf-8")

        report = auditor.audit_tender(
            raw_text=raw_text,
            tender_id="GEM/2026/B/112233",
            tender_title="MeitY Commercial Laptops",
            department="MeitY"
        )

        assert report["qco_compliant"] is True
        assert report["compliance_score"] >= 85
        assert any("13252" in s for s in report["standards_referenced"])

    def test_phed_hdpe_pipe_dilution_trap(self, auditor: TenderAuditor):
        file_path = TENDERS_DIR / "phed_water_hdpe_pipe_trap.txt"
        assert file_path.exists(), f"Sample tender missing: {file_path}"
        raw_text = file_path.read_text(encoding="utf-8")

        report = auditor.audit_tender(
            raw_text=raw_text,
            tender_id="GEM/2026/B/334455",
            tender_title="PHED Jal Jeevan Mission HDPE Pipes",
            department="PHED"
        )

        assert report["compliance_score"] < 60
        issue_types = [f["issue_type"] for f in report["findings"]]
        assert "VAGUE_SPECIFICATION" in issue_types

    def test_hindi_multilingual_tender_audit(self, auditor: TenderAuditor):
        file_path = TENDERS_DIR / "mp_pwd_hindi_tmt_spec.txt"
        assert file_path.exists(), f"Sample tender missing: {file_path}"
        raw_text = file_path.read_text(encoding="utf-8")

        report = auditor.audit_tender(
            raw_text=raw_text,
            tender_id="GEM/2026/B/221100",
            tender_title="MP PWD College Building Rebars",
            department="MP PWD"
        )

        assert report["is_indic"] is True
        assert report["detected_language"] == "hi"
        assert report["qco_compliant"] is True
        assert any("1786" in s for s in report["standards_referenced"])


class TestForeignStandardDiscrimination:
    """Tests enforcement of Public Procurement (Preference to Make in India) Order."""

    def test_pure_foreign_standard_penalty(self, auditor: TenderAuditor):
        tender_text = (
            "Supply of 200 MT structural steel plates for crane girder. "
            "Plates must conform strictly to ASTM A36 specification with manufacturer mill certificate."
        )
        report = auditor.audit_tender(tender_text)
        issue_types = [f["issue_type"] for f in report["findings"]]
        assert "FOREIGN_STANDARD_DISCRIMINATION" in issue_types
        assert any("ASTM A36" in f["original_text_snippet"] for f in report["findings"])
        assert report["compliance_score"] < 100
