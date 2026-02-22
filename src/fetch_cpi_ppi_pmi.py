import os
import pandas as pd
import akshare as ak

TARGET_MONTHS = {"202412", "202501", "202512", "202601"}
OUT_PATH = "data/raw/macro_cpi_ppi_pmi_4months.csv"

def to_month_any(series: pd.Series) -> pd.Series:
    """
    支持：
    - 1996-02-01 -> 199602
    - 2024-12-31 -> 202412
    - 2024-12 -> 202412
    - 202412 -> 202412
    - 2024/12 -> 202412
    """
    s = series.astype(str).str.strip()
    s = s.str.replace("/", "-", regex=False)
    # 先取前7位（YYYY-MM）如果存在
    s7 = s.str.slice(0, 7)
    # 把 YYYY-MM 变 YYYYMM
    s7 = s7.str.replace("-", "", regex=False)
    # 如果原本就是 YYYYMM 就保留
    s7 = s7.where(s7.str.match(r"^\d{6}$"), s.str.replace("-", "", regex=False))
    return s7

def pick_cpi_ppi(df: pd.DataFrame, name: str, product_keyword: str | None = None) -> pd.DataFrame:
    df = df.copy()

    # 可选：只取某个“商品”（避免同月多条）
    if product_keyword is not None and "商品" in df.columns:
        df = df[df["商品"].astype(str).str.contains(product_keyword, na=False)]

    df["month"] = to_month_any(df["日期"])

    # 只取目标月
    df = df[df["month"].isin(TARGET_MONTHS)].copy()

    # 同月多条：按日期排序，取最后一条（最新发布）
    df = df.sort_values("日期")
    df = df.groupby("month", as_index=False).tail(1)

    out = df[["month", "今值"]].rename(columns={"今值": name})
    out[name] = pd.to_numeric(out[name], errors="coerce")
    return out

def pick_pmi(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = to_month_any(df["月份"])

    df = df[df["month"].isin(TARGET_MONTHS)].copy()

    # 同月多条（一般不会，但也防一下）
    df = df.sort_values("月份")
    df = df.groupby("month", as_index=False).tail(1)

    out = df[["month", "制造业-指数"]].rename(columns={"制造业-指数": "pmi"})
    out["pmi"] = pd.to_numeric(out["pmi"], errors="coerce")
    return out

def main():
    os.makedirs("data/raw", exist_ok=True)

    # CPI：你截图里是“CPI月率报告”，就用关键字锁定它（避免同月多条）
    cpi = ak.macro_china_cpi_monthly()
    cpi_4m = pick_cpi_ppi(cpi, "cpi", product_keyword="CPI月率")

    # PPI：你截图是“PPI年率报告”
    ppi = ak.macro_china_ppi_yearly()
    ppi_4m = pick_cpi_ppi(ppi, "ppi", product_keyword="PPI年率")

    # PMI：官方制造业
    pmi = ak.macro_china_pmi()
    pmi_4m = pick_pmi(pmi)

    result = cpi_4m.merge(ppi_4m, on="month", how="outer").merge(pmi_4m, on="month", how="outer")
    result = result.sort_values("month")

    print("====== 四个月 CPI / PPI / PMI（去重后）======")
    print(result)

    result.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\n✅ 已导出: {OUT_PATH}")

    # 提醒未来月份必然缺数据
    future = [m for m in ["202512", "202601"] if m in TARGET_MONTHS]
    if future:
        print("\n⚠️ 提醒：202512、202601 是未来月份（如果当前还没到），PMI/CPI/PPI 很可能为 NaN，这是正常的。")

if __name__ == "__main__":
    main()