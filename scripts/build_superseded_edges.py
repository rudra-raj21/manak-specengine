#!/usr/bin/env python3
"""
Step 2: Superseded Standards Graph Builder
Extracts and builds directed (CurrentStandard)-[:SUPERSEDES]->(OldStandard) edges:
1. Historical chronological revision progression (Year N supersedes Year N-1 for same IS designator).
2. Explicit textual supersession declarations in descriptions, titles, and scopes.
3. Curated historical revision lists from BIS catalogs.
4. Cross-standard supersession rules (e.g. IS 1786 supersedes IS 432; IS 2062 supersedes IS 226).
Exports clean edges to data/edges_supersedes.csv.
"""

import json
import csv
import os
import re
from collections import defaultdict

STANDARDS_CSV = "data/nodes_standards.csv" if os.path.exists("data/nodes_standards.csv") else "data/graph_export/nodes_standards.csv"
CATALOG_JSONL = "data/full_standards_catalog.jsonl" if os.path.exists("data/full_standards_catalog.jsonl") else "data/exhaustive_standards.jsonl"
SEED_CATALOG = "data/standards_catalog.json"
OUTPUT_CSV = "data/edges_supersedes.csv"

SUPERSEDES_TEXT_REGEX = re.compile(
    r'(?:superced(?:ing|ed\s+by)|supersed(?:ing|ed\s+by)|replaces?|withdrawn\s+in\s+favour\s+of)\s*:?\s*(IS\s*[\d\w\:\-\(\)\.]+)',
    re.I
)

CROSS_STANDARD_SUPERSEDED = [
    ("IS 1786", "IS 432 (Part 1)", "High-strength TMT rebar superseded mild steel plain round bars for concrete reinforcement"),
    ("IS 2062", "IS 226", "IS 2062 amalgamated and superseded IS 226 structural steel"),
    ("IS 2062", "IS 432 (Part 1)", "IS 2062 superseded plain structural tie bars"),
    ("IS 13252 (Part 1)", "IS/IEC 60950-1", "Information Technology Equipment safety standard supersession"),
    ("IS 16046 (Part 2)", "IS 16046:2015", "Separated lithium battery systems from secondary alkaline systems"),
    ("IS 1489 (Part 1)", "IS 1489:1976", "Split into Part 1 Fly-ash and Part 2 Calcined clay"),
    ("IS 269", "IS 8112", "IS 269:2015 consolidated 33, 43, and 53 grade cement specifications (superseding IS 8112 43 grade)"),
    ("IS 269", "IS 12269", "IS 269:2015 consolidated 53 grade OPC (superseding IS 12269 53 grade)"),
    ("IS/IEC 60947-1", "IS 13947 (Part 1)", "Adoption of IEC 60947 switchgear standards"),
    ("IS/IEC 60947-2", "IS 13947 (Part 2)", "Circuit breakers supersession")
]

def clean_id(val: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]+', '_', val.strip()).strip('_')

def normalize_is(raw: str) -> str:
    s = re.sub(r'\s+', ' ', raw).strip()
    s = re.sub(r':\s*Part\s*(\d+)', r' (Part \1)', s, flags=re.I)
    s = re.sub(r'\bPart\s*(\d+)', r'(Part \1)', s, flags=re.I)
    s = s.rstrip('.,;:')
    if not s.startswith("IS"):
        s = f"IS {s}"
    return s

