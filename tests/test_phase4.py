"""
Phase 4 Verification Suite: Multilingual Indic Translation & Gemini LLM Synthesizer.
Validates regional Indic query transliteration, grounded technical tender clause generation,
statutory penal clause formulation, and prompt construction.
"""

from pathlib import Path
import pytest
from backend.app.services.llm_synthesizer import (
    IndicNormalizer,
    LLMSynthesizer,
    get_llm_synthesizer
)


class TestIndicNormalizer:
    """Tests regional Indian language detection and procurement vocabulary mapping."""

    def test_hindi_tmt_and_steel_query(self):
        text = "पुल निर्माण के लिए संरचनात्मक इस्पात और टीएमटी सरिया"
        res = IndicNormalizer.detect_and_normalize(text)
        assert res["is_indic"] is True
        assert res["language"] == "hi"
        norm_q = res["normalized_query"]
        assert "IS 2062" in norm_q or "structural steel" in norm_q
        assert "IS 1786" in norm_q or "tmt" in norm_q

    def test_hindi_hdpe_pipe_query(self):
        text = "ग्राम जल आपूर्ति के लिए पीने का पानी पाइप"
        res = IndicNormalizer.detect_and_normalize(text)
        assert res["is_indic"] is True
        assert "IS 4984" in res["normalized_query"] or "hdpe" in res["normalized_query"]

    def test_hindi_wire_and_cable_query(self):
        text = "भवन निर्माण हेतु बिजली का तार और सुरक्षा हेलमेट"
        res = IndicNormalizer.detect_and_normalize(text)
        assert res["is_indic"] is True
        assert "IS 694" in res["normalized_query"]
        assert "IS 2925" in res["normalized_query"]

    def test_english_passthrough(self):
        text = "Supply of 500 MT of hot rolled medium tensile steel plates"
        res = IndicNormalizer.detect_and_normalize(text)
        assert res["is_indic"] is False
        assert res["language"] == "en"
        assert res["normalized_query"] == text


class TestTenderClauseSynthesis:
    """Tests formulation of legally binding procurement clauses."""

    @pytest.fixture
    def synthesizer(self) -> LLMSynthesizer:
        return get_llm_synthesizer()

    def test_steel_tender_clause_synthesis(self, synthesizer: LLMSynthesizer):
        primary_std = {
            "is_number": "IS 2062",
            "title": "Hot Rolled Medium and High Tensile Structural Steel",
            "year": 2011,
            "department": "Civil Engineering",
            "status": "ACTIVE"
        }
        qco = {
            "order_name": "Steel and Steel Products (Quality Control) Order, 2024",
            "ministry": "Ministry of Steel",
            "mandatory_scheme": "Scheme-I",
            "effective_date": "2024-06-01"
        }
        test_stds = ["IS 1608:2005", "IS 1599", "IS 1757", "IS 228"]
        norm_stds = ["IS 808", "IS 1852", "IS 8910"]

        result = synthesizer.synthesize_tender_clause(
            query="Procurement of structural steel for railway foot over bridge",
            primary_standard=primary_std,
            normative_references=norm_stds,
            test_standards=test_stds,
            qco_mandate=qco,
            tender_type="GeM"
        )

        assert result["primary_standard"]["is_number"] == "IS 2062"
        assert result["statutory_qco_compliance"]["is_mandatory"] is True
        assert result["statutory_qco_compliance"]["mandatory_scheme"] == "Scheme-I"
        assert len(result["mandatory_testing_standards"]) >= 1

        clause_text = result["tender_clause"]
        assert "IS 2062:2011" in clause_text
        assert "Section 29" in clause_text
        assert "SPECIAL TERMS & CONDITIONS" in clause_text
        assert "Steel and Steel Products (Quality Control) Order" in clause_text

    def test_it_equipment_crs_clause_synthesis(self, synthesizer: LLMSynthesizer):
        primary_std = {
            "is_number": "IS 13252 (Part 1)",
            "title": "Information Technology Equipment - Safety",
            "year": 2010,
            "department": "Electronics and IT",
            "status": "ACTIVE"
        }
        qco = {
            "order_name": "Electronics IT Goods Order",
            "ministry": "MeitY",
            "mandatory_scheme": "Scheme-II (CRS)",
            "effective_date": "2021-10-01"
        }

        result = synthesizer.synthesize_tender_clause(
            query="Desktop computers and power supply units",
            primary_standard=primary_std,
            normative_references=["IS 616"],
            test_standards=["IS 302"],
            qco_mandate=qco,
            tender_type="CPWD"
        )

        assert result["statutory_qco_compliance"]["mandatory_scheme"] == "Scheme-II (CRS)"
        clause_text = result["tender_clause"]
        assert "Scheme-II" in clause_text or "CRS" in clause_text

    def test_prompt_grounding_integrity(self, synthesizer: LLMSynthesizer):
        prompt = synthesizer._build_synthesis_prompt(
            query="Supply of Portland Cement",
            is_num="IS 269",
            title="Ordinary Portland Cement",
            year=2015,
            dept="Civil Engineering",
            test_stds_str="IS 4031",
            has_qco=True,
            qco_name="Cement QCO",
            qco_ministry="DPIIT",
            qco_scheme="Scheme-I",
            tender_type="GeM"
        )
        assert "IS 269:2015" in prompt
        assert "Ordinary Portland Cement" in prompt
        assert "Cement QCO" in prompt
        assert "DPIIT" in prompt
