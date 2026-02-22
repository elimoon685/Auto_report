# src/plot_pmi_last2.py
import os
import pandas as pd
import matplotlib.pyplot as plt


def plot_pmi_last2(
    csv_path="data/raw/macro_cpi_ppi_pmi_4months.csv",
    out_path="figures/pmi_last2.png",
):
    df = pd.read_csv(csv_path)

    # 只选 202512 和 202601
    df["month"] = df["month"].astype(str)
    df = df[df["month"].isin(["202512", "202601"])]

    df["pmi"] = pd.to_numeric(df["pmi"], errors="coerce")
    df = df.sort_values("month")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    plt.figure(figsize=(7, 5))

    plt.plot(df["month"], df["pmi"], marker="o", label="PMI")

    # 50 分界线
    plt.axhline(50, linestyle="--", linewidth=1)

    plt.title("PMI (2025-12 vs 2026-01)")
    plt.ylabel("PMI")
    plt.xlabel("Month")
    plt.grid(True, linewidth=0.5, alpha=0.5)
    plt.legend()

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_pmi_last2()