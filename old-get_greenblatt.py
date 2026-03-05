import yfinance as yf
import pandas as pd
import logging
import warnings
warnings.filterwarnings('ignore')
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

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


def get_value(df, row_keywords):
    """Helper to find a row in financial statements by keyword."""
    if df is None or df.empty:
        return None
    for keyword in row_keywords:
        matches = [idx for idx in df.index if keyword.lower() in str(idx).lower()]
        if matches:
            val = df.loc[matches[0]].iloc[0]
            if pd.notna(val):
                return float(val)
    return None


def fetch_greenblatt_data(ticker):
    """
    Fetches:
    - EBIT
    - Enterprise Value  → Earnings Yield = EBIT / EV
    - Net Working Capital (Current Assets - Current Liabilities)
    - Net Fixed Assets (Total Assets - Current Assets - Intangibles)
    → Return on Capital = EBIT / (NWC + NFA)
    """
    yf_ticker = ticker + ".IS"
    stock = yf.Ticker(yf_ticker)

    try:
        info = stock.info
        if not info or info.get("regularMarketPrice") is None:
            return None

        # ── From .info ─────────────────────────────────────────────────────
        ev = info.get("enterpriseValue")
        ebitda = info.get("ebitda")

        # ── Income Statement (for EBIT) ────────────────────────────────────
        inc = stock.quarterly_financials
        ebit = get_value(inc, ["EBIT", "Operating Income", "Operating income"])

        # If EBIT not directly available, use EBITDA - D&A as fallback
        if ebit is None and ebitda:
            da = get_value(inc, ["Depreciation", "DepreciationAndAmortization"])
            if da:
                ebit = ebitda - da
            else:
                ebit = ebitda  # rough proxy

        # ── Balance Sheet ──────────────────────────────────────────────────
        bs = stock.quarterly_balance_sheet

        current_assets      = get_value(bs, ["Current Assets", "TotalCurrentAssets"])
        current_liabilities = get_value(bs, ["Current Liabilities", "TotalCurrentLiabilities"])
        total_assets        = get_value(bs, ["Total Assets", "TotalAssets"])
        intangibles         = get_value(bs, ["Intangible Assets", "IntangibleAssets", "Goodwill And Intangible"])

        # ── Calculate Metrics ──────────────────────────────────────────────
        earnings_yield = None
        if ebit and ev and ev > 0:
            earnings_yield = ebit / ev

        roc = None
        if ebit and current_assets and current_liabilities and total_assets:
            nwc = current_assets - current_liabilities
            nfa = total_assets - current_assets - (intangibles or 0)
            capital = nwc + nfa
            if capital > 0:
                roc = ebit / capital

        return {
            "Ticker":           ticker,
            "Name":             info.get("shortName", "N/A"),
            "EBIT":             ebit,
            "EnterpriseValue":  ev,
            "EarningsYield":    earnings_yield,
            "RoC":              roc,
        }

    except Exception:
        return None


def main():
    results = []
    total = len(BIST_TICKERS)

    for i, ticker in enumerate(BIST_TICKERS):
        data = fetch_greenblatt_data(ticker)
        if data and data["EarningsYield"] is not None and data["RoC"] is not None:
            results.append(data)
            print(f"[{i+1}/{total}] {ticker} - OK | EY: {data['EarningsYield']:.4f} | RoC: {data['RoC']:.4f}")
        else:
            print(f"[{i+1}/{total}] {ticker} - SKIPPED")

    df = pd.DataFrame(results)
    df.to_csv("bist_greenblatt.csv", index=False)
    print(f"\nSaved {len(df)} stocks to bist_greenblatt.csv")


if __name__ == "__main__":
    main()