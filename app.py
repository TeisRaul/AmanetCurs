import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template

app = Flask(__name__)

def get_prima_data():
    url = "https://www.primaexchange.ro/"
    # User-Agent complet ca să nu ne blocheze site-ul
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        data = []
        # Căutăm toate rândurile de tabel (tr)
        rows = soup.find_all('tr')
        
        for row in rows:
            row_text = row.get_text().upper()
            # Verificăm dacă rândul conține una din valutele dorite
            if any(v in row_text for v in ["EUR", "USD", "GBP", "HUF"]):
                cells = row.find_all('td')
                if len(cells) >= 3:
                    # cells[0] e numele, cells[1] e Cumpărare, cells[2] e Vânzare
                    currency_full = cells[0].get_text(strip=True)
                    data.append({
                        'name': cells[1].get_text(strip=True),
                        'description': cells[2].get_text(strip=True),
                        'buy': cells[3].get_text(strip=True),
                        'sell': cells[4].get_text(strip=True)
                    })
        
        # Dacă nu am găsit nimic, punem niște date de rezervă să nu fie tabelul gol
        if not data:
            return [{"name": "Eroare", "buy": "N/A", "sell": "N/A"}]
            
        return data
    except Exception as e:
        print(f"Eroare la scraping: {e}")
        return [{"name": "Eroare", "buy": "-", "sell": "-"}]

@app.route('/')
def home():
    # Luăm datele proaspete de pe site
    date_curs = get_prima_data()
    # Trimitem datele către index.html (asigură-te că variabila se numește 'cursuri')
    return render_template('index.html', cursuri=date_curs)

if __name__ == '__main__':
    # Pornim serverul
    app.run(debug=True)