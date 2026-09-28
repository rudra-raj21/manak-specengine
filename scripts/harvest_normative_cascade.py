#!/usr/bin/env python3
"""
Pipeline 3: Normative Reference Extraction Engine (Clause 2 & Clause 3 Cascade)
Enhanced with dual-mode parsing:
1. Matches explicit "IS \d+" references.
2. Matches tabular Clause 2 rows where numbers appear under "IS No." column header (e.g. "1608:2005 Metallic materials - Tensile testing").
"""

import urllib.request
import re
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

CHECKPOINT_PATH = "data/harvest_checkpoints/normative_progress.json"
OUTPUT_JSONL = "data/normative_edges_corpus.jsonl"
CONCURRENCY = 8

ANCHOR_STANDARDS = [
    # Civil & Construction
    {"is_number": "IS 2062", "archive_id": "gov.in.is.2062.2011", "file": "is.2062.2011_djvu.txt"},
    {"is_number": "IS 1786", "archive_id": "gov.in.is.1786.2008", "file": "is.1786.2008_djvu.txt"},
    {"is_number": "IS 456", "archive_id": "gov.in.is.456.2000", "file": "is.456.2000_djvu.txt"},
    {"is_number": "IS 800", "archive_id": "gov.in.is.800.2007", "file": "is.800.2007_djvu.txt"},
    {"is_number": "IS 383", "archive_id": "gov.in.is.383.1970", "file": "is.383.1970_djvu.txt"},
    {"is_number": "IS 269", "archive_id": "gov.in.is.269.1989", "file": "is.269.1989_djvu.txt"},
    {"is_number": "IS 1489 (Part 1)", "archive_id": "gov.in.is.1489.1.1991", "file": "is.1489.1.1991_djvu.txt"},
    {"is_number": "IS 10262", "archive_id": "gov.in.is.10262.2009", "file": "is.10262.2009_djvu.txt"},
    {"is_number": "IS 13920", "archive_id": "gov.in.is.13920.1993", "file": "is.13920.1993_djvu.txt"},
    {"is_number": "IS 1893 (Part 1)", "archive_id": "gov.in.is.1893.1.2002", "file": "is.1893.1.2002_djvu.txt"},
    {"is_number": "IS 1077", "archive_id": "gov.in.is.1077.1992", "file": "is.1077.1992_djvu.txt"},
    {"is_number": "IS 808", "archive_id": "gov.in.is.808.1989", "file": "is.808.1989_djvu.txt"},
    {"is_number": "IS 1852", "archive_id": "gov.in.is.1852.1985", "file": "is.1852.1985_djvu.txt"},
    {"is_number": "IS 8910", "archive_id": "gov.in.is.8910.2010", "file": "is.8910.2010_djvu.txt"},
    {"is_number": "IS 432 (Part 1)", "archive_id": "gov.in.is.432.1.1982", "file": "is.432.1.1982_djvu.txt"},

    # Electronics & IT
    {"is_number": "IS 13252 (Part 1)", "archive_id": "gov.in.is.13252.1.2010", "file": "is.13252.1.2010_djvu.txt"},
    {"is_number": "IS 616", "archive_id": "gov.in.is.616.2010", "file": "is.616.2010_djvu.txt"},
    {"is_number": "IS 302-2-25", "archive_id": "gov.in.is.302.2.25.1994", "file": "is.302.2.25.1994_djvu.txt"},
    {"is_number": "IS 1293", "archive_id": "gov.in.is.1293.2005", "file": "is.1293.2005_djvu.txt"},

    # Electrical & Power
    {"is_number": "IS 694", "archive_id": "gov.in.is.694.2010", "file": "is.694.2010_djvu.txt"},
    {"is_number": "IS 1554 (Part 1)", "archive_id": "gov.in.is.1554.1.1988", "file": "is.1554.1.1988_djvu.txt"},
    {"is_number": "IS 7098 (Part 1)", "archive_id": "gov.in.is.7098.1.1988", "file": "is.7098.1.1988_djvu.txt"},
    {"is_number": "IS 1180 (Part 1)", "archive_id": "gov.in.is.1180.1.1989", "file": "is.1180.1.1989_djvu.txt"},

    # Pipes & Chemicals
    {"is_number": "IS 4984", "archive_id": "gov.in.is.4984.1995", "file": "is.4984.1995_djvu.txt"},
    {"is_number": "IS 4985", "archive_id": "gov.in.is.4985.2000", "file": "is.4985.2000_djvu.txt"},
    {"is_number": "IS 7328", "archive_id": "gov.in.is.7328.1992", "file": "is.7328.1992_djvu.txt"},
    {"is_number": "IS 252", "archive_id": "gov.in.is.252.1991", "file": "is.252.1991_djvu.txt"},

    # PPE & Consumer Safety
    {"is_number": "IS 2925", "archive_id": "gov.in.is.2925.1984", "file": "is.2925.1984_djvu.txt"},
    {"is_number": "IS 4151", "archive_id": "gov.in.is.4151.1993", "file": "is.4151.1993_djvu.txt"},
    {"is_number": "IS 303", "archive_id": "gov.in.is.303.1989", "file": "is.303.1989_djvu.txt"},

    # Water & Textiles
    {"is_number": "IS 14543", "archive_id": "gov.in.is.14543.2004", "file": "is.14543.2004_djvu.txt"},
    {"is_number": "IS 1417", "archive_id": "gov.in.is.1417.1999", "file": "is.1417.1999_djvu.txt"}
]

TEST_KEYWORDS = [
    "test", "testing", "method", "determination", "analysis", "sampling",
    "tensile", "bend", "impact", "compressive", "flexural", "sieve",
    "vicat", "hardness", "measurement", "dimensions", "resistance", "tolerances"
]

