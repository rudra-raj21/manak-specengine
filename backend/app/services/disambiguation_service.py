"""
Entropy-Based Active Disambiguation Clarifier for Manak-SpecEngine.
Detects underspecified, ambiguous procurement queries (e.g. 'pipe', 'cement', 'steel', 'transformer')
and generates an interactive clarification dialogue to guide users to the exact statutory standard.
"""

import math
from typing import Dict, Any, List, Optional


class DisambiguationService:
    """
    Evaluates candidate entropy and detects high-ambiguity technical domains.
    Provides structured multi-choice clarification prompts for procurement officers.
    """

    AMBIGUOUS_DOMAINS = {
        "pipe": {
            "prompt": "Your query matches multiple distinct BIS pipe categories. Please select your application:",
            "options": [
                {
                    "label": "Potable Drinking Water (Underground Pressure)",
                    "standard_id": "IS_4984",
                    "standard_number": "IS 4984:2016",
                    "title": "High Density Polyethylene (HDPE) Pipes",
                    "typical_grade": "PE 100 Class PN 10 / PN 16"
                },
                {
                    "label": "Municipal Water Trunk Mains & High Pressure",
                    "standard_id": "IS_8329",
                    "standard_number": "IS 8329:2000",
                    "title": "Centrifugally Cast (Ductile) Iron Pressure Pipes",
                    "typical_grade": "Class K7 / Class K9"
                },
                {
                    "label": "Agricultural Irrigation & Cold Water Plumbing",
                    "standard_id": "IS_4985",
                    "standard_number": "IS 4985:2021",
                    "title": "Unplasticized PVC (uPVC) Pipes for Potable Water",
                    "typical_grade": "Class 2 (0.4 MPa) to Class 5 (1.0 MPa)"
                },
                {
                    "label": "Storm Water Drainage & Sewerage (Gravity Flow)",
                    "standard_id": "IS_458",
                    "standard_number": "IS 458:2021",
                    "title": "Precast Concrete Pipes (With and Without Reinforcement)",
                    "typical_grade": "Class NP2 / NP3 / NP4"
                },
                {
                    "label": "Industrial Fire-Fighting & High Temperature Fluids",
                    "standard_id": "IS_1239",
                    "standard_number": "IS 1239 (Part 1):2004",
                    "title": "Steel Tubes and Tubulars for Water, Gas & Steam",
                    "typical_grade": "Medium / Heavy Class"
                }
            ]
        },
        "cement": {
            "prompt": "Multiple BIS cement standards exist depending on strength, curing speed, and chemical exposure. Please select:",
            "options": [
                {
                    "label": "High-Strength Structural RCC & Bridges (53 Grade)",
                    "standard_id": "IS_269",
                    "standard_number": "IS 269:2015",
                    "title": "Ordinary Portland Cement (OPC 53 Grade)",
                    "typical_grade": "Minimum 28-day compressive strength 53 MPa"
                },
                {
                    "label": "General Construction & Plastering (PPC - Fly Ash based)",
                    "standard_id": "IS_1489",
                    "standard_number": "IS 1489 (Part 1):2015",
                    "title": "Portland Pozzolana Cement (Fly Ash Based)",
                    "typical_grade": "Low heat of hydration, superior long-term strength"
                },
                {
                    "label": "Marine Structures, Coastal Foundations & High Sulphate Soils",
                    "standard_id": "IS_12330",
                    "standard_number": "IS 12330:1988",
                    "title": "Sulphate Resisting Portland Cement",
                    "typical_grade": "C3A content maximum 5.0% for chemical durability"
                }
            ]
        },
        "transformer": {
            "prompt": "Select the electrical rating and installation context for distribution transformers:",
            "options": [
                {
                    "label": "Outdoor Oil-Immersed Distribution (up to 2500 kVA, 33 kV)",
                    "standard_id": "IS_1180",
                    "standard_number": "IS 1180 (Part 1):2014",
                    "title": "Outdoor Type Oil Immersed Distribution Transformers",
                    "typical_grade": "Energy Efficiency Level 2 / Level 3 (BEE 3/4-Star)"
                },
                {
                    "label": "Indoor Dry-Type / Cast Resin Transformer (Fire-Safe Buildings)",
                    "standard_id": "IS_11171",
                    "standard_number": "IS 11171:1985",
                    "title": "Dry-Type Power Transformers",
                    "typical_grade": "Class F / Class H Insulation"
                }
            ]
        },
        "steel": {
            "prompt": "Steel in public procurement is strictly divided into reinforcing bars vs structural shapes. Please select:",
            "options": [
                {
                    "label": "Concrete Reinforcement Bars (TMT Rebars for RCC)",
                    "standard_id": "IS_1786",
                    "standard_number": "IS 1786:2008",
                    "title": "High Strength Deformed Steel Bars (Fe 500D / Fe 550D)",
                    "typical_grade": "Fe 500D High Ductility"
                },
                {
                    "label": "Structural Steel Sections, Beams, Columns & Plates",
                    "standard_id": "IS_2062",
                    "standard_number": "IS 2062:2011",
                    "title": "Hot Rolled Medium and High Tensile Structural Steel",
                    "typical_grade": "Grade E250 / Grade E350"
                }
            ]
        }
    }

    @classmethod
    def check_ambiguity(
        cls,
        query: str,
        candidates: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates Shannon entropy among candidate scores and checks for broad keyword domain ambiguity.
        Returns a clarification payload if ambiguity exceeds threshold or matches broad keywords.
        """
        q_tokens = query.lower().split()

        # 1. Broad keyword match (e.g. query is literally "pipe", "pipes", "cement", "transformer", "steel")
        for domain, clarif in cls.AMBIGUOUS_DOMAINS.items():
            if len(q_tokens) <= 3 and any(domain in t for t in q_tokens):
                return {
                    "is_ambiguous": True,
                    "domain": domain,
                    "prompt": clarif["prompt"],
                    "options": clarif["options"]
                }

        # 2. Score entropy calculation for top-5 candidates
        if len(candidates) >= 3:
            scores = [c.get("score", 0.1) for c in candidates[:5]]
            sum_s = sum(scores) or 1.0
            probs = [s / sum_s for s in scores]

            # Shannon Entropy: -sum(p * log2(p))
            entropy = -sum(p * math.log2(p) for p in probs if p > 0.0)

            # High entropy (> 2.1 on 5 items) indicates very flat score distribution
            if entropy > 2.1:
                # Find matching ambiguous domain
                for domain, clarif in cls.AMBIGUOUS_DOMAINS.items():
                    if any(domain in query.lower() for domain in [domain]):
                        return {
                            "is_ambiguous": True,
                            "entropy": round(entropy, 2),
                            "domain": domain,
                            "prompt": clarif["prompt"],
                            "options": clarif["options"]
                        }

        return None
