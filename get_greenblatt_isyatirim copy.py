"""
BIST Magic Formula Screener
----------------------------
Screens Borsa Istanbul (BIST) stocks using Joel Greenblatt's Magic Formula:
  - Earnings Yield  = TTM EBIT / Enterprise Value
  - Return on Capital = TTM EBIT / (Net Working Capital + Net Fixed Assets)

Data source: isyatirim.com.tr
"""

import re
import sys
import time
import warnings
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import pandas as pd
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")

# ── Constants ──────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

BASE_URL = "https://www.isyatirim.com.tr"

# API item codes (MaliTablo XI_29 group)
ITEM_EBIT         = "3DF"   # Faaliyet Karı (EBIT)
ITEM_CURR_ASSETS  = "1A"    # Dönen Varlıklar
ITEM_CURR_LIAB    = "2A"    # Kısa Vadeli Yükümlülükler
ITEM_TOTAL_ASSETS = "1BL"   # Toplam Varlıklar
ITEM_INTANGIBLES  = "1BH"   # Maddi Olmayan Duran Varlıklar
ITEM_FIN_EXPENSE  = "4BB"   # Finansman Gideri

MIN_MARKET_CAP_MN_TL = 1_000   # Minimum market cap filter (mn TL)
MIN_VOLUME_MN_USD    = 5       # Minimum avg volume filter (mn USD), None = skip filter
MAX_WORKERS          = 5       # Concurrent threads


# ── Ticker Loading ─────────────────────────────────────────────────────────────

