import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import warnings
warnings.filterwarnings('ignore')
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


with open("bist_tickers.txt", "r") as f:
    BIST_TICKERS = [line.strip() for line in f if line.strip()]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# ── API item codes ─────────────────────────────────────────────────────────
# Resolved from MaliTablo API response (XI_29 group)
ITEM_EBIT         = "3DF"   # FAALİYET KARI (ZARARI)
ITEM_CURR_ASSETS  = "1A"    # Dönen Varlıklar
ITEM_CURR_LIAB    = "2A"    # Kısa Vadeli Yükümlülükler
ITEM_TOTAL_ASSETS = "1BL"   # TOPLAM VARLIKLAR
ITEM_INTANGIBLES  = "1BH"   # Maddi Olmayan Duran Varlıklar


def fetch_api(ticker, year, period, group="XI_29"):
    """Fetch MaliTablo API for a single period (4 columns = same period repeated)."""
    url = (
        f"https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo"
        f"?companyCode={ticker}&exchange=USD&financialGroup={group}"
        f"&year1={year}&period1={period}"
        f"&year2={year}&period2={period}"
        f"&year3={year}&period3={period}"
        f"&year4={year}&period4={period}"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        if r.status_code != 200:
            return None
        return r.json().get("value", [])
    except:
        return None


def get_value(data, item_code, col="value1"):
    """Extract a single value from API response by item code."""
    if not data:
        return None
    for item in data:
        if item.get("itemCode") == item_code:
            val = item.get(col)
            try:
                return float(val) if val not in (None, "", "0", 0) else None
            except:
                return None
    return None


def fetch_ttm_ebit(ticker, current_year, current_month):
    """
    Calculate TTM EBIT by summing the last 4 quarters.

    For annual reporters (12-month period): TTM = value1 directly.
    For quarterly reporters: TTM = Q_current + Q_current-1 + Q_current-2 + Q_current-3

    isyatirim stores cumulative YTD values per period, so TTM is derived as:
      TTM = YTD(latest) + YTD(prior year same period) reversed increments
    
    Simpler standard approach for YTD cumulative statements:
      TTM = YTD(cur_year, cur_month) 
            + YTD(prior_year, 12)        # full prior year
            - YTD(prior_year, cur_month) # minus overlap
    """
    if current_month == 12:
        # Already a full year — just return value1 directly
        data = fetch_api(ticker, current_year, 12)
        return get_value(data, ITEM_EBIT, "value1")

    # TTM = current YTD + (prior full year - prior same period YTD)
    prior_year = current_year - 1

    data_cur       = fetch_api(ticker, current_year,  current_month)
    data_prior_ful = fetch_api(ticker, prior_year, 12)
    data_prior_ytd = fetch_api(ticker, prior_year, current_month)

    ebit_cur       = get_value(data_cur,       ITEM_EBIT, "value1")
    ebit_prior_ful = get_value(data_prior_ful, ITEM_EBIT, "value1")
    ebit_prior_ytd = get_value(data_prior_ytd, ITEM_EBIT, "value1")

    if ebit_cur is None or ebit_prior_ful is None or ebit_prior_ytd is None:
        # Fallback: just use whatever we have
        return ebit_cur

    ttm = ebit_cur + ebit_prior_ful - ebit_prior_ytd
    return ttm


def detect_period(text):
    """Detect the latest financial period from page text."""
    matches = re.findall(r'(\d{4}/\d{1,2})', text)
    if matches:
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

        year  = int(period.split('/')[0])
        month = int(period.split('/')[1])

        if month == 12:
            group = "December"
        elif month == 9:
            group = "September"
        elif month == 6:
            group = "June"
        elif month == 3:
            group = "March"
        else:
            group = f"Month_{month}"

        # ── Market Cap & Net Debt → Enterprise Value (still from page) ─────
        # These are not in the income/balance sheet API so we keep scraping them
        def extract_after_keyword(t, keyword, chars=100):
            idx = t.find(keyword)
            if idx == -1:
                return None
            return t[idx + len(keyword): idx + len(keyword) + chars]

        def get_first_number(t):
            if not t:
                return None
            match = re.search(r'-?[\d]{1,3}(?:\.\d{3})*,\d+', t)
            if match:
                raw = match.group().strip().replace('\xa0', '').replace(' ', '')
                raw = re.sub(r'mn\s*TL', '', raw, flags=re.IGNORECASE).strip()
                raw = raw.replace('.', '').replace(',', '.')
                try:
                    return float(raw)
                except:
                    return None
            matches = re.findall(r'-?(?:\d{1,3}\.)+\d{3}', t)
            if matches:
                raw = matches[0].strip().replace('.', '')
                try:
                    return float(raw)
                except:
                    return None
            return None

        market_cap_text = extract_after_keyword(text, "Piyasa Değeri", 30)
        net_debt_text   = extract_after_keyword(text, "Net Borç", 30)
        volume_text     = extract_after_keyword(text, "Ort Hacim (mn$) 3A/12A", 30)

        market_cap   = get_first_number(market_cap_text)   # mn TL
        net_debt     = get_first_number(net_debt_text)     # mn TL
        volume_mn_tl = get_first_number(volume_text)

        if market_cap and net_debt:
            ev = (market_cap + net_debt) * 1_000_000
        elif market_cap:
            ev = market_cap * 1_000_000
        else:
            ev = None

        # ── TTM EBIT via API ───────────────────────────────────────────────
        ebit = fetch_ttm_ebit(ticker, year, month)

        # ── Balance Sheet via API (latest period) ──────────────────────────
        bs_data = fetch_api(ticker, year, month)

        current_assets = get_value(bs_data, ITEM_CURR_ASSETS)
        current_liab   = get_value(bs_data, ITEM_CURR_LIAB)
        total_assets   = get_value(bs_data, ITEM_TOTAL_ASSETS)
        intangibles    = get_value(bs_data, ITEM_INTANGIBLES) or 0

        # ── Finansman gideri (still from API) ─────────────────────────────
        fin_expense_raw = get_value(bs_data, "4BB")
        fin_expense = abs(fin_expense_raw) if fin_expense_raw else None

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
            "EBIT_TTM":        ebit,
            "EnterpriseValue": ev,
            "EarningsYield":   earnings_yield,
            "RoC":             roc,
            "MarketCap_mnTL":  market_cap,
            "NetDebt_mnTL":    net_debt,
            "FinansmanGideri": fin_expense,
            "Volume_mnTL":     volume_mn_tl,
        }

    except Exception as e:
        return None


