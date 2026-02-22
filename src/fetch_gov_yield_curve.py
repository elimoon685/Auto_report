"""
Fetch ChinaBond yield curve via AkShare bond_china_yield, then filter the government curve.
Doc: bond_china_yield(start_date, end_date). :contentReference[oaicite:9]{index=9}

Example:
  python src/fetch_gov_yield_curve.py --start 20260101 --end 20260131 --out data/raw/gov_yield_curve_202601.csv
"""

from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import akshare as ak


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, help="YYYYMMDD (within 1 year of end)")
    p.add_argument("--end", required=True, help="YYYYMMDD")
    p.add_argument("--curve", default="中债国债收益率曲线", help="默认筛国债曲线")
    p.add_argument("--out", required=True, help="output csv path")
    args = p.parse_args()

    df = ak.bond_china_yield(start_date=args.start, end_date=args.end)
    if df.empty:
        raise SystemExit("No data returned by ak.bond_china_yield")

    # 标准列名：曲线名称、日期、3月、6月、1年、3年、5年、7年、10年、30年 :contentReference[oaicite:10]{index=10}
    if "曲线名称" not in df.columns or "日期" not in df.columns:
        raise SystemExit(f"Unexpected columns: {list(df.columns)}")

    out = df[df["曲线名称"] == args.curve].copy()
    if out.empty:
        # 给出提示：有哪些曲线名称
        names = sorted(df["曲线名称"].dropna().unique().tolist())
        raise SystemExit(f"Curve '{args.curve}' not found. Available: {names[:10]} ... (total {len(names)})")

    out["日期"] = pd.to_datetime(out["日期"])
    out = out.sort_values("日期").reset_index(drop=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False, encoding="utf-8-sig")

    print(f"[OK] {len(out)} rows saved -> {out_path}")
    print(out.head())


if __name__ == "__main__":
    main()