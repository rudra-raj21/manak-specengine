"""
Constraint & Slot-Filling Engine for Manak-SpecEngine.
Extracts environmental exposure class, seismic zone, corrosion environment,
infrastructure type, and material constraints from unstructured procurement queries
to guide precision standard and grade recommendation.
"""

import re
from typing import Dict, Any, List, Optional


class ConstraintSlotService:
    """
    Extracts multi-attribute civil, mechanical, and regulatory slots from procurement queries:
    - Exposure Class (IS 456 Table 16): Mild, Moderate, Severe, Very Severe, Extreme
    - Seismic Zone (IS 1893 / IS 13920): Zone II, Zone III, Zone IV, Zone V
    - Corrosion Context: Coastal, Marine, Industrial, Saline, High-humidity, Chemical
    - Asset / Infrastructure Type: Bridge, Foundation, High-Rise, Tunnel, Dam, Potable Water, Road
    - Pressure Class: Gravity / Non-pressure, PN 6, PN 10, PN 16
    """

    EXPOSURE_CLASSES = {
        "extreme": ["extreme", "tidal zone", "direct sea water spray", "abrasive chemical"],
        "very severe": ["very severe", "sea water spray", "corrosive fumes", "freezing saline"],
        "severe": ["severe", "coastal", "marine", "submerged in sea water", "aggressive soil"],
        "moderate": ["moderate", "sheltered from rain", "submerged in fresh water"],
        "mild": ["mild", "indoor", "non-aggressive", "normal atmosphere"]
    }

    SEISMIC_ZONES = {
        "zone v": ["zone v", "zone 5", "high seismic", "highest earthquake", "severe seismic zone"],
        "zone iv": ["zone iv", "zone 4", "seismic zone 4", "earthquake prone"],
        "zone iii": ["zone iii", "zone 3", "moderate seismic"],
        "zone ii": ["zone ii", "zone 2", "low seismic"]
    }

    CORROSION_ENVIRONMENTS = {
        "marine_coastal": ["coastal", "marine", "sea shore", "near ocean", "saline soil", "saline water", "creek"],
        "industrial_chemical": ["chemical plant", "acidic", "effluent", "corrosive fumes", "fertilizer plant"],
        "normal": ["inland", "dry", "normal atmosphere"]
    }

    INFRASTRUCTURE_TYPES = {
        "bridge": ["bridge", "flyover", "viaduct", "metro pier", "culvert"],
        "marine_structure": ["jetty", "port", "harbour", "wharf", "quay"],
        "high_rise": ["high rise", "tall building", "multi-storey", "commercial tower"],
        "water_supply": ["potable water", "drinking water", "water transmission", "water mains", "water distribution"],
        "sewerage_drainage": ["sewer", "drainage", "storm water", "effluent drain", "sewage"],
        "electrical_substation": ["substation", "transmission line", "switchyard", "distribution grid"],
        "dam_hydraulic": ["dam", "barrage", "canal", "spillway", "hydroelectric"]
    }

    @classmethod
    def extract_slots(cls, query: str) -> Dict[str, Any]:
        """Parses query text into structured engineering and environmental slots."""
        q_lower = query.lower()

        # 1. Detect Exposure Class
        exposure = None
        for exp, kws in cls.EXPOSURE_CLASSES.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", q_lower) for kw in kws):
                exposure = exp
                break

        # 2. Detect Seismic Zone
        seismic = None
        for sz, kws in cls.SEISMIC_ZONES.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", q_lower) for kw in kws):
                seismic = sz
                break

        # 3. Detect Corrosion Context
        corrosion = None
        for corr, kws in cls.CORROSION_ENVIRONMENTS.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", q_lower) for kw in kws):
                corrosion = corr
                break

        # 4. Detect Infrastructure Type
        infra = None
        for inf_type, kws in cls.INFRASTRUCTURE_TYPES.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", q_lower) for kw in kws):
                infra = inf_type
                break

        # 5. Detect Pressure Rating
        pressure = None
        p_match = re.search(r"\b(?:working pressure\s*)?(\d+\s*(?:bar|kg/cm2|mpa)|pn\s*\d+)\b", q_lower)
        if p_match:
            pressure = p_match.group(1).upper()
        elif "gravity" in q_lower or "non-pressure" in q_lower:
            pressure = "NON-PRESSURE / GRAVITY"

        # 6. Extract Mandated Grade Hints
        grade_hint = None
        if "fe 500d" in q_lower or "500d" in q_lower:
            grade_hint = "Fe 500D"
        elif "fe 550d" in q_lower or "550d" in q_lower:
            grade_hint = "Fe 550D"
        elif "fe 415d" in q_lower:
            grade_hint = "Fe 415D"
        elif "e250" in q_lower:
            grade_hint = "E250"
        elif "e350" in q_lower:
            grade_hint = "E350"
        elif "pe 100" in q_lower:
            grade_hint = "PE 100"
        elif "pe 80" in q_lower:
            grade_hint = "PE 80"

        # 7. Check if Corrosion Resistant Steel (CRS) is required
        requires_crs = bool(corrosion == "marine_coastal" or exposure in ["severe", "very severe", "extreme"])

        # 8. Check if Ductile Detailing is required
        requires_ductility = bool(seismic in ["zone iv", "zone v"] or infra in ["bridge", "high_rise"])

        return {
            "exposure_class": exposure,
            "seismic_zone": seismic,
            "corrosion_environment": corrosion,
            "infrastructure_type": infra,
            "pressure_rating": pressure,
            "grade_hint": grade_hint,
            "requires_crs": requires_crs,
            "requires_ductility": requires_ductility,
            "has_special_constraints": bool(exposure or seismic or corrosion or infra or requires_crs or requires_ductility)
        }

    @classmethod
    def evaluate_constraint_bonus(cls, standard_id: str, doc_title: str, doc_scope: str, slots: Dict[str, Any]) -> float:
        """
        Calculates an additive or multiplicative score adjustment based on whether
        the candidate standard satisfies the extracted environmental and engineering constraints.
        """
        bonus = 0.0
        sid_norm = standard_id.upper()
        content = (doc_title + " " + doc_scope).lower()

        # Constraint 1: Rebar in Coastal / Seismic Zone V
        if "IS_1786" in sid_norm:
            if slots.get("requires_crs"):
                bonus += 0.40  # Boost IS 1786 because it governs Fe 500D CRS
            if slots.get("requires_ductility"):
                bonus += 0.35  # IS 1786 specifies high elongation 'D' grades
        
        # Constraint 2: Ductile Detailing code in Seismic Zone IV / V
        if "IS_13920" in sid_norm and slots.get("requires_ductility"):
            bonus += 0.60

        # Constraint 3: Plain and Reinforced Concrete code in severe environments
        if "IS_456" in sid_norm and (slots.get("exposure_class") or slots.get("infrastructure_type") in ["bridge", "high_rise"]):
            bonus += 0.30

        # Constraint 4: Potable Water vs Sewerage for pipes
        if slots.get("infrastructure_type") == "water_supply":
            if "IS_4984" in sid_norm or "IS_8329" in sid_norm:
                bonus += 0.50  # HDPE / DI pipes are prime potable water standards
            elif "IS_458" in sid_norm or "sewer" in content:
                bonus -= 0.50  # Penalize concrete sewer pipe for drinking water
        elif slots.get("infrastructure_type") == "sewerage_drainage":
            if "IS_458" in sid_norm or "IS_14333" in sid_norm:
                bonus += 0.50  # Precast concrete sewer or sewerage HDPE
            elif "potable" in content:
                bonus -= 0.30

        # Constraint 5: Structural Steel Grade E350 for bridges / high fatigue
        if "IS_2062" in sid_norm and slots.get("infrastructure_type") in ["bridge", "high_rise"]:
            bonus += 0.30

        return bonus
