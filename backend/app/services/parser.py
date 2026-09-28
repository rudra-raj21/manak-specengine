"""
Parser and normalizer service for BIS (Bureau of Indian Standards) documents.
Extracts Clause 2 Normative References, classifies Test Methods, and normalizes standard notations.
"""

import re
from typing import List, Dict, Any, Optional, Tuple

# Roman to Arabic numeral conversion helper
ROMAN_NUMERAL_MAP = {
    "i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5",
    "vi": "6", "vii": "7", "viii": "8", "ix": "9", "x": "10",
    "xi": "11", "xii": "12"
}

TEST_KEYWORDS = {
    "test", "testing", "sample", "sampling", "method", "determination",
    "analysis", "tolerance", "measurement", "apparatus", "tensile",
    "bend", "impact", "hardness", "spectrometric", "crackability",
    "chemical analysis", "proof stress", "elongation", "charpy",
    "microstructure", "radiographic", "ultrasonic", "flammability"
}


def normalize_roman_part(part_str: str) -> str:
    """Normalize Roman numeral or OCR typo part indicator (e.g., 'Parti', 'Part I', 'Part 1')."""
    m = re.match(r"(?i)part\s*([0-9]+|[ivxlcdm]+)", part_str.strip())
    if not m:
        return part_str.strip()
    val = m.group(1).lower()
    if val in ROMAN_NUMERAL_MAP:
        return f"Part {ROMAN_NUMERAL_MAP[val]}"
    elif val.isdigit():
        return f"Part {val}"
    return f"Part {m.group(1).upper()}"


def normalize_standard_ref(ref: str) -> str:
    """
    Normalizes a standard notation string into canonical form:
    Examples:
      'IS 1608 : Part 1 : 2018' -> 'IS 1608 (Part 1):2018'
      'IS  2062 : 2011'          -> 'IS 2062:2011'
      '1608:2005'                -> 'IS 1608:2005'
      '228 (Parts 1 to 24)'      -> 'IS 228'
      'IS/ISO 9001:2015'         -> 'IS/ISO 9001:2015'
      'lEC 60065:2001'           -> 'IEC 60065:2001'
    """
    if not ref:
        return ""

    raw = ref.strip().rstrip(".,;:")
    # Fix common OCR typos: leading lowercase l in 'lEC' or 'I EC'
    raw = re.sub(r"^[lI]\s*EC\b", "IEC", raw, flags=re.I)
    raw = re.sub(r"^IS\s*/\s*", "IS/", raw, flags=re.I)
    raw = re.sub(r"\s+", " ", raw)

    # Remove phrases like '(in various parts)', '(Parts 1 to 24)', '(all parts)'
    raw = re.sub(r"(?i)\s*\((?:in\s+various|all\s+parts|parts?\s+\d+\s+to\s+\d+)[^)]*\)", "", raw)

    # Standardize Part indicator: e.g., 'Part 1', '(Part 1)', '(Parti)', ': Part 1 :'
    part_match = re.search(r"(?i)(?:\(?\s*Part\s*[0-9a-z]+\s*\)?|\bPart\s*[0-9a-z]+)", raw)
    part_formatted = ""
    if part_match:
        part_raw = part_match.group(0).strip("()")
        part_formatted = f"({normalize_roman_part(part_raw)})"
        raw = raw[:part_match.start()] + " " + raw[part_match.end():]

    # Look for year: e.g., ': 2018', ':1989', '2011'
    year_match = re.search(r":\s*(\d{4})\b", raw)
    year_str = ""
    if year_match:
        year_str = f":{year_match.group(1)}"
        raw = raw[:year_match.start()] + raw[year_match.end():]
    else:
        # Check trailing year without colon
        tail_year = re.search(r"\b(19\d{2}|20\d{2})\b$", raw)
        if tail_year and not raw.startswith(tail_year.group(1)):
            year_str = f":{tail_year.group(1)}"
            raw = raw[:tail_year.start()]

    # Clean the remaining base identifier
    base = raw.strip()
    base = re.sub(r"[:\s]+$", "", base)
    base = re.sub(r"\s+", " ", base)

    # Ensure prefix
    if re.match(r"^\d{2,5}\b", base):
        base = f"IS {base}"
    elif re.match(r"^(?:ISO|IEC|ASTM|EN|BS)\b", base, re.I):
        pass  # Keep standard prefix
    elif not re.match(r"^(?:IS|IS/ISO|IS/IEC)\b", base, re.I):
        base = f"IS {base}"

    result = base
    if part_formatted:
        result = f"{result} {part_formatted}"
    if year_str:
        result = f"{result}{year_str}"

    return re.sub(r"\s+", " ", result).strip()


