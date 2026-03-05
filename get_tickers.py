import pandas as pd
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

# All BIST tickers - these are the .IS suffix tickers for Yahoo Finance
# This is a comprehensive list of BIST stocks
BIST_TICKERS = [
    "AEFES", "AFYON", "AGESA", "AHGAZ", "AKBNK", "AKCNS", "AKENR", "AKFEN",
    "AKGRT", "AKSA", "AKSEN", "AKSGY", "AKSUE", "AKTAE", "AKYHO", "ALARK",
    "ALBRK", "ALCAR", "ALFAS", "ALGYO", "ALKIM", "ALKLC", "ANELE", "ANGEN",
    "ANHYT", "ANSGR", "ARASE", "ARCLK", "ARDYZ", "ARENA", "ARSAN", "ASELS",
    "ASGYO", "ASTOR", "ATLAS", "ATAGY", "ATAKP", "ATASC", "ATEKS", "AVGYO",
    "AVHOL", "AVOD", "AYCES", "AYEN", "AYGAZ", "AYGAZ", "AZTEK", "BAGFS",
    "BAKAB", "BANVT", "BASCM", "BASGZ", "BAYRK", "BERA", "BEYAZ", "BFREN",
    "BIENY", "BIGCH", "BIMAS", "BINBN", "BIOEN", "BIZIM", "BJKAS", "BKFIN",
    "BNTAS", "BOBET", "BOSSA", "BRISA", "BRKO", "BRMEN", "BRKVY", "BRSAN",
    "BRYAT", "BSOKE", "BTCIM", "BUCIM", "BURCE", "BURVA", "BVSAN", "CANTE",
    "CARFA", "CASA", "CEMAS", "CEMTS", "CEOEM", "CIMSA", "CLEBI", "CMBTN",
    "CMENT", "COMAR", "COSMO", "CRDFA", "CRFSA", "CUSAN", "CVKMD", "CWENE",
    "DAGI", "DAPGM", "DARDL", "DENGE", "DERHL", "DERIM", "DESA", "DESPC",
    "DEVA", "DGATE", "DGKLB", "DGNMO", "DITAS", "DOBUR", "DOCO", "DOGUB",
    "DOHOL", "DOMEP", "DURDO", "DYOBY", "DZGYO", "ECILC", "ECZYT", "EDIP",
    "EGGUB", "EGPRO", "EGSER", "EKGYO", "ELITE", "EMKEL", "EMNIS", "ENERY",
    "ENJSA", "ENKAI", "EPLAS", "ERBOS", "ERCB", "EREGL", "ERSU", "ESCAR",
    "ESCOM", "ESEN", "ETILR", "ETYAT", "EUHOL", "EUPWR", "EUREN", "EURO",
    "EUYO", "EVREN", "FADE", "FENER", "FLAP", "FMIZP", "FONET", "FORMT",
    "FORTE", "FROTO", "FZLGY", "GARAN", "GARFA", "GEDIK", "GEDZA", "GENIL",
    "GENTS", "GEREL", "GESAN", "GIPTA", "GLBMD", "GLCVY", "GLYHO", "GMTAS",
    "GOKNR", "GOLTS", "GOODY", "GOZDE", "GRSEL", "GSDDE", "GSDHO", "GSRAY",
    "GUBRF", "GWIND", "GZNMI", "HALKB", "HATEK", "HDFGS", "HEDEF", "HEKTS",
    "HKTM", "HLGYO", "HOROZ", "HTTBT", "HUNER", "HURGZ", "ICBCT", "IEYHO",
    "IHAAS", "IHEVA", "IHGZT", "IHLAS", "IHLGM", "IHYAY", "IMASM", "INDES",
    "INFO", "INGRM", "INTEM", "INVEO", "IPEKE", "ISATR", "ISBIR", "ISCTR",
    "ISYAT", "ISGSY", "ISGYO", "ISKPL", "ISKUR", "ISYHO", "ITTFK", "IZFAS",
    "IZINV", "IZMDC", "JANTS", "KAPLM", "KAREL", "KARSN", "KARTN", "KATMR",
    "KAYSE", "KCAER", "KCHOL", "KENT", "KERVN", "KERVT", "KFEIN", "KGYO",
    "KLGYO", "KLKIM", "KLMSN", "KLNMA", "KLRHO", "KLSER", "KMPUR", "KNFRT",
    "KONKA", "KONTR", "KONYA", "KOPOL", "KORDS", "KORTHK", "KOZAA", "KOZAL",
    "KRDMA", "KRDMB", "KRDMD", "KRGYO", "KRONT", "KRPLAS", "KRSTL", "KRTEK",
    "KRVGD", "KSTUR", "KTLEV", "KUTPO", "KUVVA", "KUYAS", "KZBGY", "LIDER",
    "LIDFA", "LKMNH", "LOGO", "LRSHO", "LUKSK", "MAALT", "MACKO", "MAGEN",
    "MAKIM", "MAKTK", "MANAS", "MARBL", "MARKA", "MARTI", "MAVI", "MEDTR",
    "MEGAP", "MEPET", "MERCN", "MERIT", "MERKO", "METRO", "METUR", "MGROS",
    "MHRTN", "MIATK", "MIPAZ", "MMCAS", "MNDRS", "MNDTR", "MNVHO", "MOBTL",
    "MOGAN", "MPARK", "MRGYO", "MRSHL", "MSGYO", "MTRKS", "MZHLD", "NATEN",
    "NETAS", "NTGAZ", "NUGYO", "NUHCM", "OBAMS", "OBASE", "ODAS", "ODINE",
    "OFSYM", "ONCSM", "ORCAY", "ORGE", "ORMA", "OSMEN", "OSTIM", "OTKAR",
    "OYAKC", "OYAYO", "OYLUM", "OZGYO", "OZKGY", "OZRDN", "OZSUB", "PAGYO",
    "PAMEL", "PAPIL", "PARSN", "PASEU", "PCILT", "PEGYO", "PEKGY", "PENGD",
    "PENTA", "PETKM", "PETUN", "PGSUS", "PINSU", "PKENT", "PLTUR", "PNLSN",
    "POLHO", "POLTK", "PONDUS", "PRKAB", "PRKME", "PRZMA", "PSDTC", "PSGYO",
    "QNBFB", "QNBFL", "RAYSG", "RHEAG", "RTALB", "RUBNS", "RYGYO", "SAFKR",
    "SAHOL", "SANEL", "SANFM", "SANKO", "SARKY", "SASA", "SAYAS", "SDTTR",
    "SEKFK", "SEKUR", "SELEC", "SELGD", "SELVA", "SEYKM", "SILVR", "SISE",
    "SKBNK", "SKYLP", "SMART", "SNGYO", "SNKRN", "SODA", "SODSN", "SOKM",
    "SONME", "SRVGY", "SUMAS", "SUPRS", "SURGY", "SUWEN", "TABGD", "TACTR",
    "TATGD", "TAVHL", "TBORG", "TCELL", "TDGYO", "TEKTU", "TERA", "TEZOL",
    "THYAO", "TKFEN", "TKNSA", "TLMAN", "TMSN", "TOASO", "TRCAS", "TRGYO",
    "TRILC", "TSKB", "TSPOR", "TTKOM", "TTRAK", "TUCLK", "TUKAS", "TUPRS",
    "TUREX", "TURGG", "TURSG", "ULUFA", "ULUSE", "ULUUN", "UMPAS", "UNLU",
    "USAK", "USDTR", "UTPYA", "UZER", "VAKBN", "VAKFN", "VAKKO", "VANGD",
    "VAROL", "VCYTE", "VESBE", "VESTL", "VKFYO", "VKGYO", "VKING", "YAPRK",
    "YATAS", "YAYLA", "YBTAS", "YEOTK", "YESIL", "YGYO", "YIGIT", "YKBNK",
    "YKSLN", "YUNSA", "ZEDUR", "ZOREN", "ZRGYO"
]

