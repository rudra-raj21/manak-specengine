#!/usr/bin/env python3
"""
Step 4: Consolidation & Canonical CSV Re-Export Engine
Merges and deduplicates all harvested node and edge streams into the final production graph files:
1. data/final_nodes_standards.csv
2. data/final_nodes_qcos.csv
3. data/final_edges_all.csv (source, target, relationship, source_type, target_type, description)
Prints comprehensive terminal summary of all data files, row counts, sizes, and graph metrics.
"""

import csv
import os
import json
import re

DATA_DIR = os.path.abspath("data")

# Sources
NODES_STANDARDS_SRC = os.path.join(DATA_DIR, "graph_export", "nodes_standards.csv")
NODES_QCO_SRC = os.path.join(DATA_DIR, "graph_export", "nodes_qco.csv")
EDGES_MANDATED_SRC = os.path.join(DATA_DIR, "graph_export", "edges_mandated_by.csv")
EDGES_SUPERSEDES_SRC = os.path.join(DATA_DIR, "edges_supersedes.csv")
EDGES_TOP200_SRC = os.path.join(DATA_DIR, "edges_top200_normative.csv")
EDGES_SCOPE_SRC = os.path.join(DATA_DIR, "edges_scope_citations.csv")
EDGES_SEED_SRC = os.path.join(DATA_DIR, "normative_graph_edges.csv")

# Targets
FINAL_STANDARDS_CSV = os.path.join(DATA_DIR, "final_nodes_standards.csv")
FINAL_QCOS_CSV = os.path.join(DATA_DIR, "final_nodes_qcos.csv")
FINAL_EDGES_CSV = os.path.join(DATA_DIR, "final_edges_all.csv")
REPORT_JSON = os.path.join(DATA_DIR, "graph_consolidation_report.json")

def clean_id(val: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]+', '_', val.strip()).strip('_')

def format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} KB"
    return f"{size_bytes} B"

def count_rows(file_path: str) -> int:
    if not os.path.exists(file_path):
        return 0
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return sum(1 for _ in f) - 1  # subtract header