def extract_clause2_section(text: str) -> str:
    patterns = [
        r'(?:2\s+(?:NORMATIVE\s+)?REFERENCES?[\s\S]*?)(?=\n\s*3\s+[A-Z])',
        r'(?:Clause\s+2[\s\S]*?REFERENCES?[\s\S]*?)(?=\n\s*3\s+[A-Z])',
        r'(?:SECTION\s+2[\s\S]*?REFERENCES?[\s\S]*?)(?=\n\s*3\s+[A-Z])',
        r'(?:2\s+APPLICABLE\s+STANDARDS[\s\S]*?)(?=\n\s*3\s+[A-Z])'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return ""

def normalize_is_reference(raw: str) -> str:
    raw = re.sub(r":\s*\d{4}", "", raw)  # drop year
    raw = re.sub(r"\s+", " ", raw).strip()
    raw = re.sub(r":\s*Part\s*(\d+)", r"(Part \1)", raw, flags=re.I)
    raw = re.sub(r"Part\s*(\d+)", r"(Part \1)", raw, flags=re.I)
    if not raw.startswith("IS"):
        raw = f"IS {raw}"
    return re.sub(r"\s+", " ", raw).strip()

def process_single_standard(item: dict) -> list:
    url = f"https://archive.org/download/{item['archive_id']}/{item['file']}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    edges = []

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw_text = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  [Skip {item['is_number']}] Error downloading {url}: {e}")
        return edges

    clause2_text = extract_clause2_section(raw_text)
    target_text = clause2_text if clause2_text else raw_text[:15000]

    lines = target_text.splitlines()
    in_table = False

    for line in lines:
        stripped = line.strip()
        if "IS No." in stripped or "IS Number" in stripped:
            in_table = True
            continue

        # Strategy A: Explicit "IS 1608"
        match_explicit = re.search(r'\b(IS\s+\d+(?:[\s\:\-]+(?:Part\s*\d+|\([^\)]+\)))?)', stripped, re.I)
        if match_explicit:
            target_is = normalize_is_reference(match_explicit.group(1))
            if target_is != item["is_number"]:
                desc = stripped.replace(match_explicit.group(1), "").strip()
                desc = re.sub(r'^[\s\:\-\–]+', '', desc).strip()
                is_test = any(kw in stripped.lower() or kw in desc.lower() for kw in TEST_KEYWORDS)
                edges.append({
                    "source": item["is_number"],
                    "source_type": "Standard",
                    "target": target_is,
                    "target_type": "TestStandard" if is_test else "Standard",
                    "relation": "TESTED_BY" if is_test else "NORMATIVE_REF",
                    "clause": "Clause 2 Normative References",
                    "description": desc[:250] or f"Referenced in {item['is_number']} Clause 2"
                })
                continue

        # Strategy B: Tabular row under "IS No." (e.g., "1608:2005 Metallic materials — Tensile testing")
        if in_table:
            match_row = re.match(r'^\s*(\d{2,5}(?:\s*(?:Part\s*\d+|\([^\)]+\)))?(?:\s*:\s*\d{4})?)\s+(.*)', stripped)
            if match_row:
                num_part = match_row.group(1)
                desc = match_row.group(2).strip()
                target_is = normalize_is_reference(f"IS {num_part}")
                if target_is != item["is_number"]:
                    is_test = any(kw in stripped.lower() or kw in desc.lower() for kw in TEST_KEYWORDS)
                    edges.append({
                        "source": item["is_number"],
                        "source_type": "Standard",
                        "target": target_is,
                        "target_type": "TestStandard" if is_test else "Standard",
                        "relation": "TESTED_BY" if is_test else "NORMATIVE_REF",
                        "clause": "Clause 2 Normative References Table",
                        "description": desc[:250] or f"Referenced in {item['is_number']} Table 1"
                    })

    # Deduplicate edges
    seen = set()
    deduped = []
    for e in edges:
        key = (e["source"], e["target"], e["relation"])
        if key not in seen:
            seen.add(key)
            deduped.append(e)

    print(f"  [OK] Extracted {len(deduped):2d} reference edges from {item['is_number']}")
    return deduped

def run_harvest():
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/harvest_checkpoints", exist_ok=True)

    print(f"Pipeline 3: Extracting Normative & Test Reference Graph across {len(ANCHOR_STANDARDS)} standards with {CONCURRENCY} threads...")
    all_edges = []
    
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = {executor.submit(process_single_standard, std): std for std in ANCHOR_STANDARDS}
        for future in as_completed(futures):
            std = futures[future]
            try:
                edges = future.result()
                all_edges.extend(edges)
            except Exception as e:
                print(f"Error processing {std['is_number']}: {e}")

    # Deduplicate
    seen = set()
    unique_edges = []
    for e in all_edges:
        key = (e["source"], e["target"], e["relation"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    print(f"Total unique normative & test edges extracted: {len(unique_edges)}")

    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for e in unique_edges:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    ckpt = {
        "total_edges": len(unique_edges),
        "standards_processed": len(ANCHOR_STANDARDS),
        "normative_ref_count": sum(1 for e in unique_edges if e["relation"] == "NORMATIVE_REF"),
        "tested_by_count": sum(1 for e in unique_edges if e["relation"] == "TESTED_BY"),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "is_complete": True
    }
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, indent=2)

    print(f"Pipeline 3 Complete! Saved {len(unique_edges)} edges to {OUTPUT_JSONL}")
    print(f"  * NORMATIVE_REF edges: {ckpt['normative_ref_count']}")
    print(f"  * TESTED_BY edges:     {ckpt['tested_by_count']}")
    return len(unique_edges)

if __name__ == "__main__":
    run_harvest()