def test_tickers(sample_size=5):
    """Test a few tickers to make sure yfinance works"""
    sample = BIST_TICKERS[:sample_size]
    print(f"Testing {sample_size} tickers with yfinance...")
    
    for ticker in sample:
        yf_ticker = ticker + ".IS"
        try:
            info = yf.Ticker(yf_ticker).info
            name = info.get("shortName", "N/A")
            pe = info.get("trailingPE", "N/A")
            roa = info.get("returnOnAssets", "N/A")
            roe = info.get("returnOnEquity", "N/A")
            print(f"  {yf_ticker:12} | {name:30} | P/E: {pe} | RoA: {roa} | RoE: {roe}")
        except Exception as e:
            print(f"  {yf_ticker:12} | ERROR: {e}")



def fetch_all_to_csv(filename="bist_fundamentals.csv"):
    results = []
    total = len(BIST_TICKERS)
    
    for i, ticker in enumerate(BIST_TICKERS):
        yf_ticker = ticker + ".IS"
        try:
            info = yf.Ticker(yf_ticker).info
            if not info or info.get("regularMarketPrice") is None:
                print(f"[{i+1}/{total}] {ticker} - SKIPPED (no data)")
                continue
            results.append({
                "Ticker": ticker,
                "Name": info.get("shortName", "N/A"),
                "PE": info.get("trailingPE", None),
                "RoA": info.get("returnOnAssets", None),
                "RoE": info.get("returnOnEquity", None),
            })
            print(f"[{i+1}/{total}] {ticker} - OK")
        except Exception as e:
            print(f"[{i+1}/{total}] {ticker} - ERROR: {e}")

    df = pd.DataFrame(results)
    df.to_csv(filename, index=False)
    print(f"\nSaved {len(df)} stocks to {filename}")

if __name__ == "__main__":
    fetch_all_to_csv()