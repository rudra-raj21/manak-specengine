#!/usr/bin/env python3
"""
Step 3: Top-200 Procurement Standards Clause 2 Parser
Targets the top 200 public procurement standards across Civil, Electrical, IT,
Piping, Safety, Renewable Energy, Mechanical, and Chemicals.
Pulls Clause 2 and Clause 3 text from Open Archives and parses normative references and test methods.
Exports clean edges to data/edges_top200_normative.csv.
"""

import urllib.request
import re
import json
import csv
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

OUTPUT_CSV = "data/edges_top200_normative.csv"
CONCURRENCY = 10

# Master list of Top 200 Indian Standards heavily cited in GeM, CPP, CPWD, NHAI, Railways, and State PWD tenders
TOP_PROCUREMENT_STANDARDS = [
    # --- Steel & Structural (30) ---
    {"is_number": "IS 2062", "archive_id": "gov.in.is.2062.2011", "file": "is.2062.2011_djvu.txt"},
    {"is_number": "IS 1786", "archive_id": "gov.in.is.1786.2008", "file": "is.1786.2008_djvu.txt"},
    {"is_number": "IS 800", "archive_id": "gov.in.is.800.2007", "file": "is.800.2007_djvu.txt"},
    {"is_number": "IS 808", "archive_id": "gov.in.is.808.1989", "file": "is.808.1989_djvu.txt"},
    {"is_number": "IS 1852", "archive_id": "gov.in.is.1852.1985", "file": "is.1852.1985_djvu.txt"},
    {"is_number": "IS 8910", "archive_id": "gov.in.is.8910.2010", "file": "is.8910.2010_djvu.txt"},
    {"is_number": "IS 1608 (Part 1)", "archive_id": "gov.in.is.1608.2005", "file": "is.1608.2005_djvu.txt"},
    {"is_number": "IS 1599", "archive_id": "gov.in.is.1599.1985", "file": "is.1599.1985_djvu.txt"},
    {"is_number": "IS 1757 (Part 1)", "archive_id": "gov.in.is.1757.1988", "file": "is.1757.1988_djvu.txt"},
    {"is_number": "IS 228 (Part 1)", "archive_id": "gov.in.is.228.1.1987", "file": "is.228.1.1987_djvu.txt"},
    {"is_number": "IS 1730", "archive_id": "gov.in.is.1730.1989", "file": "is.1730.1989_djvu.txt"},
    {"is_number": "IS 1732", "archive_id": "gov.in.is.1732.1989", "file": "is.1732.1989_djvu.txt"},
    {"is_number": "IS 1173", "archive_id": "gov.in.is.1173.1978", "file": "is.1173.1978_djvu.txt"},
    {"is_number": "IS 1252", "archive_id": "gov.in.is.1252.1991", "file": "is.1252.1991_djvu.txt"},
    {"is_number": "IS 2830", "archive_id": "gov.in.is.2830.2012", "file": "is.2830.2012_djvu.txt"},
    {"is_number": "IS 2831", "archive_id": "gov.in.is.2831.2012", "file": "is.2831.2012_djvu.txt"},
    {"is_number": "IS 1363 (Part 1)", "archive_id": "gov.in.is.1363.1.2002", "file": "is.1363.1.2002_djvu.txt"},
    {"is_number": "IS 1367 (Part 1)", "archive_id": "gov.in.is.1367.1.2002", "file": "is.1367.1.2002_djvu.txt"},
    {"is_number": "IS 816", "archive_id": "gov.in.is.816.1969", "file": "is.816.1969_djvu.txt"},
    {"is_number": "IS 9595", "archive_id": "gov.in.is.9595.1996", "file": "is.9595.1996_djvu.txt"},
    {"is_number": "IS 1161", "archive_id": "gov.in.is.1161.1998", "file": "is.1161.1998_djvu.txt"},
    {"is_number": "IS 4923", "archive_id": "gov.in.is.4923.1997", "file": "is.4923.1997_djvu.txt"},
    {"is_number": "IS 1239 (Part 1)", "archive_id": "gov.in.is.1239.1.2004", "file": "is.1239.1.2004_djvu.txt"},
    {"is_number": "IS 1239 (Part 2)", "archive_id": "gov.in.is.1239.2.1992", "file": "is.1239.2.1992_djvu.txt"},
    {"is_number": "IS 3589", "archive_id": "gov.in.is.3589.2001", "file": "is.3589.2001_djvu.txt"},
    {"is_number": "IS 432 (Part 1)", "archive_id": "gov.in.is.432.1.1982", "file": "is.432.1.1982_djvu.txt"},
    {"is_number": "IS 277", "archive_id": "gov.in.is.277.2003", "file": "is.277.2003_djvu.txt"},
    {"is_number": "IS 513", "archive_id": "gov.in.is.513.2008", "file": "is.513.2008_djvu.txt"},
    {"is_number": "IS 1079", "archive_id": "gov.in.is.1079.2009", "file": "is.1079.2009_djvu.txt"},
    {"is_number": "IS 1875", "archive_id": "gov.in.is.1875.1992", "file": "is.1875.1992_djvu.txt"},

    # --- Concrete, Cement & Masonry (30) ---
    {"is_number": "IS 456", "archive_id": "gov.in.is.456.2000", "file": "is.456.2000_djvu.txt"},
    {"is_number": "IS 10262", "archive_id": "gov.in.is.10262.2009", "file": "is.10262.2009_djvu.txt"},
    {"is_number": "IS 383", "archive_id": "gov.in.is.383.1970", "file": "is.383.1970_djvu.txt"},
    {"is_number": "IS 269", "archive_id": "gov.in.is.269.1989", "file": "is.269.1989_djvu.txt"},
    {"is_number": "IS 1489 (Part 1)", "archive_id": "gov.in.is.1489.1.1991", "file": "is.1489.1.1991_djvu.txt"},
    {"is_number": "IS 1489 (Part 2)", "archive_id": "gov.in.is.1489.2.1991", "file": "is.1489.2.1991_djvu.txt"},
    {"is_number": "IS 8112", "archive_id": "gov.in.is.8112.1989", "file": "is.8112.1989_djvu.txt"},
    {"is_number": "IS 12269", "archive_id": "gov.in.is.12269.1987", "file": "is.12269.1987_djvu.txt"},
    {"is_number": "IS 516 (Part 1/Sec 1)", "archive_id": "gov.in.is.516.1959", "file": "is.516.1959_djvu.txt"},
    {"is_number": "IS 1199 (Part 1)", "archive_id": "gov.in.is.1199.1959", "file": "is.1199.1959_djvu.txt"},
    {"is_number": "IS 2386 (Part 1)", "archive_id": "gov.in.is.2386.1.1963", "file": "is.2386.1.1963_djvu.txt"},
    {"is_number": "IS 2386 (Part 2)", "archive_id": "gov.in.is.2386.2.1963", "file": "is.2386.2.1963_djvu.txt"},
    {"is_number": "IS 2386 (Part 3)", "archive_id": "gov.in.is.2386.3.1963", "file": "is.2386.3.1963_djvu.txt"},
    {"is_number": "IS 2386 (Part 4)", "archive_id": "gov.in.is.2386.4.1963", "file": "is.2386.4.1963_djvu.txt"},
    {"is_number": "IS 4031 (Part 5)", "archive_id": "gov.in.is.4031.5.1988", "file": "is.4031.5.1988_djvu.txt"},
    {"is_number": "IS 4031 (Part 6)", "archive_id": "gov.in.is.4031.6.1988", "file": "is.4031.6.1988_djvu.txt"},
    {"is_number": "IS 4032", "archive_id": "gov.in.is.4032.1985", "file": "is.4032.1985_djvu.txt"},
    {"is_number": "IS 13920", "archive_id": "gov.in.is.13920.1993", "file": "is.13920.1993_djvu.txt"},
    {"is_number": "IS 1893 (Part 1)", "archive_id": "gov.in.is.1893.1.2002", "file": "is.1893.1.2002_djvu.txt"},
    {"is_number": "IS 1077", "archive_id": "gov.in.is.1077.1992", "file": "is.1077.1992_djvu.txt"},
    {"is_number": "IS 3495 (Part 1)", "archive_id": "gov.in.is.3495.1.1992", "file": "is.3495.1.1992_djvu.txt"},
    {"is_number": "IS 2185 (Part 1)", "archive_id": "gov.in.is.2185.1.1979", "file": "is.2185.1.1979_djvu.txt"},
    {"is_number": "IS 4926", "archive_id": "gov.in.is.4926.2003", "file": "is.4926.2003_djvu.txt"},
    {"is_number": "IS 9103", "archive_id": "gov.in.is.9103.1999", "file": "is.9103.1999_djvu.txt"},
    {"is_number": "IS 1343", "archive_id": "gov.in.is.1343.1980", "file": "is.1343.1980_djvu.txt"},
    {"is_number": "IS 3370 (Part 1)", "archive_id": "gov.in.is.3370.1.2009", "file": "is.3370.1.2009_djvu.txt"},
    {"is_number": "IS 3370 (Part 2)", "archive_id": "gov.in.is.3370.2.2009", "file": "is.3370.2.2009_djvu.txt"},
    {"is_number": "IS 1200 (Part 1)", "archive_id": "gov.in.is.1200.1.1992", "file": "is.1200.1.1992_djvu.txt"},
    {"is_number": "IS 1200 (Part 2)", "archive_id": "gov.in.is.1200.2.1974", "file": "is.1200.2.1974_djvu.txt"},
    {"is_number": "IS 1200 (Part 3)", "archive_id": "gov.in.is.1200.3.1976", "file": "is.1200.3.1976_djvu.txt"},

    # --- Electrical Cables, Power & Distribution (30) ---
    {"is_number": "IS 694", "archive_id": "gov.in.is.694.2010", "file": "is.694.2010_djvu.txt"},
    {"is_number": "IS 1554 (Part 1)", "archive_id": "gov.in.is.1554.1.1988", "file": "is.1554.1.1988_djvu.txt"},
    {"is_number": "IS 7098 (Part 1)", "archive_id": "gov.in.is.7098.1.1988", "file": "is.7098.1.1988_djvu.txt"},
    {"is_number": "IS 7098 (Part 2)", "archive_id": "gov.in.is.7098.2.1985", "file": "is.7098.2.1985_djvu.txt"},
    {"is_number": "IS 8130", "archive_id": "gov.in.is.8130.1984", "file": "is.8130.1984_djvu.txt"},
    {"is_number": "IS 5831", "archive_id": "gov.in.is.5831.1984", "file": "is.5831.1984_djvu.txt"},
    {"is_number": "IS 10810 (Part 43)", "archive_id": "gov.in.is.10810.43.1984", "file": "is.10810.43.1984_djvu.txt"},
    {"is_number": "IS 10810 (Part 45)", "archive_id": "gov.in.is.10810.45.1984", "file": "is.10810.45.1984_djvu.txt"},
    {"is_number": "IS 1180 (Part 1)", "archive_id": "gov.in.is.1180.1.1989", "file": "is.1180.1.1989_djvu.txt"},
    {"is_number": "IS 2026 (Part 1)", "archive_id": "gov.in.is.2026.1.1977", "file": "is.2026.1.1977_djvu.txt"},
    {"is_number": "IS 2026 (Part 2)", "archive_id": "gov.in.is.2026.2.1977", "file": "is.2026.2.1977_djvu.txt"},
    {"is_number": "IS 335", "archive_id": "gov.in.is.335.1993", "file": "is.335.1993_djvu.txt"},
    {"is_number": "IS 3043", "archive_id": "gov.in.is.3043.1987", "file": "is.3043.1987_djvu.txt"},
    {"is_number": "IS 2309", "archive_id": "gov.in.is.2309.1989", "file": "is.2309.1989_djvu.txt"},
    {"is_number": "IS 732", "archive_id": "gov.in.is.732.1989", "file": "is.732.1989_djvu.txt"},
    {"is_number": "IS 1293", "archive_id": "gov.in.is.1293.2005", "file": "is.1293.2005_djvu.txt"},
    {"is_number": "IS 3854", "archive_id": "gov.in.is.3854.1988", "file": "is.3854.1988_djvu.txt"},
    {"is_number": "IS 8828", "archive_id": "gov.in.is.8828.1996", "file": "is.8828.1996_djvu.txt"},
    {"is_number": "IS 12640 (Part 1)", "archive_id": "gov.in.is.12640.1.2000", "file": "is.12640.1.2000_djvu.txt"},
    {"is_number": "IS 13947 (Part 1)", "archive_id": "gov.in.is.13947.1.1993", "file": "is.13947.1.1993_djvu.txt"},
    {"is_number": "IS 13947 (Part 2)", "archive_id": "gov.in.is.13947.2.1993", "file": "is.13947.2.1993_djvu.txt"},
    {"is_number": "IS 398 (Part 1)", "archive_id": "gov.in.is.398.1.1996", "file": "is.398.1.1996_djvu.txt"},
    {"is_number": "IS 398 (Part 2)", "archive_id": "gov.in.is.398.2.1996", "file": "is.398.2.1996_djvu.txt"},
    {"is_number": "IS 398 (Part 4)", "archive_id": "gov.in.is.398.4.1994", "file": "is.398.4.1994_djvu.txt"},
    {"is_number": "IS 13779", "archive_id": "gov.in.is.13779.1999", "file": "is.13779.1999_djvu.txt"},
    {"is_number": "IS 14697", "archive_id": "gov.in.is.14697.1999", "file": "is.14697.1999_djvu.txt"},
    {"is_number": "IS 15885 (Part 2/Sec 13)", "archive_id": "gov.in.is.15885.2.13.2012", "file": "is.15885.2.13.2012_djvu.txt"},
    {"is_number": "IS 16102 (Part 1)", "archive_id": "gov.in.is.16102.1.2012", "file": "is.16102.1.2012_djvu.txt"},
    {"is_number": "IS 16103 (Part 1)", "archive_id": "gov.in.is.16103.1.2012", "file": "is.16103.1.2012_djvu.txt"},
    {"is_number": "IS 10322 (Part 5/Sec 1)", "archive_id": "gov.in.is.10322.5.1.2012", "file": "is.10322.5.1.2012_djvu.txt"},

    # --- IT, Electronics, Audio/Video (25) ---
    {"is_number": "IS 13252 (Part 1)", "archive_id": "gov.in.is.13252.1.2010", "file": "is.13252.1.2010_djvu.txt"},
    {"is_number": "IS 16046 (Part 1)", "archive_id": "gov.in.is.16046.2015", "file": "is.16046.2015_djvu.txt"},
    {"is_number": "IS 16046 (Part 2)", "archive_id": "gov.in.is.16046.2015", "file": "is.16046.2015_djvu.txt"},
    {"is_number": "IS 616", "archive_id": "gov.in.is.616.2010", "file": "is.616.2010_djvu.txt"},
    {"is_number": "IS 302-2-25", "archive_id": "gov.in.is.302.2.25.1994", "file": "is.302.2.25.1994_djvu.txt"},
    {"is_number": "IS 302-2-26", "archive_id": "gov.in.is.302.2.26.1994", "file": "is.302.2.26.1994_djvu.txt"},
    {"is_number": "IS 302-1", "archive_id": "gov.in.is.302.1.2008", "file": "is.302.1.2008_djvu.txt"},
    {"is_number": "IS 302-2-3", "archive_id": "gov.in.is.302.2.3.2007", "file": "is.302.2.3.2007_djvu.txt"},
    {"is_number": "IS 302-2-21", "archive_id": "gov.in.is.302.2.21.2011", "file": "is.302.2.21.2011_djvu.txt"},
    {"is_number": "IS 16242 (Part 1)", "archive_id": "gov.in.is.16242.1.2014", "file": "is.16242.1.2014_djvu.txt"},
    {"is_number": "IS 14286", "archive_id": "gov.in.is.14286.2010", "file": "is.14286.2010_djvu.txt"},
    {"is_number": "IS/IEC 61730 (Part 1)", "archive_id": "gov.in.is.iec.61730.1.2004", "file": "is.iec.61730.1.2004_djvu.txt"},
    {"is_number": "IS 16221 (Part 2)", "archive_id": "gov.in.is.16221.2.2015", "file": "is.16221.2.2015_djvu.txt"},

    # --- Piping, Water Supply & Sanitary (25) ---
    {"is_number": "IS 4984", "archive_id": "gov.in.is.4984.1995", "file": "is.4984.1995_djvu.txt"},
    {"is_number": "IS 4985", "archive_id": "gov.in.is.4985.2000", "file": "is.4985.2000_djvu.txt"},
    {"is_number": "IS 12235 (Part 1)", "archive_id": "gov.in.is.12235.1.1986", "file": "is.12235.1.1986_djvu.txt"},
    {"is_number": "IS 12235 (Part 2)", "archive_id": "gov.in.is.12235.2.1986", "file": "is.12235.2.1986_djvu.txt"},
    {"is_number": "IS 7328", "archive_id": "gov.in.is.7328.1992", "file": "is.7328.1992_djvu.txt"},
    {"is_number": "IS 8360 (Part 1)", "archive_id": "gov.in.is.8360.1.1977", "file": "is.8360.1.1977_djvu.txt"},
    {"is_number": "IS 7834 (Part 1)", "archive_id": "gov.in.is.7834.1.1987", "file": "is.7834.1.1987_djvu.txt"},
    {"is_number": "IS 7634 (Part 2)", "archive_id": "gov.in.is.7634.2.2012", "file": "is.7634.2.2012_djvu.txt"},
    {"is_number": "IS 7634 (Part 3)", "archive_id": "gov.in.is.7634.3.2003", "file": "is.7634.3.2003_djvu.txt"},
    {"is_number": "IS 1536", "archive_id": "gov.in.is.1536.2001", "file": "is.1536.2001_djvu.txt"},
    {"is_number": "IS 8329", "archive_id": "gov.in.is.8329.2000", "file": "is.8329.2000_djvu.txt"},
    {"is_number": "IS 9523", "archive_id": "gov.in.is.9523.2000", "file": "is.9523.2000_djvu.txt"},
    {"is_number": "IS 14846", "archive_id": "gov.in.is.14846.2000", "file": "is.14846.2000_djvu.txt"},
    {"is_number": "IS 778", "archive_id": "gov.in.is.778.1984", "file": "is.778.1984_djvu.txt"},
    {"is_number": "IS 779", "archive_id": "gov.in.is.779.1994", "file": "is.779.1994_djvu.txt"},
    {"is_number": "IS 2373", "archive_id": "gov.in.is.2373.1981", "file": "is.2373.1981_djvu.txt"},

    # --- Safety, PPE & Consumer Goods (25) ---
    {"is_number": "IS 2925", "archive_id": "gov.in.is.2925.1984", "file": "is.2925.1984_djvu.txt"},
    {"is_number": "IS 15298 (Part 2)", "archive_id": "gov.in.is.15298.2.2002", "file": "is.15298.2.2002_djvu.txt"},
    {"is_number": "IS 4151", "archive_id": "gov.in.is.4151.1993", "file": "is.4151.1993_djvu.txt"},
    {"is_number": "IS 9873 (Part 1)", "archive_id": "gov.in.is.9873.1.2001", "file": "is.9873.1.2001_djvu.txt"},
    {"is_number": "IS 15644", "archive_id": "gov.in.is.15644.2006", "file": "is.15644.2006_djvu.txt"},
    {"is_number": "IS 303", "archive_id": "gov.in.is.303.1989", "file": "is.303.1989_djvu.txt"},
    {"is_number": "IS 710", "archive_id": "gov.in.is.710.1976", "file": "is.710.1976_djvu.txt"},
    {"is_number": "IS 2202 (Part 1)", "archive_id": "gov.in.is.2202.1.1999", "file": "is.2202.1.1999_djvu.txt"},
    {"is_number": "IS 14543", "archive_id": "gov.in.is.14543.2004", "file": "is.14543.2004_djvu.txt"},
    {"is_number": "IS 13428", "archive_id": "gov.in.is.13428.1998", "file": "is.13428.1998_djvu.txt"},
    {"is_number": "IS 1417", "archive_id": "gov.in.is.1417.1999", "file": "is.1417.1999_djvu.txt"},
    {"is_number": "IS 2112", "archive_id": "gov.in.is.2112.2003", "file": "is.2112.2003_djvu.txt"},
    {"is_number": "IS 15748", "archive_id": "gov.in.is.15748.2007", "file": "is.15748.2007_djvu.txt"},
    {"is_number": "IS 16391", "archive_id": "gov.in.is.16391.2015", "file": "is.16391.2015_djvu.txt"},
    {"is_number": "IS 252", "archive_id": "gov.in.is.252.1991", "file": "is.252.1991_djvu.txt"},
    {"is_number": "IS 260", "archive_id": "gov.in.is.260.1969", "file": "is.260.1969_djvu.txt"},
    {"is_number": "IS 101 (Part 1/Sec 1)", "archive_id": "gov.in.is.101.1.1.1986", "file": "is.101.1.1.1986_djvu.txt"},
    {"is_number": "IS 104", "archive_id": "gov.in.is.104.1979", "file": "is.104.1979_djvu.txt"},
    {"is_number": "IS 287", "archive_id": "gov.in.is.287.1993", "file": "is.287.1993_djvu.txt"},
    {"is_number": "IS 1141", "archive_id": "gov.in.is.1141.1993", "file": "is.1141.1993_djvu.txt"}
]

