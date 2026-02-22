# src/plot_dr_omo.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_dr007_vs_omo_net(
    dr_csv="data/raw/dr007_dr001_20251201_20260131.csv",
    omo_csv="data/raw/rr7_net_20251201_20260131.csv",
    out_path="figures/dr007_vs_omo_net.png",
):
    # ---- read dr ----
    dr = pd.read_csv(dr_csv)
    dr["date"] = pd.to_datetime(dr["date"], errors="coerce")
    dr["dr007"] = pd.to_numeric(dr["dr007"], errors="coerce")
    dr = dr.dropna(subset=["date"]).sort_values("date")[["date", "dr007"]]

    # ---- read omo ----
    omo = pd.read_csv(omo_csv)
    omo["date"] = pd.to_datetime(omo["date"], errors="coerce")
    # 你文件里列名是 injection_yi, maturity_yi, net_yi
    omo["net_yi"] = pd.to_numeric(omo["net_yi"], errors="coerce")
    omo = omo.dropna(subset=["date"]).sort_values("date")[["date", "net_yi"]]

    # ---- merge by date (outer: 保留两边全部日期) ----
    df = pd.merge(dr, omo, on="date", how="outer").sort_values("date")

    # 如果某天缺净投放/缺dr，留空即可；但柱状图空值会不画，先补0更直观
    df["net_yi"] = df["net_yi"].fillna(0)

    # ---- output dir ----
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # ---- plot ----
    fig, ax1 = plt.subplots(figsize=(11, 5))

    # 左轴：DR007
    ax1.plot(df["date"], df["dr007"], label="DR007")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("DR007 (%)")
    ax1.grid(True, linewidth=0.5, alpha=0.5)

    # 右轴：净投放柱状
    ax2 = ax1.twinx()
    ax2.bar(df["date"], df["net_yi"], width=0.8, alpha=0.35, label="OMO 7D Net Injection (Yi)")
    ax2.set_ylabel("OMO 7D Net Injection (Yi)")

    # 0轴线（净投放正负一眼看）
    ax2.axhline(0, linewidth=0.8, alpha=0.7)

    # 日期轴格式
    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

    # 标题
    plt.title("DR007 (Left) vs OMO 7D Net Injection (Right)")

    # 合并 legend（两个轴的图例一起放）
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="upper left")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_dr007_vs_omo_net()