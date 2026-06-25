#!/bin/bash

# Script de inicio rápido para Mundi TV en macOS/Linux

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║         🌍 MUNDI TV - Quick Start Script             ║"
echo "║                                                       ║"
echo "║  Backend: Python + FastAPI en puerto 8000           ║"
echo "║  Frontend: Next.js 14 en puerto 3000                ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python no está instalado. Instálalo desde https://www.python.org"
    exit 1
fi

# Verificar si Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Node.js no está instalado. Instálalo desde https://nodejs.org"
    exit 1
fi

echo "✅ Python y Node.js detectados"
echo ""

# Instalar dependencias del Backend
echo "📦 Instalando dependencias del Backend..."
cd backend || exit
pip3 install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo "❌ Error al instalar dependencias del backend"
    cd ..
    exit 1
fi
echo "✅ Dependencias del Backend instaladas"
cd ..
echo ""

# Instalar dependencias del Frontend
echo "📦 Instalando dependencias del Frontend..."
cd frontend || exit
npm install --silent
if [ $? -ne 0 ]; then
    echo "❌ Error al instalar dependencias del frontend"
    cd ..
    exit 1
fi
echo "✅ Dependencias del Frontend instaladas"
cd ..
echo ""

echo "╔═══════════════════════════════════════════════════════╗"
echo "║           ✅ LISTO PARA INICIAR MUNDI TV            ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "📖 PRÓXIMOS PASOS:"
echo ""
echo "  1️⃣  Abre una terminal y ejecuta el Backend:"
echo "      cd backend"
echo "      uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  2️⃣  Abre otra terminal y ejecuta el Frontend:"
echo "      cd frontend"
echo "      npm run dev"
echo ""
echo "  3️⃣  Accede a:"
echo "      🌐 Frontend: http://localhost:3000"
echo "      🔌 Backend API: http://localhost:8000"
echo "      📚 Swagger Docs: http://localhost:8000/docs"
echo ""
echo "❓ ¿Necesitas ayuda? Revisa el README.md"
echo ""
