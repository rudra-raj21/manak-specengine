"""
Multilingual Indic Normalizer and Gemini LLM Synthesizer for Manak-SpecEngine.
Translates regional Indian procurement terms and synthesizes legally binding,
grounded GeM / CPWD / Railways tender specification clauses and compliance statements.
"""

import os
import re
from typing import Dict, List, Any, Optional

try:
    from google import genai
    from google.genai import types
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False


# Domain translation dictionary for Indian Government procurement vernacular
INDIC_PROCUREMENT_VOCABULARY = {
    # Hindi / Devanagari (TMT Rebars, Structural Steel, Cement, Pipes, Cables, Helmets, Solar)
    "सरिया": "high strength deformed steel bars tmt rebar fe 500d IS 1786",
    "टीएमटी सरिया": "high strength deformed steel bars tmt rebar fe 500d IS 1786",
    "रीबार": "tmt steel rebar fe 500d IS 1786",
    "संरचनात्मक इस्पात": "hot rolled structural steel plates sections beams IS 2062",
    "स्टील प्लेट": "structural steel plates IS 2062",
    "गार्डर": "steel girder structural sections IS 2062 IS 808",
    "सीमेंट": "ordinary portland cement opc 43 53 grade IS 269 IS 8112 IS 12269",
    "ओपीसी": "ordinary portland cement opc IS 269",
    "पीने का पानी पाइप": "high density polyethylene hdpe pipes for potable water IS 4984",
    "एचडीपीई पाइप": "hdpe pipes potable water supply IS 4984",
    "बिजली का तार": "pvc insulated copper wire cable IS 694",
    "केबल": "pvc xlpe insulated electric power cables IS 694 IS 1554",
    "सुरक्षा हेलमेट": "industrial safety helmets head protection IS 2925",
    "हेलमेट": "industrial safety helmets IS 2925",
    "सुरक्षा जूते": "industrial safety footwear steel toe boots IS 15298",
    "सौर पैनल": "crystalline silicon terrestrial photovoltaic solar pv modules IS 14286",
    "सोलर प्लेट": "solar photovoltaic pv modules IS 14286",
    "लैपटॉप": "information technology equipment safety laptop adapter IS 13252",
    "कंप्यूटर": "information technology equipment safety IS 13252",
    "अग्निशामक": "portable fire extinguishers dry powder co2 IS 15683",
    "आग बुझाने का यंत्र": "portable fire extinguishers IS 15683",
    "प्लाईवुड": "plywood for general purposes marine plywood IS 303 IS 710",
    "फ्लश डोर": "solid core wooden flush door shutters IS 2202",
    "खिलौने": "safety aspects mechanical physical properties of toys IS 9873",
    
    # Marathi / Gujarati / Bengali transliterations
    "सळई": "tmt steel rebar fe 500d IS 1786",
    "सिमेंट": "portland cement IS 269",
    "લોખંડ": "structural steel IS 2062",
    "রড": "tmt rebar fe 500d IS 1786"
}


class IndicNormalizer:
    """
    Normalizes Indian regional procurement text (Hindi, Marathi, Gujarati, etc.)
    into technical Indian Standards search queries.
    """

    @staticmethod
    def detect_and_normalize(text: str) -> Dict[str, Any]:
        if not text:
            return {"raw_text": "", "normalized_query": "", "language": "en", "is_indic": False}

        raw_clean = text.strip()
        # Detect Devanagari Unicode block (\u0900 - \u097F)
        has_devanagari = bool(re.search(r"[\u0900-\u097F]", raw_clean))
        has_bengali = bool(re.search(r"[\u0980-\u09FF]", raw_clean))
        has_gujarati = bool(re.search(r"[\u0A80-\u0AFF]", raw_clean))
        has_tamil = bool(re.search(r"[\u0B80-\u0BFF]", raw_clean))
        has_telugu = bool(re.search(r"[\u0C00-\u0C7F]", raw_clean))

        is_indic = has_devanagari or has_bengali or has_gujarati or has_tamil or has_telugu

        language = "en"
        if has_devanagari:
            language = "hi"
        elif has_bengali:
            language = "bn"
        elif has_gujarati:
            language = "gu"
        elif has_tamil:
            language = "ta"
        elif has_telugu:
            language = "te"

        normalized_terms = []
        if is_indic:
            for term, transliteration in INDIC_PROCUREMENT_VOCABULARY.items():
                if term in raw_clean:
                    normalized_terms.append(transliteration)

        if normalized_terms:
            normalized_query = " ".join(normalized_terms)
        else:
            normalized_query = raw_clean

        return {
            "raw_text": raw_clean,
            "normalized_query": normalized_query,
            "language": language,
            "is_indic": is_indic
        }


