import os
import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext

class BrowserManager:
    """
    Mantiene una única instancia de Browser (proceso) viva,
    y gestiona un pool acotado de BrowserContexts (sesiones aisladas
    pero ligeras, sin relanzar el binario).
    """
    _instance = None

    def __init__(self):
        self.playwright = None
        self.browser: Browser | None = None
        self._pool: asyncio.Queue[BrowserContext] = asyncio.Queue()
        self._pool_size = 3  # ajustar según núcleos de CPU disponibles

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = BrowserManager()
            await cls._instance._startup()
        return cls._instance

    async def _startup(self):
        self.playwright = await async_playwright().start()
        # Un único proceso de navegador, reutilizable
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",   # evita problemas de memoria compartida en LAN/containers
                "--no-sandbox",
                "--disable-gpu",
            ],
        )
        # Pre-calentar el pool con contextos reutilizables
        for _ in range(self._pool_size):
            ctx = await self._create_context()
            await self._pool.put(ctx)

    async def _create_context(self) -> BrowserContext:
        state_file = "session_state.json"
        storage_state = state_file if self._state_exists() else None
        
        return await self.browser.new_context(
            storage_state=storage_state,
            user_agent=self._get_user_agent(),
            locale="es-MX",
            viewport={"width": 1366, "height": 768},
        )

    async def acquire_context(self) -> BrowserContext:
        # Si el pool está vacío, esperará hasta que un contexto se libere
        return await self._pool.get()

    async def release_context(self, ctx: BrowserContext):
        # Limpia estado transitorio sin destruir el contexto
        try:
            await ctx.clear_cookies()
        except Exception as e:
            print(f"[WARNING] Error limpiando cookies del contexto: {e}")
        await self._pool.put(ctx)

    async def shutdown(self):
        # Limpiar y cerrar contextos del pool
        while not self._pool.empty():
            ctx = self._pool.get_nowait()
            try:
                await ctx.close()
            except Exception:
                pass
        
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _state_exists(self) -> bool:
        return os.path.exists("session_state.json")

    def _get_user_agent(self) -> str:
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
