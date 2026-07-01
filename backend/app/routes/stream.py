from fastapi import APIRouter, Request, HTTPException
from app.core.cache import ManifestCache
from app.services.dash_capture import capture_manifest_url

router = APIRouter()
# Caché de manifiestos con TTL de 300 segundos (5 minutos)
manifest_cache = ManifestCache(ttl_seconds=300)

@router.get("/stream/{content_id}/manifest", tags=["Streaming"])
async def get_manifest(content_id: str, request: Request):
    """
    Obtiene la URL del manifiesto .mpd fresca para el canal solicitado.
    Utiliza caché local y evita stampedes mediante bloqueos concurrentes por canal.
    """
    valid_channels = ["azteca-7", "azteca-uno", "adn40"]
    if content_id not in valid_channels:
        raise HTTPException(
            status_code=400, 
            detail=f"Canal inválido '{content_id}'. Canales soportados: {', '.join(valid_channels)}"
        )

    # 1. Intento de cache hit directo
    cached = manifest_cache.get(content_id)
    if cached:
        print(f"[INFO] Cache HIT para '{content_id}'")
        return {
            "manifest_url": cached, 
            "source": "cache",
            "content_id": content_id
        }

    # 2. Lock por content_id para prevenir Cache Stampede
    lock = manifest_cache.get_lock(content_id)
    async with lock:
        # Re-chequeo dentro del lock (otro request pudo haber resuelto la automatización)
        cached = manifest_cache.get(content_id)
        if cached:
            print(f"[INFO] Cache HIT (re-checked under lock) para '{content_id}'")
            return {
                "manifest_url": cached, 
                "source": "cache",
                "content_id": content_id
            }

        # 3. Cache MISS real -> ejecutar automatización de UI
        print(f"[INFO] Cache MISS para '{content_id}'. Iniciando Playwright...")
        browser_manager = request.app.state.browser_manager
        
        try:
            manifest_url = await capture_manifest_url(browser_manager, content_id)
            manifest_cache.set(content_id, manifest_url)
            
            return {
                "manifest_url": manifest_url, 
                "source": "fresh",
                "content_id": content_id
            }
        except TimeoutError as te:
            raise HTTPException(status_code=504, detail=str(te))
        except Exception as e:
            print(f"[ERROR] Error al capturar manifiesto: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error interno al capturar el flujo en vivo: {str(e)}"
            )
