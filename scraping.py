import requests
from bs4 import BeautifulSoup

def get_prima_exchange():
    url = "https://www.primaexchange.ro/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Căutăm tabelul de curs valutar (de obicei e primul tabel din pagină)
        # Identificăm rândul care conține textul "EUR"
        eur_row = None
        for row in soup.find_all('tr'):
            if "EUR" in row.get_text():
                eur_row = row
                break
        
        if eur_row:
            # Extragem toate celulele (td) din acel rând
            cells = eur_row.find_all('td')
            # De regulă: cells[0]=Steag/Nume, cells[1]=Cumparare, cells[2]=Vanzare
            buy = cells[1].get_text(strip=True)
            sell = cells[2].get_text(strip=True)
            
            return {
                "nume": "Prima Exchange",
                "valuta": "EUR",
                "cumparare": buy,
                "vanzare": sell
            }
        
        return "Nu am găsit rândul cu EUR."

    except Exception as e:
        return f"Eroare: {e}"

print(get_prima_exchange())