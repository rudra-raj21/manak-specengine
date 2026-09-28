"""
Phase 6 Verification Suite: FastAPI REST API & GovTech Endpoints.
Validates /health, /api/recommend, /api/audit, /api/graph, /api/qcos, and /api/samples endpoints.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

TENDERS_DIR = Path(__file__).resolve().parent.parent / "data" / "gem_tender_samples"


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Fixture providing initialized FastAPI TestClient."""
    return TestClient(app)


class TestFastAPIEndpoints:
    """Tests complete REST API suite for GovTech integration."""

    def test_health_endpoint(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Manak-SpecEngine"
        assert data["standards_indexed"] >= 20000
        assert data["qco_orders_active"] >= 180
        assert data["graph_relationships"] >= 7900

    def test_recommend_endpoint_structural_steel(self, client: TestClient):
        payload = {
            "query": "Hot rolled structural steel plates Grade E250 for bridge trusses",
            "department": "Civil",
            "tender_type": "GeM",
            "top_k": 5
        }
        response = client.post("/api/recommend", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "candidate_standards" in data
        assert len(data["candidate_standards"]) >= 1

        top_is = [c["is_number"] for c in data["candidate_standards"]]
        assert any("2062" in s for s in top_is)

        # Check governing QCO
        assert data["governing_qco"] is not None
        assert "Steel" in data["governing_qco"]["order_name"]

        # Check synthesized tender clause
        clause = data["synthesis"]["tender_clause"]
        assert "IS 2062:2011" in clause or "IS 2062" in clause
        assert "Section 29" in clause

        # Check graph visualization attached
        assert "graph_visualization" in data
        assert data["graph_visualization"]["total_nodes"] >= 5

    def test_recommend_endpoint_hindi_query(self, client: TestClient):
        payload = {
            "query": "पुल निर्माण के लिए संरचनात्मक इस्पात",
            "top_k": 5
        }
        response = client.post("/api/recommend", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["indic_info"]["is_indic"] is True
        assert data["indic_info"]["language"] == "hi"
        assert any("2062" in c["is_number"] for c in data["candidate_standards"])

    def test_audit_endpoint_cpwd_trap(self, client: TestClient):
        file_path = TENDERS_DIR / "cpwd_structural_steel_trap_spec.txt"
        assert file_path.exists()
        raw_text = file_path.read_text(encoding="utf-8")

        payload = {
            "raw_text": raw_text,
            "tender_id": "GEM/2026/B/543210",
            "tender_title": "CPWD Shed Steel Tender",
            "department": "CPWD"
        }
        response = client.post("/api/audit", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["compliance_score"] < 60
        assert data["status_color"] == "red"
        assert data["qco_compliant"] is False
        assert len(data["findings"]) >= 2
        assert "CORRIGENDUM / AMENDMENT" in data["corrigendum_notice"]
        assert len(data["graph_visualization"]["nodes"]) >= 1

    def test_audit_endpoint_nhai_compliant(self, client: TestClient):
        file_path = TENDERS_DIR / "nhai_bridge_rebar_spec.txt"
        assert file_path.exists()
        raw_text = file_path.read_text(encoding="utf-8")

        payload = {
            "raw_text": raw_text,
            "tender_id": "GEM/2026/B/890123",
            "tender_title": "NHAI Bridge Rebar",
            "department": "NHAI"
        }
        response = client.post("/api/audit", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["compliance_score"] >= 85
        assert data["status_color"] == "green"
        assert data["qco_compliant"] is True
        assert len(data["deprecated_standards"]) == 0

    def test_graph_neighborhood_endpoint(self, client: TestClient):
        response = client.get("/api/graph/IS_2062?max_nodes=30")
        assert response.status_code == 200
        data = response.json()
        assert data["root_id"] == "IS_2062"
        assert data["total_nodes"] >= 5
        assert data["total_links"] >= 5

    def test_qco_directory_endpoint(self, client: TestClient):
        response = client.get("/api/qcos")
        assert response.status_code == 200
        qcos = response.json()
        assert len(qcos) >= 180

        # Ministry filter
        steel_response = client.get("/api/qcos?ministry=Steel")
        assert steel_response.status_code == 200
        steel_qcos = steel_response.json()
        assert len(steel_qcos) >= 1

    def test_samples_endpoint(self, client: TestClient):
        response = client.get("/api/samples")
        assert response.status_code == 200
        data = response.json()
        assert len(data["mode_a_recommendation_queries"]) >= 5
        assert len(data["mode_b_audit_tender_traps"]) >= 5
