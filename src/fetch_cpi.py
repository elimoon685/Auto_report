# import os
# import pandas as pd
# import akshare as ak

# TARGET_MONTHS = {"202412", "202501", "202512", "202601"}
# OUT_PATH = "data/raw/cpi_4months.csv"

# def to_month(series: pd.Series) -> pd.Series:
#     s = series.astype(str).str.strip().str.replace("/", "-", regex=False)
#     return s.str.slice(0, 7).str.replace("-", "", regex=False)

# def main():
#     os.makedirs("data/raw", exist_ok=True)

#     df = ak.macro_china_cpi_monthly()  # 你现在用的：CPI月率报告（字段：商品/日期/今值/预测值/前值）

#     # 可选：锁定“商品”避免同月多条（建议保留）
#     if "商品" in df.columns:
#         df = df[df["商品"].astype(str).str.contains("CPI月率", na=False)]

#     df["month"] = to_month(df["日期"])
#     df = df[df["month"].isin(TARGET_MONTHS)].copy()

#     # 同月多条取最新发布
#     df = df.sort_values("日期")
#     df = df.groupby("month", as_index=False).tail(1)

#     out = df[["month", "今值"]].rename(columns={"今值": "cpi"})
#     out["cpi"] = pd.to_numeric(out["cpi"], errors="coerce")

#     print(out)
#     out.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
#     print(f"✅ 已导出: {OUT_PATH}")

# if __name__ == "__main__":
#     main()
import pandas as pd
import akshare as ak

def main():
    df = ak.macro_china_cpi_monthly()  # 你的CPI月率报告：商品/日期/今值/预测值/前值

    # 只保留你要的那条商品（避免混入口径）
    if "商品" in df.columns:
        df = df[df["商品"].astype(str).str.contains("CPI月率", na=False)].copy()

    # 今值转数值，过滤掉 NaN
    df["今值"] = pd.to_numeric(df["今值"], errors="coerce")
    df = df.dropna(subset=["今值"])

    # 日期转时间并取最新一条
    df["日期_dt"] = pd.to_datetime(df["日期"], errors="coerce")
    last = df.sort_values("日期_dt").tail(1).iloc[0]

    latest_date = last["日期"]
    latest_month = str(latest_date)[:7].replace("-", "")  # YYYYMM
    latest_value = last["今值"]

    print("✅ CPI 最新数据：")
    print("最新发布日期:", latest_date)
    print("对应月份(YYYYMM):", latest_month)
    print("今值:", latest_value)

if __name__ == "__main__":
    main()