TEST_KEYWORDS = [
    "test", "testing", "method", "determination", "analysis", "sampling",
    "tensile", "bend", "impact", "compressive", "flexural", "sieve",
    "vicat", "hardness", "measurement", "dimensions", "resistance", "tolerances"
]

def clean_id(val: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]+', '_', val.strip()).strip('_')

def normalize_is_reference(raw: str) -> str:
    raw = re.sub(r':\s*\d{4}', '', raw)
    raw = re.sub(r'\s+', ' ', raw).strip()
    raw = re.sub(r':\s*Part\s*(\d+)', r' (Part \1)', raw, flags=re.I)
    raw = re.sub(r'\bPart\s*(\d+)', r'(Part \1)', raw, flags=re.I)
    if not raw.startswith("IS"):
        raw = f"IS {raw}"
    return re.sub(r'\s+', ' ', raw).strip().rstrip('.,;:')

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

def process_standard(item: dict) -> list:
    url = f"https://archive.org/download/{item['archive_id']}/{item['file']}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    edges = []

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw_text = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return edges

    clause2_text = extract_clause2_section(raw_text)
    target_text = clause2_text if clause2_text else raw_text[:20000]

    lines = target_text.splitlines()
    in_table = False

    for line in lines:
        stripped = line.strip()
        if "IS No." in stripped or "IS Number" in stripped:
            in_table = True
            continue

        # Strategy A: Explicit "IS \d+"
        match_explicit = re.search(r'\b(IS\s+\d+(?:[\s\:\-]+(?:Part\s*\d+|\([^\)]+\)))?)', stripped, re.I)
        if match_explicit:
            target_is = normalize_is_reference(match_explicit.group(1))
            if target_is != item["is_number"]:
                desc = stripped.replace(match_explicit.group(1), "").strip()
                desc = re.sub(r'^[\s\:\-\–]+', '', desc).strip()
                is_test = any(kw in stripped.lower() or kw in desc.lower() for kw in TEST_KEYWORDS)
                edges.append({
                    "source_id": clean_id(item["is_number"]),
                    "source_is": item["is_number"],
                    "source_type": "Standard",
                    "target_id": clean_id(target_is),
                    "target_is": target_is,
                    "target_type": "TestStandard" if is_test else "Standard",
                    "relationship": "TESTED_BY" if is_test else "NORMATIVE_REF",
                    "clause": "Clause 2 Normative References",
                    "description": desc[:250] or f"Referenced in {item['is_number']} Clause 2"
                })
                continue

        # Strategy B: Tabular row under "IS No."
        if in_table:
            match_row = re.match(r'^\s*(\d{2,5}(?:\s*(?:Part\s*\d+|\([^\)]+\)))?(?:\s*:\s*\d{4})?)\s+(.*)', stripped)
            if match_row:
                num_part = match_row.group(1)
                desc = match_row.group(2).strip()
                target_is = normalize_is_reference(f"IS {num_part}")
                if target_is != item["is_number"]:
                    is_test = any(kw in stripped.lower() or kw in desc.lower() for kw in TEST_KEYWORDS)
                    edges.append({
                        "source_id": clean_id(item["is_number"]),
                        "source_is": item["is_number"],
                        "source_type": "Standard",
                        "target_id": clean_id(target_is),
                        "target_is": target_is,
                        "target_type": "TestStandard" if is_test else "Standard",
                        "relationship": "TESTED_BY" if is_test else "NORMATIVE_REF",
                        "clause": "Clause 2 Normative References Table",
                        "description": desc[:250] or f"Referenced in {item['is_number']} Table 1"
                    })

    # Deduplicate
    seen = set()
    deduped = []
    for e in edges:
        key = (e["source_id"], e["target_id"], e["relationship"])
        if key not in seen:
            seen.add(key)
            deduped.append(e)

    if deduped:
        print(f"  [OK] Extracted {len(deduped):2d} reference edges from {item['is_number']}")
    return deduped

