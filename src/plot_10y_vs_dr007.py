# src/plot_10y_vs_dr007.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_10y_vs_dr007(
    gov_csv="data/raw/gov_yield_curve_20251201_20260131.csv",
    dr_csv="data/raw/dr007_dr001_20251201_20260131.csv",
    out_path="figures/10y_vs_dr007.png",
):
    # ---- read gov 10Y ----
    gov = pd.read_csv(gov_csv, encoding="utf-8")
    gov["日期"] = pd.to_datetime(gov["日期"], errors="coerce")
    gov["10年"] = pd.to_numeric(gov["10年"], errors="coerce")
    gov = gov.dropna(subset=["日期"]).sort_values("日期")[["日期", "10年"]]
    gov = gov.rename(columns={"日期": "date", "10年": "gov_10y"})

    # ---- read dr007 ----
    dr = pd.read_csv(dr_csv)
    dr["date"] = pd.to_datetime(dr["date"], errors="coerce")
    dr["dr007"] = pd.to_numeric(dr["dr007"], errors="coerce")
    dr = dr.dropna(subset=["date"]).sort_values("date")[["date", "dr007"]]

    # ---- merge ----
    df = pd.merge(gov, dr, on="date", how="inner").sort_values("date")

    # ---- output dir ----
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # ---- plot ----
    fig, ax1 = plt.subplots(figsize=(11, 5))

    # 左轴：10Y（蓝色）
    color_10y = "tab:blue"
    ax1.plot(df["date"], df["gov_10y"], color=color_10y, label="Gov 10Y")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Gov 10Y (%)", color=color_10y)
    ax1.tick_params(axis="y", labelcolor=color_10y)
    ax1.grid(True, linewidth=0.5, alpha=0.5)

    # 右轴：DR007（红色）
    ax2 = ax1.twinx()
    color_dr = "tab:red"
    ax2.plot(df["date"], df["dr007"], color=color_dr, label="DR007")
    ax2.set_ylabel("DR007 (%)", color=color_dr)
    ax2.tick_params(axis="y", labelcolor=color_dr)

    # 日期轴
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

    plt.title("Gov 10Y (Left) vs DR007 (Right)")

    # 合并 legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_10y_vs_dr007()