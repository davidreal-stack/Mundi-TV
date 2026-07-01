import re
from typing import List, Dict, Any

CORRECTIONS = {
    "Espn": "ESPN",
    "Espnpremium": "ESPN Premium",
    "Espnplus": "ESPN Plus",
    "Espndeportes": "ESPN Deportes",
    "Dazn": "DAZN",
    "Starplus": "Star Plus",
    "Staraction": "Star Action",
    "Starcine": "Star Cine",
    "Paramount": "Paramount",
    "Foxsports": "Fox Sports",
    "Fox Sportspremium": "Fox Sports Premium",
    "Fox Deportes": "Fox Deportes",
    "Foxaction": "Fox Action",
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
    "Hbo Max": "HBO Max",
    "Canalplus": "Canal Plus",
    "Laliga": "La Liga",
    "Laligahypermotion": "La Liga Hypermotion",
    "Atp": "ATP",
    "Nfl": "NFL",
    "Nba": "NBA",
    "Nhl": "NHL",
    "Mlb": "MLB",
    "Seriea": "Serie A",
    "Bundesliga": "Bundesliga",
    "Eredivisie": "Eredivisie",
    "Premierleague": "Premier League",
    "Superlig": "Super Lig",
    "Primera": "Primera División",
    "Ascenso": "Ascenso MX",
    "Liganacional": "Liga Nacional",
    "Championsleague": "Champions League",
    "Libertadores": "Copa Libertadores",
    "Sudamericana": "Copa Sudamericana",
    "Concacaf": "CONCACAF",
    "Deporte1": "Deporte 1",
    "Deporte2": "Deporte 2",
    "Tdp": "Teledeporte",
    "Rcn": "RCN",
    "Beinsport": "Bein Sport",
    "Movistar": "Movistar",
    "Plusfutbol": "Plus Fútbol",
    "Plusdeportes": "Plus Deportes",
    "Verliga": "Ver Liga",
}


def clean_channel_name(raw_name: str) -> str:
    """
    Limpia el nombre del canal aplicando correcciones y formatos estándar.
    
    Args:
        raw_name: Nombre sin procesar del canal
        
    Returns:
        Nombre limpio y formateado
    """
    # Reemplazar guiones bajos y espacios extras
    name = raw_name.replace("_", " ").replace("-", " ").strip()
    
    # Aplicar correcciones del diccionario (case-insensitive)
    for key, corrected_value in CORRECTIONS.items():
        name = re.sub(rf'\b{re.escape(key)}\b', corrected_value, name, flags=re.IGNORECASE)
    
    # Eliminar números al final
    name = re.sub(r'\s*\d+\s*$', '', name).strip()
    
    # Remover caracteres especiales innecesarios
    name = re.sub(r'[^\w\s\-\.]', '', name)
    
    # Capitalizar correctamente
    return " ".join([word.capitalize() for word in name.split() if word])


def categorize_channel(title: str) -> str:
    """
    Determina la categoría del canal basada en su nombre.
    
    Args:
        title: Nombre del canal
        
    Returns:
        Categoría del canal
    """
    title_lower = title.lower()
    
    if any(word in title_lower for word in ['nfl', 'football', 'nba', 'nhl', 'mlb']):
        return "Deportes USA"
    elif any(word in title_lower for word in ['atp', 'tenis', 'wimbledon', 'roland garros']):
        return "Tenis"
    elif any(word in title_lower for word in ['nba', 'basketball', 'baloncesto']):
        return "Baloncesto"
    elif any(word in title_lower for word in ['hbo', 'cine', 'película', 'netflix', 'disney', 'paramount']):
        return "Películas"
    else:
        return "Fútbol"


def parse_m3u_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parsea un archivo M3U y extrae los canales con sus URLs.
    
    Args:
        file_path: Ruta del archivo M3U
        
    Returns:
        Lista de diccionarios con información de cada canal
    """
    events = []
    current_title = "Canal Desconocido"
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                
                # Ignorar líneas vacías y comentarios que no sean EXTINF
                if not line or (line.startswith("#") and not line.startswith("#EXTINF")):
                    continue
                
                # Procesar líneas EXTINF para extraer nombre del canal
                if line.startswith("#EXTINF"):
                    parts = line.split(",", 1)
                    if len(parts) > 1:
                        raw_name = parts[1].strip()
                        current_title = clean_channel_name(raw_name) or "Canal Desconocido"
                
                # Procesar URLs de streaming
                elif line.startswith(("http://", "https://", "dash://")):
                    if current_title:
                        category = categorize_channel(current_title)
                        is_dash = line.startswith("dash://")
                        
                        event_data = {
                            "id": len(events) + 1,
                            "title": current_title,
                            "time": "En Vivo",
                            "category": category,
                            "status": "en vivo",
                            "resolution": "HD"
                        }
                        
                        if is_dash:
                            event_data["type"] = "dash"
                            event_data["content_id"] = line.replace("dash://", "").strip()
                            event_data["link"] = "#"
                        else:
                            event_data["type"] = "hls"
                            event_data["link"] = line
                            
                        events.append(event_data)
    
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {file_path}")
    except Exception as e:
        print(f"❌ Error al procesar {file_path}: {str(e)}")
    
    return events
