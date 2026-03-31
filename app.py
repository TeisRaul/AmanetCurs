import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template
import cloudscraper
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# --- 1. FUNCTIA PRIMA EXCHANGE ---
def get_prima_data():
    url = "https://www.primaexchange.ro/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        data = []
        rows = soup.find_all('tr')
        
        for row in rows:
            row_text = row.get_text().upper()
            if any(v in row_text for v in ["EUR", "USD", "GBP", "HUF"]):
                cells = row.find_all('td')
                if len(cells) >= 3:
                    data.append({
                        'name': cells[1].get_text(strip=True),
                        'description': cells[2].get_text(strip=True),
                        'buy': cells[3].get_text(strip=True),
                        'sell': cells[4].get_text(strip=True)
                    })
        
        if not data:
            return [{"name": "Eroare", "description": "-", "buy": "N/A", "sell": "N/A"}]
            
        return data
    except Exception as e:
        print(f"Eroare la Prima: {e}")
        return [{"name": "Eroare", "description": "-", "buy": "-", "sell": "-"}]

# --- 2. FUNCTIA EUROAMANET ---
def get_euroamanet():
    url = "https://euroamanet.ro/exchange.html"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        data = [] 
        for row in soup.find_all('tr'):
            row_text = row.get_text().upper()
            
            if any(v in row_text for v in ["EUR", "USD", "GBP", "HUF"]):
                cells = row.find_all('td')
                if len(cells) >= 3:
                    nume_valuta = cells[0].get_text(strip=True)
                    
                    if "EUR" in nume_valuta: nume_valuta = "EUR"
                    elif "USD" in nume_valuta: nume_valuta = "USD"
                    elif "GBP" in nume_valuta: nume_valuta = "GBP"
                    elif "HUF" in nume_valuta: nume_valuta = "HUF"
                    
                    data.append({
                        "name": nume_valuta,
                        "buy": cells[1].get_text(strip=True),
                        "sell": cells[2].get_text(strip=True)
                    })
        
        if not data:
            return [{"name": "Eroare", "buy": "-", "sell": "-"}]

        return data 
    except Exception as e:
        print(f"Eroare Euroamanet: {e}")
        return [{"name": "Eroare", "buy": "-", "sell": "-"}]
    
# --- 3. FUNCTIA BANCA TRANSILVANIA (CU SELENIUM SI CLICK PE COOKIES) ---
# --- 3. FUNCTIA BANCA TRANSILVANIA (CU SELENIUM SI DIV-URI MODERNE) ---
def get_bt_data():
    url = "https://www.bancatransilvania.ro/curs-valutar"
    data = []
    
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = None
    try:
        print("--> [SELENIUM] Pornesc browser-ul pentru BT...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get(url)
        print("--> [SELENIUM] Aștept să se încarce pagina...")
        time.sleep(4) 
        
        try:
            print("--> [SELENIUM] Caut butonul 'Refuz toate'...")
            cookie_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Refuz toate') or contains(text(), 'Accept toate')]")
            cookie_btn.click()
            print("--> [SELENIUM] Am dat click pe Cookies! Aștept...")
            time.sleep(3) 
        except Exception:
            print("--> [SELENIUM] Nu am găsit popup-ul. Merg mai departe.")
            
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # --- AICI E MODIFICAREA MAGICA PENTRU NOUL DESIGN ---
        # Căutăm toate div-urile care reprezintă un rând în tabel
        rows = soup.find_all('div', class_='bt-exhange-rate-table-body-row')
        print(f"--> [SELENIUM] Am găsit {len(rows)} rânduri (div-uri).")
        
        for row in rows:
            # În interiorul fiecărui rând, căutăm celulele
            cells = row.find_all('div', class_='bt-exhange-rate-table-body-row-cell')
            
            # Ne asigurăm că rândul are exact cele 4 coloane (ca să sărim peste titluri)
            if len(cells) >= 4:
                # Luăm textul din prima celulă (care conține "EUR", "USD" etc.)
                nume_valuta = cells[0].get_text(strip=True)
                
                if any(v in nume_valuta for v in ["EUR", "USD", "GBP", "HUF"]):
                    data.append({
                        "name": nume_valuta,
                        "buy": cells[2].get_text(strip=True), # Index 2 este Cumpărarea
                        "sell": cells[3].get_text(strip=True) # Index 3 este Vânzarea
                    })
                    
        if not data:
            return [{"name": "Eroare parsare HTML", "buy": "-", "sell": "-"}]
            
        print("--> [SELENIUM] Scraping BT cu succes!")
        return data
        
    except Exception as e:
        print(f"--> [SELENIUM] Eroare critică BT: {e}")
        return [{"name": "Eroare Conexiune", "buy": "-", "sell": "-"}]
    finally:
        if driver:
            driver.quit()
            
# --- 4. RUTA FLASK ---
@app.route('/')
def home():
    date_prima = get_prima_data()
    date_euro = get_euroamanet()
    date_bt = get_bt_data()
    
    return render_template('index.html', 
                           date_prima=date_prima, 
                           date_euro=date_euro, 
                           date_bt=date_bt)

if __name__ == '__main__':
    app.run(debug=True)