import traceback
import jwt
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone

# Imports absolutos a la arquitectura modular
from app.core.security import generate_jwt_token, verify_jwt_token, JWT_EXPIRATION_HOURS
from app.core.cache import events_cache, link_store
from app.schemas.iptv_schemas import (
    TokenRequest, TokenResponse, VerifyRequest, VerifyResponse, LinkResponse
)
from app.services.orquestador_iptv import ejecutar_pipeline_iptv, pipeline_stream_iptv

# NOTA: Ya no usamos clases estáticas bloqueantes, usamos las funciones asíncronas
# de iptv_service.py para no bloquear el Event Loop de FastAPI.

router = APIRouter(tags=["IPTV & Tokens"])

@router.get("/events")
async def get_events():
    """
    Obtiene la estructura completa de canales IPTV del pipeline.
    Retorna un dict con claves 'total', 'paises' y 'categorias'.
    """
    # Si la caché está vacía, invocamos el pipeline de 4 estaciones
    if not events_cache["data"]:
        try:
            datos = await ejecutar_pipeline_iptv()
            events_cache["data"] = datos
            events_cache["last_updated"] = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            print("\n" + "="*60)
            print("💥 ERROR CRÍTICO EN EL PIPELINE DENTRO DEL ENDPOINT:")
            traceback.print_exc()  # Esto va a escupir toda la traza en la terminal
            print("="*60 + "\n")
            raise HTTPException(status_code=500, detail=f"Error cargando eventos: {str(e)}")
            
    data = events_cache["data"]
    if not data or data.get("total", 0) == 0:
        # Respuesta vacía con estructura compatible
        return {
            "total": 0,
            "paises": {},
            "categorias": {
                "Deportes": [], "Peliculas": [], "TV": [], "Otros": []
            }
        }
    return data

@router.get("/events/category/{category}")
def get_events_by_category(category: str):
    """
    Filtra canales por categoría usando la caché en memoria.
    Las categorías válidas son: Deportes, Peliculas, TV, Otros.
    """
    data = events_cache.get("data", {})
    categorias = data.get("categorias", {})

    # Búsqueda case-insensitive entre las claves disponibles
    categoria_key = next(
        (k for k in categorias if k.lower() == category.lower()), None
    )

    if not categoria_key or not categorias[categoria_key]:
        return {"message": f"No hay canales en la categoría: {category}", "data": []}

    return {"categoria": categoria_key, "data": categorias[categoria_key]}

@router.post("/refresh-events")
async def refresh_events():
    """Fuerza la recarga completa del pipeline de 4 estaciones."""
    try:
        datos = await ejecutar_pipeline_iptv()
        events_cache["data"] = datos
        events_cache["last_updated"] = datetime.now(timezone.utc).isoformat()
        total = datos.get("total", 0)
        return {
            "status": "success",
            "message": f"✅ {total:,} canales cargados en el pipeline",
            "total": total,
            "paises_procesados": list(datos.get("paises", {}).keys()),
            "last_updated": events_cache["last_updated"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar eventos: {str(e)}")

# ==========================================
# ENDPOINT DE STREAMING (NDJSON en tiempo real)
# ==========================================

@router.get("/stream-canales")
async def stream_canales():
    """
    Endpoint de streaming NDJSON.

    Inicia el pipeline de IPTV y transmite los resultados al cliente
    en tiempo real, país por país, sin esperar a que todo termine.

    Formato de respuesta: application/x-ndjson
    Cada línea es un objeto JSON independiente terminado en \\n.

    Tipos de eventos:
      - { "type": "progress", "country": "mx", "percent": 10, "message": "..." }
      - { "type": "data",     "payload": { "country": "mx", "channels": [...] } }
      - { "type": "error",   "country": "mx", "message": "..." }
      - { "type": "done",    "total": 487, "message": "..." }

    El cliente debe leer el body como un ReadableStream y parsear
    cada línea como JSON independiente.
    """
    return StreamingResponse(
        pipeline_stream_iptv(),
        media_type="application/x-ndjson",
        headers={
            # Deshabilitar buffering en proxies intermedios (nginx, etc.)
            "X-Accel-Buffering": "no",
            # Mantener la conexión abierta durante todo el pipeline
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ==========================================
# ENDPOINTS DE SEGURIDAD JWT (Restaurados)
# ==========================================

@router.post("/generate-token", response_model=TokenResponse)
def generate_token(payload: TokenRequest):
    if not payload.link:
        raise HTTPException(status_code=400, detail="El campo 'link' es obligatorio")
    try:
        token = generate_jwt_token()
        link_store[token] = payload.link
        return TokenResponse(token=token, expires_in_hours=JWT_EXPIRATION_HOURS)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al generar token")

@router.get("/get_link", response_model=LinkResponse)
def get_link(token: str = Query(..., description="JWT token")):
    if not token:
        raise HTTPException(status_code=400, detail="Token no proporcionado")
    if token not in link_store:
        raise HTTPException(status_code=401, detail="Token expirado o inválido")
    try:
        verify_jwt_token(token)
        return LinkResponse(link=link_store[token])
    except jwt.ExpiredSignatureError:
        del link_store[token]
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

@router.post("/verifique_tokens", response_model=VerifyResponse)
def verify_token(payload: VerifyRequest):
    if not payload.token:
        raise HTTPException(status_code=400, detail="Token no proporcionado")
    try:
        decoded = verify_jwt_token(payload.token)
        expiration_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc).isoformat()
        return VerifyResponse(valid=True, expires_at=expiration_time, message="Token válido")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")