"""
Fetch DR007 (repo fixing rate, 7D) for Jan 2026 using AkShare
"""

import pandas as pd
import akshare as ak


def main():
    start_date = "20251201"
    end_date = "20260131"

    # 回购定盘利率历史
    df = ak.repo_rate_hist(start_date=start_date, end_date=end_date)
    print(df.columns)
    if df.empty:
        raise SystemExit("No data returned.")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # FDR007 = 存款类机构 7D 定盘
    out = df[["date", "FDR007"]].copy()
    out = df[["date", "FDR001", "FDR007"]].copy()

    out = out.rename(columns={
        "FDR001": "dr001",
        "FDR007": "dr007"
    })
    out["dr001"] = pd.to_numeric(out["dr001"], errors="coerce")
    out["dr007"] = pd.to_numeric(out["dr007"], errors="coerce")

    out.to_csv("data/raw/dr007_dr001_20251201_20260131.csv", index=False)

    print("Saved data/raw/dr007_dr001_20251201_20260131.csv")
    print(out)


if __name__ == "__main__":
    main()