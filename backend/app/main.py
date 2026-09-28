"""
FastAPI Application Entrypoint for Manak-SpecEngine.
Serves GovTech REST API endpoints for:
- Mode A: Smart Standard Finder & Grounded Tender Clause Synthesizer
- Mode B: Automated Tender Specification Auditor & Redline Compliance Checker
- Knowledge Graph Topological Traversal & React Flow Canvas
- Directory of Statutory Quality Control Orders (QCOs)
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.services.graph_service import get_graph_service, GraphService
from backend.app.services.retrieval import get_hybrid_retriever, HybridRetriever
from backend.app.services.llm_synthesizer import get_llm_synthesizer, IndicNormalizer, LLMSynthesizer
from backend.app.services.auditor import get_tender_auditor, TenderAuditor
from backend.app.services.sarvam_service import get_sarvam_service, SarvamAIService
from backend.app.services.clause_service import get_clause_service
from backend.app.services.cml_verifier import get_cml_verifier
from backend.app.services.document_parser import extract_text_from_file, generate_official_corrigendum_document
from backend.app.services.graph_explorer_service import get_graph_explorer_service
from backend.app.services.constraint_slot_service import ConstraintSlotService
from backend.app.services.standard_bom_service import StandardBOMService
from backend.app.services.schedule_of_rates_service import ScheduleOfRatesService
from backend.app.services.disambiguation_service import DisambiguationService
from backend.app.services.litigation_risk_service import LitigationRiskService
from backend.app.services.value_engineering_service import ValueEngineeringService
from backend.app.api.v1.endpoints.multilingual import router as multilingual_router

app = FastAPI(
    title="Manak-SpecEngine API",
    description="Enterprise GovTech AI Recommendation & Compliance Verification Engine for Bureau of Indian Standards (BIS)",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(multilingual_router, prefix="/api/v1")
app.include_router(multilingual_router, prefix="/api")

# Global service references
graph_svc: Optional[GraphService] = None
retriever_svc: Optional[HybridRetriever] = None
synthesizer_svc: Optional[LLMSynthesizer] = None
auditor_svc: Optional[TenderAuditor] = None
sarvam_svc: Optional[SarvamAIService] = None


@app.on_event("startup")
def startup_event():
    """Pre-warms in-memory indices and graph topology."""
    global graph_svc, retriever_svc, synthesizer_svc, auditor_svc, sarvam_svc
    graph_svc = get_graph_service()
    retriever_svc = get_hybrid_retriever(graph_service=graph_svc)
    synthesizer_svc = get_llm_synthesizer()
    auditor_svc = get_tender_auditor(graph_service=graph_svc)
    sarvam_svc = get_sarvam_service()
    print("Manak-SpecEngine services successfully initialized on startup.")


# ------------------------------------------------------------------------------
# Request / Response Schemas
# ------------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Procurement requirement or technical description")
    department: Optional[str] = Field(default=None, description="Filter by BIS Division/Department")
    tender_type: Optional[str] = Field(default="GeM", description="'GeM', 'CPWD', 'Railways', 'NHAI'")
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    language_code: Optional[str] = Field(default=None, description="Optional ISO/BCP-47 language code e.g. hi-IN, ta-IN")


class AuditRequest(BaseModel):
    raw_text: str = Field(..., min_length=5, description="Full tender specification text or notice inviting tender (NIT)")
    tender_id: Optional[str] = Field(default=None, description="Optional tender ID, e.g. GEM/2026/B/12345")
    tender_title: Optional[str] = Field(default=None, description="Optional tender description or title")
    department: Optional[str] = Field(default=None, description="Issuing authority, e.g. CPWD, DDA, NHAI")


# ------------------------------------------------------------------------------
# REST Endpoints
# ------------------------------------------------------------------------------

@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Returns engine health and topological scale metrics."""
    global graph_svc
    if graph_svc is None:
        graph_svc = get_graph_service()
    stats = graph_svc.stats()
    return {
        "status": "healthy",
        "service": "Manak-SpecEngine",
        "version": "1.0.0",
        "standards_indexed": stats["standards_nodes"],
        "qco_orders_active": stats["qcos_nodes"],
        "graph_relationships": stats["total_edges"],
        "neo4j_connected": stats["neo4j_connected"]
    }


