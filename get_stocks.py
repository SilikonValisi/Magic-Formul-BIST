import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

url = "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/Temel-Degerler-Ve-Oranlar.aspx"
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

response = requests.get(url, headers=headers, timeout=15, verify=False)
soup = BeautifulSoup(response.text, "lxml")

# Tüm ticker'ları çek
tickers = []
for option in soup.find_all("option"):
    val = option.get("value", "").strip()
    if val and len(val) <= 6 and val.isupper():
        tickers.append(val)

tickers = sorted(set(tickers))
print(f"Toplam: {len(tickers)} hisse")

# Dosyaya yaz
with open("bist_tickers.txt", "w") as f:
    for t in tickers:
        f.write(t + "\n")

print("Kaydedildi: bist_tickers.txt")