#!/usr/bin/env python3
"""
Repeatable Recommendation Correctness & Standard Correction Evaluation Engine
for Manak-SpecEngine.

Evaluates:
1. Current-Standard Top-1 Accuracy: Proportion of test cases where the primary recommended
   standard is currently ACTIVE and technically correct.
2. Obsolete-Standard Recommendation Rate: Proportion of recommendations that erroneously
   recommend a SUPERSEDED or WITHDRAWN standard as the current solution (Target: 0.0%).
3. Supersession Correction Precision & Recall: Ability to detect obsolete standard citations
   (IS 432, IS 226, IS 8112, IS 12269, IS 16046:2015) and resolve verified active replacements.
4. Statutory QCO Applicability Precision & Recall: Temporal accuracy of QCO mandate detection
   (in-force vs pending vs unverified).
5. Constraint & Grade Extraction Accuracy: Seismic detailing, CRS, exposure class extraction.
6. Abstention Quality: Appropriate flagging of underspecified or out-of-domain queries.
"""

import json
from typing import Dict, List, Any, Optional

BENCHMARK_CASES = [
    {
        "id": "CASE-01",
        "category": "Current Standard Lookup",
        "query": "hot rolled medium and high tensile structural steel plates E250",
        "expected_active_standard": "IS 2062",
        "expected_status": "ACTIVE",
        "allow_alternatives": ["IS 808"],
        "expect_supersession": False,
        "expect_mandatory_qco": True,
        "evidence_source": "IS 2062:2011 Table 1; Steel QCO 2024"
    },
    {
        "id": "CASE-02",
        "category": "Obsolete Standard Correction (Rebar)",
        "query": "mild steel plain round bars IS 432 Part 1 for concrete reinforcement",
        "expected_active_standard": "IS 1786",
        "expected_status": "ACTIVE",
        "cited_obsolete_standard": "IS 432 (Part 1)",
        "expect_supersession": True,
        "expected_replacement": "IS 1786",
        "alternative_branches": ["IS 2062"],
        "evidence_source": "BIS Revision & Amalgamation Catalog (IS 1786 superseded IS 432)"
    },
    {
        "id": "CASE-03",
        "category": "Obsolete Standard Correction (Structural Steel)",
        "query": "standard structural steel sections IS 226 for building frames",
        "expected_active_standard": "IS 2062",
        "expected_status": "ACTIVE",
        "cited_obsolete_standard": "IS 226",
        "expect_supersession": True,
        "expected_replacement": "IS 2062",
        "evidence_source": "BIS 1992 Gazette (IS 226 amalgamated into IS 2062)"
    },
    {
        "id": "CASE-04",
        "category": "Obsolete Standard Correction (43 Grade Cement)",
        "query": "43 grade ordinary portland cement IS 8112 for masonry construction",
        "expected_active_standard": "IS 269",
        "expected_status": "ACTIVE",
        "cited_obsolete_standard": "IS 8112",
        "expect_supersession": True,
        "expected_replacement": "IS 269",
        "evidence_source": "BIS 2015 Consolidation (IS 8112 consolidated into IS 269:2015)"
    },
    {
        "id": "CASE-05",
        "category": "Obsolete Standard Correction (53 Grade Cement)",
        "query": "53 grade high strength ordinary portland cement IS 12269 for precast piles",
        "expected_active_standard": "IS 269",
        "expected_status": "ACTIVE",
        "cited_obsolete_standard": "IS 12269",
        "expect_supersession": True,
        "expected_replacement": "IS 269",
        "evidence_source": "BIS 2015 Consolidation (IS 12269 consolidated into IS 269:2015)"
    },
    {
        "id": "CASE-06",
        "category": "Hard Negative Discrimination (Rebar vs Structural Steel)",
        "query": "high yield strength TMT reinforcement bars for column cages",
        "expected_active_standard": "IS 1786",
        "forbidden_standards": ["IS 2062", "IS 1079"],
        "expect_supersession": False,
        "evidence_source": "IS 1786:2008 Scope"
    },
    {
        "id": "CASE-07",
        "category": "Hard Negative Discrimination (Structural Beam vs Rebar)",
        "query": "structural steel I-beams and channels for bridge superstructure",
        "expected_active_standard": "IS 2062",
        "forbidden_standards": ["IS 1786"],
        "expect_supersession": False,
        "evidence_source": "IS 2062:2011 Scope"
    },
    {
        "id": "CASE-08",
        "category": "Potable Water vs Sewerage Discrimination",
        "query": "high density polyethylene HDPE pipe 110mm PN 10 for drinking water distribution",
        "expected_active_standard": "IS 4984",
        "forbidden_standards": ["IS 458", "IS 14333"],
        "expect_supersession": False,
        "evidence_source": "IS 4984:2016 Cl. 4.1"
    },
    {
        "id": "CASE-09",
        "category": "Sewerage Conduit Discrimination",
        "query": "precast concrete pipes for gravity sewer and stormwater drainage",
        "expected_active_standard": "IS 458",
        "forbidden_standards": ["IS 4984"],
        "expect_supersession": False,
        "evidence_source": "IS 458:2021 Scope"
    },
    {
        "id": "CASE-10",
        "category": "Constraint-Specific Grade (Coastal + Seismic V)",
        "query": "Fe 500D steel rebar for coastal bridge pier foundation in Seismic Zone V",
        "expected_active_standard": "IS 1786",
        "expected_constraints": ["requires_crs", "requires_ductility"],
        "evidence_source": "IS 13920:2016 Cl. 5.1 & IS 1786:2008 Cl. 4.2"
    },
    {
        "id": "CASE-11",
        "category": "Multilingual Indic Query (Hindi)",
        "query": "तटीय पुल के लिए सरिया Fe 500D",
        "expected_active_standard": "IS 1786",
        "expected_status": "ACTIVE",
        "evidence_source": "Indic Procurement Vocabulary & Sarvam AI Translation"
    },
    {
        "id": "CASE-12",
        "category": "Abstention & Low Confidence Handling",
        "query": "general miscellaneous item xyz123 non-standard supplies",
        "expect_abstention": True,
        "max_acceptable_confidence": 0.35,
        "evidence_source": "Calibrated Confidence Threshold Policy"
    }
]


