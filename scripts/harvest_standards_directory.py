#!/usr/bin/env python3
"""
Pipeline 1: Exhaustive Standards Directory Harvester
Targets Archive.org's Open Government Standards Collection (identifier:gov.in.is.*, 22,000+ standards).
Features:
- Cursor-based paginated streaming (batches of 1000).
- Rotating User-Agents and exponential backoff retry.
- Structured rate-limiting (0.2s - 0.5s delay).
- State persistence via data/harvest_checkpoints/standards_progress.json.
- Streams standardized JSON Lines directly into data/exhaustive_standards.jsonl.
"""

import urllib.request
import urllib.parse
import json
import os
import re
import time
import random
import sys

CHECKPOINT_PATH = "data/harvest_checkpoints/standards_progress.json"
OUTPUT_JSONL = "data/exhaustive_standards.jsonl"
BATCH_SIZE = 1000
RATE_LIMIT_DELAY = 0.35  # seconds

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "ManakSpecEngine-HarvestBot/2.0 (GovTech; OpenStandardsCrawler; +https://bis.gov.in)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0"
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }

def parse_standard_record(doc: dict) -> dict:
    """Extracts canonical attributes from Archive.org standard document metadata."""
    desc = doc.get("description", "") or ""
    title = doc.get("title", "") or ""
    identifier = doc.get("identifier", "")

    # Extract Division Name
    div_match = re.search(r"Division Name:\s*([^\n\r]+?)(?=\s*Section Name:|$)", desc, re.I)
    division = div_match.group(1).strip() if div_match else "General"

    # Extract Section Name / Committee
    sec_match = re.search(r"Section Name:\s*([^\n\r]+?)(?=\s*Designator of Legally|$)", desc, re.I)
    section = sec_match.group(1).strip() if sec_match else ""

    # Extract Committee Code (e.g. MTD 4, CED 54)
    comm_code_match = re.search(r"\(([A-Z]{2,4}\s*\d+)\)", section)
    committee = comm_code_match.group(1) if comm_code_match else section

    # Extract Designator (e.g. IS 2062)
    des_match = re.search(r"Designator of Legally Binding Document:\s*([^\n\r]+?)(?=\s*Title of Legally|$)", desc, re.I)
    raw_designator = des_match.group(1).strip() if des_match else ""
    if not raw_designator:
        t_match = re.match(r"(IS\s*[\d\.\-\(\)\s\:]+)", title)
        raw_designator = t_match.group(1).strip() if t_match else identifier.replace("gov.in.", "").upper()

    # Clean IS number (normalize spaces and hyphens)
    is_number = re.sub(r"\s+", " ", raw_designator).strip()
    if not is_number.startswith("IS"):
        is_number = f"IS {is_number}"

    # Extract Year
    year = doc.get("year")
    if not year or year == 0:
        y_match = re.search(r":\s*(\d{4})", title) or re.search(r"\b(19\d{2}|20\d{2})\b", identifier)
        year = int(y_match.group(1)) if y_match else None

    # Status detection
    status = "ACTIVE"
    if "WITHDRAWN" in desc.upper() or "WITHDRAWN" in title.upper():
        status = "WITHDRAWN"
    elif "SUPERCEDED" in desc.upper() or "SUPERSEDED" in desc.upper() or "SUPERSEDING" in desc.upper():
        status = "SUPERSEDED"

    # Extract amendments count
    amend_match = re.search(r"Number of Amendments:\s*(\d+)", desc)
    amendments = int(amend_match.group(1)) if amend_match else 0

    # Extract Superseded by / Superceding
    sup_by_match = re.search(r"Superceded by:\s*([^\n\r\.]+)", desc, re.I)
    superseded_by = sup_by_match.group(1).strip() if sup_by_match else ""
    if superseded_by.lower() in ["none", "", "decided by council"]:
        superseded_by = ""

    # ICS Code inference / extraction
    ics_match = re.search(r"ICS Code:\s*([\d\.]+)", desc, re.I)
    ics_code = ics_match.group(1) if ics_match else ""

    # Scope / Abstract snippet
    scope_text = ""
    if len(desc) > 300:
        scope_text = desc.split("LEGALLY BINDING DOCUMENT")[-1].strip()
        scope_text = re.sub(r"--[A-Za-z\s]+", "", scope_text).strip()
        if len(scope_text) < 20:
            scope_text = f"Indian Standard specification for {title} published by the Bureau of Indian Standards under division {division}."
    else:
        scope_text = f"Indian Standard specification for {title} published by the Bureau of Indian Standards."

    return {
        "identifier": identifier,
        "is_number": is_number,
        "title": title,
        "year": year,
        "department": division,
        "committee": committee,
        "status": status,
        "amendments_count": amendments,
        "superseded_by": superseded_by,
        "ics_code": ics_code,
        "gazette_date": doc.get("date"),
        "publicdate": doc.get("publicdate"),
        "scope": scope_text[:1200]
    }