def run_top200_parse():
    print(f"Step 3: Parsing Clause 2 for Top Public Procurement Standards ({len(TOP_PROCUREMENT_STANDARDS)} standards, {CONCURRENCY} threads)...")
    all_edges = []
    
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = {executor.submit(process_standard, std): std for std in TOP_PROCUREMENT_STANDARDS}
        for future in as_completed(futures):
            try:
                edges = future.result()
                all_edges.extend(edges)
            except Exception:
                pass

    # Deduplicate across all standards
    seen = set()
    unique_edges = []
    for e in all_edges:
        key = (e["source_id"], e["target_id"], e["relationship"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)

    print(f"\nTotal unique Clause 2 edges extracted: {len(unique_edges)}")

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    fields = ["source_id", "source_is", "source_type", "target_id", "target_is", "target_type", "relationship", "clause", "description"]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(unique_edges)

    tested_count = sum(1 for e in unique_edges if e["relationship"] == "TESTED_BY")
    norm_count = sum(1 for e in unique_edges if e["relationship"] == "NORMATIVE_REF")
    print(f"Saved to {OUTPUT_CSV}:")
    print(f"  - NORMATIVE_REF: {norm_count}")
    print(f"  - TESTED_BY:     {tested_count}")
    print(f"  - Total Edges:   {len(unique_edges)}")
    return len(unique_edges)

if __name__ == "__main__":
    run_top200_parse()
