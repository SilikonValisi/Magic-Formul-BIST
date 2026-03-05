import pandas as pd
import matplotlib.pyplot as plt
import scipy.stats as stats
import numpy as np

df = pd.read_csv("bist_fundamentals.csv")

# Drop nulls for each metric
metrics = {"PE": "P/E Ratio", "RoA": "Return on Assets", "RoE": "Return on Equity"}

fig, axes = plt.subplots(3, 2, figsize=(14, 12))
fig.suptitle("BIST Stocks - Distribution Analysis", fontsize=16, fontweight="bold")

for i, (col, label) in enumerate(metrics.items()):
    data = df[col].dropna()

    # Fix PE if stored as decimal (e.g. 0.3 instead of 30)
    if col == "PE" and data.median() < 2:
        data = data * 100

    # Remove negatives from PE
    if col == "PE":
        data = data[(data > 0) & (data != float('inf')) & (data < 1000)]

    # Remove extreme outliers (beyond 1st-99th percentile)
    data = data[(data >= data.quantile(0.01)) & (data <= data.quantile(0.99))]

    # Skip if not enough data
    if len(data) < 10:
        print(f"Not enough data for {col}, skipping")
        continue

    # Histogram
    ax1 = axes[i][0]
    ax1.hist(data, bins=40, color="steelblue", edgecolor="white", alpha=0.8)
    ax1.set_title(f"{label} - Histogram")
    ax1.set_xlabel(col)
    ax1.set_ylabel("Count")

    # Q-Q Plot (if normal, dots follow the red line)
    ax2 = axes[i][1]
    stats.probplot(data, dist="norm", plot=ax2)
    ax2.set_title(f"{label} - Q-Q Plot")
    if len(ax2.get_lines()) > 1:
        ax2.get_lines()[1].set_color("red")

    # Normality test result on histogram
    sample = data.dropna().sample(min(50, len(data)), random_state=42)
    _, p_value = stats.shapiro(sample)
    normality = "Likely Normal" if p_value > 0.05 else "NOT Normal"
    ax1.text(0.97, 0.95, f"Shapiro p={p_value:.3f}\n{normality}",
             transform=ax1.transAxes, ha="right", va="top",
             bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.7))

plt.tight_layout()
plt.savefig("bist_distribution.png", dpi=150)
plt.show()
print("Saved: bist_distribution.png")