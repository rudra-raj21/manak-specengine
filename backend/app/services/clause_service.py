"""
Clause-Level Specification & Engineering Properties Service for Bureau of Indian Standards (BIS).
Provides granular chemical, mechanical, dimensional, and testing tolerances for public procurement.
"""

from typing import Dict, Any, Optional, List


CLAUSE_CATALOG: Dict[str, Dict[str, Any]] = {
    "IS 1786": {
        "is_number": "IS 1786",
        "title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
        "current_revision": "IS 1786:2008 (Fourth Revision with Amendments 1, 2 & 3)",
        "grades": ["Fe 415", "Fe 415D", "Fe 500", "Fe 500D", "Fe 550", "Fe 550D", "Fe 600"],
        "chemical_composition": {
            "clause": "Clause 4.2, Table 1",
            "table_title": "Chemical Composition of High Strength Deformed Steel Bars (Max % by Mass)",
            "columns": ["Constituent", "Fe 415 / Fe 500", "Fe 415D / Fe 500D", "Fe 550D", "Fe 600"],
            "rows": [
                {"constituent": "Carbon (C)", "fe_std": "0.30% max", "fe_d": "0.25% max", "fe_550d": "0.25% max", "fe_600": "0.30% max"},
                {"constituent": "Sulphur (S)", "fe_std": "0.060% max", "fe_d": "0.040% max", "fe_550d": "0.040% max", "fe_600": "0.040% max"},
                {"constituent": "Phosphorus (P)", "fe_std": "0.060% max", "fe_d": "0.040% max", "fe_550d": "0.040% max", "fe_600": "0.040% max"},
                {"constituent": "S + P Combined", "fe_std": "0.110% max", "fe_d": "0.075% max", "fe_550d": "0.075% max", "fe_600": "0.075% max"},
                {"constituent": "Carbon Equivalent (CE)", "fe_std": "0.42% max", "fe_d": "0.42% max", "fe_550d": "0.44% max", "fe_600": "0.45% max"}
            ],
            "procurement_note": "For seismic zones III, IV & V, only 'D' grades (Fe 500D / Fe 550D) with higher ductility (S+P <= 0.075%) are legally acceptable."
        },
        "mechanical_properties": {
            "clause": "Clause 8.1, Table 3",
            "table_title": "Mechanical Requirements for Deformed Steel Bars",
            "columns": ["Property", "Fe 415", "Fe 500", "Fe 500D", "Fe 550D", "Fe 600"],
            "rows": [
                {"property": "0.2% Proof Stress / Yield Stress (Min, MPa)", "fe_415": "415.0", "fe_500": "500.0", "fe_500d": "500.0", "fe_550d": "550.0", "fe_600": "600.0"},
                {"property": "Tensile Strength Rm (Min, MPa)", "fe_415": ">= 1.10 x Re", "fe_500": ">= 1.08 x Re", "fe_500d": ">= 1.10 x Re", "fe_550d": ">= 1.08 x Re", "fe_600": ">= 1.06 x Re"},
                {"property": "Elongation on Gauge Length 5.65√A (Min %)", "fe_415": "14.5%", "fe_500": "12.0%", "fe_500d": "16.0%", "fe_550d": "14.5%", "fe_600": "10.0%"},
                {"property": "Total Elongation at Max Force Agt (Min %)", "fe_415": "--", "fe_500": "--", "fe_500d": "5.0%", "fe_550d": "5.0%", "fe_600": "--"}
            ]
        },
        "testing_protocols": [
            {"test_name": "Tensile & Yield Proof Stress Test", "clause": "Clause 8.1", "reference_standard": "IS 1608 (Part 1)", "criteria": "Full section testing without machining"},
            {"test_name": "Bend Test (Cold Bend 180°)", "clause": "Clause 8.3, Table 4", "reference_standard": "IS 1599", "criteria": "Mandrel 3d for dia <= 20mm; 4d for dia > 20mm; no transverse cracks"},
            {"test_name": "Re-bend Test", "clause": "Clause 8.4", "reference_standard": "IS 1786 Clause 8.4", "criteria": "Bent to 135°, boiled in water 100°C for 30 mins, bent back 157.5°"},
            {"test_name": "Nominal Mass & Tolerance", "clause": "Clause 6.2, Table 2", "reference_standard": "IS 1786", "criteria": "+/- 7% (dia <= 10mm), +/- 5% (12-16mm), +/- 3% (> 16mm)"}
        ]
    },
    "IS 2062": {
        "is_number": "IS 2062",
        "title": "Hot Rolled Medium and High Tensile Structural Steel",
        "current_revision": "IS 2062:2011 (Seventh Revision)",
        "grades": ["E250", "E275", "E300", "E350", "E410", "E450", "E550", "E650"],
        "chemical_composition": {
            "clause": "Clause 6.1, Table 1",
            "table_title": "Chemical Composition of Structural Steel (Max % by Mass)",
            "columns": ["Grade & Subgrade", "C max", "Mn max", "S max", "P max", "CE max"],
            "rows": [
                {"grade": "E250 Subgrade A", "c": "0.23", "mn": "1.50", "s": "0.045", "p": "0.045", "ce": "0.42"},
                {"grade": "E250 Subgrade B0", "c": "0.22", "mn": "1.50", "s": "0.045", "p": "0.045", "ce": "0.41"},
                {"grade": "E250 Subgrade BR", "c": "0.22", "mn": "1.50", "s": "0.045", "p": "0.045", "ce": "0.41"},
                {"grade": "E350 Subgrade A", "c": "0.20", "mn": "1.60", "s": "0.045", "p": "0.045", "ce": "0.47"},
                {"grade": "E350 Subgrade B0", "c": "0.20", "mn": "1.60", "s": "0.040", "p": "0.040", "ce": "0.45"}
            ],
            "procurement_note": "Carbon Equivalent CE = C + Mn/6 + (Cr+Mo+V)/5 + (Ni+Cu)/15. Mandatory for weldability assurance."
        },
        "mechanical_properties": {
            "clause": "Clause 8.1, Table 2",
            "table_title": "Mechanical Properties of Structural Steel Plates & Sections",
            "columns": ["Grade", "Yield Stress (t < 20mm)", "Tensile Strength (MPa)", "Elongation % min", "Charpy V-Notch Temp"],
            "rows": [
                {"grade": "E250 A", "yield": "250 MPa min", "tensile": "410 MPa min", "elong": "23%", "charpy": "Not tested"},
                {"grade": "E250 B0", "yield": "250 MPa min", "tensile": "410 MPa min", "elong": "23%", "charpy": "27 Joules at 0°C"},
                {"grade": "E250 C", "yield": "250 MPa min", "tensile": "410 MPa min", "elong": "23%", "charpy": "27 Joules at -20°C"},
                {"grade": "E350 B0", "yield": "350 MPa min", "tensile": "490 MPa min", "elong": "22%", "charpy": "27 Joules at 0°C"}
            ]
        },
        "testing_protocols": [
            {"test_name": "Tensile Testing", "clause": "Clause 8.1", "reference_standard": "IS 1608 (Part 1)", "criteria": "Gauge length 5.65√So"},
            {"test_name": "Charpy V-Notch Impact Test", "clause": "Clause 9.1", "reference_standard": "IS 1757", "criteria": "Average of 3 test specimens >= 27 J"},
            {"test_name": "Bend Test", "clause": "Clause 8.2", "reference_standard": "IS 1599", "criteria": "Internal diameter 2t to 3t bent through 180° without cracking"}
        ]
    },
    "IS 4984": {
        "is_number": "IS 4984",
        "title": "High Density Polyethylene (HDPE) Pipes for Potable Water Supplies",
        "current_revision": "IS 4984:2016 (Fifth Revision)",
        "grades": ["PE 63", "PE 80", "PE 100"],
        "chemical_composition": {
            "clause": "Clause 5.1 & 7.3",
            "table_title": "Raw Material Composition & Carbon Black dispersion",
            "columns": ["Parameter", "Requirement", "Test Method"],
            "rows": [
                {"parameter": "Base Polymer Density", "requirement": "940 to 958 kg/m³", "test": "IS 7328 / IS 12235 (Part 2)"},
                {"parameter": "Melt Flow Rate (MFR 190°C/5kg)", "requirement": "0.2 to 1.4 g/10 min", "test": "IS 2530"},
                {"parameter": "Carbon Black Content", "requirement": "2.0% to 2.5% by mass", "test": "IS 2530"},
                {"parameter": "Carbon Black Dispersion", "requirement": "Grade <= 3", "test": "IS 2530"}
            ]
        },
        "mechanical_properties": {
            "clause": "Clause 8.1, Table 4",
            "table_title": "Hydrostatic Strength Requirements",
            "columns": ["Test Duration", "Test Temp (°C)", "Induced Stress PE 80", "Induced Stress PE 100"],
            "rows": [
                {"test": "100 Hours Acceptance Test", "temp": "20°C", "pe_80": "9.0 MPa", "pe_100": "12.4 MPa"},
                {"test": "165 Hours Quality Test", "temp": "80°C", "pe_80": "4.6 MPa", "pe_100": "5.5 MPa"},
                {"test": "1000 Hours Type Test", "temp": "80°C", "pe_80": "4.0 MPa", "pe_100": "5.0 MPa"}
            ]
        },
        "testing_protocols": [
            {"test_name": "Internal Hydrostatic Pressure", "clause": "Clause 8.1", "reference_standard": "IS 12235 (Part 8)", "criteria": "No rupture or weep during designated test period"},
            {"test_name": "Elongation at Break", "clause": "Clause 8.2", "reference_standard": "IS 12235 (Part 5)", "criteria": ">= 350% min"},
            {"test_name": "Oxidation Induction Time (OIT)", "clause": "Clause 8.4", "reference_standard": "IS 12235 (Part 11)", "criteria": ">= 20 minutes at 200°C"}
        ]
    },
    "IS 4985": {
        "is_number": "IS 4985",
        "title": "Unplasticized PVC (uPVC) Pipes for Potable Water Supplies",
        "current_revision": "IS 4985:2021 (Fourth Revision)",
        "grades": ["Class 1 (0.25 MPa)", "Class 2 (0.4 MPa)", "Class 3 (0.6 MPa)", "Class 4 (1.0 MPa)", "Class 5 (1.25 MPa)", "Class 6 (1.6 MPa)"],
        "chemical_composition": {
            "clause": "Clause 5.1 & 5.2",
            "table_title": "Raw Material Composition & Lead Extraction Limits",
            "columns": ["Constituent / Parameter", "Limit", "Standard Clause"],
            "rows": [
                {"parameter": "PVC Resin K-Value", "requirement": "K-66 to K-68", "test": "IS 12235"},
                {"parameter": "Lead (Pb) Extraction (First extraction)", "requirement": "Max 1.0 mg/litre", "test": "IS 12235 (Part 10)"},
                {"parameter": "Lead (Pb) Extraction (Third extraction)", "requirement": "Max 0.05 mg/litre (Food Contact Safe)", "test": "IS 12235 (Part 10)"}
            ]
        },
        "mechanical_properties": {
            "clause": "Clause 10, Table 3",
            "table_title": "Physical and Mechanical Test Requirements",
            "columns": ["Property", "Requirement", "Test Method Clause"],
            "rows": [
                {"property": "Vicat Softening Temperature", "requirement": ">= 80°C min", "test": "Clause 10.3 / IS 12235 (Part 2)"},
                {"property": "Longitudinal Reversion", "requirement": "<= 5% max at 150°C", "test": "Clause 10.1 / IS 12235 (Part 6)"},
                {"property": "Short-Term Hydrostatic Test", "requirement": "1 hour at 27°C at 3.6x rated pressure without burst", "test": "Clause 10.5 / IS 12235 (Part 8)"},
                {"property": "Long-Term Hydrostatic Test", "requirement": "1000 hours at 60°C at 1.0x rated pressure", "test": "Clause 10.6 / IS 12235 (Part 8)"}
            ]
        },
        "testing_protocols": [
            {"test_name": "Impact Test at 0°C (Falling Weight)", "clause": "Clause 10.4", "reference_standard": "IS 12235 (Part 9)", "criteria": "True Relative Impact Rate (TIR) <= 10%"},
            {"test_name": "Methylene Chloride Resistance", "clause": "Clause 10.2", "reference_standard": "IS 12235 (Part 7)", "criteria": "Immersed for 30 mins at 15°C, no attack or flaking"}
        ]
    },
    "IS 1180": {
        "is_number": "IS 1180",
        "title": "Outdoor Type Oil Immersed Distribution Transformers up to 2500 kVA, 33 kV",
        "current_revision": "IS 1180 (Part 1):2014 (Third Revision)",
        "grades": ["11 kV Class", "22 kV Class", "33 kV Class", "Standard Energy Efficiency Levels 1, 2, 3"],
        "chemical_composition": {
            "clause": "Clause 6.6",
            "table_title": "Transformer Insulating Oil Specification",
            "columns": ["Property", "Requirement", "Test Standard"],
            "rows": [
                {"parameter": "Breakdown Voltage (BDV)", "requirement": "Min 30 kV (rms) in new oil", "test": "IS 6792"},
                {"parameter": "Dielectric Dissipation Factor (Tan Delta)", "requirement": "Max 0.005 at 90°C", "test": "IS 6262"},
                {"parameter": "Water Content", "requirement": "Max 30 ppm", "test": "IS 13567"}
            ]
        },
        "mechanical_properties": {
            "clause": "Clause 7.1, Table 3 to 6",
            "table_title": "Maximum Allowable Losses for 11 kV / 433V Transformers (Watts)",
            "columns": ["Rating (kVA)", "Max Losses at 50% Load (Level 2)", "Max Losses at 100% Load (Level 2)"],
            "rows": [
                {"rating": "16 kVA", "l50": "80 W", "l100": "435 W"},
                {"rating": "25 kVA", "l50": "100 W", "l100": "685 W"},
                {"rating": "63 kVA", "l50": "190 W", "l100": "1235 W"},
                {"rating": "100 kVA", "l50": "260 W", "l100": "1660 W"},
                {"rating": "250 kVA", "l50": "575 W", "l100": "3150 W"}
            ]
        },
        "testing_protocols": [
            {"test_name": "Lightning Impulse Withstand Test", "clause": "Clause 21.3", "reference_standard": "IS 2026 (Part 3)", "criteria": "75 kV peak for 11 kV system"},
            {"test_name": "Short Circuit Withstand Test", "clause": "Clause 21.4", "reference_standard": "IS 2026 (Part 5)", "criteria": "Thermal and dynamic ability to withstand external short circuit"},
            {"test_name": "Temperature Rise Test", "clause": "Clause 21.2", "reference_standard": "IS 2026 (Part 2)", "criteria": "Top oil temp rise <= 40°C, Winding temp rise <= 45°C"}
        ]
    },
    "IS 2925": {
        "is_number": "IS 2925",
        "title": "Industrial Safety Helmets - Specification",
        "current_revision": "IS 2925:1984 (Second Revision, Reaffirmed 2020)",
        "grades": ["Class A (General Industrial)", "Class B (Electrical Resistance to 1.2 kV)", "Class C (Mining Heavy Duty)"],
        "chemical_composition": {
            "clause": "Clause 5.1",
            "table_title": "Shell Material Requirements",
            "columns": ["Component", "Allowed Materials", "Requirements"],
            "rows": [
                {"parameter": "Helmet Shell", "requirement": "High Density Polyethylene (HDPE), ABS, or Polycarbonate", "test": "Non-toxic, skin-compatible"},
                {"parameter": "Harness / Cradle", "requirement": "Polyester or Nylon webbing min 20mm width", "test": "Sweatband non-irritant"}
            ]
        },
        "mechanical_properties": {
            "clause": "Clause 6.1 to 6.4",
            "table_title": "Performance Test Criteria",
            "columns": ["Test Protocol", "Performance Requirement", "Testing Apparatus"],
            "rows": [
                {"test": "Shock Absorption", "requirement": "Transmitted force to headform shall NOT exceed 5.0 kN", "test": "5 kg striker dropped from 1 meter"},
                {"test": "Penetration Resistance", "requirement": "Striker shall NOT contact headform surface", "test": "3 kg conical pointed striker dropped from 1 meter"},
                {"test": "Flammability Resistance", "requirement": "Shall not continue to burn with flame after 5 seconds of burner removal", "test": "Bunsen flame 1000°C applied for 10 seconds"},
                {"test": "Electrical Resistance", "requirement": "Leakage current shall NOT exceed 3 mA at 1.2 kV (rms)", "test": "Submerged in 1% NaCl solution"}
            ]
        },
        "testing_protocols": [
            {"test_name": "Shock Absorption Drop Test", "clause": "Clause 6.1", "reference_standard": "IS 2925 App A", "criteria": "Max deceleration load < 5.0 kN"},
            {"test_name": "Water Absorption Test", "clause": "Clause 6.5", "reference_standard": "IS 2925 App E", "criteria": "Water absorbed <= 0.5% by weight after 24 hrs"}
        ]
    }
}


class ClauseService:
    """Provides granular, clause-level engineering criteria for Indian Standards."""

    def get_clause_details(self, standard_id_or_number: str) -> Optional[Dict[str, Any]]:
        clean_key = standard_id_or_number.replace("_", " ").strip().upper()
        # Find exact or prefix match
        for key, spec in CLAUSE_CATALOG.items():
            if key.upper() in clean_key or clean_key in key.upper():
                return spec

        # Fallback generic breakdown for standards without custom deep breakdown
        return None

    def get_all_supported_standards(self) -> List[str]:
        return list(CLAUSE_CATALOG.keys())


_clause_service_instance: Optional[ClauseService] = None

def get_clause_service() -> ClauseService:
    global _clause_service_instance
    if _clause_service_instance is None:
        _clause_service_instance = ClauseService()
    return _clause_service_instance
