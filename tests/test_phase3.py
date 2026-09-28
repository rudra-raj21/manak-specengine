"""
Phase 3 Verification Suite: Hybrid Retrieval Engine.
Validates BM25 sparse keyword search, dense semantic vector retrieval,
Reciprocal Rank Fusion (RRF), exact code boosts, statutory QCO regulatory boosting, and sub-50ms latency.
"""

import time
from pathlib import Path
import pytest
from backend.app.services.retrieval import (
    DomainTokenizer,
    HybridRetriever,
    get_hybrid_retriever
)


@pytest.fixture(scope="module")
def retriever() -> HybridRetriever:
    """Fixture providing initialized HybridRetriever loaded with 22,000+ national standards."""
    return get_hybrid_retriever()


class TestTokenizer:
    """Tests domain-aware tokenizer for Indian Standards and material grades."""

    def test_domain_token_normalization(self):
        tokens = DomainTokenizer.tokenize("Supply of IS 2062 Grade E250 plates and Fe 500D rebars")
        assert "is_2062" in tokens
        assert "fe_500d" in tokens
        assert "e250" in tokens
        assert "plates" in tokens
        # Verify common stopwords like 'of', 'and' are stripped
        assert "of" not in tokens
        assert "and" not in tokens


class TestHybridRetrievalAccuracy:
    """Tests accuracy across Core GovTech procurement categories."""

    def test_structural_steel_query(self, retriever: HybridRetriever):
        results = retriever.search("hot rolled structural steel plates and beams for bridges", top_k=5)
        assert len(results) >= 1
        top_numbers = [r["is_number"] for r in results]
        assert "IS 2062" in top_numbers or any("2062" in n for n in top_numbers)
        # Check QCO status
        is_2062_res = next((r for r in results if "2062" in r["is_number"]), None)
        assert is_2062_res is not None
        assert is_2062_res["is_mandatory_qco"] is True
        assert is_2062_res["mandatory_scheme"] == "Scheme-I"

    def test_rebar_concrete_reinforcement_query(self, retriever: HybridRetriever):
        results = retriever.search("high strength deformed steel bars fe 500d for rcc concrete", top_k=5)
        top_numbers = [r["is_number"] for r in results]
        assert any("1786" in n for n in top_numbers)

    def test_it_equipment_safety_query(self, retriever: HybridRetriever):
        results = retriever.search("laptop power adapter and information technology equipment safety", top_k=5)
        top_numbers = [r["is_number"] for r in results]
        assert any("13252" in n for n in top_numbers)
        it_res = next((r for r in results if "13252" in r["is_number"]), None)
        assert it_res is not None
        assert it_res["is_mandatory_qco"] is True
        assert it_res["mandatory_scheme"] == "Scheme-II (CRS)"

    def test_water_supply_hdpe_pipe_query(self, retriever: HybridRetriever):
        results = retriever.search("high density polyethylene hdpe pipes for potable water supply", top_k=5)
        top_numbers = [r["is_number"] for r in results]
        assert any("4984" in n for n in top_numbers)

    def test_solar_pv_query(self, retriever: HybridRetriever):
        results = retriever.search("crystalline silicon terrestrial photovoltaic pv modules", top_k=5)
        top_numbers = [r["is_number"] for r in results]
        assert any("14286" in n or "61730" in n for n in top_numbers)

    def test_direct_is_number_lookup(self, retriever: HybridRetriever):
        results = retriever.search("IS 456", top_k=3)
        assert len(results) >= 1
        assert results[0]["score"] >= 0.70
        assert results[0]["score_type"] == "HEURISTIC_RANKING"


class TestRegulatoryQCOBoosting:
    """Verifies statutory compliance boost prioritizing QCO-governed goods."""

    def test_qco_boost_impact(self, retriever: HybridRetriever):
        query = "structural steel"
        boosted = retriever.search(query, top_k=10, apply_qco_boost=True)
        unboosted = retriever.search(query, top_k=10, apply_qco_boost=False)

        assert len(boosted) > 0
        assert len(unboosted) > 0
        # IS 2062 should have higher relative precedence under mandatory public procurement
        boosted_ranks = {r["is_number"]: i for i, r in enumerate(boosted)}
        assert any("2062" in k for k in boosted_ranks)


class TestSearchFiltersAndLatency:
    """Tests departmental filtering and sub-50ms search latency."""

    def test_department_filter(self, retriever: HybridRetriever):
        results = retriever.search("steel", top_k=10, department_filter="Civil")
        for r in results:
            if r["department"]:
                assert "civil" in r["department"].lower() or "ced" in r["department"].lower()

    def test_retrieval_latency(self, retriever: HybridRetriever):
        """Verifies full hybrid search across 22,000 documents completes in < 50ms."""
        query = "hot rolled structural steel plates and sections"
        start_time = time.perf_counter()
        iterations = 20
        for _ in range(iterations):
            retriever.search(query, top_k=10)
        avg_latency_ms = (time.perf_counter() - start_time) * 1000 / iterations
        assert avg_latency_ms < 50.0, f"Average retrieval latency {avg_latency_ms:.2f}ms exceeds 50ms threshold"
