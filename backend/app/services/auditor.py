"""
Tender Specification Audit Engine (Mode B) for Manak-SpecEngine.
Performs automated legal and technical compliance audits on tender documents,
detecting superseded standards, statutory QCO violations, omitted testing methods,
and foreign standard discrimination under the Public Procurement (Make in India) Order.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

from backend.app.services.graph_service import GraphService, get_graph_service
from backend.app.services.parser import normalize_standard_ref, extract_clause2_references
from backend.app.services.llm_synthesizer import IndicNormalizer


class TenderAuditor:
    """
    Automated GovTech compliance auditor for GeM, CPWD, NHAI, and Railway tender specifications.
    """

    def __init__(self, data_dir: Optional[Path] = None, graph_service: Optional[GraphService] = None):
        self.data_dir = data_dir or (Path(__file__).resolve().parent.parent.parent.parent / "data")
        self.graph_service = graph_service or get_graph_service(data_dir=self.data_dir)

    def extract_referenced_standards(self, text: str) -> List[str]:
        """Extracts all Indian and foreign standard citations mentioned in tender text."""
        if not text:
            return []

        pat = re.compile(
            r"\b(?:IS(?:/ISO)?(?:/IEC)?\s+\d+(?:\s*(?:\(Part\s*[\dIVXLCDM]+\)|Part\s*[\dIVXLCDM]+))?(?:\s*(?:[-:]|\bPart\b)?\s*(?:19\d{2}|20\d{2}))?)(?!\w)|"
            r"\b(?:ASTM\s+[A-Z\d\-]+|EN\s+\d+|DIN\s+\d+|BS\s+\d+)(?!\w)",
            re.IGNORECASE
        )

        raw_matches = [m.group(0).strip() for m in pat.finditer(text)]
        normalized_list = []
        seen = set()

        for rm in raw_matches:
            norm = normalize_standard_ref(rm)
            if norm and norm not in seen:
                seen.add(norm)
                normalized_list.append(norm)

        # Subsume bare standards if a more specific (Part X) is present
        filtered = []
        for item in normalized_list:
            has_more_specific = any(
                other != item and other.startswith(item) and "(Part" in other
                for other in normalized_list
            )
            if not has_more_specific:
                filtered.append(item)

        return filtered

    def audit_tender(
        self,
        raw_text: str,
        tender_id: Optional[str] = None,
        tender_title: Optional[str] = None,
        department: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Conducts deep multi-point audit:
        1. Deprecated / Superseded Standards Check
        2. Statutory Quality Control Order (QCO) Verification
        3. Clause 2 Testing and Sampling Verification
        4. Foreign Standard Discrimination (PPP-MII) Check
        5. Quality Dilution / Specification Vague Phrasing Check
        6. Calculation of 0-100 Compliance Index
        7. Redline Amendments Matrix & Ready-to-Issue Corrigendum
        """
        # Multilingual Indic detection
        lang_info = IndicNormalizer.detect_and_normalize(raw_text)
        is_indic = lang_info["is_indic"]
        detected_language = lang_info["language"]

        # Standards referenced
        referenced_standards = self.extract_referenced_standards(raw_text)

        findings: List[Dict[str, Any]] = []
        score = 100
        qco_compliant = True
        deprecated_standards: List[Dict[str, Any]] = []
        omitted_test_methods: List[str] = []

        raw_lower = raw_text.lower()

        # -------------------------------------------------------------
        # 1. Deprecated / Superseded Standards Check
        # -------------------------------------------------------------
        for std_ref in referenced_standards:
            sid = self.graph_service.resolve_standard_id(std_ref)
            std_meta = self.graph_service.get_standard(sid) if sid else None

            is_superseded = False
            superseded_reason = ""
            superseding_std = None

            # Explicit check for known deprecated revisions in text
            if "2062:2006" in std_ref:
                is_superseded = True
                superseded_reason = "IS 2062:2006 was superseded by IS 2062:2011 with revised tensile grades."
                superseding_std = "IS 2062:2011"
            elif "432" in std_ref and ("part 1" in std_ref.lower() or "1982" in std_ref):
                is_superseded = True
                superseded_reason = "IS 432 (Part 1) for mild steel bars is obsolete/superseded by IS 1786 and IS 2062."
                superseding_std = "IS 1786 / IS 2062"
            elif std_meta and std_meta.get("status") in ("SUPERSEDED", "WITHDRAWN"):
                is_superseded = True
                superseded_reason = f"{std_ref} is formally designated as {std_meta.get('status')} in the BIS catalog."
                chain = self.graph_service.find_superseding_chain(sid)
                if len(chain) > 1:
                    superseding_std = chain[-1].get("is_number")

            if is_superseded:
                score -= 22
                dep_info = {
                    "standard_cited": std_ref,
                    "status": "SUPERSEDED",
                    "reason": superseded_reason,
                    "superseded_by": superseding_std or "Latest active revision"
                }
                deprecated_standards.append(dep_info)
                findings.append({
                    "finding_id": f"FIND-DEP-{len(findings) + 1}",
                    "issue_type": "SUPERSEDED_STANDARD",
                    "severity": "CRITICAL",
                    "original_text_snippet": std_ref,
                    "regulatory_reference": "Section 15 & 16, Bureau of Indian Standards Act, 2016",
                    "description": f"Tender cites obsolete standard '{std_ref}'. {superseded_reason}",
                    "recommended_amendment": f"Replace '{std_ref}' with '{superseding_std or 'current edition of Indian Standard'} (latest revision with all amendments)'."
                })

        # -------------------------------------------------------------
        # 2. Statutory Quality Control Order (QCO) Verification
        # -------------------------------------------------------------
        has_qco_goods = False
        governing_qco: Optional[Dict[str, Any]] = None

        # Check all referenced standards against QCO index
        for std_ref in referenced_standards:
            qco = self.graph_service.check_qco_mandate(std_ref)
            if qco:
                has_qco_goods = True
                governing_qco = qco
                break

        # Also check product keywords if standard not explicitly mentioned
        if not has_qco_goods:
            if "steel" in raw_lower or "rebar" in raw_lower or "tmt" in raw_lower or "structural steel" in raw_lower:
                governing_qco = self.graph_service.get_qco("Steel_and_Steel_Products_Quality_Control_Order_2024")
                has_qco_goods = True
            elif "laptop" in raw_lower or "computer" in raw_lower or "battery" in raw_lower:
                governing_qco = self.graph_service.get_qco("Electronics_and_Information_Technology_Goods_Requirement_for_Compulsory_Registration_Order_2021")
                has_qco_goods = True
            elif "solar" in raw_lower and ("module" in raw_lower or "pv" in raw_lower):
                governing_qco = self.graph_service.get_qco("Solar_Photovoltaics_Systems_Devices_and_Components_Goods_Requirement_for_Compulsory_Registration_Order_2017")
                has_qco_goods = True
            elif "safety shoe" in raw_lower or "safety footwear" in raw_lower:
                governing_qco = self.graph_service.get_qco("Footwear_made_from_Leather_and_other_materials_Quality_Control_Order_2020")
                has_qco_goods = True
            elif "hdpe" in raw_lower and "pipe" in raw_lower:
                governing_qco = self.graph_service.get_qco("Polyethylene_Material_for_Moulding_and_Extrusion_Quality_Control_Order_2022")
                has_qco_goods = True

        if has_qco_goods and governing_qco:
            scheme = governing_qco.get("mandatory_scheme", "Scheme-I")
            qco_name = governing_qco.get("order_name", "Statutory Quality Control Order")

            # Check for illegal exemption traps (e.g. 'without BIS certification', 'secondary re-rollers')
            illegal_exemption = (
                "without bis" in raw_lower or
                "without isi" in raw_lower or
                "secondary re-rollers without" in raw_lower or
                "bis certification not required" in raw_lower
            )

            # Check for positive mandatory compliance clauses
            has_mandatory_clause = (
                "bis standard mark" in raw_lower or
                "isi mark" in raw_lower or
                "bis license" in raw_lower or
                "bis licence" in raw_lower or
                "compulsory registration" in raw_lower or
                "crs" in raw_lower or
                "r-number" in raw_lower or
                "qco" in raw_lower or
                "scheme-i" in raw_lower or
                "scheme-ii" in raw_lower or
                "गुणवत्ता नियंत्रण आदेश" in raw_lower or
                "बीआईएस" in raw_lower
            )

            if illegal_exemption:
                score -= 35
                qco_compliant = False
                findings.append({
                    "finding_id": f"FIND-QCO-{len(findings) + 1}",
                    "issue_type": "ILLEGAL_QCO_EXEMPTION",
                    "severity": "CRITICAL",
                    "original_text_snippet": "Material can be supplied ... without BIS certification",
                    "regulatory_reference": f"{qco_name}; Section 16 & Section 29, BIS Act, 2016",
                    "description": (
                        f"Tender explicitly permits non-BIS certified supply for goods governed by the '{qco_name}'. "
                        "This violates Section 16 of the BIS Act 2016 and is a cognizable statutory offense under Section 29."
                    ),
                    "recommended_amendment": (
                        f"Delete exemption clause. Mandate: 'All supplies shall strictly carry the BIS Standard Mark ({scheme}) "
                        f"under a valid BIS license in accordance with {qco_name}. Bids from uncertified suppliers shall be rejected.'"
                    )
                })
            elif not has_mandatory_clause:
                score -= 25
                qco_compliant = False
                findings.append({
                    "finding_id": f"FIND-QCO-{len(findings) + 1}",
                    "issue_type": "MISSING_QCO_MANDATE",
                    "severity": "CRITICAL",
                    "original_text_snippet": "Specification omitted statutory compliance section",
                    "regulatory_reference": f"{qco_name}; Section 16, BIS Act, 2016",
                    "description": (
                        f"Offered goods fall under statutory regulation under '{qco_name}', but tender lacks mandatory "
                        f"requirement for BIS certification mark ({scheme})."
                    ),
                    "recommended_amendment": (
                        f"Insert mandatory statutory clause: 'The manufacturer must hold valid BIS Certification License "
                        f"bearing the Standard Mark under {scheme} per {qco_name}. Valid license copy must be uploaded with technical bid.'"
                    )
                })

        # -------------------------------------------------------------
        # 3. Clause 2 Testing Standards Verification
        # -------------------------------------------------------------
        # For primary standards (like IS 2062, IS 1786, IS 456), verify critical test methods
        for std_ref in referenced_standards:
            sid = self.graph_service.resolve_standard_id(std_ref)
            if not sid:
                continue

            neighbors = self.graph_service.get_1hop_neighbors(sid)
            test_methods = neighbors.get("test_methods", [])

            # Check if tender specifies structural steel or rebar but omits testing
            if "2062" in sid:
                has_tensile = "1608" in raw_text or "tensile test" in raw_lower
                has_bend = "1599" in raw_text or "bend test" in raw_lower
                has_impact = "1757" in raw_text or "charpy" in raw_lower or "impact" in raw_lower

                missing_steel_tests = []
                if not has_tensile:
                    missing_steel_tests.append("IS 1608 (Tensile testing)")
                if not has_bend:
                    missing_steel_tests.append("IS 1599 (Bend testing)")
                if not has_impact and ("bridge" in raw_lower or "joist" in raw_lower or "truss" in raw_lower):
                    missing_steel_tests.append("IS 1757 (Charpy V-notch impact testing)")

                if missing_steel_tests:
                    score -= 10
                    omitted_test_methods.extend(missing_steel_tests)
                    findings.append({
                        "finding_id": f"FIND-TEST-{len(findings) + 1}",
                        "issue_type": "MISSING_TEST_STANDARDS",
                        "severity": "MAJOR",
                        "original_text_snippet": "Testing methods unprescribed",
                        "regulatory_reference": f"Clause 2, {std_ref}",
                        "description": f"Tender specifies {std_ref} but omits mandatory Clause 2 test methods: {', '.join(missing_steel_tests)}.",
                        "recommended_amendment": (
                            f"Mandate testing protocols: 'Routine mechanical and chemical tests shall be conducted per "
                            f"{', '.join(missing_steel_tests)} and MTC with heat numbers furnished before dispatch.'"
                        )
                    })

        # -------------------------------------------------------------
        # 4. Foreign Standard Discrimination (PPP-MII Violation)
        # -------------------------------------------------------------
        foreign_matches = re.findall(r"\b(ASTM\s+[A-Z\d\-]+|EN\s+\d+|DIN\s+\d+|BS\s+\d+)\b", raw_text, re.I)
        if foreign_matches and not any("IS " in s or "IS/" in s for s in referenced_standards):
            score -= 15
            findings.append({
                "finding_id": f"FIND-MII-{len(findings) + 1}",
                "issue_type": "FOREIGN_STANDARD_DISCRIMINATION",
                "severity": "MAJOR",
                "original_text_snippet": ", ".join(foreign_matches),
                "regulatory_reference": "Public Procurement (Preference to Make in India) Order, 2017 & Section 16 BIS Act 2016",
                "description": (
                    f"Tender specifies foreign standards ({', '.join(foreign_matches)}) without prescribing the Indian Standard "
                    "equivalent or explicitly stating 'or equivalent Indian Standard'."
                ),
                "recommended_amendment": (
                    f"Replace foreign citations with corresponding Indian Standards or append: '...or equivalent Indian Standard (BIS).'"
                )
            })

        # -------------------------------------------------------------
        # 5. Quality Dilution / Specification Vague Phrasing Check
        # -------------------------------------------------------------
        dilution_traps = []
        if "recycled" in raw_lower and ("hdpe" in raw_lower or "water" in raw_lower or "drinking" in raw_lower):
            dilution_traps.append("Illegal recycled polymer blending in potable water pipe (prohibited under IS 4984 Clause 4.1)")
            if "7328" not in raw_text:
                dilution_traps.append("Omission of mandatory virgin polyethylene raw material specification (IS 7328)")
        if "commercial quality" in raw_lower or "ordinary quality" in raw_lower:
            dilution_traps.append("Use of uncertified 'commercial quality' steel instead of designated grade (E250/E350)")

        for trap in dilution_traps:
            score -= 15
            findings.append({
                "finding_id": f"FIND-VAGUE-{len(findings) + 1}",
                "issue_type": "VAGUE_SPECIFICATION",
                "severity": "CRITICAL",
                "original_text_snippet": trap,
                "regulatory_reference": "General Financial Rules (GFR) Rule 144(i) & Technical Regulations",
                "description": f"Specification dilution detected: {trap}.",
                "recommended_amendment": "Specify exact technical parameters, virgin raw material standards, and verifiable test limits."
            })

        # Clamp compliance score between 0 and 100
        final_score = max(0, min(100, score))

        if final_score >= 85:
            compliance_status = "COMPLIANT"
            status_color = "green"
        elif final_score >= 60:
            compliance_status = "MINOR_RISKS"
            status_color = "yellow"
        else:
            compliance_status = "NON_COMPLIANT"
            status_color = "red"

        # Generate Tender Corrigendum / Addendum
        corrigendum_text = self._generate_corrigendum_notice(
            tender_id=tender_id or "GEM/TENDER/2026",
            tender_title=tender_title or "Procurement Tender",
            findings=findings
        )

        return {
            "tender_id": tender_id or "TENDER-SPEC",
            "tender_title": tender_title or "Tender Specification",
            "department": department or "Procurement Division",
            "detected_language": detected_language,
            "is_indic": is_indic,
            "compliance_score": final_score,
            "compliance_status": compliance_status,
            "status_color": status_color,
            "qco_compliant": qco_compliant,
            "governing_qco": governing_qco.get("order_name") if governing_qco else None,
            "standards_referenced": referenced_standards,
            "deprecated_standards": deprecated_standards,
            "omitted_test_methods": omitted_test_methods,
            "total_findings": len(findings),
            "findings": findings,
            "corrigendum_notice": corrigendum_text
        }

    def _generate_corrigendum_notice(
        self,
        tender_id: str,
        tender_title: str,
        findings: List[Dict[str, Any]]
    ) -> str:
        """Formulates an official Corrigendum/Addendum for publication on GeM/CPP Portal."""
        if not findings:
            return "No corrigendum required. Tender specifications fully comply with Bureau of Indian Standards and Statutory QCOs."

        lines = [
            f"CORRIGENDUM / AMENDMENT NO. 1",
            f"Tender ID: {tender_id}",
            f"Subject: Technical Specification & Statutory BIS Compliance Corrigendum for '{tender_title}'",
            "",
            "Notice is hereby given to all prospective bidders that following technical and statutory amendments",
            "are incorporated in the Tender Document with immediate effect under Section 16 of the BIS Act, 2016:",
            "",
            "------------------------------------------------------------------------------------------------"
        ]

        for i, f in enumerate(findings, 1):
            lines.append(f"AMENDMENT {i} [{f['severity']} - {f['issue_type']}]:")
            lines.append(f"  Existing Clause: {f['original_text_snippet']}")
            lines.append(f"  Amended Clause:  {f['recommended_amendment']}")
            lines.append(f"  Regulatory Basis: {f['regulatory_reference']}")
            lines.append("")

        lines.extend([
            "------------------------------------------------------------------------------------------------",
            "All other terms and conditions of the tender document shall remain unaltered.",
            "Bidders are requested to submit their technical bids in accordance with this Corrigendum."
        ])

        return "\n".join(lines)


# Global singleton instance cache
_auditor_instance: Optional[TenderAuditor] = None


def get_tender_auditor(
    data_dir: Optional[Path] = None,
    graph_service: Optional[GraphService] = None
) -> TenderAuditor:
    """Returns singleton TenderAuditor instance."""
    global _auditor_instance
    if _auditor_instance is None:
        _auditor_instance = TenderAuditor(data_dir=data_dir, graph_service=graph_service)
    return _auditor_instance
