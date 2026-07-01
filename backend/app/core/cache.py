import time
import asyncio
from dataclasses import dataclass

from typing import Dict, Any

# Almacenamiento en memoria para tokens y enlaces
link_store: Dict[str, str] = {}  # {token: link_original}

# Almacenamiento en memoria para el caché de los eventos M3U
events_cache: Dict[str, Any] = {
    "data": [],
    "last_updated": None
}


@dataclass
class CacheEntry:
    url: str
    expires_at: float

class ManifestCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._store: dict[str, CacheEntry] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry and entry.expires_at > time.monotonic():
            return entry.url
        # Limpieza perezosa de entradas vencidas
        self._store.pop(key, None)
        return None

    def set(self, key: str, url: str):
        self._store[key] = CacheEntry(
            url=url,
            expires_at=time.monotonic() + self.ttl,
        )

    def get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]
