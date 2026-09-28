#!/usr/bin/env python3
"""
Repeatable Recommendation Correctness & Standard Correction Evaluation Engine
for Manak-SpecEngine.

Evaluates:
1. Current-Standard Retrieval Accuracy: Proportion of direct technical queries where
   the primary recommended standard is currently ACTIVE and technically correct.
2. Obsolete-Citation Detection Accuracy: Proportion of queries citing historical/superseded
   standards where the obsolescence is correctly detected.
3. Replacement Resolution Accuracy: Proportion of obsolete citations where the correct
   active successor standard is resolved with honest CURATED_UNVERIFIED provenance.
4. Ambiguous Branching Safety: Proportion of multi-branch obsolete citations lacking context
   where the engine safely abstains (NEEDS_CONTEXT) rather than arbitrarily choosing a branch.
5. Obsolete-as-Primary Recommendation Rate: Proportion of recommendations where an obsolete
   or withdrawn standard is erroneously returned as primary_match (Target: 0.0%).
6. Statutory QCO Temporal Accuracy: Accuracy of dynamic in-force vs pending vs unverified QCO evaluation.
7. Low-Confidence Abstention: Appropriate flagging (NEEDS_CLARIFICATION / 404) for out-of-domain queries.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

BENCHMARK_CASES = [
    {
        "id": "CASE-01",
        "category": "Current Standard Direct Lookup",
        "query": "hot rolled medium and high tensile structural steel plates E250",
        "expected_active_standard": "IS 2062",
        "expected_status": "ACTIVE",
        "allow_alternatives": ["IS 808"],
        "expect_supersession": False,
        "expect_mandatory_qco": True,
        "evaluation_date": "2026-09-28",
        "expected_qco_temporal_status": "MANDATORY_IN_FORCE",
        "evidence_source": "IS 2062:2011 Table 1; Steel QCO 2024 (S.O. 2240(E))",
        "evidence_provenance_level": "STANDARDS_CATALOG_ACTIVE",
        "authoritative_source_checked": True
    },
    {
        "id": "CASE-02",
        "category": "Obsolete Citation with Application Context (Rebar)",
        "query": "mild steel plain round bars IS 432 Part 1 for concrete reinforcement",
        "expected_active_standard": "IS 1786",
        "expected_status": "ACTIVE",
        "cited_obsolete_standard": "IS 432 (Part 1)",
        "expect_supersession": True,
        "expected_replacement": "IS 1786",
        "expected_replacement_evidence_level": "CURATED_UNVERIFIED",
        "alternative_branches": ["IS 2062"],
        "evidence_source": "Civil Engineering Practice & BIS Transition (IS 1786 superseded IS 432 for rebar)",
        "evidence_provenance_level": "CURATED_UNVERIFIED_GAZETTE_PENDING",
        "authoritative_source_checked": False
    },
    {
        "id": "CASE-03",
        "category": "Obsolete Standard Amalgamation (Structural Steel)",
        "query": "standard structural steel sections IS 226 for building frames",
        "expected_active_standard": "IS 2062",
        "expected_status": "ACTIVE",
        "cited_obsolete_standard": "IS 226",
        "expect_supersession": True,
        "expected_replacement": "IS 2062",
        "expected_replacement_evidence_level": "CURATED_UNVERIFIED",
        "evidence_source": "BIS 1992 Revision Catalog (IS 226 amalgamated into IS 2062)",
        "evidence_provenance_level": "CURATED_UNVERIFIED_GAZETTE_PENDING",
        "authoritative_source_checked": False
    },
    {
        "id": "CASE-04",
        "category": "Obsolete Cement Standard Consolidation (43 Grade)",
        "query": "43 grade ordinary portland cement IS 8112 for masonry construction",
        "expected_active_standard": "IS 269",
        "expected_status": "ACTIVE",
        "cited_obsolete_standard": "IS 8112",
        "expect_supersession": True,
        "expected_replacement": "IS 269",
        "expected_replacement_evidence_level": "CURATED_UNVERIFIED",
        "evidence_source": "BIS 2015 Cement Revision (IS 8112 consolidated into IS 269:2015)",
        "evidence_provenance_level": "CURATED_UNVERIFIED_GAZETTE_PENDING",
        "authoritative_source_checked": False
    },
    {
        "id": "CASE-05",
        "category": "Obsolete Cement Standard Consolidation (53 Grade)",
        "query": "53 grade high strength ordinary portland cement IS 12269 for precast piles",
        "expected_active_standard": "IS 269",
        "expected_status": "ACTIVE",
        "cited_obsolete_standard": "IS 12269",
        "expect_supersession": True,
        "expected_replacement": "IS 269",
        "expected_replacement_evidence_level": "CURATED_UNVERIFIED",
        "evidence_source": "BIS 2015 Cement Revision (IS 12269 consolidated into IS 269:2015)",
        "evidence_provenance_level": "CURATED_UNVERIFIED_GAZETTE_PENDING",
        "authoritative_source_checked": False
    },
    {
        "id": "CASE-06",
        "category": "Hard Negative Discrimination (Rebar vs Structural Steel)",
        "query": "high yield strength TMT reinforcement bars for column cages",
        "expected_active_standard": "IS 1786",
        "expected_status": "ACTIVE",
        "forbidden_standards": ["IS 2062", "IS 1079"],
        "expect_supersession": False,
        "evidence_source": "IS 1786:2008 Scope",
        "evidence_provenance_level": "STANDARDS_CATALOG_ACTIVE",
        "authoritative_source_checked": True
    },
    {
        "id": "CASE-07",
        "category": "Hard Negative Discrimination (Structural Beam vs Rebar)",
        "query": "structural steel I-beams and channels for bridge superstructure",
        "expected_active_standard": "IS 2062",
        "expected_status": "ACTIVE",
        "forbidden_standards": ["IS 1786"],
        "expect_supersession": False,
        "evidence_source": "IS 2062:2011 Scope",
        "evidence_provenance_level": "STANDARDS_CATALOG_ACTIVE",
        "authoritative_source_checked": True
    },
    {
        "id": "CASE-08",
        "category": "Potable Water vs Sewerage Discrimination",
        "query": "high density polyethylene HDPE pipe 110mm PN 10 for drinking water distribution",
        "expected_active_standard": "IS 4984",
        "expected_status": "ACTIVE",
        "forbidden_standards": ["IS 458", "IS 14333"],
        "expect_supersession": False,
        "evidence_source": "IS 4984:2016 Cl. 4.1",
        "evidence_provenance_level": "STANDARDS_CATALOG_ACTIVE",
        "authoritative_source_checked": True
    },
    {
        "id": "CASE-09",
        "category": "Sewerage Conduit Discrimination",
        "query": "precast concrete pipes for gravity sewer and stormwater drainage",
        "expected_active_standard": "IS 458",
        "expected_status": "ACTIVE",
        "forbidden_standards": ["IS 4984"],
        "expect_supersession": False,
        "evidence_source": "IS 458:2021 Scope",
        "evidence_provenance_level": "STANDARDS_CATALOG_ACTIVE",
        "authoritative_source_checked": True
    },
    {
        "id": "CASE-10",
        "category": "Constraint-Specific Detailing (Coastal + Seismic Zone V)",
        "query": "Fe 500D steel rebar for coastal bridge pier foundation in Seismic Zone V",
        "expected_active_standard": "IS 1786",
        "expected_status": "ACTIVE",
        "expected_constraints": ["requires_crs", "requires_ductility"],
        "evidence_source": "IS 13920:2016 Cl. 5.1 & IS 1786:2008 Cl. 4.2",
        "evidence_provenance_level": "STANDARDS_CATALOG_ACTIVE",
        "authoritative_source_checked": True
    },
    {
        "id": "CASE-11",
        "category": "Multilingual Indic Query (Hindi Procurement Terminology)",
        "query": "तटीय पुल के लिए सरिया Fe 500D",
        "expected_active_standard": "IS 1786",
        "expected_status": "ACTIVE",
        "evidence_source": "Indic Procurement Vocabulary & Sarvam AI Translation",
        "evidence_provenance_level": "STANDARDS_CATALOG_ACTIVE",
        "authoritative_source_checked": True
    },
    {
        "id": "CASE-12",
        "category": "Abstention & Low Confidence Handling",
        "query": "general miscellaneous item xyz123 non-standard supplies",
        "expect_abstention": True,
        "max_acceptable_score": 0.35,
        "evidence_source": "Heuristic Ranking Score Abstention Policy",
        "evidence_provenance_level": "HEURISTIC_THRESHOLD",
        "authoritative_source_checked": False
    },
    {
        "id": "CASE-13",
        "category": "Ambiguous Supersession Branching Safety",
        "query": "mild steel bars IS 432 Part 1",
        "expect_ambiguous_branching": True,
        "expect_supersession": True,
        "expected_resolution_code": "AMBIGUOUS_BRANCHING",
        "expected_verification_level": "UNRESOLVED",
        "evidence_source": "IS 432 Part 1 branched into rebar (IS 1786) and structural (IS 2062); context is ambiguous.",
        "evidence_provenance_level": "CURATED_UNVERIFIED_GAZETTE_PENDING",
        "authoritative_source_checked": False
    },
    {
        "id": "CASE-14",
        "category": "QCO Temporal Time-Awareness (Historical/Future Evaluation Date)",
        "query": "hot rolled structural steel plates E250",
        "expected_active_standard": "IS 2062",
        "expected_status": "ACTIVE",
        "evaluation_date": "2020-01-01",
        "expect_mandatory_qco": False,
        "expected_qco_temporal_status": "PENDING_FUTURE_DATE",
        "evidence_source": "Steel QCO 2024 came into force on 2024-06-01; on 2020-01-01 it was not in force.",
        "evidence_provenance_level": "STANDARDS_CATALOG_ACTIVE",
        "authoritative_source_checked": True
    }
]


def run_evaluation(api_base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Executes benchmark queries against the recommendation API and calculates
    rigorous metrics with explicit denominators for each evaluated capability.
    """
    results = []

    # Separate metric accumulators
    retrieval_correct = 0
    retrieval_total = 0

    obsolete_as_primary_count = 0
    total_evaluated_recommendations = 0

    supersession_detected = 0
    supersession_detection_total = 0

    replacement_correct = 0
    replacement_total = 0

    branching_safe_count = 0
    branching_total = 0

    qco_correct = 0
    qco_total = 0

    abstention_correct = 0
    abstention_total = 0

    for case in BENCHMARK_CASES:
        payload_dict: Dict[str, Any] = {"query": case["query"], "top_k": 5}
        if "evaluation_date" in case:
            payload_dict["evaluation_date"] = case["evaluation_date"]

        payload = json.dumps(payload_dict).encode("utf-8")
        req = urllib.request.Request(
            f"{api_base_url}/api/recommend",
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        case_passed = True
        failure_reasons = []

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                primary = data.get("primary_match")
                p_is = primary.get("is_number", "") if primary else ""
                p_status = primary.get("status", "") if primary else ""
                sup_res = data.get("supersession_resolution", {}) or {}
                conf = data.get("confidence_assessment", {}) or {}
                rec_status = data.get("recommendation_status", "")

                total_evaluated_recommendations += 1

                # Check 1: Obsolete Standard as Primary Recommendation Rate (Target: 0.0%)
                if p_status in ("SUPERSEDED", "WITHDRAWN"):
                    obsolete_as_primary_count += 1
                    case_passed = False
                    failure_reasons.append(f"Obsolete standard '{p_is}' returned as primary recommendation.")

                # Check 2: Ambiguous Branching Safety
                if case.get("expect_ambiguous_branching"):
                    branching_total += 1
                    is_safe = (
                        rec_status == "NEEDS_CONTEXT" and
                        primary is None and
                        sup_res.get("resolution_code") == "AMBIGUOUS_BRANCHING" and
                        sup_res.get("verification_level") == "UNRESOLVED"
                    )
                    if is_safe:
                        branching_safe_count += 1
                    else:
                        case_passed = False
                        failure_reasons.append(
                            f"Expected safe abstention (NEEDS_CONTEXT/AMBIGUOUS_BRANCHING), got status '{rec_status}' "
                            f"with resolution_code '{sup_res.get('resolution_code')}'."
                        )

                # Check 3: Current Standard Retrieval Accuracy (Only for queries expecting an active primary standard)
                if case.get("expected_active_standard") and not case.get("expect_ambiguous_branching") and not case.get("expect_abstention"):
                    retrieval_total += 1
                    expected_std = case["expected_active_standard"]
                    alts = case.get("allow_alternatives", [])
                    matches_expected = (
                        expected_std.lower() in p_is.lower() or
                        any(a.lower() in p_is.lower() for a in alts)
                    )
                    forbidden = case.get("forbidden_standards", [])
                    violates_forbidden = any(f.lower() in p_is.lower() for f in forbidden)

                    if matches_expected and not violates_forbidden and p_status == case.get("expected_status", "ACTIVE"):
                        retrieval_correct += 1
                    else:
                        case_passed = False
                        failure_reasons.append(
                            f"Expected active standard '{expected_std}' (status {case.get('expected_status')}), "
                            f"got '{p_is}' (status '{p_status}')."
                        )

                # Check 4: Obsolete Citation Detection & Replacement Resolution
                if case.get("expect_supersession"):
                    supersession_detection_total += 1
                    if sup_res.get("is_superseded"):
                        supersession_detected += 1
                    else:
                        case_passed = False
                        failure_reasons.append("Expected obsolescence detection, but is_superseded is False.")

                    if case.get("expected_replacement"):
                        replacement_total += 1
                        replacements = [
                            r.get("standard", {}).get("is_number", "")
                            for r in sup_res.get("current_replacements", [])
                        ]
                        expected_rep = case["expected_replacement"]
                        rep_matches = any(expected_rep.lower() in r.lower() for r in replacements)

                        # Check evidence level if specified
                        expected_ev = case.get("expected_replacement_evidence_level")
                        actual_ev = sup_res.get("verification_level")
                        ev_matches = (expected_ev is None) or (actual_ev == expected_ev)

                        if rep_matches and ev_matches:
                            replacement_correct += 1
                        else:
                            case_passed = False
                            failure_reasons.append(
                                f"Expected replacement '{expected_rep}' ({expected_ev}), "
                                f"got replacements {replacements} ({actual_ev})."
                            )

                # Check 5: Statutory QCO Applicability & Temporal Accuracy
                if "expect_mandatory_qco" in case:
                    qco_total += 1
                    gov_qco = data.get("governing_qco") or {}
                    actual_mandatory = bool(gov_qco.get("is_mandatory"))
                    actual_temporal = gov_qco.get("temporal_status")

                    expected_mandatory = case["expect_mandatory_qco"]
                    expected_temporal = case.get("expected_qco_temporal_status")

                    mandatory_matches = (actual_mandatory == expected_mandatory)
                    temporal_matches = (expected_temporal is None) or (actual_temporal == expected_temporal)

                    if mandatory_matches and temporal_matches:
                        qco_correct += 1
                    else:
                        case_passed = False
                        failure_reasons.append(
                            f"QCO check failed: expected is_mandatory={expected_mandatory} ({expected_temporal}), "
                            f"got is_mandatory={actual_mandatory} ({actual_temporal})."
                        )

                # Check 6: Abstention Quality
                if case.get("expect_abstention"):
                    abstention_total += 1
                    is_abstained = (
                        rec_status in ("NEEDS_CLARIFICATION", "NO_ACTIVE_STANDARD_FOUND") or
                        not conf.get("has_sufficient_confidence", True) or
                        (primary is None)
                    )
                    if is_abstained:
                        abstention_correct += 1
                    else:
                        case_passed = False
                        failure_reasons.append(
                            f"Expected abstention or needs-clarification for ungrounded query, but received confident match '{p_is}'."
                        )

                results.append({
                    "case_id": case["id"],
                    "category": case["category"],
                    "query": case["query"],
                    "recommendation_status": rec_status,
                    "primary_recommended": p_is or "None (Abstained)",
                    "status": p_status,
                    "ranking_score": primary.get("score") if primary else 0.0,
                    "relevance_level": conf.get("relative_relevance"),
                    "qco_temporal_status": (data.get("governing_qco") or {}).get("temporal_status"),
                    "passed": case_passed,
                    "failure_reasons": failure_reasons,
                    "provenance_level": case.get("evidence_provenance_level"),
                    "authoritative_source_checked": case.get("authoritative_source_checked")
                })

        except urllib.error.HTTPError as e:
            total_evaluated_recommendations += 1
            if case.get("expect_abstention") and e.code == 404:
                abstention_total += 1
                abstention_correct += 1
                results.append({
                    "case_id": case["id"],
                    "category": case["category"],
                    "query": case["query"],
                    "recommendation_status": "ABSTAINED_404",
                    "primary_recommended": "None (404)",
                    "passed": True,
                    "failure_reasons": [],
                    "provenance_level": case.get("evidence_provenance_level"),
                    "authoritative_source_checked": case.get("authoritative_source_checked")
                })
            else:
                results.append({
                    "case_id": case["id"],
                    "category": case["category"],
                    "query": case["query"],
                    "error": f"HTTP {e.code}: {e.reason}",
                    "passed": False,
                    "failure_reasons": [f"Unexpected HTTP {e.code} error: {e.reason}"],
                    "provenance_level": case.get("evidence_provenance_level"),
                    "authoritative_source_checked": case.get("authoritative_source_checked")
                })

    retrieval_acc = (retrieval_correct / retrieval_total * 100) if retrieval_total else 0.0
    obsolete_rate = (obsolete_as_primary_count / total_evaluated_recommendations * 100) if total_evaluated_recommendations else 0.0
    supersession_det_acc = (supersession_detected / supersession_detection_total * 100) if supersession_detection_total else 0.0
    replacement_acc = (replacement_correct / replacement_total * 100) if replacement_total else 0.0
    branching_acc = (branching_safe_count / branching_total * 100) if branching_total else 0.0
    qco_acc = (qco_correct / qco_total * 100) if qco_total else 0.0
    abstention_acc = (abstention_correct / abstention_total * 100) if abstention_total else 0.0

    summary = {
        "evaluation_summary": {
            "total_benchmark_cases": len(BENCHMARK_CASES),
            "current_standard_retrieval_accuracy_pct": round(retrieval_acc, 2),
            "current_standard_cases_evaluated": f"{retrieval_correct}/{retrieval_total}",
            "obsolete_as_primary_recommendation_rate_pct": round(obsolete_rate, 2),
            "obsolete_as_primary_count": f"{obsolete_as_primary_count}/{total_evaluated_recommendations}",
            "supersession_detection_accuracy_pct": round(supersession_det_acc, 2),
            "supersession_detection_cases": f"{supersession_detected}/{supersession_detection_total}",
            "replacement_resolution_accuracy_pct": round(replacement_acc, 2),
            "replacement_resolution_cases": f"{replacement_correct}/{replacement_total}",
            "ambiguous_branching_safety_pct": round(branching_acc, 2),
            "ambiguous_branching_cases": f"{branching_safe_count}/{branching_total}",
            "qco_temporal_accuracy_pct": round(qco_acc, 2),
            "qco_temporal_cases": f"{qco_correct}/{qco_total}",
            "abstention_quality_pct": round(abstention_acc, 2),
            "abstention_cases": f"{abstention_correct}/{abstention_total}"
        },
        "detailed_results": results
    }

    return summary


if __name__ == "__main__":
    print("=" * 80)
    print("Manak-SpecEngine Grounded Correctness & Safety Benchmark")
    print("=" * 80)
    res = run_evaluation()
    print("\nBenchmark Metrics Summary:")
    print(json.dumps(res["evaluation_summary"], indent=2))
    print("\nCase-by-Case Breakdown:")
    for r in res["detailed_results"]:
        status_str = "PASS" if r.get("passed") else "FAIL"
        print(f"[{status_str}] {r['case_id']}: {r['category']}")
        print(f"       Query: '{r['query']}'")
        print(f"       Recommended: {r.get('primary_recommended')} ({r.get('status')})")
        print(f"       Status: {r.get('recommendation_status')} | QCO: {r.get('qco_temporal_status')}")
        if not r.get("passed"):
            print(f"       Failures: {r.get('failure_reasons')}")
        print(f"       Provenance: {r.get('provenance_level')} (Authoritative Source Checked: {r.get('authoritative_source_checked')})")
        print("-" * 60)
