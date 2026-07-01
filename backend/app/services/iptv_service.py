"""
iptv_service.py — Data Pipeline de 4 Estaciones para canales IPTV
==================================================================

Arquitectura:
  Estación A │ Recolector    → Descarga .m3u por país (aiohttp concurrente)
  Estación B │ Clasificador  → Parsea y categoriza los canales en memoria
  Estación C │ Validador     → Verifica URLs con HEAD requests + asyncio.Semaphore
  Estación D │ Formateador   → Ensambla la salida JSON estructurada para React

Todo el procesamiento usa listas y dicts nativos de Python para no
bloquear el Event Loop de FastAPI. Sin Pandas.
"""

import asyncio
import re
from typing import Any

import aiohttp

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN GLOBAL
# ──────────────────────────────────────────────────────────────────────────────
# Cabecera de navegador real para evitar bloqueos de servidores
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
# URL base del repositorio iptv-org para ingesta geográfica
IPTV_ORG_BASE_URL = "https://iptv-org.github.io/iptv/countries/{codigo}.m3u"
# Lista de países de LATAM + Norteamérica a procesar
PAISES_OBJETIVO: list[str] = [
    "us", "ca", "mx", "gt", "sv", "hn", "ni", "cr", "pa",
    "co", "ve", "ec", "pe", "bo", "br", "cl", "ar", "uy", "py",
]
# Palabras clave para la clasificación de canales (Estación B)
# El orden importa: se evalúa de arriba a abajo. El primero que coincida gana.
REGLAS_CLASIFICACION: list[tuple[str, list[str]]] = [
    ("Deportes", [
        "sport", "deport", "futbol", "fútbol", "soccer", "football",
        "nfl", "nba", "mlb", "nhl", "tennis", "tenis", "golf", "box",
        "lucha", "mma", "ufc", "olimpic", "f1", "motor", "racing",
        "béisbol", "beisbol", "basketball", "baloncesto", "volley",
        "espn", "fox sports", "directv sports", "claro sports", "dsports",
    ]),
    ("Peliculas", [
        "movie", "pelicula", "película", "cine", "cinema", "film",
        "hbo", "netflix", "amazon", "paramount", "mgm", "tcm",
        "action", "horror", "comedy", "drama", "thriller",
    ]),
    ("TV", [
        "news", "noticias", "noticia", "info", "canal", "tv", "tele",
        "national", "discovery", "history", "nat geo", "natgeo",
        "documentary", "documental", "kids", "infantil", "cartoon",
        "music", "música", "musica", "entretenimiento", "entertainment",
        "variedad",
    ]),
]
# Categoría de respaldo si ninguna regla coincide
CATEGORIA_DEFAULT = "Otros"
# Semáforo de concurrencia para la Estación C
SEMAPHORE_LIMIT = 50
# Timeout (segundos) para peticiones HEAD en la Estación C
TIMEOUT_VALIDACION = 5
# Timeout (segundos) para descargas de .m3u en la Estación A
TIMEOUT_DESCARGA = 20
# Códigos HTTP considerados como "válidos" en la Estación C
CODIGOS_VALIDOS = {200, 301, 302}


def _detectar_resolucion(nombre: str) -> str:
    """Heurística rápida para detectar la resolución por el nombre del canal."""
    nombre_lower = nombre.lower()
    if "4k" in nombre_lower or "uhd" in nombre_lower:
        return "4K"
    if "fhd" in nombre_lower or "1080" in nombre_lower:
        return "FHD"
    if "sd" in nombre_lower or "360" in nombre_lower or "240" in nombre_lower:
        return "SD"
    return "HD"

def _formatear_canal(canal: dict[str, Any], idx: int) -> dict[str, Any]:
    """
    Formatea un solo canal. Usado exclusivamente por el pipeline de Streaming
    para emitir canales on-the-fly sin esperar a la Estación D.
    """
    nombre    = canal.get("nombre", "Sin nombre")
    feed      = canal.get("feed", "")
    logo      = canal.get("logo", "")
    categoria = canal.get("categoria", "Otros") # Ajusta a tu CATEGORIA_DEFAULT si la tienes
    pais      = canal.get("pais", "xx")

    return {
        "id":         idx,
        "title":      nombre,
        "feed":       feed,
        "logo":       logo,
        "categoria":  categoria,
        "pais":       pais,
        # Si tienes la función _detectar_resolucion en este archivo, descomenta la línea de abajo:
    #"resolution": _detectar_resolucion(nombre)
        "status":     "online",
        "time":       "EN VIVO",
    }

