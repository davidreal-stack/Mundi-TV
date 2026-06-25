import re

CORRECTIONS = {
    "Espn": "ESPN",
    "Espnpremium": "ESPN Premium",
    "Espnplus": "ESPN Plus",
    "Dazn": "DAZN",
    "Starplus": "Star Plus",
    "Paramount": "Paramount",
    "Foxsports": "Fox Sports",
    "Fox Sportspremium": "Fox Sports Premium",
    "Fox Deportes": "Fox Deportes",
    "Univision": "Univisión",
    "Winsports": "Win Sports",
    "Dsports": "D Sports",
    "Tycsports": "TyC Sports",
    "Telefe": "Telefe",
    "Tvpublica": "TV Pública",
    "Liga1max": "Liga 1 MAX",
    "Goltv": "GolTV",
    "Golperú": "GolPerú",
    "Aztecadeportes": "Azteca Deportes",
    "Movistarlaliga": "Movistar LaLiga",
    "Movistarligadecampeones": "Movistar Liga de Campeones",
    "Skybundesliga": "Sky Bundesliga",
    "Premieresports": "Premier Sports",
    "Sporttv": "Sport TV",
    "Staraction": "Star Action",
    "Starcine": "Star Cine",
    "Hbo Max": "HBO Max",
    "Canalplus": "Canal Plus",
    "LaLiga": "La Liga",
    "Laligahypermotion": "La Liga Hypermotion",
    "Atp": "ATP",
    "Nfl": "NFL",
    "Nba": "NBA",
    "Seriea": "Serie A",
    "Bundesliga": "Bundesliga",
    "Eredivisie": "Eredivisie",
    "Premierleague": "Premier League",
    "Superlig": "Super Lig",
    "Primera": "Primera División",
    "Ascenso": "Ascenso MX",
    "Liganacional": "Liga Nacional",
    "Championsleague": "Champions League",
    "Concacaf": "CONCACAF",
}

def clean_channel_name(raw_name: str) -> str:
    name = raw_name.replace("_", " ").strip()
    for key, corrected_value in CORRECTIONS.items():
        name = re.sub(re.escape(key), corrected_value, name, flags=re.IGNORECASE)
    name = re.sub(r'\d+$', '', name).strip()
    return " ".join([word.capitalize() for word in name.split()])

def parse_m3u_file(file_path: str) -> list:
    """Esta es la función que main.py necesita encontrar"""
    events = []
    current_title = "Canal Desconocido"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#EXTINF"):
                    parts = line.split(",")
                    if len(parts) > 1:
                        raw_name = parts[-1].strip()
                        current_title = clean_channel_name(raw_name)
                elif line.startswith("http"):
                    category = "Fútbol"
                    if "nfl" in current_title.lower():
                        category = "NFL"
                    elif "atp" in current_title.lower():
                        category = "ATP"
                    
                    events.append({
                        "title": current_title,
                        "time": "En Vivo",
                        "category": category,
                        "status": "en vivo",
                        "link": line
                    })
    except FileNotFoundError:
        print(f"¡Alerta! No se encontró el archivo: {file_path}")
    return events