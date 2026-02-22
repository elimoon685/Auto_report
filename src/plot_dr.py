# src/plot_dr.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_dr001_dr007(
    csv_path="data/raw/dr007_dr001_20251201_20260131.csv",
    out_path="figures/dr001_dr007.png",
):
    # 1) 读数据
    df = pd.read_csv(csv_path)

    # 2) 解析日期 + 排序
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    # 3) 转数值，防止字符串/空值
    for col in ["dr001", "dr007"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4) 创建输出目录
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # 5) 画图
    fig, ax = plt.subplots(figsize=(11, 5))

    ax.plot(df["date"], df["dr001"], label="DR001")
    ax.plot(df["date"], df["dr007"], label="DR007")

    ax.set_title("DR001 vs DR007")
    ax.set_xlabel("Date")
    ax.set_ylabel("Rate (%)")

    # 6) 日期轴格式（按周显示更清晰）
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    ax.grid(True, linewidth=0.5, alpha=0.5)
    ax.legend()

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_dr001_dr007()