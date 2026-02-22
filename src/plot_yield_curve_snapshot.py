import os
import pandas as pd
import matplotlib.pyplot as plt


TENORS = ["3月", "6月", "1年", "3年", "5年", "7年", "10年", "30年"]


def _pick_date_row(df: pd.DataFrame, target_date: str, mode: str = "prev"):
    """
    mode:
      - "prev": 选择 <= target_date 的最近日期（推荐）
      - "next": 选择 >= target_date 的最近日期
      - "nearest": 选择距离 target_date 最近的日期
    """
    t = pd.to_datetime(target_date)

    # drop invalid dates
    df2 = df.dropna(subset=["日期"]).sort_values("日期").copy()

    if mode == "prev":
        cand = df2[df2["日期"] <= t]
        if cand.empty:
            # 如果目标日期之前没有数据，就退而求其次取最早一天
            row = df2.iloc[[0]]
        else:
            row = cand.iloc[[-1]]
    elif mode == "next":
        cand = df2[df2["日期"] >= t]
        if cand.empty:
            row = df2.iloc[[-1]]
        else:
            row = cand.iloc[[0]]
    elif mode == "nearest":
        idx = (df2["日期"] - t).abs().idxmin()
        row = df2.loc[[idx]]
    else:
        raise ValueError("mode must be one of: prev / next / nearest")

    actual_date = row["日期"].iloc[0].strftime("%Y-%m-%d")
    y = row[TENORS].iloc[0].astype(float).values
    return actual_date, y


def plot_yield_curve_snapshot(
    csv_path="data/raw/gov_yield_curve_20251201_20260131.csv",
    date1="2025-12-01",
    date2="2026-01-31",
    mode="prev",
    out_path="figures/yield_curve_snapshot.png",
):
    # 读取数据（中文列名一般 utf-8 就行；如果你遇到乱码再改 gbk）
    df = pd.read_csv(csv_path, encoding="utf-8")

    # 日期解析
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")

    # 取两天（自动纠偏）
    actual1, y1 = _pick_date_row(df, date1, mode=mode)
    actual2, y2 = _pick_date_row(df, date2, mode=mode)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.plot(TENORS, y1, marker="o", label=actual1)
    plt.plot(TENORS, y2, marker="o", label=actual2)

    plt.title("Government Bond Yield Curve Snapshot")
    plt.ylabel("Yield (%)")
    plt.xlabel("Tenor")
    plt.grid(True, linewidth=0.5, alpha=0.5)
    plt.legend()

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"Requested: {date1} vs {date2} | Picked: {actual1} vs {actual2}")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_yield_curve_snapshot()