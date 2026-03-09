import requests
from bs4 import BeautifulSoup
import re
import time
import warnings
warnings.filterwarnings('ignore')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

BASE_URL = (
    "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/"
    "Temel-Degerler-Ve-Oranlar.aspx?sektor={code}"
)

# ── Sector codes to exclude ────────────────────────────────────────────────
# ── Financial Sector Exclusion ─────────────────────────────────
# Codes: Bankacılık=0001, Aracı Kurumlar=0051, Sigorta=0040, Faktoring=0014

FINANCIAL_SECTOR_CODES = {
    "0001": "Bankacılık (Banks)",
    "0051": "Aracı Kurumlar (Brokerages)",
    "0040": "Sigorta (Insurance)",
    "0014": "Faktoring (Factoring)",
    "0049": "GYO gayri menkül ortaklıgı",
    
}


def fetch_tickers_for_sector(sector_code: str, sector_name: str) -> list:
    """
    Fetch all tickers listed under a sector code.
    isyatirim paginates with #page-N but the table data is
    server-side rendered — all rows appear on first load.
    """
    url = BASE_URL.format(code=sector_code)
    try:
        r = requests.get(url, headers=HEADERS, timeout=25, verify=False)
        r.raise_for_status()
    except Exception as e:
        print(f"  WARNING: Failed to fetch {sector_name}: {e}")
        return []

    soup = BeautifulSoup(r.text, "lxml")
    tickers = []

    # Method A: look for links to sirket-karti with hisse= param
    # e.g. href="...sirket-karti.aspx?hisse=GARAN"
    for a in soup.find_all("a", href=True):
        m = re.search(r'hisse=([A-Z0-9]{2,6})', a["href"])
        if m:
            tickers.append(m.group(1))

    # Method B: if the table renders ticker codes as text in <td> cells
    # (first column "Kod" in the screenshot)
    if not tickers:
        for td in soup.find_all("td"):
            text = td.get_text(strip=True)
            if re.fullmatch(r'[A-Z]{2,6}[0-9]?', text):
                tickers.append(text)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique


def build_exclusion_set() -> set:
    """
    Loop through all financial sectors and collect tickers.
    Returns a set of tickers to exclude from Magic Formula.
    """
    all_excluded = set()

    print("Fetching financial sector tickers from isyatirim...\n")
    print(f"{'Sector':<45} Tickers")
    print("-" * 65)

    for code, name in FINANCIAL_SECTOR_CODES.items():
        tickers = fetch_tickers_for_sector(code, name)
        all_excluded.update(tickers)
        ticker_str = ", ".join(tickers) if tickers else "--- none found ---"
        print(f"  [{code}] {name:<40} ({len(tickers)} tickers)")
        if tickers:
            print(f"         {ticker_str}")
        time.sleep(0.5)  # polite delay

    return all_excluded


def save_exclusion_list(tickers: set, path: str = "financial_tickers.txt"):
    """Save sorted ticker list to a text file for reuse."""
    sorted_tickers = sorted(tickers)
    with open(path, "w") as f:
        for t in sorted_tickers:
            f.write(t + "\n")
    print(f"\nSaved {len(sorted_tickers)} tickers to {path}")


if __name__ == "__main__":
    excluded = build_exclusion_set()

    print("\n" + "=" * 65)
    print(f"TOTAL EXCLUDED TICKERS: {len(excluded)}")
    print("=" * 65)
    print(sorted(excluded))

    save_exclusion_list(excluded)

    # ── Sanity check ───────────────────────────────────────────────
    EXPECTED_FINANCIALS     = {"GARAN", "AKBNK", "ISCTR", "TERA", "EKGYO", "AKGRT"}
    EXPECTED_NON_FINANCIALS = {"THYAO", "EREGL", "BIMAS", "TUPRS"}

    print("\nSanity check:")
    for t in EXPECTED_FINANCIALS:
        mark = "OK - correctly excluded" if t in excluded else "MISSING from exclusion list"
        print(f"  {t:<8} {mark}")
    for t in EXPECTED_NON_FINANCIALS:
        mark = "OK - correctly included" if t not in excluded else "WRONGLY excluded"
        print(f"  {t:<8} {mark}")