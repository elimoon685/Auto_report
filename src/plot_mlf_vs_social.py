# src/plot_mlf_vs_social.py
import os
import pandas as pd
import matplotlib.pyplot as plt


def set_chinese_font():
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Songti SC", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False


def plot_mlf_vs_social(
    mlf_csv="data/raw/mlf_monthly.csv",
    social_csv="data/raw/social_core_4months.csv",
    out_path="figures/mlf_net_vs_social_total.png",
):
    set_chinese_font()

    # ---- read mlf ----
    mlf = pd.read_csv(mlf_csv)
    mlf["month"] = mlf["month"].astype(str)
    mlf["net_yi"] = pd.to_numeric(mlf["net_yi"], errors="coerce")

    # ---- read social ----
    soc = pd.read_csv(social_csv, encoding="utf-8")
    soc["month"] = soc["month"].astype(str)
    soc["社会融资规模增量"] = pd.to_numeric(soc["社会融资规模增量"], errors="coerce")

    # ---- keep months that exist in both ----
    df = pd.merge(
        soc[["month", "社会融资规模增量"]],
        mlf[["month", "net_yi"]],
        on="month",
        how="inner",
    ).sort_values("month")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # ---- plot (dual-axis bar) ----
    fig, ax1 = plt.subplots(figsize=(9, 5))

    # 左轴：社融（蓝）
    c_social = "tab:blue"
    ax1.bar(df["month"], df["社会融资规模增量"], alpha=0.6, color=c_social, label="社融规模增量")
    ax1.set_ylabel("社融规模增量（亿元）", color=c_social)
    ax1.tick_params(axis="y", labelcolor=c_social)
    ax1.set_xlabel("月份")
    ax1.grid(axis="y", linewidth=0.5, alpha=0.5)

    # 右轴：MLF净投放（红）
    ax2 = ax1.twinx()
    c_mlf = "tab:red"
    ax2.plot(df["month"], df["net_yi"], marker="o", linewidth=2, color=c_mlf, label="MLF净投放")
    ax2.set_ylabel("MLF净投放（亿元）", color=c_mlf)
    ax2.tick_params(axis="y", labelcolor=c_mlf)
    ax2.axhline(0, linewidth=1, alpha=0.7)

    plt.title("MLF净投放 vs 社融规模增量")

    # 合并图例
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_mlf_vs_social()