# src/plot_cpi_ppi.py
import os
import pandas as pd
import matplotlib.pyplot as plt


def plot_cpi_ppi_last2(
    csv_path="data/raw/macro_cpi_ppi_pmi_4months.csv",
    out_path="figures/cpi_ppi_last2.png",
):
    df = pd.read_csv(csv_path)

    # 转成字符串方便筛选
    df["month"] = df["month"].astype(str)

    # 只选 202512 和 202601
    df = df[df["month"].isin(["202512", "202601"])]

    # 转数值
    df["cpi_yoy"] = pd.to_numeric(df["cpi_yoy"], errors="coerce")
    df["ppi_yoy"] = pd.to_numeric(df["ppi_yoy"], errors="coerce")

    df = df.sort_values("month")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    plt.figure(figsize=(8, 5))

    plt.plot(df["month"], df["cpi_yoy"], marker="o", label="CPI YoY")
    plt.plot(df["month"], df["ppi_yoy"], marker="o", label="PPI YoY")

    plt.axhline(0, linewidth=1)

    plt.title("CPI & PPI YoY (2025-12 vs 2026-01)")
    plt.ylabel("YoY (%)")
    plt.xlabel("Month")
    plt.grid(True, linewidth=0.5, alpha=0.5)
    plt.legend()

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    plot_cpi_ppi_last2()