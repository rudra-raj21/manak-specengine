#!/usr/bin/env python3
"""
Scrapes official Compulsory Registration Scheme (CRS) products from BIS portal (crsbis.in).
"""
import urllib.request
import re
import json
import os

def fetch_crs_products():
    url = "https://www.crsbis.in/BIS/products.do"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Error fetching from crsbis.in: {e}")
        return []

    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
    products = []
    for r in rows:
        cols = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL | re.IGNORECASE)]
        if len(cols) >= 4 and cols[0].isdigit():
            is_no_raw = cols[2].replace('*', '').strip()
            products.append({
                "sl_no": int(cols[0]),
                "product_name": cols[1],
                "is_number": is_no_raw,
                "implementation_date": cols[3],
                "scheme": "Scheme-II (CRS)",
                "ministry": "Ministry of Electronics and Information Technology (MeitY)"
            })
    return products

if __name__ == "__main__":
    items = fetch_crs_products()
    os.makedirs("data", exist_ok=True)
    out_path = "data/scraped_crs_products.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(items)} official CRS products to {out_path}")
