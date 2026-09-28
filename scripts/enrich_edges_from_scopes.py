#!/usr/bin/env python3
"""
Step 1: Abstract & Scope Citation Extraction Engine (Enriched)
Parses the entire 22,024 standards catalog (scopes, abstracts, titles) to extract
valid inter-standard citations and classify them as NORMATIVE_REF or TESTED_BY.
Also captures multi-part standards series normative dependencies (Part N -> Part 1 General Requirements).
Validates all target standards against the known standards index.
Exports clean edges to data/edges_scope_citations.csv.
"""

import json
import csv
import os
import re
from collections import defaultdict

STANDARDS_CSV = "data/nodes_standards.csv" if os.path.exists("data/nodes_standards.csv") else "data/graph_export/nodes_standards.csv"
CATALOG_JSONL = "data/full_standards_catalog.jsonl" if os.path.exists("data/full_standards_catalog.jsonl") else "data/exhaustive_standards.jsonl"
OUTPUT_CSV = "data/edges_scope_citations.csv"

TEST_KEYWORDS = [
    "test", "testing", "sampling", "method", "determination", "analysis",
    "tolerance", "tolerances", "measurement", "apparatus", "tensile",
    "bend", "impact", "compressive", "flexural", "sieve", "vicat", "hardness"
]

CITATION_REGEX = re.compile(
    r'\b(?:IS(?:/ISO)?(?:/IEC)?\s+\d+(?:\s*(?:Part|\(Part\))\s*\d+)?(?:\s*:\s*\d{4})?)\b',
    re.I
)

def clean_id(val: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]+', '_', val.strip()).strip('_')

def normalize_standard_number(raw: str) -> str:
    s = re.sub(r'\s+', ' ', raw).strip()
    s = re.sub(r':\s*Part\s*(\d+)', r' (Part \1)', s, flags=re.I)
    s = re.sub(r'\bPart\s*(\d+)', r'(Part \1)', s, flags=re.I)
    return s

