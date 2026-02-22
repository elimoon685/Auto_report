# src/plot_social_structure.py
import os
import pandas as pd
import matplotlib.pyplot as plt


def set_chinese_font():
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "Songti SC"]
    plt.rcParams["axes.unicode_minus"] = False


def plot_social_structure(
    csv_path="data/raw/social_core_4months.csv",
    out_path="figures/social_structure_stacked.png",
):
    set_chinese_font()

    df = pd.read_csv(csv_path, encoding="utf-8")
    df["month"] = df["month"].astype(str)
    df = df[df["month"].isin(["202512", "202601"])].sort_values("month")

    cols = [
        "其中-人民币贷款",
        "其中-未贴现银行承兑汇票",
        "其中-企业债券",
    ]

    # 固定颜色（研究风格配色）
    colors = {
        "其中-人民币贷款": "#2E6F95",        # 深蓝
        "其中-未贴现银行承兑汇票": "#E36414", # 橙色
        "其中-企业债券": "#3A7D44",          # 深绿
    }

    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))

    for i, row in df.iterrows():
        month = row["month"]

        pos_bottom = 0
        neg_bottom = 0

        for c in cols:
            value = row[c]

            if value >= 0:
                ax.bar(
                    month,
                    value,
                    bottom=pos_bottom,
                    color=colors[c],
                    label=c if i == df.index[0] else "",
                )
                pos_bottom += value
            else:
                ax.bar(
                    month,
                    value,
                    bottom=neg_bottom,
                    color=colors[c],
                    label=c if i == df.index[0] else "",
                )
                neg_bottom += value

    ax.axhline(0, linewidth=1)

    ax.set_title("社融结构拆分")
    ax.set_ylabel("金额（亿元）")
    ax.set_xlabel("月份")
    ax.legend()
    ax.grid(axis="y", linewidth=0.5, alpha=0.5)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_social_structure()