# src/plot_ncd_spread.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def plot_ncd_spread_vs_dr007(
    ncd_csv="data/raw/ncd_aaa_maturity_yield_3m_6m_1y_202512_202601.csv",
    dr_csv="data/raw/dr007_dr001_20251201_20260131.csv",
    out_path="figures/ncd_spread_vs_dr007.png",
):

    # ---------- read ncd ----------
    ncd = pd.read_csv(ncd_csv)
    ncd["date"] = pd.to_datetime(ncd["date"], errors="coerce")
    for c in ["y_3m", "y_1y"]:
        ncd[c] = pd.to_numeric(ncd[c], errors="coerce")
    ncd = ncd.dropna(subset=["date"]).sort_values("date")

    # ---------- read dr ----------
    dr = pd.read_csv(dr_csv)
    dr["date"] = pd.to_datetime(dr["date"], errors="coerce")
    dr["dr007"] = pd.to_numeric(dr["dr007"], errors="coerce")
    dr = dr.dropna(subset=["date"]).sort_values("date")[["date", "dr007"]]

    # ---------- merge ----------
    df = pd.merge(ncd, dr, on="date", how="inner").sort_values("date")

    # ---------- calculate spread ----------
    df["spread_3m"] = df["y_3m"] - df["dr007"]
    df["spread_1y"] = df["y_1y"] - df["dr007"]

    # ---------- output dir ----------
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # ---------- plot ----------
    fig, ax = plt.subplots(figsize=(11, 5))

    ax.plot(df["date"], df["spread_3m"], label="NCD 3M - DR007")
    ax.plot(df["date"], df["spread_1y"], label="NCD 1Y - DR007")

    # 0轴线（非常关键）
    ax.axhline(0, linewidth=1, alpha=0.7)

    ax.set_title("NCD Spread vs DR007 (Liquidity / Credit Stress Indicator)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Spread (percentage points)")

    ax.grid(True, linewidth=0.5, alpha=0.5)

    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    ax.legend(loc="upper left")

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_ncd_spread_vs_dr007()