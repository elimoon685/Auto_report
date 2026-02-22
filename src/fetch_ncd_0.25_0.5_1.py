import time
import requests
import pandas as pd
import random

API_URL = "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/ClsYldCurvHis"
LANDING_URL = "https://www.chinamoney.com.cn/chinese/bkcurvclosedyhis/index.html?bondType=CYCC41B&reference=1"

BASE_PARAMS = {
    "lang": "CN",
    "reference": "1",
    "bondType": "CYCC41B",
    "termId": "1",
    "pageSize": "15",
}

# ✅ 两个月
DATE_RANGES = [
    ("2025-12-01", "2025-12-31"),
    ("2026-01-01", "2026-01-31"),
]

def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Referer": LANDING_URL,
        "Origin": "https://www.chinamoney.com.cn",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    s.get(LANDING_URL, timeout=20)
    return s

def fetch_page(session: requests.Session, start_date: str, end_date: str, page_num: int) -> dict:
    params = {
        **BASE_PARAMS,
        "startDate": start_date,
        "endDate": end_date,
        "pageNum": str(page_num),
    }
    r = session.post(API_URL, params=params, data=params, timeout=(10, 90))
    r.raise_for_status()
    return r.json()

def fetch_range(session: requests.Session, start_date: str, end_date: str) -> pd.DataFrame:
    js1 = fetch_page(session, start_date, end_date, 1)
    page_total = int((js1.get("data") or {}).get("pageTotal") or 1)

    out = []

    def consume(records):
        for rec in records:
            dt = rec.get("newDateValueCN")
            tenor = rec.get("yearTermStr")
            yld = rec.get("maturityYieldStr") or rec.get("currentYieldStr")

            if not dt or tenor in (None, "") or yld in (None, "", "--", "——"):
                continue

            try:
                t = float(str(tenor).strip())
            except Exception:
                continue

            if abs(t - 0.25) < 1e-8:
                col = "y_3m"
            elif abs(t - 0.5) < 1e-8:
                col = "y_6m"
            elif abs(t - 1.0) < 1e-8:
                col = "y_1y"
            else:
                continue

            try:
                out.append({
                    "date": dt,
                    "col": col,
                    "yield": float(str(yld).strip())
                })
            except Exception:
                continue

    # 第一页
    consume(js1.get("records") or [])

    # 其余页
    for pn in range(2, page_total + 1):
        js = fetch_page(session, start_date, end_date, pn)
        consume(js.get("records") or [])
        time.sleep(0.8 + random.uniform(0.0, 0.6))

    df = pd.DataFrame(out).drop_duplicates(subset=["date", "col"])

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["date", "col"])

    return df

def main():
    s = build_session()
    frames = []

    for start_date, end_date in DATE_RANGES:
        print(f"Fetching {start_date} ~ {end_date} ...")
        frames.append(fetch_range(s, start_date, end_date))

    df_long = pd.concat(frames, ignore_index=True)

    if df_long.empty:
        raise RuntimeError("没有抓到数据")

    df_wide = (
        df_long.pivot_table(index="date", columns="col", values="yield", aggfunc="last")
        .reset_index()
        .sort_values("date")
    )

    df_wide["date"] = df_wide["date"].dt.strftime("%Y-%m-%d")

    for c in ["y_3m", "y_6m", "y_1y"]:
        if c not in df_wide.columns:
            df_wide[c] = None

    df_wide = df_wide[["date", "y_3m", "y_6m", "y_1y"]]

    out_csv = "data/raw/ncd_aaa_maturity_yield_3m_6m_1y_202512_202601.csv"
    df_wide.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print("Saved:", out_csv)
    print(df_wide.head())
    print(df_wide.tail())

if __name__ == "__main__":
    main()