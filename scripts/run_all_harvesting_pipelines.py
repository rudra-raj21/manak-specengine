#!/usr/bin/env python3
"""
Master Harvesting Orchestrator for Manak-SpecEngine
Executes and coordinates all 4 asynchronous, fault-tolerant ingestion pipelines:
1. Standards Directory Harvester (Archive.org & BIS catalog)
2. Mandatory Regulatory Matrix Harvester (100% QCOs & CRS Products)
3. Normative Reference Extraction Engine (Clause 2 & 3 Cascade)
4. Canonical Graph Exporter (Normalized CSVs & Graph Summary)
"""

import os
import sys
import time
import json
import subprocess

def log_header(title):
    print("\n" + "=" * 75)
    print(f"  {title.upper()}")
    print("=" * 75)

def run_pipeline(script_name, description, *args):
    log_header(f"Starting {description} ({script_name})")
    cmd = [sys.executable, f"scripts/{script_name}"] + list(args)
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=False)
    elapsed = time.time() - t0
    if res.returncode != 0:
        print(f"[ERROR] Pipeline {script_name} failed with exit code {res.returncode}")
        return False
    print(f"[SUCCESS] {description} finished in {elapsed:.2f}s")
    return True

def main():
    os.makedirs("data/harvest_checkpoints", exist_ok=True)
    os.makedirs("data/graph_export", exist_ok=True)

    start_time = time.time()
    print("=" * 75)
    print("  MANAK-SPECENGINE: LARGE-SCALE DATA HARVESTING ENGINE")
    print("=" * 75)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Pipeline 1: Standards Directory
    # We can pass an optional record target or let it run to complete the current batch
    run_pipeline("harvest_standards_directory.py", "Pipeline 1: Standards Directory Harvester")

    # Pipeline 2: Regulatory Matrix
    run_pipeline("harvest_regulatory_matrix.py", "Pipeline 2: Mandatory Regulatory Matrix Harvester")

    # Pipeline 3: Normative Cascade
    run_pipeline("harvest_normative_cascade.py", "Pipeline 3: Normative Reference Extraction Engine")

    # Pipeline 4: Canonical Graph Exporter
    run_pipeline("export_canonical_graph.py", "Pipeline 4: Canonical Graph Exporter")

    total_time = time.time() - start_time
    log_header("HARVEST SUMMARY & ASSET VERIFICATION")
    
    summary_path = "data/graph_export/graph_summary.json"
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
            print("Graph Assets Generated:")
            print(f"  - Standards Nodes:       {summary['nodes']['standards_count']}")
            print(f"  - QCO Order Nodes:       {summary['nodes']['qco_orders_count']}")
            print(f"  - Ministry Nodes:        {summary['nodes']['ministries_count']}")
            print(f"  - Normative Ref Edges:   {summary['edges']['normative_ref_count']}")
            print(f"  - Tested By Edges:       {summary['edges']['tested_by_count']}")
            print(f"  - Mandated By Edges:     {summary['edges']['mandated_by_count']}")
            print(f"  - Total Graph Edges:     {summary['edges']['total_edges']}")

    print(f"\nAll pipelines successfully executed in {total_time:.2f} seconds.")

if __name__ == "__main__":
    main()
