import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from contextlib import asynccontextmanager
import sys
import asyncio


import jwt
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from extractor import parse_m3u_file
from core.browser_manager import BrowserManager
from api.routes import router as stream_router

# ═════════════════════════════════════════════════════════════════
# CONFIGURACIÓN INICIAL
# ═════════════════════════════════════════════════════════════════

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "tu_clave_secreta_super_segura_change_me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 2

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Iniciando Mundi TV API y BrowserManager...")
    refresh_events_cache()
    app.state.browser_manager = await BrowserManager.get_instance()
    yield
    print("[INFO] Apagando BrowserManager...")
    await app.state.browser_manager.shutdown()

# Crear aplicación FastAPI
app = FastAPI(
    title="Mundi TV API",
    description="API Backend para streaming de eventos deportivos",
    version="1.0.0",
    lifespan=lifespan
)

# Registrar el router de streaming DASH
app.include_router(stream_router)


# ═════════════════════════════════════════════════════════════════
# MIDDLEWARE CORS
# ═════════════════════════════════════════════════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios reales
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═════════════════════════════════════════════════════════════════
# ALMACENAMIENTO EN MEMORIA
# ═════════════════════════════════════════════════════════════════

link_store: Dict[str, str] = {}  # {token: link_original}
events_cache: Dict[str, Any] = {
    "data": [],
    "last_updated": None
}

# ═════════════════════════════════════════════════════════════════
# MODELOS PYDANTIC
# ═════════════════════════════════════════════════════════════════

class TokenRequest(BaseModel):
    """Solicitud para generar un token JWT"""
    link: str

    class Config:
        json_schema_extra = {
            "example": {
                "link": "https://example.com/stream.m3u8?token=abc123"
            }
        }


class VerifyRequest(BaseModel):
    """Solicitud para verificar un token JWT"""
    token: str

    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class TokenResponse(BaseModel):
    """Respuesta con token generado"""
    token: str
    expires_in_hours: int


class LinkResponse(BaseModel):
    """Respuesta con el enlace real"""
    link: str


class VerifyResponse(BaseModel):
    """Respuesta de verificación de token"""
    valid: bool
    expires_at: str = None
    message: str = "Token válido"


# ═════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═════════════════════════════════════════════════════════════════

def generate_jwt_token(data: Dict[str, Any] = None) -> str:
    """
    Genera un token JWT con expiración.
    
    Args:
        data: Datos adicionales a incluir en el token
        
    Returns:
        Token JWT codificado
    """
    payload = data or {}
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload.update({
        "exp": expiration,
        "iat": datetime.now(timezone.utc),
        "authorized": True
    })
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verifica la validez de un token JWT.
    
    Args:
        token: Token JWT a verificar
        
    Returns:
        Datos decodificados del token
        
    Raises:
        jwt.ExpiredSignatureError: Si el token ha expirado
        jwt.InvalidTokenError: Si el token es inválido
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def refresh_events_cache():
    """Recarga el caché de eventos desde el archivo M3U."""
    try:
        m3u_path = "canales.m3u"
        if os.path.exists(m3u_path):
            events_cache["data"] = parse_m3u_file(m3u_path)
            events_cache["last_updated"] = datetime.now(timezone.utc).isoformat()
        else:
            print(f"⚠️  Archivo {m3u_path} no encontrado")
            events_cache["data"] = []
    except Exception as e:
        print(f"❌ Error al actualizar caché: {str(e)}")
        events_cache["data"] = []


# ═════════════════════════════════════════════════════════════════
# RUTAS / ENDPOINTS
# ═════════════════════════════════════════════════════════════════


@app.get("/", tags=["Root"])
def root():
    """Endpoint raíz - Información del servidor"""
    return {
        "service": "Mundi TV API",
        "version": "1.0.0",
        "status": "🟢 Online",
        "endpoints": {
            "events": "/api/events",
            "generate_token": "/api/generate-token",
            "get_link": "/api/get_link",
            "verify_token": "/api/verifique_tokens"
        }
    }


@app.get("/api/events", tags=["Events"])
def get_events():
    """
    Obtiene la lista completa de eventos en vivo desde el archivo M3U.
    
    Returns:
        Lista de eventos con sus detalles (nombre, categoría, link, etc.)
    """
    if not events_cache["data"]:
        # Reintenta cargar los eventos
        refresh_events_cache()
    
    data = events_cache["data"]
    
    if not data:
        return [{
            "id": 0,
            "title": "Sin eventos disponibles",
            "time": "--:--",
            "category": "Sin categoría",
            "status": "offline",
            "link": "#",
            "resolution": "--"
        }]
    
    return data


