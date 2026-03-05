import pandas as pd
from datetime import datetime

# Load CSV
df = pd.read_csv("bist_greenblatt.csv")  # replace with your file path

# ----------------------------
# Step 1: Rank the Stocks
# ----------------------------
df['ROC_Rank'] = df['RoC'].rank(ascending=False)        # Higher ROC = better
df['EY_Rank'] = df['EarningsYield'].rank(ascending=False)  # Higher EY = cheaper

# Combined Magic Formula Score
df['MF_Score'] = df['ROC_Rank'] + df['EY_Rank']

# Sort by Magic Formula Score (lowest = best)
df_sorted = df.sort_values('MF_Score')

# ----------------------------
# Step 2: Show Top N Stocks including individual ranks
# ----------------------------
top_n = 20
print(df_sorted[['Ticker', 'Name', 'RoC', 'ROC_Rank', 'EarningsYield', 'EY_Rank', 'MF_Score']].head(top_n))

# ----------------------------
# Step 3: Save all ranked stocks to a new CSV with date
# ----------------------------
today_str = datetime.today().strftime('%Y-%m-%d')
filename = f"bist_greenblatt_ranked_{today_str}.csv"
df_sorted.to_csv(filename, index=False)

print(f"\n✅ All ranked stocks saved to '{filename}'")