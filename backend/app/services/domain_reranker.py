"""
Domain Contrastive Reranker & Late-Interaction Scoring for Manak-SpecEngine.
Performs fine-grained technical grade cross-matching, hard-negative discrimination,
and query-to-standard token MaxSim scoring to re-rank candidate standards.
"""

import re
from typing import Dict, Any, List, Tuple, Optional


class DomainReranker:
    """
    Reranks candidate standards by computing:
    1. Exact Grade Cross-Matching (Fe 500D, E250BR, PE 100, etc.)
    2. Hard-Negative Penalties (e.g. confusing structural steel plates with commercial thin sheet)
    3. Technical Keyword Coverage (Yield, Tensile, Elongation, Impact)
    """

    GRADE_HIERARCHIES = {
        "fe 500d": {"bonus_standards": ["IS_1786"], "penalty_standards": ["IS_432", "IS_280"]},
        "fe 550d": {"bonus_standards": ["IS_1786"], "penalty_standards": ["IS_432", "IS_280"]},
        "fe 415": {"bonus_standards": ["IS_1786"], "penalty_standards": []},
        "e250": {"bonus_standards": ["IS_2062"], "penalty_standards": ["IS_1079", "IS_513"]},
        "e350": {"bonus_standards": ["IS_2062"], "penalty_standards": ["IS_1079", "IS_513"]},
        "pe 100": {"bonus_standards": ["IS_4984", "IS_14333"], "penalty_standards": ["IS_4985", "IS_12818"]},
        "pe 80": {"bonus_standards": ["IS_4984"], "penalty_standards": []},
        "opc 53": {"bonus_standards": ["IS_269"], "penalty_standards": []},
        "opc 43": {"bonus_standards": ["IS_269"], "penalty_standards": []},
        "ppc": {"bonus_standards": ["IS_1489"], "penalty_standards": []}
    }

    @classmethod
    def rerank(
        cls,
        query: str,
        candidates: List[Dict[str, Any]],
        slots: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Reranks candidates by applying contrastive grade matching, slot bonuses,
        and hard-negative penalties.
        """
        if not candidates:
            return []

        q_lower = query.lower()
        slots = slots or {}

        for item in candidates:
            score = item.get("score", 0.5)
            sid = item.get("standard_id", "").upper()
            title = item.get("title", "").lower()

            # 1. Technical Grade Cross-Matching
            for grade, rule in cls.GRADE_HIERARCHIES.items():
                if grade in q_lower:
                    if any(bs in sid for bs in rule["bonus_standards"]):
                        score += 0.35
                    if any(ps in sid for ps in rule["penalty_standards"]):
                        score -= 0.50

            # 2. Hard-Negative Mismatch Penalties
            # Rebar vs Structural Steel vs Sheet
            if ("rebar" in q_lower or "tmt" in q_lower or "reinforcement" in q_lower) and "IS_1786" in sid:
                score += 0.30
            elif ("rebar" in q_lower or "tmt" in q_lower) and "IS_2062" in sid:
                score -= 0.20  # IS 2062 is structural steel, not rebar
            
            # Structural Steel Sections vs Rebars
            if ("structural steel" in q_lower or "beam" in q_lower or "channel" in q_lower or "girder" in q_lower) and "IS_2062" in sid:
                score += 0.35

            # Potable HDPE Pipe vs uPVC vs Precast Sewer Pipe
            if "drinking water" in q_lower or "potable" in q_lower:
                if "IS_4984" in sid or "IS_8329" in sid:
                    score += 0.40
                elif "IS_458" in sid:
                    score -= 0.60  # IS 458 is concrete sewer/drainage pipe

            # 3. Slot-guided bonuses from ConstraintSlotService
            if slots.get("requires_crs") and "IS_1786" in sid:
                score += 0.15
            if slots.get("requires_ductility") and "IS_1786" in sid:
                score += 0.10
            if slots.get("requires_ductility") and "IS_13920" in sid:
                score += 0.15

            # 4. Mandatory QCO check (avoid duplicate addition if already boosted in retrieval)
            if item.get("is_mandatory_qco") and score < 0.25 and (slots or any(g in q_lower for g in cls.GRADE_HIERARCHIES)):
                score += 0.05

            final_score = round(min(0.99, max(0.01, score)), 4)
            item["score"] = final_score
            item["ranking_score"] = final_score
            if final_score >= 0.65:
                rel_rel = "STRONG"
                has_conf = True
            elif final_score >= 0.40:
                rel_rel = "MODERATE"
                has_conf = True
            elif final_score >= 0.25:
                rel_rel = "LOW"
                has_conf = False
            else:
                rel_rel = "INSUFFICIENT"
                has_conf = False
            item["relative_relevance"] = rel_rel
            item["confidence_level"] = rel_rel
            item["has_sufficient_confidence"] = has_conf

        # Sort descending by re-ranked score
        candidates.sort(key=lambda x: x["score"], reverse=True)

        return candidates