@app.get("/api/events/category/{category}", tags=["Events"])
def get_events_by_category(category: str):
    """
    Obtiene eventos filtrados por categoría.
    
    Args:
        category: Categoría a filtrar (Fútbol, NFL, ATP, Tenis, etc.)
        
    Returns:
        Lista de eventos de la categoría especificada
    """
    all_events = events_cache["data"]
    
    filtered = [
        event for event in all_events
        if event["category"].lower() == category.lower()
    ]
    
    if not filtered:
        return {
            "message": f"No hay eventos en la categoría: {category}",
            "data": []
        }
    
    return filtered


@app.post("/api/generate-token", tags=["Token"], response_model=TokenResponse)
def generate_token(payload: TokenRequest):
    """
    Genera un token JWT para ocultar el link real del stream.
    
    El token tiene validez de 2 horas y se almacena en memoria asociado al link.
    
    Args:
        payload: Objeto TokenRequest con el link a proteger
        
    Returns:
        TokenResponse con el token generado y tiempo de expiración
        
    Raises:
        HTTPException: Si hay error en la generación del token
    """
    if not payload.link:
        raise HTTPException(status_code=400, detail="El campo 'link' es obligatorio")
    
    try:
        # Generar token JWT
        token = generate_jwt_token()
        
        # Almacenar asociación token -> link
        link_store[token] = payload.link
        
        print(f"✅ Token generado: {token[:20]}... para link: {payload.link[:50]}...")
        
        return TokenResponse(
            token=token,
            expires_in_hours=JWT_EXPIRATION_HOURS
        )
    
    except Exception as e:
        print(f"❌ Error generando token: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al generar token")


@app.get("/api/get_link", tags=["Token"])
def get_link(token: str = Query(..., description="JWT token para recuperar el link")) -> LinkResponse:
    """
    Recupera el link real asociado a un token JWT válido.
    
    Args:
        token: Token JWT válido
        
    Returns:
        LinkResponse con el link real del stream
        
    Raises:
        HTTPException: Si el token es inválido o no existe
    """
    if not token:
        raise HTTPException(status_code=400, detail="Token no proporcionado")
    
    if token not in link_store:
        raise HTTPException(status_code=401, detail="Token no válido o expirado")
    
    try:
        # Verificar que el token JWT sea auténtico
        verify_jwt_token(token)
        
        link = link_store[token]
        print(f"✅ Link recuperado exitosamente para token: {token[:20]}...")
        
        return LinkResponse(link=link)
    
    except jwt.ExpiredSignatureError:
        # Limpiar token expirado
        del link_store[token]
        raise HTTPException(status_code=401, detail="Token expirado")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido o corrupto")


@app.post("/api/verifique_tokens", tags=["Token"], response_model=VerifyResponse)
def verify_token(payload: VerifyRequest):
    """
    Verifica criptográficamente la autenticidad y validez de un token JWT.
    
    Valida la firma, el algoritmo y la fecha de expiración del token.
    
    Args:
        payload: Objeto VerifyRequest con el token a verificar
        
    Returns:
        VerifyResponse indicando si el token es válido
        
    Raises:
        HTTPException: Si el token es inválido o ha expirado
    """
    if not payload.token:
        raise HTTPException(status_code=400, detail="Token no proporcionado")
    
    try:
        # Decodificar y verificar el token
        decoded = verify_jwt_token(payload.token)
        
        expiration_time = datetime.fromtimestamp(
            decoded["exp"], 
            tz=timezone.utc
        ).isoformat()
        
        return VerifyResponse(
            valid=True,
            expires_at=expiration_time,
            message="Token válido y autenticado"
        )
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expirado"
        )
    
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token inválido: {str(e)}"
        )


@app.post("/api/refresh-events", tags=["Events"])
def refresh_events():
    """
    Fuerza la recarga del caché de eventos desde el archivo M3U.
    Útil si se actualiza manualmente el archivo.
    """
    try:
        refresh_events_cache()
        return {
            "status": "success",
            "message": f"✅ {len(events_cache['data'])} eventos cargados",
            "last_updated": events_cache["last_updated"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar eventos: {str(e)}"
        )


@app.get("/health", tags=["Health"])
def health_check():
    """Health check del servidor - Usado para monitoreo"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "events_loaded": len(events_cache["data"]),
        "tokens_active": len(link_store)
    }


# ═════════════════════════════════════════════════════════════════
# EJECUCIÓN
# ═════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    print("🎬 Iniciando Mundi TV Backend en puerto 8000...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# Para ejecutar manualmente:
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
