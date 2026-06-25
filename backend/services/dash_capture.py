import os
import json
import asyncio
from playwright.async_api import BrowserContext

STATE_FILE = "session_state.json"

CHANNEL_URLS = {
    "azteca-7": "https://www.tvazteca.com/envivo/azteca7",
    "azteca-uno": "https://www.tvazteca.com/envivo/aztecauno",
    "adn40": "https://www.tvazteca.com/envivo/adn40",
}

async def capture_manifest_url(browser_manager, content_id: str) -> str:
    
    Automatiza Playwright para capturar el manifiesto .mpd con token fresco de TV Azteca.

    target_url = CHANNEL_URLS.get(content_id)
    if not target_url:
        raise ValueError(f"Canal '{content_id}' no configurado en CHANNEL_URLS")

    print(f"[INFO] Iniciando captura de manifiesto para '{content_id}' en {target_url}...")
    ctx: BrowserContext = await browser_manager.acquire_context()
    manifest_url_holder = {}
    found_event = asyncio.Event()

    try:
        page = await ctx.new_page()

        # Headers consistentes con un navegador real en LAN
        await page.set_extra_http_headers({
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Referer": "https://www.tvazteca.com/",
        })

        # Intercepción de red: captura la URL del .mpd dinámico
        async def handle_request(req):
            url = req.url
            if (".mpd" in url or "manifest" in url) and not url.endswith(".json"):
                # Filtrar posibles ruidos o URLs irrelevantes, queremos el manifiesto de video principal
                if "tvazteca.com" in url or "live" in url or "manifest" in url:
                    manifest_url_holder["url"] = url
                    found_event.set()
                    print(f"[INFO] Manifiesto capturado en tiempo real: {url[:100]}...")

        page.on("request", handle_request)

        # Ir a la página
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
        except Exception as e:
            print(f"[WARNING] Timeout/Error durante page.goto: {str(e)}")

        # Intentar simular interacción para forzar la reproducción / peticiones de red
        try:
            # Intentar clickear el video o su contenedor
            selectors = [
                ".video-player-container",
                "video",
                "button[aria-label*='play']",
                ".vjs-big-play-button",
                ".play-button"
            ]
            for selector in selectors:
                try:
                    el = await page.wait_for_selector(selector, timeout=2000)
                    if el:
                        await el.click(timeout=1000)
                        print(f"[INFO] Click exitoso en selector: {selector}")
                        break
                except Exception:
                    continue

            # Fallback por JS para asegurar play()
            await page.evaluate("() => { const v = document.querySelector('video'); if (v) { v.play().catch(()=>{}); v.muted = true; } }")
        except Exception as e:
            print(f"[WARNING] Error intentando hacer click/play: {str(e)}")

        # Esperar a capturar la URL
        try:
            await asyncio.wait_for(found_event.wait(), timeout=15.0)
        except asyncio.TimeoutError:
            print(f"[ERROR] Timeout al esperar manifiesto .mpd para '{content_id}'")
            # Si hay timeout, devolvemos una excepción para ser manejada por la ruta
            raise TimeoutError(f"No se pudo capturar la señal en vivo de TV Azteca para {content_id} (Timeout)")

        # Guardar cookies + localStorage para agilizar próximas cargas
        try:
            storage = await ctx.storage_state()
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(storage, f)
            print("[INFO] Estado de sesión guardado.")
        except Exception as e:
            print(f"[WARNING] No se pudo guardar el estado de sesión: {str(e)}")

        await page.close()
        return manifest_url_holder["url"]

    finally:
        await browser_manager.release_context(ctx)