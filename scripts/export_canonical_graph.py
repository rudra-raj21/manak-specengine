#!/usr/bin/env python3
"""
Pipeline 4: Canonical Graph Exporter
Merges harvested data from Pipelines 1, 2, and 3 into clean, relational CSV graph datasets:
1. data/graph_export/nodes_standards.csv
2. data/graph_export/nodes_qco.csv
3. data/graph_export/nodes_ministries.csv
4. data/graph_export/edges_normative_ref.csv
5. data/graph_export/edges_tested_by.csv
6. data/graph_export/edges_mandated_by.csv
7. data/graph_export/graph_summary.json
"""

import json
import csv
import os
import re

STANDARDS_JSONL = "data/exhaustive_standards.jsonl"
STANDARDS_CATALOG = "data/standards_catalog.json"
QCO_JSONL = "data/exhaustive_qco_registry.jsonl"
QCO_JSON = "data/qco_registry.json"
NORMATIVE_JSONL = "data/normative_edges_corpus.jsonl"
NORMATIVE_CSV = "data/normative_graph_edges.csv"
OUTPUT_DIR = "data/graph_export"

def clean_id(val: str) -> str:
    """Creates a deterministic alphanumeric node ID."""
    return re.sub(r'[^A-Za-z0-9_]+', '_', val.strip()).strip('_')

