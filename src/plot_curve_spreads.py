# src/plot_curve_spreads.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_curve_spreads(
    csv_path="data/raw/gov_yield_curve_20251201_20260131.csv",
    out_path="figures/curve_spreads_10y_1y_10y_3m.png",
):
    df = pd.read_csv(csv_path, encoding="utf-8")

    # 日期解析
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    df = df.dropna(subset=["日期"]).sort_values("日期")

    # 转成数值
    for c in ["3月", "1年", "10年"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # 计算期限利差（单位：百分点）
    df["spr_10y_1y"] = df["10年"] - df["1年"]
    df["spr_10y_3m"] = df["10年"] - df["3月"]

    # 输出目录
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # 画图
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df["日期"], df["spr_10y_1y"], label="10Y - 1Y")
    ax.plot(df["日期"], df["spr_10y_3m"], label="10Y - 3M")

    # 0轴线（判断是否倒挂）
    ax.axhline(0, linewidth=1, alpha=0.7)

    ax.set_title("Curve Spreads: 10Y-1Y and 10Y-3M")
    ax.set_xlabel("Date")
    ax.set_ylabel("Spread (percentage points)")
    ax.grid(True, linewidth=0.5, alpha=0.5)

    # 日期轴格式：按周显示
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_curve_spreads()