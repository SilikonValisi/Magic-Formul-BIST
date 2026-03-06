import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import warnings
warnings.filterwarnings('ignore')

with open("bist_tickers.txt", "r") as f:
    BIST_TICKERS = [line.strip() for line in f if line.strip()]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

def parse_number(raw):
    """Convert Turkish number format to float."""
    if not raw:
        return None
    raw = raw.strip().replace('\xa0', '').replace(' ', '')
    raw = re.sub(r'mn\s*TL', '', raw, flags=re.IGNORECASE).strip()
    try:
        if ',' in raw:
            # e.g. 110.723,7 → thousands=dot, decimal=comma
            raw = raw.replace('.', '').replace(',', '.')
        else:
            # e.g. 22.533.072.000 → thousands=dot only
            raw = raw.replace('.', '')
        return float(raw)
    except:
        return None

def extract_after_keyword(text, keyword, chars=100):
    """Extract text right after a keyword."""
    idx = text.find(keyword)
    if idx == -1:
        return None
    return text[idx + len(keyword): idx + len(keyword) + chars]

def get_first_number(text):
    """Extract only the FIRST number — split on Turkish thousands pattern."""
    if not text:
        return None
    # First, try to find a number with comma decimal (mn TL format e.g. 110.723,7)
    match = re.search(r'-?[\d]{1,3}(?:\.\d{3})*,\d+', text)
    if match:
        return parse_number(match.group())
    # Otherwise find integer — must end with .000 or be standalone
    # Split concatenated numbers: 22.533.072.0009.823... → take up to last .000
    # Split on where a new number starts: digits after boundary
    # Strategy: find all candidate numbers, return the first
    matches = re.findall(r'-?(?:\d{1,3}\.)+\d{3}', text)
    if matches:
        return parse_number(matches[0])
    return None

def detect_period(text):
    """Detect the latest financial period from page text."""
    # Look for period patterns like 2025/9, 2025/12 etc.
    matches = re.findall(r'(\d{4}/\d{1,2})', text)
    if matches:
        # Return the first one found (most recent)
        return matches[0]
    return None

def fetch_isyatirim(ticker):
    url = f"https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/sirket-karti.aspx?hisse={ticker}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "lxml")
        text = soup.get_text()

        # ── Detect latest period ───────────────────────────────────────────
        period = detect_period(text)
        if not period:
            return None

        # Determine group based on month
        month = int(period.split('/')[1])
        if month == 12:
            group = "December"
        elif month == 9:
            group = "September"
        if month == 6:
            group = "June"
        elif month == 3:
            group = "March"
        else:
            group = f"Month_{month}"

        # ── Market Cap & Net Debt → Enterprise Value ───────────────────────
        market_cap_text = extract_after_keyword(text, "Piyasa Değeri", 30)
        net_debt_text   = extract_after_keyword(text, "Net Borç", 30)

        market_cap = get_first_number(market_cap_text)  # in mn TL
        net_debt   = get_first_number(net_debt_text)    # in mn TL

        if market_cap and net_debt:
            ev = (market_cap + net_debt) * 1_000_000  # convert to full TRY
        elif market_cap:
            ev = market_cap * 1_000_000
        else:
            ev = None

        # ── EBIT (Faaliyet Karı) ───────────────────────────────────────────
        ebit_text = extract_after_keyword(text, "Net Faaliyet Kar/Zararı", 50)
        ebit = get_first_number(ebit_text)  # full TRY

        # ── Balance Sheet ──────────────────────────────────────────────────
        current_assets_text      = extract_after_keyword(text, "Dönen Varlıklar", 50)
        current_liab_text        = extract_after_keyword(text, "Kısa Vadeli Yükümlülükler", 50)
        total_assets_text        = extract_after_keyword(text, "TOPLAM VARLIKLAR", 50)
        intangibles_text         = extract_after_keyword(text, "Maddi Olmayan Duran Varlıklar", 50)
        fin_expense_text = extract_after_keyword(text, "Finansman Giderleri", 50)
        fin_expense = get_first_number(fin_expense_text)
        if fin_expense:
            fin_expense = abs(fin_expense)  # her zaman pozitif al

        current_assets = get_first_number(current_assets_text)
        current_liab   = get_first_number(current_liab_text)
        total_assets   = get_first_number(total_assets_text)
        intangibles    = get_first_number(intangibles_text) or 0

        # ── Calculate Metrics ──────────────────────────────────────────────
        earnings_yield = None
        if ebit and ev and ev > 0:
            earnings_yield = ebit / ev

        roc = None
        if ebit and current_assets and current_liab and total_assets:
            nwc     = current_assets - current_liab
            nfa     = total_assets - current_assets - intangibles
            capital = nwc + nfa
            if capital > 0:
                roc = ebit / capital

        # ── Company name ───────────────────────────────────────────────────
        name_tag = soup.find("title")
        name = name_tag.text.split("|")[0].strip() if name_tag else ticker

        return {
            "Ticker":          ticker,
            "Name":            name,
            "Period":          period,
            "Group":           group,
            "EBIT":            ebit,
            "EnterpriseValue": ev,
            "EarningsYield":   earnings_yield,
            "RoC":             roc,
            "MarketCap_mnTL":  market_cap,
            "NetDebt_mnTL":    net_debt,
            "FinansmanGideri": fin_expense,
        }

    except Exception as e:
        return None