@app.post("/api/recommend")
@app.post("/api/v1/recommend")
async def recommend_standards(req: RecommendRequest) -> Dict[str, Any]:
    """
    Mode A: Recommends authoritative Indian Standards, checks statutory QCO mandates,
    and synthesizes a ready-to-paste GovTech tender clause.
    Supports multilingual voice/text input via Sarvam AI.
    """
    global retriever_svc, graph_svc, synthesizer_svc, sarvam_svc
    if retriever_svc is None:
        retriever_svc = get_hybrid_retriever()
    if graph_svc is None:
        graph_svc = get_graph_service()
    if synthesizer_svc is None:
        synthesizer_svc = get_llm_synthesizer()
    if sarvam_svc is None:
        sarvam_svc = get_sarvam_service()

    # 1. Multilingual Indic Normalization on original input
    indic_info = IndicNormalizer.detect_and_normalize(req.query)

    # 2. Multilingual Voice/Text Processing with Sarvam AI
    multi_res = await sarvam_svc.process_multilingual_input(
        text=req.query,
        language_code=req.language_code
    )
    detected_lang = multi_res.get("detected_language", "en-IN")
    translated_en = multi_res.get("translated_english", req.query)
    normalized_q = multi_res.get("normalized_query", translated_en)

    language_metadata = {
        "original_query": req.query,
        "detected_language": detected_lang,
        "translated_english": translated_en,
        "normalized_query": normalized_q,
        "bypassed": multi_res.get("bypassed_translation", False),
        "provider": "Sarvam AI (mayura:v1)"
    }

    # Combine domain-expanded query from IndicNormalizer with Sarvam normalized query
    search_query = f"{indic_info['normalized_query']} {normalized_q}".strip() or req.query

    # 2.5. Pre-Ranking Standard Status & Supersession Resolution (Principle A)
    # Check if the query specifically cites a standard (especially obsolete/superseded/withdrawn)
    supersession_info = graph_svc.resolve_supersession(
        query_or_id=req.query,
        context_query=f"{req.query} {translated_en} {search_query}"
    )

    # If query cited an obsolete standard, route retrieval to the verified active replacement!
    active_search_query = search_query
    if supersession_info.get("is_superseded") and supersession_info.get("current_replacements"):
        primary_replacement = supersession_info["current_replacements"][0]
        rep_is_num = primary_replacement.get("standard", {}).get("is_number", "")
        if rep_is_num:
            active_search_query = f"{rep_is_num} {search_query}"

    # 3. Hybrid Retrieval with Strict Active-Standard Policy
    results = retriever_svc.search(
        query=active_search_query,
        top_k=req.top_k,
        department_filter=req.department,
        allow_superseded=False,  # Enforce active standards for recommendations
        apply_qco_boost=True
    )

    if not results:
        # Fallback to translated or raw query
        results = retriever_svc.search(
            query=translated_en or req.query,
            top_k=req.top_k,
            allow_superseded=False
        )

    if not results:
        raise HTTPException(status_code=404, detail="No matching Indian Standards found for this specification.")

    # 4. Graph Enrichment for Primary Standard
    top_match = results[0]
    sid = top_match["standard_id"]
    primary_std = graph_svc.get_standard(sid) or {
        "is_number": top_match["is_number"],
        "title": top_match["title"],
        "year": top_match.get("year"),
        "department": top_match.get("department", "Civil Engineering"),
        "status": top_match.get("status", "ACTIVE")
    }

    neighbors_1hop = graph_svc.get_1hop_neighbors(sid)
    normative_refs = [n["is_number"] for n in neighbors_1hop.get("normative_references", [])]
    test_methods = [n["is_number"] for n in neighbors_1hop.get("test_methods", [])]
    qco_mandate = graph_svc.evaluate_qco_applicability(sid)

    # 5. Synthesize Legal Tender Clause
    clause_payload = synthesizer_svc.synthesize_tender_clause(
        query=translated_en or req.query,
        primary_standard=primary_std,
        normative_references=normative_refs,
        test_standards=test_methods,
        qco_mandate=qco_mandate,
        tender_type=req.tender_type or "GeM"
    )

    # 6. Extract 2-Hop Graph Neighborhood for Visualizer
    graph_viz = graph_svc.get_2hop_neighborhood(sid, max_nodes=35)

    # 7. Enterprise Recommender Intelligence Layer
    # Use multilingual and translated text for accurate engineering slot extraction
    combined_query_for_slots = f"{req.query} {translated_en} {search_query}"
    slots = ConstraintSlotService.extract_slots(combined_query_for_slots)
    standard_bom = StandardBOMService.generate_bom(sid, graph_service=graph_svc)
    schedule_grounding = ScheduleOfRatesService.ground_query(req.query, top_standard_id=sid)
    value_engineering = ValueEngineeringService.get_value_engineering_matrix(sid)
    ambiguity_dialogue = DisambiguationService.check_ambiguity(req.query, results)
    litigation_risk = LitigationRiskService.analyze_tender_risk(
        clause_payload.get("raw_clause_text", "") + " " + req.query
    )

    top_score = top_match.get("score", 0.0)
    has_sufficient_confidence = top_match.get("has_sufficient_confidence", top_score >= 0.20)
    confidence_assessment = {
        "score": top_score,
        "confidence_level": top_match.get("confidence_level", "MEDIUM"),
        "has_sufficient_confidence": has_sufficient_confidence,
        "abstention_notice": None if has_sufficient_confidence else (
            "The query does not contain sufficient technical specifications or product details to make an authoritative recommendation with high confidence. Please provide additional constraints (e.g. grade, exposure class, application, dimensions)."
        )
    }

    evidence_explanation = {
        "match_rationale": f"Selected as the most relevant Indian Standard matching product type and application context.",
        "matched_constraints": top_match.get("applied_constraints", []),
        "grade_selection": slots.get("grade_hint") or "Standard default grade",
        "standard_status": primary_std.get("status", "ACTIVE"),
        "supersession_details": supersession_info if supersession_info.get("is_cited") else None,
        "qco_applicability": qco_mandate,
        "confidence": confidence_assessment
    }

    return {
        "input_query": req.query,
        "indic_info": indic_info,
        "language_metadata": language_metadata,
        "total_matches": len(results),
        "primary_match": top_match,
        "candidate_standards": results,
        "normative_references": normative_refs,
        "test_standards": test_methods,
        "governing_qco": qco_mandate,
        "synthesis": clause_payload,
        "graph_visualization": graph_viz,
        # Enterprise Upgrades
        "extracted_constraints": slots,
        "standard_bom": standard_bom,
        "schedule_of_rates": schedule_grounding,
        "value_engineering": value_engineering,
        "disambiguation": ambiguity_dialogue,
        "litigation_risk": litigation_risk,
        # Core Correctness & Provenance Additions
        "supersession_resolution": supersession_info,
        "confidence_assessment": confidence_assessment,
        "evidence_explanation": evidence_explanation
    }


