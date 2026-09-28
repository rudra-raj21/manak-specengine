"""
Comprehensive Test Suite for the 7 Enterprise Upgrades in Manak-SpecEngine:
1. Multi-Attribute Constraint Satisfaction & Slot-Filling (IS 456 / IS 1893)
2. Autonomous Standard BOM (5-Tier Statutory Procurement Bundle)
3. Domain Contrastive Reranking & Hard-Negative Discrimination
4. Schedule of Rates (CPWD DSR / MoRTH / GeM) Grounding
5. Entropy-Driven Active Disambiguation Clarifier
6. Tender Litigation & Pre-Bid Risk Analyzer (Legal Defensibility Index)
7. Multi-Tier Value Engineering Matrix (Fit-for-Purpose Grade Optimizer)
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.constraint_slot_service import ConstraintSlotService
from backend.app.services.standard_bom_service import StandardBOMService
from backend.app.services.domain_reranker import DomainReranker
from backend.app.services.schedule_of_rates_service import ScheduleOfRatesService
from backend.app.services.disambiguation_service import DisambiguationService
from backend.app.services.litigation_risk_service import LitigationRiskService
from backend.app.services.value_engineering_service import ValueEngineeringService
from backend.app.services.retrieval import get_hybrid_retriever

client = TestClient(app)


class TestDimension1ConstraintSlotFilling:
    """Verifies precision multi-attribute engineering and environmental slot extraction."""

    def test_coastal_seismic_v_slot_extraction(self):
        query = "Fe 500D steel rebar for coastal bridge pier foundation in Seismic Zone V"
        slots = ConstraintSlotService.extract_slots(query)

        assert slots["exposure_class"] == "severe"
        assert slots["seismic_zone"] == "zone v"
        assert slots["corrosion_environment"] == "marine_coastal"
        assert slots["infrastructure_type"] == "bridge"
        assert slots["requires_crs"] is True
        assert slots["requires_ductility"] is True
        assert slots["grade_hint"] == "Fe 500D"

    def test_potable_drinking_water_slot_extraction(self):
        query = "HDPE pipes 110mm working pressure 10 bar for potable drinking water transmission"
        slots = ConstraintSlotService.extract_slots(query)

        assert slots["infrastructure_type"] == "water_supply"
        assert slots["pressure_rating"] == "10 BAR"

    def test_constraint_bonuses_prioritize_correct_standards(self):
        slots = {
            "requires_crs": True,
            "requires_ductility": True,
            "infrastructure_type": "bridge",
            "exposure_class": "severe"
        }
        rebar_bonus = ConstraintSlotService.evaluate_constraint_bonus(
            "IS_1786", "High Strength Deformed Steel Bars", "Specification for rebars", slots
        )
        ductile_bonus = ConstraintSlotService.evaluate_constraint_bonus(
            "IS_13920", "Ductile Design and Detailing", "Seismic detailing code", slots
        )
        sewer_bonus = ConstraintSlotService.evaluate_constraint_bonus(
            "IS_458", "Precast Concrete Pipes", "Sewerage pipes", {"infrastructure_type": "water_supply"}
        )

        assert rebar_bonus > 0.50
        assert ductile_bonus >= 0.60
        assert sewer_bonus < 0.0  # Penalized for potable water


class TestDimension2StandardBOM:
    """Verifies 5-tier statutory procurement bundles."""

    def test_is_1786_bom_structure(self):
        bom = StandardBOMService.generate_bom("IS_1786")
        assert "tier_1_product" in bom
        assert "tier_2_code_of_practice" in bom
        assert "tier_3_testing_protocols" in bom
        assert "tier_4_sampling_and_inspection" in bom
        assert "tier_5_marking_and_delivery" in bom

        # Check Tier 1
        assert "IS 1786:2008" in bom["tier_1_product"]["standard"]
        assert "Fe 500D" in bom["tier_1_product"]["recommended_grade"]

        # Check Tier 2 companion codes
        codes = [c["standard"] for c in bom["tier_2_code_of_practice"]]
        assert any("IS 456" in c for c in codes)
        assert any("IS 13920" in c for c in codes)

        # Check Tier 3 tests
        tests = [t["standard"] for t in bom["tier_3_testing_protocols"]]
        assert any("IS 1608" in t for t in tests)
        assert any("IS 1599" in t for t in tests)

        # Check Tier 4 sampling
        assert "IS 4987" in bom["tier_4_sampling_and_inspection"]["standard"]
        assert "50 metric tonnes" in bom["tier_4_sampling_and_inspection"]["batch_frequency"]

    def test_is_2062_structural_steel_bom(self):
        bom = StandardBOMService.generate_bom("IS_2062")
        assert "IS 2062:2011" in bom["tier_1_product"]["standard"]
        codes = [c["standard"] for c in bom["tier_2_code_of_practice"]]
        assert any("IS 800" in c for c in codes)
        tests = [t["standard"] for t in bom["tier_3_testing_protocols"]]
        assert any("IS 1757" in t for t in tests)  # Charpy impact test


class TestDimension3DomainReranker:
    """Verifies contrastive reranking and hard-negative penalties."""

    def test_hard_negative_penalization_rebar_vs_structural(self):
        candidates = [
            {"standard_id": "IS_2062", "title": "Structural Steel", "score": 0.85},
            {"standard_id": "IS_1786", "title": "High Strength Deformed Steel Bars", "score": 0.80}
        ]
        reranked = DomainReranker.rerank("Fe 500D rebar for RCC", candidates)
        # IS 1786 should be boosted to #1 because of 'rebar' and 'Fe 500D'
        assert reranked[0]["standard_id"] == "IS_1786"

    def test_hard_negative_penalization_drinking_water_vs_sewer(self):
        candidates = [
            {"standard_id": "IS_458", "title": "Precast Concrete Pipes for Sewerage", "score": 0.90},
            {"standard_id": "IS_4984", "title": "High Density Polyethylene Pipes for Water Supply", "score": 0.85}
        ]
        reranked = DomainReranker.rerank("drinking water supply pipeline", candidates)
        # IS 4984 should be boosted to #1, IS 458 penalized
        assert reranked[0]["standard_id"] == "IS_4984"


class TestDimension4ScheduleOfRatesGrounding:
    """Verifies CPWD DSR, MoRTH, and GeM grounding index."""

    def test_cpwd_dsr_item_3_1_grounding(self):
        res = ScheduleOfRatesService.ground_query("CPWD Item 3.1 steel reinforcement work")
        assert res is not None
        assert "Subhead 3: Steel Work" in res["schedule"]
        assert "IS 1786:2008" in res["prescribed_standard"]
        assert "Manufacturer Test Certificate" in res["mandatory_compliance"][1]

    def test_morth_section_1600_grounding(self):
        res = ScheduleOfRatesService.ground_query("MoRTH Section 1600 girder fabrication")
        assert res is not None
        assert "MoRTH" in res["schedule"]
        assert "IS 2062" in res["prescribed_standard"]


class TestDimension5ActiveDisambiguation:
    """Verifies entropy detection and multi-choice clarification dialogue."""

    def test_underspecified_pipe_query_triggers_clarification(self):
        res = DisambiguationService.check_ambiguity("pipe", candidates=[])
        assert res is not None
        assert res["is_ambiguous"] is True
        assert res["domain"] == "pipe"
        assert len(res["options"]) >= 4
        # Options must cover potable, ductile, upvc, and sewer
        standards = [opt["standard_id"] for opt in res["options"]]
        assert "IS_4984" in standards
        assert "IS_8329" in standards
        assert "IS_4985" in standards
        assert "IS_458" in standards

    def test_precise_query_does_not_trigger_ambiguity(self):
        res = DisambiguationService.check_ambiguity("IS 1786 Fe 500D TMT rebar", candidates=[])
        assert res is None


class TestDimension6LitigationRiskAnalyzer:
    """Verifies Legal Defensibility Index (0–100) and pre-bid risk detection."""

    def test_blast_furnace_only_litigation_trap(self):
        text = "Supply of TMT bars. All bidders must be primary producers having blast furnace route only."
        risk = LitigationRiskService.analyze_tender_risk(text)

        assert risk["defensibility_score"] < 85
        assert risk["risk_rating"] != "WATERTIGHT (LOW LITIGATION RISK)"
        categories = [f["risk_category"] for f in risk["findings"]]
        assert "COMPETITION_RESTRICTION" in categories

    def test_unqualified_foreign_standard_trap(self):
        text = "Steel reinforcement conforming strictly to ASTM A615 Grade 60."
        risk = LitigationRiskService.analyze_tender_risk(text)

        assert risk["defensibility_score"] < 90
        categories = [f["risk_category"] for f in risk["findings"]]
        assert "PUBLIC_PROCUREMENT_MII_VIOLATION" in categories

    def test_compliant_safe_harbor_clause_is_watertight(self):
        text = (
            "High Strength Deformed Steel Bars conforming to IS 1786:2008 Grade Fe 500D. "
            "All supplies must bear the mandatory BIS Certification Mark (ISI Mark) with valid CM/L license. "
            "Produced by primary or BIS approved re-rollers conforming to Rule 144(i) GFR 2017."
        )
        risk = LitigationRiskService.analyze_tender_risk(text)
        assert risk["defensibility_score"] >= 90
        assert "WATERTIGHT" in risk["risk_rating"]


class TestDimension7ValueEngineeringOptimizer:
    """Verifies 3-tier comparative value engineering matrices."""

    def test_is_1786_value_engineering_tiers(self):
        tiers = ValueEngineeringService.get_value_engineering_matrix("IS_1786")
        assert len(tiers) == 3

        tier1 = tiers[0]
        assert "Fe 415D" in tier1["grade"]
        assert "1.00x" in tier1["initial_cost_index"]

        tier2 = tiers[1]
        assert "Fe 500D" in tier2["grade"]
        assert "RECOMMENDED" in tier2["tier"]
        assert "15% - 20%" in tier2["structural_weight_saving"]

        tier3 = tiers[2]
        assert "Fe 550D CRS" in tier3["grade"]
        assert "100+ Years" in tier3["lifecycle_durability"]


class TestEndToEndAPIEnhancements:
    """Verifies that FastAPI /api/recommend returns all 7 enterprise dimensions in one unified response."""

    def test_recommend_endpoint_includes_all_dimensions(self):
        res = client.post("/api/recommend", json={"query": "Fe 500D rebar for coastal bridge in seismic zone V"})
        assert res.status_code == 200
        data = res.json()

        # Dimension 1: Extracted constraints
        assert "extracted_constraints" in data
        assert data["extracted_constraints"]["requires_crs"] is True
        assert data["extracted_constraints"]["seismic_zone"] == "zone v"

        # Dimension 2: Standard BOM
        assert "standard_bom" in data
        assert "tier_1_product" in data["standard_bom"]
        assert "tier_3_testing_protocols" in data["standard_bom"]

        # Dimension 3: Domain Reranking (IS 1786 is #1)
        assert data["primary_match"]["standard_id"] == "IS_1786"

        # Dimension 4: Schedule of Rates
        assert "schedule_of_rates" in data

        # Dimension 5: Disambiguation
        assert "disambiguation" in data

        # Dimension 6: Litigation Risk
        assert "litigation_risk" in data
        assert "defensibility_score" in data["litigation_risk"]

        # Dimension 7: Value Engineering
        assert "value_engineering" in data
        assert len(data["value_engineering"]) >= 3

    def test_dedicated_bom_endpoint(self):
        res = client.get("/api/bom/IS_1786")
        assert res.status_code == 200
        assert "tier_1_product" in res.json()

    def test_dedicated_rates_grounding_endpoint(self):
        res = client.get("/api/rates/ground?query=CPWD+Item+3.1")
        assert res.status_code == 200
        assert res.json()["matched"] is True

    def test_dedicated_value_engineering_endpoint(self):
        res = client.get("/api/value-engineering/IS_2062")
        assert res.status_code == 200
        assert len(res.json()["tiers"]) == 3

    def test_dedicated_litigation_analysis_endpoint(self):
        res = client.post("/api/litigation/analyze", json={"text": "Only primary blast furnace producers allowed"})
        assert res.status_code == 200
        assert res.json()["defensibility_score"] < 85