# ──────────────────────────────────────────────────────────────────────────────
# ESTACIÓN A — EL RECOLECTOR (Ingesta Geográfica)
# ──────────────────────────────────────────────────────────────────────────────
async def _descargar_m3u_pais(
    session: aiohttp.ClientSession,
    codigo: str,
) -> tuple[str, str]:
    """
    Descarga el archivo .m3u de un país específico desde iptv-org.
    Retorna una tupla (codigo_pais, contenido_crudo).
    Si falla, retorna (codigo_pais, "") para no detener el pipeline.
    """
    url = IPTV_ORG_BASE_URL.format(codigo=codigo)
    try:
        timeout = aiohttp.ClientTimeout(total=TIMEOUT_DESCARGA)
        async with session.get(url, timeout=timeout, headers=HEADERS) as resp:
            if resp.status == 200:
                contenido = await resp.text(encoding="utf-8", errors="replace")
                print(
                    f"  [A] ✅ [{codigo.upper()}] Descargado — "
                    f"{len(contenido):,} bytes / {contenido.count('#EXTINF')} entradas"
                )
                return codigo, contenido
            else:
                print(f"  [A] ⚠️  [{codigo.upper()}] HTTP {resp.status} — omitido")
                return codigo, ""
    except asyncio.TimeoutError:
        print(f"  [A] ⏱️  [{codigo.upper()}] Timeout — omitido")
        return codigo, ""
    except Exception as exc:
        print(f"  [A] ❌ [{codigo.upper()}] Error: {exc} — omitido")
        return codigo, ""
async def estacion_a_recolector(
    paises: list[str],
) -> dict[str, str]:
    """
    ESTACIÓN A — Descarga concurrente de todos los .m3u por país.
    Args:
        paises: Lista de códigos ISO de país (e.g. ["mx", "ar"]).
    Returns:
        Dict {codigo_pais: contenido_m3u_crudo}.
        Los países que fallen tendrán una cadena vacía como valor.
    """
    print(f"\n{'='*60}")
    print(f"  [PIPELINE] 🚀 ESTACIÓN A — RECOLECTOR INICIANDO")
    print(f"  [PIPELINE] Países objetivo: {len(paises)} ({', '.join(p.upper() for p in paises)})")
    print(f"{'='*60}")
    async with aiohttp.ClientSession() as session:
        tareas = [
            _descargar_m3u_pais(session, codigo)
            for codigo in paises
        ]
        resultados: list[tuple[str, str]] = await asyncio.gather(*tareas)
    # Convertir la lista de tuplas a un dict
    contenidos_por_pais: dict[str, str] = dict(resultados)
    exitosos = sum(1 for v in contenidos_por_pais.values() if v)
    print(f"\n  [A] 📦 Descarga completa: {exitosos}/{len(paises)} países con datos")
    print(f"{'='*60}\n")
    return contenidos_por_pais
# ──────────────────────────────────────────────────────────────────────────────
# ESTACIÓN B — EL CLASIFICADOR Y EXTRACTOR (Parser)
# ──────────────────────────────────────────────────────────────────────────────
def _extraer_atributo_re(linea: str, atributo: str) -> str:
    """
    Extrae el valor de un atributo dentro de un tag #EXTINF usando regex.
    Ejemplo: tvg-logo="https://..." → "https://..."
    """
    patron = rf'{re.escape(atributo)}="([^"]*)"'
    match = re.search(patron, linea)
    return match.group(1) if match else ""
def _clasificar_canal(nombre: str, group_title: str) -> str:
    """
    Clasifica un canal en una categoría según su nombre y group-title.
    Recorre las reglas en orden; retorna la primera coincidencia.
    """
    texto_busqueda = f"{nombre} {group_title}".lower()
    for categoria, palabras_clave in REGLAS_CLASIFICACION:
        for clave in palabras_clave:
            if clave in texto_busqueda:
                return categoria
    return CATEGORIA_DEFAULT
