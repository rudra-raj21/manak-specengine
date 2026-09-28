"""
Procurement Document Parser & Official Corrigendum Generator for Manak-SpecEngine.
Extracts tender specification text from multi-format files (.pdf, .txt, .docx)
and synthesizes legally binding Government of India / GeM Corrigendum Notices.
"""

import io
from typing import Dict, Any, List, Optional
from datetime import datetime


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extracts raw text from uploaded tender files (.txt, .pdf)."""
    if not file_bytes:
        return ""

    ext = filename.split(".")[-1].lower() if "." in filename else "txt"

    if ext == "pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
            extracted = "\n".join(text_parts).strip()
            if extracted:
                return extracted
        except Exception as e:
            print(f"pypdf extraction failed for {filename}: {e}")

    # Fallback to UTF-8 text decoding with Latin-1 fallback
    try:
        return file_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="ignore").strip()


def generate_official_corrigendum_document(
    tender_id: str,
    tender_title: str,
    department: str,
    findings: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Synthesizes a formally structured Corrigendum Notice compliant with
    GeM GTC (General Terms and Conditions), CPWD Works Manual, and BIS Act 2016.
    """
    now = datetime.now()
    corrigendum_no = f"CORRIGENDUM/BIS/{now.year}/{now.strftime('%m%d%H%M')}"
    issuing_date = now.strftime("%d-%B-%Y")

    supersessions = findings.get("superseded_standards_found", [])
    missing_qcos = findings.get("missing_statutory_qcos", [])
    foreign_disc = findings.get("foreign_standards_detected", [])
    missing_tests = findings.get("omitted_testing_protocols", [])

    amendment_rows = []
    item_idx = 1

    # 1. Superseded standards amendments
    for s in supersessions:
        amendment_rows.append({
            "sl_no": item_idx,
            "clause_ref": "Technical Specifications / Quality Standards",
            "existing_provision": f"Reference to '{s.get('cited_text', s.get('superseded_standard'))}'",
            "amended_provision": f"Substituted by '{s.get('active_standard')}' ({s.get('title', 'Latest Gazette Revision')})",
            "statutory_basis": "Mandatory adherence to currently active Indian Standard in terms of Rule 144(i) of GFR, 2017."
        })
        item_idx += 1

    # 2. Missing QCO amendments
    for q in missing_qcos:
        amendment_rows.append({
            "sl_no": item_idx,
            "clause_ref": "Statutory Eligibility / Technical Compliance",
            "existing_provision": "Standard technical specifications without QCO certification mandate.",
            "amended_provision": f"Mandatory compliance with '{q.get('order_name')}' under {q.get('scheme', 'Scheme-I')}. Bidder MUST submit valid BIS CM/L License Number.",
            "statutory_basis": "Section 16 & Section 29 of Bureau of Indian Standards Act, 2016. Supply without ISI mark constitutes a cognizable offense."
        })
        item_idx += 1

    # 3. Foreign standard discrimination amendments
    for f in foreign_disc:
        amendment_rows.append({
            "sl_no": item_idx,
            "clause_ref": "Material Specification / Equivalency",
            "existing_provision": f"Exclusively requires foreign standard '{f.get('foreign_standard')}' without Indian Standard option.",
            "amended_provision": f"Amended to require Indian Standard '{f.get('indian_equivalent')}' ({f.get('product')}) or verified equivalent.",
            "statutory_basis": "Public Procurement (Preference to Make in India) Order (PPP-MII), 2017 (DPIIT Guidelines)."
        })
        item_idx += 1

    # If no specific findings, provide default compliance notice
    if not amendment_rows:
        amendment_rows.append({
            "sl_no": 1,
            "clause_ref": "Quality & Standards Assurance",
            "existing_provision": "As per published Notice Inviting Tender (NIT)",
            "amended_provision": "All offered supplies must strictly conform to current Bureau of Indian Standards specifications with operative BIS Certification Mark License (CM/L).",
            "statutory_basis": "Bureau of Indian Standards Act, 2016."
        })

    # Render formatted legal text
    text_buffer = [
        "================================================================================",
        "                     GOVERNMENT OF INDIA / PUBLIC SECTOR TENDER",
        "                         CORRIGENDUM & ADDENDUM NOTICE",
        "================================================================================",
        f"Corrigendum No: {corrigendum_no}                             Date: {issuing_date}",
        f"Tender ID / GeM Bid Ref: {tender_id or 'GEM/2026/B/REF-SPEC'}",
        f"Procuring Authority: {department or 'Central Public Works Department / GeM'}",
        f"Work / Supply Nomenclature: {tender_title or 'Procurement of Works & Engineering Goods'}",
        "--------------------------------------------------------------------------------",
        "",
        "In accordance with Rule 144(i) of General Financial Rules (GFR), 2017 and statutory",
        "Quality Control Orders enacted under Section 16 of the Bureau of Indian Standards Act, 2016,",
        "the following amendments are hereby issued and shall form an integral part of the bid:",
        "",
        "AMENDMENT SCHEDULE:"
    ]

    for row in amendment_rows:
        text_buffer.append(f"\n[Item {row['sl_no']}] Clause Ref: {row['clause_ref']}")
        text_buffer.append(f"   FOR:     {row['existing_provision']}")
        text_buffer.append(f"   READ AS: {row['amended_provision']}")
        text_buffer.append(f"   REASON:  {row['statutory_basis']}")

    text_buffer.extend([
        "",
        "--------------------------------------------------------------------------------",
        "STATUTORY PENAL ADVISORY UNDER SECTION 29, BIS ACT 2016:",
        "Any manufacturer, vendor, or contractor manufacturing, storing, distributing, or offering",
        "for sale goods covered under mandatory Quality Control Orders without a valid BIS Standard",
        "Mark (ISI Mark / CRS Registration) shall be liable to imprisonment for a term up to two years",
        "or with fine not less than two lakh rupees, or both.",
        "",
        "All other terms and conditions of the original tender document remain unaltered.",
        "",
        "Approved & Authorized for Publication by:",
        f"COMPETENT PROCUREMENT AUTHORITY / TENDER EVALUATION COMMITTEE",
        f"Date: {issuing_date}",
        "================================================================================"
    ])

    formatted_text = "\n".join(text_buffer)

    return {
        "corrigendum_no": corrigendum_no,
        "issuing_date": issuing_date,
        "tender_id": tender_id or "GEM/2026/B/DEFAULT",
        "tender_title": tender_title or "Engineering Procurement",
        "department": department or "Government Procurement Entity",
        "total_amendments": len(amendment_rows),
        "amendment_rows": amendment_rows,
        "formatted_text": formatted_text,
        "compliance_score": findings.get("compliance_score", 100),
        "status": "APPROVED_FOR_ISSUANCE"
    }