class LLMSynthesizer:
    """
    Synthesizes compliant GovTech procurement specifications and tender clauses
    grounded strictly in BIS national standards and statutory Quality Control Orders.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self.client = None

        if HAS_GOOGLE_GENAI and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini Client: {e}")
                self.client = None

    def synthesize_tender_clause(
        self,
        query: str,
        primary_standard: Dict[str, Any],
        normative_references: List[str],
        test_standards: List[str],
        qco_mandate: Optional[Dict[str, Any]] = None,
        tender_type: str = "GeM"  # 'GeM', 'CPWD', 'Railways', 'State PWD'
    ) -> Dict[str, Any]:
        """
        Synthesizes a legally defensible, complete 4-part tender clause.
        Uses Gemini LLM if API key is present; otherwise produces a verified deterministic clause.
        """
        is_num = primary_standard.get("is_number", "IS 2062")
        title = primary_standard.get("title", "")
        year = primary_standard.get("year", "Latest Revision")
        dept = primary_standard.get("department", "Engineering")

        test_stds_str = (
            ", ".join(test_standards[:4])
            if test_standards
            else f"Refer to testing and sampling clauses of {is_num} (standard-specific testing methods)"
        )
        norm_stds_str = (
            ", ".join(normative_references[:5])
            if normative_references
            else f"Refer to normative reference clause of {is_num}"
        )

        has_qco = qco_mandate is not None
        is_qco_active = bool(qco_mandate and qco_mandate.get("is_mandatory", True))
        qco_name = qco_mandate.get("order_name", "Statutory Quality Control Order") if has_qco else None
        qco_ministry = qco_mandate.get("ministry", qco_mandate.get("ministry_id", "Government of India")) if has_qco else None
        qco_scheme = qco_mandate.get("mandatory_scheme", "Scheme-I") if has_qco else None
        qco_date = qco_mandate.get("effective_date", "Currently in Force") if has_qco else None
        qco_temp_status = qco_mandate.get("temporal_status", "MANDATORY_IN_FORCE") if has_qco else None

        # Build prompt for Gemini or offline generator
        prompt = self._build_synthesis_prompt(
            query=query,
            is_num=is_num,
            title=title,
            year=year,
            dept=dept,
            test_stds_str=test_stds_str,
            has_qco=has_qco,
            qco_name=qco_name,
            qco_ministry=qco_ministry,
            qco_scheme=qco_scheme,
            tender_type=tender_type
        )

        llm_response = None
        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                if response and response.text:
                    llm_response = response.text.strip()
            except Exception as e:
                print(f"Warning: Gemini API call failed: {e}. Falling back to deterministic synthesizer.")
                llm_response = None

        # Format final structured sections
        if not llm_response:
            tender_clause_text = self._generate_deterministic_clause(
                is_num=is_num,
                title=title,
                year=year,
                test_stds=test_stds_str,
                has_qco=has_qco,
                is_qco_active=is_qco_active,
                qco_name=qco_name,
                qco_ministry=qco_ministry,
                qco_scheme=qco_scheme,
                qco_date=qco_date,
                qco_temp_status=qco_temp_status,
                tender_type=tender_type
            )
        else:
            tender_clause_text = llm_response

        compliance_summary = {
            "primary_standard": {
                "is_number": is_num,
                "title": title,
                "year": year,
                "status": primary_standard.get("status", "ACTIVE")
            },
            "normative_references": normative_references[:6],
            "mandatory_testing_standards": test_standards[:4],
            "statutory_qco_compliance": {
                "is_mandatory": has_qco,
                "qco_order_name": qco_name,
                "ministry": qco_ministry,
                "mandatory_scheme": qco_scheme,
                "effective_date": qco_date,
                "penal_provision": "Conformity to Indian Standard and BIS Mark is mandatory under Section 16 & Section 29 of the BIS Act, 2016." if has_qco else None
            },
            "inspection_protocol": {
                "type": "Pre-dispatch & On-site Verification",
                "testing_agency": "NABL Accredited Laboratory / BIS Recognized Lab / RITES Inspection",
                "acceptance_criteria": f"Physical and chemical test certificates complying strictly with {is_num}."
            },
            "tender_clause": tender_clause_text
        }

        return compliance_summary

    def _build_synthesis_prompt(
        self,
        query: str,
        is_num: str,
        title: str,
        year: Any,
        dept: str,
        test_stds_str: str,
        has_qco: bool,
        qco_name: Optional[str],
        qco_ministry: Optional[str],
        qco_scheme: Optional[str],
        tender_type: str
    ) -> str:
        qco_section = f"Governing QCO: {qco_name} ({qco_ministry}) under {qco_scheme}." if has_qco else "No mandatory QCO currently enforced."
        return f"""You are a Lead GovTech Legal & Technical Procurement Advisor for Indian Public Procurement ({tender_type}).
