import os
import pandas as pd
import akshare as ak

TARGET_MONTHS = {"202412", "202501", "202512", "202601"}
OUT_PATH = "data/raw/pmi_4months.csv"

def to_month_any(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.replace("/", "-", regex=False)
    # 兼容 YYYY-MM-DD / YYYY-MM / YYYYMM
    s7 = s.str.slice(0, 7).str.replace("-", "", regex=False)
    # 若切出来不是6位，就尝试把原始去掉“-”
    s7 = s7.where(s7.str.match(r"^\d{6}$"), s.str.replace("-", "", regex=False))
    return s7

def main():
    os.makedirs("data/raw", exist_ok=True)

    df = ak.macro_china_pmi()  # 你现在的列：月份、制造业-指数、制造业-同比增长、非制造业-指数、非制造业-同比增长

    df["month"] = to_month_any(df["月份"])
    df = df[df["month"].isin(TARGET_MONTHS)].copy()

    df = df.sort_values("月份")
    df = df.groupby("month", as_index=False).tail(1)

    out = df[["month", "制造业-指数"]].rename(columns={"制造业-指数": "pmi"})
    out["pmi"] = pd.to_numeric(out["pmi"], errors="coerce")

    print(out)
    out.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"✅ 已导出: {OUT_PATH}")

if __name__ == "__main__":
    main()