def extract_clause2_section(text: str) -> str:
    """
    Extracts the Clause 2 (Normative References) section from a BIS standard document.
    Searches for headings such as '2 NORMATIVE REFERENCES' or '2 REFERENCES'
    and stops at Clause 3 (Terminology, Definitions, Requirements, etc.).
    """
    if not text:
        return ""

    # Look for Clause 2 start
    c2_pattern = re.compile(
        r"(?:^|\n)\s*(?:SECTION\s+)?2\s+(?:NORMATIVE\s+)?REFERENCES\b|"
        r"(?:^|\n)\s*2\s+REFERENCES\b|"
        r"(?:^|\n)\s*Clause\s+2\b|"
        r"(?:^|\n)\s*Normative\s+references\b",
        re.IGNORECASE
    )
    match = c2_pattern.search(text)
    if not match:
        return text  # Fallback to full text if no explicit Clause 2 header

    start_idx = match.start()

    # Look for Clause 3 or next major section
    c3_pattern = re.compile(
        r"(?:^|\n)\s*(?:SECTION\s+)?3\s+(?:TERMINOLOGY|DEFINITIONS|REQUIREMENTS|MATERIALS|SYMBOLS|GENERAL|SCOPE)\b|"
        r"(?:^|\n)\s*3\s+[A-Z\s]{4,}\b",
        re.IGNORECASE
    )
    next_match = c3_pattern.search(text, pos=match.end())
    if next_match:
        return text[start_idx:next_match.start()]
    
    return text[start_idx:]


def extract_clause2_references(text: str) -> List[str]:
    """
    Extracts and normalizes all referenced standards from Clause 2 text.
    Handles explicit 'IS 1234', 'IS/ISO 9001', 'IEC 60065', and tabular Clause 2 rows.
    """
    if not text:
        return []

    c2_text = extract_clause2_section(text)
    extracted: List[str] = []
    seen = set()

    # Strategy 1: Explicit pattern matches (e.g. IS 2062:2011, IS 1608 (Part 1):2018)
    explicit_pat = re.compile(
        r"\b(?:IS(?:/ISO)?(?:/IEC)?\s+\d+(?:\s*(?:\(Part\s*[\dIVXLCDM]+\)|Part\s*[\dIVXLCDM]+))?(?:\s*:\s*\d{4})?)\b|"
        r"\b(?:(?:[lI]\s*EC|ISO|ASTM|EN|BS)\s+[A-Z\d\-]+(?:\s*(?:\(Part\s*[\dIVXLCDM]+\)|Part\s*[\dIVXLCDM]+))?(?:\s*:\s*\d{4})?)\b",
        re.IGNORECASE
    )

    for m in explicit_pat.finditer(c2_text):
        normalized = normalize_standard_ref(m.group(0))
        if normalized and normalized not in seen:
            seen.add(normalized)
            extracted.append(normalized)

    # Strategy 2: Tabular line-by-line scanning in Clause 2 tables (where IS prefix is omitted)
    lines = c2_text.splitlines()
    table_num_pat = re.compile(
        r"^\s*([1-9]\d{1,4}(?:\s*(?:\(Part\s*[\dIVXLCDM]+\)|Part\s*[\dIVXLCDM]+))?(?:\s*:\s*\d{4})?)\b"
    )

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if re.search(r"(?i)^(?:IS\s+No|Title|Page|Table|Section)\b", line_clean):
            continue

        tm = table_num_pat.match(line_clean)
        if tm:
            cand = tm.group(1)
            # Exclude lone 4-digit years (e.g. 1989 alone without standard number)
            if re.match(r"^(?:19|20)\d{2}$", cand):
                continue
            normalized = normalize_standard_ref(cand)
            if normalized and normalized not in seen:
                seen.add(normalized)
                extracted.append(normalized)

    return extracted