def run_export():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Pipeline 4: Building Canonical Graph Export...")

    # 1. Load Standards Nodes
    standards_map = {}

    # Seed catalog standards (high fidelity)
    if os.path.exists(STANDARDS_CATALOG):
        with open(STANDARDS_CATALOG, "r", encoding="utf-8") as f:
            for s in json.load(f):
                is_num = s["is_number"].strip()
                standards_map[is_num] = {
                    "standard_id": clean_id(is_num),
                    "is_number": is_num,
                    "title": s.get("title", ""),
                    "year": s.get("year", ""),
                    "department": s.get("committee", "").split("(")[0].strip() or "General",
                    "committee": s.get("committee", ""),
                    "status": s.get("status", "ACTIVE"),
                    "amendments_count": len(s.get("amendments", [])),
                    "ics_code": "",
                    "gazette_date": f"{s.get('year', '')}-01-01" if s.get("year") else ""
                }

    # Harvested standards (bulk corpus)
    if os.path.exists(STANDARDS_JSONL):
        with open(STANDARDS_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    s = json.loads(line)
                    is_num = s.get("is_number", "").strip()
                    if is_num and is_num not in standards_map:
                        standards_map[is_num] = {
                            "standard_id": clean_id(is_num),
                            "is_number": is_num,
                            "title": s.get("title", ""),
                            "year": s.get("year", ""),
                            "department": s.get("department", ""),
                            "committee": s.get("committee", ""),
                            "status": s.get("status", "ACTIVE"),
                            "amendments_count": s.get("amendments_count", 0),
                            "ics_code": s.get("ics_code", ""),
                            "gazette_date": s.get("gazette_date", "") or s.get("publicdate", "")
                        }
                except Exception:
                    continue

    print(f"Total standard nodes gathered: {len(standards_map)}")

    # 2. Load QCO Nodes & Ministry Nodes
    qco_map = {}
    ministry_map = {}
    mandated_edges = []

    def process_qco_entry(q):
        order_name = q.get("order_name", "").strip()
        ministry = q.get("ministry", "Department for Promotion of Industry and Internal Trade (DPIIT)").strip()
        qco_id = clean_id(order_name)
        min_id = clean_id(ministry)

        ministry_map[min_id] = {
            "ministry_id": min_id,
            "name": ministry
        }

        if qco_id not in qco_map:
            qco_map[qco_id] = {
                "qco_id": qco_id,
                "order_name": order_name,
                "gazette_no": q.get("gazette_no", "Statutory Order"),
                "order_date": q.get("order_date", ""),
                "effective_date": q.get("effective_date", ""),
                "mandatory_scheme": q.get("mandatory_scheme", "Scheme-I"),
                "ministry_id": min_id,
                "penal_clause": q.get("penal_clause", "")
            }

        # Applicable standards
        app_stds = q.get("applicable_standards", [])
        if not app_stds and q.get("is_number"):
            app_stds = [q["is_number"]]

        for std in app_stds:
            mandated_edges.append({
                "source_standard_id": clean_id(std),
                "is_number": std,
                "target_qco_id": qco_id,
                "relation": "MANDATED_BY",
                "description": f"Mandated under {order_name} ({q.get('mandatory_scheme', 'Scheme-I')})"
            })

    # Read curated QCOs
    if os.path.exists(QCO_JSON):
        with open(QCO_JSON, "r", encoding="utf-8") as f:
            for q in json.load(f):
                process_qco_entry(q)

    # Read harvested QCOs
    if os.path.exists(QCO_JSONL):
        with open(QCO_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        process_qco_entry(json.loads(line))
                    except Exception:
                        continue

    print(f"Total QCO nodes gathered: {len(qco_map)}")
    print(f"Total Ministry nodes gathered: {len(ministry_map)}")
    print(f"Total MANDATED_BY edges gathered: {len(mandated_edges)}")

    # 3. Load Normative & Test Edges
    normative_edges = []
    tested_edges = []

    def process_edge(src, tgt, rel, clause, desc):
        src_id = clean_id(src)
        tgt_id = clean_id(tgt)
        if rel == "TESTED_BY":
            tested_edges.append({
                "source_standard_id": src_id,
                "target_test_standard_id": tgt_id,
                "source_is": src,
                "target_is": tgt,
                "relation": "TESTED_BY",
                "clause": clause or "Testing Protocol",
                "description": desc
            })
        else:
            normative_edges.append({
                "source_standard_id": src_id,
                "target_standard_id": tgt_id,
                "source_is": src,
                "target_is": tgt,
                "relation": "NORMATIVE_REF",
                "clause": clause or "Clause 2 Normative References",
                "description": desc
            })

    # Read seed CSV edges
    if os.path.exists(NORMATIVE_CSV):
        with open(NORMATIVE_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rel = row.get("relation", "")
                if rel in ["NORMATIVE_REF", "TESTED_BY"]:
                    process_edge(row["source"], row["target"], rel, "Clause 2", row.get("description", ""))

    # Read harvested JSONL edges
    if os.path.exists(NORMATIVE_JSONL):
        with open(NORMATIVE_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)
                        process_edge(
                            item["source"],
                            item["target"],
                            item.get("relation", "NORMATIVE_REF"),
                            item.get("clause", "Clause 2"),
                            item.get("description", "")
                        )
                    except Exception:
                        continue

    # Deduplicate edges
    normative_deduped = []
    seen_norm = set()
    for e in normative_edges:
        key = (e["source_standard_id"], e["target_standard_id"])
        if key not in seen_norm:
            seen_norm.add(key)
            normative_deduped.append(e)

    tested_deduped = []
    seen_test = set()
    for e in tested_edges:
        key = (e["source_standard_id"], e["target_test_standard_id"])
        if key not in seen_test:
            seen_test.add(key)
            tested_deduped.append(e)

    mandated_deduped = []
    seen_mand = set()
    for e in mandated_edges:
        key = (e["source_standard_id"], e["target_qco_id"])
        if key not in seen_mand:
            seen_mand.add(key)
            mandated_deduped.append(e)

    # 4. Write CSV files
    # A. nodes_standards.csv
    with open(os.path.join(OUTPUT_DIR, "nodes_standards.csv"), "w", encoding="utf-8", newline="") as f:
        fields = ["standard_id", "is_number", "title", "year", "department", "committee", "status", "amendments_count", "ics_code", "gazette_date"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(standards_map.values())

    # B. nodes_qco.csv
    with open(os.path.join(OUTPUT_DIR, "nodes_qco.csv"), "w", encoding="utf-8", newline="") as f:
        fields = ["qco_id", "order_name", "gazette_no", "order_date", "effective_date", "mandatory_scheme", "ministry_id", "penal_clause"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(qco_map.values())

    # C. nodes_ministries.csv
    with open(os.path.join(OUTPUT_DIR, "nodes_ministries.csv"), "w", encoding="utf-8", newline="") as f:
        fields = ["ministry_id", "name"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(ministry_map.values())

    # D. edges_normative_ref.csv
    with open(os.path.join(OUTPUT_DIR, "edges_normative_ref.csv"), "w", encoding="utf-8", newline="") as f:
        fields = ["source_standard_id", "target_standard_id", "source_is", "target_is", "relation", "clause", "description"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(normative_deduped)

    # E. edges_tested_by.csv
    with open(os.path.join(OUTPUT_DIR, "edges_tested_by.csv"), "w", encoding="utf-8", newline="") as f:
        fields = ["source_standard_id", "target_test_standard_id", "source_is", "target_is", "relation", "clause", "description"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(tested_deduped)

    # F. edges_mandated_by.csv
    with open(os.path.join(OUTPUT_DIR, "edges_mandated_by.csv"), "w", encoding="utf-8", newline="") as f:
        fields = ["source_standard_id", "is_number", "target_qco_id", "relation", "description"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(mandated_deduped)

    # G. graph_summary.json
    summary = {
        "nodes": {
            "standards_count": len(standards_map),
            "qco_orders_count": len(qco_map),
            "ministries_count": len(ministry_map)
        },
        "edges": {
            "normative_ref_count": len(normative_deduped),
            "tested_by_count": len(tested_deduped),
            "mandated_by_count": len(mandated_deduped),
            "total_edges": len(normative_deduped) + len(tested_deduped) + len(mandated_deduped)
        },
        "export_directory": OUTPUT_DIR
    }
    with open(os.path.join(OUTPUT_DIR, "graph_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nCanonical Graph Export Complete!")
    print(f"  Nodes: Standards: {summary['nodes']['standards_count']} | QCOs: {summary['nodes']['qco_orders_count']} | Ministries: {summary['nodes']['ministries_count']}")
    print(f"  Edges: NORMATIVE_REF: {summary['edges']['normative_ref_count']} | TESTED_BY: {summary['edges']['tested_by_count']} | MANDATED_BY: {summary['edges']['mandated_by_count']}")
    print(f"  Total graph relationships: {summary['edges']['total_edges']}")
    return summary

if __name__ == "__main__":
    run_export()