def rank_group(df, group_name, filename):
    """Rank stocks within a group and save to CSV."""
    g = df[df["Group"] == group_name].copy()
    g = g.dropna(subset=["EarningsYield", "RoC"])
    g = g[g["EarningsYield"] > 0]
    g = g[g["RoC"] > 0]
    # Finansman gideri faaliyet karının %80'inden fazlaysa ele
    g = g[g["FinansmanGideri"].isna() | (g["FinansmanGideri"] / g["EBIT"] < 0.80)]

    if len(g) == 0:
        print(f"No valid stocks in {group_name} group")
        return

    g["EY_Rank"]  = g["EarningsYield"].rank(ascending=False, method="min")  # high EY = cheap
    g["RoC_Rank"] = g["RoC"].rank(ascending=False, method="min")             # high RoC = good
    g["Magic_Score"] = g["EY_Rank"] + g["RoC_Rank"]
    g = g.sort_values("Magic_Score").reset_index(drop=True)
    g.index += 1

    g["EarningsYield"] = (g["EarningsYield"] * 100).round(2)
    g["RoC"]           = (g["RoC"] * 100).round(2)

    from datetime import datetime
    date_str = datetime.now().strftime('%Y%m%d')
    filename = filename.replace('.csv', f'_{date_str}.csv')
    g.to_csv(filename, index=True, index_label="Rank")
    print(f"\nSaved {len(g)} stocks → {filename}")
    print(g[["Ticker", "Name", "Period", "EarningsYield", "RoC", "EY_Rank", "RoC_Rank", "Magic_Score"]].head(20).to_string())


def main():
    results = []
    total = len(BIST_TICKERS)

    for i, ticker in enumerate(BIST_TICKERS):
        data = fetch_isyatirim(ticker)
        if data and data["EarningsYield"] is not None and data["RoC"] is not None:
            results.append(data)
            print(f"[{i+1}/{total}] {ticker} - {data['Period']} ({data['Group']}) | EY: {data['EarningsYield']:.4f} | RoC: {data['RoC']:.4f}")
        else:
            print(f"[{i+1}/{total}] {ticker} - SKIPPED")
        time.sleep(0.3)  # be polite to the server

    df = pd.DataFrame(results)
    df.to_csv("bist_greenblatt_raw.csv", index=False)
    print(f"\nTotal fetched: {len(df)} stocks")
    print(df["Group"].value_counts())

    # ── Rank and save each group separately ───────────────────────────────
    rank_group(df, "December",  "magic_formula_december.csv")
    rank_group(df, "September", "magic_formula_september.csv")
    rank_group(df, "March",     "magic_formula_march.csv")
    rank_group(df, "June",      "magic_formula_june.csv")


if __name__ == "__main__":
    main()