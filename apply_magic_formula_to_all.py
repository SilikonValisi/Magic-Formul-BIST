import pandas as pd
from datetime import datetime

# ── Load raw data ──────────────────────────────────────────────────────────────
date_str = datetime.now().strftime("%Y%m%d")
df = pd.read_csv(f"bist_greenblatt_raw_{date_str}.csv")
print(f"Total stocks in raw file: {len(df)}")
print(f"Groups: {df['Group'].value_counts().to_dict()}")

# ── Filters ────────────────────────────────────────────────────────────────────
df = df.dropna(subset=["EarningsYield", "RoC"])
df = df[df["EarningsYield"] > 0]                                          # EBIT pozitif
df = df[df["RoC"] > 0]                                                    # RoC pozitif
df = df[df["MarketCap_mnTL"] >= 1000]                                     # Market cap > 1 milyar TL
df = df[df["Volume_mnTL"].isna() | (df["Volume_mnTL"] >= 5)]       # Volume > 0.1 mn$/gün
#df = df[df["FinansmanGideri"].isna() | (df["FinansmanGideri"] / df["EBIT"] < 0.80)]  # Faiz < %80 EBIT

print(f"\nAfter filters: {len(df)} stocks")

# ── Rank ───────────────────────────────────────────────────────────────────────
df["EY_Rank"]    = df["EarningsYield"].rank(ascending=False, method="min")
df["RoC_Rank"]   = df["RoC"].rank(ascending=False, method="min")
df["Magic_Score"] = df["EY_Rank"] + df["RoC_Rank"]
df = df.sort_values("Magic_Score").reset_index(drop=True)
df.index += 1

df["EarningsYield"] = (df["EarningsYield"] * 100).round(2)
df["RoC"]           = (df["RoC"] * 100).round(2)

# ── Save ───────────────────────────────────────────────────────────────────────
date_str = datetime.now().strftime('%Y%m%d')
filename = f"magic_formula_all_{date_str}.csv"
df.to_csv(filename, index=True, index_label="Rank")

print(f"\nSaved → {filename}")
print(f"\nTop 30:")
print(df[["Ticker", "Name", "Period", "Group", "EarningsYield", "RoC", "EY_Rank", "RoC_Rank", "Magic_Score"]].head(30).to_string())