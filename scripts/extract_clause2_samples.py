#!/usr/bin/env python3
"""
Downloads and extracts authentic Clause 2 ("Normative References" / "References")
from Archive.org Indian Standards text editions.
"""
import urllib.request
import re
import os
import json

STANDARDS = [
    {
        "is_number": "IS 2062",
        "archive_id": "gov.in.is.2062.2011",
        "file_name": "is.2062.2011_djvu.txt",
        "title": "Hot Rolled Medium and High Tensile Structural Steel"
    },
    {
        "is_number": "IS 1786",
        "archive_id": "gov.in.is.1786.2008",
        "file_name": "is.1786.2008_djvu.txt",
        "title": "High Strength Deformed Steel Bars and Wires for Concrete Reinforcement"
    },
    {
        "is_number": "IS 456",
        "archive_id": "gov.in.is.456.2000",
        "file_name": "is.456.2000_djvu.txt",
        "title": "Plain and Reinforced Concrete - Code of Practice"
    },
    {
        "is_number": "IS 13252 (Part 1)",
        "archive_id": "gov.in.is.13252.1.2010",
        "file_name": "is.13252.1.2010_djvu.txt",
        "title": "Information Technology Equipment - Safety - Part 1 General Requirements"
    },
    {
        "is_number": "IS 4984",
        "archive_id": "gov.in.is.4984.1995",
        "file_name": "is.4984.1995_djvu.txt",
        "title": "High Density Polyethylene Pipes for Potable Water Supplies"
    },
    {
        "is_number": "IS 694",
        "archive_id": "gov.in.is.694.2010",
        "file_name": "is.694.2010_djvu.txt",
        "title": "Polyvinyl Chloride Insulated Unsheathed and Sheathed Cables"
    },
    {
        "is_number": "IS 2925",
        "archive_id": "gov.in.is.2925.1984",
        "file_name": "is.2925.1984_djvu.txt",
        "title": "Specification for Industrial Safety Helmets"
    }
]

def extract_clause2_from_text(text: str) -> str:
    """Extracts Clause 2 / Normative References section using regex patterns."""
    # Pattern 1: standard clause 2 heading
    patterns = [
        r'(?:2\s+(?:NORMATIVE\s+)?REFERENCES?[\s\S]*?)(?=\n\s*3\s+[A-Z])',
        r'(?:Clause\s+2[\s\S]*?REFERENCES?[\s\S]*?)(?=\n\s*3\s+[A-Z])',
        r'(?:SECTION\s+2[\s\S]*?REFERENCES?[\s\S]*?)(?=\n\s*3\s+[A-Z])'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return ""

def main():
    os.makedirs("data/clause2_samples", exist_ok=True)
    summary = []

    for std in STANDARDS:
        url = f"https://archive.org/download/{std['archive_id']}/{std['file_name']}"
        print(f"Fetching {std['is_number']} from {url}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw_text = resp.read().decode("utf-8", errors="ignore")
                clause2_text = extract_clause2_from_text(raw_text)
                
                # If clause 2 was extracted, save it
                safe_name = std['is_number'].replace(' ', '_').replace('(', '').replace(')', '').lower()
                sample_file = f"data/clause2_samples/{safe_name}_clause2.txt"
                
                if clause2_text:
                    with open(sample_file, "w", encoding="utf-8") as f:
                        f.write(clause2_text)
                    print(f"  [OK] Extracted {len(clause2_text)} chars into {sample_file}")
                else:
                    # Save first 8000 chars as fallback snippet
                    with open(sample_file, "w", encoding="utf-8") as f:
                        f.write(raw_text[1000:9000])
                    print(f"  [Partial] Saved header block into {sample_file}")
                
                # Extract Indian Standard numbers mentioned in Clause 2
                refs = re.findall(r'IS\s+(\d+(?:\s*(?:\([^\)]+\)|Part\s*\d+)?(?:\s*:\s*\d{4})?)?)', clause2_text or raw_text[:10000])
                clean_refs = list(dict.fromkeys([f"IS {r.strip()}" for r in refs if r.strip()]))
                
                summary.append({
                    "is_number": std["is_number"],
                    "title": std["title"],
                    "archive_id": std["archive_id"],
                    "clause2_file": sample_file,
                    "extracted_refs_sample": clean_refs[:8]
                })
        except Exception as e:
            print(f"  [Error] {e}")

    with open("data/clause2_samples/summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("Done extracting Clause 2 samples.")

if __name__ == "__main__":
    main()
