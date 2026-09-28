"""
Schedule of Rates (CPWD / MoRTH / DSR / GeM) Grounding Service for Manak-SpecEngine.
Maps procurement queries and tender clauses to authoritative government schedule items:
- CPWD Delhi Schedule of Rates (DSR 2023 / 2021)
- Ministry of Road Transport and Highways (MoRTH) Specifications for Road & Bridge Works
- Government e-Marketplace (GeM) Golden Parameters
- Military Engineer Services (MES) Standard Schedule of Rates (SSR)
"""

import re
from typing import Dict, Any, List, Optional


class ScheduleOfRatesService:
    """
    Grounds standards recommendations in real-world public procurement rate schedules.
    """

    SCHEDULE_INDEX = [
        {
            "schedule": "CPWD DSR (Subhead 3: Steel Work)",
            "item_code": "DSR 3.1 / 3.2",
            "trigger_keywords": ["cpwd item 3", "dsr 3.1", "dsr 3.2", "steel work", "tmt bar fixing", "rebar", "subhead 3"],
            "item_title": "Steel reinforcement for R.C.C. work including straightening, cutting, bending, placing in position and binding all complete above plinth level.",
            "prescribed_standard": "IS 1786:2008 Grade Fe 500D / Fe 550D",
            "standard_id": "IS_1786",
            "unit": "Kilogram (Kg) / Quintal",
            "mandatory_compliance": [
                "Only Thermo-Mechanically Treated (TMT) bars produced by Primary Producers or BIS approved re-rollers",
                "Mandatory Manufacturer Test Certificate (MTC) for each 50 MT batch",
                "Independent NABL lab tensile and 180° cold bend test"
            ]
        },
        {
            "schedule": "CPWD DSR (Subhead 10: Structural Steel Work)",
            "item_code": "DSR 10.1 / 10.2",
            "trigger_keywords": ["cpwd item 10", "dsr 10.1", "dsr 10.2", "structural steel work", "subhead 10", "steel truss", "built up section"],
            "item_title": "Structural steel work in single section, fixed without connect or with connecting plate, including cutting, hoisting, fixing in position and applying a priming coat of approved steel primer.",
            "prescribed_standard": "IS 2062:2011 Grade E250 (Quality A or BR)",
            "standard_id": "IS_2062",
            "unit": "Kilogram (Kg) / Metric Tonne (MT)",
            "mandatory_compliance": [
                "Strict conformity to IS 2062 with BIS Standard Mark",
                "Charpy V-Notch impact testing at 0°C for welded dynamic loading (Quality BR)",
                "Full penetration butt weld testing per IS 822"
            ]
        },
        {
            "schedule": "CPWD DSR (Subhead 18: Water Supply)",
            "item_code": "DSR 18.2 / 18.49",
            "trigger_keywords": ["cpwd item 18", "dsr 18.2", "dsr 18.49", "subhead 18", "hdpe pipe fixing", "water supply pipe"],
            "item_title": "Providing and fixing High Density Polyethylene (HDPE) pipes conforming to IS 4984 in trenches including jointing with butt fusion welding equipment.",
            "prescribed_standard": "IS 4984:2016 Grade PE 100 PN 10 / PN 16",
            "standard_id": "IS_4984",
            "unit": "Metre (m)",
            "mandatory_compliance": [
                "100% virgin grade polymer compound with carbon black dispersion 2.5 ± 0.5%",
                "Butt fusion jointing by certified technician with automated data logging",
                "Hydraulic field pressure testing to 1.5 times working pressure"
            ]
        },
        {
            "schedule": "MoRTH (Section 1000: Materials & Section 1600: Structural Steel)",
            "item_code": "MoRTH Section 1000 / 1600",
            "trigger_keywords": ["morth 1000", "morth 1600", "morth section 1000", "morth section 1600", "morth bridge", "highway bridge steel", "morth specification", "morth"],
            "item_title": "Specifications for Road and Bridge Works: Structural Steel Girder Fabrication & High Strength Rebars",
            "prescribed_standard": "IS 2062:2011 Grade E350 Quality B0/C (Steel) & IS 1786 Fe 500D CRS (Rebar)",
            "standard_id": "IS_2062",
            "unit": "Metric Tonne (MT)",
            "mandatory_compliance": [
                "Killed, fine-grain steel with ultrasonic testing as per IS 4225 for plates > 25 mm",
                "Charpy V-Notch impact test energy ≥ 27 Joules at -20°C (Grade C)",
                "Corrosion Resistant Steel (CRS) for all marine/coastal bridge sub-structures"
            ]
        },
        {
            "schedule": "GeM Category: Steel TMT Bars",
            "item_code": "GeM Category Ref: 52141501",
            "trigger_keywords": ["gem tmt", "gem steel", "gem golden parameters", "gem category"],
            "item_title": "GeM Standard Product Catalogue: High Strength Deformed Steel Bars for Concrete Reinforcement",
            "prescribed_standard": "IS 1786:2008 Grade Fe 500D (ISI Marked)",
            "standard_id": "IS_1786",
            "unit": "Metric Tonne (MT)",
            "mandatory_compliance": [
                "Mandatory operative BIS CM/L License at time of bidding",
                "Sulphur + Phosphorus (S+P) maximum 0.075%",
                "Minimum elongation at fracture 16.0%, Total elongation Agt ≥ 5.0%"
            ]
        }
    ]

    @classmethod
    def ground_query(cls, query: str, top_standard_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Finds the closest matching Government Schedule of Rates item for a query or standard.
        """
        q_lower = query.lower()

        # 1. Check keyword triggers
        for item in cls.SCHEDULE_INDEX:
            if any(re.search(r"\b" + re.escape(kw) + r"\b", q_lower) for kw in item["trigger_keywords"]):
                return item

        # 2. Check standard ID matching
        if top_standard_id:
            for item in cls.SCHEDULE_INDEX:
                if item["standard_id"] == top_standard_id:
                    return item

        return None
