"""
Fetch 7-day reverse repo injection amount (亿元) from PBoC open market bulletins.

- Crawls the bulletin list pages (index + paged html)
- Opens each bulletin detail page
- Extracts:
    date (yyyy-mm-dd)
    rr7_injection_yi (float, 亿元)
    url (bulletin url)
    title (optional)
- Saves CSV

Usage:
  python src/fetch_rr7_injection.py \
    --start 20260101 \
    --end 20260131 \
    --out data/raw/rr7_202601.csv
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional, List, Dict

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE = "https://www.pbc.gov.cn"
INDEX_URL = f"{BASE}/zhengcehuobisi/125207/125213/125431/125475/index.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def req(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def parse_date_from_text(text: str) -> Optional[pd.Timestamp]:
    """
    Many PBoC pages contain date like:
      2026-02-14
    or:
      2026-02-14 09:20:30
    We'll take the first yyyy-mm-dd.
    """
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if not m:
        return None
    return pd.Timestamp(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")


def parse_rr7_injection_yi(text: str) -> Optional[float]:
    """
    Match pattern like:
      开展了3586亿元7天期逆回购操作
      开展了 3,586 亿元 7天期逆回购操作
    """
    t = text.replace(",", "")
    m = re.search(r"开展了\s*(\d+(\.\d+)?)\s*亿元\s*7天期逆回购", t)
    if m:
        return float(m.group(1))
    return None


def collect_bulletin_links(index_html: str) -> List[str]:
    """
    Extract bulletin detail links from a list page.
    """
    soup = BeautifulSoup(index_html, "lxml")
    links = []
    for a in soup.select("a"):
        href = a.get("href") or ""
        if "/125475/" in href and href.endswith("/index.html"):
            if href.startswith("http"):
                links.append(href)
            else:
                links.append(BASE + href)

    # dedup preserve order
    out, seen = [], set()
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def next_page_url(index_html: str) -> Optional[str]:
    """
    Your site uses:
      <a onclick="queryArticleByCondition(this,'/....../17081-3.html')">下一页</a>
    Sometimes there is no href.
    We'll parse onclick to get the next page path.
    """
    soup = BeautifulSoup(index_html, "lxml")

    a = soup.find("a", string=lambda s: s and "下一页" in s)
    if not a:
        return None

    # 1) Try href first (if exists)
    href = a.get("href")
    if href:
        return href if href.startswith("http") else (BASE + href)

    # 2) Parse onclick queryArticleByCondition(this,'/path/to/17081-3.html')
    onclick = a.get("onclick") or ""
    m = re.search(r"queryArticleByCondition\s*\(\s*this\s*,\s*'([^']+)'\s*\)", onclick)
    if not m:
        m = re.search(r'queryArticleByCondition\s*\(\s*this\s*,\s*"([^"]+)"\s*\)', onclick)

    if not m:
        return None

    path = m.group(1)
    return path if path.startswith("http") else (BASE + path)


def get_title(soup: BeautifulSoup) -> str:
    h2 = soup.find("h2")
    if h2:
        return clean(h2.get_text())
    if soup.title:
        return clean(soup.title.get_text())
    return ""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, help="YYYYMMDD")
    p.add_argument("--end", required=True, help="YYYYMMDD")
    p.add_argument("--out", required=True, help="output csv path")
    p.add_argument("--max-pages", type=int, default=50, help="max list pages to crawl")
    args = p.parse_args()

    start = pd.to_datetime(args.start, format="%Y%m%d")
    end = pd.to_datetime(args.end, format="%Y%m%d")

    # 1) Crawl list pages and collect bulletin URLs
    all_bulletins: List[str] = []
    seen_list_pages = set()

    page_url = INDEX_URL
    for _ in range(args.max_pages):
        if page_url in seen_list_pages:
            break
        seen_list_pages.add(page_url)

        html = req(page_url)
        all_bulletins.extend(collect_bulletin_links(html))

        nxt = next_page_url(html)
        if not nxt:
            break
        page_url = nxt

    # dedup bulletins
    bulletins, seen_b = [], set()
    for u in all_bulletins:
        if u not in seen_b:
            seen_b.add(u)
            bulletins.append(u)

    # 2) Open each bulletin and parse rr7 injection
    rows: List[Dict] = []

    for u in bulletins:
        try:
            html = req(u)
        except Exception:
            continue

        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)

        dt = parse_date_from_text(text)
        if dt is None:
            continue
        if not (start <= dt <= end):
            continue

        amt = parse_rr7_injection_yi(text)
        if amt is None:
            continue

        rows.append(
            {
                "date": dt.date().isoformat(),
                "rr7_injection_yi": amt,
                "title": get_title(soup),
                "url": u,
            }
        )

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"[OK] saved {len(df)} rows -> {out_path}")
    if len(df) > 0:
        print(df.tail(10).to_string(index=False))
    else:
        print("No rows found. (Maybe no 7D reverse repo injections in this range, or pattern mismatch.)")


if __name__ == "__main__":
    main()