"""
Build daily 7-day reverse repo (RR007) injection / maturity / net injection table
with holiday/weekend roll to next China trading day.

Rule:
- Each RR7 injection on date D matures on D + 7 natural days.
- If maturity date is not a trading day, roll forward to the next trading day.

Output columns (trading days only):
  date, injection_yi, maturity_yi, net_yi

Requires:
  pip install requests beautifulsoup4 lxml pandas akshare
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Optional, List, Dict, Set

import pandas as pd
import requests
from bs4 import BeautifulSoup
import akshare as ak

BASE = "https://www.pbc.gov.cn"
INDEX_URL = f"{BASE}/zhengcehuobisi/125207/125213/125431/125475/index.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# -----------------------------
# HTTP + HTML helpers
# -----------------------------
def req(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def get_title(soup: BeautifulSoup) -> str:
    h2 = soup.find("h2")
    if h2:
        return clean(h2.get_text())
    if soup.title:
        return clean(soup.title.get_text())
    return ""


def collect_bulletin_links(index_html: str) -> List[str]:
    """
    From list page HTML, collect bulletin detail links ending with /index.html.
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

    # dedup keep order
    out, seen = [], set()
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def next_page_url(index_html: str) -> Optional[str]:
    """
    Handles:
      <a onclick="queryArticleByCondition(this,'/....../17081-3.html')">下一页</a>
    """
    soup = BeautifulSoup(index_html, "lxml")
    a = soup.find("a", string=lambda s: s and "下一页" in s)
    if not a:
        return None

    href = a.get("href")
    if href:
        return href if href.startswith("http") else (BASE + href)

    onclick = a.get("onclick") or ""
    m = re.search(r"queryArticleByCondition\s*\(\s*this\s*,\s*'([^']+)'\s*\)", onclick)
    if not m:
        m = re.search(r'queryArticleByCondition\s*\(\s*this\s*,\s*"([^"]+)"\s*\)', onclick)
    if not m:
        return None

    path = m.group(1)
    return path if path.startswith("http") else (BASE + path)


# -----------------------------
# Parsing: date + RR7 injection
# -----------------------------
def parse_date_from_text(text: str) -> Optional[pd.Timestamp]:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if not m:
        return None
    return pd.Timestamp(f"{m.group(1)}-{m.group(2)}-{m.group(3)}")


def parse_rr7_injection_yi(text: str) -> Optional[float]:
    """
    Common phrasing:
      开展了3586亿元7天期逆回购操作
    """
    t = text.replace(",", "")
    m = re.search(r"开展了\s*(\d+(\.\d+)?)\s*亿元\s*7天期逆回购", t)
    if m:
        return float(m.group(1))
    return None


# -----------------------------
# Trading calendar + rolling
# -----------------------------
def load_cn_trading_days(start: pd.Timestamp, end: pd.Timestamp) -> List[pd.Timestamp]:
    """
    Use akshare trade date histogram (Sina) as trading calendar.
    Returns list of pd.Timestamp sorted.
    """
    cal = ak.tool_trade_date_hist_sina()
    # ak returns DataFrame with a date column; common name is "trade_date"
    # but sometimes it's "trade_date" as datetime.
    cols = [c for c in cal.columns]
    # try best guess
    date_col = None
    for c in cols:
        if "trade" in c and "date" in c:
            date_col = c
            break
    if date_col is None:
        # fallback to first column
        date_col = cols[0]

    s = pd.to_datetime(cal[date_col])
    s = s[(s >= start) & (s <= end)].sort_values().drop_duplicates()
    return list(s)


def roll_to_next_trading_day(target: pd.Timestamp, trading_set: Set[pd.Timestamp]) -> pd.Timestamp:
    """
    If target is not a trading day, roll forward to next trading day.
    """
    d = target.normalize()
    # safety loop (should converge quickly)
    for _ in range(20):
        if d in trading_set:
            return d
        d = d + pd.Timedelta(days=1)
    # if still not found, return as-is (shouldn't happen if calendar range is wide enough)
    return target.normalize()