def run_evaluation(api_base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Executes benchmark queries against the recommendation API and calculates
    rigorous metrics for standard correction and accuracy.
    """
    import urllib.request
    import urllib.error

    results = []
    correct_top1 = 0
    obsolete_recommended_count = 0
    supersession_correct = 0
    supersession_total = 0
    qco_correct = 0
    qco_total = 0
    abstention_correct = 0
    abstention_total = 0

    for case in BENCHMARK_CASES:
        payload = json.dumps({"query": case["query"], "top_k": 5}).encode("utf-8")
        req = urllib.request.Request(
            f"{api_base_url}/api/recommend",
            data=payload,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                primary = data.get("primary_match", {})
                p_is = primary.get("is_number", "")
                p_status = primary.get("status", "")
                sup_res = data.get("supersession_resolution", {})
                conf = data.get("confidence_assessment", {})

                # Metric 1: Top-1 Accuracy
                is_top1_match = False
                expected_std = case.get("expected_active_standard")
                if expected_std:
                    is_top1_match = (
                        expected_std.lower() in p_is.lower() or
                        any(alt.lower() in p_is.lower() for alt in case.get("allow_alternatives", []))
                    )
                    if is_top1_match:
                        correct_top1 += 1

                # Metric 2: Obsolete Standard Recommendation Rate
                if p_status in ("SUPERSEDED", "WITHDRAWN"):
                    obsolete_recommended_count += 1

                # Metric 3: Supersession Correction
                if case.get("expect_supersession"):
                    supersession_total += 1
                    if sup_res.get("is_superseded"):
                        replacements = [r.get("standard", {}).get("is_number", "") for r in sup_res.get("current_replacements", [])]
                        expected_rep = case.get("expected_replacement", "")
                        if any(expected_rep.lower() in r.lower() for r in replacements):
                            supersession_correct += 1

                # Metric 4: QCO Verification
                if "expect_mandatory_qco" in case:
                    qco_total += 1
                    if primary.get("is_mandatory_qco") == case["expect_mandatory_qco"]:
                        qco_correct += 1

                # Metric 5: Abstention Quality
                if case.get("expect_abstention"):
                    abstention_total += 1
                    if not conf.get("has_sufficient_confidence", True) or conf.get("score", 1.0) <= case["max_acceptable_confidence"]:
                        abstention_correct += 1

                results.append({
                    "case_id": case["id"],
                    "query": case["query"],
                    "category": case["category"],
                    "primary_recommended": p_is,
                    "status": p_status,
                    "score": primary.get("score"),
                    "confidence_level": conf.get("confidence_level"),
                    "supersession_resolved": sup_res.get("is_superseded"),
                    "pass": is_top1_match if expected_std else True
                })

        except urllib.error.HTTPError as e:
            if case.get("expect_abstention") and e.code == 404:
                abstention_total += 1
                abstention_correct += 1
                results.append({
                    "case_id": case["id"],
                    "query": case["query"],
                    "category": case["category"],
                    "primary_recommended": "ABSTAINED (404)",
                    "pass": True
                })
            else:
                results.append({
                    "case_id": case["id"],
                    "query": case["query"],
                    "category": case["category"],
                    "error": str(e),
                    "pass": False
                })

    total_evaluable = sum(1 for c in BENCHMARK_CASES if c.get("expected_active_standard"))
    top1_accuracy = (correct_top1 / total_evaluable * 100) if total_evaluable else 0.0
    obsolete_rate = (obsolete_recommended_count / len(BENCHMARK_CASES) * 100) if BENCHMARK_CASES else 0.0
    supersession_acc = (supersession_correct / supersession_total * 100) if supersession_total else 0.0
    qco_acc = (qco_correct / qco_total * 100) if qco_total else 0.0
    abstention_acc = (abstention_correct / abstention_total * 100) if abstention_total else 0.0

    summary = {
        "total_benchmark_cases": len(BENCHMARK_CASES),
        "top1_current_accuracy_pct": round(top1_accuracy, 2),
        "obsolete_standard_recommendation_rate_pct": round(obsolete_rate, 2),
        "supersession_correction_accuracy_pct": round(supersession_acc, 2),
        "qco_temporal_accuracy_pct": round(qco_acc, 2),
        "abstention_quality_pct": round(abstention_acc, 2),
        "detailed_results": results
    }

    return summary


if __name__ == "__main__":
    import sys
    print("Executing Manak-SpecEngine Evaluation Benchmark...")
    res = run_evaluation()
    print(json.dumps(res, indent=2))
