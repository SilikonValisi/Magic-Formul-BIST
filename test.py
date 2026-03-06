import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

url = "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/sirket-karti.aspx?hisse=TKNSA"
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
response = requests.get(url, headers=headers, timeout=20, verify=False)
from bs4 import BeautifulSoup
soup = BeautifulSoup(response.text, "lxml")
text = soup.get_text()

for kw in ["Net Faaliyet Kar", "Finansman Gideri Öncesi", "DÖNEM KARI"]:
    idx = text.find(kw)
    if idx != -1:
        print(f"{kw}: {text[idx:idx+60]}")