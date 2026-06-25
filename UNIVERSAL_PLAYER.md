# 🎬 UniversalPlayer - Reproductor Multi-Formato

Reproductor universal para streaming HLS (.m3u8) y MPEG-DASH (.mpd) basado en **Shaka Player**.

## 📋 Instalación

### Paso 1: Instalar Shaka Player

```bash
cd frontend
npm install shaka-player
```

También puedes usar yarn o pnpm:
```bash
yarn add shaka-player
# o
pnpm add shaka-player
```

### Paso 2: Instalar TypeScript types (opcional pero recomendado)

```bash
npm install --save-dev @types/shaka-player
```

---

## 🚀 Uso Básico

### Uso Simple

```tsx
import UniversalPlayer from '@/components/UniversalPlayer';

export default function MyPage() {
  return (
    <UniversalPlayer
      src="https://example.com/stream.m3u8"
      title="Mi Stream Favorito"
    />
  );
}
```

### Con Más Opciones

```tsx
import UniversalPlayer from '@/components/UniversalPlayer';

export default function MyPage() {
  return (
    <UniversalPlayer
      src="https://example.com/stream.mpd"
      title="NFL en Vivo"
      poster="https://example.com/poster.jpg"
      autoplay={true}
      muted={false}
    />
  );
}
```

---

## 📌 Props

| Prop | Tipo | Default | Descripción |
|------|------|---------|-------------|
| `src` | `string` | - | **Requerido**. URL del stream (.m3u8 o .mpd) |
| `title` | `string` | `'Reproductor de Video'` | Título mostrado debajo del video |
| `poster` | `string` | - | URL de la imagen de portada |
| `autoplay` | `boolean` | `false` | Reproducir automáticamente |
| `muted` | `boolean` | `false` | Silenciar por defecto |

---

## 🔌 Integración con Backend Local

### En `src/app/channel/page.tsx`:

```tsx
'use client';

import { useEffect, useSearchParams, useState } from 'react';
import UniversalPlayer from '@/components/UniversalPlayer';
import Link from 'next/link';
import { API_CONFIG } from '@/lib/api';

export default function ChannelPlayer() {
  const searchParams = useSearchParams();
  const [streamUrl, setStreamUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [channelTitle, setChannelTitle] = useState('');

  useEffect(() => {
    const fetchStream = async () => {
      try {
        const token = searchParams.get('token');
        if (!token) {
          throw new Error('Token no encontrado');
        }

        const response = await fetch(
          `${API_CONFIG.BASE_URL}/api/get_link?token=${token}`
        );

        if (!response.ok) {
          throw new Error('No se pudo obtener el stream');
        }

        const data = await response.json();
        setStreamUrl(data.link);
        setChannelTitle(data.title || 'En Vivo');
        setLoading(false);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Error desconocido';
        setError(msg);
        setLoading(false);
      }
    };

    fetchStream();
  }, [searchParams]);

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Cargando...</div>;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-screen gap-4">
        <p className="text-red-500 text-lg">{error}</p>
        <Link href="/" className="text-blue-500 hover:underline">
          Volver al inicio
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full h-screen bg-black p-4 flex flex-col items-center justify-center">
      <div className="w-full max-w-6xl">
        <UniversalPlayer
          src={streamUrl}
          title={channelTitle}
          autoplay={true}
          muted={false}
        />
        <Link
          href="/"
          className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          ← Volver
        </Link>
      </div>
    </div>
  );
}
```

---

## 🎯 Formatos Soportados

### ✅ HLS (.m3u8)

```
https://example.com/stream.m3u8
https://192.168.1.66:8000/stream.m3u8
```

**Ejemplos reales:**
- ESPN: HLS
- Apple TV+: HLS
- Disney+: HLS

### ✅ MPEG-DASH (.mpd)

```
https://example.com/stream.mpd
https://192.168.1.66:8000/stream.mpd
```

**Ejemplos reales:**
- TV Azteca: DASH
- YouTube Live: DASH
- Netflix: DASH (con DRM)

### ✅ Smooth Streaming (.ism)

```
https://example.com/stream.ism/manifest
```

---

## 🔧 Características Incluidas

