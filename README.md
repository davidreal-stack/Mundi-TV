# 🌍 MUNDI TV - Streaming de Deportes en Vivo

Una plataforma completa de streaming con **Backend en Python/FastAPI** y **Frontend en Next.js 14** para ver partidos y eventos deportivos en vivo con seguridad mediante tokens JWT.

---

## 📋 Características

✅ **Backend Robusto**
- FastAPI con CORS habilitado
- Parsing de archivos M3U con limpieza inteligente de nombres
- Generación de tokens JWT para ocultar links reales
- Gestión de cache en memoria
- Health check y endpoints de verificación

✅ **Frontend Moderno**
- Next.js 14 App Router con TypeScript
- Diseño oscuro futurista con Tailwind CSS
- Dashboard con filtros por categorías
- Reproductor HLS integrado con hls.js
- Controles personalizados de video
- Responsive design (Mobile, Tablet, Desktop)

✅ **Seguridad**
- Tokens JWT con expiración de 2 horas
- Almacenamiento seguro de links en servidor
- Validación de tokens en cada request
- CORS configurado para todos los orígenes

---

## 🚀 Instalación Rápida

### Requisitos Previos
- **Python 3.8+**
- **Node.js 18+** (incluye npm)
- **Git** (opcional)

---

## 📦 PARTE 1: Backend (Python & FastAPI)

### 1️⃣ Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

### 2️⃣ Configurar Variables de Entorno

El archivo `.env` ya está creado con una clave JWT. **En producción, cámbiala:**

```bash
# backend/.env
JWT_SECRET=tu_clave_secreta_super_segura_y_diferente
```

### 3️⃣ Ejecutar el Servidor

```bash
# Opción 1: Con uvicorn directamente
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Opción 2: Con Python
python main.py
```

**✅ Servidor ejecutándose en:** `http://localhost:8000`

### 4️⃣ Verificar el Backend

Abre en tu navegador:
- **Dashboard API:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Eventos:** http://localhost:8000/api/events

---

## 🎬 PARTE 2: Frontend (Next.js 14)

### 1️⃣ Instalar Dependencias

```bash
cd frontend
npm install
# o
yarn install
```

### 2️⃣ Variables de Entorno (Opcional)

Crea un archivo `.env.local` si tu backend no está en `localhost:8000`:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3️⃣ Ejecutar en Desarrollo

```bash
npm run dev
# o
yarn dev
```

**✅ Frontend en:** `http://localhost:3000`

### 4️⃣ Build para Producción

```bash
npm run build
npm start
```

---

## 📁 Estructura del Proyecto

```
Mundi-tv/
├── backend/
│   ├── main.py                 # Servidor FastAPI
│   ├── extractor.py           # Parsing de M3U y limpieza de nombres
│   ├── canales.m3u            # Archivo de canales
│   ├── requirements.txt        # Dependencias Python
│   └── .env                    # Variables de entorno
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # Dashboard principal
│   │   │   ├── layout.tsx            # Layout global
│   │   │   ├── globals.css           # Estilos globales
│   │   │   └── channel/
│   │   │       └── page.tsx          # Reproductor de video
│   │   └── components/
│   │       ├── Navbar.tsx            # Barra de navegación
│   │       ├── Footer.tsx            # Pie de página
│   │       └── ChannelCard.tsx       # Tarjeta de canal
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── postcss.config.js
│
└── README.md
```

---

## 🔌 API Endpoints

### 📺 Obtener Eventos
```
GET /api/events
```
Retorna lista de canales disponibles.

**Respuesta:**
```json
[
  {
    "id": 1,
    "title": "ESPN",
    "time": "En Vivo",
    "category": "Fútbol",
    "status": "en vivo",
    "link": "https://example.m3u8",
    "resolution": "HD"
  }
]
```

### 🔐 Generar Token
```
POST /api/generate-token
Content-Type: application/json

{
  "link": "https://example.m3u8/stream.m3u8"
}
```

**Respuesta:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in_hours": 2
}
```

### 🔗 Obtener Link Real
```
GET /api/get_link?token=YOUR_TOKEN
```

**Respuesta:**
```json
{
  "link": "https://example.m3u8/stream.m3u8"
}
```

### ✅ Verificar Token
```
POST /api/verifique_tokens
Content-Type: application/json

