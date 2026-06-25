import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Importamos la función que lee el M3U desde nuestro otro archivo
from extractor import parse_m3u_file

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "tu_clave_secreta")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

link_store = {}

# --- MODELOS DE DATOS (Pydantic) ---
class TokenRequest(BaseModel):
    link: str


class VerifyRequest(BaseModel):
    token: str

# --- ENDPOINTS / RUTAS ---

@app.get("/api/events")
def get_events():
    """Lee dinámicamente tu archivo 'canales.m3u' y sirve los partidos."""
    ruta_lista = "canales.m3u" 
    
    eventos = parse_m3u_file(ruta_lista)
    
    if not eventos:
        return [{"title": "Sin eventos", "time": "--:--", "category": "Default", "status": "terminado", "link": "#"}]
        
    return eventos

@app.post("/api/generate-token")
def generate_token(payload: TokenRequest):
    try:
        expiration = datetime.now(timezone.utc) + timedelta(hours=2)
        jwt_payload = {"exp": expiration, "authorized": True}
        token = jwt.encode(jwt_payload, JWT_SECRET, algorithm="HS256")
        
        link_store[token] = payload.link
        return {"token": token}
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno")

@app.get("/api/get_link")
def get_link(token: str = Query(None)):
    if not token or token not in link_store:
        raise HTTPException(status_code=400, detail="Token inválido")
    return {"link": link_store[token]}

@app.post("/api/verifique_tokens")
def verifique_tokens(payload: VerifyRequest):
    """
    Equivalente a api/verifique_tokens/router.ts
    Verifica mediante criptografía si el JWT es real, válido y no ha expirado.
    """
    if not payload.token:
        raise HTTPException(status_code=400, detail="Token no proporcionado")
        
    try:
        # Decodificar y verificar el token con la clave secreta
        decoded = jwt.decode(payload.token, JWT_SECRET, algorithms=["HS256"])
        return {"valid": True, "decoded": decoded}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Para ejecutar localmente y transmitir en tu LAN:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000