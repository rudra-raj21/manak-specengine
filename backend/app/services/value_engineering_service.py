"""
Multi-Tier Value Engineering Optimizer for Manak-SpecEngine.
Generates a 3-tier comparative matrix (Minimum Statutory, Value Engineering Optimum,
and Critical Infrastructure) to prevent both under-specification and wasteful over-engineering.
"""

from typing import Dict, Any, List, Optional


class ValueEngineeringService:
    """
    Computes comparative grade and life-cycle cost trade-offs for recommended Indian Standards.
    """

    TIER_MATRICES: Dict[str, List[Dict[str, Any]]] = {
        "IS_1786": [
            {
                "tier": "Tier 1: Minimum Statutory Compliant",
                "grade": "IS 1786 Fe 415D",
                "initial_cost_index": "1.00x (Baseline)",
                "structural_weight_saving": "0% (Heavier sections required)",
                "design_yield_strength": "415 N/mm²",
                "min_elongation": "18.0%",
                "corrosion_resistance": "Standard (Non-saline only)",
                "lifecycle_durability": "30 - 50 Years",
                "recommended_for": "Single or two-storey rural buildings, low-risk boundary structures in Seismic Zone II."
            },
            {
                "tier": "Tier 2: Value Engineering Optimum (RECOMMENDED)",
                "grade": "IS 1786 Fe 500D",
                "initial_cost_index": "1.04x (+4% material rate)",
                "structural_weight_saving": "15% - 20% Net Steel Savings",
                "design_yield_strength": "500 N/mm²",
                "min_elongation": "16.0% (Uniform Agt ≥ 5%)",
                "corrosion_resistance": "Moderate (S+P ≤ 0.075%)",
                "lifecycle_durability": "60 - 80 Years",
                "recommended_for": "Multi-storey commercial/residential buildings, institutional campuses, hospital blocks in Seismic Zones III & IV. Provides optimal balance of structural ductility and total construction cost savings."
            },
            {
                "tier": "Tier 3: Critical Infrastructure & Coastal Exposure",
                "grade": "IS 1786 Fe 550D CRS (Corrosion Resistant Steel)",
                "initial_cost_index": "1.18x (+18% material rate)",
                "structural_weight_saving": "22% - 28% Net Steel Savings",
                "design_yield_strength": "550 N/mm²",
                "min_elongation": "14.5% (Uniform Agt ≥ 5%)",
                "corrosion_resistance": "High (Micro-alloyed with Cu, Cr, P)",
                "lifecycle_durability": "100+ Years (Reduced Spalling)",
                "recommended_for": "Highway bridges, metro flyovers, coastal ports, marine jetties, dams, and major public infrastructure in Seismic Zone V."
            }
        ],
        "IS_2062": [
            {
                "tier": "Tier 1: Minimum Statutory Compliant",
                "grade": "IS 2062 Grade E250 Quality A",
                "initial_cost_index": "1.00x (Baseline)",
                "structural_weight_saving": "0% (Standard tonnage)",
                "design_yield_strength": "250 MPa",
                "min_elongation": "23%",
                "corrosion_resistance": "Standard Carbon Steel",
                "lifecycle_durability": "Standard (Requires Periodic Priming)",
                "recommended_for": "Simple shed roof trusses, agricultural storage structures, temporary falsework, standard purlins."
            },
            {
                "tier": "Tier 2: Value Engineering Optimum (RECOMMENDED)",
                "grade": "IS 2062 Grade E250 Quality BR",
                "initial_cost_index": "1.05x (+5%)",
                "structural_weight_saving": "5% - 10% (Permits dynamic loading)",
                "design_yield_strength": "250 MPa",
                "min_elongation": "23% (Charpy 27J at 0°C)",
                "corrosion_resistance": "Killed Steel with Low Inclusions",
                "lifecycle_durability": "75+ Years",
                "recommended_for": "Industrial warehouse frames, crane gantries, airport terminal canopies, and welded portal frames subjected to dynamic vibration."
            },
            {
                "tier": "Tier 3: Critical Infrastructure & Coastal Exposure",
                "grade": "IS 2062 Grade E350 Quality C (Sub-Zero Impact Tested)",
                "initial_cost_index": "1.20x (+20%)",
                "structural_weight_saving": "20% - 25% Reduction in Steel Section Weight",
                "design_yield_strength": "350 MPa",
                "min_elongation": "22% (Charpy 27J at -20°C)",
                "corrosion_resistance": "High Tensile Fully Killed Fine Grain",
                "lifecycle_durability": "100+ Years",
                "recommended_for": "Major railway bridges, highway flyovers, heavy seismic truss girders, and cold region structural installations."
            }
        ],
        "IS_4984": [
            {
                "tier": "Tier 1: Minimum Statutory Compliant",
                "grade": "IS 4984 PE 80 PN 6",
                "initial_cost_index": "1.00x (Baseline)",
                "structural_weight_saving": "0%",
                "design_yield_strength": "MRS 8.0 MPa",
                "min_elongation": "High Ductility",
                "corrosion_resistance": "100% Rust & Scale Proof",
                "lifecycle_durability": "30 - 40 Years",
                "recommended_for": "Low pressure gravity irrigation, rural single-village water schemes."
            },
            {
                "tier": "Tier 2: Value Engineering Optimum (RECOMMENDED)",
                "grade": "IS 4984 PE 100 PN 10 (SDR 17)",
                "initial_cost_index": "1.12x (+12%)",
                "structural_weight_saving": "20% Thinner Wall Thickness for Same Pressure",
                "design_yield_strength": "MRS 10.0 MPa",
                "min_elongation": "Superior Surge Resistance",
                "corrosion_resistance": "Virgin Polyethylene with 2.5% Carbon Black",
                "lifecycle_durability": "50+ Years",
                "recommended_for": "Municipal drinking water distribution networks, JJM (Jal Jeevan Mission) rural tap water networks."
            },
            {
                "tier": "Tier 3: Critical Infrastructure & Coastal Exposure",
                "grade": "IS 4984 PE 100 PN 16 (SDR 11)",
                "initial_cost_index": "1.30x (+30%)",
                "structural_weight_saving": "Extreme Pressure Containment",
                "design_yield_strength": "MRS 10.0 MPa (16 Bar Working Pressure)",
                "min_elongation": "Maximum Crack Propagation Resistance",
                "corrosion_resistance": "Impervious to Aggressive Coastal & Saline Soils",
                "lifecycle_durability": "75+ Years",
                "recommended_for": "High-head pumping transmission mains, underwater creek crossings, industrial chemical effluent lines."
            }
        ]
    }

    @classmethod
    def get_value_engineering_matrix(cls, standard_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the 3-tier comparative value engineering matrix for the given standard.
        """
        sid_norm = standard_id.upper().replace(" ", "_")
        for key in cls.TIER_MATRICES:
            if key in sid_norm:
                return cls.TIER_MATRICES[key]

        # Generic 3-tier fallback
        return [
            {
                "tier": "Tier 1: Standard Compliant",
                "grade": "Baseline Grade",
                "initial_cost_index": "1.00x",
                "structural_weight_saving": "Baseline",
                "lifecycle_durability": "Standard Operational Life",
                "recommended_for": "General non-critical public works."
            },
            {
                "tier": "Tier 2: Value Engineering Optimum (RECOMMENDED)",
                "grade": "High Performance Grade",
                "initial_cost_index": "1.08x",
                "structural_weight_saving": "10% - 15% Savings",
                "lifecycle_durability": "Extended Durability",
                "recommended_for": "Mainstream institutional and commercial government projects."
            },
            {
                "tier": "Tier 3: Critical Infrastructure",
                "grade": "Severe Duty / Special Alloy",
                "initial_cost_index": "1.25x",
                "structural_weight_saving": "20%+ Savings",
                "lifecycle_durability": "Maximum Longevity",
                "recommended_for": "Strategic infrastructure, bridges, coastal assets, and lifeline facilities."
            }
        ]