{
  "token": "YOUR_JWT_TOKEN"
}
```

**Respuesta:**
```json
{
  "valid": true,
  "expires_at": "2024-06-11T20:30:45.123456+00:00",
  "message": "Token válido y autenticado"
}
```

### 🏥 Health Check
```
GET /health
```

---

## 🎨 Personalización

### Agregar Más Canales

Edita `backend/canales.m3u`:

```m3u
#EXTM3U

#EXTINF:-1, Mi Canal
https://ejemplo.com/stream.m3u8

#EXTINF:-1, Otro Canal
https://otro.com/stream.m3u8
```

Luego, llama a:
```
POST http://localhost:8000/api/refresh-events
```

### Cambiar Colores Neon

Edita `frontend/tailwind.config.ts`:

```ts
neon: {
  blue: '#00d4ff',      // Cambiar aquí
  pink: '#ff006e',      // Cambiar aquí
  purple: '#b537f2',    // Cambiar aquí
}
```

### Agregar Nuevas Categorías

En `backend/extractor.py`, modifica la función `categorize_channel()`:

```python
def categorize_channel(title: str) -> str:
    title_lower = title.lower()
    
    if any(word in title_lower for word in ['mi_palabra']):
        return "Mi Categoría"
    # ... resto del código
```

---

## 🐛 Troubleshooting

### ❌ "No se puede conectar con el servidor"

1. Verifica que FastAPI esté corriendo en puerto 8000
2. Asegúrate que CORS esté habilitado
3. Comprueba la URL en `frontend/.env.local`

```bash
# Verificar si el puerto 8000 está en uso
netstat -ano | findstr :8000  # Windows
lsof -i :8000                # macOS/Linux
```

### ❌ "Token inválido o expirado"

Los tokens expiran en **2 horas**. Genera uno nuevo desde el frontend.

### ❌ "Video no reproduce"

- Verifica que la URL M3U sea válida
- Comprueba que el navegador soporta HLS
- Abre la consola del navegador para ver errores

### ❌ "Error al generar token"

- Asegúrate que la URL del link sea válida
- Verifica que el backend está respondiendo
- Revisa los logs en la terminal de FastAPI

---

## 📊 Monitoreo

### Ver Logs del Backend

Los logs se muestran en la terminal donde ejecutas FastAPI:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Token generado: eyJ...
✅ Link recuperado exitosamente para token: eyJ...
```

### Ver Logs del Frontend

Abre la consola del navegador (**F12**) para ver errores de red y JavaScript.

---

## 🔒 Seguridad en Producción

### 1. Cambiar JWT_SECRET
```bash
# Generar una clave fuerte
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Luego, actualiza en `backend/.env`:
```
JWT_SECRET=TU_CLAVE_SEGURA_AQUI
```

### 2. CORS en Producción

Modifica `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tunombre.com", "https://www.tunombre.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 3. HTTPS

Usa certificados SSL/TLS en producción.

### 4. Rate Limiting (Opcional)

Instala slowapi:
```bash
pip install slowapi
```

Usa en `main.py` para limitar requests por IP.

---

## 🚢 Despliegue en Producción

### Backend (Vercel, Railway, Render, Heroku)

```bash
# requirements.txt está listo
# Comando para ejecutar:
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel, Netlify, Railway)

```bash
npm run build
npm start
```

---

## 📝 Licencia

Este proyecto es de código abierto. Úsalo libremente. ¡Dale una estrella ⭐ si te gusta!

---

## 🤝 Contribuir

¿Tienes sugerencias o bugs? ¡Abre un issue o PR!

---

## 📞 Soporte

- **Email:** soporte@munditv.com
- **Discord:** Tu servidor de Discord aquí
- **GitHub:** Tu repositorio GitHub aquí

---

**Made with ❤️ by Mundi TV Team**

```
██████╗ ██╗   ██╗    ███╗   ███╗██╗   ██╗███╗   ██╗██████╗ ██╗    ██╗
██╔════╝ ██║   ██║    ████╗ ████║██║   ██║████╗  ██║██╔══██╗██║    ██║
██║  ███╗██║   ██║    ██╔████╔██║██║   ██║██╔██╗ ██║██║  ██║██║ █╗ ██║
██║   ██║██║   ██║    ██║╚██╔╝██║██║   ██║██║╚██╗██║██║  ██║██║███╗██║
╚██████╔╝╚██████╔╝    ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║██████╔╝╚███╔███╔╝
 ╚═════╝  ╚═════╝     ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═════╝  ╚══╝╚══╝
```