def load_tickers(filepath: str) -> list[str]:
    """Load ticker symbols from a plain-text file (one per line)."""
    path = Path(filepath)
    if not path.exists():
        print(f"[ERROR] Ticker file not found: {filepath}")
        sys.exit(1)
    tickers = [line.strip().upper() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not tickers:
        print(f"[ERROR] No tickers found in {filepath}")
        sys.exit(1)
    print(f"Loaded {len(tickers)} tickers from {filepath}")
    return tickers


# ── API Helpers ────────────────────────────────────────────────────────────────

def fetch_api(ticker: str, year: int, period: int, group: str = "XI_29") -> list | None:
    """
    Fetch financial table data from isyatirim MaliTablo API.
    Returns the 'value' list from the JSON response, or None on failure.
    """
    url = (
        f"{BASE_URL}/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo"
        f"?companyCode={ticker}&exchange=USD&financialGroup={group}"
        f"&year1={year}&period1={period}"
        f"&year2={year}&period2={period}"
        f"&year3={year}&period3={period}"
        f"&year4={year}&period4={period}"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        r.raise_for_status()
        return r.json().get("value", [])
    except Exception:
        return None


def get_value(data: list | None, item_code: str, col: str = "value1") -> float | None:
    """
    Extract a numeric value from the API response list by item code.
    Returns None if the item is missing or zero.
    """
    if not data:
        return None
    for item in data:
        if item.get("itemCode") == item_code:
            val = item.get(col)
            if val in (None, "", "0", 0):
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None
    return None


# ── TTM EBIT Calculation ───────────────────────────────────────────────────────

def fetch_ttm_ebit(ticker: str, current_year: int, current_month: int) -> float | None:
    """
    Calculate Trailing Twelve Months (TTM) EBIT.

    isyatirim stores YTD cumulative values, so TTM is:
        TTM = YTD(cur_year, cur_month)
            + YTD(prior_year, 12)
            - YTD(prior_year, cur_month)

    For December reporters (full-year), just return the annual value directly.
    """
    if current_month == 12:
        data = fetch_api(ticker, current_year, 12)
        return get_value(data, ITEM_EBIT, "value1")

    prior_year = current_year - 1
    data_cur        = fetch_api(ticker, current_year,  current_month)
    data_prior_full = fetch_api(ticker, prior_year, 12)
    data_prior_ytd  = fetch_api(ticker, prior_year, current_month)

    ebit_cur        = get_value(data_cur,        ITEM_EBIT, "value1")
    ebit_prior_full = get_value(data_prior_full, ITEM_EBIT, "value1")
    ebit_prior_ytd  = get_value(data_prior_ytd,  ITEM_EBIT, "value1")

    if None in (ebit_cur, ebit_prior_full, ebit_prior_ytd):
        return ebit_cur   # Fallback to whatever partial data exists

    return ebit_cur + ebit_prior_full - ebit_prior_ytd


# ── Page Scraping Helpers ──────────────────────────────────────────────────────

def detect_period(text: str) -> str | None:
    """Extract the latest YYYY/M or YYYY/MM period string from page text."""
    matches = re.findall(r"(\d{4}/\d{1,2})", text)
    return matches[0] if matches else None


def extract_after_keyword(text: str, keyword: str, chars: int = 100) -> str | None:
    """Return a substring starting right after `keyword` in `text`."""
    idx = text.find(keyword)
    if idx == -1:
        return None
    return text[idx + len(keyword): idx + len(keyword) + chars]


def parse_turkish_number(text: str | None) -> float | None:
    """
    Parse a Turkish-formatted number (1.234,56) from a string snippet.
    Returns a float or None.
    """
    if not text:
        return None
    # Try full Turkish decimal format first: 1.234,56
    match = re.search(r"-?[\d]{1,3}(?:\.\d{3})*,\d+", text)
    if match:
        raw = match.group().strip()
        raw = re.sub(r"mn\s*TL", "", raw, flags=re.IGNORECASE).strip()
        raw = raw.replace(".", "").replace(",", ".")
        try:
            return float(raw)
        except ValueError:
            return None
    # Fallback: integer with thousands separator (1.234)
    matches = re.findall(r"-?(?:\d{1,3}\.)+\d{3}", text)
    if matches:
        try:
            return float(matches[0].replace(".", ""))
        except ValueError:
            return None
    return None


def month_to_group(month: int) -> str:
    """Map a month number to the isyatirim period group name."""
    return {12: "December", 9: "September", 6: "June", 3: "March"}.get(month, f"Month_{month}")


# ── Main Fetch Function ────────────────────────────────────────────────────────

def fetch_stock(ticker: str) -> dict | None:
    """
    Fetch all required data for a single ticker.
    Returns a result dict or None if data is unavailable.
    """
    url = f"{BASE_URL}/tr-tr/analiz/hisse/Sayfalar/sirket-karti.aspx?hisse={ticker}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    text = soup.get_text()

    # ── Period detection ───────────────────────────────────────────────────
    period = detect_period(text)
    if not period:
        return None

    year  = int(period.split("/")[0])
    month = int(period.split("/")[1])
    group = month_to_group(month)

    # ── Market cap & net debt (scraped from page — not in API) ────────────
    market_cap = parse_turkish_number(extract_after_keyword(text, "Piyasa Değeri", 30))
    net_debt   = parse_turkish_number(extract_after_keyword(text, "Net Borç", 30))
    volume     = parse_turkish_number(extract_after_keyword(text, "Ort Hacim (mn$) 3A/12A", 30))

    if market_cap and net_debt:
        ev = (market_cap + net_debt) * 1_000_000
    elif market_cap:
        ev = market_cap * 1_000_000
    else:
        ev = None

    # ── TTM EBIT ───────────────────────────────────────────────────────────
    ebit = fetch_ttm_ebit(ticker, year, month)

    # ── Balance sheet (latest period) ─────────────────────────────────────
    bs_data = fetch_api(ticker, year, month)

    current_assets = get_value(bs_data, ITEM_CURR_ASSETS)
    current_liab   = get_value(bs_data, ITEM_CURR_LIAB)
    total_assets   = get_value(bs_data, ITEM_TOTAL_ASSETS)
    intangibles    = get_value(bs_data, ITEM_INTANGIBLES) or 0.0
    fin_expense_raw = get_value(bs_data, ITEM_FIN_EXPENSE)
    fin_expense     = abs(fin_expense_raw) if fin_expense_raw else None

    # ── Magic Formula metrics ──────────────────────────────────────────────
    earnings_yield = None
    if ebit and ev and ev > 0:
        earnings_yield = ebit / ev

    roc = None
    if ebit and current_assets is not None and current_liab is not None and total_assets:
        nwc    = current_assets - current_liab
        nfa    = total_assets - current_assets - intangibles
        capital = nwc + nfa
        if capital > 0:
            roc = ebit / capital

    # ── Company name ───────────────────────────────────────────────────────
    title_tag = soup.find("title")
    name = title_tag.text.split("|")[0].strip() if title_tag else ticker

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
        "Volume_mnUSD":    volume,
    }


# ── Ranking ────────────────────────────────────────────────────────────────────

def rank_and_save(df: pd.DataFrame, group_name: str, date_str: str) -> pd.DataFrame | None:
    """
    Filter, rank, and save stocks for a reporting period group.
    Returns the ranked DataFrame (or None if no valid stocks).
    """
    g = df[df["Group"] == group_name].copy()
    g = g.dropna(subset=["EarningsYield", "RoC"])
    g = g[g["EarningsYield"] > 0]
    g = g[g["RoC"] > 0]
    g = g[g["MarketCap_mnTL"] >= MIN_MARKET_CAP_MN_TL]

    if MIN_VOLUME_MN_USD is not None:
        g = g[g["Volume_mnUSD"].isna() | (g["Volume_mnUSD"] >= MIN_VOLUME_MN_USD)]

    if len(g) == 0:
        print(f"  No valid stocks in {group_name} group")
        return None

    g["EY_Rank"]     = g["EarningsYield"].rank(ascending=False, method="min")
    g["RoC_Rank"]    = g["RoC"].rank(ascending=False, method="min")
    g["Magic_Score"] = g["EY_Rank"] + g["RoC_Rank"]
    g = g.sort_values("Magic_Score").reset_index(drop=True)
    g.index += 1

    g["EarningsYield_%"] = (g["EarningsYield"] * 100).round(2)
    g["RoC_%"]           = (g["RoC"] * 100).round(2)

    filename = f"magic_formula_{group_name.lower()}_{date_str}.csv"
    g.to_csv(filename, index=True, index_label="Rank")
    print(f"  Saved {len(g)} stocks → {filename}")

    display_cols = ["Ticker", "Name", "Period", "EarningsYield_%", "RoC_%",
                    "EY_Rank", "RoC_Rank", "Magic_Score"]
    print(g[display_cols].head(20).to_string())
    return g


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="BIST Magic Formula Screener",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--tickers", default="bist_tickers.txt",
        help="Path to the ticker list file"
    )
    parser.add_argument(
        "--workers", type=int, default=MAX_WORKERS,
        help="Number of concurrent threads"
    )
    args = parser.parse_args()

    tickers = load_tickers(args.tickers)
    results = []
    total = len(tickers)
    completed = 0

    print(f"\nFetching data for {total} tickers with {args.workers} threads...\n")

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(fetch_stock, t): t for t in tickers}

        for future in as_completed(futures):
            ticker = futures[future]
            completed += 1
            data = future.result()

            if data and data["EarningsYield"] is not None and data["RoC"] is not None:
                results.append(data)
                print(
                    f"[{completed:>4}/{total}] ✓ {ticker:<6}  "
                    f"{data['Period']} ({data['Group']:<10})  "
                    f"EY: {data['EarningsYield']:.4f}  RoC: {data['RoC']:.4f}"
                )
            else:
                print(f"[{completed:>4}/{total}]   {ticker:<6}  — skipped")

            time.sleep(0.1)  # Be polite to the server

    if not results:
        print("\nNo results collected. Check your internet connection and ticker file.")
        sys.exit(1)

    df = pd.DataFrame(results)
    date_str = datetime.now().strftime("%Y%m%d")

    raw_file = f"bist_greenblatt_raw_{date_str}.csv"
    df.to_csv(raw_file, index=False)
    print(f"\nRaw data saved → {raw_file}")
    print(f"Total stocks fetched: {len(df)}")
    print("\nPeriod breakdown:")
    print(df["Group"].value_counts().to_string())

    print("\n" + "=" * 60)
    print("RANKING BY PERIOD GROUP")
    print("=" * 60)
    for group in ["December", "September", "June", "March"]:
        print(f"\n--- {group} ---")
        rank_and_save(df, group, date_str)

    print("\nDone.")


if __name__ == "__main__":
    main()