Synthesize an authoritative, ready-to-paste tender clause for procurement officers based strictly on the following verified facts:

Input Procurement Requirement: {query}
Recommended Indian Standard: {is_num}:{year} - {title}
Responsible Department: {dept}
Mandatory Testing Standards: {test_stds_str}
Regulatory QCO Status: {qco_section}

Format the output cleanly in four numbered sections:
1. Technical Scope & Designation
2. Mandatory Quality & Testing Protocol
3. Statutory QCO & Regulatory Compliance
4. Special Tender Contract Clause (ready to copy into GeM STC / NIT)"""

    def _generate_deterministic_clause(
        self,
        is_num: str,
        title: str,
        year: Any,
        test_stds: str,
        has_qco: bool,
        is_qco_active: bool,
        qco_name: Optional[str],
        qco_ministry: Optional[str],
        qco_scheme: Optional[str],
        qco_date: Optional[str],
        qco_temp_status: Optional[str],
        tender_type: str
    ) -> str:
        if has_qco and is_qco_active:
            qco_legal_text = (
                f"The offered product is subject to mandatory statutory quality control under '{qco_name}' issued by {qco_ministry} "
                f"(enforcement in force since {qco_date}). Bidders MUST hold a valid BIS certification license under {qco_scheme} "
                f"bearing the standard mark (ISI Mark/CRS Registration). Any supply without valid BIS marking constitutes a cognizable "
                f"offense punishable under Section 29 of the Bureau of Indian Standards Act, 2016."
            )
        elif has_qco and qco_temp_status == "PENDING_FUTURE_DATE":
            qco_legal_text = (
                f"A statutory Quality Control Order ('{qco_name}') has been published by {qco_ministry}, with mandatory enforcement "
                f"scheduled to take effect on {qco_date}. Prior to that date, voluntary conformity with {is_num}:{year} is recommended."
            )
        elif has_qco:
            qco_legal_text = (
                f"A statutory QCO reference ('{qco_name}') exists in the regulatory catalog, but effective date must be confirmed "
                f"against the Official Gazette prior to enforcing mandatory licensing conditions."
            )
        else:
            qco_legal_text = f"Materials shall conform strictly to {is_num}:{year} with valid factory test certificates."

        return (
            f"### SPECIAL TERMS & CONDITIONS (STC) - {tender_type.upper()} PROCUREMENT CLAUSE\n\n"
            f"**1. Material Specification & Applicable Standard:**\n"
            f"All materials and goods supplied under this tender contract shall strictly comply with Indian Standard "
            f"**{is_num}:{year} ({title})** along with all published amendments up to the date of tender submission.\n\n"
            f"**2. Mandatory Testing & Quality Verification:**\n"
            f"Sampling, physical verification, and mechanical/chemical testing shall be carried out in strict accordance with "
            f"**{test_stds}**. Manufacturer's Test Certificate (MTC) covering heat-wise/lot-wise chemical composition and mechanical "
            f"properties shall accompany every consignment.\n\n"
            f"**3. Statutory Compliance & Quality Control Order (QCO):**\n"
            f"{qco_legal_text}\n\n"
            f"**4. Pre-Dispatch Inspection & Rejection Terms:**\n"
            f"The procuring authority reserves the right to depute a third-party inspection agency (e.g. RITES, CEIL, or NABL Accredited Lab) "
            f"prior to dispatch. Consignments failing to demonstrate full compliance with {is_num}:{year} shall be rejected at vendor's cost."
        )


# Global singleton instance cache
_synthesizer_instance: Optional[LLMSynthesizer] = None


def get_llm_synthesizer() -> LLMSynthesizer:
    """Returns singleton LLMSynthesizer instance."""
    global _synthesizer_instance
    if _synthesizer_instance is None:
        _synthesizer_instance = LLMSynthesizer()
    return _synthesizer_instance