@app.post("/api/audit")
def audit_tender(req: AuditRequest) -> Dict[str, Any]:
    """
    Mode B: Audits tender document for deprecated standards, missing statutory QCOs,
    omitted testing protocols, and foreign standard discrimination under PPP-MII.
    """
    global auditor_svc, graph_svc
    if auditor_svc is None:
        auditor_svc = get_tender_auditor()
    if graph_svc is None:
        graph_svc = get_graph_service()

    report = auditor_svc.audit_tender(
        raw_text=req.raw_text,
        tender_id=req.tender_id,
        tender_title=req.tender_title,
        department=req.department
    )

    # Attach legal defensibility & pre-bid risk analysis
    report["legal_defensibility"] = LitigationRiskService.analyze_tender_risk(req.raw_text)

    # Attach official corrigendum document
    report["official_corrigendum"] = generate_official_corrigendum_document(
        tender_id=req.tender_id or "GEM/2026/B/DEFAULT",
        tender_title=req.tender_title or "Tender Notice",
        department=req.department or "Public Procurement Entity",
        findings=report
    )

    # Attach subgraph connecting all referenced standards
    referenced = report.get("standards_referenced", [])
    if referenced:
        report["graph_visualization"] = graph_svc.get_subgraph_for_standards(
            identifiers=referenced,
            include_qcos=True,
            max_nodes=40
        )
    else:
        report["graph_visualization"] = {"nodes": [], "links": []}

    return report