def _parsear_m3u(contenido: str, codigo_pais: str) -> list[dict[str, Any]]:
    """
    Parsea el texto crudo de un .m3u y extrae los canales.
    Formato típico:
        #EXTINF:-1 tvg-id="..." tvg-name="..." tvg-logo="..." group-title="...",Nombre
        https://stream.url/live
    Args:
        contenido:    Texto crudo del archivo .m3u.
        codigo_pais:  Código ISO del país origen (para trazabilidad).
    Returns:
        Lista de dicts con las claves: nombre, feed, logo, categoria, pais.
    """
    canales: list[dict[str, Any]] = []
    lineas = contenido.strip().splitlines()
    canal_en_curso: dict[str, Any] = {}
    for linea in lineas:
        linea = linea.strip()
        if linea.startswith("#EXTINF"):
            canal_en_curso = {}
            # Extraer atributos estructurados del tag
            tvg_name    = _extraer_atributo_re(linea, "tvg-name")
            tvg_logo    = _extraer_atributo_re(linea, "tvg-logo")
            group_title = _extraer_atributo_re(linea, "group-title")
            # El nombre visible está después de la última coma del tag
            partes = linea.split(",", 1)
            nombre_visible = partes[-1].strip() if len(partes) > 1 else ""
            nombre_final = tvg_name or nombre_visible or "Sin nombre"
            canal_en_curso = {
                "nombre":    nombre_final,
                "logo":      tvg_logo,
                "group":     group_title,
                "categoria": _clasificar_canal(nombre_final, group_title),
                "pais":      codigo_pais,
            }
        elif linea and not linea.startswith("#"):
            # Esta línea es la URL del stream (feed)
            if canal_en_curso and linea.startswith(("http://", "https://", "rtmp://", "rtsp://")):
                canal_en_curso["feed"] = linea
                canales.append(canal_en_curso)
                canal_en_curso = {}
    return canales
async def estacion_b_clasificador(
    contenidos_por_pais: dict[str, str],
) -> list[dict[str, Any]]:
    """
    ESTACIÓN B — Parsea y clasifica todos los canales en memoria.
    Procesa cada país secuencialmente (el parsing es CPU-bound pero muy ligero),
    delegando en _parsear_m3u() para mantener limpia la función orquestadora.
    Args:
        contenidos_por_pais: Output de la Estación A.
    Returns:
        Lista plana de canales crudos (sin deduplicar ni verificar).
    """
    print(f"{'='*60}")
    print(f"  [PIPELINE] 🔍 ESTACIÓN B — CLASIFICADOR INICIANDO")
    print(f"{'='*60}")
    todos_los_canales: list[dict[str, Any]] = []
    for codigo, contenido in contenidos_por_pais.items():
        if not contenido:
            print(f"  [B] ⏭️  [{codigo.upper()}] Sin contenido — saltado")
            continue
        canales_pais = _parsear_m3u(contenido, codigo)
        todos_los_canales.extend(canales_pais)
        print(f"  [B] 📋 [{codigo.upper()}] {len(canales_pais):,} canales extraídos")
    # ── TELEMETRÍA ESTACIÓN B ──
    print(f"\n  [B] 📊 Canales crudos encontrados: {len(todos_los_canales):,}")
    # Deduplicar por URL de feed (misma URL en distintos países = duplicado exacto)
    feeds_vistos: set[str] = set()
    canales_unicos: list[dict[str, Any]] = []
    for canal in todos_los_canales:
        feed = canal.get("feed", "").strip()
        if feed and feed not in feeds_vistos:
            feeds_vistos.add(feed)
            canales_unicos.append(canal)
    print(f"  [B] 🧹 Canales únicos tras deduplicar: {len(canales_unicos):,}")
    print(f"{'='*60}\n")
    return canales_unicos
# ──────────────────────────────────────────────────────────────────────────────
# ESTACIÓN C — EL VALIDADOR (Control de Calidad)
# ──────────────────────────────────────────────────────────────────────────────
async def _verificar_url(
    session: aiohttp.ClientSession,
    canal: dict[str, Any],
    semaforo: asyncio.Semaphore,
) -> dict[str, Any] | None:
    """
    Realiza una petición HEAD asíncrona para validar que el stream está activo.
    El semáforo garantiza que no se abran más de SEMAPHORE_LIMIT conexiones a la vez.
    Args:
        session:  ClientSession compartida (reutiliza conexiones TCP).
        canal:    Dict del canal con al menos la clave "feed".
        semaforo: asyncio.Semaphore para limitar la concurrencia de red.
    Returns:
        El dict del canal si está activo, None si no responde o falla.
    """
    url = canal.get("feed", "")
    if not url:
        return None
    async with semaforo:
        try:
            timeout = aiohttp.ClientTimeout(total=TIMEOUT_VALIDACION)
            async with session.head(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers=HEADERS,
            ) as resp:
                if resp.status in CODIGOS_VALIDOS:
                    return canal
                return None
        except Exception:
            return None
