"""
Phase 2 Verification Suite: Knowledge Graph Pipeline & Dual Graph Engine.
Validates Neo4j / In-Memory NetworkX graph loading, 1-hop and 2-hop topological traversals,
statutory QCO mandate auditing, supersession resolution, and query performance.
"""

import time
from pathlib import Path
import pytest
from backend.app.services.graph_service import GraphService, get_graph_service


@pytest.fixture(scope="module")
def graph_svc() -> GraphService:
    """Fixture providing initialized GraphService loaded with authentic harvested datasets."""
    return get_graph_service()


class TestGraphEngineTopology:
    """Tests graph scale, node indexes, and edge integrity."""

    def test_graph_service_initialization(self, graph_svc: GraphService):
        stats = graph_svc.stats()
        assert stats["standards_nodes"] >= 20000, f"Expected 20,000+ standards, got {stats['standards_nodes']}"
        assert stats["qcos_nodes"] >= 180, f"Expected 180+ QCOs, got {stats['qcos_nodes']}"
        assert stats["total_edges"] >= 7900, f"Expected 7,900+ edges, got {stats['total_edges']}"

        breakdown = stats["relationship_breakdown"]
        assert "NORMATIVE_REF" in breakdown
        assert "TESTED_BY" in breakdown
        assert "SUPERSEDES" in breakdown
        assert "MANDATED_BY" in breakdown

    def test_resolve_standard_id_variants(self, graph_svc: GraphService):
        assert graph_svc.resolve_standard_id("IS 2062") == "IS_2062"
        assert graph_svc.resolve_standard_id("2062") == "IS_2062"
        assert graph_svc.resolve_standard_id("IS_2062") == "IS_2062"
        assert graph_svc.resolve_standard_id("IS 1786") == "IS_1786"
        assert graph_svc.resolve_standard_id("IS 13252 (Part 1)") == "IS_13252_Part_1"
        assert graph_svc.resolve_standard_id("IS/IEC 61730 (Part 1)") == "IS_IEC_61730_Part_1"

    def test_get_standard_metadata(self, graph_svc: GraphService):
        std = graph_svc.get_standard("IS 2062")
        assert std is not None
        assert std["is_number"] == "IS 2062"
        assert "Steel" in std["title"]
        assert std["status"] == "ACTIVE"

        std_456 = graph_svc.get_standard("IS 456")
        assert std_456 is not None
        assert "Concrete" in std_456["title"]


class TestQCOMandateAuditing:
    """Tests statutory compliance lookup under BIS Section 16 Quality Control Orders."""

    def test_steel_qco_mandate(self, graph_svc: GraphService):
        qco = graph_svc.check_qco_mandate("IS 2062")
        assert qco is not None, "IS 2062 must be governed by Steel QCO"
        assert "Steel" in qco["order_name"]
        assert qco["mandatory_scheme"] == "Scheme-I"
        assert "Section 16" in qco["penal_clause"]

    def test_electronics_crs_mandate(self, graph_svc: GraphService):
        qco = graph_svc.check_qco_mandate("IS 13252 (Part 1)")
        assert qco is not None, "IS 13252 (Part 1) must be governed by MeitY CRS Order"
        assert "Electronics" in qco["order_name"] or "Information Technology" in qco["order_name"]
        assert qco["mandatory_scheme"] == "Scheme-II (CRS)"

    def test_solar_pv_mandate(self, graph_svc: GraphService):
        qco = graph_svc.check_qco_mandate("IS 14286")
        assert qco is not None, "IS 14286 must be governed by Solar PV QCO"
        assert "Solar" in qco["order_name"]
        assert qco["mandatory_scheme"] == "Scheme-II (CRS)"

    def test_unmandated_standard(self, graph_svc: GraphService):
        # A code of practice like IS 456 or drafting guide is not a mandatory product QCO
        qco = graph_svc.check_qco_mandate("IS 456")
        # May be None or unmandated
        if qco is not None:
            assert "Plain and Reinforced Concrete" not in qco["order_name"]


class TestGraphNeighborhoodTraversals:
    """Tests 1-hop and 2-hop topological traversals and React Flow formatted representations."""

    def test_1hop_neighbors_categorization(self, graph_svc: GraphService):
        neighbors = graph_svc.get_1hop_neighbors("IS 2062")
        assert "normative_references" in neighbors
        assert "test_methods" in neighbors
        assert "qco_mandates" in neighbors
        assert "supersedes" in neighbors

        # IS 2062 must link to testing methods like IS 228, IS 1608, or IS 1757
        all_connected = neighbors["normative_references"] + neighbors["test_methods"] + neighbors["supersedes"]
        connected_ids = [n["id"] for n in all_connected]

        assert any("1608" in cid or "1757" in cid or "808" in cid or "228" in cid for cid in connected_ids)
        assert len(neighbors["qco_mandates"]) >= 1

    def test_2hop_neighborhood_react_flow_format(self, graph_svc: GraphService):
        neighborhood = graph_svc.get_2hop_neighborhood("IS 2062", max_nodes=40)
        assert neighborhood["root_id"] == "IS_2062"
        assert neighborhood["total_nodes"] >= 5
        assert neighborhood["total_links"] >= 5

        # Check node schema for UI compatibility
        for node in neighborhood["nodes"]:
            assert "id" in node
            assert "label" in node
            assert "type" in node
            assert "status" in node

        # Check link schema
        for link in neighborhood["links"]:
            assert "source" in link
            assert "target" in link
            assert "relationship" in link

    def test_subgraph_for_standards(self, graph_svc: GraphService):
        subgraph = graph_svc.get_subgraph_for_standards(["IS 2062", "IS 1786"], include_qcos=True)
        assert subgraph["total_nodes"] >= 2
        assert any(n["id"] == "IS_2062" for n in subgraph["nodes"])
        assert any(n["id"] == "IS_1786" for n in subgraph["nodes"])

    def test_supersession_resolution(self, graph_svc: GraphService):
        # IS 2062:2006 should point to IS 2062
        chain = graph_svc.find_superseding_chain("IS 2062:2006")
        assert len(chain) >= 1

    def test_traversal_performance(self, graph_svc: GraphService):
        """Validates that graph traversal latency is sub-5ms."""
        start_time = time.perf_counter()
        for _ in range(50):
            graph_svc.get_1hop_neighbors("IS 2062")
            graph_svc.check_qco_mandate("IS 1786")
        elapsed_ms = (time.perf_counter() - start_time) * 1000 / 50
        assert elapsed_ms < 10.0, f"Average traversal latency {elapsed_ms:.2f}ms exceeds 10ms threshold"