@app.post("/api/audit/upload")
async def audit_uploaded_file(
    file: UploadFile = File(..., description="Tender document (.pdf, .txt, .docx)"),
    tender_id: Optional[str] = Query(default=None),
    tender_title: Optional[str] = Query(default=None),
    department: Optional[str] = Query(default=None)
) -> Dict[str, Any]:
    """
    Mode B: Ingests uploaded multi-page tender document (PDF or Text) directly,
    extracts specifications, and audits for compliance issues.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    raw_text = extract_text_from_file(file_bytes, file.filename or "tender.txt")
    if not raw_text or len(raw_text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Could not extract readable text from uploaded tender document.")

    global auditor_svc, graph_svc
    if auditor_svc is None:
        auditor_svc = get_tender_auditor()
    if graph_svc is None:
        graph_svc = get_graph_service()

    t_id = tender_id or f"GEM/2026/B/{file.filename.split('.')[0].upper()}"
    t_title = tender_title or f"Tender Specification: {file.filename}"
    dept = department or "CPWD / GeM Procurement"

    report = auditor_svc.audit_tender(
        raw_text=raw_text,
        tender_id=t_id,
        tender_title=t_title,
        department=dept
    )

    report["official_corrigendum"] = generate_official_corrigendum_document(
        tender_id=t_id,
        tender_title=t_title,
        department=dept,
        findings=report
    )

    referenced = report.get("standards_referenced", [])
    if referenced:
        report["graph_visualization"] = graph_svc.get_subgraph_for_standards(
            identifiers=referenced,
            include_qcos=True,
            max_nodes=40
        )
    else:
        report["graph_visualization"] = {"nodes": [], "links": []}

    return report


@app.post("/api/audit/corrigendum")
def generate_corrigendum_endpoint(req: AuditRequest) -> Dict[str, Any]:
    """Generates official Government of India Corrigendum Notice for the audited tender."""
    global auditor_svc
    if auditor_svc is None:
        auditor_svc = get_tender_auditor()

    report = auditor_svc.audit_tender(
        raw_text=req.raw_text,
        tender_id=req.tender_id,
        tender_title=req.tender_title,
        department=req.department
    )

    return generate_official_corrigendum_document(
        tender_id=req.tender_id or "GEM/2026/B/ONLINE",
        tender_title=req.tender_title or "Tender Notice",
        department=req.department or "Public Procurement Entity",
        findings=report
    )


@app.get("/api/clauses/{standard_id}")
def get_clause_breakdown(standard_id: str) -> Dict[str, Any]:
    """Returns granular engineering tables: chemical composition, mechanical properties, and test protocols."""
    svc = get_clause_service()
    res = svc.get_clause_details(standard_id)
    if not res:
        return {
            "is_number": standard_id,
            "title": f"Specification for {standard_id}",
            "current_revision": f"{standard_id} Active Edition",
            "grades": ["Standard Industrial Grade"],
            "chemical_composition": {
                "clause": "Clause 4 (Chemical Requirements)",
                "table_title": "Nominal Chemical Composition Limits",
                "columns": ["Constituent", "Specified Limit", "Test Method"],
                "rows": [
                    {"constituent": "Active Material Grade", "std": "Conforming to IS specification", "test": "Wet chemical analysis / XRF spectrometry"},
                    {"constituent": "Harmful Impurities", "std": "< 0.05% max", "test": "Spectrophotometric"}
                ]
            },
            "mechanical_properties": {
                "clause": "Clause 6 (Mechanical & Performance Requirements)",
                "table_title": "Acceptance Performance Criteria",
                "columns": ["Property", "Required Value", "Test Protocol"],
                "rows": [
                    {"property": "Ultimate Load / Strength", "val": "Meets 100% nominal rated capacity", "proto": "Proof load testing"},
                    {"property": "Safety Factor", "val": ">= 1.5x minimum", "proto": "Destructive / type sample testing"}
                ]
            },
            "testing_protocols": [
                {"test_name": "Routine Quality Inspection Test", "clause": "Clause 7.1", "reference_standard": standard_id, "criteria": "100% lot conformity"},
                {"test_name": "Type Approval Test", "clause": "Clause 7.2", "reference_standard": standard_id, "criteria": "Periodic surveillance audit sample"}
            ]
        }
    return res


@app.get("/api/cml/verify")
def verify_cml_license(cml_number: str = Query(..., description="7-digit BIS License CM/L number")) -> Dict[str, Any]:
    """Verifies authenticity and operative status of bidder's BIS Certification Marks License (CM/L)."""
    svc = get_cml_verifier()
    return svc.verify_license(cml_number)


