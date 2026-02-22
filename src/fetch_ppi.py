import os
import pandas as pd
import akshare as ak

TARGET_MONTHS = {"202412", "202501", "202512", "202601"}
OUT_PATH = "data/raw/ppi_4months.csv"

def to_month(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.replace("/", "-", regex=False)
    return s.str.slice(0, 7).str.replace("-", "", regex=False)

def main():
    os.makedirs("data/raw", exist_ok=True)

    df = ak.macro_china_ppi_yearly()  # 你截图：PPI年率报告（字段：商品/日期/今值/预测值/前值）

    # 可选：锁定“商品”
    if "商品" in df.columns:
        df = df[df["商品"].astype(str).str.contains("PPI年率", na=False)]

    df["month"] = to_month(df["日期"])
    df = df[df["month"].isin(TARGET_MONTHS)].copy()

    df = df.sort_values("日期")
    df = df.groupby("month", as_index=False).tail(1)

    out = df[["month", "今值"]].rename(columns={"今值": "ppi"})
    out["ppi"] = pd.to_numeric(out["ppi"], errors="coerce")

    print(out)
    out.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"✅ 已导出: {OUT_PATH}")

if __name__ == "__main__":
    main()