def consolidate():
    print("=" * 80)
    print("  STEP 4: CONSOLIDATING CANONICAL KNOWLEDGE GRAPH DATASETS")
    print("=" * 80)

    # 1. Consolidate Standards Nodes
    standards_nodes = {}
    if os.path.exists(NODES_STANDARDS_SRC):
        with open(NODES_STANDARDS_SRC, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sid = row.get("standard_id") or clean_id(row.get("is_number", ""))
                if sid:
                    standards_nodes[sid] = {
                        "standard_id": sid,
                        "is_number": row.get("is_number", ""),
                        "title": row.get("title", ""),
                        "year": row.get("year", ""),
                        "department": row.get("department", "General"),
                        "committee": row.get("committee", ""),
                        "status": row.get("status", "ACTIVE"),
                        "amendments_count": row.get("amendments_count", 0),
                        "ics_code": row.get("ics_code", ""),
                        "gazette_date": row.get("gazette_date", "")
                    }

    with open(FINAL_STANDARDS_CSV, "w", encoding="utf-8", newline="") as f:
        fields = ["standard_id", "is_number", "title", "year", "department", "committee", "status", "amendments_count", "ics_code", "gazette_date"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(standards_nodes.values())
    print(f"[OK] Exported {len(standards_nodes)} unique standards to {FINAL_STANDARDS_CSV}")

    # 2. Consolidate QCO Nodes
    qco_nodes = {}
    if os.path.exists(NODES_QCO_SRC):
        with open(NODES_QCO_SRC, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                qid = row.get("qco_id") or clean_id(row.get("order_name", ""))
                if qid:
                    qco_nodes[qid] = {
                        "qco_id": qid,
                        "order_name": row.get("order_name", ""),
                        "gazette_no": row.get("gazette_no", ""),
                        "order_date": row.get("order_date", ""),
                        "effective_date": row.get("effective_date", ""),
                        "mandatory_scheme": row.get("mandatory_scheme", "Scheme-I"),
                        "ministry_id": row.get("ministry_id", ""),
                        "penal_clause": row.get("penal_clause", "")
                    }

    with open(FINAL_QCOS_CSV, "w", encoding="utf-8", newline="") as f:
        fields = ["qco_id", "order_name", "gazette_no", "order_date", "effective_date", "mandatory_scheme", "ministry_id", "penal_clause"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(qco_nodes.values())
    print(f"[OK] Exported {len(qco_nodes)} unique QCO orders to {FINAL_QCOS_CSV}")

    # 3. Consolidate All Edges
    all_edges = []
    seen_edges = set()

    def add_edge(src, tgt, rel, src_type="Standard", tgt_type="Standard", desc=""):
        src_clean = clean_id(src)
        tgt_clean = clean_id(tgt)
        if not src_clean or not tgt_clean:
            return
        if src_clean == tgt_clean and rel in ["NORMATIVE_REF", "TESTED_BY", "SUPERSEDES"]:
            return
        
        edge_key = (src_clean, tgt_clean, rel)
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            all_edges.append({
                "source": src_clean,
                "target": tgt_clean,
                "relationship": rel,
                "source_type": src_type,
                "target_type": tgt_type,
                "description": desc[:250]
            })

    # A. Mandated By Edges
    if os.path.exists(EDGES_MANDATED_SRC):
        with open(EDGES_MANDATED_SRC, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                add_edge(row["source_standard_id"], row["target_qco_id"], "MANDATED_BY", "Standard", "QCO", row.get("description", ""))

    # B. Supersedes Edges
    if os.path.exists(EDGES_SUPERSEDES_SRC):
        with open(EDGES_SUPERSEDES_SRC, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                add_edge(row["source_id"], row["target_id"], "SUPERSEDES", "Standard", "Standard", row.get("description", ""))

    # C. Scope & Series Citations
    if os.path.exists(EDGES_SCOPE_SRC):
        with open(EDGES_SCOPE_SRC, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                add_edge(row["source_id"], row["target_id"], row["relationship"], row["source_type"], row["target_type"], row.get("context_snippet", ""))

    # D. Top 200 Normative & Testing Edges
    if os.path.exists(EDGES_TOP200_SRC):
        with open(EDGES_TOP200_SRC, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                add_edge(row["source_id"], row["target_id"], row["relationship"], row["source_type"], row["target_type"], row.get("description", ""))

    # E. Seed Normative Edges
    if os.path.exists(EDGES_SEED_SRC):
        with open(EDGES_SEED_SRC, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                add_edge(row["source"], row["target"], row["relation"], row.get("source_type", "Standard"), row.get("target_type", "Standard"), row.get("description", ""))

    # Export final edges
    with open(FINAL_EDGES_CSV, "w", encoding="utf-8", newline="") as f:
        fields = ["source", "target", "relationship", "source_type", "target_type", "description"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_edges)
    print(f"[OK] Exported {len(all_edges)} consolidated, deduplicated edges to {FINAL_EDGES_CSV}")

    # Edge Breakdown
    breakdown = {}
    for e in all_edges:
        rel = e["relationship"]
        breakdown[rel] = breakdown.get(rel, 0) + 1

    report = {
        "nodes": {
            "Standard": len(standards_nodes),
            "QCO": len(qco_nodes),
            "total_nodes": len(standards_nodes) + len(qco_nodes)
        },
        "edges": {
            "breakdown": breakdown,
            "total_edges": len(all_edges)
        },
        "files_generated": [
            FINAL_STANDARDS_CSV,
            FINAL_QCOS_CSV,
            FINAL_EDGES_CSV
        ]
    }

    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # 4. Terminal Report
    print("\n" + "=" * 80)
    print("  EXPLICIT DATASET INVENTORY (data/)")
    print("=" * 80)
    print(f"{'Filename / Path':<50} | {'Rows':<8} | {'File Size':<10}")
    print("-" * 80)

    # List all files directly in data/ and subdirectories
    all_files = []
    for root, dirs, files in os.walk(DATA_DIR):
        for file in sorted(files):
            if file == ".DS_Store":
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, os.path.dirname(DATA_DIR))
            size = os.path.getsize(full_path)
            rows = count_rows(full_path) if full_path.endswith((".csv", ".jsonl")) else "-"
            all_files.append((rel_path, full_path, rows, size))

    for rel_path, full_path, rows, size in sorted(all_files):
        row_str = str(rows) if isinstance(rows, int) else "-"
        print(f"{full_path:<50} | {row_str:<8} | {format_size(size):<10}")

    print("\n" + "=" * 80)
    print("  GRAPH TOPOLOGY METRICS")
    print("=" * 80)
    print("Nodes by Label:")
    print(f"  - (:Standard): {report['nodes']['Standard']:,}")
    print(f"  - (:QCO):      {report['nodes']['QCO']:,}")
    print(f"  - Total Nodes: {report['nodes']['total_nodes']:,}")
    print("\nEdges by Relationship Type:")
    for rel, count in sorted(breakdown.items(), key=lambda x: -x[1]):
        print(f"  - [:{rel}]: {count:,}")
    print(f"  - Total Consolidated Edges: {report['edges']['total_edges']:,}")
    print("=" * 80 + "\n")

    return report

if __name__ == "__main__":
    consolidate()