@app.get("/api/graph/path")
def get_shortest_path(source: str = Query(...), target: str = Query(...)) -> Dict[str, Any]:
    """Finds shortest normative reference bridge connecting two standards in the knowledge graph."""
    svc = get_graph_explorer_service()
    return svc.find_shortest_path(source, target)


@app.get("/api/graph/timeline/{standard_id}")
def get_standard_timeline(standard_id: str) -> Dict[str, Any]:
    """Returns chronological revision milestones and historical supersessions for a standard."""
    svc = get_graph_explorer_service()
    return svc.get_timeline(standard_id)


@app.get("/api/graph/clusters")
def get_graph_clusters() -> Dict[str, Any]:
    """Returns departmental node clusters for topological visualization."""
    svc = get_graph_explorer_service()
    return svc.get_department_clusters()


@app.get("/api/graph/{standard_id}")
def get_graph_neighborhood(
    standard_id: str,
    max_nodes: int = Query(default=40, ge=5, le=100)
) -> Dict[str, Any]:
    """Returns 2-hop neighborhood of a standard or QCO formatted for React Flow graph rendering."""
    global graph_svc
    if graph_svc is None:
        graph_svc = get_graph_service()

    res = graph_svc.get_2hop_neighborhood(standard_id, max_nodes=max_nodes)
    if not res["nodes"]:
        raise HTTPException(status_code=404, detail=f"Node '{standard_id}' not found in Knowledge Graph.")
    return res


