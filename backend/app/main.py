import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Imports absolutos a tu propia arquitectura
from app.core.browser_manager import BrowserManager
from app.routes.stream import router as stream_router
from app.routes.iptv import router as iptv_router




if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Iniciando Mundi TV API y dependencias...")
    # Aquí en un futuro delegaremos la actualización de caché inicial a un servicio
    
    app.state.browser_manager = await BrowserManager.get_instance()
    yield
    print("[INFO] Apagando BrowserManager...")
    await app.state.browser_manager.shutdown()

# Inicialización limpia de FastAPI
app = FastAPI(
    title="Mundi TV API",
    description="API Backend para streaming de eventos deportivos",
    version="1.0.0",
    lifespan=lifespan
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(stream_router, prefix="/api")
app.include_router(iptv_router, prefix="/api")

@app.get("/", tags=["Root"])
def root():
    """Endpoint raíz - Información del servidor"""
    return {
        "service": "Mundi TV API",
        "version": "1.0.0",
        "status": "🟢 Online",
        "message": "Servidor funcionando bajo arquitectura modular."
    }
