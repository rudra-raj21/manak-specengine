"""
Standard BOM (Bill of Standards) Cascading Generator for Manak-SpecEngine.
Constructs a complete 5-layer statutory procurement bundle for any recommended BIS standard:
1. Product Standard & Grade
2. Governing Design & Execution Code of Practice
3. Mandatory Quality & Testing Protocols
4. Lot Sampling, Inspection & Statistical Acceptance Standard
5. Marking, Packaging & Delivery Conditions
"""

from typing import Dict, Any, List, Optional
from backend.app.services.graph_service import GraphService, get_graph_service


class StandardBOMService:
    """
    Assembles an autonomous Bill of Standards (SBOM) to ensure tenders are
    legally watertight, technically complete, and compliant with GFR 2017 & BIS Act 2016.
    """

    KNOWN_BOM_CATALOG: Dict[str, Dict[str, Any]] = {
        "IS_1786": {
            "tier_1_product": {
                "standard": "IS 1786:2008",
                "title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
                "recommended_grade": "Fe 500D (Earthquake & High Ductility) / Fe 500D CRS (Corrosion Resistant)",
                "mandate": "Mandatory ISI Mark under Steel & Steel Products QCO"
            },
            "tier_2_code_of_practice": [
                {"standard": "IS 456:2000", "clause": "Clause 5.6 & Table 16", "role": "Plain and Reinforced Concrete - Code of Practice"},
                {"standard": "IS 13920:2016", "clause": "Clause 5.1 - 5.4", "role": "Ductile Design and Detailing of Reinforced Concrete Structures Subjected to Seismic Forces"},
                {"standard": "SP 34", "clause": "Section 4", "role": "Handbook on Concrete Reinforcement and Detailing"}
            ],
            "tier_3_testing_protocols": [
                {"standard": "IS 1608 (Part 1):2018", "test": "Tensile Testing (0.2% Proof Stress, Tensile Strength, Elongation at Ambient Temp)"},
                {"standard": "IS 1599:2019", "test": "Cold Bend and Rebend Testing (Mandatory 180° / 135° bend around mandrel)"},
                {"standard": "IS 228 (Various Parts)", "test": "Chemical Determination of Carbon, Sulphur, Phosphorus"}
            ],
            "tier_4_sampling_and_inspection": {
                "standard": "IS 4987:1990",
                "title": "Recommendations for Sampling of Steel Bars and Wires for Concrete Reinforcement",
                "batch_frequency": "1 test sample per 50 metric tonnes (MT) per heat/cast or part thereof"
            },
            "tier_5_marking_and_delivery": {
                "standard": "IS 1387:1993",
                "title": "General Requirements for the Supply of Metallurgical Materials",
                "marking_requirement": "Every bundle must bear a tamper-proof metal tag with CM/L License No, Heat No, Grade Fe 500D, and Manufacturer Name"
            }
        },
        "IS_2062": {
            "tier_1_product": {
                "standard": "IS 2062:2011",
                "title": "Hot Rolled Medium and High Tensile Structural Steel",
                "recommended_grade": "E250 Quality A / BR (General Construction) or E350 Quality B / C (Bridges & Heavy Loading)",
                "mandate": "Mandatory ISI Mark under Steel & Steel Products QCO"
            },
            "tier_2_code_of_practice": [
                {"standard": "IS 800:2007", "clause": "General Section 2 & 3", "role": "General Construction in Steel - Code of Practice"},
                {"standard": "IS 801:1975", "clause": "Section 4", "role": "Code of Practice for Use of Cold-formed Light Gauge Steel"}
            ],
            "tier_3_testing_protocols": [
                {"standard": "IS 1608 (Part 1):2018", "test": "Tensile & Yield Stress Determination"},
                {"standard": "IS 1599:2019", "test": "Bend Test for Plates and Sections"},
                {"standard": "IS 1757 (Part 1):2014", "test": "Charpy Impact Test (V-Notch at 0°C or -20°C for Quality BR/B/C)"}
            ],
            "tier_4_sampling_and_inspection": {
                "standard": "IS 1956",
                "title": "Glossary of terms relating to iron and steel / Sampling plans",
                "batch_frequency": "1 complete mechanical test per cast/heat or 40 tonnes lot"
            },
            "tier_5_marking_and_delivery": {
                "standard": "IS 1387:1993",
                "title": "General Requirements for the Supply of Metallurgical Materials",
                "marking_requirement": "Colour coding by grade on plate ends + stamped Heat Number and BIS ISI Certification Mark"
            }
        },
        "IS_4984": {
            "tier_1_product": {
                "standard": "IS 4984:2016",
                "title": "High Density Polyethylene (HDPE) Pipes for Water Supply - Specification",
                "recommended_grade": "PE 100 Class PN 6 / PN 10 / PN 16 (Virgin Grade Resin only)",
                "mandate": "Mandatory ISI Mark under Quality Control Order"
            },
            "tier_2_code_of_practice": [
                {"standard": "IS 7634 (Part 2):2012", "clause": "Section 3 - 6", "role": "Code of Practice for Laying and Jointing of Polyethylene Pipes in Underground Trenches"},
                {"standard": "CPHEEO Manual", "clause": "Chapter 6", "role": "Manual on Water Supply and Treatment (Ministry of Housing and Urban Affairs)"}
            ],
            "tier_3_testing_protocols": [
                {"standard": "IS 4984:2016 (Annex B)", "test": "Internal Hydrostatic Pressure Test (80°C for 165 hours and 1000 hours)"},
                {"standard": "IS 2530:1963", "test": "Carbon Black Content and Dispersion in Polyethylene Compounds (2.5 ± 0.5%)"},
                {"standard": "IS 13360 (Part 4/Sec 1)", "test": "Melt Flow Rate (MFR) Testing (0.2 to 1.1 g/10 min)"}
            ],
            "tier_4_sampling_and_inspection": {
                "standard": "IS 4984:2016 (Table 4)",
                "title": "Scale of Sampling and Permissible Number of Defectives",
                "batch_frequency": "Samples drawn from lots of up to 1000 lengths of pipe per extrusion line"
            },
            "tier_5_marking_and_delivery": {
                "standard": "IS 4984:2016 (Clause 11)",
                "title": "Marking on Pipe Shell",
                "marking_requirement": "Indelible hot-embossed lettering every 1 metre: 'IS 4984', CM/L No, 'PE 100', 'PN 10', SDR No, Batch No, and 'WATER'"
            }
        },
        "IS_1180": {
            "tier_1_product": {
                "standard": "IS 1180 (Part 1):2014",
                "title": "Outdoor Type Oil Immersed Distribution Transformers up to and including 2500 kVA, 33 kV",
                "recommended_grade": "Energy Efficiency Level 2 / Level 3 (BEE 3-Star / 4-Star Equivalent)",
                "mandate": "Mandatory ISI Mark under Distribution Transformers QCO"
            },
            "tier_2_code_of_practice": [
                {"standard": "IS 10028 (Part 1-3)", "clause": "Clause 4", "role": "Code of Practice for Selection, Installation and Maintenance of Transformers"},
                {"standard": "CEA Regulations 2010", "clause": "Regulation 35", "role": "Central Electricity Authority Measures relating to Safety and Electric Supply"}
            ],
            "tier_3_testing_protocols": [
                {"standard": "IS 2026 (Part 1-5)", "test": "Power Transformers Routine and Type Tests (Winding resistance, No-load loss, Temperature rise)"},
                {"standard": "IS 335:2018", "test": "Unused Mineral Insulating Oils for Transformers and Switchgear"},
                {"standard": "IS 6792:1992", "test": "Method for determination of electric strength of insulating oils"}
            ],
            "tier_4_sampling_and_inspection": {
                "standard": "IS 1180 (Part 1) Clause 21",
                "title": "Routine and Acceptance Tests",
                "batch_frequency": "100% routine tests at factory + 1 unit per rating subjected to temperature rise type test"
            },
            "tier_5_marking_and_delivery": {
                "standard": "IS 1180 (Part 1) Clause 22",
                "title": "Rating Plate & Terminal Marking",
                "marking_requirement": "Stainless steel rating plate stamped with BIS Standard Mark, CM/L No, BEE Star Rating, Guaranteed Total Losses at 50% and 100%"
            }
        }
    }

    @classmethod
    def generate_bom(cls, standard_id: str, graph_service: Optional[GraphService] = None) -> Dict[str, Any]:
        """
        Generates or extracts the 5-tier Standard BOM for the given standard.
        Falls back to dynamic knowledge graph neighborhood traversal if not in pre-compiled catalog.
        """
        sid_norm = standard_id.upper().replace(" ", "_")
        for key in cls.KNOWN_BOM_CATALOG:
            if key in sid_norm:
                return cls.KNOWN_BOM_CATALOG[key]

        # Dynamic fallback using GraphService
        graph = graph_service or get_graph_service()
        std_meta = graph.get_standard(standard_id) or {}
        neighbors = graph.get_1hop_neighbors(standard_id)

        normative_refs = neighbors.get("normative_references", [])
        test_methods = neighbors.get("test_methods", [])

        code_of_practices = [
            {"standard": ref["is_number"], "clause": "Applicable Clauses", "role": ref.get("title", "")}
            for ref in normative_refs if "code" in ref.get("title", "").lower() or "practice" in ref.get("title", "").lower()
        ]
        if not code_of_practices and normative_refs:
            code_of_practices = [{"standard": normative_refs[0]["is_number"], "clause": "Normative Clause", "role": normative_refs[0].get("title", "")}]

        testing_protocols = [
            {"standard": tm["is_number"], "test": tm.get("title", "Standard Quality and Performance Test")}
            for tm in test_methods
        ]
        if not testing_protocols and len(normative_refs) > 1:
            testing_protocols = [{"standard": normative_refs[1]["is_number"], "test": normative_refs[1].get("title", "")}]

        return {
            "tier_1_product": {
                "standard": std_meta.get("is_number", standard_id.replace("_", " ")),
                "title": std_meta.get("title", "Governing Standard Specification"),
                "recommended_grade": "Standard Grade conforming to Table 1 / Clause 4",
                "mandate": "BIS Conformance mandated per General Financial Rules (GFR), 2017"
            },
            "tier_2_code_of_practice": code_of_practices[:3],
            "tier_3_testing_protocols": testing_protocols[:3],
            "tier_4_sampling_and_inspection": {
                "standard": "IS 2500 (Part 1):2000",
                "title": "Sampling Procedures for Inspection by Attributes",
                "batch_frequency": "Standard production inspection lots per quality assurance plan (QAP)"
            },
            "tier_5_marking_and_delivery": {
                "standard": "IS 1387 / General Packaging Standards",
                "title": "Marking and Packaging Protocol",
                "marking_requirement": f"Permanent marking of Standard Number {std_meta.get('is_number', '')} and valid manufacturer CM/L License Number"
            }
        }