def build_valid_standards_index():
    valid_ids = {}
    valid_numbers = {}

    # Read from nodes_standards.csv
    if os.path.exists(STANDARDS_CSV):
        with open(STANDARDS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                std_id = row.get("standard_id", "").strip()
                is_num = row.get("is_number", "").strip()
                if std_id and is_num:
                    valid_ids[std_id] = is_num
                    norm = normalize_standard_number(is_num)
                    valid_numbers[norm.upper()] = std_id
                    base = norm.split(":")[0].strip().upper()
                    valid_numbers[base] = std_id

    # Augment from catalog
    if os.path.exists(CATALOG_JSONL):
        with open(CATALOG_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    s = json.loads(line)
                    is_num = s.get("is_number", "").strip()
                    if is_num:
                        std_id = clean_id(is_num)
                        valid_ids[std_id] = is_num
                        norm = normalize_standard_number(is_num)
                        valid_numbers[norm.upper()] = std_id
                        base = norm.split(":")[0].strip().upper()
                        valid_numbers[base] = std_id
                except Exception:
                    continue

    print(f"Loaded standards index: {len(valid_ids)} unique IDs, {len(valid_numbers)} alias lookup keys.")
    return valid_ids, valid_numbers

def run_extraction():
    valid_ids, valid_numbers = build_valid_standards_index()
    edges = []
    seen = set()

    # Part A: Direct regex extraction from scopes, abstracts, titles
    print(f"Scanning scopes, abstracts, and titles from {CATALOG_JSONL}...")
    series_groups = defaultdict(list)

    with open(CATALOG_JSONL, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
            except Exception:
                continue

            src_is = doc.get("is_number", "").strip()
            if not src_is:
                continue

            src_id = clean_id(src_is)
            src_norm = normalize_standard_number(src_is).upper()
            src_base = src_norm.split(":")[0].strip().upper()

            # Track for multi-part series
            m_part = re.match(r'^(IS\s+\d+)(?:[\s\:\-]+(?:Part\s*(\d+)|\((\d+)\)|(\d+)))', src_is, re.I)
            if m_part:
                base_name = m_part.group(1).upper()
                part_no = m_part.group(2) or m_part.group(3) or m_part.group(4)
                series_groups[base_name].append((part_no, src_is, src_id, doc.get("title", "")))

            title = doc.get("title", "") or ""
            scope = doc.get("scope", "") or ""
            full_text = f"{title}. {scope}"

            matches = CITATION_REGEX.findall(full_text)
            if not matches:
                continue

            for raw_target in matches:
                tgt_norm = normalize_standard_number(raw_target)
                tgt_key = tgt_norm.upper()
                tgt_base = tgt_key.split(":")[0].strip()

                if tgt_key == src_norm or tgt_base == src_base:
                    continue

                target_id = valid_numbers.get(tgt_key) or valid_numbers.get(tgt_base)
                if not target_id:
                    continue

                canonical_tgt_is = valid_ids.get(target_id, tgt_norm)

                window_start = max(0, full_text.find(raw_target) - 75)
                window_end = min(len(full_text), full_text.find(raw_target) + len(raw_target) + 75)
                context_window = full_text[window_start:window_end].lower()

                is_test = any(kw in context_window for kw in TEST_KEYWORDS)
                rel_type = "TESTED_BY" if is_test else "NORMATIVE_REF"

                edge_key = (src_id, target_id, rel_type)
                if edge_key not in seen:
                    seen.add(edge_key)
                    edges.append({
                        "source_id": src_id,
                        "source_is": src_is,
                        "source_type": "Standard",
                        "target_id": target_id,
                        "target_is": canonical_tgt_is,
                        "target_type": "TestStandard" if is_test else "Standard",
                        "relationship": rel_type,
                        "confidence": 0.90 if is_test else 0.85,
                        "context_snippet": context_window[:150]
                    })

    direct_count = len(edges)
    print(f"Extracted {direct_count} direct textual citation edges.")

    # Part B: Multi-part series normative reference cascade (Part N -> Part 1 / Base Standard)
    print(f"Extracting series normative reference dependencies across {len(series_groups)} series...")
    series_edges_count = 0

    for base_name, parts in series_groups.items():
        if len(parts) < 2:
            continue

        # Find Part 1 or base standard
        part1 = next(((p_no, is_no, s_id, t) for p_no, is_no, s_id, t in parts if p_no == '1'), None)
        
        target_info = None
        if part1:
            target_info = part1
        else:
            # Check if base standard itself exists in valid_numbers
            base_id = valid_numbers.get(base_name)
            if base_id and base_id in valid_ids:
                target_info = ("base", valid_ids[base_id], base_id, f"{base_name} General Specification")

        if not target_info:
            continue

        tgt_part_no, tgt_is, tgt_id, tgt_title = target_info

        for p_no, src_is, src_id, src_title in parts:
            if src_id == tgt_id or p_no == '1':
                continue

            # Classify if Part N is a testing part
            is_test_part = any(kw in src_title.lower() for kw in TEST_KEYWORDS)
            rel = "TESTED_BY" if is_test_part else "NORMATIVE_REF"

            edge_key = (src_id, tgt_id, rel)
            if edge_key not in seen:
                seen.add(edge_key)
                edges.append({
                    "source_id": src_id,
                    "source_is": src_is,
                    "source_type": "Standard",
                    "target_id": tgt_id,
                    "target_is": tgt_is,
                    "target_type": "TestStandard" if is_test_part else "Standard",
                    "relationship": rel,
                    "confidence": 0.96,
                    "context_snippet": f"Part {p_no} normatively references {tgt_is} (General Requirements / Scope)"
                })
                series_edges_count += 1

    print(f"Added {series_edges_count} multi-part series normative dependency edges.")

    # Save to CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    fields = ["source_id", "source_is", "source_type", "target_id", "target_is", "target_type", "relationship", "confidence", "context_snippet"]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(edges)

    tested_count = sum(1 for e in edges if e["relationship"] == "TESTED_BY")
    norm_count = sum(1 for e in edges if e["relationship"] == "NORMATIVE_REF")
    print(f"\nStep 1 Complete! Saved {len(edges)} total edges to {OUTPUT_CSV}:")
    print(f"  - Direct scope citations: {direct_count}")
    print(f"  - Series Part 1 dependencies: {series_edges_count}")
    print(f"  - NORMATIVE_REF: {norm_count}")
    print(f"  - TESTED_BY:     {tested_count}")
    return len(edges)

if __name__ == "__main__":
    run_extraction()