@app.get("/api/qcos")
def list_qcos(ministry: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns directory of all active statutory Quality Control Orders."""
    global graph_svc
    if graph_svc is None:
        graph_svc = get_graph_service()

    qcos = list(graph_svc.qcos_index.values())
    if ministry:
        qcos = [q for q in qcos if ministry.lower() in q.get("ministry_id", "").lower()]
    return qcos


@app.get("/api/samples")
def get_sample_test_scenarios() -> Dict[str, Any]:
    """
    Returns curated procurement queries (Mode A) and authentic tender test scenarios with known traps (Mode B)
    for 1-click user demonstrations.
    """
    samples_dir = Path(__file__).resolve().parent.parent.parent / "data" / "gem_tender_samples"
    manifest_file = samples_dir / "manifest.json"

    tender_traps = []
    if manifest_file.exists():
        import json
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
            for item in manifest_data:
                tender_traps.append({
                    "tender_id": item.get("tender_id"),
                    "title": item.get("title"),
                    "department": item.get("department"),
                    "language": item.get("language", "en"),
                    "file_name": item.get("file_name"),
                    "expected_score": item.get("expected_findings", {}).get("compliance_score"),
                    "qco_compliant": item.get("expected_findings", {}).get("qco_compliant"),
                    "raw_text": item.get("raw_text")
                })

    procurement_queries = [
        {
            "category": "Civil & Structural Steel",
            "query": "Supply of hot rolled structural steel plates Grade E250 and rolled joists for bridge construction",
            "expected_standard": "IS 2062",
            "qco": "Steel and Steel Products QCO (Scheme-I)"
        },
        {
            "category": "Concrete Reinforcement",
            "query": "High strength deformed TMT rebar Fe 500D for RCC building foundation",
            "expected_standard": "IS 1786",
            "qco": "Steel and Steel Products QCO (Scheme-I)"
        },
        {
            "category": "Electronics & IT Equipment",
            "query": "Commercial laptops with secondary lithium batteries and AC power adapters",
            "expected_standard": "IS 13252 (Part 1)",
            "qco": "MeitY Compulsory Registration Scheme (Scheme-II CRS)"
        },
        {
            "category": "Potable Water Piping",
            "query": "High density polyethylene HDPE pipes 110mm rating PN-10 for rural drinking water distribution",
            "expected_standard": "IS 4984",
            "qco": "Polyethylene Material for Moulding QCO"
        },
        {
            "category": "Solar Renewable Energy",
            "query": "Crystalline silicon terrestrial photovoltaic modules with safety qualification",
            "expected_standard": "IS 14286 / IS/IEC 61730",
            "qco": "MNRE Solar Photovoltaics CRS Order"
        },
        {
            "category": "Indic Language (Hindi)",
            "query": "पुल निर्माण के लिए 500 टन संरचनात्मक इस्पात और टीएमटी सरिया की आपूर्ति",
            "expected_standard": "IS 2062 & IS 1786",
            "qco": "इस्पात मंत्रालय QCO (Scheme-I)"
        }
    ]

    return {
        "mode_a_recommendation_queries": procurement_queries,
        "mode_b_audit_tender_traps": tender_traps
    }


@app.get("/api/bom/{standard_id}")
def get_standard_bom(standard_id: str) -> Dict[str, Any]:
    """Returns the complete 5-layer statutory Standard BOM for a given standard."""
    global graph_svc
    if graph_svc is None:
        graph_svc = get_graph_service()
    return StandardBOMService.generate_bom(standard_id, graph_service=graph_svc)


@app.get("/api/rates/ground")
def ground_schedule_of_rates(query: str = Query(..., min_length=2), standard_id: Optional[str] = None) -> Dict[str, Any]:
    """Matches procurement queries to CPWD DSR, MoRTH, and GeM rate schedule items."""
    matched = ScheduleOfRatesService.ground_query(query, top_standard_id=standard_id)
    if not matched:
        return {"matched": False, "query": query, "message": "No direct Schedule of Rates item matched."}
    return {"matched": True, "schedule_item": matched}


@app.get("/api/value-engineering/{standard_id}")
def get_value_engineering(standard_id: str) -> Dict[str, Any]:
    """Returns the 3-tier comparative Value Engineering Matrix for the standard."""
    matrix = ValueEngineeringService.get_value_engineering_matrix(standard_id)
    return {"standard_id": standard_id, "tiers": matrix}


@app.post("/api/litigation/analyze")
def analyze_litigation_risk(payload: Dict[str, str]) -> Dict[str, Any]:
    """Evaluates tender text for high-risk litigation traps and computes Defensibility Score."""
    text = payload.get("text", "") or payload.get("raw_text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' field in payload.")
    return LitigationRiskService.analyze_tender_risk(text)
