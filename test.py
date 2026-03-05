import requests
from bs4 import BeautifulSoup
import re
import warnings
warnings.filterwarnings('ignore')

url = "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/sirket-karti.aspx?hisse=AEFES"
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
response = requests.get(url, headers=headers, timeout=20, verify=False)
soup = BeautifulSoup(response.text, "lxml")
text = soup.get_text()

keywords = ["Piyasa Değeri", "Net Borç", "FAALİYET KARI (ZARARI)"]
for kw in keywords:
    idx = text.find(kw)
    if idx != -1:
        print(f"\n--- {kw} ---")
        print(repr(text[idx:idx+80]))