# 🌍 Configuración de Entorno - Mundi TV

## 📋 Descripción

Este archivo documenta cómo configurar correctamente las variables de entorno para que Mundi TV funcione tanto en desarrollo local como en una red local (LAN).

---

## 🎯 Casos de Uso

### 1️⃣ Desarrollo Local (Misma Máquina)

Si ejecutas tanto el frontend como el backend en **la misma computadora**:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Comando para el backend:**
```bash
cd backend
uvicorn main:app --reload --host localhost --port 8000
```

---

### 2️⃣ Acceso desde Red Local (LAN) ⭐ RECOMENDADO

Si quieres acceder a Mundi TV desde **otros dispositivos en la red Wi-Fi**:

#### Paso 1: Descubre la IP de tu máquina host

**Windows:**
```powershell
ipconfig
# Busca la línea "IPv4 Address" bajo tu adaptador de red
# Ejemplo: 192.168.1.66
```

**macOS/Linux:**
```bash
ifconfig
# Busca "inet" en tu interfaz de red (ej: en0, eth0, wlan0)
# Ejemplo: 192.168.1.66
```

#### Paso 2: Configura la variable de entorno

Edita `frontend/.env.local`:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://192.168.1.66:8000
```

#### Paso 3: Ejecuta el backend escuchando en todas las interfaces

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Paso 4: Accede desde otro dispositivo

En cualquier otro dispositivo en la red Wi-Fi:

```
http://192.168.1.66:3000
```

---

## 🔧 Configuración Centralizada del API

El frontend usa un archivo centralizado para gestionar la URL base:

**Archivo:** `frontend/src/lib/api.ts`

```typescript
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  // ... endpoints y funciones auxiliares
};
```

### Uso en Componentes

En lugar de hardcodear URLs, usa:

```typescript
import { API_CONFIG } from '@/lib/api';

// Opción 1: URL base
const response = await fetch(`${API_CONFIG.BASE_URL}/api/events`);

// Opción 2: Funciones auxiliares (recomendado)
import { getStreamLink, generateStreamToken } from '@/lib/api';

const link = await getStreamLink(token);
const token = await generateStreamToken(link);
```

---

## 📁 Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `frontend/.env.local` | Nueva - Variables de entorno (NO versionado) |
| `frontend/src/lib/api.ts` | Nueva - Configuración centralizada del API |
| `frontend/src/app/page.tsx` | Modificado - Usa `API_CONFIG` |
| `frontend/src/app/channel/page.tsx` | Modificado - Usa `API_CONFIG` |
| `frontend/src/components/Navbar.tsx` | Modificado - Usa `API_CONFIG` |
| `frontend/src/components/ChannelCard.tsx` | Modificado - Usa `API_CONFIG` |

---

## ✅ Verificación

### Verificar que el backend es accesible

Desde tu navegador o terminal, prueba:

```bash
# Opción 1: En la misma máquina
curl http://localhost:8000/health

# Opción 2: Desde la red LAN
curl http://192.168.1.66:8000/health
```

Deberías obtener:
```json
{
  "status": "healthy",
  "timestamp": "2026-06-11T20:30:45.123456+00:00",
  "events_loaded": 15,
  "tokens_active": 0
}
```

### Verificar que el frontend conecta correctamente

1. Abre http://localhost:3000 (o http://192.168.1.66:3000)
2. Abre la consola del navegador (F12)
3. Deberías ver logs como:
   ```
   🟢 Backend Online
   ✅ 15 eventos cargados
   ```

---

## 🚨 Problemas Comunes

### ❌ "Backend 🔴 Offline" en el navbar

**Causa:** La URL en `.env.local` es incorrecta.

**Solución:**
1. Verifica tu IP: `ipconfig` (Windows) o `ifconfig` (Mac/Linux)
2. Asegúrate de que el backend corre con `--host 0.0.0.0`
3. Prueba manualmente: `curl http://192.168.X.X:8000/health`
4. Reinicia Next.js (Ctrl+C y `npm run dev` nuevamente)

### ❌ "No se pudo conectar con el servidor" en dashboard

**Causa:** El frontend no puede alcanzar la URL de `API_CONFIG.BASE_URL`.

**Solución:**
1. Abre la consola del navegador (F12)
2. Ve a la pestaña "Network"
3. Busca la petición fallida a `/api/events`
4. Verifica que la URL es correcta

### ❌ Funciona en la misma máquina pero no en otros dispositivos

**Causa:** El backend no está escuchando en todas las interfaces.

**Solución:**
```bash
# Cambiar de:
uvicorn main:app --host localhost --port 8000

# A:
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📚 Referencias

- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [FastAPI CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- [Finding Your IP Address](https://www.lifewire.com/how-to-find-your-ip-address-2605520)

---

## 🔐 Seguridad en Producción

⚠️ **IMPORTANTE:** Antes de desplegar a producción:

1. **NO uses `--host 0.0.0.0`** - Solo en desarrollo
2. **Configura CORS correctamente** - Especifica dominios en lugar de `["*"]`
3. **Usa HTTPS** - No HTTP en producción
4. **Oculta tokens JWT** - No expongas nunca `JWT_SECRET`
5. **Valida input** - Sanea todas las entradas del usuario

---

## ✨ Próximos Pasos

- [x] Configurar `.env.local`
- [x] Centralizar configuración del API
- [x] Verificar conectividad LAN
- [ ] Configurar HTTPS para acceso remoto seguro
- [ ] Implementar autenticación de usuarios
- [ ] Desplegar a producción

---

**Made with ❤️ by Mundi TV Team**
