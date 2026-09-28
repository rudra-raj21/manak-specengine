"""
Phase 1 Verification Suite: Canonical Data Ingestion & Pydantic Schema Foundations.
Validates Pydantic v2 schemas, BIS Clause 2 parsing, reference normalization,
and seed dataset integrity.
"""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from backend.app.models.standard import IndianStandard, QCOOrder, ProcurementSpec
from backend.app.services.parser import (
    normalize_standard_ref,
    normalize_roman_part,
    extract_clause2_section,
    extract_clause2_references,
    extract_test_methods,
    parse_bis_document
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CLAUSE2_DIR = DATA_DIR / "clause2_samples"
SEED_FILE = DATA_DIR / "seed_data.json"


# ==============================================================================
# 1. Pydantic Model Validation Tests
# ==============================================================================

class TestPydanticSchemas:
    """Tests Pydantic v2 schemas, type constraints, and custom validators."""

    def test_indian_standard_valid_instantiation(self):
        std = IndianStandard(
            is_number="IS 2062",
            title="Hot Rolled Medium and High Tensile Structural Steel",
            year=2011,
            amendments=[1, 2],
            status="ACTIVE",
            scope="Covers requirements for structural steel grades for bridges and buildings.",
            committee="CED 54",
            normative_references=["IS 1608:2005", "IS 1599", "IS 1608:2005"],
            test_standards=["IS 1608:2005"]
        )
        assert std.is_number == "IS 2062"
        assert std.year == 2011
        assert std.status == "ACTIVE"
        # Check deduplication in normative_references validator
        assert std.normative_references == ["IS 1608:2005", "IS 1599"]

    def test_indian_standard_auto_prefix_is(self):
        std = IndianStandard(
            is_number="2062",
            title="Test Standard Title",
            scope="This is a test scope covering technical requirements.",
            committee="CED 54"
        )
        assert std.is_number == "IS 2062"

    def test_indian_standard_invalid_year_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            IndianStandard(
                is_number="IS 2062",
                title="Invalid Year Standard",
                year=1880,  # Below 1900
                scope="Valid scope description with sufficient length.",
                committee="CED 54"
            )
        assert "Year 1880 is outside acceptable range" in str(exc_info.value)

    def test_indian_standard_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            IndianStandard(
                is_number="IS 2062",
                title="Invalid Status Standard",
                status="DEPRECATED",  # Not in Literal["ACTIVE", "WITHDRAWN", "SUPERSEDED"]
                scope="Valid scope description with sufficient length.",
                committee="CED 54"
            )

    def test_qco_order_valid_instantiation(self):
        qco = QCOOrder(
            order_name="Steel and Steel Products (Quality Control) Order, 2020",
            ministry="Ministry of Steel",
            gazette_no="S.O. 1673(E)",
            effective_date="2020-05-22",
            mandatory_scheme="Scheme-I",
            applicable_standards=["IS 2062", "IS 1786"],
            scope_summary="Structural steel and rebars"
        )
        assert qco.mandatory_scheme == "Scheme-I"
        assert len(qco.applicable_standards) == 2
        assert "Section 16" in qco.penal_clause

    def test_qco_order_scheme_normalization(self):
        qco = QCOOrder(
            order_name="Electronics IT Goods Order",
            ministry="MeitY",
            gazette_no="S.O. 1248(E)",
            effective_date="2021-03-18",
            mandatory_scheme="Compulsory Registration (CRS) Scheme-II",
            applicable_standards=["IS 13252 (Part 1)"]
        )
        assert qco.mandatory_scheme == "Scheme-II (CRS)"

    def test_qco_order_empty_standards_raises(self):
        with pytest.raises(ValidationError):
            QCOOrder(
                order_name="Invalid Empty QCO",
                ministry="Ministry of Steel",
                gazette_no="S.O. 100(E)",
                effective_date="2020-01-01",
                mandatory_scheme="Scheme-I",
                applicable_standards=[]
            )

    def test_procurement_spec_validation(self):
        spec = ProcurementSpec(raw_text="Supply of 500 MT of Fe 500D TMT rebars")
        assert spec.language == "en"
        assert spec.raw_text == "Supply of 500 MT of Fe 500D TMT rebars"

        with pytest.raises(ValidationError):
            ProcurementSpec(raw_text="   ")


# ==============================================================================
# 2. Reference Normalizer & Clause 2 Parser Tests
# ==============================================================================

class TestParserAndNormalizer:
    """Tests normalization functions and Clause 2 reference extraction."""

    def test_normalize_roman_part(self):
        assert normalize_roman_part("Part I") == "Part 1"
        assert normalize_roman_part("Part II") == "Part 2"
        assert normalize_roman_part("Part IV") == "Part 4"
        assert normalize_roman_part("Parti") == "Part 1"
        assert normalize_roman_part("Part 2") == "Part 2"

    def test_normalize_standard_ref(self):
        assert normalize_standard_ref("IS 1608 : Part 1 : 2018") == "IS 1608 (Part 1):2018"
        assert normalize_standard_ref("IS 2062 : 2011") == "IS 2062:2011"
        assert normalize_standard_ref("1608:2005") == "IS 1608:2005"
        assert normalize_standard_ref("228 (Parts 1 to 24)") == "IS 228"
        assert normalize_standard_ref("IS/ISO 9001:2015") == "IS/ISO 9001:2015"
        assert normalize_standard_ref("lEC 60065:2001") == "IEC 60065:2001"

    def test_extract_clause2_section(self):
        doc = (
            "1 SCOPE\nThis standard specifies steel.\n\n"
            "2 NORMATIVE REFERENCES\n"
            "IS 228 Methods for chemical analysis of steel\n"
            "IS 1608 Tensile testing\n\n"
            "3 TERMINOLOGY\nDefinitions of terms."
        )
        c2 = extract_clause2_section(doc)
        assert "2 NORMATIVE REFERENCES" in c2
        assert "IS 1608" in c2
        assert "3 TERMINOLOGY" not in c2

    def test_extract_clause2_references_synthetic(self):
        text = (
            "2 REFERENCES\n"
            "IS 2062:2011 Structural Steel\n"
            "IS 1786 High strength deformed bars\n"
            "1608:2005 Tensile testing\n"
            "IS 2770 (Part 1): 1967 Pull out test\n"
        )
        refs = extract_clause2_references(text)
        assert "IS 2062:2011" in refs
        assert "IS 1786" in refs
        assert "IS 1608:2005" in refs
        assert "IS 2770 (Part 1):1967" in refs

    def test_extract_test_methods(self):
        text = (
            "2 REFERENCES\n"
            "1599: 1985 Method for bend test\n"
            "1608:2005 Metallic materials — Tensile testing at ambient temperature\n"
            "808 : 1989 Dimensions for hot rolled steel beam\n"
            "1757:1988 Method for Charpy impact test (V-notch)\n"
        )
        test_stds = extract_test_methods(text)
        assert any("1599" in s for s in test_stds)
        assert any("1608" in s for s in test_stds)
        assert any("1757" in s for s in test_stds)
        # IS 808 is a dimensional specification, not a test method
        assert not any("808" in s for s in test_stds)

    def test_parse_bis_document(self):
        sample_doc = (
            "IS 1786:2008\n"
            "High Strength Deformed Steel Bars\n"
            "1 SCOPE\nCovers requirements for deformed steel bars and wires.\n"
            "2 REFERENCES\n"
            "IS 1599 Method for bend test\n"
            "IS 1608 Tensile testing\n"
            "3 DEFINITIONS\n"
        )
        parsed = parse_bis_document(sample_doc, default_is_number="IS 1786", default_title="TMT Rebars")
        assert parsed["is_number"] == "IS 1786:2008"
        assert parsed["year"] == 2008
        assert "IS 1599" in parsed["normative_references"]
        assert "IS 1608" in parsed["normative_references"]
        assert "IS 1599" in parsed["test_standards"] or "IS 1608" in parsed["test_standards"]


# ==============================================================================
# 3. Real Clause 2 Sample Documents Validation
# ==============================================================================

class TestRealClause2Samples:
    """Validates parser against actual BIS Clause 2 text samples."""

    @pytest.mark.skipif(not CLAUSE2_DIR.exists(), reason="clause2_samples directory not found")
    def test_is_2062_real_sample(self):
        sample_path = CLAUSE2_DIR / "is_2062_clause2.txt"
        if not sample_path.exists():
            pytest.skip("is_2062_clause2.txt not found")
        content = sample_path.read_text(encoding="utf-8")
        refs = extract_clause2_references(content)
        # Real IS 2062 references IS 228, 808, 1608, 1757, 1852, 12778 etc.
        assert any("228" in r for r in refs), f"Expected IS 228 in {refs}"
        assert any("808" in r for r in refs), f"Expected IS 808 in {refs}"
        assert any("1608" in r for r in refs), f"Expected IS 1608 in {refs}"
        assert any("1757" in r for r in refs), f"Expected IS 1757 in {refs}"

    @pytest.mark.skipif(not CLAUSE2_DIR.exists(), reason="clause2_samples directory not found")
    def test_is_1786_real_sample(self):
        sample_path = CLAUSE2_DIR / "is_1786_clause2.txt"
        if not sample_path.exists():
            pytest.skip("is_1786_clause2.txt not found")
        content = sample_path.read_text(encoding="utf-8")
        refs = extract_clause2_references(content)
        # Real IS 1786 references IS 228, 1387, 1599, 1608, 2062, 2770, 9417
        assert any("228" in r for r in refs), f"Expected IS 228 in {refs}"
        assert any("1599" in r for r in refs), f"Expected IS 1599 in {refs}"
        assert any("2062" in r for r in refs), f"Expected IS 2062 in {refs}"

    @pytest.mark.skipif(not CLAUSE2_DIR.exists(), reason="clause2_samples directory not found")
    def test_is_4984_real_sample(self):
        sample_path = CLAUSE2_DIR / "is_4984_clause2.txt"
        if not sample_path.exists():
            pytest.skip("is_4984_clause2.txt not found")
        content = sample_path.read_text(encoding="utf-8")
        refs = extract_clause2_references(content)
        assert any("2530" in r for r in refs), f"Expected IS 2530 in {refs}"
        assert any("7328" in r for r in refs), f"Expected IS 7328 in {refs}"
        assert any("10146" in r for r in refs), f"Expected IS 10146 in {refs}"


# ==============================================================================
# 4. Seed Dataset Verification
# ==============================================================================

class TestSeedDataset:
    """Verifies data/seed_data.json conforms to all schema requirements."""

    def test_seed_file_exists_and_validates(self):
        assert SEED_FILE.exists(), f"Seed data file not found at {SEED_FILE}"
        with open(SEED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        standards = data.get("standards", [])
        qcos = data.get("qco_orders", [])

        assert len(standards) >= 50, f"Expected at least 50 standards, found {len(standards)}"
        assert len(qcos) >= 10, f"Expected at least 10 QCO orders, found {len(qcos)}"

        # Validate every standard through IndianStandard Pydantic model
        for s in standards:
            validated_std = IndianStandard.model_validate(s)
            assert validated_std.is_number.startswith("IS")
            assert len(validated_std.scope) >= 10
            assert validated_std.committee

        # Validate every QCO order through QCOOrder Pydantic model
        for q in qcos:
            validated_qco = QCOOrder.model_validate(q)
            assert validated_qco.mandatory_scheme in ["Scheme-I", "Scheme-II (CRS)", "Hallmarking", "Scheme-X"]
            assert len(validated_qco.applicable_standards) >= 1
