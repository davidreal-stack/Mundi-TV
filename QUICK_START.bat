@echo off
REM Script de inicio rápido para Mundi TV en Windows

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║         🌍 MUNDI TV - Quick Start Script             ║
echo ║                                                       ║
echo ║  Backend: Python + FastAPI en puerto 8000             ║
echo ║  Frontend: Next.js 14 en puerto 3000                  ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado. Instálalo desde https://www.python.org
    pause
    exit /b 1
)

REM Verificar si Node.js está instalado
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js no está instalado. Instálalo desde https://nodejs.org
    pause
    exit /b 1
)

echo ✅ Python y Node.js detectados
echo.

REM Instalar dependencias del Backend
echo 📦 Instalando dependencias del Backend...
cd backend
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ❌ Error al instalar dependencias del backend
    cd ..
    pause
    exit /b 1
)
echo ✅ Dependencias del Backend instaladas
cd ..
echo.

REM Instalar dependencias del Frontend
echo 📦 Instalando dependencias del Frontend...
cd frontend
call npm install --silent
if errorlevel 1 (
    echo ❌ Error al instalar dependencias del frontend
    cd ..
    pause
    exit /b 1
)
echo ✅ Dependencias del Frontend instaladas
cd ..
echo.

echo ╔═══════════════════════════════════════════════════════╗
echo ║           ✅ LISTO PARA INICIAR MUNDI TV            ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo 📖 PRÓXIMOS PASOS:
echo.
echo  1️⃣  Abre una terminal y ejecuta el Backend:
echo      cd backend
echo      uvicorn main:app --reload --host 0.0.0.0 --port 8000
echo.
echo  2️⃣  Abre otra terminal y ejecuta el Frontend:
echo      cd frontend
echo      npm run dev
echo.
echo  3️⃣  Accede a:
echo      🌐 Frontend: http://localhost:3000
echo      🔌 Backend API: http://localhost:8000
echo      📚 Swagger Docs: http://localhost:8000/docs
echo.
echo ❓ ¿Necesitas ayuda? Revisa el README.md
echo.
pause