# -----------------------------
# Main pipeline
# -----------------------------
def fetch_rr7_injections(start: pd.Timestamp, end: pd.Timestamp, max_pages: int = 80) -> pd.DataFrame:
    """
    Crawl PBC bulletin pages and extract RR7 injections within [start, end].
    Returns DataFrame: date, injection_yi, url, title
    """
    # 1) crawl list pages -> bulletin urls
    all_bulletins: List[str] = []
    seen_list_pages: Set[str] = set()

    page_url = INDEX_URL
    for _ in range(max_pages):
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
        dt = dt.normalize()
        if not (start <= dt <= end):
            continue

        amt = parse_rr7_injection_yi(text)
        if amt is None:
            continue

        rows.append(
            {
                "date": dt,
                "injection_yi": float(amt),
                "title": get_title(soup),
                "url": u,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["date", "injection_yi", "title", "url"])

    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    # if multiple bulletins same day (rare), sum injections
    df = df.groupby("date", as_index=False).agg(
        injection_yi=("injection_yi", "sum"),
        title=("title", "first"),
        url=("url", "first"),
    )
    return df


def build_daily_table(
    target_start: pd.Timestamp,
    target_end: pd.Timestamp,
    buffer_days: int,
    out_csv: str,
) -> None:
    """
    Build table for [target_start, target_end] trading days:
      injection, maturity, net
    but fetch extra earlier injections to compute maturities that roll into range.
    """
    # 1) Determine fetch window (need earlier history for maturities)
    fetch_start = (target_start - pd.Timedelta(days=buffer_days)).normalize()
    fetch_end = target_end.normalize()

    # 2) Load trading calendar wide enough for rolling maturities
    # need calendar beyond end because maturities may roll forward after holidays
    cal_start = (fetch_start - pd.Timedelta(days=30)).normalize()
    cal_end = (target_end + pd.Timedelta(days=60)).normalize()
    trading_days = load_cn_trading_days(cal_start, cal_end)
    trading_set = set([d.normalize() for d in trading_days])

    # 3) Fetch injections in fetch window
    inj_df = fetch_rr7_injections(fetch_start, fetch_end)
    inj_map = dict(zip(inj_df["date"], inj_df["injection_yi"]))

    # 4) Compute maturity map: for each injection date D -> maturity date M (rolled)
    maturity_sum: Dict[pd.Timestamp, float] = {}
    for d, amt in inj_map.items():
        raw_maturity = (d + pd.Timedelta(days=7)).normalize()
        mat = roll_to_next_trading_day(raw_maturity, trading_set)
        maturity_sum[mat] = maturity_sum.get(mat, 0.0) + float(amt)

    # 5) Build output over target trading days only
    target_trading = [d for d in trading_days if target_start <= d <= target_end]
    rows = []
    for d in target_trading:
        inj = float(inj_map.get(d.normalize(), 0.0))
        mat = float(maturity_sum.get(d.normalize(), 0.0))
        net = inj - mat
        rows.append(
            {
                "date": d.date().isoformat(),
                "injection_yi": inj,
                "maturity_yi": mat,
                "net_yi": net,
            }
        )

    out_df = pd.DataFrame(rows)

    # 6) Save
    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"[OK] saved -> {out_path}  rows={len(out_df)}")
    print(out_df.head(10).to_string(index=False))
    print(out_df.tail(10).to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="YYYYMMDD (target start)")
    ap.add_argument("--end", required=True, help="YYYYMMDD (target end)")
    ap.add_argument("--out", required=True, help="output csv path")
    ap.add_argument("--buffer-days", type=int, default=45, help="fetch extra days before start for maturity calc")
    args = ap.parse_args()

    target_start = pd.to_datetime(args.start, format="%Y%m%d").normalize()
    target_end = pd.to_datetime(args.end, format="%Y%m%d").normalize()

    build_daily_table(
        target_start=target_start,
        target_end=target_end,
        buffer_days=args.buffer_days,
        out_csv=args.out,
    )


if __name__ == "__main__":
    main()