✅ **Multi-formato**: HLS, DASH, Smooth Streaming, Progressive Download
✅ **Adaptación de bitrate**: Automática según conexión
✅ **Polyfills**: Media Source Extensions instalados automáticamente
✅ **Limpieza de memoria**: Destrucción correcta del reproductor en unmount
✅ **Manejo de errores**: Errores CORS, red y reproducción
✅ **Controles nativos**: Reproducción, volumen, pantalla completa del navegador
✅ **Responsive**: Responsive design 16:9
✅ **SSR Compatible**: Usa "use client" correctamente
✅ **Dark Mode**: Diseño oscuro moderno
✅ **Debug Info**: Logs en desarrollo

---

## 🐛 Consola de Debugging

El componente registra eventos importantes en la consola del navegador (F12):

```
📦 Instalando polyfills de Shaka Player...
🎬 Inicializando Shaka Player...
🔗 Cargando stream: https://example.com/stream.m3u8
📊 Calidad ajustada automáticamente
✅ Streaming iniciado
✨ Reproductor inicializado correctamente
```

### Errores Comunes

**❌ Error CORS**
```
XMLHttpRequest cannot load https://... due to CORS policy
```

**Solución:** Configura CORS en tu backend o usa un proxy

**❌ Error: "Unsupported MIME type"**
```
Unsupported MIME type for the media source
```

**Solución:** Verifica que el servidor devuelve los headers MIME correctos:
```
Content-Type: application/vnd.apple.mpegurl (para .m3u8)
Content-Type: application/dash+xml (para .mpd)
```

---

## 🌐 Red Local (LAN)

Para reproducir streams desde tu red local:

### Backend FastAPI

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ejecutar con:
# uvicorn main:app --host 0.0.0.0 --port 8000
```

### Consumir desde Frontend

```tsx
<UniversalPlayer
  src="http://192.168.1.66:8000/api/stream.m3u8?token=xyz"
  title="Mi Stream Local"
/>
```

---

## ⚡ Optimización de Performance

### Lazy Loading (Recomendado)

```tsx
import dynamic from 'next/dynamic';

const UniversalPlayer = dynamic(
  () => import('@/components/UniversalPlayer'),
  { loading: () => <div>Cargando reproductor...</div> }
);

export default function Page() {
  return <UniversalPlayer src="..." />;
}
```

### Pre-buffering

```tsx
useEffect(() => {
  // Pre-buffering del siguiente stream
  const player = playerRef.current;
  if (player) {
    // Shaka Player maneja automáticamente el buffering
  }
}, []);
```

---

## 🔐 Seguridad (Token en URL)

Para proteger streams con tokens JWT:

```tsx
// Backend: Generar token
POST /api/generate-token
Response: { "token": "eyJhbGciOiJIUzI1NiIs..." }

// Frontend: Incluir en URL
const streamUrl = `http://192.168.1.66:8000/stream.m3u8?token=${token}`;

<UniversalPlayer src={streamUrl} />
```

---

## 📊 Estadísticas (Desarrollo)

En desarrollo, el componente muestra:
- Estado del reproductor
- URL del stream
- Mensajes de error

Desactiva con:
```tsx
// En environment.ts
export const SHOW_PLAYER_DEBUG = process.env.NODE_ENV === 'development';
```

---

## 🚀 Casos de Uso Comunes

### Reproductor de TV en Vivo

```tsx
<UniversalPlayer
  src="https://tvpublica.cl/stream.m3u8"
  title="TV Pública"
  autoplay={true}
  muted={true}
/>
```

### VOD (Video on Demand)

```tsx
<UniversalPlayer
  src="https://example.com/movie.mpd"
  poster="https://example.com/poster.jpg"
  title="Mi Película"
  autoplay={false}
/>
```

### Multi-Stream (Dashboard)

```tsx
{channels.map(channel => (
  <UniversalPlayer
    key={channel.id}
    src={channel.streamUrl}
    title={channel.name}
    poster={channel.posterUrl}
  />
))}
```

---

## 📚 Referencias

- [Shaka Player Docs](https://shaka-player-demo.appspot.com/docs/api/tutorial-basic-setup.html)
- [MDN Media Source Extensions](https://developer.mozilla.org/en-US/docs/Web/API/Media_Source_Extensions_API)
- [HLS Specification](https://tools.ietf.org/html/rfc8216)
- [DASH Standard](https://dashif.org/)

---

## 🤝 Soporte

Si encuentras problemas:

1. **Verifica la consola** (F12) para mensajes de error
2. **Comprueba CORS** - El servidor debe permitir peticiones de tu dominio
3. **Valida URLs** - Asegúrate que la URL del stream es accesible
4. **Prueba en otro navegador** - Para descartar problemas de compatibilidad

---

**Made with ❤️ by Mundi TV Team**