def run_build_supersedes():
    edges = []
    seen = set()

    # 1. Gather all standards grouped by base number and publication year
    by_base = defaultdict(list)
    standards_info = {}

    if os.path.exists(CATALOG_JSONL):
        with open(CATALOG_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    s = json.loads(line)
                    is_num = s.get("is_number", "").strip()
                    if not is_num:
                        continue
                    
                    year = s.get("year")
                    status = s.get("status", "ACTIVE")
                    # Preserve full Part and Section hierarchy before revision year
                    cleaned_no_year = re.sub(r':\s*\d{4}.*$', '', is_num).strip()
                    base = normalize_is(cleaned_no_year)
                    
                    standards_info[clean_id(is_num)] = {
                        "is_number": is_num,
                        "year": year,
                        "status": status,
                        "title": s.get("title", "")
                    }
                    
                    if year and isinstance(year, int) and year > 1940:
                        by_base[base].append({
                            "id": clean_id(is_num),
                            "is_number": is_num,
                            "year": year,
                            "status": status
                        })
                except Exception:
                    continue

    print(f"Grouped standards by base designator: {len(by_base)} distinct standard series.")

    # 2. Add chronological supersession edges: newer year supersedes older year
    chrono_count = 0
    for base, revs in by_base.items():
        if len(revs) < 2:
            continue
        
        # Sort chronologically by year ascending
        sorted_revs = sorted(revs, key=lambda x: (x["year"], x["is_number"]))
        
        # Unique by year to avoid duplicates
        unique_by_year = []
        seen_years = set()
        for r in sorted_revs:
            if r["year"] not in seen_years:
                seen_years.add(r["year"])
                unique_by_year.append(r)

        if len(unique_by_year) >= 2:
            for i in range(len(unique_by_year) - 1):
                older = unique_by_year[i]
                newer = unique_by_year[i + 1]
                
                # Directed edge: Newer supersedes Older
                src_id = newer["id"]
                tgt_id = older["id"]
                key = (src_id, tgt_id, "SUPERSEDES")
                
                if key not in seen and src_id != tgt_id:
                    seen.add(key)
                    edges.append({
                        "source_id": src_id,
                        "source_is": newer["is_number"],
                        "source_type": "Standard",
                        "target_id": tgt_id,
                        "target_is": older["is_number"],
                        "target_type": "Standard",
                        "relationship": "SUPERSEDES",
                        "confidence": 0.95,
                        "description": f"{newer['is_number']} ({newer['year']}) chronologically supersedes {older['is_number']} ({older['year']})"
                    })
                    chrono_count += 1

    print(f"Generated {chrono_count} chronological supersession edges.")

    # 3. Add explicit supersession links from curated catalog
    curated_count = 0
    if os.path.exists(SEED_CATALOG):
        with open(SEED_CATALOG, "r", encoding="utf-8") as f:
            curated_data = json.load(f)
            for std in curated_data:
                curr_is = std.get("is_number", "")
                curr_id = clean_id(curr_is)
                hist_revs = std.get("historical_revisions", [])
                
                for prev in hist_revs:
                    prev_is = normalize_is(prev)
                    prev_id = clean_id(prev_is)
                    key = (curr_id, prev_id, "SUPERSEDES")
                    
                    if key not in seen and curr_id != prev_id:
                        seen.add(key)
                        edges.append({
                            "source_id": curr_id,
                            "source_is": curr_is,
                            "source_type": "Standard",
                            "target_id": prev_id,
                            "target_is": prev_is,
                            "target_type": "Standard",
                            "relationship": "SUPERSEDES",
                            "confidence": 0.99,
                            "description": f"{curr_is} supersedes historical revision {prev_is}"
                        })
                        curated_count += 1

    print(f"Generated {curated_count} curated historical revision supersession edges.")

    # 4. Add Cross-standard supersession rules
    cross_count = 0
    for curr_is, prev_is, reason in CROSS_STANDARD_SUPERSEDED:
        curr_id = clean_id(curr_is)
        prev_id = clean_id(prev_is)
        key = (curr_id, prev_id, "SUPERSEDES")
        if key not in seen:
            seen.add(key)
            edges.append({
                "source_id": curr_id,
                "source_is": curr_is,
                "source_type": "Standard",
                "target_id": prev_id,
                "target_is": prev_is,
                "target_type": "Standard",
                "relationship": "SUPERSEDES",
                "confidence": 1.0,
                "description": reason
            })
            cross_count += 1

    # 5. Textual supersession regex extraction from catalog
    text_count = 0
    if os.path.exists(CATALOG_JSONL):
        with open(CATALOG_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    s = json.loads(line)
                    is_num = s.get("is_number", "")
                    if not is_num:
                        continue
                    
                    curr_id = clean_id(is_num)
                    text = f"{s.get('superseded_by', '')} {s.get('scope', '')} {s.get('title', '')}"
                    
                    matches = SUPERSEDES_TEXT_REGEX.findall(text)
                    for m in matches:
                        tgt_is = normalize_is(m)
                        tgt_id = clean_id(tgt_is)
                        key = (curr_id, tgt_id, "SUPERSEDES")
                        if key not in seen and curr_id != tgt_id:
                            seen.add(key)
                            edges.append({
                                "source_id": curr_id,
                                "source_is": is_num,
                                "source_type": "Standard",
                                "target_id": tgt_id,
                                "target_is": tgt_is,
                                "target_type": "Standard",
                                "relationship": "SUPERSEDES",
                                "confidence": 0.88,
                                "description": f"Textual supersession reference found in catalog metadata"
                            })
                            text_count += 1
                except Exception:
                    continue

    print(f"Generated {text_count} textual supersession edges.")

    # Export to CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    fields = ["source_id", "source_is", "source_type", "target_id", "target_is", "target_type", "relationship", "confidence", "description"]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(edges)

    print(f"\nStep 2 Complete! Saved {len(edges)} total SUPERSEDES edges to {OUTPUT_CSV}:")
    print(f"  - Chronological pairs: {chrono_count}")
    print(f"  - Curated revisions:  {curated_count}")
    print(f"  - Cross-standards:    {cross_count}")
    print(f"  - Textual mentions:   {text_count}")
    return len(edges)

if __name__ == "__main__":
    run_build_supersedes()