def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "cursor": None,
        "total_harvested": 0,
        "batches_completed": 0,
        "is_complete": False,
        "last_batch_time": None
    }

def save_checkpoint(ckpt):
    os.makedirs(os.path.dirname(CHECKPOINT_PATH), exist_ok=True)
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, indent=2)

def fetch_batch_with_retry(cursor=None, retries=5):
    params = {
        "q": "identifier:gov.in.is.*",
        "fields": "identifier,title,description,year,date,publicdate,subject",
        "count": BATCH_SIZE
    }
    if cursor:
        params["cursor"] = cursor

    url = "https://archive.org/services/search/v1/scrape?" + urllib.parse.urlencode(params)
    
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers=get_random_headers())
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except Exception as e:
            delay = (2 ** attempt) + random.uniform(0.5, 1.5)
            print(f"  [Attempt {attempt}/{retries}] Error fetching cursor batch: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)
    raise RuntimeError(f"Failed to fetch batch after {retries} retries")

def run_harvest(max_records=None):
    os.makedirs("data", exist_ok=True)
    ckpt = load_checkpoint()
    
    if ckpt.get("is_complete") and not max_records:
        print(f"Standards directory harvest already complete! Total items: {ckpt['total_harvested']}.")
        return ckpt["total_harvested"]

    print(f"Starting/Resuming Standards Directory Harvest from checkpoint:")
    print(f"  Cursor: {ckpt['cursor'][:25] if ckpt['cursor'] else 'START'}")
    print(f"  Total already harvested: {ckpt['total_harvested']}")

    # Open output file in append mode
    file_mode = "a" if ckpt["total_harvested"] > 0 and os.path.exists(OUTPUT_JSONL) else "w"
    out_file = open(OUTPUT_JSONL, file_mode, encoding="utf-8")

    cursor = ckpt.get("cursor")
    total_harvested = ckpt.get("total_harvested", 0)
    batches = ckpt.get("batches_completed", 0)

    try:
        while True:
            t0 = time.time()
            data = fetch_batch_with_retry(cursor)
            items = data.get("items", [])
            total_in_query = data.get("total", 0)
            next_cursor = data.get("cursor")

            if not items:
                print("No more items returned by scraper. Harvesting completed!")
                ckpt["is_complete"] = True
                break

            for item in items:
                record = parse_standard_record(item)
                out_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_harvested += 1

                if max_records and total_harvested >= max_records:
                    break

            batches += 1
            batch_time = time.time() - t0
            print(f"Batch {batches:3d}: Ingested {len(items):4d} standards in {batch_time:.2f}s | Progress: {total_harvested}/{total_in_query}")

            cursor = next_cursor
            ckpt["cursor"] = cursor
            ckpt["total_harvested"] = total_harvested
            ckpt["batches_completed"] = batches
            ckpt["last_batch_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            save_checkpoint(ckpt)
            out_file.flush()

            if max_records and total_harvested >= max_records:
                print(f"Reached specified limit of {max_records} records.")
                break

            if not cursor:
                print("End of cursor stream reached.")
                ckpt["is_complete"] = True
                break

            time.sleep(RATE_LIMIT_DELAY)

    finally:
        out_file.close()
        save_checkpoint(ckpt)

    print(f"Pipeline 1 Finished. Total standards saved in {OUTPUT_JSONL}: {total_harvested}")
    return total_harvested

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_harvest(max_records=limit)