async def estacion_c_validador(
    canales: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    ESTACIÓN C — Verifica de forma concurrente qué canales están realmente online.
    Usa asyncio.Semaphore(SEMAPHORE_LIMIT) para no saturar la red
    ni provocar errores de "too many open files".
    Args:
        canales: Lista de canales únicos de la Estación B.
    Returns:
        Lista filtrada con solo los canales que respondieron correctamente.
    """
    print(f"{'='*60}")
    print(f"  [PIPELINE] 🛡️  ESTACIÓN C — VALIDADOR INICIANDO")
    print(f"{'='*60}")
    total = len(canales)
    # ── TELEMETRÍA ESTACIÓN C (inicio) ──
    print(f"  [C] 🔎 Verificando canales... ({total:,} en total)")
    print(f"  [C] ⚙️  Semáforo de concurrencia: {SEMAPHORE_LIMIT} conexiones simultáneas")
    print(f"  [C] ⏱️  Timeout por canal: {TIMEOUT_VALIDACION}s")
    semaforo = asyncio.Semaphore(SEMAPHORE_LIMIT)
    async with aiohttp.ClientSession() as session:
        tareas = [
            _verificar_url(session, canal, semaforo)
            for canal in canales
        ]
        resultados: list[dict[str, Any] | None] = await asyncio.gather(
            *tareas, return_exceptions=False
        )
    # Filtrar los None (canales inválidos o caídos)
    canales_validos: list[dict[str, Any]] = [r for r in resultados if r is not None]
    # ── TELEMETRÍA ESTACIÓN C (fin) ──
    print(f"\n  [C] ✅ Canales realmente válidos: {len(canales_validos):,} / {total:,}")
    print(f"  [C] ❌ Canales descartados: {total - len(canales_validos):,}")
    print(f"{'='*60}\n")
    return canales_validos
# ──────────────────────────────────────────────────────────────────────────────
# ESTACIÓN D — EL FORMATEADOR (Salida estructurada para React)
# ──────────────────────────────────────────────────────────────────────────────
def _detectar_resolucion(nombre: str) -> str:
    """Heurística rápida para detectar la resolución por el nombre del canal."""
    nombre_lower = nombre.lower()
    if "4k" in nombre_lower or "uhd" in nombre_lower:
        return "4K"
    if "fhd" in nombre_lower or "1080" in nombre_lower:
        return "FHD"
    if "sd" in nombre_lower or "360" in nombre_lower or "240" in nombre_lower:
        return "SD"
    return "HD"
def estacion_d_formateador(
    canales_validos: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    ESTACIÓN D — Transforma la lista de canales validados en el JSON
    estructurado que consume el frontend React.
    Estructura de salida:
    {
        "total": int,
        "paises": {
            "mx": [{ canal1 }, { canal2 }],
            "ar": [...],
            ...
        },
        "categorias": {
            "Deportes":  [{ canal1 }, ...],
            "Peliculas": [...],
            "TV":        [...],
            "Otros":     [...],
        }
    }
    Args:
        canales_validos: Output de la Estación C.
    Returns:
        Dict listo para serializar a JSON y enviar al cliente.
    """
    print(f"{'='*60}")
    print(f"  [PIPELINE] 📦 ESTACIÓN D — FORMATEADOR INICIANDO")
    print(f"{'='*60}")
    paises:     dict[str, list[dict[str, Any]]] = {}
    categorias: dict[str, list[dict[str, Any]]] = {
        "Deportes":  [],
        "Peliculas": [],
        "TV":        [],
        "Otros":     [],
    }
    for idx, canal in enumerate(canales_validos, start=1):
        nombre    = canal.get("nombre", "Sin nombre")
        feed      = canal.get("feed", "")
        logo      = canal.get("logo", "")
        categoria = canal.get("categoria", CATEGORIA_DEFAULT)
        pais      = canal.get("pais", "xx")
        canal_formateado: dict[str, Any] = {
            "id":         idx,
            "title":      nombre,
            "feed":       feed,
            "logo":       logo,
            "categoria":  categoria,
            "pais":       pais,
            "resolution": _detectar_resolucion(nombre),
            "status":     "online",
            "time":       "EN VIVO",
        }
        # Agrupar por país
        if pais not in paises:
            paises[pais] = []
        paises[pais].append(canal_formateado)
        # Agrupar por categoría (con fallback a "Otros")
        if categoria not in categorias:
            categorias[categoria] = []
        categorias[categoria].append(canal_formateado)
    # Reporte por país
    print(f"[D] 📊 Total canales formateados: {len(canales_validos):,}")
    print(f"[D] 📁 Países detectados: {len(paises)}")
    print(f"[D] 🏷️  Categorías detectadas: {len(categorias)}")
    print(f"{'='*60}\n")
    return {
        "total": len(canales_validos),
        "paises": paises,
        "categorias": categorias
    }