def extract_test_methods(text: str) -> List[str]:
    """
    Identifies test method and sampling standards from Clause 2 text.
    Extracts standards associated with testing keywords in their titles or context.
    """
    if not text:
        return []

    c2_text = extract_clause2_section(text)
    test_standards: List[str] = []
    seen = set()

    lines = c2_text.splitlines()
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean:
            continue

        refs = extract_clause2_references(line_clean)
        if not refs:
            continue

        desc = line_clean
        # If line only has standard number, look ahead to capture title until next standard
        if len(line_clean.split()) <= 4:
            subsequent = []
            for next_line in lines[i + 1:min(len(lines), i + 4)]:
                if extract_clause2_references(next_line.strip()):
                    break
                subsequent.append(next_line.strip())
            desc = f"{line_clean} {' '.join(subsequent)}"

        desc_lower = desc.lower()
        if any(kw in desc_lower for kw in TEST_KEYWORDS):
            for r in refs:
                if r not in seen:
                    seen.add(r)
                    test_standards.append(r)

    return test_standards


def parse_bis_document(
    text: str,
    default_is_number: Optional[str] = None,
    default_title: Optional[str] = None,
    committee: Optional[str] = "CED 54"
) -> Dict[str, Any]:
    """
    Parses a raw text document of an Indian Standard to populate an IndianStandard model payload.
    """
    doc_is_match = re.search(r"\b(IS\s+\d+(?:\s*(?:\(Part\s*\d+\)|Part\s*\d+))?(?:\s*:\s*\d{4})?)\b", text, re.I)
    detected_is_num = normalize_standard_ref(doc_is_match.group(1)) if doc_is_match else None

    if default_is_number:
        if ":" not in default_is_number and detected_is_num and ":" in detected_is_num and detected_is_num.startswith(default_is_number):
            is_num = detected_is_num
        else:
            is_num = normalize_standard_ref(default_is_number)
    else:
        is_num = detected_is_num or "IS Unknown"

    # Year
    year = None
    y_match = re.search(r":\s*(\d{4})\b", is_num)
    if y_match:
        year = int(y_match.group(1))
    else:
        doc_y = re.search(r"\b(19\d{2}|20\d{2})\b", text)
        if doc_y:
            year = int(doc_y.group(1))

    # Clause 2 and test methods
    norm_refs = extract_clause2_references(text)
    test_methods = extract_test_methods(text)

    # Scope / Abstract extraction
    scope_match = re.search(
        r"(?:^|\n)\s*(?:1\s+)?SCOPE\b\s*([^\n\r]+(?:\n[^\n\r]+){1,10})",
        text,
        re.IGNORECASE
    )
    scope = scope_match.group(1).strip() if scope_match else "Scope not explicitly declared."
    if len(scope) < 10:
        scope = f"Standard specification covering requirements for {default_title or is_num}."

    return {
        "is_number": is_num,
        "title": default_title or f"Specification for {is_num}",
        "year": year,
        "status": "ACTIVE",
        "scope": scope,
        "committee": committee or "CED 54",
        "normative_references": norm_refs,
        "test_standards": test_methods,
        "keywords": [w.lower() for w in re.findall(r"\b[A-Za-z]{4,}\b", default_title or "")][:10]
    }
