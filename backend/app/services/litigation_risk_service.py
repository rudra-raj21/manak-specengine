"""
Tender Litigation & Pre-Bid Risk Analyzer for Manak-SpecEngine.
Assesses tender specifications against frequent pre-bid objections, arbitration disputes,
and statutory High Court challenges (e.g. under Article 226, GFR 2017 Rule 144(i),
Competition Act 2002, and BIS Act 2016 Section 29).
"""

import re
from typing import Dict, Any, List, Optional


class LitigationRiskService:
    """
    Evaluates tender clauses for litigation-prone pitfalls and computes
    a Legal Defensibility Index (0–100).
    """

    @classmethod
    def analyze_tender_risk(cls, tender_text: str) -> Dict[str, Any]:
        """
        Analyzes raw tender text or generated clauses for legal and pre-bid risk factors.
        """
        t_lower = tender_text.lower()
        findings: List[Dict[str, Any]] = []
        base_score = 100

        # Pitfall 1: Restrictive 'Primary Producers Only / Blast Furnace Route'
        if re.search(r"\b(blast furnace|primary producers?|integrated steel plant|integrated producers?)\b", t_lower):
            if re.search(r"\b(only primary|primary.*only|only.*blast furnace|blast furnace.*only|without technical justification|all bidders must be primary|only sail|tata/jsw)\b", t_lower):
                base_score -= 25
                findings.append({
                    "risk_category": "COMPETITION_RESTRICTION",
                    "severity": "HIGH",
                    "title": "Anti-Competitive Restriction to Integrated/Primary Producers",
                    "statutory_violation": "Competition Act, 2002 & Ministry of Finance Manual for Procurement of Goods (Rule 144)",
                    "pre_bid_risk": "High probability of bidder objection or stay petition. Restricting to blast furnace route without explicit technical justification for high fatigue/ductility is routinely struck down.",
                    "recommended_remedy": "Allow secondary/induction furnace re-rollers provided they possess valid BIS CM/L license, produce virgin/refined steel conforming to IS 1786:2008 with S+P ≤ 0.075%, and submit NABL test certificates."
                })

        # Pitfall 2: Foreign Standards cited without 'or equivalent Indian Standard'
        foreign_match = re.search(r"\b(astm\s+[a-z]?\s*\d+|din\s+\d+|en\s+\d+|bs\s+\d+|iso\s+\d+)\b", t_lower)
        if foreign_match and not re.search(r"\b(or equivalent is|or equivalent indian standard|conforming to is)\b", t_lower):
            base_score -= 20
            findings.append({
                "risk_category": "PUBLIC_PROCUREMENT_MII_VIOLATION",
                "severity": "HIGH",
                "title": f"Foreign Standard '{foreign_match.group(1).upper()}' Specified Without Indian Standard Fallback",
                "statutory_violation": "Public Procurement (Preference to Make in India) Order, 2017 & GFR Rule 144(i)",
                "pre_bid_risk": "Non-Indian standard discrimination exposes the procuring authority to MSME grievance redressal and audit objections by CAG.",
                "recommended_remedy": f"Amend clause to: '{foreign_match.group(1).upper()} or equivalent Indian Standard (conforming to relevant Bureau of Indian Standards specification)'."
            })

        # Pitfall 3: Obsolete Standard or Year Omission
        if re.search(r"\bis\s+2062\s*:\s*(?:1999|2006)\b", t_lower):
            base_score -= 20
            findings.append({
                "risk_category": "OBSOLETE_SPECIFICATION",
                "severity": "CRITICAL",
                "title": "Superseded Standard IS 2062:2006 / 1999 Referenced",
                "statutory_violation": "BIS Quality Control Order, 2024",
                "pre_bid_risk": "Suppliers cannot legally obtain BIS certification for withdrawn editions.",
                "recommended_remedy": "Replace with current active revision: 'IS 2062:2011 (Seventh Revision)'."
            })

        # Pitfall 4: Missing Mandatory BIS License condition for QCO materials
        is_qco_material = any(m in t_lower for m in ["tmt", "rebar", "structural steel", "hdpe pipe", "distribution transformer", "safety helmet"])
        has_cml_requirement = bool(re.search(r"\b(isi mark|bis certification mark|cm/l|license)\b", t_lower))
        if is_qco_material and not has_cml_requirement:
            base_score -= 25
            findings.append({
                "risk_category": "CRIMINAL_STATUTORY_NON_COMPLIANCE",
                "severity": "CRITICAL",
                "title": "Omission of Mandatory BIS Standard Mark (ISI Mark) Condition",
                "statutory_violation": "Section 16 & Section 29, Bureau of Indian Standards Act, 2016",
                "pre_bid_risk": "Tender allows procurement of non-certified goods. Under Section 29, officers accepting uncertified QCO products risk penal liability.",
                "recommended_remedy": "Incorporate statutory mandate: 'All offered materials must bear the mandatory BIS Standard Mark (ISI Mark) with an operative BIS Certification Marks License (CM/L) number. Supply of non-certified material shall result in immediate disqualification and reporting under Section 29, BIS Act 2016.'"
            })

        defensibility_score = max(10, min(100, base_score))
        
        if defensibility_score >= 90:
            rating = "WATERTIGHT (LOW LITIGATION RISK)"
            badge_color = "emerald"
        elif defensibility_score >= 70:
            rating = "MODERATE RISK (AMENDMENT RECOMMENDED)"
            badge_color = "amber"
        else:
            rating = "HIGH RISK (VULNERABLE TO PRE-BID STAY / WRIT)"
            badge_color = "rose"

        return {
            "defensibility_score": defensibility_score,
            "risk_rating": rating,
            "badge_color": badge_color,
            "total_risk_factors": len(findings),
            "findings": findings,
            "statutory_safe_harbor_included": bool(defensibility_score >= 90)
        }
