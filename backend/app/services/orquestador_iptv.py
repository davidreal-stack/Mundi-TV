import asyncio
import json
from typing import Any, AsyncGenerator
import aiohttp

# Importamos las herramientas puras desde tu módulo de servicios
from app.services.iptv_service import (
    PAISES_OBJETIVO,
    SEMAPHORE_LIMIT,
    _descargar_m3u_pais,
    _parsear_m3u,
    _verificar_url,
    _formatear_canal,
    estacion_a_recolector,
    estacion_b_clasificador,
    estacion_c_validador,
    estacion_d_formateador
)

# ──────────────────────────────────────────────────────────────────────────────
# ORQUESTADOR PRINCIPAL (BATCH)
# ──────────────────────────────────────────────────────────────────────────────
async def ejecutar_pipeline_iptv(
    paises: list[str] | None = None,
) -> dict[str, Any]:
    paises_objetivo = paises or PAISES_OBJETIVO

    print(f"\n{'#'*60}")
    print(f"   🏭 MUNDI-TV DATA PIPELINE — INICIO")
    print(f"   Países: {len(paises_objetivo)} | Semáforo: {SEMAPHORE_LIMIT}")
    print(f"{'#'*60}")

    contenidos_por_pais = await estacion_a_recolector(paises_objetivo)
    canales_unicos = await estacion_b_clasificador(contenidos_por_pais)

    if not canales_unicos:
        print("   ⚠️  Pipeline detenido: ningún país aportó canales válidos.")
        return {"total": 0, "paises": {}, "categorias": {}}

    canales_validos = await estacion_c_validador(canales_unicos)

    if not canales_validos:
        print("   ⚠️  Pipeline detenido: ningún canal pasó la validación.")
        return {"total": 0, "paises": {}, "categorias": {}}

    resultado = estacion_d_formateador(canales_validos)

    print(f"{'#'*60}")
    print(f"   🏁 MUNDI-TV DATA PIPELINE — COMPLETADO")
    print(f"   Total canales listos para el frontend: {resultado['total']:,}")
    print(f"{'#'*60}\n")

    return resultado

# ──────────────────────────────────────────────────────────────────────────────
# PIPELINE STREAMING (CON GRACEFUL SHUTDOWN)
# ──────────────────────────────────────────────────────────────────────────────
async def _procesar_pais_stream(
    session: aiohttp.ClientSession,
    codigo: str,
    semaforo: asyncio.Semaphore,
    feeds_globales: set[str],
    contador_global: list[int],
) -> dict[str, Any]:
    
    _, contenido = await _descargar_m3u_pais(session, codigo)

    if not contenido:
        return {"ok": False, "codigo": codigo, "canales": [], "error": f"No se pudo descargar el .m3u para [{codigo.upper()}]"}

    canales_crudos = _parsear_m3u(contenido, codigo)
    canales_unicos_pais: list[dict[str, Any]] = []

    for canal in canales_crudos:
        feed = canal.get("feed", "").strip()
        if feed and feed not in feeds_globales:
            feeds_globales.add(feed)
            canales_unicos_pais.append(canal)

    if not canales_unicos_pais:
        return {"ok": False, "codigo": codigo, "canales": [], "error": f"[{codigo.upper()}] Sin canales únicos tras deduplicar."}

    tareas_validacion = [_verificar_url(session, canal, semaforo) for canal in canales_unicos_pais]
    resultados = await asyncio.gather(*tareas_validacion, return_exceptions=False)
    canales_validos = [r for r in resultados if r is not None]

    canales_formateados: list[dict[str, Any]] = []
    for canal in canales_validos:
        contador_global[0] += 1
        canales_formateados.append(_formatear_canal(canal, contador_global[0]))

    print(f"   [STREAM] ✅ [{codigo.upper()}] {len(canales_formateados):,} canales válidos")
    return {"ok": True, "codigo": codigo, "canales": canales_formateados, "error": ""}


async def pipeline_stream_iptv(
    paises: list[str] | None = None,
) -> AsyncGenerator[str, None]:
    
    paises_objetivo = paises or PAISES_OBJETIVO
    total_paises = len(paises_objetivo)
    total_canales_emitidos = 0

    print(f"\n{'#'*60}")
    print(f"   📡 MUNDI-TV STREAM PIPELINE — INICIO")
    print(f"   Países: {total_paises} | Semáforo compartido: {SEMAPHORE_LIMIT}")
    print(f"{'#'*60}")

    feeds_globales: set[str] = set()
    contador_global: list[int] = [0]
    semaforo = asyncio.Semaphore(SEMAPHORE_LIMIT)

    try:
        async with aiohttp.ClientSession() as session:
            tareas = {
                asyncio.ensure_future(
                    _procesar_pais_stream(session, codigo, semaforo, feeds_globales, contador_global)
                ): codigo
                for codigo in paises_objetivo
            }

            completados = 0

            try:
                for tarea in asyncio.as_completed(list(tareas.keys())):
                    completados += 1
                    percent = round((completados / total_paises) * 100)

                    try:
                        resultado = await tarea
                        codigo = resultado["codigo"]

                        evento_progress = {
                            "type":   "progress",
                            "country": codigo,
                            "percent": percent,
                            "message": f"Procesando {codigo.upper()}... ({completados}/{total_paises})",
                        }
                        yield json.dumps(evento_progress, ensure_ascii=False) + "\n"

                        if resultado["ok"]:
                            canales = resultado["canales"]
                            total_canales_emitidos += len(canales)
                            evento_data = {"type": "data", "payload": {"country": codigo, "channels": canales}}
                            yield json.dumps(evento_data, ensure_ascii=False) + "\n"
                        else:
                            print(f"   [STREAM] ⚠️  [{codigo.upper()}] {resultado['error']}")
                            evento_error = {"type": "error", "country": codigo, "message": resultado["error"]}
                            yield json.dumps(evento_error, ensure_ascii=False) + "\n"

                    except Exception as exc:
                        codigo_fallido = tareas.get(tarea, "??")
                        print(f"   [STREAM] ❌ [{codigo_fallido.upper()}] Excepción no controlada: {exc}")
                        evento_error = {"type": "error", "country": codigo_fallido, "message": f"Error interno: {exc}"}
                        yield json.dumps(evento_error, ensure_ascii=False) + "\n"

            except asyncio.CancelledError:
                print("\n   [STREAM] 🛑 CLIENTE DESCONECTADO: Cancelando tareas en segundo plano...")
                for tarea_pendiente in tareas.keys():
                    if not tarea_pendiente.done():
                        tarea_pendiente.cancel()
                raise

        evento_done = {
            "type":   "done",
            "total":  total_canales_emitidos,
            "message": f"Pipeline completado. {total_canales_emitidos:,} canales disponibles.",
        }
        yield json.dumps(evento_done, ensure_ascii=False) + "\n"
        print(f"   🏁 MUNDI-TV STREAM PIPELINE — COMPLETADO: {total_canales_emitidos:,} emitidos.\n")
        
    finally:
        print("   [STREAM] 🧹 Sesión aiohttp cerrada y recursos liberados.\n")