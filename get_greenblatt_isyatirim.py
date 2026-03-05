import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import warnings
warnings.filterwarnings('ignore')

BIST_TICKERS = [
    "AEFES", "AFYON", "AGESA", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFEN",
    "AKGRT", "AKSA", "AKSEN", "AKSGY", "AKSUE", "AKTAE", "AKYHO", "ALARK",
    "ALBRK", "ALCAR", "ALFAS", "ALGYO", "ALKIM", "ALKLC", "ANELE", "ANGEN",
    "ANHYT", "ANSGR", "ARCLK", "ARDYZ", "ARENA", "ARSAN", "ASELS", "ASGYO",
    "ASTOR", "ATLAS", "ATAGY", "ATEKS", "AVGYO", "AVHOL", "AVOD", "AYEN",
    "AYGAZ", "BAGFS", "BAKAB", "BANVT", "BAYRK", "BERA", "BFREN", "BIMAS",
    "BIOEN", "BIZIM", "BJKAS", "BNTAS", "BOBET", "BOSSA", "BRISA", "BRSAN",
    "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "CANTE",
    "CARFA", "CASA", "CEMAS", "CEMTS", "CEOEM", "CIMSA", "CLEBI", "CMBTN",
    "CMENT", "COMAR", "COSMO", "CRDFA", "CRFSA", "CUSAN", "CWENE", "DAGI",
    "DAPGM", "DARDL", "DENGE", "DERHL", "DERIM", "DESA", "DESPC", "DEVA",
    "DGATE", "DGKLB", "DGNMO", "DITAS", "DOBUR", "DOCO", "DOGUB", "DOHOL",
    "DOMEP", "DURDO", "DYOBY", "DZGYO", "ECILC", "ECZYT", "EDIP", "EGGUB",
    "EGPRO", "EGSER", "EKGYO", "ELITE", "EMKEL", "EMNIS", "ENERY", "ENJSA",
    "ENKAI", "EPLAS", "ERBOS", "ERCB", "EREGL", "ERSU", "ESCAR", "ESCOM",
    "ESEN", "ETILR", "ETYAT", "EUHOL", "EUPWR", "EUREN", "EURO", "EUYO",
    "EVREN", "FADE", "FENER", "FLAP", "FMIZP", "FONET", "FORMT", "FORTE",
    "FROTO", "FZLGY", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL", "GENTS",
    "GEREL", "GESAN", "GIPTA", "GLBMD", "GLCVY", "GLYHO", "GMTAS", "GOKNR",
    "GOLTS", "GOODY", "GOZDE", "GRSEL", "GSDDE", "GSDHO", "GSRAY", "GUBRF",
    "GWIND", "GZNMI", "HALKB", "HATEK", "HDFGS", "HEDEF", "HEKTS", "HKTM",
    "HLGYO", "HOROZ", "HTTBT", "HUNER", "HURGZ", "ICBCT", "IEYHO", "IHAAS",
    "IHEVA", "IHGZT", "IHLAS", "IHLGM", "IHYAY", "IMASM", "INDES", "INFO",
    "INGRM", "INTEM", "INVEO", "IPEKE", "ISATR", "ISBIR", "ISCTR", "ISYAT",
    "ISGSY", "ISGYO", "ISKPL", "ISKUR", "ISYHO", "ITTFK", "IZFAS", "IZINV",
    "IZMDC", "JANTS", "KAPLM", "KAREL", "KARSN", "KARTN", "KATMR", "KAYSE",
    "KCAER", "KCHOL", "KENT", "KERVN", "KERVT", "KFEIN", "KGYO", "KLGYO",
    "KLKIM", "KLMSN", "KLNMA", "KLRHO", "KLSER", "KMPUR", "KNFRT", "KONKA",
    "KONTR", "KONYA", "KOPOL", "KORDS", "KOZAA", "KOZAL", "KRDMA", "KRDMB",
    "KRDMD", "KRGYO", "KRONT", "KRSTL", "KRTEK", "KRVGD", "KSTUR", "KTLEV",
    "KUTPO", "KUVVA", "KUYAS", "LIDER", "LIDFA", "LKMNH", "LOGO", "LRSHO",
    "LUKSK", "MAALT", "MACKO", "MAGEN", "MAKIM", "MAKTK", "MANAS", "MARBL",
    "MARKA", "MARTI", "MAVI", "MEDTR", "MEGAP", "MEPET", "MERCN", "MERIT",
    "MERKO", "METRO", "METUR", "MGROS", "MHRTN", "MIATK", "MIPAZ", "MMCAS",
    "MNDRS", "MNDTR", "MNVHO", "MOBTL", "MOGAN", "MPARK", "MRGYO", "MRSHL",
    "MSGYO", "MTRKS", "MZHLD", "NATEN", "NETAS", "NTGAZ", "NUGYO", "NUHCM",
    "OBAMS", "OBASE", "ODAS", "ODINE", "OFSYM", "ONCSM", "ORCAY", "ORGE",
    "ORMA", "OSMEN", "OSTIM", "OTKAR", "OYAKC", "OYAYO", "OYLUM", "OZGYO",
    "OZKGY", "OZRDN", "OZSUB", "PAGYO", "PAMEL", "PAPIL", "PARSN", "PASEU",
    "PCILT", "PEGYO", "PEKGY", "PENGD", "PENTA", "PETKM", "PETUN", "PGSUS",
    "PINSU", "PKENT", "PLTUR", "PNLSN", "POLHO", "POLTK", "PRKAB", "PRKME",
    "PRZMA", "PSDTC", "PSGYO", "QNBFB", "QNBFL", "RAYSG", "RHEAG", "RTALB",
    "RUBNS", "RYGYO", "SAFKR", "SAHOL", "SANEL", "SANFM", "SANKO", "SARKY",
    "SASA", "SAYAS", "SDTTR", "SEKFK", "SEKUR", "SELEC", "SELGD", "SELVA",
    "SEYKM", "SILVR", "SISE", "SKBNK", "SKYLP", "SMART", "SNGYO", "SNKRN",
    "SODA", "SODSN", "SOKM", "SONME", "SRVGY", "SUMAS", "SUPRS", "SURGY",
    "SUWEN", "TABGD", "TACTR", "TATGD", "TAVHL", "TBORG", "TCELL", "TDGYO",
    "TEKTU", "TERA", "TEZOL", "THYAO", "TKFEN", "TKNSA", "TLMAN", "TMSN",
    "TOASO", "TRCAS", "TRGYO", "TRILC", "TSKB", "TSPOR", "TTKOM", "TTRAK",
    "TUCLK", "TUKAS", "TUPRS", "TUREX", "TURGG", "TURSG", "ULUFA", "ULUSE",
    "ULUUN", "UMPAS", "UNLU", "USAK", "USDTR", "UTPYA", "UZER", "VAKBN",
    "VAKFN", "VAKKO", "VANGD", "VAROL", "VCYTE", "VESBE", "VESTL", "VKFYO",
    "VKGYO", "VKING", "YAPRK", "YATAS", "YAYLA", "YBTAS", "YEOTK", "YESIL",
    "YGYO", "YIGIT", "YKBNK", "YKSLN", "YUNSA", "ZEDUR", "ZOREN", "ZRGYO"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

def parse_number(text):
    """Convert Turkish number format to float. e.g. '22.533.072.000' or '110.723,7' """
    if not text:
        return None
    text = text.strip().replace('\xa0', '').replace(' ', '')
    # Remove mn TL suffix
    text = re.sub(r'mn\s*TL', '', text, flags=re.IGNORECASE).strip()
    try:
        # Turkish format: dots as thousands sep, comma as decimal
        if ',' in text:
            text = text.replace('.', '').replace(',', '.')
        else:
            text = text.replace('.', '')
        return float(text)
    except:
        return None

def extract_after_keyword(text, keyword, chars=100):
    """Extract text right after a keyword."""
    idx = text.find(keyword)
    if idx == -1:
        return None
    return text[idx + len(keyword): idx + len(keyword) + chars]

def get_first_number(text):
    """Extract the first number from a string."""
    if not text:
        return None
    # Match numbers with dots/commas
    match = re.search(r'-?[\d]{1,3}(?:[.\d{3}])*(?:,\d+)?', text)
    if match:
        return parse_number(match.group())
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
        ebit_text = extract_after_keyword(text, "FAALİYET KARI (ZARARI)", 50)
        ebit = get_first_number(ebit_text)  # full TRY

        # ── Balance Sheet ──────────────────────────────────────────────────
        current_assets_text      = extract_after_keyword(text, "Dönen Varlıklar", 50)
        current_liab_text        = extract_after_keyword(text, "Kısa Vadeli Yükümlülükler", 50)
        total_assets_text        = extract_after_keyword(text, "TOPLAM VARLIKLAR", 50)
        intangibles_text         = extract_after_keyword(text, "Maddi Olmayan Duran Varlıklar", 50)

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
        }

    except Exception as e:
        return None


def rank_group(df, group_name, filename):
    """Rank stocks within a group and save to CSV."""
    g = df[df["Group"] == group_name].copy()
    g = g.dropna(subset=["EarningsYield", "RoC"])
    g = g[g["EarningsYield"] > 0]
    g = g[g["RoC"] > 0]

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


if __name__ == "__main__":
    main()