def rank_group(df, group_name, filename):
    """Rank stocks within a group and save to CSV."""
    g = df[df["Group"] == group_name].copy()
    g = g.dropna(subset=["EarningsYield", "RoC"])
    g = g[g["EarningsYield"] > 0]
    g = g[g["RoC"] > 0]
    g = g[g["MarketCap_mnTL"] >= 1000]
    g = g[g["Volume_mnTL"].isna() | (g["Volume_mnTL"] >= 5)]

    if len(g) == 0:
        print(f"No valid stocks in {group_name} group")
        return

    g["EY_Rank"]     = g["EarningsYield"].rank(ascending=False, method="min")
    g["RoC_Rank"]    = g["RoC"].rank(ascending=False, method="min")
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
    completed = 0

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_isyatirim, ticker): ticker for ticker in BIST_TICKERS}

        for future in as_completed(futures):
            ticker = futures[future]
            completed += 1
            data = future.result()
            if data and data["EarningsYield"] is not None and data["RoC"] is not None:
                results.append(data)
                print(f"[{completed}/{total}] {ticker} - {data['Period']} ({data['Group']}) | EY: {data['EarningsYield']:.4f} | RoC: {data['RoC']:.4f}")
            else:
                print(f"[{completed}/{total}] {ticker} - SKIPPED")
            time.sleep(0.1)

    df = pd.DataFrame(results)
    date_str = datetime.now().strftime("%Y%m%d")
    df.to_csv(f"bist_greenblatt_raw_{date_str}.csv", index=False)
    print(f"\nTotal fetched: {len(df)} stocks")
    print(df["Group"].value_counts())

    rank_group(df, "December",  "magic_formula_december.csv")
    rank_group(df, "September", "magic_formula_september.csv")
    rank_group(df, "March",     "magic_formula_march.csv")
    rank_group(df, "June",      "magic_formula_june.csv")


if __name__ == "__main__":
    main()